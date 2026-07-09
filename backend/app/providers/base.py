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
