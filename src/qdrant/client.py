from typing import Optional

from qdrant_client import QdrantClient as QClient
from qdrant_client import models
from qdrant_client.http.exceptions import ApiException, UnexpectedResponse
from qdrant_client.models import PointStruct, UpdateStatus

from src.config.config import settings


class QdrantException(Exception):
    pass


class QdrantTimeoutException(QdrantException):
    pass


class QdrantService:
    def __init__(self, collection_name: Optional[str] = None):
        self._collection_name = collection_name or settings.COLLECTION_NAME

        self._client = QClient(url=settings.BASE_URL)

    def check_collection(self) -> bool:
        try:
            return self._client.collection_exists(self._collection_name)

        except UnexpectedResponse as e:
            raise QdrantException(
                f"Failed checking collection: {self._collection_name}"
            ) from e

    def create_collection(self):
        try:
            if self.check_collection():
                return
            self._client.create_collection(
                collection_name=self._collection_name,
                vectors_config=models.VectorParams(
                    size=1536,
                    distance=models.Distance.COSINE,
                ),
                sparse_vectors_config={
                    "text": models.SparseVectorParams(),
                },
                quantization_config=models.ScalarQuantization(
                    scalar=models.ScalarQuantizationConfig(
                        type=models.ScalarType.INT8,
                        quantile=0.99,
                        always_ram=True,
                    ),
                ),
            )

        except ApiException as e:
            raise QdrantException(f"Failed creating collection: {e}") from e

    def _upsert(self, points: list[PointStruct]) -> bool:

        try:
            result = self._client.upsert(
                collection_name=self._collection_name,
                points=points,
                update_mode=models.UpdateMode.INSERT_ONLY,
            )

            status = result.status

            if status in (
                UpdateStatus.COMPLETED,
                UpdateStatus.ACKNOWLEDGED,
            ):
                return True

            if status == UpdateStatus.WAIT_TIMEOUT:
                raise QdrantTimeoutException("Qdrant write timeout")

        except ApiException as e:
            raise QdrantException(f"Qdrant API error: {e}") from e

    def batch_upsert(
        self,
        ids: list[str | int],
        embeddings: list[list[float]],
        payloads: list[dict],
    ) -> bool:

        points = self._transform_points(ids, embeddings, payloads)
        return self._upsert(points=points)

    @staticmethod
    def _transform_points(
        ids: list[str | int], embeddings: list[list[float]], payloads: list[dict]
    ) -> list[PointStruct]:

        if not (len(ids) == len(embeddings) == len(payloads)):
            raise ValueError("ids, embeddings, payloads length mismatch")

        points = [
            PointStruct(
                id=point_id,
                vector=embedding,
                payload=payload,
            )
            for point_id, embedding, payload in zip(
                ids,
                embeddings,
                payloads,
            )
        ]
        return points

    @property
    def collection_name(self) -> str:
        return self._collection_name
