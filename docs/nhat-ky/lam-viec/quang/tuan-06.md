# Nhật ký làm việc – Quang – Tuần 06 (09–15/11/2026)

## 2026-11-09 – Đưa phần dọn dẹp 08/11 vào `main` sau khi PR #27 merge nhầm base

- **Task:** chung · **Environment:** none
- **Done:** rà công việc đầu tuần, phát hiện `main` thiếu 7 commit; tạo `chore/v2-prep-to-main` từ `origin/feat/v2-prep`, gộp `origin/main`; sửa mục nhánh và PR trong `viec-sap-lam.md`.
- **Results:** gộp không conflict. Trên bản gộp: pytest `experiments` 126 passed, `loadgen` 55 passed.
- **Incidents:** PR #27 có base `feat/v2-prep` (xếp chồng trên PR #26). PR #26 merge trước nên PR #27 merge vào nhánh `feat/v2-prep` và GitHub vẫn báo `MERGED`, trong khi `main` thiếu sửa UTIL của `capacity.py`, đồng bộ tài liệu, handoff mới. Cách tránh: trước khi merge PR dưới, đổi base PR trên về `main`, giống bài học PR #24/#25 của Trình.
- **Links:** nhánh `chore/v2-prep-to-main`; PR #26, #27.

## 2026-11-09 – Sửa truy vấn A1 thay Trình (TR2)

- **Task:** TR2 (Quang làm thay, đã ghi ở thư mục Trình) · **Environment:** none
- **Done:** chạy lại tín hiệu A1 trên `metrics.csv.gz` của lượt V1 `A1-KB3-1` với nhiều cửa sổ; đổi query sang `avg_over_time(…[15s])` trên từng GPU trước khi cộng; kiểm PromQL bằng `promtool test rules`.
- **Decision:** không dùng được "chỉ GPU của pod Ready" vì exporter không có label pod. So 4 phương án trên dữ liệu V1, chọn trung bình 15 s: hạ mẫu đơn lẻ mà trễ ít. `min_over_time` cũng hết kẹt nhưng một mẫu thấp đơn lẻ sẽ kéo tụt cả tín hiệu khi tải thật. Không so A1 với cấu hình cũ của 2 lượt V1, vì tín hiệu đã đổi.
- **Results:**
  - Tín hiệu lớn nhất sau tải (14:16 trở đi): gốc 100, avg 15 s 33,3, avg 30 s 16,7, avg 60 s 8,3, min 15 s 0. Với threshold 70, chỉ bản gốc cho desired = 2.
  - Mốc desired 2 / 3 / 4 so với gốc: avg 15 s trễ 10 / 5 / 20 s; avg 30 s trễ 20 / 10 / 20 s; avg 60 s trễ 40 / 20 / 25 s.
  - `promtool` (prom/prometheus v3.5.0, CI dùng 3.15.0): một mẫu 100 % trên một GPU → 33,33; 20 s sau → 0. pytest `experiments` đạt.
  - Chưa đo: chưa chạy query này với KEDA trên cluster nào; lần đầu sẽ là V2. Đây là phép tính lại trên một lượt, tức một lần xuất hiện của lỗi.
- **Deviations:** Thông số §8.1 đổi query. A1 phản ứng chậm hơn tối đa khoảng 20 s so với query cũ.
- **Links:** nhánh `fix/a1-transient-gpu-sample`; `autoscaling/eval/A1.yaml`.
- **Thesis:** §5 (LT6, GPU util là tín hiệu kém: phải làm mượt để tránh một mẫu nhiễu giữ replica).
