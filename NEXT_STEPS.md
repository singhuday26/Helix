# Helix - Quick Start for Next Developer

## What Was Just Completed

**Phases 1-3 of the implementation plan** (see `IMPLEMENTATION_PROGRESS.md` for details):

- ✅ Fixed critical bugs (double loading, duplicate logger, stop token leak)
- ✅ Integrated PagedAttention infrastructure (wired but not active yet)
- ✅ Implemented real TTFT measurement (no more fake approximations)

**All code validated with zero syntax errors.**

---

## What's Next: Phase 4 - Batch Processing

### Current Limitation

```python
# src/speculative.py line 110
assert batch_size == 1, "Speculative decoding currently supports batch_size=1"
```

### Goal

Enable processing multiple requests in parallel to maximize GPU utilization.

### Implementation Steps

1. **Extend `SequenceBlockTable` for multi-sequence support**
   - File: `src/kv_cache.py`
   - Add sequence ID to block table mapping
   - Track per-sequence block allocations

2. **Vectorize draft generation**
   - File: `src/speculative.py` lines 115-125
   - Change from single-sequence loop to batched forward pass
   - Handle variable-length sequences with padding

3. **Implement batched verification**
   - File: `src/speculative.py` lines 135-175
   - Process multiple sequences in `_verify_with_target()`
   - Handle per-sequence acceptance rates

4. **Add request batching to API**
   - File: `src/api.py`
   - Create request queue
   - Group incoming requests with batching timeout (e.g., 50ms)

### Key Files to Modify

- `src/speculative.py`: Remove assertion, add batch logic
- `src/kv_cache.py`: Multi-sequence support
- `src/api.py`: Request queue + batching
- `src/inference.py`: Batch generation method

### Testing

```bash
# Benchmark throughput improvement
python benchmarks/throughput_bench.py
```

---

## Alternative: Phase 5 - Streaming Support

If batch processing is not a priority, implement streaming first:

### Goal

Enable real-time token delivery via Server-Sent Events (SSE).

### Implementation Steps

1. **Add `/generate/stream` endpoint**
   - File: `src/api.py`
   - Use `fastapi.responses.StreamingResponse`
   - Media type: `text/event-stream`

2. **Create async generator in engine**
   - File: `src/inference.py`
   - Add `generate_stream()` method
   - Yield tokens as they're accepted

3. **Modify speculative loop**
   - File: `src/speculative.py` line 260-280
   - Add callback/async yield after each accepted batch

### Testing

```bash
curl -N http://localhost:8000/generate/stream \
  -H "Content-Type: application/json" \
  -d '{"prompt": "Hello", "max_tokens": 50}'
```

---

## Current Code Structure

### Key Entry Points

1. **Server Start**: `python run.py`
2. **API Endpoint**: `src/api.py` → `POST /generate`
3. **Inference Engine**: `src/inference.py` → `HelixEngine.generate()`
4. **Speculative Logic**: `src/speculative.py` → `speculative_decode_step()`
5. **KV Cache**: `src/kv_cache.py` → `PagedKVCache` (wired but not active)

### Data Flow

```
HTTP Request
  ↓
src/api.py::generate_endpoint()
  ↓
src/inference.py::HelixEngine.generate()
  ↓
src/speculative.py::AdaptiveSpeculativeDecoder.generate()
  ↓
src/speculative.py::speculative_decode_step()
  ↓ (Draft Phase)
draft_model() → K tokens
  ↓ (Verify Phase)
target_model() → Accept/Reject
  ↓ (Return)
HTTP Response
```

### Critical Functions

1. **`speculative_decode_step()`** (Line 76)
   - Core algorithm: Draft → Verify → Accept/Reject
   - Returns `SpeculativeOutput` with accepted tokens + timing

2. **`AdaptiveSpeculativeDecoder.generate()`** (Line 230)
   - Adjusts speculation depth dynamically
   - Manages KV cache lifecycle (allocate → use → free)

3. **`HelixEngine.generate()`** (Line 170)
   - High-level API
   - Handles OOM recovery
   - Returns `GenerationResult` with metrics

---

## Running Tests

### Quick Validation

```bash
python validate_code_changes.py  # Syntax check (no torch required)
```

### Full Tests (requires dependencies)

```bash
# Install if needed
pip install -r requirements.txt

# Hardware check
python test_directml.py

# Model loading
python test_model_load.py

# Performance benchmark
python benchmark_speculative.py
```

### Start Server

```bash
python run.py --reload
```

Test API at: http://localhost:8000/docs

---

## Common Pitfalls to Avoid

1. **Don't hardcode `.to("cuda")`** → Use `src.model_loader.get_device()`
2. **Stop token handling** → Check BEFORE appending (see line 403 in speculative.py)
3. **KV cache cleanup** → Always use try/finally when allocating sequences
4. **TTFT measurement** → It's now real, propagate `first_token_time` through stats

---

## Trade-offs to Consider

### Batch Processing (Phase 4)

- **Pro**: 3-5x throughput improvement for concurrent requests
- **Con**: Adds complexity in handling variable-length sequences
- **Verdict**: High value for production deployment

### Streaming (Phase 5)

- **Pro**: Better UX for chat/interactive applications
- **Con**: Slightly higher CPU overhead per request
- **Verdict**: Essential for user-facing applications

### Active KV Cache Integration (Future)

- **Pro**: Reduced VRAM, ~4x batch size increase
- **Con**: Requires custom attention kernels or HF model hooks
- **Verdict**: Medium priority, infrastructure is ready

---

## Useful Commands

```bash
# Activate environment (Windows)
.\ven\Scripts\activate

# Run with auto-reload
python run.py --reload

# Check GPU status
python -c "from src.model_loader import get_device; print(get_device())"

# Benchmark latency
python benchmarks/latency_bench.py

# Benchmark throughput
python benchmarks/throughput_bench.py

# Format code
black src/

# Type check
mypy src/ --ignore-missing-imports
```

---

## Questions or Blocked?

1. **Check the plan**: See `IMPLEMENTATION_PROGRESS.md` for detailed roadmap
2. **Review AI guidelines**: `.github/copilot-instructions.md` has coding patterns
3. **Look at examples**: `test_model_load.py` shows usage patterns
4. **Trace the flow**: Add `logger.info()` statements to understand execution

---

## Success Criteria

**Phase 4 Complete When**:

- [ ] Batch size > 1 works without assertion failure
- [ ] Throughput benchmark shows >2x improvement for N=4 concurrent requests
- [ ] No memory leaks under sustained load

**Phase 5 Complete When**:

- [ ] `/generate/stream` endpoint returns SSE stream
- [ ] Tokens appear incrementally (not all at once)
- [ ] Swagger docs reflect new endpoint

---

Good luck! 🚀
