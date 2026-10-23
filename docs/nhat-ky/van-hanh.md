# Nhật ký vận hành

Mỗi kịch bản VH, mỗi sự cố thật và mỗi phiên thuê có một mục: ngày, môi trường, các bước, số đo, runbook đã dùng, chi phí, bài học ([Kế hoạch §10.6](../chi-tiet/06-ke-hoach-quan-ly.md#106-dữ-liệu-đánh-giá-và-nhật-ký-vận-hành)).

## 2026-10-23 – Sự cố: k3s tự thoát khi kéo image vLLM

- **Môi trường:** nhà, PC `zett-ubuntu-pc` (k3s server một node, `v1.36.5+k3s1`, datastore SQLite). Người xử lý: Quang.
- **Triệu chứng:** `k3s crictl pull` image `vllm/vllm-openai:v0.31.0` (~11 GB nén, ~32 GB giải nén) đứt với `error reading from server: EOF`; socket containerd `connection refused`. Hai lần: 11:25:09 (sau 20 phút kéo) và 11:35:52 (sau ~10 phút).
- **Nguyên nhân:** log k3s báo liên tục `Slow SQL` (79 lần trong lần thứ hai), rồi `level=fatal msg="Transaction commit failed: sql: transaction has already been committed or rolled back"` → tiến trình k3s thoát (exit 1), containerd chạy trong k3s nên việc kéo image chết theo. Ổ hệ thống là SSD SATA Colorful SL500 256 GB (`/dev/sda`); giải nén image ghi dồn dập làm ổ nghẽn, SQLite của k3s trên cùng ổ commit không kịp. Không phải thiếu RAM (dmesg không có OOM).
- **Xử lý:** systemd tự khởi động lại k3s mỗi lần (node Ready lại sau < 30 s). Đặt tạm giới hạn ghi cho k3s: `systemctl set-property --runtime k3s.service IOWriteBandwidthMax="/dev/sda 80M"`, kéo lại: xong sau 2 phút 34 giây, 29 lần `Slow SQL` nhưng không `fatal`. Gỡ giới hạn: xoá drop-in trong `/run/systemd/system.control/k3s.service.d/` và ghi `8:0 wbps=max` vào `/sys/fs/cgroup/system.slice/k3s.service/io.max` (chỉ `daemon-reload` thì giới hạn vẫn còn trong cgroup).
- **Số đo:** `NRestarts=2`; tổng thời gian kéo khoảng 33 phút qua ba lần (các lớp đã tải được giữ lại giữa các lần).
- **Runbook đã dùng:** chưa có runbook cho tình huống này.
- **Bài học:** ổ hệ thống của PC là điểm yếu: mọi đợt ghi lớn (kéo image, ghi cache model) có thể làm control-plane chết. Khi kéo image lớn lên node server, giới hạn ghi trước. Hướng lâu dài (chưa quyết): đưa `/var/lib/rancher` hoặc cache model sang NVMe (hiện chứa Windows và phân vùng dữ liệu NTFS), hoặc dùng datastore khác cho k3s. Liên quan rủi ro ở VH5 (dựng lại) và cold start L0 (kéo image trên máy mới).
