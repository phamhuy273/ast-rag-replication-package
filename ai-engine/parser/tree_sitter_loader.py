"""
=============================================================================
CANDIDATE SKILL MATCHING VIA SOURCE CODE - RAG REPLICATION PACKAGE
Module: TREE-SITTER AST PROGRESSIVE DISCLOSURE CHUNKER
Grammars: Java, TypeScript, JavaScript, TSX
Target: IEEE SANER 2027 (ERA Track - CORE A) & Double-Anonymous Peer Review
=============================================================================
"""

import logging
from typing import List, Dict, Any

logger = logging.getLogger("ai-engine.parser")


class ASTParserLoader:
    def __init__(self):
        self.parsers = {}
        self._init_parsers()

    def _init_parsers(self):
        """
        Load syntax grammars for Java, JavaScript, and TypeScript from Tree-sitter bindings.
        """
        try:
            from tree_sitter import Language, Parser
            self.Parser = Parser

            try:
                import tree_sitter_java
                java_lang = Language(tree_sitter_java.language())
                java_parser = Parser(java_lang)
                self.parsers["java"] = java_parser
                logger.info("Successfully loaded Tree-sitter Java grammar.")
            except Exception as e:
                logger.warning(f"Could not load tree_sitter_java: {e}")

            try:
                import tree_sitter_javascript
                js_lang = Language(tree_sitter_javascript.language())
                js_parser = Parser(js_lang)
                self.parsers["javascript"] = js_parser
                logger.info("Successfully loaded Tree-sitter JavaScript grammar.")
            except Exception as e:
                logger.warning(f"Could not load tree_sitter_javascript: {e}")

            try:
                import tree_sitter_typescript
                ts_lang = Language(tree_sitter_typescript.language_typescript())
                ts_parser = Parser(ts_lang)
                self.parsers["typescript"] = ts_parser

                tsx_lang = Language(tree_sitter_typescript.language_tsx())
                self.parsers["tsx"] = Parser(tsx_lang)
                logger.info("Successfully loaded Tree-sitter TypeScript/TSX grammar.")
            except Exception as e:
                logger.warning(f"Could not load tree_sitter_typescript: {e}")

        except ImportError:
            logger.warning("Tree-sitter library is not installed in the current environment.")

    def parse_and_chunk(self, file_path: str, source_code: str, language: str = "java") -> List[Dict[str, Any]]:
        """
        Segment source code at syntax-aware method/function AST boundaries.
        Prepends hierarchical context headers (file_path, class, method, lines).
        If syntax errors occur or language is unsupported, gracefully shifts to fallback line slicing.
        """
        parser = self.parsers.get(language.lower())
        if not parser:
            logger.info(f"No AST parser found for '{language}', shifting to fallback line-based chunking.")
            return self.fallback_line_chunking(file_path, source_code)

        try:
            tree = parser.parse(bytes(source_code, "utf8"))
            root_node = tree.root_node

            if root_node.has_error:
                logger.warning(f"File {file_path} contains syntax errors; activating fallback line-based chunking.")
                return self.fallback_line_chunking(file_path, source_code)

            chunks = []
            source_bytes = bytes(source_code, "utf8")

            def get_node_text(n):
                if n is None:
                    return None
                return source_bytes[n.start_byte:n.end_byte].decode("utf8", errors="replace")

            def get_identifier(n):
                if n is None:
                    return None
                name_node = n.child_by_field_name("name")
                if name_node:
                    return get_node_text(name_node)
                for child in n.children:
                    if child.type in ("identifier", "type_identifier", "property_identifier"):
                        return get_node_text(child)
                return None

            def traverse(node, current_class=None):
                # 1. Update current_class on encountering class/interface/record constructs
                if node.type in ("class_declaration", "interface_declaration", "record_declaration", "enum_declaration", "class"):
                    cls_name = get_identifier(node)
                    if cls_name:
                        current_class = cls_name

                # 2. Extract methods, functions, and constructors
                # Java: method_declaration, constructor_declaration
                # JS/TS: function_declaration, method_definition
                if node.type in ("method_declaration", "constructor_declaration", "function_declaration", "method_definition"):
                    start_line = source_bytes[:node.start_byte].count(b'\n') + 1
                    end_line = source_bytes[:node.end_byte].count(b'\n') + 1
                    chunk_text = source_bytes[node.start_byte:node.end_byte].decode("utf8", errors="replace")
                    method_name = get_identifier(node)

                    # Progressive Disclosure: Hierarchical context header
                    header_lines = [f"// File: {file_path}"]
                    if current_class:
                        header_lines.append(f"// Class: {current_class}")
                    if method_name:
                        header_lines.append(f"// Method: {method_name}")
                    header_lines.append(f"// Lines: {start_line}-{end_line}")
                    context_header = "\n".join(header_lines)

                    chunks.append({
                        "file_path": file_path,
                        "class_name": current_class,
                        "method_name": method_name,
                        "start_line": start_line,
                        "end_line": end_line,
                        "context_header": context_header,
                        "chunk_content": chunk_text,
                        "chunk_type": "AST_METHOD"
                    })

                for child in node.children:
                    traverse(child, current_class)

            traverse(root_node)

            if not chunks:
                return self.fallback_line_chunking(file_path, source_code)
            return chunks

        except Exception as e:
            logger.warning(f"AST chunking exception for {file_path}, falling back: {e}")
            return self.fallback_line_chunking(file_path, source_code)

    def fallback_line_chunking(self, file_path: str, source_code: str, chunk_size: int = 50, overlap: int = 10) -> List[Dict[str, Any]]:
        """
        Fallback line-based chunker:
        Segments code into fixed sliding windows (default 50 LOC, 10 overlap).
        """
        lines = source_code.splitlines()
        chunks = []
        total_lines = len(lines)
        if total_lines == 0:
            return chunks

        step = max(1, chunk_size - overlap)
        for start_idx in range(0, total_lines, step):
            end_idx = min(start_idx + chunk_size, total_lines)
            chunk_lines = lines[start_idx:end_idx]
            context_header = f"// File: {file_path}\n// Lines: {start_idx + 1}-{end_idx}"
            chunk_text = "\n".join(chunk_lines)

            chunks.append({
                "file_path": file_path,
                "class_name": None,
                "method_name": None,
                "start_line": start_idx + 1,
                "end_line": end_idx,
                "context_header": context_header,
                "chunk_content": chunk_text,
                "chunk_type": "LINE_FALLBACK"
            })
            if end_idx == total_lines:
                break
        return chunks


ast_loader = ASTParserLoader()
