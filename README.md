# Semantic Scholar MCP Server

An unofficial, community-maintained toolkit for the public [Semantic Scholar APIs](https://api.semanticscholar.org/api-docs/): a [Model Context Protocol](https://modelcontextprotocol.io/) server, two CLIs, and two independently installable agent skills.

Version 2.3.0 provides 20 endpoint-aligned operations, two backward-compatible operations, a schema-driven endpoint CLI, an evidence-oriented ScholarQA CLI, and separate skills for endpoint routing and research synthesis.

> [!IMPORTANT]
> This project is not affiliated with or endorsed by Semantic Scholar or the Allen Institute for AI. API availability, terms, and rate limits are controlled by Semantic Scholar.

## Why this exists

Language-model agents often understand the research task but call the wrong API surface. Typical failures include using generic paper search for an exact-title lookup, treating autocomplete as evidence, confusing recommendations with citation edges, inventing unsupported endpoint names, or sending fields and pagination parameters to operations that do not accept them.

Raw REST documentation leaves endpoint selection, argument construction, and response handling to the model. This project separates those concerns into composable layers:

1. **MCP server:** exposes typed tool schemas directly to MCP-capable clients.
2. **Endpoint CLI:** lets shell-based agents inspect and call those same 22 operations with validated JSON.
3. **ScholarQA CLI:** collects auditable multi-query evidence bundles and batch-verifies citations without embedding an LLM provider.
4. **Two agent skills:** one teaches exact endpoint routing; the other teaches attributed evidence synthesis and research ideation.

The endpoint MCP and CLI share the same FastMCP definitions. The ScholarQA CLI uses the same direct API client but adds a bounded evidence workflow. Skills contain agent instructions, not another API implementation.

## Choose the pieces you need

The similarly named CLI and skill are deliberately separate:

| Layer | Runtime | Optional skill | Purpose |
|---|---|---|---|
| Endpoint access | `semanticscholar-mcp` or `semanticscholar-cli` | `$semantic-scholar-cli` | Select and call an exact API operation, including citations, references, recommendations, and datasets. |
| Research QA | `scholarqa-cli` or the MCP runtime | `$scholarqa-research` | Retrieve complementary evidence, build a claim ledger, synthesize multiple papers, and verify final citations. |

Common combinations:

| Goal | Install |
|---|---|
| Give an MCP-capable agent typed Semantic Scholar tools | MCP runtime only |
| Let a shell agent make exact endpoint calls | `semanticscholar-cli` + `$semantic-scholar-cli` |
| Let a shell agent perform evidence-first literature QA | `scholarqa-cli` + `$scholarqa-research` |
| Perform research QA through MCP | MCP runtime + `$scholarqa-research` |
| Add graph traversal or endpoint-level control to shell QA | Both CLIs + both skills |

Neither skill requires the other. The Python package installs all three executables, so one package can support any runtime combination. `npx skills` installs only the selected skill instructions.

`scholarqa-cli` intentionally stops at model-free evidence collection and citation verification. The agent using `$scholarqa-research` performs the reasoning and prose synthesis, so the CLI does not require a second model API key or hide unsupported claims inside an opaque generation step.

## Highlights

- **Broad API coverage:** authors, papers, citations, references, full-text snippets, recommendations, and dataset releases.
- **No Semantic Scholar SDK dependency:** the server uses a small asynchronous `httpx` client and depends only on `mcp` and `httpx`.
- **Native responses:** endpoint-aligned tools preserve Semantic Scholar's JSON response shape instead of converting it into a reduced local model.
- **Explicit pagination:** callers control offsets or continuation tokens; the server never silently crawls an unbounded result set.
- **Rate-limit aware:** HTTP 429 and transient 5xx responses use `Retry-After` when available and bounded exponential backoff otherwise.
- **Shared endpoint contract:** MCP and `semanticscholar-cli` use the same tool names, schemas, validation, and API client.
- **Auditable QA bundles:** `scholarqa-cli` records queries, filters, raw results, candidate IDs, partial failures, and evidence-level guidance.
- **Agent-ready skills:** `semantic-scholar-cli` provides strict endpoint routing, while `scholarqa-research` provides attributed, evidence-first synthesis and ideation.
- **Installable distribution:** the release ZIP installs `semanticscholar-mcp`, `semanticscholar-cli`, and `scholarqa-cli`.
- **Offline tests:** the test suite uses an in-memory HTTP transport and does not consume Semantic Scholar API quota.

## Requirements

- Python 3.10 or later
- An MCP client that supports stdio servers, if using the MCP transport
- Optional: a [Semantic Scholar API key](https://www.semanticscholar.org/product/api) for a dedicated rate limit

Anonymous requests work for many endpoints, but they use a heavily shared rate limit.

## Quick start

### Ask Codex or Claude Code to install it

Send the following entire message to your coding agent rather than only its first line. It deliberately requires the agent to ask which form you want before changing your environment:

```text
Install this Semantic Scholar MCP / CLI / skill toolkit for me:
https://github.com/XWang20/semanticscholar-MCP-Server

Before making any changes, first ask me which form I want:
1. MCP server
2. semanticscholar-cli (exact endpoint CLI)
3. scholarqa-cli (evidence collection and citation verification CLI)
4. semantic-scholar-cli skill (endpoint routing instructions)
5. scholarqa-research skill (research QA and ideation instructions)
6. a combination of these components

Do not choose for me and do not begin installation until I answer. After I answer,
detect whether you are running in Codex or Claude Code, follow the repository README,
ask whether the installation should be project-local or global when relevant, explain any
runtime a selected skill needs, and verify the selected components without exposing or
committing an API key.
```

中文版本：

```text
为我安装这个 Semantic Scholar MCP / CLI / skill 工具集：
https://github.com/XWang20/semanticscholar-MCP-Server

开始任何更改之前，先问我要安装哪一种形式：
1. MCP server
2. semanticscholar-cli（精确端点 CLI）
3. scholarqa-cli（证据收集与引用核验 CLI）
4. semantic-scholar-cli skill（端点路由指令）
5. scholarqa-research skill（研究问答与研究构思指令）
6. 这些组件的组合

不要替我选择，也不要在我回答前开始安装。得到确认后，再判断你当前运行在
Codex 还是 Claude Code 中；按照仓库 README 安装；如果涉及安装范围，再询问
是项目级还是全局安装；说明所选 skill 需要的 runtime；最后验证所选组件，
并且不要泄露或提交 API key。
```

### Install a release ZIP

```bash
python -m venv .venv
source .venv/bin/activate
python -m pip install ./semanticscholar-mcp-server-2.3.0.zip
```

The package installs all three entry points:

```bash
semanticscholar-mcp
semanticscholar-cli tools
scholarqa-cli --help
```

### Install from a source checkout

```bash
python -m venv .venv
source .venv/bin/activate
python -m pip install -e .
```

You can then use the console entry points above or run a module directly:

```bash
python semantic_scholar_server.py
python scholarqa_cli.py --help
```

On Windows PowerShell, activate the environment with `.venv\Scripts\Activate.ps1`.

## Endpoint CLI: `semanticscholar-cli`

The CLI intentionally does not invent a second set of friendly-but-different command names. It exposes the same 22 operation names and JSON schemas as MCP.

List operations:

```bash
semanticscholar-cli tools
semanticscholar-cli tools --json
```

Inspect one operation before calling it:

```bash
semanticscholar-cli schema search_semantic_scholar_papers
```

Call an operation with a JSON object:

```bash
semanticscholar-cli call search_semantic_scholar_papers \
  --params '{"query":"retrieval augmented generation","open_access_pdf":true,"limit":5}'
```

For larger inputs, use `--params-file params.json` or `--params -` to read JSON from stdin. Add `--compact` for single-line output.

Endpoint CLI exit statuses are designed for agents and scripts:

| Status | Meaning |
|---:|---|
| `0` | Successful operation. |
| `1` | The operation returned a top-level API `error`. |
| `2` | Invalid CLI input, schema mismatch, or unknown operation. |
| `130` | Interrupted by the user. |

## Research QA CLI: `scholarqa-cli`

The ScholarQA CLI prepares evidence for an agent; it does not generate a final answer. `collect` runs complementary snippet and paper searches for each query and emits one JSON bundle:

```bash
scholarqa-cli collect "Does retrieval-augmented generation reduce factual errors?" \
  --query "retrieval augmented generation factuality evaluation" \
  --query "RAG hallucination benchmark" \
  --year "2020-" > evidence.json
```

After the agent selects the papers that support its material claims, verify their canonical records:

```bash
scholarqa-cli verify ARXIV:2005.11401 DOI:10.1145/3786335.3813161 \
  > verified.json
```

IDs can also be provided as a JSON array or one ID per line with `--ids-file FILE`; use `--ids-file -` for stdin. Show the methodology sources and adaptation boundary with:

```bash
scholarqa-cli provenance
```

For `collect`, status `0` means all searches succeeded, status `1` means the JSON bundle contains usable partial results plus `operation_errors`, and status `2` means invalid input or a local failure. For `verify`, status `0` means every ID resolved and status `1` means at least one ID was unresolved or the upstream batch request failed. Both commands use `130` for interruption.

## Agent skills

The repository contains two Agent Skills-compatible skills. They can be installed and used separately:

| Skill | Best paired runtime | Purpose |
|---|---|---|
| [`semantic-scholar-cli`](skills/semantic-scholar-cli) | `semanticscholar-cli` | Select the exact Semantic Scholar operation and construct valid parameters. |
| [`scholarqa-research`](skills/scholarqa-research) | `scholarqa-cli` or MCP | Perform evidence-first multi-paper synthesis, citation verification, and Scideator-style facet ideation. |

`scholarqa-cli` and `scholarqa-research` form an independent Semantic Scholar adaptation, not the official Ai2 Scholar QA implementation. The evidence-QA workflow credits the [Ai2 Scholar QA paper](https://doi.org/10.18653/v1/2025.acl-demo.49) and official [`allenai/ai2-scholarqa-lib`](https://github.com/allenai/ai2-scholarqa-lib) repository. The ideation workflow credits the [Scideator paper](https://doi.org/10.1145/3786335.3813161). See the skill's [provenance reference](skills/scholarqa-research/references/provenance.md) and [third-party notices](THIRD_PARTY_NOTICES.md) for scope, licenses, and adaptation boundaries. No upstream ScholarQA code or runtime dependency is bundled.

### Install with `npx skills`

List the available skills:

```bash
npx skills add XWang20/semanticscholar-MCP-Server --list
```

Install either skill for the current project; the installer detects supported agents:

```bash
npx skills add XWang20/semanticscholar-MCP-Server \
  --skill semantic-scholar-cli

npx skills add XWang20/semanticscholar-MCP-Server \
  --skill scholarqa-research
```

Install both together:

```bash
npx skills add XWang20/semanticscholar-MCP-Server \
  --skill semantic-scholar-cli --skill scholarqa-research
```

Or install either skill globally for a specific agent:

```bash
# Codex
npx skills add XWang20/semanticscholar-MCP-Server \
  --skill scholarqa-research --global --agent codex

# Claude Code
npx skills add XWang20/semanticscholar-MCP-Server \
  --skill scholarqa-research --global --agent claude-code
```

`npx skills` installs skill instructions only. It does not install the Python package or configure an MCP client. Install the Python package when the endpoint skill needs `semanticscholar-cli`, or when the research skill will use `scholarqa-cli`. The research skill may instead use an already configured MCP runtime.

### Install the skill manually

Extract the standalone skill ZIP into the appropriate global skills directory, or copy the source directory directly:

```bash
# Codex
unzip semantic-scholar-cli-skill-1.1.0.zip -d ~/.codex/skills
unzip scholarqa-research-1.1.0.zip -d ~/.codex/skills

# Claude Code
unzip semantic-scholar-cli-skill-1.1.0.zip -d ~/.claude/skills
unzip scholarqa-research-1.1.0.zip -d ~/.claude/skills

# Or, from a source checkout (Codex examples):
cp -R skills/semantic-scholar-cli ~/.codex/skills/
cp -R skills/scholarqa-research ~/.codex/skills/
```

Invoke a skill explicitly, for example:

```text
Use $semantic-scholar-cli to find recent open-access papers about retrieval-augmented generation and verify the final paper records.

Use $scholarqa-research to synthesize the evidence for whether retrieval-augmented generation reduces factual errors, with verified citations and limitations.
```

`semantic-scholar-cli` expects `semanticscholar-cli` and can use `python semantic_scholar_cli.py` during local development. `scholarqa-research` can use either `scholarqa-cli` (`python scholarqa_cli.py` in a checkout) or the connected MCP server. Install both skills only when the task benefits from both high-level research synthesis and low-level endpoint control.

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

Once the MCP server, CLI, or corresponding skills are available, an assistant can handle requests such as:

- “Find recent open-access papers about retrieval-augmented generation.”
- “Resolve this DOI and return its references with citation contexts.”
- “Recommend papers similar to these two papers but unlike this negative example.”
- “Search full-text snippets for evidence about calibration in scientific QA.”
- “List the datasets in the latest Semantic Scholar dataset release.”
- “Synthesize the evidence across these papers, cite every material claim, and surface disagreements.”
- “Generate facet-grounded research ideas from these seed papers, then check novelty against retrieved literature.”

The exact natural-language workflow depends on the agent. MCP exposes typed tools, `semanticscholar-cli` exposes the same endpoint schemas to shell agents, and `scholarqa-cli` packages evidence for the research skill to synthesize.

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

| MCP/CLI operation | REST operation |
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

| MCP/CLI operation | REST operation |
|---|---|
| `recommend_semantic_scholar_papers_for_paper` | `GET /recommendations/v1/papers/forpaper/{paper_id}` |
| `recommend_semantic_scholar_papers` | `POST /recommendations/v1/papers/` |

Single-paper recommendations support the `recent` and `all-cs` pools. Multi-paper recommendations accept positive and optional negative paper IDs. The API returns at most 500 recommendations per request.

### Datasets API

| MCP/CLI operation | REST operation |
|---|---|
| `list_semantic_scholar_dataset_releases` | `GET /datasets/v1/release/` |
| `get_semantic_scholar_dataset_release` | `GET /datasets/v1/release/{release_id}` |
| `get_semantic_scholar_dataset_download_links` | `GET /datasets/v1/release/{release_id}/dataset/{dataset_name}` |
| `get_semantic_scholar_dataset_diffs` | `GET /datasets/v1/diffs/{start}/to/{end}/{dataset_name}` |

Dataset tools return release metadata and temporary download URLs. They do not automatically download multi-gigabyte datasets. The identifier `latest` is accepted wherever the upstream API supports it.

### Backward-compatible tools

Two tool names are retained for clients built against the original project:

| MCP/CLI operation | Behavior |
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
- The CLI prints the same normalized JSON and returns a nonzero exit status for API or schema errors.
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
semantic_scholar_cli.py       Schema inspection and JSON command-line dispatch
semantic_scholar_server.py    FastMCP server and 22 registered tools
scholarqa_cli.py               Evidence-bundle collection and citation verification
skills/semantic-scholar-cli/  Endpoint-routing skill for shell-based agents
skills/scholarqa-research/    Attributed evidence synthesis and ideation skill
tests/                        Offline API, CLI, and tool-registration tests
pyproject.toml                Package metadata and three console entry points
requirements.txt              Minimal runtime dependencies
THIRD_PARTY_NOTICES.md        ScholarQA and Scideator attribution boundaries
```

### Contribution guidelines

Contributions are welcome. A change should:

1. Preserve the upstream JSON response shape for endpoint-aligned tools.
2. Keep pagination explicit and bounded.
3. Add or update offline tests for endpoint paths, parameters, payloads, CLI behavior, and tool registration.
4. Avoid adding a heavyweight API SDK when the direct client can support the operation clearly.
5. Never include API keys, generated bytecode, virtual environments, or large downloaded datasets.
6. Run `python -m unittest discover -v` before opening a pull request.

For new upstream endpoints, update the client method, MCP tool, tool-registration test, skill routing reference, and this catalog together. The CLI discovers the MCP schema automatically and should not maintain a separate endpoint registry.

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

Research workflows and adapted third-party material retain their original attribution and license boundaries as documented in [THIRD_PARTY_NOTICES.md](THIRD_PARTY_NOTICES.md). In particular, this repository does not relicense or claim authorship of Ai2 Scholar QA or Scideator.

“Semantic Scholar” is used only to identify compatibility with the public service. This project does not claim ownership of the Semantic Scholar name, API, data, or trademarks.
