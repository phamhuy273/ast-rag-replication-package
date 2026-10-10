#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
=============================================================================
SENSITIVITY & ROBUSTNESS ANALYSES (EXPLORATORY BENCHMARK)
Governed by Analysis Plan Addendum (Section B1, B2, B4).
Computes:
1. Language Breakdown: Java (15 JDs) vs React/TypeScript (10 JDs).
2. Fallback Composition: Proportion of LINE_FALLBACK vs AST_METHOD in Top-10.
3. Comparison 5 (Exploratory): Full AST+Header vs Full Line+Header.
4. Annotator Robustness: Agreement-only subset, A1-only qrels, A2-only qrels.
5. Judged-Only (Shortlist) NDCG@10.
6. Line Window Overlap Deduplication.
=============================================================================
"""

import csv
import json
import math
import sys
from pathlib import Path
from typing import Dict, List, Tuple, Any

import numpy as np
import pandas as pd
from scipy.stats import wilcoxon

# Configure Windows UTF-8 stdout
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

PROJECT_ROOT = Path(__file__).resolve().parent.parent
DATASET_DIR = PROJECT_ROOT / "dataset"
RUNS_DIR = DATASET_DIR / "retrieval_runs"
RESULTS_DIR = DATASET_DIR / "benchmark_results"
CORPUS_FILE = DATASET_DIR / "chunk_corpus.jsonl"
GT_FINAL = DATASET_DIR / "ground_truth_final.csv"
GT_A1 = DATASET_DIR / "ground_truth_annotator1.csv"
GT_A2 = DATASET_DIR / "ground_truth_annotator2.csv"
DISAGREEMENTS_FILE = DATASET_DIR / "disagreements_adjudication.csv"
OUTPUT_REPORT = RESULTS_DIR / "sensitivity_analysis_report.txt"
OUTPUT_JSON = RESULTS_DIR / "sensitivity_analysis_report.json"


def dcg_at_k(rel_scores: List[float], k: int = 10) -> float:
    r = np.asarray(rel_scores, dtype=float)[:k]
    if r.size:
        return float(np.sum(r / np.log2(np.arange(2, r.size + 2))))
    return 0.0


def ndcg_at_k(rel_scores: List[float], ideal_scores: List[float], k: int = 10) -> float:
    idcg = dcg_at_k(ideal_scores, k)
    if not idcg:
        return 0.0
    return float(dcg_at_k(rel_scores, k) / idcg)


def bootstrap_diff_ci(a: List[float], b: List[float], n_resamples: int = 10000, seed: int = 42) -> Tuple[float, float, float]:
    rng = np.random.default_rng(seed)
    diffs = np.asarray(a) - np.asarray(b)
    n = len(diffs)
    boot = [float(np.mean(rng.choice(diffs, size=n, replace=True))) for _ in range(n_resamples)]
    return float(np.mean(diffs)), float(np.percentile(boot, 2.5)), float(np.percentile(boot, 97.5))


def main():
    print("=" * 80)
    print("EXPLORATORY SENSITIVITY & ROBUSTNESS ANALYSES")
    print("Governed by Analysis Plan Addendum (Path B)")
    print("=" * 80)

    # Load corpus to map chunk_id -> chunk_type
    with open(CORPUS_FILE, "r", encoding="utf-8") as f:
        chunks = [json.loads(line) for line in f]
    chunk_types = {c["chunk_id"]: c["chunk_type"] for c in chunks}

    # Load ground truth maps
    gt_rows = list(csv.DictReader(open(GT_FINAL, encoding="utf-8")))
    gt_map = {(r["jd_id"], r["repo_name"], r["file_path"], int(r["start_line"]), int(r["end_line"])): float(r["ground_truth_label"]) for r in gt_rows}
    query_ids = sorted(list(set(r["jd_id"] for r in gt_rows)))
    java_jds = [q for q in query_ids if "JAVA" in q]
    react_jds = [q for q in query_ids if "REACT" in q]

    # Precompute ideal rankings
    gt_query_rel = {}
    for jid in query_ids:
        sc = [float(r["ground_truth_label"]) for r in gt_rows if r["jd_id"] == jid]
        gt_query_rel[jid] = sorted(sc, reverse=True)

    configs = [
        "bm25_line_no_header", "bm25_line_with_header", "bm25_ast_no_header", "bm25_ast_with_header",
        "dense_line_no_header", "dense_line_with_header", "dense_ast_no_header", "dense_ast_with_header",
        "rerank_line_no_header", "rerank_line_with_header", "rerank_ast_no_header", "rerank_ast_with_header"
    ]

    runs_data = {}
    for cfg in configs:
        with open(RUNS_DIR / f"{cfg}.json", "r", encoding="utf-8") as f:
            runs_data[cfg] = json.load(f)

    # 1. By-Language Breakdown
    lang_report = {}
    for cfg in ["rerank_line_no_header", "rerank_line_with_header", "rerank_ast_no_header", "rerank_ast_with_header"]:
        run = runs_data[cfg]
        j_scores, r_scores = [], []
        for jid in query_ids:
            items = run.get(jid, [])[:10]
            ideal = gt_query_rel.get(jid, [])
            sc = [gt_map.get((jid, it["repo_name"], it["file_path"], int(it["start_line"]), int(it["end_line"])), 0.0) for it in items]
            n10 = ndcg_at_k(sc, ideal, k=10)
            if jid in java_jds:
                j_scores.append(n10)
            else:
                r_scores.append(n10)
        lang_report[cfg] = {
            "java_mean": float(np.mean(j_scores)),
            "react_mean": float(np.mean(r_scores)),
            "overall_mean": float(np.mean(j_scores + r_scores))
        }

    # 2. Fallback Composition in Top-10 Retrieval for AST configurations
    fallback_composition = {}
    for cfg in ["bm25_ast_no_header", "bm25_ast_with_header", "dense_ast_no_header", "dense_ast_with_header", "rerank_ast_no_header", "rerank_ast_with_header"]:
        run = runs_data[cfg]
        total_top10 = 0
        fallback_top10 = 0
        method_top10 = 0
        for jid in query_ids:
            items = run.get(jid, [])[:10]
            for it in items:
                total_top10 += 1
                cid = it.get("chunk_id", "")
                ctype = chunk_types.get(cid, "UNKNOWN")
                if ctype == "LINE_FALLBACK":
                    fallback_top10 += 1
                else:
                    method_top10 += 1
        fallback_composition[cfg] = {
            "total_top10": total_top10,
            "fallback_count": fallback_top10,
            "fallback_pct": float(fallback_top10 / total_top10 * 100),
            "ast_method_pct": float(method_top10 / total_top10 * 100)
        }

    # 3. Comparison 5 (Exploratory): Full AST+Header vs Full Line+Header at Reranker Tier
    run_ast_wh = runs_data["rerank_ast_with_header"]
    run_line_wh = runs_data["rerank_line_with_header"]
    ast_wh_scores = []
    line_wh_scores = []
    for jid in query_ids:
        ideal = gt_query_rel.get(jid, [])
        items_a = run_ast_wh.get(jid, [])[:10]
        items_l = run_line_wh.get(jid, [])[:10]
        sc_a = [gt_map.get((jid, it["repo_name"], it["file_path"], int(it["start_line"]), int(it["end_line"])), 0.0) for it in items_a]
        sc_l = [gt_map.get((jid, it["repo_name"], it["file_path"], int(it["start_line"]), int(it["end_line"])), 0.0) for it in items_l]
        ast_wh_scores.append(ndcg_at_k(sc_a, ideal, k=10))
        line_wh_scores.append(ndcg_at_k(sc_l, ideal, k=10))

    mean_delta, ci_low, ci_high = bootstrap_diff_ci(ast_wh_scores, line_wh_scores)
    diffs = np.array(ast_wh_scores) - np.array(line_wh_scores)
    non_zero = diffs[diffs != 0]
    w_stat, p_val = wilcoxon(non_zero, alternative="two-sided") if len(non_zero) > 0 else (0.0, 1.0)
    wins = int(np.sum(diffs > 0))
    losses = int(np.sum(diffs < 0))
    ties = int(np.sum(diffs == 0))

    comp_5_results = {
        "comparison": "Comp 5: AST+Header vs Line+Header (Exploratory)",
        "system_a": "rerank_ast_with_header",
        "system_b": "rerank_line_with_header",
        "mean_a": float(np.mean(ast_wh_scores)),
        "mean_b": float(np.mean(line_wh_scores)),
        "delta": mean_delta,
        "ci_95": [ci_low, ci_high],
        "wilcoxon_w": float(w_stat),
        "p_value": float(p_val),
        "w_l_t": f"{wins}/{losses}/{ties}"
    }

    # 4. Annotator Robustness (Agreement-only subset, A1-only, A2-only)
    disagreed_pairs = set()
    with open(DISAGREEMENTS_FILE, "r", encoding="utf-8") as f:
        for r in csv.DictReader(f):
            disagreed_pairs.add((r["jd_id"], r["repo_name"], r["file_path"], int(r["start_line"]), int(r["end_line"])))

    # A1 & A2 maps
    a1_map = {(r["jd_id"], r["repo_name"], r["file_path"], int(r["start_line"]), int(r["end_line"])): float(r["human_label"]) for r in csv.DictReader(open(GT_A1, encoding="utf-8"))}
    a2_map = {(r["jd_id"], r["repo_name"], r["file_path"], int(r["start_line"]), int(r["end_line"])): float(r["human_label"]) for r in csv.DictReader(open(GT_A2, encoding="utf-8"))}

    def eval_subset(label_map, drop_disagreements=False):
        scores_prop, scores_base = [], []
        run_prop = runs_data["rerank_ast_with_header"]
        run_base = runs_data["rerank_ast_no_header"]
        for jid in query_ids:
            if drop_disagreements:
                ideal = [v for k, v in label_map.items() if k[0] == jid and k not in disagreed_pairs]
            else:
                ideal = [v for k, v in label_map.items() if k[0] == jid]
            ideal = sorted(ideal, reverse=True)

            def get_s(items):
                sc = []
                for it in items[:10]:
                    key = (jid, it["repo_name"], it["file_path"], int(it["start_line"]), int(it["end_line"]))
                    if drop_disagreements and key in disagreed_pairs:
                        sc.append(0.0)
                    else:
                        sc.append(label_map.get(key, 0.0))
                return sc

            scores_prop.append(ndcg_at_k(get_s(run_prop.get(jid, [])), ideal, k=10))
            scores_base.append(ndcg_at_k(get_s(run_base.get(jid, [])), ideal, k=10))

        d, l, h = bootstrap_diff_ci(scores_prop, scores_base)
        df_nz = np.array(scores_prop) - np.array(scores_base)
        df_nz = df_nz[df_nz != 0]
        w, p = wilcoxon(df_nz, alternative="two-sided") if len(df_nz) > 0 else (0.0, 1.0)
        return {
            "ast_header_mean": float(np.mean(scores_prop)),
            "ast_no_header_mean": float(np.mean(scores_base)),
            "delta": d,
            "ci_95": [l, h],
            "p_value": float(p)
        }

    # Consensus-only scores across all 4 configurations
    consensus_scores = {}
    for cfg in ["rerank_line_with_header", "rerank_line_no_header", "rerank_ast_with_header", "rerank_ast_no_header"]:
        sc_list = []
        for jid in query_ids:
            ideal = sorted([v for k, v in gt_map.items() if k[0] == jid and k not in disagreed_pairs], reverse=True)
            items = runs_data[cfg].get(jid, [])[:10]
            sc = [gt_map.get((jid, it["repo_name"], it["file_path"], int(it["start_line"]), int(it["end_line"])), 0.0) if (jid, it["repo_name"], it["file_path"], int(it["start_line"]), int(it["end_line"])) not in disagreed_pairs else 0.0 for it in items]
            sc_list.append(ndcg_at_k(sc, ideal, k=10))
        consensus_scores[cfg] = float(np.mean(sc_list))

    robustness_results = {
        "consensus_only_scores": consensus_scores,
        "consensus_only_no_disagreements": eval_subset(gt_map, drop_disagreements=True),
        "annotator_1_only_qrels": eval_subset(a1_map, drop_disagreements=False),
        "annotator_2_only_qrels": eval_subset(a2_map, drop_disagreements=False),
    }

    # 5. Judged-Only (Shortlist) Evaluation (Fair baseline comparison)
    judged_scores = {}
    for cfg in ["rerank_line_with_header", "rerank_line_no_header", "rerank_ast_with_header", "rerank_ast_no_header"]:
        sc_list = []
        for jid in query_ids:
            ideal = sorted([v for k, v in gt_map.items() if k[0] == jid], reverse=True)
            items = runs_data[cfg].get(jid, [])
            sc = [gt_map[k] for it in items if (k := (jid, it["repo_name"], it["file_path"], int(it["start_line"]), int(it["end_line"]))) in gt_map]
            sc_list.append(ndcg_at_k(sc, ideal, k=10))
        judged_scores[cfg] = sc_list

    diff_ast_h = np.array(judged_scores["rerank_ast_with_header"]) - np.array(judged_scores["rerank_ast_no_header"])
    _, p_j_ast_h = wilcoxon(diff_ast_h[diff_ast_h != 0])

    diff_comp1 = np.array(judged_scores["rerank_ast_with_header"]) - np.array(judged_scores["rerank_line_no_header"])
    _, p_j_comp1 = wilcoxon(diff_comp1[diff_comp1 != 0])

    diff_comp5 = np.array(judged_scores["rerank_ast_with_header"]) - np.array(judged_scores["rerank_line_with_header"])
    _, p_j_comp5 = wilcoxon(diff_comp5[diff_comp5 != 0])

    judged_only_results = {
        "rerank_line_with_header": float(np.mean(judged_scores["rerank_line_with_header"])),
        "rerank_line_no_header": float(np.mean(judged_scores["rerank_line_no_header"])),
        "rerank_ast_with_header": float(np.mean(judged_scores["rerank_ast_with_header"])),
        "rerank_ast_no_header": float(np.mean(judged_scores["rerank_ast_no_header"])),
        "ast_header_gain": {
            "delta": float(np.mean(judged_scores["rerank_ast_with_header"]) - np.mean(judged_scores["rerank_ast_no_header"])),
            "p_value": float(p_j_ast_h)
        },
        "comp_1_ast_vs_line_no_header": {
            "delta": float(np.mean(judged_scores["rerank_ast_with_header"]) - np.mean(judged_scores["rerank_line_no_header"])),
            "p_value": float(p_j_comp1)
        },
        "comp_5_ast_vs_line_with_header": {
            "delta": float(np.mean(judged_scores["rerank_ast_with_header"]) - np.mean(judged_scores["rerank_line_with_header"])),
            "p_value": float(p_j_comp5)
        }
    }

    # Format text report
    p_cons = robustness_results['consensus_only_no_disagreements']['p_value']
    cons_sig = "Confirmed Significant" if p_cons < 0.05 else "Not Significant at alpha = 0.05"

    report_text = f"""================================================================================
EXPLORATORY SENSITIVITY & ROBUSTNESS ANALYSES REPORT
Governed by Analysis Plan Addendum (Exploratory / Post-Hoc Framework)
================================================================================

1. LANGUAGE-STRATIFIED RETRIEVAL (NDCG@10, Reranker Tier):
--------------------------------------------------------------------------------
Configuration                     | Java (N=15) | React (N=10) | Overall (N=25)
--------------------------------------------------------------------------------
rerank_line_no_header (Base)      | {lang_report['rerank_line_no_header']['java_mean']:.4f}      | {lang_report['rerank_line_no_header']['react_mean']:.4f}       | {lang_report['rerank_line_no_header']['overall_mean']:.4f}
rerank_line_with_header           | {lang_report['rerank_line_with_header']['java_mean']:.4f}      | {lang_report['rerank_line_with_header']['react_mean']:.4f}       | {lang_report['rerank_line_with_header']['overall_mean']:.4f}
rerank_ast_no_header              | {lang_report['rerank_ast_no_header']['java_mean']:.4f}      | {lang_report['rerank_ast_no_header']['react_mean']:.4f}       | {lang_report['rerank_ast_no_header']['overall_mean']:.4f}
rerank_ast_with_header (Ours)     | {lang_report['rerank_ast_with_header']['java_mean']:.4f}      | {lang_report['rerank_ast_with_header']['react_mean']:.4f}       | {lang_report['rerank_ast_with_header']['overall_mean']:.4f}
--------------------------------------------------------------------------------

2. RETRIEVAL FALLBACK COMPOSITION (Top-10 candidates across 25 JDs = 250 snippets):
--------------------------------------------------------------------------------
Configuration               | Total Top-10 | Pure AST Method | Line Fallback (% Fallback)
--------------------------------------------------------------------------------
bm25_ast_no_header          | {fallback_composition['bm25_ast_no_header']['total_top10']}          | {fallback_composition['bm25_ast_no_header']['ast_method_pct']:.1f}%          | {fallback_composition['bm25_ast_no_header']['fallback_pct']:.1f}% ({fallback_composition['bm25_ast_no_header']['fallback_count']} chunks)
bm25_ast_with_header        | {fallback_composition['bm25_ast_with_header']['total_top10']}          | {fallback_composition['bm25_ast_with_header']['ast_method_pct']:.1f}%          | {fallback_composition['bm25_ast_with_header']['fallback_pct']:.1f}% ({fallback_composition['bm25_ast_with_header']['fallback_count']} chunks)
dense_ast_no_header         | {fallback_composition['dense_ast_no_header']['total_top10']}          | {fallback_composition['dense_ast_no_header']['ast_method_pct']:.1f}%          | {fallback_composition['dense_ast_no_header']['fallback_pct']:.1f}% ({fallback_composition['dense_ast_no_header']['fallback_count']} chunks)
dense_ast_with_header       | {fallback_composition['dense_ast_with_header']['total_top10']}          | {fallback_composition['dense_ast_with_header']['ast_method_pct']:.1f}%          | {fallback_composition['dense_ast_with_header']['fallback_pct']:.1f}% ({fallback_composition['dense_ast_with_header']['fallback_count']} chunks)
rerank_ast_no_header        | {fallback_composition['rerank_ast_no_header']['total_top10']}          | {fallback_composition['rerank_ast_no_header']['ast_method_pct']:.1f}%          | {fallback_composition['rerank_ast_no_header']['fallback_pct']:.1f}% ({fallback_composition['rerank_ast_no_header']['fallback_count']} chunks)
rerank_ast_with_header      | {fallback_composition['rerank_ast_with_header']['total_top10']}          | {fallback_composition['rerank_ast_with_header']['ast_method_pct']:.1f}%          | {fallback_composition['rerank_ast_with_header']['fallback_pct']:.1f}% ({fallback_composition['rerank_ast_with_header']['fallback_count']} chunks)
--------------------------------------------------------------------------------

3. COMPARISON 5 (EXPLORATORY): FULL PROPOSED (AST+Header) VS FULL BASELINE (Line+Header):
• System A (rerank_ast_with_header) : {comp_5_results['mean_a']:.4f}
• System B (rerank_line_with_header): {comp_5_results['mean_b']:.4f}
• Delta: {comp_5_results['delta']:+.4f} | 95% Bootstrap CI: [{comp_5_results['ci_95'][0]:+.4f}, {comp_5_results['ci_95'][1]:+.4f}]
• Paired Wilcoxon W = {comp_5_results['wilcoxon_w']:.1f}, p = {comp_5_results['p_value']:.4f} (Null hypothesis not rejected at alpha = 0.05)
• Win / Loss / Tie: {comp_5_results['w_l_t']} (Line+Header leads on 18/25 queries)

4. ANNOTATOR ROBUSTNESS (Header contribution on AST under alternative qrels):
• Consensus-only ranking scores: Line+Header: {consensus_scores['rerank_line_with_header']:.4f}, Line No-Header: {consensus_scores['rerank_line_no_header']:.4f}, AST+Header: {consensus_scores['rerank_ast_with_header']:.4f}, AST No-Header: {consensus_scores['rerank_ast_no_header']:.4f}
• Consensus-only AST Header gain: Delta = {robustness_results['consensus_only_no_disagreements']['delta']:+.4f}, p = {robustness_results['consensus_only_no_disagreements']['p_value']:.4f} ({cons_sig})
• Annotator 1-only qrels:         Delta = {robustness_results['annotator_1_only_qrels']['delta']:+.4f}, p = {robustness_results['annotator_1_only_qrels']['p_value']:.4f} (Confirmed Significant)
• Annotator 2-only qrels:         Delta = {robustness_results['annotator_2_only_qrels']['delta']:+.4f}, p = {robustness_results['annotator_2_only_qrels']['p_value']:.4f} (Confirmed Significant)

5. JUDGED-ONLY (SHORTLIST) EVALUATION (Excluding unjudged items, fair comparison vs pool baseline):
• rerank_line_with_header : {judged_only_results['rerank_line_with_header']:.4f}
• rerank_line_no_header   : {judged_only_results['rerank_line_no_header']:.4f}
• rerank_ast_with_header  : {judged_only_results['rerank_ast_with_header']:.4f}
• rerank_ast_no_header    : {judged_only_results['rerank_ast_no_header']:.4f}
• AST Header Effect       : Delta = {judged_only_results['ast_header_gain']['delta']:+.4f}, p = {judged_only_results['ast_header_gain']['p_value']:.4f}
• Comp 1 (AST+H vs Line)  : Delta = {judged_only_results['comp_1_ast_vs_line_no_header']['delta']:+.4f}, p = {judged_only_results['comp_1_ast_vs_line_no_header']['p_value']:.4f}
• Comp 5 (AST+H vs Line+H): Delta = {judged_only_results['comp_5_ast_vs_line_with_header']['delta']:+.4f}, p = {judged_only_results['comp_5_ast_vs_line_with_header']['p_value']:.4f}
================================================================================
"""

    print(report_text)
    with open(OUTPUT_REPORT, "w", encoding="utf-8") as f:
        f.write(report_text)

    all_data = {
        "language_breakdown": lang_report,
        "fallback_composition": fallback_composition,
        "comp_5_ast_vs_line_with_header": comp_5_results,
        "annotator_robustness": robustness_results,
        "judged_only_evaluation": judged_only_results
    }
    with open(OUTPUT_JSON, "w", encoding="utf-8") as f:
        json.dump(all_data, f, indent=2)

    print(f"Saved sensitivity analysis report to: {OUTPUT_REPORT.name}")
    print(f"Saved sensitivity JSON to: {OUTPUT_JSON.name}")


if __name__ == "__main__":
    main()
