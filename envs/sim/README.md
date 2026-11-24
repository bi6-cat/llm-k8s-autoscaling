# Chạy trên simulator (`envs/sim`)

Kiểm thử vòng autoscaling **không cần GPU**: cluster kind trên laptop, `llm-d-inference-sim` đóng vai vLLM (cùng API OpenAI, cùng metric `vllm:*`, trả lời có độ trễ giả lập). Dựng lại trong vài phút, nên dùng để thử mọi thay đổi về KEDA, PromQL, cảnh báo và runner trước khi đưa lên GPU thật.

| | |
|---|---|
| Cluster | kind `llm-sim` (context `kind-llm-sim`), 1 control-plane + 2 worker (`kind-config.yaml`; 2 worker để thử drain node) |
| "vLLM" | Simulator: cùng Deployment và Service với vLLM thật (overlay `serving/` chỉ đổi image và tham số) |
| Autoscaling | A2 thật (`common/autoscaling/a2`), threshold và max replica hợp với simulator (`autoscaling/`) |
| Cài đặt | helm và kubectl trực tiếp, **không** qua Argo CD (cluster dựng đi dựng lại liên tục) |
| Số đo | Chỉ kiểm logic (đạt/trượt, thời gian phản ứng của KEDA). **Không** phải số đo hiệu năng |

## Cần có

| | |
|---|---|
| Máy | Linux có Docker Engine. Trên Windows: WSL2 Ubuntu 24.04 có Docker Engine, không cần Docker Desktop (xem [Trên Windows](#trên-windows-wsl2)). Sau `make sim-up`, ba node kind dùng khoảng 2,9 GB RAM (đo 24/11) |
| Công cụ | `make`, `docker`, `kind`, `kubectl`, `helm`, `hey`, `openssl`; thêm `uv` cho runner, LT7, LT8 và phân tích. Lệnh cài: [W1 §4.2](../../docs/huong-dan/w1.md#42-công-cụ). Bản đã ghim: [phien-ban.md](../../docs/phien-ban.md) |
| Mạng | Lần đầu tải node image của kind (khoảng 1,3 GB), chart Helm, và image của Prometheus, KEDA, simulator |
| Telegram (tuỳ chọn) | `.env` có `ALERTMANAGER_TELEGRAM_BOT_TOKEN` và `ALERTMANAGER_TELEGRAM_CHAT_ID` (mẫu ở `.env.example`) thì `make sim-up` tạo Secret, và cảnh báo nào kêu trên kind cũng được gửi thật. Không có thì lệnh chỉ in cảnh báo rồi chạy tiếp |

Muốn dựng thử mà không gửi tin dù `.env` đã có bot: đặt hai biến giả trong môi trường. Script `common/platform/alertmanager-secret.sh` ưu tiên biến môi trường hơn `.env`, và chỉ kiểm dạng `<số>:<chuỗi>`:

```bash
ALERTMANAGER_TELEGRAM_BOT_TOKEN=1:fake ALERTMANAGER_TELEGRAM_CHAT_ID=1 make sim-up
```

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

## Chạy

```bash
make sim-up                    # kind + Prometheus + KEDA + simulator + A2 (~6 phút, phần lớn là chart Prometheus)
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

# Grafana: mở http://localhost:3000, đăng nhập admin với mật khẩu in ra ở lệnh thứ hai
kubectl --context kind-llm-sim -n monitoring port-forward svc/kps-grafana 3000:80
kubectl --context kind-llm-sim -n monitoring get secret grafana-admin -o jsonpath='{.data.admin-password}' | base64 -d; echo
```

| Bài | Kiểm gì |
|---|---|
| T1 | Không tải: giữ đúng 1 replica |
| T2 | Tải 2,5 × threshold: scale lên đủ số replica cần |
| T3 | Tắt tải ngay sau T2: scale-down từ từ, không dao động |
| T4 | Mất Prometheus (NetworkPolicy chặn KEDA → Prometheus, ở `common/autoscaling/tests/`): fallback lên max ≤ 30 s (N6) |
| T5 | Tạm dừng autoscaling: số replica đứng yên dù tải đổi |

Ngưỡng đạt/trượt của từng bài nằm trong `tests/run-t1-t5.sh` (theo bảng ở [w2.md §9.3](../../docs/huong-dan/w2.md)); kết quả các lần chạy ở nhật ký của Trình.

## Trên Windows (WSL2)

Chạy mọi lệnh ở trên trong terminal WSL, tại thư mục repo (ví dụ `/mnt/d/…/llm-k8s-autoscaling`).

- **Giữ ít nhất một terminal WSL mở** suốt lúc dùng simulator. Đóng hết terminal thì sau vài giây WSL tắt distro và Docker dừng giữa chừng. Lần mở sau, node kind có thể không lên lại (`Exited (128)`, lỗi `docker-….scope`). Cách sửa ở [W2 §13](../../docs/huong-dan/w2.md#13-lỗi-thường-gặp).
- **Đồng hồ của VM WSL2 có thể chạy nhanh** (máy Trình: 1,6 %). `make sim-test` đo bằng `/proc/uptime` nên không bị ảnh hưởng; khi đo tay bằng `date`, nhớ sai số này ([W2 §13](../../docs/huong-dan/w2.md#13-lỗi-thường-gặp)).
