"""Test cho analysis/kiem_van.py (soát văn phong luận văn, quy-tac-viet.md §10).

Khái niệm: Mỗi luật có ít nhất một đoạn vi phạm (phải bị bắt) và một đoạn viết đúng (không bị bắt), lấy theo
    cặp "Không viết / Viết thay" của quy-tac-viet.md §3–§5. Test chỉ xét luật đang kiểm, nên đoạn mẫu không
    cần sạch mọi luật khác. Phần sau kiểm cách tách khối, tách câu, tìm comment nguồn và CLI.
Mục đích: Giữ hành vi của bộ soát khi sửa regex: luật mới không được bắt nhầm cách viết đúng.
"""

from __future__ import annotations

import pytest

from analysis import kiem_van as kv


def rules(text: str) -> set[str]:
    return {i.rule for i in kv.check_text(text).issues}


def caught(text: str, rule: str) -> bool:
    """Có điểm nào thuộc luật có tên bắt đầu bằng `rule` không."""
    return any(r.startswith(rule) for r in rules(text))


SRC = "\n<!-- nguồn: x -->"

# (luật, đoạn vi phạm, đoạn viết đúng)
CASES = [
    ("câu > 35 chữ", " ".join(["chữ"] * 36) + ".", " ".join(["chữ"] * 35) + "."),
    ("đoạn ngoài 3–7 câu", "Câu một. Câu hai.", "Câu một. Câu hai. Câu ba."),
    ("đoạn ngoài 3–7 câu", " ".join(["Câu."] * 8), " ".join(["Câu."] * 7)),
    ("in đậm giữa câu", "Nhóm chọn **A2** làm cấu hình chính.", "**Cấu hình chính.** Nhóm chọn A2."),
    ("văn nói", "A2 chạy khá nhanh.", "A2 nhanh hơn S1."),
    ("văn nói", "Kết quả ổn.", "Kết quả ổn định."),
    ("ngôi", "Chúng tôi chọn A2.", "Nhóm chọn A2."),
    ("ngôi", "Ta thấy A2 nhanh hơn.", "Kết quả cho thấy A2 nhanh hơn."),
    ("phóng đại", "Kết quả chứng minh A2 tốt hơn.", "Trong điều kiện đo, A2 đạt SLO."),
    ("sáo rỗng", "KEDA đóng vai trò then chốt.", "KEDA quyết định số replica."),
    ("sáo rỗng", "Trong bối cảnh LLM ngày càng phổ biến.", "GPU thuê theo giờ vẫn tính tiền khi rảnh."),
    ("sáo rỗng", "Nhóm đo lại với mục tiêu so sánh.", "Nhóm đo lại để so sánh."),
    ("không chỉ… mà còn", "Hệ thống không chỉ nhanh mà còn rẻ.", "Hệ thống nhanh. Hệ thống cũng rẻ."),
    ("một cách + tính từ", "A2 scale một cách nhanh chóng.", "A2 scale trong 16,8 s."),
    ("từ to tát", "Giải pháp mạnh mẽ và vượt trội.", "Giải pháp dùng 4 GPU."),
    ("câu đệm", "Có thể thấy A2 nhanh hơn.", "A2 nhanh hơn S1."),
    ("động từ rỗng", "Nhóm tiến hành đo lại.", "Nhóm đo lại."),
    ("động từ rỗng", "Việc đo và việc ghi chạy song song.", "Đo và ghi chạy song song."),
    ("bị động dịch máy", "Log được ghi bởi runner.", "Runner ghi log."),
    (
        "gạch dài",
        "A2 — cấu hình chính — scale theo tải.",
        "A2 (cấu hình chính) scale theo tải trong 80–82 s.",
    ),
    ("mũi tên", "Cảnh báo đi Prometheus → Alertmanager.", "Cảnh báo đi từ Prometheus tới Alertmanager."),
    ("mũi tên", "Luồng A → B.", "| Luồng | A → B |"),
    (
        "nhiều : hoặc ;",
        "Pha nền: tải thấp. Pha tăng: tải cao.",
        "**Cách đo:** pha nền tải thấp, pha tăng tải cao.",
    ),
    ("nhiều : hoặc ;", "A thấp; B cao; C vừa.", "A thấp; B cao, C vừa."),
    ("2 đoạn liền", "Ngoài ra, A đo.\n\nBên cạnh đó, B đo.", "Ngoài ra, A đo.\n\nB đo sau."),
    ("nội bộ", "Quang chạy lượt này.", "Nhóm trình bày kết quả của lượt này."),
    ("nội bộ", "Lỗi sửa ở PR #57 theo D68.", "Lỗi sửa trước phiên đo V2."),
    ("nội bộ", "Agent viết nháp mục này.", "Cờ `--agent-token` của k3s cấp quyền cho node."),
    ("đường dẫn nội bộ", "Chi tiết ở `docs/chi-tiet/04-van-hanh.md`.", "Chi tiết ở mục 3.5 [@sre2016]."),
    ("đường dẫn nội bộ", "Xem [thiết kế](../chi-tiet/04-van-hanh.md).", "Xem [KEDA](https://keda.sh/docs/)."),
    ("> 4 mã/đoạn", "A1, A2, A3, A4 và S1 cùng chạy KB1.", "A1, A2, A3 và A4 cùng chạy."),
    ("nhãn dàn ý", "Mục này phục vụ TĐ1 và HG4.", "Mục này phục vụ thông điệp thứ nhất."),
    ("nhãn dàn ý", "Biểu đồ C1 cho thấy năng lực.", "Hình 5.3 cho thấy năng lực 0,5 C."),
    ("ngày tháng", "Phiên đo chạy ngày 21/11.", "Có 3/10 lượt lỗi ở pha tăng đột ngột."),
    ("dấu chấm thập phân", "TTFT là 2.5 s.", "TTFT là 2,5 s, theo mục 2.5."),
    ("số dính đơn vị", "Cold start mất 180s.", "Cold start mất 180 s."),
    ("thiếu nguồn", "TTFT là 2,5 s.", "TTFT là 2,5 s." + SRC),
    ("thiếu nguồn", "| A2 | 2,5 s |", "| A2 | 2,5 s |\n" + SRC),
]


@pytest.mark.parametrize(("rule", "bad", "good"), CASES, ids=[f"{c[0]}-{i}" for i, c in enumerate(CASES)])
def test_rule_catches_bad_and_passes_good(rule: str, bad: str, good: str):
    assert caught(bad, rule), f"{rule} không bắt: {bad!r}"
    assert not caught(good, rule), f"{rule} bắt nhầm: {good!r} -> {rules(good)}"


def test_every_rule_has_a_case():
    """Mỗi luật khai báo trong module có ít nhất một ca trong CASES (luật đếm trong check_text kể cả)."""
    declared = {r.split(" §")[0].split(" README")[0] for _, r in kv.PHRASES + kv.RAW_RULES}
    covered = {c[0] for c in CASES}
    missing = [d for d in declared if not any(d.startswith(c) for c in covered)]
    assert not missing


def test_blocks_skip_comments_headings_images_and_code():
    lines = [
        "# Tiêu đề",
        "<!-- comment",
        "nhiều dòng rất khá -->",
        "![Hình 3.1. Sơ đồ](../images/png/a.png)",
        "```",
        "Chúng tôi trong code",
        "```",
        "Đoạn một dòng một",
        "dòng hai. <!-- giữa dòng -->",
        "",
        "| a | b |",
        "| 1 | 2 |",
        "- mục một",
        "- mục hai",
    ]
    got = [(b.kind, b.start, b.end, b.text) for b in kv.blocks(lines)]
    assert got == [
        ("para", 8, 9, "Đoạn một dòng một dòng hai."),
        ("table", 11, 12, "| a | b | | 1 | 2 |"),
        ("para", 13, 13, "- mục một"),
        ("para", 14, 14, "- mục hai"),
    ]


def test_split_sentences_breaks_only_before_capital_or_opener():
    # "ở" là chữ thường có dấu: không ngắt câu (regex cũ À-Ỹ gồm cả chữ thường nên ngắt nhầm).
    assert kv.split_sentences("Câu một v.v. ở đây. Đây là hai. **Ba** là ba. `x` là bốn.") == [
        "Câu một v.v. ở đây.",
        "Đây là hai.",
        "**Ba** là ba.",
        "`x` là bốn.",
    ]


def test_source_after_whole_list_covers_every_item():
    text = (
        "- A2 scale lên 4 replica.\n- S4 giữ 4 replica.\n  dòng nối tiếp 2 lần.\n\n- S1 giữ 1 replica.\n"
        + SRC
    )
    assert not caught(text, "thiếu nguồn")
    assert caught("- A2 scale lên 4 replica.\n- S4 giữ 4 replica.\n\nĐoạn sau." + SRC, "thiếu nguồn")


def test_numbers_in_codes_sections_and_formulas_need_no_source():
    assert not caught("Mục 5.5 nói về VH4 và N7. Công thức $p = 0,95$ ở Hình 3.1.", "thiếu nguồn")


def test_table_caption_and_display_formula_are_not_checked_as_prose():
    text = "**Bảng 5.1.** Kết quả 5 lượt, ngày 21/11 — rất khá\n\n| A2 | 2,5 s |\n" + SRC
    assert rules(text) == set()
    assert rules("$$t \\approx \\frac{300\\,\\theta}{x} + 60$$") == set()


def test_stats_count_prose_only():
    rep = kv.check_text("Câu một có bốn chữ. Câu hai.\n\n| bảng | không | đếm |\n\n**Mở.** Đoạn hai. Ba.")
    assert (rep.words, rep.paras, rep.sentences, rep.bold_open) == (11, 2, 4, 1)


def test_format_report_limits_to_five_per_rule_unless_all():
    rep = kv.check_text("\n\n".join(["Câu một."] * 7))
    short = kv.format_report("docs/luan-van/x.md", rep, show_all=False)
    assert "[đoạn ngoài 3–7 câu §3.2] 7" in short
    assert short.count("\n    x.md:") == 5  # dòng tiêu đề "== docs/luan-van/x.md:" không tính
    assert kv.format_report("x.md", rep, show_all=True).count("\n    x.md:") == 7


def test_main_exit_codes(tmp_path, capsys):
    clean = tmp_path / "03-01-sach.md"
    clean.write_text("# 3.1\n\nNhóm chọn A2. Nhóm đo lại. Kết quả giống nhau.\n", encoding="utf-8")
    dirty = tmp_path / "03-02-ban.md"
    dirty.write_text("Chúng tôi chọn A2. Nhóm đo lại. Kết quả giống nhau.\n", encoding="utf-8")
    assert kv.main([str(clean)]) == 0
    assert kv.main([str(clean), str(dirty)]) == 1
    out = capsys.readouterr().out
    assert "03-02-ban.md:1 «Chúng tôi»" in out
    assert out.rstrip().endswith("Tổng: 1 điểm cần xem")
    assert kv.main([str(tmp_path / "khong-co.md")]) == 2
