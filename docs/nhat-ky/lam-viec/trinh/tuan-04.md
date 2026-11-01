# Nhật ký làm việc – Trình – Tuần 04 (26/10–01/11/2026)

## 2026-11-01 – Chạy được yamllint và `make alerts-test` trên máy Windows

- **Mã việc:** chung (công cụ kiểm tra cục bộ) · **Môi trường:** không (máy cá nhân Windows 11 + Git Bash)
- **Đã làm:**
  1. Đổi `core.autocrlf` của bản clone từ `true` (mặc định của Git for Windows) sang `input`, rồi làm mới index và checkout lại (`git rm -r --cached -q .` + `git reset --hard -q`, khi cây đang sạch). File trên đĩa giờ là LF như trong Git.
  2. Cài GNU make 4.4.1 (winget, gói `ezwinports.make`) và yamllint 1.38.0 (`uv tool install`); chép promtool 3.13.4 (bản zip đã kiểm sha256 ngày 25/10) vào `~/.local/bin`.
- **Quyết định và lý do:**
  - `input` thay vì `false`: file CRLF lỡ tạo trên Windows vẫn được đổi thành LF khi commit. Đặt trong cấu hình của bản clone, không thêm `.gitattributes` vì đó là file chung.
  - Chạy chính Makefile (`make alerts-test`) thay vì gõ tay các lệnh tương đương, để không bị lệch khi recipe thay đổi. Truyền `SHELL=bash` vì Makefile đặt `SHELL := /bin/bash` (đường dẫn kiểu Linux), và chạy trong Git Bash để có `sed`, `tail`, `mktemp`. Chưa thử chạy khi không có `SHELL=bash`.
- **Kết quả và số đo:**
  - `yamllint -s observability .yamllint.yaml`: đạt. Trước khi đổi: lỗi `new-lines` ở cả 6 file; riêng `observability/alerts/llm.yaml` có 151 ký tự CR.
  - `make alerts-test SHELL=bash PROMTOOL=promtool` (trong Git Bash): `promtool check rules` và `promtool test rules` đều SUCCESS.
  - `uv run --project loadgen pytest loadgen`: 41 passed; `ruff check` và `ruff format --check`: đạt.
- **Sự cố:**
  - `git checkout-index --force --all` không ghi lại file nào: Git bỏ qua file có stat khớp index, kể cả khi có `--force`. Phải làm mới index như bước 1.
  - Chạy thẳng `promtool test rules observability/alerts/tests/llm-test.yaml` báo `field kind not found in type rulefmt.RuleGroups`, vì rule lưu dạng CRD `PrometheusRule`. Recipe `make alerts-test` tách phần `spec:` trước khi gọi promtool.
- **Còn thiếu:** `make lint` trọn vẹn (cần `ansible-playbook` và các thư mục chỉ có trong scaffold) và `make sim-*` (cần kind, Docker) vẫn chưa chạy được trên máy này. Hướng xử lý: CI (TR1) và WSL2.
- **Liên kết:** sự cố CRLF đã ghi trong mục TR4 của `tuan-03.md`.

## 2026-11-01 – TR1: CI bằng GitHub Actions cho phần đã có trên `main`

- **Mã việc:** TR1 · **Môi trường:** không (máy cá nhân Windows 11 + Git Bash; GitHub Actions)
- **Đã làm:**
  1. Đọc Kế hoạch §10.4, w2 §10, CONTRIBUTING; xem bản nháp `ci.yaml` của Quang (67 dòng, `temp/w2-scaffold`, commit `12c4e27`, chưa chạy lần nào).
  2. Viết `.github/workflows/ci.yaml` mới, chỉ kiểm thư mục đã có trên `main` (`observability/`, `loadgen/`, `docs/`). 5 job: `yaml` (yamllint, actionlint kèm shellcheck), `manifests` (kustomize build rồi kubeconform `-strict`, tự tìm mọi `kustomization.yaml`), `alerts` (`make alerts-test`), `python` (pytest trên Python 3.11 và 3.15, ruff), `docs` (lychee `--offline --include-fragments`).
  3. Thêm target `make alerts-coverage`, đọc YAML bằng yq 4.54.1: mỗi cảnh báo phải có nhãn severity `page` hoặc `ticket`, `runbook_url` trỏ tới `docs/runbooks/<tên>.md`, file runbook đó, và ít nhất một unit test mong đợi nó bắn. `alerts-test` chạy target này trước, và dừng nếu file rule nào tách ra mà không có `groups:`. Cập nhật `docs/phien-ban.md`.
  4. Chạy `/code-review high` hai lượt. Lượt 1 được 9 điểm: `6257173` sửa 7 điểm; điểm promtool trên máy đã xử lý trước đó; điểm "thiếu nhật ký" là mục này. Lượt 2 được 9 điểm mới, không lặp điểm cũ: `afa8b40` sửa 6 điểm (đọc YAML bằng yq thay cho regex, chặn file rule rỗng, kiểm severity, link không có `/` cuối, comment của `make lint`), ghi chú 1 điểm (gói Python mới thì thêm vào job `python`), để lại 2 điểm (xem "Còn thiếu").
- **Quyết định và lý do:**
  - Cách lấy bản nháp theo bạn chốt hôm nay: viết file mới dựa trên bản nháp, ghi nguồn trong commit. Không cherry-pick commit scaffold, vì commit đó gom nhiều file chưa chạy và ghi "do not merge".
  - Ghim mọi công cụ. File chạy tải đúng phiên bản và kiểm sha256; mã băm đối chiếu giữa file checksum của bản phát hành và `digest` GitHub hiển thị. Action ghim theo commit SHA. yamllint chạy qua `uvx --exclude-newer` để cố định cả PyYAML 6.0.3 và pathspec 1.1.1. Chọn setup-uv v10.3.2 (22/10, chỉ thêm checksum), không dùng v10.3.3 vì mới ra 4 ngày.
  - promtool 3.15.0, trùng Prometheus của chart kube-prometheus-stack 92.1.1 (tra `values.yaml` của chart), để PromQL được kiểm bằng đúng bộ phân tích cú pháp sẽ chạy nó. Nâng promtool trên máy từ 3.13.4 lên 3.15.0 cho khớp.
  - Bỏ `lycheeverse/lychee-action`, tải lychee trực tiếp: action này không kiểm sha256 của lychee, và đưa tham số qua `eval`.
  - Job `docs` chỉ bỏ qua link tới thư mục chưa có trên nhánh đang kiểm (`serving/`, `autoscaling/`, `platform/`, `infra/`). Thư mục nào lên `main` thì link tới nó tự được kiểm lại.
  - Thiết kế không chốt phiên bản Python, nên test trên 3.11 (bản thấp nhất `requires-python` cam kết) và 3.15 (bản đang dùng).
  - `concurrency`: PR dùng group theo ref, push thêm commit thì huỷ lần chạy cũ. Mỗi lần push vào `main` có group riêng (`run_id`), vì GitHub chỉ giữ một lần chờ cho mỗi group và huỷ lần chờ cũ hơn.
  - Đọc YAML bằng yq thay cho regex (sau lượt soát 2). Regex bỏ sót tên cảnh báo trong nháy đơn và khi sót thì lặng lẽ cho qua. yq hiểu mọi kiểu viết, báo lỗi khi YAML hỏng, và gắn đúng severity, `runbook_url` với từng cảnh báo. Đổi lại, `make alerts-test` cần thêm yq trên máy, giống promtool.
- **Kết quả và số đo** (trên máy, trừ dòng cuối):
  - yamllint và actionlint (shellcheck 0.11.0): đạt. `make alerts-test`: `alerts-coverage` kiểm 7 cảnh báo; `promtool check rules` 4 + 4 + 7 rule SUCCESS; `promtool test rules` SUCCESS.
  - kubeconform cho `observability/`: 3 PrometheusRule hợp lệ; bản cố ý gõ sai `expr` thành `expre` bị bắt.
  - lychee: 489 link, 414 đạt, 0 lỗi, 75 bỏ qua (link http do `--offline`, cộng link tới 4 thư mục chưa merge). Nếu không loại trừ thì có 56 lỗi, và cả 56 đều trỏ vào thư mục chỉ có ở scaffold (52 ở `w2.md`, 4 ở Kiến trúc). Anchor sai bị bắt (`Cannot find fragment`).
  - pytest: 41 passed trên Python 3.11.17 và 3.15.0; ruff đạt.
  - `make alerts-coverage` trên 10 bản sao cố ý làm hỏng đều dừng, lỗi gắn đúng tên cảnh báo: thiếu runbook; `runbook_url` trỏ nhầm; severity sai; thiếu severity; chỉ có test "không bắn"; `alertname` chỉ nằm trong comment; tên trong nháy đơn; cảnh báo đặt vào `rules/`; YAML hỏng (yq báo dòng lỗi); thiếu yq. Key `"spec":` có nháy (YAML hợp lệ nhưng sed không tách được) bị chốt mới của `alerts-test` bắt.
  - Tách nguyên văn các khối `run:` khỏi `ci.yaml` rồi chạy: 4 bước cài (7 công cụ) tải đúng URL, sha256 khớp, ra file chạy Linux (ELF). Step kiểm link bỏ qua đúng link tới thư mục chưa có, kể cả `../infra` không có `/` cuối, và vẫn bắt link hỏng thật.
  - **GitHub Actions, lần chạy đầu của PR #5:** cả 6 job xanh: `yaml` 9 s, `manifests` 4 s, `alerts` 9 s, `python (3.11)` 13 s, `python (3.15)` 12 s, `docs` 5 s. Log khớp số đo trên máy: kubeconform tải schema qua mạng và thấy 3 PrometheusRule hợp lệ (Skipped: 0); `alerts-coverage` kiểm 7 cảnh báo; pytest 41 passed ở cả hai bản Python; lychee 414 link đạt, 0 lỗi, 75 bỏ qua; actionlint dùng shellcheck 0.11.0 đã ghim.
- **Sự cố:**
  - kubeconform trên máy không tải được schema: chương trình Go tự hỏi DNS 8.8.4.4 và bị timeout, trong khi `curl` và `gh` vẫn ra mạng. Cách làm: tải schema bằng `curl` về thư mục cục bộ. Vị trí schema `default` chỉ kiểm được trên GitHub.
  - Script tách `run:` bằng Python ghi CRLF trên Windows. bash của Git Bash bỏ qua CR nên lần thử đầu vẫn đạt, nhưng như vậy không giống runner Linux. Sửa: ghi byte với LF, rồi chạy lại toàn bộ.
  - actionlint báo SC1072 vì một dòng comment bắt đầu bằng chữ "shellcheck", bị shellcheck hiểu là chỉ thị. Sửa câu chữ và ghi chú bẫy ngay tại chỗ.
  - `make.exe` bản ezwinports làm vỡ chữ có dấu trong output của recipe. Chỉ ảnh hưởng hiển thị.
- **Khác thiết kế:**
  - Kế hoạch §10.4 có job `yaml` (kèm kubeconform) và job `kustomize` riêng. Tôi theo w2 §10: job `manifests` build kustomize rồi chạy kubeconform, vì kubeconform cần manifest đã build.
  - Kế hoạch đặt kiểm tra "mọi cảnh báo có runbook" ở job `docs`. Tôi đặt ở `make alerts-coverage` (job `alerts`), kiểm luôn unit test, để chạy được cả trên máy.
  - Chưa có job `helm`, `ansible` (thư mục chưa lên `main`) và `secrets` (gitleaks, mức Could). Thêm ngoài thiết kế: actionlint, kiểm anchor, ma trận hai bản Python.
- **Còn thiếu:** Branch protection với các job làm required checks: Quang là admin repo. Gộp `make lint` với job `manifests` (target `lint` của Quang, scaffold sẽ sửa): hỏi Quang. Để lại sau lượt soát 2: gom 4 khối tải công cụ thành một script (làm khi thêm job `helm`); kiểm cảnh báo nằm ngoài `observability/` (CONTRIBUTING §4 quy định cảnh báo ở `observability/alerts/`).
- **Liên kết:** PR #5; commit `9c84000`, `6257173`, `afa8b40` trên nhánh `feat/tr1-ci`; `.github/workflows/ci.yaml`, `Makefile`, `docs/phien-ban.md`.
- **Dùng cho luận văn:** §4.2 (GitOps, CI): bảng các job và lỗi mỗi job bắt được; cách ghim công cụ (sha256, commit SHA, `--exclude-newer`). Hình nên có: ảnh trang check của PR #5 với 6 job xanh (chưa chụp).
