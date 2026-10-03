# 3. Phạm vi, giả định và hạn chế: tài liệu chuyên sâu

> Thuộc [Mục 3 của bản mô tả chính](../mo-ta-chi-tiet-do-an.md#3-phạm-vi-và-giả-định) · [Danh mục tài liệu chuyên sâu](README.md)

**Tóm tắt nhanh**
- Mỗi hạng mục trong và ngoài phạm vi đều có **lý do**, kèm **ảnh hưởng tới kết quả**.
- Có 7 giả định. Mỗi giả định đi kèm cách **kiểm tra** và hệ quả **nếu nó sai**.
- Phần đánh giá chỉ cần một số **điều kiện so sánh công bằng** (cùng máy, cùng tải, cùng phiên bản, trạng thái đầu giống nhau). Đồ án không dựng một thiết kế thí nghiệm thống kê đầy đủ, nên các hạn chế được ghi rõ ở §3.

---

## 1. Ranh giới hệ thống

| Hạng mục | Trong / Ngoài | Lý do | Ảnh hưởng tới kết quả |
|---|---|---|---|
| Serving một model trên vLLM | **Trong** | Là trọng tâm của đề tài | – |
| Autoscaling mức pod (1 replica = 1 GPU) | **Trong** | Cơ chế phổ biến nhất, chạy được trên cluster tự dựng | Kết luận áp dụng cho autoscaling mức pod |
| Rút ngắn cold start | **Trong** | Quyết định tốc độ phản ứng của autoscaling | – |
| IaC, GitOps, CI | **Trong** | Để dựng lại được và giảm chi phí thuê GPU | – |
| Giám sát, SLO, cảnh báo, runbook | **Trong** | Là phần "vận hành" của nền tảng | – |
| Cập nhật phiên bản, xử lý sự cố, dựng lại | **Trong** | Là phần "vận hành" của nền tảng | – |
| Bảo mật tối thiểu (API key, giới hạn tốc độ, NetworkPolicy, bí mật) | **Trong**, ở mức tối thiểu | Không thể vận hành một API mà không có | Không đánh giá sâu về bảo mật |
| Sinh tải và đánh giá | **Trong** | Để nghiệm thu yêu cầu | – |
| Autoscaling mức node | Ngoài | Cần managed K8s có API cấp node GPU; thời gian cấp node thêm vài phút nữa | Thời gian phản ứng thực tế trên cloud công cộng có thể **dài hơn** con số đo được |
| Tensor/pipeline parallelism | Ngoài | Model 7–8B vừa với 1 GPU | Không áp dụng trực tiếp cho model hơn 30B |
| Tách prefill/decode | Ngoài | Kiến trúc khác hẳn, cần nhiều GPU và mạng nhanh | Hướng mở rộng |
| MIG / time-slicing | Ngoài | Đề cương đã loại trừ multi-tenant | Không có đơn vị scale nhỏ hơn 1 GPU |
| Định tuyến nhận biết LLM | Ngoài | Giữ kiến trúc đơn giản; mọi cấu hình đều dùng round-robin | Năng lực thực tế **có thể thấp hơn** so với khi dùng router thông minh |
| Nhiều model, LoRA | Ngoài | Làm phức tạp tải và trạng thái | Hướng mở rộng |
| Log tập trung (Loki), tracing | Ngoài | Metric và cảnh báo đủ cho các kịch bản của đồ án | Chẩn đoán dựa vào `kubectl logs` |
| Đa người dùng, phân quyền chi tiết, kiểm toán | Ngoài | Không phải trọng tâm | – |

---

## 2. Giả định

| # | Giả định | Vì sao hợp lý | Cách kiểm tra | Nếu sai thì sao |
|---|---|---|---|---|
| G1 | **Chi phí ≈ GPU-giờ cấp phát cho pod vLLM** | Trên cloud trả theo mức dùng (hoặc cluster dùng chung), GPU được giải phóng sẽ được dùng vào việc khác | Không kiểm chứng được bằng thực nghiệm; nêu rõ đây là quy ước | Trên một nhóm GPU cố định dành riêng, scale-down **không giảm tiền**. Khi đó kết quả chỉ còn nói về "GPU giải phóng được" |
| G2 | Model vừa với 1 GPU, mỗi replica dùng 1 GPU | 7–8B ở BF16 cần khoảng 15 GB, GPU 24 GB | Log vLLM: KV-cache còn đủ cho `max-num-seqs` | Phải dùng lượng tử hoá hoặc model nhỏ hơn |
| G3 | Máy tạo tải không làm nhiễu hệ thống được đo | Chạy cùng VM nhưng trên **lõi CPU riêng** (CPU manager static); không đi qua mạng ngoài | CPU của pod máy tạo tải; độ lệch lịch gửi p99 < 50 ms | Phải tách lõi hoặc đổi sang máy riêng |
| G4 | Phiên bản phần mềm cố định suốt đợt đánh giá | Ghim image digest và phiên bản Helm chart | `metadata.json` ghi digest | Kết quả giữa các lượt không so được với nhau |
| G5 | Năng lực C ổn định trong suốt đợt đánh giá | **Cùng một máy** trong cả đợt; máy đã qua burn-in | Chạy lại nhanh một mức tải giữa đợt (3 phút) | Nếu lệch hơn 10% thì đo năng lực lại và ghi vào nhật ký |
| G6 | Tải tổng hợp (Poisson, output cố định) đủ đại diện | Là cách làm chuẩn trong các benchmark serving; dễ kiểm soát | – | Tải thật đa dạng hơn; ghi thành hạn chế |
| G7 | Một node có 4 GPU đủ đại diện cho cluster nhiều node | Autoscaling mức pod không phụ thuộc số node | Kịch bản drain node chạy trên cluster laptop nhiều node | Chưa đo được độ trễ mạng giữa các node trên GPU thật |

---

## 3. Hạn chế sẽ ghi trong luận văn

1. **Chỉ một model, một loại GPU (RTX 4090, dòng consumer).** Kết luận về cơ chế (metric nào phản ánh tải, vì sao cold start dài) có khả năng khái quát. Con số cụ thể (bao nhiêu giây, bao nhiêu phần trăm) chỉ đúng cho cấu hình đã đo.
2. **Tối đa 4 replica.** Chưa kiểm tra được hành vi ở quy mô hàng chục replica, nơi scheduling và cân bằng tải phức tạp hơn.
3. **Tải tổng hợp** với độ dài output cố định, và chỉ ba kịch bản tải. Tải thật đa dạng hơn.
4. **Mỗi cấu hình chỉ chạy 2–3 lượt.** Đủ để nghiệm thu và thấy các khác biệt lớn, không đủ để khẳng định các khác biệt nhỏ. Đồ án không tính khoảng tin cậy thống kê.
5. **Không có autoscaling mức node.** Trên cloud công cộng, thời gian phản ứng thật cộng thêm thời gian cấp node GPU.
6. **Cân bằng tải round-robin.**
7. **Các kịch bản vận hành được dựng có chủ đích** (xoá pod, tắt Prometheus…). Chúng chưa bao quát mọi sự cố thật, ví dụ GPU hỏng dần hay mạng chập chờn.

---

## 4. Tiêu chí vào / ra phạm vi trong lúc làm

Khi xuất hiện một ý tưởng mới giữa chừng (ví dụ "thêm thử KServe" hay "thêm Loki"), cả nhóm tự hỏi ba câu sau trước khi đưa vào phạm vi:

1. Nó có giúp đáp ứng **một yêu cầu F hoặc N** ([02](02-muc-tieu-yeu-cau.md)) mà hiện chưa đáp ứng được không?
2. Nó có làm thay đổi các cấu hình **đã đo** trong đợt đánh giá không?
3. Nó có vừa với **thời gian và ngân sách** còn lại mà không đẩy mốc tiếp theo lùi lại không?

Chỉ khi cả ba câu đều là "có, không, có" thì mới đưa vào. Nếu không, ghi vào [14 – Hướng mở rộng](14-huong-mo-rong.md).

---

## 5. Điều kiện để so sánh công bằng

Phần đánh giá so sánh các cấu hình với nhau, nên cần một số điều kiện tối thiểu. Đây là các biện pháp kỹ thuật đơn giản, không phải một thiết kế thí nghiệm thống kê.

| Điều kiện | Vì sao cần | Cách làm |
|---|---|---|
| **Cùng máy** | Máy trên marketplace có thể khác nhau về hiệu năng | Toàn bộ đợt đánh giá chạy trên một máy, đã qua burn-in |
| **Cùng tải** | Để khác biệt đến từ cấu hình chứ không phải từ tải | Lịch gửi request sinh từ seed cố định; mọi cấu hình nhận đúng cùng một chuỗi request |
| **Cùng phiên bản và tham số** | Tham số vLLM đổi thì năng lực đổi | Ghim digest; chỉ đổi cấu hình autoscaling giữa các lượt |
| **Trạng thái đầu giống nhau** | Lượt trước có thể để lại pod đang khởi động hoặc hàng đợi | Reset về 1 replica, hàng đợi trống, chờ thêm 60 s |
| **Thứ tự xáo trộn** | Tránh việc một cấu hình luôn chạy vào giờ máy "mệt" | Xáo thứ tự các lượt bằng một seed ghi lại |
| **Không dùng số liệu laptop để kết luận** | GPU laptop giảm xung vì nhiệt, VRAM nhỏ | Laptop chỉ dùng cho phát triển, kịch bản vận hành và demo |
| **Page cache khi đo cold start** | Lần nạp model thứ hai đọc từ RAM nên nhanh bất thường | Xoá cache (`drop_caches`) trước mỗi lần đo |

Lượt chạy nào vi phạm các điều kiện trên thì được đánh dấu không hợp lệ và chạy lại ([09 §13](09-kiem-thu-danh-gia.md#13-điều-kiện-hợp-lệ-của-một-lượt)).

---

## 6. Câu hỏi hội đồng có thể đặt ra

**Chỉ 4 GPU có đủ để nói về autoscaling không?**
Đủ để quan sát và xử lý các **cơ chế**: phát hiện tải, cold start, scale-down, cập nhật khi hết GPU. Hạn chế về quy mô được ghi rõ.

**Nếu cluster là của riêng mình thì scale-down đâu có tiết kiệm được gì?**
Đúng vậy, và đó là lý do có giả định G1. Trên cloud trả theo mức dùng, hoặc cluster dùng chung cho nhiều đội, GPU được giải phóng tương đương với tiền hoặc năng lực cho việc khác. Luận văn trình bày cả hai cách hiểu.

**Sao không làm thí nghiệm có khoảng tin cậy cho chặt chẽ?**
Mục tiêu của phần đánh giá là **nghiệm thu yêu cầu**, và các khác biệt cần thấy đều lớn. Một thiết kế thống kê đầy đủ cần nhiều lượt chạy hơn nhiều lần, tức nhiều tiền thuê GPU hơn, mà không thay đổi kết luận vận hành. Nhóm báo cáo mọi lượt riêng lẻ để người đọc tự thấy độ dao động.
