"""tests/test_corpus_characteristics.py - Unit tests for 2x2 dual chunk corpus and Table 3.2.

Governed by:
- Rule R5: Both branches measured by identical functions without theoretical assignments.
- Rule R10: Sampling frame logging for AST and Line chunking.
- Rule R11: Uniqueness of chunk IDs across entire unified corpus.
- Rule R37: Cross-checking table_3_2.tex numbers against table_3_2_measured.json.
"""

import json
from pathlib import Path
import pytest

ROOT_DIR = Path(__file__).resolve().parent.parent
DATASET_DIR = ROOT_DIR / "dataset"
CORPUS_JSONL = DATASET_DIR / "chunk_corpus.jsonl"
SAMPLING_LOG = DATASET_DIR / "sampling_frame_log.json"
TABLE_3_2_JSON = DATASET_DIR / "table_3_2_measured.json"
TABLE_3_2_TEX = ROOT_DIR / "paper" / "table_3_2.tex"


class TestCorpusCharacteristics:
    """Verifies Phase 2 corpus integrity, 4 text variants, and empirical Table 3.2 measurements."""

    def test_corpus_size_and_strategies(self):
        assert CORPUS_JSONL.exists(), f"Corpus JSONL missing: {CORPUS_JSONL}"
        with open(CORPUS_JSONL, "r", encoding="utf-8") as f:
            chunks = [json.loads(line) for line in f]

        assert len(chunks) == 798, f"Expected 798 unified chunks, got {len(chunks)}"

        ast_chunks = [c for c in chunks if c["strategy"] == "AST"]
        line_chunks = [c for c in chunks if c["strategy"] == "LINE"]
        assert len(ast_chunks) == 364, f"Expected 364 AST chunks, got {len(ast_chunks)}"
        assert len(line_chunks) == 434, f"Expected 434 Line chunks, got {len(line_chunks)}"

    def test_chunk_id_uniqueness(self):
        with open(CORPUS_JSONL, "r", encoding="utf-8") as f:
            chunks = [json.loads(line) for line in f]
        chunk_ids = [c["chunk_id"] for c in chunks]
        assert len(chunk_ids) == len(set(chunk_ids)), "Duplicate chunk IDs found!"

    def test_four_text_variants_present(self):
        with open(CORPUS_JSONL, "r", encoding="utf-8") as f:
            chunks = [json.loads(line) for line in f]

        for c in chunks:
            assert "text_with_header" in c and len(c["text_with_header"]) > 5
            assert "text_no_header" in c and len(c["text_no_header"]) > 5
            assert "// File:" in c["context_header"]

    def test_sampling_frame_log_completeness(self):
        assert SAMPLING_LOG.exists()
        with open(SAMPLING_LOG, "r", encoding="utf-8") as f:
            log = json.load(f)

        assert log["universe"]["total_files"] == 189
        assert log["universe"]["total_repos"] == 40
        assert log["ast_sampling"]["retained"] == 364
        assert log["line_sampling"]["retained"] == 434

    def test_table_3_2_measured_values_and_no_zero_by_construction(self):
        assert TABLE_3_2_JSON.exists()
        with open(TABLE_3_2_JSON, "r", encoding="utf-8") as f:
            data = json.load(f)

        ast = data["ast_progressive"]
        line = data["line_based"]

        # Rule R5: No 0.0 "by construction" in boundary cut rate for overall/fallback/line
        assert ast["boundary_cut_rate_pct"] > 0.0, "AST boundary cut rate must be measured, not 0.0 by construction"
        assert line["boundary_cut_rate_pct"] > 0.0, "Line boundary cut rate must be measured"
        assert ast["syntax_error_rate_pct"] > 0.0, "AST syntax error rate must be measured"
        assert line["syntax_error_rate_pct"] > 0.0, "Line syntax error rate must be measured"

        # Rule B1: Verify all 3 AST subgroups
        assert "ast_pure" in data
        assert "ast_fallback" in data
        assert "ast_combined" in data
        pure = data["ast_pure"]
        fallback = data["ast_fallback"]

        assert pure["chunk_count"] == 234
        assert fallback["chunk_count"] == 130
        assert ast["chunk_count"] == 364
        assert line["chunk_count"] == 434

        # AST Pure boundary cut is 0, syntax intact is ~97.9%
        assert pure["boundary_cut_count"] == 0
        assert pure["boundary_intact_rate_pct"] == 100.0
        assert pure["header_retention_rate_pct"] == 100.0
        assert round(pure["syntax_intact_rate_pct"], 1) == 97.9

        # Fallback has cuts and syntax errors
        assert fallback["boundary_cut_count"] == 33
        assert fallback["header_retention_count"] == 0
        assert round(fallback["syntax_intact_rate_pct"], 1) == 20.0

        # Check LaTeX file contains the measured numbers (Rule R37)
        tex_text = TABLE_3_2_TEX.read_text(encoding="utf-8")
        assert "434" in tex_text
        assert "234" in tex_text
        assert "130" in tex_text
        assert "364" in tex_text
        assert f"{pure['loc_dist']['mean']:.1f}" in tex_text
        assert f"{fallback['loc_dist']['mean']:.1f}" in tex_text
        assert f"{ast['loc_dist']['mean']:.1f}" in tex_text
        assert f"{line['loc_dist']['mean']:.1f}" in tex_text
        assert f"{pure['boundary_intact_rate_pct']:.1f}" in tex_text
        assert f"{ast['boundary_intact_rate_pct']:.1f}" in tex_text
        assert f"{line['boundary_intact_rate_pct']:.1f}" in tex_text
