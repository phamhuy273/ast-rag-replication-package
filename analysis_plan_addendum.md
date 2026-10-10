# Pre-Registration Analysis Plan Addendum: Exploratory Analyses

**Target Venue:** 34th IEEE International Conference on Software Analysis, Evolution and Reengineering (IEEE SANER 2027)  
**Track:** Early Research Achievements (ERA Track)  
**Governing Document:** `analysis_plan.md` (Frozen at Phase 0)  
**Protocol Status:** Pre-registered Confirmatory (Path B) + Transparent Exploratory Addendum  

---

## 1. Confirmatory vs. Exploratory Boundary

To prevent post-hoc hypothesis generation (HARKing) and p-hacking, all analyses conducted in this replication package are strictly demarcated into **Confirmatory** (governed by the frozen `analysis_plan.md`) and **Exploratory** (governed by this Addendum):

| Component | Status | Hypothesis / Purpose | Pre-registered Criteria |
|:---|:---:|:---|:---|
| **Family of 4 Retrieval Comparisons (Comp 1–4)** | **Confirmatory** | Evaluate primary 2x2 factorial retrieval effects on NDCG@10 | Paired two-sided Wilcoxon signed-rank test; Holm-Bonferroni correction ($\alpha = 0.05$); 10,000 bootstrap resamples. |
| **Inter-Annotator Agreement (Table 3.1)** | **Confirmatory** | Measure annotation reliability across 603 candidate pairs | Quadratic Weighted Cohen's $\kappa_w$, Linear $\kappa$, Landis & Koch (1977) interpretation. |
| **Corpus Syntax & Morphology (Table 3.2)** | **Confirmatory** | Compare boundary cuts, syntax errors, LOC, and token truncation | Live Tree-sitter parsing and BAAI/bge-m3 tokenizer on identical 189 source files. |
| **Comp 5 (AST+Header vs. Line+Header)** | **Exploratory** | Directly compare top-performing AST against top-performing Line | Paired Wilcoxon signed-rank test; 95% bootstrap CI. Marked strictly exploratory. |
| **AST Subgroup Disaggregation (Pure vs. Fallback)** | **Exploratory** | Unpack morphology differences between AST method chunks and line fallbacks | Transparent audit of 130 fallback chunks (35.7% of AST corpus). |
| **Language Heterogeneity (Java vs. React/TS)** | **Exploratory** | Investigate language-specific retrieval performance | Sub-cohort evaluation across 15 Java JDs and 10 React/TS JDs. |
| **Candidate Pool Random Baseline** | **Exploratory** | Establish permutation baseline within the pooled candidate set | 1,000 permutations over pooled candidates ($k=10$, seed=42). |
| **Annotator Robustness Analysis** | **Exploratory** | Assess metric stability across consensus-only and individual annotators | Re-scoring 12 retrieval runs on consensus pairs ($N=481$), Annotator 1, and Annotator 2. |
| **Downstream Generation Quality (RAGAs)** | **Exploratory** | Evaluate faithfulness and relevance on Top-3 retrieved contexts | LLM-as-a-judge with deterministic offline cache. |

---

## 2. Confirmatory Protocol Summary (Frozen)

As specified in `analysis_plan.md`:
1. **Primary Metric:** Normalized Discounted Cumulative Gain at rank 10 ($\text{NDCG@10}$).
2. **Confirmatory Family of 4 Tests:**
   - **Comp 1 (Full System vs. Full Baseline):** `rerank_ast_with_header` vs. `rerank_line_with_header` ($\Delta = -0.0428$, $p_{\text{Holm}} = 0.5420$, Not statistically significant).
     *(Note: Originally registered as `rerank_ast_with_header` vs. `rerank_line_no_header` with $\Delta = -0.0138, p_{\text{Holm}} = 0.8532$, both non-significant).*
   - **Comp 2 (Chunking Effect without Context):** `rerank_ast_no_header` vs. `rerank_line_no_header` ($\Delta = -0.1258$, $p_{\text{Holm}} = 0.0001 < 0.05$, Statistically significant penalty for isolated AST snippets).
   - **Comp 3 (Header Effect on AST):** `rerank_ast_with_header` vs. `rerank_ast_no_header` ($\Delta = +0.1120$, $p_{\text{Holm}} = 0.0031 < 0.05$, Statistically significant gain of progressive context headers).
   - **Comp 4 (Header Effect on Line):** `rerank_line_with_header` vs. `rerank_line_no_header` ($\Delta = +0.0291$, $p_{\text{Holm}} = 0.7332$, Not statistically significant).

---

## 3. Exploratory Analysis Details & Results

### 3.1 Comparison 5: AST+Header vs. Line+Header (Top-Performers)
- **Empirical Numbers:**
  - $\text{NDCG@10}(\text{AST+Header}) = 0.4566$
  - $\text{NDCG@10}(\text{Line+Header}) = 0.4994$
  - $\Delta = -0.0428$
  - 95% Bootstrap Confidence Interval (10,000 resamples): $[-0.1056, +0.0211]$ (Includes zero)
  - Wilcoxon signed-rank test: $W = 100.0, p_{\text{raw}} = 0.1355 \ge 0.05$
  - Query-level wins: Line+Header wins on 18 queries, AST+Header wins on 6 queries, 1 tie.
- **Scientific Takeaway:** The line baseline with headers is the strongest overall reranking retrieval configuration. AST+Header does not outperform Line+Header on aggregate NDCG@10, but achieves higher Top-1 precision ($\text{NDCG@1} = 0.720$ vs. $0.520$) and Context Precision ($\text{CP@5} = 0.913$ vs. $0.884$) while producing chunks with zero boundary cuts and $97.9\%$ valid syntax in pure AST mode.

### 3.2 AST Subgroup Disaggregation
- **AST Pure (N=234, 64.3%):**
  - Boundary intact: **100.0%** (0 cuts across method boundaries)
  - Parse error-free rate: **97.9%** (5 minor errors in complex generic signatures)
  - Header retention: **100.0%** (234/234 include class and method context)
  - Truncation rate (> 512 tokens): **6.0%** (14 chunks)
  - Mean LOC: **19.8** (median: 13) | Mean tokens: **211.3**
- **AST Fallback (N=130, 35.7%):**
  - Trigger: Source files lacking parseable method/function nodes (e.g. JSX return-only components, type definitions, object literal configurations).
  - Boundary intact: **74.6%** (33 cuts)
  - Parse error-free rate: **20.0%** (104 syntax errors)
  - Header retention: **0.0%** (0/130)
  - Truncation rate (> 512 tokens): **20.0%** (26 chunks)
  - Mean LOC: **42.9** (median: 50) | Mean tokens: **367.0**
- **Full Fallback Audit:** Documented line-by-line in `dataset/fallback_audit.csv`.

### 3.3 Language Heterogeneity (Java vs. React/TypeScript)
- **Java Cohort (15 JDs):**
  - AST Pure chunks represent 78.4% of Java chunks.
  - AST+Header NDCG@10 = 0.441 | Line+Header NDCG@10 = 0.478 | Delta = -0.037.
- **React/TypeScript Cohort (10 JDs):**
  - AST Fallback chunks represent 52.1% of React/TS chunks due to JSX-heavy functional components and styled-components.
  - AST+Header NDCG@10 = 0.480 | Line+Header NDCG@10 = 0.531 | Delta = -0.051.

### 3.4 Candidate Pool Random Baseline
- **Methodology:** 1,000 permutations randomly shuffling candidate items within each JD's pool, computing NDCG@10 against final ground truth.
- **Result:** Mean $\text{NDCG@10} = 0.592 \pm 0.083$.
- **Interpretation:** Because the candidate pool was pre-filtered to items retrieved by at least one retrieval tier at $k=3$ (pooling budget), the pool has high base relevance concentration. The random permutation within the pool is an exploratory diagnostic baseline, not a full-corpus random retrieval.

### 3.5 Annotator Sensitivity
- **Consensus-only Subset ($N=481$ non-disputed pairs):**
  - Re-ranking NDCG@10 rankings remain strictly invariant: Line+Header (0.508) > Line No-Header (0.478) > AST+Header (0.463) > AST No-Header (0.349).
- **Annotator 1 Only vs. Annotator 2 Only:**
  - Comp 3 (AST Header effect) remains statistically significant under both individual annotators ($p < 0.01$).

---

## 4. Reproducibility Instructions

All exploratory analyses can be dynamically executed and verified via:
```bash
python scripts/evaluate_sensitivity.py
```
Outputs are saved to `dataset/benchmark_results/sensitivity_analysis_report.txt` and `dataset/benchmark_results/sensitivity_analysis_results.json`.
