"""
Model Loader for Helix Inference Engine

Handles loading of draft (small) and target (larger) models
with DirectML support for AMD GPUs.
"""

import os
import torch
from transformers import AutoModelForCausalLM, AutoTokenizer
from typing import Optional, Tuple, Literal
import logging

logger = logging.getLogger(__name__)

DeviceType = Literal["privateuseone", "cuda", "mps", "cpu"]


def get_device(force_cpu: bool = None) -> DeviceType:
    """
    Auto-detect the best available device.
    
    Args:
        force_cpu: If True, always use CPU. If None, checks HELIX_FORCE_CPU env var.
    
    Returns:
        str: Device type ("cpu", "cuda", "mps", or "privateuseone")
    
    Trade-off: CPU is slower but more reliable (no OOM issues on DirectML).
    """
    # Check if CPU mode is forced via parameter or environment variable
    if force_cpu is None:
        force_cpu = os.getenv("HELIX_FORCE_CPU", "").lower() in ("1", "true", "yes")
    
    if force_cpu:
        logger.info("Force CPU mode enabled - skipping GPU detection")
        return "cpu"
    
    # Try DirectML first (AMD GPU on Windows)
    try:
        import torch_directml
        logger.info("DirectML available - attempting GPU inference")
        return "privateuseone"  # DirectML device name
    except ImportError:
        pass
    
    if torch.cuda.is_available():
        return "cuda"
    elif torch.backends.mps.is_available():
        return "mps"
    return "cpu"


def get_directml_device():
    """Get DirectML device if available."""
    try:
        import torch_directml
        return torch_directml.device()
    except ImportError:
        return None


class ModelPair:
    """
    Manages a draft-target model pair for speculative decoding.
    
    Architecture Decision:
    - Draft model: Small, fast (TinyLlama 1.1B)
    - Target model: Larger, more accurate (can be same as draft for demo)
    
    The draft model generates K tokens speculatively.
    The target model verifies them in a single forward pass.
    Accepted tokens are kept; rejected tokens trigger re-generation.
    """
    
    def __init__(
        self,
        draft_model_id: str = "TinyLlama/TinyLlama-1.1B-Chat-v1.0",  # Use same model family
        target_model_id: Optional[str] = None,  # None = use draft as target (demo mode)
        draft_device: Optional[DeviceType] = None,
        target_device: Optional[DeviceType] = None,
        device: Optional[DeviceType] = None, # Legacy: sets both if above are None
        quantize: bool = False,
        force_cpu: bool = None,  # New parameter for CPU mode
    ):
        # Default strategy: Draft on GPU (speed), Target on CPU (capacity)
        global_device = device or get_device(force_cpu=force_cpu)
        self.draft_device = draft_device or global_device
        
        # If target device not specified, use CPU if global is privateuseone (to save VRAM)
        # unless specifically overridden
        if target_device:
            self.target_device = target_device
        elif global_device == "privateuseone":
             self.target_device = "cpu" # Default to hybrid on DirectML
        else:
            self.target_device = global_device
            
        self.draft_model_id = draft_model_id
        self.target_model_id = target_model_id or draft_model_id
        self.quantize = quantize and self.draft_device == "cuda"
        
        self._draft_model = None
        self._target_model = None
        self._tokenizer = None
        
        logger.info(
            f"ModelPair initialized: Draft={self.draft_device} ({self.draft_model_id}), "
            f"Target={self.target_device} ({self.target_model_id})"
        )
    
    @property
    def tokenizer(self) -> AutoTokenizer:
        """Lazy-load tokenizer."""
        if self._tokenizer is None:
            logger.info(f"Loading tokenizer from {self.draft_model_id}")
            self._tokenizer = AutoTokenizer.from_pretrained(
                self.draft_model_id,
                trust_remote_code=True,
            )
            # Ensure pad token exists
            if self._tokenizer.pad_token is None:
                self._tokenizer.pad_token = self._tokenizer.eos_token
        return self._tokenizer
    
    @property
    def draft_model(self) -> AutoModelForCausalLM:
        """Lazy-load draft model."""
        if self._draft_model is None:
            self._draft_model = self._load_model(
                self.draft_model_id, 
                device=self.draft_device,
                is_draft=True
            )
        return self._draft_model
    
    @property
    def target_model(self) -> AutoModelForCausalLM:
        """Lazy-load target model (may be same as draft in demo mode)."""
        if self._target_model is None:
            if self.target_model_id == self.draft_model_id:
                # Demo mode: reuse draft model as target
                logger.info("Demo mode: using draft model as target")
                self._target_model = self.draft_model
            else:
                self._target_model = self._load_model(
                    self.target_model_id, 
                    device=self.target_device,
                    is_draft=False
                )
        return self._target_model
    
    def _load_model(self, model_id: str, device: str, is_draft: bool) -> AutoModelForCausalLM:
        """
        Load a model for DirectML or CPU inference.
        
        Trade-off Analysis:
        - DirectML: Uses AMD GPU, faster than CPU
        - No quantization on DirectML (bitsandbytes needs CUDA)
        - Use safetensors format to avoid torch.load security issue
        """
        model_type = "draft" if is_draft else "target"
        logger.info(f"Loading {model_type} model: {model_id}")
        
        try:
            # Load model - use safetensors format (avoids CVE-2025-32434)
            model = AutoModelForCausalLM.from_pretrained(
                model_id,
                torch_dtype=torch.float32,  # DirectML works best with float32
                trust_remote_code=True,
                low_cpu_mem_usage=True,
                use_safetensors=True,  # Bypass torch.load security restriction
            )
            
            # Move to device with OOM fallback
            if device == "privateuseone":
                dml_device = get_directml_device()
                if dml_device is not None:
                    logger.info(f"Moving model to DirectML device: {dml_device}")
                    try:
                        model = model.to(dml_device)
                    except RuntimeError as e:
                        if "allocate" in str(e).lower() or "memory" in str(e).lower():
                            logger.warning(f"OOM on DirectML device ({e}). Falling back to CPU.")
                            model = model.to("cpu")
                        else:
                            raise e
                else:
                    logger.warning("DirectML device not available, using CPU")
                    model = model.to("cpu")
            else:
                model = model.to(device)
            
            model.eval()
            
            # Post-load verification
            # Get the actual device the model is on (might differ from requested device)
            actual_device = next(model.parameters()).device
            logger.info(f"Verifying {model_type} model on {actual_device}...")
            try:
                # Create dummy input on the ACTUAL device the model is on
                # Use a safe token ID that exists in all models (typically 0-100 range)
                # For TinyLlama and GPT-2, token ID 1 is safe
                dummy_input = torch.tensor([[1]], device=actual_device)
                with torch.no_grad():
                    _ = model(dummy_input)
                logger.info(f"{model_type.capitalize()} model verified successfully on {actual_device}")
            except Exception as e:
                logger.error(f"Verification failed for {model_type} model: {e}")
                # Fallback to CPU if GPU verification fails
                if device == "privateuseone":
                    logger.warning("Falling back to CPU due to verification failure")
                    model = model.to("cpu")
                    # Try verification again on CPU
                    try:
                        cpu_input = torch.tensor([[1]], device="cpu")
                        with torch.no_grad():
                            _ = model(cpu_input)
                        logger.info(f"{model_type.capitalize()} model verified on CPU fallback")
                    except Exception as cpu_e:
                        logger.error(f"CPU verification also failed: {cpu_e}")
                        raise
                else:
                    raise
            
            return model
            
        except Exception as e:
            logger.error(f"Failed to load {model_type} model: {e}")
            raise
    
    def load_all(self) -> None:
        """Pre-load all models (useful for startup)."""
        _ = self.tokenizer
        _ = self.draft_model
        _ = self.target_model
        logger.info("All models loaded and ready")
        
    def unload_all(self) -> None:
        """Unload all models to free VRAM."""
        self._draft_model = None
        self._target_model = None
        import gc
        gc.collect()
        if torch.cuda.is_available():
            torch.cuda.empty_cache()
        # DirectML doesn't have explicit empty_cache, but releasing references works
        logger.info("Models unloaded")
    
    def encode(self, text: str) -> torch.Tensor:
        """Encode text to token IDs. Uses draft device by default."""
        return self.tokenizer.encode(text, return_tensors="pt").to(self.draft_device)
    
    def decode(self, token_ids: torch.Tensor) -> str:
        """Decode token IDs to text."""
        return self.tokenizer.decode(token_ids[0], skip_special_tokens=True)


# Convenience function for quick setup
def load_models(
    model_id: str = "gpt2",
    device: Optional[DeviceType] = None,
) -> Tuple[AutoModelForCausalLM, AutoTokenizer]:
    """
    Quick loader for single-model inference (demo mode).
    
    Returns:
        Tuple of (model, tokenizer)
    """
    pair = ModelPair(draft_model_id=model_id, device=device, quantize=False)
    pair.load_all()
    return pair.draft_model, pair.tokenizer


if __name__ == "__main__":
    # Quick test
    logging.basicConfig(level=logging.INFO)
    print(f"Detected device: {get_device()}")
    
    # This will download TinyLlama on first run (~2GB)
    # pair = ModelPair()
    # pair.load_all()
    # print("Models loaded successfully!")
