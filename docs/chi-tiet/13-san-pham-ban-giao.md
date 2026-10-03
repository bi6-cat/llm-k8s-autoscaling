# 13. Sản phẩm bàn giao: tài liệu chuyên sâu

> Thuộc [Mục 13 của bản mô tả chính](../mo-ta-chi-tiet-do-an.md#13-sản-phẩm-bàn-giao) · [Danh mục tài liệu chuyên sâu](README.md)

**Tóm tắt nhanh**
- Có **7 sản phẩm**, mỗi sản phẩm đi kèm **tiêu chí nghiệm thu**. Sản phẩm chính là **nền tảng trong Git** và **bộ vận hành** (dashboard, cảnh báo, runbook).
- Cấu trúc repository chi tiết tới từng thư mục chính; quy ước làm việc, các lệnh Makefile, CI, cách gắn phiên bản.
- Khung luận văn: **chương 4 "Triển khai và vận hành" là chương dài nhất**; chương 5 là phần đánh giá và bảng nghiệm thu.
- Slide, kịch bản demo 5 phút (autoscaling, cảnh báo, runbook) và checklist trước khi nộp.

---

## 1. Danh sách sản phẩm

| # | Sản phẩm | Tiêu chí nghiệm thu |
|---|---|---|
| P1 | **Git repository** (IaC, manifest, Helm values, cấu hình autoscaling) | Người khác làm theo README dựng được cluster laptop trong dưới 1 giờ; CI xanh; tag `v1.0` |
| P2 | **Bộ vận hành**: 5 dashboard Grafana (JSON), recording rule, quy tắc cảnh báo có unit test, cấu hình Alertmanager, runbook cho mọi cảnh báo | Import được; mỗi cảnh báo có runbook; `promtool test rules` xanh |
| P3 | **Công cụ đánh giá**: máy tạo tải open-loop, runner | Chạy lại được một lượt bằng một lệnh `make` |
| P4 | **Dữ liệu đánh giá** và **nhật ký vận hành** | Đủ các lượt hợp lệ; kết quả VH1–VH6; có README và checksum |
| P5 | **Hướng dẫn tái lập và vận hành** | Từ `make laptop-up` tới biểu đồ C1; quy trình cập nhật, rollback, dựng lại |
| P6 | **Luận văn** | Đủ 6 chương; có bảng nghiệm thu cho F1–F7, N1–N8; đúng quy định trình bày của trường |
| P7 | **Slide, demo, video** | 15–20 slide; demo 5 phút trên cluster laptop; video dự phòng |

---

## 2. Cấu trúc repository

```text
llm-k8s-autoscaling/
├── README.md                      # giới thiệu, sơ đồ, quick start, liên kết tài liệu
├── Makefile                       # laptop-up, find, rent, burnin, bootstrap, prefetch, capacity, run, ops-tests, backup, release, analysis
├── infra/
│   ├── provision/                 # script thuê/burn-in/huỷ VM (CLI vastai; dự phòng TensorDock API)
│   └── ansible/
│       ├── inventory/             # laptop (tĩnh) và VM thuê (sinh tự động)
│       └── roles/                 # common, chrony, nvidia, k3s-server, k3s-agent, nvme, firewall, argocd-bootstrap
├── platform/                      # values Helm theo môi trường, quản lý bởi Argo CD
│   ├── gpu-operator/values-{laptop,cloud}.yaml
│   ├── kube-prometheus-stack/values.yaml       # gồm cấu hình Alertmanager
│   ├── keda/values.yaml
│   ├── sealed-secrets/
│   └── argocd/{root-app.yaml, apps/}
├── serving/
│   ├── base/                      # deployment (không có replicas), service, podmonitor, middleware Traefik, networkpolicy, prefetch job, prepull ds
│   └── overlays/{laptop,cloud}/
├── autoscaling/                   # A2.yaml (chính thức, Argo CD quản lý); S1, S4, A1, A3, A4 dùng khi đánh giá
├── observability/
│   ├── rules/                     # recording rule cho SLI
│   ├── alerts/                    # quy tắc cảnh báo + tests/ cho promtool
│   └── dashboards/*.json          # Serving, GPU, Autoscaling, SLO và chi phí, Đánh giá
├── loadgen/                       # gói Python: schedule.py, prompts.py, client.py, cli.py, tests/
├── experiments/
│   ├── runner/                    # áp cấu hình, reset, chạy, thu thập, sao lưu
│   ├── ops/                       # script cho VH2–VH4, VH6
│   ├── matrix.yaml
│   └── capacity.yaml
├── analysis/
│   ├── build_tables.py            # + tests/
│   ├── notebooks/
│   └── figures/                   # hình xuất cho luận văn
├── runs/                          # (gitignore) dữ liệu thô, đồng bộ với object storage
└── docs/
    ├── mo-ta-chi-tiet-do-an.md    # bản mô tả chính
    ├── chi-tiet/                  # 14 tài liệu chuyên sâu (thư mục này)
    ├── runbooks/                  # một file cho mỗi cảnh báo
    ├── diagrams/, images/         # mã sinh sơ đồ và ảnh
    ├── interfaces.md              # hợp đồng giao diện giữa hai người
    ├── adr/                       # nhật ký quyết định
    └── nhat-ky/                   # nhật ký tuần, nhật ký vận hành, đợt thuê
```

### 2.1. Quy ước

- **Nhánh:** `main` luôn chạy được; phát triển trên `feat/*`, `fix/*`; merge qua PR có review.
- **Commit:** tiếng Anh hoặc tiếng Việt thống nhất một kiểu, dạng `<phạm vi>: <mô tả>`, ví dụ `alerts: add LLMPodPending`.
- **Ghim phiên bản:** image theo digest; chart theo phiên bản; Python bằng lockfile; model theo revision.
- **Bí mật:** không có bí mật dạng rõ trong Git; dùng Sealed Secrets. Khoá riêng của controller được sao lưu ngoài Git ([08 §7](08-van-hanh.md#7-dựng-lại-từ-đầu-khôi-phục-sau-thảm-hoạ)).

### 2.2. Makefile

| Lệnh | Việc làm |
|---|---|
| `make laptop-up` | Dựng k3s và toàn bộ nền tảng trên cluster laptop (Ansible + Argo CD) |
| `make find` / `make rent` / `make burnin` / `make release` | Tìm máy theo tiêu chí, thuê, burn-in, huỷ (`release` từ chối chạy nếu chưa sao lưu xong) |
| `make bootstrap` | Ansible cấu hình máy, cài Argo CD, nạp khoá Sealed Secrets, áp root-app; in thời gian từng bước |
| `make prefetch` | Tải model về NVMe, pre-pull image |
| `make capacity` | Đo năng lực, sinh `capacity.json` |
| `make run MATRIX=…` | Chạy ma trận đánh giá |
| `make ops-tests` | Chạy các kịch bản vận hành tự động hoá được |
| `make backup` | Đồng bộ `runs/` lên object storage, kiểm tra checksum |
| `make analysis` | Tạo bảng, chạy notebook, xuất hình |
| `make lint test` | Kiểm tra YAML, manifest, quy tắc cảnh báo, Python |

### 2.3. CI (GitHub Actions)

| Job | Kiểm tra |
|---|---|
| `yaml` | yamllint; kubeconform cho `serving/`, `autoscaling/` (kèm schema CRD của KEDA, Traefik) |
| `helm` | `helm template` với các values trong `platform/` |
| `kustomize` | `kustomize build` cho từng overlay |
| `alerts` | `promtool check rules` và `promtool test rules` cho `observability/` |
| `python` | ruff và pytest cho `loadgen/`, `experiments/runner/`, `analysis/` |
| `docs` | Kiểm tra link hỏng trong `docs/`; mọi cảnh báo đều có file runbook tương ứng |
| `secrets` | `gitleaks` |

### 2.4. Phiên bản và phát hành

- `v0.x` cho các mốc M1, M2; `v1.0` khi nộp luận văn (gắn với commit dùng để tạo mọi hình trong luận văn).

---

## 3. Dữ liệu đánh giá và nhật ký vận hành

```text
dataset/
├── README.md             # mô tả, cấu trúc, cách dùng, giấy phép
├── capacity/             # các mức tải khi đo năng lực
├── coldstart/            # 3 lần × L0/L2
├── matrix/runs/<run-id>/ # metadata.json, requests.csv, metrics.parquet, events.jsonl, alerts.jsonl, checks.json
├── ops/                  # số đo của VH1–VH6
├── tables/               # bảng mỗi lượt một dòng
└── SHA256SUMS
```

- Cấu trúc một lượt: xem [09 §10.2](09-kiem-thu-danh-gia.md#102-dữ-liệu-của-một-lượt).
- **Kích thước ước tính:** khoảng 30 lượt × vài chục MB, tổng dưới 2 GB.
- **Giấy phép đề xuất:** CC BY 4.0 cho dữ liệu, Apache-2.0 hoặc MIT cho mã nguồn.
- **Không chứa dữ liệu cá nhân:** prompt hoàn toàn là dữ liệu tổng hợp.
- **Nhật ký vận hành** (`docs/nhat-ky/van-hanh.md`): mỗi kịch bản VH và mỗi sự cố thật trong đợt thuê có một mục: ngày, môi trường, các bước, số đo, runbook đã dùng, bài học.

---

## 4. Hướng dẫn tái lập và vận hành (dàn ý README)

1. **Yêu cầu:** phần cứng (laptop NVIDIA, hoặc tài khoản cloud GPU), công cụ (vastai CLI, ansible, kubectl, helm, kubeseal, python, uv).
2. **Chạy nhanh trên laptop:** `make laptop-up`, rồi `make run MATRIX=experiments/matrix-mini.yaml`, rồi `make analysis`.
3. **Chạy đầy đủ trên máy thuê:** cấu hình `.env` (API key Vast.ai, R2), rồi lần lượt `make find rent burnin bootstrap prefetch capacity`, sau đó `make run`, `make ops-tests`, `make backup`, `make release`.
4. **Vận hành:** cập nhật phiên bản và rollback ([08 §5.3](08-van-hanh.md#53-quy-trình-cập-nhật-qua-gitops)); xử lý cảnh báo (`docs/runbooks/`); dựng lại từ đầu ([08 §7](08-van-hanh.md#7-dựng-lại-từ-đầu-khôi-phục-sau-thảm-hoạ)).
5. **Chỉ tái tạo hình và bảng từ dữ liệu đã công bố:** tải `dataset/`, rồi `make analysis DATA=dataset/`.
6. **Phiên bản đã dùng:** bảng phiên bản kèm digest.
7. **Các lỗi thường gặp:** Argo CD và `replicas`, label `release` của PodMonitor, `/dev/shm`, label DCGM, biên bucket của histogram TTFT.

---

## 5. Luận văn

| Chương | Nội dung | Người viết chính | Dựa trên | Số trang ước tính |
|---|---|---|---|---|
| 1. Giới thiệu và bài toán | Bối cảnh, bài toán vận hành, mục tiêu, đóng góp, cấu trúc | Cả nhóm | [01](01-dat-van-de.md), [02](02-muc-tieu-yeu-cau.md) | 5–7 |
| 2. Cơ sở lý thuyết | LLM inference, vLLM, autoscaling K8s, GPU trên K8s, SLO và GitOps, giải pháp liên quan | Trình | [04](04-kien-thuc-nen.md) | 10–12 |
| 3. Phân tích yêu cầu và thiết kế | 3.1 Yêu cầu F/N · 3.2 Kiến trúc tổng thể · 3.3 Thiết kế serving và autoscaling · 3.4 Thiết kế giám sát, SLO, cảnh báo · 3.5 Thiết kế vận hành (cập nhật, sự cố, khôi phục) · 3.6 Môi trường | 3.1–3.2: cả nhóm; 3.3: Trình; 3.4–3.6: Quang | [02](02-muc-tieu-yeu-cau.md), [05](05-kien-truc-he-thong.md), [06](06-moi-truong-chi-phi.md), [07](07-chien-luoc-autoscaling.md), [08](08-van-hanh.md) | 12–15 |
| **4. Triển khai và vận hành** | 4.1 Hạ tầng cloud và cluster · 4.2 GitOps, CI, quản lý bí mật · 4.3 GPU và vLLM trên Kubernetes · 4.4 Autoscaling · 4.5 Rút ngắn cold start · 4.6 Giám sát và SLO · 4.7 Cảnh báo và runbook · 4.8 Cập nhật phiên bản khi hết GPU · 4.9 Sự cố và khôi phục · 4.10 Bảo mật tối thiểu · 4.11 Chi phí, năng lực và công cụ đánh giá | Trình: 4.3–4.5, 4.8, 4.10; Quang: 4.1–4.2, 4.6–4.7, 4.9, 4.11 | [05](05-kien-truc-he-thong.md)–[08](08-van-hanh.md) | **22–28** |
| 5. Đánh giá | Môi trường, năng lực, autoscaling so với tĩnh, cold start, kịch bản vận hành, bảng nghiệm thu, khuyến nghị, hạn chế | Trình: 5.2, 5.4; Quang: 5.1, 5.3, 5.5, 5.6 | [09](09-kiem-thu-danh-gia.md), [03](03-pham-vi-gia-dinh.md) | 12–15 |
| 6. Kết luận | Tổng kết, hạn chế, hướng phát triển | Cả nhóm | [14](14-huong-mo-rong.md) | 3–5 |
| Phụ lục | Manifest chính, quy tắc cảnh báo, một số runbook, bảng phiên bản, số liệu đầy đủ | – | – | tuỳ |

Tính trên ba chương 3–5, phần xây dựng và vận hành (chương 3, 4) chiếm khoảng **70–75%**, phần đánh giá (chương 5) khoảng **25–30%**.

**Danh mục hình đề xuất cho luận văn:** Hình 1–17 của bộ tài liệu này (thay bản minh hoạ bằng số liệu thật ở Hình 5 và 15), cộng các biểu đồ kết quả C1–C6, ảnh chụp dashboard và một tin nhắn cảnh báo thật.

---

## 6. Slide bảo vệ (15–20 trang) và demo

| # | Slide | Thời gian |
|---|---|---|
| 1 | Tên đề tài, nhóm | 0:30 |
| 2–3 | Bài toán: bối cảnh tự host, trade-off (Hình 1), vì sao khó với GPU (Hình 10, 12) | 2:00 |
| 4 | Yêu cầu F/N (tóm tắt) | 1:00 |
| 5–6 | Kiến trúc (Hình 2), vòng lặp autoscaling (Hình 4) | 2:00 |
| 7 | Chọn tín hiệu scale: vì sao A2 mà không phải GPU utilization (Hình 14, định luật Little) | 1:00 |
| 8–9 | Vận hành: SLO → cảnh báo → runbook (Hình 7); cập nhật khi hết GPU (Hình 16) | 2:00 |
| 10–12 | Kết quả: C1, C4, C5, kịch bản vận hành | 3:00 |
| 13 | Bảng nghiệm thu, khuyến nghị cấu hình | 1:00 |
| 14 | Hạn chế, hướng phát triển | 1:00 |
| 15 | Ai làm gì | 0:30 |
| – | **Demo trực tiếp** | 5:00 |

**Kịch bản demo (5 phút, trên cluster laptop):**
1. Mở dashboard Autoscaling và SLO (1 replica, không có tải).
2. Chạy `loadgen --profile KB2-mini`. Tải tăng, hàng đợi tăng, số replica mong muốn tăng lên 2–3; chỉ vào pod đang khởi động.
3. Trong lúc pod mới khởi động, cảnh báo `LLMSLOBurnFast` tới nhóm Telegram. Mở runbook, đi qua phần chẩn đoán nhanh: đúng là đang cold start. Pod mới Ready, TTFT giảm, cảnh báo tự tắt.
4. `kubectl delete pod` một pod vLLM: pod mới tự lên, không có request lỗi.
5. Dừng tải; giải thích cửa sổ ổn định trước khi scale-down. Mở biểu đồ C1 của đợt đánh giá thật.

**Dự phòng:** video quay sẵn các bước trên, cùng ảnh chụp dashboard và tin nhắn cảnh báo.

---

## 7. Checklist trước khi nộp

- [ ] Mọi số liệu trong luận văn đều truy được về `analysis/` và tag `v1.0`.
- [ ] Hình minh hoạ (Hình 5, 15) đã được thay bằng số đo thật, hoặc ghi rõ là minh hoạ.
- [ ] Mọi cảnh báo có runbook; runbook được review lần cuối sau đợt thuê.
- [ ] Không còn TODO hay placeholder (`vX.Y.Z`, `<org>`) trong repo công khai.
- [ ] Link trong tài liệu không hỏng (CI `docs`).
- [ ] Bộ dữ liệu có README, checksum và giấy phép.
- [ ] `gitleaks` sạch; không có kubeconfig, token hay khoá Sealed Secrets trong lịch sử Git.
- [ ] Đã review chéo toàn bộ luận văn; đã kiểm tra chính tả.

---

## 8. Câu hỏi hội đồng có thể đặt ra

**Người khác có thực sự tái lập được không?**
Được. Toàn bộ hạ tầng và nền tảng được mô tả bằng code và dựng bằng vài lệnh `make`. Kịch bản VH5 đo chính việc này: một thành viên dựng lại cluster laptop chỉ theo README, và nền tảng trên máy thuê được dựng từ VM trắng. Hội đồng có thể xem trực tiếp trên cluster laptop trong phần demo.

**Runbook và cảnh báo có phải chỉ để trưng bày?**
Không. Chúng được dùng trong đợt thuê GPU (trực theo ca), trong các kịch bản VH, và trong phần demo. Lịch sử sửa runbook nằm trong Git.
