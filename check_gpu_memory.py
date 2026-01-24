"""
Check GPU Memory and Provide Recommendations
"""
import torch
try:
    import torch_directml
    directml_available = True
except:
    directml_available = False

print("="*60)
print("GPU MEMORY DIAGNOSTIC")
print("="*60 + "\n")

# Check CUDA
print(f"CUDA Available: {torch.cuda.is_available()}")
if torch.cuda.is_available():
    print(f"CUDA Device: {torch.cuda.get_device_name(0)}")
    print(f"CUDA Memory: {torch.cuda.get_device_properties(0).total_memory / 1e9:.2f} GB")

# Check DirectML
print(f"\nDirectML Available: {directml_available}")
if directml_available:
    try:
        device = torch_directml.device()
        print(f"DirectML Device: {device}")
    except Exception as e:
        print(f"DirectML Error: {e}")

# Check MPS (Apple Silicon)
print(f"\nMPS (Apple Silicon) Available: {torch.backends.mps.is_available()}")

# Current PyTorch version
print(f"\nPyTorch Version: {torch.__version__}")

# Memory recommendations
print("\n" + "="*60)
print("MEMORY ANALYSIS")
print("="*60 + "\n")

print("Current Issue: DirectML OOM (16MB allocation failed)")
print("Current Model: TinyLlama-1.1B (~3.2GB VRAM required)")
print("\nRECOMMENDATIONS:\n")

print("📊 OPTION 1: Use DistilGPT2 (Smallest, Fastest)")
print("   Model Size: ~500MB VRAM")
print("   Speed: 5-10x faster than TinyLlama")
print("   Quality: Lower but usable for demos")
print("   How: Change model_name to 'distilgpt2'")

print("\n📊 OPTION 2: Use Microsoft Phi-2 (Better Quality)")
print("   Model Size: ~5GB VRAM")
print("   Speed: Similar to TinyLlama")
print("   Quality: Higher quality outputs")
print("   How: Change model_name to 'microsoft/phi-2'")
print("   Note: May still hit VRAM limits on your GPU")

print("\n📊 OPTION 3: Enable INT8 Quantization")
print("   Model Size: Reduces VRAM by 50%")
print("   TinyLlama: 3.2GB → 1.6GB")
print("   Speed: Slightly slower but fits in VRAM")
print("   How: Install bitsandbytes, use load_in_8bit=True")

print("\n📊 OPTION 4: Stay on CPU (Current - Works Fine)")
print("   Model Size: No VRAM limit")
print("   Speed: Slower but reliable")
print("   Quality: Same as GPU")
print("   Status: ✅ Currently working")

print("\n" + "="*60)
print("QUICK FIX FOR GPU")
print("="*60 + "\n")

print("To enable GPU with smaller model, edit src/model_loader.py:")
print('''
# Change line ~40:
DEFAULT_DRAFT_MODEL = "distilgpt2"  # Instead of TinyLlama
DEFAULT_TARGET_MODEL = "distilgpt2"
''')

print("\nOr set environment variable:")
print('$env:HELIX_MODEL="distilgpt2"')
print('python run.py')

print("\n" + "="*60)
print("BOTTOM LINE")
print("="*60 + "\n")

print("✅ CPU is working fine - 1.5 tokens/sec is reasonable")
print("🚀 For GPU: Switch to distilgpt2 (500MB, should fit)")
print("📈 For better quality: Use better prompts (see OUTPUT_QUALITY_GUIDE.py)")
print("⚡ For faster speed: GPU with smaller model OR batch processing")

print("\n")
