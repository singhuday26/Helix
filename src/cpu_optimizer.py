"""
CPU Inference Optimizer for Helix.

This module provides CPU-specific optimizations and configurations
to maximize performance when running on CPU instead of GPU.

Engineering Trade-offs:
- CPU vs GPU: 10-50x slower, but more consistent and no OOM issues
- Threading: More threads = better utilization, but diminishing returns after 4-8 threads
- Batch size: CPU benefits from smaller batches (better cache locality)
"""

import os
import logging
import torch
from typing import Dict, Any, Optional

logger = logging.getLogger(__name__)


def configure_cpu_optimizations() -> None:
    """
    Apply CPU-specific optimizations to PyTorch.
    
    Optimizations include:
    - Thread count based on available cores
    - Memory allocation strategies
    - NUMA awareness (if available)
    """
    # Get CPU core count
    cpu_count = os.cpu_count() or 4
    
    # Set optimal thread count (use physical cores, not hyperthreads)
    # Trade-off: More threads = better parallelism, but overhead increases
    optimal_threads = min(cpu_count // 2, 8)  # Cap at 8 for diminishing returns
    
    torch.set_num_threads(optimal_threads)
    torch.set_num_interop_threads(optimal_threads)
    
    logger.info(f"CPU Optimization: Using {optimal_threads} threads (available cores: {cpu_count})")
    
    # Enable CPU-specific optimizations
    if hasattr(torch, 'set_float32_matmul_precision'):
        # Use highest precision for CPU (no benefit from reduced precision)
        torch.set_float32_matmul_precision('highest')
        logger.info("CPU Optimization: Set float32 matmul precision to 'highest'")
    
    # Disable autograd for inference (saves memory and compute)
    torch.set_grad_enabled(False)
    logger.info("CPU Optimization: Disabled autograd for inference")


def get_cpu_generation_config() -> Dict[str, Any]:
    """
    Get optimized generation parameters for CPU inference.
    
    Trade-offs:
    - Smaller batch size: Better cache locality on CPU
    - Greedy decoding: Faster than sampling (no random number generation)
    - Lower speculation depth: Reduces wasted compute on CPU
    
    Returns:
        dict: Generation configuration parameters
    """
    return {
        "max_new_tokens": 50,  # Reasonable default for demo
        "do_sample": True,  # Use sampling for better quality
        "temperature": 0.7,  # Balanced creativity vs coherence
        "top_p": 0.9,  # Nucleus sampling for quality
        "top_k": 50,  # Limit vocabulary for faster sampling
        "repetition_penalty": 1.1,  # Prevent repetitive outputs
        "speculation_depth": 3,  # Lower than default (4) for CPU
    }


def estimate_cpu_performance(model_size_mb: float, sequence_length: int) -> Dict[str, float]:
    """
    Estimate expected performance on CPU.
    
    Args:
        model_size_mb: Model size in megabytes
        sequence_length: Expected generation length
    
    Returns:
        dict: Performance estimates (tokens/sec, latency, etc.)
    """
    # Rough estimates based on TinyLlama-1.1B benchmarks
    # Your actual performance: 1.45 tokens/sec on CPU
    
    cpu_count = os.cpu_count() or 4
    
    # Base throughput for 1B model on CPU (measured: 1.45 tok/s)
    base_throughput = 1.45
    
    # Scale by model size (linear approximation)
    size_factor = model_size_mb / 4400  # TinyLlama is ~4.4GB
    throughput = base_throughput / size_factor
    
    # Scale by thread count (sublinear scaling)
    thread_factor = min(cpu_count / 4, 2.0)  # Max 2x improvement
    throughput *= thread_factor
    
    latency = sequence_length / throughput
    
    return {
        "estimated_tokens_per_sec": throughput,
        "estimated_latency_sec": latency,
        "cpu_cores": cpu_count,
        "model_size_mb": model_size_mb,
    }


class PromptOptimizer:
    """
    Prompt engineering utilities for better inference outputs.
    
    The quality of LLM outputs heavily depends on prompt formatting.
    This class provides templates and utilities for optimizing prompts.
    """
    
    # Chat template for TinyLlama-1.1B-Chat
    TINYLLAMA_CHAT_TEMPLATE = "<|user|>\n{prompt}</s>\n<|assistant|>\n"
    
    # Generic instruction template
    INSTRUCTION_TEMPLATE = "### Instruction:\n{instruction}\n\n### Response:\n"
    
    # Story continuation template
    STORY_TEMPLATE = "{prefix}\n\nContinue the story:\n"
    
    @staticmethod
    def format_chat_prompt(user_message: str) -> str:
        """
        Format a user message using the TinyLlama chat template.
        
        Trade-off: Proper formatting improves quality but adds tokens.
        
        Args:
            user_message: Raw user input
        
        Returns:
            str: Formatted prompt
        """
        return PromptOptimizer.TINYLLAMA_CHAT_TEMPLATE.format(prompt=user_message)
    
    @staticmethod
    def format_instruction_prompt(instruction: str) -> str:
        """
        Format an instruction-following prompt.
        
        Args:
            instruction: Task instruction
        
        Returns:
            str: Formatted prompt
        """
        return PromptOptimizer.INSTRUCTION_TEMPLATE.format(instruction=instruction)
    
    @staticmethod
    def format_story_prompt(story_beginning: str) -> str:
        """
        Format a story continuation prompt.
        
        Args:
            story_beginning: Story prefix
        
        Returns:
            str: Formatted prompt
        """
        return PromptOptimizer.STORY_TEMPLATE.format(prefix=story_beginning)
    
    @staticmethod
    def optimize_prompt(
        prompt: str,
        mode: str = "chat",
        add_context: Optional[str] = None
    ) -> str:
        """
        Optimize a prompt based on the desired mode.
        
        Args:
            prompt: Raw prompt text
            mode: One of "chat", "instruction", "story", or "raw"
            add_context: Optional context to prepend
        
        Returns:
            str: Optimized prompt
        """
        # Add context if provided
        if add_context:
            prompt = f"{add_context}\n\n{prompt}"
        
        # Apply template based on mode
        if mode == "chat":
            return PromptOptimizer.format_chat_prompt(prompt)
        elif mode == "instruction":
            return PromptOptimizer.format_instruction_prompt(prompt)
        elif mode == "story":
            return PromptOptimizer.format_story_prompt(prompt)
        else:
            # Raw mode - no formatting
            return prompt
    
    @staticmethod
    def get_example_prompts() -> Dict[str, str]:
        """
        Get example high-quality prompts for testing.
        
        Returns:
            dict: Mapping of prompt names to optimized prompts
        """
        return {
            "creative_story": PromptOptimizer.format_story_prompt(
                "In a world where AI and humans coexisted peacefully, a young programmer discovered"
            ),
            "technical_question": PromptOptimizer.format_chat_prompt(
                "Explain the benefits of speculative decoding for LLM inference."
            ),
            "instruction_task": PromptOptimizer.format_instruction_prompt(
                "Write a haiku about machine learning."
            ),
            "conversation": PromptOptimizer.format_chat_prompt(
                "What are the key challenges in deploying AI on edge devices?"
            ),
        }


# Example usage and testing
if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    
    # Apply CPU optimizations
    configure_cpu_optimizations()
    
    # Get optimal config
    config = get_cpu_generation_config()
    print(f"\nOptimal CPU Generation Config:")
    for key, value in config.items():
        print(f"  {key}: {value}")
    
    # Estimate performance
    perf = estimate_cpu_performance(model_size_mb=4400, sequence_length=50)
    print(f"\nPerformance Estimate:")
    for key, value in perf.items():
        print(f"  {key}: {value}")
    
    # Show example prompts
    optimizer = PromptOptimizer()
    examples = optimizer.get_example_prompts()
    print(f"\nExample Optimized Prompts:")
    for name, prompt in examples.items():
        print(f"\n{name}:")
        print(f"  {prompt[:100]}...")
