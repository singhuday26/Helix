# Helix AI Coding Instructions

You are an expert AI assistant working on **Helix**, a speculative decoding inference engine optimized for edge devices (specifically AMD GPUs via DirectML).

## 🏗 High-Level Architecture

- **Core Pattern**: Speculative Decoding (Draft Model + Target Model).
- **Key Components**:
  - `src/speculative.py`: The heart of the algorithmic logic (generate, verify, rollback).
  - `src/kv_cache.py`: **PagedAttention** implementation. Infrastructure is wired but not actively used in forward passes yet (see Phase 4).
  - `src/model_loader.py`: Handles model instantiation. **CRITICAL**: Prioritizes `torch-directml` ("privateuseone") over CUDA/CPU.
  - `src/api.py`: FastAPI entry point.
- **Data Flow**: Request -> `api.py` -> `inference.py` (Engine) -> `speculative.py` (Decides steps) -> `kv_cache.py` (Manages state).

## 🚀 Development Workflows

### 1. Environment & Setup

- **DirectML First**: This project targets Windows AMD GPUs.
- **Dependencies**: Always respect the install order in `requirements.txt` (torch first, then torch-directml).
- Virtual environment is in `ven/` directory (not `venv/`).

### 2. Running & Testing

- **Start Server**: `python run.py --reload`
- **Run Benchmarks**: `python benchmark_speculative.py` (Use this to validate performance improvements).
- **Run Tests**: Use `pytest`. Key tests are `test_directml.py` (hardware check) and `test_model_load.py`.
- **Hardware Check**: Call `src.model_loader.get_device()` to confirm the active backend.
- **Validate Code Changes**: Run `python validate_code_changes.py` for syntax checks.

### 3. Debugging

- All modules use a standard logging pattern: `logger = logging.getLogger(__name__)`.
- Check `http://localhost:8000/docs` for API structure verification.
- TTFT measurement is now **real** (not approximated) - see `SpeculativeOutput.first_token_time`.

## 📝 Code Conventions & Patterns

### 1. "Trade-off" Documentation

- **Explicit Decisions**: When making architectural choices, document the trade-offs in comments or docstrings (e.g., "Latency vs. Throughput").
- Example (from `src/speculative.py`):
  ```python
  # Trade-off: Higher K = more speedup potential, but more wasted compute on mismatch
  DEFAULT_SPECULATION_DEPTH = 4
  ```

### 2. Paged Attention (Phase 4B COMPLETE!)

- **FULLY INTEGRATED**: `PagedKVCache` is now actively used in forward passes via `CachedModelWrapper`.
- **HuggingFace Compatibility**: `store_hf_cache()` and `get_hf_cache()` handle DynamicCache format conversion.
- **Memory Savings**: ~87.5% reduction compared to traditional KV cache.
- **Cached Inference**: Model only processes new tokens, using cached KV for previous positions.
- **Logits Indexing**: When using cache, logits shape is (batch, num_new_tokens, vocab) - see `speculative_decode_step()`.
- Use `BlockTable` mapping in `src/kv_cache.py` for logical-to-physical address translation.

### 3. Typing & Data Classes

- Use `dataclasses` for config and result objects (e.g., `GenerationConfig`, `GenerationResult`, `SpeculativeOutput`).
- Strictly type helper functions using `typing` (`Optional`, `List`, `Tuple`, `Dict`).

### 4. GPU Safety

- Always use `src.model_loader.get_device()` instead of hardcoding `.to("cuda")`.
- Use `src.inference.cleanup_memory()` for OOM recovery hooks.

### 5. Stop Token Handling

- **CRITICAL**: Always check for stop tokens **before** appending to output (see `AdaptiveSpeculativeDecoder.generate()`).
- Pattern: Extract tokens, check for stop, slice up to (not including) stop, then break.

## ⚠️ Critical Rules

1. **Never** remove the `torch-directml` import logic in `src/model_loader.py`.
2. **Speculation Logic**: Changes to verification logic in `src/speculative.py` must preserve alignment with the paper "Fast Inference from Transformers via Speculative Decoding".
3. **Async Generation**: The engine prioritizes Time To First Token (TTFT). Ensure async logic does not block the main thread.
4. **KV Cache Lifecycle**: When using `PagedKVCache`, always allocate sequence ID before generation and free in `finally` block.

## 📊 Implementation Progress

**Completed Phases**:

- ✅ Phase 1: Critical bug fixes (double loading, duplicate logger, stop token leak)
- ✅ Phase 2: PagedAttention integration framework
- ✅ Phase 3: Real TTFT measurement (replaces approximations)
- ✅ Phase 4: Batch processing infrastructure (3-5x throughput potential)
- ✅ **Phase 4B**: PagedAttention FULL end-to-end integration (~87.5% memory savings)

**Next Phases** (See `IMPLEMENTATION_PROGRESS.md`):

- Phase 4B: Parallel batch processing optimization
- Phase 5: Streaming Support (SSE endpoint)
- Phase 6: Comprehensive Testing
- Phase 7: Performance Optimization

## 🔗 Key Files for Reference

- `IMPLEMENTATION_PROGRESS.md`: Detailed implementation status and next steps
- `PHASE4_BATCH_PROCESSING.md`: Batch processing documentation
- `task.md`: Original project requirements
- `validate_code_changes.py`: Quick syntax validation tool
- `test_batch_processing.py`: Batch processing test suite
