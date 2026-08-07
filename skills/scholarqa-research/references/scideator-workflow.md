# Scideator workflow

Use this reference for facet-based scientific ideation or idea-novelty checking. Read `scideator-prompts.md` as well. For novelty classification, also read `scideator-novelty-examples.md`.

## Contents

1. Provenance and fidelity boundary
2. Shared representation
3. Module 1: Analogous Paper Facet Finder
4. Module 2: Faceted Idea Generator
5. Module 3: Idea Novelty Checker
6. Human-directed iteration
7. Semantic Scholar MCP binding
8. Fidelity checklist

## 1. Provenance and fidelity boundary

Primary source: Marissa Radensky, Simra Shahid, Raymond Fok, Pao Siangliulue, Tom Hope, and Daniel S. Weld, *Scideator: Human-LLM Compound System for Scientific Ideation through Facet Recombination and Novelty Evaluation*, ACM CAIS 2026, DOI [10.1145/3786335.3813161](https://doi.org/10.1145/3786335.3813161), arXiv [2409.14634v7](https://arxiv.org/abs/2409.14634v7).

The final source declares CC BY 4.0. Attribute reused prompt specifications to the authors and paper. This reference operationalizes the final DOI/arXiv-v7 paper, especially Sections 2–3 and Appendices F and H.

Keep these boundaries explicit:

- The final paper publishes **prompt pseudocode**, not the literal production prompt strings.
- The paper reports 67 consensus-labeled novelty examples and uses 20 examples per class, but publishes only one Novel and one Not Novel demonstration. Do not claim the two published examples reproduce the original 40-shot classifier.
- The paper states that code will be released after acceptance, but no verified official repository is bundled here.
- Lines marked **Published** describe the paper. Lines marked **Adapter** are necessary to run the workflow through the available MCP/runtime and are not claims about Scideator.
- The original model configuration was `gpt-4o-2024-08-06` at temperature 0 unless noted, temperature 0.75 for idea generation, GPT-4o for novelty re-ranking, and o3-mini for novelty assessment. Record these settings as provenance; do not claim equivalence when the runtime cannot select them.
- Appendix H permits an introduction when available in one extraction signature, while Appendix F says the implementation uses paper titles and abstracts. Follow Appendix F by default: use title and abstract only.

## 2. Shared representation

**Published.** Maintain the same three paper/idea facets through retrieval, generation, novelty assessment, and revision:

- `purpose`: the problem being addressed;
- `mechanism`: the proposed solution;
- `evaluation`: the method for determining whether the solution works.

Represent every facet as:

```text
facet_id
facet_type: purpose | mechanism | evaluation
phrase: at most 7 words
definition: 1–2 self-contained sentences
source_paper_id
source_distance: input | very-near | near | far | very-far | user
```

Preserve provenance. Never display a generated facet as paper-authored language. Link each extracted facet to its source paper.

Use these conceptual distances exactly:

| Label | Paper definition |
|---|---|
| `very-near` | Most similar papers returned directly by Semantic Scholar similarity/recommendation. |
| `near` | Same research topic; similar problem with a different approach. |
| `far` | Same subarea, different topic; shares a more abstract structural parallel. |
| `very-far` | Different subarea; connected only by a high-level analogy. |

## 3. Module 1: Analogous Paper Facet Finder

### Inputs

- one or more resolved seed papers;
- optional ideation topic;
- optional previous analogy queries to avoid repeating directions.

### Published procedure

1. Resolve the seed papers and extract one purpose, mechanism, and evaluation from each.
2. Determine the seed set's overarching purpose–mechanism pair.
3. Retrieve four `very-near` papers through Semantic Scholar paper similarity.
4. Generate four analogous purpose–mechanism/query tuples at each of three distances: `near`, `far`, and `very-far`—12 tuples total.
5. Preserve the structural relationship in every analogy: the source purpose is to its mechanism as the analogous purpose is to its mechanism, with an explicit shared relation.
6. Keep each generated retrieval query to at most five words.
7. Search Semantic Scholar for each query. When fewer than four relevant papers are found, iteratively shorten the query while preserving its most important information.
8. Use the first relevant result as that tuple's representative paper and retain the next three results as grounding context.
9. Extract the three facets from the 12 representative papers and four `very-near` papers, producing 16 analogous facet records across four distances.
10. Summarize the seed and `very-near` papers as prior work. Inject this summary into every idea-generation call so generated ideas differentiate themselves from work closest to the seeds.

### Adapter constraints

- Resolve DOI, arXiv, title, or S2 identifiers before extracting facets.
- Exclude a seed paper from its own recommendations and deduplicate all results by S2 ID, DOI/arXiv ID, then normalized title.
- Treat a result as relevant only when its title or abstract supports the intended purpose–mechanism pair. A search hit is not automatically a valid analogy.
- Cap query-shortening retries at three. If a query still yields fewer than four relevant papers, retain what is available and mark the distance cell incomplete rather than fabricating papers.
- If the recommendation endpoint cannot combine multiple seeds, retrieve per seed, merge, deduplicate, and retain the four most relevant results.

## 4. Module 2: Faceted Idea Generator

### Published common procedure

For every generation call:

1. **Ground:** Read the prior-work summary and paper details.
2. **Deduplicate:** Read previously generated ideas.
3. **Brainstorm:** Generate six candidate analogies, each with a 30–50 word idea sketch.
4. **Select:** Select the two strongest candidates against the five quality categories below.
5. **Elaborate and self-critique:** For each selected candidate, produce an imaginative twist, topic relevance, a 100–150 word initial idea, identified issues, an improvement plan, a 100–150 word revised idea, and a 200–250 word expanded idea.

Apply all five quality categories:

1. `understandability`: logical, grammatical, self-contained;
2. `relevance`: adapted to the user's topic without referring to the analogy mechanism as such;
3. `specificity`: concrete implementation direction, with about 90% of the short idea explaining how the mechanism addresses the purpose;
4. `feasibility`: achievable by a moderately resourced lab, with compatible purpose, mechanism, and evaluation;
5. `novelty`: materially different from prior work, not an obvious extension.

User instructions may specialize a direction but must not override the quality requirements.

### Branch by selected facets

**No purpose or mechanism selected.** Combine seed/very-near papers with near, far, and very-far papers. Of the two selected ideas, one must use the analogous paper's purpose with the designated paper's mechanism, and the other the designated purpose with the analogous mechanism.

**Exactly one of purpose or mechanism selected.** Put papers carrying the selected facet in Set 1 and complementary papers in Set 2. The purpose source and mechanism source must have different distance labels. If a Set-1 record contains only the selected facet type, create only the missing facet needed for the analogy and label it generated.

**Both purpose and mechanism selected.** Combine the selected Set-1 purpose with the selected Set-2 mechanism. Keep the different-distance constraint.

### Adapter constraints

- Preserve the paper's requested artifacts, but do not expose private hidden reasoning. Return concise `issues` and `improvement_plan` fields rather than unrestricted chain-of-thought.
- Assign IDs to every generated idea and record the exact facet IDs used.
- Mark generated evaluations separately when the user selected only purpose and mechanism.
- Do not describe a candidate as novel before Module 3 retrieves literature for it.

## 5. Module 3: Idea Novelty Checker

Run the four stages in order. The result is a retrieval-bounded assessment, never proof of global novelty.

### Stage 1: retrieve candidate overlapping papers

**Published.** Build a broad union from:

- all seed and analogous papers already in the workspace;
- related papers for those papers through Semantic Scholar;
- paper searches for 3–6 specific keyword phrases extracted from the idea;
- paper searches for four generated research titles;
- Semantic Scholar snippet search using the full idea text.

Keywords are 3–6 words each. Titles are at most five words. They must capture the purpose, mechanism, application domain, and what differentiates the idea—not generic terms such as “machine learning.”

### Stage 2: select the most relevant papers

**Published.** Apply two-stage retrieve-then-rerank:

1. Compute SPECTER similarity between the idea and each candidate paper; retain the top `N=100`.
2. Use facet-grounded RankGPT to order those papers by:
   1. matches all key facets;
   2. matches application domain plus purpose but differs in mechanism;
   3. shares purpose, mechanism, or evaluation across domains;
   4. partially matches the domain or a related topic.
3. Send the top `k=10` papers to novelty assessment.

**Adapter.** The Semantic Scholar API can return paper embeddings but does not encode arbitrary idea text. Use the SPECTER stage only when a compatible local/query encoder is available. Otherwise omit it, facet-rerank a manageable deduplicated candidate set directly, and disclose `SPECTER prefilter omitted`. Never compare a non-SPECTER idea vector with SPECTER paper vectors.

### Stage 3: assess novelty

**Published.** Extract these idea facets before re-ranking and assessment:

- application domain;
- purpose/objective;
- mechanism/methods;
- evaluation metrics.

Present the idea, then each of the ten papers separately so the model attends to each paper. Use expert examples as demonstrations. Produce a 60–100 word evidence-grounded review and one binary label:

- `Not Novel`: closely replicates existing work with minimal contribution.
- `Novel`: introduces an uncommon concept/approach, uniquely combines concepts in a way absent from retrieved papers, or applies an approach to a genuinely new domain.

Base the label only on the retrieved set. Cite the specific papers and overlapping or differentiating facets. Let the user override or qualify the judgment.

**Adapter.** Load the two demonstrations in `scideator-novelty-examples.md`. State that the published system used 20 examples per class and that the complete pool is unavailable; this reproduction therefore has lower classifier fidelity.

### Stage 4: suggest more-novel alternatives

Run only when the idea is classified Not Novel by the checker or user. Generate three alternatives:

1. replace exactly one purpose;
2. replace exactly one mechanism;
3. replace exactly one evaluation.

For each option, identify removed and added facet IDs, give a revised 100–150 word idea, and justify both likely novelty and usefulness relative to the retrieved papers. Do not change more than one facet per option.

## 6. Human-directed iteration

Preserve the Scideator control loop:

```text
seed papers/topic
  -> analogous papers + traceable facets
  -> user selection or explicitly marked automatic selection
  -> facet-recombined ideas
  -> user chooses an idea
  -> retrieval-bounded novelty assessment
  -> one-facet alternatives when needed
  -> return to facet selection or generation
```

Whenever interaction permits, show the facet workspace before generation and let the user select. If the user requests an automatic run, use the no-selection branch and identify which facets the system selected. The user—not the model—decides which research direction to pursue and how much weight to give novelty signals.

**Adapter checkpoint rule.** Materialize and retain each module's required artifact before starting the next module. In particular, finish the selected ideas' initial/revised/expanded records before novelty retrieval, and finish all three one-facet alternatives after a Not Novel result. If runtime or tool limits force an early stop, stop at a module boundary and report the pending module; do not silently omit required artifacts because earlier retrieval was expensive.

Recommended output sections:

1. `Facet workspace` — facets grouped by distance with source-paper links.
2. `Candidate ideas` — facet IDs, short revised idea, expanded idea on request.
3. `Novelty check` — scope, retrieval routes, top papers, overlaps/deltas, binary label, confidence and limitations.
4. `One-facet revisions` — only for Not Novel ideas.
5. `Iteration choices` — select/add facets, choose another idea, or rerun retrieval.

## 7. Semantic Scholar MCP binding

| Scideator operation | MCP operation |
|---|---|
| Resolve seed identifier/title | `get_semantic_scholar_paper_details`, `match_semantic_scholar_paper`, or batch lookup |
| Four very-near papers | `recommend_semantic_scholar_papers_for_paper` or multi-seed `recommend_semantic_scholar_papers` |
| Near/far/very-far query grounding | `search_semantic_scholar_papers` with title and abstract fields |
| Related-paper expansion | recommendation endpoint; use citations/references only when they serve the stated overlap search |
| Keyword/title candidate retrieval | `search_semantic_scholar_papers` |
| Full-idea passage retrieval | `search_semantic_scholar_snippets` |
| Candidate metadata/embeddings | `batch_get_semantic_scholar_papers`; request `embedding` only when a compatible idea encoder exists |
| Final citation verification | `batch_get_semantic_scholar_papers` |

Use `references/retrieval.md` for pagination, error handling, metadata fields, and evidence tiers. Inspect both MCP tool errors and embedded `error` fields.

## 8. Fidelity checklist

Before presenting a Scideator-style result, verify:

- The same purpose/mechanism/evaluation representation persists through all modules.
- Every extracted facet has a source paper and distance; every invented facet is labeled generated or user-provided.
- Analogy retrieval covers very-near, near, far, and very-far directions unless a documented retrieval gap prevented it.
- Idea generation follows the correct selection branch and distance-mixing rule.
- Generated ideas are not called novel before literature retrieval.
- Novelty retrieval combines existing workspace papers, related papers, keyword/title search, and snippet search.
- The top papers are re-ranked by facet overlap, not citation count.
- Novelty is explicitly bounded to retrieved evidence.
- A Not Novel revision swaps exactly one facet per option.
- Any omitted SPECTER stage, unavailable 40-shot example pool, model mismatch, or other fidelity gap is disclosed.
