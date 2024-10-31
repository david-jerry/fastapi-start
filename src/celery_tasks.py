import asyncio
from celery import Celery
from src.config.settings import Config
from src.utils.logger import LOGGER

# Initialize Celery with autodiscovery
celery_app = Celery(
    "portfolio",
    broker=Config.CELERY_BROKER_URL,
    backend=Config.REDIS_URL,
)
celery_app.config_from_object(Config)

# Autodiscover tasks from all installed apps (each app should have a 'tasks.py' file)
celery_app.autodiscover_tasks(packages=['src.apps.accounts'], related_name='tasks')


