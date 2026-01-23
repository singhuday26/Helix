"""
Helix Model Loading Test - Windows + AMD DirectML Compatible

Optimized for 4GB VRAM AMD GPUs (like RX 6500M).
Uses GPT-2 Medium which fits comfortably without quantization.

Usage:
    python test_model_load.py
"""

import sys
import time
import logging

logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")
logger = logging.getLogger(__name__)

# Model options (choose based on your VRAM)
MODELS = {
    "tiny": {
        "name": "sshleifer/tiny-gpt2",  # ~2MB - instant test
        "vram": "~50MB",
        "quality": "Test only",
    },
    "small": {
        "name": "gpt2",  # 124M params
        "vram": "~500MB", 
        "quality": "Basic",
    },
    "medium": {
        "name": "gpt2-medium",  # 355M params
        "vram": "~1.5GB",
        "quality": "Good",
    },
    "phi2": {
        "name": "microsoft/phi-2",  # 2.7B params - NEEDS 8GB+ or quantization
        "vram": "~5.5GB",
        "quality": "Excellent (too large for 4GB)",
    },
}

# Default: GPT-2 Medium - best balance for 4GB VRAM
SELECTED_MODEL = "medium"


def main():
    model_config = MODELS[SELECTED_MODEL]
    model_name = model_config["name"]
    
    print("=" * 60)
    print(" HELIX MODEL LOADING TEST (Windows + DirectML)")
    print("=" * 60)
    print(f"\n📦 Model: {model_name}")
    print(f"   VRAM: {model_config['vram']}")
    print(f"   Quality: {model_config['quality']}")
    
    # Step 1: Check DirectML
    print("\n[1/4] Checking DirectML...")
    try:
        import torch
        import torch_directml
        dml_device = torch_directml.device()
        print(f"      ✓ DirectML device: {dml_device}")
        use_directml = True
    except Exception as e:
        print(f"      ⚠ DirectML not available: {e}")
        print("      Falling back to CPU...")
        import torch
        dml_device = torch.device("cpu")
        use_directml = False
    
    # Step 2: Load tokenizer
    print("\n[2/4] Loading tokenizer...")
    try:
        from transformers import AutoTokenizer
        
        tokenizer = AutoTokenizer.from_pretrained(model_name)
        
        # GPT-2 needs pad token
        if tokenizer.pad_token is None:
            tokenizer.pad_token = tokenizer.eos_token
            
        print(f"      ✓ Tokenizer loaded")
    except Exception as e:
        print(f"      ✗ Failed: {e}")
        return False
    
    # Step 3: Load model
    print(f"\n[3/4] Loading model...")
    print(f"      (First run downloads weights, please wait...)")
    try:
        from transformers import AutoModelForCausalLM
        
        start = time.time()
        
        # Load with FP32 for DirectML compatibility
        model = AutoModelForCausalLM.from_pretrained(
            model_name,
            torch_dtype=torch.float32,  # FP32 for DirectML
            low_cpu_mem_usage=True,
        )
        
        load_time = time.time() - start
        print(f"      ✓ Model loaded in {load_time:.1f}s")
        
        # Move to DirectML
        if use_directml:
            print(f"      Moving to DirectML device...")
            try:
                model = model.to(dml_device)
                device = dml_device
                print(f"      ✓ Model on DirectML!")
            except Exception as e:
                print(f"      ⚠ DirectML transfer failed: {e}")
                print(f"      Using CPU instead...")
                device = torch.device("cpu")
                model = model.to(device)
        else:
            device = torch.device("cpu")
        
        model.eval()
        
    except Exception as e:
        print(f"      ✗ Failed: {e}")
        import traceback
        traceback.print_exc()
        return False
    
    # Step 4: Test generation
    print("\n[4/4] Testing generation...")
    try:
        prompt = "The future of AI on edge devices is"
        inputs = tokenizer(prompt, return_tensors="pt")
        inputs = {k: v.to(device) for k, v in inputs.items()}
        
        print(f"      Prompt: \"{prompt}\"")
        print(f"      Generating 30 tokens...")
        
        start = time.time()
        with torch.no_grad():
            outputs = model.generate(
                **inputs,
                max_new_tokens=30,
                do_sample=True,
                temperature=0.7,
                top_p=0.9,
                pad_token_id=tokenizer.pad_token_id,
            )
        gen_time = time.time() - start
        
        result = tokenizer.decode(outputs[0], skip_special_tokens=True)
        tokens_generated = outputs.shape[1] - inputs["input_ids"].shape[1]
        
        print(f"      ✓ Generated {tokens_generated} tokens in {gen_time:.2f}s")
        print(f"      ✓ Speed: {tokens_generated/gen_time:.1f} tokens/sec")
        print(f"\n      Output: \"{result}\"")
        
    except Exception as e:
        print(f"      ✗ Generation failed: {e}")
        import traceback
        traceback.print_exc()
        return False
    
    print("\n" + "=" * 60)
    print(" SUCCESS! Helix inference working! 🎉")
    print("=" * 60)
    
    # Summary
    print("\n📊 Configuration:")
    print(f"   • Model: {model_name}")
    print(f"   • Device: {'DirectML (GPU)' if use_directml and device != torch.device('cpu') else 'CPU'}")
    print(f"   • Speed: {tokens_generated/gen_time:.1f} tokens/sec")
    
    print("\n🚀 Next Steps for Helix Speculative Decoding:")
    print("   1. Draft model: Use 'gpt2' (small) as draft")
    print("   2. Target model: Use 'gpt2-medium' as target")
    print("   3. Implement speculative decoding loop")
    print("   4. Benchmark speedup vs autoregressive\n")
    
    return True


if __name__ == "__main__":
    # Check required packages
    missing = []
    try:
        import torch
    except ImportError:
        missing.append("torch")
    try:
        import transformers
    except ImportError:
        missing.append("transformers")
    
    if missing:
        print("❌ Missing required packages. Install with:")
        print(f"    pip install {' '.join(missing)}")
        sys.exit(1)
    
    success = main()
    sys.exit(0 if success else 1)
