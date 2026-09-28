# 2. Mục tiêu và câu hỏi nghiên cứu: tài liệu chuyên sâu

> Thuộc [Mục 2 của bản mô tả chính](../mo-ta-chi-tiet-do-an.md#2-mục-tiêu-và-câu-hỏi-nghiên-cứu) · [Danh mục tài liệu chuyên sâu](README.md)

**Tóm tắt nhanh**
- Bảy mục tiêu trong đề cương được **giữ nguyên**. Tài liệu này chỉ viết lại chúng theo dạng đo được: mỗi mục tiêu có tiêu chí hoàn thành, hạn chót và người chịu trách nhiệm.
- Ba câu hỏi nghiên cứu (RQ1–RQ3) được tách thành **biến độc lập, biến phụ thuộc, biến kiểm soát, thí nghiệm, chỉ số và quy tắc kết luận**.
- Có **ma trận truy vết** để bất kỳ ai cũng lần được từ câu hỏi tới số liệu, rồi tới biểu đồ và chương luận văn.
- Nêu rõ những gì **không phải** mục tiêu, và chia mức thành công thành **Must / Should / Could**.

---

## 1. Từ bài toán đến câu hỏi nghiên cứu

```text
Bài toán (mục 1):  tối thiểu GPU-giờ  với ràng buộc  SLO attainment ≥ α
          │
          ├─ Chính sách π dùng tín hiệu nào?           → RQ1 (chọn metric)
          ├─ Độ trễ thực thi D (cold start) lớn tới đâu,
          │  giảm được bao nhiêu?                       → RQ2 (cold start)
          └─ Cuối cùng đổi được bao nhiêu GPU-giờ
             lấy bao nhiêu SLO, ở từng mẫu tải?         → RQ3 (trade-off)
```

Ba câu hỏi đi theo đúng các "núm vặn" của bài toán: **tín hiệu đầu vào** (RQ1), **độ trễ thực thi** (RQ2), và **kết quả tổng hợp** (RQ3).

---

## 2. Mục tiêu cụ thể (dạng SMART)

| # | Mục tiêu | Tiêu chí hoàn thành (đo được) | Hạn | Chịu trách nhiệm |
|---|---|---|---|---|
| O1 | Triển khai vLLM trên Kubernetes | Model 7–8B trả lời qua `/v1/chat/completions` có streaming; triển khai lại từ đầu bằng Argo CD trong dưới 15 phút sau khi cluster đã sẵn sàng | T4 (laptop), T9 (cloud) | Trình |
| O2 | Cấu hình GPU cho inference | `nvidia.com/gpu` hiện trên node; mỗi pod dùng đúng 1 GPU; tham số vLLM ghi trong `metadata.json` của mọi lượt chạy | T4 | Trình |
| O3 | Autoscaling theo metric | A1, A2, A3 đều scale lên và xuống đúng như tính toán trong bài kiểm tra có kiểm soát (xem [07 §8](07-chien-luoc-autoscaling.md#8-kiểm-thử-nhanh-cấu-hình-autoscaling)) | T7 | Trình |
| O4 | Giám sát serving và GPU | Có 4 dashboard; metric vLLM và DCGM được scrape mỗi 5 s; không có khoảng trống quá 15 s trong một lượt chạy | T5 | Quang |
| O5 | Thử nghiệm nhiều mẫu tải | Máy tạo tải open-loop chạy KB1–KB5 với độ lệch lịch gửi p99 dưới 50 ms | T6 | Quang |
| O6 | So sánh với cấu hình tĩnh | Ma trận 5 × 5 × 3 hoàn thành ít nhất 90%, mọi lượt qua bước kiểm tra hợp lệ | T12 | Cả nhóm |
| O7 | Đánh giá trade-off | Trả lời RQ1–RQ3 kèm khoảng tin cậy; có ít nhất 3 khuyến nghị cấu hình rút ra từ dữ liệu | T13 | Cả nhóm |

---

## 3. Chi tiết từng câu hỏi nghiên cứu

### RQ1. Nên scale theo metric nào?

**Vì sao quan trọng.** Chọn sai metric có thể làm autoscaling phản ứng quá muộn (vi phạm SLO) hoặc scale quá tay (lãng phí). Metric mặc định mà nhiều người nghĩ tới trước tiên là GPU utilization, và giả thuyết của nhóm là nó phản ánh sai tải của LLM.

| Thành phần | Nội dung |
|---|---|
| Biến độc lập | Metric scale: A1 GPU utilization · A2 running + waiting · A3 KV-cache usage (tuỳ chọn thêm A4: chỉ waiting) |
| Biến phụ thuộc | SLO attainment, độ trễ phát hiện, thời gian hồi phục SLO, GPU-giờ, số lần scale |
| Biến kiểm soát | Cơ chế KEDA/HPA, min = 1, max = 4, tham số `behavior`, chu kỳ sync HPA, model, tải |
| Thí nghiệm | Ma trận chính; trọng tâm KB2 (tăng đột ngột) và KB5 (dao động); KB1, KB3, KB4 để đối chiếu |
| Giả thuyết H1 | A2 và A3 phát hiện tải tăng sớm hơn và đạt SLO cao hơn A1 ở KB2 và KB5 |
| Quy tắc kết luận | "A2 tốt hơn A1" nếu khoảng tin cậy 95% của hiệu số SLO attainment (cặp theo phiên chạy) không chứa 0 **và** hiệu số lớn hơn hoặc bằng 5 điểm phần trăm |

**Các kết quả có thể xảy ra và cách diễn giải:**
- *A1 scale lên tối đa ngay và giữ nguyên:* nghĩa là GPU utilization bão hoà. A1 khi đó hành xử gần giống Static-4 nhưng có thêm độ trễ cold start. Đây là bằng chứng ủng hộ H1 (nhờ phân tích nguyên nhân), dù SLO của A1 có thể không tệ.
- *A1 không scale lên khi cần:* xảy ra nếu target đặt quá cao so với mức bão hoà. Đây là kết quả ngược chiều, và cũng là một phát hiện có giá trị.
- *A2 và A3 tương đương nhau:* khuyến nghị A2 vì đơn giản và dễ giải thích qua định luật Little.

### RQ2. Cold start ảnh hưởng thế nào và giảm được bao nhiêu?

| Thành phần | Nội dung |
|---|---|
| Biến độc lập | Mức tối ưu cold start: L0 (không tối ưu), L1 (model trên PVC), L2 (pre-pull image, NVMe cục bộ, compile cache) |
| Biến phụ thuộc | Thời gian từng pha trong 8 pha (Hình 12), tổng cold start; SLO attainment và thời gian hồi phục ở KB2 |
| Biến kiểm soát | Model, image, loại GPU, node; trạng thái cache hệ điều hành (được xoá hoặc ghi rõ) |
| Thí nghiệm | (a) Đo cold start riêng: 5 lần mỗi mức. (b) KB2 với A2 ở mức L0 và L2, mỗi mức 3 lần |
| Giả thuyết H2 | Cold start chiếm phần lớn thời gian phản ứng. L2 giảm tổng cold start hơn 50% so với L0 và cải thiện SLO attainment ở KB2 |
| Quy tắc kết luận | So sánh trung bình kèm khoảng tin cậy; báo cáo phần trăm thời gian phản ứng do cold start gây ra |

### RQ3. Trade-off giữa GPU-giờ và SLO

| Thành phần | Nội dung |
|---|---|
| Biến độc lập | Cấu hình: S1, S4, chiến lược autoscaling tốt nhất từ RQ1 (và các chiến lược còn lại) |
| Biến phụ thuộc | GPU-giờ (so với S4), SLO attainment, số token/GPU-giờ |
| Thí nghiệm | Toàn bộ ma trận |
| Giả thuyết H3 | Với KB2, KB4, KB5: autoscaling có SLO attainment kém S4 không quá 5 điểm phần trăm, trong khi GPU-giờ không quá 70% của S4. Với KB3: lợi ích GPU-giờ nhỏ hơn 15% |
| Sản phẩm | Biểu đồ trade-off (GPU-giờ theo SLO attainment) cho từng kịch bản, kèm bảng khuyến nghị "khi nào nên dùng cấu hình nào" |

> Các ngưỡng 5 điểm phần trăm, 70% và 15% là **ngưỡng ý nghĩa thực tiễn** được đặt trước khi chạy thí nghiệm, để không phải "chọn ngưỡng sau khi đã thấy kết quả". Nếu cần đổi, phải ghi lý do vào nhật ký quyết định.

---

## 4. Ma trận truy vết

| RQ | Thí nghiệm | Chỉ số chính | Biểu đồ (xem [10](10-phan-tich-ket-qua.md#5-đặc-tả-các-biểu-đồ)) | Chương luận văn |
|---|---|---|---|---|
| RQ1 | Ma trận (A1–A3 × KB1–KB5) | SLO attainment, độ trễ phát hiện, thời gian hồi phục | C1 chuỗi thời gian, C3 SLO attainment, C7 phân rã thời gian phản ứng | 5.3 |
| RQ2 | Đo cold start L0/L1/L2; KB2 × A2 ở L0 và L2 | Thời gian từng pha, tổng; SLO ở KB2 | C6 cold start, C1 (L0 so với L2) | 5.4 |
| RQ3 | Toàn bộ ma trận | GPU-giờ, SLO attainment, token/GPU-giờ | C4 GPU-giờ, C5 trade-off | 5.5 |
| (nền) | Hiệu chỉnh | C, B\*, đường cong TTFT/ITL | Hình 15 | 5.2 |

---

## 5. Đóng góp dự kiến

1. **Một nền tảng tái lập được**: IaC, GitOps, dashboard và experiment runner. Người khác có thể dựng lại và chạy lại toàn bộ thí nghiệm bằng vài lệnh.
2. **Đánh giá thực nghiệm có kiểm soát** cho ba loại metric scale khi phục vụ LLM, chỉ ra metric nào nên dùng và vì sao, với cơ chế giải thích (bão hoà, định luật Little, flapping).
3. **Phân rã và tối ưu cold start** của vLLM trên Kubernetes thành 8 pha, lượng hoá hiệu quả của từng kỹ thuật cache.
4. **Bộ dữ liệu và công cụ sinh tải open-loop** công khai, có thể dùng lại.
5. **Khuyến nghị cấu hình**: metric, target, `behavior`, cách tối ưu cold start, kèm điều kiện áp dụng của từng khuyến nghị.

---

## 6. Những gì KHÔNG phải mục tiêu

- Không đề xuất thuật toán autoscaling mới, và không so tốc độ với các hệ thống nghiên cứu hàng đầu.
- Không tối ưu hiệu năng của bản thân vLLM (kernel, lượng tử hoá, speculative decoding…).
- Không chứng minh kết quả đúng cho mọi model và mọi GPU. Kết luận có phạm vi áp dụng rõ ràng (xem [03 §5](03-pham-vi-gia-dinh.md#5-các-mối-đe-doạ-tính-hợp-lệ)).

---

## 7. Mức độ thành công

| Mức | Nội dung | Ý nghĩa |
|---|---|---|
| **Must** (bắt buộc) | O1–O6; RQ1 và RQ3 có câu trả lời với KB1, KB2, KB4 | Đủ điều kiện bảo vệ |
| **Should** (nên có) | Đủ KB3, KB5; RQ2 với L0 và L2; khuyến nghị cấu hình | Đồ án tốt |
| **Could** (có thì tốt) | A4 (flapping), nghiên cứu độ nhạy của `stabilizationWindowSeconds`, KB5 dùng trace thật, một hướng mở rộng nhỏ | Đồ án xuất sắc |

Nếu tiến độ chậm, hãy cắt từ dưới lên theo thứ tự này (xem thêm [12 §7](12-ke-hoach.md#7-dự-phòng-và-cắt-giảm-phạm-vi)).

---

## 8. Câu hỏi hội đồng có thể đặt ra

**Giả thuyết của nhóm có phải là "đoán trước kết quả" không?**
Giả thuyết được nêu trước và có **quy tắc kết luận** cụ thể. Nếu dữ liệu bác bỏ giả thuyết, nhóm báo cáo đúng như vậy và phân tích nguyên nhân. Một kết quả "âm tính" (ví dụ GPU utilization không tệ như dự đoán) vẫn là một đóng góp.

**Vì sao chỉ ba lần chạy cho mỗi cấu hình?**
Đây là giới hạn ngân sách GPU. Nhóm bù lại bằng cách so sánh **cặp theo phiên chạy**, báo cáo toàn bộ các giá trị riêng lẻ, và chạy thêm lần cho các ô quan trọng (KB2, KB5 với A1–A3). Xem [10 §4](10-phan-tich-ket-qua.md#4-phương-pháp-thống-kê).

**Lấy đâu ra ngưỡng 5 điểm phần trăm và 70%?**
Đó là ngưỡng ý nghĩa **thực tiễn**. Chênh lệch SLO dưới 5 điểm phần trăm thường không đủ để đổi quyết định vận hành, còn tiết kiệm trên 30% GPU là đáng kể về chi phí. Các ngưỡng này được cố định trước khi chạy thí nghiệm.
