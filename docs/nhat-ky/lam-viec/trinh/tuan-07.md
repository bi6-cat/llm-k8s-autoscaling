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
