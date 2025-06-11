import os
from typing import Optional
from dotenv import load_dotenv


load_dotenv()

class LLMConfig:
    model: str = "gpt-4o-mini"
    temperature: float = 0.1
    max_tokens: int = 3000
    api_key: str = os.getenv("OPENAI_API_KEY")
    max_retries: int = 3
    max_delay: int = 1

class EmbeddingConfig:
    embedding_model: str = "all-MiniLM-L6-v2"
    embedding_dimension: int = 384

class RedisConfig:
    redis_host: str = os.getenv("REDIS_HOST", "redis")
    redis_port: int = int(os.getenv("REDIS_PORT", "6379"))
    redis_password: Optional[str] = os.getenv("REDIS_PASSWORD")
    redis_db: int = int(os.getenv("REDIS_DB", "0"))
    redis_index_name: str = os.getenv("REDIS_INDEX_NAME", "filter_index")
    redis_embedding_dimension: int = EmbeddingConfig.embedding_dimension

class FlaskConfig:
    flask_host: str = os.getenv("FLASK_HOST", "0.0.0.0")
    flask_port: int = int(os.getenv("FLASK_PORT", 5001))
    flask_debug: bool = os.getenv("FLASK_DEBUG", "False").lower() == "true"
