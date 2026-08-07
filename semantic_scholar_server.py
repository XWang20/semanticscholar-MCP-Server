"""MCP tools for all public Semantic Scholar API endpoints."""

import asyncio
import logging
from contextlib import asynccontextmanager
from typing import Any, Awaitable, List, Optional, Sequence

from mcp.server.fastmcp import FastMCP

from semantic_scholar_api import JSONValue, SemanticScholarAPI, SemanticScholarAPIError


__version__ = "2.3.0"


logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
)
logging.getLogger("httpx").setLevel(logging.WARNING)

api = SemanticScholarAPI()


@asynccontextmanager
async def lifespan(_: FastMCP):
    async with api:
        yield {}


mcp = FastMCP(
    "semanticscholar",
    instructions=(
        "Search and traverse the Semantic Scholar Academic Graph, request paper "
        "recommendations, and inspect downloadable dataset releases."
    ),
    lifespan=lifespan,
)


DEFAULT_PAPER_SEARCH_FIELDS = [
    "paperId",
    "corpusId",
    "externalIds",
    "url",
    "title",
    "abstract",
    "venue",
    "publicationVenue",
    "year",
    "referenceCount",
    "citationCount",
    "influentialCitationCount",
    "isOpenAccess",
    "openAccessPdf",
    "fieldsOfStudy",
    "s2FieldsOfStudy",
    "publicationTypes",
    "publicationDate",
    "journal",
    "citationStyles",
    "authors",
]

DEFAULT_PAPER_DETAIL_FIELDS = DEFAULT_PAPER_SEARCH_FIELDS + ["tldr"]

DEFAULT_AUTHOR_FIELDS = [
    "authorId",
    "externalIds",
    "url",
    "name",
    "affiliations",
    "homepage",
    "paperCount",
    "citationCount",
    "hIndex",
]

DEFAULT_CITATION_FIELDS = [
    "contexts",
    "intents",
    "contextsWithIntent",
    "isInfluential",
] + [f"citingPaper.{field}" for field in DEFAULT_PAPER_SEARCH_FIELDS]

DEFAULT_REFERENCE_FIELDS = [
    "contexts",
    "intents",
    "contextsWithIntent",
    "isInfluential",
] + [f"citedPaper.{field}" for field in DEFAULT_PAPER_SEARCH_FIELDS]


def _use_fields(fields: Optional[Sequence[str]], defaults: Sequence[str]) -> List[str]:
    return list(defaults if fields is None else fields)


async def _execute(operation: str, request: Awaitable[JSONValue]) -> JSONValue:
    try:
        return await request
    except (SemanticScholarAPIError, ValueError) as exc:
        logging.warning("%s failed: %s", operation, exc)
        return {"error": str(exc)}
    except Exception as exc:  # Keep MCP requests alive on unexpected client errors.
        logging.exception("%s failed unexpectedly", operation)
        return {"error": f"Unexpected error: {exc}"}


# Academic Graph API: author endpoints


@mcp.tool()
async def batch_get_semantic_scholar_authors(
    author_ids: List[str],
    fields: Optional[List[str]] = None,
) -> Any:
    """Get multiple authors by Semantic Scholar author ID (maximum 1,000)."""

    return await _execute(
        "batch author lookup",
        api.batch_authors(
            author_ids, fields=_use_fields(fields, DEFAULT_AUTHOR_FIELDS)
        ),
    )


@mcp.tool()
async def search_semantic_scholar_authors(
    query: str,
    offset: int = 0,
    limit: int = 100,
    fields: Optional[List[str]] = None,
) -> Any:
    """Search authors by name, with offset pagination."""

    return await _execute(
        "author search",
        api.search_authors(
            query,
            offset=offset,
            limit=limit,
            fields=_use_fields(fields, DEFAULT_AUTHOR_FIELDS),
        ),
    )


@mcp.tool()
async def get_semantic_scholar_author_details(
    author_id: str,
    fields: Optional[List[str]] = None,
) -> Any:
    """Get one author by Semantic Scholar author ID."""

    return await _execute(
        "author lookup",
        api.get_author(author_id, fields=_use_fields(fields, DEFAULT_AUTHOR_FIELDS)),
    )


@mcp.tool()
async def get_semantic_scholar_author_papers(
    author_id: str,
    publication_date_or_year: Optional[str] = None,
    offset: int = 0,
    limit: int = 100,
    fields: Optional[List[str]] = None,
) -> Any:
    """List an author's papers, optionally filtering by publication date/year."""

    return await _execute(
        "author papers lookup",
        api.get_author_papers(
            author_id,
            publication_date_or_year=publication_date_or_year,
            offset=offset,
            limit=limit,
            fields=_use_fields(fields, DEFAULT_PAPER_SEARCH_FIELDS),
        ),
    )


# Academic Graph API: paper endpoints


@mcp.tool()
async def autocomplete_semantic_scholar_papers(query: str) -> Any:
    """Suggest paper-title query completions for a partial query."""

    return await _execute("paper autocomplete", api.autocomplete_papers(query))


@mcp.tool()
async def batch_get_semantic_scholar_papers(
    paper_ids: List[str],
    fields: Optional[List[str]] = None,
) -> Any:
    """Get multiple papers by S2, CorpusId, DOI, arXiv, ACL, MAG, PMID, or URL ID."""

    return await _execute(
        "batch paper lookup",
        api.batch_papers(
            paper_ids,
            fields=_use_fields(fields, DEFAULT_PAPER_DETAIL_FIELDS),
        ),
    )


@mcp.tool()
async def search_semantic_scholar_papers(
    query: str,
    offset: int = 0,
    limit: int = 10,
    fields: Optional[List[str]] = None,
    publication_types: Optional[List[str]] = None,
    open_access_pdf: bool = False,
    min_citation_count: Optional[int] = None,
    publication_date_or_year: Optional[str] = None,
    year: Optional[str] = None,
    venue: Optional[List[str]] = None,
    fields_of_study: Optional[List[str]] = None,
) -> Any:
    """Run relevance-ranked paper search with filters and offset pagination."""

    return await _execute(
        "paper relevance search",
        api.search_papers(
            query,
            fields=_use_fields(fields, DEFAULT_PAPER_SEARCH_FIELDS),
            publication_types=publication_types,
            open_access_pdf=open_access_pdf,
            min_citation_count=min_citation_count,
            publication_date_or_year=publication_date_or_year,
            year=year,
            venue=venue,
            fields_of_study=fields_of_study,
            offset=offset,
            limit=limit,
        ),
    )


@mcp.tool()
async def bulk_search_semantic_scholar_papers(
    query: str,
    token: Optional[str] = None,
    fields: Optional[List[str]] = None,
    sort: Optional[str] = None,
    publication_types: Optional[List[str]] = None,
    open_access_pdf: bool = False,
    min_citation_count: Optional[int] = None,
    publication_date_or_year: Optional[str] = None,
    year: Optional[str] = None,
    venue: Optional[List[str]] = None,
    fields_of_study: Optional[List[str]] = None,
) -> Any:
    """Run high-volume paper search; pass the returned token for the next page."""

    return await _execute(
        "paper bulk search",
        api.bulk_search_papers(
            query,
            token=token,
            fields=_use_fields(fields, DEFAULT_PAPER_SEARCH_FIELDS),
            sort=sort,
            publication_types=publication_types,
            open_access_pdf=open_access_pdf,
            min_citation_count=min_citation_count,
            publication_date_or_year=publication_date_or_year,
            year=year,
            venue=venue,
            fields_of_study=fields_of_study,
        ),
    )


@mcp.tool()
async def match_semantic_scholar_paper(
    query: str,
    fields: Optional[List[str]] = None,
    publication_types: Optional[List[str]] = None,
    open_access_pdf: bool = False,
    min_citation_count: Optional[int] = None,
    publication_date_or_year: Optional[str] = None,
    year: Optional[str] = None,
    venue: Optional[List[str]] = None,
    fields_of_study: Optional[List[str]] = None,
) -> Any:
    """Find the paper whose title best matches a supplied title."""

    return await _execute(
        "paper title match",
        api.match_paper(
            query,
            fields=_use_fields(fields, DEFAULT_PAPER_SEARCH_FIELDS),
            publication_types=publication_types,
            open_access_pdf=open_access_pdf,
            min_citation_count=min_citation_count,
            publication_date_or_year=publication_date_or_year,
            year=year,
            venue=venue,
            fields_of_study=fields_of_study,
        ),
    )


@mcp.tool()
async def get_semantic_scholar_paper_details(
    paper_id: str,
    fields: Optional[List[str]] = None,
) -> Any:
    """Get one paper by S2, CorpusId, DOI, arXiv, ACL, MAG, PMID, or URL ID."""

    return await _execute(
        "paper lookup",
        api.get_paper(
            paper_id,
            fields=_use_fields(fields, DEFAULT_PAPER_DETAIL_FIELDS),
        ),
    )


@mcp.tool()
async def get_semantic_scholar_paper_authors(
    paper_id: str,
    offset: int = 0,
    limit: int = 100,
    fields: Optional[List[str]] = None,
) -> Any:
    """List the authors of a paper with offset pagination."""

    return await _execute(
        "paper authors lookup",
        api.get_paper_authors(
            paper_id,
            offset=offset,
            limit=limit,
            fields=_use_fields(fields, DEFAULT_AUTHOR_FIELDS),
        ),
    )


@mcp.tool()
async def get_semantic_scholar_paper_citations(
    paper_id: str,
    publication_date_or_year: Optional[str] = None,
    offset: int = 0,
    limit: int = 100,
    fields: Optional[List[str]] = None,
) -> Any:
    """List papers citing a paper, including contexts, intents, and influence."""

    return await _execute(
        "paper citations lookup",
        api.get_paper_citations(
            paper_id,
            publication_date_or_year=publication_date_or_year,
            offset=offset,
            limit=limit,
            fields=_use_fields(fields, DEFAULT_CITATION_FIELDS),
        ),
    )


@mcp.tool()
async def get_semantic_scholar_paper_references(
    paper_id: str,
    offset: int = 0,
    limit: int = 100,
    fields: Optional[List[str]] = None,
) -> Any:
    """List a paper's references, including contexts, intents, and influence."""

    return await _execute(
        "paper references lookup",
        api.get_paper_references(
            paper_id,
            offset=offset,
            limit=limit,
            fields=_use_fields(fields, DEFAULT_REFERENCE_FIELDS),
        ),
    )


@mcp.tool()
async def search_semantic_scholar_snippets(
    query: str,
    limit: int = 10,
    fields: Optional[List[str]] = None,
    paper_ids: Optional[List[str]] = None,
    authors: Optional[List[str]] = None,
    min_citation_count: Optional[int] = None,
    inserted_before: Optional[str] = None,
    publication_date_or_year: Optional[str] = None,
    year: Optional[str] = None,
    venue: Optional[List[str]] = None,
    fields_of_study: Optional[List[str]] = None,
) -> Any:
    """Search relevant passages from paper titles, abstracts, and full text."""

    return await _execute(
        "snippet search",
        api.search_snippets(
            query,
            fields=fields,
            paper_ids=paper_ids,
            authors=authors,
            min_citation_count=min_citation_count,
            inserted_before=inserted_before,
            publication_date_or_year=publication_date_or_year,
            year=year,
            venue=venue,
            fields_of_study=fields_of_study,
            limit=limit,
        ),
    )


# Recommendations API


@mcp.tool()
async def recommend_semantic_scholar_papers_for_paper(
    paper_id: str,
    pool_from: str = "recent",
    limit: int = 100,
    fields: Optional[List[str]] = None,
) -> Any:
    """Recommend papers similar to one positive example paper."""

    return await _execute(
        "single-paper recommendations",
        api.recommend_papers_for_paper(
            paper_id,
            pool_from=pool_from,
            limit=limit,
            fields=_use_fields(fields, DEFAULT_PAPER_SEARCH_FIELDS),
        ),
    )


@mcp.tool()
async def recommend_semantic_scholar_papers(
    positive_paper_ids: List[str],
    negative_paper_ids: Optional[List[str]] = None,
    limit: int = 100,
    fields: Optional[List[str]] = None,
) -> Any:
    """Recommend papers from positive examples and optional negative examples."""

    return await _execute(
        "multi-paper recommendations",
        api.recommend_papers(
            positive_paper_ids,
            negative_paper_ids,
            limit=limit,
            fields=_use_fields(fields, DEFAULT_PAPER_SEARCH_FIELDS),
        ),
    )


# Datasets API


@mcp.tool()
async def list_semantic_scholar_dataset_releases() -> Any:
    """List all available Semantic Scholar dataset release IDs."""

    return await _execute("dataset release listing", api.list_dataset_releases())


@mcp.tool()
async def get_semantic_scholar_dataset_release(release_id: str) -> Any:
    """List datasets and metadata in a release; ``latest`` is accepted."""

    return await _execute(
        "dataset release lookup",
        api.get_dataset_release(release_id),
    )


@mcp.tool()
async def get_semantic_scholar_dataset_download_links(
    release_id: str,
    dataset_name: str,
) -> Any:
    """Get temporary download links for one dataset in a release."""

    return await _execute(
        "dataset download-link lookup",
        api.get_dataset_download_links(release_id, dataset_name),
    )


@mcp.tool()
async def get_semantic_scholar_dataset_diffs(
    start_release_id: str,
    end_release_id: str,
    dataset_name: str,
) -> Any:
    """Get incremental update/delete files between two dataset releases."""

    return await _execute(
        "dataset diff lookup",
        api.get_dataset_diffs(start_release_id, end_release_id, dataset_name),
    )


# Backward-compatible tools from the original server


@mcp.tool()
async def search_semantic_scholar(
    query: str,
    num_results: int = 10,
) -> Any:
    """Legacy paper search returning only the result list."""

    response = await _execute(
        "legacy paper search",
        api.search_papers(
            query,
            limit=num_results,
            fields=DEFAULT_PAPER_SEARCH_FIELDS,
        ),
    )
    if isinstance(response, dict) and "error" not in response:
        return response.get("data", [])
    return response


@mcp.tool()
async def get_semantic_scholar_citations_and_references(paper_id: str) -> Any:
    """Legacy helper returning the first page of citations and references."""

    citations, references = await asyncio.gather(
        _execute(
            "legacy citations lookup",
            api.get_paper_citations(
                paper_id,
                limit=100,
                fields=DEFAULT_CITATION_FIELDS,
            ),
        ),
        _execute(
            "legacy references lookup",
            api.get_paper_references(
                paper_id,
                limit=100,
                fields=DEFAULT_REFERENCE_FIELDS,
            ),
        ),
    )

    def data_or_error(value: JSONValue) -> Any:
        if isinstance(value, dict) and "error" not in value:
            return value.get("data", [])
        return value

    return {
        "citations": data_or_error(citations),
        "references": data_or_error(references),
    }


def main() -> None:
    """Run the Semantic Scholar MCP server over stdio."""

    logging.info(
        "Starting Semantic Scholar MCP server %s with 22 tools", __version__
    )
    mcp.run(transport="stdio")


if __name__ == "__main__":
    main()
