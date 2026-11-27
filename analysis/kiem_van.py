"""Soát văn phong các mục luận văn (docs/luan-van/CC-SS-<ten>.md) theo các luật đếm được của quy tắc viết.

Khái niệm:
    Đây là một bộ "lint" cho văn bản: đọc file Markdown, tách thành khối (đoạn văn, mục danh sách, bảng),
    tách câu, rồi đối chiếu từng khối với các luật đo được bằng máy. Script chỉ báo cáo, không sửa file. Mỗi
    điểm in ra dạng `file:dòng [luật] trích đoạn`; tên luật kèm § của docs/luan-van/quy-tac-viet.md (hoặc
    README) để tra lý do và cách viết thay:
      - in đậm giữa câu, văn nói, ngôi (§3.2);
      - phóng đại (§3.3);
      - cụm sáo rỗng, câu đệm, động từ rỗng, bị động dịch máy, gạch dài, mũi tên, nhiều dấu ":" hoặc ";",
        hai đoạn liền mở bằng từ nối (§3.4);
      - chuyện nội bộ và công cụ AI, đường dẫn tới docs/ (§3.5);
      - quá 4 mã trong một đoạn, nhãn dàn ý TĐ/HG, mã biểu đồ C1–C6 (§4);
      - ngày tháng trong thân bài (§5);
      - dấu chấm thập phân, số dính đơn vị (README "Quy ước viết");
      - đoạn hoặc bảng có số mà không có comment nguồn ngay sau (README "Nguồn của mọi sự kiện và số liệu").
    Riêng độ dài và nhịp văn chỉ là gợi ý đọc lại, in ở phần riêng và không tính vào mã thoát, vì quy tắc viết
    không đặt trần cứng cho câu và đoạn (§3.2): câu > 45 chữ, đoạn > 8 câu, 3 đoạn ≤ 2 câu liền nhau (§3.2),
    ", nên" hơn một lần trong một đoạn (§3.4). Nếu tính vào mã thoát, người viết sẽ sửa cho về 0 và văn lại
    dài đều nhau.
    Comment HTML, tiêu đề, hình và khối code không được xét. Bảng, chú thích bảng ("**Bảng …**") và công thức
    riêng dòng ($$…$$) không bị xét như văn xuôi; chú thích và công thức cũng không bị đòi nguồn, vì nguồn
    đặt sau bảng hoặc sau đoạn giải thích công thức.
Mục đích: Bước soát tự động của checklist trước khi mở PR một mục (quy-tac-viet.md §10), để người viết và
    agent soát cùng một bộ luật. Luật nào cũng chỉ là cách đếm thô của quy tắc viết: tách câu và đoạn bằng
    luật đơn giản, và vài luật (từ nối, dấu hai chấm, chữ "agent" có thể là node agent của k3s) chỉ báo chỗ
    cần đọc lại. Vì vậy CI chạy test của module này nhưng không chạy soát trên docs/luan-van/.
Tham khảo: docs/luan-van/quy-tac-viet.md §3–§5, §10; docs/luan-van/README.md

Chạy (từ gốc repo):
    uv run --project analysis python -m analysis.kiem_van docs/luan-van/05-03-*.md
    uv run --project analysis python -m analysis.kiem_van          # mọi file mục docs/luan-van/CC-SS-*.md
Mặc định in tối đa 5 điểm mỗi luật; thêm --all để in hết. Mã thoát (như ruff): 0 khi không còn điểm nào,
1 khi còn điểm, 2 khi không đọc được file; gợi ý đọc lại không làm đổi mã thoát.
"""

from __future__ import annotations

import argparse
import re
import sys
from collections import defaultdict
from dataclasses import dataclass
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
# File mục: CC-SS-<ten>.md (README "Tổ chức file"); README.md, quy-tac-viet.md… không khớp mẫu này.
SECTION_GLOB = "docs/luan-van/[0-9][0-9]-*.md"

# Mã định danh của đồ án (quy-tac-viet.md §4): S1, S4, A1–A4, KB1–KB3, ĐG1–ĐG3, VH1–VH6, LT1–LT8, L0, L2,
# F1–F7, N1–N8 (kèm a/b cho chỉ tiêu con, ví dụ N3a), V0–V2.
CODES = re.compile(r"\b(S[14]|A[1-4]|KB[1-3]|ĐG[1-3]|VH[1-6]|LT[1-8]|L[02]|F[1-7]|N[1-8][ab]?|V[0-2])\b")
# Comment nguồn đặt ngay sau đoạn hoặc bảng: <!-- nguồn: … --> (README).
SOURCE = re.compile(r"^\s*<!-- nguồn:")
# Mục danh sách: "- ", "* " hoặc "1. " ở đầu dòng.
LIST_ITEM = re.compile(r"([-*]|\d+\.) ")
# Chỗ ngắt câu: dấu . ! ? rồi khoảng trắng; chỉ ngắt khi chữ tiếp theo là chữ hoa hoặc ký tự mở câu.
SENT_BREAK = re.compile(r"(?<=[.!?])\s+")
SENT_OPENERS = '*(`"“'
# Từ nối đầu đoạn (§3.4: hai đoạn liền không cùng mở bằng loại từ này); cho phép cụm in đậm đứng trước.
CONNECT = re.compile(
    r"^(\*\*[^*]+\*\*\s*)?(Bên cạnh đó|Ngoài ra|Hơn nữa|Không những thế|Như vậy|Đồng thời|Cụ thể)\b"
)

# (regex, luật) xét trên văn bản đã thay `code` bằng CODE, không phân biệt hoa thường.
PHRASES = [
    (r"đóng vai trò (quan trọng|then chốt|cốt lõi|chủ chốt)|yếu tố then chốt|chìa kho[áa]", "sáo rỗng §3.4"),
    (r"trong bối cảnh|ngày càng (phát triển|tăng|phổ biến)|phát triển mạnh mẽ", "sáo rỗng §3.4"),
    (
        r"(mang lại|đem lại) (nhiều )?(lợi ích|hiệu quả|giá trị)|\bgóp phần\b|\bhướng tới\b|nhằm mục đích"
        r"|với mục tiêu",
        "sáo rỗng §3.4",
    ),
    # [^.]{0,80}: hai vế nằm trong cùng một câu, cách nhau không quá 80 ký tự.
    (r"không (chỉ|những)\b[^.]{0,80}\bmà còn", "không chỉ… mà còn §3.4"),
    (
        r"một cách (hiệu quả|linh hoạt|toàn diện|tối ưu|đáng kể|rõ rệt|nhanh chóng|chính xác)",
        "một cách + tính từ §3.4",
    ),
    (
        r"\b(toàn diện|mạnh mẽ|vượt trội|liền mạch|vững chắc|tối ưu|hiệu quả cao|rõ rệt|đáng kể)\b",
        "từ to tát, cần số §3.4",
    ),
    (
        r"(điều này|qua đó) cho thấy|có thể thấy|đáng chú ý|điều đáng nói|nhìn chung|\btóm lại\b"
        r"|nói cách khác",
        "câu đệm §3.4",
    ),
    (r"\btiến hành\b|thực hiện việc|\bviệc\b[^.]{0,25}\bviệc\b", "động từ rỗng §3.4"),
    # "được … bởi …" trong cùng một vế câu (không qua dấu . , ;).
    (r"\bđược\b[^.,;]{1,40}\bbởi\b", "bị động dịch máy §3.4"),
    # "ổn" đứng riêng là văn nói, "ổn định" thì không; "khủng" cũng vậy với "khủng hoảng".
    (r"\b(khá|rất|cực kỳ|vô cùng|hết sức|ngon)\b|\bkhủng\b(?! hoảng)|\bổn\b(?! định)", "văn nói §3.2"),
    (r"\b(chứng minh|hoàn hảo|luôn luôn)\b", "phóng đại §3.3"),
    (r"\b(tôi|chúng tôi|chúng ta|bạn)\b|\bta (thấy|có)\b", "ngôi §3.2"),
    # "agent" có thể là node agent của k3s: đọc lại, không tự sửa. Không có "prompt": đó là thuật ngữ của LLM
    # (độ dài prompt, prefill). (?-i:…): tên người, mã việc Q1–Q8, TR1–TR8 và mã quyết định Dxx phân biệt hoa
    # thường, để "trình bày" không bị bắt nhầm là tên "Trình".
    (
        r"\b(AI agent|subagent|agent|Claude|ChatGPT|Copilot|Gemini|phiên làm việc"
        r"|nhật ký (làm việc|cá nhân))\b|\bPR ?#?\d+\b|\bcommit [0-9a-f]{7}\b"
        r"|(?-i:\bD\d{2}\b|\b(Q|TR)[1-8]\b|\bTrình\b|\bQuang\b)",
        "nội bộ / công cụ AI §3.5",
    ),
    # TĐ1–TĐ3, HG1–HG5 là nhãn của dàn ý; C1–C6 là tên nội bộ của biểu đồ (trong bài dùng số hình).
    (r"(?-i:\b(TĐ[1-3]|HG[1-5]|C[1-6])\b)", "nhãn dàn ý, mã biểu đồ §4"),
]
# Xét trên văn bản gốc, vì đường dẫn thường nằm trong `code`: docs/… và link Markdown tương đối
# (thân bài không link tới docs/, luận văn phải đọc được độc lập). Link http(s) và #neo thì bỏ qua;
# (?<![\w.:/-]): "docs/" nằm giữa một URL (keda.sh/docs/) thì không tính.
RAW_RULES = [
    (r"(?<![\w.:/-])docs/|\]\((?!https?://|#)[^)]*\)", "đường dẫn nội bộ §3.5"),
]


@dataclass(frozen=True)
class Block:
    """Một đoạn văn, một mục danh sách hoặc một bảng: kind ("para" | "table"), dòng đầu, dòng cuối (từ 1)."""

    kind: str
    start: int
    end: int
    text: str


@dataclass(frozen=True)
class Issue:
    line: int
    rule: str
    excerpt: str


@dataclass
class Report:
    issues: list[Issue]
    hints: list[Issue]  # gợi ý đọc lại về độ dài và nhịp văn: in riêng, không tính vào mã thoát
    words: int  # số chữ văn xuôi (không tính bảng, chú thích bảng)
    paras: int
    sentences: int
    bold_open: int  # số đoạn mở bằng cụm in đậm (§3.2: chỉ dùng khi có từ 3 khía cạnh song song)


def blocks(lines: list[str]) -> list[Block]:
    """Tách file thành khối; bỏ comment HTML, tiêu đề, hình và khối code."""
    out: list[Block] = []
    cur: list[str] = []
    kind, start, in_code, in_cmt = "", 0, False, False

    def flush(end: int) -> None:
        nonlocal cur, kind
        if cur:
            out.append(Block(kind, start, end, " ".join(cur)))
        cur, kind = [], ""

    for i, raw in enumerate(lines, 1):
        s = raw.strip()
        if in_cmt:  # đang trong comment nhiều dòng: bỏ tới dòng có -->
            in_cmt = "-->" not in s
            continue
        if s.startswith(("```", "~~~")):  # hai kiểu rào khối code của Markdown
            in_code = not in_code
            flush(i - 1)
            continue
        if in_code:
            continue
        if s.startswith("<!--"):
            in_cmt = "-->" not in s
            flush(i - 1)
            continue
        s = re.sub(r"<!--.*?-->", "", s).strip()  # comment nằm giữa dòng
        if "<!--" in s:  # comment mở ở cuối dòng và đóng ở dòng sau: giữ phần chữ trước nó
            s, in_cmt = s[: s.index("<!--")].strip(), True
        k = "table" if s.startswith("|") else "para"
        if LIST_ITEM.match(s):  # mỗi mục danh sách là một khối, không dính vào đoạn dẫn
            flush(i - 1)
        if not s or s.startswith(("#", "![")) or (kind and k != kind):
            flush(i - 1)
            if not s or s.startswith(("#", "![")):
                continue
        if not cur:
            kind, start = k, i
        cur.append(s)
    flush(len(lines))
    return out


def split_sentences(text: str) -> list[str]:
    """Tách câu: ngắt sau . ! ? khi chữ kế tiếp viết hoa (kể cả Đ, Ư…) hoặc là * ( ` " “."""
    out, start = [], 0
    for m in SENT_BREAK.finditer(text):
        nxt = text[m.end() : m.end() + 1]
        if nxt and (nxt.isupper() or nxt in SENT_OPENERS):
            out.append(text[start : m.start()])
            start = m.end()
    out.append(text[start:])
    return [x for x in out if x.strip()]


def has_source(lines: list[str], block: Block) -> bool:
    """Có comment nguồn ngay sau khối không.

    Giữa khối và comment nguồn chỉ được có dòng trống, comment khác (ví dụ trạng thái soát) và các mục danh
    sách đi liền: nguồn của một danh sách, và của đoạn dẫn vào danh sách, đặt một lần sau cả danh sách.
    Gặp nội dung khác (đoạn sau, tiêu đề, bảng) trước khi thấy nguồn thì coi là thiếu. Comment nguồn đặt
    ngay cuối dòng của khối cũng được tính (blocks() đã cắt nó khỏi văn bản).
    """
    if any("<!-- nguồn:" in ln for ln in lines[block.start - 1 : block.end]):
        return True
    in_cmt = False
    for raw in lines[block.end :]:  # block.end đếm từ 1, nên đây là các dòng sau khối
        s = raw.strip()
        if in_cmt:
            in_cmt = "-->" not in s
            continue
        if SOURCE.match(s):
            return True
        if s.startswith("<!--"):
            in_cmt = "-->" not in s
        elif s and not LIST_ITEM.match(s) and not raw[:1].isspace():  # mục danh sách, dòng nối tiếp thụt lề
            return False
    return False


def check_text(text: str) -> Report:
    """Soát nội dung một file Markdown; trả về các điểm cần xem và thống kê độ dài."""
    lines = text.split("\n")
    issues: list[Issue] = []
    hints: list[Issue] = []
    words = sents_n = prev_end = short_run = 0
    prev_connect = False  # đoạn văn xuôi liền trước có mở bằng từ nối không
    all_blocks = blocks(lines)

    def add(blk: Block, rule: str, excerpt: str, hint: bool = False) -> None:
        (hints if hint else issues).append(Issue(blk.start, rule, excerpt))

    for blk in all_blocks:
        t = blk.text
        # Có số thì phải có nguồn. Trước khi tìm chữ số, bỏ: `code`, công thức $…$, số mục và số hình
        # ("mục 5.5", "Chương 5", "Hình 3.1", "§5", "5.5.4a": dấu chấm + 1–2 chữ số; số thập phân viết bằng
        # dấu phẩy, phân nghìn có 3 chữ số), và mã định danh (VH4, N7…). (?i:…): "Mục", "mục" đều bỏ.
        bare = re.sub(
            r"`[^`]*`|\$[^$]*\$|(?i:\b(mục|chương|hình|bảng|phụ lục)) [\d.]*\d[a-z]?|§ ?[\d.]*\d[a-z]?|"
            r"\b\d\.\d{1,2}(\.\d{1,2})?[a-z]?\b|" + CODES.pattern,
            "",
            t,
        )
        if not t.startswith(("**Bảng", "$$")) and re.search(r"\d", bare) and not has_source(lines, blk):
            add(blk, "thiếu nguồn README", t[:70])
        # Bảng, chú thích bảng và công thức riêng dòng không phải văn xuôi: chỉ xét nguồn (ở trên). Chúng
        # cũng ngắt chuỗi "hai đoạn liền", như tiêu đề (dòng "#" nằm giữa hai đoạn).
        # short_run (số đoạn ≤ 2 câu liền nhau) cũng ngắt ở đây và ở mục danh sách: đoạn dẫn ngắn trước bảng,
        # danh sách hay tiểu mục là cách viết đúng (§3.2).
        if blk.kind == "table" or t.startswith(("**Bảng", "$$")):
            prev_connect = False
            short_run = 0
            continue
        if any(ln.lstrip().startswith("#") for ln in lines[prev_end : blk.start - 1]):
            prev_connect = False
            short_run = 0
        prev_end = blk.end
        plain = re.sub(r"`[^`]*`", "CODE", t)  # để luật cụm từ không bắt chữ trong tên metric, tên file
        words += len(t.split())
        ss = split_sentences(t)
        sents_n += len(ss)
        for x in ss:
            if len(x.split()) > 45:
                add(blk, "câu > 45 chữ §3.2", f"{len(x.split())} chữ: {x[:60]}", hint=True)
        if LIST_ITEM.match(t):
            short_run = 0
        else:
            if len(ss) > 8:
                add(blk, "đoạn > 8 câu §3.2", f"{len(ss)} câu: {t[:50]}", hint=True)
            short_run = short_run + 1 if len(ss) <= 2 else 0
            if short_run == 3:  # báo một lần cho mỗi chuỗi, ở đoạn thứ ba
                add(blk, "3 đoạn ≤ 2 câu liền nhau §3.2", t[:50], hint=True)
        n_nen = len(re.findall(r", nên(?!\w)", plain))
        if n_nen > 1:
            add(blk, "lặp «, nên» trong đoạn §3.4", f"{n_nen} lần: {t[:50]}", hint=True)
        n_codes = len(CODES.findall(t))
        if n_codes > 4:
            add(blk, "> 4 mã/đoạn §4", f"{n_codes} mã: {t[:50]}")
        for rx, rule in PHRASES:
            for m in re.finditer(rx, plain, flags=re.I):
                add(blk, rule, f"«{m.group(0)}» …{plain[max(0, m.start() - 25) : m.end() + 25]}…")
        for rx, rule in RAW_RULES:
            for m in re.finditer(rx, t):
                add(blk, rule, f"«{m.group(0)}»")
        # In đậm sau một chữ khác trong cùng câu, tức nằm giữa câu; cụm in đậm mở câu, mở đoạn hay mở mục danh
        # sách thì được.
        if any(re.search(r"\S\s?\*\*[^*]+\*\*", re.sub(r"^([-*]|\d+\.)\s+", "", x)) for x in ss):
            add(blk, "in đậm giữa câu §3.2", t[:60])
        for ch, rule in (("—", "gạch dài — §3.4"), ("→", "mũi tên trong văn xuôi §3.4")):
            if ch in plain:
                add(blk, rule, f"{plain.count(ch)} lần: {t[:50]}")
        body = re.sub(r"^\*\*[^*]+\*\*", "", plain)  # dấu ":" trong cụm in đậm mở đoạn không tính
        if body.count(":") > 1 or body.count(";") > 1:
            add(blk, "nhiều : hoặc ; §3.4", f"{body.count(':')} ':' {body.count(';')} ';': {t[:45]}")
        connect = bool(CONNECT.match(t))
        if connect and prev_connect:
            add(blk, "2 đoạn liền mở bằng từ nối §3.4", t[:50])
        prev_connect = connect
        # Dự án chạy tháng 10–12, nên chỉ bắt dd/10–dd/12; bỏ phân số kiểu "3/10 lượt".
        for m in re.finditer(r"\b\d{1,2}/1[0-2](/20\d\d)?\b(?! (lượt|request|pod|ô|phiên))", plain):
            add(blk, "ngày tháng §5", m.group(0))
        # Dấu chấm thập phân chỉ bắt khi có đơn vị theo sau ("2.5 s"); "mục 2.5" là số mục.
        for m in re.finditer(r"(?<![\w.§/])\d+\.\d{1,2} ?(s|ms|%|GB|GiB|req/s|C|phút|giờ)(?!\w)", plain):
            add(blk, "dấu chấm thập phân README", m.group(0))
        # (?<!\w): số đứng riêng, không dính sau chữ cái, để "k3s", "K8s" không bị bắt.
        for m in re.finditer(r"(?<!\w)\d+(s|ms|GB|GiB|MB|phút|C)\b", plain):
            add(blk, "số dính đơn vị README", plain[max(0, m.start() - 4) : m.end()])
    paras = [b for b in all_blocks if b.kind == "para"]
    bold_open = sum(1 for b in paras if b.text.startswith("**") and not b.text.startswith("**Bảng"))
    return Report(issues, hints, words, len(paras), sents_n, bold_open)


def format_report(name: str, rep: Report, show_all: bool) -> str:
    """Dòng thống kê, rồi mỗi luật: số điểm và tối đa 5 điểm đầu (hoặc hết, nếu show_all). Gợi ý đọc lại in
    sau cùng, dưới một dòng tiêu đề riêng."""
    out = [
        f"== {name}: {rep.words} chữ văn xuôi, {rep.paras} đoạn, {rep.sentences} câu, "
        f"TB {rep.words / max(rep.sentences, 1):.1f} chữ/câu, {rep.bold_open} đoạn mở bằng in đậm"
    ]

    def group(found: list[Issue], indent: str) -> None:
        by_rule: dict[str, list[Issue]] = defaultdict(list)
        for it in found:
            by_rule[it.rule].append(it)
        for rule, items in by_rule.items():
            out.append(f"{indent}[{rule}] {len(items)}")
            out.extend(
                f"{indent}  {Path(name).name}:{it.line} {it.excerpt}"
                for it in (items if show_all else items[:5])
            )

    group(rep.issues, "  ")
    if rep.hints:
        out.append("  Gợi ý đọc lại (không tính vào mã thoát):")
        group(rep.hints, "    ")
    return "\n".join(out)


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description="Soát văn phong các mục luận văn (quy-tac-viet.md §3–§5).")
    ap.add_argument("files", nargs="*", help=f"file Markdown; bỏ trống thì soát {SECTION_GLOB}")
    ap.add_argument("--all", action="store_true", help="in mọi điểm, không chỉ 5 điểm đầu mỗi luật")
    args = ap.parse_args(argv)
    files = [Path(f) for f in args.files] or sorted(REPO.glob(SECTION_GLOB))
    if not files:
        print(f"Không có file nào để soát ({SECTION_GLOB})", file=sys.stderr)
        return 2
    total = n_hints = 0
    for f in files:
        try:
            # utf-8-sig: bỏ BOM mà vài trình soạn thảo trên Windows thêm vào đầu file.
            text = f.read_text(encoding="utf-8-sig")
        except (OSError, UnicodeDecodeError) as e:
            print(f"Không đọc được {f}: {e}", file=sys.stderr)
            return 2
        rep = check_text(text)
        print(format_report(str(f), rep, args.all))
        total += len(rep.issues)
        n_hints += len(rep.hints)
    print(f"Tổng: {total} điểm cần xem" + (f"; {n_hints} gợi ý đọc lại" if n_hints else ""))
    return 1 if total else 0


if __name__ == "__main__":
    sys.exit(main())
