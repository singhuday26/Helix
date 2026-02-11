# PagedAttention Comparison - Quick Reference

## 🚀 Quick Start

### Backend

```bash
# Activate virtual environment
.\ven\Scripts\Activate.ps1

# Start server
python run.py
```

### Frontend

```bash
cd frontend
npm run dev
```

### Test

```bash
python test_paged_attention_comparison.py
```

### Access

- **Frontend**: http://localhost:5173/comparison
- **API Docs**: http://localhost:8000/docs
- **Memory Endpoint**: http://localhost:8000/compare/memory

## 📊 Memory Savings

For a 128-token sequence (typical conversation turn):

| Metric      | Traditional   | PagedAttention | Savings          |
| ----------- | ------------- | -------------- | ---------------- |
| Memory      | 22.00 MB      | 2.75 MB        | 19.25 MB (87.5%) |
| Allocation  | Pre-allocated | On-demand      | -                |
| Blocks Used | N/A           | 8/1024         | 0.8% utilization |

## 🎨 Visual Features

### 1. Metrics Cards

```
┌──────────────┬──────────────┬──────────────┬──────────────┐
│ Traditional  │ PagedAtten.  │ Memory Saved │ Utilization  │
│   22.0 MB    │    2.8 MB    │   19.2 MB    │    0.8%      │
│ Pre-allocated│  On-demand   │  87.5% less  │  8/1024 blks │
└──────────────┴──────────────┴──────────────┴──────────────┘
```

### 2. Traditional Memory Bar

```
┌────────────────────────────────────────────────────────────┐
│████████ (Used: 128 tokens) ░░░░░░░ (Wasted: 1920 tokens) │
└────────────────────────────────────────────────────────────┘
```

### 3. PagedAttention Block Grid

```
┌─ 1024 blocks (8×128 grid) ─────────────────────────────┐
│ ■■■■■■■■ (8 allocated blocks)                          │
│ □□□□□□□□ (1016 free blocks)                            │
│ ...                                                     │
└────────────────────────────────────────────────────────┘
```

## 🎨 Theme Colors

- **Traditional**: Gray (`#6b7280`, `#9ca3af`)
- **PagedAttention**: Purple-Pink gradient (`#a855f7` → `#ec4899`)
- **Memory Saved**: Green (`#22c55e`)
- **Utilization**: Pink (`#ec4899`)

## 📁 Files Modified

### Backend

- `src/api.py` - Added `/compare/memory` endpoint and response model

### Frontend

- `frontend/src/pages/ComparisonPage.jsx` - Added memory comparison section

### New Files

- `test_paged_attention_comparison.py` - Test suite
- `PAGED_ATTENTION_COMPARISON_DOCS.md` - Full documentation
- `PAGED_ATTENTION_QUICK_REF.md` - This file

## 🧪 Testing Checklist

- [ ] Backend server starts without errors
- [ ] Navigate to `/comparison` page
- [ ] Click "Show Memory Comparison" button
- [ ] Metrics cards appear with animation
- [ ] Memory bar shows used vs wasted
- [ ] Block grid fills progressively
- [ ] All percentages calculate correctly
- [ ] Responsive on mobile
- [ ] Works in Chrome, Firefox, Safari
- [ ] No console errors

## 💡 Key Implementation Details

### Backend Calculation

```python
# Traditional: Pre-allocate for max length
traditional_bytes = layers × 2 × max_seq_len × heads × head_dim × dtype_size

# PagedAttention: Allocate blocks as needed
blocks_needed = ⌈sequence_length / block_size⌉
paged_bytes = blocks_needed × layers × 2 × block_size × heads × head_dim × dtype_size
```

### Frontend Animation

```javascript
// Progressive block filling
const shouldAnimate = memoryAnimationProgress >= (i / blocks_used) * 100;
// Each block has staggered delay
const animationDelay = 0.6 + (i × 0.01);
```

## 🎯 User Experience Flow

1. User lands on `/comparison` page
2. Sees speculative decoding comparison first
3. Scrolls down to "Memory Efficiency: PagedAttention"
4. Clicks "Show Memory Comparison" button
5. Metrics fade in (0.1s, 0.2s, 0.3s, 0.4s delays)
6. Memory visualizations slide in from sides
7. Block grid fills progressively (smooth animation)
8. User understands memory savings visually

## 🔧 Configuration Quick Reference

### Change Sequence Length

**File**: `src/api.py`

```python
sequence_length = 128  # Change this value (1-2048)
```

### Change Animation Speed

**File**: `frontend/src/pages/ComparisonPage.jsx`

```javascript
progress += 2; // Higher = faster
// ... }, 20);  // Lower = faster
```

### Change Block Size/Count

**File**: `src/api.py`

```python
block_size = 16      # Tokens per block
num_blocks = 1024    # Total blocks
```

## 📊 Example API Response

```json
{
  "traditional_memory_mb": 22.0,
  "paged_memory_mb": 2.75,
  "memory_saved_mb": 19.25,
  "memory_saved_percent": 87.5,
  "num_blocks": 1024,
  "block_size": 16,
  "blocks_used": 8,
  "blocks_free": 1016,
  "utilization_percent": 0.8,
  "sequence_length": 128
}
```

## 🐛 Common Issues

| Issue              | Solution                                    |
| ------------------ | ------------------------------------------- |
| Connection refused | Start backend: `python run.py`              |
| Module not found   | Activate venv: `.\ven\Scripts\Activate.ps1` |
| No animation       | Check browser console for errors            |
| Wrong calculations | Verify model config matches TinyLlama       |
| CORS error         | Check CORS middleware in `src/api.py`       |

## 📚 Related Documentation

- **Full Docs**: `PAGED_ATTENTION_COMPARISON_DOCS.md`
- **Phase 4B**: `PHASE4B_RESULTS.md`
- **KV Cache**: `src/kv_cache.py`
- **API Reference**: http://localhost:8000/docs

## ✨ Feature Highlights

✅ **87.5% memory savings** visualized clearly
✅ **Animated block allocation** shows on-demand usage
✅ **Consistent theming** with existing comparisons
✅ **Comprehensive testing** script included
✅ **Mobile-responsive** design
✅ **API documented** in OpenAPI/Swagger

## 🎉 Success Metrics

When feature is working correctly, you should see:

- Memory saved: **~87.5%** for 128-token sequence
- Blocks used: **8** out of 1024 (0.8% utilization)
- Traditional: **22 MB** pre-allocated
- Paged: **2.75 MB** on-demand
- Smooth animations without jank
- No console errors
