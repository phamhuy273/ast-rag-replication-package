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
| Gold Standard ban đầu (Pre-registered) | 250 | 221 (88.4%) | 27 (10.8%) | 2 (0.8%) | **0.8808** | Gần như tuyệt đối (*Almost Perfect*) |
| Tập mở rộng ứng viên (Candidate Expansion) | 353 | 260 (73.7%) | 85 (24.1%) | 8 (2.3%) | **0.6826** | Đáng kể (*Substantial*) |
| **Toàn bộ bộ nhãn hợp nhất (Unified)** | **603** | **481 (79.8%)** | **112 (18.6%)** | **10 (1.7%)** | **0.7795** | **Đáng kể (*Substantial*)** |

> **Ý nghĩa khoa học & thực tiễn:**
> - Hệ số Kappa $\kappa_w = 0.7795$ vượt xa ngưỡng tin cậy tiêu chuẩn trong nghiên cứu phần mềm ($\kappa > 0.60$).
> - Tỷ lệ mâu thuẫn đối kháng nghiêm trọng (0 vs. 2) chỉ chiếm **1.7%** (10 cặp trên tổng số 603 cặp).
> - Toàn bộ 122 trường hợp bất đồng đều được đưa qua quy trình trọng tài độc lập có ghi log lý do minh bạch.

---

### Bảng II: Đặc tính hình thái, cú pháp và bảo toàn ngữ cảnh của Chunk
**Mục đích:** Đánh giá tính toàn vẹn cú pháp và giới hạn kích thước ngữ cảnh trên 40 repo (189 file mã nguồn, 798 chunks).

| Chiến lược phân mảnh | Tổng số chunk (Java / React) | LOC TB $\pm$ SD | Token TB (Chỉ code) | Token TB (Kèm Header) | Cú pháp hợp lệ (%) | Ranh giới nguyên vẹn (%) | Giữ Header (%) | Vượt 512 token (%) |
| :--- | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: |
| Line-50 (Baseline) | 434 (120/314) | 41.0 $\pm$ 13.1 | 390.8 | 419.5 | 22.4% | 44.0% | 0.0% | 124 (28.6%) |
| AST Pure (Thuần) | 234 (133/101) | 19.8 $\pm$ 16.7 | 211.3 | 254.5 | **97.9%** | **100.0%** | **100.0%** | **14 (6.0%)** |
| AST Fallback (Line-50) | 130 (20/110) | 42.9 $\pm$ 13.0 | 367.0 | 394.5 | 20.0% | 74.6% | 0.0% | 26 (20.0%) |
| **AST Kết hợp (Toàn nhánh)** | **364 (153/211)** | **28.1 $\pm$ 19.0** | **266.9** | **304.5** | **70.1%** | **90.9%** | **64.3%** | **40 (11.0%)** |

> **Ý nghĩa khoa học & thực tiễn:**
> - Phân mảnh AST thuần đạt độ chuẩn xác cú pháp gần như hoàn hảo (**97.9%** sạch lỗi cú pháp, **100%** không cắt ngang câu lệnh).
> - Ngược lại, phân mảnh dòng cắt ngang ranh giới câu lệnh ở **56.0%** số chunk (243 chunk), chỉ 22.4% là parse được trọn vẹn.
> - **Sự cần thiết của cơ chế Fallback:** Trong thực tế dự án, các hàm/phương thức lớn vượt quá 512 token bắt buộc phải dùng fallback (chiếm 35.7% nhánh AST, đặc biệt ở React lên tới 52.1%).

---

### Bảng III: Ma trận kết quả thực nghiệm truy hồi 2x2 đa tầng
**Mục đích:** So sánh hiệu năng trên 25 bản mô tả công việc (JDs) qua 3 tầng truy hồi (BM25, Dense BGE-M3, Re-ranking Cross-Encoder).

| Tầng mô hình | Cấu hình phân mảnh | NDCG@10 [95% CI] | NDCG@1 | MRR@10 | MAP@10 | CP@5 |
| :--- | :--- | :---: | :---: | :---: | :---: | :---: |
| **Re-ranking** | **Line With-Header** | **0.4994 [0.450, 0.543]** | **0.8000** | **0.9800** | **0.3705** | **0.9351** |
| Re-ranking | Line No-Header | 0.4704 [0.414, 0.524] | 0.7400 | 0.9400 | 0.3541 | 0.8841 |
| Re-ranking | AST With-Header | 0.4566 [0.405, 0.509] | 0.7200 | 0.9400 | 0.3340 | 0.9131 |
| Re-ranking | AST No-Header | 0.3445 [0.299, 0.390] | 0.4600 | 0.8000 | 0.2520 | 0.8130 |
| Dense | Line With-Header | 0.4504 [0.400, 0.502] | 0.6800 | 0.9200 | 0.3204 | 0.8710 |
| Dense | Line No-Header | 0.4460 [0.388, 0.505] | 0.7000 | 0.9400 | 0.3355 | 0.8522 |
| Dense | AST With-Header | 0.4082 [0.352, 0.465] | 0.6000 | 0.8800 | 0.2917 | 0.8174 |
| Dense | AST No-Header | 0.3201 [0.274, 0.366] | 0.5000 | 0.8200 | 0.2311 | 0.7304 |
| BM25 | AST No-Header | 0.1873 [0.138, 0.237] | 0.3000 | 0.6600 | 0.1278 | 0.6275 |
| BM25 | AST With-Header | 0.1704 [0.124, 0.217] | 0.3000 | 0.6200 | 0.1171 | 0.6364 |
| BM25 | Line With-Header | 0.1293 [0.088, 0.170] | 0.2400 | 0.5600 | 0.0872 | 0.5217 |
| BM25 | Line No-Header | 0.1042 [0.068, 0.140] | 0.2000 | 0.4400 | 0.0713 | 0.4902 |
| Baseline | Ngẫu nhiên toàn kho (Full Corpus) | 0.0195 | --- | --- | --- | --- |
| Baseline | Ngẫu nhiên trong pool ứng viên | 0.5920 | --- | --- | --- | --- |

> **Ý nghĩa khoa học & thực tiễn:**
> - Tầng **Cross-Encoder Re-ranking** mang lại bước nhảy vọt (+0.04 đến +0.05 so với Dense, +0.28 đến +0.37 so với BM25).
> - **Line With-Header là cấu hình chiến thắng toàn diện** trên mọi chỉ số (NDCG@10 = 0.4994, NDCG@1 = 0.8000, MRR@10 = 0.9800).
> - Baseline ngẫu nhiên trong pool ứng viên (0.5920) cao hơn các hệ thống xếp hạng vì danh sách pool chỉ gồm các ứng viên được chọn lọc trước (đều có nhãn $\ge 0$), trong khi xếp hạng thực tế phải đối mặt với hàng ngàn chunk nhiễu ngoài kho.

---

### Bảng IV: Kết quả kiểm định thống kê giả thuyết
**Mục đích:** Kiểm định cặp Wilcoxon signed-rank trên 25 JDs, hiệu chỉnh sai số gia đình bằng bước giảm Holm-Bonferroni ($\alpha=0.05, M=4$).

| ID | So sánh bản chất | Cặp đối chứng ($A - B$) | $\Delta$ NDCG@10 | 95% Bootstrap CI | W/L/T | Thống kê $W$ | $p_{\mathrm{raw}}$ | $p_{\mathrm{Holm}}$ | Kết luận thống kê |
| :--- | :--- | :--- | :---: | :---: | :---: | :---: | :---: | :---: | :--- |
| **Comp 1** | **Đề xuất vs Baseline** | AST+Header vs. Line No-Header | $-0.0138$ | [-0.088, 0.058] | 12/13/0 | 155.0 | 0.8532 | 0.8532 | **KHÔNG CÓ Ý NGHĨA** (Bác bỏ giả thuyết đề xuất) |
| **Comp 2** | Hiệu ứng phân mảnh thuần | AST No-Header vs. Line No-Header | $-0.1258$ | [-0.180, -0.076] | 5/20/0 | 22.0 | <0.001 | <0.001 | **CÓ Ý NGHĨA** (Line thuần thắng AST thuần) |
| **Comp 3** | Hiệu ứng Header trên AST | AST+Header vs. AST No-Header | $+0.1120$ | [0.056, 0.166] | 19/6/0 | 46.0 | 0.0010 | 0.0031 | **CÓ Ý NGHĨA** (Header cứu AST) |
| **Comp 4** | Hiệu ứng Header trên Line | Line+Header vs. Line No-Header | $+0.0291$ | [-0.017, 0.078] | 15/10/0 | 128.0 | 0.3666 | 0.7332 | **KHÔNG CÓ Ý NGHĨA** |
| *Comp 5* | So sánh khám phá | AST+Header vs. Line+Header | $-0.0428$ | [-0.106, 0.021] | 6/18/1 | 97.0 | 0.1355 | --- | *Khám phá* (Line+Header dẫn trước, $p>0.05$) |

> **Luận điểm khoa học then chốt:**
> 1. **Giả thuyết cốt lõi (Comp 1) không đạt ý nghĩa thống kê:** $\Delta = -0.0138, p = 0.8532$. Phân mảnh AST không vượt trội hơn phân mảnh dòng cơ bản.
> 2. **Sự thật về AST thuần (Comp 2):** Khi không có header, AST thua Line rất xa ($\Delta = -0.1258, p < 0.001$). Line thắng ở 20/25 bài toán.
> 3. **Nhân tố tạo nên sức mạnh của AST là Context Header (Comp 3):** Thêm header giúp AST tăng vọt $+0.1120$ ($p=0.0031$).
> 4. **So sánh công bằng nhất (Comp 5):** Khi cả hai đều gắn header, Line With-Header vẫn tốt hơn AST With-Header ($+0.0428$, 18 thắng / 6 thua / 1 hòa).

---

### Bảng V: Phân tầng hiệu năng truy hồi theo ngôn ngữ lập trình
**Mục đích:** Kiểm tra tính phụ thuộc của chiến lược phân mảnh vào đặc tính ngôn ngữ.

| Cấu hình | Java ($N=15$) | React/TypeScript ($N=10$) | Chung ($N=25$) |
| :--- | :---: | :---: | :---: |
| Line No-Header | 0.525 | 0.388 | 0.470 |
| Line With-Header | **0.536** | **0.445** | **0.499** |
| AST No-Header | 0.384 | 0.286 | 0.345 |
| AST With-Header | 0.515 | 0.369 | 0.457 |
| $\Delta$ (AST+Hdr vs. Line+Hdr) | **-0.0212** | **-0.0754** | **-0.0428** |

> **Ý nghĩa khoa học & thực tiễn:**
> - Ở Java (ngôn ngữ hướng đối tượng chặt chẽ, phương thức ngắn, rõ class/method), AST bám rất sát Line (0.515 vs 0.536, chênh lệch chỉ $-0.021$).
> - Ở React/TypeScript (nhiều JSX lồng nhau, functional components, hooks dài), AST bị tụt hậu rõ rệt (0.369 vs 0.445, chênh lệch $-0.075$) do tỷ lệ fallback quá lớn (52.1%).

---

### Bảng VI: Tỷ lệ phân mảnh Fallback trong Top-10 kết quả truy hồi
**Mục đích:** Đo lường mức độ thâm nhập của chunk fallback vào kết quả xếp hạng thực tế của nhánh AST.

| Tầng mô hình | Điều kiện Header | Tổng số Top-10 ($N$) | AST Pure (Số lượng & %) | Line-Fallback (Số lượng & %) |
| :--- | :--- | :---: | :---: | :---: |
| BM25 | No-Header | 250 | 59 (23.6%) | **191 (76.4%)** |
| BM25 | With-Header | 250 | 130 (52.0%) | 120 (48.0%) |
| Dense (BGE-M3) | No-Header | 250 | 77 (30.8%) | **173 (69.2%)** |
| Dense (BGE-M3) | With-Header | 250 | 166 (66.4%) | 84 (33.6%) |
| Re-ranking | No-Header | 250 | 75 (30.0%) | **175 (70.0%)** |
| Re-ranking | With-Header | 250 | 135 (54.0%) | 115 (46.0%) |

> **Hiện tượng khoa học cần nhấn mạnh:**
> - **Hiện tượng AST ngụy trang dưới dạng Line-chunk:** Khi không có header, có tới **70.0%** kết quả trả về của hệ thống AST thực chất là chunk fallback cắt theo dòng.
> - Lý do: Chunk AST thuần nếu không có header sẽ quá ngắn và thiếu thông tin class cha, khiến mô hình nhúng/re-ranker ưu tiên chọn chunk fallback dài hơn.

---

### Bảng VII: Phân tích độ nhạy của bộ nhãn chuẩn
**Mục đích:** Đánh giá tính ổn định của kết luận khi thay đổi cách gộp nhãn ground truth.

| Tập đánh giá thử nghiệm | Line+Hdr | Line No-Hdr | AST+Hdr | AST No-Hdr | Chênh lệch Header trên AST ($\Delta$) | Kết luận thống kê |
| :--- | :---: | :---: | :---: | :---: | :---: | :--- |
| **Chỉ dùng cặp đồng thuận (Loại 122 bất đồng)** | 0.426 | 0.413 | 0.369 | 0.294 | **+0.075 ($p = 0.0851$)** | **KHÔNG CÓ Ý NGHĨA** ($p \ge 0.05$) |
| Chỉ theo Đánh giá viên 1 (Annotator 1) | --- | --- | 0.455 | 0.346 | +0.104 ($p < 0.001$) | Có ý nghĩa ($p < 0.001$) |
| Chỉ theo Đánh giá viên 2 (Annotator 2) | --- | --- | 0.475 | 0.378 | +0.090 ($p < 0.01$) | Có ý nghĩa ($p < 0.01$) |
| **Chỉ tính ứng viên đã có nhãn (Judged-Only)** | 0.615 | 0.590 | 0.546 | 0.454 | +0.093 ($p < 0.01$) | Có ý nghĩa ($p < 0.01$) |

> **Ý nghĩa khoa học & thực tiễn:**
> - Khi loại bỏ 122 mẫu tranh chấp, hiệu ứng header trên AST giảm từ $+0.112$ xuống $+0.075$ và **mất ý nghĩa thống kê** ($p = 0.0851$).
> - Điều này chứng minh rằng các trường hợp biên/bất đồng chính là yếu tố làm tăng mức độ ý nghĩa thống kê của header trong bộ dữ liệu hoàn chỉnh.

---

### Bảng VIII: Kiểm toán độ phủ gán nhãn tập ứng viên
**Mục đích:** Kiểm toán tính công bằng và độ toàn vẹn của việc đánh giá ứng viên (Candidate Pooling).

| Nhóm cấu hình | Số cấu hình | Top-3 Đã đánh giá | Top-3 Chưa gán nhãn | Tỷ lệ phủ Top-3 (%) | Top-10 Chưa gán nhãn | Tỷ lệ phủ Top-10 (%) |
| :--- | :---: | :---: | :---: | :---: | :---: | :---: |
| **Dense (BGE-M3)** | 4 | 75 | **0** | **100.0%** | 102 -- 114 | 54.4% -- 59.2% |
| **Re-ranking (Cross-Encoder)** | 4 | 75 | **0** | **100.0%** | 109 -- 116 | 53.6% -- 56.4% |
| **BM25 (Lexical)** | 4 | 75 | **49 -- 61** | **18.7% -- 34.7%** | 174 -- 216 | 13.6% -- 30.4% |

> **Ý nghĩa khoa học & thực tiễn:**
> - Cả 8 cấu hình học sâu (Dense và Re-rank) đều đạt độ phủ gán nhãn **100.0% ở Top-3**.
> - Các cấu hình BM25 bị loại khỏi candidate pool để tiết kiệm ngân sách gán nhãn thủ công (có 220 slot top-3 chưa gán nhãn, được gán giá trị 0). Việc này được ghi chú minh bạch trong báo cáo.

---

### Bảng IX: Hòa giải trùng lặp tọa độ và phân bổ quyết định trọng tài
**Mục đích:** Minh bạch hóa quy trình hợp nhất dữ liệu từ pool ứng viên về bộ ground-truth chuẩn.

**Panel A: Khử trùng lặp tọa độ và mở rộng Pool**
- Tổng lượt xuất hiện Top-3 thô được ghi nhận: **415**
- Cặp tọa độ dòng độc nhất sau khử trùng lặp: **382** (92.0% - phát hiện 33 cặp trùng lặp giữa AST-fallback và Line-50)
- Trùng lặp với bộ Gold Standard 250 mẫu ban đầu: **29** (7.6%)
- Số mẫu ứng viên mới độc nhất cần gán nhãn: **353** (92.4%)
- **Tổng bộ nhãn hợp nhất hoàn chỉnh ($250 + 353$):** **603** (100.0%)

**Panel B: Phân bổ quyết định trọng tài trên 122 trường hợp bất đồng**
- Đồng thuận theo Đánh giá viên 1: **73** (59.8%)
- Đồng thuận theo Đánh giá viên 2: **47** (38.5%)
- Bác bỏ cả hai (Trọng tài tự đưa ra điểm độc lập): **2** (1.6%)
- Số chuỗi lý do phân xử cấu trúc độc nhất: **70** lý do

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
| `dataset/ground_truth_annotator1.csv` | `c5e7f85b0d98` | 2026-10-10 10:05 |
| `dataset/ground_truth_annotator2.csv` | `45f799ef3c0d` | 2026-10-10 10:05 |
| `dataset/ground_truth_final.csv` | `2260c21debbc` | 2026-10-10 10:05 |
| `dataset/chunk_corpus.parquet` | `e7db3acebd90` | 2026-10-09 18:05 |
| `dataset/table_3_2_measured.json` | `13a0ffccf7e0` | 2026-10-11 12:37 |
| `dataset/table_3_2_report.txt` | `9b3de1d208b6` | 2026-10-11 12:37 |
| `dataset/benchmark_results/table_3_retrieval_benchmark.csv` | `45e8a9b36821` | 2026-10-11 12:35 |
| `dataset/benchmark_results/per_query_evaluation.csv` | `c9e263d7533d` | 2026-10-11 12:35 |
| `dataset/benchmark_results/statistical_tests_report.json` | `ae5d97f45a9c` | 2026-10-11 12:35 |
| `dataset/benchmark_results/sensitivity_analysis_report.json` | `fb9d228cb78a` | 2026-10-11 12:35 |
| `dataset/benchmark_results/pool_coverage_report.csv` | `04ca8918dee7` | 2026-10-10 13:47 |
| `dataset/benchmark_results/pool_reconciliation_report.txt` | `b560793baa37` | 2026-10-10 13:49 |
| `dataset/benchmark_results/adjudication_summary.json` | `9d46bcda1fce` | 2026-10-10 13:49 |
| `dataset/manifest_repos.csv` | `7bd2b90ca5a5` | 2026-10-10 11:50 |

---

## 4 KẾT LUẬN KHOA HỌC THEN CHỐT CỦA ĐỀ TÀI

1. **Phân mảnh cú pháp AST không tạo ra lợi thế tự thân so với phân mảnh dòng:**
   - Kiểm định Comp 1 cho thấy $\Delta = -0.0138$ với $p = 0.8532$, hoàn toàn không có ý nghĩa thống kê.
   - Khi tách rời ngữ cảnh (Comp 2: AST thuần vs Line thuần), AST thuần thậm chí thua sút Line nghiêm trọng ($\Delta = -0.1258, p < 0.001$).

2. **Context Header là nhân tố quyết định hiệu quả của AST trong Code RAG:**
   - Gắn header ngữ cảnh cấu trúc (Class, Interface, Package) giúp AST tăng vọt $+0.1120$ NDCG@10 ($p = 0.0031$).
   - Nếu không có header, 70% kết quả xếp hạng top-10 của hệ thống AST thực chất bị chi phối bởi các chunk fallback cắt theo dòng.

3. **Line With-Header là kiến trúc tối ưu nhất xét trên tổng thể:**
   - Đạt NDCG@10 cao nhất (0.4994), NDCG@1 = 0.8000, MRR@10 = 0.9800, chi phí tính toán tạo chunk nhẹ hơn nhiều so với việc parse toàn bộ cây AST.

4. **Tác động phụ thuộc chặt chẽ vào đặc thù ngôn ngữ lập trình:**
   - Đối với Java (hướng đối tượng chặt chẽ), AST bám sát Line (0.515 vs 0.536).
   - Đối với React/TypeScript (nhiều JSX lồng nhau, hooks phức tạp), AST tụt hậu rõ rệt (0.369 vs 0.445) do tỷ lệ fallback lên tới 52.1%.

---
*Báo cáo được khởi tạo tự động hoàn toàn bởi `scripts/make_report.py` - Tuân thủ tiêu chuẩn Không Hardcode R1-R46.*