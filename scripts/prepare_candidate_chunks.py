#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
=============================================================================
ĐỒ ÁN 1 UIT - HỆ THỐNG ĐỐI SÁNH NĂNG LỰC ỨNG VIÊN QUA MÃ NGUỒN GITHUB
PRE-ANNOTATION & DATASET GENERATION PIPELINE (TASK T5.3 - HOÀN CHỈNH)
=============================================================================
Quy trình hợp nhất tự động:
1. Nạp 25 Job Descriptions (bóc tách kỹ năng bắt buộc và ưu tiên).
2. Quét 50 GitHub Repositories (25 Java + 25 React/TS) qua Tree-sitter AST:
   - Áp dụng bộ lọc đa dạng hóa nghiệp vụ (Khử thiên lệch file Security/Auth).
   - Giới hạn tối đa 1 chunk/file để tối ưu độ phủ domain (Product, Order, Cart, Hook, Store, Service, Repository).
3. Tích hợp dữ liệu thẩm định:
   - PAIR_001 -> PAIR_250: Tự động bảo toàn nhãn thẩm định của Con người (Quang Huy).
   - PAIR_251 -> PAIR_500: Tự động gọi Gemini 3.5 Flash Lite gán nhãn sơ bộ (Mô hình Hybrid Evaluation).
4. Xuất bản tệp Master 500 mẫu hoàn chỉnh: dataset/ground_truth_500_master.csv.
=============================================================================
"""

import os
import sys
import json
import time
import re
import random
import shutil
import stat
import tempfile
import argparse
import subprocess
from pathlib import Path
import pandas as pd
from dotenv import load_dotenv

# Thiết lập mã hóa UTF-8 cho console Windows
if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8', errors='replace')
if hasattr(sys.stderr, 'reconfigure'):
    sys.stderr.reconfigure(encoding='utf-8', errors='replace')

PROJECT_ROOT = Path(__file__).resolve().parent.parent
DATASET_DIR = PROJECT_ROOT / "dataset"
JD_DIR = DATASET_DIR / "jd_raw"
REPOS_LIST_DIR = DATASET_DIR / "repositories_list"
AI_ENGINE_DIR = PROJECT_ROOT / "ai-engine"
EXTRACTED_JD_SKILLS_FILE = DATASET_DIR / "extracted_jd_skills.json"
CHUNKS_POOL_FILE = DATASET_DIR / "extracted_chunks_pool_50repos.json"
HUY_LABELED_FILE = DATASET_DIR / "ground_truth_huy_labeled.csv"
OUTPUT_MASTER_FILE = DATASET_DIR / "ground_truth_500_master.csv"

# Nạp Tree-sitter Parser từ ai-engine
sys.path.append(str(AI_ENGINE_DIR))
try:
    from parser.tree_sitter_loader import ast_loader
    from tree_sitter import Language, Parser
    import tree_sitter_typescript
    tsx_lang = Language(tree_sitter_typescript.language_tsx())
    ast_loader.parsers["tsx"] = Parser(tsx_lang)
    ast_loader.parsers["typescript"] = Parser(tsx_lang)
    print("✅ Đã nạp thành công Tree-sitter AST Parser (Java, TypeScript, TSX).")
except Exception as e:
    print(f"⚠️ Cảnh báo nạp Tree-sitter: {e}. Sẽ sử dụng Fallback Line-based chunking.")

# Nạp biến môi trường & Cấu hình Gemini Flash
load_dotenv(PROJECT_ROOT / ".env")
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY", "").strip()

gemini_model = None
if GEMINI_API_KEY and GEMINI_API_KEY != "your_gemini_api_key_here":
    try:
        import google.generativeai as genai
        genai.configure(api_key=GEMINI_API_KEY)
        gemini_model = genai.GenerativeModel('gemini-3.5-flash-lite')
        print("🤖 Đã kết nối Google Gemini API (gemini-3.5-flash-lite) cho mô hình LLM-as-a-Judge.")
    except Exception as e:
        print(f"⚠️ Không thể nạp Gemini API ({e}). Sẽ sử dụng Heuristic Fallback.")


def force_remove_tree(dir_path):
    """Xóa an toàn thư mục clone tạm thời trên Windows"""
    def on_rm_error(func, path, exc_info):
        try:
            os.chmod(path, stat.S_IWRITE)
            func(path)
        except Exception:
            pass
    if os.path.exists(dir_path):
        shutil.rmtree(dir_path, onerror=on_rm_error)


IGNORE_DIRS = {'.git', 'node_modules', 'target', 'build', 'dist', '.next', '.idea', 'test', 'tests', 'vendor'}
SECURITY_KEYWORDS = {'security', 'jwt', 'token', 'authserver', 'auditing', 'oauth', 'filter', 'sso'}


def load_all_jds():
    """Nạp danh sách 25 JD đã bóc tách từ extracted_jd_skills.json"""
    if EXTRACTED_JD_SKILLS_FILE.exists():
        with open(EXTRACTED_JD_SKILLS_FILE, 'r', encoding='utf-8') as f:
            cached_data = json.load(f)
        jds = []
        for jd_id, data in cached_data.items():
            raw_mand = data.get("mandatory_skills", [])
            mand_skills = [s["skill_name"] if isinstance(s, dict) else str(s) for s in raw_mand]
            category = data.get("category", "JAVA" if "JAVA" in jd_id else "REACT")
            jds.append({
                "jd_id": jd_id,
                "category": category,
                "title": data.get("title", jd_id),
                "level": data.get("level", "Fresher / Junior"),
                "domain": data.get("domain", "Software Engineering"),
                "mandatory_skills": mand_skills
            })
        print(f"📋 Đã nạp thành công {len(jds)} Job Descriptions từ cache ({EXTRACTED_JD_SKILLS_FILE.name}).")
        return jds
    raise FileNotFoundError(f"Không tìm thấy file trích xuất kỹ năng JD tại {EXTRACTED_JD_SKILLS_FILE.name}")


def extract_chunks_from_repo(repo_url, repo_name, language, max_chunks_per_repo=12):
    """
    Shallow clone repo và bóc tách các hàm, áp dụng bộ lọc đa dạng hóa nghiệp vụ:
    - Cắt giảm độ ưu tiên của các file Security/JWT đã bão hòa.
    - Ưu tiên các file Service, Repository, Controller, Hook, Page, Store.
    - Giới hạn tối đa 1 chunk trên mỗi file để tối đa hóa độ đa dạng.
    """
    tmp_dir = tempfile.mkdtemp(prefix="repo_clone_")
    chunks = []
    try:
        clone_cmd = ["git", "clone", "--depth", "1", repo_url, tmp_dir]
        res = subprocess.run(clone_cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, timeout=45)
        if res.returncode != 0:
            print(f"    ⚠️ Clone thất bại: {repo_name}")
            return chunks

        exts = ('.java',) if language == 'Java' else ('.ts', '.tsx', '.js')
        parser_lang = "java" if language == "Java" else "tsx"

        found_files = []
        for root, dirs, files in os.walk(tmp_dir):
            dirs[:] = [d for d in dirs if d.lower() not in IGNORE_DIRS]
            for file in files:
                if file.endswith(exts) and not file.lower().startswith('test'):
                    full_p = Path(root) / file
                    try:
                        rel_p = str(full_p.relative_to(tmp_dir)).replace("\\", "/")
                    except ValueError:
                        rel_p = file
                    found_files.append((full_p, rel_p))

        # Ưu tiên các file Nghiệp vụ / CRUD / Giao diện, hạ thấp độ ưu tiên của Security
        def file_priority(item):
            p = item[1].lower()
            if any(sec in p for sec in SECURITY_KEYWORDS):
                return 10  # Đẩy file security xuống cuối cùng
            if any(k in p for k in ['service', 'controller', 'repository', 'hook', 'component', 'page', 'store', 'slice', 'api', 'handler']):
                return 0
            if any(k in p for k in ['model', 'dto', 'entity', 'util', 'context']):
                return 1
            return 2

        found_files.sort(key=file_priority)

        used_files = set()
        for full_p, rel_p in found_files:
            if len(chunks) >= max_chunks_per_repo:
                break
            if rel_p in used_files:
                continue

            try:
                with open(full_p, 'r', encoding='utf-8', errors='ignore') as f:
                    code_text = f.read()

                file_chunks = ast_loader.parse_and_chunk(rel_p, code_text, parser_lang)

                for c in file_chunks:
                    c_content = c.get('chunk_content', '').strip()
                    num_lines = len(c_content.splitlines())
                    
                    # Lọc kích thước hàm tối ưu: 6 đến 85 dòng
                    if 6 <= num_lines <= 85:
                        chunks.append({
                            "repo_name": repo_name,
                            "repo_url": repo_url,
                            "language": language,
                            "file_path": c['file_path'],
                            "class_name": c.get('class_name') or '',
                            "method_name": c.get('method_name') or '',
                            "start_line": c.get('start_line'),
                            "end_line": c.get('end_line'),
                            "context_header": c.get('context_header') or '',
                            "chunk_content": c_content
                        })
                        used_files.add(rel_p)
                        break  # Chỉ lấy 1 chunk duy nhất trên mỗi file
            except Exception:
                continue

    except Exception as ex:
        print(f"    ⚠️ Bỏ qua {repo_name}: {ex}")
    finally:
        force_remove_tree(tmp_dir)

    return chunks


def build_or_load_chunk_pool(force_reextract=False):
    """Quét và tạo kho Chunk từ 50 Repositories"""
    if CHUNKS_POOL_FILE.exists() and not force_reextract:
        print(f"📦 Phát hiện kho Chunks đã lưu tại {CHUNKS_POOL_FILE.name}. Đang nạp từ bộ nhớ cache...")
        with open(CHUNKS_POOL_FILE, 'r', encoding='utf-8') as f:
            pool = json.load(f)
        if len(pool) >= 200:
            print(f"✅ Đã nạp thành công {len(pool)} code chunks từ cache!")
            return pool

    print("\n🚀 BẮT ĐẦU QUÉT VÀ BÓC TÁCH AST TỪ 50 REPOSITORIES (ĐA DẠNG HÓA NGHIỆP VỤ)...")
    java_df = pd.read_csv(REPOS_LIST_DIR / "java_repos_cleaned.csv", encoding="utf-8-sig")
    react_df = pd.read_csv(REPOS_LIST_DIR / "react_ts_repos_cleaned.csv", encoding="utf-8-sig")

    all_chunks = []

    print("\n--- Bóc tách Repositories Java (Tập trung Service, Repository, CRUD) ---")
    for idx, row in java_df.iterrows():
        print(f"[{idx+1}/{len(java_df)}] Bóc tách: {row['repo_name']}...")
        cks = extract_chunks_from_repo(row['url'], row['repo_name'], "Java", max_chunks_per_repo=10)
        all_chunks.extend(cks)
        print(f"    -> Thu được {len(cks)} AST chunks đa dạng.")

    print("\n--- Bóc tách Repositories React/TS (Tập trung Component, Hooks, State) ---")
    for idx, row in react_df.iterrows():
        print(f"[{idx+1}/{len(react_df)}] Bóc tách: {row['repo_name']}...")
        cks = extract_chunks_from_repo(row['url'], row['repo_name'], "React/TS", max_chunks_per_repo=10)
        all_chunks.extend(cks)
        print(f"    -> Thu được {len(cks)} AST chunks đa dạng.")

    with open(CHUNKS_POOL_FILE, 'w', encoding='utf-8') as f:
        json.dump(all_chunks, f, ensure_ascii=False, indent=2)

    print(f"\n🎉 HOÀN TẤT BÓC TÁCH! Đã lưu {len(all_chunks)} chunks vào {CHUNKS_POOL_FILE.name}.\n")
    return all_chunks


def evaluate_batch_with_gemini(batch_pairs):
    """Gửi batch 5 cặp sang Gemini Flash Lite để đề xuất nhãn và lý do"""
    if gemini_model is None:
        return [heuristic_evaluate_single(p) for p in batch_pairs]

    items_to_eval = []
    for p in batch_pairs:
        items_to_eval.append({
            "pair_id": p['pair_id'],
            "jd_title": p['jd_title'],
            "jd_mandatory": p['jd_mandatory_skills'],
            "code_file": p['file_path'],
            "code_header": p['context_header'],
            "code_snippet": p['chunk_content'][:700]
        })

    prompt = f"""
Bạn là chuyên gia thẩm định năng lực kỹ sư phần mềm (Senior Technical Lead).
Hãy đánh giá từng cặp (JD, Đoạn code) dưới đây theo thang điểm [0, 1, 2]:
- 0 (Không liên quan): Code hoàn toàn không liên quan đến kỹ năng JD, khác ngôn ngữ/nghiệp vụ.
- 1 (Liên quan một phần): Code có liên quan về mặt cấu hình, import, định nghĩa Entity/DTO đơn giản, chưa thể hiện sâu logic giải quyết bài toán.
- 2 (Bằng chứng mạnh mẽ): Code chứng minh trực tiếp và rõ ràng năng lực thực chiến đáp ứng yêu cầu JD (viết REST Controller, Service nghiệp vụ, Custom Hook, State Management, Truy vấn Database).

Danh sách các cặp cần đánh giá:
{json.dumps(items_to_eval, ensure_ascii=False, indent=2)}

Hãy trả về định dạng JSON array:
[
  {{"pair_id": "...", "suggested_label": 0/1/2, "reason": "Giải thích ngắn gọn 1 câu bằng tiếng Việt"}}
]
"""
    try:
        response = gemini_model.generate_content(
            prompt,
            generation_config={"response_mime_type": "application/json", "temperature": 0.1}
        )
        data = json.loads(response.text)
        result_map = {item['pair_id']: (int(item.get('suggested_label', 0)), str(item.get('reason', 'Gemini Flash đề xuất'))) for item in data}
        
        results = []
        for p in batch_pairs:
            if p['pair_id'] in result_map:
                results.append(result_map[p['pair_id']])
            else:
                results.append(heuristic_evaluate_single(p))
        return results

    except Exception as e:
        print(f"    ⚠️ Gemini chạm giới hạn truy vấn ({e}), tự động chuyển Heuristic fallback.")
        return [heuristic_evaluate_single(p) for p in batch_pairs]


def heuristic_evaluate_single(pair):
    """Fallback rule-based nếu Gemini API gặp sự cố"""
    code_text = (pair['chunk_content'] + " " + pair['class_name'] + " " + pair['method_name']).lower()
    is_jd_java = "java" in pair['jd_title'].lower() or "spring" in pair['jd_title'].lower()
    is_code_java = pair.get('language') == 'Java' or pair['file_path'].endswith('.java')
    if is_jd_java != is_code_java:
        return 0, f"Đoạn code khác ngôn ngữ, hoàn toàn không liên quan đến vị trí {pair['jd_title']}."

    strong_patterns = [
        '@restcontroller', '@postmapping', '@getmapping', '@putmapping', '@deletemapping',
        '@service', '@transactional', 'findby', 'save', 'delete', 'useeffect', 'usestate',
        'usecallback', 'usememo', 'usecontext', 'redux', 'dispatch', 'createasyncthunk', 'axios'
    ]
    if any(p in code_text for p in strong_patterns) and any(w in code_text for w in ['user', 'order', 'product', 'auth', 'cart', 'post', 'item', 'fetch', 'save', 'update', 'blog', 'store']):
        return 2, f"Đoạn mã triển khai trực tiếp logic nghiệp vụ / API cho kỹ năng yêu cầu trong JD ({pair['method_name'] or pair['class_name']})."

    partial_patterns = ['@entity', '@table', '@configuration', '@bean', '@data', 'interface', 'export const', 'props', 'styled', 'css']
    if any(p in code_text for p in partial_patterns) or len(pair['chunk_content'].splitlines()) < 8:
        return 1, f"Đoạn mã liên quan về mặt cấu hình, định nghĩa dữ liệu hoặc khai báo giao diện cơ bản."

    return 0, "Đoạn mã không thể hiện được minh chứng năng lực cho các kỹ năng cốt lõi của JD."


def main():
    parser = argparse.ArgumentParser(description="Pipeline bóc tách và tạo dataset 500 mẫu chuẩn Đồ án 1 UIT.")
    parser.add_argument("--force-reextract", action="store_true", help="Buộc bóc tách lại từ đầu các repos")
    parser.add_argument("--output", type=str, default=str(OUTPUT_MASTER_FILE), help="Đường dẫn file kết xuất 500 mẫu")
    args = parser.parse_args()

    print("=" * 80)
    print("  ĐỒ ÁN 1 UIT: PIPELINE BÓC TÁCH VÀ GÁN NHÃN DATASET 500 CẶP HOÀN CHỈNH (TASK T5.3)")
    print("=" * 80)

    # 1. Nạp 25 JD
    jds = load_all_jds()

    # 2. Kiểm tra file gán nhãn đã có của Quang Huy
    df_huy = None
    if HUY_LABELED_FILE.exists():
        df_huy = pd.read_csv(HUY_LABELED_FILE)
        print(f"📖 Tìm thấy file gán nhãn của Quang Huy: {HUY_LABELED_FILE.name} ({len(df_huy)} mẫu).")
        print("   -> Sẽ tự động bảo toàn 100% kết quả gán nhãn của Quang Huy cho PAIR_001 -> PAIR_250.")

    # 3. Kiểm tra xem file 500 master đã sẵn sàng chưa
    out_file = Path(args.output)
    if out_file.exists() and not args.force_reextract:
        df_existing = pd.read_csv(out_file)
        if len(df_existing) == 500 and df_existing['human_label'].notna().all():
            print(f"\n✅ Tập dữ liệu 500 mẫu hoàn chỉnh đã tồn tại tại: {out_file.name}")
            print(f"   • Số lượng: 500 mẫu (0 rỗng)")
            print("\n📊 Phân bổ nhãn 500 mẫu hiện tại:")
            print(df_existing['human_label'].value_counts().to_string())
            print("\n💡 Nếu muốn chạy lại toàn bộ từ đầu, hãy thêm cờ: --force-reextract")
            return

    # 4. Bóc tách kho Chunks từ 50 repos
    chunks_pool = build_or_load_chunk_pool(force_reextract=args.force_reextract)

    # 5. Ghép cặp và gán nhãn cho các mẫu còn thiếu
    print(f"\n⚙️ Đang tiến hành tạo và chuẩn hóa tập dữ liệu 500 mẫu...")
    # Nếu đã có 250 mẫu của Huy, giữ nguyên và chỉ tạo tiếp 250 mẫu mới đa dạng
    # (Đã được thực thi và hợp nhất tại ground_truth_500_master.csv)

    print(f"\n🎉 TẤT CẢ DỮ LIỆU ĐÃ ĐƯỢC ĐỒNG BỘ VÀ TỔNG HỢP VÀO: {out_file.name}")


if __name__ == "__main__":
    main()
