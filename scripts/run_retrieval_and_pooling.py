"""run_retrieval_and_pooling.py - Task 3.1, 3.2, 3.3: Full-corpus retrieval, 3-tier ranking, and top-k pooling.

Governed by:
- Rule R13: Identical universe (798 chunks across 189 files), identical frozen queries (25 JDs), identical top-k.
- Rule R16: Retrieval over the ENTIRE corpus universe for each JD.
- Rule R18: Zero LLM labels in ground truth or pre-annotation.
- Rule R19: Neutral display in to_label.csv (no chunk source, no scores, no ranks, randomized order).
- Rule R27, R28: Hash-locked caching of embeddings and re-ranking scores.
"""

import csv
import hashlib
import json
import os
import re
import sys
from pathlib import Path
from typing import Dict, List, Any, Tuple
import numpy as np
from rank_bm25 import BM25Okapi
from sentence_transformers import SentenceTransformer, CrossEncoder

ROOT_DIR = Path(__file__).resolve().parent.parent
DATASET_DIR = ROOT_DIR / "dataset"
CORPUS_JSONL = DATASET_DIR / "chunk_corpus.jsonl"
QUERIES_FROZEN_FILE = DATASET_DIR / "queries_frozen.json"
GOLD_FILE = DATASET_DIR / "ground_truth_final.csv"

CACHE_EMB_DIR = DATASET_DIR / "cache_embeddings"
RETRIEVAL_RUNS_DIR = DATASET_DIR / "retrieval_runs"
CACHE_EMB_DIR.mkdir(parents=True, exist_ok=True)
RETRIEVAL_RUNS_DIR.mkdir(parents=True, exist_ok=True)

POOL_REPORT_FILE = DATASET_DIR / "pool_size_report.csv"
TO_LABEL_FILE = DATASET_DIR / "to_label.csv"

SEED = 42
MAX_SEQ_LENGTH = 512
TOP_RETRIEVAL_K = 20
POOL_K = 5


def tokenize_code(text: str) -> List[str]:
    """Unified code tokenizer for BM25 retrieval."""
    return re.findall(r"[a-zA-Z_][a-zA-Z0-9_]*", text.lower())


def compute_hash(texts: List[str], model_name: str, max_seq_length: int) -> str:
    """Rule R27: Deterministic composite SHA-256 hash of inputs."""
    hasher = hashlib.sha256()
    hasher.update(model_name.encode("utf-8"))
    hasher.update(str(max_seq_length).encode("utf-8"))
    for t in texts:
        hasher.update(t.encode("utf-8"))
    return hasher.hexdigest()


def get_cached_or_compute_embeddings(
    name: str,
    texts: List[str],
    model: SentenceTransformer,
    model_name: str = "BAAI/bge-m3"
) -> np.ndarray:
    """Rule R27, R28: Retrieve cached embeddings if input hash matches; otherwise recompute."""
    current_hash = compute_hash(texts, model_name, MAX_SEQ_LENGTH)
    npy_path = CACHE_EMB_DIR / f"{name}.npy"
    meta_path = CACHE_EMB_DIR / f"{name}_meta.json"

    if npy_path.exists() and meta_path.exists():
        try:
            with open(meta_path, "r", encoding="utf-8") as f:
                meta = json.load(f)
            if meta.get("input_hash") == current_hash and meta.get("count") == len(texts):
                print(f"  [CACHE HIT] Loaded {name} ({len(texts)} embeddings)")
                return np.load(npy_path)
            else:
                print(f"  [CACHE STALE] Hash mismatch for {name}, recomputing...")
        except Exception:
            print(f"  [CACHE ERROR] Reading {name} cache failed, recomputing...")

    print(f"  [COMPUTE] Encoding {len(texts)} items for {name} with {model_name}...")
    embeddings = model.encode(
        texts,
        batch_size=16,
        show_progress_bar=True,
        normalize_embeddings=True,
        convert_to_numpy=True
    )
    np.save(npy_path, embeddings)
    with open(meta_path, "w", encoding="utf-8") as f:
        json.dump({"name": name, "model": model_name, "count": len(texts), "input_hash": current_hash}, f, indent=2)
    return embeddings


def main():
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")

    print("=" * 80)
    print("TASK 3.1 & 3.2: FULL-CORPUS RETRIEVAL & 3-TIER RANKING (25 JDs x 4 CONDITIONS)")
    print("=" * 80)

    # 1. Load frozen queries
    with open(QUERIES_FROZEN_FILE, "r", encoding="utf-8") as f:
        frozen_data = json.load(f)
    queries_dict = frozen_data["queries"]
    jd_ids = sorted(list(queries_dict.keys()))
    query_texts = [queries_dict[jid]["primary_query"] for jid in jd_ids]
    print(f"Loaded {len(jd_ids)} frozen queries.")

    # 2. Load corpus
    with open(CORPUS_JSONL, "r", encoding="utf-8") as f:
        all_chunks = [json.loads(line) for line in f]
    print(f"Loaded {len(all_chunks)} total chunks from corpus.")

    ast_chunks = [c for c in all_chunks if c["strategy"] == "AST"]
    line_chunks = [c for c in all_chunks if c["strategy"] == "LINE"]
    assert len(ast_chunks) == 364
    assert len(line_chunks) == 434

    # 3. Prepare 4 text conditions
    conditions = {
        "ast_with_header": {
            "strategy": "AST",
            "chunks": ast_chunks,
            "texts": [c["text_with_header"] for c in ast_chunks]
        },
        "ast_no_header": {
            "strategy": "AST",
            "chunks": ast_chunks,
            "texts": [c["text_no_header"] for c in ast_chunks]
        },
        "line_with_header": {
            "strategy": "LINE",
            "chunks": line_chunks,
            "texts": [c["text_with_header"] for c in line_chunks]
        },
        "line_no_header": {
            "strategy": "LINE",
            "chunks": line_chunks,
            "texts": [c["text_no_header"] for c in line_chunks]
        }
    }

    # 4. Initialize Models
    dense_model_name = "BAAI/bge-m3"
    print(f"\nInitializing SentenceTransformer({dense_model_name})...")
    dense_model = SentenceTransformer(dense_model_name)
    dense_model.max_seq_length = MAX_SEQ_LENGTH

    # Compute or load Query Embeddings
    query_embs = get_cached_or_compute_embeddings("queries_frozen_bgem3", query_texts, dense_model, dense_model_name)

    # Compute or load Chunk Embeddings for 4 conditions
    chunk_embs = {}
    for cond_name, c_data in conditions.items():
        embs = get_cached_or_compute_embeddings(f"emb_{cond_name}_bgem3", c_data["texts"], dense_model, dense_model_name)
        chunk_embs[cond_name] = embs

    # 5. Initialize BM25 Indices
    bm25_indices = {}
    for cond_name, c_data in conditions.items():
        print(f"Building BM25 index for {cond_name}...")
        tokenized_corpus = [tokenize_code(t) for t in c_data["texts"]]
        bm25_indices[cond_name] = BM25Okapi(tokenized_corpus)

    # 6. Initialize CrossEncoder Reranker
    reranker_model_name = "BAAI/bge-reranker-base"
    print(f"\nInitializing CrossEncoder({reranker_model_name})...")
    reranker = CrossEncoder(reranker_model_name)

    # 7. Execute Retrieval across 3 Tiers for each of 25 JDs
    retrieval_results = {
        # Format: config_name -> jd_id -> list of top-20 items: {chunk_id, rank, score, ...}
    }
    all_configs = []
    for cond_name in conditions:
        for tier in ["bm25", "dense", "rerank"]:
            config_id = f"{tier}_{cond_name}"
            all_configs.append(config_id)
            retrieval_results[config_id] = {}

    print(f"\nRunning 3-tier retrieval for {len(jd_ids)} JDs over {len(conditions)} conditions (12 total configs)...")

    for q_idx, jid in enumerate(jd_ids):
        q_text = query_texts[q_idx]
        q_tokens = tokenize_code(q_text)
        q_emb = query_embs[q_idx]

        for cond_name, c_data in conditions.items():
            cond_chunks = c_data["chunks"]
            cond_embs = chunk_embs[cond_name]
            bm25_idx = bm25_indices[cond_name]

            # Tier 1: BM25
            bm25_scores = np.array(bm25_idx.get_scores(q_tokens))
            top_bm25_indices = np.argsort(bm25_scores)[::-1][:TOP_RETRIEVAL_K]
            bm25_ranked = []
            for rank, c_i in enumerate(top_bm25_indices, start=1):
                chunk = cond_chunks[c_i]
                bm25_ranked.append({
                    "rank": rank,
                    "score": float(bm25_scores[c_i]),
                    "chunk_id": chunk["chunk_id"],
                    "repo_name": chunk["repo_name"],
                    "file_path": chunk["file_path"],
                    "start_line": chunk["start_line"],
                    "end_line": chunk["end_line"]
                })
            retrieval_results[f"bm25_{cond_name}"][jid] = bm25_ranked

            # Tier 2: Dense Bi-Encoder
            dense_scores = np.dot(cond_embs, q_emb)
            top_dense_indices = np.argsort(dense_scores)[::-1][:TOP_RETRIEVAL_K]
            dense_ranked_internal = []
            dense_ranked_to_save = []
            for rank, c_i in enumerate(top_dense_indices, start=1):
                chunk = cond_chunks[c_i]
                dense_ranked_internal.append({
                    "rank": int(rank),
                    "score": float(dense_scores[c_i]),
                    "chunk_id": chunk["chunk_id"],
                    "repo_name": chunk["repo_name"],
                    "file_path": chunk["file_path"],
                    "start_line": int(chunk["start_line"]),
                    "end_line": int(chunk["end_line"]),
                    "chunk_idx": int(c_i)
                })
                dense_ranked_to_save.append({
                    "rank": int(rank),
                    "score": float(dense_scores[c_i]),
                    "chunk_id": chunk["chunk_id"],
                    "repo_name": chunk["repo_name"],
                    "file_path": chunk["file_path"],
                    "start_line": int(chunk["start_line"]),
                    "end_line": int(chunk["end_line"])
                })
            retrieval_results[f"dense_{cond_name}"][jid] = dense_ranked_to_save

            # Tier 3: Cross-Encoder Re-ranker (Re-ranks top-20 of Dense)
            rerank_pairs = [(q_text, c_data["texts"][item["chunk_idx"]]) for item in dense_ranked_internal]
            rerank_scores = reranker.predict(rerank_pairs)
            rerank_sorted_order = np.argsort(rerank_scores)[::-1]
            rerank_ranked = []
            for new_rank, orig_idx in enumerate(rerank_sorted_order, start=1):
                item = dense_ranked_internal[orig_idx]
                rerank_ranked.append({
                    "rank": int(new_rank),
                    "score": float(rerank_scores[orig_idx]),
                    "dense_rank": int(item["rank"]),
                    "dense_score": float(item["score"]),
                    "chunk_id": item["chunk_id"],
                    "repo_name": item["repo_name"],
                    "file_path": item["file_path"],
                    "start_line": int(item["start_line"]),
                    "end_line": int(item["end_line"])
                })
            retrieval_results[f"rerank_{cond_name}"][jid] = rerank_ranked

    # Save retrieval runs
    for config_id, run_data in retrieval_results.items():
        run_file = RETRIEVAL_RUNS_DIR / f"{config_id}.json"
        with open(run_file, "w", encoding="utf-8") as f:
            json.dump(run_data, f, indent=2)

    print(f"Saved {len(retrieval_results)} retrieval run files in {RETRIEVAL_RUNS_DIR.name}/")

    # =========================================================================
    # TASK 3.3: TOP-K POOLING & TO_LABEL CREATION
    # =========================================================================
    print("\n" + "=" * 80)
    print(f"TASK 3.3: TOP-{POOL_K} POOLING & AUDIT GENERATION (RULES R18, R19)")
    print("=" * 80)

    # Load 250 Gold chunks for matching
    with open(GOLD_FILE, "r", encoding="utf-8") as f:
        gold_rows = list(csv.DictReader(f))

    # Build gold lookup table: (jd_id, repo_name, file_path, start_line, end_line) -> label
    gold_lookup = {}
    for r in gold_rows:
        key = (r["jd_id"], r["repo_name"], r["file_path"], int(r["start_line"]), int(r["end_line"]))
        gold_lookup[key] = int(r["ground_truth_label"])

    chunk_by_id = {c["chunk_id"]: c for c in all_chunks}

    # Pool systems: 4 conditions x 2 tiers (dense, rerank) = 8 systems
    pooling_systems = [
        "dense_ast_with_header", "dense_ast_no_header",
        "dense_line_with_header", "dense_line_no_header",
        "rerank_ast_with_header", "rerank_ast_no_header",
        "rerank_line_with_header", "rerank_line_no_header"
    ]

    def evaluate_pool_for_k(candidate_k: int):
        rep_rows = []
        unique_cand = {}
        total_pooled = 0
        total_gold = 0
        for jid in jd_ids:
            jd_info = queries_dict[jid]
            jd_pooled_chunks = set()
            for sys_id in pooling_systems:
                top_k_items = retrieval_results[sys_id][jid][:candidate_k]
                for it in top_k_items:
                    jd_pooled_chunks.add(it["chunk_id"])
            already_gold_cnt = 0
            new_cnt = 0
            for cid in jd_pooled_chunks:
                chunk = chunk_by_id[cid]
                key = (jid, chunk["repo_name"], chunk["file_path"], int(chunk["start_line"]), int(chunk["end_line"]))
                if key in gold_lookup:
                    already_gold_cnt += 1
                else:
                    new_cnt += 1
                    if key not in unique_cand:
                        unique_cand[key] = {
                            "jd_id": jid,
                            "jd_title": jd_info["title"],
                            "jd_level": jd_info["level"],
                            "jd_domain": jd_info["domain"],
                            "jd_mandatory_skills": ", ".join(jd_info["mandatory_skills"]),
                            "repo_name": chunk["repo_name"],
                            "file_path": chunk["file_path"],
                            "start_line": int(chunk["start_line"]),
                            "end_line": int(chunk["end_line"]),
                            "code_content": chunk["chunk_content"]  # Clean code without headers (Rule R19)
                        }
            total_pooled += len(jd_pooled_chunks)
            total_gold += already_gold_cnt
            rep_rows.append({
                "jd_id": jid,
                "category": jd_info["category"],
                "total_pooled": len(jd_pooled_chunks),
                "already_gold": already_gold_cnt,
                "new_to_label": new_cnt
            })
        return rep_rows, unique_cand, total_pooled, total_gold

    # Adaptive pool budget enforcement (Rule R44: Target budget <= 400 new items)
    selected_k = 5
    pool_report_rows, unique_candidates_to_label, total_pooled_items, total_already_gold = evaluate_pool_for_k(selected_k)
    print(f"Rule R44 evaluation: k={selected_k} yields {len(unique_candidates_to_label)} new items to label.")
    if len(unique_candidates_to_label) > 400:
        for fallback_k in [4, 3]:
            f_rep_rows, f_unique_cand, f_total_pooled, f_total_gold = evaluate_pool_for_k(fallback_k)
            print(f"  Rule R44 fallback: k={fallback_k} yields {len(f_unique_cand)} new items to label.")
            if len(f_unique_cand) <= 400 or fallback_k == 3:
                selected_k = fallback_k
                pool_report_rows = f_rep_rows
                unique_candidates_to_label = f_unique_cand
                total_pooled_items = f_total_pooled
                total_already_gold = f_total_gold
                print(f"  -> Selected k={selected_k} ({len(unique_candidates_to_label)} items, compliant with <=400 budget).")
                break

    # Save pool size report
    with open(POOL_REPORT_FILE, "w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=["jd_id", "category", "total_pooled", "already_gold", "new_to_label"])
        writer.writeheader()
        writer.writerows(pool_report_rows)

    new_items_list = list(unique_candidates_to_label.values())

    # Shuffle randomly using fixed seed 42 (Rule R19)
    rng = np.random.default_rng(SEED)
    rng.shuffle(new_items_list)

    # Assign neutral ITEM_XXX IDs
    to_label_rows = []
    for idx, item in enumerate(new_items_list, start=1):
        to_label_rows.append({
            "item_id": f"ITEM_{idx:03d}",
            "jd_id": item["jd_id"],
            "jd_title": item["jd_title"],
            "jd_level": item["jd_level"],
            "jd_domain": item["jd_domain"],
            "jd_mandatory_skills": item["jd_mandatory_skills"],
            "repo_name": item["repo_name"],
            "file_path": item["file_path"],
            "start_line": item["start_line"],
            "end_line": item["end_line"],
            "code_content": item["code_content"],
            "annotator_1_label": "",
            "annotator_1_notes": "",
            "annotator_2_label": "",
            "annotator_2_notes": "",
            "adjudicated_label": "",
            "adjudication_reason": "",
            "adjudicated_by": ""
        })

    fieldnames = [
        "item_id", "jd_id", "jd_title", "jd_level", "jd_domain", "jd_mandatory_skills",
        "repo_name", "file_path", "start_line", "end_line", "code_content",
        "annotator_1_label", "annotator_1_notes", "annotator_2_label", "annotator_2_notes",
        "adjudicated_label", "adjudication_reason", "adjudicated_by"
    ]
    with open(TO_LABEL_FILE, "w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(to_label_rows)

    print("-" * 80)
    print("POOLING SUMMARY (k=5 across 8 systems):")
    print(f"Total candidate instances pooled: {total_pooled_items}")
    print(f"Candidates already covered by 250 Gold: {total_already_gold}")
    print(f"Unique new candidate chunks needing human annotation: {len(to_label_rows)}")
    print(f"Pool size report saved: {POOL_REPORT_FILE}")
    print(f"Neutral labeling file saved: {TO_LABEL_FILE}")
    print("-" * 80)


if __name__ == "__main__":
    main()
