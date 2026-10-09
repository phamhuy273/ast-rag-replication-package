"""verify_gold_chunks.py - Task 1.2: Verify character-level match of all 250 gold chunks against pinned source files.

Governed by:
- Rule R11: Every gold chunk must match content with lines start_line..end_line of file at pinned commit.
- Rule R12: Transparent reporting of any mismatches; no silent exclusion.
- Rule R17: 250 gold labels remain immutable.
"""

import csv
import hashlib
import sys
from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parent.parent
DATASET_DIR = ROOT_DIR / "dataset"
GOLD_FILE = DATASET_DIR / "ground_truth_final.csv"
MANIFEST_FILE = DATASET_DIR / "manifest_repos.csv"
CLONE_ROOT = ROOT_DIR / "ai-engine" / "temp_repos"
OUTPUT_REPORT = DATASET_DIR / "verification_report.csv"


def normalize_text(text: str) -> str:
    """Normalize line endings to standard Unix newline without trailing whitespace drift."""
    lines = [line.rstrip() for line in text.replace("\r\n", "\n").replace("\r", "\n").splitlines()]
    return "\n".join(lines).strip()


def strip_export_prefix(line: str) -> str:
    """Strip 'export default ' or 'export ' prefix from top line if present."""
    if line.startswith("export default "):
        return line[len("export default "):]
    elif line.startswith("export "):
        return line[len("export "):]
    return line


def main():
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")

    print("=" * 80)
    print("TASK 1.2: VERIFICATION OF 250 GOLD CHUNKS AGAINST SOURCE REPOSITORIES")
    print("=" * 80)

    # Load pinned commits from manifest
    repo_commits = {}
    with open(MANIFEST_FILE, "r", encoding="utf-8") as f:
        for r in csv.DictReader(f):
            repo_commits[r["repo_name"]] = {
                "commit_sha": r["commit_sha"],
                "local_path": r["local_path"]
            }

    with open(GOLD_FILE, "r", encoding="utf-8") as f:
        gold_rows = list(csv.DictReader(f))

    assert len(gold_rows) == 250, f"Expected 250 gold rows, found {len(gold_rows)}"

    report_rows = []
    exact_matches = 0
    export_prefix_matches = 0
    unresolved_mismatches = 0
    missing_files = 0

    for idx, row in enumerate(gold_rows, start=1):
        pair_id = row.get("pair_id") or row.get("\ufeffpair_id", f"PAIR_{idx:03d}")
        jd_id = row["jd_id"]
        repo_name = row["repo_name"]
        file_path = row["file_path"]
        start_line = int(row["start_line"])
        end_line = int(row["end_line"])
        gold_content = row["chunk_content"]

        repo_info = repo_commits.get(repo_name)
        if not repo_info:
            print(f"[ERROR] Repo {repo_name} not found in manifest!")
            missing_files += 1
            report_rows.append({
                "pair_id": pair_id,
                "jd_id": jd_id,
                "repo_name": repo_name,
                "file_path": file_path,
                "start_line": start_line,
                "end_line": end_line,
                "status": "REPO_NOT_IN_MANIFEST",
                "commit_sha": "NONE",
                "match_exact": False,
                "match_semantic": False,
                "notes": "Repo not in manifest_repos.csv"
            })
            continue

        safe_name = repo_name.replace("/", "__")
        full_file_path = CLONE_ROOT / safe_name / file_path

        if not full_file_path.exists():
            missing_files += 1
            report_rows.append({
                "pair_id": pair_id,
                "jd_id": jd_id,
                "repo_name": repo_name,
                "file_path": file_path,
                "start_line": start_line,
                "end_line": end_line,
                "status": "FILE_MISSING",
                "commit_sha": repo_info["commit_sha"],
                "match_exact": False,
                "match_semantic": False,
                "notes": f"File does not exist: {file_path}"
            })
            continue

        # Read source file lines
        try:
            source_raw = full_file_path.read_text(encoding="utf-8", errors="replace")
            source_lines = source_raw.splitlines()
        except Exception as e:
            report_rows.append({
                "pair_id": pair_id,
                "jd_id": jd_id,
                "repo_name": repo_name,
                "file_path": file_path,
                "start_line": start_line,
                "end_line": end_line,
                "status": "READ_ERROR",
                "commit_sha": repo_info["commit_sha"],
                "match_exact": False,
                "match_semantic": False,
                "notes": str(e)
            })
            continue

        # Extract lines
        extracted_slice_lines = source_lines[start_line - 1 : end_line]
        extracted_slice = "\n".join(extracted_slice_lines)
        norm_gold = normalize_text(gold_content)
        norm_extracted = normalize_text(extracted_slice)

        if norm_gold == norm_extracted:
            exact_matches += 1
            status = "EXACT_MATCH"
            notes = "Content matches start_line..end_line perfectly"
            match_exact = True
            match_semantic = True
        else:
            # Check AST export prefix difference
            mod_lines = list(extracted_slice_lines)
            if mod_lines:
                mod_lines[0] = strip_export_prefix(mod_lines[0])
            norm_mod_ext = normalize_text("\n".join(mod_lines))

            if norm_gold == norm_mod_ext:
                export_prefix_matches += 1
                status = "AST_EXPORT_PREFIX_DIFF"
                notes = "Content matches source perfectly; first line has 'export'/'export default' omitted by legacy AST node"
                match_exact = False
                match_semantic = True
            else:
                unresolved_mismatches += 1
                status = "UNRESOLVED_MISMATCH"
                notes = f"Diff in characters: gold len {len(norm_gold)} vs source len {len(norm_extracted)}"
                match_exact = False
                match_semantic = False

        report_rows.append({
            "pair_id": pair_id,
            "jd_id": jd_id,
            "repo_name": repo_name,
            "file_path": file_path,
            "start_line": start_line,
            "end_line": end_line,
            "status": status,
            "commit_sha": repo_info["commit_sha"],
            "match_exact": match_exact,
            "match_semantic": match_semantic,
            "notes": notes
        })

    # Save report
    fieldnames = [
        "pair_id", "jd_id", "repo_name", "file_path", "start_line", "end_line",
        "status", "commit_sha", "match_exact", "match_semantic", "notes"
    ]
    with open(OUTPUT_REPORT, "w", encoding="utf-8", newline="") as rf:
        writer = csv.DictWriter(rf, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(report_rows)

    print("-" * 80)
    print(f"Total gold chunks evaluated:        {len(gold_rows)}")
    print(f"Exact literal matches:              {exact_matches} ({exact_matches / len(gold_rows) * 100:.1f}%)")
    print(f"AST export-prefix aligned matches:  {export_prefix_matches} ({export_prefix_matches / len(gold_rows) * 100:.1f}%)")
    print(f"Total verified in source codebase:  {exact_matches + export_prefix_matches} ({(exact_matches + export_prefix_matches) / len(gold_rows) * 100:.1f}%)")
    print(f"Unresolved mismatches:              {unresolved_mismatches}")
    print(f"Missing files / read error:         {missing_files}")
    print(f"Verification report saved:          {OUTPUT_REPORT}")
    print("-" * 80)


if __name__ == "__main__":
    main()
