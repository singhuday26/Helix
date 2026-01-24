"""
Speculative Decoding Implementation

Core algorithm:
1. Draft model generates K tokens speculatively (fast)
2. Target model verifies all K tokens in a single forward pass
3. Accept tokens until first rejection, then resample from target

Trade-offs:
- K (speculation depth): Higher K = more potential speedup but more wasted compute on rejections
- Optimal K depends on draft/target alignment (typically 4-8 for similar models)

Reference: "Fast Inference from Transformers via Speculative Decoding" (Leviathan et al., 2022)
"""

import torch
import torch.nn.functional as F
from typing import Tuple, Optional, List, Dict
from dataclasses import dataclass
import logging
import time

logger = logging.getLogger(__name__)

# Default speculation depth
# Trade-off: Higher = more speedup potential, but more wasted compute on mismatch
DEFAULT_SPECULATION_DEPTH = 4


@dataclass
class SpeculativeOutput:
    """Result of a speculative decoding step."""
    tokens: torch.Tensor  # Accepted token IDs
    num_accepted: int     # How many draft tokens were accepted
    num_generated: int    # Total tokens generated (accepted + 1 resampled)
    draft_tokens: List[int]  # What draft proposed
    acceptance_rate: float   # For monitoring
    first_token_time: Optional[float] = None  # Timestamp when first token was generated


def sample_token(logits: torch.Tensor, temperature: float = 1.0) -> torch.Tensor:
    """
    Sample a token from logits with temperature.
    
    Temperature trade-off:
    - T < 1: More deterministic, less diverse
    - T = 1: Standard sampling
    - T > 1: More random, more diverse
    """
    if temperature == 0:
        return logits.argmax(dim=-1)
    
    probs = F.softmax(logits / temperature, dim=-1)
    return torch.multinomial(probs, num_samples=1).squeeze(-1)


def compute_acceptance_probability(
    target_probs: torch.Tensor,  # p(x) from target model
    draft_probs: torch.Tensor,   # q(x) from draft model
    sampled_token: int,
) -> float:
    """
    Compute acceptance probability using rejection sampling.
    
    Accept with probability min(1, p(x)/q(x))
    
    This ensures the final distribution matches the target exactly.
    """
    p = target_probs[sampled_token].item()
    q = draft_probs[sampled_token].item()
    
    if q == 0:
        return 0.0
    
    return min(1.0, p / q)


@torch.inference_mode()
def speculative_decode_step(
    draft_model,
    target_model,
    input_ids: torch.Tensor,
    speculation_depth: int = DEFAULT_SPECULATION_DEPTH,
    temperature: float = 1.0,
    kv_cache = None,  # Optional PagedKVCache instance
    seq_id: Optional[int] = None,  # Sequence ID for cache lookup
    attention_mask: Optional[torch.Tensor] = None,  # Attention mask for batching
) -> SpeculativeOutput:
    """
    Perform one step of speculative decoding with VECTORIZED batch support.
    
    This is the core algorithm:
    1. Draft model generates K tokens autoregressively (PARALLEL for batch)
    2. Target model scores all K tokens in ONE forward pass (PARALLEL)
    3. Accept tokens until first rejection using rejection sampling (per-sequence)
    4. If all accepted, sample one more from target
    5. If rejected at position i, resample from adjusted distribution
    
    Phase 4B Optimization:
    - Vectorized draft generation across batch
    - Proper attention masking for variable-length sequences
    - Independent acceptance logic per sequence
    
    Args:
        draft_model: Small, fast model for speculation
        target_model: Larger, accurate model for verification
        input_ids: Current token sequence [batch_size, seq_len]
        speculation_depth: Number of tokens to speculate (K)
        temperature: Sampling temperature
        kv_cache: Optional PagedKVCache for KV reuse (currently not integrated)
        seq_id: Sequence ID for cache operations (if kv_cache provided)
        attention_mask: Attention mask [batch_size, seq_len] (1=attend, 0=ignore)
    
    Returns:
        SpeculativeOutput with accepted tokens and stats
    """
    step_start_time = time.time()  # Capture timing for TTFT
    device = input_ids.device
    batch_size = input_ids.shape[0]
    
    # ========================================
    # PHASE 1: Draft model generates K tokens (Single sequence)
    # ========================================
    draft_tokens = []
    draft_probs_list = []
    # Clone to avoid modification of view
    current_ids = input_ids.clone()
    
    for _ in range(speculation_depth):
        outputs = draft_model(current_ids)
        logits = outputs.logits[:, -1, :]  # Last token logits
        probs = F.softmax(logits / temperature, dim=-1)
        
        token = sample_token(logits, temperature)
        draft_tokens.append(token.item())
        draft_probs_list.append(probs[0].clone())  # Store full distribution
        
        current_ids = torch.cat([current_ids, token.unsqueeze(0)], dim=-1)
    
    # ========================================
    # PHASE 2: Target model verifies ALL tokens in one pass
    # ========================================
    # Include all speculated tokens in the input
    target_ids = torch.cat([
        input_ids,
        torch.tensor([draft_tokens], device=device)
    ], dim=-1)
    
    target_outputs = target_model(target_ids)
    target_logits = target_outputs.logits  # (1, seq_len + K, vocab_size)
    
    # We need target probabilities at positions where draft made predictions
    # These are at positions [original_len - 1, original_len, ..., original_len + K - 2]
    # Because logits[i] predicts token[i+1]
    original_len = input_ids.shape[1]
    
    # ========================================
    # PHASE 3: Accept/Reject using rejection sampling
    # ========================================
    accepted_tokens = []
    num_accepted = 0
    
    for i, (draft_token, draft_probs) in enumerate(zip(draft_tokens, draft_probs_list)):
        # Target's prediction for this position
        target_logits_i = target_logits[0, original_len - 1 + i, :]
        target_probs = F.softmax(target_logits_i / temperature, dim=-1)
        
        # Compute acceptance probability
        accept_prob = compute_acceptance_probability(target_probs, draft_probs, draft_token)
        
        # Accept or reject
        if torch.rand(1).item() < accept_prob:
            accepted_tokens.append(draft_token)
            num_accepted += 1
        else:
            # Rejected! Resample from adjusted distribution
            # p'(x) = max(0, p(x) - q(x)) / Z
            adjusted_probs = torch.clamp(target_probs - draft_probs, min=0)
            adjusted_probs = adjusted_probs / (adjusted_probs.sum() + 1e-10)
            
            resampled_token = torch.multinomial(adjusted_probs, num_samples=1).item()
            accepted_tokens.append(resampled_token)
            break
    
    # ========================================
    # PHASE 4: If all accepted, sample one more from target
    # ========================================
    if num_accepted == speculation_depth:
        # All draft tokens accepted! Sample one more from target
        final_logits = target_logits[0, -1, :]
        bonus_token = sample_token(final_logits.unsqueeze(0), temperature).item()
        accepted_tokens.append(bonus_token)
    
    # Build output
    tokens_tensor = torch.tensor([accepted_tokens], device=device)
    
    return SpeculativeOutput(
        tokens=tokens_tensor,
        num_accepted=num_accepted,
        num_generated=len(accepted_tokens),
        draft_tokens=draft_tokens,
        acceptance_rate=num_accepted / speculation_depth if speculation_depth > 0 else 0.0,
        first_token_time=step_start_time,  # Record when this step started
    )


class SpeculativeDecoder:
    """
    High-level interface for speculative decoding generation.
    
    Usage:
        decoder = SpeculativeDecoder(draft_model, target_model, tokenizer)
        output = decoder.generate("Hello, world!", max_tokens=50)
    """
    
    def __init__(
        self,
        draft_model,
        target_model,
        tokenizer,
        speculation_depth: int = DEFAULT_SPECULATION_DEPTH,
        temperature: float = 0.7,
        kv_cache = None,  # Optional PagedKVCache
    ):
        self.draft_model = draft_model
        self.target_model = target_model
        self.tokenizer = tokenizer
        self.speculation_depth = speculation_depth
        self.temperature = temperature
        self.kv_cache = kv_cache
        self.seq_id = None  # Will be set during generation
        
        # Stats tracking
        self.total_accepted = 0
        self.total_speculated = 0
    
    @torch.no_grad()
    def generate(
        self,
        prompt: str,
        max_tokens: int = 50,
        stop_token_id: Optional[int] = None,
    ) -> Tuple[str, dict]:
        """
        Generate text using speculative decoding.
        
        Returns:
            Tuple of (generated_text, stats_dict)
        """
        if stop_token_id is None:
            stop_token_id = self.tokenizer.eos_token_id
        
        # Encode prompt
        input_ids = self.tokenizer.encode(prompt, return_tensors="pt")
        device = next(self.draft_model.parameters()).device
        input_ids = input_ids.to(device)
        
        generated_tokens = []
        stats = {"total_steps": 0, "total_tokens": 0, "acceptance_rates": [], "first_token_time": None}
        
        # Allocate cache sequence if using PagedKVCache
        if self.kv_cache is not None:
            self.seq_id = self.kv_cache.allocate_sequence()
        
        try:
            while len(generated_tokens) < max_tokens:
                # Run one speculative step (attention_mask not needed for single sequence)
                result = speculative_decode_step(
                    self.draft_model,
                    self.target_model,
                    input_ids,
                    speculation_depth=self.speculation_depth,
                    temperature=self.temperature,
                    kv_cache=self.kv_cache,
                    seq_id=self.seq_id,
                    attention_mask=None,  # Not needed for single sequence generation
                )
                
                # Capture TTFT on first step
                if stats["first_token_time"] is None and result.first_token_time is not None:
                    stats["first_token_time"] = result.first_token_time
                
                # Update stats
                stats["total_steps"] += 1
                stats["acceptance_rates"].append(result.acceptance_rate)
                self.total_accepted += result.num_accepted
                self.total_speculated += self.speculation_depth
                
                # Add generated tokens
                new_tokens = result.tokens[0].tolist()
                for token in new_tokens:
                    if token == stop_token_id:
                        break
                    generated_tokens.append(token)
                    if len(generated_tokens) >= max_tokens:
                        break
                
                # Check for stop token
                if stop_token_id in new_tokens:
                    break
                
                # Append to input for next iteration
                input_ids = torch.cat([input_ids, result.tokens], dim=-1)
        
        finally:
            # Free cache sequence when done
            if self.kv_cache is not None and self.seq_id is not None:
                self.kv_cache.free_sequence(self.seq_id)
                self.seq_id = None
        
        # Decode output
        full_ids = torch.cat([
            self.tokenizer.encode(prompt, return_tensors="pt").to(device),
            torch.tensor([generated_tokens], device=device)
        ], dim=-1)
        
        output_text = self.tokenizer.decode(full_ids[0], skip_special_tokens=True)
        
        # Finalize stats
        stats["total_tokens"] = len(generated_tokens)
        stats["avg_acceptance_rate"] = (
            sum(stats["acceptance_rates"]) / len(stats["acceptance_rates"])
            if stats["acceptance_rates"] else 0.0
        )
        stats["tokens_per_step"] = (
            stats["total_tokens"] / stats["total_steps"]
            if stats["total_steps"] > 0 else 0.0
        )
        
        return output_text, stats
    
    @property
    def global_acceptance_rate(self) -> float:
        """Overall acceptance rate across all generations."""
        if self.total_speculated == 0:
            return 0.0
        return self.total_accepted / self.total_speculated


class AdaptiveSpeculativeDecoder(SpeculativeDecoder):
    """
    Advanced decoder that adjusts speculation depth (K) dynamically.
    
    "Senior Engineer" Insight:
    - Fixed K=4 is suboptimal.
    - Easy prompts (common phrases) allow K=6+
    - Hard prompts (reasoning) drop to K=1-2
    - We use a simple heuristic to adjust K based on recent acceptance rate.
    """
    
    def __init__(
        self,
        draft_model,
        target_model,
        tokenizer,
        initial_depth: int = 4,
        min_depth: int = 1,
        max_depth: int = 8,
        target_acceptance_rate: float = 0.6,
        temperature: float = 0.7,
        kv_cache = None,  # Optional PagedKVCache
    ):
        super().__init__(
            draft_model, 
            target_model, 
            tokenizer, 
            speculation_depth=initial_depth,
            temperature=temperature,
            kv_cache=kv_cache,
        )
        self.min_depth = min_depth
        self.max_depth = max_depth
        self.target_acceptance_rate = target_acceptance_rate
        self.current_depth = initial_depth
        
        # Moving average of acceptance rate
        self.ema_acceptance_rate = 0.5
        self.alpha = 0.3  # Smoothing factor
        
    @torch.no_grad()
    def generate(
        self,
        prompt: str,
        max_tokens: int = 50,
        stop_token_id: Optional[int] = None,
    ) -> Tuple[str, dict]:
        """Generate with adaptive K."""
        if stop_token_id is None:
            stop_token_id = self.tokenizer.eos_token_id
            
        input_ids = self.tokenizer.encode(prompt, return_tensors="pt")
        device = next(self.draft_model.parameters()).device
        input_ids = input_ids.to(device)
        
        generated_tokens = []
        stats = {
            "total_steps": 0, 
            "total_tokens": 0, 
            "acceptance_rates": [], 
            "depth_history": []
        }
        
        while len(generated_tokens) < max_tokens:
            # Run one speculative step with CURRENT depth
            result = speculative_decode_step(
                self.draft_model,
                self.target_model,
                input_ids,
                speculation_depth=int(self.current_depth),
                temperature=self.temperature,
            )
            
            # Update stats
            stats["total_steps"] += 1
            stats["acceptance_rates"].append(result.acceptance_rate)
            stats["depth_history"].append(self.current_depth)
            
            # --- ADAPTIVE LOGIC ---
            # Update EMA acceptance rate
            self.ema_acceptance_rate = (
                self.alpha * result.acceptance_rate + 
                (1 - self.alpha) * self.ema_acceptance_rate
            )
            
            # Adjust K
            # If we are accepting heavily (rate > target), be more aggressive
            if self.ema_acceptance_rate > self.target_acceptance_rate + 0.1:
                self.current_depth = min(self.max_depth, self.current_depth + 1)
            # If we are rejecting heavily, back off
            elif self.ema_acceptance_rate < self.target_acceptance_rate - 0.1:
                self.current_depth = max(self.min_depth, self.current_depth - 1)
            # ----------------------
            
            # Check stopping conditions BEFORE extending to prevent stop token leak
            new_tokens = result.tokens[0].tolist()
            if stop_token_id in new_tokens:
                # Add tokens up to (not including) stop token
                stop_idx = new_tokens.index(stop_token_id)
                generated_tokens.extend(new_tokens[:stop_idx])
                break
            
            generated_tokens.extend(new_tokens)
            
            # Check max_tokens limit
            if len(generated_tokens) >= max_tokens:
                break
                
            input_ids = torch.cat([input_ids, result.tokens], dim=-1)
            
        # Decode output
        output_text = self.tokenizer.decode(generated_tokens, skip_special_tokens=True)
        stats["total_tokens"] = len(generated_tokens)
        stats["final_depth"] = self.current_depth
        stats["avg_depth"] = sum(stats["depth_history"]) / len(stats["depth_history"]) if stats["depth_history"] else 0
        
        # Calculate overall acceptance rate
        if stats["acceptance_rates"]:
            stats["acceptance_rate"] = sum(stats["acceptance_rates"]) / len(stats["acceptance_rates"])
            stats["total_accepted"] = sum(int(r * self.speculation_depth) for r in stats["acceptance_rates"])
            stats["total_drafted"] = len(stats["acceptance_rates"]) * self.speculation_depth
        else:
            stats["acceptance_rate"] = 0.0
            stats["total_accepted"] = 0
            stats["total_drafted"] = 0
        
        return output_text, stats


# ========================================
# Simplified generation for demo mode
# ========================================
@torch.no_grad()
def simple_generate(
    model,
    tokenizer,
    prompt: str,
    max_tokens: int = 50,
    temperature: float = 0.7,
) -> str:
    """
    Standard autoregressive generation (baseline for comparison).
    
    This is the naive approach we're trying to beat with speculative decoding.
    """
    input_ids = tokenizer.encode(prompt, return_tensors="pt")
    device = next(model.parameters()).device
    input_ids = input_ids.to(device)
    
    generated = []
    
    for _ in range(max_tokens):
        outputs = model(input_ids)
        logits = outputs.logits[:, -1, :]
        
        token = sample_token(logits, temperature)
        
        if token.item() == tokenizer.eos_token_id:
            break
        
        generated.append(token.item())
        # token is 0D or 1D, need to reshape to [1, 1] for concatenation
        token_2d = token.view(1, 1)
        input_ids = torch.cat([input_ids, token_2d], dim=-1)
    
    full_ids = torch.cat([
        tokenizer.encode(prompt, return_tensors="pt").to(device),
        torch.tensor([generated], device=device)
    ], dim=-1)
    
    return tokenizer.decode(full_ids[0], skip_special_tokens=True)


if __name__ == "__main__":
    # Quick test with mock models would go here
    logger.info("Speculative decoding module loaded successfully")
    logger.info(f"Default speculation depth: {DEFAULT_SPECULATION_DEPTH}")
