# Replication Package: AST-Based Progressive Disclosure Chunking and 2x2 Factorial Retrieval for Candidate Skill Matching

> **Target Publication:** 34th IEEE International Conference on Software Analysis, Evolution and Reengineering (IEEE SANER 2027)  
> **Track:** Early Research Achievements (ERA Track)  
> **Review Policy:** Double-Anonymous Peer Review  
> **Experimental Framework:** Pre-registered Protocol (Path B) governed by Anti-Hardcoding Rules R1–R46  

---

## 📌 Overview

This replication package contains all source corpora, parser implementations, curated datasets, evaluation runners, and statistical testing scripts required to independently replicate all empirical results reported in our paper from scratch.

### Research Questions & Empirical Findings:
* **RQ1 (Syntactic & Structural Integrity — Table 3.2):** How does method-level AST Progressive Disclosure chunking compare to traditional fixed-window line slicing (50 LOC) in preserving syntactic boundaries and reducing token bloat?
  * *Result:* Line-based slicing breaks syntactic boundaries in **56.0%** of chunks and causes Tree-sitter parse errors in **77.6%** of snippets. AST Progressive Disclosure preserves complete syntax boundaries in **90.9%** of chunks, reducing mean token length from 390.8 to 266.9 tokens and truncation rate (>512 tokens) from 28.6% down to 11.0%.
* **RQ2 (2x2 Factorial Retrieval Quality & Re-ranking — Table 3.3):** Across a 2×2 Factorial Design {AST Method, Line-based} × {Without Header, With Header} evaluated over 3 retrieval tiers (BM25, BGE-M3 Dense, BGE-Reranker-Base):
  * *Result:* Isolated AST method chunks without headers suffer severe context deprivation ($\text{NDCG@10} = 0.345$). Adding progressive context headers significantly boosts AST re-ranking performance to $\mathbf{0.457}$ ($\Delta = +0.1120$, paired Wilcoxon $p_{\text{Holm}} = 0.0031 < 0.05$, 95% Bootstrap CI $[+0.0559, +0.1664]$), matching the line baseline ($0.470$, $p_{\text{Holm}} = 0.8532$) while achieving higher Top-1 ranking ($\text{NDCG@1} = 0.720$ vs. $0.460$, $\text{MRR@10} = 0.940$) and superior Context Precision ($\text{CP@5} = 0.913$).
* **RQ3 (Downstream Generation Faithfulness & RAGAs — Table 3.4):** How does retrieved evidence grounding affect LLM skill evaluation reliability?
  * *Result:* Across 25 industry Job Descriptions, both grounded systems achieve perfect Faithfulness ($1.000 \pm 0.000$, zero hallucinations) with high Answer Relevance ($0.996 \pm 0.020$) and robust citation auditability ($79.3\%$ of claims citing explicit code locations).

---

## 📁 Repository Structure

```text
.
├── ai-engine/
│   └── parser/
│       └── tree_sitter_loader.py          # Tree-sitter AST Progressive Disclosure & line fallback chunker
├── dataset/
│   ├── manifest_repos.csv                 # 40 GitHub repositories with pinned commit SHAs & licenses
│   ├── queries_frozen.json                # 25 pre-registered industry Job Descriptions (15 Java, 10 TS/React)
│   ├── chunk_corpus.parquet               # Dual corpus: 798 chunks (364 AST + 434 Line-based)
│   ├── chunk_corpus.jsonl                 # JSONL export of the dual corpus
│   ├── ground_truth_final.csv             # 603 unified ground truth pairs (250 Gold + 353 Pooled)
│   ├── ground_truth_annotator1.csv        # Anonymized annotations from Annotator 1 (603 pairs)
│   ├── ground_truth_annotator2.csv        # Anonymized annotations from Annotator 2 (603 pairs)
│   ├── disagreements_adjudication.csv     # 122 adjudicated disagreements with technical rationales
│   ├── to_label.csv                       # Neutral pooling candidate file (Rule R18, R19, R44)
│   ├── pool_size_report.csv               # Adaptive pool size report across 25 JDs (k=3 budget)
│   ├── verification_report.csv            # Character-level verification of gold chunks against repos
│   ├── retrieval_runs/                    # 12 precomputed retrieval run JSON files (3 tiers x 4 conditions)
│   │   ├── bm25_ast_no_header.json
│   │   ├── bm25_ast_with_header.json
│   │   ├── bm25_line_no_header.json
│   │   ├── bm25_line_with_header.json
│   │   ├── dense_ast_no_header.json
│   │   ├── dense_ast_with_header.json
│   │   ├── dense_line_no_header.json
│   │   ├── dense_line_with_header.json
│   │   ├── rerank_ast_no_header.json
│   │   ├── rerank_ast_with_header.json
│   │   ├── rerank_line_no_header.json
│   │   └── rerank_line_with_header.json
│   └── benchmark_results/                 # Evaluation outputs, statistical reports, and LaTeX tables
│       ├── table_3_retrieval_benchmark.csv# Complete metrics for all 12 configurations + Random Baseline
│       ├── table_3_retrieval_benchmark.json
│       ├── statistical_tests_report.txt   # Family of 4 Wilcoxon tests + Holm-Bonferroni + Bootstrap CIs
│       ├── statistical_tests_report.json
│       ├── per_query_evaluation.csv       # Per-query metrics (300 records: 12 configs x 25 JDs)
│       ├── ragas_evaluation_report.txt    # RAGAs evaluation report (Faithfulness, Relevance, Citation)
│       ├── ragas_evaluation_summary.csv   # Summary table for RAGAs generation metrics
│       ├── ragas_per_query_details.json   # Full generation and LLM-as-a-Judge audit logs
│       ├── kappa_evaluation_report.txt    # Inter-annotator agreement evaluation report (Table 3.1)
│       └── confusion_matrix_kappa.png     # Heatmap visualization of annotator confusion matrix
├── paper/
│   ├── table_3_2.tex                      # Corpus structural comparison LaTeX table
│   ├── table_3_3_retrieval.tex            # 2x2 Factorial retrieval benchmark LaTeX table
│   └── table_3_4_ragas.tex                # RAGAs generation quality LaTeX table
├── scripts/
│   ├── calculate_kappa.py                 # Evaluates inter-annotator agreement & generates Table 3.1
│   ├── generate_table_3_2_real.py         # Measures real corpus characteristics via Tree-sitter (Table 3.2)
│   ├── evaluate_2x2.py                    # Evaluates all 12 retrieval configurations & hypothesis tests (Table 3.3)
│   ├── evaluate_ragas.py                  # Downstream RAG generation & RAGAs evaluator (Table 3.4)
│   ├── build_dual_corpus.py               # Generates the 798-chunk dual corpus from repositories
│   ├── run_retrieval_and_pooling.py       # Executes 12 retrieval runs and adaptive pooling (Rule R44)
│   ├── merge_and_anonymize_ground_truth.py# Merges, adjudicates, and anonymizes ground truth datasets
│   ├── verify_gold_chunks.py              # Character-level verification against pinned repos (Rule R11)
│   └── audit_no_hardcode.py               # Automated static audit enforcing Rules R1–R46
├── tests/                                 # Complete automated test suite (42 tests, 100% passing)
├── analysis_plan.md                       # Pre-registered experimental analysis plan (frozen at Phase 0)
├── requirements.txt                       # Locked dependencies
└── README.md                              # This reproduction guide
```

---

## 📊 Dataset Organization & Provenance

To guarantee complete scientific rigor and adhere to double-anonymous review standards:

1. **Frozen Queries (`queries_frozen.json`):**
   * Exactly 25 industry Job Descriptions (15 Java / Spring Boot and 10 React / TypeScript / Fullstack).
   * Fixed and pre-registered at Phase 0 before running downstream retrieval.

2. **Repository Universe (`manifest_repos.csv`):**
   * Exactly 40 open-source GitHub repositories (20 Java, 20 TypeScript/React) with pinned commit SHAs, URLs, and permissive open-source licenses (MIT, Apache-2.0, BSD-3-Clause).

3. **Dual Corpus (`chunk_corpus.parquet` — 798 chunks):**
   * **AST Method Chunks:** 364 syntax-bounded function/method nodes extracted via Tree-sitter.
   * **Line-based Chunks:** 434 fixed-window slices (50 LOC, 10 overlap).

4. **Unified Ground Truth (`ground_truth_final.csv` — 603 pairs):**
   * **250 Gold-Standard Pairs:** Curated in pilot phase and character-verified against repositories (`verification_report.csv`).
   * **353 Pooled Candidate Pairs:** Mined via adaptive pooling ($k=3$, Rule R44) across 12 retrieval runs.
   * **Human Annotation Protocol:** Double-blind independent labeling by 2 software engineers on a 3-tier scale (0 = Irrelevant, 1 = Partial/Indirect, 2 = Direct Core Implementation).
   * **Inter-Annotator Agreement:** Quadratic Weighted Cohen's Kappa $\kappa_w = \mathbf{0.7795}$ ($p_o = 79.77\%$ exact matches, $\kappa_w = 0.8808$ on Gold 250).
   * **Adjudication:** All 122 disagreements resolved with explicit technical rationales in `disagreements_adjudication.csv` without boilerplate text (Rule R21).

---

## 🚀 Quick Start & Environment Setup

### 1. Prerequisites
* Python 3.10, 3.11, 3.12, 3.13, or 3.14.
* Compatible with Windows, Linux, and macOS.

### 2. Installation
```bash
# Clone the repository
git clone <anonymous-repository-url>
cd ast-rag-replication-package

# Install dependencies
pip install -r requirements.txt
```

---

## 🔬 One-Click Reproduction Guide

Every empirical table, figure, and statistical test reported in the paper is dynamically computed from raw data with zero hardcoded values:

### 1. Verify Experimental Controls & Test Suite
Runs the full automated test suite (42 tests verifying data integrity, metric formulas against hand-calculated cases, experimental controls, and hash immutability):
```bash
python -m pytest tests/
```
*Expected Output:* `42 passed in ~2.5s`.

### 2. Verify Anti-Hardcoding Governance (Rules R1–R46)
Runs the automated static analyzer checking for hardcoded metrics, synthetic overrides, silent fallbacks, or data leakage:
```bash
python scripts/audit_no_hardcode.py
```
*Expected Output:* `Total findings detected: 0. PASS: Zero violations found.`

### 3. Reproduce Table 3.1: Inter-Annotator Reliability
Computes Quadratic Weighted Cohen's Kappa ($\kappa_w$), linear kappa, unweighted kappa, and confusion matrix heatmap:
```bash
python scripts/calculate_kappa.py
```
*Expected Output:*
* Evaluated pairs ($N$): 603
* Exact matches ($p_o$): 481 / 603 (79.77%)
* Quadratic Weighted Kappa ($\kappa_w$): **`0.7795`** (Substantial / High Agreement)
* Generates `dataset/benchmark_results/confusion_matrix_kappa.png`.

### 4. Reproduce Table 3.2: Real Corpus Chunking Characteristics
Extracts syntactic boundaries using Tree-sitter and tokenizes via BGE-M3 tokenizer on the actual 798 chunks:
```bash
python scripts/evaluate_syntax.py
```
*Expected Output:*
* Syntax Boundary Preservation: **90.9%** (AST) vs. **44.0%** (Line-based, 56.0% fragmented).
* Parse Error-Free Rate: **70.1%** (AST) vs. **22.4%** (Line-based).
* Mean Token Length: **266.9** (AST) vs. **390.8** (Line-based).
* Generates `paper/table_3_2.tex`.

### 5. Reproduce Table 3.3: 2x2 Factorial Retrieval Benchmark & Hypothesis Testing
Computes NDCG@{1, 3, 5, 10}, MRR@10, Precision@5, Recall@10, Context Precision@5, and runs the pre-registered Family of 4 Wilcoxon signed-rank tests with Holm-Bonferroni correction and 95% Bootstrap CIs (10,000 resamples):
```bash
python scripts/evaluate_retrieval.py
```
*Expected Output:*
* Comparison 3 (Header Effect on AST): $\Delta = \mathbf{+0.1120}$, 95% CI $[+0.0559, +0.1664]$, $p_{\text{Holm}} = \mathbf{0.0031} < 0.05$ (Statistically Significant positive contribution of Context Header).
* Comparison 2 (Pure Chunking Effect): $\Delta = \mathbf{-0.1258}$, $p_{\text{Holm}} = \mathbf{0.0001} < 0.05$ (Isolated AST method chunks degrade without headers).
* Comparison 1 (Full Proposed vs. Full Baseline): $\Delta = -0.0138$, 95% CI $[-0.0882, +0.0575]$, $p_{\text{Holm}} = 0.8532$ (Comparable re-ranking performance).
* Generates `paper/table_3_3_retrieval.tex` and `statistical_tests_report.txt`.

### 6. Reproduce Table 3.4: RAGAs Downstream Generation Benchmark
Generates candidate evaluation reports across 25 JDs using Top-3 retrieved code context and performs LLM-as-a-Judge RAGAs evaluation:
```bash
python scripts/evaluate_ragas.py
```
*(Requires `GEMINI_API_KEY` in `.env` if re-running online; loads from `ragas_evaluation_cache.json` immediately if recomputing offline).*
*Expected Output:*
* Faithfulness: **1.000** (AST) vs. **1.000** (Line) — 100% grounded in code context.
* Answer Relevance: **0.996** (AST) vs. **1.000** (Line).
* Citation Coverage: **79.3%** (AST) vs. **79.2%** (Line).
* Generates `paper/table_3_4_ragas.tex`.

---

## ⚖️ Ethical Considerations & Anonymity

* In compliance with double-anonymous peer review, all personal annotator identifiers have been anonymized (`annotator_1`, `annotator_2`, `Lead Adjudicator`).
* All repositories mined are public open-source projects licensed under permissive terms (MIT, Apache 2.0, BSD-3-Clause).
* All prompt instructions and raw data are preserved in open formats (CSV, JSON, Parquet).
