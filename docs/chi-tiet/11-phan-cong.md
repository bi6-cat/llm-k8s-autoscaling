# 11. Phân công công việc: tài liệu chuyên sâu

> Thuộc [Mục 11 của bản mô tả chính](../mo-ta-chi-tiet-do-an.md#11-phân-công-công-việc) · [Danh mục tài liệu chuyên sâu](README.md)

**Tóm tắt nhanh**
- Phân công theo **chuyên môn**, mỗi phần có **một người chịu trách nhiệm chính**, nhưng mọi thay đổi đều được **người còn lại review**.
- Bảng RACI chi tiết tới từng đầu việc, chia thành 10 gói công việc.
- Có **"hợp đồng giao diện"** giữa hai người: metric, cấu hình, dữ liệu, runner. Nhờ đó hai người làm song song mà không chờ nhau.
- Quy trình làm việc, học chéo, chia chương luận văn, minh chứng đóng góp cá nhân, và cách xử lý khi một người bận.

---

## 1. Nguyên tắc

1. **Đúng sở trường:** Trình (Platform) phụ trách tầng GPU, Kubernetes, vLLM và autoscaling. Quang (DevOps/SRE) phụ trách tự động hoá, giám sát, sinh tải, thí nghiệm và dữ liệu.
2. **Một đầu việc, một người chịu trách nhiệm.** Tránh tình trạng "cả hai cùng làm nên không ai làm".
3. **Luôn có người review:** mọi PR đều có người kia duyệt. Nhờ vậy cả hai hiểu toàn hệ thống, và khi bảo vệ ai cũng trả lời được mọi câu hỏi.
4. **Đóng góp nhìn thấy được:** mỗi người có sản phẩm riêng rõ ràng trong repo, và có chương luận văn riêng.

---

## 2. Bảng RACI

R = làm chính · A = chịu trách nhiệm cuối (duyệt) · C = được hỏi ý kiến · I = được thông báo. Mỗi đầu việc có đúng một A.

| Gói | Đầu việc | Trình | Quang |
|---|---|---|---|
| **WP1 Hạ tầng GPU và K8s** | Cài k3s trên laptop, join nhiều node | R/A | C |
| | Driver, container toolkit, device plugin / GPU Operator | R/A | I |
| | Chỉnh chu kỳ sync HPA; nhãn node, `nodeSelector` | R/A | C |
| | Ansible hoá các bước trên | C | R/A |
| **WP2 IaC và GitOps** | Script thuê, burn-in, huỷ VM (CLI `vastai`) | C | R/A |
| | Cấu trúc repo, Kustomize base/overlay | C | R/A |
| | Argo CD App-of-Apps; `ignoreDifferences` | C | R/A |
| | Makefile (`up/bootstrap/run/backup/down`) | I | R/A |
| **WP3 vLLM serving** | Deployment, tham số, probe, preStop, grace period | R/A | C |
| | Lưu trữ model (PVC, NVMe), Job prefetch, pre-pull | R/A | C |
| | Kiểm thử graceful shutdown | R/A | C |
| **WP4 Autoscaling** | ScaledObject A1–A4, `behavior`, fallback | R/A | C |
| | PromQL cho các trigger | R | A (review PromQL) |
| | Bài kiểm thử T1–T6 ([07 §8](07-chien-luoc-autoscaling.md#8-kiểm-thử-nhanh-cấu-hình-autoscaling)) | R/A | C |
| **WP5 Observability** | kube-prometheus-stack, PodMonitor, DCGM scrape 5 s | C | R/A |
| | Recording rule, 4 dashboard | C | R/A |
| | Annotation Grafana từ runner | I | R/A |
| **WP6 Tải và kịch bản** | Máy tạo tải open-loop (asyncio, SSE) | C | R/A |
| | Sinh prompt đúng số token; lịch Poisson không thuần nhất | C | R/A |
| | Kiểm chứng máy tạo tải (so với `vllm bench serve`) | C | R/A |
| **WP7 Experiment runner** | Máy trạng thái PREPARE → … → BACKUP | C | R/A |
| | Thu events và pod conditions; phân tích log vLLM | R (phần phân tích log vLLM) | A |
| | Bộ kiểm tra hợp lệ `checks.json` | C | R/A |
| **WP8 Hiệu chỉnh và cold start** | Quy trình hiệu chỉnh, chốt C/B\*/SLO | R/A | R (chạy tải) |
| | Thí nghiệm cold start L0/L2 | R/A | C |
| **WP9 Phân tích** | Bảng dẫn xuất, unit test | C | R/A |
| | Notebook hiệu chỉnh và cold start | R/A | C |
| | Notebook ma trận, biểu đồ C1–C8, thống kê | C | R/A |
| **WP10 Luận văn và bảo vệ** | Chương 2, 3 | R/A | C |
| | Chương 4 | C | R/A |
| | Chương 5 | R (5.2, 5.4) | R/A (5.1, 5.3, 5.5–5.8) |
| | Chương 1, 6; slide; demo | R | R (cùng làm; A: Quang cho slide, Trình cho demo) |

---

## 3. Hợp đồng giao diện giữa hai người

Được ghi vào `docs/interfaces.md` và chỉ thay đổi qua PR có người kia duyệt:

| Giao diện | Bên cung cấp → bên dùng | Nội dung cố định |
|---|---|---|
| **Metric** | Trình → Quang | Tên metric vLLM và DCGM (theo phiên bản đã ghim), label `namespace`, `pod`; tên recording rule |
| **Cấu hình** | Trình → Quang | Mỗi cấu hình là một file `autoscaling/<ID>.yaml` với ID ∈ {S1, S4, A1…A4}; tên ScaledObject `vllm-<id>`; cách pause/unpause |
| **Tham số model** | Trình → Quang | Tên `served-model-name`, `max-model-len`, tokenizer để sinh prompt |
| **Runner API** | Quang → Trình | `make run MATRIX=…`; runner đọc `calibration.json`; hook phân tích log vLLM là một hàm `parse_vllm_log(text) → dict` |
| **Dữ liệu** | Quang → cả hai | Lược đồ trong [09 §7](09-chi-so-danh-gia.md#7-lược-đồ-dữ-liệu); đổi lược đồ thì phải tăng phiên bản `schema_version` |

Nhờ hợp đồng này, Quang có thể viết runner với **simulator** trong khi Trình hoàn thiện vLLM thật, và hai bên ghép lại ở tuần 7.

---

## 4. Quy trình làm việc

| Hoạt động | Nhịp | Công cụ | Kết quả |
|---|---|---|---|
| Quản lý việc | Liên tục | GitHub Projects: Todo / Doing / Review / Done; mỗi đầu việc là một issue | Tiến độ nhìn thấy được |
| Nhánh và PR | Mỗi thay đổi | Nhánh `feat/…`, `fix/…`; PR nhỏ; **review trong 48 giờ** | Lịch sử rõ ràng |
| CI | Mỗi PR | yamllint, kubeconform, `helm template`, ruff và pytest (loadgen, runner, bảng dẫn xuất) | Không merge khi CI đỏ |
| Họp nhóm | Hằng tuần, 30 phút | Tuần trước làm gì, tuần này làm gì, đang vướng gì | Ghi chú trong `docs/nhat-ky/tuan-XX.md` |
| Họp GVHD | 2 tuần một lần | Báo cáo theo mốc, demo nhanh | Biên bản, việc cần làm |
| Nhật ký quyết định | Khi có quyết định lớn | `docs/adr/NNN-<ten>.md` (ngữ cảnh, quyết định, hệ quả) | Giải thích được mọi lựa chọn khi bảo vệ |

---

## 5. Học chéo

| Người | Cần nắm thêm | Cách học |
|---|---|---|
| Quang | vLLM (prefill, decode, KV-cache, tham số), GPU trên K8s, HPA/KEDA | Đọc [04](04-kien-thuc-nen.md); review toàn bộ PR của WP3 và WP4; tự dựng lại cluster laptop một lần |
| Trình | Prometheus/PromQL, máy tạo tải open-loop, thống kê cơ bản | Đọc [08](08-thiet-ke-thi-nghiem.md), [09](09-chi-so-danh-gia.md); viết một dashboard; chạy runner một khối mini |

**Tiêu chí:** trước tuần 14, **mỗi người tự demo được toàn hệ thống**, từ `make up` tới biểu đồ C1.

---

## 6. Minh chứng đóng góp cá nhân

- Lịch sử commit và PR (ai viết, ai review), cùng issue được gán.
- Chương luận văn theo bảng RACI.
- Nhật ký tuần và biên bản họp GVHD.
- Trong slide bảo vệ có một trang **"Ai làm gì"** tóm tắt theo gói công việc.

---

## 7. Khi một người bận hoặc chậm

1. **Phát hiện sớm:** một đầu việc trễ quá 1 tuần so với kế hoạch thì phải báo trong buổi họp tuần.
2. **Hỗ trợ:** người còn lại hỗ trợ trong phạm vi các việc có vai trò C, nhờ hợp đồng giao diện và tài liệu.
3. **Cắt phạm vi:** theo thứ tự Could → Should ([02 §7](02-muc-tieu-cau-hoi-nghien-cuu.md#7-mức-độ-thành-công)), không để trễ mốc M3.
4. **Báo GVHD** nếu phải đổi phân công đáng kể.

---

## 8. Câu hỏi hội đồng có thể đặt ra

**Phần của Quang có phải chỉ là "phụ trợ"?**
Không. Máy tạo tải open-loop, experiment runner, pipeline dữ liệu và phân tích thống kê quyết định **độ tin cậy của mọi kết luận**. IaC và GitOps là thứ làm cho thí nghiệm **tái lập được** và **vừa ngân sách**.

**Nếu hội đồng hỏi Quang về vLLM, hoặc hỏi Trình về thống kê thì sao?**
Nhờ quy tắc review chéo và kế hoạch học chéo, mỗi người đều nắm phần của người kia ở mức trình bày và giải thích được.
