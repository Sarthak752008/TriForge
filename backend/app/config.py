import os
from pydantic_settings import BaseSettings
from pydantic import ConfigDict
from dotenv import load_dotenv

# Find root .env or local .env and load it
env_path = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", ".env"))
if os.path.exists(env_path):
    load_dotenv(env_path)
else:
    load_dotenv()

class Settings(BaseSettings):
    PROJECT_NAME: str = "TriForge Routing API"
    DATABASE_URL: str = "sqlite:///./triforge.db"
    
    # Local Ollama Config
    OLLAMA_BASE_URL: str = "http://localhost:11434"
    DEFAULT_LOCAL_MODEL: str = "qwen2.5:3b-instruct"
    
    # API Keys & Remote Configurations
    FIREWORKS_API_KEY: str = ""
    OPENAI_API_KEY: str = ""
    ANTHROPIC_API_KEY: str = ""
    GEMINI_API_KEY: str = ""
    GROQ_API_KEY: str = ""
    TOGETHER_API_KEY: str = ""
    
    # Selected/Active Models
    ACTIVE_LOCAL_MODEL: str = "qwen2.5:3b-instruct"
    ACTIVE_REMOTE_MODEL: str = "accounts/fireworks/models/llama-v3p1-8b-instruct"
    
    # Routing Logic Settings
    DEFAULT_CONSISTENCY_THRESHOLD: float = 0.8
    ENABLE_CACHE: bool = True
    ENABLE_PROMPT_COMPRESSION: bool = False
    
    model_config = ConfigDict(env_file=".env", extra="ignore")

settings = Settings()
