---
name: scholarqa-research
description: Perform evidence-first scholarly research, multi-paper synthesis, and Scideator-style facet-based research ideation with the ScholarQA CLI or Semantic Scholar MCP tools. Use when Codex must answer a research question from academic literature, produce a cited literature review, compare findings, verify scholarly claims, generate research ideas from seed papers by recombining purpose/mechanism/evaluation facets, assess an idea against related literature, or revise a potentially unoriginal idea through controlled facet swaps. Do not use for general web research or a simple single-paper metadata lookup that needs only one direct tool call.
---

# ScholarQA Research

## Goal

Produce a concise, evidence-grounded answer before writing a broad narrative. Retrieve scholarly evidence with Semantic Scholar, map each material claim to verified papers, expose disagreements and evidence limits, and never invent citations.

For literature questions, treat this as a Semantic Scholar MCP/CLI adaptation of the ScholarQA workflow, not as a wrapper around or behavioral replica of `ai2-scholarqa-lib`. For research ideation, preserve Scideator's shared faceted representation and human-directed loop; do not reduce it to generic brainstorming.

## Provenance boundary

Read [references/provenance.md](references/provenance.md) before modifying or redistributing this skill, and whenever the user asks how its workflow was derived.

- Treat this skill as an independent Semantic Scholar MCP/CLI adaptation, not an official Ai2 Scholar QA release or an Allen Institute for AI product.
- Credit the Ai2 Scholar QA paper and official `allenai/ai2-scholarqa-lib` repository when describing the evidence-QA design. No upstream ScholarQA code is bundled or imported.
- Credit the Scideator paper for the facet-ideation workflow and published prompt pseudocode. Keep published specifications distinct from adapter decisions.
- Do not add these methodology citations mechanically to ordinary literature answers; cite the papers that support the user's requested claims. Include methodology citations when discussing, comparing, publishing, or redistributing the workflow itself.

## Select mode

- **Evidence QA:** Answer, review, compare, trace, or audit the literature. Follow the main workflow below.
- **Facet ideation:** Generate research directions from seed papers, explore analogies, or iteratively refine an idea. Read [references/scideator-workflow.md](references/scideator-workflow.md), [references/scideator-prompts.md](references/scideator-prompts.md), and [references/retrieval.md](references/retrieval.md) completely before acting.
- **Novelty check:** Assess a supplied idea against retrieved literature. Read the novelty sections of both Scideator references, load [references/scideator-novelty-examples.md](references/scideator-novelty-examples.md), and follow [references/retrieval.md](references/retrieval.md). Judge only relative to the retrieved evidence; never certify global novelty.
- **Hybrid:** Use Evidence QA to establish the literature first, then enter Facet ideation. Keep evidence claims and generated proposals visibly separate.

The Scideator references distinguish the final paper's published specification from MCP/runtime adaptations. Never present an adapter choice as part of the original system.

## Choose a transport

This skill is independently usable with either runtime below. Do not require the endpoint-routing skill merely to run an evidence-QA workflow.

- **ScholarQA CLI:** Prefer `scholarqa-cli collect` for repeatable multi-query evidence bundles and `scholarqa-cli verify` for final citation records. The CLI collects and verifies evidence; it deliberately does not generate answer prose. Apply this skill's ledger and synthesis rules to its JSON output.
- **Semantic Scholar MCP:** Call snippet search, paper search, graph expansion, and batch verification tools directly when MCP is connected.
- **Optional low-level composition:** Use the separate `$semantic-scholar-cli` skill with `semanticscholar-cli` when exact endpoint selection, citation traversal, recommendations, datasets, or a shell-only fallback is needed. It complements this skill but is not a prerequisite.

Do not run duplicate MCP and CLI searches by default. Select one primary transport, then switch or augment only to fill a documented evidence gap.

## Select depth

Choose the lightest depth that satisfies the request:

- **Focused answer:** Use 1-2 search formulations and usually synthesize 5-10 strong papers.
- **Deep review:** Decompose the question into 3-6 subquestions and usually synthesize 10-30 papers across methods, dates, and viewpoints.
- **Broad discovery:** Search and organize the field, but do not claim systematic-review coverage.
- **Systematic search:** Require explicit inclusion criteria, databases, dates, and screening rules. Record pagination and exclusions. State when Semantic Scholar alone is insufficient.

Read [references/retrieval.md](references/retrieval.md) before deep, broad, systematic, citation-network, or rate-limit-sensitive searches. Read [references/reporting.md](references/reporting.md) before producing a substantial review, comparison, or claim audit.

## Workflow

### 1. Frame the question

Translate the request into a precise research question. Infer harmless defaults, but ask for clarification when population, date range, field, outcome, or desired evidence type would materially change the result.

Write an internal search plan containing:

- the main question and 2-6 answerable subquestions;
- synonyms, abbreviations, and neighboring terminology;
- requested filters and exclusions;
- the appropriate search depth.

### 2. Retrieve complementary evidence

Use Semantic Scholar as the primary academic source through one selected transport.

With the ScholarQA CLI, run `scholarqa-cli collect QUESTION` with 1-6 distinct `--query` formulations and relevant filters. Preserve the returned bundle, inspect `operation_errors`, and use `candidate_paper_ids` only as a screening set. With MCP, execute the equivalent sequence directly:

1. Search full-text snippets for passages that directly address each subquestion.
2. Run relevance-ranked paper searches to recover abstracts and papers missed by snippet search.
3. Resolve ambiguous titles and identifiers before using a paper.
4. Expand only high-value seeds through references, citations, or recommendations.
5. Use bulk search and pagination only when breadth or reproducibility requires them.

Do not treat citation count as evidence of correctness. Do not substitute generic web results for scholarly retrieval. Use an open-access publisher or arXiv page only to inspect full text after identifying the paper, and label the evidence source accurately.

### 3. Normalize and select papers

Deduplicate by Semantic Scholar paper ID, DOI, arXiv ID, and normalized title. Prefer the canonical record. Rank candidates using:

1. direct relevance to the question;
2. strength and specificity of retrieved evidence;
3. methodological fit and study quality visible in the available record;
4. coverage of competing findings and approaches;
5. recency when the question is time-sensitive.

Retain foundational work where it defines the method or claim. Avoid filling the final answer with many near-duplicate papers.

### 4. Build evidence before prose

Create an internal claim ledger for every conclusion that may appear in the answer. Record the claim, paper ID, supporting passage or abstract text, evidence level, support/contradiction relationship, and uncertainty. Follow the ledger format in [references/reporting.md](references/reporting.md).

Distinguish:

- **Tier A:** a retrieved full-text passage directly supports or contradicts the claim;
- **Tier B:** the abstract directly supports or contradicts the claim;
- **Tier C:** metadata establishes publication identity or context only;
- **Tier D:** a relationship inferred from titles, graph edges, or recommendations, which cannot support a substantive claim alone.

A snippet result is not automatically Tier A. Assign Tier A only when its source is identifiable as full text; if provenance is ambiguous, use Tier B only when the same support is present in the abstract, otherwise do not use it as substantive evidence.

If the available text does not support a claim, omit or qualify it. Preserve meaningful disagreement instead of forcing consensus.

### 5. Synthesize around the question

Lead with the direct answer. Organize evidence by findings, methods, or competing explanations rather than listing papers one by one. Explain why studies disagree when the evidence permits it, such as different datasets, populations, measures, baselines, or time periods.

Keep recommendations separate from reported findings. Mark recommendations as interpretations derived from the evidence.

### 6. Verify citations

Before finalizing, batch-fetch the records for every cited paper and verify title, first author or author list, year, and stable identifier. Use `scholarqa-cli verify PAPER_ID...` (or `--ids-file`) with the CLI transport, or `batch_get_semantic_scholar_papers` with MCP. With the CLI, inspect `unresolved_ids` and each item's `resolved` value; remove unresolved citations.

Bibliographic verification does not prove that a paper supports the nearby claim. Recheck that relationship against the claim ledger, and remove a citation that does not support the prose even when its metadata resolves correctly.

With MCP, check both error channels: tool-level errors and an `error` field embedded in an otherwise successful result. With the CLI, inspect the process status plus `operation_errors` or a top-level `error`. Retry rate-limited requests conservatively and reduce concurrency.

### 7. Report transparently

Use the compact or full template from [references/reporting.md](references/reporting.md). Include stable DOI, arXiv, or Semantic Scholar links. State the search date, scope, and important coverage limits for deep reviews.

Never describe a search as exhaustive or systematic unless the executed protocol justifies that wording.

## Failure handling

- If Semantic Scholar returns too little evidence, broaden terminology once, inspect citation neighbors, and report the remaining gap.
- If snippet search is unavailable, fall back to paper abstracts and explicitly label the result as abstract-level synthesis.
- If metadata conflict across records, prefer DOI/arXiv-resolved canonical records and disclose unresolved conflicts.
- If the selected Semantic Scholar transport is unavailable, try the other installed transport. If neither MCP nor `scholarqa-cli` is available, explain that the workflow cannot be completed faithfully and ask before switching to a generic web-only approach.
