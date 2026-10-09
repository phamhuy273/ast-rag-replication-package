"""audit_no_hardcode.py - Static AST and Regex Auditor for Experimental Integrity.

Governed by Rules R1-R46 (Section 13) of the Anti-Hardcoding Specification.
Scans codebase for:
1. Suspicious keywords ("by construction", "Scientific Finding", "placeholder", "TODO: fill", "hardcoded").
2. Silent exception defaults (e.g., `except Exception: return 0.0` or `.get(..., 1.0)`).
3. Hardcoded p-values and percentages in reporting strings (e.g., "p < 0.001", "+25.4%").
4. Hardcoded float constants returned from measurement functions.
5. AST analysis of exception handlers and measurement functions.
"""

import ast
import re
import sys
from pathlib import Path
from typing import List, Dict, Any

SUSPICIOUS_REGEXES = [
    ("SUSPICIOUS_PHRASE", re.compile(r"by construction|Scientific Finding|placeholder|TODO:\s*fill|hardcoded", re.IGNORECASE)),
    ("HARDCODED_P_OR_PCT", re.compile(r"p\s*[<=]\s*0\.0[0-9]+|\+[0-9]+\.[0-9]%", re.IGNORECASE)),
    ("HARDCODED_FLOAT_TUPLE", re.compile(r"return\s+[0-9]+\.[0-9]+(,\s*[0-9.]+)+")),
    ("SILENT_GET_DEFAULT", re.compile(r"\.get\([^)]*,\s*(1\.0|0\.[0-9]+|1)\)")),
]

class HardcodeASTVisitor(ast.NodeVisitor):
    def __init__(self, filename: str):
        self.filename = filename
        self.findings: List[Dict[str, Any]] = []

    def visit_ExceptHandler(self, node: ast.ExceptHandler):
        # Rule R6: Catch silent numeric default returns or constant assignments inside except
        for stmt in node.body:
            if isinstance(stmt, ast.Return):
                if isinstance(stmt.value, ast.Constant) and isinstance(stmt.value.value, (int, float)) and not isinstance(stmt.value.value, bool):
                    self.findings.append({
                        "file": self.filename,
                        "line": stmt.lineno,
                        "type": "AST_SILENT_EXCEPT_NUMERIC_RETURN",
                        "detail": f"Silent numeric return '{stmt.value.value}' in except handler: line {stmt.lineno}",
                    })
                elif isinstance(stmt.value, ast.Tuple):
                    # Check if tuple contains numbers (e.g. return 0.0, 1.0)
                    has_num = any(isinstance(elt, ast.Constant) and isinstance(elt.value, (int, float)) for elt in stmt.value.elts)
                    if has_num:
                        self.findings.append({
                            "file": self.filename,
                            "line": stmt.lineno,
                            "type": "AST_SILENT_EXCEPT_TUPLE_RETURN",
                            "detail": f"Silent numeric tuple return in except handler: line {stmt.lineno}",
                        })
            elif isinstance(stmt, ast.Assign):
                for target in stmt.targets:
                    if isinstance(target, ast.Name) and isinstance(stmt.value, ast.Constant):
                        if isinstance(stmt.value.value, (int, float)) and not isinstance(stmt.value.value, bool):
                            self.findings.append({
                                "file": self.filename,
                                "line": stmt.lineno,
                                "type": "AST_SILENT_EXCEPT_ASSIGN",
                                "detail": f"Silent numeric assignment '{target.id} = {stmt.value.value}' in except handler",
                            })
        self.generic_visit(node)

    def visit_FunctionDef(self, node: ast.FunctionDef):
        # Check measurement / evaluation / parser functions for suspicious constant returns
        metric_func_prefixes = ("calculate_", "measure_", "evaluate_", "compute_", "benchmark_")
        if node.name.startswith(metric_func_prefixes):
            for subnode in ast.walk(node):
                if isinstance(subnode, ast.Return) and subnode.value is not None:
                    # If returning a float constant directly
                    if isinstance(subnode.value, ast.Constant) and isinstance(subnode.value.value, float):
                        # 0.0 can be a valid edge-case return, but check if there's no logic
                        if len(node.body) <= 2:
                            self.findings.append({
                                "file": self.filename,
                                "line": subnode.lineno,
                                "type": "AST_CONSTANT_METRIC_RETURN",
                                "detail": f"Function '{node.name}' returns constant float {subnode.value.value}",
                            })
        self.generic_visit(node)


def scan_file(file_path: Path) -> List[Dict[str, Any]]:
    findings = []
    rel_path = str(file_path.as_posix())

    try:
        content = file_path.read_text(encoding="utf-8")
    except Exception as e:
        return [{"file": rel_path, "line": 0, "type": "READ_ERROR", "detail": str(e)}]

    lines = content.splitlines()

    # 1. Regex line-by-line checks
    for idx, line in enumerate(lines, start=1):
        # Skip comments explaining rules (e.g., comments mentioning R1-R46 or regex patterns themselves)
        if "audit_no_hardcode" in rel_path or "test_" in rel_path:
            continue
            
        for rule_name, pattern in SUSPICIOUS_REGEXES:
            match = pattern.search(line)
            if match:
                findings.append({
                    "file": rel_path,
                    "line": idx,
                    "type": rule_name,
                    "detail": f"Matched '{match.group(0)}' in: {line.strip()}",
                })

    # 2. Python AST checks
    if file_path.suffix == ".py":
        try:
            tree = ast.parse(content, filename=str(file_path))
            visitor = HardcodeASTVisitor(rel_path)
            visitor.visit(tree)
            findings.extend(visitor.findings)
        except SyntaxError as e:
            findings.append({
                "file": rel_path,
                "line": e.lineno or 0,
                "type": "SYNTAX_ERROR",
                "detail": str(e),
            })

    return findings


def audit_directories(dirs: List[Path]) -> List[Dict[str, Any]]:
    all_findings = []
    for d in dirs:
        if not d.exists():
            continue
        for p in d.rglob("*.py"):
            findings = scan_file(p)
            all_findings.extend(findings)
    return all_findings


def main():
    root = Path(__file__).resolve().parent.parent
    scan_dirs = [root / "scripts", root / "ai-engine"]
    findings = audit_directories(scan_dirs)

    print("=" * 80)
    print("AUDIT SCAN RESULTS: ANTI-HARDCODING RULES (R1 - R46)")
    print("=" * 80)
    print(f"Total findings detected: {len(findings)}\n")

    legacy_findings = []
    new_findings = []

    for f in findings:
        # Separate legacy scripts from new Đường B pipeline scripts
        is_legacy = any(k in f["file"] for k in [
            "evaluate_retrieval_benchmarks.py",
            "benchmark_reranker.py",
            "evaluate_rag_generation.py",
            "benchmark_chunking_corpus.py"
        ])
        if is_legacy:
            legacy_findings.append(f)
        else:
            new_findings.append(f)

    if legacy_findings:
        print(f"--- Legacy Scripts Findings ({len(legacy_findings)}) [DOCUMENTED FOR OVERHAUL] ---")
        for f in legacy_findings:
            print(f"  [{f['type']}] {f['file']}:{f['line']} -> {f['detail']}")
        print()

    if new_findings:
        print(f"--- NEW / ACTIVE PIPELINE VIOLATIONS ({len(new_findings)}) [FAIL] ---")
        for f in new_findings:
            print(f"  [{f['type']}] {f['file']}:{f['line']} -> {f['detail']}")
        print("\nERROR: Violations found in active pipeline files!")
        sys.exit(1)
    else:
        print("PASS: Zero violations found in newly developed / active pipeline files.")
        print("All legacy findings are properly inventoried for Phase 1 - Phase 5 overhaul.")
        sys.exit(0)


if __name__ == "__main__":
    main()
