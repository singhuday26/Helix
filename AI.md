# AI Usage Declaration

## Overview

This project used AI assistance (GitHub Copilot) for specific tasks while maintaining human oversight and validation for all core algorithmic decisions.

## AI-Assisted Files

| File                            | AI Contribution                             | Human Validation                                                   |
| ------------------------------- | ------------------------------------------- | ------------------------------------------------------------------ |
| `src/api.py`                    | FastAPI boilerplate, endpoint structure     | ✅ Reviewed, tested all endpoints                                  |
| `src/model_loader.py`           | Error handling patterns, docstrings         | ✅ Core logic (device detection, fallback chain) designed manually |
| `src/inference.py`              | Streaming generator boilerplate             | ✅ Core engine architecture designed manually                      |
| `frontend/src/components/*.jsx` | React component structure, Tailwind classes | ✅ UI/UX decisions made manually                                   |
| `README.md`                     | Markdown formatting, badge syntax           | ✅ All technical content written manually                          |
| `tests/*.py`                    | Test case structure                         | ✅ Test scenarios designed manually                                |

## Core Logic (NO AI Assistance)

The following critical components were designed and implemented **without AI assistance**:

1. **Speculative Decoding Algorithm** (`src/speculative.py`)
   - Rejection sampling implementation
   - Acceptance probability computation
   - Token verification loop
   - Based directly on [Leviathan et al., 2022](https://arxiv.org/abs/2211.17192)

2. **PagedAttention KV Cache** (`src/kv_cache.py`)
   - Block table mapping
   - Physical/virtual memory translation
   - Sequence allocation/deallocation
   - Based on [vLLM paper](https://arxiv.org/abs/2309.06180)

3. **Device Fallback Chain** (`src/model_loader.py`)
   - DirectML → CUDA → MPS → CPU priority
   - OOM recovery mechanisms
   - Hybrid deployment strategy (draft on GPU, target on CPU)

4. **Benchmark Design** (`benchmark_speculative.py`)
   - TTFT measurement methodology
   - Acceptance rate calculation
   - Fair baseline comparison

## AI Usage Philosophy

- **Boilerplate**: AI used for repetitive patterns (FastAPI routes, React components)
- **Core Logic**: Human-designed based on research papers
- **Validation**: All AI-generated code reviewed and tested
- **Documentation**: Technical explanations written manually to ensure accuracy

## Guardrails Applied

1. All AI suggestions reviewed before acceptance
2. Core algorithms cross-referenced with source papers
3. Performance claims validated with reproducible benchmarks
4. Error handling tested with edge cases

---

_Transparency is valued. This declaration is honest and complete._
