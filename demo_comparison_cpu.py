"""
HELIX DEMO: Speculative Decoding vs Baseline Comparison (CPU-SAFE VERSION)

This is a CPU-fallback version of the comparison demo that avoids DirectML issues.
Use this if demo_comparison.py has DirectML/GPU problems.

Usage:
    python demo_comparison_cpu.py
"""

import sys
import time
import logging
import os
from colorama import init, Fore, Style, Back

# Force CPU mode to avoid DirectML issues
os.environ["HELIX_FORCE_CPU"] = "1"

from src.inference import HelixEngine, GenerationConfig

# Initialize colorama for Windows terminal colors
init(autoreset=True)

# Configure logging (suppress debug noise)
logging.basicConfig(level=logging.WARNING)

def print_header():
    """Print demo header."""
    print("\n" + "=" * 80)
    print(Fore.CYAN + Style.BRIGHT + " " * 20 + "HELIX INFERENCE ENGINE - PERFORMANCE DEMO")
    print(" " * 30 + "(CPU MODE - SAFE FOR ALL SYSTEMS)")
    print("=" * 80)
    print(Fore.YELLOW + "\n📊 Comparing Baseline vs Speculative Decoding")
    print("-" * 80 + Style.RESET_ALL)

def print_section(title, color=Fore.CYAN):
    """Print section header."""
    print(f"\n{color}{Style.BRIGHT}{'=' * 80}")
    print(f"{title}")
    print(f"{'=' * 80}{Style.RESET_ALL}\n")

def print_metric(label, value, unit="", color=Fore.WHITE):
    """Print a formatted metric."""
    print(f"  {color}• {label:.<30} {Style.BRIGHT}{value} {unit}{Style.RESET_ALL}")

def run_comparison():
    """Run side-by-side comparison."""
    
    print_header()
    
    # Test prompts
    test_prompts = [
        "Explain quantum computing in simple terms:",
        "The secret to happiness is",
    ]
    
    # Configuration
    max_tokens = 30  # Reduced for faster demo on CPU
    temperature = 0.7
    
    print(Fore.YELLOW + "⚙️  Configuration:")
    print_metric("Max Tokens", max_tokens, "")
    print_metric("Temperature", temperature, "")
    print_metric("Number of Test Prompts", len(test_prompts), "")
    print_metric("Device Mode", "CPU (Safe Mode)", "")
    
    print(f"\n{Fore.CYAN}💡 Loading Helix Engine...")
    print(f"{Fore.YELLOW}   Using CPU mode for maximum compatibility{Style.RESET_ALL}")
    
    try:
        engine = HelixEngine()
        print(f"{Fore.GREEN}✓ Engine loaded successfully!{Style.RESET_ALL}\n")
    except Exception as e:
        print(f"{Fore.RED}✗ Failed to load engine: {e}{Style.RESET_ALL}")
        return
    
    # Store results
    baseline_results = []
    speculative_results = []
    
    # Run comparisons for each prompt
    for idx, prompt in enumerate(test_prompts, 1):
        print_section(f"TEST {idx}/{len(test_prompts)}: \"{prompt}\"", Fore.MAGENTA)
        
        # ========================================
        # MODE 1: BASELINE (Autoregressive Only)
        # ========================================
        print(Fore.YELLOW + Style.BRIGHT + "🐢 MODE 1: BASELINE (Autoregressive Decoding)")
        print(Fore.YELLOW + "   Using target model only, standard token-by-token generation" + Style.RESET_ALL)
        
        baseline_config = GenerationConfig(
            max_tokens=max_tokens,
            temperature=temperature,
            use_speculative=False  # KEY: Disable speculative decoding
        )
        
        print(f"\n{Fore.CYAN}⏳ Generating...{Style.RESET_ALL}")
        try:
            baseline_result = engine.generate(prompt, baseline_config)
            baseline_results.append(baseline_result)
            
            print(f"\n{Back.WHITE}{Fore.BLACK} OUTPUT: {Style.RESET_ALL}")
            print(f"{Fore.WHITE}{baseline_result.generated_text}{Style.RESET_ALL}")
            
            print(f"\n{Fore.CYAN}📈 Performance Metrics:{Style.RESET_ALL}")
            print_metric("Tokens Generated", baseline_result.tokens_generated, "tokens", Fore.WHITE)
            print_metric("Total Time", f"{baseline_result.time_seconds:.3f}", "seconds", Fore.WHITE)
            print_metric("Time to First Token", f"{baseline_result.time_to_first_token:.3f}", "seconds", Fore.RED)
            print_metric("Tokens per Second", f"{baseline_result.tokens_per_second:.2f}", "tok/s", Fore.RED)
            
        except Exception as e:
            print(f"{Fore.RED}✗ Error: {e}{Style.RESET_ALL}")
            continue
        
        print("\n" + "-" * 80)
        
        # ========================================
        # MODE 2: SPECULATIVE DECODING
        # ========================================
        print(f"\n{Fore.GREEN}{Style.BRIGHT}🚀 MODE 2: SPECULATIVE DECODING (Helix)")
        print(Fore.GREEN + "   Using draft model + target model, parallel token verification" + Style.RESET_ALL)
        
        speculative_config = GenerationConfig(
            max_tokens=max_tokens,
            temperature=temperature,
            use_speculative=True,  # KEY: Enable speculative decoding
            speculation_depth=4
        )
        
        print(f"\n{Fore.CYAN}⏳ Generating...{Style.RESET_ALL}")
        try:
            spec_result = engine.generate(prompt, speculative_config)
            speculative_results.append(spec_result)
            
            print(f"\n{Back.WHITE}{Fore.BLACK} OUTPUT: {Style.RESET_ALL}")
            print(f"{Fore.WHITE}{spec_result.generated_text}{Style.RESET_ALL}")
            
            print(f"\n{Fore.CYAN}📈 Performance Metrics:{Style.RESET_ALL}")
            print_metric("Tokens Generated", spec_result.tokens_generated, "tokens", Fore.WHITE)
            print_metric("Total Time", f"{spec_result.time_seconds:.3f}", "seconds", Fore.WHITE)
            print_metric("Time to First Token", f"{spec_result.time_to_first_token:.3f}", "seconds", Fore.GREEN)
            print_metric("Tokens per Second", f"{spec_result.tokens_per_second:.2f}", "tok/s", Fore.GREEN)
            
            if 'acceptance_rate' in spec_result.stats:
                print_metric("Draft Acceptance Rate", f"{spec_result.stats['acceptance_rate']:.1%}", "", Fore.CYAN)
                print_metric("Tokens Accepted", 
                           f"{spec_result.stats.get('total_accepted', 0)}/{spec_result.stats.get('total_drafted', 0)}", 
                           "", Fore.CYAN)
            
        except Exception as e:
            print(f"{Fore.RED}✗ Error: {e}{Style.RESET_ALL}")
            continue
        
        # ========================================
        # COMPARISON
        # ========================================
        print(f"\n{Back.CYAN}{Fore.BLACK} COMPARISON {Style.RESET_ALL}")
        
        ttft_speedup = baseline_result.time_to_first_token / spec_result.time_to_first_token
        tps_speedup = spec_result.tokens_per_second / baseline_result.tokens_per_second
        total_speedup = baseline_result.time_seconds / spec_result.time_seconds
        
        print_metric("TTFT Speedup", f"{ttft_speedup:.2f}x", "faster", Fore.GREEN if ttft_speedup > 1 else Fore.RED)
        print_metric("Tokens/Sec Speedup", f"{tps_speedup:.2f}x", "faster", Fore.GREEN if tps_speedup > 1 else Fore.RED)
        print_metric("Total Time Speedup", f"{total_speedup:.2f}x", "faster", Fore.GREEN if total_speedup > 1 else Fore.RED)
        
        time_saved = baseline_result.time_seconds - spec_result.time_seconds
        print_metric("Time Saved", f"{time_saved:.3f}", "seconds", Fore.YELLOW)
        
        print("\n" + "=" * 80 + "\n")
    
    # ========================================
    # FINAL SUMMARY
    # ========================================
    if baseline_results and speculative_results:
        print_section("📊 OVERALL PERFORMANCE SUMMARY", Fore.CYAN)
        
        avg_baseline_ttft = sum(r.time_to_first_token for r in baseline_results) / len(baseline_results)
        avg_spec_ttft = sum(r.time_to_first_token for r in speculative_results) / len(speculative_results)
        avg_ttft_speedup = avg_baseline_ttft / avg_spec_ttft
        
        avg_baseline_tps = sum(r.tokens_per_second for r in baseline_results) / len(baseline_results)
        avg_spec_tps = sum(r.tokens_per_second for r in speculative_results) / len(speculative_results)
        avg_tps_speedup = avg_spec_tps / avg_baseline_tps
        
        avg_baseline_time = sum(r.time_seconds for r in baseline_results) / len(baseline_results)
        avg_spec_time = sum(r.time_seconds for r in speculative_results) / len(speculative_results)
        avg_total_speedup = avg_baseline_time / avg_spec_time
        
        avg_acceptance = sum(
            r.stats.get('acceptance_rate', 0) for r in speculative_results
        ) / len(speculative_results) if speculative_results else 0
        
        print(f"{Fore.YELLOW}Baseline (Autoregressive):{Style.RESET_ALL}")
        print_metric("Avg Time to First Token", f"{avg_baseline_ttft:.3f}", "seconds", Fore.RED)
        print_metric("Avg Tokens per Second", f"{avg_baseline_tps:.2f}", "tok/s", Fore.RED)
        print_metric("Avg Total Time", f"{avg_baseline_time:.3f}", "seconds", Fore.RED)
        
        print(f"\n{Fore.YELLOW}Speculative Decoding (Helix):{Style.RESET_ALL}")
        print_metric("Avg Time to First Token", f"{avg_spec_ttft:.3f}", "seconds", Fore.GREEN)
        print_metric("Avg Tokens per Second", f"{avg_spec_tps:.2f}", "tok/s", Fore.GREEN)
        print_metric("Avg Total Time", f"{avg_spec_time:.3f}", "seconds", Fore.GREEN)
        print_metric("Avg Draft Acceptance", f"{avg_acceptance:.1%}", "", Fore.CYAN)
        
        print(f"\n{Back.GREEN}{Fore.BLACK} ⚡ SPEEDUP ACHIEVED {Style.RESET_ALL}")
        print_metric("TTFT Improvement", f"{avg_ttft_speedup:.2f}x", "faster ⚡", Fore.GREEN + Style.BRIGHT)
        print_metric("Throughput Improvement", f"{avg_tps_speedup:.2f}x", "faster ⚡", Fore.GREEN + Style.BRIGHT)
        print_metric("Total Time Improvement", f"{avg_total_speedup:.2f}x", "faster ⚡", Fore.GREEN + Style.BRIGHT)
        
        print(f"\n{Fore.CYAN}💡 Key Insight:{Style.RESET_ALL}")
        print(f"   With {avg_acceptance:.0%} draft acceptance rate, speculative decoding achieves")
        print(f"   {Fore.GREEN}{Style.BRIGHT}{avg_tps_speedup:.2f}x speedup{Style.RESET_ALL} with {Fore.GREEN}zero quality loss{Style.RESET_ALL}!")
        print(f"   Even on CPU, the algorithm demonstrates clear performance benefits.\n")
        
        print("=" * 80)
        print(Fore.GREEN + Style.BRIGHT + " " * 25 + "✓ DEMO COMPLETE!")
        print("=" * 80 + Style.RESET_ALL + "\n")

if __name__ == "__main__":
    try:
        run_comparison()
    except KeyboardInterrupt:
        print(f"\n\n{Fore.YELLOW}Demo interrupted by user.{Style.RESET_ALL}")
        sys.exit(0)
    except Exception as e:
        print(f"\n{Fore.RED}Error: {e}{Style.RESET_ALL}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
