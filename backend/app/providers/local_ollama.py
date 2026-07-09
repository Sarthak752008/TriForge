import json
import requests
from typing import Tuple, Dict, Any, Generator
from app.providers.base import BaseProvider
from app.config import settings

class LocalOllamaProvider(BaseProvider):
    def __init__(self):
        self.base_url = settings.OLLAMA_BASE_URL.rstrip('/')

    def generate(self, prompt: str, model: str, options: Dict[str, Any] = None) -> Tuple[str, int, int]:
        url = f"{self.base_url}/api/chat"
        opts = {"temperature": 0.7}
        if options:
            opts.update(options)

        payload = {
            "model": model,
            "messages": [{"role": "user", "content": prompt}],
            "stream": False,
            "options": opts
        }

        try:
            response = requests.post(url, json=payload, timeout=30)
            response.raise_for_status()
            data = response.json()
            content = data.get("message", {}).get("content", "")
            prompt_tokens = data.get("prompt_eval_count", 0)
            completion_tokens = data.get("eval_count", 0)
            return content, prompt_tokens, completion_tokens
        except Exception as e:
            # Fallback when Ollama is offline or model is missing
            return f"Error querying local model ({model}) via Ollama: {str(e)}", 0, 0

    def generate_stream(self, prompt: str, model: str, options: Dict[str, Any] = None) -> Generator[Dict[str, Any], None, None]:
        url = f"{self.base_url}/api/chat"
        opts = {"temperature": 0.7}
        if options:
            opts.update(options)

        payload = {
            "model": model,
            "messages": [{"role": "user", "content": prompt}],
            "stream": True,
            "options": opts
        }

        try:
            response = requests.post(url, json=payload, stream=True, timeout=30)
            response.raise_for_status()
            
            for line in response.iter_lines():
                if not line:
                    continue
                data = json.loads(line.decode("utf-8"))
                content = data.get("message", {}).get("content", "")
                
                # Check for token metrics in the final chunk
                prompt_tokens = data.get("prompt_eval_count", 0)
                completion_tokens = data.get("eval_count", 0)
                
                yield {
                    "text": content,
                    "prompt_tokens": prompt_tokens,
                    "completion_tokens": completion_tokens,
                    "done": data.get("done", False)
                }
        except Exception as e:
            yield {
                "text": f"\n[Stream Error: {str(e)}]",
                "prompt_tokens": 0,
                "completion_tokens": 0,
                "done": True
            }
