import React, { useEffect, useState } from "react";
import { motion, AnimatePresence } from "framer-motion";

const LoadingScreen = ({ onLoadComplete }) => {
  const [progress, setProgress] = useState(0);
  const [imageLoaded, setImageLoaded] = useState(false);

  useEffect(() => {
    // Preload the helix image
    const img = new Image();
    img.src = "/Helix_image.png";
    img.onload = () => setImageLoaded(true);
    img.onerror = () => setImageLoaded(true); // Continue even if image fails

    // Simulate loading progress
    const interval = setInterval(() => {
      setProgress((prev) => {
        if (prev >= 100) {
          clearInterval(interval);
          setTimeout(() => onLoadComplete(), 600);
          return 100;
        }
        return prev + 8;
      });
    }, 180);

    return () => clearInterval(interval);
  }, [onLoadComplete]);

  return (
    <AnimatePresence>
      <motion.div
        initial={{ opacity: 1 }}
        exit={{ opacity: 0 }}
        transition={{ duration: 0.6, ease: "easeInOut" }}
        className="fixed inset-0 z-50 flex items-center justify-center bg-void-950 overflow-hidden"
      >
        {/* Background DNA Helix - Left Side */}
        <motion.div
          initial={{ opacity: 0, x: -100 }}
          animate={{ opacity: imageLoaded ? 0.08 : 0, x: 0 }}
          transition={{ duration: 1.2, ease: "easeOut" }}
          className="absolute left-0 top-0 h-full w-1/2 pointer-events-none"
          style={{
            backgroundImage: "url(/Helix_image.png)",
            backgroundRepeat: "no-repeat",
            backgroundPosition: "left center",
            backgroundSize: "contain",
            transform: "scaleX(-1)",
            filter: "blur(1px)",
          }}
        />

        {/* Background DNA Helix - Right Side */}
        <motion.div
          initial={{ opacity: 0, x: 100 }}
          animate={{ opacity: imageLoaded ? 0.08 : 0, x: 0 }}
          transition={{ duration: 1.2, ease: "easeOut", delay: 0.2 }}
          className="absolute right-0 top-0 h-full w-1/2 pointer-events-none"
          style={{
            backgroundImage: "url(/Helix_image.png)",
            backgroundRepeat: "no-repeat",
            backgroundPosition: "right center",
            backgroundSize: "contain",
            filter: "blur(1px)",
          }}
        />

        {/* Center Content */}
        <div className="relative z-10 flex flex-col items-center">
          {/* Animated Helix Icon */}
          <motion.div
            initial={{ scale: 0.8, opacity: 0 }}
            animate={{ scale: 1, opacity: 1 }}
            transition={{ duration: 0.5, ease: "easeOut" }}
            className="relative mb-8"
          >
            {/* Glowing backdrop */}
            <div className="absolute inset-0 bg-gradient-to-r from-cyan-500/20 to-emerald-500/20 rounded-full blur-3xl scale-150" />

            {/* Main helix image */}
            <motion.img
              src="/Helix_image.png"
              alt="Helix"
              className="w-32 h-32 object-contain relative z-10"
              initial={{ rotate: -10, opacity: 0 }}
              animate={{
                rotate: 0,
                opacity: 1,
              }}
              transition={{ duration: 0.8, ease: "easeOut" }}
              style={{
                filter: "drop-shadow(0 0 20px rgba(6, 182, 212, 0.4))",
              }}
            />

            {/* Rotating glow ring */}
            <motion.div
              className="absolute inset-0 rounded-full border-2 border-cyan-500/30"
              style={{ scale: 1.3 }}
              animate={{ rotate: 360 }}
              transition={{ duration: 8, repeat: Infinity, ease: "linear" }}
            />
          </motion.div>

          {/* Brand Name */}
          <motion.h1
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.5, delay: 0.3 }}
            className="text-5xl font-bold mb-2"
            style={{
              background:
                "linear-gradient(135deg, #06b6d4 0%, #10b981 50%, #22c55e 100%)",
              WebkitBackgroundClip: "text",
              WebkitTextFillColor: "transparent",
              backgroundClip: "text",
              letterSpacing: "0.05em",
            }}
          >
            Helix
          </motion.h1>

          {/* Tagline */}
          <motion.p
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            transition={{ duration: 0.5, delay: 0.5 }}
            className="text-gray-400 text-sm tracking-wider mb-8"
          >
            SPECULATIVE DECODING ENGINE
          </motion.p>

          {/* Progress Bar */}
          <motion.div
            initial={{ opacity: 0, width: 0 }}
            animate={{ opacity: 1, width: 256 }}
            transition={{ duration: 0.3, delay: 0.4 }}
            className="w-64"
          >
            <div className="h-1 bg-white/10 rounded-full overflow-hidden backdrop-blur-sm">
              <motion.div
                className="h-full rounded-full"
                style={{
                  background:
                    "linear-gradient(90deg, #06b6d4, #10b981, #22c55e)",
                }}
                initial={{ width: 0 }}
                animate={{ width: `${progress}%` }}
                transition={{ duration: 0.2 }}
              />
            </div>
            <motion.p
              initial={{ opacity: 0 }}
              animate={{ opacity: 1 }}
              transition={{ delay: 0.6 }}
              className="text-center text-gray-500 text-xs mt-2"
            >
              {progress < 100 ? "Initializing..." : "Ready"}
            </motion.p>
          </motion.div>
        </div>
      </motion.div>
    </AnimatePresence>
  );
};

export default LoadingScreen;
