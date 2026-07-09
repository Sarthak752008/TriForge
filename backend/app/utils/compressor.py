from app.providers.local_ollama import LocalOllamaProvider
from app.config import settings

class PromptCompressor:
    def __init__(self, ollama_provider: LocalOllamaProvider = None):
        self.ollama = ollama_provider or LocalOllamaProvider()

    def compress(self, prompt: str, max_words: int = 150) -> str:
        """
        Compresses long inputs to save remote model input tokens.
        If prompt word count is smaller than max_words, returns unchanged.
        """
        words = prompt.split()
        if len(words) <= max_words:
            return prompt

        system_instruction = (
            "You are a prompt compressor. Simplify the user's input by removing conversational fluff, "
            "redundant phrasing, and fillers. Maintain all core instructions, data inputs, and constraints exactly. "
            "Produce only the compressed text. Do not comment or add explanation."
        )

        compression_prompt = f"{system_instruction}\n\nInput Prompt:\n{prompt}\n\nCompressed Prompt:"
        
        try:
            compressed, _, _ = self.ollama.generate(
                prompt=compression_prompt,
                model=settings.ACTIVE_LOCAL_MODEL,
                options={"temperature": 0.1}
            )
            cleaned = compressed.strip()
            
            # Sanity check: Ensure we actually compressed it and didn't fail
            if cleaned and len(cleaned.split()) < len(words):
                return cleaned
        except Exception:
            pass

        # Fallback: Just return the original prompt if compression fails or gets corrupted
        return prompt
