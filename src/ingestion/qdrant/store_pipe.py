from src.ingestion.base_pipe import BasePipe
from src.ingestion.exceptions import RetryException
from src.qdrant.client import QdrantService, QdrantTimeoutException

from loguru import logger


class StorePipe(BasePipe):

    def __init__(self):
        self._client = QdrantService()

        if not self._client.check_collection():
            self._client.create_collection()

    @property
    def name(self):
        return "store_pipe"

    def run(self, message: dict):
        try:
            ids = ids = message["ids"]
            embeddings = message["points"]
            payloads = message["payloads"]
            logger.info("____________________________________")
            # logger.info(f"{ids}:{embeddings}:{payloads}")
            # logger.info("____________________________________")
            raise RetryException(
                f"Error while upserting retrying pipe name:{self.name}"
            )
            # self._client.batch_upsert(
            #     ids,
            #     embeddings,
            #     payloads,
            # )
        except QdrantTimeoutException:
            raise RetryException(
                f"Error while upserting retrying pipe name:{self.name}"
            )
