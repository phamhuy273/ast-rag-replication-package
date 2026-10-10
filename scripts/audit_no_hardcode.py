#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
=============================================================================
AUDIT NO HARDCODE (RULES R1 - R46 EXPERIMENTAL INTEGRITY AUDITOR)
Governed by Anti-Hardcoding Specification (Section 13).
Scans all active scripts/ and ai-engine/ files for:
1. (a) Except handlers returning or assigning numeric or dict constants (silent fallbacks).
2. (b) Dictionary .get(..., <numeric_constant>) in measurement paths.
3. (c) Guard clauses 'if not x: return False/0/None' in measurement/parser functions.
4. (d) Dict literals containing metric keys paired with constant numeric scores.
5. (e) Pre-written conclusion strings or hardcoded p-values / percentages.
6. (f) Hardcoded absolute system paths (e.g., C:\\, /Users/, /home/).
=============================================================================
"""

import ast
import re
import sys
from pathlib import Path
from typing import List, Dict, Any

# Configure Windows UTF-8 stdout
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

SUSPICIOUS_REGEXES = [
    ("SUSPICIOUS_PHRASE", re.compile(r"by construction|placeholder|TODO:\s*fill|hardcoded", re.IGNORECASE)),
    ("HARDCODED_P_VALUE", re.compile(r"p\s*(?:<=|>=|<|>|=)\s*0\.0[0-9]+", re.IGNORECASE)),
    ("HARDCODED_FLOAT_TUPLE", re.compile(r"return\s+[0-9]+\.[0-9]+(,\s*[0-9.]+)+")),
    ("ABSOLUTE_PATH", re.compile(r"[A-Za-z]:[\\/](?:Users|home|Documents|Desktop)|/(?:Users|home)/[a-zA-Z0-9_\.\-]+", re.IGNORECASE)),
]

METRIC_DICT_KEYS = {
    "faithfulness_score", "answer_relevance_score", "citation_coverage",
    "supported_claims", "ndcg@10", "ndcg@1", "mrr@10", "boundary_intact_rate"
}

MEASUREMENT_FUNC_PREFIXES = (
    "calculate_", "measure_", "evaluate_", "compute_", "benchmark_",
    "check_syntax", "extract_method"
)


class ComprehensiveHardcodeASTVisitor(ast.NodeVisitor):
    def __init__(self, filename: str):
        self.filename = filename
        self.findings: List[Dict[str, Any]] = []
        self.current_function: str = ""

    def visit_FunctionDef(self, node: ast.FunctionDef):
        old_func = self.current_function
        self.current_function = node.name
        self.generic_visit(node)
        self.current_function = old_func

    def visit_AsyncFunctionDef(self, node: ast.AsyncFunctionDef):
        old_func = self.current_function
        self.current_function = node.name
        self.generic_visit(node)
        self.current_function = old_func

    def visit_ExceptHandler(self, node: ast.ExceptHandler):
        # Rule R6: Catch silent numeric/dict default returns or constant assignments inside except
        for stmt in node.body:
            if isinstance(stmt, ast.Return):
                if isinstance(stmt.value, ast.Constant) and isinstance(stmt.value.value, (int, float)) and not isinstance(stmt.value.value, bool):
                    self.findings.append({
                        "file": self.filename,
                        "line": stmt.lineno,
                        "type": "AST_SILENT_EXCEPT_NUMERIC_RETURN",
                        "detail": f"Silent numeric return '{stmt.value.value}' in except handler: line {stmt.lineno}",
                    })
                elif isinstance(stmt.value, ast.Dict):
                    self.findings.append({
                        "file": self.filename,
                        "line": stmt.lineno,
                        "type": "AST_SILENT_EXCEPT_DICT_RETURN",
                        "detail": f"Silent dict fallback return in except handler: line {stmt.lineno}",
                    })
                elif isinstance(stmt.value, ast.Tuple):
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
                    if isinstance(stmt.value, ast.Constant) and isinstance(stmt.value.value, (int, float)) and not isinstance(stmt.value.value, bool):
                        t_name = getattr(target, "id", "variable")
                        self.findings.append({
                            "file": self.filename,
                            "line": stmt.lineno,
                            "type": "AST_SILENT_EXCEPT_ASSIGN",
                            "detail": f"Silent numeric assignment '{t_name} = {stmt.value.value}' in except handler",
                        })
                    elif isinstance(stmt.value, ast.Dict):
                        t_name = getattr(target, "id", "variable")
                        self.findings.append({
                            "file": self.filename,
                            "line": stmt.lineno,
                            "type": "AST_SILENT_EXCEPT_DICT_ASSIGN",
                            "detail": f"Silent fallback dict assignment to '{t_name}' in except handler",
                        })
        self.generic_visit(node)

    def visit_If(self, node: ast.If):
        # Catch 'if not x: return False/0/None' inside measurement functions
        if self.current_function and self.current_function.startswith(MEASUREMENT_FUNC_PREFIXES):
            # Check if test is 'not ...'
            is_not_check = isinstance(node.test, ast.UnaryOp) and isinstance(node.test.op, ast.Not)
            if is_not_check:
                for stmt in node.body:
                    if isinstance(stmt, ast.Return) and isinstance(stmt.value, ast.Constant):
                        if stmt.value.value in (False, 0, 0.0, None):
                            self.findings.append({
                                "file": self.filename,
                                "line": stmt.lineno,
                                "type": "AST_SILENT_GUARD_RETURN",
                                "detail": f"Function '{self.current_function}' silently returns '{stmt.value.value}' on guard failure: line {stmt.lineno}",
                            })
        self.generic_visit(node)

    def visit_Dict(self, node: ast.Dict):
        # Catch literal dicts with metric keys and numeric constant values
        for k, v in zip(node.keys, node.values):
            if isinstance(k, ast.Constant) and isinstance(k.value, str):
                key_str = k.value.lower()
                if key_str in METRIC_DICT_KEYS and isinstance(v, ast.Constant) and isinstance(v.value, (int, float)):
                    # Allow if it's inside a test or test generator, otherwise flag
                    self.findings.append({
                        "file": self.filename,
                        "line": k.lineno,
                        "type": "AST_HARDCODED_METRIC_DICT",
                        "detail": f"Hardcoded metric key '{k.value}' with constant value '{v.value}' in dict literal: line {k.lineno}",
                    })
        self.generic_visit(node)

    def visit_Call(self, node: ast.Call):
        # Catch .get(..., <numeric_constant>) in measurement functions
        if self.current_function and self.current_function.startswith(MEASUREMENT_FUNC_PREFIXES):
            if isinstance(node.func, ast.Attribute) and node.func.attr == "get":
                if len(node.args) >= 2 and isinstance(node.args[1], ast.Constant):
                    def_val = node.args[1].value
                    if isinstance(def_val, (int, float)) and not isinstance(def_val, bool):
                        self.findings.append({
                            "file": self.filename,
                            "line": node.lineno,
                            "type": "AST_SILENT_GET_DEFAULT",
                            "detail": f"Function '{self.current_function}' calls .get() with default numeric constant '{def_val}': line {node.lineno}",
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
        if file_path.name.startswith("test_") or "audit_no_hardcode" in file_path.name:
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
            visitor = ComprehensiveHardcodeASTVisitor(rel_path)
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
    print("Scope: All active scripts/ and ai-engine/ files")
    print("=" * 80)
    print(f"Total findings detected: {len(findings)}\n")

    if findings:
        print(f"--- DETECTED VIOLATIONS ({len(findings)}) [FAIL] ---")
        for f in findings:
            print(f"  [{f['type']}] {f['file']}:{f['line']} -> {f['detail']}")
        print("\nERROR: Violations found in replication package files!")
        sys.exit(1)
    else:
        print("PASS: Zero violations found across all pipeline and engine files.")
        print("All empirical evaluations adhere to Anti-Hardcoding Rules R1 - R46.")
        sys.exit(0)


if __name__ == "__main__":
    main()
