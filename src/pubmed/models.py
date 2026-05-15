from typing import Optional

from pydantic import BaseModel


class PubMedSearchSession(BaseModel):
    query: str

    webenv: str

    query_key: str

    count: int

    retstart: int = 0

    retmax: int = 500

    year: int | None = None


class PubMedArticle(BaseModel):
    pmid: str

    title: str

    abstract: str | None = None

    publication_year: int | None = None

    publication_types: list[str] = []

    mesh_terms: list[str] = []
