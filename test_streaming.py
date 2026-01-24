"""
Test streaming functionality (SSE endpoint)

Run this script to verify the streaming endpoint works correctly.
Simulates a real SSE client.
"""

import requests
import json
import time


def test_streaming():
    """Test the SSE streaming endpoint."""
    print("=" * 60)
    print("Testing Helix SSE Streaming Endpoint")
    print("=" * 60)
    
    # Test parameters
    url = "http://localhost:8000/generate/stream"
    payload = {
        "prompt": "Explain AI in one sentence.",
        "max_tokens": 50,
        "temperature": 0.7,
        "speculation_depth": 4,
        "use_speculative": True,
    }
    
    print(f"\n📝 Prompt: {payload['prompt']}")
    print(f"⚙️  Config: max_tokens={payload['max_tokens']}, temp={payload['temperature']}")
    print(f"🔮 Speculation depth: {payload['speculation_depth']}")
    print("\n🚀 Starting stream...\n")
    print("-" * 60)
    
    try:
        # Send POST request with streaming
        response = requests.post(
            url,
            json=payload,
            stream=True,  # Enable streaming
            headers={"Accept": "text/event-stream"},
        )
        
        if response.status_code != 200:
            print(f"❌ Error: HTTP {response.status_code}")
            print(response.text)
            return
        
        # Parse SSE stream
        output = ""
        metrics = {
            "tokens": 0,
            "time": 0,
            "acceptance_rate": None,
        }
        
        for line in response.iter_lines():
            if not line:
                continue
            
            line = line.decode('utf-8')
            
            # Parse SSE format: "data: {...}"
            if line.startswith('data: '):
                data = line[6:]  # Remove "data: " prefix
                
                try:
                    event = json.loads(data)
                    
                    # Check for errors
                    if 'error' in event:
                        print(f"\n❌ Error: {event['error']}")
                        break
                    
                    # Check for final token
                    if event.get('is_final', False):
                        print("\n")
                        print("-" * 60)
                        print("✅ Stream completed!")
                        break
                    
                    # Extract token
                    token = event.get('token', '')
                    output += token
                    
                    # Update metrics
                    metrics['tokens'] = event.get('index', 0) + 1
                    metrics['time'] = event.get('time_elapsed', 0)
                    metrics['acceptance_rate'] = event.get('acceptance_rate')
                    
                    # Print token in real-time
                    print(token, end='', flush=True)
                
                except json.JSONDecodeError as e:
                    print(f"\n⚠️  JSON parse error: {e}")
                    continue
        
        # Final metrics
        print("\n")
        print("=" * 60)
        print("📊 Metrics:")
        print("-" * 60)
        print(f"  Tokens generated: {metrics['tokens']}")
        print(f"  Time elapsed:     {metrics['time']:.2f}s")
        if metrics['time'] > 0:
            print(f"  Tokens/second:    {metrics['tokens'] / metrics['time']:.1f}")
        if metrics['acceptance_rate'] is not None:
            print(f"  Acceptance rate:  {metrics['acceptance_rate'] * 100:.0f}%")
        print("=" * 60)
        
    except requests.RequestException as e:
        print(f"❌ Request error: {e}")
    except KeyboardInterrupt:
        print("\n\n⚠️  Stream interrupted by user")


def test_health():
    """Test health endpoint first."""
    print("\n🏥 Checking server health...")
    try:
        response = requests.get("http://localhost:8000/health")
        if response.status_code == 200:
            health = response.json()
            print(f"  Status: {health.get('status', 'unknown')}")
            print(f"  Model loaded: {health.get('model_loaded', False)}")
            print(f"  Device: {health.get('device', 'unknown')}")
            return True
        else:
            print(f"  ❌ Health check failed: HTTP {response.status_code}")
            return False
    except requests.RequestException as e:
        print(f"  ❌ Cannot connect to server: {e}")
        print("\n  Make sure the server is running:")
        print("    python run.py --reload")
        return False


def main():
    """Run all tests."""
    if not test_health():
        return
    
    print("\n")
    test_streaming()
    
    print("\n✅ All tests completed!")
    print("\n💡 Next steps:")
    print("  1. Open http://localhost:3000 (frontend)")
    print("  2. Try the live demo")
    print("  3. Check the educational content")


if __name__ == "__main__":
    main()
