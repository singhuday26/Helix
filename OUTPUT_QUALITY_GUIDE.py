"""
Output Quality Improvement Guide for Helix

How to get better, more coherent, and more useful text generation
"""

from src.inference import HelixEngine, GenerationConfig

# ============================================
# 1. TEMPERATURE TUNING (Most Important!)
# ============================================

# Lower temperature = more focused, deterministic output
# Higher temperature = more creative, diverse output

config_focused = GenerationConfig(
    max_tokens=50,
    temperature=0.3,  # Very focused, factual
    use_speculative=True
)

config_balanced = GenerationConfig(
    max_tokens=50,
    temperature=0.7,  # Balanced (default)
    use_speculative=True
)

config_creative = GenerationConfig(
    max_tokens=50,
    temperature=1.0,  # More creative, diverse
    use_speculative=True
)

# ============================================
# 2. TOP-P (NUCLEUS SAMPLING)
# ============================================

# Control diversity by probability mass
# Lower top_p = more conservative choices
# Higher top_p = more diverse vocabulary

config_conservative = GenerationConfig(
    max_tokens=50,
    temperature=0.7,
    top_p=0.85,  # Only consider top 85% probability tokens
    use_speculative=True
)

config_diverse = GenerationConfig(
    max_tokens=50,
    temperature=0.7,
    top_p=0.95,  # Consider top 95% probability tokens
    use_speculative=True
)

# ============================================
# 3. TOP-K SAMPLING
# ============================================

# Limit to top K most likely tokens
config_restricted = GenerationConfig(
    max_tokens=50,
    temperature=0.7,
    top_k=40,  # Only consider top 40 tokens at each step
    use_speculative=True
)

# ============================================
# 4. BETTER PROMPTING
# ============================================

# BAD: Vague, incomplete prompts
bad_prompt = "AI is"

# GOOD: Clear, specific, with context
good_prompt = "Artificial Intelligence is transforming healthcare by"

# BEST: Structured prompts with examples (few-shot)
best_prompt = """Task: Complete the sentence with a technical explanation.

Example 1:
Input: Machine learning helps businesses by
Output: analyzing large datasets to identify patterns and predict customer behavior.

Example 2:
Input: Cloud computing enables developers to
Output: deploy scalable applications without managing physical infrastructure.

Now complete this:
Input: Artificial Intelligence is transforming healthcare by
Output:"""

# ============================================
# 5. SYSTEM PROMPTS (If using chat models)
# ============================================

# For TinyLlama-Chat, use the proper chat format
chat_prompt = """<|system|>
You are a helpful AI assistant that provides clear, concise, and accurate information.
</s>
<|user|>
Explain how neural networks learn.
</s>
<|assistant|>
"""

# ============================================
# 6. REPETITION PENALTY
# ============================================

# Prevent model from repeating itself
config_no_repeat = GenerationConfig(
    max_tokens=50,
    temperature=0.7,
    repetition_penalty=1.2,  # Penalize repeated tokens
    use_speculative=True
)

# ============================================
# RECOMMENDED SETTINGS BY USE CASE
# ============================================

# Factual/Technical Writing
FACTUAL_CONFIG = GenerationConfig(
    max_tokens=100,
    temperature=0.5,
    top_p=0.9,
    top_k=50,
    repetition_penalty=1.1,
    use_speculative=True
)

# Creative Writing
CREATIVE_CONFIG = GenerationConfig(
    max_tokens=200,
    temperature=0.9,
    top_p=0.95,
    top_k=100,
    repetition_penalty=1.0,
    use_speculative=True
)

# Code Generation
CODE_CONFIG = GenerationConfig(
    max_tokens=150,
    temperature=0.2,
    top_p=0.85,
    top_k=30,
    repetition_penalty=1.15,
    use_speculative=True
)

# ============================================
# EXAMPLE USAGE
# ============================================

if __name__ == "__main__":
    engine = HelixEngine()
    
    # Test different configs
    prompt = "The key to building scalable software systems is"
    
    print("=== LOW TEMPERATURE (Focused) ===")
    result1 = engine.generate(prompt, GenerationConfig(
        max_tokens=30, temperature=0.3, use_speculative=True
    ))
    print(result1.generated_text)
    
    print("\n=== MEDIUM TEMPERATURE (Balanced) ===")
    result2 = engine.generate(prompt, GenerationConfig(
        max_tokens=30, temperature=0.7, use_speculative=True
    ))
    print(result2.generated_text)
    
    print("\n=== HIGH TEMPERATURE (Creative) ===")
    result3 = engine.generate(prompt, GenerationConfig(
        max_tokens=30, temperature=1.2, use_speculative=True
    ))
    print(result3.generated_text)
    
    print("\n=== WITH BETTER PROMPT ===")
    better_prompt = """In software engineering, building scalable systems requires three key principles:
1. Modular architecture
2. Horizontal scaling
3."""
    result4 = engine.generate(better_prompt, GenerationConfig(
        max_tokens=30, temperature=0.6, use_speculative=True
    ))
    print(result4.generated_text)

print("\n💡 KEY TAKEAWAYS:")
print("1. Lower temperature (0.3-0.5) for factual/technical content")
print("2. Higher temperature (0.8-1.2) for creative writing")
print("3. Use structured prompts with examples (few-shot)")
print("4. Add context and specificity to your prompts")
print("5. Combine temperature + top_p + top_k for best control")
