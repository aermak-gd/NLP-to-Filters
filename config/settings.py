import os
from typing import Optional
from dotenv import load_dotenv


load_dotenv()

class LLMConfig:
    model: str = "gpt-4o-mini"
    temperature: float = 0.1
    max_tokens: int = 3000
    llm_model: str = "gpt-4o-mini"
    api_key: str = os.getenv("OPENAI_API_KEY")
    max_retries: int = 3
    max_delay: int = 1

class EmbeddingConfig:
    embedding_model: str = "all-MiniLM-L6-v2"
    embedding_dimension: int = 384

class RedisConfig:
    redis_host: str = "localhost"
    redis_port: int = 6379
    redis_password: Optional[str] = os.getenv("REDIS_PASSWORD")
    redis_db: int = 0
    redis_index_name: str = "filter_index"
    redis_embedding_dimension: int = EmbeddingConfig.embedding_dimension

class FlaskConfig:
    flask_host: str = os.getenv("FLASK_HOST", "0.0.0.0")
    flask_port: int = int(os.getenv("FLASK_PORT", 5001))
    flask_debug: bool = os.getenv("FLASK_DEBUG", "False").lower() == "true"
