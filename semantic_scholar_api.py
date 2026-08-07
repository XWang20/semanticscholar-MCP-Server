"""Async client for every endpoint in the public Semantic Scholar APIs.

The public OpenAPI documents expose three services:

* Academic Graph: ``/graph/v1``
* Recommendations: ``/recommendations/v1``
* Datasets: ``/datasets/v1``

This module deliberately returns the API's JSON unchanged.  Keeping the raw
shape makes newly-added response fields available to MCP clients without a
server release and avoids the lossy object conversion performed by some SDKs.
"""

import asyncio
import os
from typing import Any, Dict, List, Mapping, Optional, Sequence, Union

import httpx


JSONValue = Union[Dict[str, Any], List[Any], str, int, float, bool, None]


class SemanticScholarAPIError(RuntimeError):
    """An HTTP or transport error returned by Semantic Scholar."""

    def __init__(self, status_code: Optional[int], message: str) -> None:
        self.status_code = status_code
        prefix = (
            f"Semantic Scholar API error ({status_code})"
            if status_code
            else "Semantic Scholar API error"
        )
        super().__init__(f"{prefix}: {message}")


def _env_int(name: str, default: int) -> int:
    try:
        return int(os.environ.get(name, default))
    except (TypeError, ValueError):
        return default


def _env_float(name: str, default: float) -> float:
    try:
        return float(os.environ.get(name, default))
    except (TypeError, ValueError):
        return default


class SemanticScholarAPI:
    """Small, typed async wrapper around all public Semantic Scholar paths."""

    GRAPH = "/graph/v1"
    RECOMMENDATIONS = "/recommendations/v1"
    DATASETS = "/datasets/v1"

    def __init__(
        self,
        api_key: Optional[str] = None,
        api_url: Optional[str] = None,
        timeout: Optional[float] = None,
        max_retries: Optional[int] = None,
        transport: Optional[httpx.AsyncBaseTransport] = None,
    ) -> None:
        self.api_key = (
            api_key
            if api_key is not None
            else os.environ.get("SEMANTIC_SCHOLAR_API_KEY")
        )
        self.api_url = (
            api_url
            or os.environ.get("SEMANTIC_SCHOLAR_API_URL")
            or "https://api.semanticscholar.org"
        ).rstrip("/")
        self.timeout = (
            timeout
            if timeout is not None
            else _env_float("SEMANTIC_SCHOLAR_TIMEOUT", 30.0)
        )
        self.max_retries = (
            max_retries
            if max_retries is not None
            else max(0, _env_int("SEMANTIC_SCHOLAR_MAX_RETRIES", 3))
        )
        self._transport = transport
        self._client: Optional[httpx.AsyncClient] = None

    async def __aenter__(self) -> "SemanticScholarAPI":
        await self._get_client()
        return self

    async def __aexit__(self, *_: Any) -> None:
        await self.aclose()

    async def _get_client(self) -> httpx.AsyncClient:
        if self._client is None or self._client.is_closed:
            headers = {
                "Accept": "application/json",
                "User-Agent": "semanticscholar-mcp-server/2.3.0",
            }
            if self.api_key:
                headers["x-api-key"] = self.api_key
            self._client = httpx.AsyncClient(
                base_url=self.api_url,
                headers=headers,
                timeout=self.timeout,
                follow_redirects=True,
                transport=self._transport,
            )
        return self._client

    async def aclose(self) -> None:
        if self._client is not None and not self._client.is_closed:
            await self._client.aclose()

    @staticmethod
    def _error_message(response: httpx.Response) -> str:
        try:
            payload = response.json()
        except ValueError:
            payload = response.text
        if isinstance(payload, Mapping):
            message = payload.get("error") or payload.get("message") or payload
        else:
            message = payload
        return str(message)[:1000] or response.reason_phrase

    @staticmethod
    def _retry_delay(response: Optional[httpx.Response], attempt: int) -> float:
        if response is not None:
            retry_after = response.headers.get("Retry-After")
            if retry_after:
                try:
                    return min(60.0, max(0.0, float(retry_after)))
                except ValueError:
                    pass
        return min(30.0, float(2**attempt))

    async def request(
        self,
        method: str,
        path: str,
        *,
        params: Optional[Mapping[str, Any]] = None,
        json_body: Optional[Mapping[str, Any]] = None,
    ) -> JSONValue:
        """Make a request, retrying throttling and transient server failures."""

        client = await self._get_client()
        retry_statuses = {429, 500, 502, 503, 504}
        last_error: Optional[Exception] = None

        for attempt in range(self.max_retries + 1):
            response: Optional[httpx.Response] = None
            try:
                response = await client.request(
                    method, path, params=params, json=json_body
                )
            except httpx.TransportError as exc:
                last_error = exc
                if attempt >= self.max_retries:
                    raise SemanticScholarAPIError(None, str(exc)) from exc
            else:
                if (
                    response.status_code not in retry_statuses
                    or attempt >= self.max_retries
                ):
                    if response.is_error:
                        raise SemanticScholarAPIError(
                            response.status_code,
                            self._error_message(response),
                        )
                    if response.status_code == 204 or not response.content:
                        return None
                    try:
                        return response.json()
                    except ValueError as exc:
                        raise SemanticScholarAPIError(
                            response.status_code,
                            "response was not valid JSON",
                        ) from exc

            await asyncio.sleep(self._retry_delay(response, attempt))

        raise SemanticScholarAPIError(None, str(last_error or "request failed"))

    @staticmethod
    def _csv(values: Optional[Union[str, Sequence[str]]]) -> Optional[str]:
        if values is None:
            return None
        if isinstance(values, str):
            return values
        return ",".join(values)

    @staticmethod
    def _params(**values: Any) -> Dict[str, Any]:
        return {key: value for key, value in values.items() if value is not None}

    @staticmethod
    def _require_text(value: str, name: str) -> str:
        if not isinstance(value, str) or not value.strip():
            raise ValueError(f"{name} must be a non-empty string")
        return value

    @staticmethod
    def _validate_limit(limit: int, maximum: int) -> int:
        if (
            not isinstance(limit, int)
            or isinstance(limit, bool)
            or not 1 <= limit <= maximum
        ):
            raise ValueError(f"limit must be between 1 and {maximum}")
        return limit

    @staticmethod
    def _validate_offset(offset: int) -> int:
        if not isinstance(offset, int) or isinstance(offset, bool) or offset < 0:
            raise ValueError("offset must be a non-negative integer")
        return offset

    @staticmethod
    def _validate_ids(
        ids: Sequence[str], name: str, maximum: Optional[int] = None
    ) -> List[str]:
        values = list(ids)
        if not values or any(
            not isinstance(value, str) or not value.strip() for value in values
        ):
            raise ValueError(f"{name} must contain at least one non-empty ID")
        if maximum is not None and len(values) > maximum:
            raise ValueError(f"{name} accepts at most {maximum} IDs")
        return values

    def _paper_filters(
        self,
        *,
        publication_types: Optional[Sequence[str]] = None,
        open_access_pdf: bool = False,
        min_citation_count: Optional[int] = None,
        publication_date_or_year: Optional[str] = None,
        year: Optional[str] = None,
        venue: Optional[Sequence[str]] = None,
        fields_of_study: Optional[Sequence[str]] = None,
    ) -> Dict[str, Any]:
        if min_citation_count is not None and min_citation_count < 0:
            raise ValueError("min_citation_count must be non-negative")
        return self._params(
            publicationTypes=self._csv(publication_types),
            openAccessPdf="" if open_access_pdf else None,
            minCitationCount=min_citation_count,
            publicationDateOrYear=publication_date_or_year,
            year=year,
            venue=self._csv(venue),
            fieldsOfStudy=self._csv(fields_of_study),
        )

    # Academic Graph: authors

    async def batch_authors(
        self, author_ids: Sequence[str], fields: Optional[Sequence[str]] = None
    ) -> JSONValue:
        ids = self._validate_ids(author_ids, "author_ids", maximum=1000)
        return await self.request(
            "POST",
            f"{self.GRAPH}/author/batch",
            params=self._params(fields=self._csv(fields)),
            json_body={"ids": ids},
        )

    async def search_authors(
        self,
        query: str,
        *,
        offset: int = 0,
        limit: int = 100,
        fields: Optional[Sequence[str]] = None,
    ) -> JSONValue:
        self._require_text(query, "query")
        self._validate_offset(offset)
        self._validate_limit(limit, 1000)
        return await self.request(
            "GET",
            f"{self.GRAPH}/author/search",
            params=self._params(
                query=query,
                offset=offset,
                limit=limit,
                fields=self._csv(fields),
            ),
        )

    async def get_author(
        self, author_id: str, fields: Optional[Sequence[str]] = None
    ) -> JSONValue:
        self._require_text(author_id, "author_id")
        return await self.request(
            "GET",
            f"{self.GRAPH}/author/{author_id}",
            params=self._params(fields=self._csv(fields)),
        )

    async def get_author_papers(
        self,
        author_id: str,
        *,
        publication_date_or_year: Optional[str] = None,
        offset: int = 0,
        limit: int = 100,
        fields: Optional[Sequence[str]] = None,
    ) -> JSONValue:
        self._require_text(author_id, "author_id")
        self._validate_offset(offset)
        self._validate_limit(limit, 1000)
        return await self.request(
            "GET",
            f"{self.GRAPH}/author/{author_id}/papers",
            params=self._params(
                publicationDateOrYear=publication_date_or_year,
                offset=offset,
                limit=limit,
                fields=self._csv(fields),
            ),
        )

    # Academic Graph: papers

    async def autocomplete_papers(self, query: str) -> JSONValue:
        self._require_text(query, "query")
        return await self.request(
            "GET",
            f"{self.GRAPH}/paper/autocomplete",
            params={"query": query},
        )

    async def batch_papers(
        self, paper_ids: Sequence[str], fields: Optional[Sequence[str]] = None
    ) -> JSONValue:
        ids = self._validate_ids(paper_ids, "paper_ids", maximum=500)
        return await self.request(
            "POST",
            f"{self.GRAPH}/paper/batch",
            params=self._params(fields=self._csv(fields)),
            json_body={"ids": ids},
        )

    async def search_papers(
        self,
        query: str,
        *,
        fields: Optional[Sequence[str]] = None,
        publication_types: Optional[Sequence[str]] = None,
        open_access_pdf: bool = False,
        min_citation_count: Optional[int] = None,
        publication_date_or_year: Optional[str] = None,
        year: Optional[str] = None,
        venue: Optional[Sequence[str]] = None,
        fields_of_study: Optional[Sequence[str]] = None,
        offset: int = 0,
        limit: int = 100,
    ) -> JSONValue:
        self._require_text(query, "query")
        self._validate_offset(offset)
        self._validate_limit(limit, 100)
        params = self._paper_filters(
            publication_types=publication_types,
            open_access_pdf=open_access_pdf,
            min_citation_count=min_citation_count,
            publication_date_or_year=publication_date_or_year,
            year=year,
            venue=venue,
            fields_of_study=fields_of_study,
        )
        params.update(
            self._params(
                query=query,
                fields=self._csv(fields),
                offset=offset,
                limit=limit,
            )
        )
        return await self.request("GET", f"{self.GRAPH}/paper/search", params=params)

    async def bulk_search_papers(
        self,
        query: str,
        *,
        token: Optional[str] = None,
        fields: Optional[Sequence[str]] = None,
        sort: Optional[str] = None,
        publication_types: Optional[Sequence[str]] = None,
        open_access_pdf: bool = False,
        min_citation_count: Optional[int] = None,
        publication_date_or_year: Optional[str] = None,
        year: Optional[str] = None,
        venue: Optional[Sequence[str]] = None,
        fields_of_study: Optional[Sequence[str]] = None,
    ) -> JSONValue:
        self._require_text(query, "query")
        params = self._paper_filters(
            publication_types=publication_types,
            open_access_pdf=open_access_pdf,
            min_citation_count=min_citation_count,
            publication_date_or_year=publication_date_or_year,
            year=year,
            venue=venue,
            fields_of_study=fields_of_study,
        )
        params.update(
            self._params(
                query=query,
                token=token,
                fields=self._csv(fields),
                sort=sort,
            )
        )
        return await self.request(
            "GET", f"{self.GRAPH}/paper/search/bulk", params=params
        )

    async def match_paper(
        self,
        query: str,
        *,
        fields: Optional[Sequence[str]] = None,
        publication_types: Optional[Sequence[str]] = None,
        open_access_pdf: bool = False,
        min_citation_count: Optional[int] = None,
        publication_date_or_year: Optional[str] = None,
        year: Optional[str] = None,
        venue: Optional[Sequence[str]] = None,
        fields_of_study: Optional[Sequence[str]] = None,
    ) -> JSONValue:
        self._require_text(query, "query")
        params = self._paper_filters(
            publication_types=publication_types,
            open_access_pdf=open_access_pdf,
            min_citation_count=min_citation_count,
            publication_date_or_year=publication_date_or_year,
            year=year,
            venue=venue,
            fields_of_study=fields_of_study,
        )
        params.update(self._params(query=query, fields=self._csv(fields)))
        return await self.request(
            "GET", f"{self.GRAPH}/paper/search/match", params=params
        )

    async def get_paper(
        self, paper_id: str, fields: Optional[Sequence[str]] = None
    ) -> JSONValue:
        self._require_text(paper_id, "paper_id")
        return await self.request(
            "GET",
            f"{self.GRAPH}/paper/{paper_id}",
            params=self._params(fields=self._csv(fields)),
        )

    async def get_paper_authors(
        self,
        paper_id: str,
        *,
        offset: int = 0,
        limit: int = 100,
        fields: Optional[Sequence[str]] = None,
    ) -> JSONValue:
        self._require_text(paper_id, "paper_id")
        self._validate_offset(offset)
        self._validate_limit(limit, 1000)
        return await self.request(
            "GET",
            f"{self.GRAPH}/paper/{paper_id}/authors",
            params=self._params(offset=offset, limit=limit, fields=self._csv(fields)),
        )

    async def get_paper_citations(
        self,
        paper_id: str,
        *,
        publication_date_or_year: Optional[str] = None,
        offset: int = 0,
        limit: int = 100,
        fields: Optional[Sequence[str]] = None,
    ) -> JSONValue:
        self._require_text(paper_id, "paper_id")
        self._validate_offset(offset)
        self._validate_limit(limit, 1000)
        return await self.request(
            "GET",
            f"{self.GRAPH}/paper/{paper_id}/citations",
            params=self._params(
                publicationDateOrYear=publication_date_or_year,
                offset=offset,
                limit=limit,
                fields=self._csv(fields),
            ),
        )

    async def get_paper_references(
        self,
        paper_id: str,
        *,
        offset: int = 0,
        limit: int = 100,
        fields: Optional[Sequence[str]] = None,
    ) -> JSONValue:
        self._require_text(paper_id, "paper_id")
        self._validate_offset(offset)
        self._validate_limit(limit, 1000)
        return await self.request(
            "GET",
            f"{self.GRAPH}/paper/{paper_id}/references",
            params=self._params(offset=offset, limit=limit, fields=self._csv(fields)),
        )

    # Academic Graph: text snippets

    async def search_snippets(
        self,
        query: str,
        *,
        fields: Optional[Sequence[str]] = None,
        paper_ids: Optional[Sequence[str]] = None,
        authors: Optional[Sequence[str]] = None,
        min_citation_count: Optional[int] = None,
        inserted_before: Optional[str] = None,
        publication_date_or_year: Optional[str] = None,
        year: Optional[str] = None,
        venue: Optional[Sequence[str]] = None,
        fields_of_study: Optional[Sequence[str]] = None,
        limit: int = 10,
    ) -> JSONValue:
        self._require_text(query, "query")
        self._validate_limit(limit, 1000)
        if min_citation_count is not None and min_citation_count < 0:
            raise ValueError("min_citation_count must be non-negative")
        return await self.request(
            "GET",
            f"{self.GRAPH}/snippet/search",
            params=self._params(
                query=query,
                fields=self._csv(fields),
                paperIds=self._csv(paper_ids),
                authors=self._csv(authors),
                minCitationCount=min_citation_count,
                insertedBefore=inserted_before,
                publicationDateOrYear=publication_date_or_year,
                year=year,
                venue=self._csv(venue),
                fieldsOfStudy=self._csv(fields_of_study),
                limit=limit,
            ),
        )

    # Recommendations

    async def recommend_papers_for_paper(
        self,
        paper_id: str,
        *,
        pool_from: str = "recent",
        limit: int = 100,
        fields: Optional[Sequence[str]] = None,
    ) -> JSONValue:
        self._require_text(paper_id, "paper_id")
        self._validate_limit(limit, 500)
        if pool_from not in {"recent", "all-cs"}:
            raise ValueError('pool_from must be either "recent" or "all-cs"')
        return await self.request(
            "GET",
            f"{self.RECOMMENDATIONS}/papers/forpaper/{paper_id}",
            params=self._params(
                **{"from": pool_from},
                limit=limit,
                fields=self._csv(fields),
            ),
        )

    async def recommend_papers(
        self,
        positive_paper_ids: Sequence[str],
        negative_paper_ids: Optional[Sequence[str]] = None,
        *,
        limit: int = 100,
        fields: Optional[Sequence[str]] = None,
    ) -> JSONValue:
        positive = self._validate_ids(positive_paper_ids, "positive_paper_ids")
        negative = list(negative_paper_ids or [])
        if any(not isinstance(value, str) or not value.strip() for value in negative):
            raise ValueError("negative_paper_ids must contain non-empty IDs")
        self._validate_limit(limit, 500)
        return await self.request(
            "POST",
            f"{self.RECOMMENDATIONS}/papers/",
            params=self._params(limit=limit, fields=self._csv(fields)),
            json_body={
                "positivePaperIds": positive,
                "negativePaperIds": negative,
            },
        )

    # Datasets

    async def list_dataset_releases(self) -> JSONValue:
        return await self.request("GET", f"{self.DATASETS}/release/")

    async def get_dataset_release(self, release_id: str) -> JSONValue:
        self._require_text(release_id, "release_id")
        return await self.request("GET", f"{self.DATASETS}/release/{release_id}")

    async def get_dataset_download_links(
        self, release_id: str, dataset_name: str
    ) -> JSONValue:
        self._require_text(release_id, "release_id")
        self._require_text(dataset_name, "dataset_name")
        return await self.request(
            "GET",
            f"{self.DATASETS}/release/{release_id}/dataset/{dataset_name}",
        )

    async def get_dataset_diffs(
        self, start_release_id: str, end_release_id: str, dataset_name: str
    ) -> JSONValue:
        self._require_text(start_release_id, "start_release_id")
        self._require_text(end_release_id, "end_release_id")
        self._require_text(dataset_name, "dataset_name")
        return await self.request(
            "GET",
            f"{self.DATASETS}/diffs/{start_release_id}/to/{end_release_id}/{dataset_name}",
        )
