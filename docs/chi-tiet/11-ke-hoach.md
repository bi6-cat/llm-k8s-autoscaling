# 11. Kế hoạch thực hiện: tài liệu chuyên sâu

> Thuộc [Mục 11 của bản mô tả chính](../mo-ta-chi-tiet-do-an.md#11-kế-hoạch-thực-hiện) · [Danh mục tài liệu chuyên sâu](README.md) · Lựa chọn đã chốt: [ADR-001](../adr/001-cac-lua-chon-ban-dau.md), [ADR-002](../adr/002-chuyen-trong-tam-sang-van-hanh.md)

**Tóm tắt nhanh**
- Kế hoạch **từng tuần** cho 16 tuần, từ **05/10/2026 đến 24/01/2027**. Mỗi tuần ghi rõ việc của Trình, việc của Quang, và **định nghĩa hoàn thành** (DoD).
- **T2–T8 dành cho xây dựng và vận hành thử trên laptop**: nền tảng, autoscaling, cold start, SLO và cảnh báo, runbook, rolling update, bảo mật, các kịch bản vận hành.
- **Đánh giá trên GPU thuê dồn vào một đợt khoảng 37 giờ ở T9** (Vast.ai, 4 × RTX 4090). T8 chạy thử trên VM 1 GPU; T11 dành cho đợt dự phòng nếu cần.
- Viết luận văn bắt đầu từ **T10**. Chương 3 và 4 không phụ thuộc kết quả đánh giá nên viết trước.

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
| T1 | Thử vLLM bằng Docker trên laptop; đọc tài liệu KEDA | Tạo repo, cấu trúc thư mục, GitHub Projects, CI khung | Cài Ubuntu (dual-boot) trên laptop của mỗi người; đọc [04](04-kien-thuc-nen.md), [08](08-van-hanh.md); gửi GVHD bản mô tả 2.0, ADR-001 và ADR-002; xác nhận số laptop, ngôn ngữ luận văn, ngày bảo vệ | GVHD duyệt hướng đồ án; board có đủ issue cho T2–T4 |
| T2 | Driver NVIDIA, container toolkit trên các laptop; pod `nvidia-smi` chạy được | Ansible dựng k3s (server laptop 1, agent laptop 2); Argo CD, App-of-Apps khung; tài khoản Vast.ai, thử `vastai search offers` | **Chốt phiên bản vLLM (digest)** và revision của model | `nvidia.com/gpu: 1` hiện trên node; Argo CD sync được app mẫu |

### Giai đoạn 2: Xây dựng và vận hành thử trên laptop (T3–T8)

| Tuần | Trình | Quang | Cả nhóm | Định nghĩa hoàn thành |
|---|---|---|---|---|
| T3 | vLLM 1,5B chạy trên laptop (probe, `/dev/shm`); device plugin và exporter GPU trên cả hai node | kube-prometheus-stack; PodMonitor vLLM (5 s); metric Traefik | – | Gọi được API; thấy metric vLLM, GPU và Traefik trong Prometheus |
| T4 | Overlay `laptop`; PVC model-cache; preStop, grace period; `strategy` của Deployment | Dashboard Serving và GPU; khung Ansible (dùng chung cho laptop và VM thuê); CI xanh | **Rà soát M1** | **Checklist M1** |
| T5 | ScaledObject A2; bài kiểm thử T1–T3 | Recording rule SLI; quy tắc cảnh báo v1; Alertmanager → Telegram/Discord; `promtool test rules` trong CI | – | A2 scale 1 → 2 trên 2 laptop khi có tải; một cảnh báo thử tới được kênh chat |
| T6 | A1, A4, fallback; bài kiểm thử T4–T7; script đo 8 pha cold start | Dashboard Autoscaling, SLO và chi phí; mẫu runbook và runbook cho cảnh báo SLO, nền tảng; máy tạo tải v1 | – | Mọi ScaledObject qua bài kiểm thử; mỗi cảnh báo có runbook |
| T7 | Rút ngắn cold start (pre-pull, compile cache); runbook cho cảnh báo GPU, vLLM; thử rolling update khi hết GPU trên laptop | Runner đánh giá; sao lưu lên R2; Sealed Secrets; dashboard chi phí | **Kịch bản vận hành trên laptop**: VH1, VH3 (drain node), VH4, VH6 | Các kịch bản đạt hoặc đã có issue sửa; khối mini của runner chạy trọn không cần can thiệp |
| T8 | Overlay `cloud`; Job prefetch, DaemonSet pre-pull; bảo mật tối thiểu (API key, giới hạn tốc độ, NetworkPolicy) | Hạ tầng cloud: `make find/rent/burnin/bootstrap/release`, Ansible cho VM thuê (NVMe, CPU manager, firewall), script burn-in; Trình dựng lại cluster laptop theo README (VH5) | **Chạy thử trên VM 1 GPU của Vast.ai (~4 giờ)**; nạp tín dụng 100 USD; thống nhất lịch trực đợt chính | **Checklist M2** |

### Giai đoạn 3: Đánh giá trên GPU thuê (T9–T12)

| Tuần | Trình | Quang | Cả nhóm | Định nghĩa hoàn thành |
|---|---|---|---|---|
| T9 | Chủ trì **đo năng lực** và **cold start L0/L2**; VH2, VH3 trên GPU thật | Chủ trì **đợt thuê**: thuê, burn-in, dựng từ máy trắng (VH5), huỷ máy; vận hành runner và ma trận; VH4, VH6; theo dõi sao lưu và số dư | **Đợt thuê chính ~37 giờ liên tục** (ví dụ thứ Sáu 04/12 đến thứ Bảy 05/12): burn-in → dựng từ máy trắng → đo năng lực (chốt C, SLO, threshold, ghi ADR-003) → cold start → ma trận 28 lượt → kịch bản vận hành → chạy lại → sao lưu → huỷ | Dữ liệu đầy đủ và đã sao lưu; chi phí thực tế đã ghi |
| T10 | Biểu đồ cold start (C5), rolling update (C6); bắt đầu viết chương 3 | Script tính bảng mỗi lượt; kiểm tra dữ liệu; biểu đồ C1–C4 sơ bộ; **quyết định có cần đợt dự phòng không**; bắt đầu viết chương 4 | Báo cáo sơ bộ cho GVHD | Biết lượt nào còn thiếu hoặc hỏng |
| T11 | Viết chương 2, phần của mình ở chương 3 và 4 | (Nếu cần) **đợt dự phòng ≤ 8 giờ**; viết chương 4 | – | Mọi ô ma trận đủ số lượt hợp lệ |
| T12 | Viết 5.2, 5.4 | Biểu đồ cuối; bảng nghiệm thu; **đóng băng dữ liệu** | **Rà soát M3** | **Checklist M3** |

### Giai đoạn 4: Hoàn thiện (T13–T16)

| Tuần | Trình | Quang | Cả nhóm | Định nghĩa hoàn thành |
|---|---|---|---|---|
| T13 | Review chương 4, 5 | Viết 5.1, 5.3, 5.5, 5.6 | Rút ra khuyến nghị cấu hình | Mọi biểu đồ và bảng của chương 5 đã có |
| T14 | Viết chương 1, 6 | Review chương 2, 3 | **Bản thảo đầy đủ gửi GVHD** | **Checklist M4** |
| T15 | Kịch bản demo trên cluster laptop | Slide; quay video demo dự phòng | Sửa theo góp ý của GVHD | Slide v1; video demo |
| T16 | Tập demo | Tập trình bày | Tập bảo vệ 2 lần (có người hỏi thử); nộp bản cuối | **Bảo vệ (M5)** |

So với bản 1.0, đợt thuê ngắn hơn (khoảng 37 giờ thay vì 72 giờ) và ma trận nhỏ hơn (28 lượt thay vì 78). Thời gian dôi ra được chuyển vào phần vận hành ở T5–T8 và vào việc viết chương 4.

---

## 3. Checklist nghiệm thu các mốc

### M1 (cuối T4): nền tảng chạy trên laptop
- [ ] Cluster k3s gồm từ 2 laptop trở lên, mỗi node có `nvidia.com/gpu`.
- [ ] vLLM được triển khai **bằng Argo CD** từ overlay `laptop`; gọi được API có streaming.
- [ ] Prometheus có metric vLLM, GPU, Traefik (5 s); có 2 dashboard (Serving, GPU).
- [ ] Xoá pod thì pod mới tự lên và Ready; preStop hoạt động.
- [ ] Repo có CI chạy xanh.

### M2 (cuối T8): nền tảng và vận hành thử đạt trên laptop
- [ ] A1, A2 (và A4) qua bài kiểm thử T1–T7.
- [ ] Đủ năm dashboard; quy tắc cảnh báo có unit test; cảnh báo tới được Telegram/Discord; **mỗi cảnh báo có runbook**.
- [ ] Bảo mật tối thiểu đạt checklist ([08 §8](08-van-hanh.md#8-bảo-mật-tối-thiểu)).
- [ ] VH1, VH3, VH4, VH6 đạt trên laptop; VH2 đã thử trên laptop; người thứ hai dựng được cluster laptop theo README.
- [ ] Máy tạo tải đạt tiêu chí tự kiểm tra; runner chạy trọn một khối mini **không cần can thiệp**; webhook báo động hoạt động.
- [ ] **Chạy thử trên VM 1 GPU của Vast.ai thành công**: `make rent → burnin → bootstrap → run` (1 lượt) `→ backup → release`, dựng xong trong dưới 30 phút.
- [ ] Tín dụng ≥ 100 USD; lịch trực đợt chính đã chốt.

### M3 (cuối T12): xong đánh giá
- [ ] `capacity.json` đã chốt (C, B\*, SLO, threshold), có ADR-003 đi kèm.
- [ ] Cold start: 3 lần × L0 và L2 hợp lệ.
- [ ] Ma trận: mọi ô đủ số lượt hợp lệ.
- [ ] VH1–VH6 có kết quả trên môi trường tương ứng.
- [ ] Bảng nghiệm thu đã điền đủ.
- [ ] Toàn bộ dữ liệu đã sao lưu, có checksum; instance đã huỷ; chi phí thực tế đã ghi.

### M4 (cuối T14): bản thảo
- [ ] Đủ 6 chương; mọi hình và bảng có chú thích và được dẫn trong bài.
- [ ] Bảng nghiệm thu kèm số liệu cho mọi yêu cầu F1–F7, N1–N8.
- [ ] Có mục "Hạn chế".
- [ ] Hai thành viên đã review chéo toàn bộ.

### M5 (T16): bảo vệ
- [ ] Slide (15–20 trang) và bản thuyết trình 15–20 phút.
- [ ] Demo trực tiếp trên cluster laptop (autoscaling, cảnh báo, runbook); có video dự phòng.
- [ ] Repo gắn tag `v1.0`; README hướng dẫn tái lập.

---

## 4. Đường găng và phụ thuộc

```text
WP1 (T2–T4) ─► WP3 (T3–T7) ─► WP4 (T5–T6) ─┐
WP2 (T1–T8) ─► WP5 (T3–T6) ─► WP6 (T6–T8) ─┼─► Vận hành thử trên laptop (T7) ─► Chạy thử 1 GPU (T8) ─► ĐỢT CHÍNH (T9)
WP7 runner (T6–T7) ─────────────────────── ┘                                                          │
                                                                                                       ▼
                         Viết (T10–T15) ◄── Xử lý số liệu (T10–T12) ◄── (Đợt dự phòng T11, nếu cần) ◄──┘
```

- **Đường găng:** WP1 → WP3 → WP4 → vận hành thử → chạy thử → đợt chính → xử lý số liệu → bản thảo.
- **Có thời gian đệm:** WP5 và WP6 chạy song song với WP3 và WP4. Nhờ simulator, dashboard, cảnh báo và runner có thể làm trước khi vLLM thật xong.
- **Phụ thuộc bên ngoài:** máy trên Vast.ai. Phải **theo dõi giá và số máy phù hợp từ T2**; nếu tới T7 vẫn hiếm máy 4 GPU hỗ trợ VM, chuẩn bị luôn TensorDock hoặc cấu hình 4 × RTX 3090/A5000.

---

## 5. Lịch sử dụng GPU thuê

Chi tiết ở [06 §5](06-moi-truong-chi-phi.md#5-lịch-sử-dụng-gpu-thuê).

| Đợt | Tuần | Thời lượng |
|---|---|---|
| Chạy thử (VM 1 GPU) | T8 | ~4 giờ |
| **Đợt chính** (4 × RTX 4090, cùng một máy) | T9 | ~37 giờ liên tục |
| Dự phòng (chỉ khi cần) | T11 | ≤ 8 giờ |

---

## 6. Nhịp làm việc với GVHD

| Buổi | Tuần | Nội dung |
|---|---|---|
| 1 | T1 | Duyệt hướng đồ án (bản mô tả 2.0), yêu cầu F/N, ADR-001 và ADR-002 |
| 2 | T4 | Demo M1 |
| 3 | T6 | Autoscaling, SLO và cảnh báo; góp ý danh sách kịch bản vận hành |
| 4 | T8 | Demo M2 (gồm một lần cảnh báo và xử lý theo runbook); duyệt kế hoạch đợt chính và ngân sách |
| 5 | T10 | Kết quả đợt chính: năng lực, cold start, ma trận sơ bộ, kịch bản vận hành |
| 6 | T12 | Kết quả M3: bảng nghiệm thu |
| 7 | T14 | Nộp bản thảo M4 |
| 8 | T15 | Góp ý bản thảo, duyệt slide |

**Mẫu nội dung mỗi buổi (khoảng 30 phút):** (1) đã làm gì so với kế hoạch; (2) demo hoặc kết quả; (3) rủi ro và vấn đề đang vướng; (4) những điểm cần GVHD quyết định hoặc góp ý; (5) việc cần làm đến buổi sau.

---

## 7. Dự phòng và cắt giảm phạm vi

| Tình huống | Hành động |
|---|---|
| **Trễ 1 tuần** ở M2 | Dời đợt chính sang T10 (vẫn kịp); bỏ các mục Could (A3, A4) |
| **Trễ 2 tuần** | Đợt chính ở T11; bỏ VH2 trên GPU thật (giữ kết quả trên laptop); KB1 và KB3 chỉ chạy 1 lượt mỗi ô |
| **Không tìm được máy 4 × 4090 đạt burn-in** | Nới sang 4 × RTX 3090 hoặc A5000; hoặc chuyển sang TensorDock (chỉ phải viết lại `find/rent/release`) |
| **Máy hỏng giữa đợt chính** | Giữ các lượt đã xong; chạy các lượt còn lại trên máy mới trong đợt dự phòng; ghi rõ lượt nào chạy trên máy nào |
| **Hoàn toàn không thuê được GPU** (kế hoạch Z) | Chạy ma trận trên cluster laptop (model 1,5B, 2–3 replica). Phần vận hành gần như không bị ảnh hưởng; số liệu hiệu năng chỉ mang tính minh hoạ và được ghi trong phần hạn chế |
| **Một người phải nghỉ 1–2 tuần** | Người còn lại làm tiếp các việc thuộc đường găng; tạm dừng việc viết; báo GVHD |

T15–T16 là **thời gian đệm** của toàn kế hoạch. Chỉ dùng đến khi thật cần, và không lên kế hoạch dùng trước.

---

## 8. Câu hỏi hội đồng có thể đặt ra

**Vì sao dồn toàn bộ phần đánh giá trên GPU thuê vào một đợt?**
Để mọi số liệu chính đến từ **cùng một máy**, và chỉ phải dựng cluster, tải image và model một lần. Đổi lại, nền tảng phải thật ổn định từ trước; điều này được đảm bảo bằng phần vận hành thử trên laptop (T7) và lần chạy thử trên VM 1 GPU (T8). Đợt chính cũng là dịp chạy thử chính quy trình trực và runbook của nền tảng.

**Nếu kết quả đo năng lực cho thấy SLO quá dễ hoặc quá khó thì sao?**
Đo năng lực nằm ở đầu đợt chính và cả nhóm theo dõi trực tiếp. Nếu cần, nhóm chỉnh SLO **một lần** (ghi ADR-003) trước khi chạy ma trận.

**Vì sao viết luận văn song song với xử lý số liệu?**
Chương 2, 3 và 4 (lý thuyết, thiết kế, triển khai và vận hành) không phụ thuộc kết quả đánh giá, nên viết sớm để giảm áp lực cuối kỳ. Chương 5 chỉ viết sau khi dữ liệu đã đóng băng.
