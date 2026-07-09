import pytest
from unittest.mock import patch, MagicMock
from app.providers.local_ollama import LocalOllamaProvider
from app.providers.remote_fireworks import RemoteFireworksProvider
from app.providers.openai_provider import OpenAIProvider

@patch('requests.post')
def test_local_ollama_provider_success(mock_post):
    """
    Verifies Ollama API call returns token usage and completion text on HTTP 200.
    """
    mock_resp = MagicMock()
    mock_resp.status_code = 200
    mock_resp.json.return_value = {
        "message": {"content": "Ollama response text"},
        "prompt_eval_count": 12,
        "eval_count": 24,
        "done": True
    }
    mock_post.return_value = mock_resp

    provider = LocalOllamaProvider()
    ans, p_tok, c_tok = provider.generate("Test prompt", "qwen2.5:3b-instruct")

    assert ans == "Ollama response text"
    assert p_tok == 12
    assert c_tok == 24

@patch('requests.post')
def test_remote_fireworks_provider_missing_key(mock_post):
    """
    Checks that the provider gracefully handles missing API key credentials.
    """
    provider = RemoteFireworksProvider(api_key="")
    ans, p_tok, c_tok = provider.generate("Test", "llama-v3p1-8b-instruct")
    
    assert "Error" in ans
    assert p_tok == 0
    assert c_tok == 0
