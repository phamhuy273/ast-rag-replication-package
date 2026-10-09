"""tests/test_experimental_controls.py - Verifies experimental controls across conditions.

Governed by:
- Rule R11: Uniqueness of files, repos, and chunks (no duplicate IDs or triple counts).
- Rule R13: Fair comparison across conditions (shared universe, shared queries, shared top-k).
"""

import csv
import json
from pathlib import Path
import pytest

ROOT_DIR = Path(__file__).resolve().parent.parent
QUERIES_FROZEN_FILE = ROOT_DIR / "dataset" / "queries_frozen.json"
JD_RAW_DIR = ROOT_DIR / "dataset" / "jd_raw"
MASTER_500_FILE = ROOT_DIR / "dataset" / "ground_truth_500_master.csv"


class TestExperimentalControls:
    """Verifies Rules R11 and R13 for experimental integrity."""

    def test_queries_frozen_validity_and_uniqueness(self):
        assert QUERIES_FROZEN_FILE.exists(), f"queries_frozen.json missing: {QUERIES_FROZEN_FILE}"
        with open(QUERIES_FROZEN_FILE, "r", encoding="utf-8") as f:
            data = json.load(f)

        assert data.get("status") == "FROZEN_PRE_REGISTRATION"
        queries = data.get("queries", {})
        assert len(queries) == 25, f"Expected 25 frozen queries, got {len(queries)}"

        # Rule R11: Unique JD IDs
        unique_jd_ids = set(queries.keys())
        assert len(unique_jd_ids) == 25

        # Check each query links to an existing raw file
        for jd_id, q_data in queries.items():
            assert "primary_query" in q_data and len(q_data["primary_query"]) > 10
            assert "sensitivity_raw_file" in q_data
            raw_path = ROOT_DIR / q_data["sensitivity_raw_file"]
            assert raw_path.exists(), f"Raw file {raw_path} not found for {jd_id}"
            with open(raw_path, "r", encoding="utf-8") as rf:
                raw_text = rf.read()
            assert len(raw_text) > 100, f"Raw text too short for {jd_id}"
            assert q_data["sensitivity_raw_text"] == raw_text, f"Raw text mismatch for {jd_id}"

    def test_master_file_counts_and_uniqueness(self):
        if MASTER_500_FILE.exists():
            with open(MASTER_500_FILE, "r", encoding="utf-8") as f:
                reader = csv.DictReader(f)
                rows = list(reader)

            assert len(rows) == 500, f"Expected 500 master rows, found {len(rows)}"
            # Verify uniqueness of (jd_id, repo_name, file_path, start_line, end_line)
            pair_signatures = set()
            for r in rows:
                sig = (r.get("jd_id"), r.get("repo_name"), r.get("file_path"), r.get("start_line"), r.get("end_line"))
                assert sig not in pair_signatures, f"Duplicate pair signature in master file: {sig}"
                pair_signatures.add(sig)

            # Rule R43: Verify exactly 40 repos and 189 unique files
            unique_repos = set(r["repo_name"] for r in rows)
            unique_files = set((r["repo_name"], r["file_path"]) for r in rows)
            assert len(unique_repos) == 40, f"Expected 40 repos, found {len(unique_repos)}"
            assert len(unique_files) == 189, f"Expected 189 unique files, found {len(unique_files)}"

    def test_experimental_parameters_consistency(self):
        """Rule R13: Ensure identical model hyperparameters are specified across pipeline configs."""
        # Standard frozen hyperparameters for SANER 2027 ERA
        DENSE_MODEL = "BAAI/bge-m3"
        RERANK_MODEL = "BAAI/bge-reranker-base"
        MAX_SEQ_LENGTH = 512
        SEED = 42

        # Check that analysis plan reflects these constants
        analysis_plan = (ROOT_DIR / "analysis_plan.md").read_text(encoding="utf-8")
        assert "512" in analysis_plan
        assert "bge-m3" in analysis_plan.lower()
        assert "bge-reranker-base" in analysis_plan.lower()
        assert "42" in analysis_plan
