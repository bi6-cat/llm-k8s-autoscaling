# Báo cáo kỹ thuật

[`bao-cao-ky-thuat.html`](bao-cao-ky-thuat.html): báo cáo cho người không trực tiếp làm dự án (giảng viên, hội đồng): kiến trúc, số đo trên 4 × RTX A4000 ngày 08/11/2026, mô phỏng ma trận V2, hướng nâng cấp. Mở bằng trình duyệt; dữ liệu nhúng sẵn trong file.

Mỗi hình mang nhãn nguồn gốc: **đo thật**, **mô phỏng** hoặc **đề xuất**. Số đo là sơ bộ (phiên V0+V1); cập nhật sau phiên V2.

| File | Làm gì |
|---|---|
| `trich_du_lieu.py` | Trích chuỗi thời gian của 2 lượt V1 từ `runs/v1-a4000/` (cần dữ liệu thô trên máy) |
| `mo_phong.py` | Mô phỏng 12 ô ma trận và các bản A2 cải tiến; tham số lấy từ số đo, hiệu chỉnh bằng 2 lượt V1 |

```bash
python3 docs/bao-cao/trich_du_lieu.py . /tmp/v1.json
python3 docs/bao-cao/mo_phong.py . /tmp/sim.json     # ~3 s, 5 seed mỗi ô
```

Các bảng số khác trong báo cáo (benchmark, ĐG1, cold start, graceful shutdown, VH5) chép từ `docs/nhat-ky/van-hanh.md` và log phiên A4000 trong `docs/nhat-ky/lam-viec/quang/`.
