/** @type {import('tailwindcss').Config} */
export default {
  content: ["./index.html", "./src/**/*.{js,ts,jsx,tsx}"],
  theme: {
    extend: {
      colors: {
        // Helix custom palette - Draft (cyan) to Verified (emerald) spectrum
        helix: {
          draft: "#06b6d4", // Cyan - represents draft/speculation
          verify: "#10b981", // Emerald - represents verification
          accept: "#22c55e", // Green - represents accepted tokens
          reject: "#f43f5e", // Rose - represents rejected tokens
          glow: "#67e8f9", // Light cyan for glows
        },
        // Deep space background theme
        void: {
          50: "#f0fdfa",
          100: "#ccfbf1",
          200: "#99f6e4",
          300: "#5eead4",
          400: "#2dd4bf",
          500: "#14b8a6",
          600: "#0d9488",
          700: "#0f766e",
          800: "#115e59",
          900: "#0a0f1a",
          950: "#030712",
          deep: "#010409",
        },
        // Accent spectrum
        flux: {
          cyan: "#22d3ee",
          teal: "#2dd4bf",
          emerald: "#34d399",
          lime: "#a3e635",
        },
      },
      fontFamily: {
        sans: ["Inter", "system-ui", "sans-serif"],
        mono: ["JetBrains Mono", "Fira Code", "monospace"],
        display: ["Space Grotesk", "Inter", "sans-serif"],
      },
      gridTemplateColumns: {
        16: "repeat(16, minmax(0, 1fr))",
      },
      animation: {
        "helix-spin": "helixSpin 8s linear infinite",
        "draft-pulse": "draftPulse 2s ease-in-out infinite",
        "verify-sweep": "verifySweep 1.5s ease-out",
        "token-flow": "tokenFlow 0.3s ease-out",
        "strand-wave": "strandWave 3s ease-in-out infinite",
        "glow-pulse": "glowPulse 2s ease-in-out infinite",
        "scan-line": "scanLine 2s linear infinite",
      },
      keyframes: {
        helixSpin: {
          "0%": { transform: "rotateY(0deg)" },
          "100%": { transform: "rotateY(360deg)" },
        },
        draftPulse: {
          "0%, 100%": { opacity: "0.4", transform: "scale(1)" },
          "50%": { opacity: "1", transform: "scale(1.05)" },
        },
        verifySweep: {
          "0%": { clipPath: "inset(0 100% 0 0)" },
          "100%": { clipPath: "inset(0 0 0 0)" },
        },
        tokenFlow: {
          "0%": { opacity: "0", transform: "translateX(-10px)" },
          "100%": { opacity: "1", transform: "translateX(0)" },
        },
        strandWave: {
          "0%, 100%": { transform: "translateY(0) scaleY(1)" },
          "50%": { transform: "translateY(-5px) scaleY(1.1)" },
        },
        glowPulse: {
          "0%, 100%": {
            boxShadow:
              "0 0 20px rgba(6, 182, 212, 0.3), inset 0 0 20px rgba(6, 182, 212, 0.1)",
          },
          "50%": {
            boxShadow:
              "0 0 40px rgba(6, 182, 212, 0.6), inset 0 0 30px rgba(6, 182, 212, 0.2)",
          },
        },
        scanLine: {
          "0%": { transform: "translateY(-100%)" },
          "100%": { transform: "translateY(100%)" },
        },
      },
      backgroundImage: {
        "helix-gradient":
          "linear-gradient(135deg, #06b6d4 0%, #10b981 50%, #22c55e 100%)",
        "draft-gradient": "linear-gradient(90deg, #06b6d4, #22d3ee)",
        "verify-gradient": "linear-gradient(90deg, #10b981, #34d399)",
        "void-radial":
          "radial-gradient(ellipse at center, #0a0f1a 0%, #030712 50%, #010409 100%)",
        "grid-helix":
          "linear-gradient(rgba(6, 182, 212, 0.03) 1px, transparent 1px), linear-gradient(90deg, rgba(6, 182, 212, 0.03) 1px, transparent 1px)",
      },
      boxShadow: {
        helix: "0 0 30px rgba(6, 182, 212, 0.3)",
        "helix-lg": "0 0 60px rgba(6, 182, 212, 0.4)",
        draft: "0 0 20px rgba(6, 182, 212, 0.5)",
        verify: "0 0 20px rgba(16, 185, 129, 0.5)",
        accept: "0 0 20px rgba(34, 197, 94, 0.5)",
        "inner-glow": "inset 0 0 30px rgba(6, 182, 212, 0.1)",
      },
    },
  },
  plugins: [],
};
