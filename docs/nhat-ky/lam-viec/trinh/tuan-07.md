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
