from src.ingestion.celery.app import app
from src.ingestion.exceptions import RetryException
from src.ingestion.pubmed.pipes.fetch_article_pipe import FetchArticlePipe


@app.task()
def fetch_task(self, message: dict): ...
