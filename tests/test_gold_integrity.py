"""tests/test_gold_integrity.py - Verifies integrity and immutability of ground_truth_final.csv.

Governed by Rule R17 of the Anti-Hardcoding Specification:
Gold labels cannot be modified under any circumstances. Lock SHA-256 hash and verify before any run.
"""

import csv
import hashlib
from pathlib import Path
import pytest
from sklearn.metrics import cohen_kappa_score

LOCKED_GOLD_SHA256 = "96104544502C509B5B544F8D21A17667E78680CF87A889BBC6E9898E1A0CF3F2"
ROOT_DIR = Path(__file__).resolve().parent.parent
GOLD_FILE = ROOT_DIR / "dataset" / "ground_truth_final.csv"


class TestGoldIntegrity:
    """Enforces Rule R17: Gold Ground Truth Immutability & Structural Validity."""

    def test_gold_file_exists(self):
        assert GOLD_FILE.exists(), f"Ground truth file missing: {GOLD_FILE}"

    def test_gold_sha256_hash_unmodified(self):
        with open(GOLD_FILE, "rb") as f:
            computed_hash = hashlib.sha256(f.read()).hexdigest().upper()
        assert computed_hash == LOCKED_GOLD_SHA256, (
            f"VIOLATION OF RULE R17: ground_truth_final.csv has been modified!\n"
            f"Expected: {LOCKED_GOLD_SHA256}\n"
            f"Actual:   {computed_hash}"
        )

    def test_gold_row_count_and_structure(self):
        with open(GOLD_FILE, "r", encoding="utf-8") as f:
            reader = csv.DictReader(f)
            rows = list(reader)

        assert len(rows) == 250, f"Expected exactly 250 gold pairs, found {len(rows)}"

        # Check required columns
        required_cols = {"jd_id", "repo_name", "file_path", "start_line", "end_line", "ground_truth_label"}
        assert required_cols.issubset(set(reader.fieldnames or [])), (
            f"Missing required columns in gold file: {required_cols - set(reader.fieldnames or [])}"
        )

        # Check exactly 25 JDs, 10 per JD
        jds = [r["jd_id"] for r in rows]
        unique_jds = sorted(list(set(jds)))
        assert len(unique_jds) == 25, f"Expected 25 unique JDs, found {len(unique_jds)}"

        java_jds = [j for j in unique_jds if "JAVA" in j]
        react_jds = [j for j in unique_jds if "REACT" in j]
        assert len(java_jds) == 15, f"Expected 15 Java JDs, found {len(java_jds)}"
        assert len(react_jds) == 10, f"Expected 10 React JDs, found {len(react_jds)}"

        from collections import Counter
        counts = Counter(jds)
        for jd, count in counts.items():
            assert count == 10, f"JD {jd} has {count} candidates, expected exactly 10"

    def test_gold_label_domain_and_types(self):
        with open(GOLD_FILE, "r", encoding="utf-8") as f:
            reader = csv.DictReader(f)
            for idx, r in enumerate(reader, start=2):
                raw_lbl = r.get("ground_truth_label")
                assert raw_lbl is not None, f"Row {idx}: missing ground_truth_label"
                assert raw_lbl in ("0", "1", "2"), f"Row {idx}: invalid label '{raw_lbl}', must be 0, 1, or 2"
                start = int(r["start_line"])
                end = int(r["end_line"])
                assert start >= 1, f"Row {idx}: invalid start_line {start}"
                assert end >= start, f"Row {idx}: end_line {end} < start_line {start}"

    def test_annotator_kappa_reproducible(self):
        # Verify quadratic weighted kappa on raw annotator files if present
        a1_file = ROOT_DIR / "dataset" / "ground_truth_huy_labeled.csv"
        a2_file = ROOT_DIR / "dataset" / "ground_truth_an_raw.csv"
        if a1_file.exists() and a2_file.exists():
            with open(a1_file, "r", encoding="utf-8") as f1, open(a2_file, "r", encoding="utf-8") as f2:
                rows1 = list(csv.DictReader(f1))
                rows2 = list(csv.DictReader(f2))
            assert len(rows1) == len(rows2) == 250
            labels1 = [int(r["annotator_1_label"]) for r in rows1]
            labels2 = [int(r["annotator_2_label"]) for r in rows2]
            kappa = cohen_kappa_score(labels1, labels2, weights="quadratic")
            assert pytest.approx(kappa, abs=0.01) == 0.88, f"Unexpected Kappa {kappa}, expected ~0.88"
