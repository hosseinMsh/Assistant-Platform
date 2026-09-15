from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    # Database
    database_url: str = "postgresql+asyncpg://user:password@postgres:5432/assistant"

    # Redis
    redis_url: str = "redis://redis:6379/0"
    session_ttl_seconds: int = 86400  # 24h
    confirmation_ttl_seconds: int = 300  # 5 min

    # Session cookie
    session_cookie_name: str = "session_id"
    secret_key: str = "change-me-in-production"
    cookie_secure: bool = False  # True in production
    cookie_samesite: str = "lax"

    # LLM
    llm_base_url: str = "https://api.openai.com/v1"
    llm_api_key: str = ""
    llm_model: str = "gpt-4o"
    llm_timeout: float = 60.0

    # Gateway
    mcp_gateway_url: str = "http://mcp-gateway:8080"
    gateway_timeout: float = 30.0

    # App
    log_level: str = "INFO"
    cors_origins: list[str] = ["http://localhost:3000"]


settings = Settings()
