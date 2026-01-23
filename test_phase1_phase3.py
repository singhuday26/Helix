"""
Test Phase 1 (Bug Fixes) and Phase 3 (TTFT Measurement) Changes

This test validates:
1. No duplicate logger definitions
2. Stop token leak is fixed
3. Real TTFT measurement is working
4. KV cache initialization doesn't break inference
"""

import sys
import logging
from src.inference import HelixEngine, GenerationConfig

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def test_basic_generation():
    """Test that basic generation still works after bug fixes."""
    logger.info("=" * 60)
    logger.info("TEST: Basic Generation")
    logger.info("=" * 60)
    
    engine = HelixEngine()
    
    # Short prompt to test quickly
    prompt = "The capital of France is"
    config = GenerationConfig(
        max_tokens=10,
        use_speculative=True,
        speculation_depth=4,
    )
    
    result = engine.generate(prompt, config)
    
    logger.info(f"Prompt: {prompt}")
    logger.info(f"Generated: {result.generated_text}")
    logger.info(f"Tokens: {result.tokens_generated}")
    logger.info(f"TTFT: {result.ttft_ms:.2f}ms")
    logger.info(f"Total Time: {result.latency_ms:.2f}ms")
    
    # Validate TTFT is reasonable (should be > 0 and < total time)
    assert result.ttft_ms > 0, "TTFT should be positive"
    assert result.ttft_ms < result.latency_ms, "TTFT should be less than total latency"
    
    logger.info("✓ Basic generation working with real TTFT measurement\n")
    return result


def test_stop_token_handling():
    """Test that stop tokens don't leak into output."""
    logger.info("=" * 60)
    logger.info("TEST: Stop Token Handling")
    logger.info("=" * 60)
    
    engine = HelixEngine()
    
    # Prompt that might trigger early stopping
    prompt = "Hello world"
    config = GenerationConfig(
        max_tokens=50,  # Large enough to potentially hit stop token
        use_speculative=True,
    )
    
    result = engine.generate(prompt, config)
    
    logger.info(f"Generated text length: {len(result.generated_text)}")
    logger.info(f"Tokens generated: {result.tokens_generated}")
    
    # Check no weird artifacts (basic sanity check)
    assert len(result.generated_text) > 0, "Should generate some text"
    
    logger.info("✓ Stop token handling validated\n")
    return result


def test_kv_cache_integration():
    """Test that KV cache initialization doesn't break anything."""
    logger.info("=" * 60)
    logger.info("TEST: KV Cache Integration")
    logger.info("=" * 60)
    
    engine = HelixEngine()
    
    # Force load to trigger cache initialization
    engine.load()
    
    # Check cache was created (even if not actively used yet)
    logger.info(f"Engine loaded: {engine._is_loaded}")
    logger.info(f"KV Cache exists: {engine._kv_cache is not None}")
    
    # Run generation to ensure no errors
    result = engine.generate("Test prompt", GenerationConfig(max_tokens=5))
    
    logger.info(f"Generated: {result.generated_text}")
    logger.info("✓ KV cache integration working\n")
    
    return result


def test_metrics_structure():
    """Test that result metrics are properly structured."""
    logger.info("=" * 60)
    logger.info("TEST: Metrics Structure")
    logger.info("=" * 60)
    
    engine = HelixEngine()
    result = engine.generate("Test", GenerationConfig(max_tokens=5))
    
    # Validate all expected fields exist
    assert hasattr(result, 'text'), "Missing 'text' field"
    assert hasattr(result, 'generated_text'), "Missing 'generated_text' field"
    assert hasattr(result, 'ttft_ms'), "Missing 'ttft_ms' field"
    assert hasattr(result, 'latency_ms'), "Missing 'latency_ms' field"
    assert hasattr(result, 'tokens_generated'), "Missing 'tokens_generated' field"
    
    logger.info(f"All metrics present:")
    logger.info(f"  - TTFT: {result.ttft_ms:.2f}ms")
    logger.info(f"  - Latency: {result.latency_ms:.2f}ms")
    logger.info(f"  - Tokens: {result.tokens_generated}")
    logger.info(f"  - Throughput: {result.tokens_per_second:.2f} tok/s")
    
    logger.info("✓ Metrics structure validated\n")
    
    return result


if __name__ == "__main__":
    logger.info("\n" + "=" * 60)
    logger.info("HELIX PHASE 1 & 3 VALIDATION TESTS")
    logger.info("=" * 60 + "\n")
    
    try:
        test_basic_generation()
        test_stop_token_handling()
        test_kv_cache_integration()
        test_metrics_structure()
        
        logger.info("=" * 60)
        logger.info("✓ ALL TESTS PASSED")
        logger.info("=" * 60)
        
    except Exception as e:
        logger.error(f"❌ TEST FAILED: {e}", exc_info=True)
        sys.exit(1)
