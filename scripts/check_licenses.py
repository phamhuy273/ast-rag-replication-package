#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
=============================================================================
LICENSE CHECKER & PROVENANCE AUDITOR (CONCURRENT)
Fetches license files at pinned commit SHAs from GitHub for all 40 repositories
and audits license distribution against manifest_repos.csv.
=============================================================================
"""

import csv
import sys
from concurrent.futures import ThreadPoolExecutor
from urllib.request import urlopen, Request
from urllib.error import HTTPError
from pathlib import Path
from typing import Dict, Tuple

# Configure Windows UTF-8 stdout
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

PROJECT_ROOT = Path(__file__).resolve().parent.parent
MANIFEST_FILE = PROJECT_ROOT / "dataset" / "manifest_repos.csv"

LICENSE_CANDIDATE_NAMES = [
    "LICENSE", "LICENSE.md", "LICENSE.txt",
    "license", "license.md", "license.txt",
    "COPYING", "COPYING.txt"
]


def detect_license_text(text: str) -> str:
    """Classify license text based on standard SPDX identifiers."""
    t = text.lower()
    if "affero general public license" in t or "agpl" in t:
        return "AGPL-3.0"
    elif "gnu general public license" in t or "gpl v" in t or "gpl-3" in t:
        return "GPL-3.0"
    elif "apache license, version 2.0" in t or "apache-2.0" in t:
        return "Apache-2.0"
    elif "mit license" in t or "permission is hereby granted, free of charge" in t:
        return "MIT"
    elif "bsd 3-clause" in t or "neither the name of" in t:
        return "BSD-3-Clause"
    elif "bsd 2-clause" in t:
        return "BSD-2-Clause"
    elif "mozilla public license" in t:
        return "MPL-2.0"
    elif len(text.strip()) > 30:
        return "Custom License"
    return "Not specified (Public GitHub)"


def check_repo_license(row: Dict[str, str]) -> Tuple[Dict[str, str], str]:
    repo = row["repo_name"]
    sha = row["commit_sha"]
    existing_lic = row.get("license", "Unknown")
    headers = {"User-Agent": "Mozilla/5.0"}

    detected = "Not specified (Public GitHub)"
    for lic_name in LICENSE_CANDIDATE_NAMES:
        url = f"https://raw.githubusercontent.com/{repo}/{sha}/{lic_name}"
        try:
            req = Request(url, headers=headers)
            with urlopen(req, timeout=5) as resp:
                content = resp.read().decode("utf-8", errors="replace")
                det = detect_license_text(content)
                if det != "Not specified (Public GitHub)":
                    detected = det
                    break
        except Exception:
            continue

    # Normalize AGPL
    if "AFFERO" in existing_lic and detected == "AGPL-3.0":
        detected = "AGPL-3.0"

    row_copy = dict(row)
    if detected != "Not specified (Public GitHub)":
        row_copy["license"] = detected
    return row_copy, detected


def main():
    print("=" * 80)
    print("TASK A3: AUDITING OPEN-SOURCE LICENSES ACROSS 40 REPOSITORIES")
    print("=" * 80)
    sys.stdout.flush()

    with open(MANIFEST_FILE, "r", encoding="utf-8") as f:
        rows = list(csv.DictReader(f))

    print(f"Loaded {len(rows)} repositories from {MANIFEST_FILE.name}")
    print("Querying GitHub at pinned commit SHAs with 16 worker threads...")
    sys.stdout.flush()

    with ThreadPoolExecutor(max_workers=16) as executor:
        results = list(executor.map(check_repo_license, rows))

    updated_rows = []
    changes = 0
    for orig, (updated, detected) in zip(rows, results):
        if orig.get("license") != updated.get("license"):
            print(f"  [UPDATED] {orig['repo_name']}: '{orig.get('license')}' -> '{updated.get('license')}'")
            changes += 1
        updated_rows.append(updated)

    print("-" * 80)
    print(f"Audit complete. Total repositories: {len(rows)}. Re-classified: {changes}")
    from collections import Counter
    summary = Counter(r["license"] for r in updated_rows)
    for lic, cnt in summary.most_common():
        print(f"  - {lic}: {cnt} repos ({cnt / len(rows) * 100:.1f}%)")

    if changes > 0:
        with open(MANIFEST_FILE, "w", encoding="utf-8", newline="") as f:
            writer = csv.DictWriter(f, fieldnames=list(rows[0].keys()))
            writer.writeheader()
            writer.writerows(updated_rows)
        print(f"Updated {MANIFEST_FILE.name} with verified license classifications.")
    sys.stdout.flush()


if __name__ == "__main__":
    main()
