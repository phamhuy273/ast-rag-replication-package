"""tests/test_pool_coverage.py - Verifies that the 8 dense and rerank configurations have 100% judged@3 pool coverage, while BM25 is recorded separately.

Governed by Rule R44 and pool integrity verification.
"""

import csv
import json
from pathlib import Path
import pytest

ROOT_DIR = Path(__file__).resolve().parent.parent
DATASET_DIR = ROOT_DIR / "dataset"
RUNS_DIR = DATASET_DIR / "retrieval_runs"
GT_FILE = DATASET_DIR / "ground_truth_final.csv"
COVERAGE_REPORT = DATASET_DIR / "benchmark_results" / "pool_coverage_report.csv"

POOLED_CONFIGS = [
    "dense_line_no_header",
    "dense_line_with_header",
    "dense_ast_no_header",
    "dense_ast_with_header",
    "rerank_line_no_header",
    "rerank_line_with_header",
    "rerank_ast_no_header",
    "rerank_ast_with_header",
]

BM25_CONFIGS = [
    "bm25_line_no_header",
    "bm25_line_with_header",
    "bm25_ast_no_header",
    "bm25_ast_with_header",
]


def test_dense_and_rerank_configs_have_full_top3_judged_coverage():
    """All 8 dense and rerank configurations must have judged@3 = 1.0 (0 unjudged slots)."""
    gt_set = set()
    with open(GT_FILE, "r", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for r in reader:
            key = (r["jd_id"], r["repo_name"], r["file_path"], int(r["start_line"]), int(r["end_line"]))
            gt_set.add(key)

    for cfg in POOLED_CONFIGS:
        run_file = RUNS_DIR / f"{cfg}.json"
        assert run_file.exists(), f"Missing run file: {run_file}"
        with open(run_file, "r", encoding="utf-8") as f:
            run_data = json.load(f)

        unjudged_top3 = 0
        total_top3 = 0
        for qid, items in run_data.items():
            for it in items[:3]:
                key = (qid, it["repo_name"], it["file_path"], int(it["start_line"]), int(it["end_line"]))
                total_top3 += 1
                if key not in gt_set:
                    unjudged_top3 += 1

        assert total_top3 == 75, f"Expected 75 top-3 items (25 queries * 3), found {total_top3}"
        assert unjudged_top3 == 0, f"Config {cfg} has {unjudged_top3} unjudged items in top-3!"


def test_bm25_configs_were_not_pooled():
    """BM25 configurations have substantial unjudged top-3 slots (65-81% unjudged)."""
    gt_set = set()
    with open(GT_FILE, "r", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for r in reader:
            key = (r["jd_id"], r["repo_name"], r["file_path"], int(r["start_line"]), int(r["end_line"]))
            gt_set.add(key)

    for cfg in BM25_CONFIGS:
        run_file = RUNS_DIR / f"{cfg}.json"
        with open(run_file, "r", encoding="utf-8") as f:
            run_data = json.load(f)

        unjudged_top3 = 0
        total_top3 = 0
        for qid, items in run_data.items():
            for it in items[:3]:
                key = (qid, it["repo_name"], it["file_path"], int(it["start_line"]), int(it["end_line"]))
                total_top3 += 1
                if key not in gt_set:
                    unjudged_top3 += 1

        assert unjudged_top3 > 0, f"BM25 config {cfg} unexpectedly has 0 unjudged top-3 slots"
        judged_rate = (total_top3 - unjudged_top3) / total_top3
        assert 0.15 <= judged_rate <= 0.40, f"Unexpected judged@3 rate for {cfg}: {judged_rate}"
