# 1. Đặt vấn đề: tài liệu chuyên sâu

> Thuộc [Mục 1 của bản mô tả chính](../mo-ta-chi-tiet-do-an.md#1-đặt-vấn-đề) · [Danh mục tài liệu chuyên sâu](README.md)

**Tóm tắt nhanh**
- Chi phí chính của một dịch vụ LLM là **GPU**. Nhu cầu GPU phụ thuộc vào số request đang được xử lý cùng lúc, và con số này dao động mạnh theo thời gian.
- Lý thuyết hàng đợi cho thấy độ trễ **tăng vọt khi tải tiến gần năng lực tối đa**. Vì vậy hệ thống luôn phải chừa dư năng lực, và nếu cấp phát tĩnh theo mức tải đỉnh thì sẽ lãng phí GPU phần lớn thời gian.
- Autoscaling giải được bài toán lãng phí. Nhưng với LLM, autoscaling gặp ba trở ngại riêng: **cold start kéo dài hàng phút**, **metric quen thuộc (GPU utilization, VRAM) không phản ánh tải**, và **đơn vị tài nguyên rời rạc, đắt**.
- Đồ án phát biểu bài toán dưới dạng: tối thiểu hoá GPU-giờ, với ràng buộc tỷ lệ request đạt SLO không thấp hơn một ngưỡng cho trước.

---

## 1. LLM serving là gì và vì sao tốn GPU

### 1.1. Một request đi qua những bước nào

Khi người dùng gửi một câu hỏi tới dịch vụ LLM, hệ thống làm bốn việc:

1. **Tokenize**: chuyển văn bản thành chuỗi token. Mỗi token trung bình tương ứng khoảng 3–4 ký tự tiếng Anh; tiếng Việt thường tốn nhiều token hơn cho cùng lượng nội dung.
2. **Prefill**: đưa toàn bộ prompt qua model **một lần**. Kết quả là token đầu tiên của câu trả lời, cùng với **KV-cache** (bộ nhớ đệm lưu trạng thái attention của các token đã xử lý).
3. **Decode**: sinh lần lượt **từng token** của câu trả lời. Mỗi bước decode đọc lại toàn bộ trọng số (weights) của model và KV-cache.
4. **Detokenize và stream**: chuyển token thành văn bản rồi gửi dần về cho người dùng.

Chi tiết từng pha nằm trong [04 – Kiến thức nền](04-kien-thuc-nen.md#2-llm-inference-cơ-bản).

### 1.2. VRAM bị chiếm vào đâu

Lấy ví dụ một GPU 24 GB chạy Qwen2.5-7B-Instruct ở định dạng BF16, với `--gpu-memory-utilization 0.9`:

| Thành phần | Dung lượng | Ghi chú |
|---|---|---|
| Weights | ~15,2 GB | 7,6 tỷ tham số × 2 byte |
| Bộ nhớ trung gian (activation), CUDA graph | ~1–2 GB | vLLM đo lúc khởi động |
| **KV-cache** | **~4–5 GB** | Phần còn lại trong ngân sách 0,9 × 24 GB |
| Phần chừa lại | ~2,4 GB | 10% VRAM không cấp phát |

Mỗi token trong KV-cache của Qwen2.5-7B chiếm khoảng 56 KiB (cách tính ở [04 §2.3](04-kien-thuc-nen.md#23-kv-cache)). Vậy 4,5 GB KV-cache chứa được khoảng **80 nghìn token**. Nếu mỗi request dài trung bình 1.000 token (prompt cộng câu trả lời), một GPU chỉ giữ được khoảng **80 request cùng lúc**. Request thứ 81 phải chờ trong hàng đợi.

### 1.3. Vì sao "số request đồng thời" là đơn vị tiền tệ của LLM serving

Pha decode bị **giới hạn bởi băng thông bộ nhớ**: mỗi bước phải đọc toàn bộ 15 GB weights, bất kể batch có 1 request hay 32 request.

Ví dụ trên GPU A10 (băng thông khoảng 600 GB/s), một bước decode mất tối thiểu khoảng 15,2 GB ÷ 600 GB/s ≈ **25 ms**:
- Batch chỉ có 1 request: khoảng 40 token/s cho cả GPU.
- Batch 32 request: gần 32 × 35 ≈ **1.100 token/s**. Thời gian mỗi bước tăng không đáng kể vì vẫn chỉ đọc weights một lần.

Như vậy **gộp nhiều request vào cùng một batch** là cách duy nhất để khai thác GPU hiệu quả. Khi số request vượt quá khả năng chứa của batch và KV-cache, request mới phải chờ. Đây là lý do đồ án chọn **số request đồng thời** làm tín hiệu scale chính (chiến lược A2, xem [07](07-chien-luoc-autoscaling.md)).

---

## 2. Đặc điểm của tải thực tế

| Đặc điểm | Mô tả | Hệ quả cho hệ thống |
|---|---|---|
| **Theo chu kỳ** | Tải cao vào giờ làm việc, thấp vào ban đêm và cuối tuần | Cấp phát theo đỉnh thì lãng phí vào giờ thấp điểm |
| **Có đợt tăng đột biến (burst)** | Tải tăng nhanh trong vài phút, ví dụ khi có sự kiện hoặc một chiến dịch | Hệ thống phải phản ứng nhanh hơn thời gian khởi động một replica |
| **Request không đồng nhất** | Prompt dài từ vài chục đến hàng nghìn token; câu trả lời cũng vậy | Thời gian phục vụ mỗi request chênh nhau hàng chục lần; "số request/giây" không phản ánh đúng lượng việc |
| **Phân phối đuôi dài** | Một ít request rất dài chiếm phần lớn tài nguyên | Độ trễ p99 nhạy cảm hơn nhiều so với trung bình |

Các bộ trace công khai như BurstGPT [5] và Azure LLM Inference Trace [3], [18] cho thấy những đặc điểm trên có thật. Kịch bản KB5 có thể dùng một trong hai trace này, sau khi nén thời gian (xem [08 §6.4](08-thiet-ke-thi-nghiem.md#64-phát-lại-trace-thật-tuỳ-chọn)).

---

## 3. Góc nhìn hàng đợi: vì sao không thể cho GPU chạy sát 100%

![Hình 10 – Độ trễ theo mức tải](../images/10-do-tre-theo-muc-tai.svg)

*Hình 10. Độ trễ theo tốc độ request trên một replica. Đồ thị được vẽ từ mô hình hàng đợi đơn giản để minh hoạ; đường cong thật sẽ được đo ở bước hiệu chỉnh (Hình 15).*

Gọi μ là thông lượng tối đa của một replica (số request/giây nó xử lý được) và λ là tốc độ request đến. **Mức sử dụng** là ρ = λ/μ. Trong mô hình hàng đợi M/M/1 cổ điển, thời gian trung bình trong hệ thống là:

$$
W = \frac{1}{\mu - \lambda} = \frac{1/\mu}{1-\rho}
$$

Công thức này nói lên ba điều:
- Khi ρ nhỏ, độ trễ gần bằng thời gian phục vụ thuần.
- Khi ρ tiến tới 1, độ trễ **tăng không giới hạn**. Chỉ cần tăng ρ từ 0,8 lên 0,9 là thời gian chờ đã tăng gấp đôi.
- Khi λ > μ, hàng đợi **tăng mãi**. Hệ thống không bao giờ tự hồi phục được cho tới khi tải giảm.

LLM serving phức tạp hơn M/M/1 ở hai điểm. Thứ nhất, thông lượng μ **tăng theo kích thước batch** cho tới khi KV-cache đầy. Thứ hai, thời gian phục vụ phụ thuộc độ dài request. Tuy vậy, hình dạng "đầu gối" của đường cong vẫn giữ nguyên, và dữ liệu hiệu chỉnh sẽ cho thấy điều đó.

**Hệ quả thực tế:** năng lực dùng được **C** (tốc độ lớn nhất còn đạt SLO) luôn nhỏ hơn μ. Hệ thống phải giữ ρ ở mức 0,7–0,85, tức là **luôn có dư năng lực**. Câu hỏi đặt ra là dư bao nhiêu và vào lúc nào, và autoscaling chính là cách điều chỉnh lượng dư này theo thời gian.

---

## 4. Ba cách cấp phát: một ví dụ có số liệu

![Hình 1 – Bài toán trade-off](../images/01-bai-toan-trade-off.svg)

*Hình 1 (tài liệu chính). Cùng một tải, ba cách cấp phát.*

Giả sử một dịch vụ nội bộ có mỗi ngày **8 giờ cao điểm** với tải 3C và **16 giờ thấp điểm** với tải 0,5C. Target là 80% năng lực mỗi replica, tức mỗi replica gánh 0,8C:
- Giờ cao điểm cần ⌈3 ÷ 0,8⌉ = 4 replica.
- Giờ thấp điểm cần 1 replica.

| Cách cấp phát | GPU-giờ/ngày | Chi phí/tháng (0,7 USD/GPU-giờ) | Chất lượng dịch vụ |
|---|---|---|---|
| Static-min (1 replica) | 24 | ~504 USD | **Vi phạm SLO suốt 8 giờ cao điểm** (33% thời gian) |
| Static-max (4 replica) | 96 | ~2.016 USD | Đạt SLO |
| Autoscaling lý tưởng | 8 × 4 + 16 × 1 = 48 | ~1.008 USD | Đạt SLO, trừ các **khoảng trễ khi scale-up** |

Trên giấy, autoscaling tiết kiệm **50%** chi phí so với Static-max. Đồ án sẽ đo trên thực tế:
- Khoảng trễ scale-up dài bao nhiêu và gây vi phạm SLO đến mức nào.
- Phần tiết kiệm thực tế còn lại bao nhiêu, sau khi trừ các yếu tố như pod đang khởi động vẫn giữ GPU và việc chờ ổn định trước khi scale-down.

---

## 5. Vì sao autoscaling cho LLM khó

### 5.1. Cold start tính bằng phút
Một pod web thông thường sẵn sàng sau vài giây. Một pod vLLM phải pull image khoảng 10 GB, tải và nạp khoảng 15 GB weights, rồi compile và capture CUDA graph, tổng cộng **từ 1 đến 8 phút** (Hình 12). Trong khoảng thời gian đó, tải tăng đột ngột sẽ dồn hết lên các replica hiện có. → Chi tiết ở [05 §7](05-kien-truc-he-thong.md#7-cold-start-chi-tiết).

### 5.2. Metric quen thuộc chỉ sai hướng
- **VRAM:** vLLM cấp phát trước khoảng 90% VRAM ngay khi khởi động, nên metric bộ nhớ gần như là một đường thẳng.
- **GPU utilization** (`DCGM_FI_DEV_GPU_UTIL`) chỉ đo tỷ lệ thời gian *có ít nhất một kernel đang chạy*. Với continuous batching, GPU gần như lúc nào cũng có kernel chạy, nên metric này bão hoà gần 100% ngay cả khi tải còn thấp.
→ Phân tích chi tiết ở [07 §3](07-chien-luoc-autoscaling.md#3-phân-tích-từng-metric).

### 5.3. Tài nguyên rời rạc và đắt
Mỗi lần scale là thêm hoặc bớt **nguyên một GPU**. Khác với CPU chia được theo millicore, GPU không có mức "thêm 10%". Một bước scale thừa tốn cả một GPU trong suốt thời gian chờ ổn định trước khi scale-down (mặc định 5 phút).

### 5.4. Request dài và có trạng thái
Một request có thể kéo dài hàng chục giây, và trạng thái của nó (KV-cache) nằm trên đúng GPU đang xử lý. Khi scale-down, không thể "chuyển" request sang pod khác. Pod phải được xử lý xong các request đang chạy (*drain*) trước khi bị xoá, và nếu làm sai thì request bị cắt ngang. → Xem [05 §8](05-kien-truc-he-thong.md#8-scale-down-và-graceful-shutdown).

### 5.5. Cân bằng tải không biết trạng thái của pod
Service của Kubernetes chia request gần như ngẫu nhiên, không biết pod nào đang có hàng đợi dài. Hệ quả là có pod quá tải trong khi pod khác còn rảnh, nên năng lực thực tế thấp hơn tổng năng lực danh nghĩa. → Được đưa vào hướng mở rộng ở [15](15-huong-mo-rong.md#e1-định-tuyến-có-nhận-biết-llm).

---

## 6. Phát biểu bài toán

Gọi:
- λ(t): tốc độ request đến.
- N(t) ∈ {1, …, N_max}: số replica đang giữ GPU.
- π: chính sách autoscaling. π quyết định số replica mong muốn N\*(t) dựa trên metric quan sát được m(t − δ), với δ là độ trễ phát hiện.

Replica mới chỉ bắt đầu phục vụ sau thời gian cold start D. Bài toán là:

$$
\min_{\pi} \;\; \text{GPU-giờ} = \int_0^T N(t)\,dt
\qquad \text{với ràng buộc} \qquad
\text{SLO attainment} \;\ge\; \alpha
$$

trong đó SLO attainment là tỷ lệ request đạt SLO về TTFT và TPOT, và α là mức mong muốn, ví dụ 95%.

Đồ án **không đi tìm chính sách tối ưu** cho bài toán này. Thay vào đó, đồ án làm hai việc:
1. So sánh ba lựa chọn tín hiệu m(t) (chiến lược A1–A3) khi dùng cùng một cơ chế π chuẩn là HPA/KEDA. Đây là RQ1.
2. Đo và tìm cách giảm D (cold start). Đây là RQ2.

Kết quả được đặt cạnh hai "đáp án biên" là Static-1 và Static-4, để định lượng trade-off (RQ3).

---

## 7. Ý nghĩa thực tiễn

- Doanh nghiệp tự vận hành LLM (vì lý do dữ liệu, chi phí khi quy mô lớn, hoặc tuỳ biến) đều gặp đúng bài toán này. Nơi làm việc của hai thành viên cung cấp dịch vụ cloud và AI, nên kết quả đồ án có thể đem vào thực tế.
- Đồ án chỉ dùng thành phần chuẩn (KEDA, HPA, Prometheus). Vì vậy khuyến nghị rút ra (nên scale theo metric nào, đặt target bao nhiêu, cold start tối ưu tới đâu) áp dụng được ngay cho các nền tảng dựa trên cùng cơ chế như KServe hay vLLM Production Stack.

---

## 8. Câu hỏi hội đồng có thể đặt ra

**Sao không dùng API có sẵn (OpenAI, Gemini…) thay vì tự vận hành?**
Có ba lý do khiến doanh nghiệp tự vận hành: dữ liệu nhạy cảm không được gửi ra ngoài, chi phí ở quy mô lớn, và nhu cầu tuỳ biến hoặc dùng model riêng. Hơn nữa, đề tài nghiên cứu **hạ tầng serving**, không phải bản thân model.

**Kubernetes đã có sẵn HPA, vậy đóng góp của nhóm là gì?**
HPA chỉ là cơ chế. Câu hỏi mở nằm ở chỗ **dùng tín hiệu gì** và **cold start ảnh hưởng thế nào** trong trường hợp đặc thù của LLM. Đồ án trả lời hai câu hỏi đó bằng thực nghiệm có kiểm soát, có số liệu và tái lập được.

**Sao không scale-to-zero để tiết kiệm tối đa?**
Với cold start 1–8 phút, request đầu tiên sau một khoảng nghỉ sẽ phải chờ vài phút. Điều này không chấp nhận được với dịch vụ tương tác. Scale-to-zero chỉ hợp lý khi cold start giảm được xuống vài giây, nên được đặt ở hướng mở rộng.

**Sao không scale theo lịch cố định (scheduled scaling)?**
Scale theo lịch hiệu quả khi tải lặp lại đều đặn, và có thể **kết hợp** với autoscaling (ví dụ KEDA cron scaler). Tuy nhiên nó không xử lý được các đợt tăng đột biến không báo trước (KB2). Đồ án chọn autoscaling phản ứng theo tải làm trọng tâm, còn autoscaling dự báo nằm ở hướng mở rộng.

---

## Đọc thêm
- [1] vLLM/PagedAttention; [3] Splitwise (Azure trace); [5] BurstGPT (danh mục đầy đủ ở [mục 16 của tài liệu chính](../mo-ta-chi-tiet-do-an.md#16-tài-liệu-tham-khảo)).
- M. Harchol-Balter, *Performance Modeling and Design of Computer Systems: Queueing Theory in Action*, Cambridge University Press, 2013, chương về M/M/1.
