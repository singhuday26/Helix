"""
GPU Memory Optimization Guide for Helix

PROBLEM: DirectML OOM - models too large for available VRAM
SOLUTION: Use smaller models or optimize memory usage
"""

# Option 1: Use smaller model (RECOMMENDED for limited VRAM)

# Edit src/model_loader.py or pass model_name parameter

SMALLER_MODELS = [
"microsoft/phi-2", # 2.7B params, ~5GB VRAM
"TinyLlama/TinyLlama-1.1B", # 1.1B params, ~2GB VRAM (current)
"distilgpt2", # 82M params, ~500MB VRAM (very fast)
]

# Option 2: Enable model offloading (keep some layers on CPU)

# In src/model_loader.py, add to model loading:

# model = AutoModelForCausalLM.from_pretrained(

# model_name,

# device_map="auto", # Automatically split across GPU/CPU

# offload_folder="offload",

# max_memory={0: "8GB", "cpu": "16GB"} # Adjust to your VRAM

# )

# Option 3: Use INT8 quantization (reduces memory 50%)

# Install: pip install bitsandbytes

# Then in model loading:

# model = AutoModelForCausalLM.from_pretrained(

# model_name,

# load_in_8bit=True,

# device_map="auto"

# )

# Option 4: Use INT4 quantization (reduces memory 75%)

# Install: pip install bitsandbytes

# model = AutoModelForCausalLM.from_pretrained(

# model_name,

# load_in_4bit=True,

# device_map="auto"

# )

print("GPU Optimization Options:")
print("1. Use smaller model (phi-2 or distilgpt2)")
print("2. Enable device_map='auto' for CPU offloading")
print("3. Use INT8 quantization (50% memory reduction)")
print("4. Use INT4 quantization (75% memory reduction)")
print("\nFor DirectML on AMD GPU, Option 1 (smaller model) is most reliable")
