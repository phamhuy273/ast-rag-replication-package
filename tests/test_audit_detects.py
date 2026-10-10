"""tests/test_audit_detects.py - Unit tests verifying that audit_no_hardcode catches all integrity violations.

Governed by Task A5 of the SANER 2027 ERA audit enhancement protocol:
Verify that the static AST analyzer detects:
(a) Except handlers returning or assigning numeric/dict constants.
(b) .get(..., <numeric_constant>) in measurement functions.
(c) Silent guard clauses 'if not x: return False/0/None' in measurement/parsing paths.
(d) Dict literals with hardcoded metric keys and numeric scores.
(e) Hardcoded p-values in reporting strings.
(f) Local absolute file paths.
"""

import sys
import tempfile
from pathlib import Path
import pytest

ROOT_DIR = Path(__file__).resolve().parent.parent
sys.path.append(str(ROOT_DIR / "scripts"))
from audit_no_hardcode import scan_file


class TestAuditDetectsViolations:
    """Ensures audit_no_hardcode.py reliably detects all experimental integrity anti-patterns."""

    def test_detects_silent_except_numeric_return(self, tmp_path):
        bad_code = """
def calculate_metric():
    try:
        val = 1 / 0
    except Exception:
        return 0.0
"""
        f = tmp_path / "bad_except_num.py"
        f.write_text(bad_code, encoding="utf-8")
        findings = scan_file(f)
        types = [f["type"] for f in findings]
        assert "AST_SILENT_EXCEPT_NUMERIC_RETURN" in types

    def test_detects_silent_except_dict_assign(self, tmp_path):
        bad_code = """
def run():
    try:
        res = compute()
    except Exception:
        res = {"score": 1.0}
"""
        f = tmp_path / "bad_except_dict.py"
        f.write_text(bad_code, encoding="utf-8")
        findings = scan_file(f)
        types = [f["type"] for f in findings]
        assert "AST_SILENT_EXCEPT_DICT_ASSIGN" in types

    def test_detects_silent_guard_return(self, tmp_path):
        bad_code = """
def check_syntax_error(code, lang):
    parser = get_parser(lang)
    if not parser:
        return False
    return True
"""
        f = tmp_path / "bad_guard.py"
        f.write_text(bad_code, encoding="utf-8")
        findings = scan_file(f)
        types = [f["type"] for f in findings]
        assert "AST_SILENT_GUARD_RETURN" in types

    def test_detects_silent_get_default(self, tmp_path):
        bad_code = """
def evaluate_query(item):
    score = item.get("score", 1.0)
    return score
"""
        f = tmp_path / "bad_get.py"
        f.write_text(bad_code, encoding="utf-8")
        findings = scan_file(f)
        types = [f["type"] for f in findings]
        assert "AST_SILENT_GET_DEFAULT" in types

    def test_detects_hardcoded_metric_dict(self, tmp_path):
        bad_code = """
def assign_dummy():
    result = {"faithfulness_score": 1.0, "citation_coverage": 0.8}
    return result
"""
        f = tmp_path / "bad_dict.py"
        f.write_text(bad_code, encoding="utf-8")
        findings = scan_file(f)
        types = [f["type"] for f in findings]
        assert "AST_HARDCODED_METRIC_DICT" in types

    def test_detects_hardcoded_p_value(self, tmp_path):
        bad_code = 'print("Significance achieved at p <= 0.001")\n'
        f = tmp_path / "bad_p.py"
        f.write_text(bad_code, encoding="utf-8")
        findings = scan_file(f)
        types = [f["type"] for f in findings]
        assert "HARDCODED_P_VALUE" in types

    def test_detects_absolute_path(self, tmp_path):
        bad_code = f'my_dir = "{"C:"}/{"Users"}/test_user/workspace"\n'
        f = tmp_path / "bad_path.py"
        f.write_text(bad_code, encoding="utf-8")
        findings = scan_file(f)
        types = [f["type"] for f in findings]
        assert "ABSOLUTE_PATH" in types
