"""
HELIX DEMO: Quick Performance Comparison (GPT-2 based)

This version uses GPT-2 models for better compatibility and clearer speedup demo.
Uses smaller models for faster loading and better acceptance rates.

Usage:
    python demo_quick.py
"""

import sys
import os
import time
import logging

# Force CPU mode
os.environ["HELIX_FORCE_CPU"] = "1"

import torch
from colorama import init, Fore, Style, Back

# Initialize colorama
init(autoreset=True)

# Suppress verbose logging
logging.basicConfig(level=logging.WARNING)

def print_header():
    print("\n" + "=" * 70)
    print(Fore.CYAN + Style.BRIGHT + " " * 15 + "HELIX - SPECULATIVE DECODING DEMO")
    print("=" * 70 + Style.RESET_ALL)

def print_metric(label, value, unit="", color=Fore.WHITE):
    print(f"  {color}• {label:.<35} {Style.BRIGHT}{value} {unit}{Style.RESET_ALL}")

def run_demo():
    print_header()
    
    print(Fore.YELLOW + "\n⚙️  Loading GPT-2 model (small for fast demo)..." + Style.RESET_ALL)
    
    from src.model_loader import ModelPair
    from src.speculative import simple_generate, AdaptiveSpeculativeDecoder
    
    # Load GPT-2 (smaller, faster, better for demo)
    pair = ModelPair(
        draft_model_id="gpt2",  # 124M params
        target_model_id="gpt2", # Same model for demo
        force_cpu=True
    )
    pair.load_all()
    print(Fore.GREEN + "✓ Model loaded!" + Style.RESET_ALL)
    
    # Test prompt
    prompt = "The future of artificial intelligence is"
    max_tokens = 30
    
    print(f"\n{Fore.CYAN}📝 Prompt: \"{prompt}\"{Style.RESET_ALL}")
    print(f"{Fore.CYAN}📊 Max Tokens: {max_tokens}{Style.RESET_ALL}")
    
    # ========================================
    # BASELINE TEST
    # ========================================
    print(f"\n{Fore.YELLOW}{Style.BRIGHT}{'='*70}")
    print("🐢 MODE 1: BASELINE (Standard Autoregressive)")
    print(f"{'='*70}{Style.RESET_ALL}")
    
    print(f"\n{Fore.CYAN}⏳ Generating...{Style.RESET_ALL}")
    start_baseline = time.time()
    baseline_output = simple_generate(
        pair.draft_model,
        pair.tokenizer,
        prompt,
        max_tokens=max_tokens,
        temperature=0.7
    )
    end_baseline = time.time()
    baseline_time = end_baseline - start_baseline
    
    baseline_generated = baseline_output[len(prompt):].strip()
    baseline_tokens = len(pair.tokenizer.encode(baseline_generated))
    baseline_tps = baseline_tokens / baseline_time if baseline_time > 0 else 0
    
    print(f"\n{Back.WHITE}{Fore.BLACK} OUTPUT: {Style.RESET_ALL}")
    print(f"{Fore.WHITE}{baseline_generated}{Style.RESET_ALL}")
    
    print(f"\n{Fore.CYAN}📈 Metrics:{Style.RESET_ALL}")
    print_metric("Total Time", f"{baseline_time:.2f}", "seconds", Fore.RED)
    print_metric("Tokens Generated", baseline_tokens, "tokens", Fore.WHITE)
    print_metric("Tokens per Second", f"{baseline_tps:.2f}", "tok/s", Fore.RED)
    
    # ========================================
    # SPECULATIVE TEST
    # ========================================
    print(f"\n{Fore.GREEN}{Style.BRIGHT}{'='*70}")
    print("🚀 MODE 2: SPECULATIVE DECODING (Helix)")
    print(f"{'='*70}{Style.RESET_ALL}")
    
    decoder = AdaptiveSpeculativeDecoder(
        draft_model=pair.draft_model,
        target_model=pair.target_model,  # Same model = 100% acceptance expected
        tokenizer=pair.tokenizer,
        initial_depth=4,
        temperature=0.7
    )
    
    print(f"\n{Fore.CYAN}⏳ Generating...{Style.RESET_ALL}")
    start_spec = time.time()
    spec_output, stats = decoder.generate(prompt, max_tokens=max_tokens)
    end_spec = time.time()
    spec_time = end_spec - start_spec
    
    spec_tokens = stats.get('total_tokens', len(pair.tokenizer.encode(spec_output)))
    spec_tps = spec_tokens / spec_time if spec_time > 0 else 0
    
    print(f"\n{Back.WHITE}{Fore.BLACK} OUTPUT: {Style.RESET_ALL}")
    print(f"{Fore.WHITE}{spec_output}{Style.RESET_ALL}")
    
    print(f"\n{Fore.CYAN}📈 Metrics:{Style.RESET_ALL}")
    print_metric("Total Time", f"{spec_time:.2f}", "seconds", Fore.GREEN)
    print_metric("Tokens Generated", spec_tokens, "tokens", Fore.WHITE)
    print_metric("Tokens per Second", f"{spec_tps:.2f}", "tok/s", Fore.GREEN)
    print_metric("Acceptance Rate", f"{stats.get('acceptance_rate', 0):.1%}", "", Fore.CYAN)
    print_metric("Avg Speculation Depth", f"{stats.get('avg_depth', 4):.1f}", "tokens", Fore.CYAN)
    
    # ========================================
    # COMPARISON
    # ========================================
    print(f"\n{Back.CYAN}{Fore.BLACK}{'='*70}")
    print(f"{Back.CYAN}{Fore.BLACK} 📊 COMPARISON RESULTS ")
    print(f"{'='*70}{Style.RESET_ALL}")
    
    speedup = baseline_time / spec_time if spec_time > 0 else 0
    tps_improvement = spec_tps / baseline_tps if baseline_tps > 0 else 0
    time_saved = baseline_time - spec_time
    
    print(f"\n{Fore.YELLOW}Baseline:{Style.RESET_ALL}")
    print_metric("Time", f"{baseline_time:.2f}s", "", Fore.RED)
    print_metric("Speed", f"{baseline_tps:.2f} tok/s", "", Fore.RED)
    
    print(f"\n{Fore.YELLOW}Speculative Decoding:{Style.RESET_ALL}")
    print_metric("Time", f"{spec_time:.2f}s", "", Fore.GREEN)
    print_metric("Speed", f"{spec_tps:.2f} tok/s", "", Fore.GREEN)
    
    print(f"\n{Back.GREEN}{Fore.BLACK} ⚡ SPEEDUP {Style.RESET_ALL}")
    color = Fore.GREEN if speedup > 1 else Fore.RED
    print_metric("Time Speedup", f"{speedup:.2f}x", "faster" if speedup > 1 else "slower", color + Style.BRIGHT)
    print_metric("Throughput Speedup", f"{tps_improvement:.2f}x", "faster" if tps_improvement > 1 else "slower", color + Style.BRIGHT)
    print_metric("Time Saved", f"{time_saved:.2f}", "seconds", Fore.YELLOW)
    
    # ========================================
    # EXPLANATION
    # ========================================
    print(f"\n{Fore.CYAN}💡 How Speculative Decoding Works:{Style.RESET_ALL}")
    print(f"""
    1. Draft model generates {int(stats.get('avg_depth', 4))} tokens at once (speculation)
    2. Target model verifies ALL tokens in ONE forward pass
    3. Accept matching tokens, reject mismatches
    4. With {stats.get('acceptance_rate', 0):.0%} acceptance → {tps_improvement:.1f}x effective speedup!
    
    {Fore.YELLOW}Key insight:{Style.RESET_ALL} Even with same model, speculative decoding
    can batch more work per forward pass, improving throughput.
    """)
    
    print("=" * 70)
    print(Fore.GREEN + Style.BRIGHT + " " * 20 + "✓ DEMO COMPLETE!")
    print("=" * 70 + Style.RESET_ALL + "\n")

if __name__ == "__main__":
    try:
        run_demo()
    except KeyboardInterrupt:
        print(f"\n{Fore.YELLOW}Demo interrupted.{Style.RESET_ALL}")
    except Exception as e:
        print(f"\n{Fore.RED}Error: {e}{Style.RESET_ALL}")
        import traceback
        traceback.print_exc()
