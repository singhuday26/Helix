import React from "react";
import { motion } from "framer-motion";

const Hero = () => {
  return (
    <section className="relative overflow-hidden bg-gradient-to-b from-dark-900 to-dark-950 border-b border-dark-800">
      {/* Animated background grid */}
      <div className="absolute inset-0 bg-[linear-gradient(to_right,#0f172a_1px,transparent_1px),linear-gradient(to_bottom,#0f172a_1px,transparent_1px)] bg-[size:4rem_4rem] [mask-image:radial-gradient(ellipse_80%_50%_at_50%_0%,#000_70%,transparent_110%)] opacity-20"></div>

      <div className="section-container relative z-10">
        <motion.div
          initial={{ opacity: 0, y: 30 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.8 }}
          className="text-center"
        >
          {/* Logo/Badge */}
          <motion.div
            initial={{ scale: 0.9, opacity: 0 }}
            animate={{ scale: 1, opacity: 1 }}
            transition={{ delay: 0.2, duration: 0.6 }}
            className="inline-flex items-center gap-2 px-4 py-2 bg-primary-900/30 border border-primary-700/50 rounded-full mb-8"
          >
            <span className="w-2 h-2 bg-primary-500 rounded-full animate-pulse"></span>
            <span className="text-primary-300 text-sm font-medium">
              Speculative Decoding Engine
            </span>
          </motion.div>

          {/* Main Title */}
          <h1 className="text-6xl sm:text-7xl lg:text-8xl font-extrabold mb-6">
            <span className="gradient-text text-glow">Helix</span>
          </h1>

          <p className="text-2xl sm:text-3xl text-dark-300 font-light mb-4">
            Fast LLM Inference on Edge Devices
          </p>

          <p className="text-lg text-dark-400 max-w-3xl mx-auto mb-12">
            From "AI Beginner" to "Systems Architect" in 24 hours. Learn how we
            trade compute for speed using speculative decoding and
            PagedAttention.
          </p>

          {/* CTA Buttons */}
          <div className="flex flex-wrap justify-center gap-4">
            <a href="#demo" className="btn-primary">
              Try Live Demo →
            </a>
            <a href="#education" className="btn-secondary">
              Learn How It Works
            </a>
          </div>

          {/* Stats */}
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay: 0.6, duration: 0.8 }}
            className="mt-16 grid grid-cols-2 md:grid-cols-4 gap-8 max-w-4xl mx-auto"
          >
            <div className="text-center">
              <div className="text-4xl font-bold text-primary-400 mb-2">
                3-5x
              </div>
              <div className="text-dark-400 text-sm">Speedup vs Standard</div>
            </div>
            <div className="text-center">
              <div className="text-4xl font-bold text-primary-400 mb-2">
                30-50%
              </div>
              <div className="text-dark-400 text-sm">Memory Saved</div>
            </div>
            <div className="text-center">
              <div className="text-4xl font-bold text-primary-400 mb-2">
                100%
              </div>
              <div className="text-dark-400 text-sm">Quality Preserved</div>
            </div>
            <div className="text-center">
              <div className="text-4xl font-bold text-primary-400 mb-2">
                Edge
              </div>
              <div className="text-dark-400 text-sm">AMD GPU Ready</div>
            </div>
          </motion.div>
        </motion.div>
      </div>

      {/* Bottom gradient */}
      <div className="absolute bottom-0 left-0 right-0 h-px bg-gradient-to-r from-transparent via-primary-500 to-transparent"></div>
    </section>
  );
};

export default Hero;
