"""benchmark_fallback_rate.py - Measure AST vs Fallback line-chunking rates across the 189 files.

Governed by Task 1.3 and Rules R5, R10 of the Anti-Hardcoding Specification:
Evaluate real AST fallback rates dynamically on all 189 corpus source files across 40 repositories.
"""

import csv
import sys
from pathlib import Path
from collections import Counter

ROOT_DIR = Path(__file__).resolve().parent.parent
sys.path.append(str(ROOT_DIR / "ai-engine"))
from parser.tree_sitter_loader import ast_loader

MANIFEST_FILE = ROOT_DIR / "dataset" / "manifest_repos.csv"
CLONE_ROOT = ROOT_DIR / "ai-engine" / "temp_repos"
OUTPUT_REPORT = ROOT_DIR / "dataset" / "fallback_rate_report.csv"


def main():
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")

    print("=" * 80)
    print("TASK 1.3: BENCHMARKING AST PARSER & FALLBACK RATE ACROSS 189 CORPUS FILES")
    print("=" * 80)

    # 1. Gather all 189 files from manifest
    with open(MANIFEST_FILE, "r", encoding="utf-8") as f:
        manifest = list(csv.DictReader(f))

    file_entries = []
    for repo in manifest:
        rname = repo["repo_name"]
        lang = repo["language"]
        files = [f.strip() for f in repo["files_list"].split(";") if f.strip()]
        for fp in files:
            file_entries.append({
                "repo_name": rname,
                "file_path": fp,
                "repo_language": lang,
                "local_path": repo["local_path"]
            })

    assert len(file_entries) == 189, f"Expected 189 files, found {len(file_entries)}"

    results = []
    chunk_type_counts = Counter()
    java_files = 0
    java_fallbacks = 0
    react_files = 0
    react_fallbacks = 0

    for idx, fe in enumerate(file_entries, start=1):
        safe_name = fe["repo_name"].replace("/", "__")
        full_path = CLONE_ROOT / safe_name / fe["file_path"]
        assert full_path.exists(), f"Missing file: {full_path}"

        code = full_path.read_text(encoding="utf-8", errors="replace")
        ext = full_path.suffix.lower()
        if ext == ".java":
            parser_lang = "java"
            category = "JAVA"
            java_files += 1
        elif ext in (".tsx", ".jsx"):
            parser_lang = "tsx"
            category = "REACT_TS"
            react_files += 1
        else:
            parser_lang = "typescript"
            category = "REACT_TS"
            react_files += 1

        chunks = ast_loader.parse_and_chunk(fe["file_path"], code, language=parser_lang)
        is_fallback = any(c["chunk_type"] == "LINE_FALLBACK" for c in chunks)

        if is_fallback:
            if category == "JAVA":
                java_fallbacks += 1
            else:
                react_fallbacks += 1

        types_in_file = set(c["chunk_type"] for c in chunks)
        for c in chunks:
            chunk_type_counts[c["chunk_type"]] += 1

        results.append({
            "repo_name": fe["repo_name"],
            "file_path": fe["file_path"],
            "category": category,
            "total_lines": len(code.splitlines()),
            "chunk_count": len(chunks),
            "is_fallback": is_fallback,
            "chunk_types": "; ".join(sorted(types_in_file))
        })

    # Save detailed report
    fieldnames = ["repo_name", "file_path", "category", "total_lines", "chunk_count", "is_fallback", "chunk_types"]
    with open(OUTPUT_REPORT, "w", encoding="utf-8", newline="") as rf:
        writer = csv.DictWriter(rf, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(results)

    total_files = len(file_entries)
    total_fallbacks = java_fallbacks + react_fallbacks

    print("-" * 80)
    print("FALLBACK RATE EVALUATION SUMMARY:")
    print(f"Total source files evaluated: {total_files}")
    print(f"  - Java files:     {java_files:3d} | Fallbacks: {java_fallbacks:2d} ({java_fallbacks/java_files*100:5.2f}%)")
    print(f"  - React/TS files: {react_files:3d} | Fallbacks: {react_fallbacks:2d} ({react_fallbacks/react_files*100:5.2f}%)")
    print(f"  - Overall:        {total_files:3d} | Fallbacks: {total_fallbacks:2d} ({total_fallbacks/total_files*100:5.2f}%)")
    print("\nCHUNK TYPE BREAKDOWN ACROSS ENTIRE CORPUS:")
    for ctype, count in chunk_type_counts.most_common():
        print(f"  - {ctype:22s}: {count:4d} chunks ({count / sum(chunk_type_counts.values()) * 100:5.2f}%)")
    print(f"Total AST chunks extracted: {sum(chunk_type_counts.values())}")
    print(f"Detailed file report saved to: {OUTPUT_REPORT}")
    print("-" * 80)


if __name__ == "__main__":
    main()
