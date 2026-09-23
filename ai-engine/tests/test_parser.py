import pytest
from parser.tree_sitter_loader import ASTParserLoader

@pytest.fixture
def parser_loader():
    return ASTParserLoader()

def test_ast_chunking_java(parser_loader):
    sample_java = """package com.example;

public class Calculator {
    public int add(int a, int b) {
        return a + b;
    }

    public int subtract(int a, int b) {
        return a - b;
    }
}
"""
    chunks = parser_loader.parse_and_chunk("Calculator.java", sample_java, language="java")
    assert len(chunks) >= 2
    # Check that methods were extracted
    methods = [c["chunk_content"] for c in chunks]
    assert any("add" in m for m in methods)
    assert any("subtract" in m for m in methods)
    assert chunks[0]["file_path"] == "Calculator.java"
    assert "// File: Calculator.java" in chunks[0]["context_header"]

def test_ast_chunking_javascript(parser_loader):
    sample_js = """function greet(name) {
    return 'Hello, ' + name;
}

function farewell(name) {
    return 'Goodbye, ' + name;
}
"""
    chunks = parser_loader.parse_and_chunk("utils.js", sample_js, language="javascript")
    assert len(chunks) >= 2
    methods = [c["chunk_content"] for c in chunks]
    assert any("greet" in m for m in methods)
    assert any("farewell" in m for m in methods)

def test_fallback_line_chunking_on_syntax_error(parser_loader):
    # Syntax error with missing braces
    invalid_code = "public class Broken { void test() { if (true) { " * 20
    chunks = parser_loader.parse_and_chunk("Broken.java", invalid_code, language="java")
    assert len(chunks) > 0
    # Fallback line chunking should produce chunks
    assert all(c["chunk_type"] in ("LINE_FALLBACK", "AST_METHOD") for c in chunks)
    assert all("Broken.java" in c["context_header"] for c in chunks)

def test_fallback_line_chunking_directly(parser_loader):
    lines = [f"System.out.println({i});" for i in range(120)]
    source = "\n".join(lines)
    chunks = parser_loader.fallback_line_chunking("TestLines.java", source, chunk_size=50, overlap=10)
    assert len(chunks) >= 2
    assert chunks[0]["start_line"] == 1
    assert chunks[0]["end_line"] == 50
    assert chunks[0]["chunk_type"] == "LINE_FALLBACK"
