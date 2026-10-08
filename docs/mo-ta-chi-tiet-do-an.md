# Thiết kế và Đánh giá Nền tảng LLM Serving trên Kubernetes có Autoscaling

**Tên đề tài đã đăng ký:** *Design and Evaluation of an LLM Serving Platform on Kubernetes with Autoscaling*
**Loại tài liệu:** Bản mô tả đồ án tốt nghiệp (bản tổng quan gửi giảng viên hướng dẫn) · phiên bản 3.0 · 08/10/2026 (thay đổi so với bản 2.0: [ADR-004](adr/004-dieu-kien-thuc-te-va-pham-vi-rut-gon.md), [ADR-005](adr/005-sua-thiet-ke-sau-review.md))
**Thời gian thực hiện:** 08/10/2026 đến hạn nộp luận văn khoảng 08/12/2026

| Thành viên | Đơn vị | Vai trò trong đồ án |
|---|---|---|
| Trình |  | Chia đều như nhau |
| Quang |  | Chia đều như nhau |

Phân công chi tiết sẽ chốt sau ([Kế hoạch §5](chi-tiet/06-ke-hoach-quan-ly.md#5-gói-công-việc-và-ước-lượng-người-giờ)).

---

## Tóm tắt

Đồ án xây dựng và vận hành một nền tảng phục vụ (*serving*) mô hình ngôn ngữ lớn (LLM) mã nguồn mở, cho tình huống một doanh nghiệp **tự host LLM** vì dữ liệu nội bộ không được gửi ra API bên ngoài. Nền tảng dùng **vLLM** chạy trên **Kubernetes** với GPU, tự điều chỉnh số replica (*autoscaling*) theo metric của chính vLLM thông qua **KEDA + HPA**, được dựng và cập nhật hoàn toàn bằng code (**IaC + GitOps với Argo CD**), và có **giám sát, cảnh báo theo SLO và runbook** để vận hành hằng ngày.

Vận hành LLM trên GPU có những khó khăn mà cấu hình mặc định của Kubernetes không giải được:
- GPU utilization không phản ánh tải.
- Một pod mới cần tới vài phút để sẵn sàng (*cold start*).
- Scale-down có thể cắt ngang các request streaming dài.
- Rolling update kiểu web bị kẹt khi mọi GPU đều đang có pod.

Đồ án giải từng vấn đề, rồi **đánh giá** nền tảng để nghiệm thu: so với hai cấu hình tĩnh (1 và 4 replica) dưới ba kịch bản tải của đề cương, và qua sáu kịch bản vận hành (scale-down, cập nhật phiên bản, sự cố, mất nguồn metric, dựng lại từ đầu, cảnh báo).

**Tỷ trọng công việc:** khoảng **70% xây dựng và vận hành**, **30% đánh giá**. Kết quả cuối cùng là một nền tảng dựng lại được bằng vài lệnh, một bộ công cụ vận hành (dashboard, cảnh báo, runbook, quy trình), một **bảng nghiệm thu** cho từng yêu cầu, và khuyến nghị cấu hình.

**Điều kiện thực hiện** ([chi tiết](chi-tiet/00-thong-so.md#2-điều-kiện-thực-hiện)): khoảng 9 tuần đến hạn nộp; hai thành viên đều đi làm; máy nhà có GPU 6–8 GB nên chỉ dùng để phát triển và kiểm thử chức năng; phần đánh giá chạy trên GPU thuê (Vast.ai, 4 × RTX 4090) trong **một lần thuê liền vào cuối tuần**; tiền thuê GPU tối đa 150 USD.

## Mục lục

1. [Bài toán](#1-bài-toán)
2. [Mục tiêu, yêu cầu và đóng góp](#2-mục-tiêu-yêu-cầu-và-đóng-góp)
3. [Phạm vi](#3-phạm-vi)
4. [Giải pháp](#4-giải-pháp)
5. [Vận hành nền tảng](#5-vận-hành-nền-tảng)
6. [Môi trường và đánh giá](#6-môi-trường-và-đánh-giá)
7. [Kế hoạch, rủi ro và sản phẩm bàn giao](#7-kế-hoạch-rủi-ro-và-sản-phẩm-bàn-giao)
- [Bộ tài liệu](#bộ-tài-liệu)
- [Tài liệu tham khảo](#tài-liệu-tham-khảo)
- [Phụ lục A. Đối chiếu với đề cương đã nộp](#phụ-lục-a-đối-chiếu-với-đề-cương-đã-nộp)

---

## 1. Bài toán

> **Chi tiết:** [Bài toán, yêu cầu và phạm vi](chi-tiet/01-bai-toan-yeu-cau.md)

Một doanh nghiệp vài nghìn nhân viên muốn có trợ lý AI nội bộ, nhưng dữ liệu không được gửi ra ngoài, nên phải tự host một model mở trên GPU. GPU **đắt**, **rời rạc** (mỗi replica chiếm trọn một GPU), và tải **không ổn định**: cao giờ làm việc, gần bằng 0 ban đêm, có lúc tăng đột ngột.

![Hình 1 – Bài toán trade-off](images/01-bai-toan-trade-off.svg)

*Hình 1. Cùng một tải thay đổi theo thời gian, ba cách cấp phát cho ba kết quả khác nhau. C là năng lực của một replica.*

Cấp ít GPU cố định thì vi phạm SLO lúc cao điểm; cấp đủ cho đỉnh thì GPU nhàn rỗi phần lớn thời gian. Autoscaling bám theo tải, nên trên giấy tiết kiệm được khoảng một nửa GPU-giờ, nhưng chỉ khi giải được các khó khăn riêng của GPU nêu ở phần Tóm tắt.

**Phát biểu bài toán.** Xây dựng và vận hành một nền tảng phục vụ LLM tự host trên Kubernetes, với một nhóm GPU cố định, sao cho: (1) phần lớn request đạt SLO về độ trễ, kể cả khi tải thay đổi; (2) GPU-giờ chỉ ở mức cần thiết; (3) vận hành được hằng ngày: cập nhật và scale-down không làm rớt request, có cảnh báo kèm hướng dẫn xử lý, dựng lại được từ Git.

---

## 2. Mục tiêu, yêu cầu và đóng góp

> **Chi tiết:** [Bài toán §8–§10](chi-tiet/01-bai-toan-yeu-cau.md#8-từ-bài-toán-đến-yêu-cầu) · Định nghĩa và ngưỡng: [Thông số và chỉ tiêu](chi-tiet/00-thong-so.md)

**Mục tiêu tổng quát.** Xây dựng và vận hành một nền tảng LLM serving trên Kubernetes có autoscaling, triển khai và cập nhật hoàn toàn bằng code, có giám sát và cảnh báo theo SLO, có quy trình xử lý sự cố; sau đó đánh giá nền tảng bằng các kịch bản tải và kịch bản vận hành, so với cấu hình tài nguyên cố định. Bảy mục tiêu cụ thể trong đề cương được **giữ nguyên** và được cụ thể hoá thành:

- **Bảy yêu cầu chức năng F1–F7:** phục vụ một model mở qua API tương thích OpenAI có streaming; tự điều chỉnh số replica theo tải; triển khai và rollback qua Git; dựng toàn bộ từ máy trắng bằng vài lệnh; dashboard; cảnh báo kèm runbook; bảo vệ tối thiểu.
- **Tám chỉ tiêu nghiệm thu N1–N8:** chất lượng phục vụ; tốc độ phản ứng; hiệu quả GPU; 0 request lỗi khi scale-down và cập nhật; cold start sau tối ưu; tự phục hồi và dựng lại; cảnh báo kịp và không báo giả; tái lập và chi phí. Ngưỡng là sơ bộ, chốt **một lần** sau bước đo năng lực.

Kết quả của đồ án được tổng hợp thành một **bảng nghiệm thu**: mỗi yêu cầu có số đo và kết luận Đạt hoặc Không đạt.

**Đóng góp dự kiến**
1. Một nền tảng LLM serving hoàn chỉnh, dựng lại được bằng code, chạy trên cả cluster ở nhà lẫn GPU thuê.
2. Thiết kế autoscaling cho LLM dựa trên metric của vLLM, kèm số đo cho thấy vì sao không nên scale theo GPU utilization.
3. Quy trình rút ngắn cold start của vLLM trên Kubernetes, đo theo từng pha.
4. Bộ công cụ vận hành cho LLM serving: SLO, quy tắc cảnh báo, runbook, quy trình scale-down và cập nhật không làm rớt request (kể cả khi hết GPU trống), quy trình dựng lại.
5. Kết quả đánh giá so với cấu hình tĩnh, và khuyến nghị cấu hình có ghi rõ điều kiện áp dụng.

---

## 3. Phạm vi

> **Chi tiết:** [Bài toán §12](chi-tiet/01-bai-toan-yeu-cau.md#12-phạm-vi)

- **Trong phạm vi:** phục vụ **một model** bằng vLLM trên GPU; autoscaling **mức pod** trên một nhóm GPU cố định (mỗi replica một GPU); rút ngắn cold start; IaC, GitOps và CI; giám sát, SLO, cảnh báo, runbook; cập nhật phiên bản, xử lý sự cố, dựng lại từ đầu; bảo mật tối thiểu; sinh tải và đánh giá để nghiệm thu.
- **Ngoài phạm vi:** huấn luyện, fine-tuning; chia sẻ GPU (MIG, time-slicing); tensor/pipeline parallelism, tách prefill/decode; autoscaling mức node, scale-to-zero, định tuyến nhận biết LLM (hướng mở rộng); log tập trung, tracing, đa người dùng.
- **Giả định chính:** chi phí được đo bằng GPU-giờ cấp phát cho các pod vLLM. Trên một nhóm GPU cố định dành riêng, scale-down **không tự động làm giảm tiền phải trả**; luận văn ghi rõ điều này.

---

## 4. Giải pháp

> **Chi tiết:** [Kiến trúc hệ thống và thiết kế autoscaling](chi-tiet/03-kien-truc-autoscaling.md) · Nền tảng lý thuyết: [Kiến thức nền](chi-tiet/02-kien-thuc-nen.md)

![Hình 2 – Kiến trúc tổng thể](images/02-kien-truc-tong-the.svg)

*Hình 2. Kiến trúc tổng thể. Request đi từ client qua Traefik (giới hạn tốc độ) và Service tới các pod vLLM (kiểm API key), mỗi pod gắn một GPU. Prometheus thu metric; KEDA chạy PromQL và cung cấp external metric cho HPA; HPA cập nhật số replica của Deployment.*

![Hình 4 – Vòng lặp autoscaling](images/04-vong-lap-autoscaling.svg)

*Hình 4. Vòng lặp autoscaling: pha phát hiện (bước 1–4) và pha thực thi (bước 5–8). Cold start chiếm phần lớn thời gian phản ứng.*

Mỗi khó khăn riêng của GPU có một cách xử lý trong thiết kế:

| Khó khăn | Cách xử lý | Chi tiết |
|---|---|---|
| GPU utilization bão hoà, không phản ánh tải | Scale theo **số request đang xử lý cộng đang chờ** của vLLM (cấu hình A2); GPU utilization (A1) chỉ làm đối chứng | [Kiến trúc §10](chi-tiet/03-kien-truc-autoscaling.md#10-phân-tích-từng-metric) |
| Target scale dễ chọn cảm tính | Tính target từ kết quả **đo năng lực một replica** | [Kiến trúc §11](chi-tiet/03-kien-truc-autoscaling.md#11-chọn-target-từ-kết-quả-đo-năng-lực) |
| Cold start tính bằng phút | Pre-pull image, model trên NVMe cục bộ, giữ compile cache (mức L2); đo theo 8 pha | [Kiến trúc §7](chi-tiet/03-kien-truc-autoscaling.md#7-cold-start-chi-tiết) |
| Scale-down cắt request streaming | preStop, cờ `--shutdown-timeout` của vLLM (mặc định vLLM **huỷ** request khi bị tắt), grace period đủ dài | [Kiến trúc §8](chi-tiet/03-kien-truc-autoscaling.md#8-scale-down-và-graceful-shutdown) |
| Rolling update kẹt khi hết GPU trống | Xoá pod cũ trước rồi mới tạo pod mới; khi chỉ có 1 replica thì tạm nâng lên 2 trước khi cập nhật | [Vận hành §5](chi-tiet/04-van-hanh.md#5-cập-nhật-phiên-bản-khi-gpu-đã-dùng-hết) |
| Argo CD và HPA tranh nhau số replica | Không đặt `replicas` trong Git | [Kiến trúc §18.3](chi-tiet/03-kien-truc-autoscaling.md#183-cạm-bẫy-argo-cd-và-hpa-tranh-nhau-replicas) |

**Định vị.** Đồ án **không xây dựng autoscaler mới** và không tối ưu engine. Đồ án lắp ráp một nền tảng từ các thành phần chuẩn mà doanh nghiệp đang dùng (Kubernetes, KEDA, Prometheus, Argo CD), giải các vấn đề vận hành riêng của GPU và LLM, rồi đo để biết nền tảng đáp ứng được tới đâu ([Kiến thức nền §6](chi-tiet/02-kien-thuc-nen.md#6-các-giải-pháp-và-nghiên-cứu-liên-quan)).

---

## 5. Vận hành nền tảng

> **Chi tiết:** [Vận hành nền tảng](chi-tiet/04-van-hanh.md)

![Hình 7 – Từ SLO tới cảnh báo và runbook](images/07-slo-canh-bao-runbook.svg)

*Hình 7. Đường đi từ metric tới hành động: SLI tính bằng recording rule, cảnh báo theo burn rate, Alertmanager định tuyến theo mức độ, người trực mở runbook, mọi thay đổi đi qua Git.*

- **SLO** cho TTFT, TPOT và tỷ lệ lỗi; **cảnh báo theo tốc độ tiêu hao ngân sách lỗi** (burn rate) và theo sức khoẻ nền tảng, hai mức page và ticket, gửi tới Telegram; **mỗi cảnh báo có một runbook**.
- **Thay đổi an toàn:** mọi cập nhật đi qua PR và Argo CD; rollback bằng `git revert`; quy trình cập nhật riêng cho trường hợp hết GPU trống.
- **Khôi phục:** dựng lại toàn bộ từ máy trắng bằng vài lệnh; thứ duy nhất phải sao lưu ngoài Git là khoá giải mã bí mật.
- **Bảo mật tối thiểu và chi phí:** API key, giới hạn tốc độ, NetworkPolicy, bí mật mã hoá trong Git; dashboard GPU-giờ và chi phí trên 1 triệu token.

---

## 6. Môi trường và đánh giá

> **Chi tiết:** [Môi trường triển khai và đánh giá](chi-tiet/05-moi-truong-danh-gia.md) · Kịch bản, cấu hình, ma trận: [Thông số §7–§8](chi-tiet/00-thong-so.md#7-kịch-bản-tải)

![Hình 6 – Hai tầng môi trường](images/06-moi-truong-trien-khai.svg)

*Hình 6. Hai tầng môi trường từ cùng một Git repository: máy nhà và simulator để xây dựng và vận hành thử; VM 4 GPU thuê theo giờ để đánh giá.*

- **Tầng 1 (máy nhà và simulator):** phát triển, kiểm thử chức năng và phần lớn kịch bản vận hành, gần như không tốn tiền. Số liệu hiệu năng ở đây không dùng để kết luận.
- **Tầng 2 (GPU thuê):** toàn bộ phần đo trên GPU thật chạy trong **một lần thuê liền** trên cùng một máy, để các cấu hình so sánh được với nhau. Có hai mức dự phòng: máy khác cùng loại, rồi GCP bằng credit.
- **Đánh giá để nghiệm thu**, không phải nghiên cứu thống kê:
  - **ĐG1** đo năng lực một replica, từ đó chốt SLO, target và tải của các kịch bản.
  - **ĐG2** so sánh hai cấu hình tĩnh (1 và 4 replica) với hai cấu hình autoscaling (A1, A2) dưới **ba kịch bản tải của đề cương**: thấp ổn định, tăng đột ngột rồi giảm, cao kéo dài.
  - **ĐG3** đo cold start trước và sau tối ưu.
  - **VH1–VH6** kiểm chứng các quy trình vận hành.

![Hình 8 – Ba kịch bản tải](images/08-kich-ban-tai.svg)

*Hình 8. Ba kịch bản tải theo đề cương, đơn vị là C (năng lực của một replica).*

---

## 7. Kế hoạch, rủi ro và sản phẩm bàn giao

> **Chi tiết:** [Kế hoạch, rủi ro, sản phẩm bàn giao và hướng mở rộng](chi-tiet/06-ke-hoach-quan-ly.md)

![Hình 9 – Kế hoạch đến hạn nộp](images/09-ke-hoach.svg)

*Hình 9. Kế hoạch 9 tuần đến hạn nộp, với các phiên thuê GPU và các mốc.*

- **Kế hoạch:** 4 tuần đầu xây dựng và vận hành thử ở nhà, xen hai phiên thuê GPU nhỏ; tuần thứ 5 là lần thuê liền để đánh giá; dữ liệu đóng băng giữa tháng 11; phần còn lại dành cho viết luận văn ([Kế hoạch §1–§2](chi-tiet/06-ke-hoach-quan-ly.md#1-lịch-và-mốc)).
- **Rủi ro chính:** thiếu thời gian viết trước hạn nộp; không thuê được đúng loại máy vào đúng cuối tuần; phạm vi rút gọn chưa được duyệt; hội đồng đánh giá đồ án thiên về cài đặt. Mỗi rủi ro có biện pháp phòng ngừa và kế hoạch B ([Kế hoạch §9](chi-tiet/06-ke-hoach-quan-ly.md#9-rủi-ro)).
- **Sản phẩm bàn giao:** Git repository; bộ vận hành (dashboard, cảnh báo có unit test, runbook); công cụ đánh giá; dữ liệu đánh giá và nhật ký vận hành; hướng dẫn tái lập và vận hành; luận văn kèm bảng nghiệm thu; slide và demo ([Kế hoạch §10–§11](chi-tiet/06-ke-hoach-quan-ly.md#10-sản-phẩm-bàn-giao)).
- **Đề nghị với GVHD:** xác nhận phạm vi rút gọn, kế hoạch 9 tuần và hình thức demo **trước 16/10/2026**; họp khoảng 2 tuần một lần và rà soát kỹ tại mỗi mốc.

---

## Bộ tài liệu

Mỗi giá trị (yêu cầu, chỉ tiêu, SLO, kịch bản, tham số, cấu hình máy, ngân sách) chỉ được định nghĩa ở **một chỗ** là [Thông số và chỉ tiêu](chi-tiet/00-thong-so.md); các tài liệu khác link về đó. Mọi tài liệu có cùng khung: **tóm tắt nhanh**, phần nội dung, và **câu hỏi hội đồng có thể đặt ra** ở cuối để chuẩn bị bảo vệ.

| # | Tài liệu | Nội dung chính | Hình | Chương luận văn |
|---|---|---|---|---|
| 0 | [Thông số và chỉ tiêu](chi-tiet/00-thong-so.md) | Điều kiện thực hiện; F1–F7, N1–N8; Must/Should/Could; SLO; KB1–KB3; cấu hình và ma trận; tham số vLLM, Deployment, KEDA/HPA; máy; ngân sách | – | Phụ lục, 3.1 |
| 1 | [Bài toán, yêu cầu và phạm vi](chi-tiet/01-bai-toan-yeu-cau.md) | VRAM và KV-cache, batching, đặc điểm tải, lý thuyết hàng đợi, vì sao vận hành LLM trên GPU khó; phát biểu bài toán; đối chiếu đề cương; ma trận truy vết; phạm vi, giả định, hạn chế, điều kiện so sánh công bằng | 1, 10 | 1, 3.1 |
| 2 | [Kiến thức nền](chi-tiet/02-kien-thuc-nen.md) | Prefill/decode, KV-cache, vLLM V1 và metric, thuật toán HPA, KEDA, metric GPU, SLO và burn rate, GitOps, rolling update, giải pháp liên quan, thuật ngữ | 11 | 2 |
| 3 | [Kiến trúc và autoscaling](chi-tiet/03-kien-truc-autoscaling.md) | Thành phần, Deployment, lưu trữ model, Ingress; mô hình thời gian; cold start 8 pha; graceful shutdown; phân tích A1–A4, chọn target, YAML, cạm bẫy, kiểm thử, cấu hình khuyến nghị; giám sát; GitOps | 2, 3, 4, 5, 12, 13, 14, 15 | 3.2–3.3, 4.3–4.5 |
| 4 | [Vận hành](chi-tiet/04-van-hanh.md) | SLI/SLO, cảnh báo theo burn rate, Alertmanager, runbook, cập nhật khi hết GPU, sự cố, dựng lại từ đầu, bảo mật tối thiểu, chi phí và năng lực | 7, 16 | 3.4–3.5, 4.6–4.10 |
| 5 | [Môi trường và đánh giá](chi-tiet/05-moi-truong-danh-gia.md) | Máy nhà và simulator; Vast.ai chế độ VM; burn-in; Makefile; chi phí; dự phòng GCP; các phiên thuê; ĐG1–ĐG3; máy tạo tải; VH1–VH6; chỉ số; bảng nghiệm thu | 6, 8, 17 | 3.6, 4.1, 4.11, 5 |
| 6 | [Kế hoạch và quản lý](chi-tiet/06-ke-hoach-quan-ly.md) | Lịch 9 tuần, mốc, đường găng, người-giờ, hợp đồng giao diện, cắt giảm, rủi ro, sản phẩm bàn giao, cấu trúc repo, luận văn, slide, demo, hướng mở rộng | 9 | 6 |

Quyết định: [docs/adr/](adr/) ([ADR-001](adr/001-cac-lua-chon-ban-dau.md), [ADR-002](adr/002-chuyen-trong-tam-sang-van-hanh.md), [ADR-004](adr/004-dieu-kien-thuc-te-va-pham-vi-rut-gon.md), [ADR-005](adr/005-sua-thiet-ke-sau-review.md); ADR-003 dành cho kết quả đo năng lực). Review thiết kế: [docs/review/](review/review-2026-10-08.md).

**Lộ trình đọc gợi ý**
- *Để hiểu nền tảng:* 1 → 2 → 3 → 4.
- *Để bắt tay vào làm:* 0 → 5 (§1–§3) → 3 → 4 → 6 (§2).
- *Để chuẩn bị phiên đánh giá:* 0 → 5 (§6–§17) → 6 (§9.5).
- *Trước buổi bảo vệ:* đọc mục "Câu hỏi hội đồng" ở cuối mỗi tài liệu.

**Ghi chú về số liệu:** mọi con số về thời gian, năng lực và chi phí trong bộ tài liệu là **ước lượng hoặc minh hoạ** dựa trên thông số phần cứng và hiểu biết chung. Chúng sẽ được thay bằng số đo thực tế của đồ án. Tên metric, cờ dòng lệnh và cách cài đặt có thể đổi theo phiên bản, nên luôn kiểm tra lại sau khi ghim phiên bản.

**Thay đổi so với bản 2.0:** điều kiện thực tế (thời gian, máy nhà, cloud) khác giả định ban đầu, nên phạm vi được rút gọn và kế hoạch được làm lại cho tới hạn nộp ([ADR-004](adr/004-dieu-kien-thuc-te-va-pham-vi-rut-gon.md)); thiết kế được sửa ở phần graceful shutdown, rolling update khi có 1 replica và một số điểm đo lường ([ADR-005](adr/005-sua-thiet-ke-sau-review.md)); 14 tài liệu chuyên sâu được gộp thành 7. Bản 2.0 đã chuyển trọng tâm sang xây dựng và vận hành ([ADR-002](adr/002-chuyen-trong-tam-sang-van-hanh.md)).

---

## Tài liệu tham khảo

1. W. Kwon et al., "Efficient Memory Management for Large Language Model Serving with PagedAttention," *SOSP*, 2023.
2. Y. Zhong et al., "DistServe: Disaggregating Prefill and Decoding for Goodput-optimized Large Language Model Serving," *OSDI*, 2024.
3. P. Patel et al., "Splitwise: Efficient Generative LLM Inference Using Phase Splitting," *ISCA*, 2024.
4. Y. Fu et al., "ServerlessLLM: Low-Latency Serverless Inference for Large Language Models," *OSDI*, 2024.
5. Y. Wang et al., "BurstGPT: A Real-world Workload Dataset to Optimize LLM Serving Systems," arXiv:2401.17644, 2024.
6. AIBrix Team, "AIBrix: Towards Scalable, Cost-Effective Large Language Model Inference Infrastructure," 2025.
7. Kubernetes Documentation, "Horizontal Pod Autoscaling." https://kubernetes.io/docs/tasks/run-application/horizontal-pod-autoscale/
8. KEDA Documentation, "Prometheus scaler." https://keda.sh/docs/latest/scalers/prometheus/
9. vLLM Documentation (Metrics, Production deployment, CLI `serve`). https://docs.vllm.ai/
10. NVIDIA GPU Operator Documentation. https://docs.nvidia.com/datacenter/cloud-native/gpu-operator/latest/
11. NVIDIA DCGM Exporter. https://github.com/NVIDIA/dcgm-exporter
12. KServe Documentation. https://kserve.github.io/website/
13. Gateway API Inference Extension. https://gateway-api-inference-extension.sigs.k8s.io/
14. llm-d. https://github.com/llm-d/llm-d
15. vLLM Production Stack. https://github.com/vllm-project/production-stack
16. GuideLLM. https://github.com/vllm-project/guidellm
17. llm-d-inference-sim. https://github.com/llm-d/llm-d-inference-sim
18. Azure Public Dataset (LLM inference traces). https://github.com/Azure/AzurePublicDataset
19. B. Schroeder, A. Wierman, M. Harchol-Balter, "Open Versus Closed: A Cautionary Tale," *NSDI*, 2006.
20. G.-I. Yu et al., "Orca: A Distributed Serving System for Transformer-Based Generative Models," *OSDI*, 2022.
21. A. Agrawal et al., "Taming Throughput-Latency Tradeoff in LLM Inference with Sarathi-Serve," *OSDI*, 2024.
22. B. Sun et al., "Llumnix: Dynamic Scheduling for Large Language Model Serving," *OSDI*, 2024.
23. B. Beyer, N. R. Murphy, D. K. Rensin, K. Kawahara, S. Thorne (eds.), *The Site Reliability Workbook*, O'Reilly, 2018, chương "Alerting on SLOs".
24. Kubernetes Documentation, "Deployments" (rolling update). https://kubernetes.io/docs/concepts/workloads/controllers/deployment/
25. Prometheus Documentation, "Alerting rules" và "Alertmanager." https://prometheus.io/docs/alerting/latest/overview/
26. Argo CD Documentation. https://argo-cd.readthedocs.io/
27. Sealed Secrets. https://github.com/bitnami-labs/sealed-secrets

---

## Phụ lục A. Đối chiếu với đề cương đã nộp

Tên đề tài và bảy mục tiêu trong đề cương được **giữ nguyên**. Bản mô tả này chỉ **cụ thể hoá** chúng, và mọi bổ sung đều nằm trong phạm vi *"Design and Evaluation … with Autoscaling"*:

| Nội dung trong đề cương | Cụ thể hoá trong bản mô tả |
|---|---|
| "KEDA or KServe" | Chọn **KEDA + Deployment** làm cơ chế chính, vì minh bạch và ít thành phần phải vận hành; KServe để ở hướng mở rộng |
| "Autoscaling based on workload or request-related metrics" | A2 (tải đồng thời, metric của vLLM) là cấu hình vận hành; A1 (GPU utilization) làm đối chứng |
| Ba kịch bản tải | Giữ đúng ba kịch bản: thấp ổn định, tăng đột ngột, cao kéo dài. KB2 được cho giảm tải trở lại để kiểm tra scale-down; tải định nghĩa theo C sau bước đo năng lực |
| "Static vs Autoscaling" | Hai cấu hình tĩnh Static-1 và Static-4, so với A1, A2 |
| "Autoscaling Response Time" | Tách thành độ trễ phát hiện, cold start (theo từng pha) và thời gian hồi phục SLO; thêm phần rút ngắn cold start |
| "P95/P99 Latency, TTFT, Throughput, Resource Utilization" | Bổ sung TPOT, SLO attainment, tỷ lệ lỗi; "resource utilization" được báo cáo bằng GPU-giờ, token/GPU-giờ, GPU utilization trung bình và CPU/RAM của pod |
| Giám sát metric serving và GPU | Mở rộng thành SLO, cảnh báo theo burn rate và runbook |
| Phân công | Phân công chi tiết chốt sau; vai trò DevOps/SRE/Cloud vẫn là một trọng tâm của đồ án |
| (chưa có) | Yêu cầu F/N và bảng nghiệm thu; phần vận hành (scale-down không cắt request, cập nhật khi hết GPU, sự cố, dựng lại, bảo mật, chi phí); môi trường hai tầng; dự toán chi phí; kế hoạch đến hạn nộp; quản lý rủi ro |

Bản mô tả 1.0 có thêm câu hỏi nghiên cứu, giả thuyết, hai kịch bản tải KB4 và KB5 và một thiết kế thí nghiệm thống kê; bản 2.0 bỏ các phần này để quay về đúng đề cương ([ADR-002](adr/002-chuyen-trong-tam-sang-van-hanh.md)).

---

*Toàn bộ sơ đồ trong tài liệu được sinh bằng code. Để tạo lại: `python3 docs/diagrams/build_diagrams.py` (ra SVG), rồi `bash docs/diagrams/export_png.sh` (ra PNG 2× trong `docs/images/png/`, dùng cho Word hoặc slide).*
