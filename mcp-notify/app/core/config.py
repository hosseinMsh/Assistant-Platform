from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    notify_base_url: str = "https://notify.example.ir"
    notify_connect_timeout: float = 5.0
    notify_read_timeout: float = 30.0
    log_level: str = "INFO"
    # When True, server sets sendingDate to now() if not provided
    default_sending_date_to_now: bool = True


settings = Settings()
