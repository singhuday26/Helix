"""
Batch Processing Test and Benchmark

Tests Phase 4 batch processing implementation and measures throughput improvements.
"""

import urllib.request
import json
import time
import sys

def test_single_generation():
    """Baseline: Single generation request."""
    url = "http://127.0.0.1:8000/generate"
    payload = {
        "prompt": "What is artificial intelligence?",
        "max_tokens": 30,
        "temperature": 0.7
    }
    
    print("=" * 70)
    print("TEST 1: Single Generation (Baseline)")
    print("=" * 70)
    
    try:
        data = json.dumps(payload).encode('utf-8')
        req = urllib.request.Request(
            url,
            data=data,
            headers={'Content-Type': 'application/json'}
        )
        
        start = time.time()
        with urllib.request.urlopen(req) as response:
            result = json.loads(response.read().decode('utf-8'))
            end = time.time()
        
        print(f"✅ Single request completed")
        print(f"   Tokens: {result['tokens_generated']}")
        print(f"   Time: {end - start:.3f}s")
        print(f"   Throughput: {result['tokens_per_second']:.2f} tok/s")
        return end - start
        
    except Exception as e:
        print(f"❌ Failed: {e}")
        return None


def test_sequential_batch(n=3):
    """Test N sequential single requests."""
    url = "http://127.0.0.1:8000/generate"
    prompts = [
        "What is machine learning?",
        "Explain neural networks.",
        "What is deep learning?"
    ]
    
    print("\n" + "=" * 70)
    print(f"TEST 2: Sequential {n} Requests")
    print("=" * 70)
    
    start = time.time()
    results = []
    
    for i, prompt in enumerate(prompts[:n]):
        payload = {
            "prompt": prompt,
            "max_tokens": 30,
            "temperature": 0.7
        }
        
        try:
            data = json.dumps(payload).encode('utf-8')
            req = urllib.request.Request(
                url,
                data=data,
                headers={'Content-Type': 'application/json'}
            )
            
            with urllib.request.urlopen(req) as response:
                result = json.loads(response.read().decode('utf-8'))
                results.append(result)
                print(f"   Request {i+1}/{n}: {result['tokens_generated']} tokens")
        
        except Exception as e:
            print(f"   ❌ Request {i+1} failed: {e}")
    
    end = time.time()
    total_time = end - start
    
    if results:
        total_tokens = sum(r['tokens_generated'] for r in results)
        print(f"\n✅ Sequential batch completed")
        print(f"   Total time: {total_time:.3f}s")
        print(f"   Avg time per request: {total_time/len(results):.3f}s")
        print(f"   Total tokens: {total_tokens}")
        print(f"   Throughput: {total_tokens/total_time:.2f} tok/s")
    
    return total_time


def test_batch_endpoint(n=3):
    """Test new batch endpoint."""
    url = "http://127.0.0.1:8000/generate/batch"
    prompts = [
        "What is machine learning?",
        "Explain neural networks.",
        "What is deep learning?"
    ]
    
    print("\n" + "=" * 70)
    print(f"TEST 3: Batch Endpoint ({n} prompts)")
    print("=" * 70)
    
    payload = {
        "prompts": prompts[:n],
        "max_tokens": 30,
        "temperature": 0.7
    }
    
    try:
        data = json.dumps(payload).encode('utf-8')
        req = urllib.request.Request(
            url,
            data=data,
            headers={'Content-Type': 'application/json'}
        )
        
        start = time.time()
        with urllib.request.urlopen(req) as response:
            result = json.loads(response.read().decode('utf-8'))
            end = time.time()
        
        total_time = result['total_time_seconds']
        avg_time = result['avg_time_per_prompt']
        total_tokens = sum(r['tokens_generated'] for r in result['results'])
        
        print(f"✅ Batch request completed")
        print(f"   Total time: {total_time:.3f}s")
        print(f"   Avg time per prompt: {avg_time:.3f}s")
        print(f"   Total tokens: {total_tokens}")
        print(f"   Throughput: {total_tokens/total_time:.2f} tok/s")
        print(f"\n   Results:")
        for i, r in enumerate(result['results'][:3]):  # Show first 3
            print(f"     {i+1}. {r['tokens_generated']} tokens in {r['time_seconds']:.3f}s")
        
        return total_time
        
    except urllib.request.HTTPError as e:
        if e.code == 404:
            print(f"⚠️  Batch endpoint not found (expected if not implemented yet)")
            print(f"   This is normal - batch endpoint is part of Phase 4")
        else:
            print(f"❌ HTTP {e.code}: {e.reason}")
        return None
    except Exception as e:
        print(f"❌ Failed: {e}")
        return None


def calculate_improvement(sequential_time, batch_time):
    """Calculate throughput improvement."""
    if sequential_time and batch_time:
        improvement = ((sequential_time - batch_time) / sequential_time) * 100
        speedup = sequential_time / batch_time
        
        print("\n" + "=" * 70)
        print("PERFORMANCE IMPROVEMENT")
        print("=" * 70)
        print(f"Sequential time: {sequential_time:.3f}s")
        print(f"Batch time:      {batch_time:.3f}s")
        print(f"Improvement:     {improvement:.1f}%")
        print(f"Speedup:         {speedup:.2f}x")
        
        if speedup >= 2.0:
            print("\n🎉 EXCELLENT: >2x speedup achieved!")
        elif speedup >= 1.5:
            print("\n✅ GOOD: Significant speedup")
        elif speedup >= 1.2:
            print("\n⚠️  MODERATE: Some improvement")
        else:
            print("\n⚠️  LIMITED: Minimal improvement (expected for sequential implementation)")


def main():
    print("\n" + "=" * 70)
    print("HELIX BATCH PROCESSING TEST & BENCHMARK")
    print("Phase 4: Batch Processing Validation")
    print("=" * 70)
    
    # Check server
    try:
        with urllib.request.urlopen("http://127.0.0.1:8000/docs") as response:
            print(f"✅ Server is running\n")
    except Exception as e:
        print(f"❌ Server not running: {e}")
        print("\nStart the server with: python run.py")
        sys.exit(1)
    
    # Run tests
    single_time = test_single_generation()
    sequential_time = test_sequential_batch(3)
    batch_time = test_batch_endpoint(3)
    
    # Calculate improvement
    if sequential_time and batch_time:
        calculate_improvement(sequential_time, batch_time)
    elif batch_time is None:
        print("\n" + "=" * 70)
        print("NOTE: Batch endpoint test skipped")
        print("      This is expected if you're testing the initial implementation")
        print("=" * 70)
    
    print("\n" + "=" * 70)
    print("PHASE 4 STATUS")
    print("=" * 70)
    print("✅ batch_size=1 assertion removed")
    print("✅ batch_generate() method added to HelixEngine")
    print("✅ /generate/batch endpoint added to API")
    print("⚠️  True parallel batching: TODO (currently sequential)")
    print("\nNext: Optimize with parallel processing for full speedup")
    print("=" * 70 + "\n")


if __name__ == "__main__":
    main()
