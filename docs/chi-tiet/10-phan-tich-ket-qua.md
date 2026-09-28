# 10. Phân tích và trình bày kết quả: tài liệu chuyên sâu

> Thuộc [Mục 10 của bản mô tả chính](../mo-ta-chi-tiet-do-an.md#10-phân-tích-và-trình-bày-kết-quả) · [Danh mục tài liệu chuyên sâu](README.md)

**Tóm tắt nhanh**
- Pipeline phân tích **tái lập được**: dữ liệu thô → bảng dẫn xuất → biểu đồ, bằng notebook có thứ tự và môi trường Python được ghim phiên bản.
- **Kế hoạch phân tích được cố định trước** khi có dữ liệu: chỉ số chính, so sánh chính, quy tắc kết luận.
- Thống kê: đơn vị phân tích là **một lượt chạy**; so sánh **cặp theo khối**; khoảng tin cậy dùng phân phối t và bootstrap; đặt **ngưỡng ý nghĩa thực tiễn**.
- Đặc tả 8 biểu đồ (C1–C8), kèm câu hỏi nghiên cứu mà mỗi biểu đồ trả lời; hướng dẫn diễn giải và khung chương 5 của luận văn.

---

## 1. Pipeline phân tích

```text
runs/<run-id>/ (thô)
   │  00_validate.ipynb     đọc checks.json, loại lượt invalid, báo cáo độ phủ ma trận
   ▼
data/derived/*.parquet
   │  01_build_tables.py    req, phase_metrics, run_metrics, cell_summary, coldstart
   ▼
   ├─ 02_calibration.ipynb  đường cong TTFT/ITL/B theo λ → C, B*, Hình 15 (thật)
   ├─ 03_coldstart.ipynb    8 pha × L0/L1/L2 → C6
   ├─ 04_matrix.ipynb       RQ1, RQ3 → C1–C5, C7, C8, bảng tổng hợp
   └─ 05_figures.py         xuất mọi hình cho luận văn (SVG/PNG) với cùng một style
```

- Môi trường Python được ghim bằng `uv` hoặc `pip-tools` (`requirements.lock`). Chạy toàn bộ bằng `make analysis`.
- Notebook **không sửa dữ liệu thô**. Mọi quyết định loại dữ liệu đều nằm trong code, có lý do đi kèm.
- `01_build_tables.py` có **unit test** cho các hàm tính chỉ số (TPOT, cắt pha, thời gian hồi phục), chạy trên dữ liệu nhỏ biết trước kết quả.

---

## 2. Kiểm tra dữ liệu trước khi phân tích

| Kiểm tra | Hành động |
|---|---|
| Độ phủ ma trận: mỗi ô có đủ số lượt hợp lệ? | Liệt kê ô còn thiếu để lên lịch chạy bù |
| Phân phối độ lệch lịch gửi, RTT, lệch đồng hồ | Đảm bảo mọi lượt đã dùng đều đạt ngưỡng |
| So sánh TTFT client với TTFT server | Chênh lệch phải ổn định; nếu có bất thường thì điều tra |
| Tổng request mỗi lượt so với lịch | Khớp (±0,5%) |
| Giá trị bất thường (TTFT âm, n_out ≠ 256 mà không có lỗi) | Tìm nguyên nhân, **không xoá im lặng** |

---

## 3. Kế hoạch phân tích (đăng ký trước)

Cố định **trước khi** chạy khối 1 và commit vào repo (`analysis/PLAN.md`). Nếu sau này thay đổi, phải ghi lại lý do.

| RQ | So sánh chính | Chỉ số chính | Kịch bản chính | Quy tắc kết luận |
|---|---|---|---|---|
| RQ1 | A2 với A1, A3 với A1, A2 với A3 | SLO attainment (cả lượt), thời gian hồi phục (KB2) | KB2, KB5 | Khoảng tin cậy 95% của hiệu số cặp không chứa 0 **và** hiệu số ≥ 5 điểm phần trăm |
| RQ2 | L2 với L0 | Tổng cold start; SLO attainment ở KB2 × A2 | Thí nghiệm cold start | Giảm ≥ 50% (H2) |
| RQ3 | Autoscaling tốt nhất với S4 và S1 | GPU-giờ (% so với S4), SLO attainment | Từng kịch bản | H3: SLO kém S4 không quá 5 điểm phần trăm **và** GPU-giờ ≤ 70% của S4 (KB2, KB4, KB5) |

**Chỉ số phụ** (báo cáo nhưng không dùng để kết luận chính): p99, goodput, token/GPU-giờ, số lần scale, flapping, tỷ lệ dư năng lực.

---

## 4. Phương pháp thống kê

### 4.1. Đơn vị phân tích

Đơn vị là **một lượt chạy**, không phải một request. Các request trong cùng một lượt không độc lập với nhau: chúng chia chung hàng đợi, chung lần scale. Nếu coi hàng nghìn request là hàng nghìn mẫu độc lập, khoảng tin cậy sẽ hẹp giả tạo.

### 4.2. So sánh cặp theo khối

Mỗi khối (phiên) chứa một lượt của mọi ô ma trận (xem [08 §8](08-thiet-ke-thi-nghiem.md#8-ma-trận-thứ-tự-và-khối)). Với hai cấu hình X và Y trong cùng kịch bản:

$$
d_b = m_X^{(b)} - m_Y^{(b)}, \quad \bar d = \frac{1}{n}\sum_b d_b, \quad
\text{CI}_{95\%} = \bar d \pm t_{0{,}975;\,n-1}\,\frac{s_d}{\sqrt n}
$$

Với n = 3 thì t = 4,30, nên khoảng tin cậy rất rộng. Để bù lại:
- Luôn **báo cáo từng giá trị riêng lẻ** (dot plot), không chỉ trung bình.
- Các ô trọng tâm (KB2, KB5 × A1–A3) chạy **5 lượt** nếu ngân sách cho phép (t = 2,78).
- Nhấn mạnh **độ lớn hiệu ứng** và tính nhất quán qua các khối, ví dụ "A2 tốt hơn A1 trong cả 3/3 khối".

### 4.3. Bootstrap

- **Trong một lượt:** khoảng tin cậy cho p95 của một pha, bằng bootstrap trên các request (1.000 lần).
- **Theo ô ma trận:** bootstrap phân tầng: lấy mẫu lại các lượt, rồi trong mỗi lượt lấy mẫu lại các request. Dùng khi muốn khoảng tin cậy cho p95 "gộp" của một ô.

### 4.4. Ngưỡng ý nghĩa thực tiễn

| Chỉ số | Khác biệt "đáng kể" |
|---|---|
| SLO attainment | ≥ 5 điểm phần trăm |
| GPU-giờ | ≥ 10% (so với S4) |
| Cold start | ≥ 20% hoặc ≥ 30 s |
| Thời gian hồi phục | ≥ 30 s |

Kết luận chỉ được viết thành "khác biệt" khi **vừa** có ý nghĩa thống kê (khoảng tin cậy không chứa 0), **vừa** vượt ngưỡng thực tiễn.

### 4.5. So sánh nhiều lần

Mỗi RQ chỉ có một số ít so sánh chính, đã đăng ký trước. Các so sánh khác được trình bày là **khám phá**, không dùng để khẳng định.

---

## 5. Đặc tả các biểu đồ

**Quy ước chung:**
- Màu gắn cố định với từng cấu hình, theo thứ tự S1, S4, A1, A2, A3. Dùng bảng màu đã kiểm định cho người mù màu, giống các sơ đồ trong tài liệu.
- Có chú giải (legend), và gắn nhãn trực tiếp khi có từ 4 đường trở xuống.
- **Không dùng biểu đồ hai trục tung.** Hai đại lượng khác đơn vị thì vẽ hai biểu đồ riêng.
- Ghi số mẫu n trên mọi biểu đồ có khoảng tin cậy.

| Mã | Biểu đồ | Trả lời | Mã hoá |
|---|---|---|---|
| **C1** | **Chuỗi thời gian căn theo nhau**: 4 ô xếp dọc, chung trục thời gian: (1) λ(t) theo lịch, (2) số replica của từng cấu hình, (3) TTFT p95 cửa sổ trượt 30 s, (4) độ dài hàng đợi | RQ1, RQ2 | Đường bậc thang cho replica; đường ngang SLO; vùng tô khi quá tải |
| **C2** | CDF của TTFT theo cấu hình (mỗi kịch bản một ô) | RQ1 | Đường CDF; đường dọc SLO 2 s |
| **C3** | SLO attainment theo cấu hình × kịch bản | RQ1, RQ3 | Cột nhóm kèm khoảng tin cậy và chấm các lượt riêng lẻ |
| **C4** | GPU-giờ (% so với S4) theo cấu hình × kịch bản | RQ3 | Như C3 |
| **C5** | **Trade-off**: trục hoành GPU-giờ (% S4), trục tung SLO attainment; mỗi cấu hình một điểm, mỗi kịch bản một ô | RQ3 | Điểm kèm thanh sai số 2 chiều; góc trên bên trái là "tốt" |
| **C6** | Phân rã cold start đo thật ở L0/L1/L2 | RQ2 | Cột ngang chồng theo 8 pha (như Hình 5 và 12) kèm khoảng tin cậy của tổng |
| **C7** | Phân rã thời gian phản ứng ở KB2: phát hiện và cung cấp, theo A1/A2/A3 | RQ1, RQ2 | Cột chồng 2 phần |
| **C8** | Bảng nhiệt tổng hợp: SLO attainment theo cấu hình × kịch bản | Tổng quan | Thang màu một sắc độ; ghi số trong từng ô |

---

## 6. Diễn giải kết quả

### 6.1. Cách viết một phát hiện

Mỗi phát hiện gồm 4 phần: **quan sát → số liệu → cơ chế → phạm vi áp dụng**. Ví dụ (minh hoạ, chưa phải kết quả thật):

> *Ở KB2, A2 đạt SLO attainment 94% (KTC 95%: 91–97%), cao hơn A1 11 điểm phần trăm, nhất quán trong 3/3 khối. Nguyên nhân: GPU_UTIL của A1 đạt khoảng 97% ngay khi tải còn 0,5C, nên A1 đã scale lên 4 replica từ trước khi có spike. Do đó A1 không vi phạm SLO lúc spike, nhưng tốn gấp 2,1 lần GPU-giờ so với A2 ở pha `pre`. Kết luận này áp dụng cho model 7B trên GPU 24 GB với output cố định 256 token.*

### 6.2. Khi kết quả ngược giả thuyết

- Báo cáo đúng như vậy, và tìm **cơ chế** giải thích bằng metric phía server: hàng đợi, KV-cache, thời gian của từng pha cold start.
- Kiểm tra xem có phải do vấn đề đo lường (máy tạo tải, cắt pha) hay không. Nếu không phải, đó là một phát hiện.
- Ví dụ: nếu A3 tốt hơn A2, có thể vì prompt dài làm KV-cache phản ánh tải tốt hơn số request.

### 6.3. Tránh khái quát quá mức

Tách rõ:
- **Kết luận cơ chế:** khả năng khái quát cao, ví dụ "GPU_UTIL bão hoà nên không phản ánh tải".
- **Kết luận định lượng:** chỉ đúng cho cấu hình đã đo, ví dụ "tiết kiệm 38% GPU-giờ".

---

## 7. Khung chương "Thí nghiệm và đánh giá" trong luận văn

```text
5.1 Môi trường và phương pháp thí nghiệm (tóm tắt 08, 09)
5.2 Hiệu chỉnh năng lực (C, B*, đường cong)
5.3 RQ1 – So sánh các metric scale
    5.3.1 Hành vi theo thời gian (C1 cho KB2, KB5)
    5.3.2 SLO attainment và độ trễ phát hiện (C3, C7)
    5.3.3 Phân tích nguyên nhân (GPU_UTIL, định luật Little, KV-cache)
5.4 RQ2 – Cold start (C6; KB2 ở L0 so với L2)
5.5 RQ3 – Trade-off GPU-giờ và SLO (C4, C5, C8)
5.6 Scale-down và độ an toàn (lỗi trong KB4, flapping)
5.7 Khuyến nghị cấu hình
5.8 Các mối đe doạ tính hợp lệ (tham chiếu 03 §5)
```

---

## 8. Câu hỏi hội đồng có thể đặt ra

**Ba lần chạy có đủ tin cậy không?**
Nhóm không dựa vào p-value. Kết quả được trình bày kèm độ lớn hiệu ứng, khoảng tin cậy, từng giá trị riêng lẻ, và tính nhất quán qua các khối, trên một thiết kế so sánh cặp giúp loại bỏ nhiễu do phiên chạy. Các ô trọng tâm có thêm lượt chạy.

**Vì sao đơn vị phân tích không phải là request, trong khi có hàng nghìn request?**
Các request trong một lượt phụ thuộc lẫn nhau (chung hàng đợi, chung lần scale). Coi chúng là mẫu độc lập sẽ làm khoảng tin cậy hẹp sai lệch.

**Có chọn lọc kết quả đẹp không?**
Không. Kế hoạch phân tích được commit trước khi chạy, và mọi lượt kể cả lượt không hợp lệ đều được lưu và công bố cùng lý do.
