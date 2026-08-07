# Evidence synthesis and reporting

Use this reference for substantial reviews, comparisons, and claim audits.

## Internal claim ledger

Build this ledger before drafting prose. It may remain internal unless the user asks to inspect it.

| Field | Required content |
|---|---|
| `claim` | One bounded statement, not a paragraph-sized conclusion. |
| `paper_id` | Canonical Semantic Scholar paper ID and stable DOI/arXiv ID when available. |
| `evidence` | Exact retrieved passage or a faithful abstract excerpt/summary. |
| `evidence_tier` | A, B, C, or D as defined in the main skill and `retrieval.md`. |
| `relationship` | Supports, contradicts, qualifies, or contextualizes. |
| `study_context` | Population, dataset, method, comparison, and outcome when available. |
| `confidence` | High, medium, or low, with a short reason. |

Require Tier A or B evidence for substantive claims. Use Tier C only for bibliographic context. Never use Tier D alone to report a finding.

## Synthesis rules

1. Group evidence around answers to the research question.
2. Cite claims at sentence or tightly bounded paragraph level.
3. Report the strongest counterevidence near the claim it qualifies.
4. Explain heterogeneity only when supported by study differences visible in the evidence.
5. Separate source findings from the analyst's inference.
6. Avoid vote counting based only on the number of papers.
7. Avoid causal language for correlational evidence.
8. Preserve uncertainty when only abstracts or sparse snippets are available.

## Compact answer template

Use for focused questions:

1. **Answer:** State the evidence-backed conclusion directly.
2. **Key evidence:** Synthesize the most informative supporting and conflicting papers.
3. **Limits:** State important evidence or coverage limitations.
4. **Sources:** List verified papers with stable links.

## Full review template

Use only sections that add value:

1. **Conclusion** — Direct answer and confidence.
2. **Scope and method** — Search date, queries/subquestions, filters, and evidence coverage.
3. **Evidence synthesis** — Findings organized thematically or methodologically.
4. **Comparison** — Compact table for repeated fields such as population, method, dataset, outcome, and limitation.
5. **Conflicts and gaps** — Contradictory findings, missing evidence, and unresolved questions.
6. **Implications** — Clearly labeled interpretations or next research steps.
7. **Verified references** — Title, authors, year, and DOI/arXiv/Semantic Scholar link.

## Citation form

Use readable inline citations such as `[FirstAuthor et al., 2024](stable-link)`. If multiple papers support one statement, cite each source. Prefer DOI or arXiv links; otherwise use the Semantic Scholar paper URL.

Do not cite a search-results page. Do not fabricate BibTeX. Generate BibTeX only from verified metadata and flag missing fields.

## Final verification checklist

- Every material empirical claim has Tier A or B support.
- Every citation resolves to the intended paper.
- Titles, authors, years, and identifiers match the retrieved canonical record.
- Nearby prose does not overstate the cited evidence.
- Conflicting evidence is represented fairly.
- Recommendations are labeled as interpretations.
- Search scope and non-exhaustiveness are clear.
- No citation appears only because it is highly cited or recommended by similarity.
