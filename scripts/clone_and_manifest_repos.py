"""clone_and_manifest_repos.py - Task 1.1: Clone 40 repos, pin commit SHAs, licenses, and manifest files.

Governed by:
- Rule R11: Uniqueness of repos and files (exactly 40 repos, 189 files).
- Rule R40, R41: License verification and provenance tracking.
- Rule R43: Stop and report immediately if any repo or file count mismatches.
"""

import csv
import os
import shutil
import subprocess
import sys
from pathlib import Path
from typing import Dict, List, Set

ROOT_DIR = Path(__file__).resolve().parent.parent
DATASET_DIR = ROOT_DIR / "dataset"
MASTER_FILE = DATASET_DIR / "ground_truth_500_master.csv"
JAVA_REPOS_LIST = DATASET_DIR / "repositories_list" / "java_repos_cleaned.csv"
REACT_REPOS_LIST = DATASET_DIR / "repositories_list" / "react_ts_repos_cleaned.csv"
OUTPUT_MANIFEST = DATASET_DIR / "manifest_repos.csv"
CLONE_ROOT = ROOT_DIR / "ai-engine" / "temp_repos"


def get_repo_metadata() -> Dict[str, Dict[str, str]]:
    meta = {}
    for p in [JAVA_REPOS_LIST, REACT_REPOS_LIST]:
        if p.exists():
            with open(p, "r", encoding="utf-8") as f:
                reader = csv.DictReader(f)
                for r in reader:
                    rname = r.get("repo_name", "").strip()
                    if rname:
                        meta[rname] = {
                            "url": r.get("url", f"https://github.com/{rname}").strip(),
                            "language": r.get("language", "Unknown").strip(),
                            "domain": r.get("domain", "").strip()
                        }
    return meta


def detect_license(repo_dir: Path) -> str:
    """Inspect root directory for open-source license file."""
    license_names = ["LICENSE", "LICENSE.md", "LICENSE.txt", "license", "license.txt", "COPYING"]
    for name in license_names:
        lp = repo_dir / name
        if lp.exists():
            try:
                first_lines = lp.read_text(encoding="utf-8", errors="ignore").splitlines()[:5]
                text = " ".join(first_lines).strip()
                if "MIT" in text:
                    return "MIT"
                elif "Apache" in text or "Apache License" in text:
                    return "Apache-2.0"
                elif "General Public License" in text or "GPL" in text:
                    return "GPL"
                elif "BSD" in text:
                    return "BSD"
                elif "Mozilla" in text:
                    return "MPL"
                elif text:
                    return text[:30]
            except Exception:
                return "Custom License File Present"
    return "Not specified (Public GitHub)"


def main():
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")

    print("=" * 80)
    print("TASK 1.1: REPOSITORY CLONING & MANIFEST GENERATION (40 REPOS / 189 FILES)")
    print("=" * 80)

    # 1. Load 40 repos and 189 files from master file
    with open(MASTER_FILE, "r", encoding="utf-8") as f:
        master_rows = list(csv.DictReader(f))

    repo_to_files: Dict[str, Set[str]] = {}
    for r in master_rows:
        repo_to_files.setdefault(r["repo_name"], set()).add(r["file_path"])

    assert len(repo_to_files) == 40, f"Expected 40 repos in master, found {len(repo_to_files)}"
    total_files = sum(len(fs) for fs in repo_to_files.values())
    assert total_files == 189, f"Expected 189 unique files in master, found {total_files}"

    repo_meta = get_repo_metadata()
    CLONE_ROOT.mkdir(parents=True, exist_ok=True)

    manifest_rows = []
    failed_repos = []
    missing_files_total = []

    for idx, (repo_name, files) in enumerate(sorted(repo_to_files.items()), start=1):
        meta = repo_meta.get(repo_name, {})
        url = meta.get("url", f"https://github.com/{repo_name}")
        lang = meta.get("language", "Java" if any(f.endswith(".java") for f in files) else "TypeScript")

        # Destination path: use safe repo dir name (replace slash with __)
        safe_name = repo_name.replace("/", "__")
        repo_dir = CLONE_ROOT / safe_name

        print(f"[{idx:02d}/40] {repo_name} ({lang}) -> {len(files)} files")

        # Clone or update
        if not repo_dir.exists():
            clone_cmd = ["git", "clone", "--depth", "50", url, str(repo_dir)]
            res = subprocess.run(clone_cmd, capture_output=True, text=True)
            if res.returncode != 0:
                print(f"  [ERROR] Git clone failed: {res.stderr.strip()[:120]}")
                failed_repos.append((repo_name, res.stderr.strip()))
                continue

        # Get pinned commit SHA
        sha_res = subprocess.run(["git", "rev-parse", "HEAD"], cwd=str(repo_dir), capture_output=True, text=True)
        commit_sha = sha_res.stdout.strip() if sha_res.returncode == 0 else "UNKNOWN"

        license_name = detect_license(repo_dir)

        # Check that all expected files exist in this repo
        repo_missing = []
        for file_p in sorted(files):
            full_path = repo_dir / file_p
            if not full_path.exists():
                repo_missing.append(file_p)
                missing_files_total.append((repo_name, file_p))

        if repo_missing:
            print(f"  [WARNING] {len(repo_missing)}/{len(files)} files missing in HEAD!")
            for mf in repo_missing:
                print(f"    - Missing: {mf}")
        else:
            print(f"  [OK] SHA: {commit_sha[:10]} | License: {license_name} | All {len(files)} files present")

        manifest_rows.append({
            "repo_name": repo_name,
            "url": url,
            "language": lang,
            "commit_sha": commit_sha,
            "license": license_name,
            "expected_file_count": len(files),
            "found_file_count": len(files) - len(repo_missing),
            "files_list": "; ".join(sorted(files)),
            "local_path": f"ai-engine/temp_repos/{safe_name}"
        })

    # Save manifest
    fieldnames = [
        "repo_name", "url", "language", "commit_sha", "license",
        "expected_file_count", "found_file_count", "files_list", "local_path"
    ]
    with open(OUTPUT_MANIFEST, "w", encoding="utf-8", newline="") as mf:
        writer = csv.DictWriter(mf, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(manifest_rows)

    print("-" * 80)
    print(f"Generated manifest: {OUTPUT_MANIFEST} with {len(manifest_rows)} repos.")
    print(f"Failed clones: {len(failed_repos)}")
    print(f"Missing files across all repos: {len(missing_files_total)}")

    if failed_repos or missing_files_total:
        print("\n[CRITICAL RULE R43] Anomalies detected! Details:")
        if failed_repos:
            print("Failed repos:", failed_repos)
        if missing_files_total:
            print("Missing files:", missing_files_total)
        sys.exit(1)
    else:
        print("\nSUCCESS: All 40 repos cloned, all 189 files verified present in HEAD!")
        sys.exit(0)


if __name__ == "__main__":
    main()
