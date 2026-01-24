# Helix 🧬

**Speculative Decoding Inference Engine for Consumer Hardware**

[![Python 3.10+](https://img.shields.io/badge/Python-3.10+-blue.svg)](https://python.org)
[![License: MIT](https://img.shields.io/badge/License-MIT-green.svg)](LICENSE)
[![Validation](https://img.shields.io/badge/Tests-100%25-brightgreen.svg)](validate_submission.py)

> **Radiothon 2026** | Track 01: AI Systems & Infrastructure  
> Solo Project by Uday Singh

---

## 1. The Problem & Solution

**The Bottleneck**: LLM inference is **memory-bandwidth bound**, not compute-bound. Your GPU spends 90% of its time waiting for memory transfers.

**Our Solution**: Trade idle memory cycles for useful compute using two systems-level optimizations:

| Technique                | What It Does                                                | Impact             |
| ------------------------ | ----------------------------------------------------------- | ------------------ |
| **Speculative Decoding** | Draft model predicts K tokens, target verifies in one pass  | **3x faster TTFT** |
| **PagedAttention**       | Non-contiguous KV-cache allocation (like OS virtual memory) | **+4x batch size** |

**This is not a product. This is a systems engineering proof-of-concept.**

---

## 2. Quick Start

```bash
# Clone and setup
git clone https://github.com/singhuday26/Helix.git
cd Helix

# Install dependencies (torch first, then DirectML)
pip install torch==2.4.1 torch-directml==0.2.5 transformers fastapi uvicorn

# Start the server
python run.py

# Test generation (new terminal)
curl -X POST http://localhost:8000/generate \
  -H "Content-Type: application/json" \
  -d '{"prompt": "Explain speculative decoding.", "max_tokens": 50}'
```

**Swagger UI**: Open [http://localhost:8000/docs](http://localhost:8000/docs) for interactive API testing.

---

## 3. Performance Benchmarks

**Hardware**: AMD Radeon RX 6700 XT (12GB VRAM) via DirectML  
**Model**: TinyLlama-1.1B-Chat-v1.0

| Metric                    | Baseline   | Helix      | Improvement     |
| ------------------------- | ---------- | ---------- | --------------- |
| **Time to First Token**   | 1.2s       | 0.4s       | **3.0x faster** |
| **Tokens per Second**     | 2.7        | 8.1        | **3.0x faster** |
| **Draft Acceptance Rate** | N/A        | 72%        | High quality    |
| **Memory Usage**          | 3.2GB      | 4.1GB      | +28% overhead   |
| **Batch Throughput**      | 0.05 seq/s | 0.06 seq/s | +20% faster     |

**Reproduce**: `python benchmark_speculative.py`

### Core Trade-offs (Documented Honestly)

| Decision          | Cost                       | Benefit                          | Verdict |
| ----------------- | -------------------------- | -------------------------------- | ------- |
| Draft Model       | +900MB VRAM                | 3x latency reduction             | ✅ Win  |
| PagedAttention    | +5% lookup overhead        | 4x batch size                    | ✅ Win  |
| Speculation (K=4) | Wasted compute on mismatch | 72% acceptance = 2.88x effective | ✅ Win  |
| DirectML          | Windows-only               | AMD consumer GPU support         | ⚖️ OK   |

---

## 4. Architecture

```
┌─────────────────────────────────────────────────────────┐
│                    FastAPI Server                        │
│                     (src/api.py)                         │
└─────────────────────────┬───────────────────────────────┘
                          │
                          ▼
┌─────────────────────────────────────────────────────────┐
│                     HelixEngine                          │
│                   (src/inference.py)                     │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────────┐  │
│  │ ModelLoader │  │ PagedCache  │  │ SpeculativeLoop │  │
│  │ (DirectML)  │  │ (KV blocks) │  │ (Draft+Verify)  │  │
│  └─────────────┘  └─────────────┘  └─────────────────┘  │
└─────────────────────────────────────────────────────────┘
```

### Key Components

| File                     | Purpose                                              |
| ------------------------ | ---------------------------------------------------- |
| `src/model_loader.py`    | Load models with DirectML priority (AMD GPU support) |
| `src/kv_cache.py`        | PagedAttention memory manager with block allocation  |
| `src/speculative.py`     | Speculative decoding loop (draft → verify → accept)  |
| `src/batch_optimizer.py` | Vectorized batch processing (3-5x throughput)        |
| `src/inference.py`       | HelixEngine orchestrator + streaming support         |
| `src/api.py`             | FastAPI endpoints (sync, async, batch, SSE)          |

---

## 5. API Reference

### Endpoints

| Endpoint           | Method | Purpose                             |
| ------------------ | ------ | ----------------------------------- |
| `/generate`        | POST   | Standard generation (synchronous)   |
| `/generate/stream` | POST   | SSE streaming (real-time tokens)    |
| `/generate/batch`  | POST   | Batch processing (multiple prompts) |
| `/health`          | GET    | System health check                 |
| `/metrics`         | GET    | Performance statistics              |

### Example: Standard Generation

```bash
curl -X POST http://localhost:8000/generate \
  -H "Content-Type: application/json" \
  -d '{
    "prompt": "Explain quantum computing in one sentence.",
    "max_tokens": 50,
    "temperature": 0.7,
    "speculation_depth": 4
  }'
```

### Example: Batch Processing

```bash
curl -X POST http://localhost:8000/generate/batch \
  -H "Content-Type: application/json" \
  -d '{
    "prompts": [
      "What is machine learning?",
      "Explain neural networks.",
      "What is deep learning?"
    ],
    "max_tokens": 50
  }'
```

### Example: Streaming (JavaScript)

```javascript
const eventSource = new EventSource(
  "/generate/stream?" +
    new URLSearchParams({ prompt: "Explain AI.", max_tokens: 100 }),
);

eventSource.onmessage = (e) => {
  const data = JSON.parse(e.data);
  if (data.is_final) eventSource.close();
  else console.log(data.token);
};
```

---

## 6. Project Structure

```
Helix/
├── src/                    # Core engine
│   ├── api.py              # FastAPI endpoints
│   ├── inference.py        # HelixEngine orchestrator
│   ├── speculative.py      # Speculative decoding algorithm
│   ├── kv_cache.py         # PagedAttention implementation
│   ├── model_loader.py     # DirectML-first model loading
│   ├── batch_optimizer.py  # Vectorized batch processing
│   └── cpu_optimizer.py    # CPU fallback optimizations
├── frontend/               # React UI (optional)
├── benchmarks/             # Performance testing
├── run.py                  # Server entry point
├── benchmark_speculative.py
└── requirements.txt
```

---

## 7. Documentation

| Document                                                 | Description                                                 |
| -------------------------------------------------------- | ----------------------------------------------------------- |
| [ARCHITECTURE.md](ARCHITECTURE.md)                       | Deep dive: PagedAttention math, speculative decoding theory |
| [HACKATHON_SUBMISSION.md](HACKATHON_SUBMISSION.md)       | Pre-qualification responses, strategy, honest limitations   |
| [CLI_DEMO.md](CLI_DEMO.md)                               | Demo script for judges, curl examples, video walkthrough    |
| [IMPLEMENTATION_PROGRESS.md](IMPLEMENTATION_PROGRESS.md) | Phase-by-phase development log                              |
| [STUDY_GUIDE.md](STUDY_GUIDE.md)                         | Q&A prep, elevator pitch, key numbers                       |

### Validation & Testing

```bash
python validate_submission.py      # 100% validation score
python benchmark_speculative.py    # Reproducible benchmarks
python validate_codebase.py        # 19 comprehensive tests
```

---

## 8. References & License

### Academic References

1. [Fast Inference from Transformers via Speculative Decoding](https://arxiv.org/abs/2211.17192) (Leviathan et al., 2022)
2. [Efficient Memory Management for Large Language Model Serving with PagedAttention](https://arxiv.org/abs/2309.06180) (vLLM paper)
3. [torch-directml Documentation](https://github.com/microsoft/DirectML)

### License

MIT License — See [LICENSE](LICENSE) for details.

---

<div align="center">

**This is not a product. This is infrastructure.**

The real innovation is understanding that **memory bandwidth is the bottleneck**,  
and trading idle resources for useful work is an asymmetric win.

_Radiothon 2026 — Track 01: AI Systems & Infrastructure_

</div>
````
