from typing import Tuple, Dict, Any
from app.classifier.semantic_classifier import SemanticClassifier
from app.config import settings

class RoutingEngine:
    def __init__(self, classifier: SemanticClassifier = None):
        self.classifier = classifier or SemanticClassifier()
        
        # Model performance metrics metadata for estimation
        self.model_metadata = {
            "local": {
                "input_cost_per_1m": 0.0,
                "output_cost_per_1m": 0.0,
                "base_latency_ms": 350.0,
                "ms_per_token": 15.0
            },
            "remote": {
                "input_cost_per_1m": 0.20,  # Fireworks pricing estimate (USD)
                "output_cost_per_1m": 0.20,
                "base_latency_ms": 200.0,
                "ms_per_token": 8.0
            }
        }

    def estimate_metrics(self, prompt: str, category: str) -> Dict[str, Any]:
        """
        Estimates local vs remote latency and cost based on inputs and category.
        """
        word_count = len(prompt.split())
        est_input_tokens = int(word_count * 1.3)
        
        # Estimate output tokens based on category
        if category in ["summarization", "creative_writing"]:
            est_output_tokens = 150
        elif category in ["coding", "reasoning"]:
            est_output_tokens = 250
        else:
            est_output_tokens = 60

        # Calculations
        local_meta = self.model_metadata["local"]
        remote_meta = self.model_metadata["remote"]
        
        local_est_latency = local_meta["base_latency_ms"] + (est_output_tokens * local_meta["ms_per_token"])
        remote_est_latency = remote_meta["base_latency_ms"] + (est_output_tokens * remote_meta["ms_per_token"])
        
        remote_cost = (
            (est_input_tokens * (remote_meta["input_cost_per_1m"] / 1_000_000)) + 
            (est_output_tokens * (remote_meta["output_cost_per_1m"] / 1_000_000))
        )

        return {
            "word_count": word_count,
            "category": category,
            "est_local_latency_ms": round(local_est_latency, 2),
            "est_remote_latency_ms": round(remote_est_latency, 2),
            "est_remote_cost": round(remote_cost, 6)
        }

    def route(self, prompt: str) -> Tuple[str, str, Dict[str, Any]]:
        """
        Decides model routing.
        Returns:
            Tuple[str, str, Dict[str, Any]]: (route_name, reason, estimates)

        Routing strategy (token-minimisation priority):
          - LOCAL  : handles factual QA, math, reasoning, short summarization,
                     translation, extraction, conversation, general_qa
          - REMOTE : only for code generation tasks or very long prompts (>75 words)
        """
        category = self.classifier.classify(prompt)
        estimates = self.estimate_metrics(prompt, category)
        word_count = estimates["word_count"]

        # 1. Code generation → always remote (local 8B models are unreliable for synthesis)
        #    Note: simple conceptual code QA ("what does X do?") is routed to local.
        if category == "coding":
            code_gen_keywords = [
                "write", "create", "generate", "build", "implement", "develop", "make",
                "fix", "debug", "refactor", "optimise", "optimize", "add", "update", "script",
                "program", "function", "class", "algorithm", "code"
            ]
            if any(kw in prompt.lower() for kw in code_gen_keywords):
                reason = (
                    f"Query classified as 'CODING' with code-generation/debugging intent. "
                    f"Routed to remote model for reliable code synthesis."
                )
                return "remote", reason, estimates
            else:
                reason = (
                    f"Query classified as 'CODING' but appears to be conceptual/informational code QA. "
                    f"Routing to local model to conserve remote tokens."
                )
                return "local", reason, estimates

        # 2. Very long prompts → remote (avoids slow local inference & context overflow)
        if word_count > 75:
            reason = (
                f"Prompt has {word_count} words (exceeds local threshold of 75 words). "
                f"Routed to remote model to handle long context reliably."
            )
            return "remote", reason, estimates

        # 3. All other categories (math, reasoning, summarization, translation,
        #    extraction, conversation, general_qa) → try local first.
        #    The consistency checker in the chat endpoint will escalate to remote
        #    automatically if similarity falls below the configured threshold.
        reason = (
            f"Prompt is {word_count} words and task type is '{category}' (low-to-medium complexity). "
            f"Routing to local model to conserve remote tokens."
        )
        return "local", reason, estimates
