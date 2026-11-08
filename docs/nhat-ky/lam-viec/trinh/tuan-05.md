# Nhật ký làm việc – Trình – Tuần 05 (02–08/11/2026)

## 2026-11-07 – TR2: gộp `main`, sửa sau soát, đo T4 và đặt timeout 1 s cho trigger

- **Task:** TR2 · **Environment:** sim (kind trong WSL2, máy Trình)
- **Done:**
  1. Đọc lại trạng thái sau 5 ngày. Quang đã merge PR #6–#15; PR #11 đưa lên `main` bản nháp TR2 lấy từ `temp/w2-scaffold` (A2, kind, KEDA, kube-prometheus-stack, policy T4), ghi "bản chính của Trình ở `feat/tr2-sim` sẽ thay". Họp 04/11 đã dời V2 sang 14–15/11.
  2. `git merge origin/main` vào `feat/tr2-sim` (commit `1fe5b8a`). 10 file xung đột, 8 file là add/add. So từng file: hai bên cùng gốc scaffold, khác nhau chủ yếu ở comment. Giữ bản của nhánh (có `cpu: null`, `KEDA_HTTP_DISABLE_KEEP_ALIVE`, digest node image, `scrapeConfigSelectorNilUsesHelmValues`), lấy các dòng mới của `main` ở `Makefile` (`alerts-coverage`) và `docs/phien-ban.md`. Bỏ biến `SIM_SERVING` vì `main` đã có `serving/overlays/sim`. Hai mục TR2 trong `tuan-04.md` bị `merge=union` xếp lên đầu file: chuyển xuống sau các mục CI, đúng thứ tự giờ commit.
  3. Kiểm tĩnh trên bản gộp: yamllint, actionlint, shellcheck, `kubectl kustomize | kubeconform -strict` cho cả 10 thư mục kustomize (chạy trong WSL vì kubeconform trên Windows không tra được DNS), lychee, `make alerts-test`: đều đạt.
  4. `make sim-down`, rồi `make sim-up` trên bản gộp: 550 s, mã thoát 0. Kiểm: keda-operator có `KEDA_HTTP_DISABLE_KEEP_ALIVE=true` và chỉ còn limit bộ nhớ; image simulator đúng digest Quang ghim; sync HPA 5 s; ScaledObject có điều kiện `Paused`.
  5. `/code-review high` trên diff so với `main`: 10 điểm. Sửa 9, commit `22086c8`: T1 không coi metric rỗng là 0; T2/T3 đo từ lúc `hey` thật sự chạy (`load-sim.sh` in mốc); dừng sớm nếu `fallback.replicas ≠ maxReplicaCount`; T5 chờ `Paused=True` và HPA bị xoá thay vì `sleep 10`; `failures()` lấy max; kiểm câu PromQL lúc khởi động; `load-sim.sh` luôn tự mở port-forward ở cổng ngẫu nhiên.
  6. `make sim-test` lần 1 (11:19–11:38): T4 trượt. Đo T4 thêm 10 lượt với hai cấu hình timeout (mục số đo), đối chiếu mã nguồn KEDA v2.21.0.
  7. Trình chọn thêm `timeout: "1000"` vào trigger A2 ngay trong PR này. Sửa A2, Thông số §9.3, Kiến trúc §13.2, §15, §16, w2 §9.3, `run-t1-t5.sh` (T4 chấm "> failureThreshold lỗi"), comment của policy T4, runbook `KedaScalerErrors` và comment của cảnh báo. `make sim-test` lần 2 (11:50–12:09).
  8. `/code-review high` lần 2, trên phần chưa commit: 8 điểm, sửa cả 8. Kiến trúc §13.3 ghi rõ A1, A3, A4 giữ `timeout: "1000"`; mô tả cảnh báo `KedaScalerErrors` (rule, unit test, Vận hành §3) không còn khẳng định "đang fallback"; T4 chấm theo điều kiện `Fallback=True` thay cho một lần đọc `numberOfFailures` (hai luồng của KEDA cùng ghi số này); sửa nguồn số liệu 1000 ms (chỉ 07/11); đo độ trễ truy vấn Prometheus thay cho câu "chỉ mất vài ms" chưa đo; log của script ghi thêm `failureThreshold`, timeout, N6; N6 truyền được qua biến môi trường. Thêm: cận dưới T3 từ 298 s xuống 295 s (lý do ở mục quyết định).
  9. `make sim-test` lần 3 (12:11–12:29): T3 trượt (292 s). Điều tra: kube-controller-manager không khởi động lại, không đổi leader; `hey` tự báo chạy 191,8 s, trong khi theo `date` chỉ có 188 s từ lúc `hey` bắt đầu tới khi script ghi T3; journal của WSL có "Clock change detected" khoảng mỗi 32 s; đo 64 s so với đồng hồ Windows. Sửa hai script: mọi khoảng thời gian đo bằng đồng hồ đơn điệu (`/proc/uptime`), cùng loại HPA dùng. `make sim-test` lần 4 (15:05–15:24, trên cluster của lần 3, không `sim-up` lại).
  10. Kiểm tĩnh lại toàn bộ (yamllint, shellcheck, `make alerts-test`, lychee, kubeconform 10/10 thư mục): đạt. Cập nhật số T4 với 1000 ms ở A2, Thông số §9.3, w2. Commit `fe28a1a`.
  11. Push `feat/tr2-sim`, mở PR #16 vào `main`, reviewer Quang. Mô tả PR nêu 3 điểm cần review (timeout 1 s, keep-alive, `cpu: null`); câu hỏi cho Quang gửi riêng, không để trong PR (repo công khai).
- **Decision:**
  - Gộp bằng `merge` thay vì rebase hoặc tạo nhánh mới: nhánh chưa push nên rebase cũng được, nhưng merge giữ 4 commit cũ cùng nhật ký, chỉ giải xung đột một lần, và diff của PR so với `main` chỉ còn phần khác bản nháp.
  - Bỏ điểm soát #7 (dùng `replacements` của kustomize ở base để fallback tự bằng max): overlay patch `maxReplicaCount` sau khi base đã dựng xong, nên replacement đặt ở base vẫn chép giá trị 4 của base. Bước kiểm `fallback = max` lúc khởi động script đã bắt được lỗi này trên simulator.
  - Cận dưới T3 295 s (trước là 298 s): cửa sổ 300 s tính từ lần cuối HPA còn muốn 3 replica, và lần đó có thể sớm hơn hạn dừng của `hey` tới một chu kỳ scrape (5 s), vì lần scrape cuối còn thấy đủ tải có thể nằm trước hạn dừng. Lần 2 đo được 298 s, đúng bằng cận cũ. Lần 3 mới thấy nguyên nhân chính của các số thấp là đồng hồ của VM (mục sự cố); vẫn giữ 295 s vì lập luận về scrape vẫn đúng.
  - Cảnh báo `KedaScalerErrors` giữ ngưỡng `≥ 3` lỗi trong 2 phút (page sớm khi KEDA "mù"), chỉ sửa mô tả: lúc kêu, fallback có thể chưa bật.
  - Timeout 1 s (Trình chọn, 07/11; chờ Quang duyệt ở PR): giữ nguyên `failureThreshold: 3` và N6. Bỏ phương án hạ `failureThreshold` xuống 2 (nhạy hơn với lúc Prometheus chập chờn ngắn, dễ lên max oan và tốn GPU ở V2; chưa đo) và phương án nới N6 lên 45 s (làm yêu cầu yếu đi). Rủi ro: một truy vấn Prometheus chậm quá 1 s bị tính là lỗi. Trên kind không thấy truy vấn nào chậm như vậy (mục số đo); ở nhà và V2 chưa đo.
- **Results:**
  - `make sim-test` lần 1, bản gộp, timeout mặc định: T1 đạt. T2 đạt: `desired=3` sau **8 s**, metric HPA 8,334 ≈ 25 ÷ 3; mở port-forward mất 1 s, không tính vào 8 s. T3 đạt: giữ 3 trong 304 s rồi về 2, về 1 sau thêm 58 s. **T4 trượt: fallback sau 38 s** (N6 ≤ 30 s), 6 lỗi. T5 đạt: A2 cao nhất 25. Tổng 1131 s.
  - T4 đo lặp (scaleDown của ScaledObject tạm patch về cửa sổ 0 trên kind để mỗi lượt bắt đầu từ 1 replica sau vài giây; sau khi đo đã trả về bản Git và kiểm lại):

    | Cấu hình | Fallback sau (s), 5 lượt | Lỗi 1 / 2 / 3 / 4 (s sau khi áp policy) | Đạt N6 |
    |---|---|---|---|
    | Timeout mặc định 3000 ms | 26, 26, 35, 26, 32 | 10–12 / 16–20 / 20–27 / 30–33 | 3/5 |
    | `timeout: "1000"` | 20, 19, 20, 19, 19 | 4–5 / 9–10 / 14–16 / 19–20 | 5/5 |

    Mốc lỗi đọc từ log mỗi giây của `run-t1-t5.sh`. Cột lỗi 4 chỉ có ở 2/5 lượt (3000 ms) và 3/5 lượt (1000 ms), vì script gỡ policy ngay khi HPA lên 3, trước khi vòng ghi log kịp ghi dòng đó; cột "fallback sau" lấy thẳng từ HPA nên đủ 5 lượt.

    Tính cả lượt 38 s ở trên và lượt 24 s ngày 01/11 thì timeout 3000 ms vượt N6 3/7 lần, trong khoảng 24–38 s. Pod busybox trong ns `keda`, hỏi Prometheus mỗi 0,5 s, bị chặn sau 1–2 s kể từ lúc áp policy: kindnet áp policy nhanh, nên độ trễ trước lỗi đầu tiên là do chờ lần hỏi kế tiếp cộng timeout.
  - `make sim-test` lần 2, có `timeout: "1000"`, cách chấm T4 "> failureThreshold lỗi": **5/5 đạt**, mã thoát 0, 1117 s. T2: `desired=3` sau 9 s, metric 8,334. T3: giữ 3 trong 298 s, về 1 sau thêm 59 s. T4: fallback sau **23 s**, 5 lỗi, hết lỗi sau 2 s khi gỡ policy. T5: A2 cao nhất 25.
  - `make sim-test` lần 3, cách chấm T4 theo `Fallback=True`: T1, T2 (`desired=3` sau 4 s), T4 (fallback sau **17 s**, `Fallback=True`, 5 lỗi), T5 đạt; **T3 trượt: 3 → 2 sau 292 s**, về 1 sau thêm 59 s. Mã thoát 2, 1105 s.
  - `make sim-test` lần 4, đo bằng đồng hồ đơn điệu: **5/5 đạt**, mã thoát 0, 15:05:07–15:23:52. T1: metric 0 suốt 120 s. T2: `desired=3` sau 5 s, metric 8,334. T3: giữ 3 trong **302 s**, về 1 sau thêm 60 s. T4: fallback sau **21 s**, `Fallback=True`, 4 lỗi, hết lỗi sau 2 s khi gỡ policy. T5: A2 cao nhất 25. Log: `runs/sim/20261107-150507-t1-t5.log` (gitignore, chỉ trên máy Trình).
  - Gộp các lượt T4 có `timeout: "1000"`: 20, 19, 20, 19, 19 (đo lặp), 23, 17, 21 (lần 2–4) → **17–23 s, 8/8 đạt N6**. Với 3000 ms: 24–38 s, 3/7 vượt N6.
  - Đồng hồ trên WSL2 (máy Trình, 07/11): trong 64 s theo đồng hồ Windows, đồng hồ đơn điệu của WSL chạy 64,330 s (**nhanh hơn 1,62 %**), đồng hồ thực của WSL chạy 63,276 s (lệch −0,03 s, vì bị kéo về theo Windows). Thời gian `hey` tự đo (đơn điệu) so với khoảng đo bằng `date`: lần 1: 190,25 s / 190 s; lần 2: 191,65 s / 189 s; lần 3: 191,77 s / 188 s.
  - Độ trễ truy vấn Prometheus trên kind (07/11, histogram `prometheus_http_request_duration_seconds` của handler `/api/v1/query`, đo khoảng 11:55 với cửa sổ `[1h]`, nhưng Prometheus mới chạy từ lúc `make sim-up` khoảng 11:15, nên thực tế phủ khoảng 40 phút, gồm cả các lượt T4 đo lặp): 459 truy vấn, tất cả < 0,1 s (bucket nhỏ nhất), trung bình 0,6 ms; `prometheus_engine_query_duration_seconds{slice="inner_eval"}` p99 2,5 ms. Nhà và V2 chưa đo.
  - Mã nguồn KEDA v2.21.0: fallback bật khi `NumberOfFailures > FailureThreshold` (`pkg/fallback/fallback.go:144`), tức ở lần lỗi thứ 4; timeout mặc định `KEDA_HTTP_DEFAULT_TIMEOUT` = 3000 ms (`cmd/operator/main.go:236`); `timeout` của trigger không có đơn vị thì tính là ms (`pkg/scalers/scalersconfig/typed_config.go:450-468`).
  - KEDA v2.21.0 in cảnh báo khi áp A2: `pollingInterval` không ảnh hưởng scale khi `minReplicaCount ≥ 1`, nhưng vẫn quyết định KEDA làm mới điều kiện trong status và event bao lâu một lần. Comment của A2 đã ghi theo cảnh báo này.
- **Incidents:**
  - T4 trượt N6 (38 s) → fallback cần 4 lỗi, và mỗi lần hỏi bị chặn mất 3 s timeout, nên thời gian phụ thuộc hai luồng hỏi (HPA, vòng polling của KEDA) lệch pha nhau thế nào → đặt `timeout: "1000"`.
  - T3 trượt (292 s, lần 3) → đồng hồ của VM WSL2 chạy nhanh 1,6 % so với giờ thật. HPA giữ đúng 300 s theo đồng hồ của nó, tức khoảng 295 s giờ thật; script đo bằng `date` (giờ thật) nên thấy 292–304 s tuỳ độ rung của scrape và sync → script đo mọi khoảng bằng đồng hồ đơn điệu (`/proc/uptime`). Giả thuyết ban đầu là ngược lại (đồng hồ thực bị kéo lùi, làm số đo hụt); phép đo 64 s cho thấy chính đồng hồ của VM chạy nhanh, còn đồng hồ thực chỉ bị kéo về theo Windows.
  - Lần 4 khởi chạy đầu tiên (12:35) không chạy: lệnh `nohup … &` gọi qua `wsl.exe --exec` báo "started", nhưng 2,5 giờ sau không có tiến trình `make` và không có file log. Nhiều khả năng tiến trình nền bị tắt theo phiên `wsl.exe` (chưa kiểm nguyên nhân) → chạy lại `make sim-test` thành tác vụ nền của Claude Code, chờ xong ở tiền cảnh của lệnh `wsl.exe`.
  - Cảnh báo `KedaScalerErrors` hiện không kêu được (phát hiện khi soát, chưa sửa) → comment của rule ghi cần bật metric của KEDA operator (`prometheus.operator.enabled`, `podMonitor.enabled`), nhưng `platform/keda/values.yaml` chưa bật → bật ở PR sau (TR3/TR4).
- **Deviations:**
  - Thiết kế, w2, runbook `KedaScalerErrors` và comment cảnh báo đều ghi "sau 3 lần lỗi thì fallback"; thực tế là lần thứ 4. Đã sửa các chỗ đó.
  - Thông số §9.3 thêm dòng timeout trigger 1000 ms; Kiến trúc §13.2 thêm `timeout` vào YAML mẫu.
  - Ước tính "15–30 s" của w2 cho T4 không đúng với timeout mặc định.
- **Links:** PR #16; `1fe5b8a`, `22086c8`, `fe28a1a`; `autoscaling/official/base/scaledobject-a2.yaml`, `autoscaling/tests/run-t1-t5.sh`, `autoscaling/tests/load-sim.sh`, `docs/chi-tiet/00-thong-so.md`.
- **Thesis:** chương "Triển khai và vận hành" (Kiến trúc §15): bảng T4 hai cấu hình timeout là ví dụ đo được vì sao tham số mặc định không đạt yêu cầu, kèm bằng chứng từ mã nguồn; có thể vẽ hình số lỗi theo thời gian của hai cấu hình. LT7: các mẫu T2 ngày 01/11 (1, 6, 8 s) đo từ lúc gọi `load-sim.sh`, nên gồm cả thời gian mở port-forward (khoảng 1 s); từ 07/11 đo từ lúc `hey` chạy (mẫu mới: 8, 9, 4, 5 s). Mọi số đo thời gian trên simulator này có sai số đồng hồ tới 1,6 %: trước khi sửa script, đo bằng giờ thật; sau khi sửa, đo bằng đồng hồ của VM. Lệch không đáng kể với T2, T4 (< 0,4 s), nhưng là 5 s với cửa sổ 300 s của T3. Đây là ví dụ đáng nêu trong phần hạn chế của môi trường thử.

## 2026-11-07 – TR2: cấu hình đánh giá A1, A3, A4 cho runner, kiểm trên kind

- **Task:** TR2 · **Environment:** sim
- **Done:**
  1. Tạo nhánh `feat/tr2-a1-a4` từ `feat/tr2-sim` (PR #16 chưa merge), vì A1, A3, A4 phải chép đúng phần chung của A2 bản mới (`timeout: "1000"`, fallback).
  2. Đọc Kiến trúc §9–§13, Thông số §8–§9, code runner (`experiments/runner/configs.py`, `matrix.py`) và các file `matrix-*.yaml`. Runner đọc mỗi file eval như **một ScaledObject đơn** (`yaml.safe_load`, không qua kustomize) rồi ghi đè `threshold`, `maxReplicaCount`, `fallback.replicas`.
  3. Viết `autoscaling/eval/A1.yaml` (GPU util, threshold 70), `A3.yaml` (KV-cache, 0.44 minh hoạ), `A4.yaml` (chỉ hàng đợi, 5). Mọi trường ngoài `query`, `threshold`, tên và nhãn giống hệt A2.
  4. Thêm `autoscaling/eval/kustomization.yaml` (chỉ để job `manifests` của CI kiểm schema), thêm `autoscaling/eval` vào `make lint`.
  5. Thêm `experiments/tests/test_eval_configs.py`: tên `vllm-<id>`, nhãn `experiment/config`, runner ghi đè được, eval chỉ khác A2 ở tín hiệu, kustomization liệt kê đủ file.
  6. Trên kind: dựng manifest bằng `render_scaledobject` của runner (threshold như trong file, max 3), áp theo trình tự của `apply_config` (xoá ScaledObject khác → áp bản pause → bỏ pause), cho A1, A3, A4, rồi trả về A2.
  7. Sửa tài liệu cho khớp code đã có: Kế hoạch §6, Môi trường §14.1, Kiến trúc §18.2, CONTRIBUTING §1, §3.
- **Decision:**
  - Không tạo `eval/A2.yaml`: runner (`matrix-sim.yaml`) đã dùng thẳng `official/base/scaledobject-a2.yaml`, nên lượt A2 đo đúng cấu hình Argo CD vận hành; bản sao trong `eval/` có thể lệch. Không tạo file cho S1, S4: runner đặt `replicas` trực tiếp.
  - Phần chung với A2 viết lặp lại trong từng file (runner không chạy kustomize), và dùng test để chặn lệch thay cho kustomize patch.
  - Query A1 giữ tín hiệu của Thông số §8.1 (`sum(nvidia_smi_utilization_gpu_ratio) * 100`), thêm `or vector(0)` như mẫu ở Kiến trúc §13.3; không thêm `max by (uuid)` để khử trùng chuỗi: chỉ có một PodMonitor scrape exporter.
- **Results:**
  - Đối chiếu tên metric ở bản ghim: vLLM v0.31.0 có `vllm:kv_cache_usage_perc`, `vllm:num_requests_running`, `vllm:num_requests_waiting` (`vllm/v1/metrics/loggers.py`); nvidia_gpu_exporter 1.15.1 đổi cột `[%]` thành hậu tố `_ratio`, nhân 0,01 (`internal/exporter/exporter.go:73`); llm-d-inference-sim v0.12.0 có `vllm:kv_cache_usage_perc`, nhưng giá trị chỉ đổi khi bật `--enable-kvcache` (`pkg/kvcache/block_cache.go`), overlay `sim` chưa bật.
  - Kind, 16:12–16:15, không tải:

    | Cấu hình | Target HPA | Metric HPA thấy | Ready | Lỗi trong log KEDA operator | Số HPA trong ns |
    |---|---|---|---|---|---|
    | A1 | 70 | 0 | True | không | 1 |
    | A3 | 440m | 0 | True | không | 1 |
    | A4 | 5 | 0 | True | không | 1 |

    Mỗi lần đổi cấu hình, HPA cũ bị xoá cùng ScaledObject, chỉ còn một HPA (cơ chế của T6, làm trên kind; T6 theo thiết kế là bài ở nhà, chưa chạy). Trả về A2: `keda-hpa-vllm-a2` 0/10, 1 replica.
  - `pytest experiments`: 39 passed, gồm 8 test mới. Thử làm lệch có chủ đích (A1 `stabilizationWindowSeconds` 60; A4 `timeout` 3000): test báo đỏ cả hai lần, rồi trả lại.
  - `yamllint -s .`, `ruff check`, `ruff format --check` đạt; kubeconform `autoscaling/eval` 3/3 hợp lệ (schema ScaledObject từ CRDs-catalog ở commit ghim của CI); lychee 0 lỗi.
  - A1, A3 trên simulator luôn ở 1 replica (không có GPU; KV-cache luôn 0): chỉ kiểm được đường đi, không đo được hành vi. A4 dưới tải (T7) chưa chạy.
- **Deviations:** Kế hoạch §6 ghi mỗi ID trong {S1, S4, A1…A4} là một file eval; Môi trường §14.1 lấy ví dụ `eval/A2.yaml`. Đã sửa theo cách runner của Quang đang chạy (A2 dùng file base chính thức; S1, S4 không có file).
- **Links:** nhánh `feat/tr2-a1-a4`; `autoscaling/eval/`, `experiments/tests/test_eval_configs.py`.
- **Thesis:** chương "Triển khai" (Kiến trúc §13.3): bốn cấu hình chỉ khác nhau ở tín hiệu, có test bảo đảm, nên so sánh A1 với A2 là công bằng. Hạn chế của simulator: không mô phỏng được A1 (không có GPU) và A3 (cần `--enable-kvcache`).

## 2026-11-07 – TR2: ma trận ĐG2 cho V2 (bản nháp) và xáo lượt theo seed trong runner

- **Task:** TR2 · **Environment:** none
- **Done:**
  1. Phát hiện `matrix.py` không xáo được thứ tự lượt (Thông số §8.2): các lần lặp của một ô được sinh liền nhau từ `repeats`; viết tách thành nhiều dòng thì trùng `run_id` và parse báo lỗi.
  2. Thêm vào `matrix.py` trường tuỳ chọn `shuffle_seed` ở gốc file ma trận: sắp các lượt theo `sha256("<seed>:<run_id>")`. Thêm kiểm tra số dương cho `capacity`, `rate`, `duration`, `repeats`, `kb3_replicas`, `replicas` và các override `threshold`, `max_replicas`, `min_replicas`.
  3. Viết `experiments/matrix-v2.yaml`: 17 lượt theo bảng Thông số §8.2, `shuffle_seed: 20261114`, cấu hình S1, S4, A1 (`autoscaling/eval/A1.yaml`), A2 (file base chính thức). Giá trị chờ ADR-003 gom vào khối `x-adr003` (YAML anchor): `C` và threshold A2 để `null`; `N` = 4 và model `qwen2.5-7b` theo thiết kế hiện tại.
  4. Thêm test: xáo tất định và không phụ thuộc thứ tự dòng (ghim thứ tự của seed 7); 8 ca giá trị sai; bản nháp V2 bị từ chối, điền thử C = 5, threshold 24 thì đúng số lượt mỗi ô.
- **Decision:**
  - Trình chọn thêm `shuffle_seed` vào runner (khoảng 10 dòng), thay vì ghi `repeat` cho từng lượt hoặc bỏ xáo. Không xáo thì thứ tự lượt trùng với thứ tự cấu hình, nên yếu tố trôi theo thời gian (nhiệt GPU, trạng thái node) bị tính nhầm thành khác biệt giữa cấu hình.
  - Không dùng `random.shuffle`: Python chỉ cam kết giữ dãy của `random()` qua các phiên bản, không cam kết với `shuffle`. Khoá băm cho cùng thứ tự trên 3.11 và 3.15, và thêm lượt mới (ví dụ A3 × KB, mức Could) không đảo thứ tự tương đối của các lượt cũ.
  - Trình chọn viết ma trận ngay với giá trị tạm, thay vì chờ ADR-003: ở V2 chỉ cần điền 2 số từ `capacity.json` (thêm `N`, model nếu ADR-003 đổi). `null` làm runner dừng ngay lúc đọc file, kể cả `--dry-run`.
  - Nhánh `feat/tr2-matrix-v2` xếp chồng lên `feat/tr2-a1-a4`, vì ma trận trỏ tới `autoscaling/eval/A1.yaml`. Thay đổi `matrix.py` (code của Quang, Q6) đi cùng ma trận V2 trong một PR riêng, nhỏ.
- **Results:**
  - `pytest experiments`: 49 passed trên Python 3.15 và 3.11. `ruff check`, `ruff format --check`, `yamllint` đạt.
  - Đọc lại cả 4 file ma trận bằng `matrix.load`: `matrix-dg1-home` 10 lượt, `matrix-home` 1, `matrix-sim` 2 (không đổi); `matrix-v2` báo `configs.A2.overrides: threshold phải là số dương, gặp None`.
  - Thứ tự V2 khi điền thử: A2-KB3-2, A1-KB3-1, S1-KB2-1, S4-KB1-1, A2-KB2-1, A2-KB3-1, A1-KB1-2, A2-KB2-2, A2-KB1-2, A2-KB1-1, A1-KB1-1, A2-KB2-3, S4-KB3-1, A1-KB2-2, A1-KB2-1, S4-KB2-1, S1-KB3-1. Thứ tự không phụ thuộc giá trị C hay threshold.
- **Incidents:**
  - Test có sẵn `test_render_scaledobject_overrides_and_pause` đỏ trên Windows với Python 3.11 → `read_text()` không truyền `encoding`, nên Python 3.11 trên Windows đọc bằng cp1252 và vấp chữ tiếng Việt trong A2; CI (Linux) và Python 3.15 (mặc định UTF-8) không gặp → thêm `encoding="utf-8"`.
  - Runner không chạy được `--dry-run` trên Windows (`import fcntl`, chỉ có trên Linux) → kiểm bằng `matrix.load`, cũng là bước đầu của `--dry-run`. Runner thật chạy trên Linux nên không sửa.
- **Deviations:** Thông số §7 ghi máy tạo tải đi qua route Traefik riêng; `serving/` chưa có route đó, nên `matrix-v2.yaml` gọi thẳng Service như `matrix-home.yaml`.
- **Links:** nhánh `feat/tr2-matrix-v2`; `82a3a8c`; `experiments/runner/matrix.py`, `experiments/matrix-v2.yaml`, `experiments/tests/test_runner.py`.
- **Thesis:** chương "Đánh giá", phần phương pháp (Môi trường §14): thứ tự lượt xáo bằng seed ghi trong Git, lần lặp thứ k của mọi cấu hình nhận cùng lịch gửi (so sánh theo cặp).

## 2026-11-07 – TR2: soát diff A1, A3, A4, sửa giải thích `or vector(0)` theo mã KEDA

- **Task:** TR2 · **Environment:** none
- **Done:**
  1. Chạy `/code-review high` cho `feat/tr2-sim..feat/tr2-a1-a4`: 10 phát hiện, kiểm từng điểm với mã nguồn, CI và tài liệu.
  2. Đối chiếu KEDA v2.21.0 `pkg/scalers/prometheus_scaler.go`: `ignoreNullValues` mặc định `true` (dòng 59); query trả rỗng thì scaler trả 0, không lỗi (dòng 286–291). Câu "rỗng làm KEDA báo lỗi và bật fallback" ở A1, A2 base và Kiến trúc §13.4 là sai.
  3. Sửa theo đó: comment A1 và A2 base (lý do của `or vector(0)`); Kiến trúc §13.4 (lý do đúng và hệ quả "mất tín hiệu không gây lỗi"); runbook `KedaScalerErrors` và bảng gỡ lỗi `w2.md` (query rỗng không gây lỗi scaler).
  4. Sửa thêm: header A1 (runner chỉ ghi đè max replica, threshold 70 giữ nguyên); comment nhãn `experiment/config` ở A1, A2 (không code nào đọc nhãn này, chỉ để `kubectl get -L` thấy); Môi trường §14.1 (bước áp cấu hình do runner làm); docstring `test_eval_configs.py`; mục nhật ký trước (thiếu dòng trống trước tiêu đề, dẫn sai Thông số §8.1).
  5. `test_runner.py` đọc file A2 bằng `encoding="utf-8"`: Python 3.11 trên Windows đọc theo cp1252 nên báo `UnicodeDecodeError`. Lỗi có từ trước, CI Linux không bị.
- **Decision:**
  - Giữ `or vector(0)` ở mọi query. Với A2 nó bắt buộc ở từng vế: phép `+` chỉ giữ phần tử có ở cả hai vế. Với A1, A3, A4 nó chỉ ghi rõ hành vi mặc định.
  - Không đặt `ignoreNullValues: "false"` cho A1 để bật fallback khi mất exporter: fallback đưa A1 lên max, trùng hành vi dự đoán của A1 (Kiến trúc §10.1), nên lượt hỏng còn khó nhận ra hơn.
  - Trình chọn làm phần kiểm tín hiệu ở một PR riêng trước V2: thêm trường `signal` trong ma trận; lượt bị chấm invalid nếu chuỗi tín hiệu mất mẫu quá 15 s, tức áp Môi trường §17 cho cả nguồn tín hiệu.
  - Bỏ qua 4 phát hiện: A4 `maxReplicaCount: 4` trên kind (giống A2, runner ghi đè theo môi trường); gộp phần chung của A2 vào runner (trái giao diện Kế hoạch §6, mỗi cấu hình là một file đầy đủ); threshold không có ngoặc kép (job `manifests` chạy kubeconform `-strict`, schema bắt metadata trigger là string). Dòng giao diện Kế hoạch §6 chỉ ghi lại cách runner của Quang đang chạy; đưa vào mục "Điểm cần review" của PR.
- **Results:** pytest `experiments` 39 passed trên 3.15 và 3.11; ruff, yamllint đạt; kubeconform `autoscaling/eval` 3/3, overlay `sim` 1/1; lychee 0 lỗi.
- **Incidents:** nhánh `feat/tr2-matrix-v2` không đạt `ruff format --check` (dòng 111 ký tự ở `test_runner.py:77`); sửa khi merge nhánh này sang.
- **Links:** `autoscaling/eval/A1.yaml`, `autoscaling/official/base/scaledobject-a2.yaml`, `docs/chi-tiet/03-kien-truc-autoscaling.md` §13.4, `docs/runbooks/KedaScalerErrors.md`.
- **Thesis:** chương "Triển khai" hoặc "Hạn chế": giá trị mặc định của KEDA biến việc mất tín hiệu thành "tải bằng 0" mà không báo gì. Đây là ví dụ cụ thể vì sao phải đọc mã nguồn ở bản ghim thay vì tin tài liệu thiết kế.

## 2026-11-07 – TR2: soát diff ma trận V2, xáo theo khối lần lặp, chặn khoá lạ trong ma trận

- **Task:** TR2 · **Environment:** none
- **Done:**
  1. Merge `feat/tr2-a1-a4` (bản đã sửa sau soát) vào `feat/tr2-matrix-v2`. Xung đột ở `test_runner.py:77` vì hai phía cùng sửa một dòng; lấy bản đã qua `ruff format`.
  2. Chạy `/code-review high` cho `feat/tr2-a1-a4..feat/tr2-matrix-v2`: 9 phát hiện. Chạy thử để kiểm: gõ nhầm `shufle_seed` thì runner lặng lẽ không xáo; `capacity` bằng `.nan` hay `.inf` lọt qua bước kiểm "số dương"; threshold `"24"` (chuỗi) bị từ chối, trong khi trước PR vẫn chạy được.
  3. `matrix.py` (code của Quang):
     - Xáo trong từng khối lần lặp: khoá sắp xếp là `(repeat, sha256(seed:run_id))`.
     - Từ chối khoá lạ ở mọi cấp (gốc, `target`, `timing`, `configs`, `overrides`, `defaults`, từng dòng `runs`). Khoá gốc `x-…` được bỏ qua vì đó là chỗ đặt anchor.
     - Số phải hữu hạn (`math.isfinite`). Số viết trong ngoặc kép thì báo lỗi kèm gợi ý cách sửa. `min_replicas` không được lớn hơn `max_replicas`. `kb3_replicas` và `repeats` chỉ đọc một lần (giá trị mặc định 4 trước đây viết ở hai chỗ).
  4. `session.py`: ghi `shuffle_seed` vào `metadata.json` của mỗi lượt.
  5. `matrix-v2.yaml`: sửa phép tính cooldown (4→1 xong ở 420 s chứ không phải 480 s; quá 600 s thì runner vẫn pause, ép về 1 replica); cập nhật comment về xáo theo khối và khoá `x-`. Thông số §8.2: thêm "trong từng khối lần lặp".
  6. 12 test mới: các ca lỗi trên, khoá `x-` được bỏ qua, thứ tự ghim mới của seed 7, và trên file V2 thật: 11 lượt đầu là lặp-1 và phủ đủ 11 ô.
- **Decision:**
  - Trình chọn xáo theo khối lần lặp thay cho xáo toàn bộ. Khi xáo toàn bộ với seed 20261114, `S4-KB2-1` và `S1-KB3-1` (lượt đối chứng duy nhất của ô đó) nằm ở vị trí 16 và 17, còn `A2-KB3-2` chạy đầu tiên; phiên V2 bị cắt ở khoảng lượt 15 sẽ mất đúng các lượt đối chứng. Khi xáo theo khối, 11 lượt đầu phủ đủ 11 ô. Các lượt cùng lần lặp dùng chung lịch gửi (`--run-index k`) và chạy gần nhau, nên so sánh cặp ít bị trôi theo thời gian hơn.
  - Threshold trong ma trận chỉ nhận kiểu số, không nhận chuỗi: chỉ một cách viết, runner tự đổi sang chuỗi cho KEDA, và thông báo lỗi chỉ cách sửa.
  - Không cho `min_replicas: 0`: thiết kế luôn giữ ít nhất 1 pod vì cold start mất vài phút.
  - Bỏ qua phát hiện "test phải ghim N = 4": N chốt ở ADR-003 và có thể là 2; test đã kiểm N nhất quán giữa S4, max replica và KB3.
- **Results:**
  - pytest `experiments` 61 passed trên 3.15 và 3.11 (49 cũ cộng 12 mới); `loadgen` 41 passed; ruff check, ruff format và yamllint đạt; kubeconform `autoscaling/eval` 3/3; lychee 0 lỗi.
  - `--dry-run` chạy trong WSL (Python 3.12), vì trên Windows runner không chạy được do dùng `fcntl`. `matrix-sim.yaml`: 2 lượt. Bản sao `matrix-v2.yaml` điền thử C = 5, threshold 24: 17 lượt, theo thứ tự A1-KB3-1, S1-KB2-1, S4-KB1-1, A2-KB2-1, A2-KB3-1, A2-KB1-1, A1-KB1-1, S4-KB3-1, A1-KB2-1, S4-KB2-1, S1-KB3-1 (lặp-1); rồi A2-KB3-2, A1-KB1-2, A2-KB2-2, A2-KB1-2, A1-KB2-2 (lặp-2); cuối cùng A2-KB2-3.
  - `matrix-sim.yaml`, `matrix-home.yaml`, `matrix-dg1-home.yaml` đều qua bước kiểm khoá chặt.
- **Deviations:** Thông số §8.2 đổi cách xáo thành xáo trong từng khối lần lặp; đưa vào mục "Điểm cần review" của PR.
- **Links:** `experiments/runner/matrix.py`, `experiments/runner/session.py`, `experiments/matrix-v2.yaml`, `experiments/tests/test_runner.py`, `docs/chi-tiet/00-thong-so.md` §8.2.
- **Thesis:** chương "Đánh giá", phần phương pháp: xáo theo khối lần lặp (randomized block design, mỗi khối là một lần lặp có chung lịch gửi). Lý do: chống trôi theo thời gian và giữ đủ ô khi phiên bị cắt ngang.

## 2026-11-07 – TR2: runner kiểm tín hiệu scale của A1, A2 (trường `signal` trong ma trận)

- **Task:** TR2 · **Environment:** sim (chỉ đọc Prometheus của kind)
- **Done:**
  1. Tạo nhánh `feat/tr2-signal-check` từ `feat/tr2-matrix-v2` (PR #18, xếp trên #17 và #16), vì việc này cần `matrix.py` chưa merge.
  2. `matrix.py`: thêm trường tuỳ chọn `signal` cho cấu hình `scaledobject`, là selector của chuỗi mà trigger đọc. Từ chối `signal` ở cấu hình tĩnh, và từ chối biểu thức (`sum(…)`, `x[5m]`), vì runner phải đặt `[Ns]` ngay sau selector.
  3. `collect.py`: thêm `signal_gap`. Hàm đọc mẫu gốc bằng range selector `<signal>[Ns]`, gộp mẫu của mọi chuỗi khớp selector, rồi tìm khoảng trống lớn nhất, tính cả hai mép của pha chính. `max_scrape_gap` thêm tham số `window`. Truy vấn lỗi thì trả `error`, không raise.
  4. `checks.py`: thêm tiêu chí 5. Lượt invalid nếu tín hiệu không có mẫu nào, mất mẫu quá 15 s, hoặc không truy vấn được.
  5. `session.py`: gọi `signal_gap` sau mỗi lượt. `check_signals` chạy một lần đầu phiên: hỏi `count(<signal>)` (selector sai cú pháp thì phiên dừng ngay; không có chuỗi nào thì cảnh báo), và đo độ lệch đồng hồ giữa runner và Prometheus (cảnh báo nếu quá 5 s). Lọc các lượt sẽ chạy một lần (`pending`) rồi dùng chung cho cả hai việc.
  6. Ma trận: `matrix-v2.yaml` khai báo `signal` cho A1 (`nvidia_smi_utilization_gpu_ratio`) và A2 (`vllm:num_requests_running{namespace="llm-serving"}`); `matrix-sim.yaml` khai báo cho A2.
  7. Tài liệu: Môi trường §17 thêm dòng "tín hiệu scale"; Kiến trúc §13.4 dẫn tới §17; comment của A1 bỏ câu "phải xem `gpu_util` trong metrics.csv.gz".
  8. `/code-review high` cho 10 phát hiện:
     - Sửa 6: đo lệch đồng hồ; lỗi truy vấn không làm mất `checks.json`; test so khớp nguyên selector, có ranh giới, thay cho so chuỗi con; chỉ đếm mẫu trong pha chính; `window` thay cho hai tham số `start`/`end` rời; lọc lượt một lần.
     - Bỏ 1: suy selector từ `query`.
     - Ghi thành việc sau 1 (xem Incidents).
- **Decision:**
  - Gộp mẫu của mọi chuỗi rồi mới tìm khoảng trống, không xét từng chuỗi, vì pod mới do scale-up có chuỗi bắt đầu giữa lượt. Đổi lại, check chỉ bắt được khi cả tín hiệu biến mất, cũng là ca KEDA đọc rỗng thành 0.
  - Tính cả hai mép cửa sổ: exporter chết rồi không quay lại thì giữa các mẫu còn lại không có khoảng trống nào.
  - Trình đã chọn kiểm tín hiệu cho A1 (07/11). Phiên này mở rộng sang A2 vì A2 hỏng theo cùng kiểu: truy vấn có `or vector(0)`, nên mất metric vLLM thì A2 đứng ở 1 replica. Mở rộng như vậy cũng giúp lượt A2 trên kind ngày 10/11 chạy thật được đường kiểm này.
  - Không suy selector từ `query` của ScaledObject, vì phải phân tích PromQL trong Python, dễ sai. Thay vào đó, một test quét mọi `experiments/matrix-*.yaml` và kiểm rằng `signal` nằm nguyên trong query, gồm cả label và có ranh giới hai đầu.
- **Results:**
  - pytest `experiments`: 76 passed, 1 skipped, trên cả Python 3.15 và 3.11. Test bị bỏ qua cần `fcntl`, không có trên Windows. Thân của test đó chạy bằng `python3` 3.12 trong WSL: đạt. ruff check, ruff format, yamllint và lychee (0 lỗi) đều đạt.
  - `signal_gap` trên Prometheus của kind (chỉ đọc, 07/11 khoảng 19:31):

    | Ca | Chuỗi | Mẫu | Khoảng trống lớn nhất | Kết quả |
    |---|---|---|---|---|
    | A2, 300 s vừa qua | 1 | 60 | 5,0 s | hợp lệ |
    | A2, mép cuối đặt 30 s sau hiện tại (giả tín hiệu tắt cuối pha) | 1 | 60 | 33,1 s | invalid, "mất mẫu 33 s" |
    | `nvidia_smi_utilization_gpu_ratio` (kind không có GPU) | 0 | 0 | 300 s | invalid, "không có mẫu nào" |
    | `foo{a=b}` (sai cú pháp) | – | – | – | invalid, "không kiểm được" (HTTP 400) |

  - `check_signals` trên kind: đồng hồ lệch +0,1 s; cảnh báo chuỗi GPU không có; A2 có 1 chuỗi.
  - Chưa chạy: một lượt runner đầy đủ trên kind với trường mới (để đến 10/11); kubeconform (`A1.yaml` chỉ đổi comment).
- **Incidents:** Bước soát chỉ ra một lỗ hổng có sẵn từ trước. `scrape_gaps` tìm khoảng trống trong mẫu `up`, nhưng Prometheus ghi `up = 0` cả khi scrape thất bại, nên một pod vLLM bị scrape lỗi liên tục không bị phát hiện. `signal_gap` gộp chuỗi nên cũng không bắt được ca này. PR này chưa sửa vì sửa sẽ đổi nghĩa một tiêu chí đang có. Việc sau: chỉ tính các mẫu `up == 1`.
- **Deviations:** Môi trường §17 thêm một điều kiện hợp lệ (tín hiệu scale), dùng cùng ngưỡng 15 s với khoảng trống scrape. Thay đổi này được nêu trong mục "Điểm cần review" của PR.
- **Links:** PR #16; PR #17 (`feat/tr2-a1-a4`, mở 07/11); PR #18 (`feat/tr2-matrix-v2`, mở 07/11); PR #19 (`feat/tr2-signal-check` → `feat/tr2-matrix-v2`, mở 07/11). File chính: `experiments/runner/matrix.py`, `collect.py`, `checks.py`, `session.py`; `experiments/matrix-v2.yaml`, `experiments/matrix-sim.yaml`, `autoscaling/eval/A1.yaml`; Môi trường §17; Kiến trúc §13.4.
- **Thesis:**
  - §5.1 (điều kiện hợp lệ của lượt, cách bảo đảm so sánh được): KEDA không báo lỗi khi mất tín hiệu, nên phải kiểm bên ngoài. Dùng bảng 4 ca trên kind.
  - §5.3 "vì sao không chọn GPU utilization": thêm một điểm yếu vận hành của A1. Exporter không có label pod, và mất exporter thì A1 đứng yên mà không có lỗi nào.

## 2026-11-07 – TR2: merge chuỗi PR #16–#19 vào `main`

- **Task:** TR2 · **Environment:** none (GitHub). Cluster nhà chịu ảnh hưởng gián tiếp qua Argo CD.
- **Done:**
  1. Trình bàn với Quang rồi cho phép tự merge (07/11). Kiểm trước khi merge:
     - cả 4 PR ở trạng thái `MERGEABLE`/`CLEAN`, CI 6/6 xanh, 0 review, 0 bình luận;
     - `main` không có commit mới;
     - mỗi nhánh chứa bản mới nhất của nhánh nằm dưới (`git merge-base --is-ancestor`).
  2. Merge theo thứ tự #16 → #17 → #18 → #19. Sau mỗi lần merge, đổi base PR kế tiếp sang `main` (`gh pr edit <n> --base main`) và kiểm diff chỉ còn phần của PR đó. Các nhánh vẫn giữ trên remote, như các PR trước.
  3. Sửa một câu viết ở ngôi thứ nhất trong mục 07/11 (T3, đồng hồ WSL2).
- **Decision:** merge bằng merge commit như các PR trước, không squash. PR sau chứa commit gốc của PR trước; nếu squash thì PR sau sẽ lặp lại diff của PR trước và dễ xung đột khi đổi base.
- **Results:**
  - Merge commit: #16 `f28c1a8`, #17 `1eb4eb6`, #18 `2321eee`, #19 `a7d2b7c`. CI trên `main` (push) đạt ở cả 4 commit.
  - `git diff origin/feat/tr2-signal-check origin/main` rỗng: cây của `main` trùng với bản CI đã kiểm ở #19.
  - Chưa kiểm: ở nhà, Argo CD tự sync `keda` (pod khởi động lại với `KEDA_HTTP_DISABLE_KEEP_ALIVE=true`, không còn limit CPU) và `monitoring` (`values.yaml`). Các app khác ở nhà không đọc file nào trong 4 PR này, và nhà chưa có app cho `autoscaling/` hay `observability/`. Trình chưa vào được cluster nhà, nên Quang theo dõi hai app trên.
- **Links:** PR #16, #17, #18, #19.

## 2026-11-07 – TR5: chốt tiêu chí hợp lệ của lượt và giao diện dữ liệu trước V2

- **Task:** TR5 (đụng runner của Q6) · **Environment:** sim (kind trong WSL2, máy Trình)
- **Done:**
  1. Trình giao tự chốt các câu còn treo về dữ liệu và tiêu chí hợp lệ: các câu hỏi Quang từ 25/10 và 07/11, cùng 2 câu Quang hỏi ở `viec-sap-lam.md` §2. Lý do: V2 (14–15/11) ghi dữ liệu theo định dạng lúc đó, và sau 22/11 không đo lại được. Tạo nhánh `feat/tr5-run-validity` từ `origin/main`.
  2. Đo độ trễ event loop của `loadgen` trên kind trước khi chọn ngưỡng (bảng ở Results):
     - simulator patch tạm (`--max-num-seqs=256`, `--inter-token-latency=10ms`, mỗi stream 100 chunk/s), 3 replica tĩnh;
     - runner chạy phiên `loop-probe` gồm CONST 10 và 20 req/s, mỗi mức 180 s; pod `loadgen` Guaranteed 1 CPU. Runner nạp code `loadgen` vào ConfigMap ở mỗi lượt, nên lượt 10 req/s chạy code của `main`, lượt 20 req/s chạy code của nhánh (đã có `loop_lag_ok`, `throttled_pct`);
     - xong thì áp lại `serving/overlays/sim` từ Git.
  3. `loadgen/checks.py`:
     - thêm `loop_lag_ok`: p99 < 50 ms và max < 500 ms;
     - `throttle_ok` tính theo tỷ lệ `throttled_usec` ÷ thời gian giữa hai lần đọc `cpu.stat` (< 0,1 %), thay cho `nr_throttled == 0`; ghi thêm `throttled_pct`. Không tính được tỷ lệ thì quay về `nr_throttled == 0`;
     - `loadgen/__main__.py` đo thời gian giữa hai lần đọc.
  4. `experiments/runner/checks.py`: lý do trượt liệt kê mọi khoá `*_ok` bằng False, nên tiêu chí mới của `loadgen` tự hiện ra mà không phải sửa runner.
  5. `experiments/runner/collect.py` và `session.py`: `scrape_gaps` chỉ tính mẫu `up == 1`, kèm mép cửa sổ theo pod (lấy từ `pods_start`, `pods_end`).
  6. Tài liệu:
     - Môi trường §3.6, §9, §14.2 (cột `requests.csv`, `loadgen.json`, nghĩa của `status` và `error`), §15, §17;
     - Vận hành §3.2 (`for: 1m` của `LLMErrorRateHigh` và `KedaScalerErrors`, tên `keda_scaler_detail_errors_total`).
  7. `/code-review high` cho 8 phát hiện:
     - Sửa 6: mép cửa sổ của `scrape_gaps` (trước đó bỏ sót scrape lỗi ở đầu và cuối lượt, cả pod không scrape được lần nào); ghi rõ `throttled_usec` là cận trên; đường dự phòng `nr_throttled`; số liệu ca 05/11 (mức đo khoảng 3 phút, không phải 5 phút); `for: 1m` ở dòng `KedaScalerErrors`; thiếu nhật ký.
     - Không sửa 1: chép ngưỡng sang `00-thong-so.md` (xem Decision).
  8. Chạy `experiments/matrix-sim.yaml` (S1 rồi A2) bằng nhánh này trên kind: mốc "runner 2 lượt liền không cần can thiệp" của Kế hoạch §1.1, hạn 10/11.
- **Decision:**
  - Giữ cột `id`, `n_in_target` và file `loadgen.json` (câu hỏi 25/10). Runner và `capacity.py` đã dùng chúng từ 06/11. Có `id` thì ghép được từng request giữa các cấu hình, vì cùng lịch gửi.
  - Một request thành công khi và chỉ khi cột `error` rỗng; không lọc theo `status` (câu 2 của Quang). Stream bị cắt giữa chừng vẫn có `status` 200. `capacity.py` đã lọc theo `error`.
  - `throttle_ok` theo tỷ lệ thời gian < 0,1 % (câu 1 của Quang).
    - Một chu kỳ 1,4–4,4 ms trong mức đo khoảng 3 phút (≤ 0,0025 %) đã loại hai mức ĐG1-mini ngày 05/11 mà số đo không đổi.
    - Kernel cộng `throttled_usec` theo từng CPU, nên tỷ lệ là cận trên.
    - Không bỏ hẳn kiểm throttle, vì thiết kế đòi; lệch lịch và event loop chỉ bắt được gián tiếp.
  - Event loop:
    - p99 < 50 ms, cùng ngưỡng với lệch lịch gửi, vì hai kiểm này đo cùng một sai số (một lúc gửi, một lúc nhận chunk);
    - max < 500 ms, để bắt một lần nghẽn dài mà p99 không thấy (1 % của lượt 25 phút là 15 s). 500 ms là 20 % ngưỡng TTFT 2,5 s.
  - `scrape_gaps`:
    - Pod có từ đầu lượt thì tính từ đầu pha chính. Pod còn sống, không đang bị xoá, ở cuối lượt thì tính tới cuối pha.
    - Pod mới đang cold start và pod đang drain không có mép tương ứng, nên lượt có scale-up hoặc scale-down không bị loại nhầm.
    - Pod sống suốt lượt mà không scrape được lần nào, hoặc không có chuỗi `up` nào, thì khoảng trống là cả cửa sổ.
    - Bỏ phương án đoán mép theo dung sai thời gian (mẫu đầu "gần" `start`): dễ sai khi scale-up sớm. Danh sách pod đầu và cuối lượt thì runner đã có sẵn.
  - Giữ `for: 1m` cho `LLMErrorRateHigh`: một lần chuyển pod sinh vài 503 lẻ, mà vẫn kịp N7.
  - Ngưỡng hợp lệ để ở Môi trường §17, cùng chỗ với 50 ms, 70 %, 15 s. Không chép sang `00-thong-so.md`, vì file đó không có mục điều kiện hợp lệ, và chép hai nơi thì dễ lệch.
  - Giữ CPU < 70 %, không nới ngưỡng sau khi thấy lượt 20 req/s trượt. Gần 100 % thì hàng đợi của event loop tăng phi tuyến. Muốn chịu tải cao hơn thì tách `loadgen` thành nhiều tiến trình (Incidents).
- **Results:**
  - pytest `loadgen` 47 passed; `experiments` 79 passed, 1 skipped; trên cả Python 3.15 và 3.11. ruff check, ruff format, lychee (0 lỗi) đều đạt.
  - Phiên `loop-probe`:

    | λ | Chunk/s | CPU tối đa | Event loop p99 / max | Lệch lịch p99 | Throttle | TTFT p50 / p99 (sim đặt 200 ms) | Kết quả |
    |---|---|---|---|---|---|---|---|
    | 10 req/s | ~2.500 | 53,1 % | 2,6 / 36,5 ms | 3,2 ms | 0 chu kỳ | 207 / 214 ms | hợp lệ |
    | 20 req/s | ~5.100 | 86,6 % | 4,9 / 56,0 ms | 6,1 ms | 1 chu kỳ, 4,7 ms (0,0026 %) | 210 / 235 ms | invalid (`cpu_ok`) |

    Ngưỡng event loop còn dư ít nhất 9 lần, ngay cả khi CPU lên 87 %. Lượt 20 req/s có 1 chu kỳ throttle 4,7 ms: luật mới chấm `throttle_ok` đạt (`throttled_pct` 0,0026), luật cũ sẽ loại; lượt chỉ trượt vì `cpu_ok`.
  - `matrix-sim.yaml`, phiên `sim-smoke` (20:18–20:34), không can thiệp tay:
    - `S1-CONST2-1`: hợp lệ; event loop p99 2,1 / max 17,0 ms; CPU 13,0 %; `throttled_pct` 0; khoảng trống scrape 5 s.
    - `A2-CONST2-1`: hợp lệ; scale 1 → 3 replica, cooldown về 1 replica sau 357 s; 357/357 request, 0 lỗi; event loop p99 1,9 / max 16,9 ms; CPU 20,7 %; tín hiệu `vllm:num_requests_running` có 3 chuỗi, 114 mẫu, khoảng trống 5 s.
    - Runner trong phiên này dùng bản `scrape_gaps` trước khi thêm mép, vì sửa sau soát làm sau khi phiên đã bắt đầu. Chạy lại bản cuối (`at_start`, `at_end` lấy từ `pods_start.json`, `pods_end.json`) trên Prometheus của kind, cùng cửa sổ, chỉ đọc: cả 3 pod của A2 (1 pod có từ đầu, 2 pod mới) và pod của S1 đều 5 s. Mép theo pod không làm loại nhầm pod mới.
- **Incidents:**
  - CPU của `loadgen` tăng theo số chunk/s, khoảng 0,2 ms CPU mỗi chunk trên laptop này. Ở nhà, ĐG1-mini λ = 10 cũng khoảng 2.500 chunk/s nhưng chỉ tốn 25,5 %. Chưa tách được bao nhiêu phần do CPU, bao nhiêu do WSL2.
  - Mỗi request 256 token là 256 chunk, nên ngưỡng 70 % ứng với khoảng 13 req/s cả cluster trên CPU như laptop, và khoảng 27 req/s trên CPU như máy nhà. Đỉnh KB3 ở V2 là 3C. Nếu C của 7B trên 4090 khoảng 4–6 req/s (ước tính, chưa đo), đỉnh là 12–18 req/s. VM thuê có CPU chậm như laptop thì các lượt KB3 có thể bị loại vì `cpu_ok`.
  - Event loop chạy một luồng, nên thêm lõi cho pod không giúp được. Việc tiếp theo, trước V2: `loadgen` chạy nhiều tiến trình, chia lịch gửi theo `id`.
- **Deviations:** Môi trường §17 đổi tiêu chí throttle, thêm ngưỡng số cho event loop, và định nghĩa lại khoảng trống scrape. Thay đổi được nêu ở mục "Điểm cần review" của PR.
- **Links:** nhánh `feat/tr5-run-validity`. File chính: `loadgen/checks.py`, `loadgen/__main__.py`, `experiments/runner/checks.py`, `collect.py`, `session.py`; Môi trường §9, §14.2, §17; Vận hành §3.2.
- **Thesis:**
  - §5.1 (cách bảo đảm số đo đúng): bảng `loop-probe` cho thấy máy tạo tải tự kiểm được sai số của chính nó. TTFT đo lệch 7–35 ms so với độ trễ đặt trong simulator, nhỏ so với SLO 2,5 s.
  - §4.11 (công cụ đánh giá): giao diện `requests.csv`, và lý do lọc lỗi theo `error`.
  - Phần hạn chế: giới hạn CPU một luồng của máy tạo tải viết bằng Python asyncio.

## 2026-11-07 – TR5: merge PR #21 (tiêu chí hợp lệ của lượt)

- **Task:** TR5 · **Environment:** none (GitHub)
- **Done:** Trình merge PR #21 lúc 20:51 bằng merge commit, như các PR trước. Trước khi merge: CI 6/6 xanh, `MERGEABLE`/`CLEAN`, 0 review.
- **Results:** merge commit `1f307db`; CI trên `main` (push) đạt. PR chỉ sửa `loadgen/`, `experiments/` và `docs/`, không có file nào Argo CD ở nhà đọc, nên cluster nhà không đổi.
- **Links:** PR #21.

## 2026-11-07 – TR5: `loadgen` chạy nhiều tiến trình

- **Task:** TR5 · **Environment:** sim (kind trong WSL2, máy Trình)
- **Done:**
  1. Tạo nhánh `feat/tr5-loadgen-multiproc` từ `origin/main`. Lý do: một tiến trình `loadgen` lên 87 % CPU ở 20 req/s trên laptop, vượt ngưỡng 70 % (mục "tiêu chí hợp lệ" ở trên). Event loop của asyncio chạy một luồng, nên thêm lõi cho pod không giúp được.
  2. `loadgen/workers.py` (mới):
     - chia lịch theo `id mod k`;
     - tiến trình con (`multiprocessing` kiểu `spawn`) báo sẵn sàng; tiến trình cha đặt mốc chung `t0_unix` = lúc mọi con sẵn sàng + 1 s;
     - mỗi request xong, con gửi dòng kết quả qua Pipe; cha ghi một `requests.csv`, flush từng dòng như trước;
     - một con lỗi giữa chừng thì cha dừng ngay các con còn lại, ghi lỗi vào `worker_stats` và vẫn trả kết quả, không treo.
  3. `loadgen/sender.py`: `run` nhận `sink` (nơi ghi từng dòng) và `t0_unix`. Mỗi tiến trình đổi `t0_unix` sang `perf_counter` một lần.
  4. `loadgen/checks.py`:
     - lệch lịch gửi và event loop chấm riêng từng tiến trình rồi lấy tiến trình tệ nhất;
     - CPU lấy tiến trình bận nhất;
     - thêm `complete_ok`: số dòng kết quả bằng số request trong lịch, và không tiến trình nào lỗi.
  5. `loadgen/__main__.py`:
     - thêm cờ `--workers` (mặc định 1: chạy trong tiến trình chính, như trước);
     - `loadgen.json` thêm `workers` và `worker_stats` (số request, CPU, lệch lịch, event loop của từng tiến trình);
     - một tiến trình lỗi thì `valid: false` và mã thoát 1.
  6. Runner:
     - `Target.loadgen_workers` = số lõi nguyên của `loadgen_cpu`, truyền `--workers` ở cả warm-up lẫn pha chính;
     - `matrix.parse` từ chối `loadgen_cpu` không khớp `\d+(\.\d+)?m?` hoặc bằng 0 (" 2", "1_000m", "inf");
     - memory của Job = 256Mi × (k + 1).
  7. `experiments/matrix-v2.yaml`: `loadgen_cpu` đổi từ "2" sang "3".
  8. `experiments/matrix-dg1-home.yaml`: chỉ thêm comment. Ma trận ĐG1 ở nhà (`loadgen_cpu: "2"`) từ nay chạy 2 tiến trình.
  9. Tài liệu: Môi trường §3.5 (pod máy tạo tải 3 lõi, memory theo số tiến trình), §3.6, §9 (đoạn "Nhiều tiến trình gửi tải"), §14.2, §17.
  10. Kiểm trên kind:
     - simulator patch tạm (`--max-num-seqs=256`, `--inter-token-latency=10ms`, mỗi stream 100 chunk/s), 3 replica tĩnh;
     - 3 phiên runner, mỗi phiên một lượt CONST 180 s;
     - xong thì áp lại `serving/overlays/sim` và `autoscaling/official/overlays/sim` (runner đã xoá ScaledObject A2 khi áp cấu hình tĩnh S3).
  11. `/code-review high` trên diff (10 điểm, công cụ ghi rõ là chưa xác minh). Sửa 8:
      - lệch lịch gửi trước đó còn gộp mẫu của mọi tiến trình;
      - mất dòng kết quả (lỗi khi ghi CSV bị nuốt trong task) mà không tiêu chí nào bắt, nên thêm `complete_ok`;
      - một con lỗi mà cha vẫn chờ các con khác chạy hết lịch (KB3 25 phút trên máy thuê);
      - `wall_s` âm khi một tiến trình không được chia request nào;
      - `loadgen_cpu` lạ lọt qua `float()`;
      - comment ma trận ĐG1 ở nhà đã cũ;
      - số liệu CPU lệch nhau giữa các file, có số ước tính viết như số đo;
      - lặp code tạo `WorkerStats`.

      Không sửa 2 điểm, xem Decision.
- **Decision:**
  - Chia xoay vòng theo `id`, không chia theo khúc thời gian: mọi tiến trình cùng bận ở mọi pha của λ(t). Mỗi request đều 256 token, nên chunk/s chia đều.
  - Mốc chung là giờ hệ thống, đổi sang `perf_counter` một lần ở mỗi tiến trình. Python không bảo đảm `perf_counter` của hai tiến trình cùng gốc.
  - Cha ghi một `requests.csv`, không để mỗi con ghi một file rồi gộp:
    - giữ nguyên giao diện dữ liệu (Môi trường §14.2);
    - giữ runbook "60 s không có dòng CSV mới" (Kế hoạch §9.5).
  - Event loop chấm theo tiến trình tệ nhất, không gộp mẫu. Với 4 tiến trình, 1 % mẫu của một tiến trình nghẽn chỉ còn 0,25 % mẫu chung, nên p99 chung không thấy nó. Throttle vẫn đọc theo cgroup của cả pod.
  - Số tiến trình suy từ `loadgen_cpu`, không thêm khoá ma trận riêng: chỉ một núm, nên không lệch nhau được.
  - Dùng `spawn`, không dùng `fork`: không thừa kế trạng thái của cha, và chạy giống nhau trên Linux lẫn Windows. Khởi động chậm khoảng 0,3 s mỗi con, nhưng xảy ra trước t0 nên không ảnh hưởng số đo.
  - `matrix-v2` dùng 3 lõi:
    - đo được: một tiến trình ở 10 req/s tốn 53–58 % CPU, ở 20 req/s lên 87–88 %. Ước tính (chưa đo ở mức đó) một tiến trình chạm 70 % ở khoảng 12–14 req/s, nên 3 tiến trình chịu khoảng 36–42 req/s, gấp đôi đỉnh KB3 ước tính 12–18 req/s (C = 4–6, chưa đo);
    - 3 lõi vừa cả máy 32 lẫn 48 vCPU (Môi trường §3.5).
    - Bỏ "2": chỉ dư khoảng 1,4–1,6 lần nếu C = 6. Bỏ "4": không vừa máy 32 vCPU.
  - Hai điểm soát không sửa:
    - Chuẩn hoá `throttled_usec` theo số lõi. Tỷ lệ hiện tại là cận trên đã chủ ý chọn ở PR #21. Chia cho k thì bỏ sót trường hợp chỉ một tiến trình bị dừng. Hai phiên nhiều tiến trình đều 0 throttle.
    - Giảm CPU mỗi chunk thay cho chạy nhiều tiến trình. Đo `json.loads` một chunk 222 byte: 1,8 µs, tức 0,9 % của 0,2 ms. Phần lớn chi phí nằm ở httpx và asyncio, sửa phần parse không giảm được bao nhiêu.
- **Results:**
  - pytest `loadgen` 54 passed (thêm 7 test, gồm 3 test chạy 2 tiến trình thật qua server HTTP giả); `experiments` 96 passed, 1 skipped; trên Python 3.15 và 3.11. ruff check, ruff format, yamllint, lychee (0 lỗi) đạt.
  - Test mốc chung: giờ request tới server khớp `t0_unix + t_sched` trong 100 ms ở mọi request của cả 2 tiến trình.
  - Kind, CONST 180 s, phiên `mp-probe-w1/w2/w3` (21:15–21:29):

    | λ | Tiến trình | Chunk/s | CPU tối đa (tiến trình bận nhất) | Throttle | Event loop p99 / max | Lệch lịch p99 | TTFT p50 / p99 (sim đặt 200 ms) | RAM pod | Kết quả |
    |---|---|---|---|---|---|---|---|---|---|
    | 20 req/s | 1 | ~5.100 | 88,2 % | 10 chu kỳ, 194 ms (0,106 %) | 5,9 / 67,1 ms | 8,1 ms | 211 / 246 ms | 46 MiB | invalid (`cpu_ok`, `throttle_ok`) |
    | 20 req/s | 2 | ~5.100 | 57,7 % / 57,6 % | 0 | 2,6 / 57,2 ms | 3,3 ms | 207 / 214 ms | 100 MiB | hợp lệ |
    | 30 req/s | 3 | ~7.700 | 54,7 / 54,9 / 56,2 % | 0 | 2,5 / 39,1 ms | 3,0 ms | 207 / 213 ms | 133 MiB | hợp lệ |

  - Mỗi tiến trình ở 10 req/s (khoảng 2.560 chunk/s) tốn 55–58 % CPU, tức khoảng 0,22 ms CPU mỗi chunk, cùng mức với đo trước đó trong ngày.
  - Lịch của phiên 1 và 2 tiến trình trùng nhau ở cả 3.576 request (`id`, `t_sched`, `n_in_target`).
  - Ở 20 req/s, TTFT p99 từ 246 ms còn 214 ms khi tách 2 tiến trình. Hai lượt cùng simulator, cùng lịch, chỉ khác số tiến trình, nên phần chênh khoảng 32 ms nhiều khả năng là sai số do máy tạo tải quá tải.
  - RAM lấy từ `container_memory_working_set_bytes`, giá trị lớn nhất trong lượt.
  - Ba phiên trên chạy bản trước khi soát. Bản cuối (sau khi sửa theo soát) chạy thêm phiên `mp-final-w2` (21:44–21:48):
    - simulator cấu hình gốc, S1, CONST 2 req/s × 60 s, 2 tiến trình;
    - 114/114 request, mỗi tiến trình 57; mọi khoá `*_ok`, kể cả `complete_ok`, đạt;
    - lệch lịch p99 2,4 / 2,0 ms theo từng tiến trình; runner chấm `done`.
    - Sau đó áp lại A2 trên kind.
- **Incidents:**
  - Lượt 1 tiến trình hôm nay bị throttle 0,106 % (194 ms), lần đo trước đó trong ngày chỉ 0,0026 %. CPU 88 % mà pod 1 lõi thì thời gian bị throttle dao động mạnh; tách tiến trình thì hết throttle.
  - Lúc đầu ghi nhầm ngày đo là 08/11 trong comment và tài liệu. Lệnh `sed` thay hàng loạt "08/11" → "07/11" trên cả `docs/chi-tiet/` đổi nhầm 10 ngày hợp lệ (lịch V2 cũ "07–08/11", "Chủ nhật 08/11", tuần W5 "02–08/11") ở Môi trường và Kế hoạch.
    `git status` lộ ra file Kế hoạch không định sửa. Đã khôi phục cả 10 chỗ trước khi push, và đối chiếu `git diff origin/main` của từng file. Bài học: sửa ngày thì sửa từng chỗ, không thay hàng loạt.
- **Deviations:** Môi trường §3.5 trước ghi pod máy tạo tải 4 lõi, `memory 4Gi` (máy 48 vCPU); nay là 3 lõi, memory 256Mi × (số lõi + 1). Nêu ở mục "Điểm cần review" của PR.
- **Links:** nhánh `feat/tr5-loadgen-multiproc`. File chính: `loadgen/workers.py`, `sender.py`, `checks.py`, `__main__.py`; `experiments/runner/matrix.py`, `loadjob.py`, `session.py`; `experiments/matrix-v2.yaml`; Môi trường §3.5, §3.6, §9, §14.2, §17.
- **Thesis:**
  - §4.11 (công cụ đánh giá): máy tạo tải nhiều tiến trình vẫn giữ lịch open-loop tái lập được; vì sao chấm event loop theo tiến trình tệ nhất.
  - §5.1 (cách bảo đảm số đo đúng): bảng 3 phiên cho thấy máy tạo tải quá tải làm TTFT p99 tăng 32 ms, và tự kiểm bắt được lượt đó.
  - Phần hạn chế: giới hạn một lõi của Python asyncio, và cách khắc phục bằng nhiều tiến trình.

## 2026-11-07 – TR5: merge PR #22 (`loadgen` nhiều tiến trình)

- **Task:** TR5 · **Environment:** none (GitHub)
- **Done:** Trình merge PR #22 lúc 22:01 bằng merge commit. Trước khi merge: CI 6/6 xanh, `MERGEABLE`/`CLEAN`, 0 review.
- **Results:** merge commit `6905cfe`, base `1f307db`; CI trên `main` (push) đạt. PR chỉ sửa `loadgen/`, `experiments/` và `docs/`, nên cluster nhà không đổi.
- **Links:** PR #22.

## 2026-11-07 – TR3: 3 dashboard Grafana, kiểm trên kind

- **Task:** TR3 · **Environment:** sim
- **Done:**
  1. Đọc Vận hành §1–§3, §9; Kiến trúc §17; Thông số §3, §6, §8.1, §9; CONTRIBUTING §4. Đối chiếu tên metric và nhãn với mã nguồn ở bản đã ghim: vLLM v0.31.0 (`vllm/v1/metrics/loggers.py`, `buckets.py`, `FinishReason`), nvidia_gpu_exporter 1.15.1 (`internal/exporter/exporter.go`, cách đặt tên theo đơn vị), KEDA v2.21.0 (`pkg/metricscollector/prommetrics.go`), và kube-state-metrics đang chạy trên kind.
  2. Viết 3 dashboard JSON trong `observability/dashboards/`: Serving và GPU (20 panel), Autoscaling (9 panel), SLO và chi phí (16 panel). Mỗi panel có mô tả tiếng Việt giải thích metric và ngưỡng (JSON không có comment).
  3. Thêm `configMapGenerator` vào `observability/kustomization.yaml` (label `grafana_dashboard: "1"`, không hash); README cách nạp, sửa, quy ước, annotation; target `make dashboards-check` và bước tương ứng trong job `alerts` của CI.
  4. Áp `observability/` lên kind (Grafana 13.2.3 của chart 92.1.1); sidecar nạp cả 3 dashboard. Bơm 2 lượt tải `hey` 25 request đồng thời × 240 s qua `autoscaling/tests/load-sim.sh`. Chạy mọi truy vấn của dashboard qua `/api/ds/query` của Grafana, rồi chụp ảnh panel bằng grafana-image-renderer v5.12.7. Renderer chỉ bật tạm trên kind bằng một file values cục bộ, không commit.
  5. Thêm `serving/overlays/sim/patch-podmonitor-sim.yaml` để đổi nhãn `finish_reason` của simulator thành `finished_reason` lúc scrape.
- **Decision:**
  - JSON là nguồn sự thật (CONTRIBUTING §4). Trình sinh lần đầu bằng script cục bộ, không commit script. Giải nghĩa PromQL nằm trong `description` của panel.
  - Datasource là biến `${datasource}` để một file chạy ở home, cloud, sim. Giữ tên ConfigMap cố định (không hash), vì `kubectl apply` không xoá ConfigMap cũ, dẫn tới hai bản cùng uid.
  - Đổi nhãn của simulator ở PodMonitor của overlay `sim`, không dùng `label_replace` trong truy vấn, để dashboard chỉ dùng tên của vLLM thật.
  - TPOT của SLO đo bằng `vllm:request_time_per_output_token_seconds` (mỗi request một mẫu, có bucket 0,1); ITL chỉ vẽ ở dashboard Serving.
  - Các ô "trong khoảng đang xem" (GPU-giờ, chi phí, ngân sách lỗi) tính trên khoảng thời gian chọn ở Grafana, để đọc được đúng một lượt ĐG2. Panel theo ngày dùng `offset -1d` để cột của một ngày gồm chính ngày đó.
  - Annotation pha của runner: Grafana API, tag `llm-run`. Dashboard đã có lớp lọc tag này; runner chưa gửi.
  - GPU-giờ đếm pod vLLM đã được xếp lên node (`kube_pod_status_scheduled{condition="true"}`), không dùng `kube_deployment_status_replicas` như ví dụ ở Vận hành §9: cách cũ đếm cả pod Pending chưa có GPU và bỏ sót pod đang tắt (vẫn giữ GPU).
- **Results:**
  - `make dashboards-check`: 3 dashboard đạt. Thử một file hỏng có 4 lỗi (uid trùng, còn `id`, datasource ghi cứng, PromQL thiếu ngoặc): bắt đủ 4, mã thoát khác 0. `make alerts-test`, `yamllint -s .`, `actionlint`, kubeconform (`observability` 6/6, `serving/overlays/sim` 4/4) đều đạt.
  - Lượt tải 1: 15:19:56–15:24:08 UTC, 947 request đều HTTP 200, độ trễ phía `hey` p50 4,67 s, p95 13,0 s. Lượt 2: 15:26:47–15:31:00 UTC, 991 request đều HTTP 200.
  - Dashboard Autoscaling thấy đủ chuỗi: tín hiệu 25 so với target × replica 10 → desired 3. Mốc lượt 1 (Prometheus, UTC): `hey` bắt đầu 15:19:56; 16 request đang chạy lúc 15:19:58; desired = 3 lúc 15:20:04; Ready = 3 lúc 15:20:19 (kube-state-metrics scrape 15 s, hai mốc sau sai số tới 15 s); 2 pod ở "Running, chưa Ready" khoảng 7 s (cold start trên simulator 6–7 s theo bảng tạo → Ready). Scale-down 3 → 2 → 1, về 1 lúc 22:36:56, mỗi lần có pod "đang tắt" khoảng 20 s. Đường Prometheus đi trước đường HPA vài giây.
  - Sau lượt 1 (cửa sổ 1 phút): TTFT p95 0,24 s, thời gian chờ hàng đợi p95 4,68 s, toàn request p95 14,3 s; request đang chạy chạm 16 = `--max-num-seqs`.
  - Dashboard SLO và chi phí, khung 22:15–22:39: 1929 request vLLM trả xong (Prometheus `increase`, ước lượng); TTFT, TPOT tốt 100%; GPU-giờ 0,95; 149,9 nghìn token; 0,48 USD với đơn giá 0,5; 3,169 USD / 1 triệu token; 66,7% thời gian ở max replica; đỉnh 25 request đồng thời. Cảnh báo `LLMAtMaxReplicas` và `LLMPodNotReady` hiện ở trạng thái pending.
  - Trống đúng dự kiến trên kind: hàng GPU, preemption, hàng KEDA (chưa thu metric KEDA operator), 5xx (không có Traefik).
- **Incidents:**
  - Image Prometheus không có `wget` → gọi API qua `kubectl port-forward` + `curl`.
  - Simulator v0.12.0 dùng nhãn `finish_reason`, vLLM v0.31.0 dùng `finished_reason` → panel lý do kết thúc trống trên kind → sửa bằng `metricRelabelings` ở overlay `sim`.
  - TTFT của simulator không gồm thời gian chờ hàng đợi (p95 0,24 s trong khi chờ p95 4,7 s). Vì vậy quá tải trên kind không làm burn rate hay `LLMSLOBurnFast` thay đổi. Đã ghi vào README.
  - Panel state-timeline trên Grafana 13.2.3 không áp màu của value mapping khi chế độ màu là `thresholds`. Trình thử 3 biến thể trên một dashboard tạm (đã xoá) và chọn chế độ `fixed`.
  - Ô stat không có dữ liệu hiện chữ "No data" đỏ cỡ lớn → đặt `noValue` là "–", bậc màu đầu là màu chữ thường.
  - Panel theo ngày ban đầu trống vì ngày hôm nay chưa trọn → `offset -1d`. Khi dashboard đặt khoảng thời gian tuyệt đối, Grafana bỏ qua thiết lập 7 ngày riêng của panel (ghi trong mô tả panel).
- **Review:** `/code-review high` trên nhánh báo 10 điểm; sửa 9: cách đếm GPU-giờ; `dashboards-check` bắt thêm datasource dạng chuỗi, thiếu uid hoặc `null` và thay đủ biến Grafana (`$__range_s`, `${var:format}`), báo rõ khi thiếu promtool (đã thử lại từng ca); bảng cold start giữ cả pod đã scale-down (`max_over_time` trên subquery, kiểm trên kind: đủ 3 pod 6/7/6 s); mô tả mốc ngày sửa thành giờ trình duyệt (ảnh chụp cho cột ở 00:00 giờ Việt Nam, không phải 07:00); ô đơn giá ghi rõ dấu chấm thập phân; ô "Hiện tại" chạy truy vấn instant; ghi chú rủi ro `op: add` trong patch PodMonitor. Không làm: recording rule cho TPOT và GPU-giờ chỉ để bớt lặp biểu thức trong JSON (TPOT không có cảnh báo).
- **Deviations:** Vận hành §9: GPU-giờ đếm pod đã xếp lên node thay cho `kube_deployment_status_replicas`. Kiến trúc §17.3: chưa vẽ "độ lệch lịch gửi của máy tạo tải", vì `loadgen` không xuất metric Prometheus và lệch lịch đã được chấm trong `checks.json`. Annotation pha đã có phía dashboard, runner chưa gửi. Vận hành §9: GPU-giờ và chi phí tính trên khoảng đang xem thay cho cố định 24 giờ, và có thêm panel theo ngày. Hàng KEDA trống cho tới khi có việc thu metric KEDA operator.
- **Links:** nhánh `feat/tr3-dashboards`. File chính: `observability/dashboards/*.json`, `observability/dashboards/README.md`, `observability/kustomization.yaml`, `Makefile` (`dashboards-check`), `.github/workflows/ci.yaml`, `serving/overlays/sim/patch-podmonitor-sim.yaml`.
- **Thesis:** §4 (giám sát): ba dashboard, cách nạp bằng sidecar, kiểm PromQL trong CI. Ảnh chụp ba dashboard trên kind (máy Trình, `.work/tr3/screens/`) dùng làm hình minh hoạ chuỗi tín hiệu → HPA → pod → Ready; bản cuối nên chụp lại trên V2. Phần hạn chế: TTFT của simulator không gồm thời gian chờ.

## 2026-11-07 – TR3: merge PR #23 (3 dashboard Grafana)

- **Task:** TR3 · **Environment:** none (GitHub)
- **Done:** Trình merge PR #23 lúc 23:53 bằng merge commit. Trước khi merge: CI 6/6 xanh, `MERGEABLE`/`CLEAN`, 0 review.
- **Results:** merge commit `0b97acd`, base `6905cfe`; CI trên `main` (push) đạt. PR không đổi cluster nhà, vì chưa có Application Argo CD cho `observability/`.
- **Links:** PR #23.

## 2026-11-08 – TR5: bộ đọc log khởi động vLLM (`parse_vllm_log`)

- **Task:** TR5 · **Environment:** none (mã nguồn upstream, test cục bộ)
- **Done:**
  1. Đọc Kiến trúc §7 (cold start 8 pha), Môi trường §12 (ĐG3) và §14.2, Kế hoạch §6 (giao diện `parse_vllm_log(text) → dict`), việc Q4 trong bàn giao của Quang.
  2. Tải mã nguồn vLLM tag v0.31.0 (commit `db9527a`, đúng tag ghim ở `serving/base/kustomization.yaml`) và uvicorn 0.54.0. Đối chiếu từng dòng log mức INFO của pha 4–8: câu chữ, mức log, tiến trình in ra, thứ tự xuất hiện.
  3. Viết `experiments/runner/vllm_log.py`. `parse_vllm_log(text)` trả về mốc tuyệt đối, số giây vLLM tự báo, độ dài pha 4–8 lấy được từ log và vài thông số khởi động (KV-cache, dung lượng checkpoint, compile cache ấm hay lạnh). `phases()` nhận thêm `startedAt` của container và lúc pod Ready để tính đủ pha 4 và 8. Có CLI đọc file hoặc stdin. 20 test chạy trên log mẫu dựng từ câu chữ trong mã nguồn (không phải log thật, số trong đó là số bịa).
  4. Sửa câu chữ log ở Kiến trúc §7.2 (pha 5–8) cho đúng v0.31.0.
- **Decision:**
  - Mốc thời gian lấy từ tiền tố kubelet (`kubectl logs --timestamps`, tới nano giây) thay cho giờ vLLM tự in (chỉ tới giây, không có năm). Log không có tiền tố thì dùng giờ vLLM và ghi rõ trong `time_source`.
  - Pha 5 lấy số vLLM tự báo (log không có mốc bắt đầu tải); pha 6 = đồng hồ nạp model trừ pha 5. Nhờ vậy các pha nối tiếp và cộng lại đúng bằng tổng.
  - PR này chưa làm pha 1–3 và phần Kubernetes của pha 4, 8. Ảnh chụp pod của runner (`pods_*.json`) chưa có `startedAt` và conditions; việc đó để một PR nhỏ sau.
  - Mẫu regex gom trong một bảng `PATTERNS` (Kiến trúc §7.2 yêu cầu dễ chỉnh). Log của bản vLLM khác 0.31.0 vẫn đọc, kèm cảnh báo.
- **Results:**
  - Phát hiện trong mã nguồn v0.31.0 (mỗi điểm đều có test):
    - Trên CUDA, V2 model runner là mặc định (`vllm/config/vllm.py`, `use_v2_model_runner`). Dòng bắt đầu nạp model là `Loading model from scratch...`; `Starting to load model …` chỉ có ở V1.
    - `Graph capturing finished` được in hai lần. Lần đầu là chụp thử để đo bộ nhớ CUDA graph trong lúc profiling (`v1/worker/gpu/cudagraph_utils.py:928`, `capture_model(profile_only=True)`), trước dòng `GPU KV cache size`; lần sau là chụp thật. Khớp với hai số Quang ghi ở nhật ký tuần 03 (42 s + 38 s trên Docker, 44 s + 40 s trên k3s): lần chụp thử chiếm khoảng 40 s mỗi lần khởi động ở máy nhà.
    - Thời gian tải từ Hugging Face không nằm trong `Loading weights took`, vì vLLM tải xong file rồi mới bấm giờ. Dòng `Time spent downloading weights` chỉ in khi tải mất hơn 0,5 s.
    - Với torch 2.13, AOT compile bật mặc định. Khi cache đã ấm, log có `Directly load AOT compilation from path` và không có dòng `torch.compile took`.
    - Cổng 8000 được `bind` từ sớm nhưng chỉ `listen` sau khi uvicorn in `Application startup complete.` Khi nhận socket từ vLLM, uvicorn không in `Uvicorn running on`. Trước lúc `listen`, probe bị từ chối kết nối, khớp với pha 8 ở Kiến trúc §7.2.
    - `VLLM_ENABLE_STARTUP_PLAN=1` (mặc định tắt) lưu kết quả profiling vào `$VLLM_CACHE_ROOT/startup_plan/`. Các lần khởi động sau bỏ qua bước đo bộ nhớ và lần chụp graph thử, với điều kiện bộ nhớ GPU còn trống không ít hơn lúc ghi. Chưa thử trên GPU.
  - `uv run --project experiments pytest experiments`: 116 đạt, 1 bỏ qua, trên cả Python 3.15 và 3.11. `ruff check` và `ruff format --check` đạt; lychee cho Kiến trúc 03 đạt.
  - Chạy trên 3 file log simulator thật từ kind (`runs/sim/mp-probe-w1/S3-CONST20-1/attempt-1/logs/`): không lỗi, `complete = false`, thiếu đủ 6 mốc bắt buộc, đúng như dự kiến. Một log 100.037 dòng đọc hết trong 0,36 s.
  - Chưa chạy trên log vLLM thật từ GPU: cluster nhà chưa vào được và chưa thuê máy.
  - Hạn chế đã thấy ở runner: `collect.write_logs` chỉ thu log của pod còn sống lúc thu, nên pod scale-down giữa lượt KB2 mất log khởi động.
- **Incidents:**
  - Tarball mã nguồn tải từ codeload bị cụt (gzip "unexpected end of file") → chuyển sang `git clone --depth 1 --sparse`. Checkout lỗi "Filename too long" ở các file JSON cấu hình kernel → chỉ checkout `*.py`, bật `core.longpaths`.
- **Review:** `/code-review high` trên nhánh báo 10 điểm, 9 điểm sửa trong code: tách dòng vật lý theo `\n` trước để mảnh sau `\r` giữ mốc kubelet; ngày không hợp lệ (29/02 năm không nhuận) không còn làm lỗi; stdin đọc bằng UTF-8 (trên Windows mặc định là cp1252); pha 5 = 0 khi đã nạp model xong mà không có dòng tải về (gồm cả loader khác); pha 7b âm trong ±0,5 s (sai số do vLLM làm tròn 7c tới giây) thì đặt bằng 0; đọc RFC 3339 trực tiếp bằng `fromisoformat` (Python 3.11 nhận nano giây); gom mẫu theo nguồn; bỏ trạng thái thừa; regex uvicorn chấp nhận tiền tố `(APIServer pid=N)`. Riêng điểm tiền tố này không đúng với v0.31.0, vì `decorate_logs` chỉ gắn tên tiến trình vào bản ghi log chứ không bọc stdout, nhưng đúng với các bản cũ nên vẫn sửa. Điểm thứ 10 (thiếu nhật ký) được giải quyết bằng chính mục này.
- **Deviations:** Kiến trúc §7.2: sửa câu chữ log của pha 5–8 theo v0.31.0 (hai dòng chụp graph, `took … s`, dòng tải về, dòng mở cổng). Pha 1–3 chưa có bộ đọc.
- **Links:** nhánh `feat/tr5-parse-vllm-log`, commit `3088a2b`, `9d50bbd`. File chính: `experiments/runner/vllm_log.py`, `experiments/tests/test_vllm_log.py`, `docs/chi-tiet/03-kien-truc-autoscaling.md`.
- **Thesis:** §5 cold start (ĐG3, N5, LT4): bảng đối chiếu mốc log với pha; hai lần chụp CUDA graph giải thích một phần độ dài pha 7; startup plan là một phương án L2 (nếu thử). Hình nên có: dòng thời gian các mốc log của một lần khởi động thật, vẽ khi có log từ V0 hoặc V2.

## 2026-11-08 – TR5: dòng thời gian pod và log pod bị scale-down (`PodWatcher`)

- **Task:** TR5 · **Environment:** sim (kind `llm-sim`, Kubernetes v1.37.0)
- **Done:**
  1. Đọc Kiến trúc §7.2, §7.4, §8; Môi trường §12, §14.1, §14.2, §15, §17; Kế hoạch §6 (giao diện "Dữ liệu"); Thông số §9.2 (preStop 20 s, grace 180 s). Đọc JSON của một pod simulator thật trên kind để đối chiếu tên trường.
  2. `collect.snapshot_pods` thêm `node`, `created`, `deletion_timestamp`, `deletion_grace_s`, `conditions`, `containers`, `init_containers`; các trường cũ mà `checks.py` dùng giữ nguyên.
  3. Thêm `collect.pod_marks` (hàm thuần): đổi ảnh chụp sang mốc giây UNIX gắn với 8 pha (`created`, `scheduled`, `sandbox_ready`, `initialized`, `container_started`, `ready`, `delete_requested`, `container_finished`). `container_started` và `ready` dùng thẳng cho `vllm_log.phases()`.
  4. Thêm `collect.PodWatcher`: luồng nền hỏi pod mỗi 5 s từ sau reset tới hết cooldown, ghi `pods_timeline.json`, thu log pod đang tắt ở mỗi lần hỏi. Bỏ `collect.write_logs`.
  5. `session.run_one` bọc warm-up, pha chính, cooldown trong `try/finally` để luồng nền luôn dừng và timeline luôn được ghi, kể cả khi lượt lỗi. `metadata.counts` thêm `pods_seen`, `pods_without_log`, `pod_poll_errors`.
  6. Môi trường §14.1, §14.2: thêm `pods_*.json`, `pods_timeline.json`, `logs/` vào cấu trúc thư mục lượt, bảng trường của `pods_timeline.json`; sửa mô tả `events.jsonl` (chỉ có event Kubernetes, không có pod conditions).
- **Decision:**
  - Hỏi định kỳ 5 s thay cho `kubectl get --watch`: watch phải tự nối lại khi đứt và tự ghép bản cập nhật, còn condition đã có sẵn `lastTransitionTime`. Chỉ thời điểm pod biến mất có sai số tới một chu kỳ.
  - Giữ mốc **đầu tiên** của mỗi loại, riêng `container_finished` lấy theo ảnh chụp mới nhất. Lý do: API chỉ giữ lần đổi gần nhất của condition, mà pod đang tắt chuyển `Ready=False`.
  - Log pod đang tắt được tải lại trọn ở mỗi lần hỏi, ghi đè qua file tạm, nên giữ được cả log drain. Không chọn tải tăng dần (`--since-time`) hay `kubectl logs -f`: log vLLM một lượt ước khoảng 1 MB mỗi pod (chưa đo), tải lại dưới 1 s, nên không đáng thêm độ phức tạp.
  - Thiếu log không làm lượt invalid (Môi trường §17 không có tiêu chí này); chỉ ghi vào `metadata.counts` và in cảnh báo. Pod chưa từng chạy container (Pending vì hết GPU) không bị tính là thiếu log.
  - `delete_requested` = `deletionTimestamp` − `deletionGracePeriodSeconds`, vì API đặt `deletionTimestamp` là hạn chót trước SIGKILL.
  - Nhánh tạo từ `feat/tr5-parse-vllm-log` (PR #24) vì cả hai cùng sửa `collect.py`; CI #24 chưa chạy lại được (xem Incidents).
- **Results:**
  - Lỗi tìm ra khi đọc code: `write_logs` chạy sau cooldown cho các pod có tên trong `pods_end`. Lúc đó pod do scale-up tạo ra đã bị scale-down và xoá, nên mọi lượt autoscaling đều mất log khởi động của pod mới, tức đúng số liệu ĐG3 cần.
  - Đọc JSON pod thật trên kind: sau khi container restart (WSL khởi động lại), `Ready` và `PodReadyToStartContainers` mang mốc của lần đổi mới nhất (09:43:01), còn `PodScheduled`, `Initialized` giữ mốc tạo pod (14:29:47 hôm trước).
  - Lượt `A2-CONST2-1` trên kind (phiên `podwatch-a2`, 2 req/s × 180 s, threshold 10, max 3): hợp lệ. Watcher hỏi 117 lần trong 09:57:26–10:06:53 UTC, 0 lỗi; `pods_timeline.json` 6,7 KB.
    - 3 pod: 1 pod có sẵn và 2 pod do scale-up tạo ra lúc 09:58:25 và 09:58:30. Cả 3 đều có log (`pods_without_log` rỗng).
    - Pod `4vwft`: `delete_requested` 10:05:52, thấy lần cuối 10:06:10, biến mất trước 10:06:15; log thu lúc đang tắt (`source: terminating`). Với code cũ, log này đã mất.
    - Pod `46tg2`: lệnh xoá lúc 10:06:49, cooldown xong lúc 10:06:53 vì Deployment đã còn 1 replica sẵn sàng. Pod này vẫn đang tắt khi lượt dừng, nên log chỉ tới lúc dừng (`gone_at` rỗng). Đã ghi giới hạn này ở Môi trường §14.2 và docstring.
    - `delete_requested` trùng tới giây với event `Killing` của cả hai pod (10:05:52, 10:06:49). Dùng thẳng `deletionTimestamp` thì lệch 60 s (grace của overlay sim).
    - Simulator: `container_started` → `ready` = 5 s (bằng chu kỳ readiness probe); `created` = `scheduled` (không xin GPU).
    - `parse_vllm_log` + `phases()` chạy trên 3 log thu được với mốc từ `marks`: không lỗi, nhận đúng mốc kubelet (`time_source: kubelet`), `complete = false` vì log simulator không phải log vLLM. Chưa có log vLLM thật.
  - Chạy lại sau khi sửa theo soát (phiên `podwatch-a2-final`, cùng cấu hình): hợp lệ; 119 lần hỏi, 0 lỗi; 3 pod, cả 3 có log. Hai pod do scale-up tạo ra đều có log thu lúc đang tắt; pod `npvzg` có lệnh xoá lúc 10:22:56 và biến mất trước 10:23:18; pod `99l4q` vẫn đang tắt khi lượt dừng, như lượt đầu.
  - `uv run --project experiments pytest experiments`: 122 đạt, 1 bỏ qua (Python 3.15 và 3.11); 6 test mới ở `test_pod_watcher.py`. `ruff check`, `ruff format --check`, lychee đạt.
- **Incidents:**
  - Lần chạy kind đầu tiên thất bại: API server từ chối kết nối suốt 3 phút. Nguyên nhân: WSL tắt distro khi không còn tiến trình nào (systemd tắt Docker) nhưng giữ VM. Lệnh `wsl.exe` sau làm distro khởi động lại, Docker khởi động lại các node kind, và systemd báo `unable to start unit docker-<id>.scope … got failed` cho control-plane và một worker (cgroup cũ của VM còn đó). Cách sửa: giữ distro sống bằng một `wsl.exe … sleep 7200` chạy nền, `docker start` lại các node, rồi chạy lại lượt.
  - GitHub Releases trả 504 suốt phiên (thử lúc 09:28 và 09:52 UTC, cả từ máy này), API vẫn 200, githubstatus không báo sự cố. CI #24 vẫn đỏ ở 3 job tải công cụ, chưa chạy lại.
- **Review:** `/code-review high` trên diff báo 10 điểm. Sửa 8 điểm:
  - `fetch_log` bắt thêm `UnicodeError`/`OSError`; `poll()` và `stop()` không raise, để `pods_timeline.json` luôn được ghi;
  - đếm lỗi dưới lock;
  - `container_finished` theo ảnh chụp mới nhất;
  - thêm `restarts_at_first_seen`, và ghi rõ không dùng pod có restart để tính pha;
  - kiểm luồng nền đã dừng sau `join`;
  - không báo thiếu log cho pod chưa từng chạy container;
  - `pods_*.json` ghi bằng `write_json`;
  - thêm mục "Khái niệm" vào docstring test.

  Không sửa 2 điểm, kèm lý do:
  - tải log tăng dần thay cho tải lại trọn: xem Decision;
  - `stop()` chờ lâu khi Ctrl-C lúc API treo: ca hiếm, và runner chạy bằng systemd thì SIGTERM không chạy `finally`.
- **Deviations:** Môi trường §14.2 (giao diện dữ liệu, Kế hoạch §6) có thêm file `pods_timeline.json` và các trường mới trong `pods_*.json`.
- **Links:** nhánh `feat/tr5-pod-timeline` (xếp chồng trên PR #24). File chính: `experiments/runner/collect.py`, `session.py`, `experiments/tests/test_pod_watcher.py`, `docs/chi-tiet/05-moi-truong-danh-gia.md`.
- **Thesis:** §4.11 (công cụ đánh giá: vì sao phải thu dữ liệu pod trong lúc lượt chạy, mốc đầu tiên so với lần đổi gần nhất); §5 cold start (pha 1, 2, 4, 8 từ `marks`); §5 GPU-giờ (khoảng giữ GPU từ `scheduled` tới lúc pod biến mất). Hình nên có: dòng thời gian 3 pod của lượt A2 (tạo → Ready → lệnh xoá → biến mất), vẽ từ `pods_timeline.json`.
