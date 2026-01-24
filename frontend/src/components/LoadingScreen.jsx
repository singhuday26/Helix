import React, { useEffect, useState } from "react";
import { motion, AnimatePresence } from "framer-motion";

const LoadingScreen = ({ onLoadComplete }) => {
  const [progress, setProgress] = useState(0);
  const [imageLoaded, setImageLoaded] = useState(false);
  const [currentCharIndex, setCurrentCharIndex] = useState(0);
  const fullText = "HELIX";

  useEffect(() => {
    // Preload the helix image
    const img = new Image();
    img.src = "/Helix_image.png";
    img.onload = () => setImageLoaded(true);
    img.onerror = () => setImageLoaded(true);

    // Simulate loading progress
    const interval = setInterval(() => {
      setProgress((prev) => {
        if (prev >= 100) {
          clearInterval(interval);
          setTimeout(() => onLoadComplete(), 800);
          return 100;
        }
        return prev + 6;
      });
    }, 150);

    return () => clearInterval(interval);
  }, [onLoadComplete]);

  // Professional typewriter effect - one character at a time
  useEffect(() => {
    if (currentCharIndex < fullText.length) {
      const timeout = setTimeout(() => {
        setCurrentCharIndex((prev) => prev + 1);
      }, 280); // Slightly slower for dramatic effect
      return () => clearTimeout(timeout);
    }
  }, [currentCharIndex]);

  // Individual character animation variants
  const charVariants = {
    hidden: {
      opacity: 0,
      y: 50,
      scale: 0.5,
      rotateX: -90,
    },
    visible: {
      opacity: 1,
      y: 0,
      scale: 1,
      rotateX: 0,
      transition: {
        type: "spring",
        damping: 12,
        stiffness: 200,
        duration: 0.6,
      },
    },
  };

  return (
    <AnimatePresence>
      <motion.div
        initial={{ opacity: 1 }}
        exit={{ opacity: 0 }}
        transition={{ duration: 0.8, ease: "easeInOut" }}
        className="fixed inset-0 z-50 flex items-center justify-center overflow-hidden"
        style={{ backgroundColor: "#030712" }}
      >
        {/* Animated gradient background */}
        <motion.div
          className="absolute inset-0"
          animate={{
            background: [
              "radial-gradient(ellipse 80% 80% at 50% 50%, rgba(16, 185, 129, 0.03) 0%, transparent 50%)",
              "radial-gradient(ellipse 80% 80% at 50% 50%, rgba(34, 197, 94, 0.04) 0%, transparent 50%)",
              "radial-gradient(ellipse 80% 80% at 50% 50%, rgba(16, 185, 129, 0.03) 0%, transparent 50%)",
            ],
          }}
          transition={{ duration: 4, repeat: Infinity, ease: "easeInOut" }}
        />

        {/* Floating particles effect */}
        {[...Array(6)].map((_, i) => (
          <motion.div
            key={i}
            className="absolute w-1 h-1 rounded-full"
            style={{
              background: "rgba(255, 255, 255, 0.4)",
              boxShadow: "0 0 10px rgba(16, 185, 129, 0.6)",
              left: `${15 + i * 15}%`,
              top: `${20 + (i % 3) * 25}%`,
            }}
            animate={{
              y: [-20, 20, -20],
              opacity: [0.2, 0.6, 0.2],
              scale: [0.8, 1.2, 0.8],
            }}
            transition={{
              duration: 3 + i * 0.5,
              repeat: Infinity,
              ease: "easeInOut",
              delay: i * 0.3,
            }}
          />
        ))}

        {/* Background DNA Helix - Left Side */}
        <motion.div
          initial={{ opacity: 0, x: -100 }}
          animate={{ opacity: imageLoaded ? 0.07 : 0, x: 0 }}
          transition={{ duration: 1.5, ease: "easeOut" }}
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
          animate={{ opacity: imageLoaded ? 0.07 : 0, x: 0 }}
          transition={{ duration: 1.5, ease: "easeOut", delay: 0.2 }}
          className="absolute right-0 top-0 h-full w-1/2 pointer-events-none"
          style={{
            backgroundImage: "url(/Helix_image.png)",
            backgroundRepeat: "no-repeat",
            backgroundPosition: "right center",
            backgroundSize: "contain",
            filter: "blur(1px)",
          }}
        />

        {/* Center DNA Helix - Transparent with subtle green glow */}
        <motion.div
          initial={{ opacity: 0, scale: 0.8 }}
          animate={{ opacity: imageLoaded ? 0.12 : 0, scale: 1 }}
          transition={{ duration: 2, ease: "easeOut", delay: 0.3 }}
          className="absolute inset-0 pointer-events-none flex items-center justify-center"
        >
          <div
            className="w-full h-full max-w-xl"
            style={{
              backgroundImage: "url(/Helix_image.png)",
              backgroundRepeat: "no-repeat",
              backgroundPosition: "center center",
              backgroundSize: "contain",
              filter: "blur(0.5px) brightness(1.1)",
              maskImage:
                "radial-gradient(ellipse 60% 70% at center, black 20%, transparent 65%)",
              WebkitMaskImage:
                "radial-gradient(ellipse 60% 70% at center, black 20%, transparent 65%)",
            }}
          />
          {/* Subtle green-white glow overlay */}
          <motion.div
            className="absolute inset-0"
            animate={{
              opacity: [0.6, 1, 0.6],
            }}
            transition={{ duration: 3, repeat: Infinity, ease: "easeInOut" }}
            style={{
              background:
                "radial-gradient(ellipse 40% 50% at center, rgba(255, 255, 255, 0.03) 0%, rgba(16, 185, 129, 0.05) 30%, transparent 60%)",
            }}
          />
        </motion.div>

        {/* Center Content */}
        <div className="relative z-10 flex flex-col items-center">
          {/* Brand Name - Professional Typewriter with Individual Character Animation */}
          <motion.div
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            transition={{ duration: 0.5 }}
            className="mb-6 relative"
          >
            {/* Multi-layer glow effect - light green and white */}
            <motion.div
              className="absolute inset-0 pointer-events-none"
              animate={{
                opacity: [0.3, 0.5, 0.3],
              }}
              transition={{ duration: 2, repeat: Infinity, ease: "easeInOut" }}
              style={{
                background:
                  "radial-gradient(ellipse 100% 100% at center, rgba(255, 255, 255, 0.15) 0%, rgba(167, 243, 208, 0.2) 30%, transparent 60%)",
                filter: "blur(40px)",
                transform: "scale(2)",
              }}
            />

            {/* Secondary glow layer - softer */}
            <motion.div
              className="absolute inset-0 pointer-events-none"
              animate={{
                opacity: [0.2, 0.4, 0.2],
                scale: [1.8, 2.2, 1.8],
              }}
              transition={{
                duration: 3,
                repeat: Infinity,
                ease: "easeInOut",
                delay: 0.5,
              }}
              style={{
                background:
                  "radial-gradient(ellipse 80% 80% at center, rgba(134, 239, 172, 0.15) 0%, transparent 50%)",
                filter: "blur(60px)",
              }}
            />

            {/* Text container with perspective */}
            <div
              className="relative flex justify-center"
              style={{ perspective: "1000px" }}
            >
              {fullText.split("").map((char, index) => (
                <motion.span
                  key={index}
                  variants={charVariants}
                  initial="hidden"
                  animate={index < currentCharIndex ? "visible" : "hidden"}
                  className="inline-block relative"
                  style={{
                    fontSize: "clamp(4.5rem, 18vw, 12rem)",
                    fontFamily:
                      "'Inter', 'SF Pro Display', system-ui, sans-serif",
                    fontWeight: 800,
                    background:
                      "linear-gradient(180deg, #ffffff 0%, #a7f3d0 25%, #10b981 50%, #059669 100%)",
                    WebkitBackgroundClip: "text",
                    WebkitTextFillColor: "transparent",
                    backgroundClip: "text",
                    letterSpacing: "0.08em",
                    marginRight: index < fullText.length - 1 ? "0.02em" : "0",
                    filter:
                      "drop-shadow(0 0 30px rgba(167, 243, 208, 0.4)) drop-shadow(0 0 60px rgba(16, 185, 129, 0.3))",
                  }}
                >
                  {char}
                  {/* Individual character glow */}
                  {index < currentCharIndex && (
                    <motion.span
                      className="absolute inset-0 pointer-events-none"
                      initial={{ opacity: 1 }}
                      animate={{ opacity: 0 }}
                      transition={{ duration: 0.8, delay: 0.2 }}
                      style={{
                        background:
                          "linear-gradient(180deg, #ffffff 0%, #a7f3d0 50%, #10b981 100%)",
                        WebkitBackgroundClip: "text",
                        WebkitTextFillColor: "transparent",
                        backgroundClip: "text",
                        filter: "blur(8px)",
                      }}
                    >
                      {char}
                    </motion.span>
                  )}
                </motion.span>
              ))}

              {/* Blinking cursor */}
              <motion.span
                animate={{
                  opacity: currentCharIndex < fullText.length ? [1, 0, 1] : 0,
                }}
                transition={{
                  duration: 0.8,
                  repeat: Infinity,
                  ease: "linear",
                }}
                className="inline-block"
                style={{
                  fontSize: "clamp(4.5rem, 18vw, 12rem)",
                  fontWeight: 200,
                  color: "#a7f3d0",
                  marginLeft: "-0.02em",
                  textShadow: "0 0 20px rgba(167, 243, 208, 0.8)",
                }}
              >
                |
              </motion.span>
            </div>
          </motion.div>

          {/* Tagline with fade-in after text completes */}
          <motion.p
            initial={{ opacity: 0, y: 15 }}
            animate={{
              opacity: currentCharIndex >= fullText.length ? 1 : 0,
              y: currentCharIndex >= fullText.length ? 0 : 15,
            }}
            transition={{ duration: 0.8, ease: "easeOut" }}
            className="tracking-widest mb-14 font-light"
            style={{
              fontSize: "clamp(0.65rem, 2vw, 0.95rem)",
              letterSpacing: "0.4em",
              color: "rgba(167, 243, 208, 0.7)",
              textShadow: "0 0 20px rgba(167, 243, 208, 0.3)",
            }}
          >
            SPECULATIVE DECODING ENGINE
          </motion.p>

          {/* Progress Bar - Elegant minimal design */}
          <motion.div
            initial={{ opacity: 0, scaleX: 0 }}
            animate={{
              opacity: currentCharIndex >= fullText.length ? 1 : 0,
              scaleX: currentCharIndex >= fullText.length ? 1 : 0,
            }}
            transition={{ duration: 0.6, delay: 0.2 }}
            style={{ width: "min(300px, 70vw)" }}
          >
            <div
              className="h-[2px] rounded-full overflow-hidden"
              style={{
                background: "rgba(255, 255, 255, 0.08)",
                boxShadow: "inset 0 0 10px rgba(0, 0, 0, 0.3)",
              }}
            >
              <motion.div
                className="h-full rounded-full"
                style={{
                  background:
                    "linear-gradient(90deg, rgba(167, 243, 208, 0.8), #10b981, rgba(167, 243, 208, 0.9))",
                  boxShadow:
                    "0 0 15px rgba(167, 243, 208, 0.6), 0 0 30px rgba(16, 185, 129, 0.4)",
                }}
                initial={{ width: 0 }}
                animate={{ width: `${progress}%` }}
                transition={{ duration: 0.15, ease: "linear" }}
              />
            </div>
            <motion.p
              initial={{ opacity: 0 }}
              animate={{ opacity: 1 }}
              transition={{ delay: 0.4 }}
              className="text-center text-xs mt-4 tracking-widest font-light"
              style={{
                color: "rgba(167, 243, 208, 0.5)",
                letterSpacing: "0.2em",
              }}
            >
              {progress < 100 ? "Initializing..." : "Ready"}
            </motion.p>
          </motion.div>
        </div>

        {/* Bottom subtle gradient fade */}
        <div
          className="absolute bottom-0 left-0 right-0 h-32 pointer-events-none"
          style={{
            background:
              "linear-gradient(to top, rgba(3, 7, 18, 0.8) 0%, transparent 100%)",
          }}
        />
      </motion.div>
    </AnimatePresence>
  );
};

export default LoadingScreen;
