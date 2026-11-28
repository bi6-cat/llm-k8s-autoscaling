<!-- Mục đích: quy ước viết bản nguồn luận văn (Markdown, mỗi mục một file) và cách ghép thành .docx. -->
# Luận văn: bản nguồn

Thư mục này chứa **nội dung** luận văn, viết bằng Markdown, mỗi mục một file. Ở bước định dạng (W9), pandoc ghép các file thành một file `.docx` theo khuôn T ([quy tắc viết §1](quy-tac-viet.md#1-khuôn-trình-bày)).

- Dàn ý và độ dài: [Kế hoạch §11.1](../chi-tiet/06-ke-hoach-quan-ly.md#111-dàn-ý-luận-văn).
- Người viết: từ 22/11/2026, Trình viết bản base toàn bộ luận văn; Quang review, sửa và cập nhật số. Người sở hữu tính năng theo [Kế hoạch §5.1](../chi-tiet/06-ke-hoach-quan-ly.md#51-phân-công) soát kỹ mục tương ứng. Ghép và định dạng: Trình.
- Nguồn sự kiện: nhật ký làm việc ([AGENTS.md](../../AGENTS.md)), thiết kế ở `docs/chi-tiet/`, mã nguồn, và số liệu trong `analysis/`.

**Vì sao không viết thẳng trong Word:** file Markdown xem được diff, review được qua PR, AI agent sửa được, và mỗi số liệu đặt được một comment ghi nguồn. Word vẫn là định dạng cuối: GVHD góp ý trên file `.docx`, nhóm sửa ở đây rồi xuất lại.

## Tổ chức file

| File | Nội dung |
|---|---|
| `CC-SS-<ten>.md` | Chương `CC`, mục `SS`. Hai chữ số để thứ tự khi ghép đúng với thứ tự mục, ví dụ `03-05-<ten>.md` đứng trước `04-01-<ten>.md` |
| `CC-00-<ten>.md` | Tiêu đề chương (`# Chương CC. …`) và đoạn mở đầu chương |
| `00-00-mo-dau.md` | Phần Mở đầu, không đánh số: tiêu đề `# Mở đầu {.unnumbered}`. Tên bắt đầu bằng `00` để đứng trước chương 1 và khớp mẫu `[0-9]*.md` của lệnh ghép ([quy tắc viết §1](quy-tac-viet.md#1-khuôn-trình-bày)) |
| `phan-dau/NN-<ten>.md` | Các trang đứng trước Mở đầu, theo thứ tự ở [quy tắc viết §1](quy-tac-viet.md#1-khuôn-trình-bày): `01` bìa, Lời cảm ơn, trang nhận xét, Mục lục (trường TOC của Word); `02` danh mục thuật ngữ, chữ viết tắt và mã định danh; `03` danh mục hình vẽ và bảng biểu. Hai danh mục hình và bảng không viết tay: lệnh ghép (mục "Ghép thành .docx") sinh chúng từ chú thích "Hình x.y." và "Bảng x.y." rồi thay vào dòng đánh dấu `<!-- @danh-muc-hinh -->`, `<!-- @danh-muc-bang -->`. Đặt trong thư mục con để không lẫn với khoá `CC-SS` và đứng trước `00-00-mo-dau.md` khi ghép |
| `tai-lieu.bib` | Danh mục tài liệu tham khảo dùng chung (BibTeX) |
| [`quy-tac-viet.md`](quy-tac-viet.md) | Quy tắc viết chung cho hai người: chương nào nói gì, văn phong, thuật ngữ thống nhất, trình bày kết quả, review, checklist trước PR. Không ghép vào `.docx` |
| [`nguon-tu-lieu.md`](nguon-tu-lieu.md) | Mục nào lấy tư liệu ở đâu, số liệu đã chốt, những gì chưa có số, cách lấy dữ liệu V2. Không ghép vào `.docx` |
| `phu-luc/<chữ>-<ten>.md` | Phụ lục A–G, mỗi phụ lục một file, tiêu đề `# Phụ lục A. … {.unnumbered}`; mục con, hình, bảng và đoạn mã đánh số theo chữ (`A.1`, `Bảng A.1`, `Đoạn mã A.1`). Ghép sau chương 6 và danh mục tài liệu tham khảo. Trích manifest hay quy tắc thì ghi đường dẫn file và commit sửa file đó gần nhất, để người đọc tìm lại được bản đầy đủ. Vì vậy phụ lục được ghi đường dẫn trong repository ngay trong văn bản, kể cả `docs/` (ngoại lệ của [quy tắc viết §3.5](quy-tac-viet.md#35-không-nhắc-chuyện-nội-bộ-trong-thân-bài)) |

- **Mỗi mục cấp 2 là một file**, không tách phần `a`, `b` theo người viết. Góp ý qua review PR hoặc comment trên `.docx` ghép thử ([quy tắc viết §8](quy-tac-viet.md#8-phối-hợp-giữa-hai-người)).
- Dòng đầu mỗi file là comment `<!-- Mục đích: … Người viết: … -->` (CONTRIBUTING §2). Comment HTML không xuất hiện trong `.docx`.
- Tiêu đề trong file mục: `## 3.4. …`, `### 3.4.1. …`. Số mục đánh tay, khớp dàn ý §11.1.
- Hình lấy thẳng từ chỗ gốc, không chép vào đây: sơ đồ ở `docs/images/png/` (sinh từ `docs/diagrams/`), biểu đồ kết quả ở `analysis/figures/`, ảnh chụp màn hình (dashboard) ở `docs/images/anh-chup/`.

## Quy ước viết

- **Văn phong:** tiếng Việt học thuật, ngôi thứ ba ("nhóm chọn", "hệ thống dùng"). Không dùng "tôi", "bạn".
- **Thuật ngữ:** lần đầu xuất hiện thì ghi tiếng Việt, kèm tiếng Anh in nghiêng và chữ viết tắt, ví dụ "thời gian tới token đầu (*time to first token*, TTFT)". Từ đó trở đi dùng chữ viết tắt hoặc thuật ngữ tiếng Anh (GPU replica, threshold, burn rate…), như quy ước của `AGENTS.md`.
- **Tên metric, resource, file, lệnh** đặt trong `code`.
- **Số:** dấu phẩy thập phân (2,5 s), dấu chấm phân nghìn (1.942), một dấu cách giữa số và đơn vị (16 GB, 180 s), phần trăm viết liền (95%).
- **Hình:** `![Hình 3.1. <chú thích>](../images/png/<tên>.png)`, chú thích nằm dưới hình. **Bảng:** dòng `**Bảng 3.1.** <chú thích>` đặt ngay trên bảng. Hình và bảng đánh số theo chương, theo thứ tự xuất hiện. Hình nào, bảng nào cũng phải được nhắc tới trong bài (mốc M4). Mục viết khi các mục đứng trước trong chương chưa có thì dùng số tạm theo mục (`Bảng 3.4a`, `Hình 3.4a`), ghi điều đó ở dòng comment thứ hai của file, và đánh lại khi ghép chương.
- **Dẫn chéo:** "(mục 3.4.2)", "(chương 5)". Thân bài không link tới `docs/`, vì luận văn phải đọc được độc lập; đường dẫn nội bộ chỉ nằm trong comment nguồn.
- **Trích dẫn:** `[@key]`, với `key` có trong `tai-lieu.bib`. Lệnh ghép hiển thị theo kiểu IEEE đánh số `[1]` ([`ieee.csl`](ieee.csl)), nên không đánh số tay.
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

Pandoc 3.13 (ghim ở [docs/phien-ban.md](../phien-ban.md)). Chạy từ gốc repo; file `.docx` là file sinh ra nên ghi ra ngoài repo, không commit:

```bash
make thesis THESIS_OUT=../luan-van.docx
# tương đương: uv run --project analysis python -m analysis.luan_van ../luan-van.docx
```

Lệnh gọi [`analysis/luan_van.py`](../../analysis/luan_van.py), làm các việc sau:

- **Khuôn T** ([quy tắc viết §1](quy-tac-viet.md#1-khuôn-trình-bày)): dựng reference doc từ bản mặc định của pandoc rồi truyền qua `--reference-doc`. pandoc chỉ lấy style, khổ giấy, lề, đầu trang và chân trang của file này. Repo vì vậy không chứa file khuôn nhị phân; muốn đổi khuôn thì sửa hằng số `PAGE`, `STYLES` trong module.
- **Thứ tự ghép:** `phan-dau/`, Mở đầu và chương 1–6 (`[0-9][0-9]-*.md`), trang "Tài liệu tham khảo", `phu-luc/`. README và các file quy tắc không được ghép.
- **Danh mục hình và bảng:** sinh từ chú thích `![Hình x.y. …](…)` và `**Bảng x.y.** …`, mỗi dòng lấy câu đầu của chú thích, thay vào hai dòng đánh dấu ở `phan-dau/03-danh-muc-hinh-bang.md`. Số trang là trường PAGEREF trỏ tới bookmark đặt ở hình hoặc bảng. Chú thích nằm trên một dòng như mẫu ở quy ước dưới, không thì không vào danh mục.
- **Trích dẫn:** `--citeproc` thay `[@key]` bằng số `[1]` theo [`ieee.csl`](ieee.csl) (CSL IEEE, ghim ở [docs/phien-ban.md](../phien-ban.md)). Danh mục tài liệu theo locale mặc định en-US của kiểu này (`et al.`, `Accessed:`), vì nguồn đều là tiếng Anh và kiểu IEEE chỉ dịch được một phần sang tiếng Việt.
- **Khối `> **[Bước định dạng]**`** (bìa, hai trang nhận xét) bị bỏ khỏi bản ghép và được in ra để nhắc làm tay.

Sau khi ghép, mở file bằng Word và chọn **Yes** khi Word hỏi cập nhật trường: mục lục (trường TOC), số trang của hai danh mục (PAGEREF) và số trang ở chân trang (PAGE) chỉ có số sau bước này. Việc còn làm tay trong Word: bìa và bìa phụ theo mẫu của khoa, hai trang "Nhận xét, đánh giá, cho điểm". Hai biểu đồ ở dạng SVG (Hình 5.2, Hình E.1) cần Word 2016 trở lên; pandoc chỉ tạo được ảnh PNG dự phòng khi máy có `rsvg-convert`, thiếu thì in cảnh báo nhưng vẫn ghi file.
