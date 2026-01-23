# Helix: Speculative Decoding Inference Engine

## Project Goal
Build a lightweight LLM inference engine optimized for edge devices (Apple Silicon, consumer GPUs) using **Speculative Decoding** and **PagedAttention** to achieve lower latency and higher throughput.

---

## Pre-Event Tasks (Tonight - Before 9 AM Check-in)

### Phase 1: Project Setup
- [x] Create project directory structure
- [x] Initialize Python environment (venv/conda)
- [x] Set up core dependencies (PyTorch, Transformers, Triton)
- [x] Create basic project scaffold

### Phase 2: Core Architecture
- [x] Verify Model on Hardware (DirectML + gpt2-medium verified)
- [/] Implement basic autoregressive generation (baseline)
- [ ] Implement KV-Cache manager
- [ ] Add PagedAttention memory allocator
- [ ] Implement Speculative Decoding loop

### Phase 3: API Layer
- [ ] Create FastAPI server
- [ ] Define API contract (OpenAPI spec)
- [ ] Implement `/generate` endpoint
- [ ] Add Swagger documentation

### Phase 4: Benchmarking
- [ ] Create latency benchmarking script
- [ ] Create throughput benchmarking script
- [ ] Document baseline vs optimized metrics

---

## During Hackathon Tasks (Jan 24, 10 AM onwards)

- [ ] Refine speculative decoding draft/verify loop
- [ ] Tune hyperparameters (speculation depth, acceptance threshold)
- [ ] Add batch processing support
- [ ] Create demo "happy path"
- [ ] Record fallback demo video
- [ ] Prepare pitch presentation
- [ ] Submit before 3:30 AM deadline

---

## Technical Stack

| Component | Technology |
|-----------|------------|
| Language | Python 3.11+ |
| ML Framework | PyTorch 2.x |
| Model Loading | Transformers / llama.cpp bindings |
| Quantization | bitsandbytes / GPTQ / AWQ |
| Attention Kernel | Triton / FlashAttention |
| API | FastAPI |
| Docs | Swagger/OpenAPI |

---

## Key Files to Create

```
Helix/
├── .agent/workflows/radiothon-2026.md  ✓
├── src/
│   ├── __init__.py
│   ├── model_loader.py      # Load quantized models
│   ├── kv_cache.py          # KV-Cache with paging
│   ├── speculative.py       # Speculative decoding loop
│   ├── inference.py         # Main inference engine
│   └── api.py               # FastAPI server
├── benchmarks/
│   ├── latency_bench.py
│   └── throughput_bench.py
├── requirements.txt
├── README.md
└── run.py                   # Entry point
```

---

*Last Updated: Jan 23, 2026 @ 01:14 AM*
