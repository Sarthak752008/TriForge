from abc import ABC, abstractmethod
from typing import Tuple, Dict, Any, Generator

class BaseProvider(ABC):
    """
    Abstract Base class for all model execution providers (Local & Remote).
    """

    @abstractmethod
    def generate(self, prompt: str, model: str, options: Dict[str, Any] = None) -> Tuple[str, int, int]:
        """
        Executes a prompt synchronously.
        Returns:
            Tuple[str, int, int]: (response_text, prompt_tokens, completion_tokens)
        """
        pass

    @abstractmethod
    def generate_stream(self, prompt: str, model: str, options: Dict[str, Any] = None) -> Generator[Dict[str, Any], None, None]:
        """
        Executes a prompt and streams the response back.
        Yields:
            Dict[str, Any]: A chunk containing token info or delta text.
        """
        pass

    def verify_draft(self, prompt: str, draft: str, model: str, options: Dict[str, Any] = None) -> Tuple[str, int, int]:
        """
        Sends the original prompt and local draft to the remote model for verification.
        """
        verification_prompt = (
            f"You are an expert verifier. Review the draft answer for the given task.\n"
            f"If the draft is correct and complete, confirm it. If it is incorrect, incomplete, "
            f"or has errors, correct it.\n\n"
            f"Task: {prompt}\n"
            f"Draft Answer: {draft}\n\n"
            f"Response (be concise, verify/correct the draft):"
        )
        return self.generate(verification_prompt, model, options)

    def verify_draft_stream(self, prompt: str, draft: str, model: str, options: Dict[str, Any] = None) -> Generator[Dict[str, Any], None, None]:
        """
        Streams the remote model verification of the local draft response.
        """
        verification_prompt = (
            f"You are an expert verifier. Review the draft answer for the given task.\n"
            f"If the draft is correct and complete, confirm it. If it is incorrect, incomplete, "
            f"or has errors, correct it.\n\n"
            f"Task: {prompt}\n"
            f"Draft Answer: {draft}\n\n"
            f"Response (be concise, verify/correct the draft):"
        )
        return self.generate_stream(verification_prompt, model, options)
