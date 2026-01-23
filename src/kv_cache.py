"""
PagedAttention KV-Cache Manager

Implements non-contiguous memory allocation for KV-cache to reduce
fragmentation and increase batch throughput on memory-constrained devices.

Architecture Decision:
- Standard KV-cache: Pre-allocate contiguous block for max_seq_len
- PagedAttention: Allocate fixed-size "blocks" on-demand, map via block table

Trade-off:
- Pro: Eliminates internal fragmentation -> 4-5x batch size improvement
- Con: Block table lookup adds ~5% latency overhead
- Verdict: Worth it for edge devices where memory is the bottleneck
"""

import torch
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass, field
import logging

logger = logging.getLogger(__name__)

# Default block size: 16 tokens per block
# Trade-off: Smaller blocks = less fragmentation but more metadata overhead
# 16 is the sweet spot for most models (fits in GPU cache line)
DEFAULT_BLOCK_SIZE = 16


@dataclass
class Block:
    """A fixed-size memory block for storing K or V tensors."""
    block_id: int
    size: int  # Number of tokens this block can hold
    ref_count: int = 0  # For copy-on-write optimization
    
    def is_free(self) -> bool:
        return self.ref_count == 0
    
    def allocate(self) -> None:
        self.ref_count += 1
    
    def free(self) -> None:
        self.ref_count = max(0, self.ref_count - 1)


class BlockAllocator:
    """
    Manages a pool of fixed-size memory blocks.
    
    This is analogous to a page allocator in an OS kernel.
    Blocks can be allocated/freed independently, enabling
    fine-grained memory management for KV-cache.
    """
    
    def __init__(
        self,
        num_blocks: int,
        block_size: int = DEFAULT_BLOCK_SIZE,
        num_layers: int = 32,
        num_heads: int = 32,
        head_dim: int = 64,
        dtype: torch.dtype = torch.float16,
        device: str = "cuda",
    ):
        self.num_blocks = num_blocks
        self.block_size = block_size
        self.num_layers = num_layers
        self.num_heads = num_heads
        self.head_dim = head_dim
        self.dtype = dtype
        self.device = device
        
        # Metadata for each block
        self.blocks: List[Block] = [
            Block(block_id=i, size=block_size) 
            for i in range(num_blocks)
        ]
        
        # Free block stack (LIFO for cache locality)
        self.free_blocks: List[int] = list(range(num_blocks))
        
        # Pre-allocate the actual tensor storage
        # Shape: (num_blocks, 2, num_layers, block_size, num_heads, head_dim)
        # The "2" is for K and V
        self._storage = torch.zeros(
            (num_blocks, 2, num_layers, block_size, num_heads, head_dim),
            dtype=dtype,
            device=device,
        )
        
        logger.info(
            f"BlockAllocator initialized: {num_blocks} blocks x {block_size} tokens, "
            f"storage size: {self._storage.numel() * 2 / 1e9:.2f} GB"
        )
    
    def allocate(self) -> Optional[int]:
        """Allocate a single block. Returns block_id or None if OOM."""
        if not self.free_blocks:
            logger.warning("BlockAllocator: No free blocks available (OOM)")
            return None
        
        block_id = self.free_blocks.pop()
        self.blocks[block_id].allocate()
        return block_id
    
    def free(self, block_id: int) -> None:
        """Free a block back to the pool."""
        block = self.blocks[block_id]
        block.free()
        if block.is_free():
            self.free_blocks.append(block_id)
    
    def get_kv_storage(self, block_id: int) -> Tuple[torch.Tensor, torch.Tensor]:
        """Get K and V tensors for a specific block."""
        return self._storage[block_id, 0], self._storage[block_id, 1]
    
    @property
    def num_free_blocks(self) -> int:
        return len(self.free_blocks)
    
    @property
    def utilization(self) -> float:
        """Memory utilization as a percentage."""
        return 1.0 - (self.num_free_blocks / self.num_blocks)


@dataclass
class SequenceBlockTable:
    """
    Maps logical token positions to physical block IDs for a single sequence.
    
    This is the "page table" for a single generation request.
    Virtual token position i maps to:
    - block_table[i // block_size] -> physical block
    - offset = i % block_size -> position within block
    """
    block_ids: List[int] = field(default_factory=list)
    block_size: int = DEFAULT_BLOCK_SIZE
    num_tokens: int = 0
    
    def get_physical_location(self, logical_pos: int) -> Tuple[int, int]:
        """
        Map logical token position to (block_id, offset_within_block).
        """
        block_idx = logical_pos // self.block_size
        offset = logical_pos % self.block_size
        return self.block_ids[block_idx], offset
    
    def needs_new_block(self) -> bool:
        """Check if we need to allocate a new block for the next token."""
        return self.num_tokens % self.block_size == 0
    
    def add_block(self, block_id: int) -> None:
        """Add a new block to this sequence's table."""
        self.block_ids.append(block_id)
    
    def append_token(self) -> None:
        """Record that a new token was added."""
        self.num_tokens += 1


class PagedKVCache:
    """
    Main KV-Cache manager with paged memory allocation.
    
    Usage:
    1. Create cache: cache = PagedKVCache(...)
    2. Start sequence: seq_id = cache.allocate_sequence()
    3. For each token: cache.append(seq_id, k_tensor, v_tensor)
    4. Get past KV: k_cache, v_cache = cache.get_kv(seq_id)
    5. End sequence: cache.free_sequence(seq_id)
    """
    
    def __init__(
        self,
        num_blocks: int = 1024,
        block_size: int = DEFAULT_BLOCK_SIZE,
        num_layers: int = 22,  # TinyLlama has 22 layers
        num_heads: int = 4,    # TinyLlama has 4 KV heads (GQA)
        head_dim: int = 64,
        dtype: torch.dtype = torch.float16,
        device: str = "cuda",
    ):
        self.block_size = block_size
        self.allocator = BlockAllocator(
            num_blocks=num_blocks,
            block_size=block_size,
            num_layers=num_layers,
            num_heads=num_heads,
            head_dim=head_dim,
            dtype=dtype,
            device=device,
        )
        
        # Active sequences: seq_id -> block table
        self.sequences: Dict[int, SequenceBlockTable] = {}
        self._next_seq_id = 0
    
    def allocate_sequence(self) -> int:
        """Start tracking a new sequence. Returns sequence ID."""
        seq_id = self._next_seq_id
        self._next_seq_id += 1
        self.sequences[seq_id] = SequenceBlockTable(block_size=self.block_size)
        
        # Allocate first block
        block_id = self.allocator.allocate()
        if block_id is None:
            raise RuntimeError("OOM: Cannot allocate initial block")
        self.sequences[seq_id].add_block(block_id)
        
        return seq_id
    
    def free_sequence(self, seq_id: int) -> None:
        """Free all blocks associated with a sequence."""
        if seq_id not in self.sequences:
            return
        
        table = self.sequences[seq_id]
        for block_id in table.block_ids:
            self.allocator.free(block_id)
        
        del self.sequences[seq_id]
    
    def append_token_kv(
        self,
        seq_id: int,
        layer_idx: int,
        k: torch.Tensor,  # Shape: (1, num_heads, 1, head_dim)
        v: torch.Tensor,
    ) -> None:
        """
        Append K and V for a single token to the cache.
        
        This is called once per layer per token generated.
        """
        table = self.sequences[seq_id]
        
        # Check if we need a new block
        if table.needs_new_block() and table.num_tokens > 0:
            block_id = self.allocator.allocate()
            if block_id is None:
                raise RuntimeError("OOM: Cannot allocate new block")
            table.add_block(block_id)
        
        # Get physical location
        block_id, offset = table.get_physical_location(table.num_tokens)
        k_storage, v_storage = self.allocator.get_kv_storage(block_id)
        
        # Write to storage
        # k_storage shape: (num_layers, block_size, num_heads, head_dim)
        k_storage[layer_idx, offset] = k.squeeze(0).squeeze(1)  # Remove batch and seq dims
        v_storage[layer_idx, offset] = v.squeeze(0).squeeze(1)
    
    def get_kv(
        self,
        seq_id: int,
        layer_idx: int,
    ) -> Tuple[torch.Tensor, torch.Tensor]:
        """
        Get all cached K and V for a sequence at a specific layer.
        
        Returns:
            k: (1, num_heads, seq_len, head_dim)
            v: (1, num_heads, seq_len, head_dim)
        """
        table = self.sequences[seq_id]
        
        if table.num_tokens == 0:
            # No cache yet
            return None, None
        
        # Gather from all blocks
        k_parts = []
        v_parts = []
        
        for block_idx, block_id in enumerate(table.block_ids):
            k_storage, v_storage = self.allocator.get_kv_storage(block_id)
            
            # Determine how many tokens in this block
            start_token = block_idx * self.block_size
            end_token = min(start_token + self.block_size, table.num_tokens)
            num_tokens_in_block = end_token - start_token
            
            # Extract valid tokens from this block
            k_parts.append(k_storage[layer_idx, :num_tokens_in_block])
            v_parts.append(v_storage[layer_idx, :num_tokens_in_block])
        
        # Concatenate along sequence dimension
        k = torch.cat(k_parts, dim=0)  # (seq_len, num_heads, head_dim)
        v = torch.cat(v_parts, dim=0)
        
        # Reshape to expected format: (1, num_heads, seq_len, head_dim)
        k = k.permute(1, 0, 2).unsqueeze(0)
        v = v.permute(1, 0, 2).unsqueeze(0)
        
        return k, v
    
    def mark_token_complete(self, seq_id: int) -> None:
        """Mark that a token generation is complete (increment counter)."""
        self.sequences[seq_id].append_token()
    
    @property
    def stats(self) -> dict:
        """Get cache statistics."""
        return {
            "num_sequences": len(self.sequences),
            "utilization": self.allocator.utilization,
            "free_blocks": self.allocator.num_free_blocks,
            "total_blocks": self.allocator.num_blocks,
        }


if __name__ == "__main__":
    # Quick test
    logging.basicConfig(level=logging.INFO)
    
    device = "cuda" if torch.cuda.is_available() else "cpu"
    cache = PagedKVCache(num_blocks=64, device=device)
    
    # Allocate a sequence
    seq_id = cache.allocate_sequence()
    print(f"Allocated sequence {seq_id}")
    print(f"Stats: {cache.stats}")
    
    # Simulate adding tokens
    for i in range(20):  # Add 20 tokens
        for layer in range(22):
            k = torch.randn(1, 4, 1, 64, device=device, dtype=torch.float16)
            v = torch.randn(1, 4, 1, 64, device=device, dtype=torch.float16)
            cache.append_token_kv(seq_id, layer, k, v)
        cache.mark_token_complete(seq_id)
    
    print(f"After 20 tokens - Stats: {cache.stats}")
    
    # Get cached KV
    k, v = cache.get_kv(seq_id, layer_idx=0)
    print(f"Cached K shape: {k.shape}")  # Should be (1, 4, 20, 64)
    
    # Free sequence
    cache.free_sequence(seq_id)
    print(f"After free - Stats: {cache.stats}")
