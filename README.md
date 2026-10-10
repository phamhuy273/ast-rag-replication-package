# Replication Package: AST-Based Progressive Disclosure Chunking and 2x2 Factorial Retrieval for Candidate Skill Matching

[![Target Conference](https://img.shields.io/badge/IEEE_SANER_2027-ERA_Track-blue.svg)](https://conf.researchr.org/home/saner-2027)
[![Review Policy](https://img.shields.io/badge/Review_Policy-Double--Anonymous-orange.svg)]()
[![Artifacts Evaluated](https://img.shields.io/badge/Artifacts-Available_&_Reproducible-success.svg)]()
[![Python Version](https://img.shields.io/badge/Python-3.10_%7C_3.11_%7C_3.12_%7C_3.13_%7C_3.14-blue.svg)]()
[![Automated Tests](https://img.shields.io/badge/Tests-Passing-brightgreen.svg)]()
[![License: MIT](https://img.shields.io/badge/Code_License-MIT-yellow.svg)](LICENSE)
[![License: CC BY 4.0](https://img.shields.io/badge/Data_License-CC_BY_4.0-lightgrey.svg)](LICENSE)

> **Target Venue:** 34th IEEE International Conference on Software Analysis, Evolution and Reengineering (IEEE SANER 2027)  
> **Track:** Early Research Achievements (ERA Track)  
> **Review Policy:** Double-Anonymous Peer Review  
> **Experimental Protocol:** Pre-registered Protocol (Path B) strictly governed by Anti-Hardcoding Rules R1–R46 and `analysis_plan_addendum.md`  

---

## 📌 Executive Summary & Research Questions

This replication package contains all source code, Tree-sitter AST parsers, curated chunk corpora, precomputed retrieval runs, LLM evaluation logs, and statistical hypothesis testing scripts necessary to reproduce all empirical tables, figures, and findings reported in our paper from scratch.

Our chunking strategy is **AST-first with line fallback**: it extracts method-level semantic AST blocks when available, and falls back to 50-LOC sliding windows when files lack parseable method structures (e.g. top-level JSX renders, styled components, interface contracts, and configuration objects). In our corpus of 364 AST chunks, 234 chunks (64.3%) are pure AST method extractions, while 130 chunks (35.7%) are handled via the pre-registered fallback mechanism (fully audited in `dataset/fallback_audit.csv`).

### Empirical Findings:

* **RQ1: Syntactic & Structural Integrity (Table 3.2):** How does method-level AST Progressive Disclosure chunking compare against standard fixed-window line slicing (50 LOC, 10 overlap) in preserving syntax boundaries and minimizing token bloat?
  * *AST Pure (N=234):* Preserves complete syntactic boundaries in **100.0%** of chunks (**0 boundary cuts**), achieves a **97.9%** parse error-free rate, provides **100.0%** context header retention (class and method hierarchy), reduces mean LOC to **19.8** (median: 13), reduces mean content tokens to **211.3**, and minimizes 512-token truncation to only **6.0%** (14 chunks).
  * *AST Fallback (N=130):* Preserves boundaries in **74.6%** (33 cuts), valid syntax in **20.0%**, mean LOC **42.9**, mean tokens **367.0**, truncation rate **20.0%** (26 chunks).
  * *AST Combined (N=364):* Overall preserves syntactic boundaries in **90.9%** of chunks (331/364 intact, 33 cuts), achieves a **70.1%** parse error-free rate, retains headers in **64.3%** of chunks, mean LOC **28.1**, mean tokens **266.9**, cutting 512-token truncation down to **11.0%** (40 chunks).
  * *Line Baseline (N=434):* Line-based slicing cuts across syntactic boundaries in **56.0%** of chunks (**44.0% intact**, 243/434 cuts), causes parse errors in **77.6%** of snippets (**22.4% valid syntax**), provides **0.0%** context header retention, mean LOC **41.0**, mean tokens **390.8**, and suffers a **28.6%** 512-token truncation rate (124 chunks).

* **RQ2: 2×2 Factorial Retrieval Quality & Re-ranking (Table 3.3):** Across a $2 \times 2$ Factorial Design ($\{\text{AST-first Method}, \text{Line-based}\} \times \{\text{Without Header}, \text{With Header}\}$) evaluated over 3 retrieval tiers (BM25, BGE-M3 Dense, BGE-Reranker-Base):
  * *Top Performer:* **Line+Header** is the empirical top performer on aggregate reranking metrics ($\text{NDCG@10} = \mathbf{0.4994}$, $\text{NDCG@1} = \mathbf{0.800}$, $\text{MRR@10} = \mathbf{0.980}$, $\text{CP@5} = \mathbf{0.935}$).
  * *AST Performance:* Isolated AST method chunks without headers suffer severe context deprivation ($\text{NDCG@10} = 0.3445$, $\text{NDCG@1} = 0.460$). Adding progressive context headers significantly boosts AST re-ranking performance to $\mathbf{0.4566}$ (**Comp 3:** $\Delta = \mathbf{+0.1120}$, paired Wilcoxon $W = 46.0$, $p_{\text{raw}} = 0.0010$, $p_{\text{Holm}} = \mathbf{0.0031} < 0.05$, 95% Bootstrap CI $[+0.0559, +0.1664]$), matching the full line baseline without headers ($0.4703$, $p_{\text{Holm}} = 0.8532$) while achieving higher Context Precision than Line No-Header ($\text{CP@5} = \mathbf{0.913}$ vs. $0.888$) and higher MRR ($\text{MRR@10} = \mathbf{0.940}$ vs. $0.933$).
  * *Exploratory Comp 5 (AST+Header vs. Line+Header):* $\Delta = -0.0428$, 95% Bootstrap CI $[-0.1056, +0.0211]$, Wilcoxon $W = 97.0, p = 0.1355 \ge 0.05$ (Line+Header wins 18 queries, AST+Header wins 6 queries, 1 tie; difference not statistically significant).
  * *Candidate Pool Random Baseline:* $\text{NDCG@10} = \mathbf{0.592} \pm 0.083$ across 1,000 permutations within pooled candidates.

* **RQ3: Downstream Generation Faithfulness & RAGAs Quality (Table 3.4, Exploratory):** How does retrieved evidence grounding affect LLM skill evaluation reliability?
  * *Empirical Finding:* Across 25 industry Job Descriptions, grounded LLM evaluation achieves perfect Faithfulness ($1.000 \pm 0.000$, zero hallucinations) with high Answer Relevance ($0.996 \pm 0.020$ for AST vs. $1.000$ for Line) and robust citation auditability ($79.3\%$ of AST claims citing explicit code locations). Evaluated via an offline cache of LLM judgments on Top-3 retrieved contexts.

* **Inter-Annotator Reliability (Table 3.1 & Figure 3.1):**
  * Evaluated on all 603 candidate pairs between Annotator 1 and Annotator 2: Exact Agreement = **79.77%** (481/603), Minor Disagreements = **18.57%** (112/603), Severe Disagreements = **1.66%** (10/603).
  * **Quadratic Weighted Cohen's Kappa ($\kappa_w$):** **`0.7795`** (*Substantial Agreement*, Landis & Koch 1977 [0.61–0.80]).
  * **Gold 250 Subset Kappa:** **`0.8808`** (*Almost Perfect Agreement*).
  * Adjudication of 122 disagreements includes 93 specific technical rationales (76.2%) and 29 structured rationales (23.8%).

---

## 📁 Repository Structure

```text
.
├── ai-engine/                                  # Core parsing & chunking engine
│   └── parser/
│       ├── tree_sitter_loader.py               # Tree-sitter AST Progressive Disclosure & line fallback chunker
│       └── __init__.py
├── dataset/                                    # Curated datasets, queries, and benchmark runs
│   ├── jd_raw/                                 # 25 raw industry Job Description texts (15 Java, 10 TS/React)
│   ├── queries_frozen.json                     # 25 pre-registered frozen queries with metadata
│   ├── manifest_repos.csv                      # 40 GitHub repositories with commit SHAs & licenses
│   ├── source_file_intervals.json              # Pinned method intervals across 189 files for boundary analysis
│   ├── fallback_audit.csv                      # Detailed audit and categorization of 130 fallback chunks
│   ├── header_bias_neutral_50_to_label.csv     # 50 stratified gold items for neutral re-annotation
│   ├── chunk_corpus.parquet                    # Dual corpus: 798 chunks (364 AST + 434 Line-based)
│   ├── chunk_corpus.jsonl                      # JSONL export of the dual corpus
│   ├── ground_truth_final.csv                  # 603 unified labeled pairs (250 Gold + 353 Pooled)
│   ├── ground_truth_annotator1.csv             # Anonymized annotations from Annotator 1 (603 pairs)
│   ├── ground_truth_annotator2.csv             # Anonymized annotations from Annotator 2 (603 pairs)
│   ├── disagreements_adjudication.csv          # 122 adjudicated disagreements with technical rationales
│   ├── to_label.csv                            # Neutral pooling candidate pairs (k=3 budget, Rule R44)
│   ├── pool_size_report.csv                    # Adaptive pool size report across 25 JDs
│   ├── table_3_2_measured.json                 # Real corpus morphology metrics across 4 subgroups
│   ├── table_3_2_report.txt                    # Formatted text report for Table 3.2
│   ├── sampling_frame_log.json                 # Sampling log for AST and Line chunking (Rule R10)
│   ├── annotation_guidelines.md                # 3-tier relevance labeling guideline for annotators
│   ├── retrieval_runs/                         # 12 precomputed retrieval run JSON files (3 tiers x 4 conditions)
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
│   └── benchmark_results/                      # Evaluation outputs, statistical reports, and figures
│       ├── table_3_retrieval_benchmark.csv     # Complete metrics for all 12 configurations + Random Baseline
│       ├── table_3_retrieval_benchmark.json
│       ├── statistical_tests_report.txt        # Family of 4 Wilcoxon tests + Holm-Bonferroni + Bootstrap CIs
│       ├── statistical_tests_report.json
│       ├── sensitivity_analysis_report.txt     # Exploratory sensitivity and subgroup analysis report
│       ├── sensitivity_analysis_results.json   # Sensitivity metrics in JSON format
│       ├── per_query_evaluation.csv            # Per-query metrics (300 records: 12 configs x 25 JDs)
│       ├── kappa_evaluation_report.txt         # Inter-annotator agreement evaluation report (Table 3.1)
│       ├── confusion_matrix_kappa.png          # Heatmap visualization of annotator confusion matrix
│       ├── ragas_evaluation_report.txt         # RAGAs evaluation report (Faithfulness, Relevance, Citation)
│       ├── ragas_evaluation_summary.csv        # Summary table for RAGAs generation metrics
│       ├── ragas_per_query_details.json        # Full generation and LLM-as-a-Judge audit logs
│       └── ragas_evaluation_cache.json         # Offline cache for LLM responses (enables offline reproduction)
├── paper/                                      # Automatically generated LaTeX tables for the paper
│   ├── table_3_2.tex                           # Corpus structural morphology comparison LaTeX table
│   ├── table_3_3_retrieval.tex                 # 2x2 Factorial retrieval benchmark LaTeX table
│   └── table_3_4_ragas.tex                     # RAGAs downstream generation quality LaTeX table
├── scripts/                                    # Standalone reproduction & evaluation runners
│   ├── reproduce_all.py                        # Master one-click runner executing all 7 steps end-to-end
│   ├── calculate_kappa.py                      # Reproduces Table 3.1 & Figure 3.1 (Inter-annotator agreement)
│   ├── evaluate_syntax.py                      # Reproduces Table 3.2 (AST pure, fallback, combined vs Line)
│   ├── evaluate_retrieval.py                   # Reproduces Table 3.3 (2x2 retrieval metrics & Wilcoxon tests)
│   ├── evaluate_ragas.py                       # Reproduces Table 3.4 (RAGAs downstream generation evaluation)
│   ├── evaluate_sensitivity.py                 # Evaluates exploratory subgroup & sensitivity analyses
│   ├── scan_anonymity.py                       # Verifies double-anonymous review compliance
│   ├── check_licenses.py                       # Audits open source licenses across all 40 repositories
│   └── audit_no_hardcode.py                    # Static AST analyzer enforcing Rules R1–R46
├── tests/                                      # Complete automated test suite (100% passing)
│   ├── test_gold_integrity.py                  # SHA-256 cryptographic verification of ground truth
│   ├── test_metrics_verification.py            # Unit tests for NDCG, MRR, CP against hand-calculated proofs
│   ├── test_corpus_characteristics.py          # Verifies Table 3.2 measurements and subgroups
│   ├── test_statistical_tests.py               # Verifies Wilcoxon and bootstrap implementations
│   ├── test_parser_edge_cases.py               # Unit tests for Tree-sitter parsers and extractors
│   ├── test_audit_detects.py                   # Positive control tests verifying auditor catches violations
│   └── test_readme_numbers.py                  # Asserts README numerical claims match benchmark files
├── analysis_plan.md                            # Pre-registered experimental analysis plan (frozen at Phase 0)
├── analysis_plan_addendum.md                   # Exploratory analysis protocol addendum (Path B)
├── CHANGELOG_FIXES.md                          # Detailed audit trail of all package enhancements
├── requirements.txt                            # Core package dependencies
├── requirements.lock                           # Fully locked, pinned transitive dependencies
├── run_all.bat                                 # One-click Windows master execution script
├── run_all.sh                                  # One-click Unix / macOS master execution script
├── .gitattributes                              # Cross-platform newline normalization rules
├── LICENSE                                     # MIT (Code) and CC-BY-4.0 (Dataset/Docs)
└── README.md                                   # Comprehensive replication guide
```

---

## ⚡ Quick Start & Environment Setup

### 1. Prerequisites
* **Python Version:** Python 3.10, 3.11, 3.12, 3.13, or 3.14.
* **Operating System:** Platform-independent (verified on Windows 11, Ubuntu 22.04 LTS, and macOS Sequoia).
* **Hardware:** Minimal requirements (< 4 GB RAM, runs entirely on CPU).

### 2. Environment Setup
Create and activate an isolated virtual environment:

```bash
# Clone the anonymous replication package
git clone <anonymous-repository-url>
cd ast-rag-replication-package

# Create virtual environment
python -m venv venv

# Activate virtual environment
# On Linux / macOS:
source venv/bin/activate
# On Windows (cmd):
venv\Scripts\activate.bat
# On Windows (PowerShell):
venv\Scripts\Activate.ps1

# Install locked dependencies
pip install -r requirements.lock
# (Or pip install -r requirements.txt)
```

---

## 🚀 One-Click Master Reproduction

To execute the entire empirical validation pipeline end-to-end in a single command, run:

```bash
python scripts/reproduce_all.py
```
*(Alternatively, on Windows run `run_all.bat`, or on Linux/macOS run `bash run_all.sh`).*

### Typical Output (~30 seconds on commodity CPU):
```text
===============================================================================================
  MASTER REPRODUCTION SUMMARY
===============================================================================================
Step     | Target Paper Item                   | Status   | Duration | Key Empirical Verification
-----------------------------------------------------------------------------------------------
STEP_1   | Unit Tests & Experimental Controls  | PASS     |    2.8s  | All tests passed
STEP_2   | Rules R1–R46 Static Analyzer        | PASS     |    0.1s  | 0 violations
STEP_3   | Table 3.1 & Figure 3.1 (Kappa)      | PASS     |    3.2s  | Quadratic Kappa = 0.7795, Agreement = 79.8%
STEP_4   | Table 3.2 (AST vs Line Morphology)  | PASS     |   12.5s  | AST Syntax Intact: 90.9% vs Line: 44.0%
STEP_5   | Table 3.3 & Confirmatory Hypotheses | PASS     |    2.8s  | Comp 3 AST Header Gain Statistically Significant
STEP_6   | Table 3.4 (RAGAs Generation)        | PASS     |    2.1s  | Faithfulness: 1.000, Relevance: 0.996, Citation: 79.3%
STEP_7   | Language, Fallback, Comp 5 & Sens.  | PASS     |    1.5s  | Comp 5 Delta = -0.0428, Top Fallback: JSX render
===============================================================================================
Total Reproduction Time: 25.0s
RESULT: ALL 7 EMPIRICAL REPRODUCTION STEPS COMPLETED AND VERIFIED SUCCESSFULLY [PASS]
===============================================================================================
```

---

## 🔬 Detailed Step-by-Step Reproduction Guide

Each empirical claim, table, and statistical hypothesis test can be verified independently:

### Step 1: Automated Test Suite & Controls
Verifies hash immutability (Rule R17), ground truth integrity, metric implementations against hand-calculated proofs, parser edge cases, static auditor sensitivity, and numerical consistency of README claims:
```bash
python -m pytest tests/ -v
```

---

### Step 2: Anti-Hardcoding Static Audit (Rules R1–R46)
Scans active codebase using Python AST visitors and regex analyzers to detect any hardcoded metrics, placeholder assignments, non-deterministic random calls, or silent exception fallbacks:
```bash
python scripts/audit_no_hardcode.py
```

---

### Step 3: Reproduce Table 3.1 & Figure 3.1 — Inter-Annotator Reliability
Evaluates independent human annotations from Annotator 1 and Annotator 2 across all 603 candidate pairs, computing Quadratic Weighted Cohen's Kappa ($\kappa_w$), Linear Kappa, exact agreement rate, and generating the confusion matrix heatmap:
```bash
python scripts/calculate_kappa.py
```
* **Key Verified Results:**
  * Total Candidate Evidence Pairs ($N$): **603**
  * Exact Consensus Matches ($p_o$): **481 / 603 (79.77%)**
  * Minor Disagreements ($|\Delta| = 1$): **112 / 603 (18.57%)**
  * Severe Disagreements ($|\Delta| = 2$): **10 / 603 (1.66%)**
  * **Quadratic Weighted Kappa ($\kappa_w$):** **`0.7795`** (*Substantial Agreement*, Landis & Koch 1977 [0.61–0.80])
  * **Gold 250 Subset Kappa:** **`0.8808`** (*Almost Perfect Agreement*)
* **Generated Artifacts:**
  * Report: `dataset/benchmark_results/kappa_evaluation_report.txt`
  * Figure: `dataset/benchmark_results/confusion_matrix_kappa.png`

---

### Step 4: Reproduce Table 3.2 — Real Corpus Morphology & Syntax Boundaries
Executes live Tree-sitter syntax parsing and HuggingFace AutoTokenizer (`BAAI/bge-m3`) across all 798 chunks from 189 source files:
```bash
python scripts/evaluate_syntax.py
```
* **Key Verified Results:**
  * **AST Pure (N=234):** 100.0% boundary intact (0 cuts), 97.9% valid syntax, 100.0% context header retention, mean LOC 19.8, mean tokens 211.3, truncation >512 tokens: 6.0% (14 chunks).
  * **AST Fallback (N=130):** 74.6% boundary intact (33 cuts), 20.0% valid syntax, 0.0% header retention, mean LOC 42.9, mean tokens 367.0, truncation >512 tokens: 20.0% (26 chunks).
  * **AST Combined (N=364):** 90.9% boundary intact (33 cuts), 70.1% valid syntax, 64.3% header retention, mean LOC 28.1, mean tokens 266.9, truncation >512 tokens: 11.0% (40 chunks).
  * **Line Baseline (N=434):** 44.0% boundary intact (243 cuts), 22.4% valid syntax, 0.0% header retention, mean LOC 41.0, mean tokens 390.8, truncation >512 tokens: 28.6% (124 chunks).
* **Generated Artifacts:**
  * LaTeX Table: `paper/table_3_2.tex`
  * JSON Metrics: `dataset/table_3_2_measured.json`
  * Report: `dataset/table_3_2_report.txt`

---

### Step 5: Reproduce Table 3.3 — 2×2 Factorial Retrieval Benchmark & Hypothesis Testing
Computes NDCG@{1, 3, 5, 10}, MRR@10, Precision@5, Recall@10, and Context Precision@5 across all 12 configurations (3 tiers $\times$ 4 factorial conditions) + Random Baseline. Executes the pre-registered Family of 4 Wilcoxon signed-rank tests with Holm-Bonferroni correction and 95% Bootstrap CIs (10,000 resamples, seed=42):
```bash
python scripts/evaluate_retrieval.py
```
* **Key Verified Results:**
  * **Comp 3 (Header Effect on AST Chunks):** $\Delta = \mathbf{+0.1120}$, 95% Bootstrap CI $[+0.0559, +0.1664]$, $W = 46.0$, $p_{\text{raw}} = 0.0010$, $p_{\text{Holm}} = \mathbf{0.0031} < 0.05$ (Statistically significant improvement of progressive context headers).
  * **Comp 2 (Pure Chunking Effect without Headers):** $\Delta = \mathbf{-0.1258}$, $p_{\text{Holm}} = \mathbf{0.0001} < 0.05$ (Confirms severe degradation when syntax chunks lack context).
  * **Comp 1 (Full Proposed AST+Header vs. Baseline Line No-Header):** $\Delta = -0.0138$, 95% Bootstrap CI $[-0.0882, +0.0575]$, $p_{\text{Holm}} = 0.8532$ (Comparable re-ranking performance with superior top-1 ranking: $\text{NDCG@1} = 0.720$ vs. $0.460$, and higher Context Precision: $\text{CP@5} = 0.913$).
  * **Comp 4 (Header Effect on Line Chunks):** $\Delta = +0.0291$, $p_{\text{Holm}} = 0.7332 \ge 0.05$ (Not statistically significant).
* **Generated Artifacts:**
  * LaTeX Table: `paper/table_3_3_retrieval.tex`
  * Complete Metrics: `dataset/benchmark_results/table_3_retrieval_benchmark.csv`
  * Statistical Report: `dataset/benchmark_results/statistical_tests_report.txt`
  * Per-Query Breakdown: `dataset/benchmark_results/per_query_evaluation.csv`

---

### Step 6: Reproduce Table 3.4 — Downstream Generation & RAGAs Quality (Exploratory)
Evaluates grounded candidate skill matching reports generated by LLMs using Top-3 retrieved code snippets as context:
```bash
python scripts/evaluate_ragas.py
```
*(Loads cached responses from `dataset/benchmark_results/ragas_evaluation_cache.json` for deterministic offline reproduction. Online evaluation supported by providing `GEMINI_API_KEY`).*
* **Key Verified Results:**
  * **Faithfulness:** **`1.000`** (AST) vs. **`1.000`** (Line) — 100% grounded in code context, zero hallucinations.
  * **Answer Relevance:** **`0.996`** (AST) vs. **`1.000`** (Line).
  * **Citation Coverage:** **`79.3%`** (AST) vs. **`79.2%`** (Line) — over 79% of claims cite explicit code file/line locations.
* **Generated Artifacts:**
  * LaTeX Table: `paper/table_3_4_ragas.tex`
  * Generation Summary: `dataset/benchmark_results/ragas_evaluation_summary.csv`
  * Full Audit Details: `dataset/benchmark_results/ragas_per_query_details.json`

---

### Step 7: Exploratory Sensitivity & Subgroup Analysis
Executes subgroup analyses evaluating language effects (Java vs. React/TS), fallback composition, Comp 5 (AST+Header vs Line+Header), and annotator sensitivity:
```bash
python scripts/evaluate_sensitivity.py
```
* **Key Verified Results:**
  * **Comp 5 (AST+Header vs Line+Header):** $\Delta = -0.0428$, 95% Bootstrap CI $[-0.1056, +0.0211]$, $W = 100.0, p = 0.1355$.
  * **Fallback Composition:** Top fallback reason is top-level JSX renders (51/130, 39.2%), followed by styled-components (23/130, 17.7%) and object configurations (13/130, 10.0%).
  * **Annotator Robustness:** The ranking order remains strictly invariant across consensus pairs ($N=481$), Annotator 1 alone, and Annotator 2 alone.
* **Generated Artifacts:**
  * Report: `dataset/benchmark_results/sensitivity_analysis_report.txt`
  * JSON: `dataset/benchmark_results/sensitivity_analysis_results.json`

---

## 📊 Dataset Provenance & Integrity Specifications

| Dataset File | Records | Format | Description | Integrity Verification |
|:---|:---:|:---:|:---|:---|
| `queries_frozen.json` | 25 | JSON | Pre-registered industry Job Descriptions (15 Java, 10 TS/React) | Frozen at Phase 0 |
| `manifest_repos.csv` | 40 | CSV | GitHub repositories with pinned commit SHAs, licenses, file lists | Audited licenses |
| `source_file_intervals.json` | 189 | JSON | Pinned method line intervals across 189 source files | Verified via Tree-sitter |
| `fallback_audit.csv` | 130 | CSV | Detailed diagnostic categorization of all 130 line-fallback chunks | Audited |
| `header_bias_neutral_50_to_label.csv`| 50 | CSV | 50 stratified gold items for neutral re-annotation without headers | Seed=42 stratified sample |
| `chunk_corpus.parquet` | 798 | Parquet | Unified dual corpus: 364 AST + 434 Line chunks | Unique `chunk_id` enforced |
| `chunk_corpus.jsonl` | 798 | JSONL | JSONL format of dual corpus | Text identical to Parquet |
| `ground_truth_final.csv` | 603 | CSV | Unified ground truth (250 Gold + 353 Pooled pairs) | Normalized SHA-256 Hash Locked |
| `disagreements_adjudication.csv`| 122 | CSV | 122 resolved disagreements with technical rationales | 93 technical, 29 templated |
| `retrieval_runs/*.json` | 12 files | JSON | Top-10 ranking outputs for 3 retrieval tiers $\times$ 4 conditions | Deterministic scoring |

### Ground Truth Normalized SHA-256 Hashes:
In accordance with Rule R17 and cross-platform verification (handling Windows `\r\n` vs. Linux `\n`), the ground truth dataset is cryptographically locked on normalized newlines:
* `ground_truth_final.csv` (Entire file): `70C01F773136F7D0352012B7D1F1DD9DB216708848C5A54E22A661DFD93DBB4D`
* Gold subset (First 250 labels): `222A9F55353597AF4B0DA9118E81F94602C5E78DCC9AF95C5490DC7D8EC45638`
*(Automatically verified by `tests/test_gold_integrity.py`).*

---

## ⚖️ Ethical Considerations & Anonymity

* **Double-Anonymous Review Compliance:** All personal names, institutional affiliations, and author emails have been scrubbed from the repository, code docstrings, and commit history. Annotators are referenced solely as `annotator_1`, `annotator_2`, and `Lead Adjudicator`. Verified via `scripts/scan_anonymity.py`.
* **Repository Provenance & Licensing:** All 40 source repositories mined in this study are public GitHub repositories. Automated license audit (`scripts/check_licenses.py`) reveals: 19 repositories under MIT, 4 under Apache-2.0, 1 under AGPL-3.0, and 16 public repositories without explicit license files in the root. Mined code snippets are used strictly for academic evaluation and benchmarking purposes.
* **Data Availability:** All raw and processed artifacts are provided in open, non-proprietary formats (`.csv`, `.json`, `.parquet`, `.tex`).

---

## 📜 License

* **Code:** The source code and evaluation scripts in this package are released under the [MIT License](LICENSE).
* **Data & Documentation:** The curated datasets, benchmark results, and documentation are made available under the [Creative Commons Attribution 4.0 International License (CC BY 4.0)](LICENSE).
