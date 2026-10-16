# Hướng dẫn cho AI agent

Dự án: autoscaling LLM inference (vLLM) trên Kubernetes, đồ án của Quang và Trình, nộp khoảng 08/12/2026.
Tài liệu gốc: [docs/mo-ta-chi-tiet-do-an.md](docs/mo-ta-chi-tiet-do-an.md). Phân công: [Kế hoạch §5.1](docs/chi-tiet/06-ke-hoach-quan-ly.md#51-phân-công).
**Khi viết code, theo đúng [CONTRIBUTING.md](CONTRIBUTING.md)** (thư mục, header file, đặt tên, Git).
**Người dùng đang học** Kubernetes, vLLM, Argo CD, Prometheus: comment kỹ theo CONTRIBUTING §2 (giải thích thuật ngữ, mỗi khối làm gì và vì sao, ý nghĩa từng tham số), và khi trả lời thì giải thích cả lý do, không chỉ đưa lệnh.

## Bắt buộc: ghi nhật ký làm việc

Luận văn sẽ được viết lại **từ chính các nhật ký này**, nên đây là việc bắt buộc, không phải tuỳ chọn.

### Khi nào ghi

Cuối mỗi phiên làm việc, hoặc ngay sau khi xong một việc có ý nghĩa: thay đổi code hay manifest, thao tác trên cluster hay máy thuê, đo đạc, gỡ lỗi, ra quyết định. Câu hỏi thuần tuý (không đổi gì, không quyết định gì) thì không cần ghi.

### Ghi vào đâu

`docs/nhat-ky/lam-viec/<người>/tuan-XX.md`. Thêm mục mới **vào cuối file**; tạo file nếu chưa có. Mỗi người chỉ sửa thư mục của mình nên không bị xung đột khi merge.

- `<người>`: lấy từ `git config user.name`. Có "Quang" → `quang`; có "Trình" hoặc "Trinh" → `trinh`. Không xác định được thì hỏi.
- `XX` theo lịch của kế hoạch:

| Tuần | Ngày | Tuần | Ngày |
|---|---|---|---|
| 01 | 08–11/10 | 06 | 09–15/11 |
| 02 | 12–18/10 | 07 | 16–22/11 |
| 03 | 19–25/10 | 08 | 23–29/11 |
| 04 | 26/10–01/11 | 09 | 30/11–06/12 |
| 05 | 02–08/11 | 10 | từ 07/12 |

### Mẫu một mục

```markdown
## YYYY-MM-DD – <tiêu đề ngắn>

- **Mã việc:** <Q1…Q7 / TR1…TR7 / chung> · **Môi trường:** <nhà / simulator / V0 / V1 / V2 / không>
- **Đã làm:** các bước chính, theo thứ tự.
- **Quyết định và lý do:** chọn gì, bỏ phương án nào, vì sao.
- **Kết quả và số đo:** lệnh then chốt và output rút gọn, con số đo được (kèm đơn vị, điều kiện đo).
- **Sự cố:** triệu chứng → nguyên nhân → cách sửa. Ghi cả việc thất bại hoặc bỏ dở.
- **Khác thiết kế:** điểm nào làm khác tài liệu `docs/chi-tiet/`, vì sao.
- **Liên kết:** commit, PR, issue, file chính đã sửa.
- **Dùng cho luận văn:** mục nào (ví dụ §4.3, §5 cold start); hình hoặc ảnh chụp nên có.
```

Bỏ dòng nào không có nội dung. Viết tiếng Việt, ngắn, sự kiện cụ thể.

### Quy tắc

- **Chỉ ghi điều đã thực sự xảy ra.** Không bịa số liệu, không ghi "đã chạy được" khi chưa kiểm chứng. Chưa đo thì ghi "chưa đo".
- **Không ghi bí mật:** API key, token, mật khẩu, nội dung kubeconfig, IP công khai của máy thuê.
- Commit file nhật ký **cùng commit hoặc PR** với thay đổi liên quan.
- Nhật ký cá nhân không thay thế các nhật ký chung. Vẫn ghi thêm vào `docs/nhat-ky/van-hanh.md` khi chạy kịch bản VH, gặp sự cố hoặc dùng máy thuê, và vào `docs/nhat-ky/tuan-XX.md` sau họp nhóm.
