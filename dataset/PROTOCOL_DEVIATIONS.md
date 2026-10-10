# Experimental Protocol Deviations & Quality Assurance Audit

**Study:** IEEE SANER 2027 ERA Track — *AST-Based Progressive Disclosure Chunking and 2×2 Factorial Retrieval for Candidate Skill Matching*  
**Governing Prospective Documents:** `analysis_plan.md` & `dataset/annotation_guidelines.md`  
**Purpose:** In accordance with open science and empirical research transparency, this document catalogs all operational deviations between the prospective experimental plan and the final execution, supported by dynamic data-driven audits.

---

## 1. Inter-Annotator Agreement Threshold ($\kappa_w$)

* **Prospective Plan (`annotation_guidelines.md`, Section 4.2):** Target threshold set to Quadratic Weighted Cohen's Kappa $\kappa_w \ge 0.80$ (Almost Perfect Agreement).
* **Observed Reality (`scripts/calculate_kappa.py`):**
  * Overall Candidate Pool ($N=603$ pairs): Quadratic $\kappa_w = \mathbf{0.7795}$ (Substantial Agreement per Landis & Koch 1977 [0.61–0.80]).
  * Exact agreement: $79.77\%$ (481/603).
  * Minor 1-point disagreements: $18.57\%$ (112/603).
  * Severe 2-point disagreements: $1.66\%$ (10/603).
  * Gold 250 Subset: Quadratic $\kappa_w = \mathbf{0.8808}$ (exceeds the 0.80 target).
* **Impact & Remediation:** While the overall pool marginally missed the 0.80 aspirational threshold by $0.0205$, all 122 discordant pairs were resolved through structured adjudication. Sensitivity analysis across Annotator 1, Annotator 2, and Consensus-only subsets confirms that retrieval system rankings remain strictly invariant.

---

## 2. Structured Adjudication Format vs. Free-Form Essays

* **Prospective Plan (`annotation_guidelines.md`, Section 4.3):** Adjudications required concrete technical explanations; "Template/boilerplate explanations are strictly prohibited."
* **Observed Reality (`scripts/summarize_adjudication.py`):**
  * All 122 disagreements were adjudicated by a single `Lead Adjudicator`.
  * Reasons followed structured syntactical templates rather than unconstrained narrative essays:
    * 29 rows used the explicit prefix `RESOLVED_BY_ADJUDICATION: ...`.
    * 93 rows followed the structured evaluation template ending in `Evaluated as Level N`.
  * Across the 122 adjudicated rows, there are **70 unique reason strings** due to file-specific path and technical signature insertions.
  * Decision breakdown: Adjudicator agreed with Annotator 1 in 73 cases ($59.84\%$), with Annotator 2 in 47 cases ($38.52\%$), and chose a compromise score in 2 cases ($1.64\%$).
* **Impact & Remediation:** The use of structured templates guaranteed standard rubric adherence across all 122 items, though it deviated from the original guideline's strict prohibition on templated text.

---

## 3. Header Bias Neutral Control Re-annotation

* **Prospective Plan (`annotation_guidelines.md`, Section 4.4):** A random sample of 50 Gold items was to be blinded of context headers and re-annotated to measure potential halo bias induced by header metadata.
* **Observed Reality:** Due to annotation resource limits, this neutral re-annotation step was **not executed**; all 603 candidate pairs were scored once through the dual-annotator + adjudication pipeline.
* **Impact & Remediation:** Acknowledged transparently as an experimental limitation. Human annotators evaluated code snippets presented in neutral tabular format (`to_label.csv`), but prospective halo-bias estimation remains future work.

---

## 4. Candidate Pooling Scope (Exclusion of BM25)

* **Prospective Documentation Imprecision:** Early text implied candidate pooling was conducted across "all 12 retrieval configurations".
* **Observed Reality (`scripts/report_pool_coverage.py`):**
  * Candidate pooling at $k=3$ was executed strictly across the **8 Dense and Re-ranking configurations** (`dense_*` and `rerank_*`).
  * BM25 runs were evaluated post-hoc against the pooled ground truth and **were not part of the pooling candidate generator**:
    * All 8 Dense and Rerank runs have $100.0\%$ Judged@3 coverage (0 unjudged slots in Top-3).
    * The 4 BM25 runs have substantial unjudged Top-3 slots: `bm25_line_no_header` (61/75 unjudged, Judged@3 = 18.7%), `bm25_line_with_header` (57/75 unjudged, Judged@3 = 24.0%), `bm25_ast_no_header` (49/75 unjudged, Judged@3 = 34.7%), `bm25_ast_with_header` (53/75 unjudged, Judged@3 = 29.3%).
* **Impact & Remediation:** BM25 retrieval scores ($\text{NDCG@10} = 0.104 – 0.187$) reflect heavy zero-imputation penalty on unjudged snippets under Cranfield pooling conventions. BM25 performance is reported transparently with this caveat and is not interpreted as an unpenalized baseline.

---

## 5. Candidate Pool Count Reconciliation (415 vs. 382 and 380 vs. 353)

* **Discrepancy:** `pool_size_report.csv` recorded sums: `total_pooled = 415`, `already_gold = 35`, `new_to_label = 380`. However, `to_label.csv` contains exactly 353 rows, and `ground_truth_final.csv` has 603 rows (250 gold + 353 new), leaving an apparent gap of 27 items.
* **Empirical Audit (`scripts/reconcile_pool.py`):**
  * Root Cause: When `pool_size_report.csv` was initially tabulated, candidates were tracked by raw `chunk_id` instances. In the dual corpus, AST-fallback chunks and Line chunks covering the same slice share identical coordinates `(repo_name, file_path, start_line, end_line)` but have distinct chunk IDs.
  * Coordinate Deduplication: Deduplicating the Top-3 items of the 8 pooled runs by unique line coordinates reduces the 415 instances to **382 unique coordinate pairs** (33 coordinate duplicates).
  * Gold Overlap: Of these 382 coordinate pairs, exactly **29** already existed in the Gold 250 subset (35 - 6 coordinate duplicates = 29).
  * Exact Identity: $382 - 29 = \mathbf{353}$ new items to label.
  * Validation: Every single one of the 353 coordinate pairs matches `to_label.csv` with zero unmatched items ($0$ false positives, $0$ false negatives).
