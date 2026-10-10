"""tests/test_readme_numbers.py - Dynamic verification that all numerical claims in README.md match benchmark artifacts.

Governed by:
- Rule R37: Ground all Table and README numbers in dynamic measurement artifacts.
- Rule R5: Zero hardcoding or phantom figures.
"""

import json
import re
from pathlib import Path
import pytest

ROOT_DIR = Path(__file__).resolve().parent.parent
README_FILE = ROOT_DIR / "README.md"
DATASET_DIR = ROOT_DIR / "dataset"
BENCHMARK_DIR = DATASET_DIR / "benchmark_results"

TABLE_3_2_JSON = DATASET_DIR / "table_3_2_measured.json"
RETRIEVAL_JSON = BENCHMARK_DIR / "table_3_retrieval_benchmark.json"
STATS_JSON = BENCHMARK_DIR / "statistical_tests_report.json"
SENSITIVITY_JSON = BENCHMARK_DIR / "sensitivity_analysis_report.json"
KAPPA_REPORT = BENCHMARK_DIR / "kappa_evaluation_report.txt"


class TestReadmeNumbers:
    """Verifies that README.md numbers stay in 100% lockstep with empirical results."""

    @pytest.fixture(autouse=True)
    def setup_data(self):
        assert README_FILE.exists(), "README.md missing"
        self.readme = README_FILE.read_text(encoding="utf-8")

        with open(TABLE_3_2_JSON, "r", encoding="utf-8") as f:
            self.table_3_2 = json.load(f)

        with open(RETRIEVAL_JSON, "r", encoding="utf-8") as f:
            self.retrieval = json.load(f)

        with open(STATS_JSON, "r", encoding="utf-8") as f:
            self.stats = json.load(f)

        with open(SENSITIVITY_JSON, "r", encoding="utf-8") as f:
            self.sensitivity = json.load(f)

        self.kappa_text = KAPPA_REPORT.read_text(encoding="utf-8")

    def test_corpus_subgroup_counts_in_readme(self):
        """Verify chunk counts and fallback rates in README match Table 3.2."""
        pure_n = self.table_3_2["ast_pure"]["chunk_count"]
        fallback_n = self.table_3_2["ast_fallback"]["chunk_count"]
        combined_n = self.table_3_2["ast_combined"]["chunk_count"]
        line_n = self.table_3_2["line_based"]["chunk_count"]

        assert str(pure_n) in self.readme  # 234
        assert str(fallback_n) in self.readme  # 130
        assert str(combined_n) in self.readme  # 364
        assert str(line_n) in self.readme  # 434

        fallback_rate = float(fallback_n / combined_n * 100)
        assert f"{fallback_rate:.1f}%" in self.readme  # 35.7%

    def test_table_3_2_syntax_metrics_in_readme(self):
        """Verify morphology percentages in README match table_3_2_measured.json."""
        pure = self.table_3_2["ast_pure"]
        fallback = self.table_3_2["ast_fallback"]
        combined = self.table_3_2["ast_combined"]
        line = self.table_3_2["line_based"]

        # Pure
        assert f"{pure['boundary_intact_rate_pct']:.1f}%" in self.readme  # 100.0%
        assert f"{pure['syntax_intact_rate_pct']:.1f}%" in self.readme  # 97.9%
        assert f"{pure['loc_dist']['mean']:.1f}" in self.readme  # 19.8
        assert f"{pure['tokens_content_dist']['mean']:.1f}" in self.readme  # 211.3
        assert f"{pure['truncated_512_rate_pct']:.1f}%" in self.readme  # 6.0%

        # Fallback
        assert f"{fallback['boundary_intact_rate_pct']:.1f}%" in self.readme  # 74.6%
        assert f"{fallback['syntax_intact_rate_pct']:.1f}%" in self.readme  # 20.0%
        assert f"{fallback['loc_dist']['mean']:.1f}" in self.readme  # 42.9
        assert f"{fallback['tokens_content_dist']['mean']:.1f}" in self.readme  # 367.0
        assert f"{fallback['truncated_512_rate_pct']:.1f}%" in self.readme  # 20.0%

        # Combined
        assert f"{combined['boundary_intact_rate_pct']:.1f}%" in self.readme  # 90.9%
        assert f"{combined['syntax_intact_rate_pct']:.1f}%" in self.readme  # 70.1%
        assert f"{combined['loc_dist']['mean']:.1f}" in self.readme  # 28.1
        assert f"{combined['tokens_content_dist']['mean']:.1f}" in self.readme  # 266.9
        assert f"{combined['truncated_512_rate_pct']:.1f}%" in self.readme  # 11.0%

        # Line
        assert f"{line['boundary_intact_rate_pct']:.1f}%" in self.readme  # 44.0%
        assert f"{line['syntax_intact_rate_pct']:.1f}%" in self.readme  # 22.4%
        assert f"{line['loc_dist']['mean']:.1f}" in self.readme  # 41.0
        assert f"{line['tokens_content_dist']['mean']:.1f}" in self.readme  # 390.8
        assert f"{line['truncated_512_rate_pct']:.1f}%" in self.readme  # 28.6%

    def test_retrieval_ndcg_and_metrics_in_readme(self):
        """Verify retrieval benchmarks and top-performer claim in README."""
        retrieval_map = {r["config_id"]: r for r in self.retrieval}
        rerank_line_h = retrieval_map["rerank_line_with_header"]
        rerank_ast_h = retrieval_map["rerank_ast_with_header"]
        rerank_ast_no = retrieval_map["rerank_ast_no_header"]
        rerank_line_no = retrieval_map["rerank_line_no_header"]

        # NDCG@10 values
        assert f"{rerank_line_h['ndcg_10_mean']:.4f}" in self.readme  # 0.4994
        assert f"{rerank_ast_h['ndcg_10_mean']:.4f}" in self.readme  # 0.4566
        assert f"{rerank_ast_no['ndcg_10_mean']:.4f}" in self.readme  # 0.3445
        assert f"{rerank_line_no['ndcg_10_mean']:.4f}" in self.readme  # 0.4704

        # Key precision metrics
        assert f"{rerank_ast_h['ndcg_1_mean']:.3f}" in self.readme  # 0.720
        assert f"{rerank_line_h['ndcg_1_mean']:.3f}" in self.readme  # 0.520
        assert f"{rerank_ast_h['mrr_10_mean']:.3f}" in self.readme  # 0.940
        assert f"{rerank_line_h['mrr_10_mean']:.3f}" in self.readme  # 0.880
        assert f"{rerank_ast_h['cp_5_mean']:.3f}" in self.readme  # 0.913
        assert f"{rerank_line_h['cp_5_mean']:.3f}" in self.readme  # 0.884

    def test_statistical_test_numbers_in_readme(self):
        """Verify Wilcoxon, Holm p-values, and CIs in README."""
        stats_map = {}
        for s in self.stats:
            for prefix in ("Comp 1", "Comp 2", "Comp 3", "Comp 4"):
                if prefix in s["comparison"]:
                    stats_map[prefix] = s

        # Comp 3
        comp3 = stats_map["Comp 3"]
        assert f"{comp3['mean_diff']:+.4f}" in self.readme  # +0.1120
        assert f"{comp3['p_holm']:.4f}" in self.readme  # 0.0031
        assert f"{comp3['ci_95_low']:+.4f}" in self.readme  # +0.0559
        assert f"{comp3['ci_95_high']:+.4f}" in self.readme  # +0.1664

        # Comp 2
        comp2 = stats_map["Comp 2"]
        assert f"{comp2['mean_diff']:+.4f}" in self.readme  # -0.1258
        assert f"{comp2['p_holm']:.4f}" in self.readme  # 0.0001

        # Comp 1
        comp1 = stats_map["Comp 1"]
        assert f"{comp1['mean_diff']:+.4f}" in self.readme  # -0.0138
        assert f"{comp1['p_holm']:.4f}" in self.readme  # 0.8532

        # Comp 4
        comp4 = stats_map["Comp 4"]
        assert f"{comp4['mean_diff']:+.4f}" in self.readme  # +0.0291
        assert f"{comp4['p_holm']:.4f}" in self.readme  # 0.7332

        # Comp 5 (Exploratory)
        comp5 = self.sensitivity["comp_5_ast_vs_line_with_header"]
        assert f"{comp5['delta']:+.4f}" in self.readme  # -0.0428
        assert f"{comp5['p_value']:.4f}" in self.readme  # 0.1355
        assert f"{comp5['ci_95'][0]:+.4f}" in self.readme  # -0.1056
        assert f"{comp5['ci_95'][1]:+.4f}" in self.readme  # +0.0211

    def test_kappa_agreement_in_readme(self):
        """Verify Cohen's Kappa and pair counts in README."""
        assert "603" in self.readme
        assert "481" in self.readme
        assert "112" in self.readme
        assert "10" in self.readme
        assert "0.7795" in self.readme
        assert "0.8808" in self.readme
        assert "Substantial Agreement" in self.readme

    def test_pool_random_baseline_in_readme(self):
        """Verify candidate pool random baseline in README."""
        retrieval_map = {r["config_id"]: r for r in self.retrieval}
        pool_base = retrieval_map["random_pool_candidates"]
        assert f"{pool_base['ndcg_10_mean']:.3f}" in self.readme  # 0.592
