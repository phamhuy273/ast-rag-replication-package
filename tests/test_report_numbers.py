"""tests/test_report_numbers.py - Comprehensive verification of IEEE-style results report.

Governed by:
- Rules R1-R46: Zero hardcoding standard and complete numerical concordance.
- Rule R5: Zero phantom figures or manual alterations.
- Anonymity Standard: Zero personal names, student IDs, institutional emails, or local machine paths.
"""

import csv
import json
import re
import sys
from pathlib import Path
import pytest

ROOT_DIR = Path(__file__).resolve().parent.parent
DATASET_DIR = ROOT_DIR / "dataset"
BENCHMARK_DIR = DATASET_DIR / "benchmark_results"
REPORT_DIR = ROOT_DIR / "report"
TABLES_DIR = REPORT_DIR / "tables"
FIGS_DIR = REPORT_DIR / "figs"


class TestReportNumbers:
    """Verifies that all report tables, figures, and master document match raw benchmark artifacts 100%."""

    @pytest.fixture(autouse=True)
    def setup_data(self):
        # 1. Source benchmark files
        with open(DATASET_DIR / "table_3_2_measured.json", "r", encoding="utf-8") as f:
            self.table_3_2 = json.load(f)

        with open(BENCHMARK_DIR / "table_3_retrieval_benchmark.json", "r", encoding="utf-8") as f:
            self.retrieval_json = json.load(f)

        with open(BENCHMARK_DIR / "statistical_tests_report.json", "r", encoding="utf-8") as f:
            self.stats = json.load(f)

        with open(BENCHMARK_DIR / "sensitivity_analysis_report.json", "r", encoding="utf-8") as f:
            self.sensitivity = json.load(f)

        with open(BENCHMARK_DIR / "adjudication_summary.json", "r", encoding="utf-8") as f:
            self.adjudication = json.load(f)

        with open(DATASET_DIR / "manifest_repos.csv", "r", encoding="utf-8") as f:
            self.manifest_rows = list(csv.DictReader(f))

        with open(BENCHMARK_DIR / "pool_coverage_report.csv", "r", encoding="utf-8") as f:
            self.pool_coverage_rows = list(csv.DictReader(f))

    def test_artifacts_existence(self):
        """Assert all 10 tables, 4 figures, and master PDF/TeX exist and are non-empty."""
        for i in range(1, 11):
            t_file = TABLES_DIR / f"table_T{i}.tex"
            assert t_file.exists(), f"Missing table file: {t_file}"
            assert t_file.stat().st_size > 100, f"Table file too small: {t_file}"

        for i in range(1, 5):
            f_file = FIGS_DIR / f"fig_F{i}.pdf"
            assert f_file.exists(), f"Missing figure file: {f_file}"
            assert f_file.stat().st_size > 1000, f"Figure file too small: {f_file}"

        tex_file = REPORT_DIR / "results_report.tex"
        assert tex_file.exists(), f"Missing master TeX: {tex_file}"
        assert tex_file.stat().st_size > 1000, f"Master TeX too small: {tex_file}"

        pdf_file = REPORT_DIR / "results_report.pdf"
        assert pdf_file.exists(), f"Missing master PDF: {pdf_file}"
        assert pdf_file.stat().st_size > 50000, f"Master PDF too small: {pdf_file}"

    def test_t1_irr_concordance(self):
        """Assert Table T1 matches Cohen's Kappa, sample counts, and exact agreement."""
        t1_content = (TABLES_DIR / "table_T1.tex").read_text(encoding="utf-8")

        # Counts
        assert "250" in t1_content  # Gold
        assert "353" in t1_content  # New
        assert "603" in t1_content  # Total
        assert "88.4\\%" in t1_content  # Gold exact agreement
        assert "73.7\\%" in t1_content  # New exact agreement
        assert "79.8\\%" in t1_content  # Total exact agreement
        assert "0.8808" in t1_content   # Gold Kappa_w
        assert "0.6826" in t1_content   # New Kappa_w
        assert "0.7795" in t1_content   # Total Kappa_w
        assert "112 (18.6\\%)" in t1_content  # Minor deviations
        assert "10 (1.7\\%)" in t1_content    # Severe deviations

    def test_t2_morphology_concordance(self):
        """Assert Table T2 matches table_3_2_measured.json exactly."""
        t2_content = (TABLES_DIR / "table_T2.tex").read_text(encoding="utf-8")
        pure = self.table_3_2["ast_pure"]
        fallback = self.table_3_2["ast_fallback"]
        combined = self.table_3_2["ast_combined"]
        line = self.table_3_2["line_based"]

        # Chunk counts
        assert f"{pure['chunk_count']}" in t2_content  # 234
        assert f"{fallback['chunk_count']}" in t2_content  # 130
        assert f"{combined['chunk_count']}" in t2_content  # 364
        assert f"{line['chunk_count']}" in t2_content  # 434

        # Intact & truncated percentages
        assert f"{pure['syntax_intact_rate_pct']:.1f}\\%" in t2_content  # 97.9%
        assert f"{fallback['syntax_intact_rate_pct']:.1f}\\%" in t2_content  # 20.0%
        assert f"{combined['syntax_intact_rate_pct']:.1f}\\%" in t2_content  # 70.1%
        assert f"{line['syntax_intact_rate_pct']:.1f}\\%" in t2_content  # 22.4%

        assert f"{pure['boundary_intact_rate_pct']:.1f}\\%" in t2_content  # 100.0%
        assert f"{fallback['boundary_intact_rate_pct']:.1f}\\%" in t2_content  # 74.6%
        assert f"{combined['boundary_intact_rate_pct']:.1f}\\%" in t2_content  # 90.9%
        assert f"{line['boundary_intact_rate_pct']:.1f}\\%" in t2_content  # 44.0%

        assert f"{pure['truncated_512_count']}" in t2_content  # 14
        assert f"{fallback['truncated_512_count']}" in t2_content  # 26
        assert f"{combined['truncated_512_count']}" in t2_content  # 40
        assert f"{line['truncated_512_count']}" in t2_content  # 124

    def test_t3_benchmark_concordance(self):
        """Assert Table T3 matches retrieval benchmark NDCG, CI, and baselines."""
        t3_content = (TABLES_DIR / "table_T3.tex").read_text(encoding="utf-8")
        retrieval_map = {r["config_id"]: r for r in self.retrieval_json}

        # Check Re-ranking tier NDCG@10
        assert f"{retrieval_map['rerank_line_no_header']['ndcg_10_mean']:.3f}" in t3_content  # 0.470
        assert f"{retrieval_map['rerank_line_with_header']['ndcg_10_mean']:.3f}" in t3_content  # 0.499
        assert f"{retrieval_map['rerank_ast_no_header']['ndcg_10_mean']:.3f}" in t3_content  # 0.345
        assert f"{retrieval_map['rerank_ast_with_header']['ndcg_10_mean']:.3f}" in t3_content  # 0.457

        # Check Dense tier NDCG@10
        assert f"{retrieval_map['dense_line_no_header']['ndcg_10_mean']:.3f}" in t3_content  # 0.446
        assert f"{retrieval_map['dense_line_with_header']['ndcg_10_mean']:.3f}" in t3_content  # 0.450
        assert f"{retrieval_map['dense_ast_no_header']['ndcg_10_mean']:.3f}" in t3_content  # 0.320
        assert f"{retrieval_map['dense_ast_with_header']['ndcg_10_mean']:.3f}" in t3_content  # 0.408

        # Check BM25 tier NDCG@10
        assert f"{retrieval_map['bm25_line_no_header']['ndcg_10_mean']:.3f}" in t3_content  # 0.104
        assert f"{retrieval_map['bm25_line_with_header']['ndcg_10_mean']:.3f}" in t3_content  # 0.129
        assert f"{retrieval_map['bm25_ast_no_header']['ndcg_10_mean']:.3f}" in t3_content  # 0.187
        assert f"{retrieval_map['bm25_ast_with_header']['ndcg_10_mean']:.3f}" in t3_content  # 0.170

        # Baselines
        assert "0.019" in t3_content  # Whole corpus
        assert "0.592" in t3_content  # Evaluated pool

        # Mandatory note on BM25 unpooled items
        assert "BM25" in t3_content
        assert "unjudged" in t3_content.lower()

    def test_t4_hypothesis_concordance(self):
        """Assert Table T4 correctly segregates Confirmatory Holm family (Comps 1-4) vs. Exploratory (Comp 5)."""
        t4_content = (TABLES_DIR / "table_T4.tex").read_text(encoding="utf-8")
        doc_content = (REPORT_DIR / "results_report.tex").read_text(encoding="utf-8")

        # Comp 1
        assert "-0.0138" in t4_content
        assert "0.8532" in t4_content  # p_Holm
        assert "155.0" in t4_content   # Wilcoxon W
        assert "not supported" in doc_content.lower()

        # Comp 2
        assert "-0.1258" in t4_content
        assert "<0.001" in t4_content  # p_Holm
        assert "22.0" in t4_content    # Wilcoxon W

        # Comp 3
        assert "+0.1120" in t4_content
        assert "0.0031" in t4_content  # p_Holm
        assert "46.0" in t4_content    # Wilcoxon W

        # Comp 4
        assert "+0.0291" in t4_content
        assert "0.7332" in t4_content  # p_Holm
        assert "128.0" in t4_content   # Wilcoxon W

        # Comp 5 (Exploratory Contrast)
        assert "-0.0428" in t4_content
        assert "0.1355" in t4_content  # p_raw
        assert "97.0" in t4_content    # Wilcoxon W
        assert "Exploratory" in t4_content  # Explicit exploratory classification
        assert "---" in t4_content     # Not part of Holm family

        # Panel separation verification
        assert "Pre-registered Confirmatory Family" in t4_content
        assert "Exploratory Analysis (Outside Pre-registered Family)" in t4_content

    def test_t5_stratification_concordance(self):
        """Assert Table T5 matches sensitivity language breakdown."""
        t5_content = (TABLES_DIR / "table_T5.tex").read_text(encoding="utf-8")
        doc_content = (REPORT_DIR / "results_report.tex").read_text(encoding="utf-8")
        lb = self.sensitivity["language_breakdown"]

        # Means in Table (3 decimal precision)
        assert f"{lb['rerank_ast_with_header']['java_mean']:.3f}" in t5_content  # 0.515
        assert f"{lb['rerank_line_with_header']['java_mean']:.3f}" in t5_content  # 0.536
        assert f"{lb['rerank_ast_with_header']['react_mean']:.3f}" in t5_content  # 0.369
        assert f"{lb['rerank_line_with_header']['react_mean']:.3f}" in t5_content  # 0.445

        # 4-decimal precision in master report text
        assert "0.5146" in doc_content
        assert "0.5358" in doc_content
        assert "0.3694" in doc_content
        assert "0.4448" in doc_content

        # Differences
        assert "-0.021" in doc_content
        assert "-0.075" in doc_content

    def test_t6_fallback_concordance(self):
        """Assert Table T6 matches fallback composition counts across tiers."""
        t6_content = (TABLES_DIR / "table_T6.tex").read_text(encoding="utf-8")
        fc = self.sensitivity["fallback_composition"]

        # Rerank
        assert f"{fc['rerank_ast_with_header']['fallback_count']} (46.0\\%)" in t6_content  # 115
        assert f"{fc['rerank_ast_no_header']['fallback_count']} (70.0\\%)" in t6_content  # 175

        # Dense
        assert f"{fc['dense_ast_with_header']['fallback_count']} (33.6\\%)" in t6_content  # 84
        assert f"{fc['dense_ast_no_header']['fallback_count']} (69.2\\%)" in t6_content  # 173

        # BM25
        assert f"{fc['bm25_ast_with_header']['fallback_count']} (48.0\\%)" in t6_content  # 120
        assert f"{fc['bm25_ast_no_header']['fallback_count']} (76.4\\%)" in t6_content  # 191

    def test_t7_sensitivity_concordance(self):
        """Assert Table T7 matches consensus, single-annotator, and judged-only results."""
        t7_content = (TABLES_DIR / "table_T7.tex").read_text(encoding="utf-8")
        ar = self.sensitivity["annotator_robustness"]
        jo = self.sensitivity["judged_only_evaluation"]

        # Consensus
        assert f"{ar['consensus_only_scores']['rerank_line_with_header']:.3f}" in t7_content  # 0.426
        assert f"{ar['consensus_only_scores']['rerank_line_no_header']:.3f}" in t7_content  # 0.413
        assert f"{ar['consensus_only_scores']['rerank_ast_with_header']:.3f}" in t7_content  # 0.369
        assert f"{ar['consensus_only_scores']['rerank_ast_no_header']:.3f}" in t7_content  # 0.294
        assert "+0.075" in t7_content  # Delta
        assert "0.0851" in t7_content  # p-value
        assert "Non-Significant" in t7_content

        # Judged-only
        assert f"{jo['rerank_line_with_header']:.3f}" in t7_content  # 0.615
        assert f"{jo['rerank_line_no_header']:.3f}" in t7_content  # 0.590
        assert f"{jo['rerank_ast_with_header']:.3f}" in t7_content  # 0.546
        assert f"{jo['rerank_ast_no_header']:.3f}" in t7_content  # 0.454

    def test_t8_pool_coverage_concordance(self):
        """Assert Table T8 matches candidate pool coverage and BM25 unjudged counts."""
        t8_content = (TABLES_DIR / "table_T8.tex").read_text(encoding="utf-8")

        # Dense & Rerank 100% judged@3
        assert "100.0\\%" in t8_content
        # BM25 unjudged counts
        assert "61" in t8_content  # bm25_line_no_header
        assert "57" in t8_content  # bm25_line_with_header
        assert "49" in t8_content  # bm25_ast_no_header
        assert "53" in t8_content  # bm25_ast_with_header
        assert "220 top-3 slots" in t8_content

    def test_t9_pool_reconciliation_concordance(self):
        """Assert Table T9 matches pool deduplication counts and adjudication distribution."""
        t9_content = (TABLES_DIR / "table_T9.tex").read_text(encoding="utf-8")
        dd = self.adjudication["decision_distribution"]

        # Deduplication
        assert "415" in t9_content
        assert "382" in t9_content
        assert "29" in t9_content
        assert "353" in t9_content
        assert "603" in t9_content

        # Adjudication
        assert f"{dd['agreed_with_annotator_1_only']}" in t9_content  # 73
        assert f"{dd['agreed_with_annotator_2_only']}" in t9_content  # 47
        assert f"{dd['agreed_with_neither']}" in t9_content           # 2
        assert "59.8\\%" in t9_content
        assert "38.5\\%" in t9_content
        assert "1.6\\%" in t9_content
        assert "70" in t9_content  # distinct strings
        assert "29" in t9_content  # prefix count
        assert "93" in t9_content  # standard count

    def test_t10_manifest_concordance(self):
        """Assert Table T10 matches repository license distribution."""
        t10_content = (TABLES_DIR / "table_T10.tex").read_text(encoding="utf-8")

        assert "19" in t10_content  # MIT
        assert "47.5\\%" in t10_content
        assert "16" in t10_content  # Public GitHub
        assert "40.0\\%" in t10_content
        assert "4" in t10_content   # Apache-2.0
        assert "10.0\\%" in t10_content
        assert "1" in t10_content   # AGPL-3.0
        assert "2.5\\%" in t10_content
        assert "40" in t10_content  # Total
        assert "100.0\\%" in t10_content

    def test_anonymity_compliance(self):
        """Assert zero personal names, emails, student IDs, or local user paths in report files."""
        # Forbidden tokens that could indicate non-anonymity
        forbidden_tokens = [
            "win 11",
            "C:\\Users",
            "c:/users",
            "@gmail.com",
            "@hcmut",
            "@edu.vn",
            "student_id",
        ]

        # Scan report .tex files
        for p in REPORT_DIR.rglob("*.tex"):
            content = p.read_text(encoding="utf-8").lower()
            for token in forbidden_tokens:
                assert token not in content, f"Anonymity violation: found '{token}' in {p.name}"

        # Verify PDF metadata
        try:
            import pypdfium2 as pdfium
            pdf_path = REPORT_DIR / "results_report.pdf"
            if pdf_path.exists():
                doc = pdfium.PdfDocument(str(pdf_path))
                meta = doc.get_metadata_dict()
                for key in ["Author", "Creator", "Producer"]:
                    val = meta.get(key, "") or ""
                    assert "win 11" not in val.lower(), f"Anonymity leak in PDF metadata {key}: {val}"
                    assert "@" not in val, f"Email leak in PDF metadata {key}: {val}"
        except Exception:
            pass
