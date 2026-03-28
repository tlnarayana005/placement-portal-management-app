import os

from celery import Celery
from celery.schedules import crontab


CELERY_BROKER_URL = os.getenv("CELERY_BROKER_URL", "redis://localhost:6379/1")
CELERY_RESULT_BACKEND = os.getenv("CELERY_RESULT_BACKEND", "redis://localhost:6379/2")

celery_app = Celery("ppa", broker=CELERY_BROKER_URL, backend=CELERY_RESULT_BACKEND)

celery_app.conf.update(
    timezone=os.getenv("CELERY_TIMEZONE", "UTC"),
    enable_utc=True,
    broker_connection_retry_on_startup=True,
)

celery_app.autodiscover_tasks(["app.tasks"])

# Scheduled jobs:
# - daily_reminders: send deadline reminders
# - monthly_admin_report: monthly activity report on 1st day of month
daily_hour = int(os.getenv("DAILY_REMINDER_HOUR", "9"))
daily_minute = int(os.getenv("DAILY_REMINDER_MINUTE", "0"))

monthly_hour = int(os.getenv("MONTHLY_REPORT_HOUR", "9"))
monthly_minute = int(os.getenv("MONTHLY_REPORT_MINUTE", "10"))

celery_app.conf.beat_schedule = {
    "daily-reminders": {
        "task": "app.tasks.reminders.daily_reminders",
        "schedule": crontab(hour=daily_hour, minute=daily_minute),
    },
    "monthly-admin-report": {
        "task": "app.tasks.monthly_reports.monthly_admin_activity_report",
        "schedule": crontab(day_of_month="1", hour=monthly_hour, minute=monthly_minute),
    },
}

