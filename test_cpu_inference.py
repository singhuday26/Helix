#!/usr/bin/env python3
"""
CPU-Optimized Inference Test

This script demonstrates:
1. Force CPU mode (no GPU fallback overhead)
2. Optimized prompts for better output quality
3. CPU-specific performance optimizations

Usage:
    # Force CPU mode via environment variable:
    set HELIX_FORCE_CPU=1
    python test_cpu_inference.py
    
    # Or let the script set it:
    python test_cpu_inference.py
"""

import os
import sys
import time
import logging

# Force CPU mode BEFORE importing Helix modules
os.environ["HELIX_FORCE_CPU"] = "1"

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "src"))

from inference import HelixEngine, GenerationConfig
from cpu_optimizer import (
    configure_cpu_optimizations,
    get_cpu_generation_config,
    PromptOptimizer,
    estimate_cpu_performance
)

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def test_cpu_inference():
    """Run comprehensive CPU inference tests with optimized prompts."""
    
    print("=" * 70)
    print("HELIX CPU-OPTIMIZED INFERENCE TEST")
    print("=" * 70)
    print()
    
    # Step 1: Apply CPU optimizations
    print("[1/5] Applying CPU optimizations...")
    configure_cpu_optimizations()
    print()
    
    # Step 2: Get optimal generation config
    print("[2/5] Loading optimal CPU generation config...")
    cpu_params = get_cpu_generation_config()
    print("Configuration:")
    for key, value in cpu_params.items():
        print(f"  - {key}: {value}")
    
    # Create GenerationConfig object
    gen_config = GenerationConfig(
        max_tokens=cpu_params.get("max_new_tokens", 50),
        temperature=cpu_params.get("temperature", 0.7),
        speculation_depth=cpu_params.get("speculation_depth", 3),
    )
    print()
    
    # Step 3: Initialize engine
    print("[3/5] Initializing Helix Engine (CPU mode)...")
    start_time = time.time()
    
    engine = HelixEngine()
    engine.load()
    
    load_time = time.time() - start_time
    print(f"Model loaded in {load_time:.2f}s")
    print(f"Device: {engine.device}")
    print()
    
    # Step 4: Get example prompts
    print("[4/5] Preparing optimized prompts...")
    optimizer = PromptOptimizer()
    test_prompts = optimizer.get_example_prompts()
    print(f"Loaded {len(test_prompts)} test prompts")
    print()
    
    # Step 5: Run inference tests
    print("[5/5] Running inference tests...")
    print("=" * 70)
    print()
    
    results = []
    
    for idx, (name, prompt) in enumerate(test_prompts.items(), 1):
        print(f"Test {idx}/{len(test_prompts)}: {name}")
        print("-" * 70)
        print(f"PROMPT (first 100 chars):")
        print(f"  {prompt[:100]}...")
        print()
        
        # Run inference
        start_time = time.time()
        output = engine.generate(
            prompt=prompt,
            config=gen_config
        )
        elapsed = time.time() - start_time
        
        # Calculate metrics
        tokens_generated = output.tokens_generated
        tokens_per_sec = tokens_generated / elapsed if elapsed > 0 else 0
        
        print("GENERATED OUTPUT:")
        print(f"  {output.generated_text}")
        print()
        print("PERFORMANCE:")
        print(f"  - Tokens generated: {tokens_generated}")
        print(f"  - Time elapsed: {elapsed:.2f}s")
        print(f"  - Tokens/sec: {tokens_per_sec:.2f}")
        print(f"  - TTFT: {output.time_to_first_token:.3f}s")
        print()
        
        results.append({
            "name": name,
            "tokens": tokens_generated,
            "time": elapsed,
            "tokens_per_sec": tokens_per_sec,
        })
    
    # Summary
    print("=" * 70)
    print("SUMMARY")
    print("=" * 70)
    
    total_tokens = sum(r["tokens"] for r in results)
    total_time = sum(r["time"] for r in results)
    avg_tokens_per_sec = total_tokens / total_time if total_time > 0 else 0
    
    print(f"Tests completed: {len(results)}/{len(test_prompts)}")
    print(f"Total tokens generated: {total_tokens}")
    print(f"Total time: {total_time:.2f}s")
    print(f"Average throughput: {avg_tokens_per_sec:.2f} tokens/sec")
    print(f"Model load time: {load_time:.2f}s")
    print()
    
    # Performance estimate vs actual
    print("PERFORMANCE COMPARISON:")
    estimate = estimate_cpu_performance(model_size_mb=4400, sequence_length=50)
    print(f"  Estimated: {estimate['estimated_tokens_per_sec']:.2f} tokens/sec")
    print(f"  Actual: {avg_tokens_per_sec:.2f} tokens/sec")
    variance = ((avg_tokens_per_sec - estimate['estimated_tokens_per_sec']) / 
                estimate['estimated_tokens_per_sec'] * 100)
    print(f"  Variance: {variance:+.1f}%")
    print()
    
    # System health check
    print("SYSTEM HEALTH:")
    metrics = engine.get_metrics()
    print(f"  - Total requests: {metrics['total_requests']}")
    print(f"  - Status: HEALTHY" if metrics['total_requests'] > 0 else "  - Status: IDLE")
    print(f"  - Model loaded: YES")
    print(f"  - Device: {engine.device}")
    print(f"  - CPU optimization: ENABLED")
    print()
    
    print("=" * 70)
    print("CPU INFERENCE TEST COMPLETE")
    print("=" * 70)
    
    return results


if __name__ == "__main__":
    try:
        results = test_cpu_inference()
        sys.exit(0)
    except Exception as e:
        logger.error(f"Test failed: {e}", exc_info=True)
        sys.exit(1)
