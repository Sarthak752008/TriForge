import os
import requests
import json

# Simple helper to load environment variables from a .env file if it exists
def load_env():
    if os.path.exists(".env"):
        with open(".env", "r") as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith("#") and "=" in line:
                    key, val = line.split("=", 1)
                    # Strip spaces and optional surrounding quotes
                    os.environ[key.strip()] = val.strip().strip('"').strip("'")

def test_remote_model():
    load_env()
    
    # Retrieve the API key from the environment
    api_key = os.environ.get("FIREWORKS_API_KEY")
    if not api_key:
        print("[ERROR] FIREWORKS_API_KEY environment variable is not set.")
        print("Please set it in your environment or create a '.env' file in this directory with:")
        print("FIREWORKS_API_KEY=your_api_key_here")
        return
        
    url = "https://api.fireworks.ai/inference/v1/chat/completions"
    model = "accounts/fireworks/models/llama-v3p1-8b-instruct"
    
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json"
    }
    
    payload = {
        "model": model,
        "messages": [
            {
                "role": "user",
                "content": "Explain what a hybrid LLM routing agent is in one simple sentence."
            }
        ]
    }
    
    print(f"Sending prompt to Fireworks AI remote model ({model})...")
    try:
        response = requests.post(url, headers=headers, json=payload, timeout=30)
        response.raise_for_status()
        data = response.json()
        
        # Extract response text and token usage from standard OpenAI-compatible format
        content = data.get("choices", [{}])[0].get("message", {}).get("content", "")
        usage = data.get("usage", {})
        prompt_tokens = usage.get("prompt_tokens", 0)
        completion_tokens = usage.get("completion_tokens", 0)
        total_tokens = usage.get("total_tokens", 0)
        
        print("\n--- Response ---")
        print(content)
        print("----------------")
        print(f"Prompt Tokens: {prompt_tokens}")
        print(f"Completion Tokens: {completion_tokens}")
        print(f"Total Tokens: {total_tokens}")
        
    except requests.exceptions.HTTPError as he:
        print(f"\n[ERROR] HTTP Error: {he}")
        print(f"Response Body: {response.text}")
        if response.status_code == 401:
            print("Please check if your FIREWORKS_API_KEY is valid.")
    except Exception as e:
        print(f"\n[ERROR] An error occurred: {e}")

if __name__ == "__main__":
    test_remote_model()
