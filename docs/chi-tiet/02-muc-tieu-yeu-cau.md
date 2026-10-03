# 2. Mục tiêu và yêu cầu hệ thống: tài liệu chuyên sâu

> Thuộc [Mục 2 của bản mô tả chính](../mo-ta-chi-tiet-do-an.md#2-mục-tiêu-và-yêu-cầu-hệ-thống) · [Danh mục tài liệu chuyên sâu](README.md)

**Tóm tắt nhanh**
- Đồ án thuộc dạng **thiết kế – triển khai – đánh giá**. Sản phẩm chính là một nền tảng chạy được và vận hành được. Phần đánh giá dùng để chứng minh nền tảng đạt yêu cầu.
- Bảy mục tiêu trong đề cương được **giữ nguyên**. Mỗi mục tiêu được cụ thể hoá thành **yêu cầu chức năng (F1–F7)** và **yêu cầu phi chức năng có chỉ tiêu đo được (N1–N8)**.
- Mỗi yêu cầu có **cách kiểm chứng**: một bài kiểm thử trên laptop, một kịch bản vận hành (VH1–VH6) hoặc một phép đo trên GPU thuê (ĐG1–ĐG3). Kết quả cuối cùng là một **bảng nghiệm thu** ghi Đạt hoặc Không đạt cho từng yêu cầu.
- Tỷ trọng công việc dự kiến: khoảng **70% xây dựng và vận hành**, **30% đánh giá**.

---

## 1. Từ bài toán đến yêu cầu

Bài toán ở [01 §6](01-dat-van-de.md#6-phát-biểu-bài-toán) là: *vận hành một dịch vụ LLM tự host trên số GPU có hạn, khi tải thay đổi theo giờ và có lúc tăng đột ngột*. Để giải bài toán đó, nền tảng phải làm được sáu việc:

```text
Bài toán vận hành LLM tự host
   ├─ Phục vụ được, đúng chuẩn API                 → F1
   ├─ Tự co giãn theo tải, đúng tín hiệu            → F2, N1, N2, N3
   ├─ Pod mới sẵn sàng nhanh                        → N5
   ├─ Thay đổi an toàn (scale-down, cập nhật)       → F3, N4
   ├─ Biết khi nào có vấn đề và phải làm gì         → F5, F6, N7
   └─ Dựng lại được, an toàn, biết chi phí          → F4, F7, N6, N8
```

---

## 2. Mục tiêu tổng quát

Xây dựng và vận hành một nền tảng phục vụ LLM mã nguồn mở trên Kubernetes có GPU. Nền tảng tự điều chỉnh số replica theo tải, được triển khai và cập nhật hoàn toàn bằng code (IaC, GitOps), có giám sát và cảnh báo theo SLO, và có quy trình xử lý sự cố. Sau đó đánh giá nền tảng bằng các kịch bản tải và kịch bản vận hành, so với cấu hình tài nguyên cố định.

---

## 3. Yêu cầu chức năng

| # | Yêu cầu | Thành phần đáp ứng | Cách kiểm chứng |
|---|---|---|---|
| **F1** | Phục vụ một model 7–8B qua API tương thích OpenAI (`/v1/chat/completions`), có streaming | vLLM, Traefik | Gọi API có streaming; chạy được ĐG1–ĐG3 |
| **F2** | Tự điều chỉnh số replica trong khoảng [1, N] theo tải (N = số GPU) | KEDA + HPA, cấu hình A2 | Bài kiểm thử T1–T6 ([07 §8](07-chien-luoc-autoscaling.md#8-kiểm-thử-nhanh-cấu-hình-autoscaling)); ĐG2 |
| **F3** | Triển khai, cập nhật và rollback hoàn toàn qua Git, không thao tác tay trên cluster | Argo CD, Kustomize | VH2: cập nhật phiên bản và rollback bằng `git revert` |
| **F4** | Dựng toàn bộ hạ tầng từ máy trắng bằng vài lệnh `make` | Script thuê VM, Ansible, Argo CD | VH5: đo thời gian dựng lại |
| **F5** | Dashboard cho serving, GPU, autoscaling, SLO và chi phí | Prometheus, Grafana | Kiểm tra trong mọi lượt đánh giá; ảnh chụp đưa vào luận văn |
| **F6** | Cảnh báo theo SLO và theo sức khoẻ nền tảng, gửi tới kênh chat; **mỗi cảnh báo có runbook** | Alertmanager, `docs/runbooks/` | VH6: cảnh báo kích hoạt đúng lúc và không báo giả |
| **F7** | Bảo vệ tối thiểu: API key, giới hạn tốc độ, NetworkPolicy, bí mật được mã hoá trong Git | Traefik middleware, NetworkPolicy, Sealed Secrets | Kiểm tra thủ công theo checklist ([08 §8](08-van-hanh.md#8-bảo-mật-tối-thiểu)) |

---

## 4. Yêu cầu phi chức năng (chỉ tiêu nghiệm thu)

Các ngưỡng dưới đây là **sơ bộ**. Chúng được chốt **một lần** sau bước đo năng lực (ĐG1), trước khi chạy ma trận đánh giá, và được ghi vào ADR-003. Không chỉnh ngưỡng sau khi đã thấy kết quả.

| # | Nhóm | Chỉ tiêu | Đo bằng |
|---|---|---|---|
| **N1** | Chất lượng phục vụ | Với cấu hình vận hành A2: **SLO attainment ≥ 95%** ở KB1 (tải thấp) và KB3 (tải cao kéo dài). Ở KB2 (tăng đột ngột) chỉ báo cáo, vì đã có N2 | ĐG2 |
| **N2** | Tốc độ phản ứng | Ở KB2: từ lúc tải tăng đến khi replica mới Ready **≤ 2 phút** (cold start đã tối ưu, mức L2); SLO hồi phục **≤ 5 phút** | ĐG2 |
| **N3** | Hiệu quả GPU | Ở KB1: A2 dùng **≤ 50% GPU-giờ** của Static-4, trong khi SLO attainment kém Static-4 **không quá 5 điểm phần trăm**. Ở KB2: báo cáo mức tiết kiệm và cái giá về SLO | ĐG2 |
| **N4** | An toàn khi thay đổi | **0 request lỗi** do scale-down (pha giảm tải của KB2) và do cập nhật phiên bản (rolling update) | ĐG2, VH1, VH2 |
| **N5** | Cold start | Thời gian cold start ở mức L2 **≤ 50%** so với L0 | ĐG3 |
| **N6** | Tự phục hồi và khôi phục | Pod hỏng được thay tự động; mất Prometheus thì autoscaling chuyển sang chế độ dự phòng (4 replica); **dựng lại toàn bộ từ VM trắng ≤ 30 phút** | VH3, VH4, VH5 |
| **N7** | Quan sát được | Cảnh báo SLO kích hoạt **≤ 5 phút** sau khi SLO bị vi phạm thật (Static-1 ở KB3); **không có cảnh báo mức page** khi A2 chạy KB1 và KB3 | VH6 |
| **N8** | Tái lập và chi phí | Mọi phiên bản được ghim; người thứ hai dựng được cluster laptop theo README trong **< 1 giờ**; tiền thuê GPU **≤ 150 USD** | VH5, sổ chi phí |

**Vì sao chọn các ngưỡng này?**
- **95% (N1):** mức SLO phổ biến cho dịch vụ nội bộ. Chỉ áp dụng cho KB1 và KB3, vì khi tải tăng gấp 6 lần trong 30 giây (KB2), mọi hệ thống có cold start đều vi phạm SLO trong vài phút.
- **2 phút và 5 phút (N2):** cold start ở mức L2 dự kiến khoảng 0,5–1,5 phút, cộng khoảng 10 giây phát hiện. Sau khi đủ replica, hàng đợi còn cần thêm vài phút để rút hết.
- **50% (N3):** ở tải thấp (0,5C), autoscaling chỉ cần 1 trong 4 GPU. Ngưỡng 50% chừa chỗ cho thời gian GPU bị giữ trong lúc khởi động và lúc chờ ổn định.
- **30 phút (N6):** đủ cho cài k3s, GPU, Argo CD và tải model khoảng 15 GB. Đây cũng là điều kiện để đợt thuê GPU không tốn tiền vào việc dựng tay.

---

## 5. Đối chiếu với bảy mục tiêu của đề cương

| # | Mục tiêu trong đề cương | Yêu cầu tương ứng | Bằng chứng nghiệm thu |
|---|---|---|---|
| 1 | Triển khai LLM mã nguồn mở bằng vLLM trên Kubernetes | F1, F3, F4 | API chạy; triển khai qua Argo CD; VH5 |
| 2 | Cấu hình GPU cho inference | F1, N5 | GPU Operator hoặc device plugin; mỗi pod 1 GPU; ĐG3 |
| 3 | Autoscaling theo metric tải/request | F2, N2, N3 | Bài kiểm thử T1–T6; ĐG2 |
| 4 | Giám sát metric serving và GPU | F5, F6, N7 | Dashboard; cảnh báo; VH6 |
| 5 | Thử nghiệm với nhiều mẫu tải | N1–N3 | Ba kịch bản KB1–KB3 |
| 6 | So sánh với cấu hình tài nguyên cố định | N1, N3 | Static-1, Static-4 so với A1, A2 trong ĐG2 |
| 7 | Đánh giá trade-off hiệu năng và tài nguyên | N3 | Biểu đồ trade-off; khuyến nghị cấu hình |

---

## 6. Ma trận truy vết

| Yêu cầu | Kiểm thử / đánh giá | Chỉ số chính | Biểu đồ hoặc bảng ([09 §12](09-kiem-thu-danh-gia.md#12-trình-bày-kết-quả-và-bảng-nghiệm-thu)) | Chương luận văn |
|---|---|---|---|---|
| F2, N1, N2, N3 | ĐG2 (ma trận autoscaling) | SLO attainment, thời gian phản ứng, thời gian hồi phục, GPU-giờ | C1, C2, C3, C4 | 5.3 |
| N5 | ĐG3 (cold start) | Thời gian từng pha và tổng | C5 | 5.4 |
| F3, N4 | VH1, VH2 | Số request lỗi, thời gian cập nhật | C6 | 5.5 |
| F6, N7 | VH6 | Thời gian tới khi có cảnh báo, số cảnh báo giả | Bảng cảnh báo | 5.5 |
| F4, N6, N8 | VH3, VH4, VH5 | Thời gian hồi phục, thời gian dựng lại | Bảng vận hành | 5.5 |
| (nền) | ĐG1 (đo năng lực) | C, B\*, đường cong TTFT/ITL | Hình 15 | 5.2 |
| Tất cả | – | – | **Bảng nghiệm thu** | 5.6 |

---

## 7. Đóng góp dự kiến

1. **Một nền tảng LLM serving hoàn chỉnh, dựng lại được bằng code** (IaC và GitOps), chạy trên cả cluster laptop lẫn GPU thuê.
2. **Thiết kế autoscaling cho LLM** dựa trên metric của vLLM, kèm số đo cho thấy vì sao không nên scale theo GPU utilization.
3. **Quy trình rút ngắn cold start** của vLLM trên Kubernetes, đo theo từng pha.
4. **Bộ công cụ vận hành cho LLM serving**: SLO, quy tắc cảnh báo, runbook, quy trình cập nhật khi đã hết GPU trống, quy trình dựng lại.
5. **Kết quả đánh giá** so với cấu hình tĩnh, cùng **khuyến nghị cấu hình** có ghi rõ điều kiện áp dụng.

---

## 8. Những gì KHÔNG phải mục tiêu

- Không đề xuất thuật toán autoscaling mới, và không so tốc độ với các hệ thống nghiên cứu hàng đầu.
- Không tối ưu hiệu năng của bản thân vLLM (kernel, lượng tử hoá, speculative decoding…).
- Không kiểm định giả thuyết thống kê. Mỗi cấu hình chạy 2–3 lượt, đủ để nghiệm thu yêu cầu và thấy rõ khác biệt lớn. Phần đánh giá không nhằm chứng minh khác biệt nhỏ.
- Không chứng minh kết quả đúng cho mọi model và mọi GPU (xem [03 §3](03-pham-vi-gia-dinh.md#3-hạn-chế-sẽ-ghi-trong-luận-văn)).

---

## 9. Mức độ thành công

| Mức | Nội dung | Ý nghĩa |
|---|---|---|
| **Must** (bắt buộc) | F1–F6; N1, N2, N4, N6; ma trận S1, S4, A1, A2 × KB1–KB3; cold start L0 và L2; VH1, VH3, VH5 | Đủ điều kiện bảo vệ |
| **Should** (nên có) | F7; N3, N5, N7; VH2 (rolling update trên GPU thật), VH4, VH6; dashboard chi phí | Đồ án tốt |
| **Could** (có thì tốt) | Chiến lược A3 (KV-cache); kịch bản dao động dùng trace thật; kết hợp trigger theo TTFT ([14 – E6](14-huong-mo-rong.md#e6-scale-theo-slo-và-kết-hợp-nhiều-trigger)); `pod-deletion-cost` | Đồ án xuất sắc |

Nếu tiến độ chậm, cắt từ dưới lên theo thứ tự này (xem thêm [11 §7](11-ke-hoach.md#7-dự-phòng-và-cắt-giảm-phạm-vi)).

---

## 10. Câu hỏi hội đồng có thể đặt ra

**Đồ án có phải chỉ là cài đặt các công cụ có sẵn?**
Không. Mỗi phần cài đặt gắn với một vấn đề kỹ thuật riêng của GPU và LLM mà cấu hình mặc định không giải được:
- HPA theo CPU hay GPU utilization không phản ánh tải.
- Cold start tính bằng phút.
- Request streaming dài bị cắt khi scale-down.
- Rolling update kiểu web bị kẹt khi đã hết GPU trống.
- Argo CD và HPA tranh nhau trường `replicas`.

Với mỗi vấn đề, đồ án nêu nguyên nhân, đưa ra cấu hình xử lý, và đo để chứng minh cấu hình đó có tác dụng.

**Sao không có câu hỏi nghiên cứu và giả thuyết?**
Đề tài là *Design and Evaluation* của một nền tảng. Cách đánh giá phù hợp là đặt **yêu cầu đo được** rồi **nghiệm thu bằng thực nghiệm**, giống cách một hệ thống được nghiệm thu trước khi đưa vào vận hành. Các so sánh (A2 với A1, autoscaling với cấu hình tĩnh) vẫn có, nhưng với vai trò **lý giải lựa chọn thiết kế**.

**Chỉ 2–3 lượt mỗi cấu hình thì có tin được không?**
Đủ cho mục đích nghiệm thu. Các khác biệt cần thấy đều lớn: ví dụ GPU-giờ của Static-4 gấp 3–4 lần A2 ở tải thấp, và A1 chạy tối đa replica gần như suốt lượt. Nhóm báo cáo **mọi lượt riêng lẻ**, và chỉ kết luận "khác nhau" khi mọi lượt đều cùng chiều và chênh lệch vượt ngưỡng thực tiễn.

**Lấy đâu ra các ngưỡng 95%, 2 phút, 50%?**
Từ mức SLO phổ biến và từ ước lượng thời gian của từng thành phần (§4). Ngưỡng được chốt một lần trước khi chạy ma trận và ghi vào ADR, nên không bị chọn theo kết quả.
