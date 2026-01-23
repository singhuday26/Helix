"""
Quick test script for Helix API
"""
import requests
import json

# Test single generation
print("=" * 60)
print("Testing Single Generation Endpoint")
print("=" * 60)

url = "http://127.0.0.1:8000/generate"
payload = {
    "prompt": "Explain quantum computing in one sentence",
    "max_tokens": 50,
    "temperature": 0.7
}

print(f"\nRequest:")
print(f"URL: {url}")
print(f"Payload: {json.dumps(payload, indent=2)}")

try:
    response = requests.post(url, json=payload)
    print(f"\nResponse Status: {response.status_code}")
    
    if response.status_code == 200:
        result = response.json()
        print(f"\nResponse Body:")
        print(json.dumps(result, indent=2))
        print(f"\n{'='*60}")
        print(f"Generated Text: {result['generated_text']}")
        print(f"Tokens Generated: {result['tokens_generated']}")
        print(f"Generation Time: {result['time_seconds']:.2f}s")
        print(f"Tokens/Second: {result['tokens_per_second']:.2f}")
        print(f"Time to First Token: {result['time_to_first_token']:.3f}s")
        print(f"{'='*60}")
    else:
        print(f"\nError Response:")
        print(response.text)
except Exception as e:
    print(f"\nError: {e}")

# Test batch generation
print("\n" + "=" * 60)
print("Testing Batch Generation Endpoint")
print("=" * 60)

url_batch = "http://127.0.0.1:8000/generate/batch"
batch_payload = {
    "prompts": [
        "What is AI?",
        "Explain machine learning",
        "Define neural networks"
    ],
    "max_tokens": 30,
    "temperature": 0.7
}

print(f"\nRequest:")
print(f"URL: {url_batch}")
print(f"Payload: {json.dumps(batch_payload, indent=2)}")

try:
    response = requests.post(url_batch, json=batch_payload)
    print(f"\nResponse Status: {response.status_code}")
    
    if response.status_code == 200:
        result = response.json()
        print(f"\nBatch Results:")
        for i, item in enumerate(result['results']):
            print(f"\n--- Prompt {i+1}: {batch_payload['prompts'][i]} ---")
            print(f"Generated: {item['generated_text']}")
            print(f"Tokens: {item['tokens_generated']}, Time: {item['time_seconds']:.2f}s")
        
        print(f"\n{'='*60}")
        print(f"Total Prompts: {result['total_prompts']}")
        print(f"Total Time: {result['total_time']:.2f}s")
        print(f"Average Tokens/Second: {result['avg_tokens_per_second']:.2f}")
        print(f"{'='*60}")
    else:
        print(f"\nError Response:")
        print(response.text)
except Exception as e:
    print(f"\nError: {e}")
