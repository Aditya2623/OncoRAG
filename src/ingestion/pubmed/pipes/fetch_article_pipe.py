from src.ingestion.base_pipe import BasePipe
from src.pubmed.client import PubmedClient


class FetchArticlePipe(BasePipe):

    def __init__(self):
        self._client = PubmedClient()

    def name() -> str:
        return "fetch_article_pipe"

    def run(self, message):
        webenv = message["WebEnv"]
        query_key = message["QueryKey"]
        count = int(message["Count"])

        ret_start = int(message["RetStart"])
        retmax = int(message["RetMax"])

        if count > 0:
            self._client.fetch(webenv=webenv, query_key=query_key, retstart=ret_start)

        return "foo"
