# Nhật ký quyết định (ADR)

Mỗi quyết định lớn một file `NNN-<ten>.md`, không sửa nội dung cũ; quyết định mới thay thế thì ghi "Thay thế một phần" ở đầu file mới và cập nhật dòng trạng thái của file cũ ([Kế hoạch §7](../chi-tiet/06-ke-hoach-quan-ly.md#7-quy-trình-làm-việc-và-nhịp-với-gvhd)). Quy tắc: giá trị đổi thì sửa ở [Thông số](../chi-tiet/00-thong-so.md) qua PR, và nếu đó là một quyết định thì ghi thêm ADR ([Thông số §1](../chi-tiet/00-thong-so.md#1-quy-tắc-dùng)).

| # | Ngày | Nội dung | Trạng thái |
|---|---|---|---|
| [001](001-cac-lua-chon-ban-dau.md) | 30/09/2026 | 25 lựa chọn ban đầu: Vast.ai 4 × 4090, k3s, KEDA, Argo CD, ma trận 78 lượt | Bị thay một phần bởi 002, 004 |
| [002](002-chuyen-trong-tam-sang-van-hanh.md) | 04/10/2026 | Chuyển trọng tâm sang xây dựng và vận hành (70/30); F1–F7, N1–N8; 28 lượt; VH1–VH6 | Bị thay một phần bởi 004 |
| 003 | (dành) | Kết quả đo năng lực ĐG1 và các giá trị chốt: C, B\*, threshold, ngưỡng N2b, N3 theo N. Viết trong phiên V2 | Chưa viết |
| [004](004-dieu-kien-thuc-te-va-pham-vi-rut-gon.md) | 08/10/2026 | Điều kiện thực tế (hạn 08/12, máy nhà, cloud), phạm vi rút gọn, 17 lượt, kế hoạch 9 tuần; §7 ghi cập nhật tới 06/11 | Bị thay một phần bởi 006 |
| [005](005-sua-thiet-ke-sau-review.md) | 08/10/2026 | 18 sửa thiết kế kỹ thuật sau review: graceful shutdown, rolling update khi 1 replica, ngưỡng TTFT trùng bucket, VH4 bằng NetworkPolicy… | T1 bị thay bởi 006 C8 |
| [006](006-chot-may-model-va-kich-ban-truoc-v2.md) | 10/11/2026 | Chốt trước V2: chỉ còn Vast, máy 4 × A4000, model 3B, N = 4, kịch bản 12/24/17, KEDA timeout, truy vấn A1, chấp nhận grace 180 s; tình trạng phạm vi, lược các hạng mục hội đồng không thấy (12/11) | Đang áp dụng |
