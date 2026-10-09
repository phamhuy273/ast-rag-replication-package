"""build_dual_corpus.py - Task 2.1, 2.2, 2.3: Generate 2x2 Dual Chunking Corpus across 189 files.

Governed by:
- Task 2.1: AST progressive chunking, line filter 6-85 LOC, no 1-chunk/file cap, log rejections (R10).
- Task 2.2: Line-based chunking (window 50 LOC, step 40, overlap 10 LOC).
- Task 2.3: 4 text variants in dataset/chunk_corpus.parquet with unique chunk IDs (R11).
- Rule R13: Exact identical universe of 189 source files for both branches.
"""

import csv
import json
import sys
from pathlib import Path
from typing import List, Dict, Any
from collections import Counter

ROOT_DIR = Path(__file__).resolve().parent.parent
DATASET_DIR = ROOT_DIR / "dataset"
MANIFEST_FILE = DATASET_DIR / "manifest_repos.csv"
CLONE_ROOT = ROOT_DIR / "ai-engine" / "temp_repos"

OUTPUT_PARQUET = DATASET_DIR / "chunk_corpus.parquet"
OUTPUT_JSONL = DATASET_DIR / "chunk_corpus.jsonl"
SAMPLING_LOG = DATASET_DIR / "sampling_frame_log.json"

sys.path.append(str(ROOT_DIR / "ai-engine"))
from parser.tree_sitter_loader import ast_loader


def get_file_language(file_path: str) -> tuple[str, str]:
    ext = Path(file_path).suffix.lower()
    if ext == ".java":
        return "java", "JAVA"
    elif ext in (".tsx", ".jsx"):
        return "tsx", "REACT_TS"
    elif ext in (".ts", ".js"):
        return "typescript", "REACT_TS"
    return "java", "UNKNOWN"


def line_based_chunking(
    file_path: str,
    source_code: str,
    window_size: int = 50,
    overlap: int = 10,
    min_loc: int = 6
) -> tuple[List[Dict[str, Any]], Dict[str, int]]:
    """Task 2.2: Generate sliding window line chunks (50 LOC, overlap 10, step 40)."""
    lines = source_code.splitlines()
    total_lines = len(lines)
    chunks = []
    stats = {"generated": 0, "retained": 0, "rejected_short": 0}

    if total_lines == 0:
        return chunks, stats

    step = max(1, window_size - overlap)
    for start_idx in range(0, total_lines, step):
        end_idx = min(start_idx + window_size, total_lines)
        chunk_lines = lines[start_idx:end_idx]
        loc = len(chunk_lines)
        stats["generated"] += 1

        if loc < min_loc and total_lines >= min_loc:
            # Trailing sliver less than 6 lines when file itself is larger
            stats["rejected_short"] += 1
            if end_idx == total_lines:
                break
            continue

        start_line = start_idx + 1
        end_line = end_idx
        chunk_text = "\n".join(chunk_lines)

        # Minimal context header for line chunker (Rule R14)
        context_header = f"// File: {file_path}\n// Lines: {start_line}-{end_line}"
        text_with_header = f"{context_header}\n\n{chunk_text}"
        text_no_header = chunk_text

        chunks.append({
            "strategy": "LINE",
            "file_path": file_path,
            "start_line": start_line,
            "end_line": end_line,
            "loc": loc,
            "chunk_type": "LINE_50",
            "class_name": None,
            "method_name": None,
            "context_header": context_header,
            "chunk_content": chunk_text,
            "text_with_header": text_with_header,
            "text_no_header": text_no_header
        })

        if end_idx == total_lines:
            break

    stats["retained"] = len(chunks)
    return chunks, stats


def ast_based_chunking(
    file_path: str,
    source_code: str,
    language: str,
    min_loc: int = 6,
    max_loc: int = 85
) -> tuple[List[Dict[str, Any]], Dict[str, int]]:
    """Task 2.1: Generate AST progressive disclosure chunks with 6-85 LOC filter."""
    raw_chunks = ast_loader.parse_and_chunk(file_path, source_code, language=language, include_export_prefix=True)
    stats = {
        "generated": len(raw_chunks),
        "retained": 0,
        "rejected_short": 0,
        "rejected_long": 0
    }
    filtered_chunks = []

    for c in raw_chunks:
        start_line = c["start_line"]
        end_line = c["end_line"]
        loc = end_line - start_line + 1

        if loc < min_loc:
            stats["rejected_short"] += 1
            continue
        if loc > max_loc:
            stats["rejected_long"] += 1
            continue

        chunk_text = c["chunk_content"]
        header = c["context_header"]

        filtered_chunks.append({
            "strategy": "AST",
            "file_path": file_path,
            "start_line": start_line,
            "end_line": end_line,
            "loc": loc,
            "chunk_type": c["chunk_type"],
            "class_name": c.get("class_name"),
            "method_name": c.get("method_name"),
            "context_header": header,
            "chunk_content": chunk_text,
            "text_with_header": f"{header}\n\n{chunk_text}",
            "text_no_header": chunk_text
        })

    stats["retained"] = len(filtered_chunks)
    return filtered_chunks, stats


def main():
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")

    print("=" * 80)
    print("TASK 2.1, 2.2, 2.3: GENERATING DUAL CORPUS (AST vs LINE) ACROSS 189 FILES")
    print("=" * 80)

    with open(MANIFEST_FILE, "r", encoding="utf-8") as f:
        manifest = list(csv.DictReader(f))

    all_ast_chunks = []
    all_line_chunks = []

    ast_sampling_summary = {"generated": 0, "retained": 0, "rejected_short": 0, "rejected_long": 0}
    line_sampling_summary = {"generated": 0, "retained": 0, "rejected_short": 0}

    file_count = 0
    for repo in manifest:
        rname = repo["repo_name"]
        safe_name = rname.replace("/", "__")
        files = [fp.strip() for fp in repo["files_list"].split(";") if fp.strip()]

        for fp in files:
            file_count += 1
            disk_path = CLONE_ROOT / safe_name / fp
            assert disk_path.exists(), f"File missing: {disk_path}"

            code = disk_path.read_text(encoding="utf-8", errors="replace")
            parser_lang, category = get_file_language(fp)

            # 1. AST chunking
            ast_chunks, ast_stats = ast_based_chunking(fp, code, parser_lang, min_loc=6, max_loc=85)
            for s in ast_stats:
                ast_sampling_summary[s] += ast_stats[s]

            for c in ast_chunks:
                c["repo_name"] = rname
                c["category"] = category
                c["chunk_id"] = f"ast::{rname}::{fp}::{c['start_line']}_{c['end_line']}::{c['chunk_type']}"
                all_ast_chunks.append(c)

            # 2. Line chunking
            line_chunks, line_stats = line_based_chunking(fp, code, window_size=50, overlap=10, min_loc=6)
            for s in line_stats:
                line_sampling_summary[s] += line_stats[s]

            for c in line_chunks:
                c["repo_name"] = rname
                c["category"] = category
                c["chunk_id"] = f"line::{rname}::{fp}::{c['start_line']}_{c['end_line']}::{c['chunk_type']}"
                all_line_chunks.append(c)

    assert file_count == 189, f"Expected 189 files, processed {file_count}"

    # Verify ID uniqueness (Rule R11)
    ast_ids = set(c["chunk_id"] for c in all_ast_chunks)
    assert len(ast_ids) == len(all_ast_chunks), "Duplicate chunk IDs found in AST corpus!"
    line_ids = set(c["chunk_id"] for c in all_line_chunks)
    assert len(line_ids) == len(all_line_chunks), "Duplicate chunk IDs found in Line corpus!"

    combined_corpus = all_ast_chunks + all_line_chunks
    combined_ids = set(c["chunk_id"] for c in combined_corpus)
    assert len(combined_ids) == len(combined_corpus), "Duplicate chunk IDs in combined corpus!"

    # Save to JSONL
    with open(OUTPUT_JSONL, "w", encoding="utf-8") as f:
        for c in combined_corpus:
            f.write(json.dumps(c, ensure_ascii=False) + "\n")

    # Save to Parquet
    try:
        import pandas as pd
        df = pd.DataFrame(combined_corpus)
        df.to_parquet(OUTPUT_PARQUET, index=False)
        parquet_saved = True
    except Exception as e:
        print(f"Warning: Could not save Parquet directly ({e}). JSONL saved.")
        parquet_saved = False

    # Save sampling frame log (Rule R10)
    sampling_log_data = {
        "universe": {
            "total_repos": len(manifest),
            "total_files": file_count,
            "manifest_file": str(MANIFEST_FILE.name)
        },
        "filters": {
            "ast_filter": "6 <= LOC <= 85 (No 1-chunk/file cap)",
            "line_filter": "Window 50 LOC, Overlap 10 LOC (Step 40), Min 6 LOC"
        },
        "ast_sampling": ast_sampling_summary,
        "line_sampling": line_sampling_summary,
        "corpus_totals": {
            "ast_chunks_count": len(all_ast_chunks),
            "line_chunks_count": len(all_line_chunks),
            "total_corpus_chunks": len(combined_corpus)
        },
        "ast_chunk_types_breakdown": dict(Counter(c["chunk_type"] for c in all_ast_chunks))
    }
    with open(SAMPLING_LOG, "w", encoding="utf-8") as f:
        json.dump(sampling_log_data, f, indent=2, ensure_ascii=False)

    print("-" * 80)
    print("CORPUS GENERATION SUMMARY:")
    print(f"Total source files processed: {file_count}")
    print(f"AST chunks:  Generated={ast_sampling_summary['generated']}, Rejected (<6 LOC)={ast_sampling_summary['rejected_short']}, Rejected (>85 LOC)={ast_sampling_summary['rejected_long']}, Retained={len(all_ast_chunks)}")
    print(f"Line chunks: Generated={line_sampling_summary['generated']}, Rejected (<6 LOC)={line_sampling_summary['rejected_short']}, Retained={len(all_line_chunks)}")
    print(f"Total unified chunks: {len(combined_corpus)}")
    print(f"Output files: {OUTPUT_JSONL} | {OUTPUT_PARQUET if parquet_saved else 'JSONL only'}")
    print(f"Sampling log saved: {SAMPLING_LOG}")
    print("-" * 80)


if __name__ == "__main__":
    main()
