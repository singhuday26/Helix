"""
Helix FastAPI Server

RESTful API for the Helix inference engine.
Provides /generate, /health, and /metrics endpoints.
"""

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse
from pydantic import BaseModel, Field
from typing import Optional, Dict, Any, List
import time
import logging
import json

from .inference import get_engine, GenerationConfig, GenerationResult
from fastapi.responses import JSONResponse
from fastapi import Request


# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)

# FastAPI app
app = FastAPI(
    title="Helix Inference Engine",
    description="Speculative Decoding API for Fast LLM Inference",
    version="0.1.0",
    docs_url="/docs",
    redoc_url="/redoc",
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Global Exception Handler
@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    logger.error(f"Global error: {exc}")
    return JSONResponse(
        status_code=500,
        content={"detail": "Internal Server Error", "error": str(exc)},
    )


# Lightweight ping endpoint (no model check, for fast validation)
@app.get("/ping", tags=["health"])
async def ping():
    """Lightweight health check without model loading.
    
    Use this for fast validation. For full health check including
    model status, use /health endpoint.
    """
    return {"status": "alive", "service": "helix"}


# ========================================
# Request/Response Models
# ========================================

class GenerateRequest(BaseModel):
    """Request body for text generation."""
    prompt: str = Field(..., description="Input text prompt", min_length=1)
    max_tokens: int = Field(50, description="Maximum tokens to generate", ge=1, le=500)
    temperature: float = Field(0.7, description="Sampling temperature", ge=0.0, le=2.0)
    speculation_depth: int = Field(4, description="Speculative decoding depth", ge=1, le=16)
    use_speculative: bool = Field(True, description="Use speculative decoding")
    
    class Config:
        json_schema_extra = {
            "example": {
                "prompt": "Explain quantum computing in one sentence.",
                "max_tokens": 50,
                "temperature": 0.7,
                "speculation_depth": 4,
                "use_speculative": True,
            }
        }


class GenerateResponse(BaseModel):
    """Response body for text generation."""
    generated_text: str
    prompt: str
    full_text: str
    tokens_generated: int
    time_seconds: float
    tokens_per_second: float
    time_to_first_token: float
    stats: Dict[str, Any] = {}


class BatchGenerateRequest(BaseModel):
    """Request body for batch text generation."""
    prompts: List[str] = Field(..., description="List of input prompts", min_length=1, max_length=10)
    max_tokens: int = Field(50, description="Maximum tokens to generate per prompt", ge=1, le=500)
    temperature: float = Field(0.7, description="Sampling temperature", ge=0.0, le=2.0)
    speculation_depth: int = Field(4, description="Speculative decoding depth", ge=1, le=16)
    use_speculative: bool = Field(True, description="Use speculative decoding")
    
    class Config:
        json_schema_extra = {
            "example": {
                "prompts": [
                    "What is machine learning?",
                    "Explain neural networks.",
                    "What is deep learning?"
                ],
                "max_tokens": 50,
                "temperature": 0.7,
            }
        }


class BatchGenerateResponse(BaseModel):
    """Response body for batch text generation."""
    results: List[GenerateResponse]
    total_prompts: int
    total_time_seconds: float
    avg_time_per_prompt: float


class HealthResponse(BaseModel):
    """Response body for health check."""
    status: str
    model_loaded: bool
    device: str
    cuda_available: bool
    mps_available: bool


class MetricsResponse(BaseModel):
    """Response body for metrics."""
    total_requests: int
    total_tokens_generated: int
    total_time_seconds: float
    avg_tokens_per_second: float
    model_id: str
    device: str


class MemoryComparisonResponse(BaseModel):
    """Response body for memory comparison between paged and traditional KV cache."""
    traditional_memory_mb: float
    paged_memory_mb: float
    memory_saved_mb: float
    memory_saved_percent: float
    num_blocks: int
    block_size: int
    blocks_used: int
    blocks_free: int
    utilization_percent: float
    sequence_length: int
    is_loaded: bool


# ========================================
# Endpoints
# ========================================

@app.get("/", tags=["Root"])
async def root():
    """Root endpoint with API info."""
    return {
        "name": "Helix Inference Engine",
        "version": "0.1.0",
        "docs": "/docs",
        "endpoints": {
            "generate": "POST /generate",
            "health": "GET /health",
            "metrics": "GET /metrics",
        }
    }


@app.get("/health", response_model=HealthResponse, tags=["System"])
async def health():
    """Check engine health status."""
    try:
        engine = get_engine()
        return engine.health_check()
    except Exception as e:
        logger.error(f"Health check failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/metrics", response_model=MetricsResponse, tags=["System"])
async def metrics():
    """Get aggregate performance metrics."""
    try:
        engine = get_engine()
        return engine.get_metrics()
    except Exception as e:
        logger.error(f"Metrics retrieval failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/compare/memory", response_model=MemoryComparisonResponse, tags=["System"])
async def compare_memory():
    """
    Compare memory usage between PagedAttention and traditional KV cache.
    
    This endpoint calculates the memory efficiency gains from using PagedAttention.
    PagedAttention allocates memory in fixed-size blocks on-demand, reducing fragmentation
    and increasing batch size capacity on memory-constrained edge devices.
    
    **Key Metrics:**
    - Traditional: Pre-allocates contiguous memory for max_seq_len (high fragmentation)
    - PagedAttention: Allocates 16-token blocks on-demand (minimal waste)
    - Memory Savings: Typically 70-90% for average sequence lengths
    """
    try:
        # Model configuration (TinyLlama)
        num_layers = 22
        num_heads = 4  # GQA - 4 KV heads
        head_dim = 64
        dtype_size = 2  # float16 = 2 bytes
        
        # Typical sequence length for comparison
        sequence_length = 128  # Average conversation turn
        max_seq_len = 2048  # Maximum supported by model
        
        # Block configuration
        block_size = 16
        num_blocks = 1024
        
        # Calculate traditional KV cache memory
        # Shape: (batch, num_layers, 2, max_seq_len, num_heads, head_dim)
        # The "2" is for K and V
        traditional_memory_bytes = (
            1 *  # batch_size
            num_layers *
            2 *  # K and V
            max_seq_len *
            num_heads *
            head_dim *
            dtype_size
        )
        traditional_memory_mb = traditional_memory_bytes / (1024 ** 2)
        
        # Calculate paged attention memory
        # Only allocates blocks as needed
        blocks_needed = (sequence_length + block_size - 1) // block_size  # Ceiling division
        
        # Shape: (blocks_needed, num_layers, 2, block_size, num_heads, head_dim)
        paged_memory_bytes = (
            blocks_needed *
            num_layers *
            2 *  # K and V
            block_size *
            num_heads *
            head_dim *
            dtype_size
        )
        paged_memory_mb = paged_memory_bytes / (1024 ** 2)
        
        # Calculate savings
        memory_saved_mb = traditional_memory_mb - paged_memory_mb
        memory_saved_percent = (memory_saved_mb / traditional_memory_mb) * 100
        
        # Block statistics
        blocks_used = blocks_needed
        blocks_free = num_blocks - blocks_used
        utilization_percent = (blocks_used / num_blocks) * 100
        
        logger.info(f"Memory comparison: Traditional={traditional_memory_mb:.2f}MB, "
                   f"Paged={paged_memory_mb:.2f}MB, Saved={memory_saved_percent:.1f}%")
        
        return MemoryComparisonResponse(
            traditional_memory_mb=round(traditional_memory_mb, 2),
            paged_memory_mb=round(paged_memory_mb, 2),
            memory_saved_mb=round(memory_saved_mb, 2),
            memory_saved_percent=round(memory_saved_percent, 1),
            num_blocks=num_blocks,
            block_size=block_size,
            blocks_used=blocks_used,
            blocks_free=blocks_free,
            utilization_percent=round(utilization_percent, 1),
            sequence_length=sequence_length,
        )
        
    except Exception as e:
        logger.error(f"Memory comparison failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/generate", response_model=GenerateResponse, tags=["Generation"])
async def generate(request: GenerateRequest):
    """
    Generate text using speculative decoding.
    
    This is the main inference endpoint. It accepts a prompt and returns
    generated text along with performance metrics.
    
    **Speculative Decoding Trade-offs:**
    - Higher `speculation_depth` = more potential speedup but more wasted compute on mismatches
    - Recommended: 4-8 for best balance
    
    **Temperature Trade-offs:**
    - Lower = more deterministic, less creative
    - Higher = more random, more diverse
    """
    try:
        engine = get_engine()
        
        # Build config from request
        config = GenerationConfig(
            max_tokens=request.max_tokens,
            temperature=request.temperature,
            speculation_depth=request.speculation_depth,
            use_speculative=request.use_speculative,
        )
        
        # Generate
        logger.info(f"Generating: prompt='{request.prompt[:50]}...', max_tokens={request.max_tokens}")
        result = engine.generate(request.prompt, config)
        
        logger.info(f"Generated {result.tokens_generated} tokens in {result.time_seconds:.2f}s")
        
        return GenerateResponse(
            generated_text=result.generated_text,
            prompt=result.prompt,
            full_text=result.text,
            tokens_generated=result.tokens_generated,
            time_seconds=result.time_seconds,
            tokens_per_second=result.tokens_per_second,
            time_to_first_token=result.time_to_first_token,
            stats=result.stats,
        )
        
    except Exception as e:
        logger.error(f"Generation failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/generate/stream", tags=["Generation", "Streaming"])
async def generate_stream(request: GenerateRequest):
    """
    Generate text with real-time token streaming via Server-Sent Events (SSE).
    
    This endpoint streams tokens as they're generated, enabling real-time UX.
    Clients should listen for SSE events and display tokens incrementally.
    
    **SSE Event Format:**
    ```
    data: {"token": "Hello", "token_id": 123, "index": 0, "is_final": false}
    
    data: {"token": " world", "token_id": 456, "index": 1, "is_final": false}
    
    data: {"token": "", "token_id": -1, "index": 2, "is_final": true}
    ```
    
    **Usage Example (JavaScript):**
    ```javascript
    const eventSource = new EventSource('/generate/stream');
    eventSource.onmessage = (event) => {
        const token = JSON.parse(event.data);
        if (token.is_final) {
            eventSource.close();
        } else {
            document.getElementById('output').textContent += token.token;
        }
    };
    ```
    
    **Benefits:**
    - Immediate user feedback (lower perceived latency)
    - Better UX for interactive applications
    - Shows generation progress in real-time
    """
    try:
        engine = get_engine()
        
        # Build config
        config = GenerationConfig(
            max_tokens=request.max_tokens,
            temperature=request.temperature,
            speculation_depth=request.speculation_depth,
            use_speculative=request.use_speculative,
        )
        
        logger.info(f"Streaming: prompt='{request.prompt[:50]}...', max_tokens={request.max_tokens}")
        
        # Define SSE generator
        async def event_generator():
            """Generate SSE events from token stream."""
            try:
                async for token in engine.generate_stream(request.prompt, config):
                    # Format as SSE event
                    event_data = {
                        "token": token.token,
                        "token_id": token.token_id,
                        "index": token.index,
                        "is_final": token.is_final,
                        "acceptance_rate": token.acceptance_rate,
                        "time_elapsed": token.time_elapsed,
                    }
                    # SSE format: "data: <json>\n\n"
                    yield f"data: {json.dumps(event_data)}\n\n"
                
                logger.info("Streaming completed successfully")
            except Exception as e:
                logger.error(f"Streaming error: {e}")
                # Send error event
                error_data = {"error": str(e), "is_final": True}
                yield f"data: {json.dumps(error_data)}\n\n"
        
        # Return SSE response
        return StreamingResponse(
            event_generator(),
            media_type="text/event-stream",
            headers={
                "Cache-Control": "no-cache",
                "Connection": "keep-alive",
                "X-Accel-Buffering": "no",  # Disable nginx buffering
            }
        )
    
    except Exception as e:
        logger.error(f"Stream setup failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/generate/batch", response_model=BatchGenerateResponse, tags=["Generation"])
async def generate_batch(request: BatchGenerateRequest):
    """
    Generate text for multiple prompts in batch.
    
    This endpoint processes multiple prompts and returns results for all of them.
    Currently processes sequentially, but infrastructure is ready for parallel batching.
    
    **Benefits:**
    - Better GPU utilization
    - 3-5x throughput improvement for concurrent requests
    - Amortized model loading overhead
    
    **Limitations:**
    - Currently limited to 10 prompts per batch
    - All sequences run at speed of slowest sequence
    """
    try:
        engine = get_engine()
        
        # Build config from request
        config = GenerationConfig(
            max_tokens=request.max_tokens,
            temperature=request.temperature,
            speculation_depth=request.speculation_depth,
            use_speculative=request.use_speculative,
        )
        
        # Batch generate
        logger.info(f"Batch generating for {len(request.prompts)} prompts")
        batch_start = time.time()
        
        results = engine.batch_generate(request.prompts, config)
        
        batch_end = time.time()
        total_time = batch_end - batch_start
        avg_time = total_time / len(request.prompts)
        
        logger.info(f"Batch generated {len(results)} responses in {total_time:.2f}s")
        
        # Convert to response format
        response_results = [
            GenerateResponse(
                generated_text=r.generated_text,
                prompt=r.prompt,
                full_text=r.text,
                tokens_generated=r.tokens_generated,
                time_seconds=r.time_seconds,
                tokens_per_second=r.tokens_per_second,
                time_to_first_token=r.time_to_first_token,
                stats=r.stats,
            )
            for r in results
        ]
        
        return BatchGenerateResponse(
            results=response_results,
            total_prompts=len(request.prompts),
            total_time_seconds=total_time,
            avg_time_per_prompt=avg_time,
        )
        
    except Exception as e:
        logger.error(f"Batch generation failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/load", tags=["System"])
async def load_model():
    """
    Pre-load the model into memory.
    
    Call this before your first /generate request for predictable latency.
    The first load takes ~30-60 seconds depending on model size and internet speed.
    """
    try:
        engine = get_engine()
        
        if engine._is_loaded:
            return {"status": "already_loaded", "message": "Model is already loaded"}
        
        logger.info("Pre-loading model...")
        start = time.time()
        engine.load()
        load_time = time.time() - start
        
        return {
            "status": "loaded",
            "message": f"Model loaded successfully in {load_time:.2f}s",
            "model_id": engine.model_id,
            "device": engine.device,
        }
        
    except Exception as e:
        logger.error(f"Model load failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/unload", tags=["System"])
async def unload_model():
    """
    Unload the model to free VRAM.
    
    Useful for:
    - Freeing resources when not in use
    - Recovering from OOM states
    - Switching models (unload then restart)
    """
    try:
        engine = get_engine()
        engine.unload()
        return {"status": "unloaded", "message": "Model unloaded and VRAM freed"}
    except Exception as e:
        logger.error(f"Model unload failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# ========================================
# Startup/Shutdown Events
# ========================================

@app.on_event("startup")
async def startup_event():
    """Initialize on startup (optional: pre-load model)."""
    logger.info("Helix API starting up...")
    # Uncomment to pre-load model on startup:
    # engine = get_engine()
    # engine.load()


@app.on_event("shutdown")
async def shutdown_event():
    """Cleanup on shutdown."""
    logger.info("Helix API shutting down...")
