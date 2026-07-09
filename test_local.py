import requests
import json

def test_local_model():
    url = "http://localhost:11434/api/chat"
    model = "qwen2.5:3b-instruct"
    
    payload = {
        "model": model,
        "messages": [
            {
                "role": "user",
                "content": "Explain what a hybrid LLM routing agent is in one simple sentence."
            }
        ],
        "stream": False
    }
    
    print(f"Sending prompt to local Ollama instance ({model})...")
    try:
        response = requests.post(url, json=payload, timeout=30)
        response.raise_for_status()
        data = response.json()
        
        # Extract response text and token counts
        content = data.get("message", {}).get("content", "")
        prompt_tokens = data.get("prompt_eval_count", 0)
        completion_tokens = data.get("eval_count", 0)
        total_tokens = prompt_tokens + completion_tokens
        
        print("\n--- Response ---")
        print(content)
        print("----------------")
        print(f"Prompt Tokens: {prompt_tokens}")
        print(f"Completion Tokens: {completion_tokens}")
        print(f"Total Tokens: {total_tokens}")
        
    except requests.exceptions.ConnectionError:
        print("\n[ERROR] Could not connect to Ollama. Make sure Ollama is running on http://localhost:11434.")
    except Exception as e:
        print(f"\n[ERROR] An error occurred: {e}")

if __name__ == "__main__":
    test_local_model()
