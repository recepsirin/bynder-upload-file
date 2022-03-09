import asyncio
import os
from celery import Celery
from services.task_service import TaskService
from settings import Settings

settings = Settings()
celery = Celery(__name__)
celery.conf.broker_url = os.environ.get("CELERY_BROKER_URL",
                                        settings.redis_dsn)
celery.conf.result_backend = os.environ.get("CELERY_RESULT_BACKEND",
                                            settings.redis_dsn)


# NOQA celery -A tasks.celery worker --loglevel=info
# chunk_size = free_ram / number_of_max_possible_concurrent_requests

@celery.task(name="upload_file")
def upload_file(file_id: str):
    task_service = TaskService()
    asyncio.get_event_loop().run_until_complete(
        task_service.process_file(file_id))


@celery.task(name="finalise_file")
def finalise_file(file_id: str, file_hash: str, body: dict):
    task_service = TaskService()
    asyncio.get_event_loop().run_until_complete(
        task_service.finalise_file(file_id, file_hash, body))
