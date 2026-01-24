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

Phase 4 Update: Full integration with HuggingFace models
- Extracts past_key_values from model outputs
- Converts to/from HuggingFace cache format
- Provides CachedModelWrapper for transparent caching
"""

import torch
from typing import Dict, List, Optional, Tuple, Any
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
    
    def store_hf_cache(
        self,
        seq_id: int,
        past_key_values,
        start_pos: int = 0,
    ) -> None:
        """
        Store HuggingFace past_key_values into PagedKVCache.
        
        Supports both formats:
        - Legacy tuple format: Tuple of (key, value) for each layer
        - DynamicCache format: Cache object with to_legacy_cache() method
        
        key/value shape: (batch_size, num_heads, seq_len, head_dim)
        
        Args:
            seq_id: Sequence ID to store cache for
            past_key_values: HuggingFace format cache (tuple or DynamicCache)
            start_pos: Starting position (for incremental storage)
        """
        if past_key_values is None:
            return
        
        table = self.sequences[seq_id]
        
        # Handle DynamicCache format (transformers >= 4.36)
        # Check for to_legacy_cache method (most reliable way to detect DynamicCache)
        if hasattr(past_key_values, 'to_legacy_cache'):
            # DynamicCache object - convert to tuple format
            cache_tuples = past_key_values.to_legacy_cache()
            if cache_tuples is None or len(cache_tuples) == 0:
                return
            num_layers = len(cache_tuples)
            # Get sequence length from first layer
            if cache_tuples[0][0].dim() == 4:
                seq_len = cache_tuples[0][0].shape[2]
            else:
                seq_len = cache_tuples[0][0].shape[1]
        elif isinstance(past_key_values, tuple):
            # Legacy tuple format
            num_layers = len(past_key_values)
            if num_layers == 0:
                return
            
            # Get sequence length from the cache
            if past_key_values[0][0].dim() == 4:
                seq_len = past_key_values[0][0].shape[2]
            else:
                seq_len = past_key_values[0][0].shape[1]
            
            cache_tuples = past_key_values
        else:
            logger.warning(f"Unknown past_key_values type: {type(past_key_values)}")
            return
        
        # Store only new tokens (from start_pos to end)
        for pos in range(start_pos, seq_len):
            # Allocate new block if needed
            if table.needs_new_block() and table.num_tokens > 0:
                block_id = self.allocator.allocate()
                if block_id is None:
                    raise RuntimeError("OOM: Cannot allocate new block for KV cache")
                table.add_block(block_id)
            
            # Get physical location for this token
            block_id, offset = table.get_physical_location(table.num_tokens)
            k_storage, v_storage = self.allocator.get_kv_storage(block_id)
            
            # Store each layer's KV at this position
            for layer_idx in range(num_layers):
                k, v = cache_tuples[layer_idx]
                
                # Handle different tensor formats
                if k.dim() == 4:
                    # (batch, heads, seq, dim) -> extract position pos
                    k_token = k[0, :, pos, :]  # (heads, dim)
                    v_token = v[0, :, pos, :]
                else:
                    # Handle other formats
                    k_token = k[:, pos, :]
                    v_token = v[:, pos, :]
                
                # Store in block storage
                k_storage[layer_idx, offset] = k_token.to(k_storage.dtype)
                v_storage[layer_idx, offset] = v_token.to(v_storage.dtype)
            
            table.append_token()
    
    def get_hf_cache(
        self,
        seq_id: int,
        device: Optional[str] = None,
        return_dynamic_cache: bool = True,
    ):
        """
        Retrieve cache in HuggingFace past_key_values format.
        
        Supports returning either:
        - DynamicCache object (default, for transformers >= 4.36)
        - Legacy tuple format (for older transformers)
        
        Args:
            seq_id: Sequence ID to retrieve cache for
            device: Target device for tensors
            return_dynamic_cache: If True, return DynamicCache object; else tuple
        
        Returns:
            DynamicCache or Tuple of (key, value) for each layer, or None if empty
            key/value shape: (batch_size=1, num_heads, seq_len, head_dim)
        """
        table = self.sequences.get(seq_id)
        if table is None or table.num_tokens == 0:
            return None
        
        target_device = device or self.allocator.device
        num_layers = self.allocator.num_layers
        num_heads = self.allocator.num_heads
        head_dim = self.allocator.head_dim
        
        # Gather all KV from blocks for each layer
        key_cache = []
        value_cache = []
        
        for layer_idx in range(num_layers):
            k_parts = []
            v_parts = []
            
            for block_idx, block_id in enumerate(table.block_ids):
                k_storage, v_storage = self.allocator.get_kv_storage(block_id)
                
                # Calculate tokens in this block
                start_token = block_idx * self.block_size
                end_token = min(start_token + self.block_size, table.num_tokens)
                num_tokens_in_block = end_token - start_token
                
                # Extract valid tokens
                k_parts.append(k_storage[layer_idx, :num_tokens_in_block])  # (tokens, heads, dim)
                v_parts.append(v_storage[layer_idx, :num_tokens_in_block])
            
            # Concatenate tokens
            k_layer = torch.cat(k_parts, dim=0)  # (seq_len, heads, dim)
            v_layer = torch.cat(v_parts, dim=0)
            
            # Reshape to HF format: (batch=1, heads, seq_len, dim)
            k_layer = k_layer.permute(1, 0, 2).unsqueeze(0).to(target_device)
            v_layer = v_layer.permute(1, 0, 2).unsqueeze(0).to(target_device)
            
            key_cache.append(k_layer)
            value_cache.append(v_layer)
        
        # Try to return DynamicCache for newer transformers
        if return_dynamic_cache:
            try:
                from transformers.cache_utils import DynamicCache
                
                cache = DynamicCache()
                for layer_idx in range(num_layers):
                    # DynamicCache expects float32 or model's dtype
                    k = key_cache[layer_idx].float()
                    v = value_cache[layer_idx].float()
                    cache.update(k, v, layer_idx)
                
                return cache
            except ImportError:
                # Fall back to tuple format for older transformers
                pass
        
        # Return legacy tuple format
        return tuple((key_cache[i], value_cache[i]) for i in range(num_layers))
    
    def get_cached_length(self, seq_id: int) -> int:
        """Get the number of tokens currently cached for a sequence."""
        table = self.sequences.get(seq_id)
        return table.num_tokens if table else 0


class CachedModelWrapper:
    """
    Wrapper that adds PagedKVCache support to any HuggingFace model.
    
    This wrapper intercepts model forward passes and:
    1. Retrieves cached KV from PagedKVCache before forward
    2. Stores new KV in PagedKVCache after forward
    3. Handles cache lifecycle automatically
    
    Usage:
        cache = PagedKVCache(...)
        wrapped_model = CachedModelWrapper(model, cache)
        
        seq_id = wrapped_model.start_sequence()
        outputs = wrapped_model(input_ids, seq_id=seq_id)  # Uses/updates cache
        wrapped_model.end_sequence(seq_id)
    
    Trade-off:
    - ~5% latency overhead for cache management
    - Significant memory savings for long sequences
    - Enables higher batch sizes
    """
    
    def __init__(
        self, 
        model, 
        kv_cache: PagedKVCache,
        use_cache: bool = True,
    ):
        self.model = model
        self.kv_cache = kv_cache
        self.use_cache = use_cache
        self._active_sequences: Dict[int, bool] = {}
        
        # Get device from model
        try:
            self.device = next(model.parameters()).device
        except StopIteration:
            self.device = "cpu"
    
    def start_sequence(self) -> int:
        """Start a new sequence, returns sequence ID."""
        seq_id = self.kv_cache.allocate_sequence()
        self._active_sequences[seq_id] = True
        return seq_id
    
    def end_sequence(self, seq_id: int) -> None:
        """End and cleanup a sequence."""
        if seq_id in self._active_sequences:
            self.kv_cache.free_sequence(seq_id)
            del self._active_sequences[seq_id]
    
    def __call__(
        self,
        input_ids: torch.Tensor,
        seq_id: Optional[int] = None,
        attention_mask: Optional[torch.Tensor] = None,
        **kwargs,
    ):
        """
        Forward pass with automatic KV caching.
        
        Args:
            input_ids: Token IDs (batch_size, seq_len)
            seq_id: Sequence ID for cache lookup (optional)
            attention_mask: Attention mask (optional)
            **kwargs: Additional arguments passed to model
        
        Returns:
            Model outputs (same as underlying model)
        """
        past_key_values = None
        cached_len = 0
        
        # CRITICAL: Ensure input_ids is on model's device (handles hybrid DirectML/CPU)
        model_device = self.device
        if str(input_ids.device) != str(model_device):
            try:
                input_ids = input_ids.to(model_device)
            except RuntimeError as e:
                # DirectML transfer may fail, try CPU intermediary
                if 'privateuseone' in str(e).lower():
                    input_ids = input_ids.to('cpu').to(model_device)
                else:
                    raise
        
        # Also move attention_mask if provided
        if attention_mask is not None and str(attention_mask.device) != str(model_device):
            try:
                attention_mask = attention_mask.to(model_device)
            except RuntimeError:
                attention_mask = attention_mask.to('cpu').to(model_device)
        
        # Retrieve cached KV if available
        if self.use_cache and seq_id is not None:
            past_key_values = self.kv_cache.get_hf_cache(seq_id, device=str(self.device))
            if past_key_values is not None:
                cached_len = self.kv_cache.get_cached_length(seq_id)
        
        # Determine if we need to slice input (only send new tokens)
        if past_key_values is not None and cached_len > 0:
            # Only process new tokens
            input_len = input_ids.shape[1]
            if input_len > cached_len:
                # Slice to only new tokens
                new_input_ids = input_ids[:, cached_len:]
                
                # Adjust attention mask if provided
                if attention_mask is not None:
                    # Keep full mask for proper attention
                    pass  # Don't slice attention mask
            else:
                new_input_ids = input_ids
        else:
            new_input_ids = input_ids
        
        # Forward pass with past_key_values
        try:
            outputs = self.model(
                input_ids=new_input_ids if past_key_values is not None else input_ids,
                attention_mask=attention_mask,
                past_key_values=past_key_values,
                use_cache=True,  # Always request cache output
                **kwargs,
            )
        except TypeError:
            # Model doesn't support past_key_values, fall back
            outputs = self.model(
                input_ids=input_ids,
                attention_mask=attention_mask,
                **kwargs,
            )
            return outputs
        
        # Store new KV in cache
        if self.use_cache and seq_id is not None and hasattr(outputs, 'past_key_values'):
            if outputs.past_key_values is not None:
                # Store the new tokens (start from where we left off)
                self.kv_cache.store_hf_cache(
                    seq_id,
                    outputs.past_key_values,
                    start_pos=cached_len,
                )
        
        return outputs
    
    def __getattr__(self, name):
        """Delegate attribute access to wrapped model."""
        if name in ('model', 'kv_cache', 'use_cache', '_active_sequences', 'device'):
            return object.__getattribute__(self, name)
        return getattr(self.model, name)


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
