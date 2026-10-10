# Changelog & Audit Trail of Package Enhancements

**Target Venue:** 34th IEEE International Conference on Software Analysis, Evolution and Reengineering (IEEE SANER 2027)  
**Track:** Early Research Achievements (ERA Track)  
**Governing Standard:** Anti-Hardcoding Rules R1–R46 and IEEE Open Science Guidelines  

This document details all substantive enhancements and corrections applied to the replication package prior to conference submission.

---

## 1. Summary of Changes

| Identifier | Focus Area | Previous State | Enhanced / Resolved State |
|:---|:---|:---|:---|
| **A1** | Cross-Platform Hash Integrity | Raw byte SHA-256 failed on Windows `\r\n` line endings. | Implemented normalized newline hashing (`\r\n` $\to$ `\n`) in `tests/test_gold_integrity.py`. Added `.gitattributes` to lock CSV/JSON files. |
| **A2** | Double-Anonymous Review | Author names and student emails present in annotation guidelines. | Fully anonymized all guidelines and docstrings. Created automated `scripts/scan_anonymity.py` scanner verifying 0 leaked identifiers. |
| **A3** | Open Source License Audit | Unclear distribution rights across 40 crawled GitHub repos. | Built `scripts/check_licenses.py` with multi-threaded GitHub API fallback. Created unified dual `LICENSE` (MIT for code, CC-BY-4.0 for data/docs). |
| **A4** | Environment Dependency Pinning | Only high-level dependencies in `requirements.txt`. | Generated fully resolved `requirements.lock` with transitive package versions. |
| **A5** | Elimination of Silent Fallbacks | `evaluate_syntax.py` and `evaluate_ragas.py` contained fallback dummy returns. | Replaced all silent fallbacks with explicit exceptions and retries. Expanded `scripts/audit_no_hardcode.py` to 6 violation categories; verified via `tests/test_audit_detects.py`. |
| **A6** | Inter-Annotator Kappa Standard | Kappa of 0.7795 labeled "Almost Perfect" (requiring $\ge 0.81$). | Corrected to Landis & Koch (1977) "Substantial Agreement" ([0.61–0.80]) in `scripts/calculate_kappa.py`. |
| **B1** | AST Fallback Transparency | AST corpus reported as single monolithic entity (obscuring 35.7% fallback). | Generated `dataset/fallback_audit.csv` (130 items). Updated `evaluate_syntax.py` and `paper/table_3_2.tex` to disaggregate Pure (N=234) vs. Fallback (N=130). |
| **B2** | Objective Retrieval Reporting | Overstated claims ("AST outperforms line-based slicing"). | Transparently documented that Line+Header is the top retriever (NDCG@10 = 0.4994) while AST excels at Top-1 precision and syntax integrity. |
| **B3** | Pre-registration Demarcation | Exploratory analyses mixed with confirmatory tests. | Authored `analysis_plan_addendum.md` explicitly demarcating Confirmatory (Path B) vs. Exploratory findings. |
| **B4** | Sensitivity & Robustness Analysis | Missing subgroup evaluation across programming languages and annotators. | Created `scripts/evaluate_sensitivity.py` computing Java vs. React breakdown, Comp 5 stats, and annotator sensitivity. |
| **B5** | Candidate Pool Baseline | Missing baseline within pooled candidate set. | Added `random_pool_candidates` baseline (1,000 permutations, seed=42) in `scripts/evaluate_retrieval.py`. |
| **B6** | Header Bias Re-annotation Sample | Adjudication rationales partially templated; potential header visibility bias. | Sampled 50 stratified gold items into `dataset/header_bias_neutral_50_to_label.csv` for independent evaluation without context headers. |
| **B7** | One-Click Replication Runners | Reproduction required manual execution of disparate scripts. | Created unified `scripts/reproduce_all.py` (7 steps), `run_all.bat`, and `run_all.sh`. |

---

## 2. Detailed Verification Evidence

### 2.1 Cross-Platform Hash Verification (A1)
- **Problem:** Git on Windows automatically converts line endings to CRLF, altering byte-level SHA-256 hashes of `dataset/ground_truth_final.csv`.
- **Solution:** `tests/test_gold_integrity.py` was refactored to compute SHA-256 over normalized newlines:
  ```python
  normalized_bytes = raw_bytes.replace(b"\r\n", b"\n")
  ```
  Locked normalized hash: `70C01F773136F7D0352012B7D1F1DD9DB216708848C5A54E22A661DFD93DBB4D`.
  A `.gitattributes` file was created with `*.csv -text` and `*.json -text` to enforce exact line endings across OS clones.

### 2.2 Anonymity Assurance (A2)
- **Scanned Patterns:** Author names, institutional student email domains, local Windows/macOS user paths, and hardware IDs.
- **Verification Script:** `scripts/scan_anonymity.py` scans all text files, PNG metadata, and Parquet data tables. Current scan result: **0 violations detected**.

### 2.3 Strict Anti-Hardcoding Governance (A5)
- **Auditor Implementation:** `scripts/audit_no_hardcode.py` performs AST visits and regex scanning over `scripts/` and `ai-engine/` for:
  1. Hardcoded benchmark floating-point literals.
  2. Silent exception catching (`except: pass`, `except Exception: return {}`).
  3. Precomputed constant return dictionaries.
  4. Non-deterministic random calls without explicit seeds.
- **Auditor Test Suite:** `tests/test_audit_detects.py` contains 7 automated tests asserting that the auditor reliably flags violations when injected into temporary code files. Current production code status: **0 violations**.

### 2.4 AST Fallback Decomposition & Table 3.2 (B1)
- Empirical investigation of the 364 AST chunks revealed that 130 chunks (35.7%) fell back to 50-LOC window slicing because the target files lacked extractable function/method nodes (e.g., top-level JSX renders in React, styled-components, interface declarations, and configuration objects).
- All 130 chunks were categorized and diagnosed in `dataset/fallback_audit.csv`.
- Table 3.2 was updated to present 4 clear columns:
  - **Line-based (50 LOC):** $N=434$, LOC $41.0 \pm 13.1$, Boundary Intact $44.0\%$, Parse Intact $22.4\%$, Truncated $28.6\%$.
  - **AST Pure (Ours):** $N=234$, LOC $19.8 \pm 16.7$, Boundary Intact $\mathbf{100.0\%}$, Parse Intact $\mathbf{97.9\%}$, Truncated $\mathbf{6.0\%}$.
  - **AST Fallback:** $N=130$, LOC $42.9 \pm 13.0$, Boundary Intact $74.6\%$, Parse Intact $20.0\%$, Truncated $20.0\%$.
  - **AST Combined:** $N=364$, LOC $28.1 \pm 19.0$, Boundary Intact $90.9\%$, Parse Intact $70.1\%$, Truncated $11.0\%$.

### 2.5 Statistical Rigor & Scientific Honesty (B2, B3, B4)
- **Top Retrieval System:** We truthfully state that Line+Header is the empirical top performer on NDCG@10 (0.4994).
- **Comparison 5 (Exploratory):** AST+Header vs. Line+Header yields $\Delta = -0.0428$, 95% Bootstrap CI $[-0.1056, +0.0211]$, $W = 100.0, p = 0.1355$.
- **AST Advantages:** AST Progressive Disclosure provides higher Top-1 precision ($\text{NDCG@1} = 0.720$ vs. $0.520$), higher Context Precision ($\text{CP@5} = 0.913$ vs. $0.884$), and produces zero boundary cuts in pure AST mode.
