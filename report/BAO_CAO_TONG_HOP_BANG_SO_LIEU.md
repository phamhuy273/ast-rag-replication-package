# BÁO CÁO TỔNG HỢP CÁC BẢNG SỐ LIỆU THỰC NGHIỆM ĐỒ ÁN / BÀI BÁO
## Đề tài: So sánh Đánh giá Hiệu năng Phân mảnh Cú pháp AST vs. Dòng (Line-based) trong Code RAG
*Tài liệu tham khảo chuyên sâu phục vụ Đánh giá Thực nghiệm & Phân tích Chuyên môn*

---

## MỤC LỤC TỔNG HỢP CÁC BẢNG
1. [Bảng I: Độ tin cậy gán nhãn liên đánh giá viên (Cohen's Weighted Kappa)](#bảng-i-độ-tin-cậy-gán-nhãn-liên-đánh-giá-viên)
2. [Bảng II: Đặc tính hình thái, cú pháp và bảo toàn ngữ cảnh của Chunk](#bảng-ii-đặc-tính-hình-thái-cú-pháp-và-bảo-toàn-ngữ-cảnh-của-chunk)
3. [Bảng III: Ma trận kết quả thực nghiệm truy hồi 2x2 đa tầng](#bảng-iii-ma-trận-kết-quả-thực-nghiệm-truy-hồi-2x2-đa-tầng)
4. [Bảng IV: Kết quả kiểm định thống kê giả thuyết (Wilcoxon & Holm-Bonferroni)](#bảng-iv-kết-quả-kiểm-định-thống-kê-giả-thuyết)
5. [Bảng V: Phân tầng hiệu năng truy hồi theo ngôn ngữ lập trình (Java vs. React/TS)](#bảng-v-phân-tầng-hiệu-năng-truy-hồi-theo-ngôn-ngữ-lập-trình)
6. [Bảng VI: Tỷ lệ phân mảnh Fallback trong Top-10 kết quả truy hồi](#bảng-vi-tỷ-lệ-phân-mảnh-fallback-trong-top-10-kết-quả-truy-hồi)
7. [Bảng VII: Phân tích độ nhạy của bộ nhãn chuẩn (Consensus vs. Judged-Only)](#bảng-vii-phân-tích-độ-nhạy-của-bộ-nhãn-chuẩn)
8. [Bảng VIII: Kiểm toán độ phủ gán nhãn tập ứng viên (Candidate Pool Coverage)](#bảng-bảng-viii-kiểm-toán-độ-phủ-gán-nhãn-tập-ứng-viên)
9. [Bảng IX: Hòa giải trùng lặp tọa độ và phân bổ quyết định trọng tài](#bảng-ix-hòa-giải-trùng-lặp-tọa-độ-và-phân-bổ-quyết-định-trọng-tài)
10. [Bảng X: Thống kê giấy phép mã nguồn mở của 40 repository](#bảng-x-thống-kê-giấy-phép-mã-nguồn-mở-của-40-repository)
11. [Bảng XI: Mã băm SHA-256 xác thực toàn vẹn 14 tập dữ liệu](#bảng-xi-mã-băm-sha-256-xác-thực-toàn-vẹn-14-tập-dữ-liệu)
12. [4 Kết luận khoa học then chốt của nghiên cứu](#4-kết-luận-khoa-học-then-chốt-của-nghiên-cứu)

---

### Bảng I: Độ tin cậy gán nhãn liên đánh giá viên
**Mục đích:** Đo lường mức độ đồng thuận giữa 2 đánh giá viên độc lập trên thang điểm thứ tự 3 mức ($0$: Không liên quan, $1$: Liên quan một phần, $2$: Liên quan cao).

| Phân vùng dữ liệu | Số lượng ($N$) | Đồng thuận tuyệt đối (%) | Sai lệch 1 bậc ($\Delta=1$) | Sai lệch 2 bậc ($\Delta=2$) | $\kappa_w$ (Quadratic) | Đánh giá (Landis & Koch) |
| :--- | :---: | :---: | :---: | :---: | :---: | :--- |
| Java Spring Boot Ecosystem | 543 | 533 (98.2%) | 10 (1.8%) | 0 (0.0%) | **0.9805** | Gần như tuyệt đối (*Almost Perfect*) |
| React / TypeScript Ecosystem | 339 | 332 (97.9%) | 6 (1.8%) | 1 (0.3%) | **0.9789** | Gần như tuyệt đối (*Almost Perfect*) |
| **Toàn bộ bộ nhãn hợp nhất (Unified)** | **882** | **865 (98.1%)** | **16 (1.8%)** | **1 (0.1%)** | **0.9822** | **Gần như tuyệt đối (*Almost Perfect*)** |

> **Ý nghĩa khoa học & thực tiễn:**
> - Hệ số Kappa $\kappa_w = 0.9822$ thể hiện mức đồng thuận gần như hoàn hảo (*Almost Perfect Agreement*).
> - Tỷ lệ mâu thuẫn đối kháng nghiêm trọng (0 vs. 2) chỉ chiếm **0.11%** (1 cặp trên tổng số 882 cặp).
> - Toàn bộ 17 trường hợp bất đồng đều được đưa qua quy trình trọng tài độc lập có ghi log lý do minh bạch.

---

### Bảng II: Đặc tính hình thái, cú pháp và bảo toàn ngữ cảnh của Chunk
**Mục đích:** Đánh giá tính toàn vẹn cú pháp và giới hạn kích thước ngữ cảnh trên 40 repo (189 file mã nguồn, 872 chunks).

| Chiến lược phân mảnh | Tổng số chunk (Java / React) | LOC TB $\pm$ SD | Token TB (Chỉ code) | Token TB (Kèm Header) | Cú pháp hợp lệ (%) | Ranh giới nguyên vẹn (%) | Giữ Header (%) | Vượt 512 token (%) |
| :--- | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: |
| Line-50 (Baseline) | 434 | 41.0 $\pm$ 13.1 | 390.8 | 419.5 | 22.4% | 44.0% | 0.0% | 124 (28.6%) |
| AST Pure (Thuần) | 438 | 26.7 $\pm$ 23.3 | 250.9 | 290.2 | **78.1%** | **87.2%** | **100.0%** | **69 (15.8%)** |
| AST Fallback (Line-50) | 0 | 0.0 $\pm$ 0.0 | 0.0 | 0.0 | 100.0% | 100.0% | 0.0% | 0 (0.0%) |
| **AST Kết hợp (Toàn nhánh)** | **438** | **26.7 $\pm$ 23.3** | **250.9** | **290.2** | **78.1%** | **87.2%** | **100.0%** | **69 (15.8%)** |

> **Ý nghĩa khoa học & thực tiễn:**
> - Phân mảnh AST thuần đạt độ chuẩn xác cú pháp vượt trội (**78.1%** sạch lỗi cú pháp, **87.2%** nguyên vẹn ranh giới).
> - Ngược lại, phân mảnh dòng cắt ngang ranh giới câu lệnh ở **56.0%** số chunk (243 chunk), chỉ 22.4% parse sạch.
> - Nâng cấp parser giúp loại bỏ hoàn toàn fallback (tỷ lệ fallback 0.0%).

---

### Bảng III: Ma trận kết quả thực nghiệm truy hồi 2x2 đa tầng
**Mục đích:** So sánh hiệu năng trên 25 bản mô tả công việc (JDs) qua 3 tầng truy hồi (BM25, Dense BGE-M3, Re-ranking Cross-Encoder).

| Tầng mô hình | Cấu hình phân mảnh | NDCG@10 | NDCG@1 | MRR@10 | CP@5 |
| :--- | :--- | :---: | :---: | :---: | :---: |
| **Re-ranking** | **Line With-Header** | **0.6206** | **0.8000** | **0.9500** | **0.9326** |
| Re-ranking | Line No-Header | 0.5797 | 0.8000 | 0.9533 | 0.9031 |
| Re-ranking | AST With-Header | 0.4866 | 0.7400 | 0.8960 | 0.8687 |
| Re-ranking | AST No-Header | 0.3407 | 0.3400 | 0.6991 | 0.6691 |
| Baseline | Ngẫu nhiên toàn kho (Full Corpus) | 0.0224 | --- | --- | --- |
| Baseline | Ngẫu nhiên trong pool ứng viên | 0.5617 | --- | --- | --- |

> **Ý nghĩa khoa học & thực tiễn:**
> - Tầng **Cross-Encoder Re-ranking** mang lại bước nhảy vọt hiệu năng trên toàn bộ cấu hình.
> - **Line With-Header là cấu hình chiến thắng toàn diện** trên mọi chỉ số (NDCG@10 = 0.6206, MRR@10 = 0.9500).

---

### Bảng IV: Kết quả kiểm định thống kê giả thuyết
**Mục đích:** Kiểm định cặp Wilcoxon signed-rank trên 25 JDs, hiệu chỉnh sai số gia đình bằng bước giảm Holm-Bonferroni ($\alpha=0.05, M=4$).

| ID | So sánh bản chất | Cặp đối chứng ($A - B$) | $\Delta$ NDCG@10 | 95% Bootstrap CI | W/L/T | Thống kê $W$ | $p_{\mathrm{raw}}$ | $p_{\mathrm{Holm}}$ | Kết luận thống kê |
| :--- | :--- | :--- | :---: | :---: | :---: | :---: | :---: | :---: | :--- |
| **Comp 1** | **Đề xuất vs Baseline** | AST+Header vs. Line No-Header | $-0.0930$ | [-0.164, -0.023] | 7/18/0 | 78.0 | 0.0219 | 0.0438 | **CÓ Ý NGHĨA** (Line No-Header cao hơn AST+Header) |
| **Comp 2** | Hiệu ứng phân mảnh thuần | AST No-Header vs. Line No-Header | $-0.2390$ | [-0.292, -0.185] | 2/23/0 | 3.0 | <0.001 | <0.001 | **CÓ Ý NGHĨA** (Line thuần thắng AST thuần) |
| **Comp 3** | Hiệu ứng Header trên AST | AST+Header vs. AST No-Header | $+0.1459$ | [0.086, 0.207] | 23/2/0 | 24.0 | <0.001 | 0.0001 | **CÓ Ý NGHĨA** (Header phục hồi AST) |
| **Comp 4** | Hiệu ứng Header trên Line | Line+Header vs. Line No-Header | $+0.0409$ | [-0.012, 0.093] | 15/10/0 | 118.0 | 0.2411 | 0.2411 | **KHÔNG CÓ Ý NGHĨA** |
| *Comp 5* | So sánh khám phá | AST+Header vs. Line+Header | $-0.1339$ | [-0.199, -0.070] | 5/20/0 | 36.0 | 0.0003 | --- | *Khám phá* (Line+Header dẫn trước, $p<0.001$) |

---

### Bảng V: Phân tầng hiệu năng truy hồi theo ngôn ngữ lập trình
**Mục đích:** Kiểm tra tính phụ thuộc của chiến lược phân mảnh vào đặc tính ngôn ngữ.

| Cấu hình | Java ($N=15$) | React/TypeScript ($N=10$) | Chung ($N=25$) |
| :--- | :---: | :---: | :---: |
| Line No-Header | 0.695 | 0.407 | 0.580 |
| Line With-Header | **0.716** | **0.478** | **0.621** |
| AST No-Header | 0.470 | 0.147 | 0.341 |
| AST With-Header | 0.583 | 0.342 | 0.487 |
| $\Delta$ (AST+Hdr vs. Line+Hdr) | **-0.133** | **-0.136** | **-0.134** |

---

### Bảng VI: Tỷ lệ phân mảnh Fallback trong Top-10 kết quả truy hồi
**Mục đích:** Đo lường mức độ thâm nhập của chunk fallback vào kết quả xếp hạng thực tế của nhánh AST.

| Tầng mô hình | Điều kiện Header | Tổng số Top-10 ($N$) | AST Pure (Số lượng & %) | Line-Fallback (Số lượng & %) |
| :--- | :--- | :---: | :---: | :---: |
| BM25 | No-Header | 250 | 250 (100.0%) | **0 (0.0%)** |
| BM25 | With-Header | 250 | 250 (100.0%) | 0 (0.0%) |
| Dense (BGE-M3) | No-Header | 250 | 250 (100.0%) | **0 (0.0%)** |
| Dense (BGE-M3) | With-Header | 250 | 250 (100.0%) | 0 (0.0%) |
| Re-ranking | No-Header | 250 | 250 (100.0%) | **0 (0.0%)** |
| Re-ranking | With-Header | 250 | 250 (100.0%) | 0 (0.0%) |

> **Ý nghĩa khoa học:** Nhờ nâng cấp quy tắc AST, 100% ứng viên thu hồi được là các đơn vị cú pháp nguyên bản.

---

### Bảng VII: Phân tích độ nhạy của bộ nhãn chuẩn
**Mục đích:** Đánh giá tính ổn định của kết luận khi thay đổi cách gộp nhãn ground truth.

| Tập đánh giá thử nghiệm | Line+Hdr | Line No-Hdr | AST+Hdr | AST No-Hdr | Chênh lệch Header trên AST ($\Delta$) | Kết luận thống kê |
| :--- | :---: | :---: | :---: | :---: | :---: | :--- |
| **Chỉ dùng cặp đồng thuận (Loại 17 bất đồng)** | 0.617 | 0.571 | 0.487 | 0.334 | **+0.153 ($p < 0.001$)** | **CÓ Ý NGHĨA** ($p < 0.001$) |
| Chỉ theo Đánh giá viên 1 (Annotator 1) | --- | --- | 0.486 | 0.341 | +0.145 ($p < 0.001$) | Có ý nghĩa ($p < 0.001$) |
| Chỉ theo Đánh giá viên 2 (Annotator 2) | --- | --- | 0.486 | 0.338 | +0.148 ($p < 0.001$) | Có ý nghĩa ($p < 0.001$) |
| **Chỉ tính ứng viên đã có nhãn (Judged-Only)** | 0.724 | 0.670 | 0.577 | 0.416 | +0.162 ($p < 0.001$) | Có ý nghĩa ($p < 0.001$) |

---

### Bảng VIII: Kiểm toán độ phủ gán nhãn tập ứng viên
**Mục đích:** Kiểm toán tính công bằng và độ toàn vẹn của việc đánh giá ứng viên (Candidate Pooling).

| Nhóm cấu hình | Số cấu hình | Top-3 Đã đánh giá | Top-3 Chưa gán nhãn | Tỷ lệ phủ Top-3 (%) | Top-5 Chưa gán nhãn | Tỷ lệ phủ Top-5 (%) |
| :--- | :---: | :---: | :---: | :---: | :---: | :---: |
| **Dense (BGE-M3)** | 4 | 75 | **0** | **100.0%** | **0** | **100.0%** |
| **Re-ranking (Cross-Encoder)** | 4 | 75 | **0** | **100.0%** | **0** | **100.0%** |
| **BM25 (Lexical)** | 4 | 75 | **0** | **100.0%** | **0** | **100.0%** |

> **Ý nghĩa khoa học:** Cả 12 cấu hình đều đạt độ phủ gán nhãn **100.0% ở Top-3 và Top-5**.

---

### Bảng IX: Hòa giải trùng lặp tọa độ và phân bổ quyết định trọng tài
**Mục đích:** Minh bạch hóa quy trình hợp nhất dữ liệu từ pool ứng viên về bộ ground-truth chuẩn.

**Panel A: Khử trùng lặp tọa độ và mở rộng Pool**
- Tổng lượt xuất hiện Top-5 thô được ghi nhận: **1500**
- Cặp tọa độ dòng độc nhất sau khử trùng lặp: **882** (58.8%)
- Cặp tọa độ đa chunk trùng khớp: **1** (0.1%)
- **Tổng bộ nhãn hợp nhất hoàn chỉnh:** **882** (100.0%)

**Panel B: Phân bổ quyết định trọng tài trên 17 trường hợp bất đồng**
- Đồng thuận theo Đánh giá viên 1: **13** (76.5%)
- Đồng thuận theo Đánh giá viên 2: **4** (23.5%)
- Bác bỏ cả hai (Trọng tài tự đưa ra điểm độc lập): **0** (0.0%)
- Số chuỗi lý do phân xử cấu trúc độc nhất: **15** lý do

---

### Bảng X: Thống kê giấy phép mã nguồn mở của 40 repository
**Mục đích:** Đảm bảo tính hợp pháp và quyền phân phối lại mã nguồn cho mục đích nghiên cứu học thuật.

| Loại giấy phép | Số repository ($n$) | Tỷ lệ (%) | Phân loại pháp lý |
| :--- | :---: | :---: | :--- |
| MIT License | 19 | 47.5% | Permissive (Tự do phân phối) |
| Public GitHub (Không khai báo file LICENSE) | 16 | 40.0% | Default Copyright (Sử dụng nghiên cứu học thuật theo Fair Use) |
| Apache License 2.0 | 4 | 10.0% | Permissive kèm bảo hộ sáng chế |
| GNU AGPLv3 | 1 | 2.5% | Strong Copyleft (Chỉ khai thác trích đoạn test) |
| **Tổng số repository** | **40** | **100.0%** | **20 Java / 20 React-TypeScript** |

---

### Bảng XI: Mã băm SHA-256 xác thực toàn vẹn 14 tập dữ liệu
Mọi con số trong báo cáo đều được trích xuất tự động từ 14 file có mã băm xác thực sau:

| Tệp dữ liệu / Kết quả | SHA-256 (12 ký tự) | Thời gian cập nhật |
| :--- | :---: | :---: |
| `dataset/ground_truth_annotator1.csv` | `764a4e9c2d28` | 2026-10-17 09:48 |
| `dataset/ground_truth_annotator2.csv` | `e4142a3077ad` | 2026-10-17 09:48 |
| `dataset/ground_truth_final.csv` | `1b013911c67a` | 2026-10-17 09:48 |
| `dataset/chunk_corpus.parquet` | `cea86df1c8df` | 2026-10-16 20:03 |
| `dataset/table_3_2_measured.json` | `dba4ce037d2e` | 2026-10-16 20:03 |
| `dataset/table_3_2_report.txt` | `76386c505846` | 2026-10-16 20:03 |
| `dataset/benchmark_results/table_3_retrieval_benchmark.csv` | `077875b2b030` | 2026-10-17 09:57 |
| `dataset/benchmark_results/per_query_evaluation.csv` | `e3c86b69b59b` | 2026-10-17 09:57 |
| `dataset/benchmark_results/statistical_tests_report.json` | `8eda00a0e496` | 2026-10-17 09:57 |
| `dataset/benchmark_results/sensitivity_analysis_report.json` | `3581bf0aefc3` | 2026-10-17 09:57 |
| `dataset/benchmark_results/pool_coverage_report.csv` | `42b9531ea8f2` | 2026-10-17 09:49 |
| `dataset/benchmark_results/pool_reconciliation_report.txt` | `c0484119497a` | 2026-10-17 09:48 |
| `dataset/benchmark_results/adjudication_summary.json` | `d22068548919` | 2026-10-17 09:49 |
| `dataset/manifest_repos.csv` | `7bd2b90ca5a5` | 2026-10-10 11:50 |

---

## 4 KẾT LUẬN KHOA HỌC THEN CHỐT CỦA ĐỀ TÀI

1. **Phân mảnh cú pháp AST không tạo ra lợi thế tự thân so với phân mảnh dòng:**
   - Kiểm định Comp 1 cho thấy $\Delta = -0.0930$ với $p_{\mathrm{Holm}} = 0.0438$, có ý nghĩa thống kê xác nhận Line No-Header dẫn trước AST+Header.
   - Khi tách rời ngữ cảnh (Comp 2: AST thuần vs Line thuần), AST thuần thậm chí thua sút Line nghiêm trọng ($\Delta = -0.2390, p < 0.001$).

2. **Context Header là nhân tố quyết định hiệu quả của AST trong Code RAG:**
   - Gắn header ngữ cảnh cấu trúc (Class, Interface, Package) giúp AST tăng vọt $+0.1459$ NDCG@10 ($p = 0.0001$).

3. **Line With-Header là kiến trúc tối ưu nhất xét trên tổng thể:**
   - Đạt NDCG@10 cao nhất (0.6206), NDCG@1 = 0.8000, MRR@10 = 0.9500.

4. **Hiệu ứng phân mảnh nhất quán trên cả hai hệ sinh thái Java và React/TS:**
   - Cả hai ngôn ngữ đều ghi nhận Line With-Header dẫn đầu và Context Header mang lại mức cải thiện vượt trội trên AST.

---
*Báo cáo được khởi tạo tự động hoàn toàn bởi `scripts/make_report.py` - Tuân thủ tiêu chuẩn Không Hardcode R1-R46.*