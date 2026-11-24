<!-- Mục đích: quy ước viết bản nguồn luận văn (Markdown, mỗi mục một file) và cách ghép thành .docx. -->
# Luận văn: bản nguồn

Thư mục này chứa **nội dung** luận văn, viết bằng Markdown, mỗi mục một file. Ở bước định dạng (W9), pandoc ghép các file thành một file `.docx` theo khuôn của trường.

- Dàn ý và độ dài: [Kế hoạch §11.1](../chi-tiet/06-ke-hoach-quan-ly.md#111-dàn-ý-luận-văn).
- Người viết: từ 22/11/2026, Trình viết bản base toàn bộ luận văn; Quang review, sửa và cập nhật số. Người sở hữu tính năng theo [Kế hoạch §5.1](../chi-tiet/06-ke-hoach-quan-ly.md#51-phân-công) soát kỹ mục tương ứng. Ghép và định dạng: Trình.
- Nguồn sự kiện: nhật ký làm việc ([AGENTS.md](../../AGENTS.md)), thiết kế ở `docs/chi-tiet/`, mã nguồn, và số liệu trong `analysis/`.

**Vì sao không viết thẳng trong Word:** file Markdown xem được diff, review được qua PR, AI agent sửa được, và mỗi số liệu đặt được một comment ghi nguồn. Word vẫn là định dạng cuối: GVHD góp ý trên file `.docx`, nhóm sửa ở đây rồi xuất lại.

## Tổ chức file

| File | Nội dung |
|---|---|
| `CC-SS-<ten>.md` | Chương `CC`, mục `SS`. Hai chữ số để thứ tự khi ghép đúng với thứ tự mục, ví dụ `03-05-<ten>.md` đứng trước `04-01-<ten>.md` |
| `CC-00-<ten>.md` | Tiêu đề chương (`# Chương CC. …`) và đoạn mở đầu chương |
| `tai-lieu.bib` | Danh mục tài liệu tham khảo dùng chung (BibTeX) |
| [`quy-tac-viet.md`](quy-tac-viet.md) | Quy tắc viết chung cho hai người: chương nào nói gì, văn phong, thuật ngữ thống nhất, trình bày kết quả, review, checklist trước PR. Không ghép vào `.docx` |
| [`nguon-tu-lieu.md`](nguon-tu-lieu.md) | Mục nào lấy tư liệu ở đâu, số liệu đã chốt, những gì chưa có số, cách lấy dữ liệu V2. Không ghép vào `.docx` |

- **Mỗi mục cấp 2 là một file**, không tách phần `a`, `b` theo người viết. Góp ý qua review PR hoặc comment trên `.docx` ghép thử ([quy tắc viết §8](quy-tac-viet.md#8-phối-hợp-giữa-hai-người)).
- Dòng đầu mỗi file là comment `<!-- Mục đích: … Người viết: … -->` (CONTRIBUTING §2). Comment HTML không xuất hiện trong `.docx`.
- Tiêu đề trong file mục: `## 3.4. …`, `### 3.4.1. …`. Số mục đánh tay, khớp dàn ý §11.1.
- Hình lấy thẳng từ chỗ gốc, không chép vào đây: sơ đồ ở `docs/images/png/` (sinh từ `docs/diagrams/`), biểu đồ kết quả ở `analysis/figures/`.

## Quy ước viết

- **Văn phong:** tiếng Việt học thuật, ngôi thứ ba ("nhóm chọn", "hệ thống dùng"). Không dùng "tôi", "bạn".
- **Thuật ngữ:** lần đầu xuất hiện thì ghi tiếng Việt, kèm tiếng Anh in nghiêng và chữ viết tắt, ví dụ "thời gian tới token đầu (*time to first token*, TTFT)". Từ đó trở đi dùng chữ viết tắt hoặc thuật ngữ tiếng Anh (GPU replica, threshold, burn rate…), như quy ước của `AGENTS.md`.
- **Tên metric, resource, file, lệnh** đặt trong `code`.
- **Số:** dấu phẩy thập phân (2,5 s), dấu chấm phân nghìn (1.942), một dấu cách giữa số và đơn vị (16 GB, 180 s), phần trăm viết liền (95%).
- **Hình:** `![Hình 3.1. <chú thích>](../images/png/<tên>.png)`, chú thích nằm dưới hình. **Bảng:** dòng `**Bảng 3.1.** <chú thích>` đặt ngay trên bảng. Hình và bảng đánh số theo chương, theo thứ tự xuất hiện. Hình nào, bảng nào cũng phải được nhắc tới trong bài (mốc M4). Mục viết khi các mục đứng trước trong chương chưa có thì dùng số tạm theo mục (`Bảng 3.4a`, `Hình 3.4a`), ghi điều đó ở dòng comment thứ hai của file, và đánh lại khi ghép chương.
- **Dẫn chéo:** "(mục 3.4.2)", "(chương 5)". Thân bài không link tới `docs/`, vì luận văn phải đọc được độc lập; đường dẫn nội bộ chỉ nằm trong comment nguồn.
- **Trích dẫn:** `[@key]`, với `key` có trong `tai-lieu.bib`. Kiểu hiển thị (ví dụ IEEE đánh số `[1]`) chốt ở bước định dạng, nên không đánh số tay.
- **Công thức:** `$…$` trong dòng, `$$…$$` cho công thức riêng một dòng. Pandoc chuyển thành công thức Word.

## Nguồn của mọi sự kiện và số liệu

Sau mỗi đoạn văn hoặc bảng có số liệu hay khẳng định kỹ thuật, đặt một comment ghi nguồn:

```markdown
<!-- nguồn: docs/chi-tiet/00-thong-so.md §6; common/observability/alerts/llm.yaml (LLMSLOBurnFast) -->
```

- Chỉ viết điều có trong repo: thiết kế, mã nguồn, nhật ký, `analysis/`. Chưa đo thì không viết số.
- Thiết kế và mã nguồn nói khác nhau thì viết theo **cái đã làm** (mã nguồn và nhật ký), và ghi điểm lệch vào nhật ký của người viết.
- Comment nguồn giúp người soát đối chiếu nhanh, và giúp đạt mục "mọi số liệu truy được về `analysis/`" của [Kế hoạch §11.4](../chi-tiet/06-ke-hoach-quan-ly.md#114-checklist-trước-khi-nộp).

## Ghép thành .docx

Pandoc 3.13 (ghim ở [docs/phien-ban.md](../phien-ban.md)). Chạy từ gốc repo, ghi file ra ngoài repo:

```bash
pandoc docs/luan-van/[0-9]*.md \
  --resource-path=docs/luan-van \
  --citeproc --bibliography=docs/luan-van/tai-lieu.bib \
  -o ../luan-van.docx
```

- `--resource-path`: đường dẫn hình trong file viết tương đối với thư mục này (`../images/png/…`), nên pandoc cần biết gốc để tìm hình.
- `--citeproc`: thay `[@key]` bằng trích dẫn và tạo danh mục tài liệu ở cuối.
- Bước định dạng sẽ thêm `--reference-doc=<khuôn T>.docx` ([quy tắc viết §1](quy-tac-viet.md#1-khuôn-trình-bày)) (lề, phông, kiểu tiêu đề) và `--csl=<kiểu trích dẫn>.csl`.
