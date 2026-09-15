from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    servers_config_path: str = "config/servers.yml"
    mcp_connect_timeout: float = 5.0
    mcp_read_timeout: float = 30.0
    log_level: str = "INFO"
    # Tool catalog cache TTL in seconds (0 = no cache)
    tool_cache_ttl: int = 60


settings = Settings()
