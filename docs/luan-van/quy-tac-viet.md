<!-- Mục đích: quy tắc viết chung cho hai người (cấu trúc, văn phong, thuật ngữ, trình bày kết quả, phối hợp) để luận văn đọc như một người viết. Người viết: Quang; sửa qua PR, người kia review. File không ghép vào .docx. -->
# Quy tắc viết luận văn

File này bổ sung cho [README.md](README.md). README quy định phần kỹ thuật: tổ chức file, định dạng số, cách đánh số hình và bảng, trích dẫn, comment nguồn. File này quy định **viết thế nào** để hai người viết thống nhất: chương nào nói gì, văn phong, thuật ngữ, cách trình bày kết quả, cách review. Nguồn tư liệu cho từng mục ở [nguon-tu-lieu.md](nguon-tu-lieu.md).

Thứ tự ưu tiên khi hai quy định khác nhau:
1. Khuôn và quy định trình bày của trường. **Chưa có**; khi nhận được thì ghi vào §1 và sửa file này.
2. README.
3. File này.

## 1. Khuôn trình bày

Chưa có khuôn của trường. Đến khi có, viết theo các thông lệ phổ biến của đồ án tốt nghiệp kỹ thuật dưới đây. Phần định dạng (phông, lề, giãn dòng) áp ở bước ghép bằng `--reference-doc`, nên **không định dạng tay trong Markdown**.

| Mục | Thông lệ tạm dùng | Ghi chú |
|---|---|---|
| Độ dài | 55–65 trang thân bài (Kế hoạch §11.1) | Không tính phụ lục |
| Phông, cỡ, giãn dòng, lề | Áp theo khuôn của trường | Chờ khuôn |
| Cấp tiêu đề | Tối đa 3 cấp số: `3.4.1.` | Cần chia nhỏ hơn thì dùng đoạn mở bằng cụm in đậm |
| Trích dẫn | IEEE, đánh số `[1]` theo thứ tự xuất hiện | Pandoc tự đánh số qua `[@key]` |

Thứ tự các phần của quyển (tên file dự kiến ở khung luận văn, chưa dựng):
1. Bìa, nhiệm vụ đồ án: theo mẫu của trường.
2. Lời cam đoan, lời cảm ơn.
3. Tóm tắt tiếng Việt và *Abstract*: mỗi bản khoảng 1 trang.
4. Mục lục, danh mục hình, danh mục bảng, danh mục chữ viết tắt.
5. Chương 1–6.
6. Tài liệu tham khảo, phụ lục.

Tóm tắt viết **sau cùng**. Tóm tắt phải nêu bài toán, cách làm, môi trường đo, và **2–3 kết quả chính có số** (ví dụ GPU-giờ của A2 so với S4). Không viết chung chung kiểu "đã xây dựng thành công hệ thống".

## 2. Mỗi chương nói gì

Mỗi sự kiện chỉ được trình bày **đầy đủ ở một chỗ**; ở chỗ khác thì dẫn chéo "(mục 4.5)". Chương nào nói gì:

| Chương | Trả lời câu hỏi | Không đặt ở đây |
|---|---|---|
| 1 | Vì sao bài toán đáng làm, mục tiêu, đóng góp, phạm vi | Chi tiết kỹ thuật, số đo |
| 2 | Kiến thức chung mà người đọc cần để hiểu các chương sau (LLM inference, vLLM, autoscaling, SLO, GitOps), và giải pháp liên quan | Bất cứ gì về hệ thống của nhóm |
| 3 | Hệ thống **cần** gì và **được thiết kế** thế nào, vì sao chọn phương án đó | "Đã cài", lệnh, sự cố |
| 4 | **Đã làm** thế nào, gặp gì, lệch thiết kế ở đâu, kiểm chứng ra sao | Bảng kết quả đánh giá (để chương 5) |
| 5 | Số đo, giải thích, so với chỉ tiêu, hạn chế của phép đo | Lặp lại cách cài đặt |
| 6 | Tổng kết, hạn chế chính, hướng phát triển | Kết quả mới chưa nêu ở chương 5 |

**Khung của một chương:**
- **Đoạn mở đầu chương:** 3–5 câu, nói chương trả lời câu hỏi gì và gồm các mục nào. Đoạn này nằm ở file `CC-00-<ten>.md`.
- **Mỗi mục cấp 2:** mở bằng 1–2 câu nói mục giải quyết việc gì.
- **Mục cuối "Kết chương":** 1 đoạn, nói chương rút ra điều gì và dẫn sang chương sau.

Cách chia tiểu mục:
- Không để một mục chỉ có một tiểu mục: đã có 3.4.1 thì phải có 3.4.2.
- Không đặt hai tiêu đề liền nhau mà không có đoạn văn ở giữa.
- Không kết thúc một mục bằng hình hay bảng; sau hình hoặc bảng phải có ít nhất một câu nhận xét.

### 2.1. Chương 4 không được là "nhật ký cài đặt"

Rủi ro R21 của kế hoạch là hội đồng xem đồ án thiên về cài đặt. Vì vậy mỗi mục của chương 4 đi theo khung sáu bước:

1. **Vấn đề:** phần này phải giải quyết gì, khó ở đâu (với GPU, với LLM).
2. **Lựa chọn và lý do:** chọn gì, bỏ phương án nào, vì sao. Dẫn ADR bằng nội dung, không dẫn bằng số ADR.
3. **Cách làm:** vừa đủ để người khác làm lại được. Lệnh và YAML dài đưa vào phụ lục.
4. **Kiểm chứng:** bằng chứng là nó chạy đúng, có số. Chi tiết số để chương 5; ở đây chỉ nêu kết quả kiểm.
5. **Sự cố và điểm lệch:** triệu chứng → nguyên nhân → cách sửa. Đây là phần cho thấy năng lực vận hành, nên đừng cắt.
6. **Bài học hoặc khuyến nghị:** 1–2 câu.

## 3. Văn phong

- **Ngôi:** dùng ngôi thứ ba: "nhóm", "đồ án", "hệ thống". Chỉ lời cảm ơn được dùng "chúng em".
- **Câu:** câu ngắn, mỗi câu một ý. Đoạn văn 3–7 câu và có câu chủ đề ở đầu.
- **Không dùng văn nói:** không viết "khá", "rất nhiều", "cực kỳ", "ổn", "ngon", "chạy ngon", "khủng". Thay bằng số: "nhanh hơn 4 lần" thay cho "nhanh hơn rất nhiều".
- **Không cảm thán, không câu hỏi tu từ, không "ta thấy rằng".** Cần nêu nhận xét thì viết "Kết quả cho thấy…".
- **Thì:** thiết kế viết ở thì hiện tại ("A2 đọc tổng số request đang chạy và đang chờ"); việc đã làm và đã đo viết như sự kiện, có điều kiện đo ("Trong phiên đo V2, A2 dùng 25% GPU-giờ so với S4").
- **Mức chắc chắn:** ba mức dưới đây phải viết khác nhau, và không trộn trong một câu.

  | Mức | Viết là |
  |---|---|
  | Đo được | "đo được", "kết quả cho thấy" |
  | Suy ra từ số đo | "từ đó suy ra", "nhiều khả năng" |
  | Chưa kiểm | "giả thuyết của nhóm là … (chưa kiểm chứng)" |

- **Không phóng đại:**
  - Không dùng "tối ưu", "hoàn hảo", "luôn luôn", "chứng minh" khi chỉ có 1–3 lượt đo. Dùng "trong điều kiện đo, …".
  - Không viết "giảm chi phí 75%" trống trơn. Viết "giảm 75% GPU-giờ so với S4 ở kịch bản KB1".
- **Kết quả xấu là kết quả:** ví dụ A2 không đạt SLO dưới tải tăng đột ngột (KB2). Trình bày như một phát hiện: có số, có nguyên nhân, có hướng khắc phục; không giấu, không xin lỗi.
- **Không nhắc chuyện nội bộ trong thân bài:**
  - mã việc (Q6, TR7), số PR, commit, quyết định D68;
  - tên người, "nhật ký", "phiên Claude";
  - đường dẫn `docs/`.
  - Những thứ này chỉ nằm trong comment nguồn. Ngoại lệ: mục phân công ở slide.

## 4. Thuật ngữ và tên gọi thống nhất

**Quy tắc chung (theo AGENTS.md):**
- Câu viết tiếng Việt; thuật ngữ chuyên ngành giữ tiếng Anh, không Việt hoá.
- Lần đầu một thuật ngữ xuất hiện **trong cả quyển**: ghi nghĩa tiếng Việt, kèm tiếng Anh in nghiêng và chữ viết tắt (README). Từ đó trở đi chỉ dùng một dạng ở bảng dưới.
- Mọi chữ viết tắt vào danh mục chữ viết tắt.
- Muốn thêm hay đổi một dòng ở bảng này thì sửa qua PR, không tự đặt tên riêng.

| Dùng | Lần đầu giải thích | Không dùng |
|---|---|---|
| autoscaling | tự động điều chỉnh số replica theo tải | auto-scale, tự scale, co giãn tự động (trừ lần đầu) |
| scale-up, scale-down (danh từ); "scale lên 4 replica" (động từ) | | tăng/giảm quy mô |
| replica | một bản sao pod vLLM, mỗi bản dùng 1 GPU | bản sao, instance |
| GPU replica | một phần GPU chia bằng time-slicing (chỉ ở máy nhà) | GPU ảo |
| request | | yêu cầu, truy vấn |
| model (LLM) | | mô hình (dành cho mô hình toán, mô hình hàng đợi) |
| cold start | thời gian từ khi tạo pod tới khi pod phục vụ được | khởi động nguội |
| graceful shutdown | tắt pod mà không cắt request đang xử lý | tắt êm |
| rolling update | | cập nhật cuốn chiếu |
| threshold | | ngưỡng (được dùng trong câu thường, ví dụ "ngưỡng 1%", nhưng tham số của ScaledObject gọi là threshold) |
| SLO attainment | tỷ lệ request đạt SLO | độ đạt SLO |
| TTFT, TPOT, p95 | xem README; p95 = phân vị 95 | |
| burn rate, error budget (ngân sách lỗi) | | |
| page, ticket | hai mức cảnh báo (gọi người trực ngay / xử lý trong giờ làm việc) | |
| GPU-giờ | số GPU bị giữ nhân thời gian giữ | giờ GPU |
| máy tạo tải | chương trình sinh request theo lịch (*load generator*) | load generator (trừ lần đầu) |
| runner | chương trình chạy tự động các lượt đánh giá | |
| lượt (đánh giá) | một lần chạy một cấu hình với một kịch bản tải | run, lần chạy |
| phiên đo | một lần thuê máy và chạy loạt lượt (V0, V1, V2) | session |
| máy nhà; VM thuê | PC RTX 5060; VM Vast.ai | máy local, máy cloud |

**Tên sản phẩm** viết đúng chữ hoa, chữ thường như sau:
- Kubernetes (chữ K8s chỉ dùng trong bảng), k3s, kind, vLLM, KEDA, Prometheus, Grafana, Alertmanager.
- Argo CD, Kustomize, Helm, Ansible, GitHub Actions, Vast.ai, NVIDIA, Telegram.
- Model: Qwen2.5-3B-Instruct ở lần đầu, sau đó "model 3B".
- GPU: "RTX 4060 Ti 16 GB"; cụm máy viết "4 × RTX 4060 Ti".

**Tên resource Kubernetes:**
- Viết hoa theo kind khi nói đúng loại object: Deployment, Service, ScaledObject, PodMonitor, NetworkPolicy.
- Viết thường khi nói chung: pod, node, cluster.

**Mã định danh của đồ án:**
- Định nghĩa ở chương 3, gom vào một bảng, và vào danh mục chữ viết tắt. Từ chương 4 trở đi được dùng thẳng.

  | Mã | Nghĩa |
  |---|---|
  | S1, S4 | cấu hình tĩnh 1 và N replica |
  | A1–A4 | cấu hình autoscaling |
  | KB1–KB3 | ba kịch bản tải |
  | ĐG1–ĐG3 | ba đánh giá: năng lực, autoscaling, cold start |
  | VH1–VH6 | kịch bản vận hành |
  | LT1–LT8 | kiểm chứng lý thuyết |
  | L0, L2 | mức cold start |
  | F1–F7, N1–N8 | yêu cầu chức năng, chỉ tiêu nghiệm thu |
  | V0–V2 | các phiên đo |

- Ô ma trận viết "A2 × KB2".
- Mã C1–C6 của tài liệu thiết kế là tên nội bộ của biểu đồ. Trong bài dùng số hình ("Hình 5.3"), không viết "C1", vì C đã là ký hiệu năng lực.
- **Ký hiệu:** C = năng lực một replica (req/s); B\* = số request đồng thời ở mức năng lực; λ = tốc độ đến (req/s); N = số GPU ("N = 4"). Không dùng lại các chữ này cho nghĩa khác.

## 5. Trình bày số liệu và kết quả

- **Số nào cũng có điều kiện đo**, ghi ở câu đó hoặc ở chú thích bảng: máy, model, tải, số lượt. Điều kiện chung của cả chương ghi một lần ở mục 5.1, các chỗ sau dẫn chéo.
- **Độ chính xác:** giữ đúng độ chính xác của nguồn, không thêm chữ số. Khi lấy trung bình mà chỉ có 3 lượt trở xuống thì ghi cả giá trị từng lượt: "77,7 s (3 lượt: 76; 76; 81 s)".
- **Khoảng giá trị:** "80–82 s" (gạch ngang ngắn, không cách). Phép nhân: "4 × RTX 4060 Ti". Đẳng thức: "λ = 3,5 req/s" (có cách hai bên).
- **Đơn vị:** s, ms, phút (không viết "min"), req/s, GB hoặc GiB đúng như nguồn, USD. Phần trăm và mọi định dạng số khác: theo README.
- **Nhãn nguồn gốc:** số nào không phải đo thật thì gắn nhãn ngay cạnh:
  - "(mô phỏng)": ví dụ phần mô phỏng ma trận;
  - "(ước tính)": ví dụ giá thuê theo giờ;
  - "(đề xuất, chưa thực hiện)": ví dụ phần V3.
  - Số mô phỏng và số đề xuất chỉ xuất hiện ở chương 6 hoặc trong mục có tiêu đề nói rõ.
- **So với chỉ tiêu:** khi nêu kết quả của một chỉ tiêu (N1…N8), nêu theo thứ tự: chỉ tiêu, số đo, đạt/không đạt, rồi lý do nếu không đạt. Bảng nghiệm thu tổng hợp lại đúng các câu đó, không có số mới.
- **Mỗi bảng hoặc hình kết quả có một câu nhận xét chính** đứng ngay sau, nói điều người đọc cần thấy. Không chỉ viết "kết quả ở Bảng 5.2".
- **Hạn chế của phép đo** gom vào mục Hạn chế ở chương 5 (danh sách ở `nguon-tu-lieu.md` §6). Chương 6 chỉ nhắc lại các hạn chế lớn nhất.

## 6. Hình, bảng, mã nguồn

Đánh số và đặt chú thích theo README. Thêm:

- **Hình:**
  - Chú thích tự đủ nghĩa, đọc được mà không cần thân bài.
  - Hình phải được nhắc trong bài **trước** khi xuất hiện.
  - Chữ trong hình bằng tiếng Việt; trục có tên và đơn vị.
  - Hình lấy từ tài liệu khác thì ghi "Nguồn: [@key]" cuối chú thích; hình nhóm tự vẽ thì không ghi.
  - Hình minh hoạ không phải số thật thì ghi "(minh hoạ)" trong chú thích.
- **Ảnh chụp màn hình:** chỉ dùng cho dashboard, tin cảnh báo thật và giao diện. Chú thích ghi môi trường và thời điểm chụp. Không chụp terminal; cần thì chép output thành bảng hoặc đoạn mã.
- **Bảng:** không quá khoảng 7 cột. Ô trống ghi "–" và giải thích nghĩa của "–" ở chú thích.
- **Mã nguồn và cấu hình:**
  - Thân bài chỉ trích đoạn ngắn (khoảng 15 dòng trở xuống), có tiêu đề "**Đoạn mã 4.1.** …" đặt trên đoạn, đánh số theo chương như bảng.
  - Bỏ phần không liên quan, đánh dấu chỗ bỏ bằng `# …`.
  - Manifest và quy tắc cảnh báo đầy đủ đưa vào phụ lục.
  - Lệnh shell chỉ đưa vào khi chính lệnh đó là ý cần nói (ví dụ `make bootstrap` dựng lại cluster từ máy trắng).

## 7. Trích dẫn tài liệu

- Khẳng định nào không do nhóm đo hay thiết kế phải có trích dẫn: số liệu của người khác, định nghĩa, cách làm của hệ thống khác.
- **Thứ tự ưu tiên nguồn:**
  1. Bài báo khoa học.
  2. Tài liệu chính thức, đúng phiên bản đã ghim.
  3. Sách.
  4. Blog kỹ thuật của chính nhà phát triển.
- Không dùng Wikipedia, diễn đàn hay bài tổng hợp không rõ tác giả.
- **Chỉ trích dẫn tài liệu đã đọc.** Tài liệu nào trong `tai-lieu.bib` cũng phải được dẫn ít nhất một lần.
- Thêm mục vào `tai-lieu.bib` thì kiểm URL còn mở được và ghi ngày truy cập (`urldate`).
- **Mã và cấu hình của nhóm không trích dẫn như tài liệu**, mà dẫn chéo tới mục hoặc phụ lục. Đường dẫn repository ghi một lần ở chương 1 và một lần ở phụ lục.

## 8. Phối hợp giữa hai người

- **Sở hữu file:** mỗi file một người viết (README). Muốn góp ý mục của người kia thì góp qua review PR, không sửa thẳng.
- **Mục chia đôi** (3.3, 4.11; một phần chương 2 và 5): trước khi viết, hai người chốt danh sách tiểu mục và câu hỏi mỗi tiểu mục trả lời, ghi vào comment đầu file `a`. Như vậy không ai viết trùng.
- **Ranh giới hay trùng nhau.** Viết đầy đủ ở mục ghi trong bảng, chỗ khác dẫn chéo:

  | Nội dung | Viết đầy đủ ở | Chỗ khác chỉ |
  |---|---|---|
  | Định nghĩa SLO, TTFT, TPOT | 2 (khái niệm) và 3.4 (giá trị của đồ án) | dẫn chéo |
  | Lý do chọn tín hiệu A2 | 3.3b | 5.3 chỉ đối chiếu với số đo |
  | Cold start: thiết kế, cách làm, số đo | 3.3a, 4.5, 5.4 | mỗi chỗ một vai trò, theo §2 |
  | Kịch bản vận hành VH | 3.5 (thiết kế), 4.8, 4.9 (cách làm), 5.5 (kết quả) | |

- **Review:**
  - Người kia review trong 48 giờ (CONTRIBUTING §7).
  - Người review đối chiếu **mọi số** với comment nguồn, và kiểm thuật ngữ theo §4.
  - Không duyệt PR có số mà không có nguồn.
- **Ghép thử:** mỗi tối Chủ nhật, người ghép (Trình) chạy pandoc ra `.docx` để cả hai đọc thử liền mạch. Lỗi chung (thuật ngữ lệch, lặp nội dung) ghi vào issue, không sửa vội.
- **Quy tắc mới phát sinh** khi viết thì thêm vào file này qua PR, rồi báo người kia.

## 9. Dùng AI agent khi viết

- Agent được viết nháp **từ nguồn trong repo**, và phải đặt comment nguồn sau mỗi đoạn có số.
- Agent không được thêm số, khẳng định hay trích dẫn mà không có nguồn.
- Người sở hữu mục phải đọc lại toàn bộ và đối chiếu từng số. **Người sở hữu chịu trách nhiệm về nội dung**, không phải agent.
- Ghi vào nhật ký cá nhân mục nào do agent viết nháp, mục nào đã soát.
- Trước khi nộp, đọc quy định của trường về dùng công cụ AI; nếu trường yêu cầu khai báo thì khai báo trong lời cam đoan hoặc phần mở đầu.

## 10. Checklist trước khi mở PR một mục

- [ ] Dòng đầu là comment mục đích và người viết; tiêu đề và số mục khớp dàn ý.
- [ ] Mục nói đúng phần việc của chương (§2), không lặp mục khác; chỗ cần thì dẫn chéo.
- [ ] Mọi số, mọi khẳng định kỹ thuật có comment nguồn; không có số "chưa đo" (`nguon-tu-lieu.md` §4).
- [ ] Thuật ngữ, tên sản phẩm, mã định danh theo §4; thuật ngữ mới đã giải thích ở lần đầu và đã vào danh mục chữ viết tắt.
- [ ] Số và đơn vị theo README và §5; số không phải đo thật có nhãn nguồn gốc.
- [ ] Hình, bảng có chú thích, được nhắc trong bài trước khi xuất hiện, có câu nhận xét đi sau.
- [ ] Không có văn nói, mã việc, số PR, tên người, đường dẫn `docs/` trong thân bài.
- [ ] `pandoc … --citeproc` chạy không lỗi, không cảnh báo trích dẫn (lệnh ở README).
- [ ] Đã ghi nhật ký cá nhân (AGENTS.md).
