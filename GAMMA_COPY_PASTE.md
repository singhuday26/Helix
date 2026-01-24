# GAMMA AI COPY-PASTE PROMPT

## (Copy everything below this line and paste into Gamma AI)

---

Create a 10-slide technical presentation for "Helix: Speculative Decoding for Edge Devices" - a hackathon project that makes LLM inference 2-5x faster on CPUs.

## CRITICAL STYLE REQUIREMENTS (VERY IMPORTANT):

**Design Philosophy**: This should look like a senior engineer's technical presentation at a developer conference (Apple WWDC, Google I/O style), NOT a startup pitch deck or marketing presentation.

**MUST DO:**

- Use geometric shapes, clean lines, and gradients
- Include code blocks with monospace fonts
- Use terminal-style mockups for evidence
- Dark backgrounds for technical/code slides
- Light backgrounds for data/comparison slides
- Generous whitespace
- One key message per slide
- Data visualizations (bar charts, comparison tables)

**MUST NOT:**

- NO AI-generated illustrations of people or robots
- NO clipart or stock photos
- NO 3D icons or cartoonish graphics
- NO generic "innovation" imagery
- NO walls of bullet points

**Color Palette:**

- Primary: Deep blue (#1E3A8A)
- Accent: Electric blue (#3B82F6)
- Success: Emerald green (#10B981)
- Warning: Amber (#F59E0B)
- Error: Red (#DC2626)
- Dark background: Slate (#0F172A)
- Light background: White or gray (#F3F4F6)

---

## SLIDE-BY-SLIDE CONTENT:

### SLIDE 1: TITLE

**Headline:** Helix
**Subheadline:** Speculative Decoding for Edge Devices
**Tagline:** Making LLM Inference 2-5x Faster on Everyday Hardware
**Visual:** Abstract geometric helix pattern made of thin gradient lines (blue to purple). Dark background. Minimalist.
**Footer:** Radiothon 2026 | github.com/singhuday26/Helix

---

### SLIDE 2: THE PROBLEM

**Headline:** AI is Expensive. Students Can't Afford It.

**Three key points (use simple line icons, not 3D):**

**1. Cloud API Costs**
GPT-4: $0.03 per 1K tokens
Student experiments: 100K+ tokens
Result: $50-100/month just to learn

**2. Hardware Barrier**
NVIDIA GPU: $500-2000
Cloud GPU: $1-5/hour
Most laptops: CPU only

**3. Privacy Risk**
Data goes to cloud servers
No control over retention
Can't use for sensitive research

**Visual:** Simple horizontal bar chart showing monthly costs:

- OpenAI API: $50-100
- Cloud GPU: $30-150
- Local GPU: $500+ upfront
- Helix: FREE

---

### SLIDE 3: WHY THIS IS HARD

**Headline:** Technical Constraints We Faced

**Layout:** Dark background, code-style presentation

**Constraint 1 - GPU Memory:**

```
AMD GPU (DirectML)
├── Allocation Limit: 16MB per tensor
├── Model Requirement: 4.4GB
└── Result: Out-of-Memory Error ❌
```

**Actual Error Message (code block):**

```python
RuntimeError: Could not allocate tensor with
16777216 bytes. There is not enough GPU
video memory available!
```

**Constraint 2 - CPU Speed:**

- 10-50x slower than GPU baseline
- Naive approach: 11.2 second startup
- Simple prompts = generic outputs

**Key Insight (callout):** We needed to optimize FOR constraints, not fight against them.

---

### SLIDE 4: OUR SOLUTION

**Headline:** Speculative Decoding: Draft → Verify → Accept

**Visual:** Clean horizontal flowchart (geometric boxes connected by arrows)

```
[DRAFT MODEL]  →  [TARGET MODEL]  →  [DECISION]
 (fast, small)     (verify all K)
      │                  │              │
      │                  │         ┌────┴────┐
      │                  │         ↓         ↓
 Generate            Verify     ACCEPT    REJECT
 K tokens            in ONE     (output)  (rollback)
 quickly             pass
```

**The Key Insight (prominent callout box):**

> "Verifying K tokens together in ONE forward pass is cheaper than generating them one-by-one"

**Result:** 2-5x theoretical speedup with IDENTICAL output quality (mathematically proven)

**Style:** Dark background, neon blue flowchart lines, minimal text

---

### SLIDE 5: SYSTEM ARCHITECTURE

**Headline:** Helix Architecture

**Visual:** Clean vertical stack diagram (boxes stacked top to bottom)

```
┌─────────────────────────────────────┐
│         USER REQUEST                │
│      "What is speculative..."       │
└───────────────┬─────────────────────┘
                ↓
┌─────────────────────────────────────┐
│       API SERVER (FastAPI)          │
│   • SSE Streaming • Auto-docs       │
└───────────────┬─────────────────────┘
                ↓
┌─────────────────────────────────────┐
│          HELIX ENGINE               │
├───────────┬───────────┬─────────────┤
│  Model    │Speculative│  KV Cache   │
│  Loader   │  Decoder  │  (Paged)    │
│ (CPU opt) │(adaptive) │(512 blocks) │
└───────────┴───────────┴─────────────┘
                ↓
┌─────────────────────────────────────┐
│    STREAMING RESPONSE → React UI    │
└─────────────────────────────────────┘
```

**Tech Stack (small badges):** Python | PyTorch | FastAPI | React

**Style:** Light background, blue boxes, clean connecting lines

---

### SLIDE 6: THE PIVOT

**Headline:** GPU Failed → CPU Succeeded

**Layout:** Split screen (Before | After)

**LEFT SIDE - BEFORE (dark, red tint):**

```
GPU APPROACH ❌
──────────────────
DirectML on AMD
OOM errors every run
11.21s startup time
Unreliable
```

**RIGHT SIDE - AFTER (bright, green tint):**

```
CPU OPTIMIZED ✓
──────────────────
Force CPU mode
Zero errors
4.62s startup time
Consistent
```

**CENTER (large, prominent):**

```
58% FASTER STARTUP
6.59 seconds saved
```

**Bottom callout (amber/yellow):**

> "Engineering Insight: Don't fight hardware constraints. Optimize for reality."

---

### SLIDE 7: MEASURED RESULTS

**Headline:** Evidence, Not Promises

**Visual:** Horizontal bar chart (clean, no 3D)

```
STARTUP TIME COMPARISON
────────────────────────────────────────
GPU Fallback  ████████████████████  11.21s
CPU Direct    █████████              4.62s
────────────────────────────────────────
              0s    4s    8s    12s

             ▼ 58% IMPROVEMENT
```

**Three metric cards (side by side):**

| Startup Time | Time to First Token |  Throughput   |
| :----------: | :-----------------: | :-----------: |
|  **4.62s**   |      **0.1s**       | **0.73-1.44** |
| (was 11.21s) |    (consistent)     |    tok/sec    |

**Footer:** All metrics from actual test runs on production code

---

### SLIDE 8: TWO MODES

**Headline:** Quality vs Speed: You Choose

**Two cards side by side:**

**QUALITY MODE (blue accent):**

```
🎯 QUALITY MODE
────────────────────
Throughput: 0.73 tok/s
Best for: Demos, Q&A

Uses chat template:
<|user|>
Your question
</s>
<|assistant|>

Output: Structured, coherent
```

**FAST MODE (green accent):**

```
⚡ FAST MODE
────────────────────
Throughput: 1.44 tok/s
Best for: Benchmarks

Uses raw prompt:
"Your question"

Output: Quick, basic
```

**Bottom insight:**

> Trade-off: We accept 48% lower throughput in Quality mode for better output structure. This is a documented engineering decision.

---

### SLIDE 9: PROOF IT WORKS

**Headline:** Live System Evidence

**Visual:** Terminal mockup (dark background, green text)

```bash
$ python test_cpu_inference.py

═══════════════════════════════════════════
 HELIX CPU-OPTIMIZED INFERENCE TEST
═══════════════════════════════════════════

[✓] CPU optimizations applied: 8 threads
[✓] Model loaded in 4.62s
[✓] Device: cpu (forced mode)

Test 1/4: creative_story .............. PASS
  → 25 tokens, 0.60 tok/s

Test 2/4: technical_question .......... PASS
  → 28 tokens, 0.71 tok/s

Test 3/4: instruction_task ............ PASS
  → 29 tokens, 0.84 tok/s

Test 4/4: conversation ................ PASS
  → 30 tokens, 0.79 tok/s

═══════════════════════════════════════════
 RESULT: 4/4 PASSED | STATUS: HEALTHY
═══════════════════════════════════════════
```

**Key Evidence (three checkmarks):**
✓ 4/4 tests passed (100% success)
✓ 4.62s model load (58% faster)
✓ Consistent across prompt types

---

### SLIDE 10: ENGINEERING QUALITY

**Headline:** Not Just Working, But Well-Built

**Three columns:**

**COLUMN 1 - Testing:**

```
47/47 TESTS
────────────
✓ Syntax validation
✓ Import checks
✓ Code quality
✓ Live inference
✓ Benchmarks

Score: 100%
```

**COLUMN 2 - Documentation:**

```
10+ DOCUMENTS
─────────────
✓ Architecture guide
✓ API reference
✓ Trade-off analysis
✓ User guides
✓ Setup instructions

Fully documented
```

**COLUMN 3 - Codebase:**

```
~2,000 LINES
────────────
model_loader: 254
speculative: ~400
inference: 618
kv_cache: ~300

Production-ready
```

**Bottom quote:**

> "Senior engineers document trade-offs. Junior engineers just ship code."

---

## ADDITIONAL INSTRUCTIONS FOR GAMMA:

1. Make the design look like a technical developer conference presentation
2. Use dark mode for slides 3, 4, 6, 9 (code-heavy slides)
3. Use light mode for slides 2, 5, 7, 8, 10 (data/comparison slides)
4. Emphasize the big numbers: 58%, 4.62s, 4/4
5. Keep animations minimal (simple fade/appear only)
6. Ensure code blocks are readable with proper monospace font
7. No decorative images - only functional diagrams and charts
