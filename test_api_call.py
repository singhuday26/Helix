"""
Simple API Test Script

Tests the Helix inference engine without requiring torch dependencies.
Useful for verifying the server is running correctly.
"""

import urllib.request
import json
import time

def test_inference():
    base_url = "http://127.0.0.1:8000"
    generate_url = f"{base_url}/generate"

    # 1. Health Check
    try:
        print(f"Checking server health at {base_url}/docs...")
        with urllib.request.urlopen(f"{base_url}/docs") as response:
            print(f"✅ Server is up! Status: {response.getcode()}")
    except Exception as e:
        print(f"❌ Server health check failed: {e}")
        return

    # 2. Inference
    payload = {
        "prompt": "Once upon a time",
        "max_tokens": 50,
        "temperature": 0.7
    }

    print(f"\nTesting Inference: {generate_url}")
    print("-" * 40)
    print(f"Payload: {json.dumps(payload, indent=2)}")
    print("-" * 40)

    try:
        data = json.dumps(payload).encode('utf-8')
        req = urllib.request.Request(
            generate_url,
            data=data,
            headers={
                'Content-Type': 'application/json',
                'User-Agent': 'Helix-Tester'
            }
        )

        start_time = time.time()
        with urllib.request.urlopen(req) as response:
            result = response.read().decode('utf-8')
            end_time = time.time()

            print(f"\n✅ Status Code: {response.getcode()}")
            print(f"Latency: {end_time - start_time:.4f} seconds")
            print("-" * 40)
            print("Response:")
            try:
                # Try to pretty print JSON response
                json_result = json.loads(result)
                print(json.dumps(json_result, indent=2))
            except json.JSONDecodeError:
                print(result)

    except urllib.request.HTTPError as e:
        print(f"\n❌ HTTP Error {e.code}: {e.reason}")
        print(e.read().decode('utf-8'))
    except urllib.request.URLError as e:
        print(f"\n❌ Connection failed: {e.reason}")
    except Exception as e:
        print(f"\n❌ An error occurred: {e}")

if __name__ == "__main__":
    test_inference()
