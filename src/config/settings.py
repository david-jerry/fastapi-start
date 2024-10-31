from src.config.production import ProductionConfig, ProductionConfigSettings
from src.config.local import LocalConfig, LocalConfigSettings
from src.config.base import BaseConfigSettings
from src.utils.logger import LOGGER


def get_config() -> ProductionConfig | LocalConfig:
    environment = BaseConfigSettings.ENVIRONMENT
    LOGGER.info(f"Env: {environment}")

    env = LocalConfigSettings
    if environment == "production":
        env = ProductionConfigSettings

    return env


Config = get_config()
broker_url = Config.REDIS_URL
result_backend = Config.REDIS_URL
broker_connection_retry_on_startup = True
LOGGER.info(f"DATABASE_URL: {Config.DATABASE_URL}")
