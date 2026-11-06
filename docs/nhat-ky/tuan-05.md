# Tuần 5 (02–08/11/2026)

## 2026-11-04 – Rà tiến độ, dời V2 sang 14–15/11

**Người quyết định:** Quang và Trình (Trình đồng ý dời V2; Quang ghi lại).

### Tình trạng lúc rà

- Mốc M1 (hạn 18/10) đạt 2/7 mục, M2 (hạn 01/11) đạt 0/8 mục. Chi tiết đã tích ở [Kế hoạch §3](../chi-tiet/06-ke-hoach-quan-ly.md#3-checklist-các-mốc).
- Cluster nhà chỉ có vLLM, device plugin, GPU exporter. Chưa có Prometheus, KEDA, Argo CD.
- Trên `main`: CI (PR #5), cảnh báo + runbook (PR #3), máy tạo tải v1 (PR #4). Phần serving và hạ tầng của Quang chưa có PR.
- V0, V1 chưa diễn ra; chưa có runner.

### Quyết định

| Việc | Quyết định | Lý do |
|---|---|---|
| V2 | Dời từ 07–08/11 sang **14–15/11** | Không có runner, Prometheus, KEDA thì V2 không ra số liệu. Áp dụng dòng "Trễ 1 tuần ở M2" của Kế hoạch §8 |
| V3 dự phòng | Mất | Ngày 14–15/11 đã dùng cho V2 |
| Đóng băng dữ liệu | **22/11**, không lùi thêm | Mức muộn nhất trong kế hoạch gốc |
| Thứ tự làm | **Local trước**: kind + simulator trên máy dev, rồi cluster nhà, rồi mới cloud | Hai môi trường này miễn phí, sửa lỗi ở đây không tốn tiền thuê máy |
| V0, V1 | Gộp thành một phiên ngắn trước V2, dự kiến 11–12/11 | Vẫn cần kiểm VM, driver, runner trên máy thuê trước V2 vì không còn V3 |
| Chọn cloud | Để sau phần local, phải xong trước phiên V0+V1 | Theo ý Quang ngày 04/11 |

Lịch mới ghi ở [Kế hoạch §1.1](../chi-tiet/06-ke-hoach-quan-ly.md#11-điều-chỉnh-ngày-04112026) và [Môi trường §6](../chi-tiet/05-moi-truong-danh-gia.md#6-các-phiên-thuê-gpu).

### Điểm dừng mới

- **07/11:** A2 scale simulator 1 → 3 dưới tải trên kind. Chưa đạt thì cả hai dồn vào việc này, dời Argo CD.
- **10/11:** runner chạy 2 lượt liền không cần can thiệp. Chưa đạt thì V2 giảm số lượt lặp và bỏ KB3 của S1.

### Việc còn treo

- Duyệt hai thay đổi giao diện của Trình: `for: 1m` cho `LLMErrorRateHigh`; cột `id`, `n_in_target` trong `requests.csv`.
- Push `feat/home-k3s`, `feat/tr2-sim`; mở PR A, B, C.
