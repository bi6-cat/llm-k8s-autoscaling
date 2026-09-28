# 3. Phạm vi, giả định và giới hạn: tài liệu chuyên sâu

> Thuộc [Mục 3 của bản mô tả chính](../mo-ta-chi-tiet-do-an.md#3-phạm-vi-và-giả-định) · [Danh mục tài liệu chuyên sâu](README.md)

**Tóm tắt nhanh**
- Mỗi hạng mục trong và ngoài phạm vi đều có **lý do**, kèm phân tích **ảnh hưởng tới kết luận**.
- Có 8 giả định. Mỗi giả định đi kèm cách **kiểm chứng** và hệ quả **nếu nó sai**.
- Mục **các mối đe doạ tính hợp lệ** chia theo bốn loại (nội tại, cấu trúc, ngoại suy, kết luận). Đây là phần hội đồng thường hỏi, và cũng là nền cho mục "Hạn chế" trong luận văn.

---

## 1. Ranh giới hệ thống

| Hạng mục | Trong / Ngoài | Lý do | Ảnh hưởng tới kết luận |
|---|---|---|---|
| Serving một model trên vLLM | **Trong** | Là trọng tâm của đề tài | – |
| Autoscaling mức pod (1 replica = 1 GPU) | **Trong** | Cơ chế phổ biến nhất, chạy được trên cluster tự dựng | Kết luận áp dụng cho autoscaling mức pod |
| Giám sát, sinh tải, thí nghiệm | **Trong** | Cần để đánh giá | – |
| Đo và tối ưu cold start | **Trong** | Là nhân tố quyết định chất lượng autoscaling (RQ2) | – |
| IaC và GitOps | **Trong** | Cần để tái lập và giảm chi phí thuê GPU | – |
| Autoscaling mức node | Ngoài | Cần managed K8s có API cấp node GPU; thời gian cấp node thêm vài phút nữa | Thời gian phản ứng thực tế trên cloud công cộng có thể **dài hơn** con số đo được |
| Tensor/pipeline parallelism | Ngoài | Model 7–8B vừa với 1 GPU | Không áp dụng trực tiếp cho model hơn 30B |
| Tách prefill/decode | Ngoài | Kiến trúc khác hẳn, cần nhiều GPU và mạng nhanh | Hướng mở rộng |
| MIG / time-slicing | Ngoài | Đề cương đã loại trừ multi-tenant | Không có đơn vị scale nhỏ hơn 1 GPU |
| Định tuyến nhận biết LLM | Ngoài | Muốn giữ biến kiểm soát; mọi cấu hình đều dùng round-robin | Năng lực thực tế **có thể thấp hơn** so với khi dùng router thông minh, nhưng như nhau với mọi cấu hình |
| Nhiều model, LoRA | Ngoài | Làm phức tạp tải và trạng thái | Hướng mở rộng |
| Bảo mật, đa người dùng | Ngoài (chỉ ở mức tối thiểu) | Không phải trọng tâm | – |

---

## 2. Giả định

| # | Giả định | Vì sao hợp lý | Cách kiểm chứng | Nếu sai thì sao |
|---|---|---|---|---|
| G1 | **Chi phí ≈ GPU-giờ cấp phát cho pod vLLM** | Trên cloud trả theo mức dùng (hoặc cluster dùng chung), GPU được giải phóng sẽ được dùng vào việc khác | Không kiểm chứng được bằng thí nghiệm; nêu rõ đây là quy ước | Trên một nhóm GPU cố định dành riêng, scale-down **không giảm tiền**. Khi đó kết luận chỉ còn nói về "GPU giải phóng được" |
| G2 | Model vừa với 1 GPU, mỗi replica dùng 1 GPU | 7–8B ở BF16 cần khoảng 15 GB, GPU 24 GB | Log vLLM: KV-cache còn đủ cho `max-num-seqs` | Phải dùng lượng tử hoá hoặc model nhỏ hơn |
| G3 | Độ trễ mạng từ máy tạo tải tới cluster không đáng kể | Hai máy cùng region hoặc datacenter | Đo RTT (`ping`, TTFT với prompt 1 token) và ghi vào `metadata.json`; yêu cầu dưới 5 ms | TTFT bị cộng thêm một hằng số; so sánh giữa các cấu hình vẫn công bằng nhưng số tuyệt đối lệch |
| G4 | Phiên bản phần mềm cố định suốt đợt thí nghiệm | Ghim image digest và phiên bản Helm chart | `metadata.json` ghi digest; runner kiểm tra trước mỗi lượt | Kết quả giữa các phiên không so được với nhau |
| G5 | Năng lực C ổn định trong suốt đợt thí nghiệm | Cùng loại VM, cùng cấu hình | **Kiểm tra nhanh C** ở đầu mỗi phiên cloud: 2 mức tải, 3 phút mỗi mức | Máy "yếu" hơn thì phải hiệu chỉnh lại; nếu lệch hơn 10% thì không gộp dữ liệu |
| G6 | Tải tổng hợp (Poisson, output cố định) đủ đại diện | Là chuẩn mực trong các benchmark serving; dễ kiểm soát | Chạy thêm KB5 bằng trace thật nếu còn thời gian | Hành vi với tải thật (burst lồng nhau, output dài ngắn khác nhau) có thể khác; ghi thành hạn chế |
| G7 | Round-robin không làm lệch so sánh giữa các cấu hình | Mọi cấu hình cùng chịu một kiểu cân bằng tải | Theo dõi độ lệch `num_requests_running` giữa các pod | Có thể làm autoscaling trông kém hơn thực tế ở mức tải cao |
| G8 | Một node với 4 GPU (phương án A) đủ đại diện | Autoscaling mức pod không phụ thuộc số node | Đo cold start ở chế độ "node lạnh" bằng cách xoá image và cache | Chưa đo được độ trễ mạng giữa các node; nếu có ngân sách thì chạy phương án B để đối chiếu |

---

## 3. Giới hạn (limitations) sẽ ghi trong luận văn

1. **Chỉ một model, một loại GPU.** Kết luận định tính (metric nào tốt hơn, vì sao) có khả năng khái quát. Kết luận định lượng (bao nhiêu giây, bao nhiêu phần trăm) chỉ đúng cho cấu hình đã đo.
2. **Tối đa 4 replica.** Chưa kiểm tra được hành vi ở quy mô hàng chục replica, nơi scheduling và cân bằng tải phức tạp hơn.
3. **Tải tổng hợp** với độ dài output cố định. Tải thật đa dạng hơn.
4. **Chỉ 3 lần chạy mỗi ô** trong ma trận (do ngân sách), nên khoảng tin cậy rộng. Nhóm bù bằng so sánh cặp và chạy thêm lần ở các ô trọng tâm.
5. **Không có autoscaling mức node.** Trên cloud công cộng, thời gian phản ứng thật cộng thêm thời gian cấp node GPU.
6. **Cân bằng tải round-robin.**

---

## 4. Tiêu chí vào / ra phạm vi trong lúc làm

Khi xuất hiện một ý tưởng mới giữa chừng (ví dụ "thêm thử KServe"), cả nhóm tự hỏi ba câu sau trước khi đưa vào phạm vi:

1. Nó có giúp trả lời RQ1–RQ3 **trực tiếp** không?
2. Nó có làm thay đổi **biến kiểm soát** của các thí nghiệm đã chạy không?
3. Nó có vừa với **thời gian và ngân sách** còn lại mà không đẩy mốc tiếp theo lùi lại không?

Chỉ khi cả ba câu đều là "có, không, có" thì mới đưa vào. Nếu không, ghi vào [15 – Hướng mở rộng](15-huong-mo-rong.md).

---

## 5. Các mối đe doạ tính hợp lệ

### 5.1. Tính hợp lệ nội tại: kết quả có thật do metric/cấu hình gây ra không?

| Mối đe doạ | Cơ chế gây sai | Biện pháp |
|---|---|---|
| Máy dùng chung với khách thuê khác (noisy neighbor) | Hiệu năng VM dao động theo giờ | So sánh cặp **trong cùng phiên** (mỗi phiên chứa đủ mọi cấu hình); xáo trộn thứ tự lượt chạy |
| Hiệu ứng thứ tự | Lượt trước để lại trạng thái (cache, hàng đợi, pod đang khởi động) | Quy trình reset: về 1 replica, hàng đợi trống, chờ thêm 60 s |
| Page cache của hệ điều hành | Lần nạp model sau nhanh hơn vì weights đã nằm trong RAM | Ghi rõ trạng thái cache; với thí nghiệm cold start thì xoá cache (`drop_caches`) |
| Máy tạo tải là nút thắt | Gửi chậm hơn lịch, làm tải thật thấp hơn tải danh nghĩa | Theo dõi độ lệch lịch và CPU của máy tạo tải; loại những lượt không đạt |
| Đồng hồ các máy lệch nhau | Ghép dữ liệu client với server sai thời điểm | Đồng bộ bằng chrony; yêu cầu lệch dưới 50 ms |
| Giảm xung vì nhiệt (laptop) | Hiệu năng tụt giữa chừng | Không dùng số liệu laptop để kết luận |

### 5.2. Tính hợp lệ cấu trúc: chỉ số có đo đúng điều cần đo không?

| Mối đe doạ | Biện pháp |
|---|---|
| SLO attainment có thực sự phản ánh trải nghiệm người dùng? | Dùng hai tiêu chí TTFT và TPOT (phần người dùng cảm nhận được); báo cáo thêm phân phối đầy đủ (CDF) |
| GPU-giờ có phải là chi phí? | Nêu rõ giả định G1; báo cáo thêm "số request đạt SLO trên mỗi GPU-giờ" |
| TTFT phía client lẫn cả độ trễ mạng | Đo RTT; đối chiếu với histogram phía server |
| ITL đo từ các "chunk" SSE (một chunk có thể chứa nhiều token) | Dùng TPOT tính theo số token trong `usage` làm chỉ số chính (xem [09](09-chi-so-danh-gia.md#32-tpot-và-itl)) |

### 5.3. Tính hợp lệ ngoại suy: kết quả có khái quát được không?

- Khác model hoặc GPU thì C và cold start đổi, nhưng **cơ chế** (GPU utilization bão hoà, định luật Little, phân rã cold start) vẫn đúng. Luận văn phải tách rõ **kết luận định tính** và **kết luận định lượng**.
- Có thể kiểm tra sơ bộ tính khái quát bằng chính tầng laptop: model 1,5B trên RTX 4060. Nếu xu hướng giữa A1, A2, A3 giống nhau trên cả hai tầng, lập luận khái quát mạnh hơn. Chỉ so xu hướng, không so số tuyệt đối.

### 5.4. Tính hợp lệ của kết luận thống kê

- n = 3 cho khoảng tin cậy rộng, nên chỉ phát hiện được các khác biệt lớn. Nhóm sẽ báo cáo **độ lớn hiệu ứng kèm khoảng tin cậy**, không chỉ nói "có ý nghĩa / không có ý nghĩa".
- Tránh kiểm định nhiều lần rồi chỉ chọn kết quả đẹp: các so sánh chính được **đăng ký trước** (xem [10 §3](10-phan-tich-ket-qua.md#3-kế-hoạch-phân-tích-đăng-ký-trước)).

---

## 6. Câu hỏi hội đồng có thể đặt ra

**Chỉ 4 GPU có đủ để nói về autoscaling không?**
Đủ để quan sát **cơ chế**: phát hiện tải, cold start, flapping, trade-off. Hạn chế về quy mô được ghi rõ. Các hiện tượng chính (metric bão hoà, cold start) không phụ thuộc số replica.

**Nếu cluster là của riêng mình thì scale-down đâu có tiết kiệm được gì?**
Đúng vậy, và đó là lý do có giả định G1. Trên cloud trả theo mức dùng, hoặc cluster dùng chung, GPU được giải phóng tương đương với tiền hoặc năng lực cho việc khác. Luận văn trình bày cả hai cách hiểu.

**Tải tổng hợp có quá đơn giản không?**
Tải tổng hợp giúp **kiểm soát biến**, và đây là yêu cầu của một thí nghiệm so sánh. KB5 được thiết kế gần thực tế hơn và có thể thay bằng trace thật. Giới hạn này được thừa nhận ở mục 3.
