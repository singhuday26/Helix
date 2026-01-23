"""
Latency Benchmark for Helix Inference Engine

Measures:
- Time-To-First-Token (TTFT)
- Tokens per second
- End-to-end latency

Compares baseline (autoregressive) vs speculative decoding.
"""

import torch
import time
import sys
import os

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.inference import HelixEngine, GenerationConfig


def benchmark_latency(
    engine: HelixEngine,
    prompts: list[str],
    max_tokens: int = 50,
    use_speculative: bool = True,
) -> dict:
    """Run latency benchmark on a set of prompts."""
    
    results = {
        "num_prompts": len(prompts),
        "max_tokens": max_tokens,
        "use_speculative": use_speculative,
        "latencies": [],
        "tokens_generated": [],
        "tokens_per_second": [],
        "ttft": [],
    }
    
    config = GenerationConfig(
        max_tokens=max_tokens,
        temperature=0.7,
        use_speculative=use_speculative,
    )
    
    for i, prompt in enumerate(prompts):
        print(f"  [{i+1}/{len(prompts)}] Processing: '{prompt[:40]}...'")
        
        result = engine.generate(prompt, config)
        
        results["latencies"].append(result.time_seconds)
        results["tokens_generated"].append(result.tokens_generated)
        results["tokens_per_second"].append(result.tokens_per_second)
        results["ttft"].append(result.time_to_first_token)
    
    # Compute aggregates
    results["avg_latency"] = sum(results["latencies"]) / len(results["latencies"])
    results["avg_tokens_per_second"] = sum(results["tokens_per_second"]) / len(results["tokens_per_second"])
    results["avg_ttft"] = sum(results["ttft"]) / len(results["ttft"])
    results["total_tokens"] = sum(results["tokens_generated"])
    
    return results


def print_results(name: str, results: dict):
    """Pretty print benchmark results."""
    print(f"\n{'='*50}")
    print(f" {name}")
    print(f"{'='*50}")
    print(f" Prompts:            {results['num_prompts']}")
    print(f" Max Tokens:         {results['max_tokens']}")
    print(f" Speculative:        {results['use_speculative']}")
    print(f"{'─'*50}")
    print(f" Avg Latency:        {results['avg_latency']:.3f}s")
    print(f" Avg TTFT:           {results['avg_ttft']:.3f}s")
    print(f" Avg Tokens/sec:     {results['avg_tokens_per_second']:.2f}")
    print(f" Total Tokens:       {results['total_tokens']}")
    print(f"{'='*50}\n")


def main():
    print("\n" + "="*60)
    print(" HELIX LATENCY BENCHMARK")
    print("="*60 + "\n")
    
    # Test prompts
    prompts = [
        "Explain quantum computing in simple terms.",
        "What is the capital of France?",
        "Write a haiku about programming.",
        "How does photosynthesis work?",
        "What is the meaning of life?",
    ]
    
    # Initialize engine
    print("Initializing engine...")
    engine = HelixEngine()
    
    print("Loading model (this may take a minute on first run)...")
    engine.load()
    
    # Warmup
    print("\nWarmup run...")
    engine.generate("Hello world", GenerationConfig(max_tokens=10))
    
    # Run baseline benchmark
    print("\n" + "-"*60)
    print(" Running BASELINE benchmark (autoregressive)")
    print("-"*60)
    baseline_results = benchmark_latency(
        engine, prompts, max_tokens=50, use_speculative=False
    )
    
    # Run speculative benchmark
    print("\n" + "-"*60)
    print(" Running SPECULATIVE benchmark")
    print("-"*60)
    speculative_results = benchmark_latency(
        engine, prompts, max_tokens=50, use_speculative=True
    )
    
    # Print results
    print_results("BASELINE (Autoregressive)", baseline_results)
    print_results("SPECULATIVE DECODING", speculative_results)
    
    # Compute speedup
    speedup = baseline_results["avg_latency"] / speculative_results["avg_latency"]
    throughput_improvement = (
        speculative_results["avg_tokens_per_second"] / 
        baseline_results["avg_tokens_per_second"]
    )
    
    print("\n" + "="*60)
    print(" COMPARISON")
    print("="*60)
    print(f" Latency Speedup:       {speedup:.2f}x")
    print(f" Throughput Improvement: {throughput_improvement:.2f}x")
    print("="*60 + "\n")


if __name__ == "__main__":
    main()
