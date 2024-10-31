from .base import BaseConfig
from pydantic_settings import SettingsConfigDict


class LocalConfig(BaseConfig):
    DATABASE_URL: str
    REDIS_URL: str = "redis://localhost:6379/0"
    CELERY_BROKER_URL: str
    CELERY_RESULT_BACKEND: str

    model_config = SettingsConfigDict(
        env_file=".env.local", extra="ignore", env_file_encoding="utf-8"
    )


LocalConfigSettings = LocalConfig()
