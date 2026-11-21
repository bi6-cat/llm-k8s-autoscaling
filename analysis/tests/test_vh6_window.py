"""Test cho analysis/vh6_window.py (VH6, mục 5.5).

Khái niệm: Ngoài hàm thuần max_bad_ratio, test dựng một phiên GIẢ runs/<phiên>/ có
    tables/{runs,alerts,phases}.csv như build_tables ghi, và một lượt S1-KB3-1: 1 request mỗi giây, các
    request gửi trong [100, 130) đều xấu. alerts.csv có một đợt LLMSLOBurnFast bắt đầu trong lượt, một đợt
    đang kêu từ lượt trước và một cảnh báo khác; chỉ đợt đầu được in.
Mục đích: Kiểm quy ước cửa sổ (τ − 60, τ] (cùng metrics.slo_violation_start) và cách chọn đợt page.
"""

from __future__ import annotations

import csv
import json
from pathlib import Path

import pytest

from analysis import metrics as m
from analysis import vh6_window as vh

T0 = 1_800_000_000.0
KEY = {"session": "v2-dg2", "run_id": "S1-KB3-1", "attempt": "attempt-1"}


def _reqs(n: int = 400, bad: tuple[float, float] = (100, 130)) -> list[dict]:
    rows = []
    for i in range(n):
        t = i + 0.5
        ttft = 3.0 if bad[0] <= t < bad[1] else 0.2
        rows.append({"id": i, "t_sched": t, "t_send": t, "t_first": t + ttft, "t_last": t + ttft + 0.3,
                     "n_out": 16, "error": ""})  # fmt: skip
    return rows


def _parse(rows: list[dict]) -> list[m.Request]:
    return [m.parse_request({k: str(v) for k, v in r.items()}, T0) for r in rows]


def test_max_bad_ratio_finds_first_window_holding_all_bad_requests():
    reqs = _parse(_reqs())
    # Cửa sổ 60 s chứa đủ 30 request xấu (gửi lúc 100,5 … 129,5) trong 60 request: 0,5, lần đầu ở τ = 130
    assert vh.max_bad_ratio(reqs, T0 + 100, T0 + 200) == (pytest.approx(0.5), T0 + 130)
    assert vh.max_bad_ratio(reqs, T0 + 300, T0 + 310) == (0.0, T0 + 300)
    assert vh.max_bad_ratio([], T0, T0 + 10) == (None, None)


def test_max_bad_ratio_window_is_open_on_the_left_closed_on_the_right():
    rows = [
        {"id": 0, "t_sched": 10.0, "t_send": 10.0, "t_first": 13.0, "t_last": 13.3, "n_out": 16, "error": ""}
    ]
    reqs = _parse(rows)
    assert vh.max_bad_ratio(reqs, T0 + 10, T0 + 10) == (1.0, T0 + 10)  # τ = 10: có request lúc 10
    assert vh.max_bad_ratio(reqs, T0 + 70, T0 + 70) == (None, None)  # τ = 70: (10, 70] không chứa 10


def _write_csv(path: Path, rows: list[dict]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w", encoding="utf-8", newline="") as fh:
        w = csv.DictWriter(fh, fieldnames=list(rows[0]))
        w.writeheader()
        w.writerows(rows)


def _session(tmp_path: Path) -> Path:
    sess = tmp_path / "v2-dg2"
    run = {**KEY, "counted": "True", "slo_violation_s": "120.0"}
    # Dòng của phiên khác trùng run_id (build_tables chạy trên hai phiên): phải bị bỏ
    _write_csv(sess / "tables" / "runs.csv", [run, run | {"session": "v2-dg2-rerun", "attempt": "attempt-2"}])
    alert = {**KEY, "alertname": "LLMSLOBurnFast", "first_s": "220.0",
             "firing_at_start": "False", "client_bad_ratio": "0.1"}  # fmt: skip
    _write_csv(
        sess / "tables" / "alerts.csv",
        [
            alert,
            alert | {"first_s": "-150.0", "firing_at_start": "True"},  # đang kêu từ lượt trước: bỏ
            alert | {"alertname": "LLMSLOBurnSlow"},
            alert | {"session": "v2-dg2-rerun", "first_s": "100.0"},
        ],
    )
    phase = {**KEY, "phase": "ramp", "slo_attainment": "0.9"}
    _write_csv(
        sess / "tables" / "phases.csv",
        [phase, phase | {"phase": "sustain", "slo_attainment": "1.0"}, phase | {"phase": "main"}],
    )
    d = sess / "S1-KB3-1" / "attempt-1"
    d.mkdir(parents=True)
    lg = {"t0_unix": T0, "phases_s": {"ramp": [0.0, 300.0], "sustain": [300.0, 1020.0]}}
    (d / "loadgen.json").write_text(json.dumps(lg), encoding="utf-8")
    _write_csv(d / "requests.csv", _reqs())
    return sess


def test_report_prints_only_pages_that_start_in_the_run(tmp_path):
    out = vh.report(_session(tmp_path)).splitlines()
    assert len(out) == 1
    line = out[0]
    assert line.startswith("S1-KB3-1  vi_pham= 120.0 page= 220.0 tre= 100.0 | max1m=0.500 @tau=130.0 | ")
    # 5 phút trước page (−80, 220): 30 xấu / 220 request; cột alerts.csv in lại để đối chiếu
    assert f"bad5m_truoc_page={30 / 220:.3f} (alerts.csv 0.100)" in line
    assert "phases(bad) ramp=0.100 sustain=0.000 |" in line


def test_report_without_pages(tmp_path):
    sess = _session(tmp_path)
    row = {**KEY, "alertname": "Watchdog", "first_s": "0",
           "firing_at_start": "False", "client_bad_ratio": ""}  # fmt: skip
    _write_csv(sess / "tables" / "alerts.csv", [row])
    assert vh.report(sess).startswith("Không có đợt LLMSLOBurnFast")
