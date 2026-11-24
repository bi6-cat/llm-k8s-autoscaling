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
ANSIBLE_DIR := ansible
# Tên cluster kind của simulator; context kubectl tương ứng là kind-llm-sim
KIND_CLUSTER := llm-sim
SIM := --context kind-$(KIND_CLUSTER)
# Phiên bản chart: phải trùng docs/phien-ban.md và Application trong envs/home/argocd/apps/
KPS_VERSION := 92.1.1
KEDA_VERSION := 2.21.0
# Argo CD cho sim-argocd: trùng argocd_version của ansible/inventory/group_vars/all.yaml (bản cài ở nhà)
ARGOCD_VERSION := v3.5.4
# Loại máy thuê: v0 (1 GPU, thử) hoặc v2 (4 GPU, đánh giá). `?=` = chỉ gán nếu người gọi chưa truyền.
MODE ?= v0
# Đường dẫn promtool (đi kèm bản tải Prometheus). Không có trong PATH thì truyền vào:
# make alerts-test PROMTOOL=/đường/dẫn/promtool
PROMTOOL ?= promtool
# yq (bản của mikefarah) = bộ xử lý YAML dòng lệnh, dùng ở alerts-coverage. Phiên bản ghim ở docs/phien-ban.md.
YQ ?= yq
# amtool = công cụ dòng lệnh đi kèm Alertmanager (kiểm cấu hình, render template). Cùng bản với Alertmanager
# trong chart, ghim ở docs/phien-ban.md.
AMTOOL ?= amtool

# .PHONY: các target này không phải tên file, make luôn chạy chúng (kể cả khi có file trùng tên)
.PHONY: help home-up alertmanager-secret home-eval-begin home-eval-end sim-up sim-down sim-argocd sim-test-load sim-test sim-lt7 sim-lt8 find rent attach probe bootstrap prefetch cloud-platform run backup backup-check ops-tests vh5 release lint alerts-test alerts-coverage alertmanager-check dashboards-check

# In danh sách lệnh, chia nhóm theo môi trường. Hai loại dòng được in:
#   `##@ <tiêu đề>`        = đầu một nhóm (in thành dòng tiêu đề);
#   `<target>: … ## mô tả` = một lệnh trong nhóm đó.
# Thêm target mới thì nhớ viết `## …` cùng dòng, và đặt nó dưới đúng `##@` của môi trường.
help: ## In danh sách lệnh
	@grep -E '^(##@ |[a-z0-9-]+:.*## )' $(MAKEFILE_LIST) | awk -F':.*## ' \
	  '/^##@ /{printf "\n%s\n", substr($$0, 5); next} {printf "  %-16s %s\n", $$1, $$2}'
	@echo; echo "Đã lược (ADR-006 §3.1, hội đồng không thấy): $(NOT_YET)"

# ── Cluster nhà ─────────────────────────────────────────────────────────────────
##@ Ở nhà: PC RTX 5060, k3s + Argo CD (hướng dẫn: envs/home/README.md)
# Chạy toàn bộ playbook: chuẩn bị OS, NVIDIA toolkit, k3s server (PC) + agent (laptop), Argo CD.
# Chạy lại bao nhiêu lần cũng được (idempotent). Tắt Argo CD lần đầu: thêm `-e argocd_enabled=false`
# bằng cách chạy ansible-playbook trực tiếp (w2.md §3.5).
home-up: ## Dựng k3s + Argo CD trên PC và laptop (Ansible)
	cd $(ANSIBLE_DIR) && ansible-playbook -i inventory/home.yaml site.yml

# Secret token bot và chat id cho Alertmanager, lấy từ .env (common/platform/alertmanager-secret.sh).
# sim-up và cloud-platform tự gọi script này; chạy tay khi đổi bot trong .env, hoặc ở nhà (Secret không nằm
# trong Git nên Argo CD không tạo được): make alertmanager-secret CTX=llm-home. CTX trống = context hiện
# tại của kubectl.
alertmanager-secret: ## Tạo Secret bot Telegram của Alertmanager từ .env: make alertmanager-secret [CTX=…]
	common/platform/alertmanager-secret.sh kubectl $(if $(CTX),--context $(CTX))

# Phiên đánh giá ở nhà (envs/home/README.md, Kiến trúc §18.2): runner áp ScaledObject của từng lượt bằng
# kubectl. Application `autoscaling` còn auto-sync thì Argo CD áp lại A2 giữa lượt, nên runner dừng ngay.
# Root-app bỏ qua trường syncPolicy.automated của app này, nên tắt ở đây không bị bật lại. CTX mặc định
# llm-home (context của cluster nhà, envs/home/README.md).
HOME_KUBECTL = kubectl --context $(or $(CTX),llm-home)
home-eval-begin: ## Tắt auto-sync của A2 ở nhà trước phiên đánh giá [CTX=llm-home]
#	JSON patch `remove` báo lỗi khi trường đã không còn, nên kiểm trước: chạy lại bao nhiêu lần cũng được
	@if [ -n "$$($(HOME_KUBECTL) -n argocd get application autoscaling -o jsonpath='{.spec.syncPolicy.automated}')" ]; then \
	  $(HOME_KUBECTL) -n argocd patch application autoscaling --type json \
	    -p '[{"op":"remove","path":"/spec/syncPolicy/automated"}]'; \
	else echo "auto-sync của Application autoscaling đã tắt"; fi

home-eval-end: ## Xoá ScaledObject khác A2 rồi bật lại auto-sync của A2 theo Git [CTX=llm-home] (cần yq)
#	0) Đọc khối automated từ file Application trong Git TRƯỚC khi đổi gì trên cluster, không viết tay giá
#	   trị: root bỏ qua trường này nên sửa nó trong Git không tự lên cluster. Chạy từ bản checkout đã cập
#	   nhật main. Kiểm kết quả là một JSON object (bắt đầu bằng `{`): tên `yq` còn là một công cụ khác
#	   (bản Python, bọc jq) không hiểu `-o json -I0` và in ra rỗng; khi đó dừng ở đây, chưa xoá gì, thay
#	   vì xoá ScaledObject rồi gửi patch hỏng và để auto-sync tắt mãi (gặp trên PC nhà 16/11, yq 3.4.3).
#	1) Webhook của KEDA chặn hai ScaledObject cùng trỏ một Deployment, nên xoá mọi ScaledObject khác
#	   vllm-a2 trước khi bật auto-sync. `|| true`: grep trả mã 1 khi không còn dòng nào để xoá.
#	2) Merge patch khối automated lên Application.
	@automated=$$($(YQ) -o json -I0 '.spec.syncPolicy.automated' envs/home/argocd/apps/autoscaling.yaml 2>/dev/null); \
	case "$$automated" in \
	  "{"*) ;; \
	  *) echo "Không đọc được khối automated bằng '$(YQ)'. Cần yq bản mikefarah (phiên bản ở docs/phien-ban.md); hoặc truyền YQ=/đường/dẫn/yq" >&2; exit 1 ;; \
	esac; \
	set -e; \
	$(HOME_KUBECTL) -n llm-serving get scaledobject -o name | { grep -v '/vllm-a2$$' || true; } \
	  | xargs -r $(HOME_KUBECTL) -n llm-serving delete; \
	$(HOME_KUBECTL) -n argocd patch application autoscaling --type merge \
	  -p "{\"spec\":{\"syncPolicy\":{\"automated\":$$automated}}}"

# ── Simulator trên laptop (không cần GPU) ──────────────────────────────────────
##@ Simulator: kind + llm-d-inference-sim, không cần GPU (envs/sim/README.md)
# Cluster kind tách biệt với cluster nhà. Ở đây cài thẳng bằng helm/kubectl (không qua Argo CD) vì
# cluster này dựng đi dựng lại liên tục và không cần đồng bộ với Git.
sim-up: ## Dựng kind + Prometheus + KEDA + simulator + A2 trên laptop
#	1) Tạo cluster nếu chưa có (`grep -qx` = khớp nguyên dòng, im lặng)
	kind get clusters | grep -qx $(KIND_CLUSTER) || kind create cluster --config envs/sim/kind-config.yaml
#	2) Khai báo kho chart Helm (--force-update: cập nhật nếu đã có)
	helm repo add prometheus-community https://prometheus-community.github.io/helm-charts --force-update >/dev/null
	helm repo add kedacore https://kedacore.github.io/charts --force-update >/dev/null
#	3) Secret mật khẩu Grafana. `create --dry-run=client -o yaml | apply` = tạo namespace nếu chưa có
#	   mà không báo lỗi khi đã có. Secret chỉ tạo một lần (`get … ||`), để mật khẩu không đổi mỗi lần chạy.
	kubectl $(SIM) create namespace monitoring --dry-run=client -o yaml | kubectl $(SIM) apply -f -
	kubectl $(SIM) -n monitoring get secret grafana-admin >/dev/null 2>&1 || \
	  kubectl $(SIM) -n monitoring create secret generic grafana-admin \
	    --from-literal=admin-user=admin --from-literal=admin-password=$$(openssl rand -hex 12)
#	   Secret bot Telegram của Alertmanager, từ .env. .env chưa có bot thì script chỉ cảnh báo, không dừng.
	common/platform/alertmanager-secret.sh kubectl $(SIM)
#	4) Prometheus + Grafana + Alertmanager. `-f` sau ghi đè `-f` trước: values chung, định tuyến
#	   Alertmanager, kube-state-metrics đọc condition của ScaledObject (KedaScalerErrors cần), rồi values
#	   riêng cho simulator.
#	   `upgrade --install` = cài nếu chưa có, nâng cấp nếu đã có. `--wait`: chờ mọi pod Ready.
	helm --kube-context kind-$(KIND_CLUSTER) upgrade --install kps prometheus-community/kube-prometheus-stack \
	  --version $(KPS_VERSION) -n monitoring \
	  -f common/platform/kube-prometheus-stack-values.yaml -f common/platform/alertmanager-values.yaml \
	  -f common/platform/kube-state-metrics-values.yaml -f envs/sim/platform/kube-prometheus-stack-values.yaml \
	  --wait --timeout 10m
#	   Recording rule, 7 quy tắc cảnh báo và 3 dashboard. Phải sau chart, vì chart cài CRD PrometheusRule.
	kubectl $(SIM) apply -k common/observability
#	5) KEDA: đọc metric từ Prometheus và điều khiển HPA. Lớp values thứ hai bật PodMonitor cho metric của
#	   KEDA (hàng KEDA của dashboard autoscaling); phải sau chart kps vì cần CRD PodMonitor.
	helm --kube-context kind-$(KIND_CLUSTER) upgrade --install keda kedacore/keda \
	  --version $(KEDA_VERSION) -n keda --create-namespace \
	  -f common/platform/keda-values.yaml -f common/platform/keda-metrics-values.yaml --wait
#	6) Simulator (overlay sim của serving) rồi ScaledObject A2. Phải chờ Deployment xong trước, vì
#	   ScaledObject trỏ tới Deployment `vllm`.
	kubectl $(SIM) apply -k envs/sim/serving
	kubectl $(SIM) -n llm-serving rollout status deploy/vllm --timeout=5m
	kubectl $(SIM) apply -k envs/sim/autoscaling

sim-down: ## Xoá cluster simulator
	kind delete cluster --name $(KIND_CLUSTER)

# Chỉ cho VH2 trên kind (D113): cài Argo CD bản core (không UI, không API server) rồi giao serving và A2 của
# sim cho Git, ở nhánh REV. Sau đó commit lên nhánh REV là cập nhật, `git revert` là rollback (Vận hành §5.3,
# §5.4). Chạy sau make sim-up: Argo CD nhận lại Deployment và ScaledObject đang chạy, không tạo lại pod.
# --server-side: CRD của Argo CD quá lớn cho apply thường (giới hạn 256 KB của annotation last-applied);
# --force-conflicts: chạy lại vẫn được. Gỡ Argo CD (giữ nguyên simulator): envs/sim/README.md, mục VH2.
# Gọi: make sim-argocd REV=<nhánh>. REV mặc định là main.
REV ?= main
sim-argocd: ## Cài Argo CD lên kind và giao simulator + A2 cho nhánh Git REV (VH2): make sim-argocd REV=<nhánh>
	kubectl $(SIM) create namespace argocd --dry-run=client -o yaml | kubectl $(SIM) apply -f -
	kubectl $(SIM) apply -n argocd --server-side --force-conflicts \
	  -f https://raw.githubusercontent.com/argoproj/argo-cd/$(ARGOCD_VERSION)/manifests/core-install.yaml >/dev/null
#	Chờ CRD và controller sẵn sàng trước khi áp Application (như role argocd-bootstrap ở nhà)
	kubectl $(SIM) -n argocd wait --for=condition=Available deploy --all --timeout=5m
	kubectl $(SIM) -n argocd rollout status statefulset/argocd-application-controller --timeout=5m
	kubectl $(SIM) apply -f envs/home/argocd/project-default.yaml
#	Đổi nhánh lúc áp, không sửa file: `targetRevision: main` trong Git là giá trị an toàn khi quên REV
	sed 's|targetRevision: main|targetRevision: $(REV)|' envs/sim/argocd/apps.yaml | kubectl $(SIM) apply -f -
#	Chờ cả hai app Synced + Healthy (tối đa 5 phút). jsonpath in "Synced Healthy" cho mỗi app.
	@for i in $$(seq 1 30); do \
	  st=$$(kubectl $(SIM) -n argocd get application serving autoscaling \
	    -o jsonpath='{range .items[*]}{.status.sync.status} {.status.health.status};{end}'); \
	  [ "$$st" = "Synced Healthy;Synced Healthy;" ] && { echo "sim-argocd: serving, autoscaling Synced Healthy ở $(REV)"; exit 0; }; \
	  sleep 10; \
	done; echo "sim-argocd: sau 5 phút vẫn chưa Synced Healthy: $$st" >&2; exit 1

# Bơm tải cho bài T2: `hey` giữ C request đồng thời trong DUR giây (envs/sim/tests/load-sim.sh, cùng file
# make sim-test dùng). Tự mở port-forward riêng ở cổng ngẫu nhiên tới đúng cluster, xong thì tự tắt.
# `$${DUR:-120s}` = biến môi trường DUR, mặc định 120s. Gọi: make sim-test-load C=25 DUR=180s
sim-test-load: ## Tải đồng thời cho T2 (C=25, DUR=120s)
	CTX=kind-$(KIND_CLUSTER) envs/sim/tests/load-sim.sh $${C:-25} $${DUR:-120s}

# Chạy T1–T5 tự động (tự bơm tải qua load-sim.sh), chấm đạt/trượt theo bảng ở w2.md §9.3, ghi log mỗi giây
# vào runs/sim/. Cả 5 bài mất khoảng 20 phút, phần lớn là chờ scale-down (cửa sổ 300 s + 60 s mỗi pod).
# Một bài: make sim-test T=t4 (t2 gồm cả T3).
sim-test: ## Chạy T1–T5 trên simulator, chấm đạt/trượt (T=t1|t2|t4|t5|all)
	CTX=kind-$(KIND_CLUSTER) envs/sim/tests/run-t1-t5.sh $${T:-all}

# LT7 (TR8, Môi trường §19): HPA có chọn đúng ⌈C ÷ threshold⌉ ở mỗi mức tải không, và trễ phản ứng gồm những
# chặng nào. Ghi dữ liệu thô vào runs/sim/lt7-<giờ>/ (khoảng 25 phút), rồi tính bảng bằng analysis/lt7_hpa.py.
# LEVELS, REPS, DUR đặt trên dòng lệnh make thì được đưa vào môi trường của script.
sim-lt7: ## LT7 trên simulator (LEVELS="5 15 25 35" REPS=3 DUR=60)
	CTX=kind-$(KIND_CLUSTER) envs/sim/tests/lt7-hpa.sh

# LT8 (TR8, Môi trường §19): LLMSLOBurnFast kêu sau bao lâu theo tỷ lệ request xấu x, và có im lặng khi
# x ≤ 20 % không. Bộ đo đổi TTFT của simulator lúc đang chạy (POST /admin/config) và giữ KEDA ở 1 replica.
# Dữ liệu thô vào runs/sim/lt8-<giờ>/ (3 mức × 3 lượt, khoảng 2 giờ), rồi tính bảng bằng analysis/lt8_burn.py.
sim-lt8: ## LT8 trên simulator (LEVELS="0.1 0.3 0.6" REPS=3)
	uv run --project experiments python -m experiments.ops.lt8_burn --matrix envs/sim/experiments/matrix.yaml \
	  --context kind-$(KIND_CLUSTER) $(if $(LEVELS),--levels $(LEVELS)) $(if $(REPS),--reps $(REPS))

# ── Máy thuê trên Vast.ai ───────────────────────────────────────────────────────
##@ Cloud: thuê và dựng VM 4 × RTX A4000 trên Vast.ai (envs/cloud/README.md)
# Mọi thao tác với Vast nằm trong envs/cloud/provision/vast.sh; ở đây chỉ đặt tên ngắn cho chúng.
# Biến đặt trên dòng lệnh make (GPU=…, NGPU=…, MAX_DPH=…) được make đưa vào môi trường của lệnh con,
# nên vast.sh đọc được trực tiếp, không cần khai báo ở đây. Mặc định: RTX_A4000, 4 GPU, ≤ 2 USD/giờ.
find: ## Tìm offer Vast: make find MODE=v0|v2 [GPU=RTX_5060_Ti NGPU=2 MAX_DPH=1]
	envs/cloud/provision/vast.sh find $(MODE)

# Thuê rồi chờ tới khi SSH vào được. Tiền bắt đầu tính từ lệnh này: nhớ `make release` khi xong.
rent: ## Thuê offer: make rent OFFER=<id> MODE=v0|v2
	envs/cloud/provision/vast.sh rent $(OFFER) $(MODE)
	envs/cloud/provision/vast.sh wait

# Máy thuê qua giao diện web của Vast (không qua `make rent`): gắn script vào máy bằng host và cổng SSH mà
# Vast hiển thị. Sau đó probe, bootstrap, cloud-platform, run dùng như thường và không cần API key.
# `make release` KHÔNG huỷ được máy này: huỷ trên trang Vast, rồi `envs/cloud/provision/vast.sh detach`.
attach: ## Gắn một máy đã thuê qua web: make attach HOST=<ip> PORT=<cổng SSH>
	envs/cloud/provision/vast.sh attach $(HOST) $(PORT)

# Kiểm máy thật trước khi bootstrap: giữ hay trả máy (cột mạng của Vast không tin được, log phiên 08/11 §1).
probe: ## Đo phần cứng và mạng thật của VM vừa thuê
	envs/cloud/provision/vast.sh probe

# Sinh inventory/cloud.yaml từ instance đang thuê, rồi chạy CÙNG playbook như ở nhà. `time` in tổng
# thời gian: đây là số đo cho VH5 (dựng lại từ máy trắng).
bootstrap: ## Dựng k3s trên VM thuê (Ansible), in thời gian
	envs/cloud/provision/vast.sh inventory
	cd $(ANSIBLE_DIR) && time ansible-playbook -i inventory/cloud.yaml site.yml

# Chạy lại riêng phần tải model và image nếu bootstrap lỗi ở đó (tag `prefetch` trong site.yml).
prefetch: ## Tải model, kéo image trên VM thuê (bootstrap đã gồm bước này)
	envs/cloud/provision/vast.sh inventory
	cd $(ANSIBLE_DIR) && ansible-playbook -i inventory/cloud.yaml site.yml --tags prefetch

# Trên cloud không dùng Argo CD (ADR-006 §3.1). OVERLAY mặc định envs/cloud/serving.
cloud-platform: ## Cài device plugin, Prometheus, KEDA, GPU exporter, vLLM lên VM thuê
	envs/cloud/provision/vast.sh platform

##@ Đánh giá, kịch bản vận hành, sao lưu, trả máy
# Chạy ma trận bằng systemd trên VM, không phụ thuộc SSH (commit đang đứng phải đã push).
run: ## Chạy ma trận trên VM: make run MATRIX=envs/cloud/experiments/matrix-v2.yaml
	envs/cloud/provision/vast.sh runner-start $(MATRIX)

# Đọc .env để có R2_REMOTE và khoá. `set -a` = biến gán sau đó tự export cho lệnh con.
backup: ## Đẩy runs/ lên R2 rồi xác nhận checksum
	set -a; . ./.env; set +a; uv run --project experiments python -m experiments.runner.backup push

backup-check: ## Xác nhận mọi file trong runs/ đã có trên R2
	set -a; . ./.env; set +a; uv run --project experiments python -m experiments.runner.backup check

# Một kịch bản VH dưới tải. RATE nên khoảng 0,5 C. Kết quả ở runs/ops-<kịch bản>-<thời điểm>/.
ops-tests: ## Chạy kịch bản VH: make ops-tests S=vh3-delete MATRIX=… RATE=2 [CTX=…]
	uv run --project experiments python -m experiments.ops.vh $(S) --matrix $(MATRIX) --rate $(RATE) \
	  $(if $(CTX),--context $(CTX))

# Bấm giờ VH5 từ VM vừa thuê tới API trả lời có streaming (N6 ≤ 30 phút).
vh5: ## Dựng lại từ VM trắng, ghi thời gian từng bước vào runs/vh5-*
	envs/cloud/provision/vh5.sh

# Từ chối huỷ máy khi dữ liệu chưa có trên R2 (FORCE_RELEASE=1 để bỏ qua; xem vast.sh).
release: ## Huỷ instance Vast đang thuê
	envs/cloud/provision/vast.sh release

# ── Kiểm tra trước khi mở PR ────────────────────────────────────────────────────
##@ Kiểm tra trước khi mở PR (CI chạy cùng các lệnh này)
# Bản rút gọn của CI để chạy trên máy: danh sách thư mục kustomize ở đây viết sẵn và không chạy kubeconform,
# còn job manifests của CI (.github/workflows/ci.yaml) tự tìm thư mục và kiểm schema.
# Danh sách thư mục là đích cuối của repo; thư mục nào chưa có (phần chưa làm, hoặc glob `*` không khớp nên
# shell giữ nguyên chữ `*`) thì in "bỏ qua" thay vì báo lỗi, để lint không đỏ oan trong lúc các phần còn
# đang làm dở, mà vẫn thấy rõ thư mục nào chưa được kiểm.
lint: ## yamllint, kubectl kustomize, ansible syntax-check
	yamllint -s .
	for d in common/serving common/autoscaling/a2 common/autoscaling/eval common/observability common/platform/gpu-exporter common/platform/kube-prometheus-stack-extras envs/*/serving envs/sim/autoscaling; do \
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
alerts-test: alerts-coverage ## Đủ severity/runbook/test, rồi promtool check + test rule trong common/observability/ (PROMTOOL=…)
	@set -euo pipefail; tmp=$$(mktemp -d); trap 'rm -rf "$$tmp"' EXIT; \
	for f in common/observability/rules/*.yaml common/observability/alerts/*.yaml; do \
	  mkdir -p "$$tmp/$$(dirname "$$f")"; \
	  sed -n '/^spec:/,$$p' "$$f" | tail -n +2 | sed 's/^  //' > "$$tmp/$$f"; \
	  grep -q '^groups:' "$$tmp/$$f" \
	    || { echo "::error::$$f: không tách được rule (cần dòng 'spec:' ở cột đầu, ngay dưới là 'groups:')"; exit 1; }; \
	done; \
	cp -r common/observability/alerts/tests "$$tmp/common/observability/alerts/"; \
	$(PROMTOOL) check rules "$$tmp"/common/observability/rules/*.yaml "$$tmp"/common/observability/alerts/*.yaml; \
	$(PROMTOOL) test rules "$$tmp"/common/observability/alerts/tests/*.yaml

# Cấu hình Alertmanager nằm trong values Helm (common/platform/alertmanager-values.yaml). Trên cluster, lỗi
# chỉ lộ ra khi Operator nạp nó (Alertmanager giữ cấu hình cũ, lỗi nằm trong status của object Alertmanager),
# và template sai chỉ lộ ra khi có cảnh báo thật. Target này kiểm trước, không cần cluster:
#   1) yq tách từng file của `alertmanager.templateFiles` ra thư mục tạm;
#   2) yq tách `alertmanager.config` và đổi `templates` thành '*.tmpl'. Alertmanager tính đường dẫn tương
#      đối từ thư mục chứa file cấu hình. amtool chạy trong thư mục tạm (subshell `( cd … )`, để thư mục
#      hiện tại của shell không nằm trong thư mục sắp xoá) với đường dẫn tương đối, vì trên Windows Git
#      Bash không đổi glob kiểu /tmp/…/*.tmpl sang đường dẫn Windows cho amtool.exe. AMTOOL phải là
#      đường dẫn tuyệt đối hoặc tên trong PATH;
#   3) amtool check-config: cú pháp, receiver mà route nhắc tới có thật, template biên dịch được;
#   4) amtool template render với ba bộ dữ liệu sinh từ common/platform/tests/alertmanager-telegram.json:
#      firing (2 cảnh báo đang kêu, 1 đã hết, chữ < > & trong annotation); resolved (yq đổi mọi status
#      thành resolved, để chạy cả nhánh "đã hết" của template); many (yq nhân 5 danh sách cảnh báo: 10 đang
#      kêu, 5 đã hết, để chạy nhánh giới hạn số dòng). In từng tin ra để xem bằng mắt;
#   5) với mỗi tin: bỏ các thẻ Telegram cho phép (<b>, </b>, <a href="…">, </a>) và entity (&lt; &#39;…),
#      còn sót < > hay & thì báo lỗi (Telegram, parse_mode HTML, từ chối cả tin); tin dài quá 4096 ký tự
#      (`wc -m` = đếm ký tự, không phải byte) thì báo lỗi; bộ many phải in đúng 8 dòng cho 10 cảnh báo
#      đang kêu (pod …-abcde, …-fghij). Mẫu grep chỉ dùng ASCII: make.exe bản ezwinports trên Windows đổi mã
#      chữ có dấu trong recipe, nên mẫu có dấu không khớp.
# inhibit_rules lấy theo mặc định của chart, không nằm trong file này nên không được kiểm ở đây.
alertmanager-check: ## Kiểm cấu hình Alertmanager và render thử tin Telegram (cần yq, amtool)
	@set -euo pipefail; tmp=$$(mktemp -d); trap 'rm -rf "$$tmp"' EXIT; v=common/platform/alertmanager-values.yaml; \
	command -v $(YQ) >/dev/null || { echo "::error::Cần yq (bản mikefarah); hoặc truyền YQ=/đường/dẫn/yq"; exit 1; }; \
	command -v $(AMTOOL) >/dev/null || { echo "::error::Cần amtool (gói Alertmanager, bản ở docs/phien-ban.md); hoặc truyền AMTOOL=…"; exit 1; }; \
	for name in $$($(YQ) '.alertmanager.templateFiles | keys | .[]' "$$v"); do \
	  $(YQ) ".alertmanager.templateFiles[\"$$name\"]" "$$v" > "$$tmp/$$name"; \
	done; \
	$(YQ) '.alertmanager.config | .templates = ["*.tmpl"]' "$$v" > "$$tmp/alertmanager.yaml"; \
	(cd "$$tmp" && $(AMTOOL) check-config alertmanager.yaml); \
	d=common/platform/tests/alertmanager-telegram.json; cp "$$d" "$$tmp/firing.json"; \
	$(YQ) -p json -o json '.status = "resolved" | .alerts[].status = "resolved"' "$$d" > "$$tmp/resolved.json"; \
	$(YQ) -p json -o json '.alerts = .alerts + .alerts + .alerts + .alerts + .alerts' "$$d" > "$$tmp/many.json"; \
	fail=0; \
	for c in firing resolved many; do \
	  out=$$(cd "$$tmp" && $(AMTOOL) template render --template.glob='*.tmpl' --template.data=$$c.json \
	    --template.text='{{ template "telegram.llm.message" . }}'); \
	  printf -- '--- Tin mẫu: %s ---\n%s\n' "$$c" "$$out"; \
	  rest=$$(sed -E 's#</?b>##g; s#<a href="[^"<>]*">##g; s#</a>##g; s/&(lt|gt|amp|quot|#[0-9]+);//g' <<< "$$out"); \
	  if grep -q '[<>&]' <<< "$$rest"; then echo "::error::$$c: tin còn < > hoặc & chưa escape (dùng | html)"; fail=1; fi; \
	  n=$$(printf %s "$$out" | LC_ALL=C.UTF-8 wc -m); \
	  [ "$$n" -le 4096 ] || { echo "::error::$$c: tin dài $$n ký tự, Telegram nhận tối đa 4096"; fail=1; }; \
	  [ "$$c" != many ] || [ "$$(grep -cE 'vllm-7d9c6b5f4-(abcde|fghij)' <<< "$$out")" = 8 ] \
	    || { echo "::error::many: phải in đúng 8 trên 10 cảnh báo đang kêu (giới hạn số dòng mỗi tin)"; fail=1; }; \
	done; \
	[ "$$fail" = 0 ] && echo "alertmanager-check: đạt"; exit $$fail

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
	alerts=$$($(YQ) ea -N '.spec.groups[].rules[] | select(has("alert")) | [.alert, .labels.severity // "", .annotations.runbook_url // ""] | join("|")' common/observability/rules/*.yaml common/observability/alerts/*.yaml); \
	tested=$$($(YQ) ea -N '.tests[].alert_rule_test[] | select((.exp_alerts // []) | length > 0) | .alertname' common/observability/alerts/tests/*.yaml); \
	if [ -z "$$alerts" ]; then echo "::error::Không thấy cảnh báo nào trong common/observability/"; exit 1; fi; \
	fail=0; err() { echo "::error::Cảnh báo $$name: $$1"; fail=1; }; \
	while IFS='|' read -r name sev url; do \
	  case "$$sev" in page|ticket) ;; *) err "nhãn severity phải là page hoặc ticket (đang là '$$sev')";; esac; \
	  [[ "$$url" == */docs/runbooks/"$$name".md ]] || err "runbook_url phải trỏ tới docs/runbooks/$$name.md (đang là '$$url')"; \
	  [ -f "docs/runbooks/$$name.md" ] || err "thiếu file docs/runbooks/$$name.md"; \
	  grep -qxF "$$name" <<< "$$tested" || err "chưa có unit test nào mong đợi cảnh báo bắn (exp_alerts) trong common/observability/alerts/tests/"; \
	done <<< "$$alerts"; \
	echo "alerts-coverage: đã kiểm $$(wc -l <<< "$$alerts") cảnh báo"; \
	exit $$fail

# Dashboard Grafana lưu dạng JSON (CONTRIBUTING §4). Grafana chỉ báo PromQL sai khi đã mở panel, nên
# target này bắt lỗi trước khi merge, không cần cluster. Với mỗi file common/observability/dashboards/*.json:
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
	files=(common/observability/dashboards/*.json); [ -f "$${files[0]}" ] || { echo "::error::Không thấy dashboard nào"; exit 1; }; \
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

# ── Lệnh có trong thiết kế nhưng đã lược ────────────────────────────────────────
# Tên lấy từ Môi trường §3.7. ADR-006 §3.1 (12/11) lược phần đóng gói thành lệnh `make` vì hội đồng chỉ thấy
# kết quả; việc thật vẫn làm bằng lệnh khác (in ra bên dưới). Gọi thì trả mã lỗi 1 để script gọi nó dừng lại.
NOT_YET := burnin capacity analysis test
.PHONY: $(NOT_YET)
$(NOT_YET):
	@echo "make $@: đã lược (ADR-006 §3.1). Thay bằng:"; \
	case $@ in \
	  burnin) echo "  make probe, rồi vllm bench serve chạy tay (Môi trường §3.4)";; \
	  capacity) echo "  make run MATRIX=envs/cloud/experiments/matrix-dg1.yaml (runner ghi capacity.json)";; \
	  analysis) echo "  uv run --project analysis python -m analysis.build_tables runs/<phiên> (bảng chương 5)"; \
	            echo "  uv run --project analysis python -m analysis.charts runs/<phiên> (biểu đồ C1–C4)";; \
	  test) echo "  make lint alerts-test dashboards-check; pytest theo CONTRIBUTING §7";; \
	esac; exit 1
