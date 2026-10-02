"""
DOC-03 Tech Spec Section 2.3:
Phân đoạn mã nguồn bằng Abstract Syntax Tree (AST) qua Tree-sitter
và cơ chế chuyển tầng dự phòng Fallback Line-based.
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
        Nạp các grammar cho Java, JavaScript, TypeScript từ tree-sitter.
        """
        try:
            from tree_sitter import Language, Parser
            self.Parser = Parser
            
            # Cố gắng nạp grammar ngôn ngữ nếu có sẵn
            try:
                import tree_sitter_java
                java_lang = Language(tree_sitter_java.language())
                java_parser = Parser(java_lang)
                self.parsers["java"] = java_parser
                logger.info("Đã nạp thành công Tree-sitter Java grammar.")
            except Exception as e:
                logger.warning(f"Không thể nạp tree_sitter_java: {e}")

            try:
                import tree_sitter_javascript
                js_lang = Language(tree_sitter_javascript.language())
                js_parser = Parser(js_lang)
                self.parsers["javascript"] = js_parser
                logger.info("Đã nạp thành công Tree-sitter JavaScript grammar.")
            except Exception as e:
                logger.warning(f"Không thể nạp tree_sitter_javascript: {e}")

            try:
                import tree_sitter_typescript
                ts_lang = Language(tree_sitter_typescript.language_typescript())
                ts_parser = Parser(ts_lang)
                self.parsers["typescript"] = ts_parser
                logger.info("Đã nạp thành công Tree-sitter TypeScript grammar.")
            except Exception as e:
                logger.warning(f"Không thể nạp tree_sitter_typescript: {e}")

        except ImportError:
            logger.warning("Thư viện tree-sitter chưa được cài đặt trong môi trường hiện tại.")

    def parse_and_chunk(self, file_path: str, source_code: str, language: str = "java") -> List[Dict[str, Any]]:
        """
        Thực hiện phân đoạn AST cấp hàm/phương thức.
        Nếu gặp lỗi cú pháp hoặc chưa nạp được grammar -> tự động Fallback sang Line-based (Mục 2.3.4).
        """
        parser = self.parsers.get(language.lower())
        if not parser:
            logger.info(f"Chưa có AST parser cho '{language}', sử dụng fallback line-based chunking.")
            return self.fallback_line_chunking(file_path, source_code)

        try:
            tree = parser.parse(bytes(source_code, "utf8"))
            root_node = tree.root_node

            if root_node.has_error:
                logger.warning(f"Tệp {file_path} có lỗi cú pháp, kích hoạt Fallback Line-based theo Mục 2.3.4.")
                return self.fallback_line_chunking(file_path, source_code)

            # Bóc tách AST method_declaration / function_declaration kèm tên lớp & tên hàm
            chunks = []
            lines = source_code.splitlines()
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
                # 1. Cập nhật current_class khi gặp cấu trúc lớp/giao diện
                if node.type in ("class_declaration", "interface_declaration", "record_declaration", "enum_declaration", "class"):
                    cls_name = get_identifier(node)
                    if cls_name:
                        current_class = cls_name

                # 2. Bóc tách hàm/phương thức/constructor
                # Java: method_declaration, constructor_declaration
                # JS/TS: function_declaration, method_definition
                if node.type in ("method_declaration", "constructor_declaration", "function_declaration", "method_definition"):
                    start_line = source_bytes[:node.start_byte].count(b'\n') + 1
                    end_line = source_bytes[:node.end_byte].count(b'\n') + 1
                    chunk_text = source_bytes[node.start_byte:node.end_byte].decode("utf8", errors="replace")
                    method_name = get_identifier(node)

                    # Tạo Context Header chứa File, Class, Method và Lines
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
            logger.warning(f"Lỗi AST chunking cho {file_path}, kích hoạt fallback: {e}")
            return self.fallback_line_chunking(file_path, source_code)

    def fallback_line_chunking(self, file_path: str, source_code: str, chunk_size: int = 60, overlap: int = 10) -> List[Dict[str, Any]]:
        """
        Cơ chế dự phòng Section 2.3.4:
        Phân tách từng đoạn 50-80 dòng code, độ gối đầu overlap 10 dòng, gắn context header.
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
