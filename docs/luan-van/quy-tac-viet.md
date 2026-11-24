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
| Độ dài | Theo nội dung lõi; định hướng 70–90 trang thân bài, trần 100; khoảng trang của từng chương ở cột "Trang" của bảng dàn ý, Kế hoạch §11.1 | Không tính phụ lục. Không có ngân sách trang cho từng mục: mục dài hay ngắn theo phần nội dung 20/80 của nó (§3.1). Độ dài đo theo **trang, gồm cả bảng và hình**. Dàn trang thử ngày 23/11 trên A4, Times New Roman, giãn 1,5 dòng, chữ trong bảng nhỏ hơn văn xuôi 1 pt; hai khuôn: khuôn A cỡ 13 pt, lề trên/dưới/trái/phải 2/2/3/2 cm; khuôn B cỡ 14 pt, lề 3,5/3/3,5/2 cm. Kết quả: văn xuôi khoảng 410–510 chữ mỗi trang; 17 bảng của các bản nháp chương 3 chiếm trung bình 0,5–0,75 trang mỗi bảng. Lập kế hoạch theo khoảng 450 chữ văn xuôi mỗi trang; đo lại khi có khuôn của trường |
| Phông, cỡ, giãn dòng, lề | Áp theo khuôn của trường | Chờ khuôn |
| Cấp tiêu đề | Tối đa 3 cấp số: `3.4.1.` | Khi nào đặt tiêu đề: §2. Cần chia nhỏ hơn thì dùng đoạn mở bằng cụm in đậm |
| Trích dẫn | IEEE, đánh số `[1]` theo thứ tự xuất hiện | Pandoc tự đánh số qua `[@key]` |

Thứ tự các phần của quyển (tên file dự kiến ở khung luận văn, chưa dựng):
1. Bìa, nhiệm vụ đồ án: theo mẫu của trường.
2. Lời cam đoan (có khai báo dùng công cụ AI, §9), lời cảm ơn.
3. Tóm tắt tiếng Việt và *Abstract*: mỗi bản khoảng 1 trang.
4. Mục lục, danh mục hình, danh mục bảng, danh mục chữ viết tắt, mã định danh và thuật ngữ.
5. Chương 1–6.
6. Tài liệu tham khảo, phụ lục.

Nếu khuôn của trường đòi phần "Mở đầu" và "Kết luận" không đánh số thay cho chương 1 và 6 thì chỉ đổi tên, giữ nguyên nội dung.

Tóm tắt viết **sau cùng**. Tóm tắt phải nêu bài toán, cách làm, môi trường đo, và **2–3 kết quả chính có số** (ví dụ GPU-giờ của A2 so với S4). Không viết chung chung kiểu "đã xây dựng thành công hệ thống".

## 2. Mỗi chương nói gì

Luận văn có một mạch chung: ba thông điệp TĐ1–TĐ3 và năm hướng giải HG1–HG5, đi qua chương 3–6 (Kế hoạch §11.1). Mục nào không phục vụ một thông điệp, một yêu cầu F/N hoặc một mục tiêu của đề cương thì đưa xuống phụ lục hoặc bỏ.

Mỗi sự kiện chỉ được trình bày **đầy đủ ở một chỗ**; ở chỗ khác thì dẫn chéo "(mục 4.5)". Chương nào nói gì:

| Chương | Trả lời câu hỏi | Không đặt ở đây |
|---|---|---|
| 1 | Vì sao bài toán đáng làm; mục tiêu, phạm vi và giả định; phương pháp thực hiện; đóng góp | Chi tiết kỹ thuật. Số đo chỉ có 2–3 số chính ở mục Đóng góp, kèm dẫn chéo tới chương 5 |
| 2 | Kiến thức chung mà người đọc cần để hiểu các chương sau (LLM inference, vLLM, autoscaling, SLO, GitOps), và giải pháp liên quan | Bất cứ gì về hệ thống của nhóm |
| 3 | Hệ thống **cần** gì và **được thiết kế** thế nào, vì sao chọn phương án đó | "Đã cài", lệnh, sự cố |
| 4 | **Đã làm** thế nào, gặp gì, lệch thiết kế ở đâu, kiểm chứng ra sao | Bảng kết quả đánh giá (để chương 5) |
| 5 | Số đo, giải thích, so với chỉ tiêu, hạn chế của phép đo | Lặp lại cách cài đặt |
| 6 | Kết luận theo ba thông điệp, hạn chế của hệ thống và phạm vi, hướng phát triển | Kết quả mới chưa nêu ở chương 5 |

**Khung của một chương:**
- **Đoạn mở đầu chương:** 3–5 câu, nói chương trả lời câu hỏi gì và gồm các mục nào. Đoạn này nằm ở file `CC-00-<ten>.md`.
- **Mỗi mục cấp 2:** mở bằng 1–2 câu nói mục giải quyết việc gì (không viết "Mục này trình bày…"). Trước khi viết, ghi 1–3 thông điệp chính của mục vào comment đầu file: `<!-- Thông điệp: … -->`. Đoạn nào không phục vụ một thông điệp thì bỏ hoặc chuyển xuống phụ lục.
- **Mục cuối "Kết chương":** 1 đoạn, nói chương rút ra điều gì và dẫn sang chương sau.

Cách chia tiểu mục:
- **Một tiêu đề phải đáng có:** nội dung dưới nó dài từ khoảng 1 trang (§1: khoảng 450 chữ văn xuôi, ít hơn khi có bảng hoặc hình), và trả lời một câu hỏi mà người đọc sẽ tra trong mục lục. Miễn cho các tiêu đề mà khung bắt buộc và vốn ngắn: "Kết chương", "Cấu trúc luận văn". Ngắn hơn thì không đặt tiêu đề: viết thành đoạn có câu chủ đề rõ (§3.1), hoặc mở đoạn bằng cụm in đậm khi có từ 3 khía cạnh song song (§3.2).
- Mục cấp 2 dài dưới khoảng 2,5 trang thì không chia cấp 3.
- **Tiêu đề nói nội dung hoặc kết luận**, không nói bước của khung ("Cách làm", "Kiểm chứng") hay mã kịch bản ("VH2"). Mã định danh nằm trong câu.
- Các tiểu mục ngang hàng có độ nặng tương đương, mỗi nhóm 2–4 tiểu mục. Số tiêu đề tỷ lệ với giá trị: mục mang thông điệp TĐ1–TĐ3 nhiều nội dung nên có tiểu mục, mục ngoại vi thường không.
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

Sáu bước là **thứ tự các đoạn** trong mục, không đặt thành tiêu đề; tiêu đề của chương 4 theo cách chia tiểu mục ở §2. Sự cố viết thành đoạn ngay trong mục của thành phần gặp sự cố, rồi được gom ở bảng kết chương.

### 2.2. Trình bày quy trình làm việc và con người

Chỉ mô tả quy trình đã thật sự diễn ra. Ví dụ: không viết "hai thành viên review chéo mọi thay đổi" khi thực tế không như vậy; viết đúng điều đã làm, như "mọi thay đổi đi qua PR và được CI kiểm tự động trước khi merge".

- **Phần phương pháp và tổ chức thực hiện ở mục 1.2** (khoảng 300 chữ): làm theo vòng (thiết kế; dựng và thử trên simulator; kiểm trên máy nhà; đo trên máy thuê); kế hoạch theo tuần có mốc; phân công theo hai mảng; quản lý thay đổi bằng Git (PR, CI tự kiểm); ghi quyết định kiến trúc (ADR) và nhật ký vận hành.
- **Con người trong vòng vận hành** (mục 3.5, 4.5, 4.6): hệ thống tự xử lý việc lặp lại (scale, thay pod hỏng, fallback). Người trực vào cuộc khi có page, làm theo runbook, và quyết định những việc cần phán đoán (rollback, thêm GPU).
- **Quyết định** viết theo kiểu ADR: "Nhóm cân nhắc A và B; chọn A vì …; đánh đổi là …".
- **Phụ lục F** có bảng kế hoạch và phân công, kèm tên thành viên (theo mẫu của trường).

## 3. Văn phong

**Giọng văn cần đạt:** một sinh viên kỹ thuật vững chuyên môn trình bày cho hội đồng: rõ, chắc, khiêm tốn, không văn hoa. Chuyên nghiệp ở nội dung (đúng, có số, có lý do), không ở từ ngữ to tát. Đọc lên phải giống người thật viết.

**Người đọc:** giảng viên CNTT chưa vận hành Kubernetes hay vLLM. Không giả định người đọc biết pod, HPA, KV cache, TTFT, PromQL. Chương 2 giải thích mỗi khái niệm **một lần**; chương 3–6 dùng thẳng. Chương sau cần khái niệm mà chương 2 chưa có thì bổ sung vào chương 2, không giải thích tại chỗ.

### 3.1. Trọng tâm và mật độ

- **Quy tắc 20/80:** mỗi mục tập trung vào 1–3 thông điệp chính (§2), là điều người đọc phải nhớ sau khi đọc xong.
- **Câu đầu đoạn là kết luận**, các câu sau là bằng chứng (số, lý do). Không dẫn dắt vòng trước khi vào ý.
- **Một ý nói một lần.** Không kết đoạn hay kết mục bằng câu nhắc lại điều vừa nói.
- **Thử từng câu:** bỏ câu đó thì người đọc mất gì cho một thông điệp, một yêu cầu F/N hay một quyết định thiết kế? Không mất gì thì bỏ.
- **Cắt**, theo thứ tự này, khi một đoạn không qua phép thử ở trên, hoặc khi tổng độ dài vượt trần ở §1:
  1. bối cảnh chung mà chương 2 đã có;
  2. chuyện của chương khác: cách cài, lệnh, sự cố để chương 4; số của từng lượt để chương 5 hoặc phụ lục E;
  3. diễn biến theo thời gian không làm đổi kết luận;
  4. chi tiết chỉ người làm cần (tham số phụ, tên file, danh sách đầy đủ): đưa phụ lục và dẫn chéo, giữ tham số chính kèm lý do;
  5. số phụ, giới hạn nhỏ (gom vào mục Hạn chế).

  Phương án bị loại: chỉ giữ phương án mà người đọc dễ hỏi "sao không làm thế", mỗi phương án một câu lý do.
- **Mật độ gọn:** văn xuôi nêu khoảng giá trị kèm số lượt, ví dụ "79,7–81,5 s (3 lượt)"; số của từng lượt chỉ để trong bảng. Không lặp ở văn xuôi điều bảng đã nói; câu sau bảng nêu điều người đọc cần thấy.

### 3.2. Câu và đoạn

- **Ngôi:** dùng ngôi thứ ba: "nhóm", "đồ án", "hệ thống". Chỉ lời cảm ơn được dùng "chúng em".
- **Câu:** mỗi câu một ý, tối đa 35 chữ, trung bình khoảng 18–25 chữ; độ dài thay đổi tự nhiên. Không lồng định nghĩa vào câu ("…, tức …", hay "(*…*, viết tắt)" giữa một câu liệt kê). Liệt kê từ 3 vế trở lên mà vế nào cũng cần giải thích thì tách câu, hoặc lập bảng nếu đủ điều kiện ở §6.
- **Đoạn:** 3–7 câu. Thân bài là văn xuôi; danh sách chỉ dùng khi liệt kê từ 3 mục song song, ngắn, không lồng nhau. Chỉ mở đoạn bằng cụm in đậm khi tiểu mục có từ 3 khía cạnh song song (thay cho tiêu đề cấp 4, §1); không in đậm giữa câu.
- **Chủ ngữ rõ:** "Nhóm chọn …", "A2 thêm replica …"; không viết câu cụt chủ ngữ kiểu "Được thiết kế để …". Giải thích lý do như khi trình bày cho thầy cô: "Nhóm không dùng GPU utilization vì …".
- **Không dùng văn nói:** không viết "khá", "rất nhiều", "cực kỳ", "ổn", "ngon", "chạy ngon", "khủng". Thay bằng số: "nhanh hơn 4 lần" thay cho "nhanh hơn rất nhiều".
- **Không cảm thán, không câu hỏi tu từ, không "ta thấy rằng".** Cần nêu nhận xét thì viết "Kết quả cho thấy…".
- **Thì:** thiết kế viết ở thì hiện tại ("A2 đọc tổng số request đang chạy và đang chờ"); việc đã làm và đã đo viết như sự kiện, có điều kiện đo ("Trong phiên đo V2, A2 dùng 25% GPU-giờ so với S4").

### 3.3. Mức chắc chắn và cách nói về kết quả

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
- **Nói thẳng điều chưa làm:** "Nhóm chưa đo …". Không tự khen hệ thống của mình.

### 3.4. Tránh văn sáo và dấu hiệu văn do máy sinh

**Cụm sáo rỗng, không dùng.** Thay bằng nội dung cụ thể, hoặc bỏ hẳn:

| Không viết | Viết thay |
|---|---|
| "đóng vai trò quan trọng/then chốt", "yếu tố then chốt", "chìa khoá" | nói nó làm gì: "KEDA quyết định số replica" |
| "trong bối cảnh … ngày càng …", "ngày càng phát triển mạnh mẽ" | nêu sự kiện có số, hoặc bỏ |
| "không chỉ … mà còn …" | hai câu thường |
| "một cách hiệu quả/linh hoạt/toàn diện/nhanh chóng" | số: "trong 16,8 s" |
| "toàn diện", "mạnh mẽ", "vượt trội", "liền mạch", "tối ưu (hoá)", "hiệu quả cao", "mang lại lợi ích" | số so sánh, hoặc bỏ |
| "góp phần", "hướng tới", "nhằm mục đích", "với mục tiêu" | "để" |
| "Điều này cho thấy", "Có thể thấy rằng", "Đáng chú ý là", "Nhìn chung", "Tóm lại" (trừ Kết chương) | bỏ, nói thẳng kết luận |
| "tiến hành", "thực hiện việc", "việc … việc …" | động từ thường: đo, chạy, thêm, chọn, sửa |
| "được … bởi …" (bị động dịch từ tiếng Anh) | câu chủ động: "Runner ghi …" |

**Dấu hiệu cấu trúc, tránh:**
- Mọi đoạn cùng một khuôn (in đậm mở đầu, 4 câu, câu tóm tắt cuối).
- Bộ ba tính từ cho kêu ("nhanh, ổn định và tiết kiệm") khi không có số cho từng vế.
- Cặp "không phải X, mà là Y" để tạo kịch tính; rào đón kép ("về cơ bản là tương đối").
- Hai đoạn liên tiếp cùng mở bằng từ nối ("Bên cạnh đó", "Ngoài ra", "Hơn nữa"). Mỗi đoạn dùng tối đa một từ nối loại này.

**Dấu hiệu chữ, tránh:**
- Gạch dài "—" trong câu: dùng dấu phẩy, ngoặc đơn, hoặc tách câu. Gạch ngắn "–" chỉ dùng cho khoảng số.
- Mũi tên "→" trong văn xuôi: viết "từ Prometheus tới Alertmanager". Mũi tên chỉ dùng trong bảng và hình.
- Hơn một dấu hai chấm hoặc hơn một dấu chấm phẩy trong một đoạn: tách câu.

**Ví dụ.**
- Không viết: "Trong bối cảnh nhu cầu sử dụng LLM ngày càng tăng, việc tối ưu hoá chi phí GPU đóng vai trò then chốt. Hệ thống không chỉ đảm bảo chất lượng dịch vụ mà còn tiết kiệm tài nguyên một cách hiệu quả."
- Viết: "GPU thuê theo giờ vẫn tính tiền khi không có request nào. Nhóm muốn biết có thể tắt bớt GPU lúc tải thấp mà vẫn giữ TTFT dưới 2,5 s cho 95% request hay không."

### 3.5. Không nhắc chuyện nội bộ trong thân bài

- mã việc (Q6, TR7), số PR, commit, mã quyết định (D68);
- tên người, nhật ký cá nhân, "phiên làm việc", "phiên Claude";
- AI agent và tên công cụ AI (chỉ khai báo một lần ở Lời cam đoan, §9);
- đường dẫn `docs/`.

Những thứ này chỉ nằm trong comment nguồn. Ngoại lệ: mục phân công ở slide và Phụ lục F.

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
- Tối đa 4 mã trong một đoạn. Câu chủ đề viết bằng lời, không mở bằng mã.
- Mã yêu cầu và chỉ tiêu (F1–F7, N1–N8) chỉ dùng ở bảng ánh xạ mục tiêu của mục 1.2 (kèm tên ngắn, vì mã được định nghĩa ở 3.1), ở mục 3.1, ở câu so với chỉ tiêu của chương 5 (§5) và ở bảng nghiệm thu 5.6. Chỗ khác nói bằng lời kèm số, ví dụ "thời gian phản ứng không quá 2 phút".
- TĐ1–TĐ3 (ba thông điệp) và HG1–HG5 (năm hướng giải) là nhãn của dàn ý (Kế hoạch §11.1), không dùng trong thân bài; trong bài nói bằng lời.
- Tên pha viết tiếng Việt, không để trong `code`: pha nền (`pre`), pha tăng đột ngột (`spike`), pha giảm (`drop`), pha ổn định (`steady`), pha tăng dần (`ramp`), pha duy trì (`sustain`).
- `code` chỉ dành cho tên người đọc có thể tra hoặc gõ lại: metric, tham số cấu hình, tên file, tên cảnh báo.
- Mã C1–C6 của tài liệu thiết kế là tên nội bộ của biểu đồ. Trong bài dùng số hình ("Hình 5.3"), không viết "C1", vì C đã là ký hiệu năng lực.
- **Ký hiệu:** C = năng lực một replica (req/s); B\* = số request đồng thời ở mức năng lực; λ = tốc độ đến (req/s); N = số GPU ("N = 4"). Không dùng lại các chữ này cho nghĩa khác.

## 5. Trình bày số liệu và kết quả

- **Số nào cũng có điều kiện đo**, ghi ở câu đó hoặc ở chú thích bảng: máy, model, tải, số lượt. Điều kiện chung của cả chương ghi một lần ở mục 5.1, các chỗ sau dẫn chéo.
- **Làm tròn:** phần trăm 1 chữ số thập phân (75,4%); thời gian 1 chữ số thập phân nếu dưới 100 s, số nguyên nếu từ 100 s trở lên; GPU-giờ và req/s 2 chữ số thập phân. Không thêm chữ số mà nguồn không có.
- **Ít lượt:** khi chỉ có 3 lượt trở xuống, văn xuôi ghi khoảng giá trị kèm số lượt ("76–81 s (3 lượt)"), không ghi trung bình đứng một mình; giá trị từng lượt để ở bảng hoặc Phụ lục E (§3.1).
- **Chênh lệch** giữa hai tỷ lệ viết bằng "điểm phần trăm". Ký hiệu năng lực có dấu cách: "0,5 C".
- **Ngày tháng** chỉ ghi một lần cho phiên đo, ở mục 5.1. Bối cảnh phát hiện (ví dụ "phát hiện trên simulator ngày 01/11") để ở phần sự cố của chương 4, hoặc trong comment nguồn.
- **Khoảng giá trị:** "80–82 s" (gạch ngang ngắn, không cách). Phép nhân: "4 × RTX 4060 Ti". Đẳng thức: "λ = 3,5 req/s" (có cách hai bên).
- **Đơn vị:** s, ms, phút (không viết "min"), req/s, GB hoặc GiB đúng như nguồn, USD. Phần trăm và mọi định dạng số khác: theo README.
- **Nhãn nguồn gốc:** số nào không phải đo thật thì gắn nhãn ngay cạnh:
  - "(mô phỏng)": ví dụ phần mô phỏng ma trận;
  - "(ước tính)": ví dụ giá thuê theo giờ;
  - "(đề xuất, chưa thực hiện)": ví dụ phần V3.
  - Số mô phỏng và số đề xuất chỉ xuất hiện ở chương 6 hoặc trong mục có tiêu đề nói rõ.
- **So với chỉ tiêu:** khi nêu kết quả của một chỉ tiêu (N1…N8), nêu theo thứ tự: chỉ tiêu, số đo, đạt/không đạt, rồi lý do nếu không đạt. Bảng nghiệm thu tổng hợp lại đúng các câu đó, không có số mới.
- **Mỗi bảng hoặc hình kết quả có một câu nhận xét chính** đứng ngay sau, nói điều người đọc cần thấy. Không chỉ viết "kết quả ở Bảng 5.2".
- **Hạn chế của phép đo** gom vào mục 5.7 (danh sách ở `nguon-tu-lieu.md` §6). Hạn chế của hệ thống và phạm vi viết ở mục 6.2.

## 6. Hình, bảng, mã nguồn

Đánh số và đặt chú thích theo README. Thêm:

- **Hình:**
  - Chú thích tự đủ nghĩa, đọc được mà không cần thân bài.
  - Hình phải được nhắc trong bài **trước** khi xuất hiện.
  - Chữ trong hình bằng tiếng Việt; trục có tên và đơn vị.
  - Hình lấy từ tài liệu khác thì ghi "Nguồn: [@key]" cuối chú thích; hình nhóm tự vẽ thì không ghi.
  - Hình minh hoạ không phải số thật thì ghi "(minh hoạ)" trong chú thích.
- **Ảnh chụp màn hình:** chỉ dùng cho dashboard, tin cảnh báo thật và giao diện. Chú thích ghi môi trường và thời điểm chụp. Không chụp terminal; cần thì chép output thành bảng hoặc đoạn mã.
- **Bảng:** không quá khoảng 7 cột. Ô trống ghi "–" và giải thích nghĩa của "–" ở chú thích. Ô ghi cụm từ ngắn, không viết câu: bảng mà ô nào cũng cần câu giải thích thì viết văn xuôi, hoặc đưa bảng đầy đủ vào phụ lục và giữ trong thân bài các cột người đọc cần. Bảng tốn chỗ (§1), nên chỉ lập bảng khi có từ 3 dòng và 3 cột trở lên, tính cả cột tên.
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

- **Người viết:** từ 22/11/2026, Trình viết bản base toàn bộ luận văn (Kế hoạch §11.1), nên mỗi mục là một file, không tách phần `a`, `b` theo người viết. Khi base xong, Quang review, sửa và cập nhật số. Người sở hữu tính năng theo Kế hoạch §5.1 soát kỹ mục tương ứng.
- **Quy trình cho mỗi chương:**
  1. Chốt dàn ý của chương: tiểu mục, thông điệp của từng mục, khoảng trang định hướng (Kế hoạch §11.1).
  2. Viết nháp theo README, file này và mẫu văn.
  3. Soát: đối chiếu toàn bộ số với comment nguồn, soát văn phong theo §3.
  4. Người viết đọc lại ý và soát xác suất vài số, rồi mở một PR cho cả chương.
- **Mẫu văn:** mục 3.5 viết theo file này và được duyệt trước khi viết các mục khác. Mẫu dùng cho văn phong; độ dài của mỗi mục theo nội dung lõi của nó (§1).
- **Góp ý:** tới bước định dạng (W9), bản gốc là Markdown. Góp ý qua review PR hoặc comment trên file `.docx` ghép thử; người viết sửa ở Markdown rồi xuất lại.
- **Ranh giới hay trùng nhau.** Viết đầy đủ ở mục ghi trong bảng, chỗ khác dẫn chéo:

  | Nội dung | Viết đầy đủ ở | Chỗ khác |
  |---|---|---|
  | SLO, TTFT, TPOT | 2 (khái niệm), 3.1 (giá trị của đồ án), 3.5 (SLI và cảnh báo) | Chương 5 chỉ báo SLO attainment |
  | Lý do chọn tín hiệu A2 | 3.3 | 5.3 chỉ đối chiếu với số đo |
  | Cold start: thiết kế, cách làm, số đo | 3.4, 4.4, 5.4 | Mỗi chỗ một vai trò, theo §2 |
  | Tính hợp lệ của lượt đo | 3.6 (tiêu chí, lý do), 4.7 (runner kiểm thế nào), 5.1 (kết quả) | |
  | Scale-down không rớt request | 5.5.1 (số đo lấy từ pha giảm tải của KB2) | 5.3 chỉ dẫn chéo |
  | Kịch bản vận hành VH | 3.6 (thiết kế phép thử), 4.1, 4.5, 4.6 (cách làm), 5.5 (kết quả) | |
  | Cách chấm cảnh báo, định nghĩa page giả | 3.6 | 5.5 chỉ báo kết quả |
  | Hạn chế | 5.7 (phép đo), 6.2 (hệ thống, phạm vi) | |

- **Review:**
  - Người review đọc trong 48 giờ (CONTRIBUTING §7).
  - Người review đối chiếu **mọi số** với comment nguồn, và kiểm thuật ngữ theo §4.
  - Không duyệt PR có số mà không có nguồn.
- **Ghép thử:** mỗi tối Chủ nhật, người ghép (Trình) chạy pandoc ra `.docx` để cả hai đọc thử liền mạch. Lỗi chung (thuật ngữ lệch, lặp nội dung) ghi vào issue, không sửa vội.
- **Quy tắc mới phát sinh** khi viết thì thêm vào file này qua PR, rồi báo người kia.

## 9. Dùng AI agent khi viết

- Agent được viết nháp **từ nguồn trong repo**, và phải đặt comment nguồn sau mỗi đoạn có số.
- Agent không được thêm số, khẳng định hay trích dẫn mà không có nguồn.
- Bước soát ở §8 do một agent khác với agent viết nháp làm; người viết vẫn đọc lại và đối chiếu số. **Người viết và người review chịu trách nhiệm về nội dung**, không phải agent.
- Ghi vào nhật ký cá nhân mục nào do agent viết nháp, mục nào đã soát.
- **Thân bài (chương 1–6) không nhắc** AI agent hay tên công cụ AI (§3.5). Đồ án nói về phục vụ LLM, nên không dùng chữ "AI" chung chung: "model", "LLM" là đối tượng mà hệ thống phục vụ.
- **Khai báo một lần, ở Lời cam đoan,** theo quy định của trường (cần hỏi GVHD hoặc khoa), và đúng mức dùng thật. Dự án dùng công cụ AI cho cả viết mã, phân tích số liệu, soạn và rà soát văn bản, nên không viết nhẹ hơn thực tế. Câu mẫu (hai người chốt câu cuối cùng): "Trong quá trình thực hiện, nhóm dùng công cụ AI để hỗ trợ viết mã, phân tích số liệu, soạn thảo và rà soát văn bản. Nhóm đã kiểm tra lại các kết quả đó và chịu trách nhiệm hoàn toàn về nội dung đồ án. Mọi số liệu trong báo cáo đều truy được về dữ liệu đo lưu trong kho mã của đồ án."
- **Comment trong file luận văn** (repo công khai) chỉ ghi nguồn và trạng thái soát, theo dạng trung tính: `<!-- Soát số: <ngày> · Soát văn phong: <ngày> · Người viết đọc lại: <ngày> -->`. Việc dùng AI ghi ở nhật ký cá nhân và Lời cam đoan.

## 10. Checklist cho từng mục, trước khi mở PR của chương

- [ ] Dòng đầu là comment mục đích và người viết; có comment thông điệp (§2) và trạng thái soát (§9); tiêu đề và số mục khớp dàn ý (Kế hoạch §11.1).
- [ ] Mục nói đúng phần việc của chương (§2), không lặp mục khác (bảng ranh giới ở §8); chỗ cần thì dẫn chéo.
- [ ] Mọi số, mọi khẳng định kỹ thuật có comment nguồn; không có số "chưa đo" (`nguon-tu-lieu.md` §4).
- [ ] Độ dài theo nội dung lõi (§1, §3.1): không có đoạn ngoại vi chiếm chỗ của phần lõi. Đề mục theo §2: mỗi tiêu đề (trừ các tiêu đề được miễn) có từ khoảng 1 trang nội dung và nói nội dung, không nói bước của khung.
- [ ] Văn phong theo §3: câu đầu đoạn là kết luận; không có cụm sáo và dấu hiệu ở §3.4.
- [ ] Thuật ngữ, tên sản phẩm, mã định danh theo §4; thuật ngữ mới đã giải thích ở lần đầu và đã vào danh mục chữ viết tắt.
- [ ] Số và đơn vị theo README và §5; số không phải đo thật có nhãn nguồn gốc.
- [ ] Hình, bảng có chú thích, được nhắc trong bài trước khi xuất hiện, có câu nhận xét đi sau.
- [ ] Không có văn nói và không nhắc chuyện nội bộ (§3.5) trong thân bài.
- [ ] `pandoc … --citeproc` chạy không lỗi, không cảnh báo trích dẫn (lệnh ở README).
- [ ] Đã ghi nhật ký cá nhân (AGENTS.md).
