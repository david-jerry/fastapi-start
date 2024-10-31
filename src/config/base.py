from pathlib import Path
from typing import Optional
from pydantic_settings import BaseSettings, SettingsConfigDict

BASE_URL = Path(__file__).resolve().parent.parent.parent

class BaseConfig(BaseSettings):
    ENVIRONMENT: str
    SECRET_KEY: str
    ALGORITHM: Optional[str] = "HS256"
    BASE_DIR: Optional[Path] = BASE_URL
    APP_DIR: Optional[Path] = BASE_DIR / 'src/apps'
    VERSION: Optional[str] = "v1"
    ACCESS_TOKEN_EXPIRY: Optional[int] = 1800
    RESEND_API: str

    CLOUDINARY_CLOUD_NAME: str
    CLOUDINARY_KEY: str
    CLOUDINARY_SECRET: str
    CLOUDINARY_URL: str

    BINANCE_API: str
    BINANCE_SECRET: str
    HTX_API: str
    HTX_SECRET: str
    BITFINEX_API: str
    BITFINEX_SECRET: str
    BYBIT_API: str
    BYBIT_SECRET: str
    KRAKEN_API: str
    KRAKEN_SECRET: str

    model_config = SettingsConfigDict(
        env_file=".env",
        extra="ignore",
        env_file_encoding='utf-8'
    )


BaseConfigSettings = BaseConfig()

