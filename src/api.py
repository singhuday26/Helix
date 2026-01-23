"""
Helix FastAPI Server

RESTful API for the Helix inference engine.
Provides /generate, /health, and /metrics endpoints.
"""

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
from typing import Optional, Dict, Any
import time
import logging

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
