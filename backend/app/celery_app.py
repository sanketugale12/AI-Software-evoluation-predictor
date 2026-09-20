from celery import Celery
from celery.signals import worker_ready, worker_shutdown
import logging

from backend.app.config import settings

logger = logging.getLogger(__name__)

# Create Celery app
celery_app = Celery(
    "asep",
    broker="redis://localhost:6379/0",
    backend="redis://localhost:6379/1",
    include=[
        "backend.app.tasks.analysis_task",
    ]
)

# Celery configuration
celery_app.conf.update(
    # Task serialization
    task_serializer="json",
    result_serializer="json",
    accept_content=["json"],

    # Timezone
    timezone="UTC",
    enable_utc=True,

    # Task routing
    task_routes={
        "backend.app.tasks.analysis_task.run_analysis": {"queue": "analysis"},
    },

    # Task execution
    task_acks_late=True,
    task_reject_on_worker_lost=True,
    worker_prefetch_multiplier=1,

    # Result backend
    result_expires=3600,  # 1 hour
    result_compression="gzip",

    # Retry policy
    task_default_retry_delay=60,  # 1 minute
    task_max_retries=3,

    # Monitoring
    worker_send_task_events=True,
    task_send_sent_event=True,

    # Beat schedule (if needed for periodic tasks)
    beat_schedule={},
)

# Auto-discover tasks
celery_app.autodiscover_tasks([
    "backend.app.tasks",
])


@worker_ready.connect
def on_worker_ready(**kwargs):
    logger.info("Celery worker is ready")


@worker_shutdown.connect
def on_worker_shutdown(**kwargs):
    logger.info("Celery worker is shutting down")


# Task base class with common functionality
class BaseTask(celery_app.Task):
    """Base task class with common functionality"""

    autoretry_for = (Exception,)
    retry_backoff = True
    retry_backoff_max = 600  # 10 minutes max
    retry_jitter = True

    def on_failure(self, exc, task_id, args, kwargs, einfo):
        """Called when task fails after all retries"""
        logger.error(f"Task {task_id} failed: {exc}")
        super().on_failure(exc, task_id, args, kwargs, einfo)

    def on_retry(self, exc, task_id, args, kwargs, einfo):
        """Called when task is retried"""
        logger.warning(f"Task {task_id} retrying: {exc}")
        super().on_retry(exc, task_id, args, kwargs, einfo)


# Set default task base class
celery_app.Task = BaseTask