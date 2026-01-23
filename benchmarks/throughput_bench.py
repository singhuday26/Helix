"""
Throughput Benchmark for Helix Inference Engine

Simulates concurrent requests to measure:
- Requests per second at various batch sizes
- System behavior under load
"""

import torch
import time
import sys
import os
import asyncio
import aiohttp
from typing import List
import statistics

# Server URL
BASE_URL = "http://127.0.0.1:8000"


async def make_request(
    session: aiohttp.ClientSession,
    prompt: str,
    max_tokens: int = 30,
) -> dict:
    """Make a single generation request."""
    start = time.time()
    
    payload = {
        "prompt": prompt,
        "max_tokens": max_tokens,
        "temperature": 0.7,
        "use_speculative": True,
    }
    
    async with session.post(f"{BASE_URL}/generate", json=payload) as resp:
        result = await resp.json()
        
    elapsed = time.time() - start
    return {
        "elapsed": elapsed,
        "tokens": result.get("tokens_generated", 0),
        "status": resp.status,
    }


async def benchmark_concurrent(
    num_requests: int,
    concurrency: int,
    prompts: List[str],
) -> dict:
    """Run benchmark with specified concurrency level."""
    
    results = []
    semaphore = asyncio.Semaphore(concurrency)
    
    async def bounded_request(prompt: str):
        async with semaphore:
            return await make_request(session, prompt)
    
    connector = aiohttp.TCPConnector(limit=concurrency)
    async with aiohttp.ClientSession(connector=connector) as session:
        start = time.time()
        
        tasks = [
            bounded_request(prompts[i % len(prompts)])
            for i in range(num_requests)
        ]
        
        results = await asyncio.gather(*tasks)
        
        total_time = time.time() - start
    
    # Compute metrics
    successful = [r for r in results if r["status"] == 200]
    failed = len(results) - len(successful)
    
    latencies = [r["elapsed"] for r in successful]
    total_tokens = sum(r["tokens"] for r in successful)
    
    return {
        "num_requests": num_requests,
        "concurrency": concurrency,
        "total_time_seconds": total_time,
        "requests_per_second": len(successful) / total_time,
        "tokens_per_second": total_tokens / total_time,
        "successful_requests": len(successful),
        "failed_requests": failed,
        "avg_latency": statistics.mean(latencies) if latencies else 0,
        "p50_latency": statistics.median(latencies) if latencies else 0,
        "p99_latency": (
            sorted(latencies)[int(len(latencies) * 0.99)]
            if len(latencies) >= 100 else max(latencies or [0])
        ),
    }


def print_results(results: dict):
    """Pretty print benchmark results."""
    print(f"\n{'='*50}")
    print(f" Concurrency: {results['concurrency']}")
    print(f"{'='*50}")
    print(f" Total Requests:     {results['num_requests']}")
    print(f" Successful:         {results['successful_requests']}")
    print(f" Failed:             {results['failed_requests']}")
    print(f"{'─'*50}")
    print(f" Total Time:         {results['total_time_seconds']:.2f}s")
    print(f" Requests/sec:       {results['requests_per_second']:.2f}")
    print(f" Tokens/sec:         {results['tokens_per_second']:.2f}")
    print(f"{'─'*50}")
    print(f" Avg Latency:        {results['avg_latency']:.3f}s")
    print(f" P50 Latency:        {results['p50_latency']:.3f}s")
    print(f" P99 Latency:        {results['p99_latency']:.3f}s")
    print(f"{'='*50}\n")


async def main():
    print("\n" + "="*60)
    print(" HELIX THROUGHPUT BENCHMARK")
    print("="*60 + "\n")
    
    # Test prompts
    prompts = [
        "What is machine learning?",
        "Explain neural networks.",
        "How does AI work?",
        "What is deep learning?",
        "Describe natural language processing.",
    ]
    
    # Check server health
    print("Checking server health...")
    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(f"{BASE_URL}/health") as resp:
                if resp.status != 200:
                    print(f"ERROR: Server not healthy (status {resp.status})")
                    print("Make sure the server is running: python run.py")
                    return
                health = await resp.json()
                print(f"Server status: {health['status']}")
                if not health.get('model_loaded'):
                    print("Loading model... (this may take a minute)")
                    async with session.post(f"{BASE_URL}/load") as load_resp:
                        load_result = await load_resp.json()
                        print(f"Model loaded: {load_result.get('message', 'OK')}")
    except aiohttp.ClientError as e:
        print(f"ERROR: Cannot connect to server at {BASE_URL}")
        print("Make sure the server is running: python run.py")
        return
    
    # Run benchmarks at different concurrency levels
    concurrency_levels = [1, 2, 4]
    requests_per_level = 10
    
    all_results = []
    
    for concurrency in concurrency_levels:
        print(f"\nRunning benchmark: concurrency={concurrency}, requests={requests_per_level}")
        results = await benchmark_concurrent(
            num_requests=requests_per_level,
            concurrency=concurrency,
            prompts=prompts,
        )
        all_results.append(results)
        print_results(results)
    
    # Summary
    print("\n" + "="*60)
    print(" SUMMARY")
    print("="*60)
    print(f" {'Concurrency':<15} {'Req/sec':<12} {'Tok/sec':<12} {'Avg Lat':<12}")
    print("-"*60)
    for r in all_results:
        print(f" {r['concurrency']:<15} {r['requests_per_second']:<12.2f} {r['tokens_per_second']:<12.2f} {r['avg_latency']:<12.3f}s")
    print("="*60 + "\n")


if __name__ == "__main__":
    asyncio.run(main())
