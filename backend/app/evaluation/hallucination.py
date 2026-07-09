from typing import Tuple, List

class HallucinationDetector:
    def __init__(self):
        self.hedging_phrases = [
            "i'm not sure", "i am not sure", "not sure if", "might be", "could be",
            "i don't know", "i do not know", "cannot answer", "unable to answer",
            "i apologize", "as an ai", "cannot verify", "my knowledge cutoff",
            "not have access", "cannot guarantee", "uncertain if"
        ]

    def detect_hedging(self, text: str) -> Tuple[bool, List[str]]:
        """
        Scans the text for common hedging / uncertain expressions.
        Returns:
            Tuple[bool, List[str]]: (hedging_detected, list_of_matching_phrases)
        """
        text_lower = text.lower()
        matches = [phrase for phrase in self.hedging_phrases if phrase in text_lower]
        
        return len(matches) > 0, matches

    def check_hallucination_signals(self, text: str) -> dict:
        """
        Executes a series of heuristic checks.
        """
        hedging_detected, matches = self.detect_hedging(text)
        
        # Simple rule-based flags
        reasons = []
        if hedging_detected:
            reasons.append(f"Hedging detected: matches {matches}")

        # Empty response check
        if not text.strip():
            reasons.append("Empty output detected")

        # Refusal keywords
        refusal_keywords = ["sorry, but", "cannot fulfill", "inappropriate content", "unsafe query"]
        found_refusal = [kw for kw in refusal_keywords if kw in text.lower()]
        if found_refusal:
            reasons.append(f"Refusal keywords matched: {found_refusal}")

        return {
            "flagged": len(reasons) > 0,
            "reasons": reasons,
            "hedging_matches": matches
        }
