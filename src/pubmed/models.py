from pydantic import BaseModel
from typing import Optional


class AbstractSection(BaseModel):
    label: str | None = None
    text: str


class Abstract(BaseModel):
    sections: list[AbstractSection] = []


class PubMedSearchSession(BaseModel):
    query: str

    webenv: str

    query_key: str

    count: int

    retstart: int = 0

    retmax: int = 500

    year: int | None = None


class PubMedFetchArticle(BaseModel):
    pmid: str

    title: str

    abstract: Optional[Abstract] = None

    publication_year: int | None = None

    publication_types: list[str] = []

    mesh_terms: list[str] = []
