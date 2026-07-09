import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from app.database.models import Base
from app.cache.smart_cache import SmartCache

# In-memory database setup for testing
engine = create_engine("sqlite:///:memory:")
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

@pytest.fixture(scope="function")
def db_session():
    Base.metadata.create_all(bind=engine)
    db = TestingSessionLocal()
    try:
        yield db
    finally:
        db.close()
        Base.metadata.drop_all(bind=engine)

def test_cache_set_and_get(db_session):
    cache = SmartCache()
    prompt = "Test query prompt"
    response = "This is a cached response"
    model = "mock-model"
    
    # Verify cache is empty initially
    hit = cache.get(db_session, prompt)
    assert hit is None

    # Set cache
    cache.set(
        db=db_session,
        prompt=prompt,
        response_text=response,
        model_name=model,
        prompt_tokens=10,
        completion_tokens=20,
        latency_ms=100.0
    )

    # Get cache and verify
    hit = cache.get(db_session, prompt)
    assert hit is not None
    assert hit.prompt == prompt
    assert hit.response_text == response
    assert hit.model_name == model
    assert hit.prompt_tokens == 10
    assert hit.completion_tokens == 20
    assert hit.latency_ms == 100.0
