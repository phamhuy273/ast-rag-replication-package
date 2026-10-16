# CHANGES.md: Detailed Audit of Modifications to SANER 2027 ERA Manuscript

**Date:** 2026-10-12  
**Target Venue:** 34th IEEE International Conference on Software Analysis, Evolution and Reengineering (SANER 2027)  
**Track:** Early Research Achievements (ERA Track) — Research Preview  
**Governing Documents:** Guidelines for AI-Generated Text, ERA Call for Papers, and Revision Directive v1.0.

---

## 1. Title, Abstract, and Index Terms

### Title
* **Before:** `Does Structure or Context Matter More? Chunking and Context Headers for Retrieving Requirement Evidence from Source Code`
* **After:** `An Empirical Evaluation of Source Code Chunking and Context Headers for Requirement Evidence Retrieval`

### Abstract
* **Before:** Speculative opening ("Prior work assumes..."), omitted statistically significant Comp 2 ($p=0.0001$), lacked explicit mention of sample size power constraint ($n=25$).
* **After:** Exactly replaced with audited 198-word abstract stating:
  - Context & Motivation: Locating code evidencing technical requirements.
  - Factorial $2 \times 2$ conditions over 25 JDs and 40 repositories (798 chunks).
  - Explicit metrics: Comp 3 ($\Delta = +0.112$, $p_{\mathrm{Holm}} = 0.0031$), Comp 2 ($\Delta = -0.126$, $p_{\mathrm{Holm}} = 0.0001$), Comp 1 ($\Delta = -0.014$, $p_{\mathrm{Holm}} = 0.85$), and Line+Header highest numerical score ($0.499$).
  - Explicit limitations: 35.7% AST fallback and $N=25$ query power limit.

### Index Terms
* **Before:** `Source code retrieval, Code chunking, Abstract syntax tree, Requirements traceability, Retrieval-augmented generation`
* **After:** `Source code retrieval, code chunking, abstract syntax trees, context headers, requirements traceability, empirical software engineering` (Dropped "Retrieval-augmented generation" as text generation is not evaluated).

---

## 2. Section I: Introduction

* **Paragraph 1:**
  - *Before:* Generic motivation framing candidate evaluation and automated credential verification.
  - *After:* Anchored firmly in software analysis and requirements traceability literature (Antoniol et al. [1], Gao et al. [15], Kuang et al. [16]).
* **Paragraph 2 (RAG & Code Chunking):**
  - *Before:* Speculative assertion that "In literature, it is widely assumed that syntax-aware chunking is inherently superior..."
  - *After:* Cited recent empirical counter-evidence from code completion (Wu et al. [5]) and compute-budget RAG (Galimzyanov et al. [N1]), highlighting the confound between chunk boundaries and hierarchical context headers.
* **Research Questions:**
  - *Before (RQ2):* "...when context header metadata is strictly controlled?"
  - *After (RQ2):* "...when both conditions use, or both omit, context headers?"
* **Contributions:**
  - *Before:* Claimed "pre-registered gold subset" and uncalibrated metrics.
  - *After:* Updated with exact quadratic weighted kappa values ($\kappa_w = 0.78$ overall, $0.88$ gold, $0.68$ new pooled) and audited fallback proportion ($35.7\%$).
* **Closing Sentence:**
  - *Before:* "This work directly contributes to SANER's focus on software analysis, repository mining, and program comprehension."
  - *After:* "The study relates to SANER topics on software analysis, mining software repositories, and program comprehension."

---

## 3. Section II: Related Work

* **Structure:** Completely rewritten into four balanced subsections adhering strictly to Guideline Section 2.3:
  1. *Code Chunking for Retrieval-Augmented Generation:* Contrast with cAST (Zhang et al. [4]), Wu et al. [5], and Galimzyanov et al. [N1].
  2. *Dense Code Retrieval and Reranking:* Added two-stage code search literature (Hu et al. [N2] TOSS, Liu et al. [11] CoSTV) alongside BGE-M3 [9] and BGE-Reranker [10].
  3. *Context Enrichment:* Focused on repository completion (RepoCoder [12], RepoBench [13], CrossCodeEval [14]) vs. short hierarchical headers.
  4. *Requirements Traceability and Skill Mining:* Tracing requirements (Antoniol [1], Gao [15], Kuang [16]) and developer expertise mining (Montandon et al. [2], corrected to MSR 2019). Explicitly affirmed: "We do not assess individual developers."

---

## 4. Section III: Approach and Study Design

* **Query Extraction Model:** Corrected from speculative "GPT-4o" to actual audited model: `gemini-1.5-flash` as frozen in `queries_frozen.json`.
* **Reranker Model:** Clarified model variant as `BAAI/bge-reranker-base` [10], consistent with `analysis_plan.md` and PROVENANCE logs.
* **Annotator Blinding & Agreement:** Transparently disclosed that blinding applied to the 353 new pooled items; gold 250 items were annotated in an earlier phase. Disclosed that the 0.80 target was met on gold ($\kappa_w = 0.88$) but was 0.68 on pooled new items.
* **Hypothesis Testing:** Renamed Comp 1 to "AST+Header vs. Line No-Header" (dropped "Full Proposed vs. Baseline"). Added citations for Wilcoxon test [N4] and Holm-Bonferroni correction [N5].

---

## 5. Section IV: Preliminary Results, Tables, and Figures

* **Condition Naming Macros:** Implemented `\astH`, `\astN`, `\lineH`, `\lineN` across text and tables.
* **Table I (`tables/table_1_paper.tex`):**
  - Streamlined into a single-column layout without margin overflow.
  - Replaced long names with "Line" and "AST" with "Yes/No" header indicators.
  - Removed bold formatting from the auxiliary `J@10` column.
* **Table II (`tables/table_2_paper.tex`):**
  - Removed redundant $p_{\mathrm{raw}}$ column (already reported in narrative text).
  - Enclosed in `\resizebox{\columnwidth}{!}{...}` to eliminate the 75pt overfull hbox.
  - Converted hyphens in confidence intervals to proper mathematical minus signs (e.g., `$-0.088$`).
* **Figure 1 (`figs/fig1.pdf` & `figs/fig_F2.pdf`):**
  - Re-rendered using Type 42 TrueType/Type 1 Serif fonts (Times New Roman / Nimbus Roman).
  - Eliminated Type 3 fonts and un-embedded Helvetica fonts.
  - Offset Delta annotations with semi-transparent white bounding boxes to prevent plot lines from striking through text.
* **Fallback Root Cause Breakdown:**
  - Expanded exact frequency distribution across 110 React and 20 Java fallback chunks from `fallback_audit.csv`.
  - Removed "custom hooks" and acknowledged parser gaps in React JSX handling.

---

## 6. Section V: Discussion and Threats to Validity

* **Section Title:** Renamed Subsection V.A from "Discussion of Underlying Mechanisms" to "Possible Explanations".
* **Tone Calibration:** Replaced speculative causal claims with hypothesis framing ("is consistent with, but does not establish, two explanations").
* **Empirical Caveats:** Clarified that the 100% boundary intact rate for pure AST chunks is by construction, not an empirical finding.
* **Minimum Detectable Effect (MDE):** Explicitly reported power analysis threshold ($\text{MDE} \approx 0.11$ NDCG@10 at 80% power with $N=25$).

---

## 7. Section VI: Research Plan and Risks

* **Table III (Roadmap):** Condensed to 4 core phases (P1–P4), removing speculative P5 (citation-grounded generation).
* **Text Formatting:** Applied `\raggedright\arraybackslash` to Table III column specifications, preventing ugly hyphenation breaks ("Expan-sion").
* **Risks:** Replaced candidate evaluation phrasing with requirements verification and human-subjects ethical safeguards.

---

## 8. Section VII: Conclusion, Data Availability, and Acknowledgments

* **Conclusion:** Re-stated findings with exact 3-decimal formatting and framed 3 open questions for the SANER community.
* **Data Availability:** Updated third-party licensing disclosure to reflect that public code chunks are provided alongside commit SHAs and coordinates.
* **Acknowledgments:** Standardized AI disclosure for Google Antigravity, confirming human origin of all relevance labels.

---

## 9. References (`refs.bib`)

* **Corrected [2] (Montandon et al.):** MSR 2019 (pp. 276–287), replacing erroneous IEEE Software citation.
* **Corrected [3] (Survey):** Updated to Tao, Qin, Liu (arXiv:2510.04905, 2025).
* **Corrected [4] (cAST):** Added pagination pp. 8106–8116 (Findings of EMNLP 2025).
* **Corrected [10] (C-Pack):** Capitalized "Chinese".
* **Corrected [11] (CoSTV):** Corrected title to "CoSTV: Accelerating Code Search with Two-Stage Paradigm and Vector Retrieval" (APSEC 2024).
* **Corrected [15] (Triad):** Added pagination pp. 2668–2680 (ICSE 2024).
* **Added [N1]–[N5]:** Galimzyanov et al. (Code RAG at scale), Hu et al. (TOSS, WSDM 2023), Landis & Koch (1977), Wilcoxon (1945), Holm (1979).

---

## 10. Round 3 Revisions (v1.0 Guideline Compliance, 12/10/2026)

* **A1 (Table II Presentation & Overlap Fix):**
  - Replaced sprawling table notes with a clean 2-line `\parbox{\columnwidth}{...}` note.
  - Wrapped `tabular` in `\resizebox{\columnwidth}{!}{...}` eliminating the 75pt overfull hbox.
  - Removed all occurrences of "pre-registered" from Table II caption and headers (`grep -in "pre-registered\|preregistered"` returns 0 across entire paper).
  - Converted all confidence interval hyphens to mathematical minus signs (`$-0.088$`).
* **A2 (Layout & Large White Space on Pages 4–5):**
  - Removed artificial `\clearpage` before Section VI (`section_plan.tex`).
  - Table III (Roadmap) floats naturally at the top right of Page 4; Sections V.B and VI flow beneath it.
  - Page 4 is 100% full across both columns; main content finishes on Page 5; references are isolated on Page 6 (strict 5+1 IEEE page budget).
* **A3 (Table I Second-Best Formatting):**
  - Replaced confusing underlines with `\textit{...}` for all second-best values in Table I.
  - Updated note: "Bold: best; italic: second best within the reranking tier."
* **A4 (Official Macro `\castname`):**
  - Defined `\newcommand{\castname}{cAST}` in `main.tex`.
  - Replaced all instances of `\textsc{cAST}` with `\castname` throughout the manuscript.
* **B1 (Data Availability & Ethics Consistency):**
  - Standardized strictly on Option 2 across Data Availability and Ethics, acknowledging package distribution of chunk text from public repositories with author copyright retention.
* **B2 & B3 (Reference Corrections & Citations):**
  - Corrected author list for Galimzyanov et al. [6] to Timur Galimzyanov, Olga Kolomyttseva, and Egor Bogomolov (arXiv:2510.20609).
  - Verified and completed metadata for CoSTV (APSEC 2024), Kuang et al. (TSE 2023), Wu et al. (2026), and TOSS (WSDM 2023).
  - Updated cross-encoder citation in Section II.B to cite TOSS [11] and CoSTV [12].
  - Generated and expanded `paper/references_verification.csv` covering all 20 cited references.
* **B4 (Lexical BM25 Narrative & Bounds):**
  - Updated Section IV.A to specify NDCG@10 range [0.104, 0.187] across all 4 BM25 configurations in the package, noting Table I presents the two with headers.
  - Updated Judged@10 range to 13.6%–30.4%, and dense gain over BM25 to 0.238–0.322.
* **B5 (Secondary Metrics Clarification):**
  - Removed mention of unreported CP@5 in Section III.D; clarified secondary metrics are NDCG@1 and MRR@10 (Table I).
* **B6 (Power Analysis & MDE Calculation):**
  - Created `scripts/power_analysis.py`, calculating paired $t$-test MDE across all 5 comparisons.
  - Reported MDE range of 0.07 to 0.14 NDCG@10 at 80% power in Section V.B.
  - Documented MDE in `analysis_plan_addendum.md` (Section 3.6) and added automated pytest regression test `tests/test_power_analysis.py`.
* **B7 (Kappa Partition Breakdown):**
  - Extended `scripts/calculate_kappa.py` to compute and export quadratic weighted kappa for Gold 250 (0.8808), Pooled new 353 (0.6826), and Total 603 (0.7795) to `kappa_evaluation_report.txt` and `.json`.
* **B8 (Novelty Statement Literature Verification):**
  - Executed systematic search across arXiv, DBLP, and Google Scholar across 5 queries.
  - Confirmed novelty statement and documented audit in `paper/literature_search_log.md`.
* **B9 (Minor Academic Wording Refinements):**
  - Section VI.B: "dual annotation of newly pooled candidates".
  - Section IV.C: "the deficit widens more than threefold".
  - Section IV.C: "The audit offers a possible mechanism:".
* **B10 (Full AI Disclosure in Acknowledgments):**
  - Expanded Acknowledgments to disclose Google Antigravity with Anthropic Claude and Google Gemini models.
  - Updated `paper/ai_usage_log.md`.
* **Clean-up:**
  - Removed redundant draft tables (`paper/tables/table_T*.tex`), retaining only `table_1_paper.tex`, `table_2_paper.tex`, and optional `table_4_paper.tex`.
  - Retained test fixtures `paper/table_3_2.tex` and `paper/table_3_3_retrieval.tex` to maintain 100% test suite pass rate (62/62 tests passing).
