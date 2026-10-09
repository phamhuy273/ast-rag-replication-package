# Replication Package: AST-Based Progressive Disclosure Chunking and Two-Stage Retrieval for Candidate Skill Matching

> **Target Publication:** 34th IEEE International Conference on Software Analysis, Evolution and Reengineering (IEEE SANER 2027)  
> **Track:** Early Research Achievements (ERA Track)  
> **Review Policy:** Double-Anonymous Peer Review  

---

## 📌 Overview

This replication package contains all curated datasets, evaluation scripts, precomputed embedding representations, and generation caches to reproduce all empirical findings reported in our paper.

### Research Questions & Key Contributions:
* **RQ1 (Syntactic & Structural Integrity):** How does AST Progressive Disclosure chunking compare to traditional fixed-window line slicing in preserving syntactic validity and context anchors across real-world repositories? (**Table 3.2**)
* **RQ2 (Two-Stage Retrieval Performance):** How effectively does the two-stage retrieval pipeline (Bi-Encoder BGE-M3 + Cross-Encoder BGE-Reranker-Base) retrieve and rank candidate evidence compared to lexical BM25 and single-stage baselines? (**Table 3.3 & Table II**)
* **RQ3 (Generation Groundedness & Faithfulness):** How does hierarchical AST context enrichment affect hallucination prevention and evidence citation coverage in RAG generation? (**Table 3.4**)

---

## 📁 Repository Structure

```text
.
├── dataset/
│   ├── ground_truth_final.csv             # 250 Gold-Standard pairs (double-annotated, adjudicated)
│   ├── ground_truth_500_master.csv        # 500 candidate pairs across 50 GitHub repositories
│   ├── ground_truth_annotator1_labeled.csv# Independent annotations by Annotator 1
│   ├── ground_truth_annotator2_labeled.csv# Independent annotations by Annotator 2
│   ├── disagreements_adjudication.csv     # 19 adjudicated disagreement cases with technical rationales
│   ├── extracted_jd_skills.json           # 25 curated industry Job Descriptions with extracted skills
│   ├── repositories_list/                 # Curated metadata for 50 GitHub repositories (25 Java, 25 TS)
│   ├── jd_raw/                            # Raw text of 25 Job Descriptions
│   ├── embeddings_ast_bgem3.npy           # Precomputed BGE-M3 embeddings for AST chunks (1024-dim)
│   ├── embeddings_line_bgem3.npy          # Precomputed BGE-M3 embeddings for Line-based chunks
│   ├── embeddings_jd_bgem3.npy            # Precomputed BGE-M3 embeddings for 25 JD queries
│   ├── reranker_scores_cache.npy          # Cached BGE-Reranker-Base cross-attention scores
│   └── benchmark_results/                 # Precomputed benchmark logs and visualization plots
├── scripts/
│   ├── calculate_kappa.py                 # Evaluates inter-annotator agreement (Table 3.1)
│   ├── benchmark_chunking_corpus.py       # Computes corpus structural characteristics (Table 3.2)
│   ├── evaluate_retrieval_benchmarks.py   # Computes Stage 1 IR retrieval metrics (Table 3.3)
│   ├── benchmark_reranker.py              # Computes Stage 2 Re-ranking & Wilcoxon tests (Table II)
│   ├── evaluate_rag_generation.py         # Evaluates RAGAs generation metrics (Table 3.4)
│   └── prepare_candidate_chunks.py       # Tree-sitter AST extraction pipeline
├── requirements.txt                       # Python dependencies
└── README.md                              # Replication guide
```

### 📊 Dataset Organization: Gold-Standard Benchmark vs. Full Corpus

To ensure absolute methodological transparency, we provide both the full mined corpus and the rigorously verified evaluation benchmark:

1. **`ground_truth_final.csv` (250 pairs — Primary Gold-Standard Benchmark):**
   * **Purpose:** Serves as the official evaluation benchmark for all Information Retrieval experiments (**Table 3.3, Table II**) and RAG generation evaluations (**Table 3.4**).
   * **Protocol:** Contains $25 \text{ JDs} \times 10 \text{ retrieved candidate chunks}$. Each candidate evidence chunk underwent strict **Double-Blind Independent Annotation** by two software engineers, achieving an inter-annotator agreement of **$\kappa_w = 0.8808$** (Almost Perfect), with all 19 disagreements adjudicated transparently in `disagreements_adjudication.csv`.

2. **`ground_truth_500_master.csv` (500 pairs — Extended Full Corpus):**
   * **Purpose:** Encompasses all 500 candidate chunks mined across the 50 curated GitHub repositories ($25 \text{ JDs} \times 20 \text{ chunks}$).
   * **Protocol:** Used specifically for the structural and syntactic chunking analysis in **Table 3.2** (measuring the 100% syntax validity rate vs. 31.6% in line-based chunking, context header preservation, and token compression).
   * *Note:* The 250 gold-standard evaluation pairs form a strict subset of this 500-sample corpus.

---

## 🚀 Quick Start & Environment Setup

### 1. Prerequisites
* Python 3.10 or higher.
* Compatible with Windows, Linux, and macOS.

### 2. Installation
```bash
# Clone the repository (or extract the downloaded ZIP archive)
git clone <anonymous-repository-url>
cd ast-rag-replication-package

# Install required dependencies
pip install -r requirements.txt
```

---

## 🔬 One-Click Reproduction Guide

All experimental tables in the paper can be reproduced immediately using the provided evaluation scripts:

### Step 1: Inter-Annotator Agreement (Table 3.1)
Calculates Quadratic Weighted Cohen's Kappa ($\kappa_w$) across the 250 double-blind candidate pairs:
```bash
python scripts/calculate_kappa.py
```
* **Expected Output:** Quadratic Weighted $\kappa_w = 0.8808$ (Almost Perfect agreement, Landis & Koch 1977), Exact consensus $P_o = 88.40\%$. Generates `confusion_matrix_kappa.png`.

### Step 2: Code Chunking Corpus Benchmark (Table 3.2)
Analyzes syntactic validity and context retention on 500 chunks across 50 repositories:
```bash
python scripts/benchmark_chunking_corpus.py
```
* **Expected Output:** AST chunking achieves **100.0%** syntax boundary preservation vs **31.6%** for line-based (68.4% broken), 100% context header preservation, and -19.6% token bloat reduction.

### Step 3: First-Stage Code Retrieval Benchmark (Table 3.3)
Evaluates dense Bi-Encoder (BGE-M3) and sparse lexical (BM25Okapi) retrieval across 25 JDs:
```bash
python scripts/evaluate_retrieval_benchmarks.py
```
* **Expected Output:** AST achieves NDCG@5 = 0.7913 (+25.4% over BM25, $p < 0.001$), winning in 14 of 25 JDs against line-based dense retrieval (NDCG@5 = 0.7747).

### Step 4: Two-Stage Re-ranking Performance (Table II)
Evaluates cross-attention re-ranking via BAAI/bge-reranker-base and performs Paired Wilcoxon Signed-Rank tests:
```bash
python scripts/benchmark_reranker.py
```
* **Expected Output:** AST NDCG@1 surges from **0.6200 to 0.8800 (+41.9%)** with $p = 0.000395 < 0.001$, MRR reaches **1.0000**. Line-based baseline plateaus at 0.6800.

### Step 5: RAG Generation Quality via RAGAs (Table 3.4)
Evaluates Faithfulness, Citation Coverage, and Answer Relevance:
```bash
python scripts/evaluate_rag_generation.py
```
* **Expected Output:** AST achieves Faithfulness = **0.9932** (exceeding the $\ge 0.85$ acceptance threshold) and Citation Coverage = **75.12%** (outperforming line-based 74.40%).

---

## 🔒 Anonymity Notice

In compliance with the IEEE SANER 2027 Double-Anonymous review guidelines:
* All author identities, affiliations, and institutional references have been removed.
* Repository commit history is anonymized.
* Contact information will be reinstated upon publication.
