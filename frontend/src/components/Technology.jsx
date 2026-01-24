import React from "react";
import { motion } from "framer-motion";

const steps = [
  {
    number: "01",
    title: "Draft Phase",
    description:
      "A small, fast draft model (e.g., 125M params) generates K candidate tokens speculatively. This is cheap and fast.",
    visual: (
      <div className="font-mono text-sm space-y-1">
        <div className="text-gray-500">draft_model.generate(K=4)</div>
        <div className="flex gap-1 mt-2">
          {["The", "cat", "sat", "on"].map((token, i) => (
            <span
              key={i}
              className="px-2 py-1 rounded bg-helix-draft/20 text-helix-draft border border-helix-draft/30"
            >
              {token}
            </span>
          ))}
        </div>
      </div>
    ),
  },
  {
    number: "02",
    title: "Verify Phase",
    description:
      "The target model (e.g., 1.1B params) verifies all K tokens in a single forward pass. Parallel verification is the key insight.",
    visual: (
      <div className="font-mono text-sm space-y-1">
        <div className="text-gray-500">target_model.verify(drafts)</div>
        <div className="flex gap-1 mt-2">
          {[
            { token: "The", status: "accept" },
            { token: "cat", status: "accept" },
            { token: "sat", status: "accept" },
            { token: "on", status: "reject" },
          ].map((item, i) => (
            <span
              key={i}
              className={`px-2 py-1 rounded border ${
                item.status === "accept"
                  ? "bg-helix-accept/20 text-helix-accept border-helix-accept/30"
                  : "bg-helix-reject/20 text-helix-reject border-helix-reject/30"
              }`}
            >
              {item.token}
            </span>
          ))}
        </div>
      </div>
    ),
  },
  {
    number: "03",
    title: "Accept & Continue",
    description:
      "Accepted tokens are appended to output. On rejection, discard that token and all following drafts, then sample the correct token.",
    visual: (
      <div className="font-mono text-sm space-y-1">
        <div className="text-gray-500">output += accepted_tokens</div>
        <div className="flex gap-1 mt-2">
          {["The", "cat", "sat"].map((token, i) => (
            <span
              key={i}
              className="px-2 py-1 rounded bg-helix-verify/20 text-helix-verify border border-helix-verify/30"
            >
              {token}
            </span>
          ))}
          <span className="px-2 py-1 rounded bg-white/10 text-white border border-white/20">
            quietly
          </span>
        </div>
        <div className="text-gray-600 text-xs mt-1">
          → 4 tokens generated, 1 forward pass
        </div>
      </div>
    ),
  },
];

const Technology = () => {
  return (
    <section
      id="technology"
      className="py-24 bg-void-900 relative overflow-hidden"
    >
      {/* DNA Helix Background - Right Side */}
      <div className="helix-bg-section right" aria-hidden="true" />

      <div className="max-w-6xl mx-auto px-6 relative z-10">
        {/* Section Header */}
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          whileInView={{ opacity: 1, y: 0 }}
          viewport={{ once: true }}
          className="text-center mb-16"
        >
          <h2 className="text-3xl sm:text-4xl font-bold text-white mb-4">
            How Speculative Decoding Works
          </h2>
          <p className="text-gray-400 max-w-2xl mx-auto">
            Trade compute for latency. Instead of generating tokens one at a
            time, speculate multiple tokens and verify them in parallel.
          </p>
        </motion.div>

        {/* Steps */}
        <div className="space-y-8">
          {steps.map((step, index) => (
            <motion.div
              key={step.number}
              initial={{ opacity: 0, x: index % 2 === 0 ? -30 : 30 }}
              whileInView={{ opacity: 1, x: 0 }}
              viewport={{ once: true }}
              transition={{
                delay: index * 0.15,
                type: "spring",
                stiffness: 50,
              }}
              className="flex flex-col md:flex-row gap-8 items-start group"
            >
              {/* Step Content */}
              <div className="flex-1 order-2 md:order-1">
                <div className="flex items-center gap-4 mb-4">
                  <span className="text-5xl font-bold text-white/10 group-hover:text-white/20 transition-colors">
                    {step.number}
                  </span>
                  <h3 className="text-xl font-semibold text-white group-hover:text-transparent group-hover:bg-gradient-to-r group-hover:from-helix-draft group-hover:to-helix-verify group-hover:bg-clip-text transition-all duration-300">
                    {step.title}
                  </h3>
                </div>
                <p className="text-gray-400 leading-relaxed mb-6 group-hover:text-gray-300 transition-colors">
                  {step.description}
                </p>
              </div>

              {/* Visual */}
              <div className="flex-1 order-1 md:order-2">
                <div className="p-6 rounded-xl bg-void-950 border border-white/5 group-hover:border-helix-draft/30 group-hover:shadow-lg group-hover:shadow-helix-draft/5 transition-all duration-300">
                  {step.visual}
                </div>
              </div>
            </motion.div>
          ))}
        </div>

        {/* Why It's Fast */}
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          whileInView={{ opacity: 1, y: 0 }}
          viewport={{ once: true }}
          className="mt-16 p-8 rounded-2xl bg-gradient-to-br from-helix-draft/5 to-helix-verify/5 border border-white/5"
        >
          <h3 className="text-xl font-semibold text-white mb-4">
            Why This Works
          </h3>
          <div className="grid md:grid-cols-2 gap-6 text-sm">
            <div>
              <h4 className="text-helix-draft font-medium mb-2">
                The Bottleneck
              </h4>
              <p className="text-gray-400">
                LLM inference is memory-bandwidth bound, not compute-bound.
                Moving model weights from RAM to processor takes ~95% of the
                time. The actual matrix math is nearly instant.
              </p>
            </div>
            <div>
              <h4 className="text-helix-verify font-medium mb-2">
                The Solution
              </h4>
              <p className="text-gray-400">
                Since we're waiting on memory anyway, we use that time to verify
                multiple tokens at once. If the draft model is 75% accurate, we
                get ~3 tokens per forward pass instead of 1.
              </p>
            </div>
          </div>
        </motion.div>
      </div>
    </section>
  );
};

export default Technology;
