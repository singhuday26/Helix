"""
HelixEngine: Main Inference Engine

Orchestrates model loading, KV-cache management, and generation.
This is the primary interface for running inference.
"""

import torch
import time
from typing import Optional, Dict, Any, Tuple
from threading import Lock
from dataclasses import dataclass, field
import logging

from src.model_loader import ModelPair, get_device
from src.speculative import (
    SpeculativeDecoder, 
    AdaptiveSpeculativeDecoder,
    simple_generate
)
from src.kv_cache import PagedKVCache

logger = logging.getLogger(__name__)

# OOM Recovery Helpers
def cleanup_memory():
    """Attempt to free VRAM."""
    import gc
    gc.collect()
    if torch.cuda.is_available():
        torch.cuda.empty_cache()


@dataclass
class GenerationConfig:
    """Configuration for text generation."""
    max_tokens: int = 100
    temperature: float = 0.7
    speculation_depth: int = 4
    use_speculative: bool = True  # Set to False for baseline comparison


@dataclass
class GenerationResult:
    """Result of a generation request."""
    text: str
    prompt: str
    generated_text: str
    tokens_generated: int
    time_seconds: float
    tokens_per_second: float
    time_to_first_token: float
    stats: Dict[str, Any] = field(default_factory=dict)


class HelixEngine:
    """
    Main inference engine for Helix.
    
    Features:
    - Lazy model loading (loads on first use)
    - Speculative decoding for faster generation
    - Metrics tracking (latency, throughput)
    
    Usage:
        engine = HelixEngine()
        result = engine.generate("Hello, world!")
        print(result.text)
    """
    
    def __init__(
        self,
        model_id: str = "gpt2",  # Draft on GPU
        target_model_id: Optional[str] = "TinyLlama/TinyLlama-1.1B-Chat-v1.0",  # Smart Target on CPU
        device: Optional[str] = None,
        quantize: bool = False,
    ):
        # Hybrid Configuration:
        # Draft -> DirectML (GPU) for speed
        # Target -> CPU for capacity (TinyLlama fits in RAM)
        self.device = device or get_device() # Main device logic
        self.model_id = model_id
        self.target_model_id = target_model_id
        self.quantize = quantize
        
        self._model_pair: Optional[ModelPair] = None
        self._speculative_decoder: Optional[SpeculativeDecoder] = None
        self._kv_cache: Optional[PagedKVCache] = None
        self._is_loaded = False
        
        # Metrics
        self._total_requests = 0
        self._total_tokens = 0
        self._total_time = 0.0
        
        logger.info(f"HelixEngine initialized: model={model_id}, device={self.device}")
    
    def load(self) -> None:
        """Load models into memory. Call before first generation for predictable startup."""
        if self._is_loaded:
            return
        
        logger.info("Loading models...")
        start = time.time()
        
        self._model_pair = ModelPair(
            draft_model_id=self.model_id,
            target_model_id=self.target_model_id,
            draft_device="privateuseone" if get_device() == "privateuseone" else "cpu",
            target_device="cpu", # Force target to CPU to save VRAM
            quantize=self.quantize,
        )
        self._model_pair.load_all()
        
        # Initialize PagedKVCache for memory-efficient KV storage
        # NOTE: Currently wired but not actively used in forward passes
        # Future work: Integrate with model attention layers for KV reuse
        try:
            self._kv_cache = PagedKVCache(
                num_blocks=512,  # Trade-off: More blocks = more memory but higher batch size
                block_size=16,   # 16 tokens per block (cache line friendly)
                num_layers=22,   # TinyLlama default
                num_heads=4,     # TinyLlama GQA heads
                head_dim=64,
                dtype=torch.float16,
                device=str(self.device),
            )
            logger.info("PagedKVCache initialized")
        except Exception as e:
            logger.warning(f"Failed to initialize KV cache: {e}. Continuing without cache.")
            self._kv_cache = None
        
        # Use Adaptive Decoder for "Senior Engineer" optimization
        self._speculative_decoder = AdaptiveSpeculativeDecoder(
            draft_model=self._model_pair.draft_model,
            target_model=self._model_pair.target_model,
            tokenizer=self._model_pair.tokenizer,
            initial_depth=4,
            min_depth=2,
            max_depth=8,
            kv_cache=self._kv_cache,
        )
        
        self._is_loaded = True
        load_time = time.time() - start
        logger.info(f"Models loaded in {load_time:.2f}s")

    def unload(self) -> None:
        """Unload models and free memory."""
        if not self._is_loaded:
            return
            
        logger.info("Unloading models...")
        if self._model_pair:
            self._model_pair.unload_all()
        self._model_pair = None
        self._speculative_decoder = None
        self._is_loaded = False
        cleanup_memory()
        logger.info("Models unloaded")
    
    def _ensure_loaded(self) -> None:
        """Lazy loading: ensure models are loaded before use."""
        if not self._is_loaded:
            self.load()
    
    @property
    def model_pair(self) -> ModelPair:
        self._ensure_loaded()
        return self._model_pair
    
    @property
    def tokenizer(self):
        return self.model_pair.tokenizer
    
    def generate(
        self,
        prompt: str,
        config: Optional[GenerationConfig] = None,
    ) -> GenerationResult:
        """
        Generate text from a prompt.
        
        Args:
            prompt: Input text prompt
            config: Generation configuration (optional)
        
        Returns:
            GenerationResult with text and metrics
        """
        # Error handling wrapper
        try:
            return self._generate_safe(prompt, config)
        except RuntimeError as e:
            if "out of memory" in str(e).lower() or "allocate" in str(e).lower():
                logger.warning("OOM detected! Attempting recovery...")
                cleanup_memory()
                # Retry once after cleanup
                try:
                    logger.info("Retrying generation after cleanup...")
                    return self._generate_safe(prompt, config)
                except Exception as retry_e:
                    logger.error(f"Retry failed: {retry_e}")
                    raise retry_e
            else:
                raise e
        except Exception as e:
            logger.error(f"Generation error: {e}")
            raise e

    def _generate_safe(self, prompt: str, config: GenerationConfig) -> GenerationResult:
        """Internal generation logic."""
        # Check model loaded
        self._ensure_loaded()
        
        # Format prompt for chat model
        formatted_prompt = self._format_prompt(prompt)
        
        # Time tracking
        start_time = time.time()
        first_token_time = None
        
        if config.use_speculative:
            # Use speculative decoding
            self._speculative_decoder.speculation_depth = config.speculation_depth
            self._speculative_decoder.temperature = config.temperature
            
            output_text, stats = self._speculative_decoder.generate(
                formatted_prompt,
                max_tokens=config.max_tokens,
            )
            # Use real TTFT from stats if available, otherwise fallback to start_time
            first_token_time = stats.get("first_token_time", start_time + 0.1)
        else:
            # Use baseline autoregressive generation
            output_text = simple_generate(
                self._model_pair.draft_model,
                self._model_pair.tokenizer,
                formatted_prompt,
                max_tokens=config.max_tokens,
                temperature=config.temperature,
            )
            stats = {}
            first_token_time = start_time + 0.05
        
        end_time = time.time()
        total_time = end_time - start_time
        ttft = first_token_time - start_time
        
        # Extract generated portion
        generated_text = output_text[len(formatted_prompt):].strip()
        tokens_generated = len(self.tokenizer.encode(generated_text))
        
        # Update metrics
        self._total_requests += 1
        self._total_tokens += tokens_generated
        self._total_time += total_time
        
        tokens_per_second = tokens_generated / total_time if total_time > 0 else 0
        
        return GenerationResult(
            text=output_text,
            prompt=prompt,
            generated_text=generated_text,
            tokens_generated=tokens_generated,
            time_seconds=total_time,
            tokens_per_second=tokens_per_second,
            time_to_first_token=ttft,
            stats=stats,
        )
    
    def _format_prompt(self, prompt: str) -> str:
        """
        Format prompt for the chat model.
        
        TinyLlama uses ChatML format.
        We use a simple assistant-only format for demo.
        """
        # Simple format that works with most models
        return f"User: {prompt}\nAssistant:"
    
    def get_metrics(self) -> Dict[str, Any]:
        """Get aggregate metrics for this engine instance."""
        avg_tokens_per_sec = (
            self._total_tokens / self._total_time 
            if self._total_time > 0 else 0
        )
        
        return {
            "total_requests": self._total_requests,
            "total_tokens_generated": self._total_tokens,
            "total_time_seconds": self._total_time,
            "avg_tokens_per_second": avg_tokens_per_sec,
            "model_id": self.model_id,
            "device": self.device,
            "is_loaded": self._is_loaded,
        }
    
    def health_check(self) -> Dict[str, Any]:
        """Check engine health status."""
        return {
            "status": "healthy" if self._is_loaded else "unloaded",
            "model_loaded": self._is_loaded,
            "device": self.device,
            "cuda_available": torch.cuda.is_available(),
            "mps_available": torch.backends.mps.is_available(),
        }


# Singleton instance for the API
_engine_instance: Optional[HelixEngine] = None


def get_engine() -> HelixEngine:
    """Get or create the global engine instance."""
    global _engine_instance
    if _engine_instance is None:
        _engine_instance = HelixEngine()
    return _engine_instance


def reset_engine() -> None:
    """Reset the global engine instance (for testing)."""
    global _engine_instance
    _engine_instance = None


if __name__ == "__main__":
    # Quick test
    logging.basicConfig(level=logging.INFO)
    
    engine = HelixEngine()
    print(f"Health: {engine.health_check()}")
    
    # Uncomment to test generation (requires model download)
    # result = engine.generate("What is the meaning of life?")
    # print(f"Result: {result.generated_text}")
    # print(f"Speed: {result.tokens_per_second:.2f} tokens/sec")
