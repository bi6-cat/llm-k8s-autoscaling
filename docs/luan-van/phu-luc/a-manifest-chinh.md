<!-- Mục đích: Phụ lục A, trích đoạn các manifest chính (Deployment vLLM, overlay VM thuê, ScaledObject A2, Application gốc của Argo CD) mà thân bài dẫn tới ở mục 3.2, 4.1, 4.2, 4.3. Người viết: Trình. -->
<!-- Trích đoạn chép từ main ngày 27/11/2026; commit ghi cạnh mỗi đoạn là commit sửa file đó gần nhất (git log -1 -- <file>). Comment YAML rút gọn từ comment trong repo, không thêm ý mới. Sửa manifest thì cập nhật đoạn trích và commit ở đây. -->

# Phụ lục A. Manifest chính {.unnumbered}

Mã nguồn, manifest và tài liệu thiết kế của đồ án nằm ở repository <https://github.com/bi6-cat/llm-k8s-autoscaling>. Phụ lục này trích những đoạn mà thân bài nhắc tới, mỗi đoạn kèm đường dẫn file và commit. Comment trong file gốc dài hơn, nên ở đây chỉ giữ dòng giải thích tham số chính, còn các khối bỏ bớt được đánh dấu bằng `# …`. Các trường không liên quan tới ý của thân bài, như nhãn, selector, cổng và nodeSelector, được bỏ mà không đánh dấu.
<!-- nguồn: repository công khai của nhóm; cách trích theo quy tắc viết §6 -->

## A.1. Deployment vLLM

Manifest chung của tầng phục vụ nằm ở `common/serving/deployment.yaml` (commit `3101142`). Đoạn mã A.1 giữ ba nhóm khai báo mà mục 3.4 và 4.5 dựa vào: không đặt `replicas`, rolling update không xin thêm GPU, và chuỗi tắt pod an toàn (preStop 20 s, `--shutdown-timeout=150`, grace period 180 s). Image `vllm/vllm-openai` được ghim ở `common/serving/kustomization.yaml` theo tag `v0.31.0` kèm digest.
<!-- nguồn: common/serving/deployment.yaml; common/serving/kustomization.yaml (newTag v0.31.0); commit 3101142 -->

**Đoạn mã A.1.** Deployment vLLM dùng chung cho mọi môi trường (trích)
<!-- nguồn: common/serving/deployment.yaml, commit 3101142 -->

```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: vllm
  namespace: llm-serving
spec:
  # Không đặt replicas: HPA do KEDA tạo quản lý số pod, Argo CD không kéo ngược lại.
  strategy:
    type: RollingUpdate
    # Tắt 1 pod cũ trước rồi mới tạo pod mới, vì pod mới cần GPU mà mọi GPU có thể đang bận.
    rollingUpdate: {maxSurge: 0, maxUnavailable: 1}
  progressDeadlineSeconds: 900
  template:
    spec:
      runtimeClassName: nvidia
      enableServiceLinks: false        # tránh biến VLLM_PORT trùng tên cấu hình của vLLM
      terminationGracePeriodSeconds: 180   # > preStop 20 s + shutdown-timeout 150 s
      containers:
        - name: vllm
          image: vllm/vllm-openai      # tag và digest ghim ở kustomization.yaml
          args:
            - --port=8000
            - --no-enable-prefix-caching   # prompt lặp lại không làm TTFT nhanh bất thường
            - --shutdown-timeout=150       # nhận SIGTERM thì cho request đang chạy tối đa 150 s
          env:
            - name: VLLM_API_KEY
              valueFrom: {secretKeyRef: {name: vllm-api-key, key: key}}
            - {name: HF_HOME, value: /cache/hf}
            - {name: VLLM_CACHE_ROOT, value: /cache/vllm}
          resources:
            limits: {nvidia.com/gpu: 1}
          # …
          startupProbe:                # 5 s × 120 lần = tối đa 10 phút cho cold start
            httpGet: {path: /health, port: http}
            periodSeconds: 5
            failureThreshold: 120
          readinessProbe:
            httpGet: {path: /health, port: http}
            periodSeconds: 5
          livenessProbe:
            httpGet: {path: /health, port: http}
            periodSeconds: 10
            failureThreshold: 6
          lifecycle:
            preStop:
              sleep: {seconds: 20}     # chờ pod được rút khỏi Service trước khi nhận SIGTERM
      volumes:
        - name: cache
          emptyDir: {}                 # overlay nhà và VM thay bằng hostPath
        - name: dshm
          emptyDir: {medium: Memory, sizeLimit: 8Gi}
```

Mỗi môi trường thêm model và tham số theo GPU bằng một JSON patch. Đoạn mã A.2 là overlay của VM thuê ở phiên V2 (`envs/cloud/serving/patch-vllm.yaml`, commit `3101142`): model Qwen2.5-3B-Instruct ghim theo revision, tối đa 64 request chạy cùng lúc mỗi pod, và QoS Guaranteed với 3 lõi CPU, 16 GiB RAM.
<!-- nguồn: envs/cloud/serving/patch-vllm.yaml, commit 3101142 -->

**Đoạn mã A.2.** Overlay của VM thuê nối thêm tham số vLLM và đặt tài nguyên (trích)
<!-- nguồn: envs/cloud/serving/patch-vllm.yaml, commit 3101142 -->

```yaml
- op: add
  path: /spec/template/spec/containers/0/args/-
  value: --model=Qwen/Qwen2.5-3B-Instruct
- op: add
  path: /spec/template/spec/containers/0/args/-
  value: --revision=aa8e72537993ba99e69dfaafa59ed015b17504d1
# …
- op: add
  path: /spec/template/spec/containers/0/args/-
  value: --max-num-seqs=64             # giới hạn đồng thời thật; KV-cache đủ cho ~210 request 1.000 token
- op: add
  path: /spec/template/spec/containers/0/args/-
  value: --gpu-memory-utilization=0.90
- op: replace                          # requests = limits, CPU nguyên: QoS Guaranteed
  path: /spec/template/spec/containers/0/resources
  value:
    requests: {cpu: "3", memory: 16Gi, nvidia.com/gpu: 1}
    limits: {cpu: "3", memory: 16Gi, nvidia.com/gpu: 1}
- op: replace                          # cache model trên ổ NVMe của VM
  path: /spec/template/spec/volumes/0
  value:
    name: cache
    hostPath: {path: /mnt/nvme/cache, type: Directory}
```

## A.2. ScaledObject của cấu hình A2

Đoạn mã A.3 là manifest gốc của A2 (`common/autoscaling/a2/scaledobject-a2.yaml`, commit `3101142`), mà mục 4.3 mô tả. Threshold 24 trong file là giá trị tạm đặt trước khi đo năng lực. Overlay ở nhà đặt 23, overlay simulator đặt 10 kèm tối đa 3 replica. Trên VM thuê không có overlay autoscaling: runner đọc chính file này rồi ghi đè threshold và số replica tối đa theo ma trận `envs/cloud/experiments/matrix-v2.yaml`, nên các lượt A2 của phiên V2 chạy với threshold 37 và tối đa 4 replica.
<!-- nguồn: common/autoscaling/a2/scaledobject-a2.yaml (commit 3101142); envs/home/autoscaling/kustomization.yaml (threshold 23); envs/sim/autoscaling/kustomization.yaml (threshold 10, max 3); envs/cloud/experiments/matrix-v2.yaml dòng 23, 27, 82 (A2_threshold 37, N 4); experiments/runner/configs.py render_scaledobject -->

**Đoạn mã A.3.** ScaledObject A2 scale theo số request đang chạy và đang chờ (trích)
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

## A.3. Application gốc của Argo CD

Ở cluster nhà, Argo CD dựng mọi thành phần theo mẫu App-of-Apps: một Application gốc (`envs/home/argocd/root-app.yaml`, commit `ffee403`) theo dõi thư mục `envs/home/argocd/apps/` trên nhánh `main`, mỗi file trong thư mục là một Application con. Đoạn mã A.4 giữ phần đồng bộ và hai khai báo `ignoreDifferences` mà mục 4.1 giải thích. Khai báo thứ nhất cho phép tắt auto-sync của riêng Application `autoscaling` trước đợt đánh giá mà Application gốc không bật lại.
<!-- nguồn: envs/home/argocd/root-app.yaml, commit ffee403; envs/home/argocd/apps/autoscaling.yaml, commit 91dd660 -->

**Đoạn mã A.4.** Application gốc theo mẫu App-of-Apps (trích)
<!-- nguồn: envs/home/argocd/root-app.yaml, commit ffee403 -->

```yaml
apiVersion: argoproj.io/v1alpha1
kind: Application
metadata:
  name: root-home
  namespace: argocd
spec:
  project: default
  source:
    repoURL: https://github.com/bi6-cat/llm-k8s-autoscaling.git
    targetRevision: main               # chỉ thay đổi đã merge vào main mới lên cluster
    path: envs/home/argocd/apps
  destination:
    server: https://kubernetes.default.svc
    namespace: argocd
  syncPolicy:
    automated: {prune: true, selfHeal: true}
    # Khi sync vẫn giữ giá trị trên cluster của các trường trong ignoreDifferences.
    syncOptions: [RespectIgnoreDifferences=true]
  ignoreDifferences:
    - group: argoproj.io               # auto-sync của app autoscaling được tắt khi đánh giá
      kind: Application
      name: autoscaling
      jsonPointers: [/spec/syncPolicy/automated]
    - group: argoproj.io               # trường Argo CD tự ghi khi refresh hay sync tay
      kind: Application
      jsonPointers:
        - /metadata/annotations/argocd.argoproj.io~1refresh
        - /operation
```

Bảng A.1 liệt kê tám Application con. Ba Application cài Helm chart của bên ngoài, có ghim phiên bản; năm Application còn lại đồng bộ một thư mục của repository.
<!-- nguồn: envs/home/argocd/apps/*.yaml -->

**Bảng A.1.** Tám Application con của Application gốc ở cluster nhà

| Application | Nguồn | Namespace đích |
|---|---|---|
| `autoscaling` | `envs/home/autoscaling` | `llm-serving` |
| `gpu-device-plugin` | Chart NVIDIA device plugin 0.20.1, giá trị trong repository | `gpu` |
| `gpu-exporter` | `common/platform/gpu-exporter` | `gpu` |
| `keda` | Chart KEDA 2.21.0, giá trị trong repository | `keda` |
| `monitoring` | Chart kube-prometheus-stack 92.1.1, giá trị trong repository | `monitoring` |
| `monitoring-extras` | `common/platform/kube-prometheus-stack-extras` | `monitoring` |
| `observability` | `common/observability` | `monitoring` |
| `serving` | `envs/home/serving` | `llm-serving` |
<!-- nguồn: envs/home/argocd/apps/*.yaml (spec.source(s), spec.destination.namespace), main 27/11/2026 -->
