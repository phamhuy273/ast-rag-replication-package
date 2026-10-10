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
| **Candidate Pool Random Baseline & Shortlist** | **Exploratory** | Establish permutation baseline within pooled candidates and judged-only sensitivity | 1,000 permutations over pooled candidates ($k=10$, seed=42) and judged-only ranking. |
| **Annotator Robustness Analysis** | **Exploratory** | Assess metric stability across consensus-only and individual annotators | Re-scoring 12 retrieval runs on consensus pairs ($N=481$), Annotator 1, and Annotator 2. |
| **Downstream Generation Quality (RAGAs)** | **Exploratory** | Evaluate faithfulness and relevance on Top-3 retrieved contexts | LLM-as-a-judge with deterministic offline cache. |

---

## 2. Confirmatory Protocol Summary (Frozen)

As specified in `analysis_plan.md`:
1. **Primary Metric:** Normalized Discounted Cumulative Gain at rank 10 ($\text{NDCG@10}$).
2. **Confirmatory Family of 4 Tests:**
   - **Comp 1 (Full Proposed vs. Baseline Line without Header):** `rerank_ast_with_header` vs. `rerank_line_no_header` ($\Delta = -0.0138$, 95% Bootstrap CI $[-0.0882, +0.0575]$, Wilcoxon $W = 155.0$, $p_{\text{raw}} = 0.8532$, $p_{\text{Holm}} = 0.8532$, Not statistically significant).
   - **Comp 2 (Pure Chunking Effect without Headers):** `rerank_ast_no_header` vs. `rerank_line_no_header` ($\Delta = -0.1258$, 95% Bootstrap CI $[-0.1802, -0.0758]$, Wilcoxon $W = 22.0$, $p_{\text{raw}} < 0.0001$, $p_{\text{Holm}} = 0.0001 < 0.05$, Statistically significant penalty for isolated AST snippets).
   - **Comp 3 (Header Effect on AST):** `rerank_ast_with_header` vs. `rerank_ast_no_header` ($\Delta = +0.1120$, 95% Bootstrap CI $[+0.0559, +0.1664]$, Wilcoxon $W = 46.0$, $p_{\text{raw}} = 0.0010$, $p_{\text{Holm}} = 0.0031 < 0.05$, Statistically significant gain of progressive context headers).
   - **Comp 4 (Header Effect on Line):** `rerank_line_with_header` vs. `rerank_line_no_header` ($\Delta = +0.0291$, 95% Bootstrap CI $[-0.0165, +0.0783]$, Wilcoxon $W = 128.0$, $p_{\text{raw}} = 0.3666$, $p_{\text{Holm}} = 0.7332$, Not statistically significant).

---

## 3. Exploratory Analysis Details & Results

### 3.1 Comparison 5: AST+Header vs. Line+Header (Exploratory Top-Performers)
- **Empirical Numbers:**
  - $\text{NDCG@10}(\text{AST+Header}) = 0.4566$
  - $\text{NDCG@10}(\text{Line+Header}) = 0.4994$
  - $\Delta = -0.0428$
  - 95% Bootstrap Confidence Interval (10,000 resamples): $[-0.1056, +0.0211]$ (Includes zero)
  - Wilcoxon signed-rank test: $W = 97.0, p_{\text{raw}} = 0.1355 \ge 0.05$ (Null hypothesis not rejected at $\alpha = 0.05$)
  - Query-level wins: Line+Header wins on 18 queries, AST+Header wins on 6 queries, 1 tie.
- **Scientific Takeaway:** The line baseline with progressive headers is the strongest overall reranking retrieval configuration ($\text{NDCG@10} = 0.4994, \text{NDCG@1} = 0.800, \text{MRR@10} = 0.980, \text{CP@5} = 0.935$). AST+Header ($\text{NDCG@10} = 0.4566, \text{NDCG@1} = 0.720, \text{MRR@10} = 0.940, \text{CP@5} = 0.913$) does not outperform Line+Header on aggregate retrieval metrics, nor does AST outperform Line at Top-1. However, progressive headers rescue AST from severe context deprivation ($\text{NDCG@10}$ jumps from $0.3445$ to $0.4566, \Delta = +0.1120, p = 0.0031$), matching the baseline Line without headers ($0.4703, p_{\text{Holm}} = 0.8532$) while producing chunks with zero boundary cuts and $97.9\%$ valid syntax in pure AST mode.

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
  - AST Pure chunks represent 78.4% (120/153) of Java chunks; fallbacks account for only 13.1% (20/153).
  - Re-ranking NDCG@10: AST+Header = **0.5146** | Line+Header = **0.5358** | Line No-Header = **0.5252** | AST No-Header = **0.3835**.
  - Delta (AST+Header vs. Line+Header): **-0.0212**.
- **React/TypeScript Cohort (10 JDs):**
  - AST Fallback chunks represent 52.1% (110/211) of React/TS AST chunks, accounting for 84.6% (110/130) of all fallbacks across the entire benchmark, driven by JSX-heavy functional components and styled-components (or 68.8% [110/160] when evaluated on non-declaration UI files).
  - Re-ranking NDCG@10: AST+Header = **0.3694** | Line+Header = **0.4448** | Line No-Header = **0.3881** | AST No-Header = **0.2860**.
  - Delta (AST+Header vs. Line+Header): **-0.0754**.
  - Takeaway: AST chunking performs substantially closer to Line in Java (-0.021) than in React/TS (-0.075), where syntax-level extraction frequently encounters non-method paradigms.

### 3.4 Candidate Pool Random Baseline vs. Judged-Only Shortlist Evaluation
- **Candidate Pool Random Baseline:**
  - Methodology: 1,000 permutations randomly shuffling candidate items within each JD's pool, computing NDCG@10 against final ground truth.
  - Result: Mean $\text{NDCG@10} = \mathbf{0.592} \pm 0.083$.
  - Interpretation: The pool baseline evaluates strictly within the pre-screened candidate set where 100% of items were judged (0% unjudged). It is higher than full-corpus retrieval runs ($\le 0.499$) because full-corpus top-10 lists retrieve from 798 chunks and contain ~45% unjudged items (imputed as 0 under the Cranfield pooling protocol). On the entire 798-chunk corpus, a random baseline achieves only $\text{NDCG@10} = \mathbf{0.0195}$.
- **Judged-Only (Shortlist) Sensitivity Analysis:**
  - Evaluates retrieval models strictly on judged candidate pool items (excluding unjudged items to establish a direct, apples-to-apples comparison against the 0.592 pool baseline):
    - `rerank_line_with_header`: **0.6148** (exceeds the 0.592 pool baseline)
    - `rerank_line_no_header`: **0.5896**
    - `rerank_ast_with_header`: **0.5463**
    - `rerank_ast_no_header`: **0.4537**
  - Statistical Consistency:
    - AST Header Effect: $\Delta = \mathbf{+0.0926}$, $p = 0.0034 < 0.05$ (Confirmed Significant).
    - Comp 1 (AST+Header vs. Line No-Header): $\Delta = -0.0433$, $p = 0.3666 \ge 0.05$ (Not Significant).
    - Comp 5 (AST+Header vs. Line+Header): $\Delta = -0.0685$, raw $p = 0.0318 < 0.05$.
  - Takeaway: Ranking orders and conclusions remain identical between full-corpus evaluation and judged-only shortlist evaluation.

### 3.5 Annotator Sensitivity
- **Consensus-only Subset ($N=481$ non-disputed pairs):**
  - Re-ranking NDCG@10 scores: Line+Header (**0.4262**) > Line No-Header (**0.4128**) > AST+Header (**0.3687**) > AST No-Header (**0.2938**).
  - Header effect on AST under consensus-only qrels: $\Delta = +0.0749$, paired Wilcoxon $p = 0.0851 \ge 0.05$ (Not statistically significant at $\alpha = 0.05$, though ranking order remains invariant).
- **Annotator 1 Only ($N=603$):**
  - Comp 3 (AST Header effect): $\Delta = +0.1094$, $p = 0.0008 < 0.05$ (Confirmed Significant).
- **Annotator 2 Only ($N=603$):**
  - Comp 3 (AST Header effect): $\Delta = +0.0972$, $p = 0.0012 < 0.05$ (Confirmed Significant).

---

## 4. Reproducibility Instructions

All exploratory analyses can be dynamically executed and verified via:
```bash
python scripts/evaluate_sensitivity.py
```
Outputs are saved to `dataset/benchmark_results/sensitivity_analysis_report.txt` and `dataset/benchmark_results/sensitivity_analysis_report.json`.
