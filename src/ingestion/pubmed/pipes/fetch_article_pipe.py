import uuid

from loguru import logger

from src.ingestion.base_pipe import BasePipe
from src.ingestion.s3.client import S3Client
from src.ingestion.s3.exceptions import S3UploadError
from src.pubmed.client import PubmedClient
from src.pubmed.models import Abstract, PubMedArticle


class FetchArticlePipe(BasePipe):

    def __init__(self):
        self._client = PubmedClient()
        self._s3_client = S3Client()

    def name() -> str:
        return "fetch_article_pipe"

    def run(self, message):
        from src.ingestion.pubmed.tasks import fetch_task

        webenv = message["webenv"]
        query_key = message["query_key"]
        count = int(message["count"])

        retstart = int(message["retstart"])
        retmax = int(message["retmax"])

        if count <= 0:
            logger.info("No more records left to fetch.")
            return

        try:
            records = self._client.fetch(
                webenv=webenv,
                query_key=query_key,
                retstart=retstart,
                retmax=retmax,
            )

            articles = self._normalize_records(records)

            s3_key = f"{webenv}/fetch/{uuid.uuid4()}.json"

            self._s3_client.upload_data(
                key=s3_key,
                data=[article.model_dump() for article in articles],
            )
            # preprocess_task.delay(
            #     {
            #         "raw_s3_key": s3_key,
            #         "webenv": webenv,
            #     }
            # )

            logger.info(
                f"Successfully uploaded fetched records to S3. "
                f"retstart={retstart}, retmax={retmax}, key={s3_key}"
            )

        except S3UploadError as e:
            logger.exception(
                f"S3 upload failed for pubmed batch. "
                f"retstart={retstart}, retmax={retmax}, error={e}"
            )

            # TODO:
            # retry / DLQ / send alert
            return

        except Exception as e:
            logger.exception(
                f"Unexpected error in FetchArticlePipe. "
                f"retstart={retstart}, retmax={retmax}, error={e}"
            )

            return

        next_message = {
            "webenv": webenv,
            "query_key": query_key,
            "retstart": retstart + retmax,
            "retmax": retmax,
            "count": max(0, count - retmax),
        }

        fetch_task.delay(next_message)

    def _normalize_records(
        self,
        records: dict,
    ) -> list[PubMedArticle]:

        return [
            self._parse_article(article) for article in records.get("PubmedArticle", [])
        ]

    def _parse_article(self, article: dict) -> PubMedArticle:

        medline = article.get("MedlineCitation", {})

        article_data = medline.get("Article", {})

        mesh_terms = [
            mesh.get("DescriptorName") for mesh in medline.get("MeshHeadingList", [])
        ]

        publication_types = article_data.get("PublicationTypeList", [])

        publication_year = (
            article_data.get("Journal", {})
            .get("JournalIssue", {})
            .get("PubDate", {})
            .get("Year")
        )

        return PubMedArticle(
            pmid=medline.get("PMID"),
            title=article_data.get("ArticleTitle"),
            abstract=self._parse_abstract(article_data.get("Abstract", {})),
            publication_year=(
                int(publication_year)
                if publication_year and publication_year.isdigit()
                else None
            ),
            publication_types=publication_types,
            mesh_terms=mesh_terms,
        )

    def _parse_abstract(
        self,
        abstract_obj: dict,
    ) -> str | None:

        abstract_text = " ".join(map(str, abstract_obj.get("AbstractText", []))).strip()

        if not abstract_text:
            return None

        return abstract_text
