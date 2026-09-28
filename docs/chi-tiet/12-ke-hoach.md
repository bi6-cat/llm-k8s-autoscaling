# 12. Kế hoạch thực hiện: tài liệu chuyên sâu

> Thuộc [Mục 12 của bản mô tả chính](../mo-ta-chi-tiet-do-an.md#12-kế-hoạch-thực-hiện) · [Danh mục tài liệu chuyên sâu](README.md)

**Tóm tắt nhanh**
- Kế hoạch **từng tuần** cho 16 tuần. Mỗi tuần ghi rõ việc của Trình, việc của Quang, và **định nghĩa hoàn thành** (DoD).
- Có 5 mốc, mỗi mốc có **checklist nghiệm thu** kiểm chứng được.
- Chỉ ra **đường găng**, các phụ thuộc, lịch các phiên thuê GPU, và **kế hoạch cắt giảm** khi trễ 1 tuần, 2 tuần, hoặc khi không thuê được GPU.

---

## 1. Tổng quan

![Hình 9 – Kế hoạch 16 tuần](../images/09-ke-hoach-16-tuan.svg)

*Hình 9 (tài liệu chính). Kế hoạch 16 tuần.*

**Ví dụ quy đổi ra ngày** (nếu tuần T1 bắt đầu thứ Hai 28/09/2026; nhóm tự điều chỉnh theo lịch thật):

| Tuần | Ngày | Tuần | Ngày |
|---|---|---|---|
| T1 | 28/09 – 04/10 | T9 | 23/11 – 29/11 |
| T2 | 05/10 – 11/10 | T10 | 30/11 – 06/12 |
| T3 | 12/10 – 18/10 | T11 | 07/12 – 13/12 |
| T4 (M1) | 19/10 – 25/10 | T12 (M3) | 14/12 – 20/12 |
| T5 | 26/10 – 01/11 | T13 | 21/12 – 27/12 |
| T6 | 02/11 – 08/11 | T14 (M4) | 28/12 – 03/01 (có nghỉ Tết Dương lịch) |
| T7 | 09/11 – 15/11 | T15 | 04/01 – 10/01 |
| T8 (M2) | 16/11 – 22/11 | T16 (M5) | 11/01 – 17/01 |

---

## 2. Kế hoạch từng tuần

### Giai đoạn 1: Chuẩn bị (T1–T2)

| Tuần | Trình | Quang | Cả nhóm | Định nghĩa hoàn thành |
|---|---|---|---|---|
| T1 | Kiểm tra phần cứng laptop; cài Ubuntu (dual-boot) | Tạo repo, cấu trúc thư mục, GitHub Projects, CI khung | Đọc [04](04-kien-thuc-nen.md); chốt RQ và thiết kế; gửi GVHD bản mô tả | GVHD duyệt thiết kế; board có đủ issue cho T2–T4 |
| T2 | Driver, container toolkit, k3s trên laptop 1; pod `nvidia-smi` chạy được | Cài Argo CD, App-of-Apps khung; khảo sát 3–5 nhà cung cấp GPU (bảng so sánh) | Chọn model; dự toán chi phí | `nvidia.com/gpu: 1` hiện trên node; Argo CD sync được một app mẫu |

### Giai đoạn 2: Xây dựng nền tảng trên laptop (T3–T8)

| Tuần | Trình | Quang | Cả nhóm | Định nghĩa hoàn thành |
|---|---|---|---|---|
| T3 | vLLM 1,5B chạy trên laptop (probe, `/dev/shm`); join laptop 2 | kube-prometheus-stack; PodMonitor vLLM (5 s); DCGM exporter | – | Gọi được API; thấy `vllm:num_requests_running` trong Prometheus |
| T4 | Overlay `laptop`; PVC model-cache; preStop, grace period | Dashboard Serving và GPU; khung Terraform + Ansible (generic) | **Rà soát M1** | **Checklist M1** |
| T5 | ScaledObject A2; bài kiểm thử T1–T3 | Máy tạo tải v1 (Poisson hằng số, sinh prompt theo số token, ghi CSV) | – | A2 scale 1 → 2 trên 2 laptop khi có tải |
| T6 | A1, A3, A4, fallback; bài T4–T6 | Profile λ(t) KB1–KB5; kiểm chứng máy tạo tải với `vllm bench serve`; dashboard Autoscaling và Thí nghiệm | – | Mọi ScaledObject qua bài kiểm thử; độ lệch lịch gửi p99 < 50 ms |
| T7 | `parse_vllm_log`; script đo 8 pha cold start | Runner (máy trạng thái), `checks.json`, backup rclone | **Pilot khối mini** trên laptop | Khối mini chạy trọn không cần can thiệp |
| T8 | Chuẩn bị overlay `cloud`; Job prefetch, DaemonSet pre-pull | Hoàn thiện IaC cho nhà cung cấp đã chọn; `00_validate`, `01_build_tables`; commit `analysis/PLAN.md` | Phiên S0 (thử nhà cung cấp), S1 (dựng cluster cloud, pilot 3 lượt) | **Checklist M2** |

### Giai đoạn 3: Thí nghiệm trên GPU thuê (T9–T13)

| Tuần | Trình | Quang | Cả nhóm | Định nghĩa hoàn thành |
|---|---|---|---|---|
| T9 | **S2**: hiệu chỉnh (chủ trì); cold start L0/L1/L2 | Vận hành runner trên cloud, kiểm tra backup | Chốt C, SLO, threshold (ghi ADR) | `calibration.json`, dữ liệu cold start đã sao lưu |
| T10 | Notebook cold start (C6); bắt đầu viết chương 2 | **S3**: khối 1 qua đêm; kiểm tra nhanh dữ liệu khối 1 | Xem kết quả khối 1, sửa lỗi nếu có | Khối 1 hợp lệ ≥ 90% |
| T11 | Viết chương 2 và 3 | **S4**: khối 2 + KB2 × A2 ở L0/L2; **S5**: khối 3; notebook `04_matrix` | – | 3 khối xong |
| T12 | Hoàn thiện biểu đồ cold start | **S6**: chạy lại lượt hỏng và thêm lượt cho các ô trọng tâm; **đóng băng dữ liệu** | **Rà soát M3** | **Checklist M3** |
| T13 | Viết 5.2, 5.4 | Thống kê, C1–C8; viết chương 4, 5.1, 5.3 | Rút ra khuyến nghị | Mọi biểu đồ và bảng của chương 5 đã có |

### Giai đoạn 4: Hoàn thiện (T14–T16)

| Tuần | Trình | Quang | Cả nhóm | Định nghĩa hoàn thành |
|---|---|---|---|---|
| T14 | Viết 1, 6; review chương 4, 5 | Viết 5.5–5.8; review chương 2, 3 | **Bản thảo đầy đủ gửi GVHD** | **Checklist M4** |
| T15 | Kịch bản demo trên cluster laptop | Slide; quay video demo dự phòng | Sửa theo góp ý của GVHD | Slide v1; video demo |
| T16 | Tập demo | Tập trình bày | Tập bảo vệ 2 lần (có người hỏi thử); nộp bản cuối | **Bảo vệ (M5)** |

---

## 3. Checklist nghiệm thu các mốc

### M1 (cuối T4): nền tảng chạy trên laptop
- [ ] Cluster k3s gồm từ 2 laptop trở lên, mỗi node có `nvidia.com/gpu`.
- [ ] vLLM được triển khai **bằng Argo CD** từ overlay `laptop`; gọi được API có streaming.
- [ ] Prometheus có metric vLLM và DCGM (5 s); có 2 dashboard (Serving, GPU).
- [ ] Xoá pod thì pod mới tự lên và Ready; preStop hoạt động.
- [ ] Repo có CI chạy xanh.

### M2 (cuối T8): pipeline hoàn chỉnh và pilot
- [ ] A1–A3 (và A4) qua bài kiểm thử T1–T6.
- [ ] Máy tạo tải đạt tiêu chí tự kiểm tra; chạy đủ KB1–KB5.
- [ ] Runner chạy trọn một khối mini **không cần can thiệp**; `checks.json` hoạt động.
- [ ] `01_build_tables` tạo được bảng dẫn xuất; notebook vẽ được C1 từ dữ liệu pilot.
- [ ] Cluster cloud dựng được bằng `make up && make bootstrap` trong dưới 30 phút.
- [ ] `analysis/PLAN.md` đã commit.

### M3 (cuối T12): xong thí nghiệm
- [ ] `calibration.json` đã chốt (C, B\*, SLO, threshold), có ADR đi kèm.
- [ ] Cold start: 5 lần × L0/L1/L2 hợp lệ.
- [ ] Ma trận: ≥ 90% lượt hợp lệ; các ô trọng tâm đủ số lượt.
- [ ] Toàn bộ dữ liệu đã sao lưu, có checksum; VM đã huỷ; chi phí thực tế đã ghi.

### M4 (cuối T14): bản thảo
- [ ] Đủ 6 chương; mọi hình và bảng có chú thích và được dẫn trong bài.
- [ ] Câu trả lời cho RQ1–RQ3 kèm số liệu và khoảng tin cậy.
- [ ] Có mục "Hạn chế" và "Các mối đe doạ tính hợp lệ".
- [ ] Hai thành viên đã review chéo toàn bộ.

### M5 (T16): bảo vệ
- [ ] Slide (15–20 trang) và bản thuyết trình 15–20 phút.
- [ ] Demo trực tiếp trên cluster laptop; có video dự phòng.
- [ ] Repo gắn tag `v1.0`; README hướng dẫn tái lập.

---

## 4. Đường găng và phụ thuộc

```text
WP1 (T2–T4) ─► WP3 (T3–T4) ─► WP4 (T5–T7) ─┐
WP5 (T3–T6) ─────────────────────────────── ├─► Pilot (T7–T8) ─► S1 cloud (T8) ─► S2 hiệu chỉnh (T9)
WP6 (T5–T6) ─► WP7 runner (T6–T7) ──────── ┘                                              │
                                                                                          ▼
                                   Viết (T10–T15) ◄── Phân tích (T12–T13) ◄── S3–S6 ma trận (T10–T12)
```

- **Đường găng:** WP1 → WP3 → WP4 → Pilot → S1 → S2 → ma trận → phân tích → bản thảo. Trễ ở bất kỳ bước nào trên chuỗi này đều đẩy M3 và M4 lùi lại.
- **Có thời gian đệm:** WP5 và WP6 chạy song song với WP3 và WP4. Nhờ simulator, WP7 có thể bắt đầu trước khi WP4 xong.
- **Phụ thuộc bên ngoài:** GPU thuê. Phải **khảo sát từ T2**, và **thử nhà cung cấp (S0) chậm nhất T7–T8**, để kịp đổi nhà cung cấp nếu cần.

---

## 5. Lịch các phiên thuê GPU

Chi tiết ở [06 §5](06-moi-truong-chi-phi.md#5-lịch-các-phiên-thuê-gpu). Tóm tắt: S0 và S1 ở T8; S2 ở T9; S3 ở T10; S4, S5 ở T11; S6 ở T12.

---

## 6. Nhịp làm việc với GVHD

| Buổi | Tuần | Nội dung |
|---|---|---|
| 1 | T1 | Duyệt thiết kế và RQ (bản mô tả này) |
| 2 | T4 | Demo M1 |
| 3 | T6 | Chiến lược autoscaling và máy tạo tải; góp ý thiết kế thí nghiệm |
| 4 | T8 | Demo M2; duyệt `PLAN.md`, SLO và ngân sách |
| 5 | T10 | Kết quả hiệu chỉnh, cold start, khối 1 |
| 6 | T12 | Kết quả sơ bộ M3 |
| 7 | T14 | Nộp bản thảo M4 |
| 8 | T15 | Góp ý bản thảo, duyệt slide |

**Mẫu nội dung mỗi buổi (khoảng 30 phút):** (1) đã làm gì so với kế hoạch; (2) demo hoặc kết quả; (3) rủi ro và vấn đề đang vướng; (4) những điểm cần GVHD quyết định hoặc góp ý; (5) việc cần làm đến buổi sau.

---

## 7. Dự phòng và cắt giảm phạm vi

| Tình huống | Hành động |
|---|---|
| **Trễ 1 tuần** ở M2 | Bỏ A4, bỏ nghiên cứu độ nhạy, bỏ phát lại trace; chuyển sang ma trận rút gọn ([06 §4.2](06-moi-truong-chi-phi.md#42-dự-toán)) |
| **Trễ 2 tuần** | Như trên, cộng: cold start chỉ đo L0 và L2; S1 chỉ chạy KB1, KB2; KB3 rút còn 20 phút; không chạy thêm lượt cho các ô trọng tâm |
| **Không thuê được GPU phù hợp** (kế hoạch B) | Dùng GPU 16 GB với model 3–4B (phương án C), hoặc 2 × 2 GPU (phương án B) |
| **Hoàn toàn không có cloud** (kế hoạch Z) | Chạy ma trận trên cluster laptop (model 1,5B, 2–3 replica). Kết luận chỉ mang tính **định tính và cơ chế**; ghi rõ trong phần hạn chế |
| **Một người phải nghỉ 1–2 tuần** | Người còn lại làm tiếp các việc thuộc đường găng; tạm dừng việc viết; báo GVHD |

T15–T16 là **thời gian đệm** của toàn kế hoạch. Chỉ dùng đến khi thật cần, và không lên kế hoạch dùng trước.

---

## 8. Câu hỏi hội đồng có thể đặt ra

**Nếu kết quả khối 1 cho thấy thiết kế thí nghiệm có vấn đề thì sao?**
Khối 1 được kiểm tra ngay trong T10. Nếu phát hiện lỗi thiết kế (ví dụ SLO quá dễ hoặc quá khó, target sai), nhóm sửa, ghi ADR, và **chạy lại khối 1**. Đây là lý do tuần T12 có phiên S6 dành cho việc chạy lại.

**Vì sao viết luận văn song song với thí nghiệm?**
Chương 2 và 3 (lý thuyết, thiết kế) không phụ thuộc kết quả, nên viết sớm để giảm áp lực cuối kỳ. Chương 5 chỉ viết sau khi dữ liệu đã đóng băng.
