---
name: semantic-scholar-cli
description: Route scholarly discovery, exact paper resolution, author lookup, citation traversal, full-text snippet search, recommendations, and dataset inspection through the schema-driven `semanticscholar-cli`. Use when an agent must call Semantic Scholar from a shell, when MCP is unavailable, or when choosing the exact API operation and valid parameters matters. Do not use for general web research or make substantive claims from metadata-only results.
---

# Semantic Scholar CLI

## Goal

Choose the narrowest correct Semantic Scholar operation, inspect its live schema, call it with a JSON object, and preserve the native response. Do not guess endpoint names or arguments.

The CLI and MCP server share the same 22 FastMCP tool definitions. Treat `tools` and `schema` output as authoritative when this skill and the installed version differ.

## Workflow

1. Confirm `semanticscholar-cli` is available. If working from this repository before installation, use `python semantic_scholar_cli.py` instead.
2. Translate the request into one or more bounded retrieval operations.
3. Select the operation using the routing rules below. Read [references/operations.md](references/operations.md) completely for unfamiliar, filtered, paginated, or multi-stage tasks.
4. Inspect the operation before its first call:

   ```bash
   semanticscholar-cli schema search_semantic_scholar_papers
   ```

5. Pass arguments as one JSON object:

   ```bash
   semanticscholar-cli call search_semantic_scholar_papers \
     --params '{"query":"retrieval augmented generation","limit":5}'
   ```

6. Inspect both the process exit status and a top-level `error` field. Correct invalid parameters rather than retrying them unchanged.
7. Preserve paper IDs, external IDs, pagination state, and evidence provenance for downstream synthesis.

Use `--params-file FILE` for complex input or `--params -` to read a JSON object from stdin. Use `--compact` when another program will consume the response.

## Route to the correct operation

- **Exact or near-exact title:** `match_semantic_scholar_paper`.
- **Partial title completion only:** `autocomplete_semantic_scholar_papers`; never use autocomplete output as evidence.
- **Ordinary topical paper discovery:** `search_semantic_scholar_papers`.
- **High-volume discovery or token pagination:** `bulk_search_semantic_scholar_papers`.
- **Passage-level evidence from available full text:** `search_semantic_scholar_snippets`.
- **One known paper or author:** the corresponding `get_*_details` operation.
- **Many known IDs:** a `batch_get_*` operation instead of repeated single calls.
- **Works citing a paper:** `get_semantic_scholar_paper_citations`.
- **Works cited by a paper:** `get_semantic_scholar_paper_references`.
- **Similar papers:** a recommendation operation, not citations or generic search.
- **An author's publication list:** `get_semantic_scholar_author_papers`.
- **Dataset releases and download links:** the four dataset operations.

Avoid the two legacy tools unless compatibility is explicitly required. They expose fewer controls and collapse pagination.

## Retrieval discipline

- Resolve ambiguous titles or identifiers before treating a result as canonical.
- Request only fields needed for screening; batch-fetch final records for verification.
- Do not treat citation count, recommendation rank, or title similarity as evidence that a claim is true.
- Label whether support comes from a full-text snippet, abstract, or metadata only.
- Deduplicate by Semantic Scholar paper ID, then DOI/arXiv ID, then normalized title.
- Keep pagination explicit. Continue only when the task requires more coverage and retain the returned offset or token.
- Prefer DOI, arXiv, or Semantic Scholar URLs in user-facing citations.

## Error and rate-limit handling

Exit status `0` indicates a successful result, `1` indicates a tool result containing a top-level API error, and `2` indicates a CLI/schema/argument error.

On throttling, let the built-in bounded retry policy run. After repeated rate limits, reduce request frequency or batch IDs; do not create a tight retry loop. An empty successful result is not an API failure.

If the executable is missing, report that the package must be installed. Do not silently switch to invented REST calls. If the user permits a fallback and the Semantic Scholar MCP server is available, use the exact same operation name there.
