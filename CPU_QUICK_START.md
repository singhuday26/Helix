# Quick Start: CPU-Optimized Inference

## 3-Step Setup

### Step 1: Enable CPU Mode

```bash
# Windows CMD
set HELIX_FORCE_CPU=1

# PowerShell
$env:HELIX_FORCE_CPU="1"

# Linux/Mac
export HELIX_FORCE_CPU=1
```

### Step 2: Run Test

```bash
# Activate virtual environment
.\ven\Scripts\activate  # Windows
source ven/bin/activate  # Linux/Mac

# Run CPU-optimized test
python test_cpu_inference.py
```

### Step 3: Review Results

Expected output:

```
Model loaded in ~4.6s (was 11.2s = 58% faster!)
Average throughput: ~0.7 tokens/sec
Tests completed: 4/4
Status: HEALTHY
```

## Code Example

```python
import os
os.environ["HELIX_FORCE_CPU"] = "1"

from src.inference import HelixEngine, GenerationConfig
from src.cpu_optimizer import configure_cpu_optimizations, PromptOptimizer

# 1. Apply CPU optimizations
configure_cpu_optimizations()

# 2. Initialize engine (CPU mode)
engine = HelixEngine(force_cpu=True)
engine.load()

# 3. Optimize prompt
optimizer = PromptOptimizer()
prompt = optimizer.format_chat_prompt("What is AI?")

# 4. Generate
config = GenerationConfig(
    max_tokens=50,
    temperature=0.7,
    speculation_depth=3
)
result = engine.generate(prompt, config)

print(result.generated_text)
print(f"Performance: {result.tokens_per_second:.2f} tok/s")
```

## Prompt Templates

### Chat Format (TinyLlama)

```python
optimizer.format_chat_prompt("Your question here")
# Result: "<|user|>\nYour question here</s>\n<|assistant|>\n"
```

### Instruction Format

```python
optimizer.format_instruction_prompt("Write a haiku")
# Result: "### Instruction:\nWrite a haiku\n\n### Response:\n"
```

### Story Continuation

```python
optimizer.format_story_prompt("Once upon a time")
# Result: "Once upon a time\n\nContinue the story:\n"
```

## Performance Comparison

| Metric  | Before       | After | Improvement       |
| ------- | ------------ | ----- | ----------------- |
| Startup | 11.2s        | 4.6s  | **-58%** ✅       |
| Errors  | OOM warnings | None  | **Eliminated** ✅ |
| TTFT    | 0.1s         | 0.1s  | Same ✅           |

## Troubleshooting

### Still seeing GPU warnings?

Make sure to set `HELIX_FORCE_CPU=1` **before** importing:

```python
import os
os.environ["HELIX_FORCE_CPU"] = "1"  # Do this FIRST

from src.inference import HelixEngine  # Then import
```

### Low throughput?

Try simpler prompts:

```python
# Instead of template:
prompt = "The future of AI is"  # Direct input

# Instead of sampling:
config = GenerationConfig(
    max_tokens=50,
    temperature=0.0,  # Greedy decoding
    speculation_depth=2  # Lower speculation
)
```

## Files Reference

- **Test Script**: `test_cpu_inference.py`
- **Optimizer Module**: `src/cpu_optimizer.py`
- **User Guide**: `CPU_OPTIMIZATION_GUIDE.md`
- **Results**: `CPU_OPTIMIZATION_RESULTS.md`

## Next Steps

1. ✅ Run test: `python test_cpu_inference.py`
2. ✅ Verify results: Check for "4.6s load time"
3. ✅ Update demo script: Add CPU optimization to talking points
4. 📹 Record demo: Show before/after comparison
5. 🚀 Push to GitHub: Commit all changes
6. 📝 Submit: Include CPU optimization as key feature
