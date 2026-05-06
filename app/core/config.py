from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    app_name: str = "ContextForge"
    env: str = "local"
    database_url: str = "sqlite:///./contextforge.db"
    redis_url: str = "redis://localhost:6379/0"
    llm_provider: str = "mock"
    llm_model: str = "mock-engineering-assistant"
    llm_api_key: str | None = None
    embedding_provider: str = "mock"
    vector_backend: str = "mock"
    use_mock_llm: bool = True
    use_mock_embeddings: bool = True

    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")


settings = Settings()
