# Semantic Scholar retrieval playbook

Use this reference for deep or multi-stage searches. Tool prefixes may vary by client; select tools by operation name.

## Transport selection

Use one primary transport for a run:

- `scholarqa-cli collect` packages complementary snippet and paper searches into one auditable JSON bundle. It is the shortest shell path for Evidence QA.
- `scholarqa-cli verify` batch-resolves the papers selected for final citation.
- Semantic Scholar MCP exposes the same underlying academic source as direct typed tools and is preferable when the agent already has MCP access or needs interactive graph expansion.
- `semanticscholar-cli` exposes all endpoint-aligned operations in a shell. The separate `semantic-scholar-cli` skill helps choose them, but neither is required when `scholarqa-cli` covers the task.

Example CLI retrieval and verification:

```bash
scholarqa-cli collect "Does retrieval-augmented generation reduce factual errors?" \
  --query "retrieval augmented generation factuality evaluation" \
  --query "RAG hallucination benchmark" \
  --year "2020-" > evidence.json

scholarqa-cli verify S2_PAPER_ID DOI:10.0000/example > verified.json
```

Treat a `collect` exit status of `1` as a partial bundle: retain usable results and inspect `operation_errors`. For `verify`, status `1` also covers unresolved IDs; remove or replace those citations. Status `2` is an input or local execution error. The CLI output is evidence input, not a finished answer.

## Endpoint selection

| Need | Preferred operation | Notes |
|---|---|---|
| Direct evidence passages | `search_semantic_scholar_snippets` | Search titles, abstracts, and available full text. Omit `fields` unless the server documents supported snippet fields. |
| Ranked paper discovery | `search_semantic_scholar_papers` | Use for relevance search with year, venue, field, type, citation, and open-access filters. |
| High-volume discovery | `bulk_search_semantic_scholar_papers` | Use tokens until the planned stopping rule is met; record every token/page. |
| Exact title resolution | `match_semantic_scholar_paper` | Confirm the match score and title before treating it as canonical. |
| Partial title assistance | `autocomplete_semantic_scholar_papers` | Use only to form or resolve a title, not as evidence. |
| One paper's metadata | `get_semantic_scholar_paper_details` | Accept S2, DOI, arXiv, ACL, MAG, PMID, CorpusId, or URL identifiers. |
| Citation verification | `batch_get_semantic_scholar_papers` | Batch all final citations and request only necessary fields. |
| Backward citation chasing | `get_semantic_scholar_paper_references` | Expand a few high-value seeds; do not crawl indiscriminately. |
| Forward citation chasing | `get_semantic_scholar_paper_citations` | Useful for updates, replications, critiques, and later applications. |
| Similar-paper discovery | `recommend_semantic_scholar_papers` | Use positive seeds and optional negative seeds to diversify retrieval. |

Avoid legacy helper operations when canonical endpoints are available.

## Query construction

For each subquestion, prepare complementary queries:

1. **Concept query:** main phenomenon plus common synonyms.
2. **Method query:** phenomenon plus measurement, benchmark, intervention, or study design.
3. **Conflict query:** phenomenon plus failure, limitation, replication, contradiction, or critique when appropriate.
4. **Recency query:** apply an explicit year or publication-date filter for current-state questions.

Do not stuff every synonym into one query. Run short, distinct searches and merge their results.

## Retrieval sequence

1. Run snippet and paper search for each subquestion.
2. Deduplicate results before expansion.
3. Select high-relevance seed papers.
4. Expand references for foundations and methods.
5. Expand citations for newer evidence, replications, and critiques.
6. Use recommendations only to fill a documented topical or methodological gap.
7. Stop when new pages mostly duplicate known evidence or the planned limit is reached.

For broad discovery, maintain a small search log containing query, filters, returned count, pagination state, and reason for stopping.

## Metadata fields

For discovery, request only fields needed for screening:

`paperId`, `title`, `authors`, `year`, `abstract`, `venue`, `externalIds`, `url`, `openAccessPdf`, `citationCount`, `publicationDate`, `publicationTypes`, `fieldsOfStudy`.

For final verification, resolve each record again and confirm at least:

`paperId`, `title`, `authors`, `year`, `externalIds`, `url`.

## Evidence tiers

Rank evidence availability separately from study quality:

- **Tier A:** A retrieved full-text passage directly supports or contradicts the claim.
- **Tier B:** The abstract directly supports or contradicts the claim.
- **Tier C:** Metadata establishes only publication identity or context.
- **Tier D:** The relationship is inferred from titles, citation links, or recommendations; do not use it as substantive support.

Do not quote an abstract as though it were full text. Do not infer study results from a title.

## Rate limits and API errors

- Keep concurrent Semantic Scholar calls low; prefer batches for record verification.
- On HTTP 429, pause expansion, reduce concurrency, and retry only the failed request.
- Some MCP wrappers return `{ "error": ... }` inside a result while setting `isError` to false. Inspect both.
- A successful empty result is not an API failure. Broaden the query only if the empty result conflicts with the intended scope.
- Do not repeatedly retry invalid fields or malformed filters; correct the request first.

## Coverage language

Use precise wording:

- "The retrieved literature suggests..." for ordinary searches.
- "Within the searched Semantic Scholar records..." for broad searches.
- Reserve "systematic" for a documented protocol with reproducible queries, screening, and exclusions.
