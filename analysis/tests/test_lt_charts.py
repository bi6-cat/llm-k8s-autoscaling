"""Test cho analysis/lt_charts.py (hình LT7, LT8).

Khái niệm: Dữ liệu LT8 dựng bằng _simulate của test_lt8_burn (đúng định dạng bộ đo ghi); dữ liệu LT7 là một
    CSV nhỏ cùng cột với lt7_hpa.
Mục đích: Kiểm phần chuẩn bị dữ liệu bằng số cụ thể (đường dự đoán r_w, chọn lượt có trễ, căn mốc theo lúc
    bơm, bỏ lần bơm không hợp lệ), và kiểm phần vẽ ở mức "chạy hết, ghi đủ file, chạy lại ra đúng cùng
    file" (không so pixel), như test_charts.
"""

from __future__ import annotations

import csv
import json
from pathlib import Path

import pytest

from analysis import lt7_hpa as l7
from analysis import lt_charts as lc
from analysis.tests.test_lt8_burn import _simulate


def test_window_pred_rises_holds_and_falls():
    # x = 0,3 bơm 360 s: cửa sổ 5m đầy sau 300 s, cửa sổ 1m xả hết 60 s sau khi gỡ
    assert lc.window_pred(-10, 0.3, 300, 360) == 0
    assert lc.window_pred(150, 0.3, 300, 360) == pytest.approx(0.15)
    assert lc.window_pred(360, 0.3, 300, 360) == pytest.approx(0.3)
    assert lc.window_pred(420, 0.3, 300, 360) == pytest.approx(0.24)
    assert lc.window_pred(400, 0.3, 60, 360) == pytest.approx(0.1)
    assert lc.window_pred(420, 0.3, 60, 360) == 0
    # Bơm ngắn hơn cửa sổ: đỉnh chỉ là x · dur / w
    assert lc.window_pred(100, 0.6, 300, 100) == pytest.approx(0.2)


def _lt7_csv(tmp: Path) -> Path:
    rows = [
        # c, rep, desired_end, formula_ok, clock, d_scrape, d_visible, d_wait, d_decide, d_ready
        (5, 1, 1, True, "", None, None, None, None, None),
        (15, 1, 2, True, "mono", 3.0, 0.5, 4.5, 8.0, 6.0),
        (15, 2, 2, True, "mono?", 2.0, 1.7, 4.5, 8.2, 5.0),
        (35, 1, 3, True, "mono", 1.0, 0.4, 2.0, 3.4, 7.0),
        (25, 1, 3, False, "mono", 4.0, 0.5, 0.1, 4.6, None),  # thiếu mốc Ready: không vẽ được thanh
    ]
    p = tmp / "lt7-hpa.csv"
    with p.open("w", newline="", encoding="utf-8") as fh:
        w = csv.DictWriter(fh, fieldnames=l7.COLUMNS, extrasaction="ignore")
        w.writeheader()
        for c, rep, end, ok, clock, s, v, wt, dec, rd in rows:
            w.writerow({"c": c, "rep": rep, "threshold": 10, "max_replicas": 3, "predicted": end,
                        "desired_end": end, "restarted": False, "formula_ok": ok, "clock": clock,
                        "d_scrape": s, "d_visible": v, "d_wait": wt, "d_decide": dec, "d_ready": rd,
                        "rescale_sizes": "" if c == 5 else str(end)})  # fmt: skip
    return p


def test_lt7_rows_parse_and_stage_runs_skip_unsure_clock(tmp_path):
    rows = lc.lt7_rows(_lt7_csv(tmp_path))
    assert rows[0]["c"] == 5 and rows[0]["d_scrape"] is None and rows[0]["formula_ok"] is True
    assert rows[4]["formula_ok"] is False and rows[1]["d_ready"] == 6.0
    runs, n_unsure, n_partial = lc.lt7_stage_runs(rows)
    # "mono?" (mốc không chắc) và lượt thiếu chặng bị bỏ, đếm riêng; còn lại sắp theo C
    assert [(r["c"], r["rep"]) for r in runs] == [(15, 1), (35, 1)]
    assert (n_unsure, n_partial) == (1, 1)
    # Lượt có pod restart bị bỏ như bảng của lt7_hpa, không đếm vào hai loại trên
    rows[3]["restarted"] = True
    runs, n_unsure, n_partial = lc.lt7_stage_runs(rows)
    assert [(r["c"], r["rep"]) for r in runs] == [(15, 1)] and (n_unsure, n_partial) == (1, 1)


def test_lt8_injections_align_to_injection(tmp_path):
    d = _simulate(tmp_path, every=2)  # x = 0,5, bơm ở T0 + 400 s trong 360 s
    [inj] = lc.lt8_injections(d)
    assert inj["x"] == 0.5 and inj["order"] == 1
    assert min(t for t, _ in inj["r5"]) >= -lc.PRE_S and max(t for t, _ in inj["r5"]) <= 360 + lc.POST_S
    # Trước lúc bơm tỷ lệ là 0; cuối lúc bơm cửa sổ 5m đã đầy, gần x
    assert all(v == 0 for t, v in inj["r5"] if t < 0)
    assert max(v for _, v in inj["r5"]) == pytest.approx(0.5, abs=0.02)


def test_lt8_groups_drop_invalid_injection(tmp_path):
    good = _simulate(tmp_path / "a", every=2)
    groups, log = lc.lt8_groups(good.parent)
    assert list(groups) == [0.5] and log == []
    [inj] = groups[0.5]
    # Fixture ghi μ = 2706 ms (x dự đoán 0,6) dù bơm đúng 1/2: x_pred phải lấy từ bảng, không từ dữ liệu
    assert inj["x_pred"] == pytest.approx(0.6, abs=0.001) and inj["dur"] == pytest.approx(360)
    a, b = inj["firing"]
    assert 180 <= a <= 180 + 3 + 5 + 15 + 15  # như test_lt8_burn: firing sau θ·300/x + 60 s cộng các trễ
    assert 360 + 36 - 5 <= b <= 360 + 36 + 3 + 5 + 15  # hết khi cửa sổ 1m xuống dưới θ: 60·(1 − θ/x) = 36 s
    bad = _simulate(tmp_path / "b", every=2)
    prom = json.loads((bad / "prom.json").read_text())
    prom["r1"] = []  # thiếu recording rule → analyze_rep đánh dấu không hợp lệ
    (bad / "prom.json").write_text(json.dumps(prom))
    groups, log = lc.lt8_groups(bad.parent)
    assert groups == {} and "thiếu mẫu recording rule" in log[0]


def test_main_writes_both_figures_reproducibly(tmp_path, capsys):
    lt7 = _lt7_csv(tmp_path)
    lt8 = _simulate(tmp_path / "s", every=2).parent
    _simulate(tmp_path / "s10", every=10)  # x = 0,1 ở phiên khác: không gộp vào hình
    assert list(lc.lt8_groups(lt8)[0]) == [0.5]
    args = ["--lt7", str(lt7), "--lt8", str(lt8), "--formats", "svg"]
    assert lc.main([*args, "--out", str(tmp_path / "o1")]) == 0
    assert lc.main([*args, "--out", str(tmp_path / "o2")]) == 0
    for name in ("lt7-hpa.svg", "lt8-burn.svg"):
        assert (tmp_path / "o1" / name).read_bytes() == (tmp_path / "o2" / name).read_bytes()
    assert "ghi" in capsys.readouterr().out


def test_main_without_valid_injection_fails(tmp_path, capsys):
    d = _simulate(tmp_path, every=2)
    (d / "load" / "requests.csv").unlink()
    assert lc.main(["--lt8", str(d.parent), "--out", str(tmp_path / "o")]) == 1
    assert "không có lần bơm hợp lệ" in capsys.readouterr().out
