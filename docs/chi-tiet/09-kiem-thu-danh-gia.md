# 9. Kiểm thử và đánh giá: tài liệu chuyên sâu

> Thuộc [Mục 9 của bản mô tả chính](../mo-ta-chi-tiet-do-an.md#9-kiểm-thử-và-đánh-giá) · [Danh mục tài liệu chuyên sâu](README.md)

**Tóm tắt nhanh**
- Phần đánh giá dùng để **nghiệm thu** các yêu cầu F1–F7 và N1–N8 ([02](02-muc-tieu-yeu-cau.md)). Đây không phải một nghiên cứu thống kê.
- Có ba lớp kiểm thử: **kiểm thử chức năng** trên laptop, **kịch bản vận hành VH1–VH6** (phần lớn trên laptop), và **đánh giá trên GPU thuê ĐG1–ĐG3**.
- **ĐG2** so sánh 4 cấu hình (S1, S4, A1, A2) dưới **3 kịch bản tải của đề cương** (thấp ổn định, tăng đột ngột, cao kéo dài), tổng **28 lượt**.
- Số liệu báo cáo dạng **trung bình kèm min–max**, có vẽ từng lượt riêng lẻ. Sản phẩm cuối cùng là **bảng nghiệm thu**.

---

## 1. Cách tiếp cận: đánh giá để nghiệm thu

Đánh giá trả lời câu hỏi *"nền tảng có đạt yêu cầu không, và đánh đổi những gì?"*. Vì vậy:
- Mỗi phép đo gắn với ít nhất một yêu cầu. Phép đo nào không phục vụ yêu cầu nào thì không làm.
- Ngưỡng nghiệm thu được chốt **trước** khi chạy ma trận (ADR-003), và không đổi sau khi đã thấy kết quả.
- Chỉ dùng số đo đủ để kết luận về **các khác biệt lớn**. Các khác biệt nhỏ được báo cáo là "không phân biệt được".
- So sánh công bằng nhờ một số điều kiện đơn giản: cùng máy, cùng tải, cùng phiên bản, cùng trạng thái đầu ([03 §5](03-pham-vi-gia-dinh.md#5-điều-kiện-để-so-sánh-công-bằng)).

---

## 2. Ba lớp kiểm thử

| Lớp | Ở đâu | Nội dung | Kết quả |
|---|---|---|---|
| **Kiểm thử chức năng** | Laptop (hoặc simulator), từ T4 | API, probe, preStop; bài kiểm thử autoscaling T1–T7 ([07 §8](07-chien-luoc-autoscaling.md#8-kiểm-thử-nhanh-cấu-hình-autoscaling)); quy tắc cảnh báo (`promtool test rules`); checklist bảo mật | Đạt / không đạt; chạy lại trong CI nếu tự động hoá được |
| **Kịch bản vận hành VH1–VH6** | Laptop trước (T7–T8), lặp lại trên GPU thuê những gì cần GPU thật (T9) | Scale-down, rolling update, sự cố, mất Prometheus, dựng lại, cảnh báo (§9) | Đạt / không đạt, kèm số đo |
| **Đánh giá trên GPU thuê ĐG1–ĐG3** | VM 4 × RTX 4090, một đợt khoảng 37 giờ (T9) | Đo năng lực; ma trận autoscaling; cold start (§4, §7, §8) | Số liệu cho chương 5 |

---

## 3. SLO dùng khi đánh giá

| SLO | Giá trị sơ bộ | Lý do |
|---|---|---|
| TTFT | ≤ 2 s | Với dịch vụ chat, người dùng bắt đầu thấy "chậm" khi phải chờ quá vài giây mà chưa có phản hồi |
| TPOT | ≤ 100 ms | Tương đương ít nhất 10 token/s, nhanh hơn tốc độ đọc |

- **Một request đạt SLO** khi TTFT và TPOT đều đạt ngưỡng, và request không lỗi.
- **Chốt một lần** sau ĐG1, ghi vào ADR-003. Ngưỡng TTFT nên **trùng một biên bucket** của histogram vLLM, để cảnh báo trên Prometheus và số liệu đánh giá dùng cùng một ngưỡng ([08 §2.1](08-van-hanh.md#21-chọn-sli)).

---

## 4. ĐG1: Đo năng lực một replica

![Hình 15 – Đo năng lực một replica](../images/15-hieu-chinh-nang-luc.svg)

*Hình 15. Quét tốc độ request trên 1 replica để tìm C và B\* (số liệu minh hoạ).*

**Mục đích:** tìm **C**, tốc độ request lớn nhất mà một replica phục vụ được trong khi vẫn đạt SLO. Mọi kịch bản tải được tính theo bội số của C, và target của A1, A2 được suy ra từ đây. Đây cũng chính là bước **capacity planning** của vận hành ([08 §9](08-van-hanh.md#9-chi-phí-và-kế-hoạch-năng-lực)).

**Quy trình:**
1. Cố định 1 replica (S1).
2. Quét λ ∈ {0,5; 1,0; 1,5; …} req/s theo Poisson. Mỗi mức gồm 1 phút làm ấm (không tính) và **4 phút đo**. Quét dày hơn (bước 0,25) quanh điểm bắt đầu vi phạm SLO.
3. Dừng khi TTFT p95 vượt 3 lần SLO, hoặc khi hàng đợi tăng liên tục.
4. Với mỗi mức, ghi: TTFT và TPOT p50/p95, **B** (trung bình `running + waiting`), KV-cache, GPU_UTIL, CPU của pod.
5. **C** = mức λ lớn nhất còn đạt SLO. Đọc **B\*** và **UTIL\*** tại C.
6. Kiểm tra nhanh bằng định luật Little: B\* ≈ C × E2E trung bình. Lệch hơn 15% thì xem lại cách đo.
7. Đối chiếu một mức tải với `vllm bench serve` để chắc máy tạo tải không sai lệch có hệ thống.

**Sản phẩm:** `capacity.json` = `{C, B_star, UTIL_star, slo, curves}`. Runner đọc file này để tính λ(t) và threshold.

---

## 5. Mô hình tải và máy tạo tải

### 5.1. Request

| Thuộc tính | Thiết lập | Lý do |
|---|---|---|
| Prompt | Văn bản tổng hợp, mỗi request khác nhau; độ dài phân phối đều 256–1024 token (đếm bằng tokenizer của model) | Kiểm soát lượng việc prefill; tránh prefix cache |
| Output | **Cố định 256 token** (`max_tokens=256`, `ignore_eos=true`) | Kiểm soát lượng việc decode |
| Streaming | `stream=true`, `stream_options.include_usage=true` | Đo TTFT; lấy số token chính xác |
| Timeout | 120 s | Quá hạn thì tính là lỗi |
| Xác thực | Khoá API riêng cho máy tạo tải, giới hạn tốc độ được nới rộng | Đi qua Traefik như người dùng thật |

### 5.2. Open-loop và lịch gửi

Với máy tạo tải kiểu **closed-loop** (N "người dùng", mỗi người chờ câu trả lời rồi mới gửi tiếp), khi hệ thống chậm thì tốc độ gửi tự giảm theo, che mất tình trạng quá tải [19]. Người dùng thật không chờ nhau. Vì vậy máy tạo tải chạy **open-loop**: thời điểm gửi được sinh trước theo λ(t) (quá trình Poisson có tốc độ thay đổi theo thời gian), độc lập với phản hồi của hệ thống.

Lịch gửi và độ dài prompt được sinh từ **seed** suy ra từ (kịch bản, số thứ tự lượt), nên **mọi cấu hình trong cùng một lượt nhận đúng cùng một chuỗi request**.

### 5.3. Máy tạo tải

Viết bằng Python asyncio và httpx, khoảng vài trăm dòng:

```python
async def one_request(client, i, t_sched, prompt):
    await sleep_until(t_sched)                       # lịch sinh trước; đến giờ thì gửi
    rec = {"id": i, "t_sched": t_sched, "t_send": now(), "n_in": prompt.n_tokens}
    try:
        async with client.stream("POST", URL, json=payload(prompt), timeout=120) as r:
            rec["status"] = r.status_code
            async for line in r.aiter_lines():
                if not line.startswith("data: ") or line == "data: [DONE]":
                    continue
                chunk = json.loads(line[6:])
                if chunk["choices"] and chunk["choices"][0]["delta"].get("content"):
                    rec.setdefault("t_first", now())     # chunk có nội dung đầu tiên
                    rec["t_last"] = now()
                if chunk.get("usage"):
                    rec["n_out"] = chunk["usage"]["completion_tokens"]
    except Exception as e:
        rec["error"] = type(e).__name__
    writer.write(rec)                                 # một dòng CSV cho mỗi request
```

- Chạy trong cluster dưới dạng pod có **lõi CPU riêng** ([06 §3.6](06-moi-truong-chi-phi.md#36-máy-tạo-tải-chạy-cùng-vm)).
- **Tự kiểm tra** ở mọi lượt: độ lệch `t_send − t_sched` p99 < 50 ms và CPU < 70%. Không đạt thì lượt đó không hợp lệ.

---

## 6. Ba kịch bản tải

![Hình 8 – Ba kịch bản tải](../images/08-kich-ban-tai.svg)

*Hình 8 (tài liệu chính). Ba kịch bản tải theo đề cương, đơn vị C.*

| KB | λ(t) / C | Thời lượng | Các pha khi phân tích | Kiểm chứng chủ yếu |
|---|---|---|---|---|
| **KB1** Thấp, ổn định | 0,5 | 20 phút | `steady` [2, 20] | N1, N3: chất lượng và lượng GPU lãng phí khi tải thấp |
| **KB2** Tăng đột ngột rồi giảm | 0,5 khi t < 5; lên 3,0 trong [5; 5,5]; giữ tới 15; về 0,5 trong [15; 15,5]; giữ tới 25 | 25 phút | `pre` [2, 5] · `spike` [5, 15] · `drop` [15, 25] | N2 (pha `spike`), N4 (pha `drop`), N3 |
| **KB3** Cao, kéo dài | tăng 0,5 → 3,5 trong [0, 5]; giữ tới 25 | 25 phút | `ramp` [0, 5] · `sustain` [5, 25] | N1: ổn định dưới tải cao; không flapping; N7 |

(t tính bằng phút; hai phút đầu của KB1 và KB2 là thời gian ổn định, không tính.)

**Vì sao ba kịch bản này?** Đây đúng là ba kịch bản trong đề cương. Gộp lại, chúng tái hiện các pha của một ngày tải ở bối cảnh [01 §4](01-dat-van-de.md#4-bối-cảnh-giả-định-và-ba-cách-cấp-phát): ban đêm (KB1), 9 giờ sáng (KB2) và giờ cao điểm kéo dài (KB3). KB2 được cho **giảm tải trở lại** ở phút 15, để cùng một lượt kiểm tra được cả scale-up lẫn scale-down an toàn.

---

## 7. ĐG2: Đánh giá autoscaling so với cấu hình tĩnh

| Cấu hình \ Kịch bản | KB1 | KB2 | KB3 |
|---|---|---|---|
| S1 Static-1 | 2 | 3 | 2 |
| S4 Static-4 | 2 | 3 | 2 |
| A1 GPU utilization | 2 | 3 | 2 |
| A2 Tải đồng thời | 2 | 3 | 2 |

- Tổng **28 lượt**. KB2 chạy 3 lượt vì là kịch bản quan trọng nhất (phản ứng và scale-down).
- Thứ tự các lượt được **xáo trộn** bằng một seed ghi lại.
- Mọi lượt chạy ở mức cold start **L2** (đã tối ưu), là cấu hình vận hành thật.
- Nếu còn thời gian (Could): thêm A3 × KB1–KB3, mỗi ô 2 lượt (6 lượt).

**Đo gì từ ĐG2:**

| Yêu cầu | Số đo |
|---|---|
| N1 | SLO attainment của A2 ở KB1, KB3 |
| N2 | Ở KB2: thời gian phản ứng (tải tăng → replica mới Ready), thời gian hồi phục SLO |
| N3 | GPU-giờ của A2 so với S4 ở KB1, KB2; chênh lệch SLO attainment |
| N4 | Số request lỗi trong pha `drop` của KB2 |
| Lựa chọn thiết kế | A1 so với A2: số replica theo thời gian, GPU-giờ, SLO. Đây là bằng chứng cho việc chọn A2 ([07 §3](07-chien-luoc-autoscaling.md#3-phân-tích-từng-metric)) |
| N7 | Cảnh báo kích hoạt ở S1 × KB3, và không kích hoạt mức page ở A2 × KB1, KB3 (ghi lại từ Alertmanager trong mọi lượt) |

---

## 8. ĐG3: Cold start

| Bước | L0 (không tối ưu) | L2 (tối ưu đầy đủ) |
|---|---|---|
| Chuẩn bị node | `crictl rmi` image vLLM; xoá model và compile cache | Image đã pre-pull; model trên NVMe; compile cache đã làm ấm |
| Làm lạnh RAM | `sync; echo 3 > /proc/sys/vm/drop_caches` | như L0 |
| Kích hoạt | Scale từ 1 lên 2 replica | như L0 |
| Đo | Mốc thời gian của 8 pha: pod conditions, event pull image, log vLLM ([05 §7](05-kien-truc-he-thong.md#7-cold-start-chi-tiết)) | như L0 |
| Số lần | 3 | 3 |

Sau đó chạy **KB2 với A2 ở mức L0**, 2 lượt, rồi so với các lượt A2 × KB2 của ma trận (ở L2). Kết quả cho thấy cold start ảnh hưởng thế nào tới thời gian phản ứng và SLO trong tình huống thật (N5, N2).

---

## 9. Kịch bản vận hành VH1–VH6

| # | Kịch bản | Ở đâu | Cách làm | Tiêu chí đạt | Yêu cầu |
|---|---|---|---|---|---|
| **VH1** | Scale-down an toàn | Laptop; GPU thuê (pha `drop` của KB2) | Tắt tải đột ngột khi đang có 3–4 replica; đếm request lỗi hoặc bị cắt stream trong cửa sổ scale-down | 0 request lỗi | N4 |
| **VH2** | Cập nhật phiên bản khi hết GPU | Laptop (2–3 GPU); GPU thuê | Đổi tham số hoặc digest qua PR → Argo CD. (a) Tải thấp, 1–2 replica; (b) tải cao, 4/4 GPU, phương án `maxSurge: 0`; (c) thử phương án kiểu web để thấy bị kẹt và cảnh báo `LLMPodPending` kêu. Sau đó rollback bằng `git revert` | (a), (b) hoàn tất, 0 request lỗi; ghi thời gian và SLO trong lúc cập nhật. (c) bị kẹt và có cảnh báo, đúng như phân tích | F3, N4 |
| **VH3** | Sự cố pod và node | Laptop (drain node); GPU thuê (xoá pod) | Khi đang có tải: `kubectl delete pod`; `kill -9` tiến trình vLLM; `kubectl drain` một laptop | Pod mới Ready tự động; xoá êm thì 0 lỗi; kill thì chỉ lỗi các request đang chạy trên pod đó; có cảnh báo tương ứng | N6 |
| **VH4** | Mất nguồn metric | Laptop; GPU thuê | Scale Prometheus về 0 khi đang có tải; sau 5 phút bật lại | KEDA fallback lên max replica trong ≤ 30 s; SLO không bị ảnh hưởng; bật lại thì trở về bình thường | N6 |
| **VH5** | Dựng lại từ máy trắng | GPU thuê (đầu đợt chính); laptop | `make bootstrap prefetch` trên VM vừa thuê; người thứ hai dựng cluster laptop theo README | ≤ 30 phút tới khi API phục vụ được; người thứ hai dựng được trong < 1 giờ | F4, N6, N8 |
| **VH6** | Cảnh báo đúng, không báo giả | Ghi lại trong mọi lượt ĐG2; laptop | So sánh thời điểm vi phạm SLO (từ log client) với thời điểm Alertmanager gửi cảnh báo | Cảnh báo SLO ≤ 5 phút sau khi vi phạm; không có cảnh báo page ở A2 × KB1, KB3 | F6, N7 |

Mỗi kịch bản có một mục trong `docs/nhat-ky/van-hanh.md`: ngày, môi trường, các bước, số đo, đạt hay không, và runbook đã dùng.

---

## 10. Quy trình tự động của một đợt đánh giá

![Hình 17 – Quy trình một đợt đánh giá](../images/17-quy-trinh-danh-gia.svg)

*Hình 17. Quy trình một đợt đánh giá trên GPU thuê. Nhãn màu trên mỗi bước cho biết người phụ trách.*

### 10.1. Các bước của một lượt

| Bước | Việc làm | Lệnh hoặc chi tiết |
|---|---|---|
| **Áp cấu hình** | Tĩnh: xoá ScaledObject, đặt số replica. Autoscaling: áp ScaledObject rồi tạm dừng ở 1 replica | `kubectl apply -f autoscaling/A2.yaml`; annotation `autoscaling.keda.sh/paused-replicas: "1"` |
| **Reset** | Chờ hệ thống yên | 1 pod Ready (S4: 4 pod Ready); hàng đợi trống; chờ thêm 60 s |
| **Warm-up** | Làm ấm | 0,3C trong 2 phút, không tính |
| **Chạy** | Bỏ tạm dừng, chạy kịch bản | Bỏ annotation; máy tạo tải chạy lịch; runner gửi annotation lên Grafana ở đầu mỗi pha |
| **Thu thập** | Lấy dữ liệu | CSV của máy tạo tải; chuỗi Prometheus trong cửa sổ lượt; sự kiện pod; log vLLM; cảnh báo từ Alertmanager |
| **Cooldown** | Về trạng thái đầu | Chờ còn 1 replica (tối đa 10 phút) |
| **Kiểm tra, sao lưu** | | Ghi `checks.json` (§13); đẩy thư mục lượt lên R2 |

Trước đợt đánh giá, runner **tắt auto-sync** của Application `autoscaling` trên Argo CD; hết đợt thì bật lại ([05 §10.2](05-kien-truc-he-thong.md#102-cấu-hình-autoscaling-trong-git-tạm-tách-khi-đánh-giá)).

### 10.2. Dữ liệu của một lượt

```text
runs/<run-id>/
├── metadata.json     # cấu hình, kịch bản, seed, phiên bản (digest), tham số vLLM, máy, thời gian
├── requests.csv      # một dòng cho mỗi request: t_sched, t_send, t_first, t_last, n_in, n_out, status, error
├── metrics.parquet   # chuỗi Prometheus trong cửa sổ lượt (replicas, hàng đợi, KV-cache, GPU…)
├── events.jsonl      # pod conditions, sự kiện HPA, sự kiện Kubernetes
├── alerts.jsonl      # cảnh báo nhận được từ Alertmanager (cho VH6)
└── checks.json       # kết quả tự kiểm tra
```

Một script `analysis/build_tables.py` (có unit test) đọc các thư mục này và tạo một bảng mỗi lượt một dòng. Notebook vẽ biểu đồ từ bảng đó.

---

## 11. Chỉ số và cách tính

| Nhóm | Chỉ số | Cách tính | Nguồn |
|---|---|---|---|
| Hiệu năng | **TTFT** p50/p95/p99 | t_first − t_send | Log máy tạo tải |
| | **TPOT** p50/p95 | (t_last − t_first) ÷ (n_out − 1), với n_out lấy từ `usage` (một chunk có thể chứa nhiều token) | Log máy tạo tải |
| | **SLO attainment** | Số request đạt SLO ÷ **số request đã gửi** trong pha. Request lỗi vẫn nằm ở mẫu số | Log máy tạo tải |
| | **Throughput** | Token output mỗi giây | Log máy tạo tải, đối chiếu `vllm:generation_tokens_total` |
| | **Tỷ lệ lỗi** | Request lỗi HTTP, timeout, hoặc stream bị cắt (không có `usage`) | Log máy tạo tải |
| Tài nguyên | **GPU-giờ** | Tổng thời gian các pod vLLM giữ GPU, **tính cả lúc cold start và lúc drain** | Sự kiện pod (chính xác); `kube_deployment_status_replicas` (xấp xỉ) |
| | **GPU-giờ so với S4** | GPU-giờ của cấu hình ÷ GPU-giờ của S4 trong cùng kịch bản | Tính toán |
| | **Token / GPU-giờ** | Tổng token output ÷ GPU-giờ | Tính toán |
| Autoscaling | **Thời gian phản ứng** | Từ lúc tải tăng (theo lịch) đến lúc replica mới đầu tiên Ready; tách thành phần phát hiện (đến khi `desiredReplicas` đổi) và phần cold start | Lịch tải, kube-state-metrics, sự kiện pod |
| | **Thời gian hồi phục SLO** | Từ lúc tải tăng đến khi TTFT p95 (cửa sổ trượt 30 s) ≤ SLO và giữ được ít nhất 60 s | Log máy tạo tải |
| | **Số lần scale, flapping** | Số lần `desiredReplicas` đổi; số lần đổi chiều trong vòng 5 phút | kube-state-metrics |
| Vận hành | **Thời gian tới cảnh báo** | Thời điểm Alertmanager gửi − thời điểm SLO bắt đầu bị vi phạm | `alerts.jsonl`, log máy tạo tải |
| | **Thời gian dựng lại, thời gian cập nhật** | Theo các bước của VH2, VH5 | Runner, `kubectl rollout status` |

**Hai nguyên tắc tính:**
- Phân vị (p95, p99) tính trên **tất cả request** của pha, không lấy trung bình các p95 theo phút hay theo pod. Pha nào có ít hơn khoảng 200 request thì chỉ báo cáo p95 kèm số mẫu.
- Số liệu độ trễ trong luận văn lấy từ **log máy tạo tải** (chính xác tới từng request). Histogram của Prometheus nội suy theo bucket nên chỉ dùng cho dashboard và cảnh báo.

---

## 12. Trình bày kết quả và bảng nghiệm thu

**Cách báo cáo số liệu.** Mỗi ô (cấu hình × kịch bản) có 2–3 lượt. Báo cáo **trung bình kèm min–max**, và vẽ **từng lượt** thành chấm trên biểu đồ. Chỉ viết "A khác B" khi **mọi lượt đều cùng chiều** và chênh lệch vượt ngưỡng thực tiễn: 5 điểm phần trăm với SLO attainment, 10% với GPU-giờ, 30 s với thời gian.

| Mã | Biểu đồ | Phục vụ |
|---|---|---|
| **C1** | **Chuỗi thời gian** của KB2 cho S4, A1, A2: λ(t), số replica, TTFT p95 trượt, độ dài hàng đợi, xếp dọc chung trục thời gian | N2, N4, lựa chọn A2. Đây là biểu đồ trung tâm |
| **C2** | SLO attainment theo cấu hình × kịch bản (cột kèm chấm từng lượt) | N1 |
| **C3** | GPU-giờ (% so với S4) theo cấu hình × kịch bản | N3 |
| **C4** | Trade-off: trục hoành GPU-giờ (% S4), trục tung SLO attainment; mỗi cấu hình một điểm, mỗi kịch bản một ô | N3, khuyến nghị |
| **C5** | Cold start 8 pha ở L0 và L2 (cột ngang chồng) | N5 |
| **C6** | Dòng thời gian rolling update (VH2): số pod mỗi phiên bản, năng lực, TTFT p95, lỗi | F3, N4 |

Không dùng biểu đồ hai trục tung; màu gắn cố định với từng cấu hình; mọi biểu đồ có ghi số lượt.

**Bảng nghiệm thu** (khung, điền sau đợt đánh giá):

| Yêu cầu | Chỉ tiêu | Kết quả đo | Đạt? | Ghi chú |
|---|---|---|---|---|
| N1 | SLO attainment A2 ≥ 95% ở KB1, KB3 | … | … | … |
| N2 | Phản ứng ≤ 2 phút; hồi phục ≤ 5 phút (KB2) | … | … | … |
| N3 | GPU-giờ A2 ≤ 50% S4 ở KB1; SLO kém S4 ≤ 5 điểm % | … | … | … |
| N4 | 0 lỗi khi scale-down và rolling update | … | … | … |
| N5 | Cold start L2 ≤ 50% L0 | … | … | … |
| N6 | Tự phục hồi; fallback; dựng lại ≤ 30 phút | … | … | … |
| N7 | Cảnh báo ≤ 5 phút; không báo giả mức page | … | … | … |
| N8 | Phiên bản ghim; dựng laptop < 1 giờ; chi phí ≤ 150 USD | … | … | … |
| F1–F7 | Theo cách kiểm chứng ở [02 §3](02-muc-tieu-yeu-cau.md#3-yêu-cầu-chức-năng) | … | … | … |

Yêu cầu không đạt **không bị giấu đi**. Luận văn phân tích nguyên nhân và nêu cách khắc phục; nếu đã sửa thì đo lại và ghi cả hai lần.

**Khung chương 5 của luận văn:**

```text
5.1 Môi trường và cách đánh giá
5.2 Năng lực một replica (ĐG1)
5.3 Autoscaling so với cấu hình tĩnh (ĐG2): hành vi theo thời gian (C1), SLO và GPU-giờ (C2–C4),
    vì sao không chọn GPU utilization
5.4 Cold start (ĐG3, C5)
5.5 Kịch bản vận hành (VH1–VH6, C6)
5.6 Bảng nghiệm thu và khuyến nghị cấu hình
5.7 Hạn chế
```

---

## 13. Điều kiện hợp lệ của một lượt

| Kiểm tra | Ngưỡng |
|---|---|
| Độ lệch gửi p99 của máy tạo tải | < 50 ms |
| CPU máy tạo tải (tối đa) | < 70% |
| Khoảng trống scrape của Prometheus | ≤ 15 s |
| Node có sự cố, pod bị OOMKilled ngoài dự kiến | Không có |
| Trạng thái đầu đúng (1 replica, hàng đợi trống; S4: 4 replica) | Đúng |

Lượt không đạt được đánh dấu `invalid` kèm lý do và **chạy lại** ở cuối đợt (giờ 32–36) hoặc trong đợt dự phòng. Dữ liệu lượt hỏng vẫn được giữ lại.

---

## 14. Câu hỏi hội đồng có thể đặt ra

**Vì sao output cố định 256 token, trong khi thực tế độ dài output rất khác nhau?**
Để lượng việc giữa các cấu hình như nhau, và để E2E so sánh được. Đây là cách làm phổ biến trong benchmark serving, và được ghi thành hạn chế.

**Vì sao S1 vẫn chạy cả KB3, trong khi biết trước là quá tải?**
S1 ở KB3 là tình huống "thiếu GPU" thật. Nó cho thấy chất lượng sụp đổ ra sao khi cấp thiếu (một đầu của trade-off), và là phép thử cho cảnh báo SLO (VH6).

**Làm sao biết máy tạo tải không phải nút thắt?**
Máy tạo tải tự kiểm tra độ lệch lịch gửi và CPU ở mọi lượt (§5.3), và được đối chiếu với `vllm bench serve` ở bước đo năng lực.

**Nếu một yêu cầu không đạt thì sao?**
Đó vẫn là một kết quả. Bảng nghiệm thu ghi rõ "không đạt", luận văn phân tích nguyên nhân và đề xuất cách sửa. Ví dụ nếu N2 không đạt vì cold start dài, phần phân tích dùng số đo 8 pha để chỉ ra pha nào cần tối ưu tiếp.
