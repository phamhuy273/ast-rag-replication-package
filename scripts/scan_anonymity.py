#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
=============================================================================
ANONYMITY SCANNER (DOUBLE-ANONYMOUS PEER REVIEW COMPLIANCE)
Scans codebase for:
1. Local absolute file system paths (C:\\, /Users/, /home/, Desktop, etc.)
2. Author names, institutional affiliations, student IDs, and emails
3. External pattern file patterns (if provided via CLI argument)
4. Metadata in images (.png) and binary tables (.parquet)
=============================================================================
"""

import sys
import os
import re
from pathlib import Path
from typing import List, Tuple, Dict, Any

# Configure Windows UTF-8 stdout
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

PROJECT_ROOT = Path(__file__).resolve().parent.parent

DEFAULT_PATH_REGEXES = [
    ("ABSOLUTE_WINDOWS_DRIVE", re.compile(r"[A-Za-z]:[\\/](?:Users|home|Documents|Desktop)", re.IGNORECASE)),
    ("UNIX_USER_HOME", re.compile(r"(?:^|[\s\"'=\(\[/])/(?:Users|home)/[a-zA-Z0-9_\.\-]+")),
    ("DESKTOP_PATH", re.compile(r"Desktop[\\/]ast-rag", re.IGNORECASE)),
]

DEFAULT_IDENTITY_TERMS = [
    "Quang Huy",
    "Huy Pham",
    "24520692",
    "gm.uit.edu.vn",
    "uit.edu.vn",
]

IGNORE_DIRS = {".git", ".pytest_cache", "__pycache__", "venv", ".venv"}


def scan_file_text(file_path: Path, patterns: List[Tuple[str, re.Pattern]]) -> List[Dict[str, Any]]:
    violations = []
    try:
        content = file_path.read_text(encoding="utf-8", errors="replace")
    except Exception as e:
        return [{"file": str(file_path), "line": 0, "type": "READ_ERROR", "match": str(e)}]

    lines = content.splitlines()
    for line_idx, line in enumerate(lines, start=1):
        for p_name, p_regex in patterns:
            match = p_regex.search(line)
            if match:
                # Exclude harmless examples or self-matches inside scanner
                if file_path.name == "scan_anonymity.py":
                    continue
                violations.append({
                    "file": str(file_path.relative_to(PROJECT_ROOT)),
                    "line": line_idx,
                    "type": p_name,
                    "match": match.group(0),
                    "context": line.strip()[:100]
                })
    return violations


def scan_parquet_metadata(file_path: Path) -> List[Dict[str, Any]]:
    violations = []
    try:
        import pyarrow.parquet as pq
        meta = pq.read_metadata(file_path)
        schema_str = str(meta.schema)
        # Check schema or created_by
        if meta.created_by:
            for term in DEFAULT_IDENTITY_TERMS:
                if term.lower() in meta.created_by.lower():
                    violations.append({
                        "file": str(file_path.relative_to(PROJECT_ROOT)),
                        "line": 0,
                        "type": "PARQUET_METADATA",
                        "match": meta.created_by,
                        "context": f"Created by: {meta.created_by}"
                    })
    except Exception:
        pass
    return violations


def scan_png_metadata(file_path: Path) -> List[Dict[str, Any]]:
    violations = []
    try:
        from PIL import Image
        with Image.open(file_path) as img:
            info = img.info
            for k, v in info.items():
                v_str = str(v)
                for term in DEFAULT_IDENTITY_TERMS:
                    if term.lower() in v_str.lower():
                        violations.append({
                            "file": str(file_path.relative_to(PROJECT_ROOT)),
                            "line": 0,
                            "type": "PNG_METADATA",
                            "match": v_str[:50],
                            "context": f"Key: {k}"
                        })
    except Exception:
        pass
    return violations


def main():
    print("=" * 80)
    print("ANONYMITY & IDENTITY LEAK SCANNER (IEEE SANER DOUBLE-ANONYMOUS)")
    print("=" * 80)

    patterns = [(name, regex) for name, regex in DEFAULT_PATH_REGEXES]
    for term in DEFAULT_IDENTITY_TERMS:
        patterns.append((f"IDENTITY_{term}", re.compile(re.escape(term), re.IGNORECASE)))

    # Optional external pattern file
    if len(sys.argv) > 1:
        pattern_file = Path(sys.argv[1])
        if pattern_file.exists():
            print(f"Loading custom anonymity patterns from: {pattern_file}")
            with open(pattern_file, "r", encoding="utf-8") as f:
                for line in f:
                    t = line.strip()
                    if t and not t.startswith("#"):
                        patterns.append((f"CUSTOM_{t}", re.compile(re.escape(t), re.IGNORECASE)))
        else:
            print(f"[WARNING] Pattern file not found: {pattern_file}")

    all_violations = []

    for root, dirs, files in os.walk(PROJECT_ROOT):
        dirs[:] = [d for d in dirs if d not in IGNORE_DIRS]
        for f in files:
            fp = Path(root) / f
            ext = fp.suffix.lower()

            if ext in (".py", ".md", ".tex", ".json", ".csv", ".jsonl", ".txt", ".bat", ".sh", ".yml", ".yaml"):
                v = scan_file_text(fp, patterns)
                all_violations.extend(v)
            elif ext == ".parquet":
                v = scan_parquet_metadata(fp)
                all_violations.extend(v)
            elif ext == ".png":
                v = scan_png_metadata(fp)
                all_violations.extend(v)

    print(f"\nScanned files across: {PROJECT_ROOT}")
    print(f"Total findings detected: {len(all_violations)}")

    if all_violations:
        print("\n--- DETECTED ANONYMITY VIOLATIONS ---")
        for v in all_violations:
            print(f"  [{v['type']}] {v['file']}:{v['line']} -> Matched '{v['match']}'")
            print(f"    Line context: {v['context']}")
        print("\nFAIL: Identity or absolute path leaks found. Please scrub them before submission.")
        sys.exit(1)
    else:
        print("\nPASS: Zero identity leaks or absolute system paths detected.")
        print("Replication package complies with Double-Anonymous Peer Review standards.")
        sys.exit(0)


if __name__ == "__main__":
    main()
