# Optimization Mode Guide

## Overview

Helix supports two optimization modes with different trade-offs:

| Mode        | Throughput | Quality | Use Case                  |
| ----------- | ---------- | ------- | ------------------------- |
| **FAST**    | ~1.4 tok/s | Basic   | Benchmarks, simple Q&A    |
| **QUALITY** | ~0.7 tok/s | High    | Demos, structured outputs |

## Mode Comparison

### FAST Mode (Simple Prompts)

**Performance**: 1.4-1.5 tokens/sec

**Configuration**:

```python
# Simple prompt (no template)
prompt = "What is AI?"

# Greedy decoding config
config = GenerationConfig(
    max_tokens=50,
    temperature=0.0,  # Greedy (deterministic)
    speculation_depth=2  # Lower speculation
)

result = engine.generate(prompt, config)
```

**Output Example**:

```
Input: "The future of AI is"
Output: "the end of the world. No, I'm kidding. The future..."
```

**Pros**:

- ✅ 2x faster throughput
- ✅ Simpler implementation
- ✅ Good for benchmarking

**Cons**:

- ❌ Generic outputs
- ❌ Lacks structure
- ❌ May be incomplete

**When to Use**:

- Performance benchmarks
- Quick testing
- Simple Q&A tasks
- When speed > quality

---

### QUALITY Mode (Optimized Prompts)

**Performance**: 0.7-0.8 tokens/sec

**Configuration**:

```python
from src.cpu_optimizer import PromptOptimizer

optimizer = PromptOptimizer()

# Use chat template
prompt = optimizer.format_chat_prompt("What is AI?")

# Sampling config
config = GenerationConfig(
    max_tokens=50,
    temperature=0.7,  # Sampling (creative)
    speculation_depth=3  # Standard speculation
)

result = engine.generate(prompt, config)
```

**Output Example**:

```
Input: optimizer.format_chat_prompt("What is speculative decoding?")
Output: "rating multiple hypotheses using different input data and
selecting the best one, speculative decoding can help LLMs achieve
higher accuracy."
```

**Pros**:

- ✅ Better coherence
- ✅ Structured responses
- ✅ Follows chat format
- ✅ More natural outputs

**Cons**:

- ❌ 50% slower throughput
- ❌ Longer prompts (template overhead)

**When to Use**:

- Demo videos
- Structured conversations
- Technical explanations
- When quality > speed

---

## Implementation Guide

### Where to Add the Code

#### Option 1: Create a Demo Script (Recommended)

**File**: `demo_cpu_optimized.py` ✅ (Already created)

```bash
# Run the demo
python demo_cpu_optimized.py
```

This shows both modes side-by-side for comparison.

#### Option 2: Modify Existing Test Script

**File**: `test_cpu_inference.py`

**Current**: Uses QUALITY mode (PromptOptimizer templates)

**To Switch to FAST Mode**:

```python
# Line 60-66: Remove template formatting
# OLD (Quality):
prompt = optimizer.format_chat_prompt("Your question")

# NEW (Fast):
prompt = "Your question"  # Direct input

# Line 49-56: Change config
# OLD (Quality):
gen_config = GenerationConfig(
    max_tokens=50,
    temperature=0.7,
    speculation_depth=3,
)

# NEW (Fast):
gen_config = GenerationConfig(
    max_tokens=50,
    temperature=0.0,  # Greedy
    speculation_depth=2,  # Lower
)
```

#### Option 3: In Your Own Script

Add the example code to any new Python file:

```python
# my_inference.py
import os
os.environ["HELIX_FORCE_CPU"] = "1"

from src.inference import HelixEngine, GenerationConfig
from src.cpu_optimizer import configure_cpu_optimizations, PromptOptimizer

# Choose your mode:

# FAST MODE:
configure_cpu_optimizations()
engine = HelixEngine(force_cpu=True)
engine.load()
prompt = "The future of AI is"
config = GenerationConfig(max_tokens=50, temperature=0.0, speculation_depth=2)
result = engine.generate(prompt, config)

# QUALITY MODE:
configure_cpu_optimizations()
engine = HelixEngine(force_cpu=True)
engine.load()
optimizer = PromptOptimizer()
prompt = optimizer.format_chat_prompt("What is speculative decoding?")
config = GenerationConfig(max_tokens=50, temperature=0.7, speculation_depth=3)
result = engine.generate(prompt, config)
```

---

## Configuration Reference

### GenerationConfig Parameters

| Parameter           | FAST Mode | QUALITY Mode | Description                 |
| ------------------- | --------- | ------------ | --------------------------- |
| `max_tokens`        | 50        | 50           | Same for both               |
| `temperature`       | 0.0       | 0.7          | Greedy vs. Sampling         |
| `speculation_depth` | 2         | 3            | Lower = less wasted compute |
| `use_speculative`   | True      | True         | Always enabled              |

### PromptOptimizer Templates

Available in QUALITY mode only:

```python
optimizer = PromptOptimizer()

# 1. Chat format (best for TinyLlama-Chat)
optimizer.format_chat_prompt("Your question")
# → "<|user|>\nYour question</s>\n<|assistant|>\n"

# 2. Instruction format
optimizer.format_instruction_prompt("Write a haiku")
# → "### Instruction:\nWrite a haiku\n\n### Response:\n"

# 3. Story continuation
optimizer.format_story_prompt("Once upon a time")
# → "Once upon a time\n\nContinue the story:\n"

# 4. Raw mode (no template)
optimizer.optimize_prompt("Your text", mode="raw")
# → "Your text"
```

---

## Recommendation by Use Case

### For Hackathon Demo: **QUALITY Mode**

- Shows engineering sophistication
- Better outputs for video
- Demonstrates prompt engineering
- Trade-off is well-documented

### For Performance Benchmarks: **FAST Mode**

- Maximize throughput numbers
- Compare with baselines
- Stress test system
- Clearer performance metrics

### For Production: **Hybrid Approach**

```python
def generate_smart(prompt, use_quality=False):
    if use_quality:
        optimizer = PromptOptimizer()
        prompt = optimizer.format_chat_prompt(prompt)
        config = GenerationConfig(temperature=0.7, speculation_depth=3)
    else:
        config = GenerationConfig(temperature=0.0, speculation_depth=2)

    return engine.generate(prompt, config)
```

---

## Testing Both Modes

### Quick Test (Fast Mode)

```bash
# Use prove_system_works.py (already uses simple prompts)
python prove_system_works.py
# Expected: ~1.45 tok/s
```

### Quick Test (Quality Mode)

```bash
# Use test_cpu_inference.py (already uses PromptOptimizer)
python test_cpu_inference.py
# Expected: ~0.73 tok/s
```

### Side-by-Side Comparison

```bash
# Run the demo script
python demo_cpu_optimized.py
# Shows both modes in one run
```

---

## Summary

**The code you asked about should go in**:

1. ✅ `demo_cpu_optimized.py` (already created) - Shows both modes
2. Your own inference scripts (when you need CPU mode)
3. NOT needed in existing test files (already configured)

**For hackathon submission**:

- **Use QUALITY mode** in demo video
- **Mention FAST mode** as available option
- **Document trade-offs** (you already have this)

Run `python demo_cpu_optimized.py` to see both modes in action!
