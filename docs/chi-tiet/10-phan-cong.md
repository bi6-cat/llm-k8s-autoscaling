# 10. Phân công công việc: tài liệu chuyên sâu

> Thuộc [Mục 10 của bản mô tả chính](../mo-ta-chi-tiet-do-an.md#10-phân-công-công-việc) · [Danh mục tài liệu chuyên sâu](README.md)

**Tóm tắt nhanh**
- Phân công theo **chuyên môn**: Trình (Platform) lo tầng GPU, vLLM, autoscaling, cold start, cập nhật phiên bản và bảo mật tối thiểu; Quang (DevOps/SRE/Cloud) lo hạ tầng cloud và cluster, IaC, GitOps, giám sát, SLO, cảnh báo, runbook, khôi phục, chi phí và công cụ đánh giá.
- Mỗi phần có **một người chịu trách nhiệm chính**, nhưng mọi thay đổi đều được **người còn lại review**.
- Bảng RACI chia thành **8 gói công việc**. Có **hợp đồng giao diện** giữa hai người để làm song song mà không chờ nhau.
- Chương luận văn được chia theo gói công việc, nên đóng góp của mỗi người nhìn thấy được.

---

## 1. Nguyên tắc

1. **Đúng sở trường:** Trình phụ trách những gì chạy trên GPU và quyết định năng lực phục vụ. Quang phụ trách hạ tầng bên dưới (máy thuê, cluster) và những gì giúp nền tảng dựng lại được, quan sát được và vận hành được.
2. **Một đầu việc, một người chịu trách nhiệm.** Tránh tình trạng "cả hai cùng làm nên không ai làm".
3. **Luôn có người review:** mọi PR đều có người kia duyệt. Nhờ vậy cả hai hiểu toàn hệ thống, và khi bảo vệ ai cũng trả lời được mọi câu hỏi.
4. **Đóng góp nhìn thấy được:** mỗi người có sản phẩm riêng rõ ràng trong repo, và có chương hoặc mục luận văn riêng.

---

## 2. Bảng RACI

R = làm chính · A = chịu trách nhiệm cuối (duyệt) · C = được hỏi ý kiến · I = được thông báo. Mỗi đầu việc có đúng một A.

| Gói | Đầu việc | Trình | Quang |
|---|---|---|---|
| **WP1 Hạ tầng cloud và cluster** | Chọn nhà cung cấp, lọc máy, thuê và huỷ VM (CLI `vastai`); burn-in | C | R/A |
| | Dựng k3s bằng Ansible trên laptop và VM thuê, join nhiều node; NVMe, chrony, firewall | C | R/A |
| | Giá trị tham số k3s phục vụ autoscaling và cô lập CPU (chu kỳ sync HPA, CPU manager) | R/A | C (đưa vào Ansible) |
| | Lưu trữ dữ liệu (R2), ngân sách, theo dõi số dư | I | R/A |
| **WP2 IaC, GitOps, CI** | Cấu trúc repo, Kustomize base/overlay, Argo CD App-of-Apps, sync window | C | R/A |
| | Quản lý bí mật bằng Sealed Secrets; sao lưu khoá | C | R/A |
| | CI: lint, kubeconform, `promtool test rules`, pytest | I | R/A |
| | Makefile (`laptop-up`, `rent`, `bootstrap`, `run`, `release`…) | I | R/A |
| **WP3 GPU, vLLM serving và cold start** | Driver, container toolkit, device plugin / GPU Operator, exporter GPU | R/A | C |
| | Deployment, tham số, probe, preStop, grace period | R/A | C |
| | Lưu trữ model (PVC, NVMe), Job prefetch, DaemonSet pre-pull, compile cache | R/A | C |
| | Script đo 8 pha cold start | R/A | C |
| **WP4 Autoscaling** | ScaledObject A1, A2 (A3, A4), `behavior`, fallback | R/A | C |
| | PromQL cho các trigger | R | A (review PromQL) |
| | Bài kiểm thử T1–T7 | R/A | C |
| **WP5 Giám sát, SLO, cảnh báo** | kube-prometheus-stack, PodMonitor, metric Traefik | C | R/A |
| | Recording rule cho SLI; năm dashboard | C | R/A |
| | Quy tắc cảnh báo, Alertmanager, kênh Telegram/Discord | C | R/A |
| **WP6 Vận hành** | Runbook cho cảnh báo về GPU, vLLM, autoscaling | R/A | C |
| | Runbook cho cảnh báo về SLO, nền tảng; mẫu runbook | C | R/A |
| | Chiến lược rolling update khi hết GPU; quy trình cập nhật và rollback | R/A | C |
| | Dựng lại từ đầu (VH5) | C | R/A |
| | Bảo mật tối thiểu (API key, giới hạn tốc độ, NetworkPolicy) | R/A | C |
| | Dashboard chi phí; kế hoạch năng lực | C | R/A |
| **WP7 Đánh giá** | Máy tạo tải open-loop, lịch gửi theo λ(t) | C | R/A |
| | Runner (áp cấu hình, reset, chạy, thu thập, sao lưu) | C | R/A |
| | Đo năng lực (ĐG1), cold start (ĐG3) | R/A | R (chạy tải) |
| | Ma trận autoscaling (ĐG2) và xử lý số liệu | C | R/A |
| | Kịch bản vận hành VH1–VH6 | R (VH1–VH3) | R/A (VH4–VH6) |
| **WP8 Luận văn và bảo vệ** | Chương 2; mục 3.3; mục 4.3–4.5, 4.8, 4.10 | R/A | C |
| | Mục 3.4–3.6; mục 4.1–4.2, 4.6–4.7, 4.9, 4.11 | C | R/A |
| | Chương 5 | R (5.2, 5.4) | R/A (5.1, 5.3, 5.5, 5.6) |
| | Chương 1, 6; slide; demo | R | R (cùng làm; A: Quang cho slide, Trình cho demo) |

---

## 3. Hợp đồng giao diện giữa hai người

Được ghi vào `docs/interfaces.md` và chỉ thay đổi qua PR có người kia duyệt:

| Giao diện | Bên cung cấp → bên dùng | Nội dung cố định |
|---|---|---|
| **Hạ tầng** | Quang → Trình | Kubeconfig, danh sách node và nhãn, đường dẫn NVMe, tham số k3s; cách thuê và huỷ máy |
| **Metric** | Trình → Quang | Tên metric vLLM và GPU (theo phiên bản đã ghim), label `namespace`, `pod`; **danh sách bucket** của histogram TTFT |
| **Cấu hình** | Trình → Quang | Mỗi cấu hình là một file `autoscaling/<ID>.yaml` với ID ∈ {S1, S4, A1…A4}; tên ScaledObject `vllm-<id>`; cách tạm dừng và bỏ tạm dừng |
| **Tham số model** | Trình → Quang | `served-model-name`, `max-model-len`, tokenizer để sinh prompt |
| **Cảnh báo và runbook** | Quang → Trình | Tên cảnh báo, nhãn `severity`, đường dẫn runbook; mẫu runbook |
| **Runner** | Quang → Trình | `make run MATRIX=…`; runner đọc `capacity.json`; hook phân tích log vLLM là một hàm `parse_vllm_log(text) → dict` |
| **Dữ liệu** | Quang → cả hai | Cấu trúc thư mục lượt chạy ([09 §10.2](09-kiem-thu-danh-gia.md#102-dữ-liệu-của-một-lượt)) |

Nhờ hợp đồng này, Quang có thể viết dashboard, cảnh báo và runner với **simulator** (`llm-d-inference-sim`) trong khi Trình hoàn thiện vLLM thật, và hai bên ghép lại ở tuần 7.

---

## 4. Quy trình làm việc

| Hoạt động | Nhịp | Công cụ | Kết quả |
|---|---|---|---|
| Quản lý việc | Liên tục | GitHub Projects: Todo / Doing / Review / Done; mỗi đầu việc là một issue | Tiến độ nhìn thấy được |
| Nhánh và PR | Mỗi thay đổi | Nhánh `feat/…`, `fix/…`; PR nhỏ; **review trong 48 giờ** | Lịch sử rõ ràng |
| CI | Mỗi PR | yamllint, kubeconform, `helm template`, `promtool test rules`, ruff và pytest | Không merge khi CI đỏ |
| Họp nhóm | Hằng tuần, 30 phút | Tuần trước làm gì, tuần này làm gì, đang vướng gì; rà cảnh báo trong tuần | Ghi chú trong `docs/nhat-ky/tuan-XX.md` |
| Họp GVHD | 2 tuần một lần | Báo cáo theo mốc, demo nhanh | Biên bản, việc cần làm |
| Nhật ký quyết định | Khi có quyết định lớn | `docs/adr/NNN-<ten>.md` (ngữ cảnh, quyết định, hệ quả) | Giải thích được mọi lựa chọn khi bảo vệ |
| Nhật ký vận hành | Sau mỗi kịch bản VH và mỗi sự cố | `docs/nhat-ky/van-hanh.md` | Bằng chứng cho chương 4 và 5 |

---

## 5. Học chéo

| Người | Cần nắm thêm | Cách học |
|---|---|---|
| Quang | vLLM (prefill, decode, KV-cache, tham số), GPU trên K8s, HPA/KEDA, cold start | Đọc [04](04-kien-thuc-nen.md); review toàn bộ PR của WP3 và WP4; tự dựng lại cluster laptop một lần |
| Trình | PromQL, SLO và burn rate, Alertmanager, Argo CD, Ansible | Đọc [08](08-van-hanh.md); viết một dashboard và một quy tắc cảnh báo; làm theo một runbook trong diễn tập; tự chạy `make laptop-up` một lần |

**Tiêu chí:** trước tuần 14, **mỗi người tự demo được toàn hệ thống**: từ `make laptop-up`, qua một lần cảnh báo và xử lý theo runbook, tới biểu đồ C1.

---

## 6. Minh chứng đóng góp cá nhân

- Lịch sử commit và PR (ai viết, ai review), cùng issue được gán.
- Mục luận văn theo bảng RACI.
- Nhật ký tuần, nhật ký vận hành và biên bản họp GVHD.
- Trong slide bảo vệ có một trang **"Ai làm gì"** tóm tắt theo gói công việc.

---

## 7. Khi một người bận hoặc chậm

1. **Phát hiện sớm:** một đầu việc trễ quá 1 tuần so với kế hoạch thì phải báo trong buổi họp tuần.
2. **Hỗ trợ:** người còn lại hỗ trợ trong phạm vi các việc có vai trò C, nhờ hợp đồng giao diện và tài liệu.
3. **Cắt phạm vi:** theo thứ tự Could → Should ([02 §9](02-muc-tieu-yeu-cau.md#9-mức-độ-thành-công)), không để trễ mốc M3.
4. **Báo GVHD** nếu phải đổi phân công đáng kể.

---

## 8. Câu hỏi hội đồng có thể đặt ra

**Phần của Quang có phải chỉ là "phụ trợ"?**
Không. Phần của Quang gồm toàn bộ hạ tầng bên dưới (máy GPU thuê, cluster) và là thứ biến một bản cài đặt vLLM thành một **nền tảng vận hành được**: dựng lại được từ Git, có SLO, cảnh báo, runbook và quy trình khôi phục. Đây chiếm khoảng một nửa chương 4 của luận văn.

**Nếu hội đồng hỏi Quang về vLLM, hoặc hỏi Trình về cảnh báo thì sao?**
Nhờ quy tắc review chéo và kế hoạch học chéo, mỗi người đều nắm phần của người kia ở mức trình bày và giải thích được.
