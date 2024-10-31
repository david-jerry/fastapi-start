from .base import BaseConfig
from pydantic_settings import SettingsConfigDict


class ProductionConfig(BaseConfig):
    DATABASE_URL: str
    REDIS_URL: str = "redis://localhost:6379/0"
    CELERY_BROKER_URL: str
    CELERY_RESULT_BACKEND: str


    model_config = SettingsConfigDict(
        env_file=".env.production", extra="ignore", env_file_encoding="utf-8"
    )


ProductionConfigSettings = ProductionConfig()
