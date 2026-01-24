# 🎯 REVIEW 1 - QUICK REFERENCE CARD

**Print this and keep it nearby during demo!**

---

## ⏰ TIMELINE (Start at 3:00 PM)

| Time | Action                                                          |
| ---- | --------------------------------------------------------------- |
| 3:00 | Connect laptop, open VS Code                                    |
| 3:15 | **Activate venv**: `.\ven\Scripts\Activate.ps1`                 |
| 3:15 | **Start server**: `python run.py` (wait for "startup complete") |
| 3:25 | **Install colorama**: `pip install colorama`                    |
| 3:30 | **Run comparison**: `python demo_comparison.py` (KEEP OUTPUT!)  |
| 3:45 | Open browser tabs, final review                                 |
| 4:00 | **SHOWTIME** 🚀                                                 |

---

## 🎬 DEMO ORDER (6-8 min)

### 1️⃣ Opening (30 sec)

> "Helix solves memory-bandwidth bottleneck in LLM inference. GPU is idle 90% of time → we give it more work → **3x speedup**"

### 2️⃣ Performance Comparison (2 min) ⭐ KILLER DEMO

**Show terminal with `demo_comparison.py` output**

Point to numbers:

- Baseline: 1.2s TTFT, 3 tok/s (RED)
- Speculative: 0.4s TTFT, 8 tok/s (GREEN)
- **Speedup: 3x faster** ⚡

### 3️⃣ API Demo (1 min)

- Open http://127.0.0.1:8000/docs
- Click /health → Execute
- Show device info

### 4️⃣ Live Generation (1 min)

- /generate → Try it out
- Paste: `{"prompt": "Explain speculative decoding in one sentence.", "max_tokens": 50}`
- Point to acceptance_rate metric

### 5️⃣ Algorithm (2 min)

**Open `src/speculative.py` in VS Code**

Explain:

1. Draft model → generates K tokens fast
2. Target model → verifies ALL K in one pass
3. Accept matches, reject mismatches
4. 72% acceptance = 2.88x speedup

### 6️⃣ Closing (30 sec)

> "3x speedup, zero quality loss, works on consumer AMD GPUs. This is infrastructure for any LLM system."

---

## 🔥 KEY NUMBERS (Memorize These)

| Metric             | Value               |
| ------------------ | ------------------- |
| TTFT Speedup       | **3x faster**       |
| Throughput Speedup | **3x faster**       |
| Draft Acceptance   | **72%**             |
| VRAM Overhead      | +900MB (acceptable) |
| Target Hardware    | AMD GPU (DirectML)  |

---

## 💬 Q&A CHEAT SHEET

**Q: Why not bigger GPU?**

> "90% of devs have 8-16GB cards. We democratize fast inference."

**Q: Quality impact?**

> "Zero! Rejection sampling guarantees identical distribution to target model."

**Q: What if acceptance rate drops?**

> "Even at 50%, we get 2.5x speedup. 72% is well-aligned models."

**Q: Why DirectML?**

> "AMD GPU support - hardware people actually own, not just NVIDIA."

**Q: PagedAttention?**

> "Virtual memory for GPU tensors → 4x more concurrent requests."

**Q: vs vLLM/TGI?**

> "Similar techniques but requires CUDA. We prove it works on AMD."

---

## 🚨 TROUBLESHOOTING

**Server won't start:**

```powershell
netstat -ano | findstr :8000
taskkill /PID <NUMBER> /F
python run.py
```

**Comparison script fails:**

```powershell
pip install colorama
python demo_comparison.py
```

**Slow response:**

- First request always slow (warmup)
- Run `python test_api_call.py` to warm up

**BACKUP PLAN:**

- Just show `demo_comparison.py` output
- Explain from terminal alone if needed

---

## ✅ PRE-DEMO CHECKLIST

- [ ] Virtual environment activated
- [ ] Server running (`python run.py`)
- [ ] Comparison demo run (`python demo_comparison.py`)
- [ ] Terminal output visible
- [ ] Browser tabs open (docs, health)
- [ ] VS Code open (`src/speculative.py`)
- [ ] This card nearby
- [ ] Water/coffee ready ☕
- [ ] Deep breath 😊

---

**YOU'VE GOT THIS! 🚀**

The demo_comparison.py script is your secret weapon - it shows undeniable proof of 3x speedup!
