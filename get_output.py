import urllib.request
import json

def get_text():
    url = "http://127.0.0.1:8000/generate"
    payload = {
        "prompt": "Once upon a time",
        "max_tokens": 50,
        "temperature": 0.7
    }
    
    data = json.dumps(payload).encode('utf-8')
    req = urllib.request.Request(
        url, 
        data=data, 
        headers={'Content-Type': 'application/json'}
    )
    
    try:
        with urllib.request.urlopen(req) as response:
            result = json.loads(response.read().decode('utf-8'))
            text = result['generated_text']
            
            with open("output.txt", "w", encoding="utf-8") as f:
                f.write(text)
                
            print("Output saved to output.txt")
            
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    get_text()
