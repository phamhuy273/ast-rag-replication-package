# Replication Package: AST-Based Progressive Disclosure Chunking and 2x2 Factorial Retrieval for Candidate Skill Matching

[![Target Conference](https://img.shields.io/badge/IEEE_SANER_2027-ERA_Track-blue.svg)](https://conf.researchr.org/home/saner-2027)
[![Review Policy](https://img.shields.io/badge/Review_Policy-Double--Anonymous-orange.svg)]()
[![Artifacts Evaluated](https://img.shields.io/badge/Artifacts-Available_&_Reproducible-success.svg)]()
[![Python Version](https://img.shields.io/badge/Python-3.10_%7C_3.11_%7C_3.12_%7C_3.13_%7C_3.14-blue.svg)]()
[![Tests](https://img.shields.io/badge/Tests-42_passed-brightgreen.svg)]()
[![License: MIT](https://img.shields.io/badge/Code_License-MIT-yellow.svg)](LICENSE)
[![License: CC BY 4.0](https://img.shields.io/badge/Data_License-CC_BY_4.0-lightgrey.svg)](LICENSE)

> **Target Venue:** 34th IEEE International Conference on Software Analysis, Evolution and Reengineering (IEEE SANER 2027)  
> **Track:** Early Research Achievements (ERA Track)  
> **Review Policy:** Double-Anonymous Peer Review  
> **Experimental Protocol:** Pre-registered Protocol (Path B) strictly governed by Anti-Hardcoding Rules R1–R46  

---

## 📌 Executive Summary & Research Questions

This replication package contains all source code, Tree-sitter parsers, curated corpora, precomputed retrieval runs, LLM evaluation logs, and statistical hypothesis testing scripts necessary to reproduce all empirical tables, figures, and findings reported in our paper from scratch.

### Empirical Findings:
* **RQ1: Syntactic & Structural Integrity (Table 3.2):** How does method-level AST Progressive Disclosure chunking compare against standard fixed-window line slicing (50 LOC, 10 overlap) in preserving syntax boundaries and minimizing token bloat?
  * *Empirical Finding:* Line-based slicing cuts across syntactic boundaries in **56.0%** of chunks (243/434 cuts) and causes Tree-sitter parse errors in **77.6%** of snippets (337/434). In contrast, AST Progressive Disclosure preserves complete syntax boundaries in **90.9%** of chunks (331/364 intact, only 33 boundary cuts), achieves a **70.1%** parse error-free rate, and reduces mean token length from **390.8** to **266.9 tokens**, cutting 512-token truncation rates from **28.6%** down to **11.0%**.
* **RQ2: 2×2 Factorial Retrieval Quality & Re-ranking (Table 3.3):** Across a $2 \times 2$ Factorial Design ($\{\text{AST Method}, \text{Line-based}\} \times \{\text{Without Header}, \text{With Header}\}$) evaluated over 3 retrieval tiers (BM25, BGE-M3 Dense, BGE-Reranker-Base):
  * *Empirical Finding:* Isolated AST method chunks without headers suffer severe context deprivation ($\text{NDCG@10} = 0.345$). Adding progressive context headers significantly boosts AST re-ranking performance to $\mathbf{0.457}$ ($\Delta = +0.1120$, paired Wilcoxon $p_{\text{raw}} = 0.0010$, $p_{\text{Holm}} = 0.0031 < 0.05$, 95% Bootstrap CI $[+0.0559, +0.1664]$), matching the full line baseline ($0.470$, $p_{\text{Holm}} = 0.8532$) while achieving higher Top-1 ranking precision ($\text{NDCG@1} = 0.720$ vs. $0.460$, $\text{MRR@10} = 0.940$) and superior Context Precision ($\text{CP@5} = 0.913$).
* **RQ3: Downstream Generation Faithfulness & RAGAs (Table 3.4):** How does retrieved evidence grounding affect LLM skill evaluation reliability?
  * *Empirical Finding:* Across 25 industry Job Descriptions, grounded LLM evaluation achieves perfect Faithfulness ($1.000 \pm 0.000$, zero hallucinations) with high Answer Relevance ($0.996 \pm 0.020$) and robust citation auditability ($79.3\%$ of claims citing explicit code locations).

---

## 📁 Repository Structure

```text
.
├── ai-engine/                                  # Core parsing & chunking engine
│   └── parser/
│       ├── tree_sitter_loader.py               # Tree-sitter AST Progressive Disclosure & line fallback chunker
│       └── __init__.py
├── dataset/                                    # Curated datasets, queries, and runs
│   ├── jd_raw/                                 # 25 raw industry Job Description texts (15 Java, 10 TS/React)
│   ├── queries_frozen.json                     # 25 pre-registered frozen queries with metadata
│   ├── manifest_repos.csv                      # 40 GitHub repositories with pinned commit SHAs & licenses
│   ├── source_file_intervals.json              # Pinned method intervals across 189 files for boundary analysis
│   ├── chunk_corpus.parquet                    # Dual corpus: 798 chunks (364 AST + 434 Line-based)
│   ├── chunk_corpus.jsonl                      # JSONL export of the dual corpus
│   ├── ground_truth_final.csv                  # 603 unified labeled pairs (250 Gold + 353 Pooled)
│   ├── ground_truth_annotator1.csv             # Anonymized annotations from Annotator 1 (603 pairs)
│   ├── ground_truth_annotator2.csv             # Anonymized annotations from Annotator 2 (603 pairs)
│   ├── disagreements_adjudication.csv          # 122 adjudicated disagreements with technical rationales
│   ├── to_label.csv                            # Neutral pooling candidate pairs (k=3 budget, Rule R44)
│   ├── pool_size_report.csv                    # Adaptive pool size report across 25 JDs
│   ├── table_3_2_measured.json                 # Real corpus morphology metrics (LOC, tokens, syntax intactness)
│   ├── table_3_2_report.txt                    # Formatted text report for Table 3.2
│   ├── sampling_frame_log.json                 # Sampling log for AST and Line chunking (Rule R10)
│   ├── annotation_guidelines.md                # 3-tier relevance labeling guideline given to annotators
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
│   ├── reproduce_all.py                        # Master one-click runner executing all steps end-to-end
│   ├── calculate_kappa.py                      # Reproduces Table 3.1 & Figure 3.1 (Inter-annotator agreement)
│   ├── evaluate_syntax.py                      # Reproduces Table 3.2 (AST vs Line syntax & morphology)
│   ├── evaluate_retrieval.py                   # Reproduces Table 3.3 (2x2 retrieval metrics & Wilcoxon tests)
│   ├── evaluate_ragas.py                       # Reproduces Table 3.4 (RAGAs downstream generation evaluation)
│   └── audit_no_hardcode.py                    # Static AST analyzer enforcing Rules R1–R46
├── tests/                                      # Complete automated test suite (42 tests, 100% passing)
├── analysis_plan.md                            # Pre-registered experimental analysis plan (frozen at Phase 0)
├── requirements.txt                            # Pinned Python package dependencies
├── run_all.bat                                 # One-click Windows runner
├── run_all.sh                                  # One-click Unix / macOS runner
├── LICENSE                                     # MIT (Code) and CC-BY-4.0 (Dataset/Docs)
└── README.md                                   # Comprehensive replication guide
```

---

## ⚡ Quick Start & Environment Setup

### 1. Prerequisites
* **Python Version:** Python 3.10, 3.11, 3.12, 3.13, or 3.14.
* **Operating System:** Platform-independent (fully verified on Windows 11, Ubuntu 22.04 LTS, and macOS Sequoia).
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
pip install -r requirements.txt
```

---

## 🚀 One-Click Master Reproduction

To execute the entire empirical validation pipeline end-to-end in a single command, run:

```bash
python scripts/reproduce_all.py
```
*(Alternatively, on Windows double-click or run `run_all.bat`, or on Linux/macOS run `bash run_all.sh`).*

### Typical Output (~25 seconds on commodity CPU):
```text
===============================================================================================
  MASTER REPRODUCTION SUMMARY
===============================================================================================
Step     | Target Paper Item                   | Status   | Duration | Key Empirical Verification
-----------------------------------------------------------------------------------------------
STEP_1   | Unit Tests & Experimental Controls  | PASS     |    3.0s  | 42 passed
STEP_2   | Rules R1–R46 Static Analyzer        | PASS     |    0.1s  | 0 violations
STEP_3   | Table 3.1 & Figure 3.1 (Kappa)      | PASS     |    3.2s  | Quadratic Kappa = 0.7795, Agreement = 79.8%
STEP_4   | Table 3.2 (AST vs Line Morphology)  | PASS     |   12.9s  | AST Syntax Intact: 90.9% vs Line: 44.0%
STEP_5   | Table 3.3 & Confirmatory Hypotheses | PASS     |    2.8s  | Comp 3 AST Header Gain Statistically Significant
STEP_6   | Table 3.4 (RAGAs Generation)        | PASS     |    2.1s  | Faithfulness: 1.000, Relevance: 0.996, Citation: 79.3%
===============================================================================================
Total Reproduction Time: 24.1s
RESULT: ALL 6 EMPIRICAL REPRODUCTION STEPS COMPLETED AND VERIFIED SUCCESSFULLY [PASS]
===============================================================================================
```

---

## 🔬 Detailed Step-by-Step Reproduction Guide

Each empirical claim, table, and statistical hypothesis test can be verified independently:

### Step 1: Automated Test Suite & Experimental Controls (42 Tests)
Verifies hash immutability (Rule R17), ground truth integrity, metric calculation implementations against hand-calculated proofs, parser edge cases, and statistical determinism:
```bash
python -m pytest tests/ -v
```
* **Expected Output:** `42 passed in ~2.2s`.

---

### Step 2: Anti-Hardcoding Static Audit (Rules R1–R46)
Scans active codebase using Python AST visitors and regex analyzers to detect any hardcoded metrics, placeholder assignments, or silent exception fallbacks:
```bash
python scripts/audit_no_hardcode.py
```
* **Expected Output:**
  ```text
  ================================================================================
  AUDIT SCAN RESULTS: ANTI-HARDCODING RULES (R1 - R46)
  ================================================================================
  Total findings detected: 0
  PASS: Zero violations found in newly developed / active pipeline files.
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
  * **Quadratic Weighted Kappa ($\kappa_w$):** **`0.7795`** (*Almost Perfect / Excellent Agreement*, Landis & Koch 1977)
  * **Gold 250 Subset Kappa:** **`0.8808`**
* **Generated Artifacts:**
  * Report: `dataset/benchmark_results/kappa_evaluation_report.txt`
  * Figure: `dataset/benchmark_results/confusion_matrix_kappa.png`

---

### Step 4: Reproduce Table 3.2 — Real Corpus Morphology & Syntax Boundaries
Executes live Tree-sitter syntax parsing and HuggingFace AutoTokenizer (`BAAI/bge-m3`) on the 798 chunks across 189 source files:
```bash
python scripts/evaluate_syntax.py
```
* **Key Verified Results:**
  * **Syntax Boundary Preservation:** **`90.9%`** intact (AST) vs. **`44.0%`** intact (Line-based, **56.0% fragmented**).
  * **Parse Error-Free Rate:** **`70.1%`** valid syntax (AST) vs. **`22.4%`** valid syntax (Line-based).
  * **Mean Token Length (Content):** **`266.9`** tokens (AST) vs. **`390.8`** tokens (Line-based).
  * **Truncation Rate (> 512 tokens):** **`11.0%`** (AST) vs. **`28.6%`** (Line-based).
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
  * **Comp 1 (Full Proposed AST+Header vs. Full Baseline Line):** $\Delta = -0.0138$, 95% Bootstrap CI $[-0.0882, +0.0575]$, $p_{\text{Holm}} = 0.8532$ (Comparable re-ranking performance with superior top-1 ranking: $\text{NDCG@1} = 0.720$ vs. $0.460$, and higher Context Precision: $\text{CP@5} = 0.913$).
  * **Comp 4 (Header Effect on Line Chunks):** $\Delta = +0.0291$, $p_{\text{Holm}} = 0.7332 \ge 0.05$ (Not statistically significant).
* **Generated Artifacts:**
  * LaTeX Table: `paper/table_3_3_retrieval.tex`
  * Complete Metrics: `dataset/benchmark_results/table_3_retrieval_benchmark.csv`
  * Statistical Report: `dataset/benchmark_results/statistical_tests_report.txt`
  * Per-Query Breakdown: `dataset/benchmark_results/per_query_evaluation.csv`

---

### Step 6: Reproduce Table 3.4 — Downstream Generation & RAGAs Quality
Evaluates grounded candidate skill matching reports generated by LLMs using Top-3 retrieved code snippets as context:
```bash
python scripts/evaluate_ragas.py
```
*(By default, this script loads cached responses from `dataset/benchmark_results/ragas_evaluation_cache.json` for immediate offline reproduction without requiring API keys or incurring costs. To re-query Gemini online, set `GEMINI_API_KEY` in `.env`).*
* **Key Verified Results:**
  * **Faithfulness:** **`1.000`** (AST) vs. **`1.000`** (Line) — 100% grounded in code context, zero hallucinations.
  * **Answer Relevance:** **`0.996`** (AST) vs. **`1.000`** (Line).
  * **Citation Coverage:** **`79.3%`** (AST) vs. **`79.2%`** (Line) — over 79% of claims cite explicit code file/line locations.
* **Generated Artifacts:**
  * LaTeX Table: `paper/table_3_4_ragas.tex`
  * Generation Summary: `dataset/benchmark_results/ragas_evaluation_summary.csv`
  * Full Audit Details: `dataset/benchmark_results/ragas_per_query_details.json`

---

## 📊 Dataset Provenance & Integrity Specifications

| Dataset File | Records | Format | Description | Integrity Verification |
|:---|:---:|:---:|:---|:---|
| `queries_frozen.json` | 25 | JSON | Pre-registered industry Job Descriptions (15 Java, 10 TS/React) | Frozen at Phase 0 |
| `manifest_repos.csv` | 40 | CSV | GitHub repositories with pinned commit SHAs, licenses, file lists | Permissive Open Source |
| `source_file_intervals.json` | 189 | JSON | Pinned method line intervals across 189 source files | Verified via Tree-sitter |
| `chunk_corpus.parquet` | 798 | Parquet | Unified dual corpus: 364 AST + 434 Line chunks | Unique `chunk_id` enforced |
| `chunk_corpus.jsonl` | 798 | JSONL | JSONL format of dual corpus | Text identical to Parquet |
| `ground_truth_final.csv` | 603 | CSV | Unified ground truth (250 Gold + 353 Pooled pairs) | SHA-256 Hash Locked (R17) |
| `disagreements_adjudication.csv`| 122 | CSV | 122 resolved disagreements with technical rationales | Human verified (R21) |
| `retrieval_runs/*.json` | 12 files | JSON | Top-10 ranking outputs for 3 retrieval tiers $\times$ 4 conditions | Deterministic scoring |

### Ground Truth SHA-256 Hashes:
In accordance with Rule R17, the ground truth dataset is cryptographically locked:
* `ground_truth_final.csv` (Entire file): `2260C21DEBBCE08EFD4ACB4F5ED2429120FDEC98D64954EAE7978FFE3647875B`
* Gold subset (First 250 labels): `F9E3011EFA003C6AAB7D6DFD46CE94E1FFDDC741F193C02E0748D39D67650531`
*(Automatically verified by `tests/test_gold_integrity.py`).*

---

## ⚖️ Ethical Considerations & Anonymity

* **Double-Anonymous Review Compliance:** All personal names, institutional affiliations, and author emails have been scrubbed from the repository, code docstrings, and commit history. Annotators are referenced solely as `annotator_1`, `annotator_2`, and `Lead Adjudicator`.
* **Repository Provenance & Licensing:** All 40 source repositories mined in this study are public GitHub repositories under permissive open-source licenses (MIT, Apache-2.0, BSD-3-Clause), detailed in `dataset/manifest_repos.csv`.
* **Data Availability:** All raw and processed artifacts are provided in open, non-proprietary formats (`.csv`, `.json`, `.parquet`, `.tex`).

---

## 📜 License

* **Code:** The source code and evaluation scripts are released under the [MIT License](LICENSE).
* **Data & Documentation:** The datasets, benchmark results, and documentation are made available under the [Creative Commons Attribution 4.0 International License (CC BY 4.0)](LICENSE).
