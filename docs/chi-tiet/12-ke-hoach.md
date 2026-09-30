# 12. Kế hoạch thực hiện: tài liệu chuyên sâu

> Thuộc [Mục 12 của bản mô tả chính](../mo-ta-chi-tiet-do-an.md#12-kế-hoạch-thực-hiện) · [Danh mục tài liệu chuyên sâu](README.md) · Lựa chọn đã chốt: [ADR-001](../adr/001-cac-lua-chon-ban-dau.md)

**Tóm tắt nhanh**
- Kế hoạch **từng tuần** cho 16 tuần, từ **05/10/2026 đến 24/01/2027**. Mỗi tuần ghi rõ việc của Trình, việc của Quang, và **định nghĩa hoàn thành** (DoD).
- Toàn bộ thí nghiệm chính dồn vào **một đợt thuê GPU liên tục khoảng 72 giờ ở tuần T9**, trên cùng một máy (Vast.ai, 4 × RTX 4090). Tuần T8 chạy thử trên VM 1 GPU; tuần T11 dành cho đợt dự phòng nếu cần.
- Có 5 mốc, mỗi mốc có **checklist nghiệm thu**; kèm đường găng, lịch làm việc với GVHD, và **kế hoạch cắt giảm**.

---

## 1. Tổng quan và lịch

![Hình 9 – Kế hoạch 16 tuần](../images/09-ke-hoach-16-tuan.svg)

*Hình 9 (tài liệu chính). Kế hoạch 16 tuần.*

Lịch dưới đây giả định tuần T1 bắt đầu thứ Hai 05/10/2026 và buổi bảo vệ vào cuối tháng 01/2027. **Hai mốc này cần xác nhận** (ADR-001 §6).

| Tuần | Ngày | Tuần | Ngày |
|---|---|---|---|
| T1 | 05/10 – 11/10 | T9 (**đợt thuê chính**) | 30/11 – 06/12 |
| T2 | 12/10 – 18/10 | T10 | 07/12 – 13/12 |
| T3 | 19/10 – 25/10 | T11 (dự phòng) | 14/12 – 20/12 |
| T4 (M1) | 26/10 – 01/11 | T12 (M3) | 21/12 – 27/12 |
| T5 | 02/11 – 08/11 | T13 | 28/12 – 03/01 (có nghỉ Tết Dương lịch) |
| T6 | 09/11 – 15/11 | T14 (M4) | 04/01 – 10/01 |
| T7 | 16/11 – 22/11 | T15 | 11/01 – 17/01 |
| T8 (M2) | 23/11 – 29/11 | T16 (M5) | 18/01 – 24/01 (trước Tết Nguyên đán 06/02/2027) |

---

## 2. Kế hoạch từng tuần

### Giai đoạn 1: Chuẩn bị (T1–T2)

| Tuần | Trình | Quang | Cả nhóm | Định nghĩa hoàn thành |
|---|---|---|---|---|
| T1 | Kiểm tra phần cứng laptop; cài Ubuntu (dual-boot) | Tạo repo, cấu trúc thư mục, GitHub Projects, CI khung | Đọc [04](04-kien-thuc-nen.md); gửi GVHD bản mô tả và ADR-001; xác nhận số laptop, ngôn ngữ luận văn, ngày bảo vệ | GVHD duyệt thiết kế; board có đủ issue cho T2–T4 |
| T2 | Driver, container toolkit, k3s trên laptop 1; pod `nvidia-smi` chạy được | Cài Argo CD, App-of-Apps khung; tạo tài khoản Vast.ai, thử `vastai search offers` theo tiêu chí ADR-001 | **Chốt phiên bản vLLM (digest)** và revision của model | `nvidia.com/gpu: 1` hiện trên node; Argo CD sync được app mẫu; có danh sách máy Vast.ai phù hợp và giá |

### Giai đoạn 2: Xây dựng nền tảng trên laptop (T3–T8)

| Tuần | Trình | Quang | Cả nhóm | Định nghĩa hoàn thành |
|---|---|---|---|---|
| T3 | vLLM 1,5B chạy trên laptop (probe, `/dev/shm`); join laptop 2 | kube-prometheus-stack; PodMonitor vLLM (5 s); exporter GPU (DCGM, hoặc `nvidia_gpu_exporter` nếu DCGM không chạy trên GeForce) | – | Gọi được API; thấy metric vLLM và GPU trong Prometheus |
| T4 | Overlay `laptop`; PVC model-cache; preStop, grace period | Dashboard Serving và GPU; khung Ansible (generic, dùng chung cho laptop và VM thuê) | **Rà soát M1** | **Checklist M1** |
| T5 | ScaledObject A2; bài kiểm thử T1–T3 | Máy tạo tải v1 (Poisson hằng số, sinh prompt theo số token, ghi CSV) | – | A2 scale 1 → 2 trên 2 laptop khi có tải |
| T6 | A1, A3, A4, fallback; bài T4–T6; CPU manager static và pod Guaranteed trên laptop | Profile λ(t) KB1–KB5; kiểm chứng máy tạo tải với `vllm bench serve`; máy tạo tải chạy dạng pod có lõi CPU riêng | – | Mọi ScaledObject qua bài kiểm thử; độ lệch lịch gửi p99 < 50 ms |
| T7 | `parse_vllm_log`; script đo 8 pha cold start | Runner (máy trạng thái), `checks.json`, backup lên R2, **webhook báo động** | **Pilot khối mini** trên laptop | Khối mini chạy trọn không cần can thiệp |
| T8 | Overlay `cloud`; Job prefetch, DaemonSet pre-pull; script burn-in | `make find/rent/burnin/release` (CLI `vastai`); `00_validate`, `01_build_tables`; commit `analysis/PLAN.md` | **Chạy thử trên VM 1 GPU của Vast.ai (~4 giờ)**; nạp tín dụng 150 USD; thống nhất lịch trực đợt chính | **Checklist M2** |

### Giai đoạn 3: Thí nghiệm trên GPU thuê (T9–T13)

| Tuần | Trình | Quang | Cả nhóm | Định nghĩa hoàn thành |
|---|---|---|---|---|
| T9 | Chủ trì **hiệu chỉnh** và **cold start L0/L2** | Vận hành runner và ba khối ma trận; theo dõi backup và số dư | **Đợt thuê chính ~72 giờ liên tục** (ví dụ thứ Năm 03/12 đến Chủ nhật 06/12): burn-in → dựng → hiệu chỉnh (chốt C, SLO, threshold, ghi ADR-002) → cold start → khối 1–3 → chạy lại → backup → huỷ instance | Dữ liệu đợt chính đầy đủ và đã sao lưu; chi phí thực tế đã ghi |
| T10 | Notebook cold start (C6); bắt đầu viết chương 2 | Kiểm tra dữ liệu, `04_matrix` sơ bộ; **quyết định có cần đợt dự phòng không** | Báo cáo sơ bộ cho GVHD | Biết ô nào còn thiếu hoặc hỏng |
| T11 | Viết chương 2 và 3 | (Nếu cần) **đợt dự phòng ≤ 12 giờ**: lượt bổ sung cho các ô trọng tâm, nghiên cứu độ nhạy; thống kê | – | Ma trận đủ theo `PLAN.md` |
| T12 | Hoàn thiện biểu đồ cold start; viết 5.2, 5.4 | Biểu đồ C1–C8; **đóng băng dữ liệu** | **Rà soát M3** | **Checklist M3** |
| T13 | Review chương 4 | Thống kê cuối; viết chương 4, 5.1, 5.3 | Rút ra khuyến nghị | Mọi biểu đồ và bảng của chương 5 đã có |

### Giai đoạn 4: Hoàn thiện (T14–T16)

| Tuần | Trình | Quang | Cả nhóm | Định nghĩa hoàn thành |
|---|---|---|---|---|
| T14 | Viết 1, 6; review chương 4, 5 | Viết 5.5–5.8; review chương 2, 3 | **Bản thảo đầy đủ gửi GVHD** | **Checklist M4** |
| T15 | Kịch bản demo trên cluster laptop | Slide; quay video demo dự phòng | Sửa theo góp ý của GVHD | Slide v1; video demo |
| T16 | Tập demo | Tập trình bày | Tập bảo vệ 2 lần (có người hỏi thử); nộp bản cuối | **Bảo vệ (M5)** |

Việc đưa thí nghiệm lên sớm (T9 thay vì trải qua T9–T12) cho nhóm **thêm khoảng 2 tuần** để phân tích và viết, và vẫn còn đợt dự phòng ở T11.

---

## 3. Checklist nghiệm thu các mốc

### M1 (cuối T4): nền tảng chạy trên laptop
- [ ] Cluster k3s gồm từ 2 laptop trở lên, mỗi node có `nvidia.com/gpu`.
- [ ] vLLM được triển khai **bằng Argo CD** từ overlay `laptop`; gọi được API có streaming.
- [ ] Prometheus có metric vLLM và GPU (5 s); có 2 dashboard (Serving, GPU).
- [ ] Xoá pod thì pod mới tự lên và Ready; preStop hoạt động.
- [ ] Repo có CI chạy xanh.

### M2 (cuối T8): pipeline hoàn chỉnh và chạy thử trên máy thuê
- [ ] A1–A3 (và A4) qua bài kiểm thử T1–T6.
- [ ] Máy tạo tải (pod có lõi CPU riêng) đạt tiêu chí tự kiểm tra; chạy đủ KB1–KB5.
- [ ] Runner chạy trọn một khối mini **không cần can thiệp**; `checks.json` hoạt động; webhook báo động hoạt động.
- [ ] `01_build_tables` tạo được bảng dẫn xuất; notebook vẽ được C1 từ dữ liệu pilot.
- [ ] **Chạy thử trên VM 1 GPU của Vast.ai thành công**: `make rent → burnin → bootstrap → run` (1 lượt) `→ backup → release`, dựng xong trong dưới 30 phút.
- [ ] `analysis/PLAN.md` đã commit; tín dụng ≥ 150 USD; lịch trực đợt chính đã chốt.

### M3 (cuối T12): xong thí nghiệm
- [ ] `calibration.json` đã chốt (C, B\*, SLO, threshold), có ADR-002 đi kèm.
- [ ] Cold start: 5 lần × L0 và L2 hợp lệ.
- [ ] Ma trận: ≥ 90% lượt hợp lệ; các ô trọng tâm đủ số lượt; ghi rõ lượt nào chạy trên máy nào.
- [ ] Toàn bộ dữ liệu đã sao lưu, có checksum; instance đã huỷ; chi phí thực tế đã ghi.

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
WP5 (T3–T6) ─────────────────────────────── ├─► Pilot laptop (T7) ─► Chạy thử 1 GPU (T8) ─► ĐỢT CHÍNH (T9)
WP6 (T5–T6) ─► WP7 runner (T6–T7) ──────── ┘                                                  │
                                                                                               ▼
                       Viết (T10–T15) ◄── Phân tích (T10–T13) ◄── (Đợt dự phòng T11, nếu cần) ◄┘
```

- **Đường găng:** WP1 → WP3 → WP4 → pilot → chạy thử → đợt chính → phân tích → bản thảo.
- **Có thời gian đệm:** WP5 và WP6 chạy song song với WP3 và WP4. Nhờ simulator, WP7 có thể bắt đầu trước khi WP4 xong.
- **Phụ thuộc bên ngoài:** máy trên Vast.ai. Phải **theo dõi giá và số máy phù hợp từ T2**; nếu tới T7 vẫn hiếm máy 4 GPU hỗ trợ VM, chuẩn bị luôn TensorDock hoặc cấu hình 4 × RTX 3090/A5000.

---

## 5. Lịch sử dụng GPU thuê

Chi tiết ở [06 §5](06-moi-truong-chi-phi.md#5-lịch-sử-dụng-gpu-thuê).

| Đợt | Tuần | Thời lượng |
|---|---|---|
| Chạy thử (VM 1 GPU) | T8 | ~4 giờ |
| **Đợt chính** (4 × RTX 4090, cùng một máy) | T9 | ~72–76 giờ liên tục |
| Dự phòng (chỉ khi cần) | T11 | ≤ 12 giờ |

---

## 6. Nhịp làm việc với GVHD

| Buổi | Tuần | Nội dung |
|---|---|---|
| 1 | T1 | Duyệt thiết kế, RQ và ADR-001 |
| 2 | T4 | Demo M1 |
| 3 | T6 | Chiến lược autoscaling và máy tạo tải; góp ý thiết kế thí nghiệm |
| 4 | T8 | Demo M2; duyệt `PLAN.md`, SLO, ngân sách và lịch đợt chính |
| 5 | T10 | Kết quả đợt chính: hiệu chỉnh, cold start, ma trận sơ bộ |
| 6 | T12 | Kết quả M3 |
| 7 | T14 | Nộp bản thảo M4 |
| 8 | T15 | Góp ý bản thảo, duyệt slide |

**Mẫu nội dung mỗi buổi (khoảng 30 phút):** (1) đã làm gì so với kế hoạch; (2) demo hoặc kết quả; (3) rủi ro và vấn đề đang vướng; (4) những điểm cần GVHD quyết định hoặc góp ý; (5) việc cần làm đến buổi sau.

---

## 7. Dự phòng và cắt giảm phạm vi

| Tình huống | Hành động |
|---|---|
| **Trễ 1 tuần** ở M2 | Dời đợt chính sang T10 (vẫn kịp); bỏ A4 và nghiên cứu độ nhạy |
| **Trễ 2 tuần** | Đợt chính ở T11 với ma trận rút gọn ([06 §4.2](06-moi-truong-chi-phi.md#42-dự-toán)); không có đợt dự phòng; không chạy lượt bổ sung |
| **Không tìm được máy 4 × 4090 đạt burn-in** | Nới sang 4 × RTX 3090 hoặc A5000; hoặc chuyển sang TensorDock (chỉ phải viết lại `find/rent/release`) |
| **Máy hỏng giữa đợt chính** | Giữ các khối đã xong. Chạy **trọn** các khối còn lại trên máy mới trong đợt dự phòng. Thiết kế khối giúp so sánh cặp vẫn hợp lệ, vì khác biệt giữa hai máy được hấp thụ vào hiệu ứng khối |
| **Hoàn toàn không thuê được GPU** (kế hoạch Z) | Chạy ma trận trên cluster laptop (model 1,5B, 2–3 replica). Kết luận chỉ mang tính **định tính và cơ chế**; ghi rõ trong phần hạn chế |
| **Một người phải nghỉ 1–2 tuần** | Người còn lại làm tiếp các việc thuộc đường găng; tạm dừng việc viết; báo GVHD |

T15–T16 là **thời gian đệm** của toàn kế hoạch. Chỉ dùng đến khi thật cần, và không lên kế hoạch dùng trước.

---

## 8. Câu hỏi hội đồng có thể đặt ra

**Vì sao dồn toàn bộ thí nghiệm vào một đợt 72 giờ?**
Để mọi số liệu chính đến từ **cùng một máy**, tránh nhiễu do phần cứng khác nhau giữa các lần thuê trên marketplace. Việc dựng cluster và tải image, model cũng chỉ phải làm một lần. Đổi lại, pipeline phải thật ổn định từ trước; điều này được đảm bảo bằng pilot trên laptop (T7) và lần chạy thử trên VM 1 GPU (T8).

**Nếu kết quả hiệu chỉnh cho thấy thiết kế thí nghiệm có vấn đề thì sao?**
Hiệu chỉnh nằm ở đầu đợt chính và cả nhóm theo dõi trực tiếp. Nếu SLO quá dễ hoặc quá khó, nhóm chỉnh **một lần** (ghi ADR-002) trước khi chạy các khối. Nếu vấn đề lộ ra sau khối 1, có đợt dự phòng ở T11.

**Vì sao viết luận văn song song với thí nghiệm?**
Chương 2 và 3 (lý thuyết, thiết kế) không phụ thuộc kết quả, nên viết sớm để giảm áp lực cuối kỳ. Chương 5 chỉ viết sau khi dữ liệu đã đóng băng.
