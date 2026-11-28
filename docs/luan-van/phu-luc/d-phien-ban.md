<!-- Mục đích: Phụ lục D, bảng phiên bản đã ghim của mọi thành phần mà thân bài dựa vào (mục 1.2, 4.1, 5.1 dẫn "Phụ lục D"). Người viết: Trình. -->
<!-- Chép từ docs/phien-ban.md trên main (commit 03ce930, 18/11/2026). Bỏ: dòng laptop (driver, Container Toolkit chưa điền, laptop không dùng cho số đo), model nhà trước 06/11 (chỉ dùng cho LT1–LT3 ở nhà, thân bài không dẫn), vastai CLI, schema CRD, GitHub Actions và tham chiếu "Dùng ở" (đường dẫn trong repo, người đọc tra ở phien-ban.md). Rút gọn digest như trong phien-ban.md. Sửa phien-ban.md thì cập nhật bảng ở đây. -->

# Phụ lục D. Phiên bản thành phần {.unnumbered}

Mọi thành phần của hệ thống được ghim theo phiên bản cụ thể, image container ghim thêm digest, model ghim theo commit của kho trên Hugging Face. Nhờ vậy cấu hình đã đo có thể dựng lại đúng như cũ, đúng yêu cầu N8 (Bảng 3.1). Bảng phiên bản gốc nằm ở `docs/phien-ban.md` của repository (commit `03ce930`), cũng là nơi duy nhất được sửa khi đổi phiên bản. Hai bảng dưới chép lại các dòng mà thân bài dựa vào. Phần lớn phiên bản được tra ngày 09/10/2026, các công cụ của CI tra ngày 01/11/2026, còn model và vài công cụ thêm sau được tra khi đưa vào.
<!-- nguồn: docs/phien-ban.md (dòng mở đầu: tra 09/10/2026, CI 01/11/2026; model tra 06/11, amtool tra 15/11; "Đổi phiên bản: sửa ở đây và ở file dùng nó trong cùng một PR"), commit 03ce930; 00-thong-so.md §4 (N8) -->

## D.1. Nền tảng và tầng phục vụ

**Bảng D.1.** Phiên bản các thành phần chạy trên cluster

| Thành phần | Phiên bản | Ghi chú |
|---|---|---|
| Ubuntu (máy nhà) | 26.04.1 LTS | Bản desktop |
| NVIDIA driver (máy nhà) | `595.99.02` (open) | Image vLLM CUDA 13 cần driver từ 580 trở lên |
| NVIDIA Container Toolkit (máy nhà) | `1.20.1` | |
| k3s | `v1.36.5+k3s1` | Kênh stable |
| Argo CD | `v3.5.4` | Bản core |
| kube-prometheus-stack (Helm chart) | `92.1.1` | Kèm chart con kube-state-metrics `8.6.0` (kube-state-metrics `v2.20.0`) |
| KEDA (Helm chart) | `2.21.0` | |
| NVIDIA device plugin (Helm chart) | `0.20.1` | Ở nhà chia GPU thành 2 GPU replica bằng time-slicing (từ 06/11) |
| nvidia_gpu_exporter | `1.15.1` | |
| vLLM | `vllm/vllm-openai:v0.31.0@sha256:c1c9f6fd…c3` | CUDA 13.0. Bản `-cu129` hỏng lúc khởi động nên không dùng |
| Model ở nhà | `Qwen/Qwen2.5-0.5B-Instruct@7ae55760…` | Từ 06/11 |
| Model trên VM thuê (V2) | `Qwen/Qwen2.5-3B-Instruct@aa8e7253…` | Chốt cho V2 ngày 08/11 |
| llm-d-inference-sim | `ghcr.io/llm-d/llm-d-inference-sim:v0.12.0@sha256:c6838d86…60` | Simulator thay vLLM trên kind |
| kind, node image | `v0.33.0`, `kindest/node:v1.37.0@sha256:a1ed56cf…0ae5` | Máy simulator |
| Helm, kubectl (máy simulator) | `v4.3.1`, `v1.36.5` | kubectl trùng bản của CI |
| Helm, uv, huggingface_hub, rclone (VM thuê) | `v3.19.0`, `0.13.7`, `2.4.0`, `v1.71.2` | Cài bởi script dựng nền tảng trên VM |
<!-- nguồn: docs/phien-ban.md các dòng Ubuntu, NVIDIA driver, NVIDIA Container Toolkit, k3s, Argo CD, kube-prometheus-stack, KEDA, NVIDIA device plugin, nvidia_gpu_exporter, vLLM (ADR-004 §7 cho -cu129), Model nhà, Model cloud (V2), llm-d-inference-sim, kind / node image, Helm, kubectl (máy simulator), Helm, uv, huggingface_hub, rclone (VM thuê); commit đầy đủ của model: 7ae557604adf67be50417f59c2c2f167def9a775 và aa8e72537993ba99e69dfaafa59ed015b17504d1 -->

## D.2. Công cụ kiểm tra và dựng tài liệu

**Bảng D.2.** Phiên bản công cụ dùng trong CI và trên máy cá nhân

| Công cụ | Phiên bản | Dùng để |
|---|---|---|
| kubeconform | `v0.8.0` | Kiểm manifest theo schema |
| kubectl (CI) | `v1.36.5` | Dựng manifest bằng Kustomize, trùng bản k3s |
| promtool | `3.15.0` | Unit test quy tắc cảnh báo, trùng Prometheus của chart 92.1.1 |
| amtool | `0.34.1` | Kiểm cấu hình Alertmanager, trùng Alertmanager của chart 92.1.1 |
| yq (bản của mikefarah) | `v4.54.1` | Kiểm mọi cảnh báo đều có test |
| yamllint | `1.38.0` | Kiểm cú pháp YAML |
| actionlint, shellcheck | `1.7.12`, `0.11.0` | Kiểm workflow của CI và script shell |
| lychee | `0.24.2` | Kiểm link trong tài liệu |
| uv, Python | `0.13.1`; Python `3.11` và `3.15` | Chạy test của máy tạo tải |
| pandoc | `3.13` | Ghép luận văn từ Markdown ra `.docx`, không chạy trong CI |
<!-- nguồn: docs/phien-ban.md các dòng kubeconform (CI), kubectl (CI), promtool (CI), amtool, yq, yamllint (CI), actionlint/shellcheck/lychee (CI), uv/Python (CI cho loadgen/), pandoc; Makefile alerts-coverage (yq) -->
