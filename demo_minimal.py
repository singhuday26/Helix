"""
HELIX DEMO - MINIMAL VERSION
Shows speculative decoding vs baseline in simplest possible form.
Run: python demo_minimal.py
"""

import os
os.environ["HELIX_FORCE_CPU"] = "1"

import time
import torch

print("=" * 60)
print("      HELIX SPECULATIVE DECODING - MINIMAL DEMO")
print("=" * 60)

print("\n⏳ Loading model (GPT-2 small)...")
from transformers import AutoModelForCausalLM, AutoTokenizer

model = AutoModelForCausalLM.from_pretrained("gpt2", use_safetensors=True)
model.eval()
tokenizer = AutoTokenizer.from_pretrained("gpt2")
print("✓ Model loaded!")

prompt = "The future of AI is"
max_new = 20

print(f"\n📝 Prompt: '{prompt}'")
print(f"📊 Generating {max_new} tokens...\n")

# ============ BASELINE ============
print("-" * 60)
print("🐢 BASELINE (token by token):")

input_ids = tokenizer.encode(prompt, return_tensors="pt")

start = time.time()
with torch.no_grad():
    for _ in range(max_new):
        out = model(input_ids)
        next_token = out.logits[:, -1, :].argmax(dim=-1, keepdim=True)
        input_ids = torch.cat([input_ids, next_token], dim=-1)
        if next_token.item() == tokenizer.eos_token_id:
            break
baseline_time = time.time() - start

baseline_text = tokenizer.decode(input_ids[0], skip_special_tokens=True)
baseline_tokens = input_ids.shape[1] - len(tokenizer.encode(prompt))
baseline_tps = baseline_tokens / baseline_time

print(f"   Output: {baseline_text}")
print(f"   Time: {baseline_time:.2f}s | {baseline_tps:.2f} tok/s")

# ============ SPECULATIVE ============
print("\n" + "-" * 60)
print("🚀 SPECULATIVE (verify 4 at once):")

K = 4  # Speculation depth
input_ids = tokenizer.encode(prompt, return_tensors="pt")
generated = 0

start = time.time()
with torch.no_grad():
    while generated < max_new:
        # Step 1: Draft K tokens
        draft_ids = input_ids.clone()
        for _ in range(K):
            out = model(draft_ids)
            next_token = out.logits[:, -1, :].argmax(dim=-1, keepdim=True)
            draft_ids = torch.cat([draft_ids, next_token], dim=-1)
        
        # Step 2: Verify ALL at once (single forward pass)
        target_out = model(draft_ids)
        target_predictions = target_out.logits[:, -(K+1):-1, :].argmax(dim=-1)
        draft_tokens = draft_ids[0, -K:]
        
        # Step 3: Accept matching tokens
        matches = (target_predictions[0] == draft_tokens).int()
        first_mismatch = (1 - matches).argmax().item()
        if matches[first_mismatch] == 1:  # All matched
            accept_count = K
        else:
            accept_count = first_mismatch
        
        # Add accepted + 1 resampled
        if accept_count == K:
            # All accepted, add bonus token
            bonus = target_out.logits[:, -1, :].argmax(dim=-1, keepdim=True)
            input_ids = torch.cat([input_ids, draft_tokens.unsqueeze(0), bonus], dim=-1)
            generated += K + 1
        else:
            # Partial accept
            accepted = draft_tokens[:accept_count]
            resampled = target_predictions[0, accept_count].unsqueeze(0)
            input_ids = torch.cat([
                input_ids, 
                accepted.unsqueeze(0) if accept_count > 0 else torch.tensor([[]], dtype=torch.long),
                resampled.unsqueeze(0)
            ], dim=-1)
            generated += accept_count + 1
        
        if tokenizer.eos_token_id in input_ids[0, -generated:]:
            break

spec_time = time.time() - start

spec_text = tokenizer.decode(input_ids[0], skip_special_tokens=True)
spec_tokens = input_ids.shape[1] - len(tokenizer.encode(prompt))
spec_tps = spec_tokens / spec_time

print(f"   Output: {spec_text}")
print(f"   Time: {spec_time:.2f}s | {spec_tps:.2f} tok/s")

# ============ RESULTS ============
print("\n" + "=" * 60)
print("📊 COMPARISON:")
print(f"   Baseline:    {baseline_time:.2f}s ({baseline_tps:.2f} tok/s)")
print(f"   Speculative: {spec_time:.2f}s ({spec_tps:.2f} tok/s)")

speedup = baseline_time / spec_time if spec_time > 0 else 1
tps_gain = spec_tps / baseline_tps if baseline_tps > 0 else 1

print(f"\n   ⚡ SPEEDUP: {speedup:.2f}x faster!")
print(f"   ⚡ THROUGHPUT: {tps_gain:.2f}x more tokens/sec!")
print("=" * 60)
print("✓ Demo complete!")
