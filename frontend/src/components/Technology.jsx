import React, {
  useState,
  useEffect,
  useCallback,
  useRef,
  useMemo,
} from "react";
import { motion, AnimatePresence } from "framer-motion";

// ═══════════════════════════════════════════════════════════════
//  SIMULATION DATA
// ═══════════════════════════════════════════════════════════════

const ROUNDS = [
  {
    drafts: ["Large", "language", "models", "generate"],
    results: ["accept", "accept", "accept", "accept"],
    correction: null,
  },
  {
    drafts: ["text", "rapidly", "with", "ease"],
    results: ["accept", "reject", "skip", "skip"],
    correction: "quickly",
  },
  {
    drafts: ["using", "speculative", "decoding", "on"],
    results: ["accept", "accept", "accept", "accept"],
    correction: null,
  },
  {
    drafts: ["edge", "hardware", "for", "inference"],
    results: ["accept", "reject", "skip", "skip"],
    correction: "devices",
  },
];

const getRoundOutput = (round) => {
  const tokens = [];
  for (let i = 0; i < round.drafts.length; i++) {
    if (round.results[i] === "accept") tokens.push(round.drafts[i]);
    else break;
  }
  if (round.correction) tokens.push(round.correction);
  return tokens;
};

const ALL_TOKENS = ROUNDS.flatMap(getRoundOutput);

// Pre-compute animation frames: idle → [draft, verify, accept] × rounds → complete
const FRAMES = (() => {
  const f = [{ type: "idle" }];
  ROUNDS.forEach((_, i) => {
    f.push({ type: "draft", round: i });
    f.push({ type: "verify", round: i });
    f.push({ type: "accept", round: i });
  });
  f.push({ type: "complete" });
  return f;
})();

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

const TokenPill = ({ text, status, delay = 0 }) => {
  const styles = {
    draft:
      "bg-cyan-500/15 text-cyan-400 border-cyan-500/30 shadow-sm shadow-cyan-500/10",
    accept:
      "bg-emerald-500/15 text-emerald-400 border-emerald-500/30 shadow-sm shadow-emerald-500/10",
    reject:
      "bg-rose-500/15 text-rose-400 border-rose-500/30 line-through opacity-70",
    skip: "bg-gray-800/40 text-gray-600 border-gray-700/30 opacity-30",
    correction:
      "bg-amber-500/15 text-amber-300 border-amber-500/30 shadow-sm shadow-amber-500/10",
    output: "bg-white/[.06] text-gray-200 border-white/[.08]",
  };

  const icons = {
    accept: "✓",
    reject: "✗",
    correction: "→",
  };

  return (
    <motion.span
      layout
      initial={{ opacity: 0, scale: 0.7, y: 8 }}
      animate={{ opacity: 1, scale: 1, y: 0 }}
      exit={{ opacity: 0, scale: 0.7, y: -8 }}
      transition={{
        delay,
        duration: 0.3,
        type: "spring",
        stiffness: 400,
        damping: 25,
      }}
      className={`inline-flex items-center gap-1 px-2.5 py-1 rounded-lg border font-mono text-sm whitespace-nowrap ${styles[status] || styles.output}`}
    >
      {icons[status] && (
        <span className="text-[11px] leading-none">{icons[status]}</span>
      )}
      {text}
    </motion.span>
  );
};

const StageBox = ({ icon, title, subtitle, active, color, children }) => (
  <motion.div
    animate={{
      borderColor: active ? color : "rgba(255,255,255,0.05)",
      boxShadow: active ? `0 0 30px ${color}18, 0 0 60px ${color}08` : "none",
    }}
    transition={{ duration: 0.4 }}
    className="relative rounded-xl border bg-void-950/80 backdrop-blur-sm p-5"
  >
    {/* Active glow bar */}
    <motion.div
      animate={{ opacity: active ? 1 : 0 }}
      className="absolute inset-x-0 top-0 h-px rounded-t-xl"
      style={{
        background: `linear-gradient(90deg, transparent, ${color}, transparent)`,
      }}
    />

    <div className="flex items-center gap-2.5 mb-3">
      <span className="text-lg">{icon}</span>
      <div>
        <h4 className="text-sm font-semibold text-white leading-tight">
          {title}
        </h4>
        {subtitle && (
          <p className="text-[11px] text-gray-500 leading-tight mt-0.5">
            {subtitle}
          </p>
        )}
      </div>
    </div>

    <div className="min-h-[52px] flex flex-wrap items-center gap-1.5">
      <AnimatePresence mode="popLayout">{children}</AnimatePresence>
    </div>
  </motion.div>
);

const FlowArrow = ({ active }) => (
  <div className="flex justify-center py-2">
    <motion.div
      animate={{ opacity: active ? 0.8 : 0.15, scale: active ? 1.1 : 1 }}
      transition={{ duration: 0.3 }}
      className="flex flex-col items-center gap-0.5"
    >
      <div
        className={`w-px h-4 ${active ? "bg-helix-draft" : "bg-gray-700"}`}
      />
      <svg
        width="10"
        height="6"
        viewBox="0 0 10 6"
        className={active ? "text-helix-draft" : "text-gray-700"}
      >
        <path d="M0 0 L5 6 L10 0" fill="currentColor" />
      </svg>
    </motion.div>
  </div>
);

// ═══════════════════════════════════════════════════════════════
//  INTERACTIVE PIPELINE SIMULATOR
// ═══════════════════════════════════════════════════════════════

const PipelineSimulator = () => {
  const [frameIdx, setFrameIdx] = useState(0);
  const [playing, setPlaying] = useState(false);
  const intervalRef = useRef(null);

  const frame = FRAMES[frameIdx];
  const currentRound = frame.round !== undefined ? ROUNDS[frame.round] : null;
  const isComplete = frame.type === "complete";
  const isIdle = frame.type === "idle";

  // Derive stats from frame index
  const { outputTokens, forwardPasses } = useMemo(() => {
    let output = [];
    let passes = 0;
    for (let i = 0; i <= frameIdx; i++) {
      if (FRAMES[i].type === "accept") {
        output = [...output, ...getRoundOutput(ROUNDS[FRAMES[i].round])];
      }
      if (FRAMES[i].type === "verify") {
        passes++;
      }
    }
    return { outputTokens: output, forwardPasses: passes };
  }, [frameIdx]);

  const speedup =
    forwardPasses > 0 ? (outputTokens.length / forwardPasses).toFixed(1) : "—";

  // Autoplay with interval
  useEffect(() => {
    if (playing && !isComplete) {
      intervalRef.current = setInterval(() => {
        setFrameIdx((i) => {
          if (i >= FRAMES.length - 1) {
            setPlaying(false);
            return i;
          }
          return i + 1;
        });
      }, 1400);
    }
    return () => clearInterval(intervalRef.current);
  }, [playing, isComplete]);

  const reset = useCallback(() => {
    setPlaying(false);
    clearInterval(intervalRef.current);
    setFrameIdx(0);
  }, []);

  const step = useCallback(() => {
    if (frameIdx < FRAMES.length - 1) setFrameIdx((i) => i + 1);
  }, [frameIdx]);

  const togglePlay = useCallback(() => {
    if (isComplete) {
      reset();
      setTimeout(() => setPlaying(true), 100);
    } else {
      setPlaying((p) => !p);
    }
  }, [isComplete, reset]);

  const displayRound =
    frame.round !== undefined ? frame.round + 1 : isComplete ? 4 : 0;

  // Phase description text
  const phaseText = {
    idle: "Press Play to watch speculative decoding in action",
    draft: "Draft model rapidly generates K candidate tokens...",
    verify:
      "Target model verifies ALL tokens in a single forward pass — this is the key!",
    accept: "Accepted tokens move to output. Rejected tokens get corrected.",
    complete: `Done! Generated ${ALL_TOKENS.length} tokens in just ${ROUNDS.length} forward passes`,
  };

  return (
    <div className="max-w-2xl mx-auto">
      {/* Round Progress Indicator */}
      <div className="flex items-center justify-center gap-2 mb-4">
        {ROUNDS.map((_, i) => (
          <motion.div
            key={i}
            animate={{
              width: frame.round !== undefined && i <= frame.round ? 32 : 8,
              backgroundColor:
                frame.round !== undefined && i <= frame.round
                  ? "#06b6d4"
                  : "#1f2937",
            }}
            className="h-2 rounded-full"
            transition={{ duration: 0.3 }}
          />
        ))}
        <span className="text-xs text-gray-500 ml-2 font-mono">
          {isIdle
            ? "Ready"
            : isComplete
              ? "Complete"
              : `Round ${displayRound}/${ROUNDS.length}`}
        </span>
      </div>

      {/* Phase Description */}
      <motion.p
        key={frame.type + (frame.round || "")}
        initial={{ opacity: 0, y: -5 }}
        animate={{ opacity: 1, y: 0 }}
        className="text-center text-sm text-gray-400 mb-6 min-h-[40px]"
      >
        {phaseText[frame.type]}
      </motion.p>

      {/* ── DRAFT MODEL ── */}
      <StageBox
        icon="⚡"
        title="Draft Model"
        subtitle="68M params · Sequential generation"
        active={frame.type === "draft"}
        color="rgb(6, 182, 212)"
      >
        {frame.type === "draft" &&
          currentRound.drafts.map((token, i) => (
            <TokenPill
              key={`d-${frame.round}-${i}`}
              text={token}
              status="draft"
              delay={i * 0.15}
            />
          ))}
        {isIdle && (
          <motion.span
            animate={{ opacity: [0.3, 0.6, 0.3] }}
            transition={{ repeat: Infinity, duration: 2 }}
            className="text-gray-600 text-sm italic"
          >
            Waiting to draft tokens...
          </motion.span>
        )}
        {frame.type === "verify" && (
          <span className="text-cyan-800 text-xs">
            Sent {currentRound.drafts.length} draft tokens →
          </span>
        )}
        {frame.type === "accept" && (
          <span className="text-gray-700 text-xs">Preparing next round...</span>
        )}
        {isComplete && (
          <span className="text-emerald-700 text-xs">
            ✓ All rounds complete
          </span>
        )}
      </StageBox>

      <FlowArrow active={frame.type === "draft" || frame.type === "verify"} />

      {/* ── TARGET MODEL ── */}
      <StageBox
        icon="🔍"
        title="Target Model"
        subtitle="1.1B params · Parallel verification in ONE pass"
        active={frame.type === "verify"}
        color="rgb(16, 185, 129)"
      >
        {frame.type === "verify" && (
          <>
            {currentRound.drafts.map((token, i) => (
              <TokenPill
                key={`v-${frame.round}-${i}`}
                text={token}
                status={currentRound.results[i]}
                delay={0.3}
              />
            ))}
            {currentRound.correction && (
              <TokenPill
                key={`c-${frame.round}`}
                text={currentRound.correction}
                status="correction"
                delay={0.5}
              />
            )}
          </>
        )}
        {frame.type === "draft" && (
          <span className="text-gray-700 text-xs">
            Waiting for draft tokens...
          </span>
        )}
        {frame.type === "accept" && (
          <span className="text-emerald-800 text-xs">
            Verified → forwarding accepted tokens ↓
          </span>
        )}
        {isIdle && (
          <span className="text-gray-700 text-xs">Standing by...</span>
        )}
        {isComplete && (
          <span className="text-emerald-700 text-xs">
            ✓ All tokens verified
          </span>
        )}
      </StageBox>

      <FlowArrow active={frame.type === "verify" || frame.type === "accept"} />

      {/* ── OUTPUT ── */}
      <StageBox
        icon="📝"
        title="Generated Output"
        subtitle={`${outputTokens.length} / ${ALL_TOKENS.length} tokens`}
        active={frame.type === "accept" || isComplete}
        color="rgb(34, 197, 94)"
      >
        {outputTokens.length > 0 ? (
          <>
            {outputTokens.map((token, i) => (
              <TokenPill key={`o-${i}`} text={token} status="output" />
            ))}
            {!isComplete && (
              <motion.span
                animate={{ opacity: [1, 0] }}
                transition={{ repeat: Infinity, duration: 0.8 }}
                className="text-helix-draft font-mono text-sm"
              >
                ▌
              </motion.span>
            )}
          </>
        ) : (
          <span className="text-gray-700 text-xs italic">
            Output will appear here...
          </span>
        )}
      </StageBox>

      {/* ── CONTROLS ── */}
      <div className="flex items-center justify-center gap-3 mt-6">
        <button
          onClick={togglePlay}
          className="px-5 py-2.5 rounded-lg bg-helix-draft/20 text-cyan-400 border border-helix-draft/30 hover:bg-helix-draft/30 active:scale-95 transition-all text-sm font-medium"
          aria-label={playing ? "Pause" : isComplete ? "Replay" : "Play"}
        >
          {playing ? "⏸ Pause" : isComplete ? "↺ Replay" : "▶ Play"}
        </button>
        <button
          onClick={step}
          disabled={isComplete || playing}
          className="px-5 py-2.5 rounded-lg bg-white/5 text-gray-300 border border-white/10 hover:bg-white/10 active:scale-95 transition-all text-sm font-medium disabled:opacity-30 disabled:cursor-not-allowed"
          aria-label="Step forward"
        >
          ⏭ Step
        </button>
        <button
          onClick={reset}
          className="px-5 py-2.5 rounded-lg bg-white/5 text-gray-400 border border-white/10 hover:bg-white/10 active:scale-95 transition-all text-sm font-medium"
          aria-label="Reset"
        >
          ↺ Reset
        </button>
      </div>

      {/* ── LIVE STATS ── */}
      <motion.div
        layout
        className="mt-6 flex items-center justify-center gap-6 sm:gap-8 py-4 px-6 rounded-xl bg-white/[.02] border border-white/[.05]"
      >
        <StatBadge label="Tokens" value={outputTokens.length} />
        <div className="w-px h-8 bg-white/10" />
        <StatBadge
          label="Forward Passes"
          value={forwardPasses}
          color="text-cyan-400"
        />
        <div className="w-px h-8 bg-white/10" />
        <StatBadge
          label="Speedup"
          value={`${speedup}×`}
          color="text-emerald-400"
        />
      </motion.div>
    </div>
  );
};

// ═══════════════════════════════════════════════════════════════
//  DECODING SPEED RACE
// ═══════════════════════════════════════════════════════════════

const DecodingRace = () => {
  const [racing, setRacing] = useState(false);
  const [finished, setFinished] = useState(false);
  const [stdProgress, setStdProgress] = useState(0);
  const [specProgress, setSpecProgress] = useState(0);
  const [stdPasses, setStdPasses] = useState(0);
  const [specPasses, setSpecPasses] = useState(0);
  const stdRef = useRef(null);
  const specRef = useRef(null);
  const total = ALL_TOKENS.length;

  useEffect(() => {
    return () => {
      clearInterval(stdRef.current);
      clearInterval(specRef.current);
    };
  }, []);

  const startRace = () => {
    setStdProgress(0);
    setSpecProgress(0);
    setStdPasses(0);
    setSpecPasses(0);
    setFinished(false);
    setRacing(true);

    // Standard decoding: 1 token per 350ms
    let sc = 0;
    stdRef.current = setInterval(() => {
      sc++;
      setStdProgress(sc);
      setStdPasses(sc);
      if (sc >= total) clearInterval(stdRef.current);
    }, 350);

    // Speculative decoding: 1 round per 350ms, variable tokens per round
    let specRound = 0;
    let specCount = 0;
    specRef.current = setInterval(() => {
      if (specRound < ROUNDS.length) {
        const roundTokens = getRoundOutput(ROUNDS[specRound]).length;
        specCount += roundTokens;
        specRound++;
        setSpecProgress(specCount);
        setSpecPasses(specRound);
      }
      if (specRound >= ROUNDS.length) {
        clearInterval(specRef.current);
        setFinished(true);
      }
    }, 350);
  };

  const resetRace = () => {
    clearInterval(stdRef.current);
    clearInterval(specRef.current);
    setRacing(false);
    setFinished(false);
    setStdProgress(0);
    setSpecProgress(0);
    setStdPasses(0);
    setSpecPasses(0);
  };

  const specDone = specProgress >= total;
  const stdDone = stdProgress >= total;

  return (
    <div>
      <div className="grid md:grid-cols-2 gap-4 sm:gap-6">
        {/* Standard Decoding */}
        <div className="relative p-5 sm:p-6 rounded-xl bg-void-950 border border-white/[.06]">
          <div className="flex items-center gap-2 mb-4">
            <span className="text-base">🐢</span>
            <h4 className="text-sm font-semibold text-gray-400">
              Standard Decoding
            </h4>
          </div>

          <div className="h-3 rounded-full bg-gray-800/80 overflow-hidden mb-3">
            <motion.div
              className="h-full bg-gray-500 rounded-full"
              animate={{ width: `${(stdProgress / total) * 100}%` }}
              transition={{ duration: 0.25 }}
            />
          </div>

          <div className="flex justify-between text-xs mb-3">
            <span className="text-gray-500">
              {stdProgress}/{total} tokens
            </span>
            <span className="text-gray-500 font-mono">
              {stdPasses} forward passes
            </span>
          </div>

          <div className="min-h-[48px] p-3 rounded-lg bg-gray-900/50 border border-gray-800/50">
            <p className="text-sm text-gray-400 font-mono leading-relaxed break-words">
              {ALL_TOKENS.slice(0, stdProgress).join(" ")}
              {!stdDone && stdProgress > 0 && (
                <span className="animate-pulse text-gray-600 ml-0.5">▌</span>
              )}
              {stdDone && <span className="text-gray-600 ml-1">■</span>}
            </p>
          </div>
        </div>

        {/* Speculative Decoding */}
        <div className="relative p-5 sm:p-6 rounded-xl bg-void-950 border border-cyan-500/20">
          <AnimatePresence>
            {specDone && !stdDone && (
              <motion.div
                initial={{ opacity: 0, scale: 0.6, y: -10 }}
                animate={{ opacity: 1, scale: 1, y: 0 }}
                className="absolute -top-3 -right-2 px-2.5 py-1 rounded-full bg-emerald-500/20 text-emerald-400 text-xs font-bold border border-emerald-500/30 shadow-lg shadow-emerald-500/10"
              >
                🏆 Winner!
              </motion.div>
            )}
          </AnimatePresence>

          <div className="flex items-center gap-2 mb-4">
            <span className="text-base">⚡</span>
            <h4 className="text-sm font-semibold text-cyan-400">
              Speculative Decoding
            </h4>
          </div>

          <div className="h-3 rounded-full bg-gray-800/80 overflow-hidden mb-3">
            <motion.div
              className="h-full bg-gradient-to-r from-cyan-500 to-emerald-500 rounded-full"
              animate={{ width: `${(specProgress / total) * 100}%` }}
              transition={{ duration: 0.25 }}
            />
          </div>

          <div className="flex justify-between text-xs mb-3">
            <span className="text-gray-500">
              {specProgress}/{total} tokens
            </span>
            <span className="text-cyan-500 font-mono">
              {specPasses} forward passes
            </span>
          </div>

          <div className="min-h-[48px] p-3 rounded-lg bg-cyan-950/20 border border-cyan-900/30">
            <p className="text-sm text-gray-300 font-mono leading-relaxed break-words">
              {ALL_TOKENS.slice(0, specProgress).join(" ")}
              {!specDone && specProgress > 0 && (
                <span className="animate-pulse text-cyan-500 ml-0.5">▌</span>
              )}
              {specDone && <span className="text-emerald-500 ml-1">■</span>}
            </p>
          </div>
        </div>
      </div>

      {/* Result Message */}
      <AnimatePresence>
        {finished && stdDone && (
          <motion.div
            initial={{ opacity: 0, y: 10 }}
            animate={{ opacity: 1, y: 0 }}
            className="text-center mt-4"
          >
            <p className="text-sm text-gray-400">
              Speculative decoding used{" "}
              <span className="text-cyan-400 font-bold">{specPasses}</span>{" "}
              forward passes vs{" "}
              <span className="text-gray-300 font-bold">{total}</span> — a{" "}
              <span className="text-emerald-400 font-bold text-base">
                {(total / specPasses).toFixed(1)}× speedup
              </span>
            </p>
          </motion.div>
        )}
      </AnimatePresence>

      {/* Race Button */}
      <div className="flex justify-center mt-5">
        <button
          onClick={racing ? resetRace : startRace}
          className="px-6 py-2.5 rounded-lg bg-gradient-to-r from-cyan-600 to-emerald-600 text-white font-medium text-sm hover:from-cyan-500 hover:to-emerald-500 active:scale-95 transition-all shadow-lg shadow-cyan-500/20"
        >
          {racing ? "↺ Reset Race" : "🏁 Start Race"}
        </button>
      </div>
    </div>
  );
};

// ═══════════════════════════════════════════════════════════════
//  K-DEPTH EXPLORER
// ═══════════════════════════════════════════════════════════════

const DepthExplorer = () => {
  const [k, setK] = useState(4);

  // Expected tokens per round using geometric acceptance model
  const P = 0.8;
  const expectedTokens = (P * (1 - Math.pow(P, k))) / (1 - P) + 1;
  const draftCost = 0.08;
  const effectiveSpeedup = expectedTokens / (1 + k * draftCost);
  const acceptedCount = Math.round(
    (k * ((P * (1 - Math.pow(P, k))) / (1 - P))) / k,
  );

  const labels = {
    1: "Minimal",
    2: "Conservative",
    3: "Moderate",
    4: "Balanced ★",
    5: "Aggressive",
    6: "High",
    7: "Very High",
    8: "Maximum",
  };

  return (
    <div className="p-6 sm:p-8 rounded-2xl bg-void-950 border border-white/[.06]">
      <h3 className="text-lg font-semibold text-white mb-2 text-center">
        Speculation Depth Trade-off
      </h3>
      <p className="text-xs text-gray-500 text-center mb-6">
        Adjust K to explore how speculation depth affects performance
      </p>

      <div className="max-w-lg mx-auto">
        {/* Slider */}
        <div className="flex items-center gap-4 mb-2">
          <span className="text-sm text-gray-500 font-mono w-8">K=1</span>
          <input
            type="range"
            min={1}
            max={8}
            value={k}
            onChange={(e) => setK(parseInt(e.target.value))}
            className="flex-1 h-2 bg-gray-800 rounded-full appearance-none cursor-pointer
                       [&::-webkit-slider-thumb]:appearance-none [&::-webkit-slider-thumb]:w-5 [&::-webkit-slider-thumb]:h-5
                       [&::-webkit-slider-thumb]:rounded-full [&::-webkit-slider-thumb]:bg-cyan-500
                       [&::-webkit-slider-thumb]:shadow-lg [&::-webkit-slider-thumb]:shadow-cyan-500/30
                       [&::-webkit-slider-thumb]:cursor-pointer"
            aria-label="Speculation depth K"
          />
          <span className="text-sm text-gray-500 font-mono w-8">K=8</span>
        </div>
        <div className="text-center mb-6">
          <span className="text-xs text-gray-600">
            K = {k} · {labels[k]}
          </span>
        </div>

        {/* Token Visualization */}
        <div className="flex items-center justify-center gap-1.5 mb-6">
          {Array.from({ length: 8 }).map((_, i) => {
            let status = "inactive";
            if (i < k) {
              status = i < acceptedCount ? "accepted" : "rejected";
            }
            return (
              <motion.div
                key={i}
                animate={{
                  opacity: i < k ? 1 : 0.15,
                  scale: i < k ? 1 : 0.8,
                }}
                transition={{ duration: 0.2 }}
                className={`w-10 h-10 rounded-lg flex items-center justify-center text-xs font-mono border transition-colors duration-200 ${
                  status === "accepted"
                    ? "bg-emerald-500/15 text-emerald-400 border-emerald-500/30"
                    : status === "rejected"
                      ? "bg-rose-500/15 text-rose-400 border-rose-500/30"
                      : "bg-gray-900 text-gray-700 border-gray-800"
                }`}
              >
                {i < k ? (status === "accepted" ? "✓" : "✗") : ""}
              </motion.div>
            );
          })}
        </div>

        {/* Stats Grid */}
        <div className="grid grid-cols-3 gap-3 mb-5">
          <motion.div
            key={`speed-${k}`}
            initial={{ scale: 0.95 }}
            animate={{ scale: 1 }}
            className="text-center p-3 rounded-xl bg-white/[.03] border border-white/[.05]"
          >
            <div className="text-xl font-bold text-cyan-400 font-mono">
              {effectiveSpeedup.toFixed(1)}×
            </div>
            <div className="text-[10px] text-gray-500 mt-1 uppercase tracking-wider">
              Speedup
            </div>
          </motion.div>
          <motion.div
            key={`rate-${k}`}
            initial={{ scale: 0.95 }}
            animate={{ scale: 1 }}
            className="text-center p-3 rounded-xl bg-white/[.03] border border-white/[.05]"
          >
            <div className="text-xl font-bold text-emerald-400 font-mono">
              {expectedTokens.toFixed(1)}
            </div>
            <div className="text-[10px] text-gray-500 mt-1 uppercase tracking-wider">
              Tokens/Pass
            </div>
          </motion.div>
          <motion.div
            key={`waste-${k}`}
            initial={{ scale: 0.95 }}
            animate={{ scale: 1 }}
            className="text-center p-3 rounded-xl bg-white/[.03] border border-white/[.05]"
          >
            <div className="text-xl font-bold text-rose-400 font-mono">
              {Math.max(0, k - expectedTokens + 1).toFixed(1)}
            </div>
            <div className="text-[10px] text-gray-500 mt-1 uppercase tracking-wider">
              Wasted Tokens
            </div>
          </motion.div>
        </div>

        {/* Insight */}
        <div className="p-3 rounded-lg bg-cyan-500/[.04] border border-cyan-500/10">
          <p className="text-xs text-gray-400 leading-relaxed">
            <span className="text-cyan-400 font-medium">Trade-off: </span>
            {k <= 2
              ? "Low K gives high acceptance rates but limited speedup. Each forward pass of the target model is underutilized."
              : k <= 5
                ? "K=4 is the sweet spot for most models. Good speedup with manageable waste from rejected tokens."
                : "High K speculates aggressively. Diminishing returns as the draft model becomes less accurate further into the future."}
          </p>
        </div>
      </div>
    </div>
  );
};

// ═══════════════════════════════════════════════════════════════
//  WHY IT WORKS — Memory Bandwidth Visualization
// ═══════════════════════════════════════════════════════════════

const WhyItWorks = () => (
  <div className="grid md:grid-cols-2 gap-4 sm:gap-6">
    {/* Standard Decoding */}
    <div className="p-5 sm:p-6 rounded-xl bg-void-950 border border-white/[.06]">
      <h4 className="text-sm font-semibold text-gray-400 mb-5 flex items-center gap-2">
        <span className="text-base">🐢</span>
        Standard: 1 Token per Pass
      </h4>
      <div className="space-y-2.5">
        {[1, 2, 3, 4].map((i) => (
          <div key={i} className="flex items-center gap-2.5">
            <span className="text-[10px] text-gray-600 w-12 font-mono">
              Pass {i}
            </span>
            <div className="flex-1 h-6 rounded-md bg-gray-900 flex overflow-hidden">
              <div className="flex-[95] flex items-center justify-center bg-amber-500/[.12] border-r border-amber-500/20">
                <span className="text-[9px] text-amber-500/60 font-medium">
                  Memory Wait
                </span>
              </div>
              <div className="flex-[5] flex items-center justify-center bg-cyan-500/20">
                <span className="text-[9px] text-cyan-400/80">⚡</span>
              </div>
            </div>
            <span className="text-[10px] text-gray-600 w-12 text-right font-mono">
              1 tok
            </span>
          </div>
        ))}
      </div>
      <p className="text-xs text-gray-600 text-right mt-3 font-mono">
        4 passes → 4 tokens
      </p>
    </div>

    {/* Speculative Decoding */}
    <div className="p-5 sm:p-6 rounded-xl bg-void-950 border border-cyan-500/15">
      <h4 className="text-sm font-semibold text-cyan-400 mb-5 flex items-center gap-2">
        <span className="text-base">⚡</span>
        Speculative: ~4 Tokens per Pass
      </h4>
      <div className="space-y-2.5">
        <div className="flex items-center gap-2.5">
          <span className="text-[10px] text-gray-600 w-12 font-mono">
            Pass 1
          </span>
          <div className="flex-1 h-6 rounded-md bg-gray-900 flex overflow-hidden">
            <div className="flex-[95] flex items-center justify-center bg-amber-500/[.12] border-r border-amber-500/20">
              <span className="text-[9px] text-amber-500/60 font-medium">
                Same memory wait
              </span>
            </div>
            <div className="flex-[5] flex items-center justify-center bg-cyan-500/20">
              <span className="text-[9px] text-cyan-400/80">⚡</span>
            </div>
          </div>
          <span className="text-[10px] text-emerald-500 w-12 text-right font-mono font-bold">
            ~4 tok
          </span>
        </div>
      </div>
      <p className="text-xs text-emerald-600 text-right mt-3 font-mono">
        1 pass → ~4 tokens
      </p>

      <div className="mt-5 p-4 rounded-lg bg-cyan-500/[.05] border border-cyan-500/10">
        <p className="text-xs text-gray-400 leading-relaxed">
          <span className="text-cyan-400 font-semibold">Key insight: </span>
          GPUs spend ~95% of inference time moving model weights from memory.
          The actual matrix math is nearly free. Verifying 4 tokens in parallel
          costs almost the same as generating 1 — because we&apos;re
          bottlenecked by memory bandwidth, not compute.
        </p>
      </div>
    </div>
  </div>
);

// ═══════════════════════════════════════════════════════════════
//  MAIN TECHNOLOGY COMPONENT
// ═══════════════════════════════════════════════════════════════

const Technology = () => {
  return (
    <section
      id="technology"
      className="py-20 sm:py-24 bg-void-900 relative overflow-hidden"
    >
      {/* DNA Helix Background */}
      <div className="helix-bg-section right" aria-hidden="true" />

      <div className="max-w-6xl mx-auto px-4 sm:px-6 relative z-10">
        {/* ── Section Header ── */}
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          whileInView={{ opacity: 1, y: 0 }}
          viewport={{ once: true }}
          className="text-center mb-14"
        >
          <div className="inline-flex items-center px-3 py-1 rounded-full bg-cyan-500/10 border border-cyan-500/20 text-cyan-400 text-xs font-medium mb-4">
            Interactive Demo
          </div>
          <h2 className="text-3xl sm:text-4xl font-bold text-white mb-4">
            How Speculative Decoding Works
          </h2>
          <p className="text-gray-400 max-w-2xl mx-auto text-sm sm:text-base">
            Instead of generating tokens one at a time, speculate multiple
            tokens and verify them in parallel. Trade cheap compute for massive
            latency savings.
          </p>
        </motion.div>

        {/* ── Interactive Pipeline ── */}
        <motion.div
          initial={{ opacity: 0, y: 30 }}
          whileInView={{ opacity: 1, y: 0 }}
          viewport={{ once: true }}
          transition={{ delay: 0.1 }}
          className="mb-20"
        >
          <PipelineSimulator />
        </motion.div>

        {/* ── Speed Race Comparison ── */}
        <motion.div
          initial={{ opacity: 0, y: 30 }}
          whileInView={{ opacity: 1, y: 0 }}
          viewport={{ once: true }}
          className="mb-16"
        >
          <div className="text-center mb-8">
            <h3 className="text-xl sm:text-2xl font-bold text-white mb-2">
              See the Difference
            </h3>
            <p className="text-gray-500 text-sm">
              Watch both approaches generate the same text — side by side
            </p>
          </div>
          <DecodingRace />
        </motion.div>

        {/* ── K-Depth Explorer ── */}
        <motion.div
          initial={{ opacity: 0, y: 30 }}
          whileInView={{ opacity: 1, y: 0 }}
          viewport={{ once: true }}
          className="mb-16"
        >
          <DepthExplorer />
        </motion.div>

        {/* ── Why It Works ── */}
        <motion.div
          initial={{ opacity: 0, y: 30 }}
          whileInView={{ opacity: 1, y: 0 }}
          viewport={{ once: true }}
        >
          <div className="text-center mb-8">
            <h3 className="text-xl sm:text-2xl font-bold text-white mb-2">
              Why This Works
            </h3>
            <p className="text-gray-500 text-sm">
              LLM inference is memory-bound, not compute-bound
            </p>
          </div>
          <WhyItWorks />
        </motion.div>
      </div>
    </section>
  );
};

export default Technology;
