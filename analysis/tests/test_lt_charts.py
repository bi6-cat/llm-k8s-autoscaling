"""Test cho analysis/lt_charts.py (hình LT5–LT8).

Khái niệm: Dữ liệu LT8 dựng bằng _simulate của test_lt8_burn (đúng định dạng bộ đo ghi); dữ liệu LT5, LT6,
    LT7 là CSV nhỏ cùng cột với lt5_little, lt6_gpu_util, lt7_hpa.
Mục đích: Kiểm phần chuẩn bị dữ liệu bằng số cụ thể (cửa sổ LT5 bị bỏ theo lý do, nhóm màu theo nguồn,
    kết luận "tách được" của LT6, đường dự đoán r_w, chọn lượt có trễ, căn mốc theo lúc bơm, bỏ lần bơm
    không hợp lệ), và kiểm phần vẽ ở mức "chạy hết, ghi đủ file, chạy lại ra đúng cùng file" (không so
    pixel), như test_charts.
"""

from __future__ import annotations

import csv
import json
from collections.abc import Sequence
from pathlib import Path
from typing import Any

import pytest

from analysis import lt5_little as l5
from analysis import lt6_gpu_util as l6
from analysis import lt7_hpa as l7
from analysis import lt_charts as lc
from analysis.tests.test_lt8_burn import _simulate


def _write(p: Path, columns: Sequence[str], rows: Sequence[dict[str, Any]]) -> Path:
    with p.open("w", newline="", encoding="utf-8") as fh:
        w = csv.DictWriter(fh, fieldnames=columns, extrasaction="ignore")
        w.writeheader()
        w.writerows(rows)
    return p


def _lt5_csv(tmp: Path) -> Path:
    def win(src, env, run, window, *, ok=True, valid=True, pred=7.0, srv=7.2, wait=0.0, se=0.9):
        dev = "" if srv == "" else srv / pred - 1
        return {"source": src, "env": env, "run_id": run, "attempt": "attempt-1" if env == "sim" else "",
                "valid": valid, "window": window, "applicable": ok, "L_pred": pred, "L_server": srv,
                "waiting_mean": wait, "se_sampling": se if wait < 1 else "", "dev_server": dev}  # fmt: skip

    rows = [
        win("capacity-1.5b.json", "home", "lambda-1", "measure", pred=2.0, srv=2.3, se=0.29),
        win("capacity.json", "home", "S1-CONST14-1", "measure", valid=False, pred=211, srv=182, wait=166),
        win("tr7-kb2-sim-2", "sim", "A2-KB2-1", "pre"),
        win("tr7-kb2-sim-2", "sim", "A2-KB2-1", "main", pred=16.1, srv=16.1),  # chồng lên pre: bỏ
        win("tr7-kb2-sim-2", "sim", "S1-KB2-1", "spike", ok=False, pred=70.6, srv=143.6, wait=128),
        win("tr7-kb2-sim-2", "sim", "S1-KB2-1", "drop", ok=False, pred=15.6, srv=47.0, wait=36),
        win("mp-final-w2", "sim", "S1-CONST2-1", "steady", pred=57.4, srv=37.0, wait=22),
        win("mp-final-w2", "sim", "S1-CONST4-1", "steady", srv=""),  # thiếu L_server: bỏ
        win("mp-final-w2", "sim", "S1-CONST6-1", "steady", srv=0.0),  # 0 không đặt được lên thang log: bỏ
    ]
    return _write(tmp / "lt5-little.csv", l5.COLUMNS, rows)


def test_lt5_points_skip_by_reason_and_parse_types(tmp_path):
    rows = lc.read_rows(_lt5_csv(tmp_path), lc.LT5_TEXT, ("valid", "applicable"))
    assert rows[0]["run_id"] == "lambda-1" and rows[0]["valid"] is True and rows[0]["L_pred"] == 2.0
    assert rows[1]["valid"] is False and rows[1]["se_sampling"] is None  # có hàng đợi: không có SE
    pts, skipped = lc.lt5_points(rows)
    assert [(r["run_id"], r["window"]) for r in pts] == [
        ("lambda-1", "measure"), ("S1-CONST14-1", "measure"), ("A2-KB2-1", "pre"), ("S1-CONST2-1", "steady"),
    ]  # fmt: skip
    assert skipped == {
        "có request lỗi": 2, "main (chồng lên pre, spike, drop)": 1, "thiếu số liệu": 1,
        "có L_server = 0 (thang log)": 1,
    }  # fmt: skip
    # Không có lý do nào thì không ghi lý do đó
    assert lc.lt5_points(rows[:3])[1] == {}


def test_source_group_and_queued():
    assert lc.source_group({"source": "capacity-1.5b.json", "env": "home"}) == "nhà, model 1,5B"
    assert lc.source_group({"source": "capacity.json", "env": "home"}) == "nhà, model 0,5B"
    assert lc.source_group({"source": "tr7-kb2-sim-2", "env": "sim"}) == "simulator"
    # Nguồn chưa có trong bảng, kể cả trùng tên file với nguồn ở nhà (ĐG1 trên V2 cũng ghi capacity.json):
    # ghi môi trường và tên file, vẽ màu xám, không nhận nhầm là model 0,5B
    other = {"source": "capacity.json", "env": "v2"}
    assert lc.source_group(other) == "v2, capacity.json"
    assert lc.GROUP_COLOR.get(lc.source_group(other), lc.OTHER_COLOR) == lc.OTHER_COLOR
    rows = [other, {"source": "x", "env": "sim"}, {"source": "capacity.json", "env": "home"}]
    assert lc._ordered_groups(rows) == ["nhà, model 0,5B", "simulator", "v2, capacity.json"]
    # LT5 gộp mọi phiên simulator (cùng cấu hình); LT6 tách từng phiên, như lt6_gpu_util.summary
    sims = [{"source": "a", "env": "sim"}, {"source": "b", "env": "sim"}]
    assert lc._ordered_groups(sims) == ["simulator"]
    assert lc._ordered_groups(sims, lc.lt6_group) == ["simulator (a)", "simulator (b)"]
    # Cùng quy ước với lt5_little.capacity_level: thiếu waiting coi như có hàng đợi
    assert lc.queued({"waiting_mean": None}) and lc.queued({"waiting_mean": 1.0})
    assert not lc.queued({"waiting_mean": 0.99})


def test_comma_log_labels_minor_ticks_only_on_narrow_axis():
    fig, ax = lc.plt.subplots()
    ax.set_yscale("log")
    lc._comma_log(ax, "y")
    major, minor = ax.yaxis.get_major_formatter(), ax.yaxis.get_minor_formatter()
    ax.set_ylim(0.2, 0.9)  # hẹp hơn một bậc 10: vạch phụ 2, 3, 5 có nhãn, dấu phẩy
    assert (minor(0.3), minor(0.5), minor(0.4)) == ("0,3", "0,5", "")
    ax.set_ylim(1, 300)  # rộng: chỉ vạch chính có nhãn
    assert (major(10), minor(20)) == ("10", "")
    lc.plt.close(fig)


def _lt6_rows() -> list[dict[str, Any]]:
    def lvl(src, load, band, util, l_srv, *, wait=0.0, valid=True):
        return {"source": src, "env": "home", "run_id": f"l-{load}", "valid": valid, "load": load,
                "band": band, "gpu_util": util, "util_pred": 1.0 if wait < 1 else None, "L_server": l_srv,
                "waiting_mean": wait, "a1_target_pct": 70.0,
                "a2_target": 21.0 if "1.5b" in src else 23.0}  # fmt: skip

    a, b = "capacity-1.5b.json", "capacity.json"
    return [
        lvl(a, 0.17, "khác", 0.89, 2.0),
        lvl(a, 0.5, "vừa", 1.0, 9.0),
        lvl(a, 0.67, "vừa", 1.0, 10.0),
        lvl(a, 1.17, "quá tải", 1.0, 50.0, wait=20, valid=False),
        lvl(b, 0.32, "vừa", 0.96, 4.0),
        lvl(b, 0.64, "vừa", 1.0, 8.0),
        lvl(b, 1.12, "quá tải", 0.9996, 60.0, wait=50),
    ]


def test_separation_text_per_model():
    rows = _lt6_rows()
    # util: max(vừa) = 1,0 không nhỏ hơn min(quá tải) ở cả hai model
    assert lc.separation_text(rows, "gpu_util") == "không tách được tải vừa / quá tải"
    assert lc.separation_text(rows, "L_server") == "tách được, hở 5,0× (1,5B), 7,5× (0,5B)"
    # Một model tách được, model kia không: ghi riêng, không mở đầu bằng "tách được"
    rows[-1]["L_server"] = 5.0
    assert lc.separation_text(rows, "L_server") == "1,5B: hở 5,0×; 0,5B: không tách được"
    # Thiếu nhóm quá tải ở mọi model: không có gì để kết luận
    assert lc.separation_text([r for r in rows if r["band"] != "quá tải"], "L_server") == ""


def test_main_writes_lt5_lt6_reproducibly(tmp_path, capsys):
    lt5 = _lt5_csv(tmp_path)
    lt6 = _write(tmp_path / "lt6-gpu-util.csv", l6.COLUMNS, _lt6_rows())
    args = ["--lt5", str(lt5), "--lt6", str(lt6), "--formats", "svg,png"]
    assert lc.main([*args, "--out", str(tmp_path / "o1")]) == 0
    assert lc.main([*args, "--out", str(tmp_path / "o2")]) == 0
    for name in ("lt5-little.svg", "lt5-little.png", "lt6-gpu-util.svg", "lt6-gpu-util.png"):
        assert (tmp_path / "o1" / name).read_bytes() == (tmp_path / "o2" / name).read_bytes()
    capsys.readouterr()
    # CSV chỉ có cửa sổ bị bỏ: không ghi hình, báo lỗi
    empty = _write(tmp_path / "e.csv", l5.COLUMNS, [{"source": "s", "env": "sim", "applicable": False}])
    assert lc.main(["--lt5", str(empty), "--out", str(tmp_path / "o3")]) == 1
    assert "không có cửa sổ nào vẽ được" in capsys.readouterr().out
    assert not (tmp_path / "o3").exists()
    # Một input hỏng không chặn hình khác: LT6 vẫn vẽ, vẫn báo file đã ghi, rồi mới báo lỗi LT5
    assert lc.main(["--lt5", str(empty), "--lt6", str(lt6), "--out", str(tmp_path / "o4")]) == 1
    out = capsys.readouterr().out
    assert "ghi" in out and "LT5:" in out and (tmp_path / "o4" / "lt6-gpu-util.svg").exists()


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
