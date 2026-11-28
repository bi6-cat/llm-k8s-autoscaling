"""Test cho analysis/luan_van.py (ghép luận văn ra .docx theo khuôn T).

Khái niệm: Phần lớn test chạy trên chuỗi Markdown và một .docx giả dựng bằng zipfile, nên không cần pandoc
    (CI không cài pandoc, docs/phien-ban.md). Test cuối ghép thật toàn bộ docs/luan-van/, chỉ chạy khi máy có
    pandoc.
Mục đích: Kiểm câu đầu của chú thích, id gắn vào hình và bảng, danh mục có trường PAGEREF trỏ đúng bookmark,
    thứ tự các phần (tài liệu tham khảo trước phụ lục), và reference doc mang đúng khuôn T.
"""

from __future__ import annotations

import io
import shutil
import zipfile
from pathlib import Path

import pytest

from analysis import luan_van as lv


def test_first_sentence_stops_outside_brackets_and_drops_citations():
    assert (
        lv.first_sentence("Ba cách (minh hoạ. xem) cấp GPU [@a; @b]. Câu hai.")
        == "Ba cách (minh hoạ. xem) cấp GPU."
    )
    assert lv.first_sentence("TTFT p95 0,24 s") == "TTFT p95 0,24 s"
    assert lv.first_sentence("Model 3B v0.31.0, 4 GPU. Hết") == "Model 3B v0.31.0, 4 GPU."


def test_mark_captions_tags_figures_and_tables_but_not_code():
    md = "\n".join(
        [
            "![Hình 3.1. Kiến trúc tổng thể. Ba luồng.](../images/png/02.png)",
            "",
            "**Bảng G.2.** Ba dashboard [@x]. Chi tiết",
            "",
            "```text",
            "**Bảng 9.9.** trong khối code",
            "```",
            "<!-- comment nhiều dòng",
            "**Bảng 9.8.** trong comment -->",
            "![Hình 3.2. Sơ đồ.](a.png)",
            "<!-- nguồn: a.py -->",
            "**Bảng 3.4a.** số tạm",
        ]
    )
    found, unknown = [], []
    out = lv.mark_captions(md, found, unknown)
    assert found == [
        ("Hình", "3.1", "Hình 3.1. Kiến trúc tổng thể.", "hinh_3_1"),
        ("Bảng", "G.2", "Bảng G.2. Ba dashboard.", "bang_G_2"),
        ("Hình", "3.2", "Hình 3.2. Sơ đồ.", "hinh_3_2"),
    ]
    assert unknown == ["**Bảng 3.4a.** số tạm"]
    # Dòng trống sau hình: comment nguồn ngay dưới không làm pandoc mất chú thích của hình
    assert "![Hình 3.2. Sơ đồ.](a.png){#hinh_3_2}\n\n<!-- nguồn: a.py -->" in out
    assert out.splitlines()[0].endswith("02.png){#hinh_3_1}")
    assert (
        '::: {custom-style="Table Caption"}\n[**Bảng G.2.**]{#bang_G_2} Ba dashboard [@x]. Chi tiết\n:::'
        in out
    )
    assert "**Bảng 9.9.** trong khối code" in out and "**Bảng 9.8.** trong comment -->" in out


def test_caption_list_points_pageref_at_pandoc_bookmark():
    entries = [("Hình", "1.1", "Hình 1.1. A.", "hinh_1_1"), ("Bảng", "1.1", "Bảng 1.1. **B**.", "bang_1_1")]
    figs = lv.caption_list(entries, "Bảng")
    assert figs.startswith('::: {custom-style="Danh muc"}\nBảng 1.1. B. `<w:r><w:tab/></w:r>')
    assert "PAGEREF _bang_1_1 \\h" in figs and "hinh_1_1" not in figs
    assert lv.caption_list(entries, "Phụ lục") == ""


def test_prepare_orders_parts_and_fills_lists(tmp_path):
    src = tmp_path / "lv"
    (src / "phan-dau").mkdir(parents=True)
    (src / "phu-luc").mkdir()
    (src / "phan-dau/03-danh-muc.md").write_text(
        "<!-- @danh-muc-hinh -->\n\n<!-- @danh-muc-bang -->\n", encoding="utf-8"
    )
    (src / "phan-dau/01-bia.md").write_text(
        "> **[Bước định dạng]** Bìa\n> theo mẫu.\n\n# Lời cảm ơn\n", encoding="utf-8"
    )
    (src / "01-01-a.md").write_text("![Hình 1.1. Một. Hai.](x.png)\n", encoding="utf-8")
    (src / "06-01-b.md").write_text("**Bảng 6.1.** Kết quả\n", encoding="utf-8")
    (src / "phu-luc/a-x.md").write_text("# Phụ lục A\n", encoding="utf-8")
    (src / "README.md").write_text("không ghép\n", encoding="utf-8")
    out = tmp_path / "out"
    out.mkdir()
    files, notes = lv.prepare(lv.sources(src), out)
    assert [f.name for f in files] == [
        "00-01-bia.md",
        "01-03-danh-muc.md",
        "02-01-01-a.md",
        "03-06-01-b.md",
        "tai-lieu-tham-khao.md",
        "05-a-x.md",
    ]
    assert notes == ["Còn làm tay: 01-bia.md: > **[Bước định dạng]** Bìa\n> theo mẫu."]
    assert "Bước định dạng" not in files[0].read_text(encoding="utf-8")
    lists = files[1].read_text(encoding="utf-8")
    assert "Hình 1.1. Một." in lists and "PAGEREF _hinh_1_1" in lists and "PAGEREF _bang_6_1" in lists
    assert "{#refs}" in files[4].read_text(encoding="utf-8")


def test_prepare_stops_on_duplicate_numbers(tmp_path):
    (tmp_path / "01-01-a.md").write_text("**Bảng 1.1.** A\n\n**Bảng 1.1.** B\n", encoding="utf-8")
    with pytest.raises(SystemExit, match="bang_1_1"):
        lv.prepare([tmp_path / "01-01-a.md"], tmp_path)


def _fake_default_docx() -> bytes:
    """Bộ khung tối thiểu giống reference.docx mặc định của pandoc: đủ các phần mà reference_doc sửa."""
    buf = io.BytesIO()
    with zipfile.ZipFile(buf, "w") as z:
        z.writestr("[Content_Types].xml", '<Types xmlns="x"></Types>')
        z.writestr("word/_rels/document.xml.rels", '<Relationships xmlns="y"></Relationships>')
        z.writestr("word/settings.xml", '<w:settings xmlns:w="w"><w:zoom/></w:settings>')
        z.writestr(
            "word/document.xml",
            '<w:document xmlns:w="w"><w:body><w:p/><w:sectPr><w:footnotePr/>'
            "</w:sectPr></w:body></w:document>",
        )
        z.writestr(
            "word/styles.xml",
            '<w:styles xmlns:w="w"><w:docDefaults><w:rPrDefault/></w:docDefaults>'
            '<w:style w:type="paragraph" w:styleId="Heading1"><w:name w:val="old"/>'
            '</w:style><w:style w:type="paragraph" w:styleId="Caption"/>'
            '<w:style w:type="paragraph" w:styleId="Keep"><w:name w:val="k"/></w:style>'
            '<w:style w:type="paragraph" w:styleId="Heading10"/></w:styles>',
        )
    return buf.getvalue()


def test_reference_doc_applies_khuon_t():
    z = zipfile.ZipFile(io.BytesIO(lv.reference_doc(_fake_default_docx())))
    styles = z.read("word/styles.xml").decode("utf-8")
    assert styles.count('w:styleId="Heading1"') == 1 and 'w:val="old"' not in styles
    assert 'w:styleId="Heading10"' in styles  # chỉ thay style trùng id, không đụng id có cùng tiền tố
    assert 'w:styleId="Keep"><w:name w:val="k"/>' in styles  # style tự đóng (Caption) không nuốt style sau
    assert '<w:style w:type="paragraph" w:styleId="Heading2">' in styles  # style có sẵn: không customStyle
    assert 'w:customStyle="1" w:styleId="Compact"' in styles
    assert '<w:sz w:val="26"/>' in styles and 'w:line="276"' in styles  # 13 pt, giãn dòng 1,15
    doc = z.read("word/document.xml").decode("utf-8")
    assert 'w:w="11906" w:h="16838"' in doc and 'w:left="1701"' in doc and "rIdKhuonTFooter" in doc
    assert "Nguyễn Ngọc Quang" in z.read("word/footer1.xml").decode("utf-8")
    assert "footer1.xml" in z.read("word/_rels/document.xml.rels").decode("utf-8")
    assert "/word/header1.xml" in z.read("[Content_Types].xml").decode("utf-8")
    assert '<w:updateFields w:val="true"/>' in z.read("word/settings.xml").decode("utf-8")


def test_keep_case_wraps_only_title_fields():
    bib = "@a{k,\n  title     = {{GQA}: Training},\n  booktitle = {Adv. NeurIPS},\n  author = {A B}\n}\n"
    assert lv.keep_case(bib) == (
        "@a{k,\n  title     = {{{GQA}: Training}},\n  booktitle = {{Adv. NeurIPS}},\n  author = {A B}\n}\n"
    )


def test_missing_bookmarks():
    buf = io.BytesIO()
    with zipfile.ZipFile(buf, "w") as z:
        z.writestr(
            "word/document.xml",
            '<w:bookmarkStart w:id="1" w:name="_hinh_1_1"/>'
            "<w:instrText> PAGEREF _hinh_1_1 \\h </w:instrText>"
            "<w:instrText> PAGEREF _bang_1_1 \\h </w:instrText>",
        )
    assert lv.missing_bookmarks(buf.getvalue()) == ["_bang_1_1"]


@pytest.mark.skipif(shutil.which("pandoc") is None, reason="cần pandoc (không có trong CI)")
def test_build_whole_thesis(tmp_path):
    out = tmp_path / "luan-van.docx"
    notes = lv.build(out, lv=Path(__file__).resolve().parents[2] / "docs/luan-van")
    assert out.stat().st_size > 100_000 and all("Bước định dạng" in n for n in notes)
