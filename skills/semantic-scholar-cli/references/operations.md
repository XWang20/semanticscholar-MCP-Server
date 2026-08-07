# Semantic Scholar CLI operation routing

Use this reference to select an operation and construct valid JSON parameters. Confirm the installed schema with `semanticscholar-cli schema TOOL` before relying on optional fields.

## Contents

1. CLI protocol
2. Operation map
3. Identifier and field conventions
4. Filters and pagination
5. Common call patterns

## 1. CLI protocol

```bash
semanticscholar-cli tools
semanticscholar-cli tools --json
semanticscholar-cli schema TOOL
semanticscholar-cli call TOOL --params '{...}'
semanticscholar-cli call TOOL --params-file params.json
```

All call parameters form one JSON object. Lists are JSON arrays, booleans are `true` or `false`, and omitted optional values use server defaults. Output is JSON. Add `--compact` for single-line output.

## 2. Operation map

### Authors

| Intent | Operation | Core parameters |
|---|---|---|
| Search authors by name | `search_semantic_scholar_authors` | `query`; optional `offset`, `limit`, `fields` |
| Fetch one known author | `get_semantic_scholar_author_details` | `author_id`; optional `fields` |
| Fetch many known authors | `batch_get_semantic_scholar_authors` | `author_ids`; optional `fields` |
| List an author's papers | `get_semantic_scholar_author_papers` | `author_id`; optional date filter, `offset`, `limit`, `fields` |

### Paper discovery and resolution

| Intent | Operation | Core parameters |
|---|---|---|
| Complete a partial title query | `autocomplete_semantic_scholar_papers` | `query` |
| Resolve a supplied title | `match_semantic_scholar_paper` | `query`; optional paper filters and `fields` |
| Relevance-ranked discovery | `search_semantic_scholar_papers` | `query`; optional filters, `offset`, `limit`, `fields` |
| High-volume discovery | `bulk_search_semantic_scholar_papers` | `query`; optional filters, `token`, `sort`, `fields` |
| Fetch one known paper | `get_semantic_scholar_paper_details` | `paper_id`; optional `fields` |
| Fetch many known papers | `batch_get_semantic_scholar_papers` | `paper_ids`; optional `fields` |
| List a paper's authors | `get_semantic_scholar_paper_authors` | `paper_id`; optional `offset`, `limit`, `fields` |
| Search evidence passages | `search_semantic_scholar_snippets` | `query`; optional paper/author and publication filters |

Use autocomplete only to improve a title string. Use match to resolve the title to a paper record. Use snippet search when a question needs passage-level support rather than paper discovery alone.

### Citation graph and recommendations

| Intent | Operation | Core parameters |
|---|---|---|
| Papers citing the seed | `get_semantic_scholar_paper_citations` | `paper_id`; optional date filter, `offset`, `limit`, `fields` |
| References cited by the seed | `get_semantic_scholar_paper_references` | `paper_id`; optional `offset`, `limit`, `fields` |
| Similar papers from one seed | `recommend_semantic_scholar_papers_for_paper` | `paper_id`; optional `pool_from`, `limit`, `fields` |
| Similar papers from positive/negative seeds | `recommend_semantic_scholar_papers` | `positive_paper_ids`; optional `negative_paper_ids`, `limit`, `fields` |

Recommendations model similarity; citations model explicit graph edges. Do not substitute one for the other.

### Dataset releases

| Intent | Operation | Core parameters |
|---|---|---|
| List release IDs | `list_semantic_scholar_dataset_releases` | none |
| Inspect one release | `get_semantic_scholar_dataset_release` | `release_id` (`latest` allowed upstream) |
| Get download URLs | `get_semantic_scholar_dataset_download_links` | `release_id`, `dataset_name` |
| Get incremental diffs | `get_semantic_scholar_dataset_diffs` | `start_release_id`, `end_release_id`, `dataset_name` |

Dataset operations return metadata or temporary URLs; they do not download dataset files.

### Legacy compatibility

| Operation | Limitation |
|---|---|
| `search_semantic_scholar` | Returns only a first result list and omits modern filters. |
| `get_semantic_scholar_citations_and_references` | Combines only the first page of each relationship. |

Do not select a legacy operation for new workflows.

## 3. Identifier and field conventions

Paper IDs may be an S2 paper ID or a supported prefixed/external identifier such as `CorpusId:`, `DOI:`, `ARXIV:`, `ACL:`, `MAG:`, `PMID:`, or `PMCID:`. Supported paper URLs may also work.

Useful screening fields:

```json
["paperId", "title", "authors", "year", "abstract", "venue", "externalIds", "url", "openAccessPdf", "citationCount", "publicationDate", "publicationTypes", "fieldsOfStudy"]
```

Useful final-verification fields:

```json
["paperId", "title", "authors", "year", "externalIds", "url"]
```

The large `embedding` field is excluded from defaults. Request it explicitly only when required.

## 4. Filters and pagination

Paper search and related operations may expose:

- `publication_types`: JSON array such as `["JournalArticle", "Conference"]`;
- `open_access_pdf`: boolean;
- `min_citation_count`: integer;
- `publication_date_or_year` and/or `year`: upstream-supported date expressions;
- `venue`: JSON array;
- `fields_of_study`: JSON array.

Use `offset` and `limit` for ordinary search, authors, citations, and references. Use the returned `token` for the next bulk-search page. Never invent a token or assume a missing token means an error.

## 5. Common call patterns

Resolve a title:

```bash
semanticscholar-cli call match_semantic_scholar_paper \
  --params '{"query":"Retrieval-Augmented Generation for Knowledge-Intensive NLP Tasks"}'
```

Search recent open-access papers:

```bash
semanticscholar-cli call search_semantic_scholar_papers \
  --params '{"query":"scientific question answering","open_access_pdf":true,"year":"2024-","limit":10}'
```

Search evidence passages:

```bash
semanticscholar-cli call search_semantic_scholar_snippets \
  --params '{"query":"retrieval reduces hallucination","limit":10}'
```

Batch-verify papers:

```bash
semanticscholar-cli call batch_get_semantic_scholar_papers \
  --params '{"paper_ids":["ARXIV:2005.11401","ARXIV:2310.11511"],"fields":["paperId","title","authors","year","externalIds","url"]}'
```

Get multi-seed recommendations:

```bash
semanticscholar-cli call recommend_semantic_scholar_papers \
  --params '{"positive_paper_ids":["ARXIV:2005.11401"],"negative_paper_ids":[],"limit":20}'
```

When a call returns `{"error": ...}`, inspect the message and the operation schema. Do not report the failed response as an empty scholarly result.
