import difflib
from typing import Tuple
from app.providers.local_ollama import LocalOllamaProvider
from app.config import settings

class ConsistencyChecker:
    def __init__(self, ollama_provider: LocalOllamaProvider = None):
        self.ollama = ollama_provider or LocalOllamaProvider()

    def check_consistency(self, prompt: str, model: str = None, threshold: float = None) -> Tuple[float, str, str, int, int]:
        """
        Samples the local model twice at temperature 0.7.
        Returns:
            Tuple[float, str, str, int, int]: (similarity_score, sample1, sample2, total_prompt_tokens, total_completion_tokens)
        """
        target_model = model or settings.ACTIVE_LOCAL_MODEL
        target_threshold = threshold or settings.DEFAULT_CONSISTENCY_THRESHOLD

        # Sample 1
        sample1, s1_p, s1_c = self.ollama.generate(
            prompt, 
            model=target_model, 
            options={"temperature": 0.7}
        )

        # Sample 2
        sample2, s2_p, s2_c = self.ollama.generate(
            prompt, 
            model=target_model, 
            options={"temperature": 0.7}
        )

        total_prompt_tokens = s1_p + s2_p
        total_completion_tokens = s1_c + s2_c

        # Clean responses for clean comparison
        s1_clean = sample1.strip()
        s2_clean = sample2.strip()

        if not s1_clean or not s2_clean:
            return 0.0, sample1, sample2, total_prompt_tokens, total_completion_tokens

        # Use SequenceMatcher ratio
        similarity = difflib.SequenceMatcher(None, s1_clean, s2_clean).ratio()

        return similarity, sample1, sample2, total_prompt_tokens, total_completion_tokens
