import React, {
  useState,
  useEffect,
  useCallback,
  useRef,
  useMemo,
} from "react";
import { motion, AnimatePresence } from "framer-motion";

// ═══════════════════════════════════════════════════════════════
//  CONFIGURATION & CONSTANTS
// ═══════════════════════════════════════════════════════════════

const BLOCK_SIZE = 16; // tokens per block
const NUM_LAYERS = 22;
const NUM_KV_HEADS = 4;
const HEAD_DIM = 64;
const DTYPE_SIZE = 2; // float16 = 2 bytes
const MAX_SEQ_LEN = 2048;
const TOTAL_BLOCKS = 1024;

// Simulation sequences: increasing token counts
const SEQUENCES = [
  { id: 1, name: "Request A", tokens: 32, color: "#a855f7" },
  { id: 2, name: "Request B", tokens: 48, color: "#ec4899" },
  { id: 3, name: "Request C", tokens: 64, color: "#8b5cf6" },
  { id: 4, name: "Request D", tokens: 24, color: "#d946ef" },
];

const calculateMemory = (tokens) => {
  // Memory = layers × 2 (K+V) × tokens × heads × head_dim × dtype_size
  const bytes = NUM_LAYERS * 2 * tokens * NUM_KV_HEADS * HEAD_DIM * DTYPE_SIZE;
  return bytes / (1024 * 1024); // Convert to MB
};

const calculateBlocks = (tokens) => Math.ceil(tokens / BLOCK_SIZE);

// ═══════════════════════════════════════════════════════════════
//  SMALL REUSABLE COMPONENTS
// ═══════════════════════════════════════════════════════════════

const StatBadge = ({ label, value, color = "text-white" }) => (
  <div className="flex flex-col items-center">
    <span className={`text-xl font-bold font-mono ${color}`}>{value}</span>
    <span className="text-[10px] uppercase tracking-wider text-gray-500 mt-0.5">
      {label}
    </span>
  </div>
);

const MemoryBlock = ({ used, total, label, color = "#6b7280" }) => {
  const percentage = (used / total) * 100;
  return (
    <div>
      <div className="flex justify-between text-xs mb-1.5">
        <span className="text-gray-400">{label}</span>
        <span className="text-gray-500 font-mono">
          {used}/{total} tokens
        </span>
      </div>
      <div className="h-8 rounded-lg bg-gray-900 overflow-hidden relative border border-gray-800">
        <motion.div
          initial={{ width: 0 }}
          animate={{ width: `${percentage}%` }}
          transition={{ duration: 0.6, ease: "easeOut" }}
          className="h-full"
          style={{ background: color }}
        />
        <div className="absolute inset-0 flex items-center justify-center">
          <span className="text-[10px] font-mono text-white/80 drop-shadow">
            {percentage.toFixed(1)}% used
          </span>
        </div>
      </div>
    </div>
  );
};

const BlockCell = ({ active, index, delay = 0, color = "#a855f7" }) => (
  <motion.div
    initial={{ opacity: 0, scale: 0.6 }}
    animate={{
      opacity: active ? 1 : 0.15,
      scale: active ? 1 : 0.8,
      backgroundColor: active ? color : "#1f2937",
    }}
    transition={{ delay, duration: 0.3 }}
    className="w-full aspect-square rounded border"
    style={{
      borderColor: active ? `${color}80` : "#374151",
    }}
    title={active ? `Block ${index}` : `Free`}
  />
);

// ═══════════════════════════════════════════════════════════════
//  MEMORY ALLOCATION SIMULATOR
// ═══════════════════════════════════════════════════════════════

const AllocationSimulator = () => {
  const [activeSequences, setActiveSequences] = useState([]);
  const [playing, setPlaying] = useState(false);
  const [step, setStep] = useState(0);
  const intervalRef = useRef(null);

  const totalTokens = useMemo(
    () => activeSequences.reduce((sum, seq) => sum + seq.tokens, 0),
    [activeSequences],
  );

  const totalBlocks = useMemo(
    () =>
      activeSequences.reduce(
        (sum, seq) => sum + calculateBlocks(seq.tokens),
        0,
      ),
    [activeSequences],
  );

  const traditionalMemory = useMemo(() => {
    // Traditional: pre-allocate for max_seq_len per sequence
    return activeSequences.length * calculateMemory(MAX_SEQ_LEN);
  }, [activeSequences]);

  const pagedMemory = useMemo(() => {
    return activeSequences.reduce(
      (sum, seq) => sum + calculateMemory(seq.tokens),
      0,
    );
  }, [activeSequences]);

  const savings = traditionalMemory - pagedMemory;
  const savingsPercent =
    traditionalMemory > 0 ? (savings / traditionalMemory) * 100 : 0;

  useEffect(() => {
    if (playing && step < SEQUENCES.length) {
      intervalRef.current = setTimeout(() => {
        setActiveSequences((prev) => [...prev, SEQUENCES[step]]);
        setStep((s) => s + 1);
      }, 1200);
    } else if (step >= SEQUENCES.length) {
      setPlaying(false);
    }
    return () => clearTimeout(intervalRef.current);
  }, [playing, step]);

  const reset = useCallback(() => {
    setPlaying(false);
    setActiveSequences([]);
    setStep(0);
  }, []);

  const togglePlay = useCallback(() => {
    if (step >= SEQUENCES.length) {
      reset();
      setTimeout(() => setPlaying(true), 100);
    } else {
      setPlaying((p) => !p);
    }
  }, [step, reset]);

  // Block allocation map
  const blockMap = useMemo(() => {
    const map = [];
    let offset = 0;
    activeSequences.forEach((seq) => {
      const blocks = calculateBlocks(seq.tokens);
      for (let i = 0; i < blocks; i++) {
        map.push({ seqId: seq.id, color: seq.color });
      }
      offset += blocks;
    });
    return map;
  }, [activeSequences]);

  return (
    <div className="max-w-4xl mx-auto">
      <div className="text-center mb-6">
        <p className="text-sm text-gray-400">
          {step === 0
            ? "Press Play to simulate incoming requests"
            : step < SEQUENCES.length
              ? `Allocating request ${step}/${SEQUENCES.length}...`
              : `All ${SEQUENCES.length} requests allocated`}
        </p>
      </div>

      {/* Traditional Allocation */}
      <div className="mb-6 p-5 rounded-xl bg-void-950 border border-white/[.06]">
        <div className="flex items-center justify-between mb-4">
          <div className="flex items-center gap-2">
            <span className="text-base">📦</span>
            <h4 className="text-sm font-semibold text-gray-400">
              Traditional Cache
            </h4>
          </div>
          <span className="text-xs text-gray-500 font-mono">
            {traditionalMemory.toFixed(1)} MB
          </span>
        </div>
        <div className="space-y-3">
          {activeSequences.map((seq, i) => (
            <motion.div
              key={seq.id}
              initial={{ opacity: 0, x: -20 }}
              animate={{ opacity: 1, x: 0 }}
              transition={{ delay: i * 0.3 }}
            >
              <MemoryBlock
                used={seq.tokens}
                total={MAX_SEQ_LEN}
                label={seq.name}
                color="#6b7280"
              />
            </motion.div>
          ))}
        </div>
        {activeSequences.length > 0 && (
          <p className="text-xs text-rose-400/80 mt-3 text-right">
            Wasted:{" "}
            {(
              ((activeSequences.length * MAX_SEQ_LEN - totalTokens) /
                (activeSequences.length * MAX_SEQ_LEN)) *
              100
            ).toFixed(1)}
            % of allocated memory
          </p>
        )}
      </div>

      {/* PagedAttention Allocation */}
      <div className="mb-6 p-5 rounded-xl bg-void-950 border border-purple-500/20">
        <div className="flex items-center justify-between mb-4">
          <div className="flex items-center gap-2">
            <span className="text-base">🧩</span>
            <h4 className="text-sm font-semibold text-purple-400">
              PagedAttention (On-Demand)
            </h4>
          </div>
          <span className="text-xs text-purple-400 font-mono">
            {pagedMemory.toFixed(1)} MB
          </span>
        </div>

        {/* Block Grid Visualization */}
        <div className="grid grid-cols-16 gap-1 mb-3">
          {Array.from({ length: 64 }).map((_, i) => {
            const block = blockMap[i];
            return (
              <BlockCell
                key={i}
                active={!!block}
                index={i}
                delay={i * 0.02}
                color={block?.color}
              />
            );
          })}
        </div>
        <p className="text-xs text-gray-500 text-center">
          Showing first 64 blocks (of {TOTAL_BLOCKS} total)
        </p>
      </div>

      {/* Controls */}
      <div className="flex items-center justify-center gap-3 mb-6">
        <button
          onClick={togglePlay}
          className="px-5 py-2.5 rounded-lg bg-purple-600/20 text-purple-400 border border-purple-500/30 hover:bg-purple-600/30 active:scale-95 transition-all text-sm font-medium"
        >
          {playing
            ? "⏸ Pause"
            : step >= SEQUENCES.length
              ? "↺ Replay"
              : "▶ Play"}
        </button>
        <button
          onClick={reset}
          className="px-5 py-2.5 rounded-lg bg-white/5 text-gray-400 border border-white/10 hover:bg-white/10 active:scale-95 transition-all text-sm font-medium"
        >
          ↺ Reset
        </button>
      </div>

      {/* Stats */}
      <motion.div
        layout
        className="flex items-center justify-center gap-6 sm:gap-8 py-4 px-6 rounded-xl bg-white/[.02] border border-white/[.05]"
      >
        <StatBadge
          label="Traditional"
          value={`${traditionalMemory.toFixed(1)} MB`}
          color="text-gray-400"
        />
        <div className="w-px h-8 bg-white/10" />
        <StatBadge
          label="PagedAttention"
          value={`${pagedMemory.toFixed(1)} MB`}
          color="text-purple-400"
        />
        <div className="w-px h-8 bg-white/10" />
        <StatBadge
          label="Memory Saved"
          value={savingsPercent > 0 ? `${savingsPercent.toFixed(0)}%` : "—"}
          color="text-emerald-400"
        />
      </motion.div>
    </div>
  );
};

// ═══════════════════════════════════════════════════════════════
//  FRAGMENTATION COMPARISON
// ═══════════════════════════════════════════════════════════════

const FragmentationDemo = () => {
  const [scenario, setScenario] = useState("sequential");

  const scenarios = {
    sequential: {
      label: "Sequential Arrivals",
      requests: [
        { tokens: 80, status: "active" },
        { tokens: 120, status: "active" },
        { tokens: 60, status: "active" },
      ],
    },
    interleaved: {
      label: "Request B Completes Early",
      requests: [
        { tokens: 80, status: "active" },
        { tokens: 120, status: "completed" },
        { tokens: 60, status: "active" },
      ],
    },
    newRequest: {
      label: "New Request Arrives",
      requests: [
        { tokens: 80, status: "active" },
        { tokens: 120, status: "completed" },
        { tokens: 60, status: "active" },
        { tokens: 100, status: "pending" },
      ],
    },
  };

  const currentScenario = scenarios[scenario];

  // Traditional: contiguous allocation leads to fragmentation
  const traditionalWaste = scenario === "newRequest" ? 120 : 0;

  // Paged: can reuse freed blocks
  const pagedReuse = scenario === "newRequest" ? 100 : 0;

  return (
    <div className="grid md:grid-cols-2 gap-6">
      {/* Traditional */}
      <div className="p-5 rounded-xl bg-void-950 border border-white/[.06]">
        <h4 className="text-sm font-semibold text-gray-400 mb-4 flex items-center gap-2">
          <span>📦</span>
          Traditional: Contiguous Allocation
        </h4>

        <div className="space-y-2 mb-4">
          {currentScenario.requests.map((req, i) => (
            <motion.div
              key={i}
              layout
              className={`h-10 rounded-lg flex items-center justify-center text-xs font-mono ${
                req.status === "active"
                  ? "bg-gray-700 text-gray-200"
                  : req.status === "completed"
                    ? "bg-rose-900/30 text-rose-400 border border-rose-500/20"
                    : "bg-amber-900/30 text-amber-400 border border-amber-500/20"
              }`}
              style={{ width: `${(req.tokens / 120) * 100}%` }}
            >
              {req.tokens} tokens
            </motion.div>
          ))}
        </div>

        {scenario === "newRequest" && (
          <motion.p
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            className="text-xs text-rose-400"
          >
            ⚠️ Cannot reuse freed space! Must allocate new contiguous block →
            fragmentation
          </motion.p>
        )}
      </div>

      {/* PagedAttention */}
      <div className="p-5 rounded-xl bg-void-950 border border-purple-500/20">
        <h4 className="text-sm font-semibold text-purple-400 mb-4 flex items-center gap-2">
          <span>🧩</span>
          PagedAttention: Block Reuse
        </h4>

        <div className="grid grid-cols-12 gap-1 mb-4">
          {Array.from({ length: 24 }).map((_, i) => {
            let status = "free";
            if (i < 5) status = "req-a";
            else if (i >= 5 && i < 13) {
              status =
                scenario === "interleaved" || scenario === "newRequest"
                  ? "freed"
                  : "req-b";
            } else if (i >= 13 && i < 17) status = "req-c";
            else if (i >= 5 && i < 11 && scenario === "newRequest")
              status = "req-d";

            return (
              <motion.div
                key={i}
                layout
                className={`aspect-square rounded ${
                  status === "req-a"
                    ? "bg-cyan-600"
                    : status === "req-b"
                      ? "bg-purple-600"
                      : status === "req-c"
                        ? "bg-pink-600"
                        : status === "req-d"
                          ? "bg-emerald-600"
                          : status === "freed"
                            ? "bg-gray-800 border border-dashed border-gray-600"
                            : "bg-gray-900"
                }`}
                animate={{
                  scale: status === "req-d" ? [1, 1.1, 1] : 1,
                }}
                transition={{ duration: 0.5 }}
              />
            );
          })}
        </div>

        {scenario === "newRequest" && (
          <motion.p
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            className="text-xs text-emerald-400"
          >
            ✓ Reuses freed blocks! New request fits in existing memory → no
            fragmentation
          </motion.p>
        )}
      </div>

      {/* Scenario Selector */}
      <div className="md:col-span-2 flex items-center justify-center gap-2">
        {Object.entries(scenarios).map(([key, value]) => (
          <button
            key={key}
            onClick={() => setScenario(key)}
            className={`px-4 py-2 rounded-lg text-xs font-medium transition-all ${
              scenario === key
                ? "bg-purple-600/30 text-purple-400 border border-purple-500/30"
                : "bg-white/5 text-gray-500 border border-white/10 hover:bg-white/10"
            }`}
          >
            {value.label}
          </button>
        ))}
      </div>
    </div>
  );
};

// ═══════════════════════════════════════════════════════════════
//  BLOCK TABLE EXPLORER
// ═══════════════════════════════════════════════════════════════

const BlockTableExplorer = () => {
  const [tokenPos, setTokenPos] = useState(42);

  const blockId = Math.floor(tokenPos / BLOCK_SIZE);
  const offset = tokenPos % BLOCK_SIZE;

  // Simulate block table with scattered physical blocks
  const virtualToPhysical = (virtualBlock) => {
    const mapping = [0, 5, 2, 13, 8, 21, 17, 9, 3, 14];
    return mapping[virtualBlock] || virtualBlock;
  };

  const physicalBlockId = virtualToPhysical(blockId);

  return (
    <div className="p-6 sm:p-8 rounded-2xl bg-void-950 border border-white/[.06]">
      <h3 className="text-lg font-semibold text-white mb-2 text-center">
        Virtual Memory Mapping
      </h3>
      <p className="text-xs text-gray-500 text-center mb-6">
        Explore how logical token positions map to physical memory blocks
      </p>

      <div className="max-w-lg mx-auto">
        {/* Token Position Slider */}
        <div className="mb-8">
          <div className="flex items-center justify-between mb-2">
            <span className="text-sm text-gray-400">Token Position</span>
            <span className="text-lg font-mono text-purple-400">
              {tokenPos}
            </span>
          </div>
          <input
            type="range"
            min={0}
            max={159}
            value={tokenPos}
            onChange={(e) => setTokenPos(parseInt(e.target.value))}
            className="w-full h-2 bg-gray-800 rounded-full appearance-none cursor-pointer
                       [&::-webkit-slider-thumb]:appearance-none [&::-webkit-slider-thumb]:w-5 [&::-webkit-slider-thumb]:h-5
                       [&::-webkit-slider-thumb]:rounded-full [&::-webkit-slider-thumb]:bg-purple-500
                       [&::-webkit-slider-thumb]:shadow-lg [&::-webkit-slider-thumb]:shadow-purple-500/30"
          />
        </div>

        {/* Mapping Visualization */}
        <div className="space-y-6 mb-8">
          <div className="flex items-center gap-4">
            <div className="flex-1 p-4 rounded-lg bg-cyan-950/20 border border-cyan-500/20">
              <div className="text-xs text-cyan-400 mb-1">Logical Address</div>
              <div className="font-mono text-lg text-white">
                Token[{tokenPos}]
              </div>
            </div>
            <div className="text-2xl text-gray-600">→</div>
            <div className="flex-1 p-4 rounded-lg bg-purple-950/20 border border-purple-500/20">
              <div className="text-xs text-purple-400 mb-1">Virtual Block</div>
              <div className="font-mono text-lg text-white">
                Block {blockId}
              </div>
              <div className="text-xs text-gray-500 mt-1">Offset: {offset}</div>
            </div>
          </div>

          <div className="flex items-center justify-center">
            <div className="text-2xl text-gray-600">↓</div>
          </div>

          <div className="p-4 rounded-lg bg-pink-950/20 border border-pink-500/20">
            <div className="text-xs text-pink-400 mb-1">Physical Memory</div>
            <div className="font-mono text-lg text-white">
              Block {physicalBlockId} + Offset {offset}
            </div>
            <div className="text-xs text-gray-500 mt-2">
              Physical address: {physicalBlockId * BLOCK_SIZE + offset}
            </div>
          </div>
        </div>

        {/* Block Table Snippet */}
        <div className="p-4 rounded-lg bg-gray-900/50 border border-gray-800">
          <div className="text-xs text-gray-500 mb-2 font-mono">
            Block Table (excerpt):
          </div>
          <div className="space-y-1 font-mono text-xs">
            {[...Array(Math.min(blockId + 3, 10))].map((_, i) => (
              <div
                key={i}
                className={`flex justify-between py-1 px-2 rounded ${
                  i === blockId
                    ? "bg-purple-900/30 text-purple-400"
                    : "text-gray-600"
                }`}
              >
                <span>virtual[{i}]</span>
                <span>→</span>
                <span>physical[{virtualToPhysical(i)}]</span>
              </div>
            ))}
          </div>
        </div>

        {/* Insight */}
        <div className="mt-6 p-3 rounded-lg bg-purple-500/[.04] border border-purple-500/10">
          <p className="text-xs text-gray-400 leading-relaxed">
            <span className="text-purple-400 font-medium">Key insight: </span>
            PagedAttention uses a lookup table (like virtual memory) to map
            logical token positions to scattered physical blocks. This
            eliminates the need for contiguous allocation while adding only ~5%
            lookup overhead.
          </p>
        </div>
      </div>
    </div>
  );
};

// ═══════════════════════════════════════════════════════════════
//  WHY IT WORKS
// ═══════════════════════════════════════════════════════════════

const WhyItWorks = () => (
  <div className="grid md:grid-cols-2 gap-4 sm:gap-6">
    {/* The Problem */}
    <div className="p-5 sm:p-6 rounded-xl bg-void-950 border border-white/[.06]">
      <h4 className="text-sm font-semibold text-rose-400 mb-5 flex items-center gap-2">
        <span className="text-base">⚠️</span>
        The Problem: Fragmentation
      </h4>
      <div className="space-y-4">
        <div>
          <div className="text-xs text-gray-500 mb-2">Traditional Approach</div>
          <div className="h-16 rounded-lg bg-gray-900 border border-gray-800 flex items-center px-3 gap-2">
            <div className="flex-1 h-10 bg-gray-700 rounded flex items-center justify-center text-xs">
              Req A
            </div>
            <div className="flex-[2] h-10 bg-rose-900/30 border border-rose-500/30 rounded flex items-center justify-center text-xs text-rose-400">
              Wasted
            </div>
          </div>
        </div>
        <ul className="space-y-2 text-xs text-gray-400">
          <li className="flex items-start gap-2">
            <span className="text-rose-400 mt-0.5">✗</span>
            <span>Must pre-allocate max_seq_len (2048 tokens) per request</span>
          </li>
          <li className="flex items-start gap-2">
            <span className="text-rose-400 mt-0.5">✗</span>
            <span>Average request uses ~128 tokens → 93% waste</span>
          </li>
          <li className="flex items-start gap-2">
            <span className="text-rose-400 mt-0.5">✗</span>
            <span>On 12GB GPU: fits only ~6 concurrent requests</span>
          </li>
        </ul>
      </div>
    </div>

    {/* The Solution */}
    <div className="p-5 sm:p-6 rounded-xl bg-void-950 border border-purple-500/15">
      <h4 className="text-sm font-semibold text-purple-400 mb-5 flex items-center gap-2">
        <span className="text-base">✓</span>
        The Solution: Paged Blocks
      </h4>
      <div className="space-y-4">
        <div>
          <div className="text-xs text-gray-500 mb-2">PagedAttention</div>
          <div className="grid grid-cols-8 gap-1 p-2 rounded-lg bg-gray-900 border border-purple-500/20">
            {Array.from({ length: 8 }).map((_, i) => (
              <div
                key={i}
                className="aspect-square bg-gradient-to-br from-purple-600 to-pink-600 rounded"
              />
            ))}
          </div>
        </div>
        <ul className="space-y-2 text-xs text-gray-400">
          <li className="flex items-start gap-2">
            <span className="text-emerald-400 mt-0.5">✓</span>
            <span>Allocate 16-token blocks on-demand as sequence grows</span>
          </li>
          <li className="flex items-start gap-2">
            <span className="text-emerald-400 mt-0.5">✓</span>
            <span>128-token request uses 8 blocks → 87.5% memory savings</span>
          </li>
          <li className="flex items-start gap-2">
            <span className="text-emerald-400 mt-0.5">✓</span>
            <span>
              Same 12GB GPU: fits ~30 concurrent requests (5× improvement)
            </span>
          </li>
        </ul>
      </div>
    </div>
  </div>
);

// ═══════════════════════════════════════════════════════════════
//  MAIN COMPONENT
// ═══════════════════════════════════════════════════════════════

const PagedAttention = () => {
  return (
    <section
      id="paged-attention"
      className="py-20 sm:py-24 bg-void-900 relative overflow-hidden"
    >
      {/* Background */}
      <div className="helix-bg-section left" aria-hidden="true" />

      <div className="max-w-6xl mx-auto px-4 sm:px-6 relative z-10">
        {/* ── Section Header ── */}
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          whileInView={{ opacity: 1, y: 0 }}
          viewport={{ once: true }}
          className="text-center mb-14"
        >
          <div className="inline-flex items-center px-3 py-1 rounded-full bg-purple-500/10 border border-purple-500/20 text-purple-400 text-xs font-medium mb-4">
            Memory Optimization
          </div>
          <h2 className="text-3xl sm:text-4xl font-bold text-white mb-4">
            How PagedAttention Works
          </h2>
          <p className="text-gray-400 max-w-2xl mx-auto text-sm sm:text-base">
            Eliminate memory fragmentation with virtual memory for KV cache.
            Allocate fixed-size blocks on-demand instead of pre-allocating
            contiguous memory.
          </p>
        </motion.div>

        {/* ── Memory Allocation Simulator ── */}
        <motion.div
          initial={{ opacity: 0, y: 30 }}
          whileInView={{ opacity: 1, y: 0 }}
          viewport={{ once: true }}
          transition={{ delay: 0.1 }}
          className="mb-20"
        >
          <div className="text-center mb-8">
            <h3 className="text-xl sm:text-2xl font-bold text-white mb-2">
              Dynamic Memory Allocation
            </h3>
            <p className="text-gray-500 text-sm">
              Watch how requests allocate memory in real-time
            </p>
          </div>
          <AllocationSimulator />
        </motion.div>

        {/* ── Fragmentation Comparison ── */}
        <motion.div
          initial={{ opacity: 0, y: 30 }}
          whileInView={{ opacity: 1, y: 0 }}
          viewport={{ once: true }}
          className="mb-16"
        >
          <div className="text-center mb-8">
            <h3 className="text-xl sm:text-2xl font-bold text-white mb-2">
              Fragmentation Problem
            </h3>
            <p className="text-gray-500 text-sm">
              See how PagedAttention handles memory reuse
            </p>
          </div>
          <FragmentationDemo />
        </motion.div>

        {/* ── Block Table Explorer ── */}
        <motion.div
          initial={{ opacity: 0, y: 30 }}
          whileInView={{ opacity: 1, y: 0 }}
          viewport={{ once: true }}
          className="mb-16"
        >
          <BlockTableExplorer />
        </motion.div>

        {/* ── Why It Works ── */}
        <motion.div
          initial={{ opacity: 0, y: 30 }}
          whileInView={{ opacity: 1, y: 0 }}
          viewport={{ once: true }}
        >
          <div className="text-center mb-8">
            <h3 className="text-xl sm:text-2xl font-bold text-white mb-2">
              The Impact
            </h3>
            <p className="text-gray-500 text-sm">
              87.5% memory savings for typical workloads
            </p>
          </div>
          <WhyItWorks />
        </motion.div>
      </div>
    </section>
  );
};

export default PagedAttention;
