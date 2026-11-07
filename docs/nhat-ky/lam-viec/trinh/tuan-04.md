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
  - Cách lấy bản nháp theo Trình chốt hôm nay: viết file mới dựa trên bản nháp, ghi nguồn trong commit. Không cherry-pick commit scaffold, vì commit đó gom nhiều file chưa chạy và ghi "do not merge".
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

## 2026-11-01 – TR1: job `docs` bỏ qua link theo từng file chưa có, không theo cả thư mục

- **Mã việc:** TR1 · **Môi trường:** không (máy Windows, lychee cục bộ)
- **Đã làm:** Khi làm TR2, nhánh `feat/tr2-sim` thêm một phần `infra/` (`kind/`), `platform/` (`keda/`, `kube-prometheus-stack/`) và `autoscaling/`. Chạy lychee với đúng logic của job `docs` thì có 31 lỗi. Sửa step "Kiểm link và anchor": lấy mọi link Markdown trỏ vào `serving/`, `autoscaling/`, `platform/`, `infra/`, tính đường dẫn từ gốc repo, và chỉ bỏ qua đường dẫn nào chưa có trên nhánh; trước đây bỏ qua cả thư mục khi thư mục chưa có.
- **Quyết định và lý do:** Bỏ qua theo thư mục chỉ đúng khi thư mục chưa có gì. Code lên `main` dần theo từng PR, nên một thư mục có thể mới có một phần (`platform/keda/` đã có, `platform/argocd/` chưa); khi đó mọi link tới phần chưa có làm job đỏ. Bỏ qua theo file thì link (cả anchor) tới mọi file đã có vẫn được kiểm. Dấu chấm trong tên file viết thành `[.]`, vì trong regex "." là ký tự bất kỳ.
- **Kết quả và số đo** (lychee 0.24.2 trên máy, chạy nguyên văn khối `run:` tách bằng yq):
  - `feat/tr1-ci`: bỏ qua 51 đường dẫn chưa có; 414 link đạt, 0 lỗi (bằng logic cũ).
  - `feat/tr2-sim`: logic cũ 31 lỗi (30 link vào file chưa có trong `infra/`, `platform/`; 1 link tới `.github/workflows/ci.yaml`, vì nhánh tách từ `main` chưa có file này). Logic mới bỏ qua 42 đường dẫn, 422 link đạt, chỉ còn lỗi `ci.yaml`; lỗi này hết khi PR #5 merge, vì CI kiểm bản gộp với `main`.
  - actionlint (shellcheck 0.11.0) và yamllint: đạt.
- **Sự cố:** Lần thử đầu escape dấu chấm bằng `\&` trong sed: dấu `\` bị mất trên đường truyền lệnh vào shell, dấu chấm thành `&`, nên không exclude nào khớp (47 lỗi). Đổi sang `[.]`, không cần escape.
- **Liên kết:** PR #5; `.github/workflows/ci.yaml` (commit cùng mục này).

## 2026-11-01 – TR2: simulator trên kind (WSL2 trên máy Trình), chạy T1–T5

- **Mã việc:** TR2 · **Môi trường:** simulator (kind trong WSL2, laptop Windows của Trình)
- **Đã làm:**
  1. Máy của Quang đang trục trặc nên chưa vào được cluster nhà; dựng simulator ngay trên máy Trình. Cài WSL2 Ubuntu 24.04 vào `D:\WSL\Ubuntu-24.04` (`wsl --install -d Ubuntu-24.04 --location … --no-launch --web-download`). Trong Ubuntu, bằng root: Docker Engine 29.9.2 (kho apt của Docker), kind v0.33.0, kubectl v1.36.5, helm v4.3.1, kubeconform v0.8.0 (file tải về đều kiểm sha256), `hey` từ apt, giới hạn inotify như w1 §5.3. `.wslconfig` có sẵn trên máy giới hạn WSL ở 6 GB RAM, 6 CPU.
  2. Nhánh `feat/tr2-sim` từ `origin/main`. Viết lại phần của Trình dựa trên bản nháp của Quang (`temp/w2-scaffold`, `12c4e27`), ghi nguồn ở header: `infra/kind/kind-config.yaml`, `platform/keda/values.yaml`, `platform/kube-prometheus-stack/values.yaml` và `values-sim.yaml`, `autoscaling/official/{base,overlays/sim}/`, `autoscaling/tests/` (body request, NetworkPolicy của T4). `serving/` của Quang lấy từ `feat/serving` (`dbc72b0`) bằng `git archive` ra `/opt/llm-sim/serving`, không commit; Makefile thêm biến `SIM_SERVING` để `make sim-up` dùng thư mục đó.
  3. Đối chiếu từng key trong values với `helm show values` của đúng bản chart đã ghim (kube-prometheus-stack 92.1.1, KEDA 2.21.0), render thử bằng `helm template`; `kubectl kustomize | kubeconform -strict` như job `manifests` của CI.
  4. `make sim-up SIM_SERVING=/opt/llm-sim/serving/overlays/sim`, rồi kiểm điều kiện trước khi thử: kube-controller-manager có `--horizontal-pod-autoscaler-sync-period=5s`; target `podMonitor/llm-serving/vllm/0` up, chu kỳ 5 s; câu PromQL của A2 trả 0; APIService `v1beta1.external.metrics.k8s.io` True.
  5. Chạy T1–T5 bằng một script nháp ghi trạng thái HPA mỗi giây (lần 1). Sửa theo kết quả, đưa vào repo thành `autoscaling/tests/run-t1-t5.sh` (gọi bằng `make sim-test`, tự chấm đạt/trượt theo bảng w2 §9.3), chạy lại cả 5 bài (lần 2).
- **Quyết định và lý do:**
  - WSL2 + Docker Engine, không dùng Docker Desktop (Trình chọn): môi trường Linux giống cluster thật và CI, nhẹ hơn, sau này chạy được cả Ansible.
  - Lấy code như TR1 (Trình chọn): nhánh mới từ `main`, viết lại, ghi nguồn. Không commit `serving/` để không đụng phần của Quang.
  - `platform/keda/values.yaml` thêm `cpu: null`. Helm gộp values vào mặc định của chart, mà mặc định có `limits.cpu: 1`; bản nháp chỉ ghi `limits.memory` nên limit CPU vẫn còn, trái với comment "không đặt limit CPU". `helm template` xác nhận: có `cpu: null` thì cả 3 Deployment của KEDA chỉ còn limit bộ nhớ.
  - Ghim node image theo digest (`kindest/node:v1.37.0@sha256:a1ed56cf…0ae5`, lấy từ release notes kind v0.33.0), theo CONTRIBUTING §2.
  - kubectl v1.36.5, trùng CI, để `kubectl kustomize` cho cùng kết quả. helm v4.3.1, bản chính hiện tại; hai chart đã ghim cài được bằng bản này.
  - kube-prometheus-stack thêm `scrapeConfigSelectorNilUsesHelmValues: false` cho đủ bộ "nhận mọi CR, không đòi label".
- **Kết quả và số đo:**
  - `make sim-up` lần đầu (kéo node image và mọi image): **501 s**, mã thoát 0. Kết quả đúng như w2 §9.2: 1 pod `vllm-…` Ready, `vllm-a2` `READY=True`, HPA `0/10 (avg)`. `keda-operator` khởi động lại 1 lần (`Completed`, exit 0, log không có dòng lỗi).
  - RAM khi chạy T3 (3 pod simulator): 3 container node của kind tổng khoảng 2,39 GiB (914 + 813 + 666 MiB); VM WSL 2,8 GB (`vmmemWSL`). Khớp ước tính "kind + giám sát + simulator khoảng 3 GB" (w1 §5.1). Ổ của WSL dùng 8,5 GB.
  - Lần 1 (script nháp, 21:45–22:01):
    - T1: `desired=1`, metric 0 suốt 120 s. Đạt.
    - T2 (hey C=25, 180 s): `desired=3` sau **1 s**; pod thứ 2 Ready sau 7 s, pod thứ 3 sau 16 s kể từ lúc HPA quyết định; metric HPA ở 3 replica là `8334m` ≈ 25 ÷ 3. hey: 750 request, cả 750 trả 200, 3,92 request/s. Đạt (tiêu chí ≤ 15 s). 1 s là do lần scrape và lần sync HPA cùng rơi ngay sau lúc bắt đầu tải; trường hợp xấu nhất theo lý thuyết khoảng 10 s (scrape 5 s + sync 5 s).
    - T3: về 2 sau 301 s tính từ hạn dừng của hey, về 1 sau thêm 61 s. Đạt.
    - T4: áp NetworkPolicy 120 s, `numberOfFailures` vẫn 0, không fallback. Trượt; nguyên nhân ở mục Sự cố.
    - T5: KEDA xoá HPA khoảng 1 s sau khi gắn annotation; `ready=1` ở cả 83 lần đọc trong lúc có tải; hey 257/257 request trả 200. Gỡ annotation thì HPA được tạo lại. Đạt.
  - Lần 2 (`make sim-test`, script trong repo, 22:01–22:20, mã thoát 0): cả 5 bài đạt.
    - T1: `desired=1` suốt 120 s.
    - T2: `desired=3` sau **6 s**; metric HPA ở 3 replica 8,334 ≈ 25 ÷ 3. hey 760/760 request trả 200.
    - T3: giữ 3 trong 302 s tính từ hạn dừng của hey, về 1 sau thêm 60 s.
    - T4 (có bước xoá pod keda-operator): operator mới Ready sau 23 s; KEDA báo lỗi lần 1, 2, 3 ở giây +4, +10, +12; fallback ở +18 s (`desired=3`, metric 30 = 3 × threshold 10, `Fallback=True`), tổng **19 s** kể từ lúc operator Ready, `numberOfFailures=4` (tiêu chí ≤ 30 s). Gỡ policy thì lần hỏi kế tiếp thành công, `numberOfFailures` về 0, rồi scale-down như T3.
    - T5: `spec.replicas=1` ở cả 71 lần đọc trong lúc tạm dừng có tải; hey 255/255 request trả 200.
- **Sự cố:**
  - T4 không fallback. Pod busybox mới trong ns `keda` gọi Prometheus thì `download timed out`, ở ns `default` thì gọi được: kindnet có thực thi NetworkPolicy. Nhưng KEDA dùng lại kết nối keep-alive đã mở (hỏi mỗi 5 s nên kết nối không bao giờ rảnh để đóng), còn NetworkPolicy chỉ chặn kết nối mới (conntrack cho kết nối đã mở đi qua). Sửa: sau khi áp policy thì `kubectl -n keda delete pod -l app=keda-operator`; không dùng `rollout restart`, vì Argo CD ở nhà sẽ hoàn tác thay đổi template. Lệnh kiểm tra cũ ở w2 §9.3 (`kubectl exec deploy/keda-operator -- wget`) không chạy được vì image không có `wget`; đổi sang pod busybox. VH4 (TR6) gây sự cố bằng cùng policy nên cũng cần bước này.
  - WSL tự tắt distro khi không còn phiên `wsl.exe` nào (sau khi lệnh chạy nền kết thúc), làm Docker dừng giữa chừng. Lần mở sau, `llm-sim-control-plane` `Exited (128)`: `runc` không tạo được unit `docker-<id>.scope`. Sửa: `systemctl reset-failed` rồi `docker start llm-sim-control-plane`; API server sẵn sàng sau khoảng 2 s; vài pod báo `CreateContainerConfigError` ("services have not yet been read at least once") rồi tự hết sau khoảng 2 phút. Tránh: giữ một phiên WSL mở khi dùng simulator (phiên này giữ bằng `sleep infinity`); xong thì `make sim-down`. Đã ghi vào bảng lỗi w2 §13.
  - Script nháp đo T3 từ lúc tiến trình hey thoát nên ra 291 s, trông như trượt tiêu chí 300 s. Tới hạn, hey thôi gửi request mới nhưng còn chờ request dở dang khoảng 10 s; cửa sổ 300 s tính từ lần cuối HPA còn muốn 3 replica (21:51:01 + 300 s = 21:56:01, đúng lúc về 2). Sửa mốc 0 thành hạn dừng của hey.
  - Thêm `platform/`, `infra/` một phần làm job `docs` của PR #5 báo 31 link hỏng; sửa trên `feat/tr1-ci` (mục TR1 cùng ngày, nhánh đó).
- **Khác thiết kế:**
  - Simulator chạy trên laptop Windows của Trình qua WSL2, không phải laptop Ubuntu của Quang (w1 §5.1), vì máy Quang đang trục trặc và TR2 là việc của Trình. Thiết kế loại WSL2 vì không hợp Kubernetes có GPU (Môi trường §2.1); simulator không cần GPU.
  - `serving/` chưa có trên nhánh: `make sim-up` cần `SIM_SERVING` tới khi `feat/serving` merge.
  - T4 thêm bước xoá pod keda-operator; w2 §9.3 và file NetworkPolicy đã sửa theo.
  - T1–T5 chạy tự động bằng `make sim-test`; hướng dẫn gốc chạy tay bằng ba terminal (vẫn giữ trong w2 §9.3).
- **Liên kết:** nhánh `feat/tr2-sim` (commit cùng mục này); log thô ở `runs/sim/` trên máy Trình (không commit).
- **Dùng cho luận văn:** chương "Triển khai và vận hành" (Kiến trúc §15): bảng T1–T5 kèm số đo; hình số replica theo thời gian ở T2–T3 vẽ từ log mỗi giây (chưa vẽ); sự cố T4 (NetworkPolicy và conntrack) là ví dụ "cách gây sự cố cũng phải được kiểm chứng". LT7 (TR8, Môi trường §19) cần T2 chạy 5 lần; hiện có 2 lần: quyết định scale sau 1 s và 6 s (dự đoán ≤ ~15 s).

## 2026-11-01 – TR2: soát bằng `/code-review high`, KEDA tắt keep-alive, chạy lại T1–T5

- **Mã việc:** TR2 · **Môi trường:** simulator (kind trong WSL2)
- **Đã làm:**
  1. Chạy `/code-review high` trên `feat/tr2-sim` (commit `076afbe`): 9 điểm, đều ở `run-t1-t5.sh` và Makefile.
  2. Đối chiếu điểm "KEDA có biến tắt keep-alive" với mã nguồn KEDA v2.21.0: `pkg/util/http.go` đọc `KEDA_HTTP_DISABLE_KEEP_ALIVE` (mặc định false) và gán vào `DisableKeepAlives` của transport HTTP dùng chung; scaler Prometheus tạo client bằng `kedautil.CreateHTTPClient` nên theo biến này. `helm template` cho thấy khối `env:` cấp cao nhất của chart vào cả 3 thành phần.
  3. Sửa theo cả 9 điểm, chạy lại `make sim-up` và `make sim-test` (lần 3).
- **Quyết định và lý do:**
  - `platform/keda/values.yaml` đặt `KEDA_HTTP_DISABLE_KEEP_ALIVE=true` và bỏ bước xoá pod keda-operator ở T4. NetworkPolicy có tác dụng ngay từ lần hỏi kế tiếp, đúng như VH4 (ADR-005 T6) giả định; T4 đo từ lúc áp policy chứ không từ một lần khởi động lại operator (trong lúc khởi động lại, HPA không lấy được metric nào). Chi phí: thêm một lần bắt tay TCP trong cluster cho mỗi lần hỏi. Cách xoá pod giữ lại làm cách tạm trong w2 §9.3. Biến này áp cả ở nhà và cloud, nên hỏi Quang trong PR.
  - Tách lệnh tải ra `autoscaling/tests/load-sim.sh`, dùng chung cho `make sim-test-load` và `make sim-test`, để hai cách chạy gửi đúng một kiểu tải. Script dùng port-forward có sẵn ở cổng 8000, chưa có thì tự mở; bị dừng giữa chừng thì tự tắt hey và port-forward.
  - `run-t1-t5.sh` đọc max, fallback, threshold và câu PromQL từ chính ScaledObject, tính C = 2,5 × threshold; sửa overlay thì bài thử đổi theo.
  - T1 kiểm cả metric 0. T4 kiểm thêm: trước khi áp policy KEDA có 0 lỗi, gỡ policy thì lỗi về 0, để nối lỗi với đúng policy. Không đặt cận dưới cho thời gian fallback, vì lần 2 thấy lỗi thứ 2 và thứ 3 chỉ cách nhau 2 s. T5 hỏi thẳng Prometheus qua API server để chắc tải đã tới simulator: A2 cao nhất phải ≥ 21, tức không tạm dừng thì đã lên 3 replica.
  - Hàm đọc trạng thái không làm dừng script khi kubectl lỗi thoáng qua (`set -e`). `make sim-up` kiểm `SIM_SERVING` trước tiên, thiếu thì báo ngay thay vì lỗi ở bước 6 sau khoảng 8 phút.
- **Kết quả và số đo:**
  - `make sim-up` thiếu `SIM_SERVING`: dừng sau 0 s, in hướng dẫn. Có `SIM_SERVING`: 57 s (chỉ nâng cấp hai release Helm); keda-operator mới có `KEDA_HTTP_DISABLE_KEEP_ALIVE=true`.
  - Lần 3 (`make sim-test`, 22:33–22:52; mã thoát 0, 5/5 đạt):
    - T1: `desired=1`, metric 0 suốt 120 s. Đạt.
    - T2: `desired=3` sau **8 s**; metric HPA 8,334 ≈ 25 ÷ 3; hey 731/731 phản hồi 200 (3,81 request/s). Đạt.
    - T3: giữ 3 trong 304 s tính từ hạn dừng của hey, về 1 sau thêm 61 s. Đạt.
    - T4 (không xoá pod): áp policy lúc 22:44:51; lỗi lần 1 ở +11 s, lần 3 ở +19 s; fallback ở **+24 s** (`desired=3`, `Fallback=True`, `numberOfFailures=4`). Gỡ policy thì lỗi về 0 ngay (0 s). 3 pod KEDA không khởi động lại lần nào. Đạt (tiêu chí ≤ 30 s; w2 ghi khoảng 15–30 s).
    - T5: `spec=1`, `ready=1` ở cả 71 lần đọc (mỗi giây) trong 60 s có tải; A2 cao nhất 25 (cần ≥ 21); hey 246/246 phản hồi 200 (3,49 request/s). Đạt.
  - LT7: 3 mẫu thời gian quyết định ở T2: 1 s, 6 s, 8 s (dự đoán ≤ ~15 s).
  - Mỗi lần `kubectl annotate` ScaledObject (T5), webhook KEDA 2.21.0 in cảnh báo: `PollingInterval is configured but is not relevant for scaling. It only affects scaling when minReplicaCount = 0, idleReplicaCount is set, or useCachedMetrics is enabled`. Khớp với comment trong `scaledobject-a2.yaml`: với A2 (min 1), chu kỳ sync 5 s của HPA quyết định scale 1↔N. Theo chính cảnh báo này, `pollingInterval` khi đó chỉ còn quyết định KEDA làm mới trạng thái và event của ScaledObject nhanh đến đâu.
- **Khác thiết kế:** T4 không cần bước thêm, nhưng KEDA phải tắt keep-alive (thiết kế không nói tới keep-alive).
- **Liên kết:** nhánh `feat/tr2-sim` (commit cùng mục này); `platform/keda/values.yaml`, `autoscaling/tests/`, `Makefile`, `docs/huong-dan/w2.md`.
- **Dùng cho luận văn:** chương "Triển khai và vận hành": T4 trước và sau khi tắt keep-alive (0 lỗi trong 120 s, so với fallback sau 24 s) cho thấy cách gây sự cố cũng phải được kiểm chứng.
