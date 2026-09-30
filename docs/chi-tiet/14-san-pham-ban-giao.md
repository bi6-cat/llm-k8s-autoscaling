# 14. Sản phẩm bàn giao: tài liệu chuyên sâu

> Thuộc [Mục 14 của bản mô tả chính](../mo-ta-chi-tiet-do-an.md#14-sản-phẩm-bàn-giao) · [Danh mục tài liệu chuyên sâu](README.md)

**Tóm tắt nhanh**
- Có **6 sản phẩm**, mỗi sản phẩm đi kèm **tiêu chí nghiệm thu**.
- Cấu trúc repository chi tiết tới từng file chính; quy ước làm việc, các lệnh Makefile, CI, cách gắn phiên bản.
- Bộ dữ liệu có cấu trúc, metadata và giấy phép sử dụng; có hướng dẫn tái lập.
- Dàn ý luận văn và slide, kịch bản demo 5 phút, và checklist trước khi nộp.

---

## 1. Danh sách sản phẩm

| # | Sản phẩm | Tiêu chí nghiệm thu |
|---|---|---|
| P1 | **Git repository** (mã nguồn, IaC, manifest, công cụ) | Người khác làm theo README dựng được cluster laptop trong dưới 1 giờ; CI xanh; tag `v1.0` |
| P2 | **Bộ dữ liệu thí nghiệm** (thô và dẫn xuất) | Đủ các lượt hợp lệ của ma trận, cold start và hiệu chỉnh; có README dữ liệu và checksum |
| P3 | **Dashboard Grafana** (JSON) | Import được; hiển thị đúng với dữ liệu mẫu |
| P4 | **Hướng dẫn tái lập** | Từ `make up` tới biểu đồ C1 bằng các lệnh có sẵn |
| P5 | **Luận văn** | Đủ 6 chương; trả lời RQ1–RQ3; đúng quy định trình bày của trường |
| P6 | **Slide, demo, video** | 15–20 slide; demo 5 phút chạy trên cluster laptop; video dự phòng |

---

## 2. Cấu trúc repository

```text
llm-k8s-autoscaling/
├── README.md                      # giới thiệu, sơ đồ, quick start, liên kết tài liệu
├── Makefile                       # find, rent, burnin, bootstrap, prefetch, calibrate, run, backup, release, analysis
├── infra/
│   ├── provision/                 # script thuê/burn-in/huỷ VM (CLI vastai; dự phòng TensorDock API)
│   └── ansible/
│       ├── inventory/             # sinh từ thông tin instance vừa thuê
│       └── roles/                 # common, chrony, nvidia, k3s-server, k3s-agent, nvme, argocd-bootstrap
├── platform/                      # values Helm theo môi trường
│   ├── gpu-operator/values-{laptop,cloud}.yaml
│   ├── kube-prometheus-stack/values.yaml
│   ├── keda/values.yaml
│   └── argocd/{root-app.yaml, apps/}
├── serving/
│   ├── base/                      # deployment (không có replicas), service, podmonitor, prefetch job, prepull ds
│   └── overlays/{laptop,cloud}/
├── autoscaling/                   # S1.yaml, S4.yaml, A1.yaml … A4.yaml (runner tự áp)
├── observability/
│   ├── rules/vllm-rules.yaml      # recording rules
│   └── dashboards/*.json          # Serving, GPU, Autoscaling, Thí nghiệm
├── loadgen/                       # gói Python: schedule.py, prompts.py, client.py, cli.py, tests/
├── experiments/
│   ├── runner/                    # state machine, k8s watcher, exporter, checks, backup
│   ├── matrix-session-*.yaml
│   └── calibration.yaml
├── analysis/
│   ├── PLAN.md                    # kế hoạch phân tích đăng ký trước
│   ├── build_tables.py            # + tests/
│   ├── notebooks/00…05
│   └── figures/                   # hình xuất cho luận văn
├── runs/                          # (gitignore) dữ liệu thô, đồng bộ với object storage
└── docs/
    ├── mo-ta-chi-tiet-do-an.md    # bản mô tả chính
    ├── chi-tiet/                  # 15 tài liệu chuyên sâu (thư mục này)
    ├── diagrams/, images/         # mã sinh sơ đồ và ảnh
    ├── interfaces.md              # hợp đồng giao diện giữa hai người
    ├── adr/                       # nhật ký quyết định
    └── nhat-ky/                   # nhật ký tuần, phiên thí nghiệm, nhà cung cấp
```

### 2.1. Quy ước

- **Nhánh:** `main` luôn chạy được; phát triển trên `feat/*`, `fix/*`, `exp/*`; merge qua PR có review.
- **Commit:** tiếng Anh hoặc tiếng Việt thống nhất một kiểu, dạng `<phạm vi>: <mô tả>`, ví dụ `autoscaling: add A3 kv-cache trigger`.
- **Ghim phiên bản:** image theo digest; chart theo phiên bản; Python bằng lockfile; model theo revision.
- **Bí mật:** không commit token, khoá API hay kubeconfig; dùng `.env` (đã gitignore) hoặc SOPS.

### 2.2. Makefile

| Lệnh | Việc làm |
|---|---|
| `make laptop-up` | Cài k3s và các thành phần trên laptop (Ansible, inventory local) |
| `make find` / `make rent` / `make burnin` / `make release` | Tìm máy theo tiêu chí, thuê, burn-in, huỷ (`release` từ chối chạy nếu chưa backup xong) |
| `make bootstrap` | Ansible cấu hình máy, cài Argo CD, áp root-app |
| `make prefetch` | Tải model về NVMe, pre-pull image |
| `make calibrate` | Chạy hiệu chỉnh, sinh `calibration.json` |
| `make run MATRIX=…` | Chạy một khối theo file ma trận |
| `make backup` | Đồng bộ `runs/` lên object storage, kiểm tra checksum |
| `make analysis` | Tạo bảng dẫn xuất, chạy notebook, xuất hình |
| `make lint test` | Kiểm tra YAML, manifest, Python |

### 2.3. CI (GitHub Actions)

| Job | Kiểm tra |
|---|---|
| `yaml` | yamllint; kubeconform cho `serving/`, `autoscaling/` (kèm schema CRD của KEDA) |
| `helm` | `helm template` với các values trong `platform/` |
| `kustomize` | `kustomize build` cho từng overlay |
| `python` | ruff và pytest cho `loadgen/`, `experiments/runner/`, `analysis/` |
| `docs` | Kiểm tra link hỏng trong `docs/` |

### 2.4. Phiên bản và phát hành

- `v0.x` cho các mốc M1, M2; `v1.0` khi nộp luận văn (gắn với commit dùng để tạo mọi hình trong luận văn).
- Tuỳ chọn: lưu trữ bộ dữ liệu trên Zenodo để có DOI trích dẫn.

---

## 3. Bộ dữ liệu

```text
dataset/
├── README.md             # mô tả, lược đồ, cách trích dẫn, giấy phép
├── calibration/          # các lượt quét λ
├── coldstart/            # 5 lần × L0/L2
├── matrix/
│   └── runs/<run-id>/    # metadata.json, phases.json, requests.csv, metrics.parquet, events.jsonl, vllm-logs/, checks.json
├── derived/              # req.parquet, phase_metrics.parquet, run_metrics.parquet, cell_summary.parquet, coldstart.parquet
└── SHA256SUMS
```

- **Lược đồ:** xem [09 §7](09-chi-so-danh-gia.md#7-lược-đồ-dữ-liệu). Mỗi file có `schema_version`.
- **Kích thước ước tính:** khoảng 75 lượt × (vài MB CSV + vài chục MB Parquet), tổng khoảng 2–5 GB. Nén lại khi phát hành.
- **Giấy phép đề xuất:** CC BY 4.0 cho dữ liệu, Apache-2.0 hoặc MIT cho mã nguồn.
- **Không chứa dữ liệu cá nhân:** prompt hoàn toàn là dữ liệu tổng hợp.

---

## 4. Hướng dẫn tái lập (dàn ý README)

1. **Yêu cầu:** phần cứng (laptop NVIDIA, hoặc tài khoản cloud GPU), công cụ (vastai CLI, ansible, kubectl, helm, python, uv).
2. **Chạy nhanh trên laptop:** `make laptop-up`, rồi `make run MATRIX=experiments/matrix-mini.yaml`, rồi `make analysis`.
3. **Chạy đầy đủ trên máy thuê:** cấu hình `.env` (API key Vast.ai, R2), rồi lần lượt `make find rent burnin bootstrap prefetch calibrate`, sau đó `make run` cho 3 khối, `make backup`, `make release`.
4. **Chỉ tái tạo hình và bảng từ dữ liệu đã công bố:** tải `dataset/`, rồi `make analysis DATA=dataset/`.
5. **Phiên bản đã dùng:** bảng phiên bản kèm digest.
6. **Các lỗi thường gặp:** Argo CD và `replicas`, label `release` của PodMonitor, `/dev/shm`, label DCGM.

---

## 5. Luận văn

| Chương | Nội dung | Dựa trên | Số trang ước tính |
|---|---|---|---|
| 1. Giới thiệu | Bối cảnh, bài toán, RQ, đóng góp, cấu trúc | [01](01-dat-van-de.md), [02](02-muc-tieu-cau-hoi-nghien-cuu.md) | 6–8 |
| 2. Cơ sở lý thuyết | LLM inference, vLLM, autoscaling K8s, GPU trên K8s, nghiên cứu liên quan | [04](04-kien-thuc-nen.md) | 15–20 |
| 3. Thiết kế hệ thống | Kiến trúc, chiến lược autoscaling, giám sát, cold start | [05](05-kien-truc-he-thong.md), [07](07-chien-luoc-autoscaling.md) | 12–15 |
| 4. Triển khai | Môi trường hai tầng, IaC/GitOps, máy tạo tải, runner, pipeline dữ liệu | [06](06-moi-truong-chi-phi.md), [08 §7, §9](08-thiet-ke-thi-nghiem.md) | 10–12 |
| 5. Thí nghiệm và đánh giá | Phương pháp, hiệu chỉnh, RQ1–RQ3, khuyến nghị, tính hợp lệ | [08](08-thiet-ke-thi-nghiem.md), [09](09-chi-so-danh-gia.md), [10](10-phan-tich-ket-qua.md), [03](03-pham-vi-gia-dinh.md) | 18–25 |
| 6. Kết luận | Tổng kết, hạn chế, hướng phát triển | [15](15-huong-mo-rong.md) | 3–5 |
| Phụ lục | Manifest chính, bảng phiên bản, bảng số liệu đầy đủ, hướng dẫn tái lập | – | tuỳ |

**Danh mục hình đề xuất cho luận văn:** Hình 1–16 của bộ tài liệu này (thay bản minh hoạ bằng số liệu thật ở Hình 5 và 15), cộng thêm các biểu đồ kết quả C1–C8.

---

## 6. Slide bảo vệ (15–20 trang) và demo

| # | Slide | Thời gian |
|---|---|---|
| 1 | Tên đề tài, nhóm | 0:30 |
| 2–3 | Bài toán: trade-off (Hình 1), vì sao khó (Hình 10, 12) | 2:00 |
| 4 | RQ1–RQ3 | 1:00 |
| 5–6 | Kiến trúc (Hình 2), vòng lặp autoscaling (Hình 4) | 2:00 |
| 7 | Các chiến lược A1–A3 và lý do (Hình 14, định luật Little) | 1:30 |
| 8–9 | Thiết kế thí nghiệm: kịch bản (Hình 7), ma trận, tính công bằng | 1:30 |
| 10–13 | Kết quả RQ1, RQ2, RQ3 (C1, C5, C6) | 4:00 |
| 14 | Khuyến nghị | 1:00 |
| 15 | Hạn chế, hướng phát triển | 1:00 |
| 16 | Ai làm gì | 0:30 |
| – | **Demo trực tiếp** | 5:00 |

**Kịch bản demo (5 phút, trên cluster laptop):**
1. Mở dashboard Autoscaling (1 replica, không có tải).
2. Chạy `loadgen --profile KB2-mini`. Tải tăng, hàng đợi tăng, desired tăng lên 2–3; chỉ vào pod đang khởi động (pha cold start).
3. Pod mới Ready, TTFT p95 giảm trở lại dưới ngưỡng.
4. Dừng tải. Giải thích cửa sổ ổn định; tua nhanh bằng dashboard của một lần chạy đã ghi sẵn.
5. Mở notebook với biểu đồ C1 của đúng lượt vừa chạy.

**Dự phòng:** video quay sẵn các bước trên, cùng ảnh chụp dashboard.

---

## 7. Checklist trước khi nộp

- [ ] Mọi số liệu trong luận văn đều truy được về `analysis/` và tag `v1.0`.
- [ ] Hình minh hoạ (Hình 5, 15) đã được thay bằng số đo thật, hoặc ghi rõ là minh hoạ.
- [ ] Không còn TODO hay placeholder (`vX.Y.Z`, `<ten>`) trong repo công khai.
- [ ] Link trong tài liệu không hỏng (CI `docs`).
- [ ] Bộ dữ liệu có README, checksum và giấy phép.
- [ ] Đã xoá token và kubeconfig khỏi lịch sử Git (kiểm tra bằng `gitleaks`).
- [ ] Đã review chéo toàn bộ luận văn; đã kiểm tra chính tả.

---

## 8. Câu hỏi hội đồng có thể đặt ra

**Người khác có thực sự tái lập được không?**
Được. Toàn bộ hạ tầng và thí nghiệm được mô tả bằng code và dựng bằng vài lệnh `make`. Dữ liệu và notebook được công bố kèm phiên bản. Hội đồng có thể kiểm chứng ngay trên cluster laptop trong phần demo.
