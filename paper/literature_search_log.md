# Literature Search Log: Novelty Verification

**Date Conducted:** October 12, 2026  
**Target Statement (Section I & II):**  
> *"To the best of our knowledge, no prior study crosses chunking strategy with context headers for requirement-to-code evidence retrieval with human relevance labels."*

---

## 1. Search Scope and Venues
- **Databases Queried:** arXiv (cs.SE, cs.IR, cs.CL), DBLP Computer Science Bibliography, Google Scholar, ACL Anthology, IEEE Xplore, ACM Digital Library.
- **Search Period:** 2019 – October 2026.

---

## 2. Systematic Search Queries & Results Summary

| Query ID | Search String | Venues Searched | Key Relevant Papers Identified | Crosses Chunking x Context Headers for Requirement-to-Code? |
|:---|:---|:---|:---|:---:|
| **Q1** | `"context header" OR "contextualized chunk" "code retrieval" OR "code RAG"` | arXiv, Google Scholar, Web | Anthropic Contextual Retrieval (2024); blogs/industry pipelines adding file/class headers; HiChunk (2024); HRR (2024). | **No** (industry practices or text RAG; no factorial crossing of AST vs. Line with headers for code requirements). |
| **Q2** | `"AST chunking" "line chunking" OR "sliding window" "retrieval" "requirement" OR "traceability"` | arXiv, DBLP, Google Scholar | cAST (Zhang et al., 2025); Wu et al. (2026); Galimzyanov et al. (2025). | **No** (these evaluate chunking for code completion or RepoEval/SWE-bench without isolating prepended headers, or study general code RAG without human requirement-evidence ground truth). |
| **Q3** | `site:arxiv.org OR site:dblp.org "chunking" "context header" OR "hierarchical header" "retrieval" "requirement"` | arXiv, DBLP | HiChunk (arXiv 2024); MultiDocFusion (arXiv 2024); HRR (Hierarchical Re-ranker Retriever). | **No** (focuses on natural language documents/policy text, not multi-file source code repositories with AST extraction). |
| **Q4** | `"context header chunk code retrieval"` | Google Scholar, arXiv | RepoCoder (Zhang et al., 2023); RepoBench (Liu et al., 2024); CrossCodeEval (Ding et al., 2023). | **No** (iterative retrieval or prompt enrichment for completion, not prepended hierarchical headers evaluated on human-labeled requirements). |
| **Q5** | `"requirement to code retrieval LLM traceability chunking"` | Google Scholar, DBLP | Antoniol et al. (2002); Triad (Gao et al., 2024); Kuang et al. (2023). | **No** (traceability recovery between issues/PRs/commits and code, without factorial comparison of AST vs. line chunking under header conditions). |

---

## 3. Findings & Scientific Synthesis

1. **AST vs. Line Chunking in Code Intelligence:**  
   - cAST (Zhang et al., 2025) proposed recursive AST splitting and reported gains on RepoEval and SWE-bench.
   - Wu et al. (2026) and Galimzyanov et al. (2025) showed that line-based sliding windows match or outperform structure-aware splitting for code completion.
   - *However*, none of these papers tested whether prepending context headers (file path, class, method signature) alters the relative ranking of AST and line chunking.

2. **Context Headers in Retrieval:**  
   - Industry pipelines (e.g., Anthropic Contextual Retrieval, 2024) and recent text RAG frameworks (HiChunk, HRR) recognize that isolated chunks lose namespace context and recommend adding hierarchical metadata.
   - *However*, no prior academic study has evaluated this systematically on source code in a $2 \times 2$ factorial experiment crossing chunking strategies with header presence/absence.

3. **Requirement Evidence Retrieval with Human Labels:**  
   - Existing software engineering traceability benchmarks (e.g., Triad, Kuang et al.) focus on issue-to-commit or requirement-to-file tracing, rather than chunk-level evidence retrieval scored by independent human annotators on a 3-point relevance scale.

---

## 4. Conclusion & Audit Verification

- **Verdict:** **Confirmed Novel.** No prior study was found that crosses chunking strategy (AST vs. line) with context headers in a factorial design for requirement-to-code evidence retrieval with human relevance labels.
- **Action:** Retain the novelty statement in Section I and Section II without dilution.
- **Audit Date:** October 12, 2026.
