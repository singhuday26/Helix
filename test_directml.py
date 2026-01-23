"""
DirectML GPU Test Script

Quick test to see if DirectML works on your AMD GPU.
Run this FIRST before proceeding with the full project.

Usage:
    python test_directml.py
"""

import sys

def test_directml():
    print("=" * 50)
    print(" DIRECTML GPU TEST")
    print("=" * 50)
    
    # Step 1: Check if torch-directml is installed
    print("\n[1/4] Checking torch-directml installation...")
    try:
        import torch
        import torch_directml
        print(f"      ✓ PyTorch version: {torch.__version__}")
        print(f"      ✓ torch-directml imported successfully")
    except ImportError as e:
        print(f"      ✗ torch-directml not installed")
        print(f"      Run: pip install torch-directml")
        return False
    
    # Step 2: Check if DirectML device is available
    print("\n[2/4] Checking DirectML device...")
    try:
        dml_device = torch_directml.device()
        print(f"      ✓ DirectML device: {dml_device}")
    except Exception as e:
        print(f"      ✗ DirectML device not available: {e}")
        return False
    
    # Step 3: Test tensor operations on DirectML
    print("\n[3/4] Testing tensor operations on GPU...")
    try:
        # Create tensors on DirectML device
        a = torch.randn(1000, 1000, device=dml_device)
        b = torch.randn(1000, 1000, device=dml_device)
        
        # Matrix multiplication
        c = torch.matmul(a, b)
        
        # Verify result
        result = c.sum().item()
        print(f"      ✓ Matrix multiplication successful")
        print(f"      ✓ Result sum: {result:.2f}")
    except Exception as e:
        print(f"      ✗ Tensor operations failed: {e}")
        return False
    
    # Step 4: Test with transformers (if available)
    print("\n[4/4] Testing with HuggingFace transformers...")
    try:
        from transformers import AutoModelForCausalLM, AutoTokenizer
        
        print("      Loading tiny model for test (this may take a minute)...")
        
        # Use a very small model for testing
        model_id = "sshleifer/tiny-gpt2"  # ~2MB, just for testing
        
        tokenizer = AutoTokenizer.from_pretrained(model_id)
        model = AutoModelForCausalLM.from_pretrained(model_id)
        
        # Try moving model to DirectML
        model = model.to(dml_device)
        
        # Test inference
        inputs = tokenizer("Hello world", return_tensors="pt")
        inputs = {k: v.to(dml_device) for k, v in inputs.items()}
        
        with torch.no_grad():
            outputs = model(**inputs)
        
        print(f"      ✓ Model loaded on DirectML successfully!")
        print(f"      ✓ Inference works!")
        
    except Exception as e:
        print(f"      ⚠ Transformers test failed: {e}")
        print(f"      This might still work with some models...")
        # Don't return False - DirectML might still work for basic ops
    
    print("\n" + "=" * 50)
    print(" RESULT: DirectML appears to be working! 🎉")
    print("=" * 50)
    print("\nYou can proceed with GPU acceleration.")
    print("If you see errors during actual model loading,")
    print("we'll fall back to CPU.\n")
    
    return True


def test_cpu_fallback():
    """Test CPU as fallback."""
    print("\n" + "=" * 50)
    print(" CPU FALLBACK TEST")
    print("=" * 50)
    
    import torch
    print(f"\n[1/2] PyTorch version: {torch.__version__}")
    print(f"      CPU threads: {torch.get_num_threads()}")
    
    print("\n[2/2] Testing CPU tensor operations...")
    a = torch.randn(1000, 1000)
    b = torch.randn(1000, 1000)
    c = torch.matmul(a, b)
    print(f"      ✓ CPU operations work fine")
    
    print("\n" + "=" * 50)
    print(" CPU fallback is ready if DirectML fails")
    print("=" * 50 + "\n")


if __name__ == "__main__":
    success = test_directml()
    
    if not success:
        print("\n⚠ DirectML test failed. Testing CPU fallback...")
        test_cpu_fallback()
        print("\nRecommendation: Proceed with CPU inference.")
        print("Run: pip install torch torchvision torchaudio")
        sys.exit(1)
    
    sys.exit(0)
