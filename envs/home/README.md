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
| `argocd/root-app.yaml` | Application gốc (App-of-Apps): trỏ vào `argocd/apps/`, Ansible áp một lần khi dựng |
| `argocd/apps/*.yaml` | Mỗi file một thành phần: GPU device plugin, GPU exporter, kube-prometheus-stack, KEDA, vLLM |
| `serving/` | Overlay vLLM của nhà: model 0,5B, RAM giới hạn, cache trên ổ, Ingress `llm.home` |
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
