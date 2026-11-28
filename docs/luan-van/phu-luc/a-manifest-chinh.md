<!-- Mục đích: Phụ lục A, trích đoạn các manifest chính (Deployment vLLM, ScaledObject A2, Application con của Argo CD) mà thân bài dẫn tới ở mục 3.2, 4.1, 4.2, 4.3. Người viết: Trình. -->
<!-- Trích đoạn chép từ main ngày 27/11/2026; commit ghi cạnh mỗi đoạn là commit sửa file đó gần nhất (git log -1 -- <file>). Comment YAML rút gọn từ comment trong repo, không thêm ý mới. Sửa manifest thì cập nhật đoạn trích và commit ở đây. -->
<!-- Rút gọn 28/11 (bản nộp: phụ lục A 5 tr, đích ≤ 2,5 tr). Ý không đưa vào, người đọc tra trong repository: phần còn lại của Deployment vLLM (cờ --no-enable-prefix-caching, để prompt lặp lại không làm TTFT nhanh bất thường, mục 4.2 đã nêu; progressDeadlineSeconds 900, runtimeClassName nvidia, enableServiceLinks false, env VLLM_API_KEY từ Secret vllm-api-key, HF_HOME, VLLM_CACHE_ROOT, readinessProbe 5 s, livenessProbe 10 s × 6, volume cache emptyDir và dshm 8Gi; common/serving/deployment.yaml, commit 3101142); đoạn mã overlay VM thuê (envs/cloud/serving/patch-vllm.yaml, commit 3101142: --model Qwen2.5-3B-Instruct ghim revision aa8e725, --max-num-seqs=64, --gpu-memory-utilization=0.90, requests = limits 3 CPU 16Gi 1 GPU, cache hostPath /mnt/nvme/cache; mục 4.2 đã nêu đủ); YAML của Application gốc root-home (envs/home/argocd/root-app.yaml, commit ffee403: targetRevision main, path envs/home/argocd/apps, automated prune + selfHeal, RespectIgnoreDifferences=true, ignoreDifferences /spec/syncPolicy/automated của app autoscaling và annotation refresh, /operation của mọi Application; mục 4.1 đã giải thích bằng lời). -->

# Phụ lục A. Manifest chính {.unnumbered}

Mã nguồn, manifest và tài liệu thiết kế của đồ án nằm ở repository <https://github.com/bi6-cat/llm-k8s-autoscaling>. Phụ lục này trích những đoạn mà thân bài nhắc tới, mỗi đoạn kèm đường dẫn file và commit. Comment trong file gốc dài hơn, nên ở đây chỉ giữ dòng giải thích tham số chính, còn các khối bỏ bớt được đánh dấu bằng `# …`. Các trường không liên quan tới ý của thân bài, như nhãn, selector, cổng và nodeSelector, được bỏ mà không đánh dấu.
<!-- nguồn: repository công khai của nhóm; cách trích theo quy tắc viết §6 -->

## A.1. Deployment vLLM

Manifest chung của tầng phục vụ nằm ở `common/serving/deployment.yaml` (commit `3101142`). Đoạn mã A.1 là phần spec của Deployment `vllm` trong namespace `llm-serving`, mà ScaledObject ở Đoạn mã A.2 trỏ tới. Đoạn trích chỉ giữ các trường mà mục 3.4 và 4.5 dựa vào. Deployment không đặt `replicas`, rolling update không xin thêm GPU, startup probe cho phép cold start tới 10 phút, và pod được tắt an toàn bằng preStop 20 s, `--shutdown-timeout=150` cùng grace period 180 s. Các trường khác, như biến môi trường, readiness probe, liveness probe và volume mà mục 4.2 mô tả, được bỏ, và vài khối được viết gọn trên một dòng. Image `vllm/vllm-openai` được ghim ở `common/serving/kustomization.yaml` theo tag `v0.31.0` kèm digest. Model và tham số theo GPU của từng môi trường được nối vào bằng JSON patch, ví dụ `envs/cloud/serving/patch-vllm.yaml` cho VM thuê ở phiên V2.
<!-- nguồn: common/serving/deployment.yaml; common/serving/kustomization.yaml (newTag v0.31.0); envs/cloud/serving/patch-vllm.yaml; commit 3101142 -->

**Đoạn mã A.1.** Deployment vLLM dùng chung cho mọi môi trường (trích)
<!-- nguồn: common/serving/deployment.yaml, commit 3101142 -->

```yaml
spec:                  # không đặt replicas: HPA do KEDA tạo quản lý số pod
  strategy:            # tắt 1 pod cũ trước, vì GPU có thể đang bận hết
    rollingUpdate: {maxSurge: 0, maxUnavailable: 1}
  template:
    spec:
      terminationGracePeriodSeconds: 180  # > preStop 20 s + 150 s
      containers:
        - name: vllm
          args: [--port=8000, --shutdown-timeout=150]  # SIGTERM: chờ ≤ 150 s
          ports: [{name: http, containerPort: 8000}]
          resources: {limits: {nvidia.com/gpu: 1}}
          startupProbe:    # 5 s × 120 lần = tối đa 10 phút cold start
            httpGet: {path: /health, port: http}
            periodSeconds: 5
            failureThreshold: 120
          lifecycle:       # chờ rút pod khỏi Service rồi mới SIGTERM
            preStop: {sleep: {seconds: 20}}
```

## A.2. ScaledObject của cấu hình A2

Đoạn mã A.2 là manifest gốc của A2 (`common/autoscaling/a2/scaledobject-a2.yaml`, commit `3101142`), mà mục 4.3 mô tả. Threshold 24 trong file là giá trị tạm đặt trước khi đo năng lực. Overlay ở nhà đặt 23, overlay simulator đặt 10 kèm tối đa 3 replica. Trên VM thuê không có overlay autoscaling: runner đọc chính file này rồi ghi đè threshold và số replica tối đa theo ma trận `envs/cloud/experiments/matrix-v2.yaml`, nên các lượt A2 của phiên V2 chạy với threshold 37 và tối đa 4 replica.
<!-- nguồn: common/autoscaling/a2/scaledobject-a2.yaml (commit 3101142); envs/home/autoscaling/kustomization.yaml (threshold 23); envs/sim/autoscaling/kustomization.yaml (threshold 10, max 3); envs/cloud/experiments/matrix-v2.yaml dòng 23, 27, 82 (A2_threshold 37, N 4); experiments/runner/configs.py render_scaledobject -->

**Đoạn mã A.2.** ScaledObject A2 scale theo số request đang chạy và đang chờ (trích)
<!-- nguồn: common/autoscaling/a2/scaledobject-a2.yaml, commit 3101142 -->

```yaml
apiVersion: keda.sh/v1alpha1
kind: ScaledObject
metadata:
  name: vllm-a2
  namespace: llm-serving
spec:
  scaleTargetRef: {name: vllm}
  minReplicaCount: 1                   # cold start vài phút nên không scale về 0
  maxReplicaCount: 4                   # bằng số GPU của VM thuê
  pollingInterval: 5
  # Lỗi khi hỏi Prometheus quá 3 lần liên tiếp thì HPA nhận giá trị giả để lên 4 replica.
  fallback: {failureThreshold: 3, replicas: 4}
  advanced:
    horizontalPodAutoscalerConfig:
      behavior:
        scaleDown:                     # scale-up giữ mặc định của HPA
          stabilizationWindowSeconds: 300
          policies: [{type: Pods, value: 1, periodSeconds: 60}]
  triggers:
    - type: prometheus
      metricType: AverageValue         # desired = ⌈tổng ÷ threshold⌉
      metadata:
        serverAddress: http://prometheus-operated.monitoring.svc:9090
        query: |
          (sum(vllm:num_requests_running{namespace="llm-serving"}) or vector(0))
          + (sum(vllm:num_requests_waiting{namespace="llm-serving"}) or vector(0))
        threshold: "24"                # giá trị tạm; phiên V2 ghi đè thành 37
        timeout: "1000"                # ms cho mỗi lần hỏi Prometheus
```

## A.3. Application của Argo CD

Ở cluster nhà, Argo CD dựng mọi thành phần theo mẫu App-of-Apps. Application gốc (`envs/home/argocd/root-app.yaml`, commit `ffee403`) theo dõi thư mục `envs/home/argocd/apps/` trên nhánh `main`, bật prune và self-heal, và bỏ qua trường bật tắt auto-sync của riêng Application `autoscaling` như mục 4.1 giải thích. Mỗi file trong thư mục là một Application con. Bảng A.1 liệt kê tám Application con: ba Application cài Helm chart của bên ngoài, có ghim phiên bản; năm Application còn lại đồng bộ một thư mục của repository.
<!-- nguồn: envs/home/argocd/root-app.yaml, commit ffee403; envs/home/argocd/apps/autoscaling.yaml, commit 91dd660; envs/home/argocd/apps/*.yaml -->

**Bảng A.1.** Tám Application con của Application gốc ở cluster nhà

| Application | Nguồn | Namespace đích |
|-------|-------------|------|
| `autoscaling` | `envs/home/autoscaling` | `llm-serving` |
| `gpu-device-plugin` | Chart NVIDIA device plugin 0.20.1, giá trị trong repository | `gpu` |
| `gpu-exporter` | `common/platform/gpu-exporter` | `gpu` |
| `keda` | Chart KEDA 2.21.0, giá trị trong repository | `keda` |
| `monitoring` | Chart kube-prometheus-stack 92.1.1, giá trị trong repository | `monitoring` |
| `monitoring-extras` | `common/platform/kube-prometheus-stack-extras` | `monitoring` |
| `observability` | `common/observability` | `monitoring` |
| `serving` | `envs/home/serving` | `llm-serving` |
<!-- nguồn: envs/home/argocd/apps/*.yaml (spec.source(s), spec.destination.namespace), main 27/11/2026 -->
