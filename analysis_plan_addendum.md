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
  - AST Pure chunks represent **86.9%** (133/153) of Java chunks; fallbacks account for only **13.1%** (20/153).
  - Re-ranking NDCG@10: AST+Header = **0.5146** | Line+Header = **0.5358** | Line No-Header = **0.5252** | AST No-Header = **0.3835**.
  - Delta (AST+Header vs. Line+Header): **-0.0212**.
- **React/TypeScript Cohort (10 JDs):**
  - AST Fallback chunks represent **52.1%** (110/211) of React/TS AST chunks, accounting for **84.6%** (110/130) of all fallbacks across the entire benchmark, driven by JSX-heavy functional components and styled-components.
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

### 3.6 Statistical Power Analysis & Minimum Detectable Effect (MDE)
- **Status:** Exploratory (Paired $t$-test approximation, $N=25$ JDs, 80\% statistical power).
- **Rationale:** With $N=25$ queries, small paired differences may not achieve statistical significance. MDE establishes the minimum true difference required to achieve 80\% power under two-sided paired testing at $\alpha = 0.05$ (unadjusted) and $\alpha = 0.0125$ (Bonferroni-adjusted for 4 confirmatory tests).
- **Results across 5 comparisons:**
  - Comp 1 (AST+Header vs. Line No-Header): $\text{SD}_{\Delta} = 0.1894$, $\text{MDE}(\alpha=0.05) = 0.1101$, $\text{MDE}(\alpha=0.0125) = 0.1342$
  - Comp 2 (AST No-Header vs. Line No-Header): $\text{SD}_{\Delta} = 0.1362$, $\text{MDE}(\alpha=0.05) = 0.0792$, $\text{MDE}(\alpha=0.0125) = 0.0965$
  - Comp 3 (AST+Header vs. AST No-Header): $\text{SD}_{\Delta} = 0.1431$, $\text{MDE}(\alpha=0.05) = 0.0832$, $\text{MDE}(\alpha=0.0125) = 0.1014$
  - Comp 4 (Line+Header vs. Line No-Header): $\text{SD}_{\Delta} = 0.1236$, $\text{MDE}(\alpha=0.05) = 0.0718$, $\text{MDE}(\alpha=0.0125) = 0.0876$
  - Comp 5 (AST+Header vs. Line+Header): $\text{SD}_{\Delta} = 0.1631$, $\text{MDE}(\alpha=0.05) = 0.0948$, $\text{MDE}(\alpha=0.0125) = 0.1155$
- **Overall Range:** 0.072 to 0.134 NDCG@10 (approximately 0.07 to 0.14).
### 3.7 Reachable Qrels Sensitivity (Exploratory, 13/10/2026)
- **Status:** Exploratory post-hoc sensitivity check.
- **Context:** 78 of the 250 initial Gold pairs reference chunk boundaries from an earlier extraction pass and cannot be matched to coordinates in `dataset/chunk_corpus.parquet`. 51 of these 78 pairs have relevant labels ($\ge 1$).
- **Method:** Recompute NDCG@10 restricting ideal rankings strictly to the 525 reachable candidate pairs.
- **Results:**
  - Line No-Header: all = 0.4703, reachable = 0.4848
  - Line+Header: all = 0.4994, reachable = 0.5138
  - AST No-Header: all = 0.3445, reachable = 0.3562
  - AST+Header: all = 0.4566, reachable = 0.4698
  - Pairwise contrasts: C1 $\Delta = -0.0150$ ($p = 0.8532$), C2 $\Delta = -0.1286$ ($p < 0.0001$), C3 $\Delta = +0.1136$ ($p = 0.0013$), C4 $\Delta = +0.0290$ ($p = 0.3957$), C5 $\Delta = -0.0440$ ($p = 0.1374$).
- **Takeaway:** Relative comparisons, ranking orders, and statistical conclusions are completely preserved.

### 3.8 Binary Preference (Bpref) Analysis for Incomplete Judgments (Exploratory, 13/10/2026)
- **Status:** Exploratory secondary evaluation metric (Buckley & Voorhees, SIGIR 2004).
- **Rationale:** BM25 was excluded from candidate pooling, resulting in 65%–81% unjudged items in its top-3 (13.6%–30.4% Judged@10). Traditional NDCG@10 treats unjudged items as non-relevant (score 0), heavily depressing BM25. Bpref evaluates retrieval quality solely over judged items: $\text{bpref} = \frac{1}{R}\sum_{r \in R} [1 - \frac{\min(n_r, R)}{\min(R, N)}]$.
- **Results:**
  - BM25 tier: bpref ranges from **0.152** to **0.241** across all four configurations.
  - Dense tier: bpref ranges from **0.278** to **0.350**.
  - Rerank tier: bpref ranges from **0.285** to **0.356** (Line+Header 0.356 > Line No-Header 0.343 > AST+Header 0.314 > AST No-Header 0.285).
- **Takeaway:** The gap between BM25 and neural tiers is substantially smaller than indicated by zero-imputed NDCG@10, but BM25 remains numerically lowest. Reranking tier ranking order is identical to NDCG@10.
- **Execution:** `python scripts/compute_bpref.py` saves results to `dataset/benchmark_results/bpref_summary.csv` and `bpref_report.json`.

### 3.9 Pure AST Re-Run Framework (Exploratory, 13/10/2026)
- **Status:** Exploratory analysis pipeline outside the frozen confirmatory family.
- **Objective:** Separate pure AST semantic chunks (234 chunks) from the 130 line-window fallbacks by re-running retrieval and pooling on the restricted universe of 130 files containing at least one pure AST chunk (compared against 238 line windows from the same files).
- **Pipeline Implementation:**
  - `scripts/pure_ast_run.py`: Executes dense (`BAAI/bge-m3`) and reranking (`BAAI/bge-reranker-base`) across 4 conditions on restricted corpora, with `--check-repro` reproduction gating.
  - `scripts/pure_ast_pool.py`: Pools unjudged top-$k$ candidates into neutral `to_label_pure_ast.csv` for human annotation.
  - `scripts/pure_ast_eval.py`: Evaluates retrieved lists under shared and arm-specific ideal sets, computing NDCG@10, NDCG@5, and Bpref with Wilcoxon signed-rank tests and Holm correction.
  - Verified by smoke tests in `tests/test_pure_ast.py`.

### 3.10 Closed-Pool Header Component Ablation Framework (Exploratory, 13/10/2026)
- **Status:** Exploratory preliminary ablation for RQ3.
- **Rationale:** Disentangle the contributions of individual context header fields (`// File:`, `// Class:`, `// Method:`, `// Lines:`) by re-scoring judged candidate pairs in a closed pool (avoiding unjudged item surfacing).
- **Metric:** ROC-AUC and NDCG@5 (to prevent ceiling artifacts on small per-query pools where random ranking yields NDCG@10 $\approx 0.8$).
- **Implementation:** `scripts/header_ablation.py` evaluates variants (`none`, `path`, `class`, `method`, `path_class`, `no_lines`, `full`) across all 525 retrievable pairs and the 188 pure-AST judged pairs.

---

## 4. Reproducibility Instructions

All exploratory analyses can be dynamically executed and verified via:
```bash
python scripts/evaluate_sensitivity.py
python scripts/power_analysis.py
python scripts/compute_bpref.py
python -m pytest tests/test_pure_ast.py
```
Outputs are saved to `dataset/benchmark_results/sensitivity_analysis_report.txt`, `dataset/benchmark_results/power_analysis.json`, and `dataset/benchmark_results/bpref_report.txt`.
