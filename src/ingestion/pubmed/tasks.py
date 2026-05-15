from loguru import logger

from src.ingestion.celery.app import app
from src.ingestion.exceptions import RetryException
from src.ingestion.pubmed.pipes.fetch_article_pipe import FetchArticlePipe
from src.ingestion.pubmed.pipes.start_session_pipe import StartSessionPipe


@app.task(
    bind=True,
)
def start_task(self):
    try:
        pipe = StartSessionPipe()
        pipe.run()
    except Exception as e:
        logger.exception(f"Error while calling the start_task : {e}")


@app.task(
    bind=True,
    default_retry_delay=5,
    max_retries=3,
)
def fetch_task(self, message: dict):
    try:
        pipe = FetchArticlePipe()
        pipe.run(message)
    except Exception as e:
        logger.exception(f"Error while calling the fetch_task: {e}")
