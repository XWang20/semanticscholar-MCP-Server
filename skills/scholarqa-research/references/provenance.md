# Provenance and attribution

Use this reference when describing, modifying, publishing, or redistributing the skill. The skill is an independent adaptation that combines two attributed research workflows with the Semantic Scholar operations exposed by this repository.

## Ai2 Scholar QA

The evidence-QA mode is adapted conceptually from:

- Amanpreet Singh, Joseph Chee Chang, Dany Haddad, Aakanksha Naik, Jena D. Hwang, Rodney Kinney, Daniel S. Weld, Doug Downey, and Sergey Feldman. **Ai2 Scholar QA: Organized Literature Synthesis with Attribution.** ACL 2025 System Demonstrations, pages 513–523. [DOI 10.18653/v1/2025.acl-demo.49](https://doi.org/10.18653/v1/2025.acl-demo.49); [ACL Anthology](https://aclanthology.org/2025.acl-demo.49/); [arXiv:2504.10861](https://arxiv.org/abs/2504.10861).
- Official implementation: [allenai/ai2-scholarqa-lib](https://github.com/allenai/ai2-scholarqa-lib), licensed under Apache-2.0. Provenance was reviewed against [commit `a962328`](https://github.com/allenai/ai2-scholarqa-lib/tree/a96232870bdb0bd763f0131320e8377c6deb575e).

The source system retrieves scientific passages and abstracts, reranks and aggregates evidence by paper, extracts supporting quotations, plans an organized answer, and synthesizes attributed sections. This skill preserves the high-level evidence-first ordering while replacing the source runtime with explicit Semantic Scholar MCP operations, a claim ledger, bounded evidence tiers, and final batch citation verification.

No source code, Python package, model configuration, web application, or runtime dependency from `ai2-scholarqa-lib` is bundled here. Do not claim behavioral equivalence, benchmark equivalence, affiliation, or endorsement. The ACL paper is available under CC BY 4.0; the repository's Apache-2.0 license continues to govern its code.

## Scideator

The facet-ideation and retrieval-bounded novelty modes adapt:

- Marissa Radensky, Simra Shahid, Raymond Fok, Pao Siangliulue, Tom Hope, and Daniel S. Weld. **Scideator: Human-LLM Compound System for Scientific Ideation through Facet Recombination and Novelty Evaluation.** ACM CAIS 2026. [DOI 10.1145/3786335.3813161](https://doi.org/10.1145/3786335.3813161); [arXiv:2409.14634v7](https://arxiv.org/abs/2409.14634v7).

The final paper declares CC BY 4.0. The files `scideator-workflow.md`, `scideator-prompts.md`, and `scideator-novelty-examples.md` identify published material, adapter additions, fidelity gaps, and changed runtime assumptions. Preserve those notices and indicate that adaptations were made. The paper publishes prompt pseudocode rather than verified literal production prompts; do not represent the executable transcription as the authors' original strings.

## Citation practice

- Cite the Ai2 Scholar QA and Scideator sources when explaining or publishing this skill's methodology.
- Cite retrieved domain papers—not these methodology sources—next to substantive answers to a user's research question.
- Preserve stable DOI, arXiv, ACL Anthology, and repository links.
- Keep the project MIT license separate from third-party paper and repository licenses; the project license does not relicense upstream material.
