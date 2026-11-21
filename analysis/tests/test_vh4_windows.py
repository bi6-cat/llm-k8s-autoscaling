"""Test cho analysis/vh4_windows.py (VH4, mục 5.5).

Khái niệm: Dựng một lượt VH4 GIẢ đúng định dạng experiments/ops/vh.py ghi: timeline.json (mốc theo giây UNIX),
    load/loadgen.json, load/requests.csv. Tải 1 request mỗi giây trong 300 s; chặn Prometheus ở 100 s, gỡ ở
    250 s; các request gửi trong [150, 160) có TTFT 3 s (xấu).
Mục đích: Kiểm ranh giới ba khoảng (theo mốc của timeline, xếp request theo lịch gửi) và các khoảng 1 phút,
    gồm khoảng cuối bị cắt khi thời lượng không chia hết cho 60 s.
"""

from __future__ import annotations

import csv
import json
from pathlib import Path

import pytest

from analysis import vh4_windows as vh

T0 = 1_800_000_000.0


def test_windows_follow_block_and_unblock_marks():
    marks = {"settled": T0 - 5, "block_prometheus": T0 + 100, "unblocked": T0 + 250}
    assert vh.windows(T0, T0 + 300, marks) == [
        ("truoc_chan", T0, T0 + 100),
        ("dang_chan", T0 + 100, T0 + 250),
        ("sau_go", T0 + 250, T0 + 300),
        ("ca_luot", T0, T0 + 300),
    ]
    with pytest.raises(KeyError):
        vh.windows(T0, T0 + 300, {"block_prometheus": T0 + 100})  # lượt dừng giữa chừng, chưa gỡ chặn


def test_minutes_cut_last_window_at_end():
    assert vh.minutes(0, 150) == [(0, 60), (60, 120), (120, 150)]
    assert vh.minutes(0, 120) == [(0, 60), (60, 120)]


def _run(tmp_path: Path) -> Path:
    run = tmp_path / "ops-vh4-20261118-183127"
    (run / "load").mkdir(parents=True)
    timeline = [
        {"t": T0 - 6, "event": "settled", "replicas": 1},
        {"t": T0 + 100, "event": "block_prometheus", "replicas_before": 1},
        {"t": T0 + 117, "event": "fallback_reached", "seconds": 17},
        {"t": T0 + 250, "event": "unblocked"},
    ]
    (run / "timeline.json").write_text(json.dumps(timeline), encoding="utf-8")
    lg = {"t0_unix": T0, "duration_s": 300.0, "rate_rps": 1.0}
    (run / "load" / "loadgen.json").write_text(json.dumps(lg), encoding="utf-8")
    with open(run / "load" / "requests.csv", "w", encoding="utf-8", newline="") as fh:
        w = csv.writer(fh)
        w.writerow(["id", "t_sched", "t_send", "t_first", "t_last", "n_out", "error"])
        for i in range(300):
            t = i + 0.5
            ttft = 3.0 if 150 <= t < 160 else 0.2
            w.writerow([i, t, t, t + ttft, t + ttft + 15 * 0.025, 16, ""])
    return run


def test_report_splits_requests_by_schedule_into_the_three_windows(tmp_path):
    out = vh.report(_run(tmp_path)).splitlines()
    assert out[0].endswith("/ops-vh4-20261118-183127")
    assert out[1] == f"t0={T0:.1f} dur=300.0 rate=1.0 n=300"
    assert "  fallback_reached   rel_t0=   117.0 s" in out  # mốc tính từ t0, không từ lúc chặn
    rows = {line.split()[0]: line for line in out if line.split()[0] in ("truoc_chan", "dang_chan", "sau_go")}
    assert "[   0.0,  100.0) n=  100 err=  0 SLO=100.00%" in rows["truoc_chan"]
    # 10 request xấu trong 150 request của khoảng đang chặn
    assert "[ 100.0,  250.0) n=  150 err=  0 SLO= 93.33%" in rows["dang_chan"]
    assert "TPOT p50=25.0 p95=25.0 ms" in rows["sau_go"]
    minutes = out[out.index("theo phut (t tu t0):") + 1 :]
    assert [line.split(")")[0].strip() for line in minutes] == [
        "[    0,   60",
        "[   60,  120",
        "[  120,  180",
        "[  180,  240",
        "[  240,  300",
    ]
    assert "SLO= 83.33%" in minutes[2]  # 10 xấu / 60


def test_report_warns_when_block_comes_before_t0(tmp_path):
    run = _run(tmp_path)
    assert not any(line.startswith("CẢNH BÁO") for line in vh.report(run).splitlines())
    timeline = json.loads((run / "timeline.json").read_text(encoding="utf-8"))
    timeline[1]["t"] = T0 - 3  # máy tạo tải khởi động chậm: chặn trước khi tải bắt đầu
    (run / "timeline.json").write_text(json.dumps(timeline), encoding="utf-8")
    assert any(line.startswith("CẢNH BÁO: mốc không theo thứ tự") for line in vh.report(run).splitlines())


def test_main_rejects_run_without_unblocked_mark(tmp_path, capsys):
    run = _run(tmp_path)
    timeline = json.loads((run / "timeline.json").read_text(encoding="utf-8"))
    (run / "timeline.json").write_text(json.dumps(timeline[:3]), encoding="utf-8")  # lỗi trước khi gỡ chặn
    with pytest.raises(SystemExit):
        vh.main([str(run)])
    assert "thiếu mốc unblocked" in capsys.readouterr().err


def test_main_rejects_run_without_timeline(tmp_path, capsys):
    run = _run(tmp_path)
    (run / "timeline.json").unlink()
    with pytest.raises(SystemExit):
        vh.main([str(run)])
    assert "timeline.json" in capsys.readouterr().err
