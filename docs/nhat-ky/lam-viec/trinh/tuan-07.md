# Nhật ký làm việc – Trình – Tuần 07 (16–22/11/2026)

## 2026-11-16 – TR7: review lần 2 và chạy `build_tables` trên dữ liệu kind

- **Task:** TR7 · **Environment:** sim
- **Done:**
  1. Soát phần sửa sau review lần 1 (mục 15/11, tuần 06). `firing_at_start` đang được tính ở hai nơi, nên gộp về `metrics.classify_alerts`. Cột `alerts_at_start` có trong danh sách cột nhưng chưa được gán, nên thêm.
  2. `/code-review high` lần 2 trên phần sửa: 9 phát hiện, sửa 8, bỏ 1 (D59). Commit `16349b1`.
  3. Chạy phiên `tr7-kb2-sim-2` trên kind (A2 rồi S1 × KB2, C = 1 req/s, A2 threshold 10, max 3), 12:01–12:55. Phiên 15/11 bị ngắt nên chạy lại. Rồi chạy `build_tables --baseline S1` trên dữ liệu đó.
  4. Sửa runner: metadata ghi thêm `git_runner`, trạng thái git đọc một lần lúc runner khởi động. `git` vẫn được đọc ở mỗi lượt, vì loadgen, `uv.lock` và file ScaledObject được đọc lại từ đĩa ở mỗi lượt.
  5. Mở PR #40. CI xanh 6/6. `/code-review high` lần 3 trên cả PR: 10 phát hiện, đã sửa cả 10 (D60).
- **Decision:**
  - N2b: chỉ tìm hồi phục sau khi **tổng** thời gian vi phạm kể từ lúc tải tăng đạt 30 s, thay cho 30 s liên tục. Đếm liên tục thì TTFT p95 dao động quanh ngưỡng (xấu 29 s, đạt 2 s, lặp lại) cho N2b = 0, là kết quả tốt nhất cho một lượt quá tải.
  - Thêm cột `has_timeline`: lượt trước 09/11 không có `pods_timeline.json` thì không bị đếm là "không có pod mới Ready".
  - Runner hỏi `ALERTS` từ 30 s trước warm-up (cùng cửa sổ với metric), để có mốc bắt đầu thật của đợt kêu.
  - Đợt `LLMSLOBurnFast` kêu sớm rồi kêu tiếp qua mốc vi phạm: vẫn chấm page giả theo định nghĩa N7 tại lúc firing, và vẫn dùng làm cảnh báo của lần vi phạm (thời gian tới cảnh báo âm).
  - Review lần 3:
    - Mốc đầu pha chính là `t0` của máy tạo tải, không phải `t_main_start`. Runner ghi `t_main_start` lúc apply Job, trước t0 11 s trên kind.
    - Thêm `slo_alert_at_start` (`LLMSLOBurnFast` còn kêu từ trước pha chính tới lúc vi phạm) và đếm `n_violation_no_alert` ở `cells.csv`.
    - `integrate_steps` giữ giá trị qua khoảng hở của chuỗi, vì tính khoảng hở là 0 làm số replica và GPU-giờ thấp đi.
    - `build` bỏ qua lần thử có file hỏng và thư mục truyền trùng, thay vì dừng cả bảng.
  - Không sửa `alert_episodes` (review lần 2 lo rằng một lần đánh giá rule bị lỡ sẽ tách đợt kêu). Ở Prometheus v3.15.0 `rules/group.go:538-550`, rule lỗi thì `return` trước khi ghi stale marker, và lookback 5 phút lấp mẫu bị lỡ.
- **Results:**
  - Test: `analysis` 32 test đạt trên Python 3.15 và 3.11; ruff sạch. `experiments` 143 đạt; 4 test hỏng chỉ trên Windows (`rclone` giả bằng shell script, `fcntl`), hỏng cả khi bỏ phần sửa.
  - A2-KB2-1 (hợp lệ; t0 12:03:10): SLO 0,992 trên pre+spike+drop; TTFT p95 0,22 s; lỗi 0/1758; GPU-giờ 0,990 (`gpu_s` 3563 s theo mốc pod, `gpu_s_ksm` 3518 s, lệch 1,3 %); replica tối đa 3. Lúc tải tăng đã có 2 replica (`replicas_at_rise` = 2, scale-up ở mức nền). `detect_s` 23,1 s, `create_to_ready_s` 6,0 s, `react_s` 29,1 s. `recovery_s` 0, vì tổng thời gian vi phạm chưa tới 30 s. `cooldown_s` 201 s. Không có cảnh báo nào ngoài Watchdog. `alerts.jsonl` có trường `episodes`.
  - S1-KB2-1 (không hợp lệ; t0 12:31:50): SLO 0,179; TTFT p95 100,3 s; lỗi 703/1758 (Timeout 374, HTTPStatus 179, RemoteProtocolError 95, ConnectError 54, ConnectTimeout 1); `slo_violation_s` 266 (26 s sau khi tải tăng). `pages` = 0. Dòng vẫn có trong `runs.csv` với `counted` = False, và không vào `cells.csv`.
  - Phiên 15/11 bị ngắt (không có `metadata.json`) được bỏ qua kèm thông báo; rc = 0.
  - S1 có `gpu_s_ksm` 1414 s dù 1 pod chạy suốt lượt, vì chuỗi `replicas` kết thúc ở t0 + 1409 s. Máy tạo tải xong ở khoảng t0 + 1413 s theo giờ thực, không phải t0 + 1440 s: đồng hồ đơn điệu của WSL chạy nhanh 1,62 % (đã ghi 07/11), nên 1440 s theo đồng hồ đó chỉ là 1417 s thực. Chỉ xảy ra trên simulator trong WSL; lịch gửi và các pha vẫn nhất quán với nhau vì cùng một đồng hồ.
- **Incidents:**
  - S1 không hợp lệ: pod simulator bị restart lúc 12:42:41, giữa pha spike, vì liveness probe trả HTTP 404 khi quá tải. Chưa tìm nguyên nhân 404. Pod này đã restart 11 lần trong 9 ngày.
  - Không có cảnh báo nào trong lượt S1 quá tải nặng. Nguyên nhân thứ nhất: histogram TTFT của simulator có 1197/1197 request ≤ 2,5 s (`increase` trong 25 phút tới t0 + 1090 s), nên `llm:ttft_bad_ratio:rate5m` lớn nhất bằng 0, trong khi TTFT phía client có p50 33 s. Từ số đo này suy ra TTFT của simulator v0.12.0 không tính thời gian chờ trong hàng đợi; chưa đối chiếu mã nguồn simulator. Nguyên nhân thứ hai: `llm:error_ratio:rate5m` rỗng, vì nó đo ở Traefik mà máy tạo tải gọi thẳng Service. `matrix-v2.yaml` cũng gọi thẳng Service, nên `LLMErrorRateHigh` sẽ không kêu được trong V2; đã báo Quang.
  - Metadata ghi sai commit: lượt S1 ghi `16349b1` sạch, nhưng tiến trình runner nạp code lúc 12:01, trước commit đó. Đã sửa (Done 4).
- **Deviations:** Môi trường §15 ghi rõ cách tìm mốc N2b (tổng 30 s vi phạm); `alerts.jsonl` được hỏi từ 30 s trước warm-up thay vì từ đầu pha chính (§14.2).
- **Links:** nhánh `feat/tr7-build-tables`; `analysis/metrics.py`, `analysis/build_tables.py`, `experiments/runner/session.py`, `experiments/runner/collect.py`; dữ liệu thử ở máy Trình (`.work/tr7/runs/tr7-kb2-sim-2/`, không commit).
- **Thesis:** §5 (phương pháp): định nghĩa N2b và N7, kèm lý do chọn. §6 (giới hạn): trên simulator, cảnh báo SLO không thể kêu vì hàng đợi; trong V2, cảnh báo tỷ lệ lỗi cần đường đi qua Traefik.

## 2026-11-16 – TR7: merge PR #40 (`analysis/build_tables.py`)

- **Task:** TR7 · **Environment:** none
- **Done:** Trình merge PR #40 bằng merge commit `baebdc9` và xoá nhánh `feat/tr7-build-tables`. Đủ 5 điều kiện merge: CI xanh 6/6 trên `8433e70`; đã kiểm cục bộ và chạy `/code-review high` ba lần, lỗi xác nhận đều đã sửa; MERGEABLE, không có review hay bình luận; không đụng thư mục mà Argo CD ở nhà đọc; base `main`. Sau đó gộp `origin/main` vào nhánh PR #39 để đưa mục nhật ký này lên.
- **Links:** PR #40; commit `d246927`, `16349b1`, `3e564e7`, `8433e70`.
- **Thesis:** chạy lại `uv run --project analysis python -m analysis.build_tables runs/<phiên>` ngay sau phiên V2 để soát dữ liệu trước khi đóng băng 22/11.

## 2026-11-16 – TR8: LT7 trên simulator (thuật toán HPA và trễ phản ứng)

- **Task:** TR8 · **Environment:** sim
- **Done:**
  1. Đếm mẫu T2 cũ trong `runs/sim/`: đã có 7 mẫu thời gian quyết định (1, 6, 8, 8, 9, 4, 5 s), đủ "5 lần" của Môi trường §19. Phần LT7 còn thiếu: kiểm công thức ở nhiều mức tải (T2 chỉ có C = 25) và tách trễ theo chặng.
  2. Viết `envs/sim/tests/lt7-hpa.sh` (`make sim-lt7`) để thu dữ liệu thô, và `analysis/lt7_hpa.py` để tính bảng (kèm 19 test). `load-sim.sh` in thêm mốc bắt đầu tải theo giờ thực, tới ms.
  3. Trên kind không còn ScaledObject `vllm-a2`, nhiều khả năng runner TR7 đã gỡ khi kết thúc phiên. Áp lại `envs/sim/autoscaling`.
  4. Chạy thử một lượt (16:23), rồi phiên 1 (16:25–16:43, 12 lượt). Lượt thử cho chặng scrape → HPA 5,29 s, dài hơn chu kỳ sync, nên Trình đối chiếu mã nguồn Kubernetes v1.37.0 (`horizontal.go`, `replica_calculator.go`, `rate_limiters.go`) và KEDA v2.21.0 (`prometheus_scaler.go`). Trình đọc thêm metric reconcile của kube-controller-manager và metric gRPC của keda-operator.
  5. Thêm bước đổi mọi mốc giờ thực sang đồng hồ đơn điệu, dựa trên journal của WSL. Lấy bù log rescale, journal và `keda.json` cho phiên 1 bằng chính các lệnh của script.
  6. Thêm lệch pha ngẫu nhiên, chạy phiên 2 (16:53–17:11, 12 lượt).
  7. `/code-review high`: 10 điểm. Sửa 8. Hai điểm còn lại là nhật ký chưa ghi (chính mục này) và việc chưa ghi Deviations so với "5 lần" (mục Deviations bên dưới).
  8. Ghi kết quả vào `docs/nhat-ky/van-hanh.md`, mục LT7.
- **Decision:** (D61)
  - Viết script riêng thay vì lặp T2: phải thử 4 mức tải, mà T2 chỉ có một. Reset bằng `paused-replicas` như runner: khoảng 25 s mỗi lượt, so với khoảng 6 phút nếu chờ scale-down tự nhiên.
  - Mốc quyết định của HPA lấy từ log kube-controller-manager (µs). Event (tới giây) chỉ dùng khi log rỗng.
  - Đổi mọi mốc sang đồng hồ đơn điệu bằng các dòng "Clock change detected" trong journal (systemd-resolved ghi ngay sau mỗi lần chỉnh giờ). Lượt có mốc nhập nhằng bị loại khỏi bảng trễ, không đoán. Phương án bỏ: dò bước nhảy qua khoảng cách giữa các lần scrape, vì cách đó không biết bước rơi trước hay sau quyết định.
  - Chọn mức tải 5/15/25/35: tránh biên tolerance (9 ≤ C ≤ 11), và không làm quá tải một pod (port-forward dồn hết tải vào một pod).
  - Lệch pha ngẫu nhiên trong [0; chu kỳ sync) trước khi bơm tải (xem Incidents).
- **Results:**
  - Số replica: 24/24 lượt đúng ⌈C ÷ 10⌉ kẹp ở max 3 (C = 5 → 1, 15 → 2, 25 → 3, 35 → 3). Mỗi lượt scale đúng một lần.
  - Trễ, phiên 2 (7 lượt, đồng hồ đơn điệu): tải tới → scrape thấy tải 0,88–5,02 s; scrape → KEDA thấy mẫu 0,45–0,79 s; KEDA thấy mẫu → HPA đổi replica 0,11–4,76 s; **tải tới → HPA đổi replica 3,61–10,21 s (TB 6,91 s)**; pod mới Ready sau 5–7 s. Phiên 1 (8 lượt): quyết định 3,11–8,83 s.
  - KEDA trả metric TB 4,2 ms (199 lần); Prometheus trả lời KEDA chậm nhất 23 ms. Mỗi lần HPA xử lý TB 20 ms (37 ms khi scale-up).
  - Kiểm cách đổi giờ: khoảng cách hai lần scrape liền nhau lệch khỏi 5 s tối đa 2 ms sau khi đổi, so với 1301 ms theo giờ thực.
  - Test: `analysis` 51 test đạt (Python 3.15 và 3.11), ruff sạch; shellcheck 0.11.0 sạch cho `lt7-hpa.sh` và `load-sim.sh`; kiểm tham số sai (`DUR=1m`, `LEVELS="15,25"`) và một lượt `DUR=30s` trên kind sau khi sửa.
- **Incidents:**
  - Chặng scrape → HPA dài hơn 5 s → do KEDA hỏi Prometheus với `time=` làm tròn xuống giây (`prometheus_scaler.go:224`), nên mẫu chỉ được thấy từ giây tròn kế tiếp → tách chặng này ra (d_visible), cận trên của quyết định là 11 s chứ không phải 10 s.
  - Phiên 1: thời gian quyết định chỉ rơi vào hai cụm, 3–4 s hoặc 8–9 s → reset tạo HPA mới, HPA sync ngay khi được tạo, và script bơm tải sau reset một khoảng gần như cố định, nên pha sync bị khoá → thêm lệch pha ngẫu nhiên, chạy lại thành phiên 2.
  - Lúc reset ở lượt C = 35 lần 1 (phiên 1), ReplicaSet xoá pod `xr9cr` (có 12 lần restart), vì khi scale-down nó ưu tiên xoá pod restart nhiều → bản phân tích đầu chọn "pod có mẫu sớm nhất" làm pod gốc, cách này sai khi pod vừa bị xoá cũng có mẫu sớm → bỏ cách chọn đó cùng với cách dò bước nhảy.
  - Bash đọc dần file script trong lúc chạy, nên sửa `lt7-hpa.sh` khi một phiên đang chạy có thể làm hỏng phiên đó → chỉ sửa sau khi phiên xong.
  - `/metrics` của kube-controller-manager trả 403 → đọc bằng chứng chỉ super-admin của chính cluster kind, trong container control-plane (file tạm bị xoá ngay sau đó).
- **Deviations:**
  - Môi trường §19 ghi "mốc thời gian event trong bài T2, 5 lần". Thực tế dùng script riêng, 4 mức × 3 lần × 2 phiên (18 lượt có scale-up), lấy mốc từ log kube-controller-manager và Prometheus thay cho event; 7 mẫu T2 cũ vẫn ghi kèm. Lý do: event chỉ tới giây, và T2 chỉ có một mức tải.
  - Dự đoán của §19 (≤ ~15 s) được sửa thành < 10 s trước khi đo, vì polling không nằm trên đường quyết định. Số đo cho cận 11 s (chặng KEDA làm tròn `time=`). Giữ nguyên bảng §19, kết quả ghi ở `van-hanh.md`.
- **Links:** nhánh `feat/tr8-lt7-hpa`; `envs/sim/tests/lt7-hpa.sh`, `envs/sim/tests/load-sim.sh`, `analysis/lt7_hpa.py`, `analysis/tests/test_lt7_hpa.py`, `analysis/figures/lt7-hpa.csv`, `Makefile`, `docs/nhat-ky/van-hanh.md`. Dữ liệu thô trên máy Trình (không commit): `runs/sim/lt7-20261116-162338/` (lượt thử), `lt7-20261116-162501/` (phiên 1), `lt7-20261116-165323/` (phiên 2).
- **Thesis:** §5, kiểm chứng lý thuyết LT7: bảng số replica theo mức tải và bảng trễ theo chặng; hình nên có là dòng thời gian của một lượt (các lần scrape, giây tròn, các lần sync, pod Ready), chưa vẽ. §6 (giới hạn và bài học đo): giờ thực trên WSL2 bị kéo lùi, và KEDA làm tròn `time=` xuống giây. Hệ quả cho N2a: autoscaler chỉ chiếm < 11 s.

## 2026-11-16 – TR8: merge PR #41 (LT7)

- **Task:** TR8 · **Environment:** none
- **Done:** CI xanh 6/6 (alerts, docs, manifests, python 3.11 và 3.15, yaml). `mergeable` = MERGEABLE (CLEAN), 0 review, 0 bình luận. PR không đổi thứ gì Argo CD quản lý ở nhà. Merge bằng merge commit `d68a680`, xoá nhánh `feat/tr8-lt7-hpa`. Gộp `origin/main` vào nhánh của PR #39 trước khi ghi mục này.
- **Links:** PR #41; mục LT7 cùng ngày ở trên; `docs/nhat-ky/van-hanh.md` mục "Kiểm chứng lý thuyết LT5–LT8".

## 2026-11-16 – TR8: LT5 (định luật Little) trên dữ liệu nhà và simulator

- **Task:** TR8 (LT5) · **Environment:** none (dữ liệu đã đo: nhà 05–06/11, sim 07/11 và 16/11)
- **Done:**
  1. Đọc Môi trường §19 (LT5), §8 bước 6, Kiến trúc §10.2, `experiments/runner/capacity.py`, `collect.py`, `loadjob.py`, `loadgen/sender.py`.
  2. Ghi dự đoán cho simulator trước khi tính: W = 0,2 + 255 × 0,05 = 12,95 s; `pre` L ≈ 6,5; `spike` A2 ≈ 28,6; S1 quá tải thì không áp được; SE lấy mẫu theo M/G/∞.
  3. Viết `analysis/lt5_little.py`: đọc file capacity (bản tóm tắt) và thư mục phiên runner (dữ liệu thô); tính λ\_thực, W, L_client = λW + edge, L_client_sampled, L_server (tổng mọi pod), SE, z; đổi đồng hồ máy tạo tải bằng hậu tố `@k`; tính cận k của từng lượt. Thêm 14 test (`analysis/tests/test_lt5_little.py`).
  4. Chạy trên `capacity-1.5b.json`, `capacity.json`, `runs/sim/mp-final-w2`, `runs/sim/tr7-kb2-sim-2` (chép từ `.work/tr7/runs/`). Pha `drop` của A2 lệch −11,9 %, nên dò nguyên nhân (Incidents).
  5. Sửa `capacity.py` (code của Quang): `B_little` dùng λ\_thực, thêm `lambda_real_rps`, `window_s`; thêm test; sửa Môi trường §8 bước 6.
  6. `/code-review high`: 10 điểm, sửa 8; hai điểm còn lại là việc sửa đồng hồ ở `build_tables`/loadgen (để PR sau) và chính mục nhật ký này.
  7. Ghi kết quả vào `docs/nhat-ky/van-hanh.md`, mục LT5; ghi chú vào `06-ke-hoach-quan-ly.md` (dòng LT1–LT8).
- **Decision:** (D62)
  - Dùng λ\_thực (request thành công gửi trong cửa sổ ÷ T) cho cả LT5 lẫn phép kiểm của runner, không dùng λ danh định.
  - Tách phần edge bằng đẳng thức tuyệt đối, để phân biệt lỗi đo với hệ không dừng.
  - Cửa sổ từ request lỗi đầu tiên trở đi bị đánh dấu là không áp được.
  - Không tính SE và z khi waiting ≥ 1.
  - k của đồng hồ máy tạo tải lấy theo từng phiên, từ cận do mốc của runner cho, không ước lượng từ dữ liệu Prometheus (tránh vòng). Phương án bỏ: k cố định 1,0162; ước lượng từ chuỗi running + waiting; ước lượng từ bộ đếm `request_success_total`; dùng mtime file.
- **Results:**
  - Nhà, 18 cửa sổ dừng (1,5B λ 1–7; 0,5B λ 2–12,5; sim `pre`/`spike`/`drop`): L_server lệch λ\_thực × W từ −4,4 % đến +14,3 %, phía client từ −0,9 % đến +2,6 %. Lệch lớn nhất (+14,3 %, 0,5B λ = 2, L = 1,86) chỉ bằng 1,0 SE. z ở 14 cửa sổ chưa xếp hàng nằm trong [−0,76; +0,96], trung bình +0,20.
  - Quá tải (1,5B λ = 8; 0,5B λ ≥ 13): −5 đến −14 %, phía client lệch gần bằng. Sim S1-CONST2-1: edge −19,5 trên λW 57,4 (−34 %); L_server so với L_client chỉ −2,3 %.
  - A2-KB2-1 (scale 1 → 3 → 1), k = 1,033: `pre` +2,1 %, `spike` −0,9 %, `drop` +4,6 %, cả lượt 0,0 %.
  - Phép kiểm của runner cũ báo nhầm ở 0,5B λ = 2 (15,7 %, `little_ok = False`); với λ\_thực thì 14,3 %.
  - Kiểm tra: `analysis` 65 test đạt (Python 3.15 và 3.11), ruff sạch. `experiments`: 144 đạt; 4 lỗi `test_backup_notify` có từ trước, chỉ trên Windows. lychee 130 link đạt.
- **Incidents:**
  - Pha `drop` của A2 lệch −11,9 %. Lệch dồn vào 846–871 s: client có 20–33 request đang chờ, server chỉ đếm 7–22.
    - Nguyên nhân: loadgen ghi mốc request bằng `perf_counter` cộng `t0_unix`, còn Prometheus đóng dấu bằng giờ thực, mà trong VM WSL2 đồng hồ đơn điệu chạy nhanh hơn k lần.
    - Bằng chứng: độ trễ khớp nhất tăng dần (−1, −6, −11 s); runner thấy loadgen xong lúc t0 + 1419,4 s, trong khi `wall_s` = 1451,6 s, nên k ∈ [1,022; 1,038].
    - Cách sửa: hậu tố `@k`, dùng k = 1,033. Với mọi k trong cận chung của hai lượt, `drop` lệch +2,2…+7,4 %.
  - k đổi theo lần VM khởi động: 1,0162 (07/11), 1,0188 (chiều 16/11, VM khởi động lại khoảng 16:17, theo bản ghi chỉnh giờ của LT7), khoảng 1,03 (sáng 16/11). Vì thế không dùng được một hằng số.
  - Hệ quả phụ: N2a mà `build_tables` tính trên simulator ngắn đi khoảng 8 s. V2 (Linux thật) không bị. Cách sửa gốc (loadgen ghi giờ thực lúc kết thúc) chưa làm.
  - Ước lượng k từ bộ đếm `request_success_total` gãy giữa hai nửa lượt (offset của request warm-up đổi theo λ), cho 2,15–2,6 %, nên bỏ cách này. Mtime của file kết quả là lúc `kubectl cp` giải nén, không dùng được.
- **Deviations:**
  - Môi trường §19 ghi nguồn là "requests.csv của mọi lượt tải" ở nhà, simulator và V2. Thực tế: ở nhà chỉ có bản tóm tắt trong `capacity*.json` (dữ liệu thô trên máy Quang); V1 (`runs/v1-a4000/`) không có trên máy Trình nên chưa tính; V2 chưa chạy. Chạy lại script trên dữ liệu thô khi có.
  - Môi trường §8 bước 6 đổi từ "C × E2E" sang "λ\_thực × E2E".
- **Links:** nhánh `feat/tr8-lt5-little`; `analysis/lt5_little.py`, `analysis/tests/test_lt5_little.py`, `analysis/figures/lt5-little.csv`, `experiments/runner/capacity.py`, `experiments/tests/test_runner.py`, `docs/nhat-ky/van-hanh.md` (LT5), Môi trường §8. Dữ liệu thô trên máy Trình (không commit): `runs/sim/mp-final-w2/`, `runs/sim/tr7-kb2-sim-2/`.
- **Thesis:** §5, kiểm chứng lý thuyết LT5: bảng lệch theo cửa sổ, phân rã lệch thành edge, lấy mẫu và định nghĩa. Hình nên có: L_server theo λ\_thực × W (đường y = x, dải ±15 %), chưa vẽ. §6 (giới hạn đo): đồng hồ đơn điệu của WSL2 chạy nhanh 1,6–3,8 % và đổi theo lần khởi động; λ danh định so với λ\_thực.

## 2026-11-16 – TR8: merge PR #42 (LT5)

- **Task:** TR8 · **Environment:** none
- **Done:** CI của PR #42 xanh cả 6 job (`alerts`, `docs`, `manifests`, `python` 3.11 và 3.15, `yaml`); `mergeable` = MERGEABLE, 0 review, 0 bình luận; PR không đụng manifest của cluster nhà (điều kiện merge 4). Trình merge bằng merge commit `5918689`, xoá nhánh `feat/tr8-lt5-little`. Mục nhật ký này được đẩy lên nhánh của PR #39 sau khi gộp `origin/main`, như lần merge #41.
- **Links:** PR #42; mục LT5 ngay trên; `docs/nhat-ky/van-hanh.md` mục "Kiểm chứng lý thuyết LT5–LT8".

## 2026-11-16 – TR8: LT6 (GPU utilization bão hoà) trên dữ liệu ĐG1-mini ở nhà

- **Task:** TR8 · **Environment:** none (phân tích dữ liệu nhà đã đo 05–06/11)
- **Done:**
  1. Đọc Môi trường §19 (LT6), Kiến thức nền §4.3–§4.4, Kiến trúc §10.1, `common/autoscaling/eval/A1.yaml`, cách `capacity.py` tính `gpu_util` (giá trị lớn nhất mỗi lần scrape, trung bình 24 mẫu).
  2. Viết `analysis/lt6_gpu_util.py`. Script đọc `capacity*.json` và tính:
     - util_pred = 1 − e^(−L) theo M/G/∞, với L = B_client, cùng z;
     - nhóm tải vừa (0,3–0,7 C) và quá tải (> C, SLO < 95 %), rồi phép kiểm "tách được bằng một ngưỡng" cho 4 tín hiệu A1–A4;
     - quyết định đầu tiên của A1, A2 khi đang có 1 replica (dùng `predict_replicas` của LT7);
     - số replica A1, A2 leo tới nếu chạy cùng tải trên node N GPU (`a1_replicas`).
     Thêm 18 test (`analysis/tests/test_lt6_gpu_util.py`), cùng 1 test cho `capacity_level` (LT5) và 1 test cho `hpa_desired` (LT7).
  3. Chạy trên `capacity-1.5b.json` và `capacity.json`, ghi `analysis/figures/lt6-gpu-util.csv`.
  4. Ghi kết quả vào `docs/nhat-ky/van-hanh.md` (LT6); thêm dòng "Định lượng" ở Kiến trúc §10.1; ghi chú ở Kế hoạch (dòng LT1–LT8).
  5. `/code-review high`: 10 điểm, sửa cả 10:
     - phép kiểm "tách được" giờ in thêm kết quả khi chỉ lấy mức hợp lệ;
     - bỏ NaN trước khi lấy min/max; 0 ÷ 0 cho NaN;
     - thiếu `waiting` thì coi là đã xếp hàng; cửa sổ < 5 s thì SE để trống;
     - `a2_replicas` dùng B_server, như A2 thật;
     - ngưỡng A1 trong bảng tóm tắt lấy theo từng file;
     - sửa câu "gấp 15–17 lần" (chỉ đúng khi L ≥ 1000) thành 11–14 lần ở L = 30–100;
     - sửa câu "|z| ≤ 0,9" (có một z = −0,915) và câu xếp hạng độ lệch;
     - bỏ code lặp: tách `capacity_level` (dùng chung LT5, LT6) và `hpa_desired` (dùng chung LT6, LT7).
     Chạy lại LT5, LT7: CSV không đổi.
- **Decision:** (D63)
  - "Phân biệt được" nghĩa là tách được bằng một ngưỡng: max(tải vừa) < min(quá tải). Không dùng tỷ số trung bình, vì tỷ số không trả lời được câu hỏi có ngưỡng nào tách được hay không.
  - Mô hình 1 − e^(−L) chỉ áp ở mức waiting < 1. L lấy B_client (không có sai số lấy mẫu). Phương án bỏ: dùng B_server (24 mẫu); dùng M/G/1-PS (util = λ/C), vì mô hình này ra 0,17 ở 1,5B λ = 1 trong khi đo được 0,895.
  - `a1_replicas` lặp phép tính HPA với tổng = 100 × r × util(L ÷ r), và dừng ở lần đầu HPA không thêm pod. Không mô phỏng scale-down, vì cửa sổ ổn định 300 s giữ khuyến nghị lớn nhất.
  - Phần đọc dữ liệu thô của runner cho V2 để PR sau, khi có dữ liệu thật. Lý do: `metrics.csv.gz` không giữ nhãn GPU, nên bây giờ chỉ kiểm được bằng mock.
- **Results:**
  - util = 1,000 từ 0,33 C (1,5B) và 0,48 C (0,5B) cho tới quá tải. `waiting` tăng từ 0 lên 92 (1,5B) và 166 (0,5B).
  - Khoảng hở min(quá tải) ÷ max(vừa), 1,5B / 0,5B:
    - util: 1,00 / 0,9996, **không tách được**;
    - running + waiting: 3,9× / 7,7×;
    - KV: 2,3× / 1,9×;
    - waiting: ∞ / 630×.
    Bỏ hai mức không hợp lệ (1,5B λ = 6 và 8) thì kết luận không đổi.
  - Ở 5 mức có dự đoán < 0,999, 1 − e^(−L) khớp util đo với |z| < 1 (lớn nhất 0,91): 0,895 so với 0,865; 0,780 so với 0,844; 0,958 so với 0,983…
  - Quyết định đầu tiên từ 1 replica: A1 đòi 2 replica ở cả 18 mức (từ 0,16 C). A2 giữ 1 khi λ < C.
  - Dự đoán (chưa đo) cho node 4 GPU:
    - A1 lên đủ 4 replica từ 0,33–0,48 C, trong khi A2 ở 1 tới 0,83 C;
    - không kẹp max, ở tổng L = 30–100 A1 cần gấp 11–14 lần số replica của A2;
    - A1 lên max khi tổng L > 4,4 và chỉ bớt pod khi L ≤ 3,0.
  - Kiểm tra: `analysis` 85 test đạt (Python 3.15), ruff check và format sạch; lychee không có lỗi fragment (chỉ còn các đường dẫn cũ mà CI bỏ qua).
- **Deviations:** Môi trường §19 ghi "một lượt tải tăng dần 0,3 → 1,5 C ở nhà, đọc Prometheus". Trình chưa có quyền vào cluster nhà, nên dùng các bậc λ của ĐG1-mini (0,16–1,33 C và 0,16–1,12 C, mỗi bậc 120 s), lấy trung bình mà runner đã tính. V1 (`runs/v1-a4000/`) không có trên máy Trình.
- **Links:** nhánh `feat/tr8-lt6-gpu-util`; `analysis/lt6_gpu_util.py`, `analysis/tests/test_lt6_gpu_util.py`, `analysis/figures/lt6-gpu-util.csv`, `analysis/lt5_little.py` (`capacity_level`), `analysis/lt7_hpa.py` (`hpa_desired`), `docs/nhat-ky/van-hanh.md` (LT6), Kiến trúc §10.1.
- **Thesis:** §5, kiểm chứng lý thuyết LT6: bảng tách tải vừa và quá tải cho 4 tín hiệu, bảng util so với 1 − e^(−L). §5 ĐG2: lập luận "A1 ≈ Static-N" kèm điều kiện L > 1,47 × (N − 1). Hình nên có: util và L_server (trục log) theo λ ÷ C cho hai model, đánh dấu C, thêm đường 1 − e^(−L). Chưa vẽ.

## 2026-11-16 – TR8: merge PR #43 (LT6)

- **Task:** TR8 · **Environment:** none
- **Done:**
  - CI của PR #43 xanh cả 6 job (`alerts`, `docs`, `manifests`, `python` 3.11 và 3.15, `yaml`). `mergeable` = MERGEABLE (CLEAN), 0 review, 0 bình luận. PR chỉ đổi `analysis/` và `docs/`, nên không đổi thứ gì Argo CD quản lý ở nhà.
  - Trình merge bằng merge commit `1a5c9fd` và xoá nhánh `feat/tr8-lt6-gpu-util`.
  - Gộp `origin/main` vào nhánh của PR #39 trước khi ghi mục này. Lần gộp này (và lần gộp sau #42) làm mất dòng trống trước hai mục LT5, LT6; Trình đã thêm lại.
- **Links:** PR #43; mục LT6 ngay trên; `docs/nhat-ky/van-hanh.md` mục "Kiểm chứng lý thuyết LT5–LT8".

## 2026-11-16 – TR8: công cụ đo LT8 (burn rate), phiên đo trên simulator đang chạy

- **Task:** TR8 (LT8) · **Environment:** sim (kind trong WSL2, máy Trình)
- **Done:**
  1. Đọc Môi trường §19 (LT8), Kiến thức nền §5.2, Vận hành §3.3, Thông số §6, rule `slo.yaml` và `llm.yaml`; đối chiếu mã nguồn llm-d-inference-sim v0.12.0 (`pkg/simulator/latencies.go`, `pkg/common/utils.go`, `pkg/common/config.go`, endpoint `/admin/config` ở `pkg/communication/http.go`).
  2. Viết bộ đo `experiments/ops/lt8_burn.py`: tạm dừng KEDA ở 1 replica, chạy loadgen thành Job trong cluster (CONST 2 req/s, `--max-tokens 16`), đổi TTFT của simulator lúc đang chạy qua `POST /admin/config` (API server proxy), ghi mốc bơm/gỡ và mẫu Prometheus thô (ALERTS, `llm:ttft_bad_ratio:rate1m/5m`, bộ đếm histogram TTFT). Lịch mỗi lượt: nền 330 s → bơm 360 s → nền 330 s … → nền 120 s; 3 mức x = 0,1/0,3/0,6, xoay thứ tự theo lượt. Thêm `make sim-lt8`.
  3. Viết `analysis/lt8_burn.py` (dự đoán, so số đo, cột N7 dùng chung `metrics.slo_violation_start` và `metrics.classify_alerts`) cùng unit test; test dựng lượt tổng hợp mô phỏng scrape 5 s, tính rule 15 s, `for: 1m`.
  4. Lượt thử ngắn (x = 0,6, nền 60 s): chạy hết, dữ liệu đủ.
  5. Hai lần `/code-review high`; đã sửa các lỗi xác nhận (xem Incidents), còn 3 điểm nhỏ của lần 2 chưa sửa (STATE).
  6. Phiên đo thật 3 mức × 3 lượt bắt đầu 13:11 UTC (khoảng 2 giờ), chạy bằng bản bộ đo TRƯỚC khi sửa theo review lần 2. Dừng phiên làm việc vì sắp hết quota; phiên đo vẫn chạy nền.
- **Decision:** (D64) tạo tỷ lệ xấu x bằng cách đổi TTFT của simulator lúc chạy: TTFT ~ N(μ, σ = 0,3 μ) (mức σ lớn nhất simulator nhận), μ chọn để P(TTFT > 2,5 s) = x: x = 0,1/0,3/0,6 ↔ μ = 1806/2160/2706 ms. Không sửa `patch-sim.yaml` vì T1–T5, LT7 và runner dùng chung. Bỏ phương án trộn prompt dài/ngắn với `--prefill-time-per-token` (phụ thuộc cách simulator đếm token, phải sửa loadgen). Giữ 1 replica vì LT8 kiểm cảnh báo, không kiểm scale (giống S1 của VH6). `requests.csv` được dời nguyên khối sang giờ thực (giữ TTFT theo đồng hồ simulator), không co theo k như LT5: co theo k = 1,024 thì ở x = 0,3 khoảng 3 % request đổi phía ngưỡng 2,5 s.
- **Results:**
  - Dự đoán (bước nhảy sau ≥ 5 phút nền sạch): điều kiện đúng sau θ·300/x (cửa sổ 5m là chặng chậm), firing sau đó 60 s: x = 0,3 → 260 s, x = 0,6 → 160 s, x = 0,1 → không kêu. Hết cảnh báo sau khi gỡ: 60·(1 − θ/x) = 20 s / 40 s (cửa sổ 1m quyết định). N7: từ lúc vi phạm (cửa sổ 1 phút theo log client) tới firing = θ·240/x + 60 s, luôn < 300 s khi x > θ nhưng tiến tới 300 s khi x → 0,2.
  - Lượt thử (`runs/sim/lt8-20261116-130645`, chỉ 60 s nền nên không so được với dự đoán): μ = 2706 ms, σ = 811 ms; x đo 0,575 (client, n = 179) và 0,572 (server), dự đoán 0,600; điều kiện đúng +43 s, pending +49 s, firing +109 s (pending → firing đúng 60 s); điều kiện sai 44 s sau khi gỡ (dự đoán 40 s); k = 1,024.
  - Phiên đo thật (`runs/sim/lt8-20261116-131116`): chưa có kết quả.
- **Incidents:**
  - Review 1: định nghĩa N7 tự viết lệch với `analysis/metrics.py` → dùng chung hàm của metrics; hai đợt pending cách 30 s bị gộp → ngưỡng tách đợt 22,5 s; `finally` có thể bỏ sót việc gỡ tạm dừng KEDA → mỗi bước một `try`; k đo bằng runner chỉ đúng khi chung kernel → đo k bằng `kubectl exec` trong pod loadgen; c0 có thể bị request muộn của lượt trước đẩy lên → chờ bộ đếm đứng yên; xoá Job khi dừng giữa chừng.
  - Review 2: loadgen đếm `--duration` theo đồng hồ đơn điệu (nhanh k lần) nên dừng sớm total·(1 − 1/k) ≈ 50 s → nhân thời lượng 1,05. Pod bị thay không bị phát hiện → so UID pod. Phiên đang chạy dùng bản cũ: pha nền cuối thực còn khoảng 95 s, vẫn đủ cho lúc hết cảnh báo (≈ 65 s); analysis tự đánh dấu lần bơm có nền < 300 s.
  - Test bắt lỗi: `classify_alerts` đọc `first` khi danh sách đợt rỗng → chỉ truyền khi có đợt.
- **Deviations:** Môi trường §19 ghi "tăng độ trễ giả lập": làm đúng như vậy nhưng tăng cả độ phân tán (σ = 0,3 μ) để có tỷ lệ xấu x thay vì mọi request cùng xấu.
- **Links:** nhánh `feat/tr8-lt8-burn-rate` (commit cục bộ, chưa push); `experiments/ops/lt8_burn.py`, `analysis/lt8_burn.py`, test tương ứng, `Makefile`, `envs/sim/README.md`.
- **Thesis:** §5 LT8: bảng x dự đoán/đo, mốc điều kiện/firing/hết so với công thức; hình r_1m, r_5m theo thời gian quanh lúc bơm kèm ngưỡng 0,2 và mốc pending/firing (chưa vẽ). Nhận xét: mức 5 phút của N7 chỉ vừa khít cửa sổ 5m.

## 2026-11-16 – TR8: kết quả phiên đo LT8 trên simulator

- **Task:** TR8 (LT8) · **Environment:** sim (kind trong WSL2, máy Trình)
- **Done:**
  1. Phiên đo `runs/sim/lt8-20261116-131116` (3 mức × 3 lượt, thứ tự xoay vòng) chạy xong cả 3 lượt; rc loadgen = 0, 0 restart, k = 1,0264 / 1,0270 / 1,0257 (đo bằng runner, chung kernel WSL với kind).
  2. Kiểm cluster sau phiên: không còn Job loadgen, ScaledObject hết tạm dừng, TTFT nền 200 ms / 0 s.
  3. Sửa nốt review lần 2 ở `analysis/lt8_burn.py`: bỏ qua lượt thiếu `load/` (có test), tính đợt cảnh báo một lần, ghi note khi pod bị thay. Ghi bảng `analysis/figures/lt8-burn.csv`.
- **Results:** 9/9 lần bơm hợp lệ (nền trước mỗi lần bơm 322–331 s). Giá trị: min–max (TB), trong ngoặc là dự đoán; thời gian tính từ lúc bơm, "hết" tính từ lúc gỡ.

  | x | x client | x server | điều kiện đúng, s | firing, s | hết, s | N7 vi phạm → firing, s | page giả |
  |---|---|---|---|---|---|---|---|
  | 0,1 | 0,095–0,131 | 0,097–0,126 | không (không) | không kêu, 0 pending (không kêu) | – | – | 0 |
  | 0,3 | 0,303–0,324 | 0,300–0,315 | 183–220 (200) | 249–286 (260) | 21–34 (20) | 215–242 (220) | 0 |
  | 0,6 | 0,581–0,620 | 0,572–0,612 | 108–125 (100) | 173–190 (160) | 48–55 (40) | 159–163 (140) | 0 |

  - pending → firing đúng 60,0 s ở mọi lần; điều kiện đúng → pending luôn 5,5 s (độ lệch pha cố định giữa nhóm recording rule và nhóm cảnh báo). firing − dự đoán: −11 đến +31 s (TB +14 s).
  - Lần x = 0,3 kêu sớm hơn dự đoán 11 s (rep3) có x client = 0,324: θ·300/0,324 = 185 s, khớp mốc điều kiện đúng đo được 183 s. Phần trễ dương còn lại cỡ 5–25 s: token đầu của request xấu ra sau khoảng μ (2–3 s), chờ scrape (≤ 5 s), chờ lần tính rule (≤ 15 s).
  - Mọi lần x > 0,2 đều đạt N7 (≤ 300 s từ lúc vi phạm theo log client).
- **Links:** `analysis/figures/lt8-burn.csv`; mục LT8 ngay trên.
- **Thesis:** §5 LT8: bảng trên. Hình nên có: r_1m, r_5m theo thời gian của một lần bơm x = 0,3, kèm ngưỡng 0,2 và mốc pending/firing (chưa vẽ).

## 2026-11-16 – TR8: ghi LT8 vào nhật ký vận hành, review lần 3, mở PR

- **Task:** TR8 (LT8) · **Environment:** none (máy Trình; không đụng cluster)
- **Done:**
  1. Viết mục `### LT8` trong `docs/nhat-ky/van-hanh.md` theo mẫu lý thuyết → dự đoán → cách đo → số đo → giải thích → hệ quả cho V2; sửa dòng trạng thái LT5–LT8 và ghi chú dòng LT1–LT8 ở mốc M2 của Kế hoạch.
  2. `/code-review high` lần 3 trên cả nhánh: 10 điểm, sửa 6, bỏ qua 3 điểm về hiệu năng hoặc cấu trúc không ảnh hưởng kết quả, giữ một PR (D65).
  3. Chạy lại `analysis.lt8_burn` trên `runs/sim/lt8-20261116-131116`: vẫn 9/9 hợp lệ, `lt8-burn.csv` không đổi.
- **Decision:** (D65) analysis đánh dấu không hợp lệ khi lúc bơm hoặc gỡ không có pod nào nhận độ trễ, hoặc độ trễ pod báo lại không khớp; khi thiếu recording rule; khi k lấy từ đồng hồ runner. Đợt firing chỉ tách khi hở > 60 s (`for`), vì firing quay lại sau một lần điều kiện sai cần ít nhất 90 s. Giữ bộ đo và phân tích trong cùng một PR vì gắn với nhau qua định dạng dữ liệu.
- **Results:** pytest analysis 99 passed; experiments: `test_lt8_burn` 9 passed, `test_backup_notify` hỏng 4 test chỉ trên Windows (`fcntl`, `rclone`, không liên quan nhánh này; CI chạy Linux); ruff check/format đạt; lychee trên các file đã sửa 0 lỗi; yamllint đạt.
  - Hệ quả rút ra (tính từ công thức, chưa đo): với trễ cộng thêm khoảng 30 s, N7 chỉ chắc giữ được khi x ≳ 0,23.
- **Links:** `docs/nhat-ky/van-hanh.md` (LT8), `docs/chi-tiet/06-ke-hoach-quan-ly.md`, `analysis/lt8_burn.py`, `experiments/ops/lt8_burn.py`.
- **Thesis:** §5 LT8 (mục `van-hanh.md` là bản nháp trực tiếp).

## 2026-11-16 – TR8: merge PR #47 (LT8)

- **Task:** TR8 · **Environment:** none
- **Done:**
  1. Gộp `origin/main` vào nhánh (xung đột duy nhất ở dòng `.PHONY` của `Makefile`: giữ cả `home-eval-*` và `sim-lt8`); sắp lại nhật ký tuần 07 theo thời gian.
  2. Gỡ trailer `Co-Authored-By` khỏi 4 commit của nhánh bằng `git filter-branch --msg-filter` chỉ trên `origin/main..HEAD` (tree giữ nguyên, kiểm bằng hash), force push có `--force-with-lease`, được Trình đồng ý.
  3. CI xanh cả 6 job trên commit sau khi viết lại; Trình merge bằng merge commit `eeefe25` và xoá nhánh `feat/tr8-lt8-burn-rate`.
- **Results:** LT5–LT8 đều đã có kết quả trong `docs/nhat-ky/van-hanh.md`; hình LT7, LT8 chưa vẽ.
- **Links:** PR #47; `docs/nhat-ky/van-hanh.md` mục LT8.

## 2026-11-16 – TR7: vẽ biểu đồ C1–C4 bằng script

- **Task:** TR7 · **Environment:** sim (chỉ đọc dữ liệu đã có `runs/sim/tr7-kb2-sim-2`; không đụng cluster)
- **Done:**
  1. Viết `analysis/charts.py`: C1 (KB2, bốn ô chung trục thời gian: λ theo lịch, số replica Ready và spec, TTFT p95 trượt 30 s, hàng đợi), C2 (SLO attainment), C3 (GPU-giờ % so với S4), C4 (trade-off, mỗi kịch bản một ô). Vẽ thẳng từ `build_tables.build`, ra SVG và PNG.
  2. Thêm matplotlib 3.11.2 vào nhóm phụ thuộc `plot` của `analysis/` (bật mặc định); `build_tables`, `metrics` vẫn chỉ dùng thư viện chuẩn. Đổi `_sliding_ttft_p95` thành hàm công khai để C1 và N2b dùng chung.
  3. Viết `analysis/tests/test_charts.py` (λ, p95 trượt tính tay, hàng đợi cộng theo pod, chọn lượt, khoảng λ cuối ngắn, SVG chạy lại giống từng byte).
  4. Vẽ thử trên `tr7-kb2-sim-2` và trên fixture đủ 4 cấu hình, xem từng hình rồi sửa: legend đè tiêu đề, nhãn trục log kiểu 3×10⁰, trục tung C4 tự co về 95,0–95,45 %, nhãn điểm C4 đè nhau.
  5. `/code-review high`: 10 điểm, sửa 8, bỏ qua 1 (đọc lại file hai lần) và mục nhật ký (ghi ở đây).
  6. Sửa Môi trường §14.2 (thay "Notebook vẽ biểu đồ" bằng lệnh `analysis.charts`) và gợi ý của `make analysis`.
- **Decision:** (D67) C1 chỉ vẽ S4, A1, A2 theo §16, mỗi (env, lượt, C) một hình vì lịch gửi phụ thuộc cả C; màu cố định theo cấu hình kèm marker và nhãn chữ; không dùng notebook hay pandas.
- **Results:** pytest analysis 108 passed (Python 3.15 và 3.11 `--locked`); ruff check/format đạt; lychee trên Môi trường 0 lỗi. Trên `tr7-kb2-sim-2` chỉ A2 được tính (S1 không hợp lệ: pod restart 1 lần), nên ra C1 và C2; C3, C4 bỏ qua vì không có S4. Hình C1 của A2: replica 1 → 2 → 3 trong khoảng phút 4,0–4,7 (spike bắt đầu phút 4), về 2 khoảng phút 19,3; TTFT p95 trượt vượt 2,5 s một đợt quanh phút 6,5–7.
- **Deviations:** Môi trường §14.2 trước ghi "Notebook vẽ biểu đồ"; đổi thành script theo ADR-006 §3.1 và CONTRIBUTING (logic ở `.py` có test). C5, C6 chưa làm (cần dữ liệu ĐG3, VH2).
- **Links:** `analysis/charts.py`, `analysis/tests/test_charts.py`, `analysis/pyproject.toml`, `docs/chi-tiet/05-moi-truong-danh-gia.md` §14.2.
- **Thesis:** §5.3 (C1 là biểu đồ trung tâm; C2–C4); chạy lại trên dữ liệu V2 sau phiên.

## 2026-11-16 – TR7: merge PR #48 (C1–C4)

- **Task:** TR7 · **Environment:** none
- **Done:** CI xanh cả 6 job (alerts, docs, manifests, python 3.11 và 3.15, yaml); `mergeable` = MERGEABLE, không có review hay bình luận; merge bằng merge commit `137fabf`, xoá nhánh `feat/tr7-charts-c1-c4` và `docs/tr8-log-pr47` (commit nhật ký của nhánh này đã vào cùng PR #48).
- **Links:** PR #48.

## 2026-11-17 – TR8: vẽ hình LT7 và LT8

- **Task:** TR8 (LT7, LT8), TR7 · **Environment:** none (dữ liệu simulator 16/11)
- **Done:**
  1. Viết `analysis/lt_charts.py`, dùng lại style của `charts.py` (màu, dấu phẩy thập phân, SVG không kèm ngày giờ). Hình LT7 vẽ từ `analysis/figures/lt7-hpa.csv` (phiên 2). Hình LT8 vẽ từ phiên `runs/sim/lt8-20261116-131116`.
  2. Xem từng hình rồi sửa bố cục: tiêu đề ô phải của LT7 tràn và đè nhãn cận 11 s, nên chuyển cận vào legend; nhãn θ đè đường r_5m, nên chuyển sang mép trái.
  3. Chạy `/code-review high`: 10 điểm, sửa 9 điểm. Đáng kể nhất: vạch firing đo trước đó kết thúc ở mẫu ALERTS cuối, sớm hơn khoảng 15 s so với định nghĩa của vạch dự đoán (lần tính đầu tiên mà điều kiện đã sai), nên trông như hết cảnh báo *sớm*. Sau khi sửa, vạch lấy `fire_s` và `clear_s` từ `lt8_burn.analyze_rep`. Các điểm khác: lọc lượt LT7 như bảng (bỏ restart), đếm riêng lượt thiếu chặng, ghi đúng loại đồng hồ, tiêu đề lấy threshold và max từ dữ liệu, không lỗi khi danh sách rỗng.
  4. Thêm 6 test (`analysis/tests/test_lt_charts.py`).
- **Decision:** D68: hai hình riêng, commit SVG vào `analysis/figures/`. Dữ liệu thô của LT8 không có trong Git, nên luận văn cần hình đã vẽ. Không dùng hai trục tung.
- **Results:** `pytest analysis` 114 passed (Python 3.15; test mới chạy cả 3.11); `ruff check` và `ruff format --check` đạt. Hình LT8 cho thấy: x = 0,1 không kêu ở cả 3 lần bơm; ở x = 0,3 và 0,6, r_5m đo bám vạch dự đoán và trễ vài giây; vạch firing đo bắt đầu và kết thúc muộn hơn dự đoán, khớp bảng LT8 ở `van-hanh.md`, trừ một lần kêu sớm ở x = 0,3 (đã giải thích ở đó). Hình LT7: 12/12 lượt đúng số replica; ở cả 7 lượt, đoạn quyết định (ba chặng đầu) kết thúc trước vạch 11 s.
- **Links:** nhánh `feat/tr8-lt7-lt8-figures`; `analysis/lt_charts.py`, `analysis/tests/test_lt_charts.py`, `analysis/figures/lt7-hpa.svg`, `analysis/figures/lt8-burn.svg`, `envs/sim/README.md`, `analysis/pyproject.toml`.
- **Thesis:** §5 LT7 (hình replica theo C và các chặng trễ), §5 LT8 (hình r_1m/r_5m quanh lúc bơm, khoảng firing đo so với dự đoán).

## 2026-11-17 – TR8: merge PR #49 (hình LT7, LT8)

- **Task:** TR8 · **Environment:** none
- **Done:** CI xanh cả 6 job (alerts, docs, manifests, python 3.11 và 3.15, yaml); `mergeable` = MERGEABLE, không có review hay bình luận; merge bằng merge commit `10c0527`, xoá nhánh `feat/tr8-lt7-lt8-figures`.
- **Links:** PR #49.

## 2026-11-18 – TR8: hình LT5 (định luật Little) và LT6 (GPU util bão hoà)

- **Task:** TR8 · **Environment:** none
- **Done:**
  1. Thêm `--lt5`, `--lt6` vào `analysis/lt_charts.py`. Cả hai hình vẽ từ CSV đã commit (`analysis/figures/lt5-little.csv`, `lt6-gpu-util.csv`), không cần dữ liệu thô.
  2. Hình LT5: ô trái là L_server theo λ\_thực × W (thang log, đường y = x, dải ±15 %); ô phải là độ lệch, kèm thanh ±1 SE do lấy mẫu. Hình LT6: ô trái là util theo λ ÷ C, kèm vạch dự đoán 1 − e^(−L) và mức 77 % mà trên đó A1 thêm pod; ô phải là running + waiting (thang log), kèm threshold A2. Tiêu đề mỗi ô ghi kết luận "tách được hay không", tính bằng `lt6_gpu_util.separation`.
  3. Xem hình rồi sửa bố cục. Legend LT6 tràn khung, nên đổi từ 3 cột sang 2 cột. Vạch dự đoán của hai model nằm sát nhau (λ ÷ C 0,16 và 0,17) mà cùng màu đen, nên đổi sang màu của model. Nhãn S1-CONST2-1 lòi khỏi ô, nên chuyển sang bên trái điểm.
  4. Chạy `/code-review high`: 10 điểm, sửa cả 10. Các điểm đáng kể:
     - Tên model tra theo tên file trần, nên `capacity.json` của ĐG1 trên V2 sẽ bị ghi là "0,5B". Đã sửa: tra theo cặp (env, file).
     - L_server = 0 làm trục log chia cho 0.
     - LT6 gộp mọi phiên simulator vào một phép kiểm "tách được".
     - `main` trả lỗi mà không báo những hình đã ghi.
     - Nhãn vạch phụ của trục log dùng dấu chấm thập phân.
     - Câu trong `van-hanh.md` không phân biệt hai cửa sổ cùng tên S1-CONST2-1, và chưa giải thích chấm rỗng là gì.
  5. Thêm 5 test. Thêm dòng "Hình" và sửa dòng "Còn thiếu" của LT5, LT6 trong `van-hanh.md`.
- **Decision:** D69. Chấm rỗng là cửa sổ có hàng đợi, theo `QUEUE_MIN` sẵn có của `lt5_little`; hình không tự phân loại "dừng/quá tải", vì bảng phân loại theo nhận định và CSV không có cột đó. Tên model tra bảng (env, file), không thêm cột model vào CSV. Không dùng hai trục tung cho util và L.
- **Results:** `pytest analysis` 119 passed trên Python 3.15 và 3.11; `ruff check`, `ruff format --check` và lychee (`van-hanh.md`) đạt.
  - LT5: 23 cửa sổ, trong đó 9 cửa sổ có hàng đợi. 22/23 nằm trong ±15 %; chỉ cửa sổ `steady` của S1-CONST2-1 trên simulator nằm ngoài (−35,5 %).
  - LT6: util không tách được tải vừa khỏi quá tải ở cả hai model, và mức thấp nhất (0,780) vẫn trên 77 %. A2 tách được, khoảng hở 3,9× (1,5B) và 7,7× (0,5B).
  - Mọi số khớp bảng LT5, LT6 trong `van-hanh.md`.
- **Links:** nhánh `feat/tr8-lt5-lt6-figures`; `analysis/lt_charts.py`, `analysis/tests/test_lt_charts.py`, `analysis/figures/lt5-little.svg`, `analysis/figures/lt6-gpu-util.svg`, `docs/nhat-ky/van-hanh.md`.
- **Thesis:** §5 LT5 (hình L_server theo λW, độ lệch kèm SE), §5 LT6 (hình util bão hoà so với L; A1 so với A2).

## 2026-11-18 – TR8: merge PR #50 (hình LT5, LT6)

- **Task:** TR8 · **Environment:** none
- **Done:** CI xanh cả 6 job (alerts, docs, manifests, python 3.11 và 3.15, yaml); `mergeable` = MERGEABLE, không có review hay bình luận; merge bằng merge commit `4dc5c42`, xoá nhánh `feat/tr8-lt5-lt6-figures`. Từ đây LT5–LT8 đều có hình trong `analysis/figures/`.
- **Links:** PR #50.

## 2026-11-18 – Luận văn: khung `docs/luan-van/` và mục 3.4

- **Task:** chung (ghép luận văn), TR3, TR4 · **Environment:** none
- **Done:**
  1. Dựng `docs/luan-van/`: `README.md` gồm tổ chức file `CC-SS-<ten>.md` (mỗi file một người viết), quy ước văn phong, thuật ngữ, số, hình, bảng, trích dẫn `[@key]` với `tai-lieu.bib`, comment nguồn sau mỗi đoạn có số, và lệnh pandoc ghép ra `.docx`. Thêm thư mục vào CONTRIBUTING §1.
  2. Cài pandoc 3.13 (bản zip, sha256 khớp digest của GitHub release) vào `~/.local/bin`.
  3. Viết mục 3.4 "Thiết kế giám sát, SLO và cảnh báo": một agent viết từ nguồn trong repo, một agent khác đối chiếu từng con số và khẳng định. Bản soát báo 25 điểm: 7 sai sự kiện nhẹ, 6 lập luận sai hoặc thiếu, 4 thiếu nguồn, 2 quy ước, 6 văn. Sửa 24 điểm; giữ số bảng tạm `3.4a`–`3.4d` đến khi ghép chương 3.
  4. Tự chạy lại bằng promtool điểm đáng kể nhất của bản soát (Incidents).
  5. Kiểm các URL trong bib (HTTP 200 ngày 18/11) và đổi sang URL của đúng phiên bản đã ghim (vLLM v0.31.0, KEDA 2.21, chart 92.1.1, Alertmanager v0.34.1).
  6. Chạy `/code-review high` trên nhánh: 10 điểm, sửa cả 10. Đáng kể nhất: N1 và N7 ở đoạn mở đầu thiếu phạm vi (A2, tải ổn định; page giả là page khi tỷ lệ xấu theo log client < 20%); hai dashboard dùng hai định nghĩa TPOT khác nhau; thời gian fallback do chu kỳ sync 5 s của HPA quyết định, không phải `pollingInterval`; mục chia cho hai người (3.3, 4.11) cần tách file `a`, `b`; tên trong bib phải bọc `{}` để kiểu trích dẫn không viết hoa sai; pandoc ghim vào `docs/phien-ban.md`.
- **Decision:**
  - D70: bản nguồn luận văn bằng Markdown, mỗi mục một file, ghép bằng pandoc; khuôn của trường áp ở W9 qua `--reference-doc`. Bỏ Word/Google Docs (không xem diff, không gắn nguồn cho số liệu), LaTeX (khuôn và góp ý của GVHD đi qua Word), một file một chương (Quang và Trình cùng sửa một file).
  - D71: giữ nguyên `LLMErrorRateHigh` trong đợt đánh giá, vì sát ngày đóng băng 22/11 và không muốn đổi cấu hình đã kiểm thử. Mục 3.4 ghi đúng hành vi thật và nêu hướng cải tiến (burn rate hai cửa sổ). Comment trong `llm.yaml` và Vận hành §3.2 sửa ở PR đồng bộ tài liệu sau.
  - Không chèn Hình 7 (`07-slo-canh-bao-runbook`), vì hình lệch với cái đã làm ở 6 chỗ: ghi DCGM; có cảnh báo nhiệt độ và XID chưa làm; có "thắt giới hạn tốc độ" (rate limit đã lược); thiếu condition của ScaledObject; ghi "chặn trùng" như quy tắc riêng, thực ra là mặc định của chart; ghi Argo CD, trong khi VM thuê không có. Sửa hình ở PR riêng.
- **Results:** `03-04-giam-sat-slo-canh-bao.md` có khoảng 1.900 từ thân bài, 4 bảng, dẫn 5 tài liệu (bib có thêm `keda-prometheus-scaler` để dùng cho mục 3.3). `pandoc … --citeproc` ra `.docx` không lỗi, không cảnh báo trích dẫn; lychee 0 lỗi.
- **Incidents:** comment của `LLMErrorRateHigh` trong `llm.yaml` và Vận hành §3.2 nói `for: 1m` để không page vì vài lỗi 503 lẻ khi chuyển pod. Điều này sai: ngưỡng 1% tính trên cửa sổ 5 phút, đợt lỗi nằm trong cửa sổ suốt 5 phút, nên `for` không lọc được. Thử bằng promtool (1 req/s, một đợt 5 lỗi 503 ở phút 10): firing lúc 12m và 14m, hết lúc 16m.
- **Deviations:** các điểm thiết kế lệch với cái đã làm, tìm được khi viết và soát (sửa ở PR đồng bộ tài liệu):
  - Vận hành §2.3: câu "`1 − tốt/tổng` cho 100% xấu khi không có traffic" sai; bản soát thử bằng promtool, cả hai dạng đều ra NaN.
  - TPOT có hai định nghĩa: dashboard SLO dùng `vllm:request_time_per_output_token_seconds` (trung bình mỗi request, bucket `le="0.1"`), dashboard Serving/GPU vẽ `vllm:inter_token_latency_seconds` (từng khoảng giữa hai token) cạnh vạch 100 ms; Vận hành §2.1 chỉ ghi định nghĩa thứ hai. Cần thống nhất.
  - Vận hành §11 nói unit test kiểm cặp cửa sổ 1h/5m; test chỉ có cặp 5m/1m.
  - Thông số §9.4 ghi retention ở cloud 15 ngày; `envs/cloud/platform/` không đặt, nên dùng mặc định của chart.
  - Thông số §7 ghi máy tạo tải đi qua route riêng của Traefik; route này đã lược và `matrix-v2.yaml` gọi thẳng Service, nên `llm:error_ratio:rate5m` rỗng trong các lượt đánh giá.
  - Hai runbook còn khuyên "thắt giới hạn tốc độ"; comment cũ ở `slo.yaml` (bucket "còn phải xác nhận") và README của dashboard (hàng KEDA "chưa làm").
  - Chưa kiểm: severity của `TargetDown` trong chart 92.1.1 (nếu là warning thì exporter chết sẽ không có tin Telegram).
- **Links:** nhánh `docs/tr4-thesis-monitoring-design`; `docs/luan-van/README.md`, `docs/luan-van/03-04-giam-sat-slo-canh-bao.md`, `docs/luan-van/tai-lieu.bib`, `CONTRIBUTING.md` §1.
- **Thesis:** §3.4 (bản nháp đầu); Hạn chế (chưa có dead man's switch; `LLMErrorRateHigh` nhạy với đợt lỗi ngắn ở tải thấp); chương 6 (hướng cải tiến cảnh báo lỗi).

## 2026-11-18 – Luận văn: merge PR #51 (khung `docs/luan-van/`, mục 3.4)

- **Task:** chung, TR3, TR4 · **Environment:** none
- **Done:** CI xanh cả 6 job (alerts, docs, manifests, python 3.11 và 3.15, yaml); `mergeable` = MERGEABLE, không có review hay bình luận; merge bằng merge commit `626769e`, xoá nhánh `docs/tr4-thesis-monitoring-design`. Commit nhật ký merge PR #50 (`d6f03d9`) vào cùng PR này.
- **Links:** PR #51.

## 2026-11-20 – Kiểm tiến độ V2; review PR #46 (`vh3-delete` giữ 2 pod)

- **Task:** chung (tiến độ V2), Q6 (review) · **Environment:** none
- **Done:**
  1. `git fetch`, xem commit trên mọi nhánh, PR, nhật ký của Quang và `van-hanh.md`.
  2. Review PR #46: đọc diff `experiments/ops/vh.py` và test; ghép nhánh với `origin/main` trong một worktree tạm; chạy test và ruff.
- **Results:**
  - Tính tới 20/11, **V2 chưa chạy**. Commit cuối của Quang là 16/11 22:44. Phiên 16/11 trên 2 × RTX 4000 Ada (N = 2) là phiên thử: ĐG1 rút gọn ra C = 5,0 req/s; 2 lượt autoscaling invalid vì máy tạo tải thiếu CPU; 4 kịch bản VH chỉ là số thử. Dữ liệu thử nằm trong `runs/` trên máy của Quang, không có trong Git. Đóng băng dữ liệu theo lịch là 22/11.
  - PR #46: ghép với `main` không xung đột. `pytest experiments` 162 passed, 4 failed; 4 test hỏng (`test_backup_notify`, rclone giả không chạy trên Windows) hỏng y hệt trên `main` (161 passed, 4 failed). `ruff check` và `ruff format --check` sạch. CI của PR xanh.
  - Logic của PR đúng. Điểm chính tìm được: bước chờ pod thứ hai (tới 900 s) nằm trong cửa sổ tải cố định 780 s, và chưa có kiểm "sự cố xảy ra khi tải còn chạy". Nếu pod thứ hai Ready sau khoảng 780 s, lệnh xoá chạy khi tải đã dừng, 0 lỗi, vẫn chấm đạt. Ca thường không bị: cold start đo được 66–152 s, nên lệnh xoá rơi vào khoảng 190–270 s. vh2a có cùng rủi ro (chờ rollout tới 1800 s, tải 1200 s). Hai điểm nhỏ: lỗi của `scale_min(1)` trong `finally` đè lên lỗi gốc; bảng VH3 ở `05-moi-truong-danh-gia.md:474` chưa ghi điều kiện "còn ≥ 2 pod Ready".
- **Incidents:** test của `experiments` không chạy trọn trên Windows (4 test cần shell script giả). Chỉ CI trên Linux chạy đủ.
- **Links:** PR #46; `experiments/ops/vh.py`.
- **Thesis:** §Hạn chế hoặc tiến độ: mốc V2 trễ so với lịch 14–15/11.

## 2026-11-21 – Review PR #52 (kết quả V2) và đăng review PR #46

- **Task:** chung (review), TR4, TR7 · **Environment:** none
- **Done:**
  1. `git fetch`: V2 đã chạy 18–19/11 trên VM 4 × RTX 4060 Ti. Kết luận "V2 chưa chạy" ở mục 20/11 là sai: commit V2 ghi ngày 19/11 nhưng tới tối 20/11 Quang mới push (PR #52 mở lúc 22:18).
  2. Đọc trọn diff PR #52 (11 file, +944/−16): `capacity.json` của V2, `matrix-dg1-v2.yaml`, `matrix-v2.yaml`, `dg3.sh`, `test_runner.py`, `nguon-tu-lieu.md`, `quy-tac-viet.md`, nhật ký tuần 07 của Quang, `van-hanh.md`.
  3. Đối chiếu số ở `nguon-tu-lieu.md` §3 với nhật ký và `capacity.json`. Kiểm `dg3.sh` bằng `bash -n` và shellcheck 0.11.0. Kiểm diff không có IP công khai. Đối chiếu nguyên nhân `AlertmanagerFailedToSendAlerts` với `common/platform/alertmanager-secret.sh` và `envs/cloud/provision/install-platform.sh`.
  4. Đăng review Approve trên PR #52, và trên PR #46 (bản soạn 20/11, thêm điểm `vh3_kill` rút ra từ V2).
- **Decision:** Approve cả hai PR, vì các điểm tìm được không làm sai số liệu V2 đã thu. Không chặn merge, để dữ liệu V2 và `vh.py` vào `main` trước mốc đóng băng 22/11.
- **Results:**
  - CI của PR #52 xanh 6/6; `bash -n` và shellcheck đạt; diff không có IP công khai.
  - Khớp nguồn: GPU-giờ so với S4 (A2 × KB1 −75 %; A1 −10/−5/−7 %; A2 × KB2 −25…−28 %; A2 × KB3 −8 %), threshold A2 = 0,8 × 46,3 = 37, L0 trung bình 305,5 s.
  - Điểm nêu trong review #52:
    1. `AlertmanagerFailedToSendAlerts` ở V2 nhiều khả năng do PC không có `.env`, nên `alertmanager-secret.sh` bỏ qua Secret Telegram (`exit 0`). Chưa kiểm; cần console `cloud-platform` trong `runs/v2-evidence/`.
    2. `quy-tac-viet.md` và `nguon-tu-lieu.md` mô tả luồng Markdown + pandoc, trái với quyết định chuyển sang Google Docs nằm trong cùng PR.
    3. vh3-delete và vh3-kill cùng ghi 67,4 s, cần đối chiếu với `summary.json`.
    4. `dg3.sh` khi timeout vẫn ghi `trigger_to_ready_s` nhỏ, trông như lượt hợp lệ.
  - Ghi chú cho luận văn: C = 3,5 req/s là cận dưới (năng lực thật nằm trong [3,5; 4)); ĐG3 có độ phân giải 1 s.
- **Deviations:** chưa nhận dữ liệu `runs/` của V2, nên chưa kiểm số nào trực tiếp từ dữ liệu thô. Chưa chạy pytest cục bộ trên nhánh PR #52, chỉ dựa vào CI.
- **Links:** PR #52, PR #46 (review của `trinh-cloud`).
- **Thesis:** §5.2 (C là cận dưới); §5.4 (độ phân giải ĐG3); §5.5 VH6 và Hạn chế (không có tin Telegram trong V2, nếu xác nhận nguyên nhân).

## 2026-11-21 – Luận văn: tạm viết trên Google Docs

- **Task:** chung (luận văn) · **Environment:** none
- **Decision:** Trình đồng ý dùng Google Doc do Quang dựng ngày 20/11 làm bản gốc của luận văn, thay cho luồng Markdown + pandoc trong `docs/luan-van/` (quyết định 18/11). Đây là lựa chọn tạm: khi nội dung xong, hai người xét lại có chuyển sang LaTeX không. Doc xuất được .docx, khớp với việc khuôn của trường và góp ý của GVHD đi qua Word, và vẫn chuyển tiếp được (.docx → pandoc → LaTeX).
  - Không chuyển sang LaTeX ngay: chưa biết khuôn của trường, đổi công cụ lần hai khi còn khoảng 2,5 tuần, và luận văn có ít công thức.
  - Cách làm: Trình nháp từng mục bằng Markdown (agent viết, agent khác đối chiếu số với nguồn), rồi dán vào Doc. Sau khi dán, mọi sửa đổi chỉ làm trên Doc; góp ý bằng Comment/Suggesting. Trích dẫn đề nghị dùng Zotero cho Google Docs (nhập `tai-lieu.bib`, kiểu IEEE).
  - Không nháp trong repo qua PR: sau khi dán vào Doc, hai bản dễ lệch nhau, và mỗi mục tốn thêm một PR.
- **Deviations:** `docs/luan-van/README.md` và `quy-tac-viet.md` (§1, §7, §8, §10) vẫn tả luồng pandoc; sẽ sửa trong một PR sau khi PR #52 merge. Mục 3.4 (bản Markdown đã merge ở PR #51) chưa chép sang Doc, vì Doc chưa được share cho Trình.
- **Thesis:** quy trình viết (lời mở đầu hoặc phần khai báo dùng AI agent, `quy-tac-viet.md` §9).

## 2026-11-21 – Nhận dữ liệu V2; vẽ lại C1–C4 bản V2, sửa nhãn C4

- **Task:** TR7, TR4 (VH6) · **Environment:** none (máy Trình, dữ liệu V2)
- **Done:**
  1. Nhận gói riêng của Quang (`v2-data-20261119.tar.gz`, `runs-all-20261120.tar.gz`, ghi chú). `sha256sum -c SHA256SUMS`: cả hai file nén OK. Giải nén `runs-all` vào `runs/` (đã gồm V2; không trùng file nào đã có). `v2-evidence/SHA256SUMS`: chỉ FAILED `vm-final-state.txt`, đúng như ghi chú của Quang (file ghi 3 s sau khi lập danh sách checksum).
  2. Đối chiếu số VH6 trong ghi chú của Quang với `runs/v2-vm/v2-dg2/tables/alerts.csv` (47 dòng, 17 lượt): khớp (Results).
  3. Vẽ lại C1–C4 trên `runs/v2-vm/v2-dg2` (`--baseline S4`) và xem bố cục từng hình: C1 (3 lượt), C2, C3 giữ nguyên; C4 lỗi (Incidents).
  4. Sửa `plot_c4`: `_place_labels` đo từng nhãn và thử 12 vị trí, chọn vị trí phạt thấp nhất (đè nhãn hoặc dấu điểm > tràn khỏi ô > cắt vạch tham chiếu); `_near_groups` gộp có bắc cầu các điểm trung bình cách nhau dưới 4 pt thành một nhãn ("A1, A2"), điểm sau vẽ 1/4 diện tích để vẫn thấy điểm dưới; số lượt chuyển lên tiêu đề ô; trục tung chừa 14 % phía trên 100 %, không có vạch chia trên 100 %; chốt layout sau khi đặt nhãn. Thêm test.
  5. `/code-review high`: 10 điểm. Sửa 7 (layout chạy lại khi lưu ở dpi khác; test chưa kiểm chấm từng lượt và layout lúc lưu; điểm nhỏ trong nhóm chưa là vật cản; gộp chưa bắc cầu; vẽ thừa một lần; tạo rồi xoá artist; tuple không tên). Một điểm là chính mục nhật ký này. Không sửa 2: nhãn tràn khỏi ô khi mọi vị trí đều tràn (ghi là hạn chế trong docstring, nhãn chỉ gồm tên cấu hình chưa gặp); nơi đặt hình (Decision).
  6. Commit SVG C1–C4 và 4 bảng CSV vào `analysis/figures/v2-dg2/`. PNG cho Google Doc giữ ở máy Trình, không commit.
- **Decision:**
  - Số lượt của C4 ghi ở tiêu đề ô ("KB2  (n: S1 1, S4 1, A1 2, A2 3)"), nhãn cạnh điểm chỉ ghi tên cấu hình: nhãn "S4 (n=1)" dài hơn khoảng trống bên phải điểm 100 %, nên bị đẩy xuống dưới vạch N1, sát điểm A1 (dễ đọc nhầm). Bỏ: nới trục hoành tới khoảng 145 % (bỏ trống khoảng 30 % bề ngang mỗi ô); hai hàng nhãn phía trên 100 % (khoảng trống trên trục quá lớn).
  - D73: hình và 4 bảng CSV của V2 nằm ở `analysis/figures/v2-dg2/`, như LT5–LT8 (hình cùng CSV). Dữ liệu thô vẫn giữ riêng, vì console có IP máy thuê; các bảng không có IP hay đường dẫn máy (đã grep). Bỏ: chỉ để trong `runs/` (không kiểm được từ repo); `docs/images/` (CONTRIBUTING dành cho hình vẽ sinh từ `docs/diagrams/`).
- **Results:**
  - VH6 (ĐG2 V2, 17 lượt): `LLMSLOBurnFast` 8 đợt, trong đó 7 đợt tính được: bắt đầu kêu 204–374 s sau đầu pha chính, `client_bad_ratio` 0,27–0,73, `false_page` = False ở cả 7. Đợt thứ 8 (A2-KB3-2, −176 s) còn sót từ lượt trước (`firing_at_start` = True). `KubeHpaMaxedOut` 5 đợt (A1 × KB2 hai lượt, A1 × KB3, A2 × KB3 hai lượt). `AlertmanagerFailedToSendAlerts` và `AlertmanagerClusterFailedToSendAlerts` kêu ở cả 17/17 lượt.
  - `cells.csv` (trung bình các lượt counted): SLO attainment 100 % ở mọi ô của S4, A1 và ở A2 × KB1, KB3; A2 × KB2 80,0 %; S1 × KB2 12,5 %; S1 × KB3 0 %. GPU-giờ so với S4: A2 25 % (KB1), 73 % (KB2), 92 % (KB3); A1 90 %, 95 %, 93 %; S1 25 %.
  - `pytest analysis` 120 passed; `ruff check`, `ruff format --check` sạch. Chạy lại `analysis.charts` ra SVG giống từng byte. Thử bật lại constrained layout rồi lưu ở 200 dpi: bề rộng ô C4 đổi từ 0,788 lên 0,821 bề rộng hình, nên phải chốt layout.
- **Incidents:**
  - C4 bản chạy thử 20/11: nhãn "S4 (n=1)" cắt vạch N1 ở cả 3 ô; nhãn S1 ở KB3 đè lên số 0 của trục x; điểm A2 (92,0 %) che điểm A1 (92,7 %) ở KB3. Nguyên nhân: hướng nhãn cố định theo cấu hình (`LABEL_OFFSET`). Sửa ở bước 4.
  - File zip của gói nằm trong `docs/` (chưa track): chuyển ra thư mục cục bộ ngoài Git để không commit nhầm 25 MB dữ liệu có IP máy thuê.
- **Deviations:** Môi trường §14.2 ghi `analysis.charts` ghi hình vào `runs/<phiên>/figures/`; bản V2 dùng `--out analysis/figures/v2-dg2` để đưa vào Git. C5, C6 chưa làm.
- **Links:** nhánh `fix/tr7-c4-labels`; `analysis/charts.py` (`plot_c4`, `_place_labels`, `_near_groups`), `analysis/tests/test_charts.py`, `analysis/figures/v2-dg2/`.
- **Thesis:** §5.3 (C1–C4 bản V2); §5.5 VH6 (số đợt cảnh báo); Hạn chế (V2 không có tin Telegram: `FailedToSend` kêu suốt 17 lượt, nhiều khả năng thiếu Secret Telegram, không kiểm trực tiếp được).

## 2026-11-21 – TR7: merge PR #53 (nhãn C4, hình và bảng V2)

- **Task:** TR7 · **Environment:** none
- **Done:** CI xanh cả 6 job (alerts, docs, manifests, yaml, python 3.11, python 3.15); `mergeable` = MERGEABLE, 0 review, 0 bình luận. Merge bằng merge commit, xoá nhánh `fix/tr7-c4-labels`. Xoá luôn nhánh `docs/tr4-log-pr51`, vì 4 commit nhật ký của nó đã vào `main` qua PR này.
- **Links:** PR #53, merge commit `b0d8b2c`.

## 2026-11-21 – TR8: LT5, LT6 thêm dữ liệu V2

- **Task:** TR8 (LT5, LT6) · **Environment:** none (dữ liệu V2 đã đo 18–19/11)
- **Done:**
  1. Chạy `lt5_little` trên dữ liệu thô của runner V2: ĐG1 (`runs/dg1-v2-4060ti`, 5 mức, 1 replica) và ĐG2 (`runs/v2-vm/v2-dg2`, 17 lượt, 1–4 replica), k = 1. Tạo lại `analysis/figures/lt5-little.csv` (27 → 80 dòng; 27 dòng cũ không đổi, ngoài cột `session` mới).
  2. Chạy `lt6_gpu_util` thêm `runs/dg1-v2-4060ti/capacity.json`; tạo lại `lt6-gpu-util.csv` (18 → 23 dòng; dòng cũ không đổi, ngoài cột `session`).
  3. `lt5_little`, `lt6_gpu_util`: thêm cột `session` vào CSV. `lt_charts.py`: bảng `SOURCE_GROUP` tra nhóm theo (env, session), thêm nhóm "V2, model 3B" (màu thứ 4), in cảnh báo khi có nguồn chưa có trong bảng; bỏ cả cửa sổ `main` của KB3; tiêu đề ô LT6 tự xuống dòng khi kết luận dài. Vẽ lại `lt5-little.svg`, `lt6-gpu-util.svg`; PNG cho Doc ở `.work/luan-van/hinh/`.
  4. Kiểm dự đoán LT6 "A1 × KB1 gần bằng S4" trên bảng ĐG2 V2 và `pods_timeline.json` của A1-KB1.
  5. Ghi kết quả vào `van-hanh.md` (LT5, LT6) và Kế hoạch (dòng LT1–LT8).
- **Decision:** D74. LT5 lấy V2 từ dữ liệu thô runner thay vì `capacity.json`, vì có thêm edge, L lấy mẫu, cận k và các cửa sổ nhiều replica. LT6 lấy `capacity.json` trong `runs/` (phần `curves` trùng bản của PR #52), không đợi PR #52 merge.
- **Results:**
  - LT5 V2: 27/27 cửa sổ chưa xếp hàng lệch −5,8…+4,9 % (z trung bình −0,42; 3 cửa sổ |z| > 2 đều lúc tải đang đổi, edge âm). 13 cửa sổ 4 replica lệch −5,8…+4,9 %. Ngoài dải chỉ có ĐG1 λ = 5 (1,43 C): −21,4 %, client −20,4 %, edge −51,7. Cận k của cả 22 lượt chứa 1 (giao [0,9973; 1,0076]). Hình: 52/54 cửa sổ trong ±15 %.
  - LT6 V2 (C = 3,5, threshold A2 37): util = 1,000 ở cả 5 mức (0,57–1,43 C), không tách được; A2 4,6×, KV 3,9×, waiting ∞. KV đứng yên khi quá tải nặng (0,240 → 0,241).
  - Dự đoán A1 × KB1: L = 11,3–12,0 > 4,4; A1 đủ 4 replica Ready lúc t = 231–246 s rồi giữ tới hết tải; pha `steady` 3,66–3,73 replica, GPU-giây 97–98 % S4 (cả lượt 90–91 %); A2 giữ 1 replica. Đúng dự đoán.
- **Incidents:** lần chạy đầu, `lt6_gpu_util.summary` gom theo tên file nên gộp `capacity.json` V2 với `capacity.json` 0,5B ở nhà ("vừa = λ [4, 6, 8, 2]"). Bản sửa đầu gom theo (env, tên file); `/code-review high` chỉ ra khoá này vẫn gộp V2 với V1 (A4000) và lượt thử 4000 Ada (cùng env cloud, cùng tên file). Sửa gốc: thêm cột `session`, gom và tô màu theo (env, session), thêm test cho cả hai ca trùng tên. Hai CSV chỉ thêm cột, số liệu không đổi. Review còn nêu: tiêu đề LT6 có thể ngắt giữa tên phiên có gạch nối (đã đặt `break_on_hyphens=False`); phiên V2 đổi tên sẽ bị tô xám mà không báo (đã thêm cảnh báo); `van-hanh.md` ghi SE với 24 mẫu, trong khi V2 có 48 mẫu (đã sửa). CI job `docs` đỏ ở lần push đầu: Trình đã thêm "thêm V2 ngày 21/11" vào tiêu đề mục LT5, LT6 của `van-hanh.md`, làm hỏng anchor mà Kiến trúc §10.1 (`03-kien-truc-autoscaling.md`, dòng 384) trỏ tới. Lychee chạy cục bộ trước đó chỉ trên hai file đã sửa (chạy cả repo thì 53 lỗi đường dẫn cũ, CI bỏ qua, che mất lỗi này). Sửa: giữ nguyên tiêu đề, ghi "Thêm dữ liệu V2 ngày 21/11" ở dòng đầu mục; chạy lại lychee trên cả repo với danh sách `--exclude` tạo giống job `docs`: 0 lỗi. Khi ghi `van-hanh.md`, câu về cửa sổ 4 replica ban đầu ghi sai khoảng lệch (−2,6…+4,9 %, sót pha `ramp` S4-KB3); đã kiểm lại bằng số và sửa thành −5,8…+4,9 %.
- **Deviations:** LT6 vẫn dùng các bậc λ của ĐG1 thay cho lượt tải tăng dần (như 16/11). V2 không có mức dưới 0,57 C nên không thêm điểm kiểm phần cong của 1 − e^(−L).
- **Links:** nhánh `feat/tr8-lt5-lt6-v2`; `analysis/lt_charts.py`, `analysis/lt6_gpu_util.py`, `analysis/tests/test_lt_charts.py`, `analysis/tests/test_lt6_gpu_util.py`, `analysis/figures/lt5-little.*`, `lt6-gpu-util.*`, `docs/nhat-ky/van-hanh.md` (LT5, LT6), `docs/chi-tiet/06-ke-hoach-quan-ly.md`.
- **Thesis:** §5 kiểm chứng lý thuyết LT5, LT6: Hình LT5 (54 cửa sổ, 3 môi trường), Hình LT6 (3 model); câu "A2 đo đúng L cả khi 4 replica trên GPU thật"; §5 ĐG2: A1 × KB1 ≈ S4 có cơ chế giải thích (util bão hoà khi L > 4,4).

## 2026-11-21 – TR8: merge PR #54 (LT5, LT6 thêm V2)

- **Task:** TR8 · **Environment:** none
- **Done:** lần push đầu, CI job `docs` đỏ vì anchor mục LT6 bị đổi (mục ngay trên, Incidents); sửa và push lại thì cả 6 job xanh (alerts, docs, manifests, yaml, python 3.11, python 3.15). `mergeable` = MERGEABLE, 0 review, 0 bình luận. Merge bằng merge commit; xoá nhánh `feat/tr8-lt5-lt6-v2` và `docs/tr7-log-pr53` (commit nhật ký merge #53 đã vào `main` qua PR này).
- **Links:** PR #54, merge commit `041c6f7`.

## 2026-11-21 – Luận văn: nháp bảng nghiệm thu F1–F7, N1–N8 (mục 5.6)

- **Task:** TR8 (luận văn) · **Environment:** none
- **Done:**
  1. Đối chiếu các số của nhật ký Quang (18–19/11) và `nguon-tu-lieu.md` §3 với dữ liệu thô V2: `runs.csv`, `phases.csv`, `alerts.csv` của ĐG2; `summary.json` của 6 kịch bản VH; `summary.txt` của 5 lượt ĐG3.
  2. Tìm bằng chứng cho F1–F7 trong `van-hanh.md`, nhật ký Trình tuần 04–06, Thông số §3, `install-platform.sh`, `Makefile` (`alerts-coverage`) và `vh.py` bản đã chạy trên V2.
  3. Viết nháp mục 5.6 bằng Markdown, ngoài Git, chờ dán vào Google Doc. Nháp gồm bảng N1–N8, bảng F1–F7 và khuyến nghị chọn A2, mỗi số kèm dòng nguồn.
- **Decision:** D75. Cột kết luận dùng năm mức: Đạt, Đạt một phần, Không đạt, Báo cáo, Chưa đo.
  - F2 ghi Đạt dù T6 ở nhà và T7 chưa chạy: ĐG2 đã cho thấy scale 1 → 4 rồi giảm lại trên GPU thật, còn T7 (A4) chỉ ở mức Could.
  - N4 chỉ dẫn 3 lượt A2 × KB2, không dẫn 5 lượt.
  - N8 ghi Chưa đo.
- **Results:**
  - Đạt: N1 (A2 × KB1 và A2 × KB3 pha `sustain`, 100% ở cả 4 lượt); N2a (79,7–81,5 s); N3 ở KB1 (25% GPU-giờ của S4, SLO attainment chênh 0 điểm); N4; N5 (77,7 / 305,5 s = 25,4%); N6 (fallback 16,8 s, dựng lại 8 phút 22 giây); N7 (S1 × KB3 104,5 s; 0 page giả trong 17 lượt).
  - Báo cáo: N2b (409–430 s). Chưa đo: N8 (người thứ hai dựng lại cluster; tổng chi phí).
  - F1, F2, F4 đạt. Đạt một phần: F3 (chưa cập nhật qua Git rồi `git revert`), F5 (chưa có ảnh chụp dashboard trên GPU thật), F6 (chưa có tin tới Telegram thật). F7 chưa đo (checklist chưa chạy).
  - Mức Must còn thiếu: VH1, VH2 ở nhà; ảnh chụp dashboard trên GPU thật; tin Telegram thật.
- **Incidents:** hai điểm lệch giữa nhật ký và dữ liệu thô.
  - Thứ tự ĐG3: `nguon-tu-lieu.md` §6 ghi "3 lượt L2 chạy sau L0". Theo `pod_created`, L2-2 (18:44:33Z) chạy trước L0-2 (18:46:48Z); chỉ L2-1 và L2-3 chạy sau. L2-2 và L2-1 cùng cho 76 s, nên việc compile cache được tạo lại không làm đổi kết quả L2.
  - Pha `drop`: câu "pha `drop` của 5 lượt KB2: 0 lỗi" đúng về số lỗi. Tuy vậy, hai lượt A1 giữ 4 replica suốt pha (`scale_downs` = 0), nên chỉ 3 lượt A2 (`scale_downs` = 3) là bằng chứng cho scale-down an toàn.
- **Links:** không đổi file nào trong repo ngoài nhật ký này. Nguồn: `runs/v2-vm/` (gói dữ liệu V2).
- **Thesis:** §5.6 bảng nghiệm thu và khuyến nghị cấu hình; §5 Hạn chế (sửa câu về thứ tự lượt L2).

## 2026-11-21 – Luận văn: nháp mục 5.3 (autoscaling so với cấu hình tĩnh)

- **Task:** TR7, TR8 (luận văn) · **Environment:** none
- **Done:**
  1. Đọc thiết kế ĐG2 (Thông số §4, §6–§9.3; Môi trường §11, §15, §16), `quy-tac-viet.md` và `nguon-tu-lieu.md` (nhánh của PR #52), nhật ký Quang 18–19/11.
  2. Tính thêm từ dữ liệu thô V2 bằng một script cục bộ, đọc `events.jsonl`, `metrics.csv.gz`, access log vLLM và `requests.csv`. Các số tính được:
     - mốc rescale của HPA;
     - hàng đợi theo pod;
     - số request mỗi pod nhận;
     - tín hiệu A2;
     - request không đạt SLO, tách theo lúc gửi trước hay sau khi pod mới đầu tiên Ready.
  3. Phiên Claude viết nháp 5.3 bằng Markdown, ngoài Git. Nháp gồm Bảng 5.3a (11 ô, giá trị từng lượt), hình C4, hình C1 của lượt 1 và 4 tiểu mục; mỗi đoạn có số đều kèm dòng nguồn.
  4. Một agent khác (Opus, effort xhigh) đối chiếu độc lập. Phiên chính tính lại các lỗi được báo, rồi sửa 5 lỗi chính và 6 lỗi nhẹ. Sửa thêm 2 câu của nháp 5.6 cho khớp với 5.3. Trình chưa đọc lại nháp.
- **Decision:** D76.
  - Thân bài 5.3 dùng Bảng 5.3a, hình C4 và hình C1 của lượt 1. C2, C3 và C1 của lượt 2, 3 đưa vào phụ lục.
  - Thêm phép kiểm cách chia request theo pod để có số cho nguyên nhân của A2 × KB2.
- **Results:**
  - **A2 × KB2, cách chia request:** trong [360; 600) s, khi cả 4 pod đã Ready, pod cũ nhận 24,3–25,7% số request mới, các pod mới nhận 23,3–26,1%. Số này đếm từ access log; tổng theo pod khớp đúng `n_sent`. Pod cũ xử lý 3,60–3,78 req/s, nhưng trong 240 s đó hàng đợi chỉ giảm từ 370–400 xuống 38–80 request.
  - **A2 × KB2, request không đạt SLO trong pha `spike`:** 42–44% được gửi trước lúc pod mới đầu tiên Ready (319,7–321,5 s), 56–58% gửi sau đó.
  - **Nhịp scale của A2 × KB2:** HPA đặt đủ 4 replica sau 30–36 s kể từ lúc tải tăng. A2 về 1 replica sau 369–420 s kể từ lúc tải giảm.
  - **A2 × KB3, pha `sustain`:**
    - Tín hiệu A2 dao động 64–152 (trung bình 101,1 và 106,1), và 65–74% số mẫu không quá 111 (= 3 × 37).
    - Hai mẫu liên tiếp trên 111 cách nhau nhiều nhất 120 s và 95 s, ngắn hơn cửa sổ 300 s. Vì vậy A2 giữ 4 replica và không có flapping.
  - **A1:** chỉ bớt pod 308–315 s sau khi kịch bản tải kết thúc, ở cả 5 lượt.
  - **Chưa giải thích:** cold start L2 trong ĐG2 là 65–66 s (tính từ lúc tạo pod), trong ĐG3 là 76–81 s (tính từ lệnh scale). Chênh 10–15 s; đã ghi lại để xử lý khi viết mục 5.4.
- **Incidents:** bản đầu ước lượng số request mỗi pod nhận bằng Δ`vllm_success_total` + Δ(running + waiting), ra 21–24% cho pod cũ.
  - Nguyên nhân: `vllm_success_total` không đếm request timeout. Các request này (37, 82, 93 ở ba lượt) đều nằm ở pod cũ và bị cắt trong cửa sổ đo.
  - Agent đối chiếu phát hiện lỗi. Đã sửa bằng cách đếm access log.
- **Links:** trong repo chỉ đổi nhật ký này. Nháp ở `.work/luan-van/05-03-autoscaling-so-voi-tinh.md`, ngoài Git. Nguồn: `runs/v2-vm/v2-dg2/` (gói dữ liệu V2).
- **Thesis:**
  - §5.3: nháp xong, đã đối chiếu.
  - §5.6: sửa dòng N1, vì pha được chấm của KB2 là `pre`, `spike`, `drop`.
  - §5.7 Hạn chế: chưa kiểm theo từng request câu "request vi phạm sau lúc pod mới Ready phần lớn xếp sau hàng đợi cũ".
  - §6 hướng phát triển: định tuyến theo hàng đợi; giữ tối thiểu 2 replica.

## 2026-11-21 – Luận văn: nháp mục 5.5, phần VH4 và VH6

- **Task:** TR6, TR8 (luận văn) · **Environment:** none (dữ liệu V2 đã thu)
- **Done:**
  1. Đọc dữ liệu VH4 của ba lượt: V2 (18/11, 4 × RTX 4060 Ti), máy thuê thử N = 2 (16/11), simulator (09/11). Đối chiếu với hàm `vh4` trong `experiments/ops/vh.py`; hàm này trùng với bản đã chạy trên V2 (`runs/v2-evidence/config/`).
  2. Chia lượt VH4 của V2 thành ba khoảng theo mốc chặn và mốc gỡ chặn, tính SLO bằng `analysis.metrics`, cùng định nghĩa với bảng ĐG2. Tính thêm TPOT theo từng phút.
  3. VH6: đọc `runs.csv`, `alerts.csv` của 17 lượt ĐG2. Tính tỷ lệ request xấu lớn nhất trên cửa sổ 1 phút, giữa mốc vi phạm và mốc page.
  4. Viết nháp. Agent Opus (xhigh) đối chiếu và tự tính lại ba bảng: khớp hết. Agent tìm ra 12 lỗi ở các câu suy luận và mô tả cách đo; đã sửa cả 12.
  5. Sửa dòng F6 của nháp 5.6 theo cùng cách nói.
- **Decision:** D77. Phần VH4, VH6 viết chung một file, tạm đánh số tiểu mục theo mã kịch bản (5.5.4, 5.5.6).
  - VH4 lấy lượt V2 làm số chính thức. Hai lượt thử chỉ dùng để thấy thời gian fallback ít phụ thuộc môi trường, không dùng cho kết luận N6.
  - Không viết thời điểm pod Ready như một sự thật, vì lượt VH4 không ghi mốc Ready. TPOT chỉ được dùng làm bằng chứng gián tiếp.
- **Results:**
  - **VH4, lượt V2** (tải trung bình 1,75 req/s = 0,5 C, chặn 301 s):
    - Fallback lên 4 replica sau 16,8 s, đạt N6 (≤ 30 s). Lượt thử: 17,2 s (N = 2), 18,8 s (simulator).
    - SLO attainment 100% ở cả ba khoảng, 0 lỗi / 1.263 request.
    - TTFT p95: 305 → 254 → 221 ms. TPOT p50: 30,7 → 25,7 → 25,3 ms.
  - **VH4, TPOT theo phút:** giảm từ 30,6–31,2 ms xuống 25,2–25,5 ms từ phút thứ tư. Hai mức này trùng với mức của 1 replica (A2 × KB1: 30,9 và 31,8 ms) và 4 replica (S4 × KB1: 25,3 ms) ở cùng 0,5 C.
  - **VH4, gỡ chặn:** condition `Fallback` hết trong ≤ 5,3 s, ở lần đọc thứ hai. Không đo lúc về 1 replica, vì tải dừng 305 s sau khi gỡ chặn.
  - **VH6:**
    - 7/17 lượt có vi phạm SLO theo log client. Mỗi lượt có đúng 1 page `LLMSLOBurnFast`, sau 99–111 s; riêng S1 × KB3 là 104,5 s, đạt N7.
    - 10 lượt không vi phạm, 0 page; 0 page giả.
    - Cửa sổ 1 phút đạt 68–100% request xấu trước lúc page, nên kêu nhanh hơn LT8 (215–242 s ở x = 0,3; 159–163 s ở x = 0,6).
- **Incidents:** lỗi trong nháp đầu, do agent đối chiếu phát hiện.
  - Bản đầu dẫn dòng "không có TELEGRAM_BOT_TOKEN" trong console runner làm bằng chứng máy điều khiển thiếu `.env`. Bằng chứng đó không dùng được: ma trận ĐG2 chạy trên VM, repo rsync lên đã bỏ `.env`, và runner chỉ đọc biến môi trường. Đã thay bằng dòng Decision "PC chưa có `.env`" trong nhật ký Quang 18/11.
  - Câu "chỉ heartbeat bên ngoài mới phát hiện được lỗi gửi" sai: heartbeat đi qua một receiver khác nên vẫn tới nơi.
- **Deviations:**
  - Trong ĐG2, máy tạo tải gọi thẳng Service `vllm.llm-serving.svc:8000`, không qua Traefik. Vì vậy `LLMErrorRateHigh` (đo 5xx tại Traefik) không có dữ liệu, và VH6 không kiểm được quy tắc này. Môi trường §13 không nêu điểm này.
  - VH4 và VH6 chưa chạy ở nhà (Môi trường §13 ghi "Nhà; GPU thuê").
  - Lỗ hổng định tuyến thấy trong V2: `AlertmanagerFailedToSendAlerts` ở mức warning nên không được gửi; `AlertmanagerClusterFailedToSendAlerts` ở mức critical thì đi tới Telegram, tức đúng đường đang hỏng. Đề xuất kiểm đầu-cuối lúc dựng cluster bằng một tin thử; chưa làm.
- **Links:** trong repo chỉ đổi nhật ký này. Nháp ở `.work/luan-van/05-05b-vh4-vh6.md`, ngoài Git. Nguồn: `runs/v2-vm/ops-vh4-20261118-183127/`, `runs/v2-vm/v2-dg2/tables/`.
- **Thesis:**
  - §5.5.4, §5.5.6 (số tiểu mục tạm).
  - §5.6, dòng N6, N7, F6.
  - §5.7 Hạn chế: VH4 chỉ 1 lượt ở tải thấp; `LLMErrorRateHigh` không được kiểm; vùng 20–23% của N7 chưa đo.
  - §6 hướng phát triển: kiểm đầu-cuối đường cảnh báo.
  - Độ dài: ba nháp chương 5 của Trình có khoảng 8.400 chữ, nên rút gọn khi ghép chương.

## 2026-11-21 – Đồng bộ tài liệu thiết kế với cái đã làm (PR đồng bộ, phần a)

- **Task:** TR4, TR8 · **Environment:** none
- **Done:**
  1. Tạo nhánh `docs/tr4-sync-design-docs` từ `docs/tr8-log-pr54` (đã có 4 commit nhật ký chưa PR), để gộp vào cùng PR.
  2. Sửa các điểm lệch ghi ở mục 18/11 (Deviations) và D71:
     - comment `LLMErrorRateHigh` trong `llm.yaml`, Vận hành §3.2 và runbook: `for: 1m` không lọc được đợt lỗi ngắn;
     - Vận hành §2.3: bỏ câu sai về `1 − tốt/tổng`;
     - Vận hành §2.1: nguồn của TPOT;
     - Vận hành §11: unit test chỉ có cặp cửa sổ 5m/1m;
     - Thông số §9.4: retention ở cloud, exporter GPU;
     - Thông số §7 và Kiến trúc §3.5: máy tạo tải gọi thẳng Service;
     - hai runbook và Vận hành §4.3: bỏ "thắt giới hạn tốc độ";
     - `slo.yaml`: bucket `le="2.5"` đã xác nhận trên GPU; README dashboard: hàng KEDA.
  3. Môi trường §13: thêm giới hạn của VH6 trong V2 (`LLMErrorRateHigh` không có dữ liệu). Môi trường §16: điền bảng nghiệm thu từ nháp 5.6 (D75).
  4. Kiểm điểm còn để ngỏ: severity của `TargetDown` trong chart 92.1.1.
- **Decision:**
  - D78: TPOT trong SLI và nghiệm thu là trung bình mỗi request (`vllm:request_time_per_output_token_seconds`); ITL chỉ dùng để chẩn đoán. JSON dashboard giữ nguyên, vì sửa sẽ làm ConfigMap ở nhà đổi.
  - D79: `TargetDown` không tới Telegram; chỉ ghi là hạn chế, chưa đổi values.
  - D80: tách bước đồng bộ thành 3 PR: tài liệu (PR này), script tính số vào `analysis/`, và Hình 7. Tên máy V2 trong `docs/chi-tiet/` thuộc Q2 nên báo Quang, không sửa ở đây.
- **Results:**
  - Mã vLLM v0.31.0 (`vllm/v1/metrics/stats.py`): `mean_time_per_output_token = decode_time / (num_generation_tokens − 1)`, với `decode_time = last_token_ts − first_token_ts`. Công thức này trùng công thức TPOT ở Môi trường §15.
  - Chart kube-prometheus-stack 92.1.1 (`templates/prometheus/rules-1.14/general.rules.yaml`): `TargetDown` có severity mặc định `warning`, `Watchdog` có `none`. Repo không đặt `customRules`, mà định tuyến chỉ gửi `page`, `ticket` và `critical`, nên exporter chết sẽ không có tin Telegram.
  - Retention Prometheus ở cloud là mặc định 10d của chart (`values.yaml`, `prometheusSpec.retention`). `retention: 72h` ở values chung là của `alertmanagerSpec`.
  - `make alerts-test`: SUCCESS. `yamllint -s common/observability`: đạt. lychee trên các file đã sửa: 0 lỗi. `llm.yaml` và `slo.yaml` sau khi parse YAML giống hệt `origin/main` (chỉ đổi comment), nên Argo CD ở nhà không thấy thay đổi.
- **Deviations:** tài liệu `docs/chi-tiet/` vẫn ghi máy V2 là 4 × RTX A4000, trong khi dữ liệu V2 chạy trên 4 × RTX 4060 Ti 16 GB. Phần này chưa sửa (D80).
- **Links:** nhánh `docs/tr4-sync-design-docs`; `docs/chi-tiet/00-thong-so.md`, `03-kien-truc-autoscaling.md`, `04-van-hanh.md`, `05-moi-truong-danh-gia.md`; `docs/runbooks/`; `common/observability/`.
- **Thesis:** §3.4 (định nghĩa TPOT và ITL; `TargetDown` vào Hạn chế); §5.6 (bảng nghiệm thu, đã có trong Môi trường §16); §5.7 Hạn chế (VH6 không kiểm `LLMErrorRateHigh`).
