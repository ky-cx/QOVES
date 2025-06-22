from celery import Celery
from app.core.config import settings

# 在这里中心化地定义Celery应用实例
celery_app = Celery(
    "qoves_worker",
    broker=settings.CELERY_BROKER_URL,
    backend=settings.CELERY_RESULT_BACKEND,
    include=["app.workers.celery_worker"] # 告诉Celery去哪里找任务
)

celery_app.conf.update(
    task_track_started=True,
)