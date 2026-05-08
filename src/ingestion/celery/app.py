from celery import Celery

app = Celery(
    "oncorag",
    broker="redis://localhost:6379",
    backend="redis://localhost:6379",
)

app.conf.update(
    result_expires=3600,
)

app.autodiscover_tasks(
    [
        "src.ingestion.pubmed",
        "src.ingestion.qdrant",
    ]
)
