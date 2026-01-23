#!/usr/bin/env python
"""
Helix Inference Engine - Entry Point

Start the server with:
    python run.py

Or with custom settings:
    python run.py --port 8080 --host 0.0.0.0
"""

import argparse
import uvicorn
import logging


def main():
    parser = argparse.ArgumentParser(
        description="Helix Speculative Decoding Inference Engine"
    )
    parser.add_argument(
        "--host",
        type=str,
        default="127.0.0.1",
        help="Host to bind to (default: 127.0.0.1)"
    )
    parser.add_argument(
        "--port",
        type=int,
        default=8000,
        help="Port to bind to (default: 8000)"
    )
    parser.add_argument(
        "--reload",
        action="store_true",
        help="Enable auto-reload for development"
    )
    parser.add_argument(
        "--log-level",
        type=str,
        default="info",
        choices=["debug", "info", "warning", "error"],
        help="Logging level (default: info)"
    )
    
    args = parser.parse_args()
    
    # Configure logging
    logging.basicConfig(
        level=getattr(logging, args.log_level.upper()),
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    )
    
    print("""
    ╦ ╦╔═╗╦  ╦═╗ ╦
    ╠═╣║╣ ║  ║╔╩╦╝
    ╩ ╩╚═╝╩═╝╩╩ ╚═
    Speculative Decoding Inference Engine
    ──────────────────────────────────────
    """)
    print(f"    Starting server at http://{args.host}:{args.port}")
    print(f"    Swagger docs at http://{args.host}:{args.port}/docs")
    print(f"    ReDoc at http://{args.host}:{args.port}/redoc")
    print()
    
    # Run server
    uvicorn.run(
        "src.api:app",
        host=args.host,
        port=args.port,
        reload=args.reload,
        log_level=args.log_level,
    )


if __name__ == "__main__":
    main()
