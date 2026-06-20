# Settings package — import Celery app so it's loaded on startup
from config.celery import app as celery_app

__all__ = ["celery_app"]
