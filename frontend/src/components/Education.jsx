import React, { useState } from "react";
import { motion } from "framer-motion";

const levels = [
  {
    id: 1,
    color: "green",
    emoji: "🟢",
    title: "Level 1: The Basics",
    concept: "Autoregressive Generation",
    analogy:
      "Imagine writing an essay, but you're only allowed to write one word at a time. After every word, you have to re-read the entire essay from the start to decide the next word.",
    example: [
      'Read "The" → Write "cat"',
      'Read "The cat" → Write "sat"',
      'Read "The cat sat" → Write "on"',
    ],
    problem:
      "This is inherently slow. Typically, an LLM generates 30-50 words (tokens) per second.",
    jargon: '"LLMs are serial generative models."',
  },
  {
    id: 2,
    color: "yellow",
    emoji: "🟡",
    title: "Level 2: The Bottleneck",
    concept: "Memory Bandwidth Bound",
    analogy:
      "You might think LLMs are slow because the math (matrix multiplication) is hard. False. On a modern CPU/GPU, the math is instant. The slow part is moving the model weights from RAM to the Processor.",
    example: [
      "The Processor is a super-fast chef (can cut 100 onions/sec)",
      "The RAM is the fridge in the basement",
      "Workflow: To cut one onion (generate one token), the chef runs to the basement, grabs the entire model (3GB), runs upstairs, cuts the onion, then returns the model to the basement",
    ],
    problem:
      "The chef spends 99% of the time running on the stairs (Memory Bandwidth) and 1% cutting onions (Compute).",
    jargon:
      '"We are memory-bound. The chef is idle. Let\'s give the chef more work to do while they are upstairs."',
  },
  {
    id: 3,
    color: "orange",
    emoji: "🟠",
    title: "Level 3: The Solution",
    concept: "Speculative Decoding",
    analogy: "Since the chef is bored, let's hire a Junior Chef (Draft Model).",
    example: [
      'Junior Chef (Small Model): Can\'t cook perfectly, but runs fast. Guesses: "The cat sat on the"',
      "Senior Chef (Target Model): Instead of generating 1 word, the Senior Chef takes the Junior's 4 guesses and checks them all at once",
      "\"Is 'The' right?\" YES",
      "\"Is 'cat' right?\" YES",
      "\"Is 'sat' right?\" YES",
      "\"Is 'on' right?\" YES",
    ],
    problem:
      'We got 4 words for the "price" (memory movement cost) of 1 verification pass.',
    jargon:
      "\"We convert the 'waiting for memory' time into 'doing useful verification work'.\"",
  },
  {
    id: 4,
    color: "red",
    emoji: "🔴",
    title: "Level 4: The Optimization",
    concept: "KV Cache",
    analogy:
      'Remember Level 1? "Re-read the entire essay." That\'s wasteful. KV Cache (Key-Value Cache) is like taking notes.',
    example: [
      'Instead of re-reading "The cat sat", we save the mathematical representation of "The cat sat" in a cache',
      'For the next word, we just load the cache + the new word "on"',
    ],
    problem:
      "Speed: Much faster (math is easier). Memory: The cache grows huge. It eats up your RAM.",
    jargon: "Trade-off between speed and memory consumption.",
  },
  {
    id: 5,
    color: "purple",
    emoji: "🟣",
    title: "Level 5: The Boss Move",
    concept: "PagedAttention",
    analogy:
      'Standard KV Cache reserves huge blocks of memory "just in case" the sentence gets long. This wastes ~30-50% of RAM (fragmentation). PagedAttention (inspired by OS Virtual Memory) breaks the cache into tiny, non-contiguous blocks.',
    example: [
      'Old Way: "I need a continuous 1GB block." (Hard to find)',
      'PagedAttention: "I\'ll take any 10 small blocks you have, anywhere in RAM."',
    ],
    problem:
      "PagedAttention saves memory. We use that saved memory to load the Draft Model.",
    jargon: '"So we get Speed (Speculative) without running out of RAM (OOM)."',
  },
];

const LevelCard = ({ level, index }) => {
  const [isExpanded, setIsExpanded] = useState(false);

  const colorMap = {
    green: "from-green-600 to-green-800",
    yellow: "from-yellow-600 to-yellow-800",
    orange: "from-orange-600 to-orange-800",
    red: "from-red-600 to-red-800",
    purple: "from-purple-600 to-purple-800",
  };

  return (
    <motion.div
      initial={{ opacity: 0, y: 50 }}
      whileInView={{ opacity: 1, y: 0 }}
      viewport={{ once: true }}
      transition={{ delay: index * 0.1, duration: 0.6 }}
      className="card hover:border-primary-700 transition-all duration-300 cursor-pointer"
      onClick={() => setIsExpanded(!isExpanded)}
    >
      {/* Header */}
      <div className="flex items-center gap-4 mb-4">
        <div
          className={`text-5xl flex-shrink-0 bg-gradient-to-br ${colorMap[level.color]} p-4 rounded-xl shadow-lg`}
        >
          {level.emoji}
        </div>
        <div className="flex-1">
          <h3 className="text-2xl font-bold text-dark-100 mb-1">
            {level.title}
          </h3>
          <p className="text-primary-400 font-medium">{level.concept}</p>
        </div>
        <div
          className={`text-dark-500 transform transition-transform ${isExpanded ? "rotate-180" : ""}`}
        >
          <svg
            className="w-6 h-6"
            fill="none"
            stroke="currentColor"
            viewBox="0 0 24 24"
          >
            <path
              strokeLinecap="round"
              strokeLinejoin="round"
              strokeWidth={2}
              d="M19 9l-7 7-7-7"
            />
          </svg>
        </div>
      </div>

      {/* Content */}
      <motion.div
        initial={false}
        animate={{
          height: isExpanded ? "auto" : 0,
          opacity: isExpanded ? 1 : 0,
        }}
        transition={{ duration: 0.3 }}
        className="overflow-hidden"
      >
        <div className="pt-4 border-t border-dark-800 space-y-4">
          <div>
            <h4 className="text-sm font-semibold text-dark-400 uppercase tracking-wide mb-2">
              Analogy
            </h4>
            <p className="text-dark-200">{level.analogy}</p>
          </div>

          <div>
            <h4 className="text-sm font-semibold text-dark-400 uppercase tracking-wide mb-2">
              How It Works
            </h4>
            <div className="code-block">
              {level.example.map((line, i) => (
                <div key={i} className="text-primary-300 py-1">
                  {line}
                </div>
              ))}
            </div>
          </div>

          <div>
            <h4 className="text-sm font-semibold text-dark-400 uppercase tracking-wide mb-2">
              Key Insight
            </h4>
            <p className="text-dark-200 italic">{level.problem}</p>
          </div>

          <div className="bg-primary-900/20 border border-primary-800/30 rounded-lg p-4">
            <p className="text-primary-300 font-mono text-sm">
              💡 {level.jargon}
            </p>
          </div>
        </div>
      </motion.div>
    </motion.div>
  );
};

const CheatSheet = () => {
  const questions = [
    {
      q: "Why is this faster?",
      a: "We moved from memory-bound to compute-bound operations using speculative decoding.",
    },
    {
      q: "Does it lower quality?",
      a: "No. It is mathematically identical to the target model. We rely on Rejection Sampling to guarantee accuracy.",
    },
    {
      q: "Why PagedAttention?",
      a: "To reduce KV-cache fragmentation, allowing us to fit the extra Draft Model on consumer hardware.",
    },
  ];

  return (
    <motion.div
      initial={{ opacity: 0, y: 30 }}
      whileInView={{ opacity: 1, y: 0 }}
      viewport={{ once: true }}
      className="card bg-gradient-to-br from-primary-900/20 to-purple-900/20 border-primary-700/50"
    >
      <h3 className="text-2xl font-bold text-primary-300 mb-6 flex items-center gap-3">
        <span className="text-3xl">🎓</span>
        The Cheat Sheet for Judges
      </h3>

      <div className="space-y-4">
        {questions.map((item, i) => (
          <div
            key={i}
            className="bg-dark-950/50 rounded-lg p-4 border border-dark-800"
          >
            <div className="font-bold text-primary-400 mb-2">{item.q}</div>
            <div className="text-dark-200">{item.a}</div>
          </div>
        ))}
      </div>
    </motion.div>
  );
};

const Education = () => {
  return (
    <section id="education" className="bg-dark-950 py-20">
      <div className="section-container">
        <motion.div
          initial={{ opacity: 0, y: 30 }}
          whileInView={{ opacity: 1, y: 0 }}
          viewport={{ once: true }}
          className="text-center mb-16"
        >
          <h2 className="text-5xl font-bold mb-4">
            <span className="gradient-text">
              The "Senior Engineer" Crash Course
            </span>
          </h2>
          <p className="text-xl text-dark-400 max-w-3xl mx-auto">
            From "AI Beginner" to "Systems Architect" in 24 hours. Understand
            the core concepts behind Helix.
          </p>
        </motion.div>

        {/* Level Cards */}
        <div className="space-y-6 mb-12">
          {levels.map((level, index) => (
            <LevelCard key={level.id} level={level} index={index} />
          ))}
        </div>

        {/* Cheat Sheet */}
        <CheatSheet />
      </div>
    </section>
  );
};

export default Education;
