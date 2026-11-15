# Quy ước code và thư mục

Áp dụng cho cả hai người và cho AI agent. Khi quy ước ở đây khác với code đang có, sửa code theo quy ước (hoặc sửa quy ước trong cùng PR, kèm lý do).
Đây là nguồn duy nhất về cấu trúc thư mục; tài liệu khác chỉ link tới đây.

## 1. Thư mục

Repo chia theo hai câu hỏi: **chạy ở đâu** (`envs/<env>/`, mỗi môi trường một thư mục, có README hướng dẫn chạy) và **chạy cái gì** (`common/`, manifest và cấu hình giống nhau ở mọi môi trường). Thư mục môi trường chỉ chứa phần khác biệt, chồng lên `common/` bằng Kustomize overlay hoặc file values Helm thứ hai.

```text
llm-k8s-autoscaling/
├── README.md                     # bắt đầu từ đây: dự án là gì, chạy ở đâu
├── AGENTS.md, CLAUDE.md          # quy tắc cho AI agent (gồm ghi nhật ký)
├── Makefile                      # mọi thao tác: `make help` (chia nhóm theo môi trường)
├── envs/                         # ── CHẠY Ở ĐÂU ──
│   ├── home/                     # PC RTX 5060 8 GB, k3s + Argo CD: demo ở nhà
│   │   ├── README.md             # dựng và chạy demo ở nhà
│   │   ├── argocd/               # root-app.yaml, project-default.yaml, apps/<thành phần>.yaml
│   │   ├── serving/              # overlay vLLM: model 0,5B, 2 GPU replica time-slicing, Ingress
│   │   ├── platform/             # values Helm riêng của nhà (device plugin, kube-prometheus-stack)
│   │   └── experiments/          # ma trận và capacity đo ở nhà
│   ├── cloud/                    # VM Vast.ai 4 × RTX A4000 16 GB: phiên đánh giá V2
│   │   ├── README.md             # thuê, dựng, chạy V2, trả máy
│   │   ├── provision/            # vast.sh, probe.sh, install-platform.sh, vh5.sh, llm-runner.service;
│   │   │                         #   CHỈ nơi này phụ thuộc nhà cung cấp
│   │   ├── serving/              # overlay vLLM: model 3B, QoS Guaranteed, cache NVMe
│   │   ├── platform/             # values kube-prometheus-stack riêng của cloud (nhãn env=cloud cho cảnh báo)
│   │   └── experiments/          # matrix-v2.yaml (V2), matrix-dg1.yaml (ĐG1), matrix-v1.yaml (V1, lưu lại)
│   └── sim/                      # kind + llm-d-inference-sim trên laptop, không cần GPU
│       ├── README.md
│       ├── kind-config.yaml
│       ├── serving/, autoscaling/  # overlay simulator, A2 với ngưỡng của simulator
│       ├── platform/             # values kube-prometheus-stack nhẹ cho kind
│       ├── tests/                # T1–T5: run-t1-t5.sh, load-sim.sh
│       └── experiments/          # matrix.yaml
├── common/                       # ── CHẠY CÁI GÌ (dùng chung) ──
│   ├── serving/                  # Deployment vLLM, Service, PodMonitor (Kustomize base)
│   ├── autoscaling/
│   │   ├── a2/                   # A2 chính thức (KEDA ScaledObject theo số request đang chạy)
│   │   ├── eval/<ID>.yaml        # cấu hình chỉ dùng khi đánh giá: A1, A3, A4 (runner áp)
│   │   └── tests/                # NetworkPolicy chặn KEDA → Prometheus (T4, VH4)
│   ├── observability/            # rules/, alerts/{,tests/}, dashboards/
│   └── platform/                 # values Helm chung, gpu-exporter/, kube-prometheus-stack-extras/
├── ansible/                      # dựng k3s từ máy trắng: site.yml, inventory/, roles/ (dùng cho home và cloud)
├── loadgen/                      # gói Python: máy tạo tải
├── experiments/                  # gói Python: runner/ (chạy ma trận), ops/ (kịch bản VH2–VH4), tests/
├── runs/                         # (gitignore) dữ liệu thô của các lượt chạy
└── docs/
    ├── mo-ta-chi-tiet-do-an.md   # bản mô tả tổng; chi-tiet/ là thiết kế chi tiết
    ├── bao-cao/                  # báo cáo kỹ thuật HTML cho người không trực tiếp làm
    ├── huong-dan/                # hướng dẫn theo tuần (W1, W2: tư liệu, đường dẫn cũ)
    ├── adr/NNN-<ten>.md          # quyết định kiến trúc
    ├── runbooks/<TênCảnhBáo>.md  # mỗi cảnh báo một file
    ├── nhat-ky/                  # tuan-XX.md (họp), van-hanh.md, lam-viec/<người>/ (cá nhân)
    └── phien-ban.md              # bảng ghim phiên bản duy nhất
```

Cấu trúc này có từ 12/11/2026. Trước đó repo chia theo thành phần (`serving/overlays/<env>`, `platform/`, `infra/`…); nhật ký, ADR và hướng dẫn W1, W2 viết trước ngày đó vẫn dùng đường dẫn cũ và được giữ nguyên.

**Đặt file mới ở đâu**

| Loại | Chỗ đặt |
|---|---|
| Manifest giống nhau ở mọi môi trường | `common/<thành phần>/` (Kustomize base) |
| Phần khác biệt của một môi trường | `envs/<env>/<thành phần>/` (overlay trỏ về `../../../common/<thành phần>`, chỉ chứa patch) |
| Thành phần nền cài bằng Helm | values chung `common/platform/<tên>-values.yaml`, values riêng `envs/<env>/platform/<tên>-values.yaml`, và (ở nhà) một Application trong `envs/home/argocd/apps/` |
| Cấu hình chỉ dùng khi đánh giá | `common/autoscaling/eval/` hoặc `envs/<env>/experiments/` (không để Argo CD quản lý) |
| Script vận hành một lần | `experiments/ops/` (kịch bản VH) hoặc `envs/cloud/provision/` (máy thuê); gọi qua `make` |
| Hình cho luận văn | `docs/images/` (sinh từ `docs/diagrams/`) |

Môi trường (`<env>`) chỉ có ba giá trị: `home` (PC ở nhà), `cloud` (VM thuê), `sim` (kind + simulator).
Tên file và thư mục: chữ thường, nối bằng `-`, không dấu (`scaledobject-a2.yaml`). Ngoại lệ: runbook đặt đúng tên cảnh báo; module Python dùng `_`; cấu hình đánh giá đặt theo mã (`A1.yaml`).

## 2. Quy tắc chung

- **Header ở đầu mỗi file** (trừ JSON, file sinh tự động và `__init__.py` rỗng chỉ để đánh dấu package). Viết bằng ký tự comment của ngôn ngữ đó:

  ```yaml
  # ──────────────────────────────────────────────────────────────────────────────
  # <đường dẫn từ gốc repo>                                      (DEMO – hoàn thiện ở Wx)
  # Khái niệm: <thứ này là gì, một hai câu cho người chưa biết>
  # Mục đích:  <vì sao có file này, điểm then chốt>
  # Tham khảo: <tài liệu §mục>
  # ──────────────────────────────────────────────────────────────────────────────
  ```

  Nhãn `(DEMO – …)` chỉ dùng khi file chưa xong, và phải gỡ khi đã xong. Python dùng docstring của module với các mục `Khái niệm` và `Mục đích` thay cho khối này.
- **Ngôn ngữ:** comment và tài liệu bằng tiếng Việt. Tên biến, hàm, resource, metric và nhãn bằng tiếng Anh.
- **Comment theo kiểu "vừa học vừa làm".** Cả nhóm đang học Kubernetes, vLLM, Argo CD và Prometheus, nên code phải đọc hiểu được mà không cần mở tài liệu ngoài:
  - **Thuật ngữ mới:** giải thích ngắn ở lần đầu xuất hiện trong file, ví dụ `# HPA (Horizontal Pod Autoscaler) = bộ điều khiển tăng/giảm số pod theo metric`.
  - **Mỗi khối logic** (task Ansible, mục trong manifest, hàm, đoạn bash) có comment nói nó làm gì và **vì sao cần**.
  - **Tham số, flag, con số không hiển nhiên:** comment cùng dòng nói ý nghĩa và lý do chọn giá trị đó, dẫn nguồn thiết kế nếu có, ví dụ `terminationGracePeriodSeconds: 180  # > preStop 20 s + shutdown-timeout 150 s (Vận hành §5)`.
  - **PromQL, regex, jq, lệnh bash dài:** giải nghĩa từng phần.
  - **Cái bẫy đã gặp:** ghi lại ngay tại chỗ (`# Lưu ý: thiếu label release thì Prometheus không thấy PodMonitor`).
  - Không viết comment thừa kiểu `i += 1  # tăng i`. Sửa code thì sửa comment theo; comment sai còn tệ hơn không có comment.
- **Ghim phiên bản:** image theo digest, chart theo version, model theo revision, Python bằng lockfile. Mỗi lần đổi phiên bản phải sửa cả `docs/phien-ban.md` trong cùng PR.
- **Bí mật:** không bao giờ commit. Giá trị cục bộ để trong `.env` (mẫu ở `.env.example`, đã gitignore); Secret tạo tay từ đó. Sealed Secrets đã lược (ADR-006 §3.1).
- Không sửa tay trên cluster những thứ Argo CD quản lý. Mọi thay đổi đi qua Git; selfHeal sẽ ghi đè thay đổi sửa tay.

## 3. YAML và Kubernetes

- Đuôi `.yaml`. Ngoại lệ: Ansible dùng `.yml`, theo quy ước của Ansible. Thụt lề 2 dấu cách; phải qua `yamllint` (`.yamllint.yaml`).
- Map ngắn được viết một dòng: `labels: {app: vllm}`.
- Namespace: `llm-serving` (vLLM và ScaledObject), `monitoring`, `keda`, `argocd`, `gpu`.
- Nhãn chung: `app: <tên>`. Ví dụ Deployment vLLM tên `vllm`, nhãn `app: vllm`.
- **Deployment không có `replicas`**, để HPA của KEDA quản lý mà không tranh với Argo CD.
- Image khai báo không kèm tag trong manifest; tag và digest ghim ở `images:` của `kustomization.yaml`.
- ScaledObject đặt tên `vllm-<id>` (`vllm-a2`). Mỗi cấu hình đánh giá là một file `common/autoscaling/eval/<ID>.yaml`, trừ A2 (runner dùng thẳng `common/autoscaling/a2`) và S1, S4 (không có ScaledObject).
- Overlay chỉ chứa phần khác biệt (patch). Thứ gì giống nhau ở mọi môi trường thì đưa lên `common/`.

## 4. Prometheus, cảnh báo, dashboard

- Recording rule đặt tên theo dạng `level:metric:operation`, ví dụ `llm:ttft_bad_ratio:rate5m`.
- Cảnh báo đặt tên PascalCase có tiền tố (`LLM…`, `Keda…`). Bắt buộc có nhãn `severity: page|ticket` và annotation `runbook_url`.
- Mỗi cảnh báo bắt buộc có **ba thứ trong cùng PR**: quy tắc trong `common/observability/alerts/`, unit test trong `alerts/tests/` (`promtool test rules`) và runbook `docs/runbooks/<TênCảnhBáo>.md` theo mẫu ở [Vận hành §4.2](docs/chi-tiet/04-van-hanh.md#42-ví-dụ-llmsloburnfast).
- ScaledObject dùng biểu thức PromQL gốc, không dùng recording rule, vì recording rule thêm một chu kỳ trễ.
- Dashboard lưu ở dạng JSON đã export, bỏ `id` và đặt `uid` cố định.

## 5. Python

- Python ≥ 3.11. Mỗi gói (`loadgen/`, `experiments/`, `analysis/`) có `pyproject.toml` riêng và ghim phụ thuộc bằng `uv.lock`.
- Format và lint bằng `ruff` (line-length 110). Test bằng `pytest` trong thư mục `tests/` cạnh code.
- Dùng type hint, và `from __future__ import annotations` ở đầu module.
- Logic mà pipeline dùng phải nằm trong `.py` có test, không nằm trong notebook. Notebook chỉ để khám phá dữ liệu.
- Kết quả phải tái lập được: mọi thứ ngẫu nhiên nhận `seed` làm tham số.

## 6. Shell, Ansible, Makefile

- **Shell:** `#!/usr/bin/env bash` + `set -euo pipefail`; `cd` về gốc repo ở đầu script; nhận tham số dạng lệnh con (`vast.sh rent …`).
- **Ansible:** module ghi tên đầy đủ (`ansible.builtin.apt`), `name:` của task viết tiếng Việt, task phải idempotent (chạy lại không đổi gì). `command`/`shell` phải có `changed_when` hoặc `creates`.
- **Comment cuối dòng không phải chỗ nào cũng được:** `.gitignore` không có comment cuối dòng (`abc  # x` bị hiểu là một mẫu), và trong Makefile `X := a  # c` làm biến dính dấu cách. Ở hai loại file này, comment luôn nằm trên dòng riêng.
- **Makefile:** mỗi target có comment `## mô tả` để hiện trong `make help`. Lệnh chưa làm vẫn khai báo, in "chưa làm" rồi `exit 1`. Biến dài (phiên bản, tên cluster) đặt ở đầu file.

## 7. Git và PR

- **Nhánh:** `main` luôn chạy được, vì Argo CD đọc từ đó. Mọi việc làm trên `feat/<chủ-đề>`, `fix/<chủ-đề>` hoặc `docs/<chủ-đề>`, ví dụ `feat/alerts-telegram`.
- **Commit:** tiếng Anh, thể mệnh lệnh, dạng `<phạm vi>: <mô tả>`. Phạm vi là thư mục cấp một hoặc thành phần (`serving`, `alerts`, `loadgen`, `ansible`, `docs`, `ci`). Ví dụ: `alerts: add LLMPodPending with runbook`.
- **PR:** nhỏ (lý tưởng dưới 400 dòng, không tính file sinh tự động) và giải quyết đúng một việc. Mô tả PR dùng các nhãn **Task** (Q1…, TR1…, xem [Kế hoạch §5.1](docs/chi-tiet/06-ke-hoach-quan-ly.md#51-phân-công)), **Environment**, **Tested** (đã kiểm thế nào, kết quả) và **Base** (với PR xếp chồng). Người review là **người còn lại**: từ W3 cần 1 approval, trả lời trong 48 giờ.
- **Trước khi mở PR**, chạy:
  - `make lint` (yamllint, kustomize build, ansible syntax-check);
  - `pytest` và `ruff check` với gói Python đã sửa;
  - `promtool check rules` và `promtool test rules` nếu có sửa `common/observability/`.
- **Nhật ký:** PR nào cũng kèm mục nhật ký cá nhân tương ứng ([AGENTS.md](AGENTS.md)).
