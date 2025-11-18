import os
from celery import Celery
from app.config import settings

# Celery configuration
celery_app = Celery(
    "oxlas_suite",
    broker=f"redis://{os.getenv('REDIS_HOST', 'localhost')}:{os.getenv('REDIS_PORT', '6379')}/0",
    backend=f"redis://{os.getenv('REDIS_HOST', 'localhost')}:{os.getenv('REDIS_PORT', '6379')}/1",
    include=["app.tasks.email_tasks", "app.tasks.monitoring_tasks"]
)

# Celery configuration
celery_app.conf.update(
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    timezone="UTC",
    enable_utc=True,
    task_track_started=True,
    task_time_limit=30 * 60,  # 30 minutes
    task_soft_time_limit=25 * 60,  # 25 minutes
    worker_prefetch_multiplier=1,
    worker_max_tasks_per_child=1000,
    
    # Retry configuration
    task_acks_late=True,
    task_reject_on_worker_lost=True,
    task_default_retry_delay=60,  # 1 minute
    task_max_retries=3,
    
    # Rate limiting
    task_annotations={
        'app.tasks.email_tasks.send_email_task': {'rate_limit': '10/m'},
        'app.tasks.email_tasks.receive_email_task': {'rate_limit': '5/m'},
    }
)

# Periodic tasks
celery_app.conf.beat_schedule = {
    'reset-monthly-usage': {
        'task': 'app.tasks.monitoring_tasks.reset_monthly_usage',
        'schedule': 30 * 24 * 60 * 60.0,  # Run on the first day of each month
    },
    'cleanup-expired-tokens': {
        'task': 'app.tasks.monitoring_tasks.cleanup_expired_tokens',
        'schedule': 24 * 60 * 60.0,  # Daily
    },
    'cleanup-old-logs': {
        'task': 'app.tasks.monitoring_tasks.cleanup_old_logs',
        'schedule': 7 * 24 * 60 * 60.0,  # Weekly
    },
}

if __name__ == "__main__":
    celery_app.start()