# Helix 🧬

**Speculative Decoding Inference Engine for Edge Devices**

> Built for Radiothon 2026 | Track 01: AI Systems & Infrastructure

---

## What is Helix?

Helix is a lightweight LLM inference engine that demonstrates **Senior Engineer** architectural thinking through:

1. **Speculative Decoding** — Uses a small draft model to predict tokens speculatively, then verifies with target model in a single forward pass
2. **PagedAttention** — Non-contiguous KV-cache allocation to reduce memory fragmentation and increase batch throughput

## Key Trade-offs

| Decision | Choice | Rationale |
|----------|--------|-----------|
| Draft Model | TinyLlama-1.1B | Fastest speculation, fits in L2 cache |
| Memory Strategy | Paged (vs Contiguous) | +4x batch size, +~5% latency overhead |
| Consistency | Eventual (async verify) | Prioritize TTFT over strict ordering |

---

## Quick Start

```bash
# 1. Create environment
python -m venv venv
venv\Scripts\activate  # Windows
# source venv/bin/activate  # Linux/Mac

# 2. Install dependencies
pip install -r requirements.txt

# 3. Start the server
python run.py

# 4. Open Swagger docs
# Navigate to http://localhost:8000/docs
```

## API Usage

```bash
# Generate text
curl -X POST http://localhost:8000/generate \
  -H "Content-Type: application/json" \
  -d '{"prompt": "Explain quantum computing in one sentence.", "max_tokens": 50}'
```

## Architecture

```
┌─────────────────────────────────────────────────────────┐
│                      FastAPI Server                      │
│                     (src/api.py)                         │
└─────────────────────┬───────────────────────────────────┘
                      │
                      ▼
┌─────────────────────────────────────────────────────────┐
│                    HelixEngine                           │
│                  (src/inference.py)                      │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────────┐  │
│  │ ModelLoader │  │ PagedCache  │  │ SpeculativeLoop │  │
│  └─────────────┘  └─────────────┘  └─────────────────┘  │
└─────────────────────────────────────────────────────────┘
```

## Project Structure

```
Helix/
├── src/
│   ├── __init__.py
│   ├── model_loader.py    # Load quantized models
│   ├── kv_cache.py        # PagedAttention memory manager
│   ├── speculative.py     # Speculative decoding loop
│   ├── inference.py       # Main HelixEngine class
│   └── api.py             # FastAPI endpoints
├── benchmarks/
│   ├── latency_bench.py
│   └── throughput_bench.py
├── tests/
│   └── ...
├── requirements.txt
├── run.py                 # Entry point
└── README.md
```

## Benchmarks

```bash
# Run latency benchmark
python benchmarks/latency_bench.py

# Run throughput benchmark
python benchmarks/throughput_bench.py
```

---

## License

MIT — Built for Radiothon 2026
