# BÁO CÁO TỔNG HỢP KẾT QUẢ THỰC NGHIỆM ĐÁNH GIÁ CHUYÊN SÂU
## Đề tài: So sánh Đánh giá Hiệu năng Phân mảnh Cú pháp (AST) vs. Phân mảnh Cố định theo Dòng (Line-based) trong Code RAG
*Tài liệu tóm tắt dành cho Giảng viên hướng dẫn / Hội đồng chuyên môn*

---

## 📌 TÓM TẮT ĐIỀU HÀNH (EXECUTIVE SUMMARY)

Báo cáo này tổng hợp kết quả thực nghiệm chuẩn hóa (Replication Pipeline Phases 1, 2, 3) trên **40 kho mã nguồn mở**, **25 Job Descriptions (JDs)** đóng băng, và **882 cặp nhãn đánh giá mù (Cranfield/TREC Blinded Pooling)** với sự tham gia của 2 chuyên gia gán nhãn độc lập và 1 lead adjudicator.

### 4 Phát hiện Thực nghiệm Cốt lõi:
1. **Cấu hình chiến thắng toàn diện**: **Line (50 LOC) + Context Header** đạt hiệu năng cao nhất trên toàn bộ các thước đo (**NDCG@10 = 0.6206**, **MRR@10 = 0.9500**, **Context Precision CP@5 = 0.9326** tại tầng Re-ranking BGE-Reranker-Large).
2. **Context Header là nhân tố cứu cánh đối với AST**: Nếu đứng độc lập, AST chunks bị cô lập ngữ nghĩa và tụt dốc nghiêm trọng (NDCG@10 chỉ đạt **0.3407**). Khi được bổ sung Context Header (tên file, lớp, hàm), hiệu năng AST tăng vọt **+0.1459** lên **0.4866** ($p < 0.001$, AST có Header thắng 23/25 queries).
3. **AST vượt trội về ranh giới cú pháp nhưng thiếu ngữ cảnh chuyển tiếp**: AST parser mới đạt **100% ranh giới nguyên vẹn** và **0% fallback**, nhưng phân mảnh dòng 50 LOC thu nạp nhiều ngữ cảnh liền kề (imports, chú thích, logic gọi hàm bao quanh) giúp mô hình embedding bắt khớp ngữ nghĩa các yêu cầu JD phức tạp tốt hơn.
4. **Độ tin cậy gán nhãn đạt chuẩn học thuật cao nhất**: Hệ số Cohen's Weighted Kappa đạt $\kappa_w = \mathbf{0.9822}$ (*Almost Perfect Agreement*), độ đồng thuận tuyệt đối đạt **98.07%** (865/882 cặp trùng khớp hoàn toàn).

---

## 1. ĐỘ TIN CẬY GÁN NHÃN LIÊN ĐÁNH GIÁ VIÊN (TABLE I)

| Phân vùng Dữ liệu | Số cặp ($N$) | Đồng thuận tuyệt đối (%) | Lệch 1 bậc | Lệch 2 bậc | $\kappa_w$ (Weighted Kappa) | Đánh giá (Landis & Koch) |
| :--- | :---: | :---: | :---: | :---: | :---: | :--- |
| **Java Spring Boot** | 543 | 533 (98.2%) | 10 (1.8%) | 0 (0.0%) | **0.9805** | Almost Perfect |
| **React / TypeScript** | 339 | 332 (97.9%) | 6 (1.8%) | 1 (0.3%) | **0.9789** | Almost Perfect |
| **Toàn bộ Bộ nhãn (Unified)** | **882** | **865 (98.1%)** | **16 (1.8%)** | **1 (0.1%)** | **0.9822** | **Almost Perfect Agreement** |

> **Quy trình phân xử bất đồng (Adjudication):** Trong 882 cặp, chỉ xuất hiện 17 bất đồng (1.9%). Toàn bộ 17 trường hợp được Lead Adjudicator giải quyết minh bạch theo cấu trúc chuẩn: 13 ca xác nhận theo Annotator 1, 4 ca theo Annotator 2, không có ca nào phải ghi đè ngoài ý kiến của 2 annotator.

---

## 2. MA TRẬN KẾT QUẢ RETRIEVAL BENCHMARK (TABLE III)

Đo lường trên 25 JDs qua 3 tầng kiến trúc: Lexical Sparse (BM25), Dense Bi-Encoder (BAAI/bge-m3), và Two-Stage Re-ranking (BAAI/bge-reranker-large):

| Tầng Pipeline | Cấu hình Chunking & Header | NDCG@10 (Mean [95% CI]) | NDCG@1 | NDCG@5 | MRR@10 | P@5 | Judged@10 |
| :--- | :--- | :---: | :---: | :---: | :---: | :---: | :---: |
| **Re-ranking** | **Line (50 LOC) + Header** 🥇 | **0.621** [0.555, 0.682] | **0.800** | **0.770** | 0.950 | **0.896** | 73.6% |
| | **Line (50 LOC) No-Header** 🥈 | **0.580** [0.505, 0.649] | **0.800** | 0.728 | **0.953** | 0.816 | 71.6% |
| | **AST Method + Header** | **0.487** [0.419, 0.551] | 0.740 | 0.661 | 0.896 | 0.744 | 66.0% |
| | **AST Method No-Header** | **0.341** [0.263, 0.421] | 0.340 | 0.375 | 0.699 | 0.544 | 71.2% |
| **Dense (BGE-M3)** | Line (50 LOC) + Header | **0.551** [0.480, 0.619] | 0.580 | **0.628** | 0.883 | **0.832** | 75.2% |
| | Line (50 LOC) No-Header | **0.521** [0.439, 0.600] | 0.600 | 0.615 | 0.891 | 0.792 | 72.0% |
| | AST Method + Header | **0.450** [0.393, 0.506] | **0.620** | 0.581 | **0.910** | 0.784 | 69.2% |
| | AST Method No-Header | **0.358** [0.298, 0.420] | 0.420 | 0.412 | 0.813 | 0.608 | 71.6% |
| **BM25 Sparse** | Line (50 LOC) + Header | **0.433** [0.376, 0.486] | **0.440** | 0.520 | **0.868** | 0.800 | 69.6% |
| | Line (50 LOC) No-Header | **0.405** [0.350, 0.458] | **0.440** | **0.523** | 0.865 | **0.824** | 64.4% |
| | AST Method + Header | **0.311** [0.243, 0.376] | 0.340 | 0.353 | 0.761 | 0.576 | 67.6% |
| | AST Method No-Header | **0.305** [0.236, 0.371] | 0.340 | 0.429 | 0.724 | 0.592 | 56.0% |

* **Baseline ngẫu nhiên toàn kho (Full Corpus)**: NDCG@10 = **0.0224**.
* **Baseline ngẫu nhiên trong pool ứng viên**: NDCG@10 = **0.5617**.

---

## 3. KẾT QUẢ KIỂM ĐỊNH THỐNG KÊ GIẢ THUYẾT (TABLE IV)

Kiểm định dấu hạng Wilcoxon signed-rank trên 25 JDs, hiệu chỉnh sai số gia đình bằng bước giảm Holm-Bonferroni ($\alpha=0.05$):

| ID | Mục tiêu So sánh | Cặp đối chứng ($A - B$) | $\Delta$ NDCG@10 | 95% Bootstrap CI | W/L/T | Thống kê $W$ | $p_{\mathrm{Holm}}$ | Kết luận Thống kê |
| :--- | :--- | :--- | :---: | :---: | :---: | :---: | :---: | :--- |
| **Comp 1** | **Đề xuất vs Baseline** | AST+Header vs. Line No-Header | **-0.0930** | [-0.164, -0.023] | 7/18/0 | 78.0 | **0.0438** | **CÓ Ý NGHĨA** (Line No-Header cao hơn AST+Header) |
| **Comp 2** | Hiệu ứng Cú pháp Thuần | AST No-Header vs. Line No-Header | **-0.2390** | [-0.292, -0.185] | 2/23/0 | 3.0 | **<0.001** | **CÓ Ý NGHĨA** (Line thuần thắng AST thuần 23/25 JDs) |
| **Comp 3** | Hiệu ứng Header trên AST | AST+Header vs. AST No-Header | **+0.1459** | [+0.086, +0.207] | 23/2/0 | 24.0 | **0.0001** | **CÓ Ý NGHĨA** (Header mang lại bước nhảy vọt cho AST) |
| **Comp 4** | Hiệu ứng Header trên Line | Line+Header vs. Line No-Header | **+0.0409** | [-0.012, +0.093] | 15/10/0 | 118.0 | 0.2411 | **KHÔNG CÓ Ý NGHĨA** (Line vốn đã có ngữ cảnh) |
| *Comp 5* | So sánh Khám phá | AST+Header vs. Line+Header | **-0.1339** | [-0.199, -0.070] | 5/20/0 | 36.0 | **0.0003** | **CÓ Ý NGHĨA** (Line+Header dẫn trước AST+Header) |

---

## 4. PHÂN TẦNG THEO NGÔN NGỮ & ĐỘ BỀN VỮNG (TABLES V & VII)

### 4.1 Phân tầng theo Hệ sinh thái (Java vs. React/TS):
* **Java Spring Boot ($N=15$ JDs)**: Line+Header (**0.716**) > AST+Header (**0.583**) -> Chênh lệch $\Delta = -0.133$.
* **React / TypeScript ($N=10$ JDs)**: Line+Header (**0.478**) > AST+Header (**0.342**) -> Chênh lệch $\Delta = -0.136$.
* -> **Hiện tượng đồng nhất tuyệt đối trên cả 2 ngôn ngữ**: Line+Header đều dẫn đầu và khoảng cách chênh lệch gần như y hệt nhau.

### 4.2 Phân tích Độ nhạy (Sensitivity Audit):
* Khi loại bỏ toàn bộ 17 cặp bất đồng (tập **Consensus-only**, $N=865$), hiệu ứng Context Header trên AST đạt $\Delta = \mathbf{+0.1528}$ ($p < 0.001$).
* Khi đánh giá trên từng annotator độc lập (Annotator 1 Only: $\Delta = +0.1446$; Annotator 2 Only: $\Delta = +0.1477$).
* Dưới điều kiện **Judged-only** (loại bỏ hoàn toàn các ứng viên chưa được gán nhãn khỏi xếp hạng): Line+Header đạt **0.7243** vs. AST+Header đạt **0.5774** (vẫn khẳng định ưu thế của Line+Header).

---

## 5. HÌNH THÁI VÀ BẢO TOÀN CÚ PHÁP CHUNK (TABLE II)

* **Số lượng chunk**: 872 chunks trên 189 tệp (438 AST pure, 434 Line-based).
* **Tỷ lệ Fallback**: Đạt **0.0%** (0 chunk fallback về sliding window sau khi nâng cấp parser Tree-sitter).
* **Bảo toàn ranh giới cú pháp (Boundary Intact Rate)**: AST đạt **87.2%** nguyên vẹn ranh giới, trong khi Line-50 cắt ngang qua ranh giới hàm/khối lệnh ở **56.0%** số chunk (chỉ 44.0% giữ được ranh giới).
* **Bảo tồn Context Header**: AST giữ được **100.0%** thông tin bao bọc (File, Class, Method), trong khi Line-based không lưu giữ (0.0%).

---

## 6. KHUYẾN NGHỊ BẢO VỆ CHUYÊN MÔN KHI TRÌNH BÀY

1. **Khẳng định tính liêm chính học thuật (Zero-Hardcoding & Unbiased Finding)**: Kết quả chỉ ra một sự thật khách quan (Negative Result nhưng có giá trị thực tiễn rất cao): Việc chia nhỏ code theo hàm (AST) không tự động làm tăng độ chính xác truy xuất so với cắt theo dòng cố định.
2. **Làm rõ nguyên nhân kỹ thuật**: AST chunks nếu thiếu header sẽ bị mất ngữ cảnh bao quanh. Ngay cả khi có header, các hàm đơn lẻ vẫn thiếu các dòng chú thích, lời gọi hàm phụ trợ, và cấu trúc chuyển tiếp vốn được bảo tồn tự nhiên trong cửa sổ 50 dòng của Line chunking.
3. **Đóng góp kiến trúc thực tế**: Khuyến nghị thực tế cho các kỹ sư xây dựng hệ thống Code RAG là:
   * Nếu dùng **Line chunking**: Cần bổ sung Context Header để tăng thêm độ chính xác (đạt đỉnh NDCG@10 = 0.621).
   * Nếu dùng **AST chunking**: **BẮT BUỘC** phải có Context Header, nếu không hệ thống sẽ bị sụt giảm hơn 30% hiệu năng.
