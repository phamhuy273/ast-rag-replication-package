#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
=============================================================================
ĐỒ ÁN 1 UIT - HỆ THỐNG ĐỐI SÁNH NĂNG LỰC ỨNG VIÊN QUA MÃ NGUỒN GITHUB
Task: THỰC NGHIỆM TÍCH HỢP TWO-STAGE RETRIEVAL VỚI CROSS-ENCODER RE-RANKER
Mô hình Stage 1 (Bi-Encoder): BAAI/bge-m3 (Dense 1024-dim)
Mô hình Stage 2 (Cross-Encoder): BAAI/bge-reranker-base (hoặc bge-reranker-large)
Mục tiêu: Đánh giá tối ưu hóa xếp hạng tại vị trí Top-1 / Top-3 theo góp ý của GVHD
Áp dụng cho: Báo cáo Đồ án 1 UIT & Section IV.B Bài báo IEEE SANER 2027
=============================================================================
"""

import sys
import os
import json
import argparse
from pathlib import Path
import numpy as np
import pandas as pd
from scipy import stats

# Thiết lập mã hóa UTF-8 cho Windows console
if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8', errors='replace')
if hasattr(sys.stderr, 'reconfigure'):
    sys.stderr.reconfigure(encoding='utf-8', errors='replace')

PROJECT_ROOT = Path(__file__).resolve().parent.parent
DATASET_DIR = PROJECT_ROOT / "dataset"
BENCHMARK_RESULTS_DIR = DATASET_DIR / "benchmark_results"
BENCHMARK_RESULTS_DIR.mkdir(parents=True, exist_ok=True)

JD_SKILLS_FILE = DATASET_DIR / "extracted_jd_skills.json"
FINAL_GT_FILE = DATASET_DIR / "ground_truth_final.csv"

OUTPUT_REPORT = BENCHMARK_RESULTS_DIR / "reranker_evaluation_report.txt"
PER_QUERY_CSV = BENCHMARK_RESULTS_DIR / "reranker_per_query_results.csv"

# Đường dẫn lưu cache vector Stage 1 (Bi-Encoder BGE-M3)
EMB_JD_CACHE = DATASET_DIR / "embeddings_jd_bgem3.npy"
EMB_AST_CACHE = DATASET_DIR / "embeddings_ast_bgem3.npy"
EMB_LINE_CACHE = DATASET_DIR / "embeddings_line_bgem3.npy"

# Đường dẫn lưu cache điểm Stage 2 (Cross-Encoder Re-ranker)
RERANK_SCORES_CACHE = DATASET_DIR / "reranker_scores_cache.npy"


def dcg_at_k(relevance_scores, k=5):
    """Tính Discounted Cumulative Gain tại k (chuẩn Linear Gain)."""
    relevance_scores = np.asarray(relevance_scores, dtype=float)[:k]
    if not len(relevance_scores):
        return 0.0
    gains = relevance_scores
    discounts = np.log2(np.arange(2, len(relevance_scores) + 2))
    return float(np.sum(gains / discounts))


def ndcg_at_k(relevance_scores, k=5):
    """Tính Normalized Discounted Cumulative Gain tại k."""
    actual_dcg = dcg_at_k(relevance_scores, k)
    ideal_scores = sorted(relevance_scores, reverse=True)
    ideal_dcg = dcg_at_k(ideal_scores, k)
    if ideal_dcg == 0.0:
        return 0.0
    return float(actual_dcg / ideal_dcg)


def context_precision_at_k(relevance_scores, k=5, threshold=1.0):
    """Tính Context Precision@k theo chuẩn RAGAs."""
    sub_scores = relevance_scores[:k]
    v = [1 if s >= threshold else 0 for s in sub_scores]
    n_relevant = sum(v)
    if n_relevant == 0:
        return 0.0

    cumulative_hits = 0
    weighted_precisions = 0.0
    for idx, is_rel in enumerate(v):
        if is_rel:
            cumulative_hits += 1
            precision_at_idx = cumulative_hits / (idx + 1)
            weighted_precisions += precision_at_idx

    return float(weighted_precisions / n_relevant)


def precision_recall_at_k(relevance_scores, k=5, threshold=1.0):
    """Tính Precision@k, Recall@k và F1@k."""
    sub_scores = relevance_scores[:k]
    binary_hits = [1 if s >= threshold else 0 for s in sub_scores]
    total_relevant = sum([1 if s >= threshold else 0 for s in relevance_scores])
    
    p_at_k = sum(binary_hits) / k if k > 0 else 0.0
    r_at_k = sum(binary_hits) / total_relevant if total_relevant > 0 else 0.0
    f1_at_k = (2 * p_at_k * r_at_k / (p_at_k + r_at_k)) if (p_at_k + r_at_k) > 0 else 0.0
    return p_at_k, r_at_k, f1_at_k


def mrr_score(relevance_scores, k=5, threshold=1.0):
    """Tính Mean Reciprocal Rank tại top-k."""
    sub_scores = relevance_scores[:k] if k is not None else relevance_scores
    for idx, score in enumerate(sub_scores):
        if score >= threshold:
            return 1.0 / (idx + 1)
    return 0.0


def count_win_loss_tie(scores_a, scores_b, tol=1e-5):
    """Đếm số truy vấn Thắng / Thua / Hòa."""
    wins = sum(1 for a, b in zip(scores_a, scores_b) if a - b > tol)
    losses = sum(1 for a, b in zip(scores_a, scores_b) if b - a > tol)
    ties = sum(1 for a, b in zip(scores_a, scores_b) if abs(a - b) <= tol)
    return wins, losses, ties


def safe_wilcoxon(x, y, alternative='greater'):
    """Kiểm định Wilcoxon an toàn tránh crash khi tất cả phần tử x - y đều bằng 0."""
    diff = np.array(x) - np.array(y)
    if np.all(np.isclose(diff, 0, atol=1e-7)):
        return 0.0, 1.0
    try:
        res = stats.wilcoxon(x, y, alternative=alternative)
        return float(res.statistic), float(res.pvalue)
    except Exception:
        return 0.0, 1.0



def evaluate_ranking_dict(ranked_labels_list):
    """Tính toán bộ metrics trung bình cho một danh sách kết quả xếp hạng."""
    metrics = {'p5': [], 'r5': [], 'f15': [], 'ndcg1': [], 'ndcg3': [], 'ndcg5': [], 'mrr': [], 'ctx_p5': []}
    for lbls in ranked_labels_list:
        p5, r5, f15 = precision_recall_at_k(lbls, k=5)
        metrics['p5'].append(p5)
        metrics['r5'].append(r5)
        metrics['f15'].append(f15)
        metrics['ndcg1'].append(ndcg_at_k(lbls, k=1))
        metrics['ndcg3'].append(ndcg_at_k(lbls, k=3))
        metrics['ndcg5'].append(ndcg_at_k(lbls, k=5))
        metrics['mrr'].append(mrr_score(lbls, k=5))
        metrics['ctx_p5'].append(context_precision_at_k(lbls, k=5))
    return metrics


def run_reranker_benchmark(model_name="BAAI/bge-reranker-base", force_recompute=False):
    print("=" * 80)
    print("🚀 BẮT ĐẦU THỰC NGHIỆM TWO-STAGE RETRIEVAL VỚI CROSS-ENCODER RE-RANKER")
    print(f"Mô hình Stage 1 (Bi-Encoder): BAAI/bge-m3 (Dense 1024-dim)")
    print(f"Mô hình Stage 2 (Cross-Encoder Re-ranker): {model_name}")
    print("=" * 80)

    # 1. Nạp Ground Truth
    if not FINAL_GT_FILE.exists():
        print(f"❌ Không tìm thấy file {FINAL_GT_FILE.name}!")
        return

    df = pd.read_csv(FINAL_GT_FILE)
    label_col = 'ground_truth_label' if 'ground_truth_label' in df.columns else 'human_label'
    print(f"✅ Đã nạp {len(df)} mẫu ground truth từ {FINAL_GT_FILE.name}")

    # 2. Nạp dữ liệu 25 JDs
    if not JD_SKILLS_FILE.exists():
        print(f"❌ Không tìm thấy file {JD_SKILLS_FILE.name}!")
        return

    with open(JD_SKILLS_FILE, 'r', encoding='utf-8') as f:
        jd_skills_data = json.load(f)

    jd_queries = {}
    for jd_id, data in jd_skills_data.items():
        title = data.get("title", jd_id)
        domain = data.get("domain", "")
        raw_mand = data.get("mandatory_skills", [])
        mand_skills = [s["skill_name"] if isinstance(s, dict) else str(s) for s in raw_mand]
        skills_str = ", ".join(mand_skills)
        query_text = f"Job Title: {title}. Domain: {domain}. Mandatory Technical Skills: {skills_str}."
        jd_queries[jd_id] = {
            "title": title,
            "domain": domain,
            "skills": mand_skills,
            "query_text": query_text
        }

    unique_jds = sorted(df['jd_id'].unique().tolist())
    print(f"🎯 Đã nạp thông tin truy vấn cho {len(unique_jds)} JDs.")

    # 3. Chuẩn bị nội dung văn bản cho Chunks
    ast_texts = []
    line_texts = []
    for _, row in df.iterrows():
        ctx = str(row.get('context_header', '')).strip()
        code = str(row.get('chunk_content', '')).strip()
        ast_texts.append(f"{ctx}\n\n{code}" if ctx else code)
        line_texts.append(code)

    # 4. Nạp Cache Vector Stage 1 (BGE-M3) để lấy thứ hạng ban đầu
    print("⚡ Đang nạp ma trận vector embedding Stage 1 (BGE-M3)...")
    if not (EMB_JD_CACHE.exists() and EMB_AST_CACHE.exists() and EMB_LINE_CACHE.exists()):
        print("❌ Thiếu file cache vector BGE-M3! Vui lòng chạy evaluate_retrieval_benchmarks.py trước.")
        return

    jd_embs_dict = np.load(EMB_JD_CACHE, allow_pickle=True).item()
    emb_ast = np.load(EMB_AST_CACHE)
    emb_line = np.load(EMB_LINE_CACHE)

    # 5. Xây dựng danh sách cặp (Pairs) cho Stage 2 Cross-Encoder
    all_pairs_ast = []
    all_pairs_line = []
    jd_slice_map = {}

    current_idx = 0
    for jd_id in unique_jds:
        jd_indices = df.index[df['jd_id'] == jd_id].tolist()
        q_text = jd_queries[jd_id]["query_text"]
        count = len(jd_indices)
        jd_slice_map[jd_id] = (current_idx, current_idx + count, jd_indices)
        for idx in jd_indices:
            all_pairs_ast.append((q_text, ast_texts[idx]))
            all_pairs_line.append((q_text, line_texts[idx]))
        current_idx += count

    print(f"📦 Đã chuẩn bị {len(all_pairs_ast)} cặp (JD, Code) cho 25 JDs.")

    # 6. Chạy / Nạp điểm Cross-Encoder Re-ranker
    cache_valid = (
        not force_recompute
        and RERANK_SCORES_CACHE.exists()
    )

    if cache_valid:
        print("⚡ Nạp điểm dự đoán Cross-Encoder từ cache...")
        cached_data = np.load(RERANK_SCORES_CACHE, allow_pickle=True).item()
        scores_rerank_ast_all = cached_data.get("ast")
        scores_rerank_line_all = cached_data.get("line")
    else:
        print(f"🤖 Đang nạp mô hình Cross-Encoder Re-ranker: {model_name}...")
        from sentence_transformers import CrossEncoder
        reranker = CrossEncoder(model_name)
        print("✅ Đã nạp thành công Re-ranker.")

        print(f"⏳ Đang chấm điểm Cross-Encoder cho {len(all_pairs_ast)} cặp AST...")
        scores_rerank_ast_all = reranker.predict(all_pairs_ast, batch_size=16, show_progress_bar=True)

        print(f"⏳ Đang chấm điểm Cross-Encoder cho {len(all_pairs_line)} cặp Line-based...")
        scores_rerank_line_all = reranker.predict(all_pairs_line, batch_size=16, show_progress_bar=True)

        # Lưu cache
        np.save(RERANK_SCORES_CACHE, {
            "model": model_name,
            "ast": scores_rerank_ast_all,
            "line": scores_rerank_line_all
        })
        print("💾 Đã lưu cache điểm Re-ranker ra file .npy.")

    # 7. Xếp hạng và tính toán số liệu cho 4 Cấu hình đối đầu
    # Config 1: AST Stage 1 (Bi-Encoder BGE-M3 thuần túy)
    # Config 2: Line-based Stage 1 (Bi-Encoder BGE-M3 thuần túy)
    # Config 3: Line-based Stage 2 (+ Re-ranker)
    # Config 4: AST Stage 2 (+ Re-ranker - Đề xuất hoàn chỉnh!)
    ranked_labels_ast_s1 = []
    ranked_labels_line_s1 = []
    ranked_labels_line_s2 = []
    ranked_labels_ast_s2 = []

    per_query_rows = []

    for jd_id in unique_jds:
        start_pos, end_pos, jd_indices = jd_slice_map[jd_id]
        gt_labels = df.loc[jd_indices, label_col].values.astype(float)
        query_vec = jd_embs_dict[jd_id]

        # a) AST Stage 1: Cosine similarity
        scores_ast_s1 = np.dot(emb_ast[jd_indices], query_vec)
        rank_ast_s1 = np.argsort(-scores_ast_s1)
        ranked_labels_ast_s1.append(gt_labels[rank_ast_s1])

        # b) Line Stage 1: Cosine similarity
        scores_line_s1 = np.dot(emb_line[jd_indices], query_vec)
        rank_line_s1 = np.argsort(-scores_line_s1)
        ranked_labels_line_s1.append(gt_labels[rank_line_s1])

        # c) Line Stage 2: Cross-Encoder scores
        scores_line_s2 = scores_rerank_line_all[start_pos:end_pos]
        rank_line_s2 = np.argsort(-scores_line_s2)
        ranked_labels_line_s2.append(gt_labels[rank_line_s2])

        # d) AST Stage 2: Cross-Encoder scores
        scores_ast_s2 = scores_rerank_ast_all[start_pos:end_pos]
        rank_ast_s2 = np.argsort(-scores_ast_s2)
        ranked_labels_ast_s2.append(gt_labels[rank_ast_s2])

        per_query_rows.append({
            "jd_id": jd_id,
            "title": jd_queries[jd_id]["title"],
            "ast_s1_ndcg1": ndcg_at_k(gt_labels[rank_ast_s1], 1),
            "ast_s2_ndcg1": ndcg_at_k(gt_labels[rank_ast_s2], 1),
            "line_s1_ndcg1": ndcg_at_k(gt_labels[rank_line_s1], 1),
            "line_s2_ndcg1": ndcg_at_k(gt_labels[rank_line_s2], 1),
            "ast_s1_ndcg5": ndcg_at_k(gt_labels[rank_ast_s1], 5),
            "ast_s2_ndcg5": ndcg_at_k(gt_labels[rank_ast_s2], 5),
            "line_s1_ndcg5": ndcg_at_k(gt_labels[rank_line_s1], 5),
            "line_s2_ndcg5": ndcg_at_k(gt_labels[rank_line_s2], 5),
        })

    # Lưu per-query ra CSV
    pd.DataFrame(per_query_rows).to_csv(PER_QUERY_CSV, index=False, encoding='utf-8-sig')

    # Tính toán toàn bộ metrics
    m_ast_s1 = evaluate_ranking_dict(ranked_labels_ast_s1)
    m_line_s1 = evaluate_ranking_dict(ranked_labels_line_s1)
    m_line_s2 = evaluate_ranking_dict(ranked_labels_line_s2)
    m_ast_s2 = evaluate_ranking_dict(ranked_labels_ast_s2)

    # Trung bình
    avg_ast_s1 = {k: np.mean(v) for k, v in m_ast_s1.items()}
    avg_line_s1 = {k: np.mean(v) for k, v in m_line_s1.items()}
    avg_line_s2 = {k: np.mean(v) for k, v in m_line_s2.items()}
    avg_ast_s2 = {k: np.mean(v) for k, v in m_ast_s2.items()}

    # 8. Kiểm định Ý nghĩa Thống kê (Wilcoxon Signed-Rank Test)
    # So sánh 1: AST Stage 2 (có Reranker) vs AST Stage 1 (không có Reranker) trên NDCG@1
    w_ast_s2_vs_s1_n1, p_ast_s2_vs_s1_n1 = safe_wilcoxon(m_ast_s2['ndcg1'], m_ast_s1['ndcg1'], alternative='greater')
    w_ast_s2_vs_s1_n5, p_ast_s2_vs_s1_n5 = safe_wilcoxon(m_ast_s2['ndcg5'], m_ast_s1['ndcg5'], alternative='greater')
    wins_s2_vs_s1_n1, losses_s2_vs_s1_n1, ties_s2_vs_s1_n1 = count_win_loss_tie(m_ast_s2['ndcg1'], m_ast_s1['ndcg1'])

    # So sánh 2: AST Stage 2 vs Line-based Stage 1 (Baseline gốc) trên NDCG@1 và NDCG@5
    w_ast_s2_vs_line_s1_n1, p_ast_s2_vs_line_s1_n1 = safe_wilcoxon(m_ast_s2['ndcg1'], m_line_s1['ndcg1'], alternative='greater')
    w_ast_s2_vs_line_s1_n5, p_ast_s2_vs_line_s1_n5 = safe_wilcoxon(m_ast_s2['ndcg5'], m_line_s1['ndcg5'], alternative='greater')
    wins_s2_vs_line_n1, losses_s2_vs_line_n1, ties_s2_vs_line_n1 = count_win_loss_tie(m_ast_s2['ndcg1'], m_line_s1['ndcg1'])
    wins_s2_vs_line_n5, losses_s2_vs_line_n5, ties_s2_vs_line_n5 = count_win_loss_tie(m_ast_s2['ndcg5'], m_line_s1['ndcg5'])

    report_text = f"""=============================================================================
BÁO CÁO THỰC NGHIỆM: TWO-STAGE RETRIEVAL VỚI CROSS-ENCODER RE-RANKER
MÔ HÌNH STAGE 1: BAAI/bge-m3 (Dense Bi-Encoder 1024-dim)
MÔ HÌNH STAGE 2: {model_name} (Cross-Encoder Re-ranker)
ĐÁP ỨNG GÓP Ý HỌC THUẬT: TỐI ƯU HÓA XẾP HẠNG TOP-1 VÀ TOP-3
=============================================================================

1. BẢNG SO SÁNH HIỆU NĂNG TOÀN DIỆN (TRUNG BÌNH QUA 25 JDs):
--------------------------------------------------------------------------------------------------------------------
Cấu hình (Configuration)                     | P@5    | R@5    | F1@5   | NDCG@1 | NDCG@3 | NDCG@5 | MRR    | Ctx-P@5
--------------------------------------------------------------------------------------------------------------------
Baseline 2 (GĐ 1): Line-based + BGE-M3       | {avg_line_s1['p5']:.4f} | {avg_line_s1['r5']:.4f} | {avg_line_s1['f15']:.4f} | {avg_line_s1['ndcg1']:.4f} | {avg_line_s1['ndcg3']:.4f} | {avg_line_s1['ndcg5']:.4f} | {avg_line_s1['mrr']:.4f} | {avg_line_s1['ctx_p5']:.4f}
Proposed (GĐ 1): AST Progressive + BGE-M3    | {avg_ast_s1['p5']:.4f} | {avg_ast_s1['r5']:.4f} | {avg_ast_s1['f15']:.4f} | {avg_ast_s1['ndcg1']:.4f} | {avg_ast_s1['ndcg3']:.4f} | {avg_ast_s1['ndcg5']:.4f} | {avg_ast_s1['mrr']:.4f} | {avg_ast_s1['ctx_p5']:.4f}
--------------------------------------------------------------------------------------------------------------------
Baseline 2 (GĐ 2): Line-based + BGE-Reranker | {avg_line_s2['p5']:.4f} | {avg_line_s2['r5']:.4f} | {avg_line_s2['f15']:.4f} | {avg_line_s2['ndcg1']:.4f} | {avg_line_s2['ndcg3']:.4f} | {avg_line_s2['ndcg5']:.4f} | {avg_line_s2['mrr']:.4f} | {avg_line_s2['ctx_p5']:.4f}
⭐ Proposed (GĐ 2): AST + BGE-Reranker (Ours)| {avg_ast_s2['p5']:.4f} | {avg_ast_s2['r5']:.4f} | {avg_ast_s2['f15']:.4f} | {avg_ast_s2['ndcg1']:.4f} | {avg_ast_s2['ndcg3']:.4f} | {avg_ast_s2['ndcg5']:.4f} | {avg_ast_s2['mrr']:.4f} | {avg_ast_s2['ctx_p5']:.4f}
--------------------------------------------------------------------------------------------------------------------
Độ tăng trưởng của AST sau Re-ranker (Δ GĐ2 vs GĐ1):
  • NDCG@1: {avg_ast_s1['ndcg1']:.4f} -> {avg_ast_s2['ndcg1']:.4f} ({(avg_ast_s2['ndcg1']-avg_ast_s1['ndcg1'])/avg_ast_s1['ndcg1']*100:+.1f}%)
  • NDCG@3: {avg_ast_s1['ndcg3']:.4f} -> {avg_ast_s2['ndcg3']:.4f} ({(avg_ast_s2['ndcg3']-avg_ast_s1['ndcg3'])/avg_ast_s1['ndcg3']*100:+.1f}%)
  • NDCG@5: {avg_ast_s1['ndcg5']:.4f} -> {avg_ast_s2['ndcg5']:.4f} ({(avg_ast_s2['ndcg5']-avg_ast_s1['ndcg5'])/avg_ast_s1['ndcg5']*100:+.1f}%)

2. KẾT QUẢ KIỂM ĐỊNH THỐNG KÊ (WILCOXON SIGNED-RANK TEST):
--------------------------------------------------------------------------------------------------------------------
(a) Hiệu quả của Re-ranker đối với giải pháp AST (AST GĐ 2 vs AST GĐ 1):
  • Trên chỉ số NDCG@1:
    - Wilcoxon W = {w_ast_s2_vs_s1_n1:.1f}, p-value = {p_ast_s2_vs_s1_n1:.6f}
    - Thắng (Tăng điểm Top-1) = {wins_s2_vs_s1_n1} | Thua = {losses_s2_vs_s1_n1} | Hòa = {ties_s2_vs_s1_n1}
  • Trên chỉ số NDCG@5:
    - Wilcoxon W = {w_ast_s2_vs_s1_n5:.1f}, p-value = {p_ast_s2_vs_s1_n5:.6f}

(b) AST + Re-ranker đối đầu với Baseline 2 Line-based (AST GĐ 2 vs Line GĐ 1):
  • Trên chỉ số NDCG@1:
    - Wilcoxon W = {w_ast_s2_vs_line_s1_n1:.1f}, p-value = {p_ast_s2_vs_line_s1_n1:.6f}
    - Phân phối truy vấn: Thắng = {wins_s2_vs_line_n1} | Thua = {losses_s2_vs_line_n1} | Hòa = {ties_s2_vs_line_n1}
  • Trên chỉ số NDCG@5:
    - Wilcoxon W = {w_ast_s2_vs_line_s1_n5:.1f}, p-value = {p_ast_s2_vs_line_s1_n5:.6f}
    - Phân phối truy vấn: Thắng = {wins_s2_vs_line_n5} | Thua = {losses_s2_vs_line_n5} | Hòa = {ties_s2_vs_line_n5}

3. ĐỊNH DẠNG BẢNG LATEX CHO BÀI BÁO IEEE SANER (ABLATION TABLE):
--------------------------------------------------------------------------------------------------------------------
\\begin{{table*}}[t]
\\caption{{Two-Stage Retrieval Performance with Cross-Encoder Re-ranking across 25 JDs}}
\\label{{tab:reranker_performance}}
\\centering
\\begin{{tabular}}{{lccccccc}}
\\hline
\\textbf{{Configuration}} & \\textbf{{P@5}} & \\textbf{{R@5}} & \\textbf{{F1@5}} & \\textbf{{NDCG@1}} & \\textbf{{NDCG@3}} & \\textbf{{NDCG@5}} & \\textbf{{MRR}} \\\\
\\hline
Line-based + BGE-M3 (Stage 1) & {avg_line_s1['p5']:.3f} & {avg_line_s1['r5']:.3f} & {avg_line_s1['f15']:.3f} & {avg_line_s1['ndcg1']:.3f} & {avg_line_s1['ndcg3']:.3f} & {avg_line_s1['ndcg5']:.3f} & {avg_line_s1['mrr']:.3f} \\\\
AST Progressive + BGE-M3 (Stage 1) & {avg_ast_s1['p5']:.3f} & {avg_ast_s1['r5']:.3f} & {avg_ast_s1['f15']:.3f} & {avg_ast_s1['ndcg1']:.3f} & {avg_ast_s1['ndcg3']:.3f} & {avg_ast_s1['ndcg5']:.3f} & {avg_ast_s1['mrr']:.3f} \\\\
\\hline
Line-based + BGE-Reranker (Stage 2) & {avg_line_s2['p5']:.3f} & {avg_line_s2['r5']:.3f} & {avg_line_s2['f15']:.3f} & {avg_line_s2['ndcg1']:.3f} & {avg_line_s2['ndcg3']:.3f} & {avg_line_s2['ndcg5']:.3f} & {avg_line_s2['mrr']:.3f} \\\\
\\textbf{{Proposed: AST + BGE-Reranker (Stage 2)}} & \\textbf{{{avg_ast_s2['p5']:.3f}}} & \\textbf{{{avg_ast_s2['r5']:.3f}}} & \\textbf{{{avg_ast_s2['f15']:.3f}}} & \\textbf{{{avg_ast_s2['ndcg1']:.3f}}} & \\textbf{{{avg_ast_s2['ndcg3']:.3f}}} & \\textbf{{{avg_ast_s2['ndcg5']:.3f}}} & \\textbf{{{avg_ast_s2['mrr']:.3f}}} \\\\
\\hline
\\end{{tabular}}
\\end{{table*}}
--------------------------------------------------------------------------------------------------------------------
"""

    print(report_text)
    with open(OUTPUT_REPORT, 'w', encoding='utf-8') as f:
        f.write(report_text)
    print(f"✅ Đã ghi thành công Báo cáo Thực nghiệm Re-ranker ra: {OUTPUT_REPORT.name}")
    print(f"📑 Đã lưu chi tiết từng query ra: {PER_QUERY_CSV.name}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Đánh giá thực nghiệm Two-Stage Retrieval với Cross-Encoder Re-ranker")
    parser.add_argument("--model", type=str, default="BAAI/bge-reranker-base", help="Tên mô hình Cross-Encoder trên HuggingFace")
    parser.add_argument("--recompute", action="store_true", help="Bắt buộc tính toán lại điểm Re-ranker")
    args = parser.parse_args()

    run_reranker_benchmark(model_name=args.model, force_recompute=args.recompute)
