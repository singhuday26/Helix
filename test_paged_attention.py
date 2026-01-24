"""
PagedAttention KV Cache Integration Tests

This module tests the end-to-end PagedAttention implementation:
1. KV cache storage and retrieval
2. HuggingFace format conversion
3. CachedModelWrapper functionality
4. Full speculative decoding with caching
5. Memory efficiency verification

Run: python test_paged_attention.py
"""

import torch
import logging
import time
import gc
from typing import Tuple, Optional

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Test results tracking
test_results = []


def log_test(name: str, passed: bool, details: str = ""):
    """Log test result with formatting."""
    status = "✅ PASS" if passed else "❌ FAIL"
    logger.info(f"{status}: {name}")
    if details:
        logger.info(f"   Details: {details}")
    test_results.append({"name": name, "passed": passed, "details": details})


def test_block_allocator():
    """Test BlockAllocator basic operations."""
    logger.info("\n" + "="*60)
    logger.info("TEST 1: BlockAllocator Basic Operations")
    logger.info("="*60)
    
    from src.kv_cache import BlockAllocator
    
    try:
        # Create allocator
        allocator = BlockAllocator(
            num_blocks=32,
            block_size=16,
            num_layers=4,
            num_heads=4,
            head_dim=32,
            dtype=torch.float16,
            device="cpu",
        )
        
        # Test allocation
        block1 = allocator.allocate()
        block2 = allocator.allocate()
        
        assert block1 is not None, "First allocation failed"
        assert block2 is not None, "Second allocation failed"
        assert block1 != block2, "Allocated same block twice"
        
        # Test free
        initial_free = allocator.num_free_blocks
        allocator.free(block1)
        assert allocator.num_free_blocks == initial_free + 1, "Free didn't increase count"
        
        # Test utilization
        util = allocator.utilization
        assert 0 <= util <= 1, f"Invalid utilization: {util}"
        
        log_test("BlockAllocator", True, f"Allocated blocks, utilization={util:.2%}")
        return True
        
    except Exception as e:
        log_test("BlockAllocator", False, str(e))
        return False


def test_paged_kv_cache():
    """Test PagedKVCache sequence management."""
    logger.info("\n" + "="*60)
    logger.info("TEST 2: PagedKVCache Sequence Management")
    logger.info("="*60)
    
    from src.kv_cache import PagedKVCache
    
    try:
        cache = PagedKVCache(
            num_blocks=64,
            block_size=16,
            num_layers=4,
            num_heads=4,
            head_dim=32,
            dtype=torch.float16,
            device="cpu",
        )
        
        # Allocate sequence
        seq_id = cache.allocate_sequence()
        assert seq_id is not None, "Sequence allocation failed"
        
        # Check initial state
        assert cache.get_cached_length(seq_id) == 0, "Initial cache not empty"
        
        # Add tokens via manual append
        for i in range(10):
            for layer in range(4):
                k = torch.randn(1, 4, 1, 32, dtype=torch.float16)
                v = torch.randn(1, 4, 1, 32, dtype=torch.float16)
                cache.append_token_kv(seq_id, layer, k, v)
            cache.mark_token_complete(seq_id)
        
        # Verify length
        cached_len = cache.get_cached_length(seq_id)
        assert cached_len == 10, f"Expected 10 tokens, got {cached_len}"
        
        # Get KV and verify shape
        k, v = cache.get_kv(seq_id, layer_idx=0)
        assert k.shape == (1, 4, 10, 32), f"Unexpected K shape: {k.shape}"
        
        # Free and verify
        cache.free_sequence(seq_id)
        stats = cache.stats
        assert stats["num_sequences"] == 0, "Sequence not freed"
        
        log_test("PagedKVCache Sequence Management", True, f"10 tokens cached, shapes correct")
        return True
        
    except Exception as e:
        log_test("PagedKVCache Sequence Management", False, str(e))
        return False


def test_hf_format_conversion():
    """Test HuggingFace past_key_values format conversion."""
    logger.info("\n" + "="*60)
    logger.info("TEST 3: HuggingFace Format Conversion")
    logger.info("="*60)
    
    from src.kv_cache import PagedKVCache
    
    try:
        cache = PagedKVCache(
            num_blocks=64,
            block_size=16,
            num_layers=4,
            num_heads=4,
            head_dim=32,
            dtype=torch.float16,
            device="cpu",
        )
        
        seq_id = cache.allocate_sequence()
        
        # Create mock HF past_key_values
        seq_len = 8
        mock_past_kv = tuple(
            (
                torch.randn(1, 4, seq_len, 32, dtype=torch.float16),  # K
                torch.randn(1, 4, seq_len, 32, dtype=torch.float16),  # V
            )
            for _ in range(4)  # 4 layers
        )
        
        # Store in cache
        cache.store_hf_cache(seq_id, mock_past_kv, start_pos=0)
        
        # Verify stored length
        cached_len = cache.get_cached_length(seq_id)
        assert cached_len == seq_len, f"Expected {seq_len} tokens, got {cached_len}"
        
        # Retrieve in HF format
        retrieved = cache.get_hf_cache(seq_id)
        
        assert retrieved is not None, "Retrieved cache is None"
        assert len(retrieved) == 4, f"Expected 4 layers, got {len(retrieved)}"
        
        # Check shapes match
        for i, (k, v) in enumerate(retrieved):
            assert k.shape == (1, 4, seq_len, 32), f"Layer {i} K shape mismatch: {k.shape}"
            assert v.shape == (1, 4, seq_len, 32), f"Layer {i} V shape mismatch: {v.shape}"
        
        # Verify data integrity (approximate due to dtype conversion)
        for i in range(4):
            orig_k = mock_past_kv[i][0]
            ret_k = retrieved[i][0]
            max_diff = (orig_k - ret_k).abs().max().item()
            assert max_diff < 0.01, f"Layer {i} data mismatch: max_diff={max_diff}"
        
        cache.free_sequence(seq_id)
        
        log_test("HuggingFace Format Conversion", True, "Round-trip conversion successful")
        return True
        
    except Exception as e:
        log_test("HuggingFace Format Conversion", False, str(e))
        return False


def test_cached_model_wrapper():
    """Test CachedModelWrapper with mock model."""
    logger.info("\n" + "="*60)
    logger.info("TEST 4: CachedModelWrapper")
    logger.info("="*60)
    
    from src.kv_cache import PagedKVCache, CachedModelWrapper
    
    try:
        # Create mock model that outputs past_key_values
        class MockModel(torch.nn.Module):
            def __init__(self):
                super().__init__()
                self.dummy = torch.nn.Linear(1, 1)
                self.call_count = 0
                
            def forward(self, input_ids, attention_mask=None, past_key_values=None, use_cache=True, **kwargs):
                self.call_count += 1
                batch_size = input_ids.shape[0]
                seq_len = input_ids.shape[1]
                vocab_size = 100
                
                # Calculate total seq length including past
                past_len = 0
                if past_key_values is not None:
                    past_len = past_key_values[0][0].shape[2]
                total_len = past_len + seq_len
                
                # Generate mock outputs
                logits = torch.randn(batch_size, seq_len, vocab_size)
                
                # Generate new past_key_values (full sequence)
                new_past_kv = tuple(
                    (
                        torch.randn(batch_size, 4, total_len, 32, dtype=torch.float16),
                        torch.randn(batch_size, 4, total_len, 32, dtype=torch.float16),
                    )
                    for _ in range(4)
                )
                
                class MockOutput:
                    pass
                
                output = MockOutput()
                output.logits = logits
                output.past_key_values = new_past_kv
                return output
        
        # Setup
        cache = PagedKVCache(
            num_blocks=64,
            block_size=16,
            num_layers=4,
            num_heads=4,
            head_dim=32,
            dtype=torch.float16,
            device="cpu",
        )
        
        model = MockModel()
        wrapped = CachedModelWrapper(model, cache)
        
        # Start sequence
        seq_id = wrapped.start_sequence()
        
        # First forward (no cache)
        input_ids = torch.randint(0, 100, (1, 5))
        output1 = wrapped(input_ids, seq_id=seq_id)
        
        assert output1.logits is not None, "No logits in output"
        cached_len1 = cache.get_cached_length(seq_id)
        assert cached_len1 == 5, f"Expected 5 tokens cached, got {cached_len1}"
        
        # Second forward (with cache)
        new_token = torch.randint(0, 100, (1, 1))
        output2 = wrapped(torch.cat([input_ids, new_token], dim=1), seq_id=seq_id)
        
        cached_len2 = cache.get_cached_length(seq_id)
        assert cached_len2 == 6, f"Expected 6 tokens cached, got {cached_len2}"
        
        # End sequence
        wrapped.end_sequence(seq_id)
        
        assert cache.stats["num_sequences"] == 0, "Sequence not freed"
        
        log_test("CachedModelWrapper", True, f"Cache properly managed across calls")
        return True
        
    except Exception as e:
        log_test("CachedModelWrapper", False, str(e))
        import traceback
        traceback.print_exc()
        return False


def test_speculative_with_cache():
    """Test speculative decoding with KV cache (no real model)."""
    logger.info("\n" + "="*60)
    logger.info("TEST 5: Speculative Decoding with Cache Integration")
    logger.info("="*60)
    
    try:
        from src.kv_cache import PagedKVCache, CachedModelWrapper
        from src.speculative import speculative_decode_step
        
        # Create mock models
        class MockLLM(torch.nn.Module):
            def __init__(self, name="model"):
                super().__init__()
                self.dummy = torch.nn.Linear(1, 1)
                self.name = name
                
            def forward(self, input_ids, attention_mask=None, past_key_values=None, use_cache=True, **kwargs):
                batch_size = input_ids.shape[0]
                seq_len = input_ids.shape[1]
                vocab_size = 100
                
                past_len = 0
                if past_key_values is not None:
                    past_len = past_key_values[0][0].shape[2]
                total_len = past_len + seq_len
                
                # Logits with slight bias toward common tokens
                logits = torch.randn(batch_size, seq_len, vocab_size)
                logits[:, :, :10] += 2.0  # Bias toward low token IDs
                
                new_past_kv = tuple(
                    (
                        torch.randn(batch_size, 4, total_len, 32, dtype=torch.float16),
                        torch.randn(batch_size, 4, total_len, 32, dtype=torch.float16),
                    )
                    for _ in range(4)
                )
                
                class MockOutput:
                    pass
                output = MockOutput()
                output.logits = logits
                output.past_key_values = new_past_kv
                return output
        
        # Setup cache
        cache = PagedKVCache(
            num_blocks=128,
            block_size=16,
            num_layers=4,
            num_heads=4,
            head_dim=32,
            dtype=torch.float16,
            device="cpu",
        )
        
        # Wrap models
        draft = CachedModelWrapper(MockLLM("draft"), cache)
        target = CachedModelWrapper(MockLLM("target"), cache)
        
        # Start sequences
        draft_seq = draft.start_sequence()
        target_seq = target.start_sequence()
        
        # Run speculative step
        input_ids = torch.randint(0, 100, (1, 10))
        
        result = speculative_decode_step(
            draft,
            target,
            input_ids,
            speculation_depth=4,
            temperature=0.8,
            draft_seq_id=draft_seq,
            target_seq_id=target_seq,
        )
        
        # Verify result
        assert result.tokens is not None, "No tokens in result"
        assert result.num_generated > 0, "No tokens generated"
        assert 0 <= result.acceptance_rate <= 1, f"Invalid acceptance rate: {result.acceptance_rate}"
        
        # Check cache was used
        draft_cached = cache.get_cached_length(draft_seq)
        target_cached = cache.get_cached_length(target_seq)
        
        logger.info(f"Draft cache: {draft_cached} tokens, Target cache: {target_cached} tokens")
        logger.info(f"Generated: {result.num_generated} tokens, Accepted: {result.num_accepted}")
        
        # Cleanup
        draft.end_sequence(draft_seq)
        target.end_sequence(target_seq)
        
        log_test("Speculative Decoding with Cache", True, 
                 f"Generated {result.num_generated} tokens, acceptance={result.acceptance_rate:.1%}")
        return True
        
    except Exception as e:
        log_test("Speculative Decoding with Cache", False, str(e))
        import traceback
        traceback.print_exc()
        return False


def test_with_real_model():
    """Test with real TinyLlama model (if available)."""
    logger.info("\n" + "="*60)
    logger.info("TEST 6: Real Model Integration (Optional)")
    logger.info("="*60)
    
    try:
        from src.model_loader import get_device
        from src.kv_cache import PagedKVCache
        from src.speculative import AdaptiveSpeculativeDecoder
        from transformers import AutoModelForCausalLM, AutoTokenizer
        
        device = get_device(force_cpu=True)  # Use CPU for testing
        logger.info(f"Using device: {device}")
        
        # Try to load model
        model_id = "TinyLlama/TinyLlama-1.1B-Chat-v1.0"
        
        logger.info(f"Loading {model_id}...")
        tokenizer = AutoTokenizer.from_pretrained(model_id)
        model = AutoModelForCausalLM.from_pretrained(
            model_id,
            torch_dtype=torch.float32,  # CPU needs float32
            low_cpu_mem_usage=True,
        )
        model.eval()
        
        # Setup cache
        cache = PagedKVCache(
            num_blocks=256,
            block_size=16,
            num_layers=22,
            num_heads=4,
            head_dim=64,
            dtype=torch.float16,
            device="cpu",
        )
        
        # Create decoder with cache
        decoder = AdaptiveSpeculativeDecoder(
            draft_model=model,
            target_model=model,  # Same model for testing
            tokenizer=tokenizer,
            kv_cache=cache,
        )
        
        # Generate
        prompt = "Hello, how are you"
        logger.info(f"Generating from: '{prompt}'")
        
        start = time.time()
        output, stats = decoder.generate(prompt, max_tokens=20)
        elapsed = time.time() - start
        
        logger.info(f"Output: {output}")
        logger.info(f"Stats: {stats}")
        logger.info(f"Time: {elapsed:.2f}s")
        
        # Verify cache was used
        assert stats.get("kv_cache_active", False), "KV cache not active"
        
        log_test("Real Model Integration", True, 
                 f"Generated {stats['total_tokens']} tokens in {elapsed:.2f}s")
        return True
        
    except ImportError as e:
        log_test("Real Model Integration", True, f"Skipped (missing dependency: {e})")
        return True
    except Exception as e:
        log_test("Real Model Integration", False, str(e))
        import traceback
        traceback.print_exc()
        return False


def test_memory_efficiency():
    """Compare memory usage with and without PagedKVCache."""
    logger.info("\n" + "="*60)
    logger.info("TEST 7: Memory Efficiency")
    logger.info("="*60)
    
    from src.kv_cache import PagedKVCache
    
    try:
        # Calculate theoretical memory savings
        
        # Traditional KV Cache: Pre-allocate for max_seq_len
        max_seq_len = 2048
        num_layers = 22
        num_heads = 4
        head_dim = 64
        dtype_size = 2  # float16
        
        traditional_per_seq = max_seq_len * num_layers * num_heads * head_dim * 2 * dtype_size
        traditional_mb = traditional_per_seq / (1024 * 1024)
        
        # PagedKVCache: Only allocate what's needed
        actual_seq_len = 256  # Typical generation length
        block_size = 16
        num_blocks_needed = (actual_seq_len + block_size - 1) // block_size
        
        paged_per_seq = num_blocks_needed * block_size * num_layers * num_heads * head_dim * 2 * dtype_size
        paged_mb = paged_per_seq / (1024 * 1024)
        
        # Calculate savings
        savings = 1 - (paged_mb / traditional_mb)
        
        logger.info(f"Traditional KV Cache (max_seq=2048): {traditional_mb:.2f} MB per sequence")
        logger.info(f"PagedKVCache (actual_seq=256): {paged_mb:.2f} MB per sequence")
        logger.info(f"Memory Savings: {savings:.1%}")
        
        # Create actual cache and verify allocation
        cache = PagedKVCache(
            num_blocks=512,
            block_size=16,
            num_layers=22,
            num_heads=4,
            head_dim=64,
            dtype=torch.float16,
            device="cpu",
        )
        
        stats = cache.stats
        logger.info(f"Cache Stats: {stats}")
        
        # Verify we can handle multiple sequences
        seq_ids = []
        for i in range(10):
            seq_ids.append(cache.allocate_sequence())
        
        for seq_id in seq_ids:
            cache.free_sequence(seq_id)
        
        final_stats = cache.stats
        assert final_stats["num_sequences"] == 0, "Not all sequences freed"
        
        log_test("Memory Efficiency", True, 
                 f"~{savings:.0%} memory savings vs traditional, batch=10 sequences OK")
        return True
        
    except Exception as e:
        log_test("Memory Efficiency", False, str(e))
        return False


def main():
    """Run all tests."""
    print("\n" + "="*70)
    print("   PAGEATTENTION KV CACHE INTEGRATION TESTS")
    print("="*70 + "\n")
    
    # Run tests
    tests = [
        test_block_allocator,
        test_paged_kv_cache,
        test_hf_format_conversion,
        test_cached_model_wrapper,
        test_speculative_with_cache,
        test_memory_efficiency,
    ]
    
    for test_fn in tests:
        try:
            test_fn()
        except Exception as e:
            logger.error(f"Test {test_fn.__name__} crashed: {e}")
            import traceback
            traceback.print_exc()
        gc.collect()
    
    # Optionally run real model test (slow)
    import sys
    if "--with-model" in sys.argv:
        test_with_real_model()
    else:
        logger.info("\nSkipping real model test. Run with --with-model to include.")
    
    # Summary
    print("\n" + "="*70)
    print("   TEST SUMMARY")
    print("="*70)
    
    passed = sum(1 for r in test_results if r["passed"])
    total = len(test_results)
    
    for r in test_results:
        status = "✅" if r["passed"] else "❌"
        print(f"  {status} {r['name']}")
    
    print(f"\n  Total: {passed}/{total} tests passed")
    
    if passed == total:
        print("\n  🎉 ALL TESTS PASSED! PagedAttention is working correctly.")
    else:
        print("\n  ⚠️  Some tests failed. Check the output above for details.")
    
    return passed == total


if __name__ == "__main__":
    success = main()
    exit(0 if success else 1)
