# 12. Rủi ro và phương án giảm thiểu: tài liệu chuyên sâu

> Thuộc [Mục 12 của bản mô tả chính](../mo-ta-chi-tiet-do-an.md#12-rủi-ro-và-phương-án-giảm-thiểu) · [Danh mục tài liệu chuyên sâu](README.md)

**Tóm tắt nhanh**
- Rủi ro được chấm theo **khả năng × ảnh hưởng** (mỗi yếu tố từ 1 đến 3), có người theo dõi và được rà soát hằng tuần.
- Sổ đăng ký gồm **22 rủi ro** thuộc 9 nhóm. Mỗi rủi ro có **dấu hiệu sớm**, **biện pháp phòng ngừa** và **kế hoạch B**.
- Phân tích sâu 4 rủi ro đáng chú ý, trong đó có rủi ro **hội đồng đánh giá đồ án thiên về cài đặt**; đặt **ngưỡng cảnh báo ngân sách**, và soạn **runbook xử lý sự cố** trong đợt đánh giá.

---

## 1. Phương pháp

- **Khả năng (K):** 1 thấp · 2 trung bình · 3 cao.
- **Ảnh hưởng (A):** 1 chậm vài ngày · 2 chậm một mốc hoặc giảm chất lượng một phần kết quả · 3 đe doạ việc hoàn thành đồ án.
- **Điểm = K × A.** Từ 6 trở lên là **ưu tiên cao**, phải có kế hoạch B chi tiết.
- Rà soát hằng tuần (5 phút cuối buổi họp nhóm), cập nhật trạng thái trong `docs/rui-ro.md` hoặc trên board.

---

## 2. Sổ đăng ký rủi ro

| ID | Nhóm | Rủi ro | Dấu hiệu sớm | K | A | Điểm | Phòng ngừa | Kế hoạch B | Theo dõi |
|---|---|---|---|---|---|---|---|---|---|
| R1 | Chi phí | Tiền thuê GPU vượt dự toán | Sau đo năng lực (giờ 8 của đợt chính) đã tiêu quá 30% dự toán | 2 | 3 | **6** | Phát triển trên laptop; chạy thử 1 GPU trước; **tín dụng trả trước làm giới hạn cứng**; một đợt liên tục tự động; báo động số dư | Ma trận rút gọn (KB1, KB3 mỗi ô 1 lượt); xin credit hoặc hỗ trợ nội bộ | Quang |
| R2 | Hạ tầng | Không tìm được máy 4 GPU chế độ VM đạt tiêu chí và burn-in | Theo dõi từ T2 thấy ít máy; 3 máy liên tiếp trượt burn-in | 2 | 3 | **6** | Theo dõi giá và số máy từ T2; chỉ phần `find/rent/release` phụ thuộc nhà cung cấp | Nới sang 4 × RTX 3090/A5000; chuyển sang TensorDock | Quang |
| R3 | Hạ tầng | Thuê nhầm máy container (không chạy được K8s) | Không có systemd | 1 | 2 | 2 | Chỉ lọc máy `vms_enabled=true`; chạy thử trên VM 1 GPU ở T8 ([06 §3.4](06-moi-truong-chi-phi.md#34-burn-in-trước-khi-chốt-máy)) | Huỷ, thuê máy khác | Quang |
| R4 | Hạ tầng | Máy lỗi hoặc bị thu hồi giữa đợt chính | Mất kết nối, node NotReady, GPU biến mất | 2 | 2 | 4 | Chỉ thuê on-demand (không interruptible), độ tin cậy ≥ 99%; sao lưu sau mỗi lượt | Giữ các lượt đã xong; chạy các lượt còn lại trên máy mới trong đợt dự phòng T11; ghi rõ lượt nào chạy trên máy nào | Quang |
| R5 | Kỹ thuật | GPU Operator hoặc device plugin khó chạy trên laptop/k3s | Tới cuối T2 vẫn chưa thấy `nvidia.com/gpu` | 2 | 2 | 4 | Theo hướng dẫn k3s; có phương án chỉ cài device plugin | Dùng simulator để phát triển tiếp; dựng GPU sớm trên cloud trong một phiên ngắn | Trình |
| R6 | Kỹ thuật | Cold start quá dài làm autoscaling "vô dụng" ở KB2 | L2 vẫn ≥ 3 phút | 2 | 1 | 2 | Tối ưu L2 | Ghi N2 là "không đạt", dùng số đo 8 pha chỉ ra pha chậm; cân nhắc warm pool (`minReplicaCount: 2`) | Trình |
| R7 | Kỹ thuật | Scale-down hoặc rolling update làm lỗi request | Có lỗi trong VH1 hoặc VH2 trên laptop | 2 | 2 | 4 | preStop, grace period; kiểm thử từ T4 | Tăng preStop; chủ động gỡ pod khỏi Endpoints trước; ghi vào runbook và đo lại | Trình |
| R8 | Kỹ thuật | Tên hoặc ý nghĩa metric vLLM thay đổi | Truy vấn trả rỗng sau khi đổi image | 2 | 1 | 2 | Ghim digest; kiểm tra `/metrics`; hợp đồng giao diện | Cập nhật truy vấn, ghi vào phụ lục | Trình |
| R9 | Đo lường | Máy tạo tải là nút thắt hoặc đo sai | Độ lệch lịch gửi p99 > 50 ms; TTFT lệch với `vllm bench` | 2 | 2 | 4 | Asyncio với lịch sinh trước; tự kiểm tra mọi lượt; đối chiếu công cụ chuẩn | Nhiều tiến trình hoặc nhiều máy; loại lượt hỏng | Quang |
| R10 | Đo lường | Kết quả dao động lớn giữa các lượt, khó nghiệm thu | Năng lực kiểm tra giữa đợt lệch hơn 10%; hai lượt cùng ô chênh nhau nhiều | 2 | 2 | 4 | Cùng một máy; xáo trộn thứ tự; kiểm tra năng lực giữa đợt | Thêm lượt cho ô đó trong phần chạy lại; báo cáo đủ mọi lượt | Quang |
| R11 | Đánh giá | Một yêu cầu N không đạt | Lượt đầu tiên của ô đã cho thấy | 2 | 1 | 2 | Ngưỡng hợp lý, chốt sau đo năng lực | Ghi "không đạt", phân tích nguyên nhân; sửa cấu hình và đo lại nếu còn thời gian | Cả nhóm |
| R12 | Đánh giá | SLO hoặc C chọn sai khiến mọi cấu hình đều "đạt" hoặc đều "trượt" | Vài lượt đầu: mọi cấu hình đều > 99% hoặc < 50% | 1 | 3 | 3 | Đo năng lực kỹ ở đầu đợt chính, cả nhóm theo dõi trực tiếp | Chỉnh SLO hoặc tải **một lần** (ghi ADR-003), chạy lại các lượt đã xong | Trình |
| R13 | Dữ liệu | Mất dữ liệu khi huỷ VM | Backup báo lỗi hoặc thiếu lượt | 1 | 3 | 3 | Backup sau mỗi lượt; `make release` kiểm tra backup trước | Chạy lại (tốn tiền); vì vậy không được bỏ qua bước kiểm tra | Quang |
| R14 | Tiến độ | Bận việc công ty, chậm tiến độ | Hai tuần liên tiếp không đạt DoD | 3 | 2 | **6** | Kế hoạch có thời gian đệm; issue nhỏ; họp tuần | Cắt phạm vi theo [11 §7](11-ke-hoach.md#7-dự-phòng-và-cắt-giảm-phạm-vi) | Cả nhóm |
| R15 | Tiến độ | Phụ thuộc lẫn nhau khiến một người phải chờ người kia | Người này chờ người kia hơn 3 ngày | 2 | 2 | 4 | Hợp đồng giao diện; simulator | Hoán đổi việc trong cùng gói | Cả nhóm |
| R16 | Bảo vệ | Demo hỏng trong buổi bảo vệ | Laptop hoặc mạng không ổn định khi tập | 2 | 2 | 4 | Demo trên cluster laptop (không cần Internet); tập 2 lần | Video demo dự phòng | Trình |
| R17 | Chi phí | Tín dụng về 0 khiến instance bị dừng hoặc **xoá** (mất dữ liệu chưa sao lưu) | Số dư < 30 USD | 1 | 3 | 3 | Nạp dư; runner kiểm tra số dư mỗi giờ và báo động; sao lưu sau mỗi lượt | Nạp thêm ngay; nếu instance đã mất thì chạy lại các lượt chưa sao lưu | Quang |
| R18 | Kỹ thuật | DCGM không chạy trên GPU GeForce | `dcgm-exporter` lỗi hoặc thiếu metric | 2 | 1 | 2 | Thử trên laptop (cũng là GeForce) từ T3 | Dùng `nvidia_gpu_exporter`, đổi truy vấn A1 và cảnh báo GPU | Trình |
| R19 | Đo lường | RTX 4090 giảm xung vì nhiệt giữa đợt | Xung nhịp giảm, nhiệt > 83 °C, TTFT tăng dần | 2 | 2 | 4 | Burn-in kiểm tra nhiệt độ; cảnh báo `GPUTemperatureHigh`; kiểm tra năng lực giữa đợt | Nếu một GPU giảm xung liên tục: dừng, báo cáo; có thể khoá xung nhịp (`nvidia-smi -lgc`) | Trình |
| R20 | Phạm vi | Phần vận hành phình to (thêm Loki, service mesh, nhiều cảnh báo…) | Có issue mới không gắn với yêu cầu F/N nào | 2 | 2 | 4 | Tiêu chí vào/ra phạm vi ([03 §4](03-pham-vi-gia-dinh.md#4-tiêu-chí-vào--ra-phạm-vi-trong-lúc-làm)); Must/Should/Could | Đưa vào hướng mở rộng | Cả nhóm |
| R21 | Bảo vệ | Hội đồng đánh giá đồ án thiên về cài đặt, thiếu chiều sâu | GVHD nhận xét như vậy ở buổi T6 hoặc T8 | 2 | 2 | 4 | Mỗi phần cài đặt gắn với một vấn đề kỹ thuật riêng của GPU/LLM và có số đo; bảng nghiệm thu; chuẩn bị câu trả lời ([02 §10](02-muc-tieu-yeu-cau.md#10-câu-hỏi-hội-đồng-có-thể-đặt-ra)) | Nhấn mạnh hơn phần phân tích trong chương 5 (vì sao A1 không phù hợp, cold start theo pha); thêm A3 nếu còn thời gian | Cả nhóm |
| R22 | Kỹ thuật | Cảnh báo báo giả nhiều, hoặc không bao giờ kêu | Kênh chat bị "spam" khi chạy thử; VH6 không thấy cảnh báo | 2 | 1 | 2 | `promtool test rules` trong CI; ngưỡng trùng biên bucket; rà cảnh báo hằng tuần | Chỉnh ngưỡng hoặc cửa sổ; ghi lý do vào ADR | Quang |

---

## 3. Phân tích sâu các rủi ro đáng chú ý

### R1. Chi phí vượt dự toán
- **Nguyên nhân thường gặp:** sửa lỗi trên cloud thay vì trên laptop; quên tắt VM; chạy lại nhiều vì pipeline chưa ổn định; giá thực tế cao hơn lúc khảo sát.
- **Phòng ngừa:** chỉ lên cloud sau M2 và sau lần chạy thử 1 GPU; tín dụng trả trước là giới hạn cứng (nạp 100 USD); runner báo động khi số dư thấp; một đợt liên tục có kế hoạch theo từng giờ ([06 §5](06-moi-truong-chi-phi.md#5-lịch-sử-dụng-gpu-thuê)); ghi chi phí thực tế sau mỗi nhóm lượt.
- **Kế hoạch B:** ma trận rút gọn (KB1, KB3 mỗi ô 1 lượt); sau đó cắt tiếp theo mức Should và Could.

### R2. Không có GPU phù hợp
- **Phòng ngừa:** theo dõi giá và số máy trên Vast.ai từ T2; chạy thử VM 1 GPU ở T8; chỉ phần `find/rent/release` phụ thuộc nhà cung cấp, còn phần chung (Ansible trở đi) giữ nguyên.
- **Kế hoạch B:** 4 × RTX 3090/A5000, hoặc TensorDock ([06 §3](06-moi-truong-chi-phi.md#3-tầng-2-gpu-thuê-trên-marketplace)). **Kế hoạch Z:** chạy trên laptop, chỉ rút kết luận định tính.

### R21. Hội đồng cho rằng đồ án thiên về cài đặt
- **Vì sao đáng chú ý:** đồ án chủ ý dành khoảng 70% cho xây dựng và vận hành. Nếu trình bày như một danh sách "đã cài X, đã cài Y", hội đồng dễ đánh giá thấp.
- **Phòng ngừa:** trình bày theo cặp **vấn đề → cách xử lý → số đo**. Ví dụ: "rolling update kiểu web bị kẹt khi hết GPU" → "`maxSurge: 0`" → "VH2: cập nhật xong trong X phút, 0 lỗi". Bảng nghiệm thu là xương sống của chương 5. Hỏi GVHD sớm (buổi T6, T8) xem tỷ trọng đã ổn chưa.
- **Kế hoạch B:** tăng phần phân tích trong chương 5 bằng dữ liệu đã có (hành vi của A1, phân rã cold start); thêm A3 (Could) nếu còn thời gian.

### R14. Chậm tiến độ do công việc
- **Phòng ngừa:** chia việc thành issue nhỏ (≤ 2 ngày); DoD rõ cho từng tuần; T15–T16 là thời gian đệm.
- **Kế hoạch B:** cắt phạm vi, **không** lùi M3. Bản thảo có thể thu hẹp chương 5 thay vì trễ hạn nộp.

---

## 4. Ngưỡng cảnh báo ngân sách

| Mức | Chi phí luỹ kế | Hành động |
|---|---|---|
| Xanh | Chi tiêu bám theo dự toán từng giờ của đợt chính | Tiếp tục kế hoạch đầy đủ |
| Vàng | Vượt dự toán 15% ở giờ 15 của đợt chính | Rà soát; chuẩn bị ma trận rút gọn cho các lượt còn lại |
| Đỏ | > 80% dự toán trước khi xong ma trận | Chuyển sang ma trận rút gọn; bỏ A3 và các lượt thêm |
| Dừng | 100% | Dừng thuê; phân tích với dữ liệu hiện có; báo GVHD |

---

## 5. Runbook xử lý sự cố trong đợt đánh giá

Runbook cho các cảnh báo của nền tảng nằm ở `docs/runbooks/` ([08 §4](08-van-hanh.md#4-runbook)). Bảng dưới đây dành cho sự cố của **chính đợt đánh giá** (runner, dữ liệu, máy thuê).

| Sự cố | Nhận biết | Xử lý ngay | Sau đó |
|---|---|---|---|
| Pod vLLM CrashLoopBackOff | Runner thấy pod không Ready sau 15 phút | Xem log (OOM? thiếu `/dev/shm`? sai đường dẫn model?); đánh dấu lượt invalid | Sửa manifest, ghi ADR nếu đổi tham số |
| Node NotReady / GPU biến mất | `kubectl get nodes`; `nvidia-smi` lỗi | Dừng runner; khởi động lại node; kiểm tra lại năng lực | Chạy lại các lượt bị ảnh hưởng ở cuối đợt (hoặc trên máy mới trong đợt dự phòng) |
| Prometheus đầy ổ hoặc ngừng scrape | Khoảng trống scrape > 15 s; lỗi ghi | Tăng dung lượng hoặc giảm retention; khởi động lại Prometheus | Lượt bị ảnh hưởng là invalid |
| Máy tạo tải treo | Không có dòng CSV mới quá 60 s | Runner kill và đánh dấu invalid | Điều tra (hết file descriptor? hết RAM?) |
| KEDA hoặc HPA không scale | `kubectl get hpa`: `<unknown>` metrics | Kiểm tra PromQL, `serverAddress`, label | Sửa và chạy lại |
| Mất SSH tới VM | Không truy cập được | Runner chạy như dịch vụ `systemd` trên chính VM nên vẫn tiếp tục; dữ liệu vẫn được đẩy lên R2 | Kiểm tra lại khi có kết nối |
| Hết ngân sách giữa phiên | Cảnh báo mức Đỏ | Hoàn tất lượt đang chạy, backup, rồi `make down` | Theo §4 |

---

## 6. Câu hỏi hội đồng có thể đặt ra

**Rủi ro lớn nhất của đồ án là gì?**
Là **chi phí và khả năng có GPU** (R1, R2). Hai rủi ro này được giảm bằng chiến lược hai tầng, tự động hoá, và dự toán mới chỉ dùng khoảng một nửa ngân sách. Rủi ro lớn nhất khi bảo vệ là đồ án bị xem là thiên về cài đặt (R21), được giảm bằng cách trình bày theo cặp vấn đề – cách xử lý – số đo.
