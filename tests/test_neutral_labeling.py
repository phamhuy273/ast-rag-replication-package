"""tests/test_neutral_labeling.py - Verifies that to_label.csv adheres strictly to Rules R18, R19, and R44.

Governed by:
- Rule R18: Zero LLM pre-labels or artificial ground truth.
- Rule R19: Neutral display across all items (no source strategy leakage, no retrieval scores/ranks).
- Rule R44: Target pool size within feasible human annotation limits (<= 400 items).
"""

import csv
from pathlib import Path
import pytest

ROOT_DIR = Path(__file__).resolve().parent.parent
DATASET_DIR = ROOT_DIR / "dataset"
TO_LABEL_FILE = DATASET_DIR / "to_label.csv"
POOL_REPORT_FILE = DATASET_DIR / "pool_size_report.csv"


class TestNeutralLabeling:
    """Enforces Rules R18, R19, and R44 for blind, neutral human annotation."""

    def test_to_label_exists_and_pool_size_reasonable(self):
        assert TO_LABEL_FILE.exists(), f"to_label.csv missing: {TO_LABEL_FILE}"
        with open(TO_LABEL_FILE, "r", encoding="utf-8") as f:
            reader = csv.DictReader(f)
            rows = list(reader)

        assert len(rows) > 0, "to_label.csv is empty!"
        # Rule R44: Pool size must be within feasible human budget (<= 400 items)
        assert len(rows) <= 400, f"Pool size {len(rows)} exceeds 400 items budget! Reduce k to 3."

    def test_neutral_columns_and_no_leakage(self):
        with open(TO_LABEL_FILE, "r", encoding="utf-8") as f:
            reader = csv.DictReader(f)
            fieldnames = set(reader.fieldnames or [])

        # Allowed neutral fields
        expected_fields = {
            "item_id", "jd_id", "jd_title", "jd_level", "jd_domain", "jd_mandatory_skills",
            "repo_name", "file_path", "start_line", "end_line", "code_content",
            "annotator_1_label", "annotator_1_notes", "annotator_2_label", "annotator_2_notes",
            "adjudicated_label", "adjudication_reason", "adjudicated_by"
        }
        assert fieldnames == expected_fields, f"Unexpected columns in to_label.csv: {fieldnames ^ expected_fields}"

        # Forbidden columns (Rules R18, R19)
        forbidden_substrings = ["score", "rank", "strategy", "system", "llm", "ast", "line_50", "predicted", "ground_truth"]
        for col in fieldnames:
            for forbidden in forbidden_substrings:
                assert forbidden not in col.lower(), f"Leakage detected in column name '{col}' (matches '{forbidden}')"

    def test_initial_labels_are_empty_for_human_annotation(self):
        """Rule R18: No LLM pre-annotations or pre-filled labels."""
        with open(TO_LABEL_FILE, "r", encoding="utf-8") as f:
            reader = csv.DictReader(f)
            for idx, r in enumerate(reader, start=1):
                assert r["annotator_1_label"] == "", f"Row {idx}: annotator_1_label is not empty!"
                assert r["annotator_2_label"] == "", f"Row {idx}: annotator_2_label is not empty!"
                assert r["adjudicated_label"] == "", f"Row {idx}: adjudicated_label is not empty!"

    def test_code_content_is_clean_without_ast_headers(self):
        """Rule R19: Code content must not disclose chunking type via injected AST headers."""
        with open(TO_LABEL_FILE, "r", encoding="utf-8") as f:
            reader = csv.DictReader(f)
            for idx, r in enumerate(reader, start=1):
                code = r["code_content"]
                assert "// Class:" not in code, f"Row {idx}: AST header leaked in code_content"
                assert "// Method:" not in code, f"Row {idx}: AST header leaked in code_content"

    def test_pool_size_report_covers_all_25_jds(self):
        assert POOL_REPORT_FILE.exists()
        with open(POOL_REPORT_FILE, "r", encoding="utf-8") as f:
            rows = list(csv.DictReader(f))
        assert len(rows) == 25, f"Expected 25 JDs in pool report, found {len(rows)}"
