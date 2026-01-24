import React, { useState, useEffect, useRef, useCallback } from "react";
import { motion, AnimatePresence } from "framer-motion";
import { Link } from "react-router-dom";
import Navbar from "../components/Navbar";

// Simulated token generation for demo purposes
const SAMPLE_TOKENS = [
  "The",
  " quick",
  " brown",
  " fox",
  " jumps",
  " over",
  " the",
  " lazy",
  " dog",
  ".",
  " This",
  " sentence",
  " demonstrates",
  " the",
  " difference",
  " between",
  " standard",
  " and",
  " speculative",
  " decoding",
  " methods",
  ".",
];

const DRAFT_ACCEPTANCE_RATE = 0.75; // 75% of draft tokens are accepted

const ComparisonPage = () => {
  const [isRunning, setIsRunning] = useState(false);
  const [hasCompleted, setHasCompleted] = useState(false);

  // Autoregressive state
  const [autoTokens, setAutoTokens] = useState([]);
  const [autoTime, setAutoTime] = useState(0);
  const [autoTokensPerSec, setAutoTokensPerSec] = useState(0);

  // Speculative state
  const [specTokens, setSpecTokens] = useState([]);
  const [specTime, setSpecTime] = useState(0);
  const [specTokensPerSec, setSpecTokensPerSec] = useState(0);
  const [draftTokens, setDraftTokens] = useState([]);
  const [verifyingIndex, setVerifyingIndex] = useState(-1);
  const [acceptedCount, setAcceptedCount] = useState(0);
  const [rejectedCount, setRejectedCount] = useState(0);

  // Refs for animation control
  const autoIntervalRef = useRef(null);
  const specIntervalRef = useRef(null);
  const startTimeRef = useRef(null);

  const AUTOREGRESSIVE_DELAY = 300; // ms per token (slow)
  const SPECULATIVE_DELAY = 80; // ms per token (fast due to batching)
  const DRAFT_BATCH_SIZE = 4;

  const resetDemo = useCallback(() => {
    setAutoTokens([]);
    setAutoTime(0);
    setAutoTokensPerSec(0);
    setSpecTokens([]);
    setSpecTime(0);
    setSpecTokensPerSec(0);
    setDraftTokens([]);
    setVerifyingIndex(-1);
    setAcceptedCount(0);
    setRejectedCount(0);
    setHasCompleted(false);

    if (autoIntervalRef.current) clearInterval(autoIntervalRef.current);
    if (specIntervalRef.current) clearInterval(specIntervalRef.current);
  }, []);

  const runAutoregressive = useCallback(() => {
    let tokenIndex = 0;
    const startTime = Date.now();

    autoIntervalRef.current = setInterval(() => {
      if (tokenIndex >= SAMPLE_TOKENS.length) {
        clearInterval(autoIntervalRef.current);
        return;
      }

      setAutoTokens((prev) => [
        ...prev,
        {
          text: SAMPLE_TOKENS[tokenIndex],
          status: "generated",
          index: tokenIndex,
        },
      ]);

      const elapsed = (Date.now() - startTime) / 1000;
      setAutoTime(elapsed);
      setAutoTokensPerSec((tokenIndex + 1) / elapsed);

      tokenIndex++;
    }, AUTOREGRESSIVE_DELAY);
  }, []);

  const runSpeculative = useCallback(() => {
    let tokenIndex = 0;
    let accepted = 0;
    let rejected = 0;
    const startTime = Date.now();

    const processBatch = () => {
      if (tokenIndex >= SAMPLE_TOKENS.length) {
        setDraftTokens([]);
        setVerifyingIndex(-1);
        return;
      }

      // Draft phase: generate batch of draft tokens
      const batchEnd = Math.min(
        tokenIndex + DRAFT_BATCH_SIZE,
        SAMPLE_TOKENS.length,
      );
      const draftBatch = [];

      for (let i = tokenIndex; i < batchEnd; i++) {
        draftBatch.push({
          text: SAMPLE_TOKENS[i],
          status: "draft",
          index: i,
        });
      }

      setDraftTokens(draftBatch);

      // Verify phase: check each draft token
      let verifyIndex = 0;
      const verifyInterval = setInterval(() => {
        if (verifyIndex >= draftBatch.length) {
          clearInterval(verifyInterval);
          setDraftTokens([]);
          setVerifyingIndex(-1);

          // Schedule next batch
          setTimeout(processBatch, SPECULATIVE_DELAY);
          return;
        }

        setVerifyingIndex(verifyIndex);

        // Simulate acceptance/rejection
        const isAccepted = Math.random() < DRAFT_ACCEPTANCE_RATE;
        const currentToken = draftBatch[verifyIndex];

        if (!currentToken) {
          clearInterval(verifyInterval);
          return;
        }

        if (isAccepted) {
          accepted++;
          setAcceptedCount(accepted);
          setSpecTokens((prev) => [
            ...prev,
            {
              text: currentToken.text || "",
              status: "accepted",
              index: tokenIndex,
            },
          ]);
          tokenIndex++;
        } else {
          rejected++;
          setRejectedCount(rejected);
          // On rejection, we still add the correct token (target model generates it)
          setSpecTokens((prev) => [
            ...prev,
            {
              text: currentToken.text || "",
              status: "corrected",
              index: tokenIndex,
            },
          ]);
          tokenIndex++;
          // Stop verifying rest of batch on rejection
          clearInterval(verifyInterval);
          setDraftTokens([]);
          setVerifyingIndex(-1);
          setTimeout(processBatch, SPECULATIVE_DELAY);
          return;
        }

        const elapsed = (Date.now() - startTime) / 1000;
        setSpecTime(elapsed);
        setSpecTokensPerSec(tokenIndex / elapsed);

        verifyIndex++;
      }, SPECULATIVE_DELAY / 2);
    };

    processBatch();
  }, []);

  const startDemo = useCallback(() => {
    resetDemo();
    setIsRunning(true);
    startTimeRef.current = Date.now();

    // Start both simultaneously
    runAutoregressive();
    runSpeculative();
  }, [resetDemo, runAutoregressive, runSpeculative]);

  // Check completion
  useEffect(() => {
    if (
      autoTokens.length >= SAMPLE_TOKENS.length &&
      specTokens.length >= SAMPLE_TOKENS.length
    ) {
      setIsRunning(false);
      setHasCompleted(true);
    }
  }, [autoTokens.length, specTokens.length]);

  // Cleanup on unmount
  useEffect(() => {
    return () => {
      if (autoIntervalRef.current) clearInterval(autoIntervalRef.current);
      if (specIntervalRef.current) clearInterval(specIntervalRef.current);
    };
  }, []);

  const speedup =
    autoTime > 0 && specTime > 0 ? (autoTime / specTime).toFixed(2) : "—";

  return (
    <div className="min-h-screen bg-void-950 relative overflow-hidden">
      {/* Global DNA Helix Background Decoration */}
      <div className="helix-bg-decoration" aria-hidden="true" />

      <Navbar />

      {/* Main Content */}
      <main className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-24 relative z-10">
        {/* Title Section */}
        <motion.div
          className="text-center mb-12"
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
        >
          <h1 className="text-4xl sm:text-5xl font-bold text-white mb-4">
            Decoding Comparison
          </h1>
          <p className="text-lg max-w-2xl mx-auto text-gray-400">
            Watch the difference in real-time. See how speculative decoding
            achieves faster inference by predicting and verifying tokens in
            parallel.
          </p>
        </motion.div>

        {/* Control Panel */}
        <motion.div
          className="flex justify-center gap-4 mb-8"
          initial={{ opacity: 0 }}
          animate={{ opacity: 1 }}
          transition={{ delay: 0.2 }}
        >
          <button
            onClick={startDemo}
            disabled={isRunning}
            className={`px-6 py-3 font-medium rounded-lg transition-all flex items-center gap-2 ${
              isRunning
                ? "bg-white/10 text-gray-400 cursor-not-allowed"
                : "bg-white text-void-950 hover:bg-gray-100"
            }`}
          >
            {isRunning ? (
              <>
                <div className="w-4 h-4 border-2 border-current border-t-transparent rounded-full animate-spin"></div>
                Running...
              </>
            ) : (
              <>
                <svg
                  className="w-5 h-5"
                  fill="none"
                  viewBox="0 0 24 24"
                  stroke="currentColor"
                >
                  <path
                    strokeLinecap="round"
                    strokeLinejoin="round"
                    strokeWidth={2}
                    d="M14.752 11.168l-3.197-2.132A1 1 0 0010 9.87v4.263a1 1 0 001.555.832l3.197-2.132a1 1 0 000-1.664z"
                  />
                  <path
                    strokeLinecap="round"
                    strokeLinejoin="round"
                    strokeWidth={2}
                    d="M21 12a9 9 0 11-18 0 9 9 0 0118 0z"
                  />
                </svg>
                Start Comparison
              </>
            )}
          </button>
          <button
            onClick={resetDemo}
            className="btn-secondary flex items-center gap-2"
          >
            <svg
              className="w-5 h-5"
              fill="none"
              viewBox="0 0 24 24"
              stroke="currentColor"
            >
              <path
                strokeLinecap="round"
                strokeLinejoin="round"
                strokeWidth={2}
                d="M4 4v5h.582m15.356 2A8.001 8.001 0 004.582 9m0 0H9m11 11v-5h-.581m0 0a8.003 8.003 0 01-15.357-2m15.357 2H15"
              />
            </svg>
            Reset
          </button>
        </motion.div>

        {/* Comparison Terminals */}
        <div className="grid lg:grid-cols-2 gap-6 mb-8">
          {/* Autoregressive Terminal */}
          <motion.div
            className="rounded-2xl overflow-hidden"
            style={{
              background: "rgba(10, 15, 26, 0.8)",
              border: "1px solid rgba(107, 114, 128, 0.3)",
            }}
            initial={{ opacity: 0, x: -30 }}
            animate={{ opacity: 1, x: 0 }}
            transition={{ delay: 0.3 }}
          >
            {/* Terminal Header */}
            <div
              className="flex items-center justify-between px-4 py-3"
              style={{
                background: "rgba(107, 114, 128, 0.1)",
                borderBottom: "1px solid rgba(107, 114, 128, 0.2)",
              }}
            >
              <div className="flex items-center gap-3">
                <div className="flex gap-1.5">
                  <span
                    className="w-3 h-3 rounded-full"
                    style={{ background: "#6b7280" }}
                  ></span>
                  <span
                    className="w-3 h-3 rounded-full"
                    style={{ background: "#6b7280" }}
                  ></span>
                  <span
                    className="w-3 h-3 rounded-full"
                    style={{ background: "#6b7280" }}
                  ></span>
                </div>
                <span
                  className="text-sm font-medium"
                  style={{ color: "#9ca3af" }}
                >
                  🐢 Autoregressive Decoding
                </span>
              </div>
              <span className="status-draft text-xs">STANDARD</span>
            </div>

            {/* Terminal Body */}
            <div className="p-4 min-h-[300px]">
              <div
                className="font-mono text-sm leading-relaxed min-h-[200px]"
                style={{ color: "#9ca3af" }}
              >
                {autoTokens.length === 0 && !isRunning && (
                  <span style={{ color: "#6b7280" }}>Waiting to start...</span>
                )}
                {autoTokens.map((token, i) => (
                  <motion.span
                    key={i}
                    initial={{ opacity: 0, y: 5 }}
                    animate={{ opacity: 1, y: 0 }}
                    style={{ color: "#d1d5db" }}
                  >
                    {token?.text || ""}
                  </motion.span>
                ))}
                {isRunning && autoTokens.length < SAMPLE_TOKENS.length && (
                  <span
                    className="inline-block w-2 h-4 ml-1 animate-pulse"
                    style={{ background: "#6b7280" }}
                  ></span>
                )}
              </div>

              {/* Metrics */}
              <div
                className="mt-4 pt-4 grid grid-cols-3 gap-4"
                style={{ borderTop: "1px solid rgba(107, 114, 128, 0.2)" }}
              >
                <div>
                  <div
                    className="text-xs uppercase tracking-wider mb-1"
                    style={{ color: "#6b7280" }}
                  >
                    Tokens
                  </div>
                  <div
                    className="text-xl font-bold"
                    style={{ color: "#9ca3af" }}
                  >
                    {autoTokens.length}
                  </div>
                </div>
                <div>
                  <div
                    className="text-xs uppercase tracking-wider mb-1"
                    style={{ color: "#6b7280" }}
                  >
                    Time
                  </div>
                  <div
                    className="text-xl font-bold"
                    style={{ color: "#9ca3af" }}
                  >
                    {autoTime.toFixed(2)}s
                  </div>
                </div>
                <div>
                  <div
                    className="text-xs uppercase tracking-wider mb-1"
                    style={{ color: "#6b7280" }}
                  >
                    Tokens/sec
                  </div>
                  <div
                    className="text-xl font-bold"
                    style={{ color: "#9ca3af" }}
                  >
                    {autoTokensPerSec.toFixed(1)}
                  </div>
                </div>
              </div>
            </div>
          </motion.div>

          {/* Speculative Terminal */}
          <motion.div
            className="rounded-2xl overflow-hidden"
            style={{
              background: "rgba(10, 15, 26, 0.8)",
              border: "1px solid rgba(6, 182, 212, 0.3)",
            }}
            initial={{ opacity: 0, x: 30 }}
            animate={{ opacity: 1, x: 0 }}
            transition={{ delay: 0.3 }}
          >
            {/* Terminal Header */}
            <div
              className="flex items-center justify-between px-4 py-3"
              style={{
                background: "rgba(6, 182, 212, 0.05)",
                borderBottom: "1px solid rgba(6, 182, 212, 0.2)",
              }}
            >
              <div className="flex items-center gap-3">
                <div className="flex gap-1.5">
                  <span
                    className="w-3 h-3 rounded-full"
                    style={{ background: "#f43f5e" }}
                  ></span>
                  <span
                    className="w-3 h-3 rounded-full"
                    style={{ background: "#f59e0b" }}
                  ></span>
                  <span
                    className="w-3 h-3 rounded-full"
                    style={{ background: "#22c55e" }}
                  ></span>
                </div>
                <span
                  className="text-sm font-medium"
                  style={{ color: "#67e8f9" }}
                >
                  ⚡ Speculative Decoding
                </span>
              </div>
              <span className="status-active text-xs">HELIX</span>
            </div>

            {/* Terminal Body */}
            <div className="p-4 min-h-[300px]">
              {/* Draft tokens preview */}
              {draftTokens.length > 0 && (
                <div
                  className="mb-3 p-2 rounded-lg"
                  style={{
                    background: "rgba(6, 182, 212, 0.1)",
                    border: "1px dashed rgba(6, 182, 212, 0.3)",
                  }}
                >
                  <div
                    className="text-xs uppercase tracking-wider mb-2"
                    style={{ color: "#06b6d4" }}
                  >
                    Draft Model Predictions:
                  </div>
                  <div className="font-mono text-sm flex flex-wrap gap-1">
                    {draftTokens.map((token, i) => (
                      <span
                        key={i}
                        className="px-2 py-0.5 rounded transition-all"
                        style={{
                          background:
                            verifyingIndex === i
                              ? "rgba(6, 182, 212, 0.3)"
                              : "rgba(6, 182, 212, 0.1)",
                          border:
                            verifyingIndex === i
                              ? "1px solid #06b6d4"
                              : "1px solid transparent",
                          color: "#67e8f9",
                        }}
                      >
                        {token?.text || ""}
                        {verifyingIndex === i && (
                          <span className="ml-1 text-xs">🔍</span>
                        )}
                      </span>
                    ))}
                  </div>
                </div>
              )}

              <div className="font-mono text-sm leading-relaxed min-h-[150px]">
                {specTokens.length === 0 && !isRunning && (
                  <span style={{ color: "#6b7280" }}>Waiting to start...</span>
                )}
                {specTokens.map((token, i) => (
                  <motion.span
                    key={i}
                    initial={{ opacity: 0, scale: 0.8 }}
                    animate={{ opacity: 1, scale: 1 }}
                    style={{
                      color:
                        token?.status === "accepted" ? "#22c55e" : "#f59e0b",
                    }}
                  >
                    {token?.text || ""}
                  </motion.span>
                ))}
                {isRunning && specTokens.length < SAMPLE_TOKENS.length && (
                  <span
                    className="inline-block w-2 h-4 ml-1 animate-pulse"
                    style={{ background: "#06b6d4" }}
                  ></span>
                )}
              </div>

              {/* Metrics */}
              <div
                className="mt-4 pt-4 grid grid-cols-3 gap-4"
                style={{ borderTop: "1px solid rgba(6, 182, 212, 0.2)" }}
              >
                <div>
                  <div
                    className="text-xs uppercase tracking-wider mb-1"
                    style={{ color: "#6b7280" }}
                  >
                    Tokens
                  </div>
                  <div
                    className="text-xl font-bold"
                    style={{ color: "#06b6d4" }}
                  >
                    {specTokens.length}
                  </div>
                </div>
                <div>
                  <div
                    className="text-xs uppercase tracking-wider mb-1"
                    style={{ color: "#6b7280" }}
                  >
                    Time
                  </div>
                  <div
                    className="text-xl font-bold"
                    style={{ color: "#10b981" }}
                  >
                    {specTime.toFixed(2)}s
                  </div>
                </div>
                <div>
                  <div
                    className="text-xs uppercase tracking-wider mb-1"
                    style={{ color: "#6b7280" }}
                  >
                    Tokens/sec
                  </div>
                  <div
                    className="text-xl font-bold"
                    style={{ color: "#22c55e" }}
                  >
                    {specTokensPerSec.toFixed(1)}
                  </div>
                </div>
              </div>

              {/* Acceptance Stats */}
              <div className="mt-3 flex gap-4">
                <div className="flex items-center gap-2">
                  <span
                    className="w-2 h-2 rounded-full"
                    style={{ background: "#22c55e" }}
                  ></span>
                  <span className="text-xs" style={{ color: "#6b7280" }}>
                    Accepted: {acceptedCount}
                  </span>
                </div>
                <div className="flex items-center gap-2">
                  <span
                    className="w-2 h-2 rounded-full"
                    style={{ background: "#f59e0b" }}
                  ></span>
                  <span className="text-xs" style={{ color: "#6b7280" }}>
                    Corrected: {rejectedCount}
                  </span>
                </div>
              </div>
            </div>
          </motion.div>
        </div>

        {/* Results Summary */}
        <AnimatePresence>
          {hasCompleted && (
            <motion.div
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              exit={{ opacity: 0 }}
              className="rounded-2xl p-8 text-center"
              style={{
                background:
                  "linear-gradient(135deg, rgba(6, 182, 212, 0.1), rgba(16, 185, 129, 0.1))",
                border: "1px solid rgba(6, 182, 212, 0.3)",
              }}
            >
              <h2 className="text-2xl font-bold mb-6 gradient-text">Results</h2>

              <div className="grid sm:grid-cols-4 gap-6 max-w-3xl mx-auto">
                <div className="helix-metric">
                  <div
                    className="text-4xl font-bold mb-2"
                    style={{ color: "#06b6d4" }}
                  >
                    {speedup}x
                  </div>
                  <div className="text-sm" style={{ color: "#6b7280" }}>
                    Speedup
                  </div>
                </div>

                <div className="helix-metric">
                  <div
                    className="text-4xl font-bold mb-2"
                    style={{ color: "#10b981" }}
                  >
                    {autoTime > 0
                      ? ((1 - specTime / autoTime) * 100).toFixed(0)
                      : 0}
                    %
                  </div>
                  <div className="text-sm" style={{ color: "#6b7280" }}>
                    Time Saved
                  </div>
                </div>

                <div className="helix-metric">
                  <div
                    className="text-4xl font-bold mb-2"
                    style={{ color: "#22c55e" }}
                  >
                    {acceptedCount + rejectedCount > 0
                      ? (
                          (acceptedCount / (acceptedCount + rejectedCount)) *
                          100
                        ).toFixed(0)
                      : 0}
                    %
                  </div>
                  <div className="text-sm" style={{ color: "#6b7280" }}>
                    Acceptance Rate
                  </div>
                </div>

                <div className="helix-metric">
                  <div
                    className="text-4xl font-bold mb-2"
                    style={{ color: "#67e8f9" }}
                  >
                    100%
                  </div>
                  <div className="text-sm" style={{ color: "#6b7280" }}>
                    Quality Preserved
                  </div>
                </div>
              </div>

              <p
                className="mt-6 text-sm max-w-2xl mx-auto"
                style={{ color: "#9ca3af" }}
              >
                Speculative decoding achieved{" "}
                <span style={{ color: "#06b6d4" }}>{speedup}x speedup</span>{" "}
                while maintaining identical output quality. The draft model
                correctly predicted{" "}
                <span style={{ color: "#22c55e" }}>{acceptedCount}</span>{" "}
                tokens, with only{" "}
                <span style={{ color: "#f59e0b" }}>{rejectedCount}</span>{" "}
                requiring correction.
              </p>
            </motion.div>
          )}
        </AnimatePresence>

        {/* How It Works Section */}
        <motion.div
          className="mt-12 grid md:grid-cols-2 gap-8"
          initial={{ opacity: 0 }}
          animate={{ opacity: 1 }}
          transition={{ delay: 0.5 }}
        >
          {/* Autoregressive Explanation */}
          <div className="card">
            <h3 className="text-xl font-bold mb-4" style={{ color: "#9ca3af" }}>
              🐢 Autoregressive Decoding
            </h3>
            <div className="space-y-4">
              <div className="flex gap-3">
                <div
                  className="w-8 h-8 rounded-full flex items-center justify-center flex-shrink-0"
                  style={{ background: "rgba(107, 114, 128, 0.2)" }}
                >
                  <span className="text-sm">1</span>
                </div>
                <div>
                  <div
                    className="font-medium mb-1"
                    style={{ color: "#d1d5db" }}
                  >
                    Generate One Token
                  </div>
                  <div className="text-sm" style={{ color: "#6b7280" }}>
                    The model processes the entire context to predict a single
                    token.
                  </div>
                </div>
              </div>
              <div className="flex gap-3">
                <div
                  className="w-8 h-8 rounded-full flex items-center justify-center flex-shrink-0"
                  style={{ background: "rgba(107, 114, 128, 0.2)" }}
                >
                  <span className="text-sm">2</span>
                </div>
                <div>
                  <div
                    className="font-medium mb-1"
                    style={{ color: "#d1d5db" }}
                  >
                    Append to Context
                  </div>
                  <div className="text-sm" style={{ color: "#6b7280" }}>
                    The new token is added to the sequence.
                  </div>
                </div>
              </div>
              <div className="flex gap-3">
                <div
                  className="w-8 h-8 rounded-full flex items-center justify-center flex-shrink-0"
                  style={{ background: "rgba(107, 114, 128, 0.2)" }}
                >
                  <span className="text-sm">3</span>
                </div>
                <div>
                  <div
                    className="font-medium mb-1"
                    style={{ color: "#d1d5db" }}
                  >
                    Repeat
                  </div>
                  <div className="text-sm" style={{ color: "#6b7280" }}>
                    Process repeats for each token. Memory bandwidth becomes the
                    bottleneck.
                  </div>
                </div>
              </div>
            </div>
          </div>

          {/* Speculative Explanation */}
          <div
            className="card"
            style={{ borderColor: "rgba(6, 182, 212, 0.3)" }}
          >
            <h3 className="text-xl font-bold mb-4" style={{ color: "#67e8f9" }}>
              ⚡ Speculative Decoding
            </h3>
            <div className="space-y-4">
              <div className="flex gap-3">
                <div
                  className="w-8 h-8 rounded-full flex items-center justify-center flex-shrink-0"
                  style={{ background: "rgba(6, 182, 212, 0.2)" }}
                >
                  <span className="text-sm" style={{ color: "#06b6d4" }}>
                    1
                  </span>
                </div>
                <div>
                  <div
                    className="font-medium mb-1"
                    style={{ color: "#d1d5db" }}
                  >
                    Draft Multiple Tokens
                  </div>
                  <div className="text-sm" style={{ color: "#6b7280" }}>
                    A small, fast draft model predicts K tokens ahead (e.g.,
                    K=4).
                  </div>
                </div>
              </div>
              <div className="flex gap-3">
                <div
                  className="w-8 h-8 rounded-full flex items-center justify-center flex-shrink-0"
                  style={{ background: "rgba(16, 185, 129, 0.2)" }}
                >
                  <span className="text-sm" style={{ color: "#10b981" }}>
                    2
                  </span>
                </div>
                <div>
                  <div
                    className="font-medium mb-1"
                    style={{ color: "#d1d5db" }}
                  >
                    Verify in Parallel
                  </div>
                  <div className="text-sm" style={{ color: "#6b7280" }}>
                    Target model verifies all K tokens in a single forward pass.
                  </div>
                </div>
              </div>
              <div className="flex gap-3">
                <div
                  className="w-8 h-8 rounded-full flex items-center justify-center flex-shrink-0"
                  style={{ background: "rgba(34, 197, 94, 0.2)" }}
                >
                  <span className="text-sm" style={{ color: "#22c55e" }}>
                    3
                  </span>
                </div>
                <div>
                  <div
                    className="font-medium mb-1"
                    style={{ color: "#d1d5db" }}
                  >
                    Accept or Correct
                  </div>
                  <div className="text-sm" style={{ color: "#6b7280" }}>
                    Accepted tokens are kept. Rejected tokens are corrected.
                    Result is mathematically identical.
                  </div>
                </div>
              </div>
            </div>
          </div>
        </motion.div>
      </main>
    </div>
  );
};

export default ComparisonPage;
