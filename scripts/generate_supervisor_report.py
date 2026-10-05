#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Script sinh báo cáo tiến độ thực nghiệm tuần này gửi Giảng viên hướng dẫn (GVHD)
Đồ án 1 UIT & Bài báo khoa học IEEE SANER 2027 (ERA Track)
"""

import sys
from pathlib import Path
from docx import Document
from docx.shared import Inches, Pt, RGBColor
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.enum.table import WD_TABLE_ALIGNMENT, WD_ALIGN_VERTICAL
from docx.oxml import OxmlElement, parse_xml
from docx.oxml.ns import nsdecls, qn

if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8', errors='replace')

PROJECT_ROOT = Path(__file__).resolve().parent.parent
RESULTS_DIR = PROJECT_ROOT / "dataset" / "benchmark_results"
OUTPUT_DOCX_DOAN1 = PROJECT_ROOT / "Dò a'n 1" / "Bao_Cao_Tien_Do_Thuc_Nghiem_Tuan_Nay.docx"
OUTPUT_DOCX_RESULTS = RESULTS_DIR / "Bao_Cao_Tien_Do_Thuc_Nghiem_Tuan_Nay.docx"

# Màu chủ đạo theo phong cách UIT / Học thuật
COLOR_PRIMARY = RGBColor(0, 51, 102)     # UIT Navy Blue #003366
COLOR_SECONDARY = RGBColor(41, 128, 185) # Blue #2980B9
COLOR_DARK = RGBColor(44, 62, 80)        # Dark Slate #2C3E50
COLOR_GRAY = RGBColor(127, 140, 141)     # Muted Gray

HEX_HEADER_BG = "003366"
HEX_ZEBRA_BG = "F4F6F9"
HEX_HIGHLIGHT_BG = "EBF5FB"


def set_cell_background(cell, fill_hex):
    tcPr = cell._tc.get_or_add_tcPr()
    shd = parse_xml(f'<w:shd {nsdecls("w")} w:fill="{fill_hex}"/>')
    tcPr.append(shd)


def set_cell_margins(cell, top=100, bottom=100, left=150, right=150):
    tcPr = cell._tc.get_or_add_tcPr()
    tcMar = parse_xml(
        f'<w:tcMar {nsdecls("w")}>'
        f'<w:top w:w="{top}" w:type="dxa"/>'
        f'<w:bottom w:w="{bottom}" w:type="dxa"/>'
        f'<w:left w:w="{left}" w:type="dxa"/>'
        f'<w:right w:w="{right}" w:type="dxa"/>'
        f'</w:tcMar>'
    )
    tcPr.append(tcMar)


def add_heading_with_accent(doc, text, level=1):
    h = doc.add_heading(text, level=level)
    h.paragraph_format.space_before = Pt(14)
    h.paragraph_format.space_after = Pt(6)
    h.paragraph_format.keep_with_next = True
    run = h.runs[0]
    run.font.name = "Arial"
    if level == 1:
        run.font.size = Pt(14)
        run.font.bold = True
        run.font.color.rgb = COLOR_PRIMARY
    elif level == 2:
        run.font.size = Pt(12)
        run.font.bold = True
        run.font.color.rgb = COLOR_SECONDARY
    return h


def style_table_header(row, col_widths=None):
    for idx, cell in enumerate(row.cells):
        set_cell_background(cell, HEX_HEADER_BG)
        set_cell_margins(cell, top=120, bottom=120, left=120, right=120)
        cell.vertical_alignment = WD_ALIGN_VERTICAL.CENTER
        for p in cell.paragraphs:
            p.alignment = WD_ALIGN_PARAGRAPH.CENTER
            for r in p.runs:
                r.font.name = "Arial"
                r.font.size = Pt(9.5)
                r.font.bold = True
                r.font.color.rgb = RGBColor(255, 255, 255)
        if col_widths and idx < len(col_widths):
            cell.width = Inches(col_widths[idx])


def style_table_data(table, col_widths=None, highlight_last_row=False):
    for r_idx, row in enumerate(table.rows[1:]):
        is_highlight = highlight_last_row and (r_idx == len(table.rows) - 2)
        bg = HEX_HIGHLIGHT_BG if is_highlight else (HEX_ZEBRA_BG if r_idx % 2 == 1 else "FFFFFF")
        for c_idx, cell in enumerate(row.cells):
            set_cell_background(cell, bg)
            set_cell_margins(cell, top=80, bottom=80, left=100, right=100)
            cell.vertical_alignment = WD_ALIGN_VERTICAL.CENTER
            for p in cell.paragraphs:
                for r in p.runs:
                    r.font.name = "Arial"
                    r.font.size = Pt(9.0)
                    if is_highlight:
                        r.font.bold = True
                        r.font.color.rgb = COLOR_PRIMARY
                    else:
                        r.font.color.rgb = COLOR_DARK
            if col_widths and c_idx < len(col_widths):
                cell.width = Inches(col_widths[c_idx])


def build_report():
    print("🚀 Bắt đầu tạo file báo cáo tiến độ tuần cho GVHD...")
    doc = Document()

    # Cấu hình lề trang chuẩn báo cáo học thuật
    sections = doc.sections
    for section in sections:
        section.top_margin = Inches(0.8)
        section.bottom_margin = Inches(0.8)
        section.left_margin = Inches(0.8)
        section.right_margin = Inches(0.8)

    # 1. Header trường & đề tài
    p_inst = doc.add_paragraph()
    p_inst.alignment = WD_ALIGN_PARAGRAPH.CENTER
    r_inst1 = p_inst.add_run("TRƯỜNG ĐẠI HỌC CÔNG NGHỆ THÔNG TIN - ĐHQG TP.HCM\n")
    r_inst1.font.name = "Arial"
    r_inst1.font.size = Pt(11)
    r_inst1.font.bold = True
    r_inst1.font.color.rgb = COLOR_PRIMARY

    r_inst2 = p_inst.add_run("KHOA HỆ THỐNG THÔNG TIN / KỸ THUẬT PHẦN MỀM\n")
    r_inst2.font.name = "Arial"
    r_inst2.font.size = Pt(10)
    r_inst2.font.color.rgb = COLOR_GRAY

    # Dòng kẻ ngang
    p_rule = doc.add_paragraph()
    p_rule.alignment = WD_ALIGN_PARAGRAPH.CENTER
    r_rule = p_rule.add_run("—" * 45)
    r_rule.font.color.rgb = COLOR_SECONDARY

    # Tiêu đề báo cáo
    p_title = doc.add_paragraph()
    p_title.alignment = WD_ALIGN_PARAGRAPH.CENTER
    p_title.paragraph_format.space_before = Pt(6)
    p_title.paragraph_format.space_after = Pt(12)
    r_title = p_title.add_run("BÁO CÁO TIẾN ĐỘ THỰC NGHIỆM TUẦN\nĐỒ ÁN 1 & NGHIÊN CỨU IEEE SANER 2027")
    r_title.font.name = "Arial"
    r_title.font.size = Pt(16)
    r_title.font.bold = True
    r_title.font.color.rgb = COLOR_PRIMARY

    # Bảng thông tin sinh viên & đề tài
    meta_table = doc.add_table(rows=4, cols=2)
    meta_table.alignment = WD_TABLE_ALIGNMENT.CENTER
    meta_data = [
        ("Đề tài nghiên cứu:", "Hệ thống đối sánh năng lực ứng viên qua mã nguồn GitHub bằng mô hình RAG kết hợp AST Progressive Disclosure"),
        ("Sinh viên thực hiện:", "Phạm Huy (22520556) - Trưởng nhóm | Nguyễn An (Cộng sự gán nhãn độc lập)"),
        ("Đối tượng báo cáo:", "Giảng viên Hướng dẫn (GVHD) Đồ án 1 UIT"),
        ("Giai đoạn thực hiện:", "Hoàn tất kiểm định nhãn vàng (Table 3.1), Thực nghiệm Chunking (Table 3.2), Thực nghiệm Retrieval BGE-M3 (Table 3.3)")
    ]
    for idx, (label, val) in enumerate(meta_data):
        row = meta_table.rows[idx]
        cell_lbl, cell_val = row.cells[0], row.cells[1]
        cell_lbl.text = label
        cell_val.text = val
        cell_lbl.paragraphs[0].runs[0].font.bold = True
        cell_lbl.paragraphs[0].runs[0].font.size = Pt(9.5)
        cell_lbl.paragraphs[0].runs[0].font.color.rgb = COLOR_PRIMARY
        cell_val.paragraphs[0].runs[0].font.size = Pt(9.5)
        set_cell_background(cell_lbl, "EBF5FB")
        set_cell_background(cell_val, "FAFAFA")
        set_cell_margins(cell_lbl, top=60, bottom=60, left=80, right=80)
        set_cell_margins(cell_val, top=60, bottom=60, left=80, right=80)
        cell_lbl.width = Inches(1.8)
        cell_val.width = Inches(5.0)

    doc.add_paragraph().paragraph_format.space_after = Pt(10)

    # =========================================================================
    # PHẦN 1: TỔNG QUAN CÁC CÔNG VIỆC ĐÃ HOÀN THÀNH
    # =========================================================================
    add_heading_with_accent(doc, "1. TỔNG QUAN TIẾN ĐỘ THỰC HIỆN TRONG TUẦN", level=1)
    
    p_sum = doc.add_paragraph()
    p_sum.add_run(
        "Trong tuần này, nhóm sinh viên đã tập trung giải quyết toàn bộ các yêu cầu học thuật khắt khe nhất "
        "nhằm đảm bảo tính liêm chính dữ liệu (Scientific Integrity), xóa bỏ hoàn toàn phụ thuộc vào AI hòa giải, "
        "và thực thi trọn vẹn quy trình benchmark thực nghiệm từ mô hình Deep Learning thật (không sử dụng số liệu giả lập). "
        "Cụ thể nhóm đã hoàn thành 4 hạng mục lớn:\n"
    )
    
    bullets = [
        ("Chuẩn hóa Tập Dữ liệu Nhãn Vàng 100% Con Người:", " Rà soát và loại bỏ toàn bộ các nhãn gợi ý/lý do của Gemini trong 250 mẫu đánh giá (25 JDs x 10 pairs). Toàn bộ 29 cặp bất đồng đã được hòa giải độc lập theo chuẩn chuyên gia (Adjudication Consensus), biến tập dữ liệu thành Pure Human Ground Truth chuẩn mực."),
        ("Thực nghiệm Đo lường Độ tin cậy Liên Người Gán (Table 3.1):", " Sử dụng Quadratic Weighted Cohen's Kappa, đạt hệ số tin cậy κ_w = 0.8808, thuộc mức Almost Perfect Agreement."),
        ("Thực nghiệm Phân tích Ngữ pháp AST Chunking (Table 3.2):", " Đo lường trên 50 repositories và 500 candidate pairs, chứng minh thuật toán AST Progressive Disclosure bảo toàn 100% ranh giới cú pháp và tiết kiệm 19.6% token bloat so với phương pháp cắt theo dòng."),
        ("Đánh giá Thực nghiệm Truy xuất RAG bằng BAAI/bge-m3 (Table 3.3):", " Chạy lại mô hình Deep Learning BGE-M3 (1024 chiều) kết hợp BM25Okapi trên 25 JDs thực tế, thực hiện kiểm định Paired Wilcoxon Signed-Rank Test và Paired t-test đạt độ tin cậy vượt trội so với baseline truyền thống.")
    ]
    for b_title, b_desc in bullets:
        bp = doc.add_paragraph(style='List Bullet')
        bp.paragraph_format.space_after = Pt(3)
        r_b1 = bp.add_run(b_title)
        r_b1.bold = True
        r_b1.font.color.rgb = COLOR_PRIMARY
        r_b2 = bp.add_run(b_desc)
        r_b2.font.color.rgb = COLOR_DARK

    # =========================================================================
    # PHẦN 2: BẢNG 3.1 - ĐỘ TIN CẬY NHÃN VÀNG (COHEN'S KAPPA)
    # =========================================================================
    add_heading_with_accent(doc, "2. BẢNG 3.1: ĐỘ ĐỒNG THUẬN LIÊN NGƯỜI GÁN (INTER-ANNOTATOR AGREEMENT)", level=1)
    
    p_k = doc.add_paragraph()
    p_k.add_run(
        "Để đảm bảo ground truth có giá trị khoa học trước hội đồng và hội nghị quốc tế, nhóm thực hiện gán nhãn độc lập song song "
        "(Double-blind Annotation) giữa hai annotator: Huy (Annotator 1) và An (Annotator 2) trên thang đo 3 mức: "
        "Mức 0 (Không liên quan), Mức 1 (Khớp kỹ năng cơ bản), Mức 2 (Khớp kỹ năng sâu / Core Evidence)."
    )

    t1 = doc.add_table(rows=6, cols=3)
    t1.alignment = WD_TABLE_ALIGNMENT.CENTER
    t1_headers = ["Chỉ số Thống kê (Metric)", "Giá trị Thực nghiệm", "Ý nghĩa & Chuẩn Học thuật"]
    for i, h in enumerate(t1_headers):
        t1.rows[0].cells[i].text = h
    style_table_header(t1.rows[0], [2.2, 1.8, 2.8])

    t1_rows = [
        ("Tổng số cặp đánh giá (Sample Size)", "250 cặp (25 JDs x 10)", "25 JDs phong phú từ Backend, DevOps, Data"),
        ("Số cặp đồng thuận tuyệt đối (Exact Match)", "221 / 250 cặp", "Đạt tỷ lệ đồng thuận thô 88.40%"),
        ("Số cặp bất đồng cần hòa giải (Disagreements)", "29 / 250 cặp", "11.60% (Chỉ lệch 1 bậc nhãn: 0-1 hoặc 1-2, 0 lệch 0-2)"),
        ("Unweighted Cohen's Kappa (κ)", "0.8037", "Mức đồng thuận rất cao (Substantial / Almost Perfect)"),
        ("Quadratic Weighted Kappa (κ_w)", "0.8808", "Almost Perfect Agreement (Chuẩn Landis & Koch 1977)")
    ]
    for r_idx, row_data in enumerate(t1_rows):
        for c_idx, val in enumerate(row_data):
            t1.rows[r_idx + 1].cells[c_idx].text = val
    style_table_data(t1, [2.2, 1.8, 2.8], highlight_last_row=True)

    p_note1 = doc.add_paragraph()
    p_note1.paragraph_format.space_before = Pt(6)
    r_n1 = p_note1.add_run("Nhận xét học thuật: ")
    r_n1.bold = True
    p_note1.add_run(
        "Hệ số κ_w = 0.8808 chứng minh tiêu chuẩn gán nhãn được định nghĩa vô cùng chặt chẽ. Đặc biệt, không có bất kỳ cặp nào "
        "xảy ra xung đột cực đoan (Annotator 1 chấm 0 mà Annotator 2 chấm 2). 29 cặp bất đồng sau đó được họp bàn và thống nhất "
        "100% bằng chuyên môn con người (Adjudication Consensus), ghi chép minh bạch tại file disagreements_adjudication.csv."
    )

    # Chèn ảnh Ma trận nhầm lẫn
    cm_path = RESULTS_DIR / "confusion_matrix_kappa.png"
    if cm_path.exists():
        p_img = doc.add_paragraph()
        p_img.alignment = WD_ALIGN_PARAGRAPH.CENTER
        p_img.paragraph_format.space_before = Pt(8)
        run_img = p_img.add_run()
        run_img.add_picture(str(cm_path), width=Inches(4.8))
        
        p_cap = doc.add_paragraph()
        p_cap.alignment = WD_ALIGN_PARAGRAPH.CENTER
        r_cap = p_cap.add_run("Hình 3.1: Ma trận nhầm lẫn (Confusion Matrix) giữa hai người gán nhãn độc lập (κ_w = 0.8808)")
        r_cap.font.size = Pt(8.5)
        r_cap.font.italic = True
        r_cap.font.color.rgb = COLOR_GRAY

    # =========================================================================
    # PHẦN 3: BẢNG 3.2 - CHẤT LƯỢNG PHÂN MẢNH MÃ NGUỒN (CORPUS BENCHMARK)
    # =========================================================================
    add_heading_with_accent(doc, "3. BẢNG 3.2: THỰC NGHIỆM CHẤT LƯỢNG PHÂN MẢNH MÃ NGUỒN (50 REPOSITORIES)", level=1)
    
    doc.add_paragraph(
        "Bảng 3.2 so sánh chất lượng ngữ pháp và tính toán chi phí token giữa chiến lược phân mảnh đề xuất "
        "(AST Progressive Disclosure) và phương pháp truyền thống (Line-based Chunking: cắt cố định 50 dòng, overlap 10 dòng) "
        "trên quy mô 50 kho chứa mã nguồn Java thực tế từ GitHub (500 candidate pairs):"
    )

    t2 = doc.add_table(rows=3, cols=6)
    t2.alignment = WD_TABLE_ALIGNMENT.CENTER
    t2_headers = ["Phương pháp (Method)", "Mean LOC", "Mean Tokens", "Boundary Preservation", "Syntax Frag.", "Context Header"]
    for i, h in enumerate(t2_headers):
        t2.rows[0].cells[i].text = h
    style_table_header(t2.rows[0], [2.0, 0.9, 1.0, 1.1, 0.9, 0.9])

    t2_rows = [
        ("Line-based Chunking (Baseline)", "35.2 dòng", "~260 tokens", "31.6%", "68.4%", "0.0%"),
        ("AST Progressive Disclosure (Ours)", "28.6 dòng", "209 tokens", "100.0%", "0.0%", "100.0%")
    ]
    for r_idx, row_data in enumerate(t2_rows):
        for c_idx, val in enumerate(row_data):
            t2.rows[r_idx + 1].cells[c_idx].text = val
    style_table_data(t2, [2.0, 0.9, 1.0, 1.1, 0.9, 0.9], highlight_last_row=True)

    p_note2 = doc.add_paragraph()
    p_note2.paragraph_format.space_before = Pt(6)
    r_n2 = p_note2.add_run("Phân tích giá trị cốt lõi: ")
    r_n2.bold = True
    p_note2.add_run(
        "1) Bảo toàn ranh giới cú pháp (100.0% vs 31.6%): Tree-sitter giúp cắt chính xác tại ranh giới method/class, triệt tiêu hoàn toàn "
        "nguy cơ cắt đứt ngang thân vòng lặp hay cấu trúc try-catch (vốn xảy ra tới 68.4% ở cách cắt dòng).\n"
        "2) Bảo tồn ngữ cảnh (100.0% vs 0.0%): Mỗi đoạn code đều được gắn kèm Package, Class, Interface và Annotations (@Service, @Repository), "
        "giúp LLM hiểu rõ vị trí kiến trúc của đoạn code.\n"
        "3) Tối ưu chi phí Context Window (-19.6% Token Bloat): Giảm kích thước trung bình từ 260 xuống 209 tokens, tiết kiệm đáng kể chi phí gọi LLM."
    )

    # =========================================================================
    # PHẦN 4: BẢNG 3.3 - ĐÁNH GIÁ THỰC NGHIỆM TRUY XUẤT RAG (RETRIEVAL BENCHMARK)
    # =========================================================================
    add_heading_with_accent(doc, "4. BẢNG 3.3: HIỆU NĂNG TRUY XUẤT THỰC NGHIỆM (RETRIEVAL BENCHMARK)", level=1)
    
    doc.add_paragraph(
        "Nhóm đã nạp mô hình Deep Learning BAAI/bge-m3 (1024 chiều) để mã hóa toàn bộ 25 truy vấn JD và 500 đoạn mã thực tế, "
        "sau đó tiến hành so sánh đối đầu trực tiếp trên 25 Job Descriptions với 3 cấu hình:"
    )

    t3 = doc.add_table(rows=5, cols=7)
    t3.alignment = WD_TABLE_ALIGNMENT.CENTER
    t3_headers = ["Phương pháp (Configuration)", "P@5", "R@5", "F1@5", "NDCG@5", "MRR", "Ctx-P@5"]
    for i, h in enumerate(t3_headers):
        t3.rows[0].cells[i].text = h
    style_table_header(t3.rows[0], [2.2, 0.75, 0.75, 0.75, 0.85, 0.75, 0.75])

    t3_rows = [
        ("Baseline 1: Line-based + BM25 (Sparse)", "0.768", "0.565", "0.649", "0.631", "0.900", "0.854"),
        ("Baseline 2: Line-based + BGE-M3 (Dense)", "0.944", "0.695", "0.799", "0.775", "1.000", "0.987"),
        ("Proposed: AST Progressive + BGE-M3 (Ours)", "0.944", "0.693", "0.797", "0.791", "0.980", "0.973"),
        ("Độ cải thiện so với Baseline 2 (Δ vs B2)", "+0.0%", "-0.3%", "-0.2%", "+2.1%", "-2.0%", "-1.4%")
    ]
    for r_idx, row_data in enumerate(t3_rows):
        for c_idx, val in enumerate(row_data):
            t3.rows[r_idx + 1].cells[c_idx].text = val
    style_table_data(t3, [2.2, 0.75, 0.75, 0.75, 0.85, 0.75, 0.75], highlight_last_row=False)
    # Highlight hàng Proposed
    for cell in t3.rows[3].cells:
        set_cell_background(cell, HEX_HIGHLIGHT_BG)
        for p in cell.paragraphs:
            for r in p.runs:
                r.font.bold = True
                r.font.color.rgb = COLOR_PRIMARY

    # Kiểm định thống kê
    p_stat = doc.add_paragraph()
    p_stat.paragraph_format.space_before = Pt(6)
    r_st_title = p_stat.add_run("Kết quả Kiểm định Ý nghĩa Thống kê (Statistical Significance Tests, α = 0.05):\n")
    r_st_title.bold = True
    r_st_title.font.color.rgb = COLOR_PRIMARY

    stat_bullets = [
        ("So với Baseline 1 (BM25 từ khóa):", " Phương pháp đề xuất vượt trội hoàn toàn với Wilcoxon W = 278.0, p = 0.000577 < 0.001 (***) và Paired t-test t = 3.9356, p = 0.000310 < 0.001 (***). Tỷ lệ thắng áp đảo: Thắng 20 / 25 JDs (80%), Thua 5 JDs, Hòa 0 JDs."),
        ("So với Baseline 2 (Line-based Dense BGE-M3):", " Phương pháp đề xuất đạt NDCG@5 cao hơn (0.7913 vs 0.7747, tăng +2.1%). Phân phối truy vấn đối đầu: Thắng 14 / 25 JDs (56%), Thua 6 JDs, Hòa 5 JDs."),
        ("Đánh giá Liêm chính Khoa học (Scientific Integrity):", " Với cỡ mẫu N = 25 JDs, kiểm định cặp giữa AST và Line-based Dense cho p = 0.1659. Kết quả này phản ánh chân thực rằng dù AST thắng ở 14/25 JD, sự sai khác ở tầng dense embedding giữa hai kỹ thuật chunking cần bổ sung thêm Cross-Encoder Re-ranker để khuếch đại khoảng cách.")
    ]
    for st_title, st_desc in stat_bullets:
        bp = doc.add_paragraph(style='List Bullet')
        bp.paragraph_format.space_after = Pt(3)
        r_sb1 = bp.add_run(st_title)
        r_sb1.bold = True
        bp.add_run(st_desc)

    # Giải thích học thuật chuyên sâu về NDCG@1 vs NDCG@5
    add_heading_with_accent(doc, "5. PHÂN TÍCH CHUYÊN SÂU: NGHỊCH LÝ GIỮA TOP-1 VÀ TOP-5", level=2)
    p_insight = doc.add_paragraph()
    p_insight.add_run(
        "Một phát hiện nghiên cứu rất thú vị và giá trị trong Bảng 3.3 là: Baseline 2 (Line-based) có NDCG@1 (0.6800 vs 0.6200) "
        "và MRR (1.0000 vs 0.9800) nhỉnh hơn nhẹ, trong khi AST Progressive lại chiến thắng ở tổng thể Top-5 (NDCG@5: 0.7913 vs 0.7747, thắng 14/25 JD). "
        "Nhóm giải trình hiện tượng này dưới hai góc độ kỹ thuật:\n\n"
        "1) Hiện tượng Pha loãng Vector (Embedding Dilution): Khi đưa Context Header (package, imports, class annotations) vào chunk AST, "
        "mô hình Transformer (BGE-M3) phân bổ trọng số attention cho cả cấu trúc chung của file, làm giảm nhẹ mật độ token tập trung ở vị trí Top-1. "
        "Ngược lại, đoạn code Line-based ngắn ngủn nhưng chứa đúng từ khóa sẽ tạo ra cú 'Spike' điểm Cosine giả tạo ở vị trí số 1.\n"
        "2) Đánh đổi giữa Retrieval Score và Khả năng Ứng dụng RAG thực tế: Tuy Line-based có điểm Top-1 cao nhưng đoạn code đó bị "
        "vỡ cú pháp tới 68.4% (mất class, mất method signature). Khi đưa vào LLM để sinh báo cáo đánh giá ứng viên, LLM hoàn toàn không biết "
        "đoạn code thuộc class/service nào, dẫn tới ảo giác (hallucination). Trong khi đó, AST Progressive đưa trọn vẹn Top-5 bằng chứng "
        "hoàn chỉnh 100% cú pháp, là tiền đề quyết định để LLM sinh báo cáo chuẩn xác."
    )

    # =========================================================================
    # PHẦN 6: KẾ HOẠCH TUẦN TIẾP THEO
    # =========================================================================
    add_heading_with_accent(doc, "6. KẾ HOẠCH TRIỂN KHAI TRONG TUẦN TỚI", level=1)
    
    plan_bullets = [
        ("Thực nghiệm Đánh giá Độ tin cậy Tạo sinh (Bảng 3.4 - RAG Generation & Faithfulness):", " Đo lường mức độ trung thực của câu trả lời từ LLM qua bộ chỉ số Ragas (Faithfulness, Answer Relevance) nhằm chứng minh ưu thế vượt trội của Context Header khi đưa vào Prompt."),
        ("Cập nhật Bản thảo Bài báo IEEE SANER 2027 (paper/main.tex):", " Điền toàn bộ số liệu thực nghiệm Bảng 3.1, Bảng 3.2, Bảng 3.3 vào bản thảo LaTeX theo chuẩn IEEE Conference format 5 trang."),
        ("Hoàn thiện Báo cáo Đồ án 1 UIT (DoAn1_Bao_Cao.docx):", " Cập nhật toàn bộ các bảng biểu và phân tích học thuật vào Chương 3 của thuyết minh đề tài."),
        ("Đóng gói Replication Package:", " Chuẩn bị mã nguồn sạch, dataset chuẩn người gán và hướng dẫn tái lập thực nghiệm để nộp kèm bài báo.")
    ]
    for p_title, p_desc in plan_bullets:
        bp = doc.add_paragraph(style='List Bullet')
        bp.paragraph_format.space_after = Pt(3)
        r_p1 = bp.add_run(p_title)
        r_p1.bold = True
        r_p1.font.color.rgb = COLOR_PRIMARY
        bp.add_run(p_desc)

    # Footer ký tên
    p_sign = doc.add_paragraph()
    p_sign.paragraph_format.space_before = Pt(20)
    p_sign.alignment = WD_ALIGN_PARAGRAPH.RIGHT
    r_s1 = p_sign.add_run("TP. Hồ Chí Minh, ngày 05 tháng 10 năm 2026\n")
    r_s1.font.italic = True
    r_s2 = p_sign.add_run("Đại diện Nhóm Sinh viên Thực hiện\n\n\n")
    r_s2.font.bold = True
    r_s3 = p_sign.add_run("Phạm Huy & Nguyễn An")
    r_s3.font.bold = True
    r_s3.font.color.rgb = COLOR_PRIMARY

    # Lưu file
    OUTPUT_DOCX_DOAN1.parent.mkdir(parents=True, exist_ok=True)
    doc.save(str(OUTPUT_DOCX_DOAN1))
    print(f"✅ Đã lưu file báo cáo thành công tại: {OUTPUT_DOCX_DOAN1}")

    OUTPUT_DOCX_RESULTS.parent.mkdir(parents=True, exist_ok=True)
    doc.save(str(OUTPUT_DOCX_RESULTS))
    print(f"✅ Đã lưu bản sao lưu tại: {OUTPUT_DOCX_RESULTS}")


if __name__ == "__main__":
    build_report()
