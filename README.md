# Semantic Scholar MCP Server

An unofficial, community-maintained [Model Context Protocol](https://modelcontextprotocol.io/) server for the public [Semantic Scholar APIs](https://api.semanticscholar.org/api-docs/).

It exposes the Academic Graph, Recommendations, and Datasets APIs to MCP clients over stdio. Version 2.0.0 provides 20 endpoint-aligned tools plus two backward-compatible tools.

> [!IMPORTANT]
> This project is not affiliated with or endorsed by Semantic Scholar or the Allen Institute for AI. API availability, terms, and rate limits are controlled by Semantic Scholar.

## Highlights

- **Broad API coverage:** authors, papers, citations, references, full-text snippets, recommendations, and dataset releases.
- **No Semantic Scholar SDK dependency:** the server uses a small asynchronous `httpx` client and depends only on `mcp` and `httpx`.
- **Native responses:** endpoint-aligned tools preserve Semantic Scholar's JSON response shape instead of converting it into a reduced local model.
- **Explicit pagination:** callers control offsets or continuation tokens; the server never silently crawls an unbounded result set.
- **Rate-limit aware:** HTTP 429 and transient 5xx responses use `Retry-After` when available and bounded exponential backoff otherwise.
- **Installable distribution:** run from source or install the release ZIP as a Python package with the `semanticscholar-mcp` console entry point.
- **Offline tests:** the test suite uses an in-memory HTTP transport and does not consume Semantic Scholar API quota.

## Requirements

- Python 3.10 or later
- An MCP client that supports stdio servers
- Optional: a [Semantic Scholar API key](https://www.semanticscholar.org/product/api) for a dedicated rate limit

Anonymous requests work for many endpoints, but they use a heavily shared rate limit.

## Quick start

### Install a release ZIP

```bash
python -m venv .venv
source .venv/bin/activate
python -m pip install ./semanticscholar-mcp-server-2.0.0.zip
```

Start the installed stdio server:

```bash
semanticscholar-mcp
```

### Install from a source checkout

```bash
python -m venv .venv
source .venv/bin/activate
python -m pip install -e .
```

You can then use the console entry point above or run the module directly:

```bash
python semantic_scholar_server.py
```

On Windows PowerShell, activate the environment with `.venv\Scripts\Activate.ps1`.

## MCP client configuration

After installing the package, configure your MCP client with the absolute path to the virtual environment's console script:

```json
{
  "mcpServers": {
    "semanticscholar": {
      "command": "/absolute/path/to/.venv/bin/semanticscholar-mcp",
      "env": {
        "SEMANTIC_SCHOLAR_API_KEY": "your-optional-api-key"
      }
    }
  }
}
```

For a source checkout without package installation:

```json
{
  "mcpServers": {
    "semanticscholar": {
      "command": "/absolute/path/to/.venv/bin/python",
      "args": ["/absolute/path/to/semantic_scholar_server.py"],
      "env": {
        "SEMANTIC_SCHOLAR_API_KEY": "your-optional-api-key"
      }
    }
  }
}
```

Do not commit an API key to an MCP configuration stored in a public repository. Prefer your client's secret or environment-variable mechanism when available.

## Example requests

Once the server is connected, an MCP-capable assistant can handle requests such as:

- “Find recent open-access papers about retrieval-augmented generation.”
- “Resolve this DOI and return its references with citation contexts.”
- “Recommend papers similar to these two papers but unlike this negative example.”
- “Search full-text snippets for evidence about calibration in scientific QA.”
- “List the datasets in the latest Semantic Scholar dataset release.”

The exact natural-language workflow depends on the MCP client. The server itself exposes typed tools rather than a chat interface.

## Configuration

| Environment variable | Default | Description |
|---|---:|---|
| `SEMANTIC_SCHOLAR_API_KEY` | unset | Sent to Semantic Scholar as the `x-api-key` header. |
| `SEMANTIC_SCHOLAR_TIMEOUT` | `30` | Request timeout in seconds. |
| `SEMANTIC_SCHOLAR_MAX_RETRIES` | `3` | Retries for HTTP 429 and transient 5xx responses. |
| `SEMANTIC_SCHOLAR_API_URL` | `https://api.semanticscholar.org` | API origin override, primarily for tests and compatible proxies. |

> [!CAUTION]
> When `SEMANTIC_SCHOLAR_API_URL` is overridden, the API key is sent to that origin. Only use an endpoint you trust.

## Tool catalog

### Academic Graph API

| MCP tool | REST operation |
|---|---|
| `batch_get_semantic_scholar_authors` | `POST /graph/v1/author/batch` |
| `search_semantic_scholar_authors` | `GET /graph/v1/author/search` |
| `get_semantic_scholar_author_details` | `GET /graph/v1/author/{author_id}` |
| `get_semantic_scholar_author_papers` | `GET /graph/v1/author/{author_id}/papers` |
| `autocomplete_semantic_scholar_papers` | `GET /graph/v1/paper/autocomplete` |
| `batch_get_semantic_scholar_papers` | `POST /graph/v1/paper/batch` |
| `search_semantic_scholar_papers` | `GET /graph/v1/paper/search` |
| `bulk_search_semantic_scholar_papers` | `GET /graph/v1/paper/search/bulk` |
| `match_semantic_scholar_paper` | `GET /graph/v1/paper/search/match` |
| `get_semantic_scholar_paper_details` | `GET /graph/v1/paper/{paper_id}` |
| `get_semantic_scholar_paper_authors` | `GET /graph/v1/paper/{paper_id}/authors` |
| `get_semantic_scholar_paper_citations` | `GET /graph/v1/paper/{paper_id}/citations` |
| `get_semantic_scholar_paper_references` | `GET /graph/v1/paper/{paper_id}/references` |
| `search_semantic_scholar_snippets` | `GET /graph/v1/snippet/search` |

Paper search exposes publication type, open-access, minimum citation count, publication date/year, venue, and field-of-study filters. Bulk search uses token pagination and supports sorting. Citation and reference tools can request citation contexts, intents, context/intent pairs, and influential-citation status.

### Recommendations API

| MCP tool | REST operation |
|---|---|
| `recommend_semantic_scholar_papers_for_paper` | `GET /recommendations/v1/papers/forpaper/{paper_id}` |
| `recommend_semantic_scholar_papers` | `POST /recommendations/v1/papers/` |

Single-paper recommendations support the `recent` and `all-cs` pools. Multi-paper recommendations accept positive and optional negative paper IDs. The API returns at most 500 recommendations per request.

### Datasets API

| MCP tool | REST operation |
|---|---|
| `list_semantic_scholar_dataset_releases` | `GET /datasets/v1/release/` |
| `get_semantic_scholar_dataset_release` | `GET /datasets/v1/release/{release_id}` |
| `get_semantic_scholar_dataset_download_links` | `GET /datasets/v1/release/{release_id}/dataset/{dataset_name}` |
| `get_semantic_scholar_dataset_diffs` | `GET /datasets/v1/diffs/{start}/to/{end}/{dataset_name}` |

Dataset tools return release metadata and temporary download URLs. They do not automatically download multi-gigabyte datasets. The identifier `latest` is accepted wherever the upstream API supports it.

### Backward-compatible tools

Two tool names are retained for clients built against the original project:

| MCP tool | Behavior |
|---|---|
| `search_semantic_scholar` | Returns only the paper result list from the first relevance-search request. |
| `get_semantic_scholar_citations_and_references` | Returns the first page of both relationships. |

New integrations should use the endpoint-aligned search, citation, and reference tools because they expose filters, fields, and independent pagination.

## Paper identifiers and response fields

Paper tools accept identifiers supported by Semantic Scholar, including:

- Semantic Scholar paper ID
- `CorpusId:`
- `DOI:`
- `ARXIV:`
- `ACL:`
- `MAG:`
- `PMID:` and `PMCID:`
- supported Semantic Scholar paper URLs

Most tools accept a `fields` list. Useful paper fields include `abstract`, `authors`, `externalIds`, `openAccessPdf`, `tldr`, `journal`, `citationStyles`, `s2FieldsOfStudy`, and `embedding`.

Default field sets are intentionally rich but exclude the large embedding vector. Request it explicitly when needed:

```json
{
  "paper_id": "ARXIV:2005.11401",
  "fields": ["paperId", "title", "embedding"]
}
```

## Pagination, retries, and errors

- Offset-paginated tools return only the requested page.
- Bulk paper search returns the upstream continuation token; pass it back to request the next page.
- The server honors `Retry-After` for throttled responses and otherwise uses bounded exponential backoff.
- Validation, upstream HTTP, and unexpected transport failures are returned as `{"error": "..."}` so one failed request does not terminate the MCP server.
- A successful empty result is returned unchanged and is not converted into an error.

Semantic Scholar can change limits or schemas independently of this project. Consult the official API documentation when an upstream validation rule differs from the server's current defaults.

## Security and data handling

- Queries, identifiers, filters, and requested fields are sent to the configured Semantic Scholar API origin.
- The API key is used only as the `x-api-key` request header.
- The server does not persist API responses, maintain a paper database, or automatically download dataset files.
- Avoid placing secrets in prompts, search queries, logs, issues, or public MCP configuration files.
- Dataset download URLs can be temporary and should be treated accordingly.

If you discover a security issue, do not publish credentials or exploit details in a public issue. Use the repository owner's private security-reporting channel; if none is listed, open a minimal issue requesting private contact without disclosing the vulnerability.

## Development

Create a development environment and install the project in editable mode:

```bash
python -m venv .venv
source .venv/bin/activate
python -m pip install -e .
```

Run the complete test suite:

```bash
python -m unittest discover -v
```

The tests use `httpx.MockTransport`; they do not call the live Semantic Scholar API or consume rate-limit quota.

### Project layout

```text
semantic_scholar_api.py       Async HTTP client, validation, retries, and API paths
semantic_scholar_server.py    FastMCP server and 22 registered tools
tests/                        Offline API and tool-registration tests
pyproject.toml                Package metadata and console entry point
requirements.txt              Minimal runtime dependencies
```

### Contribution guidelines

Contributions are welcome. A change should:

1. Preserve the upstream JSON response shape for endpoint-aligned tools.
2. Keep pagination explicit and bounded.
3. Add or update offline tests for endpoint paths, parameters, payloads, and tool registration.
4. Avoid adding a heavyweight API SDK when the direct client can support the operation clearly.
5. Never include API keys, generated bytecode, virtual environments, or large downloaded datasets.
6. Run `python -m unittest discover -v` before opening a pull request.

For new upstream endpoints, update the client method, MCP tool, tool-registration test, and this catalog together.

## API references

- [Academic Graph API](https://api.semanticscholar.org/api-docs/graph)
- [Recommendations API](https://api.semanticscholar.org/api-docs/recommendations)
- [Datasets API](https://api.semanticscholar.org/api-docs/datasets)
- [Semantic Scholar API overview](https://www.semanticscholar.org/product/api)
- [Model Context Protocol](https://modelcontextprotocol.io/)

## Project lineage

Version 2 is a substantial rewrite and expansion of [JackKuo666/semanticscholar-MCP-Server](https://github.com/JackKuo666/semanticscholar-MCP-Server). It replaces the original SDK-backed runtime with a direct asynchronous API client, expands coverage from four tools to 22, preserves native responses, and adds pagination, retry handling, tests, and packaging.

The two original high-level tool names listed under backward compatibility remain available so existing clients can migrate gradually. Repository history and this attribution are retained in recognition of the original work.

## License

Distributed under the [MIT License](LICENSE).

“Semantic Scholar” is used only to identify compatibility with the public service. This project does not claim ownership of the Semantic Scholar name, API, data, or trademarks.
