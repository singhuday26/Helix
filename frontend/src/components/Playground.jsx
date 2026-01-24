import React, { useState, useRef } from "react";
import { motion } from "framer-motion";

const Playground = () => {
  const [prompt, setPrompt] = useState("");
  const [output, setOutput] = useState("");
  const [isStreaming, setIsStreaming] = useState(false);
  const [activeTab, setActiveTab] = useState("speculative");
  const [config, setConfig] = useState({
    max_tokens: 100,
    temperature: 0.7,
    speculation_depth: 4,
  });
  const [metrics, setMetrics] = useState({
    tokens: 0,
    time: 0,
    tokensPerSecond: 0,
    acceptanceRate: null,
  });
  const [error, setError] = useState(null);
  const eventSourceRef = useRef(null);

  const presets = [
    {
      label: "Explain quantum computing",
      prompt: "Explain quantum computing in simple terms.",
    },
    {
      label: "Write a function",
      prompt: "Write a Python function to calculate fibonacci numbers.",
    },
    {
      label: "Summarize AI",
      prompt: "What is artificial intelligence and how does it work?",
    },
  ];

  const startGeneration = async () => {
    if (!prompt.trim()) {
      setError("Please enter a prompt");
      return;
    }

    setError(null);
    setOutput("");
    setIsStreaming(true);
    setMetrics({
      tokens: 0,
      time: 0,
      tokensPerSecond: 0,
      acceptanceRate: null,
    });

    try {
      if (eventSourceRef.current) {
        eventSourceRef.current.close();
      }

      const requestBody = {
        prompt: prompt,
        max_tokens: config.max_tokens,
        temperature: config.temperature,
        speculation_depth: config.speculation_depth,
        use_speculative: activeTab === "speculative",
      };

      const response = await fetch("/generate/stream", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(requestBody),
      });

      if (!response.ok) {
        throw new Error(`HTTP ${response.status}: ${response.statusText}`);
      }

      const reader = response.body.getReader();
      const decoder = new TextDecoder();
      let buffer = "";

      while (true) {
        const { done, value } = await reader.read();
        if (done) break;

        buffer += decoder.decode(value, { stream: true });
        const lines = buffer.split("\n");
        buffer = lines.pop() || "";

        for (const line of lines) {
          if (line.startsWith("data: ")) {
            try {
              const event = JSON.parse(line.slice(6));

              if (event.error) {
                setError(event.error);
                setIsStreaming(false);
                return;
              }

              if (event.is_final) {
                setIsStreaming(false);
                return;
              }

              setOutput((prev) => prev + event.token);
              setMetrics({
                tokens: event.index + 1,
                time: event.time_elapsed || 0,
                tokensPerSecond:
                  event.time_elapsed > 0
                    ? ((event.index + 1) / event.time_elapsed).toFixed(1)
                    : 0,
                acceptanceRate: event.acceptance_rate,
              });
            } catch (e) {
              // Skip malformed JSON
            }
          }
        }
      }
    } catch (err) {
      setError(err.message);
    } finally {
      setIsStreaming(false);
    }
  };

  const stopGeneration = () => {
    if (eventSourceRef.current) {
      eventSourceRef.current.close();
    }
    setIsStreaming(false);
  };

  return (
    <section id="playground" className="py-24 bg-void-950">
      <div className="max-w-6xl mx-auto px-6">
        {/* Header */}
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          whileInView={{ opacity: 1, y: 0 }}
          viewport={{ once: true }}
          className="text-center mb-12"
        >
          <h2 className="text-3xl sm:text-4xl font-bold text-white mb-4">
            Playground
          </h2>
          <p className="text-gray-400 max-w-2xl mx-auto">
            Test the inference engine directly. Compare speculative vs
            autoregressive decoding and see the performance difference.
          </p>
        </motion.div>

        <div className="grid lg:grid-cols-2 gap-6">
          {/* Input Panel */}
          <motion.div
            initial={{ opacity: 0, x: -20 }}
            whileInView={{ opacity: 1, x: 0 }}
            viewport={{ once: true }}
            className="space-y-4"
          >
            {/* Mode Tabs */}
            <div className="flex rounded-lg bg-white/5 p-1">
              {[
                { id: "speculative", label: "Speculative" },
                { id: "autoregressive", label: "Autoregressive" },
              ].map((tab) => (
                <button
                  key={tab.id}
                  onClick={() => setActiveTab(tab.id)}
                  disabled={isStreaming}
                  className={`flex-1 px-4 py-2 text-sm font-medium rounded-md transition-all duration-300 ${
                    activeTab === tab.id
                      ? "bg-white text-void-950 shadow-lg"
                      : "text-gray-400 hover:text-white hover:bg-white/5"
                  }`}
                >
                  {tab.label}
                </button>
              ))}
            </div>

            {/* Prompt Input */}
            <div className="rounded-xl bg-white/[0.02] border border-white/5 overflow-hidden">
              <div className="flex items-center justify-between px-4 py-3 border-b border-white/5">
                <span className="text-sm text-gray-400">Prompt</span>
                <div className="flex gap-2">
                  {presets.map((preset, i) => (
                    <button
                      key={i}
                      onClick={() => setPrompt(preset.prompt)}
                      disabled={isStreaming}
                      className="px-2 py-1 text-xs text-gray-500 hover:text-white bg-white/5 hover:bg-white/10 rounded hover:scale-105 transition-all duration-200"
                    >
                      {preset.label}
                    </button>
                  ))}
                </div>
              </div>
              <textarea
                value={prompt}
                onChange={(e) => setPrompt(e.target.value)}
                placeholder="Enter your prompt here..."
                disabled={isStreaming}
                className="w-full h-40 px-4 py-3 bg-transparent text-white placeholder-gray-600 resize-none focus:outline-none"
              />
            </div>

            {/* Settings */}
            <div className="grid grid-cols-3 gap-4">
              <div>
                <label className="block text-xs text-gray-500 mb-1">
                  Max Tokens
                </label>
                <input
                  type="number"
                  min="20"
                  max="500"
                  value={config.max_tokens}
                  onChange={(e) => {
                    const value = e.target.value;
                    // Allow empty or any number while typing
                    if (value === "" || !isNaN(parseInt(value))) {
                      setConfig({
                        ...config,
                        max_tokens: value === "" ? "" : parseInt(value),
                      });
                    }
                  }}
                  onBlur={(e) => {
                    // Validate on blur - enforce min/max
                    let value = parseInt(e.target.value);
                    if (isNaN(value) || value < 20) {
                      value = 50; // default
                    } else if (value > 500) {
                      value = 500;
                    }
                    setConfig({
                      ...config,
                      max_tokens: value,
                    });
                  }}
                  disabled={isStreaming}
                  className="w-full px-3 py-2 text-sm bg-white/5 border border-white/10 rounded-lg text-white focus:outline-none focus:border-helix-draft"
                />
              </div>
              <div>
                <label className="block text-xs text-gray-500 mb-1">
                  Temperature
                </label>
                <input
                  type="number"
                  step="0.1"
                  min="0"
                  max="2"
                  value={config.temperature}
                  onChange={(e) =>
                    setConfig({
                      ...config,
                      temperature: parseFloat(e.target.value) || 0.7,
                    })
                  }
                  disabled={isStreaming}
                  className="w-full px-3 py-2 text-sm bg-white/5 border border-white/10 rounded-lg text-white focus:outline-none focus:border-helix-draft"
                />
              </div>
              <div>
                <label className="block text-xs text-gray-500 mb-1">
                  Speculation Depth
                </label>
                <input
                  type="number"
                  min="1"
                  max="8"
                  value={config.speculation_depth}
                  onChange={(e) =>
                    setConfig({
                      ...config,
                      speculation_depth: parseInt(e.target.value) || 4,
                    })
                  }
                  disabled={isStreaming || activeTab !== "speculative"}
                  className="w-full px-3 py-2 text-sm bg-white/5 border border-white/10 rounded-lg text-white focus:outline-none focus:border-helix-draft disabled:opacity-50"
                />
              </div>
            </div>

            {/* Generate Button */}
            <button
              onClick={isStreaming ? stopGeneration : startGeneration}
              className={`w-full py-3 font-medium rounded-lg transition-all ${
                isStreaming
                  ? "bg-helix-reject text-white"
                  : "bg-white text-void-950 hover:bg-gray-100"
              }`}
            >
              {isStreaming ? "Stop Generation" : "Generate"}
            </button>

            {error && (
              <div className="px-4 py-3 rounded-lg bg-helix-reject/10 border border-helix-reject/30 text-helix-reject text-sm">
                {error}
              </div>
            )}
          </motion.div>

          {/* Output Panel */}
          <motion.div
            initial={{ opacity: 0, x: 20 }}
            whileInView={{ opacity: 1, x: 0 }}
            viewport={{ once: true }}
            className="space-y-4"
          >
            {/* Output Display */}
            <div className="rounded-xl bg-white/[0.02] border border-white/5 overflow-hidden">
              <div className="flex items-center justify-between px-4 py-3 border-b border-white/5">
                <span className="text-sm text-gray-400">Output</span>
                {isStreaming && (
                  <span className="flex items-center gap-2 text-xs text-helix-draft">
                    <span className="w-2 h-2 rounded-full bg-helix-draft animate-pulse" />
                    Streaming...
                  </span>
                )}
              </div>
              <div className="h-40 px-4 py-3 overflow-y-auto">
                {output ? (
                  <p className="text-white font-mono text-sm whitespace-pre-wrap leading-relaxed">
                    {output}
                    {isStreaming && (
                      <span className="inline-block w-2 h-4 ml-0.5 bg-helix-draft animate-pulse" />
                    )}
                  </p>
                ) : (
                  <p className="text-gray-600 text-sm italic">
                    Output will appear here...
                  </p>
                )}
              </div>
            </div>

            {/* Metrics */}
            <div className="grid grid-cols-4 gap-3">
              {[
                { label: "Tokens", value: metrics.tokens },
                { label: "Time", value: `${metrics.time.toFixed(2)}s` },
                { label: "Speed", value: `${metrics.tokensPerSecond}/s` },
                {
                  label: "Acceptance",
                  value:
                    metrics.acceptanceRate !== null
                      ? `${(metrics.acceptanceRate * 100).toFixed(0)}%`
                      : "—",
                },
              ].map((metric) => (
                <div
                  key={metric.label}
                  className="p-4 rounded-xl bg-white/[0.02] border border-white/5 text-center"
                >
                  <div className="text-xl font-bold text-white">
                    {metric.value}
                  </div>
                  <div className="text-xs text-gray-500">{metric.label}</div>
                </div>
              ))}
            </div>

            {/* Mode Indicator */}
            <div className="p-4 rounded-xl bg-gradient-to-r from-helix-draft/10 to-helix-verify/10 border border-white/5">
              <div className="flex items-center gap-3">
                <div
                  className={`w-3 h-3 rounded-full ${
                    activeTab === "speculative"
                      ? "bg-helix-draft"
                      : "bg-gray-500"
                  }`}
                />
                <div>
                  <div className="text-sm font-medium text-white">
                    {activeTab === "speculative"
                      ? "Speculative Decoding"
                      : "Autoregressive Decoding"}
                  </div>
                  <div className="text-xs text-gray-500">
                    {activeTab === "speculative"
                      ? `Draft model generates ${config.speculation_depth} tokens, target model verifies in parallel`
                      : "Standard token-by-token generation"}
                  </div>
                </div>
              </div>
            </div>
          </motion.div>
        </div>
      </div>
    </section>
  );
};

export default Playground;
