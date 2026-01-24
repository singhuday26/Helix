"""
Model Loader for Helix Inference Engine

Handles loading of draft (small) and target (larger) models
with robust fallback chain: DirectML → CUDA → MPS → CPU.

Fallback Strategy:
1. DirectML (AMD GPUs on Windows) - prioritized for consumer hardware
2. CUDA (NVIDIA GPUs) - if available
3. MPS (Apple Silicon) - if on macOS
4. CPU - always available fallback

Each transition includes error handling and automatic recovery.
"""

import os
import sys
import torch
from transformers import AutoModelForCausalLM, AutoTokenizer
from typing import Optional, Tuple, Literal, Dict, Any
import logging
import warnings

logger = logging.getLogger(__name__)

# Supported device types in fallback order
DeviceType = Literal["privateuseone", "cuda", "mps", "cpu"]

# Device capability cache (avoid repeated detection)
_device_capabilities: Dict[str, Any] = {}


def detect_device_capabilities() -> Dict[str, Any]:
    """
    Detect all available device capabilities once and cache results.
    
    Returns:
        Dict with device availability and details
    """
    global _device_capabilities
    
    if _device_capabilities:
        return _device_capabilities
    
    capabilities = {
        "directml_available": False,
        "directml_device_count": 0,
        "cuda_available": False,
        "cuda_device_count": 0,
        "mps_available": False,
        "cpu_thread_count": os.cpu_count() or 4,
        "detection_errors": [],
    }
    
    # Check DirectML (AMD GPU on Windows)
    try:
        import torch_directml
        capabilities["directml_available"] = True
        capabilities["directml_device_count"] = torch_directml.device_count()
        logger.info(f"DirectML available: {capabilities['directml_device_count']} device(s)")
    except ImportError:
        logger.debug("torch-directml not installed")
    except Exception as e:
        capabilities["detection_errors"].append(f"DirectML: {e}")
        logger.warning(f"DirectML detection error: {e}")
    
    # Check CUDA (NVIDIA GPU)
    try:
        capabilities["cuda_available"] = torch.cuda.is_available()
        if capabilities["cuda_available"]:
            capabilities["cuda_device_count"] = torch.cuda.device_count()
            logger.info(f"CUDA available: {capabilities['cuda_device_count']} device(s)")
    except Exception as e:
        capabilities["detection_errors"].append(f"CUDA: {e}")
        logger.warning(f"CUDA detection error: {e}")
    
    # Check MPS (Apple Silicon)
    try:
        capabilities["mps_available"] = (
            hasattr(torch.backends, "mps") and torch.backends.mps.is_available()
        )
        if capabilities["mps_available"]:
            logger.info("MPS (Apple Silicon) available")
    except Exception as e:
        capabilities["detection_errors"].append(f"MPS: {e}")
        logger.warning(f"MPS detection error: {e}")
    
    _device_capabilities = capabilities
    return capabilities


def get_device(force_cpu: bool = None, prefer_device: Optional[str] = None) -> DeviceType:
    """
    Auto-detect the best available device with robust fallback chain.
    
    Fallback Order: DirectML → CUDA → MPS → CPU
    
    Args:
        force_cpu: If True, always use CPU. If None, checks HELIX_FORCE_CPU env var.
        prefer_device: Preferred device to try first ("directml", "cuda", "mps", "cpu")
    
    Returns:
        str: Device type ("cpu", "cuda", "mps", or "privateuseone")
    
    Trade-off: 
        - GPU: Faster but may have OOM issues
        - CPU: Slower but more reliable and always available
    """
    # Check if CPU mode is forced via parameter or environment variable
    if force_cpu is None:
        force_cpu = os.getenv("HELIX_FORCE_CPU", "").lower() in ("1", "true", "yes")
    
    if force_cpu:
        logger.info("Force CPU mode enabled - skipping GPU detection")
        return "cpu"
    
    # Check environment variable for preferred device
    env_prefer = os.getenv("HELIX_PREFER_DEVICE", "").lower()
    if env_prefer and prefer_device is None:
        prefer_device = env_prefer
    
    capabilities = detect_device_capabilities()
    
    # If a specific device is preferred, try it first
    if prefer_device:
        if prefer_device in ("directml", "privateuseone") and capabilities["directml_available"]:
            return "privateuseone"
        elif prefer_device == "cuda" and capabilities["cuda_available"]:
            return "cuda"
        elif prefer_device == "mps" and capabilities["mps_available"]:
            return "mps"
        elif prefer_device == "cpu":
            return "cpu"
        logger.warning(f"Preferred device '{prefer_device}' not available, falling back to auto-detection")
    
    # Standard fallback chain: DirectML → CUDA → MPS → CPU
    if capabilities["directml_available"]:
        logger.info("Selected device: DirectML (AMD GPU)")
        return "privateuseone"
    
    if capabilities["cuda_available"]:
        logger.info("Selected device: CUDA (NVIDIA GPU)")
        return "cuda"
    
    if capabilities["mps_available"]:
        logger.info("Selected device: MPS (Apple Silicon)")
        return "mps"
    
    logger.info("Selected device: CPU (fallback)")
    return "cpu"


def get_directml_device(device_index: int = 0) -> Optional[torch.device]:
    """
    Get DirectML device if available, with error handling.
    
    Args:
        device_index: Which GPU to use (default: 0)
    
    Returns:
        torch.device or None if DirectML not available
    """
    try:
        import torch_directml
        device_count = torch_directml.device_count()
        if device_count == 0:
            logger.warning("DirectML available but no devices found")
            return None
        if device_index >= device_count:
            logger.warning(f"Requested device {device_index} but only {device_count} available, using 0")
            device_index = 0
        return torch_directml.device(device_index)
    except ImportError:
        logger.debug("torch-directml not installed")
        return None
    except Exception as e:
        logger.warning(f"DirectML device creation failed: {e}")
        return None


def validate_device_tensor_ops(device: str) -> bool:
    """
    Validate that basic tensor operations work on a device.
    
    Args:
        device: Device string to test
    
    Returns:
        bool: True if device is functional
    """
    try:
        if device == "privateuseone":
            dml_device = get_directml_device()
            if dml_device is None:
                return False
            test_device = dml_device
        else:
            test_device = torch.device(device)
        
        # Test basic operations
        x = torch.tensor([1.0, 2.0, 3.0], device=test_device)
        y = x * 2
        result = y.sum().item()
        
        if abs(result - 12.0) > 0.01:
            logger.warning(f"Device {device} math validation failed: expected 12.0, got {result}")
            return False
        
        logger.debug(f"Device {device} validated successfully")
        return True
    except Exception as e:
        logger.warning(f"Device {device} validation failed: {e}")
        return False


def get_validated_device(force_cpu: bool = None, validate: bool = True) -> DeviceType:
    """
    Get device with optional validation of tensor operations.
    
    This provides an extra safety layer by testing the device before use.
    
    Args:
        force_cpu: Force CPU mode
        validate: Whether to validate device with test operations
    
    Returns:
        Validated device type
    """
    device = get_device(force_cpu=force_cpu)
    
    if not validate:
        return device
    
    # Validate the selected device
    if validate_device_tensor_ops(device):
        return device
    
    # Fallback chain if validation fails
    fallback_order = ["cuda", "mps", "cpu"]
    if device == "privateuseone":
        fallback_order = ["cuda", "mps", "cpu"]
    elif device == "cuda":
        fallback_order = ["mps", "cpu"]
    elif device == "mps":
        fallback_order = ["cpu"]
    
    for fallback in fallback_order:
        if fallback == "cuda" and not torch.cuda.is_available():
            continue
        if fallback == "mps" and not (hasattr(torch.backends, "mps") and torch.backends.mps.is_available()):
            continue
        
        if validate_device_tensor_ops(fallback):
            logger.warning(f"Device {device} failed validation, using {fallback}")
            return fallback
    
    logger.warning("All device validations failed, forcing CPU")
    return "cpu"


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
        Load a model with robust fallback chain.
        
        Fallback Strategy:
        1. Try requested device (DirectML/CUDA/MPS/CPU)
        2. On OOM or device error: fallback to CPU
        3. Verify model works with test forward pass
        4. If verification fails: try CPU as last resort
        
        Trade-off Analysis:
        - DirectML: Uses AMD GPU, faster than CPU but may have compatibility issues
        - CUDA: NVIDIA GPU, well-supported
        - CPU: Slowest but most reliable
        """
        model_type = "draft" if is_draft else "target"
        logger.info(f"Loading {model_type} model: {model_id} (target device: {device})")
        
        # Track attempted devices for logging
        attempted_devices = []
        
        def try_load_to_device(model, target_device: str) -> Tuple[AutoModelForCausalLM, str]:
            """Attempt to move model to device with error handling."""
            nonlocal attempted_devices
            attempted_devices.append(target_device)
            
            try:
                if target_device == "privateuseone":
                    dml_device = get_directml_device()
                    if dml_device is None:
                        raise RuntimeError("DirectML device not available")
                    logger.info(f"Moving model to DirectML device: {dml_device}")
                    model = model.to(dml_device)
                elif target_device == "cuda":
                    if not torch.cuda.is_available():
                        raise RuntimeError("CUDA not available")
                    model = model.to("cuda")
                elif target_device == "mps":
                    if not (hasattr(torch.backends, "mps") and torch.backends.mps.is_available()):
                        raise RuntimeError("MPS not available")
                    model = model.to("mps")
                else:
                    model = model.to("cpu")
                
                return model, target_device
                
            except RuntimeError as e:
                error_msg = str(e).lower()
                if "memory" in error_msg or "allocate" in error_msg or "oom" in error_msg:
                    logger.warning(f"OOM on {target_device}: {e}")
                elif "not available" in error_msg:
                    logger.warning(f"Device {target_device} not available: {e}")
                else:
                    logger.warning(f"Failed to move model to {target_device}: {e}")
                raise
        
        def verify_model(model, device_name: str) -> bool:
            """Verify model works with a test forward pass."""
            try:
                actual_device = next(model.parameters()).device
                dummy_input = torch.tensor([[1]], device=actual_device)
                with torch.no_grad():
                    _ = model(dummy_input)
                logger.info(f"{model_type.capitalize()} model verified on {actual_device}")
                return True
            except Exception as e:
                logger.warning(f"Model verification failed on {device_name}: {e}")
                return False
        
        try:
            # Load model to CPU first (safest approach)
            logger.info(f"Loading {model_type} model weights from {model_id}")
            model = AutoModelForCausalLM.from_pretrained(
                model_id,
                torch_dtype=torch.float32,  # DirectML works best with float32
                trust_remote_code=True,
                low_cpu_mem_usage=True,
                use_safetensors=True,  # Security: avoid torch.load vulnerabilities
            )
            
            # Attempt to move to requested device
            final_device = device
            try:
                model, final_device = try_load_to_device(model, device)
            except RuntimeError:
                # Fallback chain: try next available device
                fallback_order = self._get_fallback_chain(device)
                for fallback in fallback_order:
                    if fallback in attempted_devices:
                        continue
                    try:
                        logger.info(f"Trying fallback device: {fallback}")
                        model, final_device = try_load_to_device(model, fallback)
                        break
                    except RuntimeError:
                        continue
                else:
                    # All fallbacks failed, ensure we're on CPU
                    logger.warning("All GPU devices failed, forcing CPU")
                    model = model.to("cpu")
                    final_device = "cpu"
            
            # Set model to evaluation mode
            model.eval()
            
            # Verify the model works
            if not verify_model(model, final_device):
                if final_device != "cpu":
                    logger.warning(f"Verification failed on {final_device}, falling back to CPU")
                    model = model.to("cpu")
                    final_device = "cpu"
                    if not verify_model(model, "cpu"):
                        raise RuntimeError(f"Model verification failed on all devices")
            
            # Update the device attribute if it changed
            if is_draft and final_device != self.draft_device:
                logger.info(f"Draft device changed: {self.draft_device} -> {final_device}")
                self.draft_device = final_device
            elif not is_draft and final_device != self.target_device:
                logger.info(f"Target device changed: {self.target_device} -> {final_device}")
                self.target_device = final_device
            
            logger.info(f"✓ {model_type.capitalize()} model loaded on {final_device}")
            return model
            
        except Exception as e:
            logger.error(f"Failed to load {model_type} model: {e}")
            raise
    
    def _get_fallback_chain(self, failed_device: str) -> List[str]:
        """Get fallback device order based on what failed."""
        if failed_device == "privateuseone":
            return ["cuda", "mps", "cpu"]
        elif failed_device == "cuda":
            return ["privateuseone", "mps", "cpu"]
        elif failed_device == "mps":
            return ["cuda", "privateuseone", "cpu"]
        else:
            return ["cpu"]
    
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
