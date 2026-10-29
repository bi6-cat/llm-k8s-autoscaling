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

# .PHONY: các target này không phải tên file, make luôn chạy chúng (kể cả khi có file trùng tên)
.PHONY: help home-up sim-up sim-down sim-test-load find rent bootstrap release lint alerts-test

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

# Bơm tải cho bài T2: `hey` giữ C request đồng thời trong DUR giây. Cần port-forward cổng 8000 ở terminal
# khác (w2.md §9.3). `$${DUR:-120s}` = biến môi trường DUR, mặc định 120s. Gọi: make sim-test-load C=25 DUR=180s
sim-test-load: ## Tải đồng thời cho T2 (C=25, DUR=120s); cần port-forward ở terminal khác
	hey -z $${DUR:-120s} -c $${C:-25} -m POST -T application/json -D autoscaling/tests/request-sim.json \
	  http://localhost:8000/v1/chat/completions

# ── Máy thuê trên Vast.ai ───────────────────────────────────────────────────────
# Mọi thao tác với Vast nằm trong infra/provision/vast.sh; ở đây chỉ đặt tên ngắn cho chúng.
find: ## Tìm offer Vast: make find MODE=v0|v2
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
# Giống CI (.github/workflows/ci.yaml) nhưng chạy trên máy mình, nhanh hơn chờ GitHub.
lint: ## yamllint, kubectl kustomize, ansible syntax-check
	yamllint -s .
	for d in serving/overlays/* autoscaling/official/overlays/* platform/gpu/exporter platform/kube-prometheus-stack/extras observability; do \
	  kubectl kustomize $$d >/dev/null || exit 1; done
	cd $(ANSIBLE_DIR) && ansible-playbook -i inventory/home.yaml site.yml --syntax-check

# promtool chỉ đọc file rule thuần (`groups:` ở gốc), còn repo lưu rule dạng PrometheusRule (CRD, có
# apiVersion/kind/metadata, `groups:` nằm dưới `spec:`). Để chỉ giữ MỘT bản rule, target này:
#   1) với mỗi file rule: lấy từ dòng `spec:` tới hết file (sed -n '/^spec:/,$$p'), bỏ chính dòng
#      `spec:` (tail -n +2), bỏ 2 dấu cách thụt đầu dòng (sed 's/^  //'), ghi vào thư mục tạm cùng
#      đường dẫn tương đối;
#   2) chép file test sang cạnh đó, nên rule_files trong test (../llm.yaml…) vẫn đúng;
#   3) promtool check rules (cú pháp, PromQL hợp lệ) rồi promtool test rules (unit test).
# Vì vậy `spec:` phải là key cuối cùng trong mỗi file rule. `trap … EXIT` xoá thư mục tạm kể cả khi lỗi.
alerts-test: ## promtool check + test rule trong observability/ (PROMTOOL=…)
	@set -euo pipefail; tmp=$$(mktemp -d); trap 'rm -rf "$$tmp"' EXIT; \
	for f in observability/rules/*.yaml observability/alerts/*.yaml; do \
	  mkdir -p "$$tmp/$$(dirname "$$f")"; \
	  sed -n '/^spec:/,$$p' "$$f" | tail -n +2 | sed 's/^  //' > "$$tmp/$$f"; \
	done; \
	cp -r observability/alerts/tests "$$tmp/observability/alerts/"; \
	$(PROMTOOL) check rules "$$tmp"/observability/rules/*.yaml "$$tmp"/observability/alerts/*.yaml; \
	$(PROMTOOL) test rules "$$tmp"/observability/alerts/tests/*.yaml

# ── Lệnh đã đặt tên nhưng chưa làm ──────────────────────────────────────────────
# Tên lấy từ Môi trường §3.7. Gọi bây giờ thì báo "chưa làm" và trả mã lỗi 1, để script gọi nó dừng lại.
NOT_YET := burnin prefetch capacity run ops-tests backup analysis test
.PHONY: $(NOT_YET)
$(NOT_YET):
	@echo "make $@: chưa làm (xem kế hoạch W3–W5)"; exit 1
