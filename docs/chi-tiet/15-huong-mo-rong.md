# 15. Hướng mở rộng: tài liệu chuyên sâu

> Thuộc [Mục 15 của bản mô tả chính](../mo-ta-chi-tiet-do-an.md#15-hướng-mở-rộng) · [Danh mục tài liệu chuyên sâu](README.md)

**Tóm tắt nhanh**
- 11 hướng mở rộng. Mỗi hướng có **động cơ, cách làm, chỉ số cần đo, công sức ước tính và điều kiện cần**.
- Bảng xếp hạng theo **giá trị so với công sức** giúp chọn nhanh nếu còn dư 1–2 tuần.
- Cuối tài liệu có gợi ý cách viết mục "Hướng phát triển" trong luận văn.

---

## 1. Xếp hạng

| Mã | Hướng | Giá trị | Công sức | Điều kiện cần | Gợi ý |
|---|---|---|---|---|---|
| E1 | Định tuyến nhận biết LLM | Cao | Trung bình (1–2 tuần) | Envoy Gateway hoặc llm-d | **Nếu dư 2 tuần** |
| E5 | Autoscaling dự báo | Cao | Trung bình | Dữ liệu KB5 hoặc trace | **Nếu dư 2 tuần** |
| E6 | Scale theo SLO, nhiều trigger | Trung bình | **Thấp** (vài ngày) | Hạ tầng hiện có | **Nếu dư 1 tuần** |
| E11 | Pod deletion cost khi scale-down | Trung bình | **Thấp** | Hạ tầng hiện có | **Nếu dư 1 tuần** |
| E3 | Scale-to-zero và khởi động nhanh | Cao | Cao | Tối ưu cold start sâu | Luận văn tiếp theo |
| E4 | So sánh với KServe / Knative KPA | Trung bình | Trung bình | Cài KServe | – |
| E2 | Autoscaling mức node | Trung bình | Trung bình–cao | Managed K8s (GKE/EKS) | – |
| E7 | Chia sẻ GPU (MIG, time-slicing) | Trung bình | Trung bình | GPU hỗ trợ MIG (A100/H100) | – |
| E8 | Nhiều model, LoRA | Trung bình | Cao | – | – |
| E9 | Tách prefill/decode | Cao | Rất cao | Nhiều GPU, mạng nhanh | Nghiên cứu sâu |
| E10 | Tối ưu chi phí bằng spot | Trung bình | Trung bình | Cloud có spot GPU | – |

---

## 2. Chi tiết từng hướng

### E1. Định tuyến có nhận biết LLM
- **Động cơ:** round-robin làm lệch tải giữa các pod (xem [05 §3.3](05-kien-truc-he-thong.md#33-service-và-cân-bằng-tải)), khiến năng lực thực tế thấp hơn N × C.
- **Cách làm:** (a) Envoy Gateway dùng thuật toán `LEAST_REQUEST`; (b) Gateway API Inference Extension hoặc llm-d, định tuyến theo độ dài hàng đợi và KV-cache của từng pod.
- **Đo:** độ lệch `running` giữa các pod; SLO attainment và GPU-giờ ở KB3, KB5; C "hiệu dụng" khi có N replica.
- **Giả thuyết:** định tuyến thông minh làm tăng năng lực hiệu dụng, cho phép dùng target cao hơn, nên tiết kiệm thêm GPU-giờ.

### E2. Autoscaling mức node
- **Động cơ:** trên cloud công cộng, thêm replica có thể cần thêm node GPU, và việc này cộng thêm vài phút.
- **Cách làm:** GKE hoặc EKS có node pool GPU, dùng Cluster Autoscaler hoặc Karpenter; đo thời gian từ lúc pod Pending tới khi node Ready và có GPU.
- **Đo:** phân rã cold start thành "cấp node" cộng 8 pha hiện tại; chi phí node chạy không (idle).

### E3. Scale-to-zero và khởi động nhanh
- **Động cơ:** các model ít được dùng không nên giữ GPU suốt ngày.
- **Cách làm:** KEDA `minReplicaCount: 0` và `activationThreshold`; kết hợp các kỹ thuật khởi động nhanh: sleep mode của vLLM (dời weights sang CPU rồi "đánh thức"), stream weights (`--load-format runai_streamer`), snapshot hoặc checkpoint nhanh (ý tưởng từ ServerlessLLM [4]).
- **Đo:** TTFT của request đầu tiên sau khoảng nghỉ; GPU-giờ tiết kiệm được; độ trễ kích hoạt từ 0 lên 1.

### E4. So sánh với KServe / Knative KPA
- **Cách làm:** triển khai cùng model bằng KServe ở chế độ serverless (KPA theo request đồng thời, có panic mode); chạy KB2 và KB5.
- **Đo:** so với A2 (cùng loại tín hiệu); ảnh hưởng của activator và panic mode.

### E5. Autoscaling dự báo
- **Động cơ:** cold start dài thì phản ứng sau khi tải đã tăng luôn là muộn. **Dự báo** tải để scale trước.
- **Cách làm:** mô hình đơn giản (Holt-Winters, hồi quy theo giờ trong ngày) dự báo λ(t + D), với D là thời gian cold start. Đưa kết quả thành external metric (qua KEDA metrics-api scaler hoặc một exporter riêng); lấy giá trị lớn hơn giữa dự báo và A2.
- **Đo:** vi phạm SLO lúc tải tăng ở KB5 hoặc trace thật; GPU-giờ thêm do dự báo sai.

### E6. Scale theo SLO và kết hợp nhiều trigger
- **Cách làm:** ScaledObject có hai trigger: A2 (chính) và TTFT p95 (chốt chặn, ví dụ threshold 1,5 s). HPA lấy desired **lớn nhất** trong các trigger.
- **Đo:** có giảm vi phạm SLO ở KB2 không; có gây scale thừa do tín hiệu TTFT đi trễ không.
- **Ưu điểm:** hạ tầng hiện có dùng được luôn; làm trong vài ngày.

### E7. Chia sẻ GPU (MIG, time-slicing)
- **Động cơ:** đơn vị scale nhỏ hơn 1 GPU cho model nhỏ.
- **Cách làm:** MIG trên A100/H100 (ví dụ `1g.10gb`), mỗi replica một lát MIG; hoặc time-slicing (không cô lập).
- **Đo:** độ mịn khi scale so với hiệu năng mỗi lát; cô lập hiệu năng giữa các replica.

### E8. Nhiều model và LoRA
- **Cách làm:** vLLM phục vụ nhiều LoRA adapter trên một base model; hoặc nhiều Deployment, mỗi model một Deployment, dùng chung nhóm GPU.
- **Đo:** autoscaling khi các model tranh nhau GPU; chính sách ưu tiên.

### E9. Tách prefill và decode
- **Động cơ:** prefill (nặng sức tính) và decode (nặng băng thông) có nhu cầu khác nhau, nên có thể scale riêng hai nhóm.
- **Cách làm:** llm-d hoặc NVIDIA Dynamo; hai nhóm pod và KV-cache được chuyển giữa chúng.
- **Đo:** SLO và GPU-giờ so với serving gộp; chi phí truyền KV-cache.

### E10. Tối ưu chi phí bằng spot
- **Cách làm:** giữ replica nền trên máy on-demand, còn replica tăng thêm chạy trên spot; xử lý khi spot bị thu hồi (drain nhanh).
- **Đo:** chi phí trên 1 triệu token; vi phạm SLO khi bị thu hồi.

### E11. Pod deletion cost khi scale-down
- **Động cơ:** ReplicaSet có thể xoá đúng pod đang **bận nhất**, làm nhiều request phải drain lâu.
- **Cách làm:** một controller nhỏ định kỳ gắn annotation `controller.kubernetes.io/pod-deletion-cost` theo `num_requests_running` của từng pod, để pod rảnh nhất bị xoá trước.
- **Đo:** thời gian drain, lỗi trong cửa sổ scale-down ở KB4.

---

## 3. Viết mục "Hướng phát triển" trong luận văn

Mỗi hướng nên viết 3–5 câu theo thứ tự: **hạn chế hiện tại → hướng đề xuất → kỳ vọng → cách đánh giá**. Ví dụ:

> *Đồ án dùng round-robin nên các pod có thể lệch tải (quan sát được độ lệch `running` tới X ở KB3). Hướng tiếp theo là dùng định tuyến dựa trên độ dài hàng đợi (Gateway API Inference Extension). Kỳ vọng năng lực hiệu dụng tăng, cho phép target cao hơn và tiết kiệm thêm GPU-giờ. Có thể đánh giá bằng chính ma trận thí nghiệm và các chỉ số của đồ án.*

**Ưu tiên nêu:** E1, E5, E3 (liên hệ trực tiếp với kết quả RQ1 và RQ2), rồi E2, E9 (mở rộng quy mô).

---

## 4. Câu hỏi hội đồng có thể đặt ra

**Nếu có thêm thời gian, nhóm sẽ làm gì trước?**
E6 và E11: công sức thấp, dùng lại được toàn bộ hạ tầng, và trả lời trực tiếp những điểm yếu phát hiện ở RQ1 (vi phạm SLO lúc tăng tải) và ở KB4 (scale-down). Sau đó là E1 hoặc E5.
