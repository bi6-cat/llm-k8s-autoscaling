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
  - T3 trượt (292 s, lần 3) → đồng hồ của VM WSL2 chạy nhanh 1,6 % so với giờ thật. HPA giữ đúng 300 s theo đồng hồ của nó, tức khoảng 295 s giờ thật; script đo bằng `date` (giờ thật) nên thấy 292–304 s tuỳ độ rung của scrape và sync → script đo mọi khoảng bằng đồng hồ đơn điệu (`/proc/uptime`). Lúc đầu tôi tưởng ngược lại (đồng hồ thực bị kéo lùi, làm số đo hụt); phép đo 64 s cho thấy chính đồng hồ của VM chạy nhanh, còn đồng hồ thực chỉ bị kéo về theo Windows.
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
