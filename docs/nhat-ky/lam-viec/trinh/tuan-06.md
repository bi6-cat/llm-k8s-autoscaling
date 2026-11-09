# Nhật ký làm việc – Trình – Tuần 06 (09–15/11/2026)

## 2026-11-09 – TR2: truy vấn A1 đã sửa (Quang làm thay)

> Mục này do **Quang** ghi vào thư mục của Trình để Trình biết việc đã xong và không làm lại. Trình không tham gia lần sửa này; **Trình cần review**, vì đây là phần TR2 của Trình.

- **Task:** TR2 (Quang làm thay) · **Environment:** none (chưa chạy trên cluster)
- **Done:** đổi query trong `autoscaling/eval/A1.yaml` thành `(sum(avg_over_time(nvidia_smi_utilization_gpu_ratio[15s])) * 100) or vector(0)`; sửa Thông số §8.1, Kiến trúc §13; thêm test.
- **Decision:** handoff ghi "chỉ tính GPU của pod Ready", nhưng exporter không có label pod nên không lọc được. Chọn trung bình 15 s trên từng GPU; chưa chuyển sang dcgm-exporter vì chưa kiểm được trên máy thuê trước V2. Việc này đổi tín hiệu của A1 so với thiết kế, nên cần Trình xem lại.
- **Results:** xem nhật ký Quang tuần 06.
- **Links:** nhánh `fix/a1-transient-gpu-sample`; nhật ký Quang [tuần 06](../quang/tuan-06.md).
