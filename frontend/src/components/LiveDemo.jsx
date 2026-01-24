import React, { useState, useRef, useEffect } from "react";
import { motion } from "framer-motion";

const LiveDemo = () => {
  const [prompt, setPrompt] = useState("");
  const [output, setOutput] = useState("");
  const [isStreaming, setIsStreaming] = useState(false);
  const [metrics, setMetrics] = useState({
    tokensGenerated: 0,
    timeElapsed: 0,
    acceptanceRate: null,
    tokensPerSecond: 0,
  });
  const [error, setError] = useState(null);
  const eventSourceRef = useRef(null);

  const examplePrompts = [
    "Explain quantum computing in simple terms.",
    "What is the difference between AI and ML?",
    "Write a haiku about coding.",
    "Explain how neural networks learn.",
  ];

  const startStreaming = async () => {
    if (!prompt.trim()) {
      setError("Please enter a prompt");
      return;
    }

    setError(null);
    setOutput("");
    setIsStreaming(true);
    setMetrics({
      tokensGenerated: 0,
      timeElapsed: 0,
      acceptanceRate: null,
      tokensPerSecond: 0,
    });

    try {
      // Build query parameters
      const params = new URLSearchParams({
        prompt: prompt,
        max_tokens: "100",
        temperature: "0.7",
        speculation_depth: "4",
        use_speculative: "true",
      });

      // Close existing connection
      if (eventSourceRef.current) {
        eventSourceRef.current.close();
      }

      // Create SSE connection via POST proxy
      const response = await fetch(`/generate/stream?${params}`, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify({
          prompt: prompt,
          max_tokens: 100,
          temperature: 0.7,
          speculation_depth: 4,
          use_speculative: true,
        }),
      });

      if (!response.ok) {
        throw new Error(`HTTP ${response.status}: ${response.statusText}`);
      }

      // Read SSE stream
      const reader = response.body.getReader();
      const decoder = new TextDecoder();
      let buffer = "";

      while (true) {
        const { done, value } = await reader.read();
        if (done) break;

        buffer += decoder.decode(value, { stream: true });
        const lines = buffer.split("\n");
        buffer = lines.pop() || ""; // Keep incomplete line in buffer

        for (const line of lines) {
          if (line.startsWith("data: ")) {
            const data = line.slice(6);
            try {
              const event = JSON.parse(data);

              if (event.error) {
                setError(event.error);
                setIsStreaming(false);
                return;
              }

              if (event.is_final) {
                setIsStreaming(false);
                return;
              }

              // Update output
              setOutput((prev) => prev + event.token);

              // Update metrics
              setMetrics({
                tokensGenerated: event.index + 1,
                timeElapsed: event.time_elapsed || 0,
                acceptanceRate: event.acceptance_rate,
                tokensPerSecond:
                  event.time_elapsed > 0
                    ? (event.index + 1) / event.time_elapsed
                    : 0,
              });
            } catch (e) {
              console.error("Failed to parse SSE event:", e);
            }
          }
        }
      }
    } catch (err) {
      setError(err.message);
      setIsStreaming(false);
    }
  };

  const stopStreaming = () => {
    if (eventSourceRef.current) {
      eventSourceRef.current.close();
      eventSourceRef.current = null;
    }
    setIsStreaming(false);
  };

  useEffect(() => {
    return () => {
      if (eventSourceRef.current) {
        eventSourceRef.current.close();
      }
    };
  }, []);

  return (
    <section id="demo" className="bg-dark-900 py-20">
      <div className="section-container">
        <motion.div
          initial={{ opacity: 0, y: 30 }}
          whileInView={{ opacity: 1, y: 0 }}
          viewport={{ once: true }}
          className="text-center mb-12"
        >
          <h2 className="text-5xl font-bold mb-4">
            <span className="gradient-text">Live Demo</span>
          </h2>
          <p className="text-xl text-dark-400 max-w-3xl mx-auto">
            See speculative decoding in action. Watch tokens stream in
            real-time.
          </p>
        </motion.div>

        <div className="max-w-5xl mx-auto">
          <div className="grid md:grid-cols-2 gap-6">
            {/* Input Panel */}
            <motion.div
              initial={{ opacity: 0, x: -30 }}
              whileInView={{ opacity: 1, x: 0 }}
              viewport={{ once: true }}
              className="card"
            >
              <h3 className="text-2xl font-bold text-dark-100 mb-4">Input</h3>

              <div className="mb-4">
                <label className="block text-sm font-medium text-dark-400 mb-2">
                  Your Prompt
                </label>
                <textarea
                  value={prompt}
                  onChange={(e) => setPrompt(e.target.value)}
                  placeholder="Enter your prompt here..."
                  className="w-full h-32 px-4 py-3 bg-dark-950 border border-dark-700 rounded-lg text-dark-100 placeholder-dark-600 focus:outline-none focus:ring-2 focus:ring-primary-600 resize-none"
                  disabled={isStreaming}
                />
              </div>

              <div className="mb-6">
                <label className="block text-sm font-medium text-dark-400 mb-2">
                  Example Prompts
                </label>
                <div className="space-y-2">
                  {examplePrompts.map((example, i) => (
                    <button
                      key={i}
                      onClick={() => setPrompt(example)}
                      disabled={isStreaming}
                      className="w-full text-left px-3 py-2 bg-dark-950 hover:bg-dark-800 border border-dark-700 rounded-lg text-sm text-dark-300 transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
                    >
                      {example}
                    </button>
                  ))}
                </div>
              </div>

              <div className="flex gap-3">
                <button
                  onClick={startStreaming}
                  disabled={isStreaming || !prompt.trim()}
                  className="flex-1 btn-primary disabled:opacity-50 disabled:cursor-not-allowed flex items-center justify-center gap-2"
                >
                  {isStreaming ? (
                    <>
                      <div className="w-4 h-4 border-2 border-white border-t-transparent rounded-full animate-spin"></div>
                      Generating...
                    </>
                  ) : (
                    <>
                      <svg
                        className="w-5 h-5"
                        fill="none"
                        stroke="currentColor"
                        viewBox="0 0 24 24"
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
                      Generate
                    </>
                  )}
                </button>
                {isStreaming && (
                  <button onClick={stopStreaming} className="btn-secondary">
                    Stop
                  </button>
                )}
              </div>

              {error && (
                <div className="mt-4 p-3 bg-red-900/20 border border-red-700/50 rounded-lg text-red-400 text-sm">
                  {error}
                </div>
              )}
            </motion.div>

            {/* Output Panel */}
            <motion.div
              initial={{ opacity: 0, x: 30 }}
              whileInView={{ opacity: 1, x: 0 }}
              viewport={{ once: true }}
              className="card"
            >
              <h3 className="text-2xl font-bold text-dark-100 mb-4">Output</h3>

              <div className="mb-4 h-64 p-4 bg-dark-950 border border-dark-700 rounded-lg overflow-y-auto">
                {output ? (
                  <p className="text-dark-100 whitespace-pre-wrap font-mono text-sm leading-relaxed">
                    {output}
                    {isStreaming && (
                      <span className="inline-block w-2 h-4 bg-primary-500 ml-1 animate-pulse"></span>
                    )}
                  </p>
                ) : (
                  <p className="text-dark-600 italic">
                    Output will appear here...
                  </p>
                )}
              </div>

              {/* Metrics */}
              <div className="grid grid-cols-2 gap-4">
                <div className="bg-dark-950 rounded-lg p-3 border border-dark-800">
                  <div className="text-xs text-dark-500 uppercase tracking-wide mb-1">
                    Tokens
                  </div>
                  <div className="text-2xl font-bold text-primary-400">
                    {metrics.tokensGenerated}
                  </div>
                </div>
                <div className="bg-dark-950 rounded-lg p-3 border border-dark-800">
                  <div className="text-xs text-dark-500 uppercase tracking-wide mb-1">
                    Time (s)
                  </div>
                  <div className="text-2xl font-bold text-primary-400">
                    {metrics.timeElapsed.toFixed(2)}
                  </div>
                </div>
                <div className="bg-dark-950 rounded-lg p-3 border border-dark-800">
                  <div className="text-xs text-dark-500 uppercase tracking-wide mb-1">
                    Tokens/sec
                  </div>
                  <div className="text-2xl font-bold text-primary-400">
                    {metrics.tokensPerSecond.toFixed(1)}
                  </div>
                </div>
                <div className="bg-dark-950 rounded-lg p-3 border border-dark-800">
                  <div className="text-xs text-dark-500 uppercase tracking-wide mb-1">
                    Acceptance
                  </div>
                  <div className="text-2xl font-bold text-primary-400">
                    {metrics.acceptanceRate !== null
                      ? `${(metrics.acceptanceRate * 100).toFixed(0)}%`
                      : "-"}
                  </div>
                </div>
              </div>
            </motion.div>
          </div>

          {/* Info Banner */}
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            whileInView={{ opacity: 1, y: 0 }}
            viewport={{ once: true }}
            className="mt-8 p-6 bg-primary-900/20 border border-primary-700/50 rounded-xl"
          >
            <div className="flex items-start gap-4">
              <div className="text-3xl">⚡</div>
              <div>
                <h4 className="font-bold text-primary-300 mb-2">
                  Real-Time Streaming
                </h4>
                <p className="text-dark-300 text-sm">
                  This demo uses Server-Sent Events (SSE) to stream tokens as
                  they're generated. The "Acceptance" metric shows how many
                  draft tokens were accepted by the target model - higher is
                  better! Typical values are 50-80% for well-matched
                  draft/target pairs.
                </p>
              </div>
            </div>
          </motion.div>
        </div>
      </div>
    </section>
  );
};

export default LiveDemo;
