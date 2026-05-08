from src.ingestion.base_pipe import BasePipe
from src.ingestion.pubmed.tasks import fetch_task
from src.pubmed.client import PubmedClient

ONCOLOGY_QUERY = (
    '("neoplasms"[MeSH Terms] OR "neoplasms"[All Fields] OR "oncology"[All Fields] '
    'OR "oncology s"[All Fields]) AND ((y_10[Filter]) AND '
    "(clinicaltrial[Filter] OR clinicaltrialprotocol[Filter] OR clinicaltrialphasei[Filter] "
    "OR clinicaltrialphaseii[Filter] OR clinicaltrialphaseiii[Filter] OR clinicaltrialphaseiv[Filter] "
    "OR randomizedcontrolledtrial[Filter]) AND (fft[Filter]) AND (humans[Filter]) AND (english[Filter]))"
)


class StartSessionPipe(BasePipe):
    def __init__(self):
        self.client = PubmedClient()

    @property
    def name(self) -> str:
        return "start_session_pipe"

    def run(self):
        session = self.client.search(term=ONCOLOGY_QUERY)

        # Call next task
        fetch_task.delay(session.model_dump())
