from src.ingestion.celery.app import app
from src.ingestion.exceptions import RetryException
from src.ingestion.qdrant.store_pipe import StorePipe

from loguru import logger


@app.task(
    bind=True,
    default_retry_delay=5,
    max_retries=3,
    ignore_result=True,
)
def store_task(self, message: dict):
    try:
        pipe = StorePipe()
        pipe.run(message)

    except RetryException as e:
        retry_count = self.request.retries

        if retry_count >= self.max_retries:
            # TODO: Store them for re-ingestion
            logger.error("Task failed permanently")
            return

        logger.warning(
            f"Retrying store task retry_count:{self.request.retries,}",
            extra={
                "task_id": self.request.id,
            },
        )

        raise self.retry(
            exc=e,
            countdown=2**self.request.retries,
        )
