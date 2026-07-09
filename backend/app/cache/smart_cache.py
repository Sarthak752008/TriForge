import hashlib
from datetime import datetime
from sqlalchemy.orm import Session
from app.database.models import CacheModel

class SmartCache:
    @staticmethod
    def _hash_prompt(prompt: str) -> str:
        """
        Creates a SHA-256 hash of the cleaned prompt.
        """
        cleaned = prompt.strip().lower()
        return hashlib.sha256(cleaned.encode("utf-8")).hexdigest()

    def get(self, db: Session, prompt: str) -> CacheModel:
        """
        Looks up the prompt in the cache database.
        Returns:
            CacheModel or None
        """
        p_hash = self._hash_prompt(prompt)
        return db.query(CacheModel).filter(CacheModel.prompt_hash == p_hash).first()

    def set(
        self, 
        db: Session, 
        prompt: str, 
        response_text: str, 
        model_name: str, 
        prompt_tokens: int, 
        completion_tokens: int, 
        latency_ms: float
    ) -> CacheModel:
        """
        Caches a new prompt response pair.
        """
        p_hash = self._hash_prompt(prompt)
        
        # Check if already exists (to prevent unique constraint errors)
        existing = db.query(CacheModel).filter(CacheModel.prompt_hash == p_hash).first()
        if existing:
            existing.response_text = response_text
            existing.model_name = model_name
            existing.prompt_tokens = prompt_tokens
            existing.completion_tokens = completion_tokens
            existing.latency_ms = latency_ms
            existing.timestamp = datetime.utcnow()
            db.commit()
            db.refresh(existing)
            return existing

        cache_entry = CacheModel(
            prompt_hash=p_hash,
            prompt=prompt,
            response_text=response_text,
            model_name=model_name,
            prompt_tokens=prompt_tokens,
            completion_tokens=completion_tokens,
            latency_ms=latency_ms
        )
        
        try:
            db.add(cache_entry)
            db.commit()
            db.refresh(cache_entry)
            return cache_entry
        except Exception:
            db.rollback()
            # If a race condition occurred, just fetch it
            return db.query(CacheModel).filter(CacheModel.prompt_hash == p_hash).first()
