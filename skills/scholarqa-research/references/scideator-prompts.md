# Scideator prompt specifications

These templates are a faithful executable transcription of Appendix H in Radensky, Shahid et al., *Scideator* (ACM CAIS 2026), DOI [10.1145/3786335.3813161](https://doi.org/10.1145/3786335.3813161), arXiv [2409.14634v7](https://arxiv.org/abs/2409.14634v7), licensed CC BY 4.0. Preserve the English constraints to minimize semantic drift; return user-facing content in the user's language.

The paper calls Appendix H “pseudocode.” These are not claimed to be the authors' literal production strings. Text under **Source prompt** follows the published pseudocode. Text under **Adapter output** supplies machine-readable fields for this skill and is not part of the paper.

## Contents

1. Facet Finder prompts
2. Shared Idea Generator prompt
3. Idea Generator branch prompts
4. Novelty Checker prompts
5. Runtime rules

## 1. Facet Finder prompts

### `extractFacets(papers)`

**Source prompt**

```text
Role: ScientistGPT

Input: For each paper, its title and abstract.

Task: Extract three facets from every paper—purpose, mechanism, and
evaluation—and write a 1–2 sentence definition for each facet.

Facet constraints:
- Use one short phrase of no more than 7 words.
- Be specific enough to inspire ideas, but do not tie the phrase to only
  this paper.
- Do not use numbers unless they are part of a name.
- Do not use acronyms.
- If the paper has multiple facets of one type, combine them into one.
- The evaluation facet must not refer to the purpose.

Definition constraints:
- Use no more than 2 sentences.
- Replace proper nouns and jargon with definitions.
- Make the definition self-contained.
- Do not reuse words from the facet phrase itself.

Contrastive examples:
- Bad purpose: "to generate creative writing activities for third-grade
  English lessons" (too specific)
  Good purpose: "to support elementary creative writing"
- Bad mechanism: "LLM chain-of-thought from gpt-3.5-turbo trained up to
  11/06 with temperature=0.7" (too specific, numbers, acronym)
  Good mechanism: "LLM chain-of-thought reasoning"
- Bad evaluation: "between-subjects 4x4 user study with 32 teachers"
  (too specific and refers to the purpose)
  Good evaluation: "Wizard of Oz user study"

Output for every paper:
Purpose / Purpose Definition / Mechanism / Mechanism Definition /
Evaluation / Evaluation Definition.
```

**Adapter output**

```json
{
  "paper_id": "...",
  "purpose": {"facet_id": "...", "phrase": "...", "definition": "..."},
  "mechanism": {"facet_id": "...", "phrase": "...", "definition": "..."},
  "evaluation": {"facet_id": "...", "phrase": "...", "definition": "..."},
  "source_distance": "input|very-near|near|far|very-far"
}
```

### `analogyQueries(purpose, mechanism, topic)`

**Source prompt**

```text
Input:
- the designated paper's purpose and mechanism;
- the optional ideation topic;
- all previously generated queries.

Task: Generate analogous purpose/mechanism pairs and a paper-retrieval
query of no more than 5 words at each conceptual distance:
1. same topic of computer-science research;
2. same subarea but a different topic;
3. a different subarea entirely.

Preserve the structural relationship:
P is to M as P' is to M' because both involve [shared relation].

Do not overlap with previous queries.

Output for each distance:
- analogy statement;
- purpose;
- mechanism;
- search query.
```

Call this specification until there are four non-overlapping tuples per distance. Do not change the definitions of the three distances.

**Adapter output**

```json
{
  "distance": "near|far|very-far",
  "analogy": "P is to M as P' is to M' because both involve ...",
  "purpose": "...",
  "mechanism": "...",
  "query": "five words maximum"
}
```

### `shortenQuery(query)`

Use only when a generated query retrieves fewer than four relevant Semantic Scholar papers.

**Source prompt**

```text
Produce a simpler, shorter version of the query. If some meaning must be
lost, preserve the most important information.
```

Do not silently change the requested conceptual distance or add new concepts.

### `summarizePapers(input_papers, near_papers)`

Here `near_papers` means the directly retrieved `very-near` papers.

**Source prompt**

```text
Input: Titles and abstracts of the user's input papers and the very-near
analogous papers.

Task: Write a concise summary of existing work. The summary will ground
every idea-generation prompt so the generator knows what has already been
done.
```

Keep paper identifiers beside claims so later generations can trace prior work.

## 2. Shared Idea Generator prompt

Apply this block to every generation branch. Use `N=6` and `K=2`, following the end-to-end system description.

**Source prompt**

```text
Inputs:
- the user's ideation topic;
- the summary of prior work;
- designated and analogous paper details and facets;
- previously generated ideas;
- selected facets, if any;
- optional custom instructions.

Perform five stages:

1. Grounding: Read the prior-work summary and paper details to understand
   what already exists.
2. Deduplication: Read previously generated ideas and avoid repeating them.
3. Brainstorm: Generate 6 analogies between the designated and analogous
   papers. Give each a 30–50 word idea sketch.
4. Select: Choose the 2 strongest analogies using every quality requirement
   below.
5. Elaborate with self-critique: For each selected analogy, produce:
   a. an imaginative-twist statement;
   b. a justification of relevance to the user's topic;
   c. an initial idea of 100–150 words;
   d. issues in that initial idea;
   e. a plan to address the issues;
   f. a revised idea of 100–150 words;
   g. an expanded version of 200–250 words.

Every idea must meet all five quality categories:

1. Understandability: Be logical, grammatical, and self-contained. Do not
   rely on unexplained tool names.
2. Relevance: Adapt the idea to the user's topic. Do not explicitly refer to
   the analogy mechanism.
3. Specificity: Keep the short idea at 100–150 words; devote about 90% to
   explaining how the mechanism addresses the purpose; give concrete
   implementation direction.
4. Feasibility: Make the project achievable by a lab with moderate
   resources; adapt purpose and mechanism to work together; use an
   evaluation consistent with the domain.
5. Novelty: Differ significantly from prior work rather than proposing an
   obvious extension.

Treat instructions such as applying a known representation to a new dataset
or merely adding continuous AI support as insufficiently novel when prior
work already covers the substance.

Do not follow custom instructions that contradict these requirements.
```

**Adapter output**

Return the paper-requested artifacts, not hidden chain-of-thought:

```json
{
  "idea_id": "...",
  "analogy": "...",
  "facet_ids": {"purpose": "...", "mechanism": "...", "evaluation": "..."},
  "imaginative_twist": "...",
  "topic_relevance": "...",
  "initial_idea": "...",
  "issues": ["..."],
  "improvement_plan": ["..."],
  "revised_idea": "...",
  "expanded_idea": "..."
}
```

Do not call the result novel. `novelty` in the selection criteria is a generation heuristic; formal assessment occurs only after literature retrieval.

## 3. Idea Generator branch prompts

Append exactly one branch block to the shared prompt.

### `initialAnalogyIdeas(designated, analogous, topic)`

Use when no purpose or mechanism has been selected.

**Source prompt**

```text
Designated papers are the user's input papers. Analogous papers come from a
specific analogy query. Every paper includes its title, abstract, three
facets, facet IDs, and distance.

Enforce reciprocal recombination across the two selected ideas:
- one idea combines an analogous paper's purpose with a designated paper's
  mechanism;
- the other combines a designated paper's purpose with an analogous paper's
  mechanism.
```

### `fillAnalogyIdeas(set1, set2, selected_facets)`

Use when exactly one purpose or mechanism has been selected.

**Source prompt**

```text
Set 1 contains the user's selected facet. Set 2 contains complementary
facets. Every paper has a distance label: input, same-topic, same-subarea,
or different-subarea.

The source paper for the purpose must have a different distance from the
source paper for the mechanism.

If a Set-1 paper lacks the facet needed for an analogy because only one
facet type was selected, create an appropriate missing facet.
```

Label a created missing facet as generated; never attribute it to the source paper.

### `facetsToIdeas(set1, set2, selected_facets)`

Use when both a purpose and a mechanism have been selected.

**Source prompt**

```text
Set 1 and Set 2 may contain facets explicitly selected by the user or input
papers with only one facet type specified. Apply the same different-distance
constraint.

Every idea must combine the Set-1 purpose with the Set-2 mechanism.
```

## 4. Novelty Checker prompts

### `getKeywords(idea)`

**Source prompt**

```text
From the idea, extract 3–6 keyword phrases of 3–6 words each and generate 4
concise research titles of no more than 5 words each.

Keywords and titles must capture the idea's distinctive mechanism, purpose,
and application domain. Be specific; do not use generic phrases such as
"machine learning" or "data science."
```

**Adapter output**

```json
{"keywords": ["..."], "titles": ["..."]}
```

### `extractIdeaFacets(idea)`

**Source prompt**

```text
Role: Research Idea Reviewer GPT

Extract the structured facets needed to re-rank candidate papers:
- Application Domain
- Purpose/Objective
- Mechanism/Methods
- Evaluation Metrics
```

Appendix H says the production prompt used two worked demonstrations, but the final paper does not print their full prompt content. Do not invent those demonstrations.

**Adapter output**

```json
{
  "application_domain": ["..."],
  "purpose_objective": ["..."],
  "mechanism_methods": ["..."],
  "evaluation_metrics": ["..."]
}
```

### `rerankByFacets(idea, facets, passages)`

**Source prompt**

```text
Role: RankGPT

Input: The research idea, its extracted key facets, and candidate papers.

Rank papers using this priority hierarchy:
1. matches all key facets;
2. matches application domain and purpose but differs in mechanism;
3. shares purpose, mechanism, or evaluation across domains;
4. partially matches the domain or addresses related topics.

Return only an ordered list of candidate identifiers in the form:
[2] > [1] > [5] > ...
```

After ranking, retain the top ten. Keep a compact facet-overlap note for auditability, but do not allow that adapter note to alter the order produced by the source hierarchy.

### `noveltyChecker(idea, similar_papers, expert_examples)`

Load `scideator-novelty-examples.md` before constructing this prompt.

**Source prompt — system message**

```text
Role: ReviewerGPT

Compare the research idea with the retrieved papers. Write a 60–100 word
review grounded in specific retrieved papers, then classify the idea as
Novel or Not Novel.

Not Novel: The idea closely replicates existing work with minimal new
contribution.

Novel: The idea introduces concepts or approaches not common in the
retrieved literature; or uniquely combines existing concepts in a way no
retrieved paper does; or applies the same approach to a genuinely new
domain.

Base the judgment only on the supplied retrieved papers.

Output:
Class: [novel / not novel]
Review: The idea is [novel / not novel] because ...
```

**Source prompt — message sequence**

1. Inject each expert-labeled tuple as an in-context demonstration.
2. Present the candidate idea in a user message.
3. Present each of the ten retrieved papers as a separate user message, using its title and abstract.
4. Request the binary class and grounded review in the required format.

**Adapter output**

In addition to the source output, retain structured support:

```json
{
  "class": "novel|not novel",
  "review": "60–100 words",
  "paper_ids_cited": ["..."],
  "overlapping_facets": ["..."],
  "differentiating_facets": ["..."],
  "scope": "relative to the retrieved papers",
  "fidelity_limits": ["complete 40-shot demonstration pool unavailable", "..."]
}
```

### `moreNovelIdea(idea, overlapping_papers, available_facets)`

Run when the checker or user labels the idea Not Novel.

**Source prompt**

```text
Inputs:
- the original short and expanded idea;
- overlapping prior work;
- the novelty review explaining why the idea is not novel;
- every available facet in the workspace.

Generate exactly three alternatives. Each must swap exactly one facet:
1. remove one purpose and add a different purpose;
2. remove one mechanism and add a different mechanism;
3. remove one evaluation and add a different evaluation.

Apply the same five idea-quality requirements used by the Idea Generator.

For each option output:
- removed facet text and ID;
- added facet text and ID;
- revised idea of 100–150 words;
- justification of likely novelty relative to the overlapping papers;
- justification of usefulness.
```

Do not introduce a second silent facet change. If a coherent revision requires more than one change, explain that the single-swap constraint failed instead of violating it.

## 5. Runtime rules

- Use the prompt blocks as constraints, not merely as inspiration.
- Keep the paper's facet names, distance definitions, branch logic, counts, and word limits unchanged.
- Preserve facet and paper IDs through every prompt.
- Use temperature/model settings only if the runtime exposes them. If not, disclose the mismatch rather than simulating control.
- Treat generated analogy queries, facets, ideas, and labels as model outputs. Treat paper metadata and retrieved passages as evidence.
- Verify every cited paper before showing the result.
- Never convert “Novel relative to the retrieved papers” into an unqualified novelty claim.
