# 🆘 Helix: Offline Survival Guide

> **READ THIS if the AI Agent disconnects or you hit a quota limit.**
> This file contains everything you need to win the Radiothon.

---

## 🚀 1. Start the Server (The Product)
This is your main demo. It runs the **Adaptive Speculative Decoding** engine.

```powershell
cd C:\0001_Project\Helix
.\venv\Scripts\activate
python run.py
```
- **Verify**: Open [http://localhost:8000/docs](http://localhost:8000/docs)
- **Action**: Use `POST /generate` to show text appearing.

---

## 📊 2. Run the Benchmark (The Proof)
This proves you are faster than baseline.

```powershell
python benchmarks\latency_bench.py
```
- **What to show judges**: The "Latency Speedup" number (e.g., "1.8x").
- **If it crashes**: Ensure you have activated `venv`.

---

## 🎨 3. The Visual Pitch (The System Design)
Open this file in your browser to explain **Adaptive K**:
`C:\Users\singh\.gemini\antigravity\brain\fe891bfb-6084-47f5-b731-72fd45e52efe\adaptive_viz.html`

**Talking Point**: 
"We don't just guess blindly. We dynamically adjust our speculation depth based on the Draft Model's confidence, maximizing throughput for every specific prompt."

---

## 🏆 4. The "Senior Engineer" Pitch Checklist

| If Judge Asks... | You Answer... |
| :--- | :--- |
| **"Why is this fast?"** | "We trade idle compute for memory bandwidth. It's Speculative Decoding." |
| **"Why not just use Cloud?"** | "Disaggregated serving on Edge devices saves cost and privacy." |
| **"What about memory?"** | "We use PagedAttention to eliminate fragmentation." |
| **"How do you handle drift?"** | "Our Adaptive Controller reduces speculation depth if rejection rate spikes." |

---

## 🛠️ Troubleshooting (Panic Button)

**Issue**: `RuntimeError: version_counter...`
**Fix**: You are likely running an old version of `speculative.py`.
**Manual Fix**: Open `src/speculative.py` and ensure the function `speculative_decode_step` has the decorator `@torch.inference_mode()` (NOT `@torch.no_grad()`).

**Issue**: `OOM` (Out of Memory)
**Fix**: 
1. Open `src/inference.py`
2. Change class `AdaptiveSpeculativeDecoder(..., max_depth=8)` to `max_depth=4`.
3. Restart server.

---

**GOOD LUCK! You have a working, senior-grade system. Go ship it.** 🚀
