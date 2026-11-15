# Chạy ở nhà (`envs/home`)

Môi trường demo và vận hành thử trên GPU thật, chi phí bằng 0. Mọi thứ trên cluster được **Argo CD** đồng bộ từ nhánh `main`: sửa file, merge PR, Argo CD tự áp. Không `kubectl apply` tay những thứ Argo CD quản lý (selfHeal sẽ ghi đè).

| | |
|---|---|
| Máy | PC Ubuntu server, RTX 5060 8 GB, 16 GB RAM; k3s server chạy trên IP Tailscale |
| GPU | 1 GPU vật lý chia thành **2 GPU replica** bằng time-slicing (device plugin) |
| Model | Qwen2.5-0.5B-Instruct (`serving/patch-vllm.yaml`) |
| Dùng để | Demo, kịch bản vận hành (VH2 qua Git), ĐG1-mini, kiểm chứng LT1–LT3. **Không** dùng số đo hiệu năng ở đây cho chương 5 |

## Trong thư mục này

| Đường dẫn | Là gì |
|---|---|
| `argocd/root-app.yaml` | Application gốc (App-of-Apps): trỏ vào `argocd/apps/`, Ansible áp một lần khi dựng. Bỏ qua auto-sync của app `autoscaling`, để tắt được khi đánh giá |
| `argocd/apps/*.yaml` | Mỗi file một thành phần: GPU device plugin, GPU exporter, kube-prometheus-stack (kèm Alertmanager → Telegram), KEDA, vLLM, A2 (`autoscaling`), rule + cảnh báo + dashboard (`observability`) |
| `serving/` | Overlay vLLM của nhà: model 0,5B, RAM giới hạn, cache trên ổ, Ingress `llm.home` |
| `autoscaling/` | Overlay A2 của nhà: tối đa 2 replica (2 GPU replica), threshold 23 |
| `platform/*-values.yaml` | Values Helm riêng của nhà, chồng lên values chung ở `common/platform/` |
| `experiments/` | Ma trận chạy thử (`matrix.yaml`, `matrix-dg1.yaml`) và năng lực đo được (`capacity*.json`) |

Thứ dùng chung (Deployment vLLM, A2, cảnh báo, dashboard) nằm ở `common/`.

## Dựng từ đầu

1. **Inventory:** `ansible/inventory/home.yaml` ghi IP Tailscale và user SSH của PC.
2. **Secret** (không nằm trong Git; Sealed Secrets đã lược, ADR-006 §3.1):

   ```bash
   K="kubectl --context llm-home"
   $K create namespace monitoring  --dry-run=client -o yaml | $K apply -f -
   $K create namespace llm-serving --dry-run=client -o yaml | $K apply -f -
   $K -n monitoring create secret generic grafana-admin \
     --from-literal=admin-user=admin --from-literal=admin-password="$(openssl rand -hex 12)"
   $K -n llm-serving create secret generic vllm-api-key --from-literal=key="$(openssl rand -hex 24)"
   # Bot Telegram của Alertmanager, đọc từ .env (mẫu: .env.example). .env chưa có bot thì chỉ cảnh báo;
   # Alertmanager vẫn chạy, chỉ không gửi được tin.
   make alertmanager-secret CTX=llm-home
   ```

3. **Dựng cluster:** `make home-up` (Ansible: OS, NVIDIA toolkit, k3s, Argo CD, áp `root-app.yaml`). Chạy lại bao nhiêu lần cũng được.
4. **Chờ đồng bộ:** `kubectl --context llm-home -n argocd get applications -w`: mọi app `Synced` / `Healthy` sau 5–10 phút (lâu nhất là kéo image vLLM).

## Chạy demo

```bash
# Gọi API (Ingress của Traefik; chưa có DNS nên chỉ định IP bằng --resolve)
KEY=$(kubectl --context llm-home -n llm-serving get secret vllm-api-key -o jsonpath='{.data.key}' | base64 -d)
curl --resolve llm.home:80:<IP của PC> http://llm.home/v1/chat/completions \
  -H "Authorization: Bearer $KEY" -H 'Content-Type: application/json' \
  -d '{"model":"qwen2.5-0.5b","messages":[{"role":"user","content":"Xin chào"}],"stream":true}'

# Grafana (3 dashboard: Serving + GPU, Autoscaling, SLO + chi phí) tại http://localhost:3000
kubectl --context llm-home -n monitoring port-forward svc/kps-grafana 3000:80

# Một phiên chạy thử bằng runner (máy tạo tải chạy trong cluster)
uv run --project experiments python -m experiments.runner \
  --matrix envs/home/experiments/matrix.yaml --context llm-home

# Kịch bản vận hành dưới tải, ví dụ xoá pod giữa lúc phục vụ (VH3)
make ops-tests S=vh3-delete MATRIX=envs/home/experiments/matrix.yaml RATE=6 CTX=llm-home   # RATE ≈ 0,5 C; C nhà = 12,5
```

Cập nhật cấu hình (VH2) **đi qua Git**: sửa file trong `envs/home/` hoặc `common/`, mở PR, merge; Argo CD tự rollout. Rollback = `git revert`.

## Phiên đánh giá ở nhà

Runner và `make ops-tests` áp ScaledObject của từng lượt bằng `kubectl apply`. Nếu Application `autoscaling` còn auto-sync thì Argo CD áp lại A2 giữa lượt, nên runner kiểm trước và dừng ngay ([Kiến trúc §18.2](../../docs/chi-tiet/03-kien-truc-autoscaling.md#182-cấu-hình-autoscaling-trong-git-tạm-tách-khi-đánh-giá)).

```bash
make home-eval-begin    # trước phiên: tắt auto-sync của A2 (root-app bỏ qua trường này nên không bật lại)
# … chạy runner hoặc make ops-tests …
make home-eval-end      # sau phiên: xoá ScaledObject khác vllm-a2, rồi bật lại auto-sync theo Git (cần yq)
```

- Sau `home-eval-end`, Argo CD đưa A2 về đúng Git sau vài giây, bỏ cả annotation pause mà runner để lại. Phải xoá ScaledObject khác trước, vì webhook của KEDA chặn hai ScaledObject cùng trỏ một Deployment.
- Trong lúc tắt, app `autoscaling` hiện `OutOfSync`, và hiện `Suspended` khi ScaledObject đang pause. Đó là lệch có chủ đích.
- Đừng sync tay root kèm `--sync-option`, vì làm vậy auto-sync bị bật lại (xem comment trong `argocd/root-app.yaml`).
- Ma trận chạy A2 ở nhà phải ghi đè `threshold: 23` và `max_replicas: 2`, giá trị của overlay; nếu không, runner dùng giá trị của VM thuê trong file base.

## Một lần khi thêm app `autoscaling` và `observability`

Merge xong là root tạo ngay app `autoscaling` với auto-sync bật. Vì vậy ba việc đầu phải làm **trước khi merge**:

1. Không có phiên runner hay `make ops-tests` nào đang chạy, vì A2 sẽ bị áp giữa lượt.
2. Xoá ScaledObject khác A2 còn sót từ runner. Nếu còn, webhook của KEDA chặn A2, app `autoscaling` lỗi sync cho đến khi hết lượt `retry`.
3. Áp `root-app.yaml` mới từ nhánh của PR. Root không tự quản lý chính nó. Bản mới chỉ thêm `ignoreDifferences` và `RespectIgnoreDifferences`, vẫn đọc `main`, nên áp trước khi merge cũng không đổi gì trên cluster.

Rồi merge PR, tạo Secret và chờ đồng bộ:

```bash
K="kubectl --context llm-home"
# Trước khi merge (bước 2, 3)
$K -n llm-serving get scaledobject -o name | { grep -v '/vllm-a2$' || true; } | xargs -r $K -n llm-serving delete
$K apply -f envs/home/argocd/root-app.yaml
# Sau khi merge
make alertmanager-secret CTX=llm-home
$K -n argocd get applications -w        # autoscaling, observability, monitoring, keda: Synced / Healthy
```

Kiểm sau khi sync xong:
- ScaledObject `vllm-a2` có `maxReplicaCount` 2 và threshold 23.
- PromQL `kube_scaledobject_status_condition{namespace="llm-serving"}` có 5 chuỗi.
- Alertmanager nhận cảnh báo `Watchdog` mang nhãn `env="home"`. Prometheus chỉ gắn `externalLabels` khi gửi sang Alertmanager, nên chuỗi `ALERTS` trong Prometheus không có nhãn này:
  `$K -n monitoring exec alertmanager-kps-alertmanager-0 -c alertmanager -- amtool alert query alertname=Watchdog --alertmanager.url=http://localhost:9093 -o extended`
- Grafana có 3 dashboard của nhóm.

## Một lần sau khi đổi cấu trúc repo (12/11/2026)

Application gốc trên cluster vẫn trỏ đường dẫn cũ `platform/argocd/apps/home`, nên sau khi merge cấu trúc mới phải áp lại một lần:

```bash
kubectl --context llm-home apply -f envs/home/argocd/root-app.yaml
```

Application gốc đọc `envs/home/argocd/apps/`, cập nhật đường dẫn của các app con (cùng tên nên không app nào bị xoá), rồi các app con sync lại. Manifest render ra không đổi so với trước (đã so từng byte), nên không có pod nào khởi động lại.

## Lưu ý vận hành

- **Không suspend PC** khi vLLM đang chạy: `nvidia-suspend` treo (05/11). Muốn nghỉ thì `shutdown`, hoặc scale vLLM về 0 trước.
- **Không xoá máy hay revoke key của PC trên Tailscale:** k3s chạy trên IP Tailscale, mất Tailscale là cluster mất mạng.
- 2 pod vLLM vừa VRAM nhưng sát RAM 16 GB khi desktop đang chạy; chi tiết ở [nhật ký vận hành](../../docs/nhat-ky/van-hanh.md).
