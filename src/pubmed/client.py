import time
from collections.abc import Generator
from typing import Optional

from Bio import Entrez
from Bio.Entrez import Parser  # for type hints

from src.config.config import settings
from src.pubmed.models import PubMedSearchSession


class PubmedClient:
    """
    Wrapper around Bio.Entrez that handles:
      - email / api_key
      - rate limiting (3 req/s without key, 10 req/s with key)
      - proper handle closing
      - structured exceptions per NCBI E-utilities docs

    Usage
    -----
    client = EntrezClient(email="you@example.com")

    # Search
    result = client.search(db="pubmed", term="cancer[MeSH]", retmax=0, usehistory=True)
    webenv     = result["WebEnv"]
    query_key  = result["QueryKey"]
    count      = int(result["Count"])

    # Fetch
    xml = client.fetch(
        db="pubmed",
        query_key=query_key,
        webenv=webenv,
        retstart=0,
        retmax=10,
        rettype="abstract",
        retmode="xml",
    )
    """

    # NCBI hard limits
    _MAX_RETMAX = 10_000  # ESearch cap per call
    _RATE_NO_KEY = 1 / 3  # seconds between calls — 3 req/s
    _RATE_WITH_KEY = 1 / 10  # seconds between calls — 10 req/s

    def __init__(
        self,
        email: Optional[str] = None,
        api_key: Optional[str] = None,
    ):
        """
        Parameters
        ----------
        email    : Required by NCBI. Must be a valid address.
        api_key  : Optional NCBI API key (raises limit to 10 req/s).
        """

        Entrez.email = email or settings.PUBMED_EMAIL
        Entrez.api_key = api_key

        self._min_interval = self._RATE_WITH_KEY if api_key else self._RATE_NO_KEY
        self._last_request_time: float = 0.0

    # ------------------------------------------------------------------
    # Public methods
    # ------------------------------------------------------------------

    def search(
        self,
        term: str,
        retmax: int = 20,
        retstart: int = 0,
    ) -> PubMedSearchSession:
        """
        Run ESearch and return the parsed result dict.

        Parameters
        ----------
        term        : Entrez query string.
        retmax      : Max UIDs to return (0 = count only; cap = 10,000).
        retstart    : Index of first UID to return.

        Returns
        -------
        PubMedSearchSession data class

        Raises
        ------
        ValueError  : Bad parameters.
        RuntimeError: NCBI returned an error or the response was malformed.
        IOError     : Network/connection failure.
        """
        if retmax > self._MAX_RETMAX:
            raise ValueError(
                f"`retmax` cannot exceed {self._MAX_RETMAX} per NCBI policy. "
                "Use pagination (retstart) for larger sets."
            )

        self._rate_limit()
        handle = None
        try:
            handle = Entrez.esearch(
                db="pubmed", term=term, retmax=retmax, retstart=retstart, usehistory="y"
            )
            record = Entrez.read(handle)
        except RuntimeError as exc:
            # Bio.Entrez raises RuntimeError for malformed XML / NCBI errors
            raise RuntimeError(
                f"ESearch failed — NCBI returned an error: {exc}"
            ) from exc
        except OSError as exc:
            raise IOError(f"ESearch network error: {exc}") from exc
        finally:
            if handle:
                handle.close()

        return PubMedSearchSession(
            query=term,
            webenv=record["WebEnv"],
            query_key=record["QueryKey"],
            count=int(record["Count"]),
            retstart=int(record["RetStart"]),
            retmax=int(record["RetMax"]),
        )

    def fetch(
        self,
        retstart: int = 0,
        retmax: int = 20,
        rettype: str = "abstract",
        retmode: str = "xml",
        webenv: Optional[str] = None,
        query_key: Optional[str] = None,
        ids: Optional[list[str]] = None,
    ) -> Generator[dict, None, None]:
        """
        Run EFetch and return raw bytes (XML, text, etc.).

        You must supply either (webenv + query_key) or ids.

        Parameters
        ----------
        db        : Entrez database name.
        retstart  : Offset into result set.
        retmax    : Records to fetch per call (cap = 10,000).
        rettype   : e.g. "abstract", "medline", "fasta".
        retmode   : e.g. "xml", "text", "asn.1".
        webenv    : WebEnv string from a prior esearch/epost.
        query_key : QueryKey from a prior esearch/epost.
        ids       : List of UIDs (alternative to webenv/query_key).

        Returns
        -------
        bytes — raw response body (parse as needed).

        Raises
        ------
        ValueError  : Bad / missing parameters.
        RuntimeError: NCBI returned an error or malformed response.
        IOError     : Network/connection failure.
        """

        has_history = webenv and query_key
        has_ids = ids and len(ids) > 0

        if not has_history and not has_ids:
            raise ValueError(
                "Supply either (webenv + query_key) from a prior search, "
                "or a list of UIDs via `ids`."
            )
        if retmax > self._MAX_RETMAX:
            raise ValueError(
                f"`retmax` cannot exceed {self._MAX_RETMAX}. Use pagination."
            )

        kwargs = dict(
            db="pubmed",
            retstart=retstart,
            retmax=retmax,
            rettype=rettype,
            retmode=retmode,
        )
        if has_history:
            kwargs["WebEnv"] = webenv
            kwargs["query_key"] = query_key
        else:
            kwargs["id"] = ",".join(ids)

        self._rate_limit()
        handle = None
        try:

            handle = Entrez.efetch(**kwargs)

            return Entrez.read(handle)

        except RuntimeError as exc:
            raise RuntimeError(
                f"EFetch failed — NCBI returned an error: {exc}"
            ) from exc
        except OSError as exc:
            raise IOError(f"EFetch network error: {exc}") from exc
        finally:
            if handle:
                handle.close()

    # ------------------------------------------------------------------
    # Private helpers
    # ------------------------------------------------------------------

    def _rate_limit(self) -> None:
        """Sleep if necessary to stay within NCBI's request rate limit."""
        elapsed = time.monotonic() - self._last_request_time
        wait = self._min_interval - elapsed
        if wait > 0:
            time.sleep(wait)
        self._last_request_time = time.monotonic()
