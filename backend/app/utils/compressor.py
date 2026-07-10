from app.providers.groq_provider import GroqProvider
from app.config import settings

class PromptCompressor:
    def __init__(self, local_provider: GroqProvider = None):
        self.local_provider = local_provider or GroqProvider()
        self._cache = {}

    def compress(self, prompt: str, max_words: int = 150) -> str:
        """
        Compresses long inputs to save remote model input tokens.
        If prompt word count is smaller than max_words, returns unchanged.
        """
        words = prompt.split()
        if len(words) <= max_words:
            return prompt

        cleaned_prompt = prompt.strip()
        if cleaned_prompt in self._cache:
            return self._cache[cleaned_prompt]

        system_instruction = (
            "You are a prompt compressor. Simplify the user's input by removing conversational fluff, "
            "redundant phrasing, and fillers. Maintain all core instructions, data inputs, and constraints exactly. "
            "Produce only the compressed text. Do not comment or add explanation."
        )

        compression_prompt = f"{system_instruction}\n\nInput Prompt:\n{prompt}\n\nCompressed Prompt:"
        
        try:
            compressed, _, _ = self.local_provider.generate(
                prompt=compression_prompt,
                model=settings.ACTIVE_LOCAL_MODEL,
                options={"temperature": 0.1}
            )
            cleaned = compressed.strip()
            
            if cleaned.startswith("Error querying Groq model"):
                return prompt
                
            # Sanity check: Ensure we actually compressed it and didn't fail
            if cleaned and len(cleaned.split()) < len(words):
                if len(self._cache) > 500:
                    self._cache.clear()
                self._cache[cleaned_prompt] = cleaned
                return cleaned
        except Exception:
            pass

        # Fallback: Just return the original prompt if compression fails or gets corrupted
        return prompt
