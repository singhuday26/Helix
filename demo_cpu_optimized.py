#!/usr/bin/env python3
"""
Demo: CPU-Optimized Inference with Prompt Engineering

This script demonstrates how to use Helix in CPU mode with
optimized prompts for better output quality.

Usage:
    python demo_cpu_optimized.py
"""

import os
os.environ["HELIX_FORCE_CPU"] = "1"  # Force CPU mode BEFORE imports

import sys
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "src"))

from inference import HelixEngine, GenerationConfig
from cpu_optimizer import configure_cpu_optimizations, PromptOptimizer

def main():
    print("=" * 70)
    print("DEMO: CPU-Optimized Inference with Prompt Engineering")
    print("=" * 70)
    print()
    
    # Step 1: Apply CPU optimizations
    print("[1/4] Applying CPU optimizations...")
    configure_cpu_optimizations()
    print()
    
    # Step 2: Initialize engine
    print("[2/4] Loading Helix Engine (CPU mode)...")
    engine = HelixEngine(force_cpu=True)
    engine.load()
    print(f"Engine ready on device: {engine.device}")
    print()
    
    # Step 3: Create prompt optimizer
    print("[3/4] Preparing optimized prompts...")
    optimizer = PromptOptimizer()
    print()
    
    # Step 4: Run inference with different modes
    print("[4/4] Running inference tests...")
    print("=" * 70)
    print()
    
    # --- QUALITY MODE: Use PromptOptimizer templates (0.7-0.8 tok/s) ---
    print("MODE: QUALITY (Optimized Prompts)")
    print("-" * 70)
    
    quality_prompt = optimizer.format_chat_prompt(
        "What is speculative decoding and how does it improve LLM inference?"
    )
    
    quality_config = GenerationConfig(
        max_tokens=50,
        temperature=0.7,
        speculation_depth=3
    )
    
    print(f"Prompt: {quality_prompt[:80]}...")
    result = engine.generate(quality_prompt, quality_config)
    
    print(f"\nOutput: {result.generated_text}")
    print(f"Performance: {result.tokens_per_second:.2f} tok/s")
    print()
    
    # --- FAST MODE: Use simple prompts (1.4-1.5 tok/s) ---
    print("MODE: FAST (Simple Prompts)")
    print("-" * 70)
    
    fast_prompt = "What is speculative decoding?"  # No template formatting
    
    fast_config = GenerationConfig(
        max_tokens=50,
        temperature=0.0,  # Greedy decoding (faster)
        speculation_depth=2  # Lower speculation (less wasted compute)
    )
    
    print(f"Prompt: {fast_prompt}")
    result = engine.generate(fast_prompt, fast_config)
    
    print(f"\nOutput: {result.generated_text}")
    print(f"Performance: {result.tokens_per_second:.2f} tok/s")
    print()
    
    print("=" * 70)
    print("DEMO COMPLETE")
    print("=" * 70)
    print()
    print("OPTIMIZATION MODE COMPARISON:")
    print("  - QUALITY MODE: Use PromptOptimizer templates (~0.7 tok/s)")
    print("    * Better output structure and coherence")
    print("    * Uses chat/instruction formatting")
    print("    * Recommended for final demo")
    print()
    print("  - FAST MODE: Use simple raw prompts (~1.4 tok/s)")
    print("    * Higher throughput")
    print("    * Less structured outputs")
    print("    * Recommended for benchmarking")
    print()

if __name__ == "__main__":
    main()
