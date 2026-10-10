# Data & Artifact Provenance

**Target Study:** IEEE SANER 2027 ERA Track — *AST-Based Progressive Disclosure Chunking and 2×2 Factorial Retrieval for Candidate Skill Matching*  
**Governing Documents:** `analysis_plan.md` (Frozen at Phase 0) & `analysis_plan_addendum.md`  
**Review Mode:** Double-Anonymous Peer Review  

---

## 1. Overview and Scope

This document provides a transparent and rigorous audit trail for all data sources, curation steps, licensing classifications, human annotations, adjudication procedures, and benchmark artifacts included in this replication package.

To guarantee permanent, deterministic reproducibility and eliminate external network dependencies, this package provides the complete, pre-curated corpora, frozen queries, precomputed retrieval runs, and cryptographically verified ground truth files.

---

## 2. Source Repositories Universe

The candidate code universe is constructed from **40 public GitHub repositories** across two major software engineering ecosystems:
* **Java Backend Ecosystem (20 repositories):** Enterprise frameworks including Spring Boot, Spring Security, Hibernate/JPA, Kafka integrations, and microservice architectures.
* **TypeScript / React Frontend Ecosystem (20 repositories):** Modern web applications featuring functional React components, custom hooks, Redux/Context state management, Next.js, and TypeScript typing contracts.

All repositories are pinned to specific Git commit SHAs in [`dataset/manifest_repos.csv`](file:///c:/Users/win%2011/Desktop/ast-rag-replication-package/dataset/manifest_repos.csv) to guarantee temporal immutability:
* **Total files mined:** 189 source files (68 Java files, 121 TypeScript/React files).
* **Interval registry:** Pinned line-level intervals for all 189 files are stored in [`dataset/source_file_intervals.json`](file:///c:/Users/win%2011/Desktop/ast-rag-replication-package/dataset/source_file_intervals.json).

### Licensing Audit and Academic Fair Use

A granular audit of repository licenses in `manifest_repos.csv` reveals the following distribution:
* **MIT License (19 repositories):** Permissive open-source license.
* **Apache-2.0 License (4 repositories):** Permissive open-source license with patent grant.
* **AGPL-3.0 License (1 repository):** Strong copyleft license (`anoma/namada-interface`).
* **Not Specified / Public GitHub (16 repositories):** Publicly accessible repositories on GitHub without an explicit root license file.

**Academic Fair Use & Research Exemption:**  
Source code snippets mined from these 40 repositories are retained in `dataset/chunk_corpus.*` strictly for non-commercial academic research, empirical software analysis, and benchmark reproducibility under fair use doctrines (17 U.S. Code § 107 in the United States, research exceptions under Berne Convention member jurisdictions, and equivalent academic citation rights). Original copyrights remain entirely with the respective upstream authors and open-source contributors.

---

## 3. Query Universe (Job Descriptions)

The query set consists of **25 frozen industry Job Descriptions (JDs)** documented in [`dataset/queries_frozen.json`](file:///c:/Users/win%2011/Desktop/ast-rag-replication-package/dataset/queries_frozen.json) and raw text in `dataset/jd_raw/`:
* **15 Java Backend JDs (`JD_JAVA_01` – `JD_JAVA_15`):** Cover competencies such as Spring Boot MVC/WebFlux, Spring Security (JWT, OAuth2, RBAC), JPA/Hibernate transactions, distributed messaging (Kafka/RabbitMQ), and microservice resilience.
* **10 React/TypeScript JDs (`JD_REACT_01` – `JD_REACT_10`):** Cover competencies including React 18 functional components, custom hooks (`useAuth`, `useFetch`), asynchronous state management, TypeScript type narrowing, and UI performance optimization.
* **Seniority Stratification:** Balanced across Junior, Mid-Level, and Senior roles.

---

## 4. Chunk Corpora Architecture

The study evaluates two chunking paradigms across identical source files, comprising a unified corpus of **798 chunks** stored in [`dataset/chunk_corpus.parquet`](file:///c:/Users/win%2011/Desktop/ast-rag-replication-package/dataset/chunk_corpus.parquet) and [`dataset/chunk_corpus.jsonl`](file:///c:/Users/win%2011/Desktop/ast-rag-replication-package/dataset/chunk_corpus.jsonl):

### 4.1 AST-First Progressive Disclosure Corpus (364 Chunks)
* **Strategy:** Extracts semantic function/method/constructor nodes via Tree-sitter AST parsers with progressive context headers (`// Class: ...`, `// Method: ...`). Falls back to 50-LOC sliding windows when files lack parseable method structures.
* **Pure AST Chunks (N=234, 64.3%):**
  * Java: 133 chunks (**86.9%** of Java AST corpus).
  * React/TS: 101 chunks (**47.9%** of React AST corpus).
  * Syntax intact rate: 97.9% | Boundary cuts: 0 (100.0% intact) | Header retention: 100.0%.
* **Line-Fallback Chunks (N=130, 35.7%):**
  * Java: 20 fallback chunks (**13.1%** of Java AST corpus).
  * React/TS: 110 fallback chunks (**52.1%** of React AST corpus).
  * **Asymmetry:** React/TypeScript files account for **84.6%** (110/130) of all fallbacks in the benchmark due to JSX-heavy functional components, styled-components, and configuration modules.
  * Every fallback chunk is individually diagnosed and audited in [`dataset/fallback_audit.csv`](file:///c:/Users/win%2011/Desktop/ast-rag-replication-package/dataset/fallback_audit.csv).

### 4.2 Fixed-Window Line Baseline Corpus (434 Chunks)
* **Strategy:** Standard 50-LOC sliding window with 10-LOC overlap (step 40 LOC, minimum 6 LOC).
* **Characteristics:** 120 Java chunks, 314 React/TS chunks.
* **Syntax degradation:** Boundary cuts in 56.0% (243 cuts), syntax errors in 77.6% (337 chunks), 0% context header retention.

---

## 5. Candidate Pooling and Ground Truth Annotations

### 5.1 Pooling Strategy
To construct an unbiased ground truth without favoring any single retrieval paradigm:
* Candidates were retrieved across 12 distinct system configurations (3 retrieval tiers $\times$ 4 factorial chunking/header conditions).
* The top $k=3$ retrieved items per query per system were pooled.
* Duplicate snippets were deduplicated by exact `(jd_id, repo_name, file_path, start_line, end_line)` coordinates, producing **603 unique candidate pairs**.

### 5.2 Blinding & Annotation Protocol
* **Blinding (Rules R18, R19):** Human annotators reviewed candidate pairs via [`dataset/to_label.csv`](file:///c:/Users/win%2011/Desktop/ast-rag-replication-package/dataset/to_label.csv). The annotation sheet presented only neutral metadata and raw code content; all system identifiers, similarity scores, ranks, and chunking strategy tags were completely removed.
* **Independent Dual Annotation:**
  * **Annotator 1:** Evaluated all 603 pairs using the 3-point ordinal scale (`0`: Irrelevant, `1`: Partially Relevant, `2`: Highly Relevant) following the rubric criteria directly without free-form text notes (recorded in `dataset/ground_truth_annotator1.csv`).
  * **Annotator 2:** Evaluated all 603 pairs independently, assigning ordinal scores and contributing 45 diagnostic technical notes (recorded in `dataset/ground_truth_annotator2.csv`).
* **Inter-Annotator Agreement (Table 3.1 & Figure 3.1):**
  * Exact agreement: **79.77%** (481/603 pairs).
  * Minor 1-point disagreements: **18.57%** (112/603 pairs).
  * Severe 2-point disagreements: **1.66%** (10/603 pairs).
  * Quadratic Weighted Cohen's Kappa: $\kappa_w = \mathbf{0.7795}$ (*Substantial Agreement*, Landis & Koch 1977).
  * Gold 250 Subset Kappa: $\kappa_w = \mathbf{0.8808}$ (*Almost Perfect Agreement*).

### 5.3 Consensus Adjudication
* Disagreements occurred on **122 pairs** ($label_1 \neq label_2$).
* An adjudication session was conducted by a single **Lead Adjudicator**, resolving every disagreement based on the technical rubric.
* **70 distinct, concrete technical rationales** were recorded across the 122 items in [`dataset/disagreements_adjudication.csv`](file:///c:/Users/win%2011/Desktop/ast-rag-replication-package/dataset/disagreements_adjudication.csv).
* The adjudicated labels were combined with unanimous agreement pairs into [`dataset/ground_truth_final.csv`](file:///c:/Users/win%2011/Desktop/ast-rag-replication-package/dataset/ground_truth_final.csv).

### 5.4 Header Bias Neutral Control Status
* *Original Pre-Registration Proposal:* The study design proposed a 50-item neutral control experiment where a random subset of Gold items would be blinded and re-annotated without headers to detect potential halo bias.
* *Implementation Reality:* Due to human annotation resource constraints, this control step was **not executed**; all 603 candidate pairs were scored once through the dual-annotator + adjudication pipeline. This is reported transparently as a known experimental limitation.

### 5.5 Cryptographic Hash Locking
To prevent post-hoc label drift, ground truth files are locked on normalized newlines (Rule R17):
* `ground_truth_final.csv` (SHA-256): `70C01F773136F7D0352012B7D1F1DD9DB216708848C5A54E22A661DFD93DBB4D`
* Gold 250 subset (SHA-256): `222A9F55353597AF4B0DA9118E81F94602C5E78DCC9AF95C5490DC7D8EC45638`
*(Verified dynamically by `tests/test_gold_integrity.py`).*

---

## 6. Precomputed Retrieval Runs and Downstream Cache

* **Retrieval Runs (`dataset/retrieval_runs/*.json`):** 12 deterministic JSON ranking files containing Top-10 retrieved candidate lists across 3 retrieval tiers (BM25 with Rank-BM25, Dense with BAAI/bge-m3, and Re-ranking with BAAI/bge-reranker-base) $\times$ 4 factorial conditions.
* **RAGAs Evaluation Cache (`dataset/benchmark_results/ragas_evaluation_cache.json`):** Deterministic evaluation cache of LLM-as-a-Judge outputs on Top-3 retrieved code contexts, measuring Faithfulness ($1.000$ on evaluated sample), Answer Relevance ($0.996$ AST vs $1.000$ Line), and Citation Coverage ($79.3\%$ AST vs $79.2\%$ Line).

---

## 7. Reproduction Pipeline Boundaries

This replication package is architected to reproduce and verify all empirical findings, tables, figures, sensitivity analyses, and statistical hypothesis tests from the frozen curated artifacts:
* **Included:** Live Tree-sitter AST parsing, syntax morphology analysis, full 2×2 factorial retrieval evaluation, bootstrap confidence intervals, Wilcoxon signed-rank tests, Holm-Bonferroni corrections, RAGAs generation metric evaluation, subgroup sensitivity analysis, and automated pytest integrity test suite.
* **Excluded by Design:** The initial raw web scraping of 40 GitHub repositories and the iterative interactive pooling workflow are excluded because they rely on external network services and live GitHub APIs that are subject to upstream repository changes, rate limits, and network volatility. Providing the frozen curated corpora and ground truth ensures permanent, deterministic, offline reproducibility for conference reviewers.
