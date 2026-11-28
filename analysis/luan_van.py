"""Ghép bản nguồn luận văn (docs/luan-van/*.md) thành một file .docx theo khuôn T.

Khái niệm:
    pandoc đọc Markdown và ghi .docx. Định dạng (lề, phông, kiểu tiêu đề, đầu và chân trang) không viết trong
    Markdown mà lấy từ một "reference doc": file .docx mẫu, pandoc chỉ đọc các style và phần sectPr (khổ giấy,
    lề, tham chiếu đầu trang, chân trang) của nó. Module tự dựng reference doc khuôn T từ bản mặc định của
    pandoc (`--print-default-data-file reference.docx`), nên repo không phải chứa file nhị phân.
    Trường (field) của Word là đoạn mã Word tự tính lại: TOC (mục lục), PAGEREF (số trang của một bookmark),
    PAGE (số trang hiện tại). pandoc chỉ chèn mã; Word điền số khi cập nhật trường. Reference doc bật
    `updateFields`, nên khi mở file Word hỏi có cập nhật trường không, chọn Yes là mục lục và hai danh mục có
    số trang.
Mục đích: Bước định dạng của docs/luan-van/README.md mục "Ghép thành .docx": khuôn T (quy-tac-viet §1),
    danh mục hình và bảng sinh từ chú thích (chỉ lấy câu đầu, kèm số trang), trang "Tài liệu tham khảo" kiểu
    IEEE đặt giữa chương 6 và phụ lục. Bìa, bìa phụ và hai trang nhận xét theo mẫu của khoa vẫn làm tay trong
    Word; khối `> **[Bước định dạng]**` đánh dấu các chỗ đó bị bỏ khỏi bản ghép và được in ra để nhắc.
Tham khảo: docs/luan-van/quy-tac-viet.md §1, §6, §7; docs/luan-van/README.md mục "Ghép thành .docx"

Chạy (từ gốc repo; cần pandoc 3.13 theo docs/phien-ban.md):
    uv run --project analysis python -m analysis.luan_van ../luan-van.docx
"""

from __future__ import annotations

import argparse
import io
import os
import re
import subprocess
import sys
import tempfile
import zipfile
from pathlib import Path

LV = Path("docs/luan-van")

# Chú thích theo README của docs/luan-van: hình `![Hình 3.1. …](…)` ở đầu dòng, bảng `**Bảng 3.1.** …`.
# Phụ lục đánh số bằng chữ cái (Hình G.1).
NUM = r"([A-Z]|\d+)\.(\d+)"
FIGURE = re.compile(r"^!\[Hình " + NUM + r"\.")
TABLE = re.compile(r"^\*\*Bảng " + NUM + r"\.\*\*\s*(.*)$")
# Khối nhắc việc của bước định dạng: dòng trích dẫn mở bằng `> **[Bước định dạng]**`, tới dòng trống.
FORMAT_NOTE = re.compile(r"^> \*\*\[Bước định dạng\]\*\*.*?(?:\n(?!\n)>.*)*(?:\n|$)", re.M)

# ── Khuôn T (quy-tac-viet §1). Đơn vị của Word: twip = 1/20 pt = 1/1440 inch (1 cm ≈ 567 twip);
#    cỡ chữ tính bằng nửa pt (26 = 13 pt); giãn dòng `line` tính theo 1/240 dòng (276 = 1,15 dòng).
PAGE = {
    "w": 11906,
    "h": 16838,
    "top": 1418,
    "bottom": 1418,
    "left": 1701,
    "right": 1134,
}  # A4, lề 2,5/2,5/3/2 cm
TEXT_WIDTH = PAGE["w"] - PAGE["left"] - PAGE["right"]  # 9071 twip = 16 cm: điểm dừng tab sát lề phải
AUTHORS = "Trần Đức Trình – Nguyễn Ngọc Quang"
HEADER_TEXT = "Đồ án tốt nghiệp Đại học"

FONT = (
    "<w:rFonts " + " ".join(f'w:{a}="Times New Roman"' for a in ("ascii", "hAnsi", "eastAsia", "cs")) + "/>"
)
# Cỡ 13 pt và giãn dòng đặt ở docDefaults, không đặt ở style Normal: style bảng chỉ thắng docDefaults, không
# thắng style đoạn, nên đặt ở đây thì chữ trong bảng mới nhận được 12 pt và dòng đơn từ style "Table".
DOC_DEFAULTS = f"""<w:docDefaults><w:rPrDefault><w:rPr>{FONT}<w:sz w:val="26"/><w:szCs w:val="26"/>
<w:lang w:val="vi-VN" w:eastAsia="en-US" w:bidi="ar-SA"/></w:rPr></w:rPrDefault>
<w:pPrDefault><w:pPr><w:spacing w:before="0" w:after="120" w:line="276" w:lineRule="auto"/></w:pPr>
</w:pPrDefault>
</w:docDefaults>"""

# Style có sẵn của Word: không gắn customStyle, để Word nhận là style của nó (mục lục dùng "toc 1"…).
BUILTIN = {"BodyText", "Heading1", "Heading2", "Heading3", "Heading4", "TOCHeading", "Caption"}
BUILTIN |= {"TOC1", "TOC2", "TOC3", "Header", "Footer"}


def _para_style(sid, name, based="Normal", ppr="", rpr="", extra=""):
    custom = "" if sid in BUILTIN else ' w:customStyle="1"'
    return (
        f'<w:style w:type="paragraph"{custom} w:styleId="{sid}"><w:name w:val="{name}"/>'
        f'<w:basedOn w:val="{based}"/>{extra}<w:qFormat/><w:pPr>{ppr}</w:pPr><w:rPr>{rpr}</w:rPr></w:style>'
    )


_TAB_RIGHT = f'<w:tabs><w:tab w:val="right" w:leader="dot" w:pos="{TEXT_WIDTH}"/></w:tabs>'
_HEADING = '<w:keepNext/><w:keepLines/><w:ind w:firstLine="0"/>'
# Mỗi style ghi đè trọn style cùng styleId trong reference doc mặc định của pandoc.
STYLES = {
    "Normal": (
        '<w:style w:type="paragraph" w:default="1" w:styleId="Normal"><w:name w:val="Normal"/><w:qFormat/>'
        "</w:style>"
    ),
    # Văn xuôi: căn đều, thụt đầu dòng 1,27 cm. Compact (ô bảng, danh sách liền) không thụt, căn trái.
    "BodyText": _para_style("BodyText", "Body Text", ppr='<w:ind w:firstLine="720"/><w:jc w:val="both"/>'),
    "FirstParagraph": _para_style("FirstParagraph", "First Paragraph", based="BodyText"),
    "Compact": _para_style("Compact", "Compact", ppr='<w:spacing w:before="20" w:after="20"/>'),
    # Chương: 16 pt, đậm, căn giữa, sang trang mới. Cấp 2: 13 pt đậm. Cấp 3: 13 pt đậm nghiêng.
    "Heading1": _para_style(
        "Heading1",
        "heading 1",
        extra='<w:next w:val="BodyText"/>',
        ppr=f'{_HEADING}<w:pageBreakBefore/><w:spacing w:before="0" w:after="240"/>'
        '<w:jc w:val="center"/><w:outlineLvl w:val="0"/>',
        rpr='<w:b/><w:bCs/><w:sz w:val="32"/><w:szCs w:val="32"/>',
    ),
    "Heading2": _para_style(
        "Heading2",
        "heading 2",
        extra='<w:next w:val="BodyText"/>',
        ppr=f'{_HEADING}<w:spacing w:before="240" w:after="120"/><w:outlineLvl w:val="1"/>',
        rpr="<w:b/><w:bCs/>",
    ),
    "Heading3": _para_style(
        "Heading3",
        "heading 3",
        extra='<w:next w:val="BodyText"/>',
        ppr=f'{_HEADING}<w:spacing w:before="120" w:after="120"/><w:outlineLvl w:val="2"/>',
        rpr="<w:b/><w:bCs/><w:i/><w:iCs/>",
    ),
    "Heading4": _para_style(
        "Heading4",
        "heading 4",
        extra='<w:next w:val="BodyText"/>',
        ppr=f'{_HEADING}<w:outlineLvl w:val="3"/>',
        rpr="<w:i/><w:iCs/>",
    ),
    "TOCHeading": _para_style(
        "TOCHeading", "TOC Heading", based="Heading1", ppr='<w:outlineLvl w:val="9"/>'
    ),  # cấp 9 = không vào mục lục
    # Chú thích: 13 pt, nghiêng, căn giữa; tên bảng ở trên bảng nên giữ liền với bảng (keepNext).
    "Caption": _para_style(
        "Caption",
        "caption",
        ppr='<w:spacing w:before="60" w:after="240"/><w:jc w:val="center"/>',
        rpr="<w:i/><w:iCs/>",
    ),
    "TableCaption": _para_style(
        "TableCaption",
        "Table Caption",
        based="Caption",
        ppr='<w:keepNext/><w:spacing w:before="240" w:after="60"/>',
    ),
    "ImageCaption": _para_style("ImageCaption", "Image Caption", based="Caption"),
    "Figure": _para_style("Figure", "Figure", ppr='<w:jc w:val="center"/>'),
    "CaptionedFigure": _para_style(
        "CaptionedFigure",
        "Captioned Figure",
        based="Figure",
        ppr='<w:keepNext/><w:spacing w:before="120" w:after="0"/>',
    ),
    # Dòng của danh mục hình và bảng: số trang căn phải, dẫn bằng dấu chấm.
    "Danhmuc": _para_style("Danhmuc", "Danh muc", ppr=f'{_TAB_RIGHT}<w:ind w:left="1134" w:hanging="1134"/>'),
    "TOC1": _para_style(
        "TOC1", "toc 1", ppr=f'{_TAB_RIGHT}<w:spacing w:before="120" w:after="0"/>', rpr="<w:b/>"
    ),
    "TOC2": _para_style("TOC2", "toc 2", ppr=f'{_TAB_RIGHT}<w:ind w:left="260"/><w:spacing w:after="0"/>'),
    "TOC3": _para_style("TOC3", "toc 3", ppr=f'{_TAB_RIGHT}<w:ind w:left="520"/><w:spacing w:after="0"/>'),
    "SourceCode": _para_style(
        "SourceCode",
        "Source Code",
        ppr='<w:wordWrap w:val="off"/><w:spacing w:after="0" w:line="240" w:lineRule="auto"/>'
        '<w:shd w:val="clear" w:color="auto" w:fill="F2F2F2"/>',
    ),
    "VerbatimChar": (
        '<w:style w:type="character" w:customStyle="1" w:styleId="VerbatimChar">'
        '<w:name w:val="Verbatim Char"/><w:rPr><w:rFonts w:ascii="Consolas" w:hAnsi="Consolas"/>'
        '<w:sz w:val="22"/><w:szCs w:val="22"/></w:rPr></w:style>'
    ),
    "Header": _para_style(
        "Header",
        "header",
        ppr='<w:jc w:val="center"/><w:spacing w:after="0"/>',
        rpr='<w:i/><w:sz w:val="24"/><w:szCs w:val="24"/>',
    ),
    "Footer": _para_style(
        "Footer",
        "footer",
        ppr=f'<w:tabs><w:tab w:val="right" w:pos="{TEXT_WIDTH}"/></w:tabs><w:spacing w:after="0"/>',
        rpr='<w:sz w:val="24"/><w:szCs w:val="24"/>',
    ),
    # Bảng: chữ 12 pt dòng đơn, kẻ khung, dòng tiêu đề in đậm và lặp lại khi bảng sang trang.
    "Table": (
        '<w:style w:type="table" w:default="1" w:styleId="Table"><w:name w:val="Table"/>'
        '<w:basedOn w:val="TableNormal"/><w:qFormat/>'
        '<w:pPr><w:spacing w:before="20" w:after="20" w:line="240" w:lineRule="auto"/></w:pPr>'
        '<w:rPr><w:sz w:val="24"/><w:szCs w:val="24"/></w:rPr><w:tblPr><w:tblBorders>'
        + "".join(
            f'<w:{s} w:val="single" w:sz="4" w:space="0" w:color="auto"/>'
            for s in ("top", "left", "bottom", "right", "insideH", "insideV")
        )
        + '</w:tblBorders><w:tblCellMar><w:left w:w="85" w:type="dxa"/><w:right w:w="85" w:type="dxa"/>'
        '</w:tblCellMar></w:tblPr><w:tblStylePr w:type="firstRow"><w:rPr><w:b/><w:bCs/></w:rPr>'
        "<w:trPr><w:tblHeader/></w:trPr></w:tblStylePr></w:style>"
    ),
}

_REL = "http://schemas.openxmlformats.org/officeDocument/2006/relationships"
_W = "http://schemas.openxmlformats.org/wordprocessingml/2006/main"
_RUN_FIELD = (
    '<w:r><w:fldChar w:fldCharType="begin"/></w:r><w:r><w:instrText xml:space="preserve"> {code} '
    '</w:instrText></w:r><w:r><w:fldChar w:fldCharType="separate"/></w:r><w:r><w:t>{shown}</w:t></w:r>'
    '<w:r><w:fldChar w:fldCharType="end"/></w:r>'
)
HEADER_XML = (
    f'<?xml version="1.0" encoding="UTF-8" standalone="yes"?><w:hdr xmlns:w="{_W}" xmlns:r="{_REL}">'
    f'<w:p><w:pPr><w:pStyle w:val="Header"/></w:pPr><w:r><w:t>{HEADER_TEXT}</w:t></w:r></w:p></w:hdr>'
)
FOOTER_XML = (
    f'<?xml version="1.0" encoding="UTF-8" standalone="yes"?><w:ftr xmlns:w="{_W}" xmlns:r="{_REL}">'
    f'<w:p><w:pPr><w:pStyle w:val="Footer"/></w:pPr><w:r><w:t>{AUTHORS}</w:t></w:r><w:r><w:tab/></w:r>'
    + _RUN_FIELD.format(code="PAGE", shown="1")
    + "</w:p></w:ftr>"
)
SECT_PR = (
    f'<w:sectPr><w:headerReference w:type="default" r:id="rIdKhuonTHeader"/>'
    f'<w:footerReference w:type="default" r:id="rIdKhuonTFooter"/>'
    f'<w:pgSz w:w="{PAGE["w"]}" w:h="{PAGE["h"]}"/><w:pgMar w:top="{PAGE["top"]}" w:right="{PAGE["right"]}" '
    f'w:bottom="{PAGE["bottom"]}" w:left="{PAGE["left"]}" w:header="709" w:footer="709" w:gutter="0"/>'
    '<w:footnotePr><w:numRestart w:val="eachSect"/></w:footnotePr></w:sectPr>'
)


def reference_doc(default_docx: bytes) -> bytes:
    """Từ reference doc mặc định của pandoc, trả về reference doc khuôn T (bytes của file .docx)."""
    src = zipfile.ZipFile(io.BytesIO(default_docx))
    files = {n: src.read(n) for n in src.namelist()}
    styles = files["word/styles.xml"].decode("utf-8")
    styles = re.sub(
        r"<w:docDefaults>.*?</w:docDefaults>", lambda _: DOC_DEFAULTS, styles, count=1, flags=re.S
    )
    for (
        sid
    ) in STYLES:  # bỏ bản cũ của từng style (kể cả dạng tự đóng `<w:style …/>`), thêm bản khuôn T vào cuối
        old = rf'<w:style\b[^>]*?\bw:styleId="{sid}"(?:[^>/]|/(?!>))*(?:/>|>.*?</w:style>)\s*'
        styles = re.sub(old, "", styles, flags=re.S)
    styles = styles.replace("</w:styles>", "".join(STYLES.values()) + "</w:styles>")
    files["word/styles.xml"] = styles.encode("utf-8")
    doc = files["word/document.xml"].decode("utf-8")
    if 'xmlns:r="' not in doc[:2000]:
        doc = doc.replace("<w:document ", f'<w:document xmlns:r="{_REL}" ', 1)
    files["word/document.xml"] = re.sub(
        r"<w:sectPr>.*?</w:sectPr>", lambda _: SECT_PR, doc, flags=re.S
    ).encode()
    files["word/header1.xml"], files["word/footer1.xml"] = HEADER_XML.encode(), FOOTER_XML.encode()
    rels = files["word/_rels/document.xml.rels"].decode("utf-8")
    rels = rels.replace(
        "</Relationships>",
        f'<Relationship Id="rIdKhuonTHeader" Type="{_REL}/header" Target="header1.xml"/>'
        f'<Relationship Id="rIdKhuonTFooter" Type="{_REL}/footer" Target="footer1.xml"/>'
        "</Relationships>",
    )
    files["word/_rels/document.xml.rels"] = rels.encode("utf-8")
    ct = files["[Content_Types].xml"].decode("utf-8")
    ct = ct.replace(
        "</Types>",
        "".join(
            f'<Override PartName="/word/{p}1.xml" ContentType="application/'
            f'vnd.openxmlformats-officedocument.wordprocessingml.{p}+xml"/>'
            for p in ("header", "footer")
        )
        + "</Types>",
    )
    files["[Content_Types].xml"] = ct.encode("utf-8")
    settings = files["word/settings.xml"].decode(
        "utf-8"
    )  # Word hỏi cập nhật trường (TOC, PAGEREF) khi mở file
    files["word/settings.xml"] = re.sub(
        r"(<w:settings\b[^>]*>)", r'\1<w:updateFields w:val="true"/>', settings, count=1
    ).encode("utf-8")
    out = io.BytesIO()
    with zipfile.ZipFile(out, "w", zipfile.ZIP_DEFLATED) as z:
        for name, data in files.items():
            z.writestr(name, data)
    return out.getvalue()


def first_sentence(text: str) -> str:
    """Câu đầu chú thích, bỏ trích dẫn `[@key]`: tới dấu chấm đầu tiên ngoài ngoặc và có dấu cách sau."""
    text = re.sub(r"\s*\[@[^\]]*\]", "", text).strip()
    depth = 0
    for i, ch in enumerate(text):
        depth += {"(": 1, "[": 1, ")": -1, "]": -1}.get(ch, 0)
        if ch == "." and depth == 0 and (i + 1 == len(text) or text[i + 1] == " "):
            return text[: i + 1]
    return text


def _figure_alt(line: str) -> str | None:
    """Phần trong `![…]` của dòng hình; ngoặc vuông lồng nhau (trích dẫn) được giữ."""
    depth, i = 1, 2
    while i < len(line) and depth:
        depth += {"[": 1, "]": -1}.get(line[i], 0)
        i += 1
    return line[2 : i - 1] if depth == 0 else None


def _anchor(kind: str, chap: str, num: str) -> str:
    """Id của hình hoặc bảng trong Markdown; chỉ chữ, số và gạch dưới để làm được tên bookmark của Word."""
    return f"{kind}_{chap}_{num}"


def bookmark(anchor: str) -> str:
    """Tên bookmark pandoc 3.13 ghi vào .docx cho một id: thêm "_" ở đầu (bookmark ẩn của Word)."""
    return "_" + anchor


def mark_captions(md: str, found: list[tuple[str, str, str, str]], unknown: list[str] | None = None) -> str:
    """Gắn id vào từng hình và bảng để danh mục dẫn số trang tới đó; tên bảng nhận style "Table Caption".

    pandoc bỏ span rỗng, nên id đặt ở thuộc tính của hình (`![…](…){#id}`) và ở span bọc nhãn "Bảng x.y.".
    Sau dòng hình luôn có một dòng trống: pandoc chỉ coi ảnh là hình có chú thích khi ảnh đứng một mình
    thành một đoạn, mà nhiều hình có comment nguồn nằm ngay dòng dưới.
    found nhận thêm (loại, số, câu đầu, id) theo thứ tự xuất hiện; unknown nhận các dòng trông như chú thích
    mà không đúng mẫu (ví dụ số tạm "Bảng 3.4a"). Dòng trong khối code và comment HTML giữ nguyên.
    """
    out, fence, comment = [], None, False
    for line in md.split("\n"):
        f = re.match(r"^\s*(```|~~~)", line)
        if f and not comment:
            fence = None if fence == f.group(1) else (fence or f.group(1))
        skip = fence is not None or comment
        if "<!--" in line or comment:  # comment HTML nhiều dòng: bỏ qua tới dòng có "-->"
            comment = line.rfind("<!--") > line.rfind("-->")
        if skip or f:
            out.append(line)
            continue
        m = FIGURE.match(line)
        if m and line.rstrip().endswith(")") and (alt := _figure_alt(line)) is not None:
            name = _anchor("hinh", m.group(1), m.group(2))
            num = f"{m.group(1)}.{m.group(2)}"
            found.append(("Hình", num, f"Hình {num}. " + first_sentence(alt[m.end() - 2 :]), name))
            line = line.rstrip() + f"{{#{name}}}\n"
        elif m := TABLE.match(line):
            name = _anchor("bang", m.group(1), m.group(2))
            num = f"{m.group(1)}.{m.group(2)}"
            found.append(("Bảng", num, f"Bảng {num}. " + first_sentence(m.group(3)), name))
            label = f"**Bảng {num}.**"
            line = f'::: {{custom-style="Table Caption"}}\n[{label}]{{#{name}}}{line[len(label) :]}\n:::'
        elif unknown is not None and re.match(r"^(!\[Hình|\*\*Bảng) ", line):
            unknown.append(line[:60])
        out.append(line)
    return "\n".join(out)


def caption_list(entries: list[tuple[str, str, str, str]], kind: str) -> str:
    """Danh mục một loại (Hình hoặc Bảng): mỗi dòng gồm câu đầu của chú thích, tab, số trang (PAGEREF)."""
    lines = []
    for k, _num, text, name in entries:
        if k != kind:
            continue
        text = re.sub(r"\*\*", "", text)  # "**Bảng 3.1.**" in đậm trong bài, trong danh mục thì không
        # Dấu cách trước khối openxml: chú thích kết thúc bằng mã inline (`LLMSLOBurnFast`) thì hai dấu ` liền
        # nhau sẽ thành một dấu mở dài hơn và nuốt mất khối XML.
        page = (
            " `<w:r><w:tab/></w:r>"
            + _RUN_FIELD.format(code=f"PAGEREF {bookmark(name)} \\h", shown="?")
            + "`{=openxml}"
        )
        lines.append(text + page)
    if not lines:
        return ""
    return '::: {custom-style="Danh muc"}\n' + "\n\n".join(lines) + "\n:::"


def sources(lv: Path = LV) -> list[Path]:
    """Thứ tự các phần theo quy-tac-viet §1: phần đầu, Mở đầu và chương 1–6, phụ lục."""
    return (
        sorted((lv / "phan-dau").glob("[0-9]*.md"))
        + sorted(lv.glob("[0-9][0-9]-*.md"))
        + sorted((lv / "phu-luc").glob("*.md"))
    )


REFS_PAGE = "# Tài liệu tham khảo {.unnumbered}\n\n::: {#refs}\n:::\n"


def prepare(files: list[Path], outdir: Path) -> tuple[list[Path], list[str]]:
    """Ghi bản đã xử lý của từng file vào outdir; trả về các file theo thứ tự và các dòng cần người ghép xem.

    Dừng nếu hai chú thích trùng số: cả hai dòng danh mục sẽ trỏ về cùng một chỗ mà không báo gì.
    """
    texts, entries, notes = {}, [], []
    for p in files:
        md, unknown = p.read_text(encoding="utf-8"), []
        notes += [f"Còn làm tay: {p.name}: {n.strip()[:110]}" for n in FORMAT_NOTE.findall(md)]
        texts[p] = mark_captions(FORMAT_NOTE.sub("", md), entries, unknown)
        notes += [f"Chú thích không đúng mẫu, không vào danh mục: {p.name}: {u}" for u in unknown]
    names = [e[3] for e in entries]
    if dup := sorted({n for n in names if names.count(n) > 1}):
        raise SystemExit(f"Chú thích trùng số: {', '.join(dup)}")
    refs = outdir / "tai-lieu-tham-khao.md"
    refs.write_text(REFS_PAGE, encoding="utf-8")
    body = [p for p in texts if p.parent.name != "phu-luc"]
    out = []
    for p in [*body, refs, *[p for p in texts if p not in body]]:  # tài liệu tham khảo đứng trước phụ lục
        if p is refs:
            out.append(refs)
            continue
        md = texts[p].replace("<!-- @danh-muc-hinh -->", caption_list(entries, "Hình"))
        md = md.replace("<!-- @danh-muc-bang -->", caption_list(entries, "Bảng"))
        out.append(outdir / f"{len(out):02d}-{p.name}")
        out[-1].write_text(md, encoding="utf-8")
    return out, notes


def build(output: Path, lv: Path = LV, pandoc: str = "pandoc") -> list[str]:
    """Ghép toàn bộ luận văn ra output; trả về các khối nhắc việc còn phải làm tay trong Word."""
    with tempfile.TemporaryDirectory() as tmp:
        tmp = Path(tmp)
        ref = tmp / "khuon-t.docx"
        # Bản mặc định ghi ra file: `-o -` không đổ nhị phân ra stdout mà tạo file tên "-".
        subprocess.run([pandoc, "-o", str(ref), "--print-default-data-file", "reference.docx"], check=True)
        ref.write_bytes(reference_doc(ref.read_bytes()))
        files, notes = prepare(sources(lv), tmp)
        # pandoc tìm hình theo --resource-path: đường dẫn hình viết tương đối với docs/luan-van, riêng phụ lục
        # tương đối với phu-luc/. Dùng os.pathsep vì pandoc tách bằng ";" trên Windows, ":" ở nơi khác.
        res = os.pathsep.join(str(d.resolve()) for d in (lv, lv / "phu-luc"))
        bib = tmp / "tai-lieu.bib"
        bib.write_text(keep_case((lv / "tai-lieu.bib").read_text(encoding="utf-8")), encoding="utf-8")
        subprocess.run(
            [
                pandoc,
                *map(str, files),
                "--from=markdown",
                f"--resource-path={res}",
                "--citeproc",
                f"--bibliography={bib}",
                f"--csl={lv / 'ieee.csl'}",
                # Không đặt `lang`: citeproc dùng locale en-US mặc định của ieee.csl, nên danh mục ghi
                # "et al.", "Accessed: Nov. 27, 2026" như chuẩn IEEE, không lẫn "và c.s." với
                # "[Online]. Available at" (ieee.csl chỉ dịch một phần). Ngôn ngữ soát chính tả của
                # văn bản là vi-VN, đặt ở docDefaults của reference doc.
                "--metadata=link-citations:true",
                f"--reference-doc={ref}",
                "-o",
                str(tmp / "out.docx"),
            ],
            check=True,
        )
        docx = (tmp / "out.docx").read_bytes()
    # Kiểm trước khi ghi đè output. pandoc bản khác đặt tên bookmark khác thì danh mục sẽ hiện
    # "Error! Bookmark not defined".
    missing = missing_bookmarks(docx)
    if missing:
        raise SystemExit(f"{len(missing)} trường PAGEREF không có bookmark, ví dụ {missing[0]}")
    output.write_bytes(docx)
    return notes


def keep_case(bib: str) -> str:
    """Bọc thêm một lớp ngoặc nhọn quanh tiêu đề, tên hội nghị, tạp chí, giữ cách viết hoa của file .bib.

    Với tài liệu tiếng Anh, pandoc đổi tiêu đề BibTeX sang sentence case, kể cả tên hội nghị ("Advances in
    neural information processing systems"); phần nằm trong ngoặc nhọn thì giữ nguyên. Mỗi trường nằm trên
    một dòng, như mọi mục của tai-lieu.bib.
    """
    return re.sub(
        r"^(\s*(?:title|booktitle|journal|series)\s*=\s*)\{(.*)\}(,?)\s*$", r"\1{{\2}}\3", bib, flags=re.M
    )


def missing_bookmarks(docx: bytes) -> list[str]:
    """Các bookmark được trường PAGEREF nhắc tới mà không có trong document.xml."""
    xml = zipfile.ZipFile(io.BytesIO(docx)).read("word/document.xml").decode("utf-8")
    have = set(re.findall(r'<w:bookmarkStart\b[^>]*\bw:name="([^"]+)"', xml))
    return [n for n in re.findall(r"PAGEREF (\S+)", xml) if n not in have]


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("output", type=Path, help="file .docx ghi ra (nên đặt ngoài repo)")
    ap.add_argument("--pandoc", default="pandoc")
    a = ap.parse_args(argv)
    notes = build(a.output, pandoc=a.pandoc)
    print(
        f"Đã ghi {a.output}. Mở bằng Word, chọn Yes khi được hỏi cập nhật trường (mục lục, trang danh mục)."
    )
    for n in notes:
        print(n)
    return 0


if __name__ == "__main__":
    sys.exit(main())
