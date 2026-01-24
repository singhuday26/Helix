import React from "react";
import { motion } from "framer-motion";
import { Link } from "react-router-dom";

const Hero = () => {
  return (
    <section className="relative min-h-screen flex items-center justify-center overflow-hidden pt-16">
      {/* DNA Helix Hero Background */}
      <div className="helix-bg-hero" aria-hidden="true" />

      {/* Background */}
      <div className="absolute inset-0 bg-void-950">
        {/* Subtle grid */}
        <div
          className="absolute inset-0 opacity-[0.02]"
          style={{
            backgroundImage: `linear-gradient(rgba(255,255,255,0.1) 1px, transparent 1px),
                              linear-gradient(90deg, rgba(255,255,255,0.1) 1px, transparent 1px)`,
            backgroundSize: "64px 64px",
          }}
        />
        {/* Gradient orbs */}
        <div className="absolute top-1/4 left-1/4 w-96 h-96 bg-helix-draft/10 rounded-full blur-3xl" />
        <div className="absolute bottom-1/4 right-1/4 w-96 h-96 bg-helix-verify/10 rounded-full blur-3xl" />
      </div>

      <div className="relative z-10 max-w-5xl mx-auto px-6 text-center">
        {/* Version Badge */}
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.5 }}
          className="inline-flex items-center gap-2 px-3 py-1.5 rounded-full bg-white/5 border border-white/10 mb-8"
        >
          <span className="w-2 h-2 rounded-full bg-helix-accept animate-pulse" />
          <span className="text-sm text-gray-400">v1.0 — Now Available</span>
        </motion.div>

        {/* Main Headline */}
        <motion.h1
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.5, delay: 0.1 }}
          className="text-5xl sm:text-6xl lg:text-7xl font-bold text-white mb-6 tracking-tight"
        >
          LLM Inference,{" "}
          <span className="bg-gradient-to-r from-helix-draft via-helix-verify to-helix-accept bg-clip-text text-transparent">
            Accelerated
          </span>
        </motion.h1>

        {/* Subheadline */}
        <motion.p
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.5, delay: 0.2 }}
          className="text-xl text-gray-400 max-w-2xl mx-auto mb-10 leading-relaxed"
        >
          Helix delivers 3-5x faster inference through speculative decoding. Run
          large language models efficiently on edge devices without sacrificing
          output quality.
        </motion.p>

        {/* CTA Buttons */}
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.5, delay: 0.3 }}
          className="flex flex-wrap items-center justify-center gap-4 mb-16"
        >
          <Link
            to="/comparison"
            className="group px-6 py-3 bg-white text-void-950 font-medium rounded-lg hover:bg-gray-100 transition-colors flex items-center gap-2"
          >
            See It In Action
            <svg
              className="w-4 h-4 transition-transform group-hover:translate-x-0.5"
              fill="none"
              viewBox="0 0 24 24"
              stroke="currentColor"
            >
              <path
                strokeLinecap="round"
                strokeLinejoin="round"
                strokeWidth={2}
                d="M9 5l7 7-7 7"
              />
            </svg>
          </Link>
          <a
            href="#playground"
            className="px-6 py-3 text-white font-medium rounded-lg border border-white/20 hover:bg-white/5 hover:border-white/30 hover:-translate-y-0.5 transition-all duration-300"
          >
            Open Playground
          </a>
        </motion.div>

        {/* Key Metrics */}
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.5, delay: 0.4 }}
          className="grid grid-cols-2 md:grid-cols-4 gap-8 max-w-3xl mx-auto"
        >
          {[
            { value: "3-5×", label: "Faster Inference" },
            { value: "100%", label: "Output Quality" },
            { value: "<100ms", label: "Time to First Token" },
            { value: "~2GB", label: "Memory Footprint" },
          ].map((stat, i) => (
            <motion.div
              key={stat.label}
              initial={{ opacity: 0, scale: 0.5 }}
              animate={{ opacity: 1, scale: 1 }}
              transition={{
                delay: 0.5 + i * 0.1,
                type: "spring",
                stiffness: 100,
              }}
              className="text-center group cursor-default"
            >
              <div className="text-3xl font-bold text-white mb-1 group-hover:text-transparent group-hover:bg-gradient-to-r group-hover:from-helix-draft group-hover:to-helix-verify group-hover:bg-clip-text transition-all duration-300">
                {stat.value}
              </div>
              <div className="text-sm text-gray-500 group-hover:text-gray-400 transition-colors">
                {stat.label}
              </div>
            </motion.div>
          ))}
        </motion.div>
      </div>

      {/* Bottom fade */}
      <div className="absolute bottom-0 left-0 right-0 h-32 bg-gradient-to-t from-void-950 to-transparent" />
    </section>
  );
};

export default Hero;
