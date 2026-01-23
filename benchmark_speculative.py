"""
Helix Speculative Decoding Benchmark

Measures performance speedup of Speculative Decoding (GPT-2 + GPT-2 Medium)
vs Autoregressive Decoding (GPT-2 Medium only) on DirectML.

Usage:
    python benchmark_speculative.py
"""

import sys
import time
import torch
import logging
from src.model_loader import ModelPair
from src.speculative import SpeculativeDecoder, simple_generate

# Configure logging
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(message)s")
logger = logging.getLogger("benchmark")

def run_benchmark():
    print("=" * 60)
    print(" HELIX SPECULATIVE DECODING BENCHMARK")
    print("=" * 60)
    print(" Configuration:")
    print("   • Draft Model:  gpt2 (124M)")
    print("   • Target Model: gpt2-medium (355M)")
    print("   • Device:       DirectML (AMD GPU)")
    print("-" * 60)
    
    # 1. Load Models
    print("\n[1/4] Loading models...")
    start_load = time.time()
    try:
        model_pair = ModelPair(
            draft_model_id="gpt2",
            target_model_id="gpt2-medium",
            quantize=False
        )
        model_pair.load_all()
        print(f"      ✓ Models loaded in {time.time() - start_load:.2f}s")
    except Exception as e:
        print(f"      ✗ Failed to load models: {e}")
        return
        
    device = model_pair.device
    tokenizer = model_pair.tokenizer
    
    # Test Prompts
    prompts = [
        "The future of artificial intelligence in healthcare is",
        "To break the world record in the 100m sprint, you must",
        "Python is a popular programming language because",
    ]
    
    # 2. Benchmark Autoregressive (Baseline)
    print("\n[2/4] Benchmarking Autoregressive (Baseline)...")
    base_times = []
    base_tokens = []
    
    for i, prompt in enumerate(prompts):
        print(f"      Run {i+1}: \"{prompt[:30]}...\"")
        
        # Warmup for first run
        if i == 0:
            simple_generate(model_pair.target_model, tokenizer, "Warmup", max_tokens=5)
            
        start = time.time()
        output = simple_generate(
            model_pair.target_model,
            tokenizer,
            prompt,
            max_tokens=30,
            temperature=0.0, # Greedy for stable timing
        )
        duration = time.time() - start
        
        # Count JUST generated tokens (approximate)
        num_tokens = 30 
        speed = num_tokens / duration
        base_times.append(speed)
        print(f"      → {speed:.2f} tokens/sec")

    avg_base_speed = sum(base_times) / len(base_times)
    print(f"      ✓ Average Baseline Speed: {avg_base_speed:.2f} tok/s")
    
    # 3. Benchmark Speculative Decoding (Helix)
    print("\n[3/4] Benchmarking Speculative Decoding (Helix)...")
    spec_times = []
    
    decoder = SpeculativeDecoder(
        draft_model=model_pair.draft_model,
        target_model=model_pair.target_model,
        tokenizer=tokenizer,
        speculation_depth=5, # Try to speculate 5 tokens ahead
        temperature=0.0, 
    )
    
    for i, prompt in enumerate(prompts):
        print(f"      Run {i+1}: \"{prompt[:30]}...\"")
        
        start = time.time()
        output, stats = decoder.generate(
            prompt,
            max_tokens=30,
        )
        duration = time.time() - start
        
        speed = stats["tokens_per_step"] / (duration / stats["total_steps"]) # approx
        # More accurate speed calculation:
        real_speed = stats["total_tokens"] / duration
        spec_times.append(real_speed)
        
        print(f"      → {real_speed:.2f} tokens/sec (Accept Rate: {stats['avg_acceptance_rate']:.2f})")

    avg_spec_speed = sum(spec_times) / len(spec_times)
    print(f"      ✓ Average Helix Speed:    {avg_spec_speed:.2f} tok/s")
    
    # 4. Results
    print("\n" + "=" * 60)
    print(" RESULTS")
    print("=" * 60)
    
    speedup = avg_spec_speed / avg_base_speed
    print(f" Baseline Speed: {avg_base_speed:.2f} tokens/sec")
    print(f" Helix Speed:    {avg_spec_speed:.2f} tokens/sec")
    print(f" Speedup:        {speedup:.2f}x")
    
    if speedup > 1.0:
        print("\n ✅ SUCCESS: Speculative decoding provided a speedup!")
    else:
        print("\n ⚠ NOTE: No speedup observed. This can happen if:")
        print("    1. Models are too small (overhead dominates)")
        print("    2. GPU is not fully utilized")
        print("    3. Draft model is too slow or inaccurate")
        
    print("\n Done.")

if __name__ == "__main__":
    run_benchmark()
