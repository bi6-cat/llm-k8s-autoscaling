# ──────────────────────────────────────────────────────────────────────────────
# Makefile
# Khái niệm: Makefile = "bảng điều khiển" của repo. Mỗi target (`tên:`) là một thao tác vận hành có
#            tên cố định; `make <tên>` chạy các dòng lệnh (thụt bằng TAB) bên dưới target đó.
# Mục đích:  Gom các lệnh dài (Ansible, kind, helm, Vast) thành `make <lệnh>`. Tên lệnh là hợp đồng với
#            README và tài liệu (Môi trường §3.7), nên lệnh chưa làm vẫn có mặt và báo lỗi rõ ràng.
#            Gõ `make help` để xem danh sách.
# Cách đọc:  `$(X)` = giá trị biến X của make. `$$` = ký tự `$` truyền xuống shell (vì make tự dùng `$`).
#            Dòng lệnh bắt đầu bằng `@` thì make không in lại lệnh trước khi chạy.
# Lưu ý:     Không viết comment cuối dòng gán biến (`X := a  # c`): make giữ cả dấu cách trước `#`.
# Tham khảo: docs/huong-dan/w2.md §2.2, CONTRIBUTING.md §6
# ──────────────────────────────────────────────────────────────────────────────

# Mọi dòng lệnh chạy bằng bash thay cho sh mặc định, để dùng được cú pháp riêng của bash
# (ví dụ `set -o pipefail`).
SHELL := /bin/bash
ANSIBLE_DIR := infra/ansible
# Tên cluster kind của simulator; context kubectl tương ứng là kind-llm-sim
KIND_CLUSTER := llm-sim
SIM := --context kind-$(KIND_CLUSTER)
# Phiên bản chart: phải trùng docs/phien-ban.md và Application trong platform/argocd/apps/home/
KPS_VERSION := 92.1.1
KEDA_VERSION := 2.21.0
# Loại máy thuê: v0 (1 GPU, thử) hoặc v2 (4 GPU, đánh giá). `?=` = chỉ gán nếu người gọi chưa truyền.
MODE ?= v0
# Đường dẫn promtool (đi kèm bản tải Prometheus). Không có trong PATH thì truyền vào:
# make alerts-test PROMTOOL=/đường/dẫn/promtool
PROMTOOL ?= promtool
# yq (bản của mikefarah) = bộ xử lý YAML dòng lệnh, dùng ở alerts-coverage. Phiên bản ghim ở docs/phien-ban.md.
YQ ?= yq

# .PHONY: các target này không phải tên file, make luôn chạy chúng (kể cả khi có file trùng tên)
.PHONY: help home-up sim-up sim-down sim-test-load sim-test find rent bootstrap release lint alerts-test alerts-coverage dashboards-check

# In mọi target có comment `## mô tả` cùng dòng. Thêm target mới thì nhớ viết `## …` để nó hiện ở đây.
help: ## In danh sách lệnh
	@grep -E '^[a-z-]+:.*## ' $(MAKEFILE_LIST) | awk -F':.*## ' '{printf "  %-16s %s\n", $$1, $$2}'
	@echo "  Chưa làm (W3–W5): $(NOT_YET)"

# ── Cluster nhà ─────────────────────────────────────────────────────────────────
# Chạy toàn bộ playbook: chuẩn bị OS, NVIDIA toolkit, k3s server (PC) + agent (laptop), Argo CD.
# Chạy lại bao nhiêu lần cũng được (idempotent). Tắt Argo CD lần đầu: thêm `-e argocd_enabled=false`
# bằng cách chạy ansible-playbook trực tiếp (w2.md §3.5).
home-up: ## Dựng k3s + Argo CD trên PC và laptop (Ansible)
	cd $(ANSIBLE_DIR) && ansible-playbook -i inventory/home.yaml site.yml

# ── Simulator trên laptop (không cần GPU) ──────────────────────────────────────
# Cluster kind tách biệt với cluster nhà. Ở đây cài thẳng bằng helm/kubectl (không qua Argo CD) vì
# cluster này dựng đi dựng lại liên tục và không cần đồng bộ với Git.
sim-up: ## Dựng kind + Prometheus + KEDA + simulator + A2 trên laptop
#	1) Tạo cluster nếu chưa có (`grep -qx` = khớp nguyên dòng, im lặng)
	kind get clusters | grep -qx $(KIND_CLUSTER) || kind create cluster --config infra/kind/kind-config.yaml
#	2) Khai báo kho chart Helm (--force-update: cập nhật nếu đã có)
	helm repo add prometheus-community https://prometheus-community.github.io/helm-charts --force-update >/dev/null
	helm repo add kedacore https://kedacore.github.io/charts --force-update >/dev/null
#	3) Secret mật khẩu Grafana. `create --dry-run=client -o yaml | apply` = tạo namespace nếu chưa có
#	   mà không báo lỗi khi đã có. Secret chỉ tạo một lần (`get … ||`), để mật khẩu không đổi mỗi lần chạy.
	kubectl $(SIM) create namespace monitoring --dry-run=client -o yaml | kubectl $(SIM) apply -f -
	kubectl $(SIM) -n monitoring get secret grafana-admin >/dev/null 2>&1 || \
	  kubectl $(SIM) -n monitoring create secret generic grafana-admin \
	    --from-literal=admin-user=admin --from-literal=admin-password=$$(openssl rand -hex 12)
#	4) Prometheus + Grafana. `-f` sau ghi đè `-f` trước: values chung rồi values riêng cho simulator.
#	   `upgrade --install` = cài nếu chưa có, nâng cấp nếu đã có. `--wait`: chờ mọi pod Ready.
	helm --kube-context kind-$(KIND_CLUSTER) upgrade --install kps prometheus-community/kube-prometheus-stack \
	  --version $(KPS_VERSION) -n monitoring \
	  -f platform/kube-prometheus-stack/values.yaml -f platform/kube-prometheus-stack/values-sim.yaml \
	  --wait --timeout 10m
#	5) KEDA: đọc metric từ Prometheus và điều khiển HPA
	helm --kube-context kind-$(KIND_CLUSTER) upgrade --install keda kedacore/keda \
	  --version $(KEDA_VERSION) -n keda --create-namespace -f platform/keda/values.yaml --wait
#	6) Simulator (overlay sim của serving) rồi ScaledObject A2. Phải chờ Deployment xong trước, vì
#	   ScaledObject trỏ tới Deployment `vllm`.
	kubectl $(SIM) apply -k serving/overlays/sim
	kubectl $(SIM) -n llm-serving rollout status deploy/vllm --timeout=5m
	kubectl $(SIM) apply -k autoscaling/official/overlays/sim

sim-down: ## Xoá cluster simulator
	kind delete cluster --name $(KIND_CLUSTER)

# Bơm tải cho bài T2: `hey` giữ C request đồng thời trong DUR giây (autoscaling/tests/load-sim.sh, cùng file
# make sim-test dùng). Tự mở port-forward riêng ở cổng ngẫu nhiên tới đúng cluster, xong thì tự tắt.
# `$${DUR:-120s}` = biến môi trường DUR, mặc định 120s. Gọi: make sim-test-load C=25 DUR=180s
sim-test-load: ## Tải đồng thời cho T2 (C=25, DUR=120s)
	CTX=kind-$(KIND_CLUSTER) autoscaling/tests/load-sim.sh $${C:-25} $${DUR:-120s}

# Chạy T1–T5 tự động (tự bơm tải qua load-sim.sh), chấm đạt/trượt theo bảng ở w2.md §9.3, ghi log mỗi giây
# vào runs/sim/. Cả 5 bài mất khoảng 20 phút, phần lớn là chờ scale-down (cửa sổ 300 s + 60 s mỗi pod).
# Một bài: make sim-test T=t4 (t2 gồm cả T3).
sim-test: ## Chạy T1–T5 trên simulator, chấm đạt/trượt (T=t1|t2|t4|t5|all)
	CTX=kind-$(KIND_CLUSTER) autoscaling/tests/run-t1-t5.sh $${T:-all}

# ── Máy thuê trên Vast.ai ───────────────────────────────────────────────────────
# Mọi thao tác với Vast nằm trong infra/provision/vast.sh; ở đây chỉ đặt tên ngắn cho chúng.
# Biến đặt trên dòng lệnh make (GPU=…, NGPU=…, MAX_DPH=…) được make đưa vào môi trường của lệnh con,
# nên vast.sh đọc được trực tiếp, không cần khai báo ở đây. Mặc định: RTX_4090, 4 GPU, ≤ 2 USD/giờ.
find: ## Tìm offer Vast: make find MODE=v0|v2 [GPU=RTX_5060_Ti NGPU=2 MAX_DPH=1]
	infra/provision/vast.sh find $(MODE)

# Thuê rồi chờ tới khi SSH vào được. Tiền bắt đầu tính từ lệnh này: nhớ `make release` khi xong.
rent: ## Thuê offer: make rent OFFER=<id> MODE=v0|v2
	infra/provision/vast.sh rent $(OFFER) $(MODE)
	infra/provision/vast.sh wait

# Sinh inventory/cloud.yaml từ instance đang thuê, rồi chạy CÙNG playbook như ở nhà. `time` in tổng
# thời gian: đây là số đo cho VH5 (dựng lại từ máy trắng).
bootstrap: ## Dựng k3s trên VM thuê (Ansible), in thời gian
	infra/provision/vast.sh inventory
	cd $(ANSIBLE_DIR) && time ansible-playbook -i inventory/cloud.yaml site.yml

release: ## Huỷ instance Vast đang thuê
	infra/provision/vast.sh release

# ── Kiểm tra trước khi mở PR ────────────────────────────────────────────────────
# Bản rút gọn của CI để chạy trên máy: danh sách thư mục kustomize ở đây viết sẵn và không chạy kubeconform,
# còn job manifests của CI (.github/workflows/ci.yaml) tự tìm thư mục và kiểm schema.
# Danh sách thư mục là đích cuối của repo; thư mục nào chưa có (phần chưa làm, hoặc glob `*` không khớp nên
# shell giữ nguyên chữ `*`) thì in "bỏ qua" thay vì báo lỗi, để lint không đỏ oan trong lúc các phần còn
# đang làm dở, mà vẫn thấy rõ thư mục nào chưa được kiểm.
lint: ## yamllint, kubectl kustomize, ansible syntax-check
	yamllint -s .
	for d in serving/overlays/* autoscaling/official/overlays/* autoscaling/eval platform/gpu/exporter platform/kube-prometheus-stack/extras observability; do \
	  if [ ! -d "$$d" ]; then echo "lint: bỏ qua $$d (chưa có)"; continue; fi; \
	  kubectl kustomize $$d >/dev/null || exit 1; done
	cd $(ANSIBLE_DIR) && ansible-playbook -i inventory/home.yaml site.yml --syntax-check

# promtool chỉ đọc file rule thuần (`groups:` ở gốc), còn repo lưu rule dạng PrometheusRule (CRD, có
# apiVersion/kind/metadata, `groups:` nằm dưới `spec:`). Để chỉ giữ MỘT bản rule, target này:
#   1) với mỗi file rule: lấy từ dòng `spec:` tới hết file (sed -n '/^spec:/,$$p'), bỏ chính dòng
#      `spec:` (tail -n +2), bỏ 2 dấu cách thụt đầu dòng (sed 's/^  //'), ghi vào thư mục tạm cùng
#      đường dẫn tương đối. File tách ra mà không có dòng `groups:` (thiếu `spec:` ở cột đầu) thì dừng
#      ngay: promtool coi file rỗng là hợp lệ (`SUCCESS: 0 rules found`), CI sẽ xanh mà không kiểm gì;
#   2) chép file test sang cạnh đó, nên rule_files trong test (../llm.yaml…) vẫn đúng;
#   3) promtool check rules (cú pháp, PromQL hợp lệ) rồi promtool test rules (unit test).
# Vì vậy `spec:` phải là key cuối cùng trong mỗi file rule. `trap … EXIT` xoá thư mục tạm kể cả khi lỗi.
# `alerts-test: alerts-coverage` = chạy alerts-coverage trước (kiểm nhanh bằng yq, không cần promtool).
alerts-test: alerts-coverage ## Đủ severity/runbook/test, rồi promtool check + test rule trong observability/ (PROMTOOL=…)
	@set -euo pipefail; tmp=$$(mktemp -d); trap 'rm -rf "$$tmp"' EXIT; \
	for f in observability/rules/*.yaml observability/alerts/*.yaml; do \
	  mkdir -p "$$tmp/$$(dirname "$$f")"; \
	  sed -n '/^spec:/,$$p' "$$f" | tail -n +2 | sed 's/^  //' > "$$tmp/$$f"; \
	  grep -q '^groups:' "$$tmp/$$f" \
	    || { echo "::error::$$f: không tách được rule (cần dòng 'spec:' ở cột đầu, ngay dưới là 'groups:')"; exit 1; }; \
	done; \
	cp -r observability/alerts/tests "$$tmp/observability/alerts/"; \
	$(PROMTOOL) check rules "$$tmp"/observability/rules/*.yaml "$$tmp"/observability/alerts/*.yaml; \
	$(PROMTOOL) test rules "$$tmp"/observability/alerts/tests/*.yaml

# CONTRIBUTING §4: mỗi cảnh báo phải có nhãn `severity: page|ticket`, annotation runbook_url trỏ tới runbook
# của chính nó, file runbook và unit test. promtool không bắt được việc thiếu test (không có test thì không có
# gì để trượt), nên target này kiểm riêng. yq đọc YAML thật, nên mọi kiểu viết (nháy, map một dòng) đều được
# hiểu, và file YAML hỏng thì yq báo lỗi chứ không lặng lẽ bỏ qua.
#   1) `yq ea` (eval-all: gộp mọi file thành một luồng): với mỗi rule có key `alert` trong rules/ lẫn alerts/
#      (cảnh báo lỡ đặt vào rules/ cũng bị kiểm), in một dòng "tên|severity|runbook_url". `// ""` = thiếu
#      thì để rỗng.
#   2) Tên các cảnh báo có ít nhất một unit test mong đợi nó BẮN (exp_alerts không rỗng). Test chỉ kiểm
#      "không bắn" chưa chứng minh được biểu thức đúng.
#   3) Với từng cảnh báo: severity là page hoặc ticket; runbook_url kết thúc bằng docs/runbooks/<tên>.md;
#      file đó có thật; tên có trong danh sách ở bước 2.
# Dòng bắt đầu bằng `::error::` được GitHub Actions tô đỏ trên trang PR; chạy trên máy thì chỉ là chữ thường.
alerts-coverage: ## Mỗi cảnh báo có severity, runbook và unit test (CONTRIBUTING §4; cần yq, YQ=…)
	@set -euo pipefail; \
	command -v $(YQ) >/dev/null || { echo "::error::Cần yq (bản mikefarah, phiên bản ở docs/phien-ban.md); hoặc truyền YQ=/đường/dẫn/yq"; exit 1; }; \
	alerts=$$($(YQ) ea -N '.spec.groups[].rules[] | select(has("alert")) | [.alert, .labels.severity // "", .annotations.runbook_url // ""] | join("|")' observability/rules/*.yaml observability/alerts/*.yaml); \
	tested=$$($(YQ) ea -N '.tests[].alert_rule_test[] | select((.exp_alerts // []) | length > 0) | .alertname' observability/alerts/tests/*.yaml); \
	if [ -z "$$alerts" ]; then echo "::error::Không thấy cảnh báo nào trong observability/"; exit 1; fi; \
	fail=0; err() { echo "::error::Cảnh báo $$name: $$1"; fail=1; }; \
	while IFS='|' read -r name sev url; do \
	  case "$$sev" in page|ticket) ;; *) err "nhãn severity phải là page hoặc ticket (đang là '$$sev')";; esac; \
	  [[ "$$url" == */docs/runbooks/"$$name".md ]] || err "runbook_url phải trỏ tới docs/runbooks/$$name.md (đang là '$$url')"; \
	  [ -f "docs/runbooks/$$name.md" ] || err "thiếu file docs/runbooks/$$name.md"; \
	  grep -qxF "$$name" <<< "$$tested" || err "chưa có unit test nào mong đợi cảnh báo bắn (exp_alerts) trong observability/alerts/tests/"; \
	done <<< "$$alerts"; \
	echo "alerts-coverage: đã kiểm $$(wc -l <<< "$$alerts") cảnh báo"; \
	exit $$fail

# Dashboard Grafana lưu dạng JSON (CONTRIBUTING §4). Grafana chỉ báo PromQL sai khi đã mở panel, nên
# target này bắt lỗi trước khi merge, không cần cluster. Với mỗi file observability/dashboards/*.json:
#   1) `uid` có và không trùng giữa các file (sidecar nạp hai dashboard cùng uid thì chỉ giữ một);
#      không có `id` (id do từng Grafana tự cấp, để lại thì import vào Grafana khác bị lỗi);
#   2) mọi `datasource` là object có `uid` bằng biến `$${datasource}` hoặc nguồn có sẵn `-- Grafana --`
#      (annotation), để cùng một file chạy được ở home, cloud và sim. Kiểu cũ `"datasource": "Prometheus"`
#      (chuỗi), object thiếu uid hay `null` (rơi về datasource mặc định) đều bị báo;
#   3) file < 200 KiB: Argo CD và `kubectl apply` lưu cả object vào annotation last-applied-configuration,
#      mà annotation bị giới hạn 256 KiB;
#   4) lấy mọi `expr` (truy vấn của panel và annotation; yq `..` = duyệt mọi tầng), thay biến của
#      Grafana bằng giá trị mẫu, theo thứ tự: $$__range_s, $$__interval_ms… (số) → 1; $$__rate_interval,
#      $$__interval, $$__range (khoảng thời gian) → 5m; $${tên} hay $${tên:định_dạng} → 1; $$tên → 1. "1" vừa
#      là số vừa là chuỗi hợp lệ. Rồi gói thành recording rule giả cho `promtool check rules` phân tích cú pháp.
#      `--lint=none`: hai panel dùng cùng biểu thức là bình thường, không phải lỗi "rule trùng".
dashboards-check: ## Kiểm JSON dashboard: uid, datasource, kích thước, PromQL (cần yq, promtool)
	@set -euo pipefail; tmp=$$(mktemp -d); trap 'rm -rf "$$tmp"' EXIT; \
	command -v $(YQ) >/dev/null || { echo "::error::Cần yq (bản mikefarah); hoặc truyền YQ=/đường/dẫn/yq"; exit 1; }; \
	command -v $(PROMTOOL) >/dev/null || { echo "::error::Cần promtool; hoặc truyền PROMTOOL=/đường/dẫn/promtool"; exit 1; }; \
	files=(observability/dashboards/*.json); [ -f "$${files[0]}" ] || { echo "::error::Không thấy dashboard nào"; exit 1; }; \
	fail=0; err() { echo "::error file=$$f::$$1"; fail=1; }; uids=""; \
	for f in "$${files[@]}"; do \
	  uid=$$($(YQ) -p json -o yaml '.uid // ""' "$$f"); \
	  if [ -z "$$uid" ]; then err "thiếu uid"; continue; fi; \
	  grep -qxF "$$uid" <<< "$$uids" && err "uid '$$uid' trùng với dashboard khác"; uids+="$$uid"$$'\n'; \
	  [ "$$($(YQ) -p json -o yaml 'has("id")' "$$f")" = false ] || err "còn trường id: xoá đi"; \
	  bad=$$($(YQ) -p json -o yaml '[.. | select(tag == "!!map" and has("datasource")) | .datasource | select(tag != "!!map" or ((.uid // "") != "$${datasource}" and (.uid // "") != "-- Grafana --")) | @json] | unique | join(", ")' "$$f"); \
	  [ -z "$$bad" ] || err "datasource phải có uid \$${datasource} (đang có: $$bad)"; \
	  [ "$$(wc -c < "$$f")" -lt 204800 ] || err "file ≥ 200 KiB"; \
	  $(YQ) -p json -o yaml '{"groups": [{"name": .uid, "rules": [.. | select(tag == "!!map" and has("expr")) | .expr | sub("\$$\{?__(rate_interval|interval|range)_(s|ms)\}?"; "1") | sub("\$$\{?__(rate_interval|interval|range)\}?"; "5m") | sub("\$$\{[^}]*\}"; "1") | sub("\$$[A-Za-z_][A-Za-z0-9_]*"; "1") | {"record": "dashboard:expr", "expr": .}]}]}' "$$f" > "$$tmp/$$uid.yaml"; \
	  $(PROMTOOL) check rules --lint=none "$$tmp/$$uid.yaml" >/dev/null || err "PromQL không hợp lệ (lỗi của promtool ở trên)"; \
	done; \
	echo "dashboards-check: đã kiểm $${#files[@]} dashboard"; \
	exit $$fail

# ── Lệnh đã đặt tên nhưng chưa làm ──────────────────────────────────────────────
# Tên lấy từ Môi trường §3.7. Gọi bây giờ thì báo "chưa làm" và trả mã lỗi 1, để script gọi nó dừng lại.
NOT_YET := burnin prefetch capacity run ops-tests backup analysis test
.PHONY: $(NOT_YET)
$(NOT_YET):
	@echo "make $@: chưa làm (xem kế hoạch W3–W5)"; exit 1
