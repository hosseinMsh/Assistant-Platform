import os
from pydantic_settings import BaseSettings

class Config(BaseSettings):
    service_name: str = "mcp-knowledge"
    port: int = int(os.getenv("PORT", "8080"))
    knowledge_path: str = os.getenv("KNOWLEDGE_PATH", "knowledge")

    class ConfigMeta:
        env_prefix = "KNOWLEDGE_"

config = Config()
