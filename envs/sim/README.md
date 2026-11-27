# Chạy trên simulator (`envs/sim`)

Kiểm thử vòng autoscaling **không cần GPU**: cluster kind trên laptop, `llm-d-inference-sim` đóng vai vLLM (cùng API OpenAI, cùng metric `vllm:*`, trả lời có độ trễ giả lập). Dựng lại trong vài phút, nên dùng để thử mọi thay đổi về KEDA, PromQL, cảnh báo và runner trước khi đưa lên GPU thật.

| | |
|---|---|
| Cluster | kind `llm-sim` (context `kind-llm-sim`), 1 control-plane + 2 worker (`kind-config.yaml`; 2 worker để thử drain node) |
| "vLLM" | Simulator: cùng Deployment và Service với vLLM thật (overlay `serving/` chỉ đổi image và tham số) |
| Autoscaling | A2 thật (`common/autoscaling/a2`), threshold và max replica hợp với simulator (`autoscaling/`) |
| Cài đặt | helm và kubectl trực tiếp, **không** qua Argo CD (cluster dựng đi dựng lại liên tục). Riêng VH2 thì thêm Argo CD ([VH2 qua Git](#vh2-qua-git-thêm-argo-cd-vào-kind)) |
| Số đo | Chỉ kiểm logic (đạt/trượt, thời gian phản ứng của KEDA). **Không** phải số đo hiệu năng |

## Cần có

| | |
|---|---|
| Máy | Linux có Docker Engine. Trên Windows: WSL2 Ubuntu 24.04 có Docker Engine, không cần Docker Desktop (xem [Trên Windows](#trên-windows-wsl2)). Ba node kind dùng khoảng 2,9 GB RAM lúc nghỉ và 3,1 GB khi có tải với 3 replica (đo 24/11, WSL có 6 GB) |
| Công cụ | `make`, `docker`, `kind`, `kubectl`, `helm`, `hey`, `jq`, `curl`, `openssl` (`make sim-test` và `make sim-lt7` dừng ngay nếu thiếu `kubectl`, `jq`, `curl` hoặc `hey`). Lệnh cài: [W1 §4.2](../../docs/huong-dan/w1.md#42-công-cụ). Bản đã ghim: [phien-ban.md](../../docs/phien-ban.md) |
| `uv` | Cho runner, LT7, LT8 và phân tích; W1 không cài. Cài bản CI dùng: `curl -LsSf https://astral.sh/uv/0.13.1/install.sh \| sh` |
| Mạng | Lần đầu tải node image của kind (khoảng 1,3 GB), chart Helm, và image của Prometheus, KEDA, simulator |
| Telegram (tuỳ chọn) | `.env` có `ALERTMANAGER_TELEGRAM_BOT_TOKEN` và `ALERTMANAGER_TELEGRAM_CHAT_ID` (mẫu ở `.env.example`) thì `make sim-up` tạo Secret, và cảnh báo nào kêu trên kind cũng được gửi thật. Không có thì lệnh chỉ in cảnh báo rồi chạy tiếp |

Muốn dựng thử mà không gửi tin dù `.env` đã có bot: đặt hai biến giả trong môi trường. Script `common/platform/alertmanager-secret.sh` ưu tiên biến môi trường hơn `.env`, và chỉ kiểm dạng `<số>:<chuỗi>`:

```bash
ALERTMANAGER_TELEGRAM_BOT_TOKEN=1:fake ALERTMANAGER_TELEGRAM_CHAT_ID=1 make sim-up
```

Secret giả ở lại trong cluster: Alertmanager vẫn thử gửi và chỉ ghi lỗi vào log. Muốn chuyển sang bot thật trên cùng cluster thì tạo lại Secret từ `.env` bằng `make alertmanager-secret CTX=kind-llm-sim`.

## Trong thư mục này

| Đường dẫn | Là gì |
|---|---|
| `kind-config.yaml` | Hình dạng cluster kind |
| `serving/` | Overlay: image simulator thay vLLM, PodMonitor khớp simulator |
| `autoscaling/` | Overlay A2: threshold và max replica cho simulator |
| `platform/kube-prometheus-stack-values.yaml` | Values Prometheus nhẹ cho kind |
| `tests/run-t1-t5.sh` | Bài kiểm thử T1–T5, chấm đạt/trượt (cần `hey`) |
| `tests/load-sim.sh` | Bơm tải đồng thời bằng `hey` qua port-forward |
| `experiments/matrix.yaml` | Ma trận chạy thử runner trên kind |
| `argocd/apps.yaml` | Application `serving`, `autoscaling` cho VH2 (chỉ khi chạy `make sim-argocd`) |

## Chạy

```bash
make sim-up                    # kind + Prometheus + KEDA + simulator + A2 (~6 phút khi đã có node image, phần lớn là chart Prometheus)
make sim-test                  # T1–T5, ~20 phút; một bài: make sim-test T=t4
make sim-test-load C=25 DUR=180s   # chỉ bơm tải, xem scale trên Grafana
make sim-lt7                   # LT7: số replica theo ⌈C ÷ threshold⌉ và trễ từng chặng, ~27 phút
uv run --project analysis python -m analysis.lt7_hpa runs/sim/lt7-<giờ>   # bảng của LT7
make sim-lt8                   # LT8: lúc LLMSLOBurnFast kêu theo tỷ lệ request xấu x = 0,1/0,3/0,6, ~2 giờ
uv run --project analysis python -m analysis.lt8_burn runs/sim/lt8-<giờ>  # bảng của LT8
uv run --project analysis python -m analysis.lt_charts --lt7 analysis/figures/lt7-hpa.csv \
  --lt8 runs/sim/lt8-<giờ>     # hình LT7, LT8 → analysis/figures/*.svg

# Runner trên kind (máy tạo tải chạy trong cluster)
uv run --project experiments python -m experiments.runner \
  --matrix envs/sim/experiments/matrix.yaml --context kind-llm-sim

# Kịch bản vận hành, ví dụ chặn KEDA → Prometheus (VH4): mong đợi fallback lên max trong ≤ 30 s
make ops-tests S=vh4 MATRIX=envs/sim/experiments/matrix.yaml RATE=0.2 CTX=kind-llm-sim

make sim-down                  # xoá cluster
```

Kiểm tra sau `make sim-up`:

```bash
kubectl --context kind-llm-sim -n llm-serving get pods,scaledobject,hpa
# Mong đợi: 1 pod vllm-… Running 1/1; scaledobject/vllm-a2 READY=True; HPA keda-hpa-vllm-a2 TARGETS 0/10 (avg)

# Grafana: lấy mật khẩu của admin, rồi mở cổng (lệnh port-forward giữ terminal; Ctrl+C để tắt)
kubectl --context kind-llm-sim -n monitoring get secret grafana-admin -o jsonpath='{.data.admin-password}' | base64 -d; echo
kubectl --context kind-llm-sim -n monitoring port-forward svc/kps-grafana 3000:80   # mở http://localhost:3000
```

| Bài | Kiểm gì |
|---|---|
| T1 | Không tải: giữ đúng 1 replica |
| T2 | Tải 2,5 × threshold: scale lên đủ số replica cần |
| T3 | Tắt tải ngay sau T2: scale-down từ từ, không dao động |
| T4 | Mất Prometheus (NetworkPolicy chặn KEDA → Prometheus, ở `common/autoscaling/tests/`): fallback lên max ≤ 30 s (N6) |
| T5 | Tạm dừng autoscaling: số replica đứng yên dù tải đổi |

Ngưỡng đạt/trượt của từng bài nằm trong `tests/run-t1-t5.sh` (theo bảng ở [w2.md §9.3](../../docs/huong-dan/w2.md)); kết quả các lần chạy ở nhật ký của Trình.

## VH2 qua Git: thêm Argo CD vào kind

VH2 cần vòng "commit → Argo CD sync → rolling update → `git revert`" như ở nhà ([Vận hành §5.3, §5.4](../../docs/chi-tiet/04-van-hanh.md#53-quy-trình-cập-nhật-qua-gitops)). Trên kind, vòng này chạy với một nhánh riêng, để commit thử không đụng `main` hay cluster nhà.

```bash
make sim-up                          # nếu cluster chưa có
make sim-argocd ARGOCD_REV=<nhánh>   # Argo CD core + app serving, autoscaling theo nhánh đó (lần thử đầu: 142 s)
```

`make sim-argocd` chờ tới khi cả hai app `Synced Healthy` (tối đa 300 s; hết hạn thì in condition, ví dụ nhánh chưa push). Nếu ScaledObject đang tạm dừng do runner để lại, target báo lệnh gỡ annotation. Argo CD nhận lại Deployment và ScaledObject đang chạy, không tạo pod mới. Sau đó:

- Commit và push lên nhánh `ARGOCD_REV` là cập nhật; Argo CD đọc Git mỗi 2 phút cộng ngẫu nhiên tối đa 1 phút (log `appResyncPeriod=2m0s, appResyncJitter=1m0s` của `argocd-application-controller`). `git revert` rồi push là rollback.
- Self-heal bật: sửa tay ScaledObject hay Deployment thì Argo CD đưa về đúng Git sau vài giây. Muốn đổi thứ gì thì đổi trong Git.
- Runner (`experiments.runner`, `make ops-tests`) dừng ngay khi app `autoscaling` còn auto-sync (`guard_argocd`), giống ở nhà. Chạy runner thì gỡ Argo CD trước (`make sim-argocd-down`). Không dùng `make home-eval-begin`: target đó mặc định nhắm cluster nhà. Ngoại lệ duy nhất là kịch bản `vh2-git` bên dưới: kịch bản này đòi Argo CD đang tự sync.

### Đo VH2 dưới tải: kịch bản `vh2-git`

`experiments/ops/vh.py vh2-git` làm đúng quy trình Vận hành §5.3, §5.4, mỗi bước là một commit push lên nhánh `ARGOCD_REV`: nâng `minReplicaCount` lên 2, đổi `--time-to-first-token` của simulator 200 → 300 ms, `git revert` commit đó, `git revert` commit nâng min. Script không bấm refresh, nên thời gian đo gồm cả chu kỳ đọc Git của Argo CD. Máy tạo tải chạy trong cluster và gọi Service, như các kịch bản VH khác. Nếu một bước lỗi, script revert các commit đã push để nhánh về như trước lượt.

```bash
# Worktree riêng ở nhánh thử, sạch và trùng origin (commit thử không lẫn vào nhánh đang làm việc)
git worktree add -b <nhánh> <thư mục> origin/main && git -C <thư mục> push -u origin <nhánh>
make sim-argocd ARGOCD_REV=<nhánh>
# Trong WSL: python3 của Ubuntu có pyyaml; --git-cmd git.exe để push bằng credential của Windows
python3 -m experiments.ops.vh vh2-git --matrix envs/sim/experiments/matrix.yaml --rate 0.3 \
  --context kind-llm-sim --git-worktree <thư mục> --git-branch <nhánh> --git-cmd git.exe
```

Dùng `--rate 0.3` (khoảng 4 request đồng thời). Ở `--rate 0.5` (trung bình 6–7, nhưng tải Poisson có lúc vượt threshold 10) A2 tự lên 2 replica trước bước nâng min, nên lượt đó không còn là ca 1 replica và script chấm không đạt. Kết quả ở `runs/ops-vh2-git-<thời điểm>/`; `summary.json` có `sync_s` (push xong → Argo CD sync xong) và `total_s` của từng bước.

Đo 25/11 ở `--rate 0.3`, `--duration 2100`: đạt, 615 request, 0 lỗi. Push → sync mất 138–247 s mỗi bước. Rollout 2 pod xong 10–11 s sau sync. TTFT p50 là 206 ms trước cập nhật, 306 ms sau cập nhật và 206 ms sau `git revert`. Push → sync có thể tới khoảng 6 phút: Argo CD so lại với Git mỗi 2–3 phút, còn repo-server giữ commit của nhánh trong cache 3 phút (`--revision-cache-expiration`, mặc định `3m0s`). Lượt thử ở 0,5 req/s có một bước mất 367 s: lần so lúc 2 phút sau push vẫn thấy commit cũ.

Gỡ Argo CD, giữ nguyên simulator và A2 (Application không có finalizer, nên xoá Application không xoá tài nguyên của nó): `make sim-argocd-down`.

## Trên Windows (WSL2)

Chạy mọi lệnh ở trên trong terminal WSL, tại thư mục repo (ví dụ `/mnt/d/…/llm-k8s-autoscaling`).

- **Giữ ít nhất một terminal WSL mở** suốt lúc dùng simulator. Đóng hết terminal thì sau vài giây WSL tắt distro và Docker dừng giữa chừng. Lần mở sau, node kind có thể không lên lại (`Exited (128)`, lỗi `docker-….scope`). Cách sửa ở [W2 §13](../../docs/huong-dan/w2.md#13-lỗi-thường-gặp).
- **Đồng hồ của VM WSL2 có thể chạy nhanh** (máy Trình: 1,6 %). `make sim-test` đo bằng `/proc/uptime` nên không bị ảnh hưởng; khi đo tay bằng `date`, nhớ sai số này ([W2 §13](../../docs/huong-dan/w2.md#13-lỗi-thường-gặp)).
