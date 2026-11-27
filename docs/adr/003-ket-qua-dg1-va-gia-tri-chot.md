# ADR-003: Kết quả đo năng lực ĐG1 trên V2 và các giá trị chốt

- **Trạng thái:** Đã chấp nhận. G1–G3 và G7 được chốt ngày **18/11/2026**, sau khi ĐG1 xong (16:28 +07) và **trước** lượt đầu tiên của ma trận ĐG2 (16:30 +07), C và target A2 nằm trong khối `x-adr003` của [`matrix-v2.yaml`](../../envs/cloud/experiments/matrix-v2.yaml); B\* nằm trong `capacity.json` do `capacity.py` sinh cùng lúc (console ĐG1 trong `runs/v2-evidence/console/04-…`). Bản ma trận trên VM chưa commit; sha256 của nó trùng bản được commit vào Git ngày 19/11 (`a44ae71`), và console runner in C = 3,5 ngay từ lượt đầu (`runs/v2-evidence/`, không nằm trong Git). G4 (SLO 2,5 s) và G6 (N = 4) là các giá trị có từ trước V2 và đã được dùng nguyên như vậy ngày 18/11; ngày 27/11 chỉ bỏ nhãn *tạm* của G4. G5 được chốt ngày 27/11, với đúng con số đã ghi trước V2. File ADR này được viết ngày 27/11/2026, sau khi đã có kết quả ma trận, để ghi lại các giá trị đó cùng căn cứ; không giá trị nào bị chỉnh sau khi thấy kết quả.
- **Người quyết định:** Quang chạy ĐG1 và chốt G1–G3, G7, G8 trong phiên V2 (Q6, Q2). G4 giữ nguyên giá trị đã có, vì không ai đề xuất chỉnh SLO. G6 đã chốt ở [ADR-006](006-chot-may-model-va-kich-ban-truoc-v2.md) C4; ngày 18/11 chỉ xác nhận máy có đủ 4 GPU. G5 do Trình chốt khi viết ADR này.
- **Thay thế một phần:** [ADR-006](006-chot-may-model-va-kich-ban-truoc-v2.md) C2 (loại máy V2), xem G8.
- **Liên quan:** [Thông số §4, §6, §7, §8](../chi-tiet/00-thong-so.md), [Môi trường §7, §8](../chi-tiet/05-moi-truong-danh-gia.md#8-đg1-đo-năng-lực-một-replica), [Kiến trúc §11](../chi-tiet/03-kien-truc-autoscaling.md#11-chọn-target-từ-kết-quả-đo-năng-lực), [Kế hoạch](../chi-tiet/06-ke-hoach-quan-ly.md) mốc M3 và rủi ro R12, [nhật ký Quang tuần 07](../nhat-ky/lam-viec/quang/tuan-07.md) (18/11, 19/11), [nhật ký vận hành](../nhat-ky/van-hanh.md) (18/11, 19/11). Số liệu: [`envs/cloud/experiments/capacity.json`](../../envs/cloud/experiments/capacity.json), bảng ĐG2 ở [`analysis/figures/v2-dg2/`](../../analysis/figures/v2-dg2/).

## 1. Bối cảnh

Thông số đánh dấu *tạm* các giá trị phụ thuộc máy và model: SLO TTFT, target của A2 và ngưỡng N2b. Theo [Môi trường §7](../chi-tiet/05-moi-truong-danh-gia.md#7-đánh-giá-để-nghiệm-thu), các giá trị này phải được chốt trước khi chạy ma trận và không đổi sau khi đã thấy kết quả. Mọi kịch bản tải tính theo C, nên C cũng phải có trước lượt đầu tiên.

Ngày 18/11, phiên V2 chạy trên VM 4 × RTX 4060 Ti 16 GB (Canada, 61 vCPU), với Qwen2.5-3B-Instruct và image vLLM v0.31.0 đã ghim. Các tham số vLLM được ghi trong `capacity.json`: `--max-num-seqs=64`, `--max-model-len=8192`, `--gpu-memory-utilization=0.90`, tắt prefix caching. ĐG1 chạy bằng [`matrix-dg1-v2.yaml`](../../envs/cloud/experiments/matrix-dg1-v2.yaml): cố định 1 replica (S1), tải hằng (CONST). Mỗi mức có 30 s làm ấm ở 0,3 λ, rồi 300 s ở λ, trong đó bỏ 60 s đầu và đo 240 s. Runner chạy trên PC qua tunnel, với cờ `--no-backup`.

## 2. Kết quả ĐG1

Cả 5 lượt đều hợp lệ. Thứ tự chạy là 2, 3, 4, 5 req/s, sau đó mới thêm mức 3,5.

| λ (req/s) | λ thực (req/s) | Số request đo | Đạt SLO | TTFT p95 | TPOT p95 | B server (Little) | waiting TB | KV-cache |
|---|---|---|---|---|---|---|---|---|
| 2 | 1,95 | 468 | 100 % | 0,314 s | 36,4 ms | 16,4 (16,5) | 0 | 0,062 |
| 3 | 2,98 | 716 | 100 % | 0,454 s | 51,7 ms | 32,7 (32,5) | 0 | 0,124 |
| **3,5** | 3,52 | 844 | **100 %** | 1,216 s | 61,3 ms | **46,3** (46,4) | 0,4 | 0,175 |
| 4 | 4,06 | 975 | 28,5 % | 7,321 s | 64,5 ms | 75,9 (79,0) | 12,4 | 0,240 |
| 5 | 4,93 | 1.183 | 0 % | 69,7 s | 64,3 ms | 232 (291,8) | 168,4 | 0,241 |

Không lượt nào có request lỗi. GPU util trung bình bằng 1,0 ở cả 5 mức, kể cả mức 2 req/s. B server là trung bình `running + waiting` đọc từ metric của vLLM; số trong ngoặc là B tính theo định luật Little (λ thực × E2E trung bình).

## 3. Quyết định

| # | Giá trị | Chốt | Căn cứ |
|---|---|---|---|
| G1 | **C** | **3,5 req/s** | Mức λ lớn nhất còn đạt SLO ≥ 95 % (`capacity.py`: lượt hợp lệ, attainment ≥ 0,95). Ở mức đạt này, attainment là 100 %. Mức kế tiếp, 4 req/s, chỉ đạt 28,5 %, nên năng lực thật nằm trong khoảng [3,5; 4) và C là **cận dưới** (xem §4) |
| G2 | **B\*** | **46,3** | B server tại C. B theo Little bằng 46,4, lệch 0,2 %, trong khi Môi trường §8 bước 6 cho phép lệch tới 15 % |
| G3 | Target A2 | **37** | 0,8 × B\* = 0,8 × 46,31 ≈ 37,05, làm tròn thành 37 ([Thông số §8.1](../chi-tiet/00-thong-so.md#81-các-cấu-hình)). Target A1 giữ 70 % vì không suy từ ĐG1: UTIL\* = 1,0, và util đã bằng 1,0 từ 2 req/s (0,57 C). A3 = 0,8 × KV\* = 0,14, nhưng A3 là mức Could và không chạy |
| G4 | SLO TTFT | **2,5 s**, bỏ nhãn *tạm*. TPOT giữ 100 ms | `le="2.5"` là một biên bucket có thật của v0.31.0 ([Thông số §6](../chi-tiet/00-thong-so.md#6-slo)). Ngưỡng này tách rõ hai mức λ cạnh nhau: tại C, TTFT p95 = 1,216 s và đạt SLO 100 %; ở 4 req/s, TTFT p95 = 7,3 s và chỉ đạt 28,5 %. Như vậy SLO không khiến một replica luôn đạt hoặc luôn trượt, nên không cần dùng quyền chỉnh SLO "một lần" ở Kế hoạch R12. TPOT p95 không quá 64,5 ms ở mọi mức, nên TTFT là ràng buộc quyết định C |
| G5 | Ngưỡng N2b | **Mức tham chiếu 5 phút**. N2b vẫn chỉ báo cáo (Should), không tính đạt hay trượt | Đây là con số "dự kiến ≤ 5 phút" đã ghi ở Thông số §4 từ trước V2 ([ADR-005](005-sua-thiet-ke-sau-review.md) T10). Phương án bị bỏ: (a) bỏ hẳn ngưỡng sau khi thấy số đo vượt, vì như vậy là né kết quả; (b) nâng ngưỡng cho vừa số đo, vì trái Môi trường §7 |
| G6 | N và N3 | **N = 4** (giữ như [ADR-006](006-chot-may-model-va-kich-ban-truoc-v2.md) C4). N3 giữ nguyên định nghĩa | V2 có đủ 4 GPU. Điều khoản viết lại N3 theo N ([ADR-005](005-sua-thiet-ke-sau-review.md) T12, [ADR-006](006-chot-may-model-va-kich-ban-truoc-v2.md) C2(b)) chỉ áp dụng khi N = 2 |
| G7 | Mức tải | KB1 = 0,5 C = **1,75 req/s**. Đỉnh KB2, KB3 = 0,75 × N × C = **10,5 req/s** (3,0 C). Tải nền của VH2–VH4 là 1,75 req/s | Theo [Thông số §7](../chi-tiet/00-thong-so.md#7-kịch-bản-tải). Runner tự tính từ C và N trong `x-adr003`, và `runs.csv` của cả 17 lượt ghi `capacity_rps` = 3,5 |
| G8 | Máy V2 | **4 × RTX 4060 Ti 16 GB** thay cho 4 × A4000 của ADR-006 C2 | Ngày 18/11 không có máy A4000. Máy 4 × 4090 thuê trước đó không lên SSH. Theo `make probe`, máy 4060 Ti vượt tiêu chí CPU và RAM của Thông số §10.2 (61 vCPU, 197 GB), mạng tới Hugging Face đo được 222,3 MB/s, giá 1,5 USD/giờ cả máy, dưới trần 2 USD. Ổ đĩa không đạt: 126 GB (120 GB trống, `runs/v2-evidence/console/00-probe.txt`), dưới mức 130 GB, dù nhật ký 18/11 ghi máy "đạt mọi tiêu chí khác"; tốc độ đọc tuần tự không đo, vì probe chỉ đo tốc độ ghi (972 MB/s). Vì C gắn với máy, G1–G3 chỉ đúng cho máy này (băng thông bộ nhớ 288 GB/s, so với 448 GB/s của A4000, nơi ĐG1 thử ngày 08/11 cho C = 4,5) |

## 4. Chỗ ĐG1 làm khác quy trình

So với [Môi trường §8](../chi-tiet/05-moi-truong-danh-gia.md#8-đg1-đo-năng-lực-một-replica) và [Thông số §8.3](../chi-tiet/00-thong-so.md#83-đg1-và-đg3):

| Quy trình | Thực tế V2 | Ảnh hưởng |
|---|---|---|
| Quét từ 0,5 req/s, bước 0,5; bước 0,25 quanh điểm vi phạm | 5 mức: 2; 3; 3,5; 4; 5. Giữa 3,5 và 4 không có mức nào | C là cận dưới. Tải danh nghĩa x × C bằng khoảng 0,875x đến x lần năng lực thật, nên các kịch bản có thể nhẹ hơn danh nghĩa tới 12,5 % |
| Mỗi mức 1 phút làm ấm, 4 phút đo | 300 s ở λ, bỏ 60 s đầu, đo 240 s. Trước đó runner thêm 30 s làm ấm ở 0,3 λ (console `03-…`, `04-…`) | Khớp quy trình; 30 s ở 0,3 λ không nằm trong cửa sổ đo |
| Dừng khi TTFT p95 vượt 3 lần SLO | Mức 5 req/s có TTFT p95 = 69,7 s | Đúng |
| Bước 7: đối chiếu một mức với `vllm bench serve` | Không có trong dữ liệu phiên (`runs/dg1-v2-4060ti/`, `runs/v2-evidence/`) | **Chưa làm** cho máy V2. Kiểm tra theo Little (G2) chỉ cho thấy B nhất quán với λ thực và E2E, không thay được bước đối chiếu này |
| Không quy định số lượt mỗi mức | Một lượt mỗi mức | Không có khoảng dao động giữa các lượt cho C |
| Giá trị chốt và ADR-003 ghi ngay trong phiên V2, trước ma trận (Môi trường §7, §8) | G1–G4, G6, G7 có trước ma trận (dòng Trạng thái). G5 chốt và ADR này viết ngày 27/11, sau khi đã có kết quả | G5 dùng con số ghi từ trước V2 và không đổi, nhưng thời điểm chốt nằm sau kết quả; ghi vào Hạn chế |

## 5. Kiểm tra sau ma trận (không dùng để chỉnh giá trị)

Kế hoạch R12 lấy dấu hiệu "mọi cấu hình đều > 99 % hoặc đều < 50 %" để nhận ra SLO hoặc C bị chọn sai. Trên 17 lượt ĐG2 không có dấu hiệu đó: S1 đạt 12,5 % ở KB2 và 0 % ở KB3, S4 đạt 100 % ở cả ba kịch bản, A2 × KB2 đạt 79,4–80,7 % ([nhật ký Quang](../nhat-ky/lam-viec/quang/tuan-07.md), 18/11). Thời gian hồi phục N2b của A2 × KB2 là 409–430 s, vượt mức tham chiếu 5 phút của G5. Số này được báo cáo nguyên như vậy.

## 6. Hệ quả

- Các giá trị *tạm* trong [Thông số](../chi-tiet/00-thong-so.md) được thay bằng giá trị chốt ở trên. Sau ADR này, Thông số không còn giá trị nào của V2 mang nhãn *tạm*. Các "target tạm" ở nhà lấy từ ĐG1-mini và không thuộc ADR này.
- Mọi số đo của chương 5 gắn với RTX 4060 Ti và model 3B. Phần Hạn chế ghi: card thay cho A4000, ổ đĩa dưới tiêu chí 130 GB; C là cận dưới với độ phân giải 0,5 req/s; chưa đối chiếu với `vllm bench serve`; ADR này và mức tham chiếu N2b được ghi sau khi đã có kết quả ma trận.
- Target A2 = 37 chỉ dùng cho VM V2. Ở nhà vẫn dùng target 23 từ ĐG1-mini với model 0,5B ([Thông số §8.1](../chi-tiet/00-thong-so.md#81-các-cấu-hình)).
