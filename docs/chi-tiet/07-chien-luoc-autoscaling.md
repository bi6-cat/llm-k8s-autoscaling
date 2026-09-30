# 7. Thiết kế các chiến lược autoscaling: tài liệu chuyên sâu

> Thuộc [Mục 7 của bản mô tả chính](../mo-ta-chi-tiet-do-an.md#7-thiết-kế-các-chiến-lược-autoscaling) · [Danh mục tài liệu chuyên sâu](README.md)

**Tóm tắt nhanh**
- Mọi chiến lược dùng **cùng một cơ chế**: KEDA đưa kết quả PromQL cho HPA, và HPA tính ⌈tổng ÷ target⌉. **Chỉ có metric là khác nhau.**
- Phân tích từng metric: vì sao **A1 (GPU utilization)** bão hoà; vì sao **A2 (running + waiting)** tỷ lệ với tải theo định luật Little; A3 (KV-cache) nhạy với độ dài request; A4 (chỉ hàng đợi) gây **flapping**.
- Target được **tính từ dữ liệu hiệu chỉnh**, không chọn cảm tính.
- Có YAML đầy đủ cho S1, S4, A1–A4; PromQL chống lỗi; bài kiểm thử nhanh trên laptop; và các cạm bẫy khi vận hành.

---

## 1. Cơ chế chung và mô hình thời gian

```text
vLLM/DCGM ──scrape 5 s──► Prometheus ◄──PromQL── KEDA metrics server ◄──hỏi mỗi chu kỳ sync── HPA
                                                                                          │
                              desired = ceil( giá trị PromQL (tổng) ÷ threshold )           │
                              → behavior (stabilization, policies) → [min, max]            ▼
                                                                          Deployment.spec.replicas
```

- Chu kỳ sync của HPA đặt **5 s** (tham số của k3s). Mặc định là 15 s, và đó mới là bên quyết định tốc độ phát hiện khi scale giữa 1 và N (xem [04 §4.3](04-kien-thuc-nen.md#43-keda)).
- `pollingInterval` của KEDA vẫn đặt 5 s cho đồng bộ, nhưng tham số này chủ yếu ảnh hưởng việc kích hoạt 0 ↔ 1 (không dùng trong đồ án) và cache metric.
- `metricType: AverageValue` cho mọi trigger, để công thức thống nhất là ⌈tổng ÷ threshold⌉.

---

## 2. Danh sách cấu hình

| Mã | Tín hiệu | PromQL (tổng toàn Deployment) | threshold (mỗi replica) | Vai trò |
|---|---|---|---|---|
| S1 | – | – | – (cố định 1 replica) | Cận dưới chi phí |
| S4 | – | – | – (cố định 4 replica) | Cận trên hiệu năng |
| A1 | GPU utilization | `sum(DCGM_FI_DEV_GPU_UTIL{…pod vllm…})` | 70 | Baseline "truyền thống" |
| **A2** | Tải đồng thời | `sum(vllm:num_requests_running) + sum(vllm:num_requests_waiting)` | 0,8 × B\* | **Đề xuất chính** |
| A3 | KV-cache | `sum(vllm:kv_cache_usage_perc)` | 0,8 × KV\* | Đề xuất phụ |
| A4 (tuỳ chọn) | Chỉ hàng đợi | `sum(vllm:num_requests_waiting)` | ví dụ 5 | Minh hoạ flapping |

Trong đó B\* và KV\* là giá trị đo được tại C (xem §4).

---

## 3. Phân tích từng metric

### 3.1. A1: GPU utilization

**Đo gì:** tỷ lệ thời gian GPU có kernel đang chạy (xem [04 §5.4](04-kien-thuc-nen.md#54-vì-sao-gpu_util-bão-hoà)).

**Hành vi dự đoán:**
- Chỉ cần có vài request, `GPU_UTIL` đã khoảng 90–100%. Với threshold 70 và 1 replica: desired = ⌈95 ÷ 70⌉ = 2. Với 2 replica, mỗi pod vẫn khoảng 95%: desired = ⌈190 ÷ 70⌉ = 3. Quá trình cứ thế **leo lên tối đa** ngay khi mỗi pod có tải, dù là tải nhẹ.
- Ngược lại, khi tải rất thấp (KB1, 0,5C, có những khoảng không có request), `GPU_UTIL` dao động theo từng đợt request, nên có thể scale lên rồi xuống thất thường.
- Kết luận dự kiến: A1 **gần như Static-4 cộng thêm độ trễ cold start**, tức là không tiết kiệm GPU-giờ. Tệ hơn, nó có thể dao động khi tải thấp.

**Biến thể A1′ (không khả thi trên RTX 4090, ADR-001):** dùng `DCGM_FI_PROF_SM_ACTIVE` hoặc `DCGM_FI_PROF_DRAM_ACTIVE`, phản ánh mức làm việc thật tốt hơn. Nếu các metric này có trên GPU thuê, A1′ là đối chứng thú vị: *metric phần cứng "tốt" so với metric ứng dụng*.

**Công bằng:** chu kỳ thu metric DCGM phải là 5 s, giống vLLM (xem [05 §6](05-kien-truc-he-thong.md#6-vòng-lặp-autoscaling-và-mô-hình-thời-gian)).

### 3.2. A2: số request đồng thời (running + waiting)

**Cơ sở lý thuyết: định luật Little.** Ở trạng thái ổn định, số request đang có trong hệ thống bằng tốc độ đến nhân thời gian trung bình mỗi request lưu lại:

$$
B = \lambda \times \overline{E2E}
$$

Khi hệ thống chưa quá tải, E2E gần như không đổi, nên **B tỷ lệ thuận với λ**. B là thước đo trực tiếp của lượng việc đang có trong hệ thống. Khi quá tải, request dồn vào hàng đợi, B tăng nhanh hơn λ, và HPA scale mạnh hơn. Đây đúng là hành vi mong muốn.

**Vì sao cộng cả running và waiting:**
- Chỉ `running` thì bị chặn trên bởi `max-num-seqs`: khi pod bão hoà, metric không tăng thêm nữa và không phản ánh phần tải vượt.
- Chỉ `waiting` thì bằng 0 khi chưa quá tải, gây flapping (§3.4).
- Tổng hai giá trị vừa tỷ lệ với tải khi bình thường, vừa "bùng lên" khi quá tải.

**Điểm yếu:** request có output dài làm B lớn hơn ở cùng λ. Nhưng đó cũng là tải thật về số token phải sinh, nên có thể coi là ưu điểm. Nếu độ dài request thay đổi theo thời gian, B\* đo lúc hiệu chỉnh có thể không còn đúng (ghi thành hạn chế).

### 3.3. A3: KV-cache usage

**Đo gì:** tỷ lệ số block KV đang được dùng, cộng trên các pod.

**Hành vi dự đoán:**
- Tỷ lệ với **tổng số token đang nằm trong hệ thống**, không phải số request. Prompt dài làm metric tăng nhanh; prompt ngắn làm nó tăng chậm.
- Trong một request, KV tăng dần theo từng token được sinh. Metric vì thế **đi sau** một nhịp so với lúc request đến, nhưng vẫn nhanh hơn TTFT tính từ histogram.
- Nếu nút thắt là **sức tính** (prompt ngắn, batch lớn) chứ không phải bộ nhớ, KV-cache có thể còn thấp trong khi TTFT đã tăng. Khi đó A3 scale **quá muộn**.
- Khi KV gần 1, preemption xảy ra. Đó là dấu hiệu quá tải rõ ràng nhưng đã muộn.

**Lưu ý:** khi bật prefix caching, cách tính "đang dùng" có thể bao gồm cả block đã cache. Đây thêm một lý do để tắt prefix caching trong thí nghiệm.

### 3.4. A4: chỉ hàng đợi (minh hoạ flapping)

![Hình 14 – Flapping](../images/14-flapping.svg)

*Hình 14. Khi tải ổn định ở mức cao, A4 scale-up xong thì hàng đợi về 0. HPA tính ra 1 replica, và sau cửa sổ ổn định lại scale-down, gây quá tải lần nữa. Chu kỳ này lặp lại.*

Diễn biến cụ thể: sau khi scale-up, 3 replica xử lý hết hàng đợi, nên `waiting = 0` và desired = ⌈0 ÷ 5⌉ = 0 → kẹp về minReplicas = 1. Stabilization giữ nguyên 5 phút, rồi scale-down từng pod mỗi 60 s. Khi năng lực giảm xuống dưới tải, hàng đợi tăng trở lại và hệ thống scale-up. Nhưng mỗi lần scale-up lại phải chịu thêm một lần cold start.

### 3.5. Các tín hiệu đã cân nhắc nhưng không chọn

| Tín hiệu | Vì sao không chọn làm chiến lược chính |
|---|---|
| RPS (số request/giây) | Bỏ qua độ dài request; target phải đoán trước từ C; sai khi phân phối độ dài thay đổi |
| TTFT p95 (histogram) | **Tín hiệu trễ**: phải chờ request xong phần prefill và phải qua cửa sổ `rate()` 1 phút. Có vòng phản hồi (scale làm TTFT giảm, rồi lại scale-down). Hợp làm "chốt chặn" trong trigger phụ ([15 – E6](15-huong-mo-rong.md#e6-scale-theo-slo-và-kết-hợp-nhiều-trigger)) |
| Token/s | Bão hoà khi GPU đầy, giống `running` |
| CPU của pod | Phản ánh API server, không phản ánh GPU |

### 3.6. Bảng so sánh

| | A1 GPU util | A2 running + waiting | A3 KV-cache | A4 waiting |
|---|---|---|---|---|
| Phản ánh | Có kernel chạy hay không | Số request trong hệ thống | Số token trong hệ thống | Phần quá tải |
| Tỷ lệ với tải? | Không (bão hoà) | **Có** (Little) | Gần đúng (phụ thuộc độ dài) | Không (0 khi chưa quá tải) |
| Độ trễ tín hiệu | Thấp (nếu chu kỳ thu 5 s) | Thấp (gauge) | Thấp–vừa | Thấp |
| Nguy cơ | Scale quá tay, luôn ở mức tối đa | Target sai khi độ dài request đổi | Scale muộn khi nút thắt là sức tính | Flapping |
| Dự đoán | ≈ S4 + cold start | Tốt nhất | Tốt, kém A2 khi prompt ngắn | Dao động |

---

## 4. Chọn target từ dữ liệu hiệu chỉnh

![Hình 15 – Hiệu chỉnh năng lực](../images/15-hieu-chinh-nang-luc.svg)

*Hình 15. Quét tốc độ request trên 1 replica. C là mức lớn nhất còn đạt SLO; B\* là số request đồng thời tại C (số liệu minh hoạ).*

| Chiến lược | Giá trị đo tại C | threshold | Lý do |
|---|---|---|---|
| A1 | GPU_UTIL tại C (có thể khoảng 95–100) | 70 (phổ biến) | Giữ đúng cách "mọi người hay làm" để kiểm chứng giả thuyết |
| A2 | B\* (ví dụ 30) | **0,8 × B\* (= 24)** | Chừa 20% để hấp thụ dao động trong lúc chờ cold start |
| A3 | KV\* (ví dụ 0,55) | 0,8 × KV\* (≈ 0,44) | Như A2 |

**Vì sao chọn hệ số 0,8?** Hệ số này giữ mỗi pod ở khoảng ρ ≈ 0,8 × (C/μ), dưới "đầu gối" của đường cong (Hình 10). Hệ số thấp hơn (0,6) thì an toàn hơn nhưng tốn GPU hơn; hệ số cao hơn (0,95) thì rẻ hơn nhưng dễ vi phạm SLO. Nếu còn thời gian, nhóm thử thêm {0,6; 0,8; 0,95} cho A2 ở KB2 và KB5 (nghiên cứu độ nhạy).

---

## 5. Tham số hành vi

| Tham số | Giá trị | Lý do |
|---|---|---|
| `minReplicaCount` | 1 | Không scale về 0 (cold start dài) |
| `maxReplicaCount` | 4 | Bằng số GPU và bằng S4 để so sánh công bằng |
| scaleUp | **Giữ mặc định**: cửa sổ 0, tăng 100% hoặc +4 pod mỗi 15 s | Cold start đã chậm, nên scale-up phải quyết đoán |
| scaleDown `stabilizationWindowSeconds` | 300 | Tránh scale-down ngay sau một đợt giảm tải ngắn |
| scaleDown policy | 1 pod mỗi 60 s | Giảm dần, dễ quan sát |
| HPA sync period | 5 s (k3s) | Phát hiện nhanh |
| tolerance | 10% (mặc định) | – |
| `fallback` | `failureThreshold: 3`, `replicas: 4` | Nếu Prometheus sập thì cấp tối đa, an toàn cho SLO |

---

## 6. YAML đầy đủ

### 6.1. Cấu hình tĩnh

Runner đặt số replica trực tiếp, và **đảm bảo không còn ScaledObject nào** trỏ vào Deployment:

```bash
kubectl -n llm-serving delete scaledobject --all --wait
kubectl -n llm-serving scale deploy/vllm --replicas=4        # S4 (hoặc 1 cho S1)
kubectl -n llm-serving rollout status deploy/vllm --timeout=15m
```

### 6.2. Mẫu dùng chung (A2)

```yaml
apiVersion: keda.sh/v1alpha1
kind: ScaledObject
metadata:
  name: vllm-a2
  namespace: llm-serving
  labels: {experiment/config: A2}
spec:
  scaleTargetRef: {name: vllm}
  minReplicaCount: 1
  maxReplicaCount: 4
  pollingInterval: 5
  fallback: {failureThreshold: 3, replicas: 4}
  advanced:
    horizontalPodAutoscalerConfig:
      behavior:
        scaleDown:
          stabilizationWindowSeconds: 300
          policies: [{type: Pods, value: 1, periodSeconds: 60}]
  triggers:
    - type: prometheus
      metricType: AverageValue
      metadata:
        serverAddress: http://prometheus-operated.monitoring.svc:9090
        query: |
          (sum(vllm:num_requests_running{namespace="llm-serving"}) or vector(0))
          + (sum(vllm:num_requests_waiting{namespace="llm-serving"}) or vector(0))
        threshold: "24"
```

### 6.3. A1, A3, A4 chỉ khác phần `triggers`

```yaml
# A1: GPU utilization. Kiểm tra tên label pod/namespace trong metric DCGM của cluster mình.
# Nếu dùng nvidia_gpu_exporter thay DCGM: sum(nvidia_smi_utilization_gpu_ratio) * 100
query: sum(DCGM_FI_DEV_GPU_UTIL{exported_namespace="llm-serving"}) or vector(0)
threshold: "70"

# A3: KV-cache
query: sum(vllm:kv_cache_usage_perc{namespace="llm-serving"}) or vector(0)
threshold: "0.44"

# A4: chỉ hàng đợi (tuỳ chọn)
query: sum(vllm:num_requests_waiting{namespace="llm-serving"}) or vector(0)
threshold: "5"
```

### 6.4. PromQL chống lỗi

- `or vector(0)`: khi chưa có pod nào xuất metric (ví dụ đúng lúc khởi động), truy vấn trả về rỗng. Không có vế này, KEDA sẽ báo lỗi và kích hoạt fallback.
- Luôn lọc theo `namespace` để không cộng nhầm metric của pod khác.
- Metric DCGM: xác định đúng label chỉ pod vLLM (`pod`/`exported_pod`, `namespace`/`exported_namespace`) bằng cách chạy truy vấn thử trên Prometheus.
- Kiểm tra giá trị mà HPA đang thấy: `kubectl get hpa keda-hpa-vllm-a2 -o yaml`, phần `status.currentMetrics`.

---

## 7. Cạm bẫy khi vận hành

| Cạm bẫy | Biểu hiện | Cách tránh |
|---|---|---|
| Argo CD tranh `replicas` với HPA | Số replica bị đặt lại liên tục | Bỏ `replicas` khỏi manifest hoặc dùng `ignoreDifferences` ([05 §10.3](05-kien-truc-he-thong.md#103-cạm-bẫy-argo-cd-và-hpa-tranh-nhau-replicas)) |
| Còn sót ScaledObject của lượt trước | Hai HPA cùng trỏ một Deployment và "đánh nhau" | Runner xoá mọi ScaledObject trước khi áp cái mới; KEDA admission webhook cũng chặn trường hợp này |
| Pod Pending vì hết GPU | desired lớn hơn số GPU | `maxReplicaCount` = số GPU |
| Chu kỳ scrape và sync mặc định | Phát hiện chậm khoảng 45 s | Chỉnh về 5 s như §5 |
| KV-cache bị cache ảo | A3 cao dù ít request | Tắt prefix caching |
| Target sai sau khi đổi dạng tải | A2 scale lệch | Hiệu chỉnh lại B\* nếu đổi phân phối độ dài prompt/output |

---

## 8. Kiểm thử nhanh cấu hình autoscaling

Làm trên laptop (hoặc với simulator) **trước khi lên cloud**. Mỗi bài có kết quả mong đợi tính được bằng tay:

| Bài | Thao tác | Kết quả mong đợi |
|---|---|---|
| T1 | A2, tải bằng 0 | Giữ 1 replica |
| T2 | A2, tạo khoảng 2,5 × threshold request đồng thời | desired = 3 trong vòng khoảng 10 s; `status.currentMetrics` đúng giá trị |
| T3 | Tắt tải | Giữ 3 replica trong 300 s, rồi giảm 1 pod mỗi 60 s |
| T4 | Chặn Prometheus (scale deploy prometheus về 0) | Sau 3 lần lỗi, fallback lên 4 replica |
| T5 | Annotation `paused-replicas: "1"` | Giữ đúng 1 replica bất kể tải |
| T6 | Chuyển từ A2 sang A1 | Chỉ còn một HPA; không có dao động ngoài ý muốn |

Ghi kết quả vào nhật ký. Đây cũng là tư liệu cho chương "Triển khai" trong luận văn.

---

## 9. Nghiên cứu độ nhạy (tuỳ chọn)

| Tham số | Giá trị thử | Kịch bản | Câu hỏi |
|---|---|---|---|
| Hệ số target của A2 | 0,6 / 0,8 / 0,95 | KB2, KB5 | Đánh đổi giữa SLO và GPU-giờ thay đổi thế nào? |
| `stabilizationWindowSeconds` | 60 / 300 / 600 | KB4, KB5 | Scale-down nhanh có gây flapping hay vi phạm SLO không? |
| HPA sync period | 5 s / 15 s | KB2 | Độ trễ phát hiện chiếm bao nhiêu phần trong thời gian phản ứng? |

---

## 10. Câu hỏi hội đồng có thể đặt ra

**Sao không kết hợp nhiều metric trong một ScaledObject?**
KEDA hỗ trợ nhiều trigger, và HPA sẽ lấy giá trị desired **lớn nhất** trong các trigger. Đồ án cố ý tách riêng từng metric để trả lời RQ1. Kết hợp nhiều metric được đặt ở hướng mở rộng E6.

**Target 0,8 × B\* có phụ thuộc model không?**
Có. B\* phụ thuộc model, GPU và phân phối độ dài request. Vì vậy **quy trình để tìm ra target** (hiệu chỉnh rồi nhân hệ số) mới là khuyến nghị, không phải con số 24.

**Nếu A1 cho SLO tốt thì sao?**
Khi đó phải xem **GPU-giờ**. Nếu A1 luôn chạy tối đa replica, SLO tốt chỉ vì nó hoạt động như Static-4, và A1 không đạt mục tiêu tiết kiệm. RQ3 được thiết kế để làm rõ trường hợp này.
