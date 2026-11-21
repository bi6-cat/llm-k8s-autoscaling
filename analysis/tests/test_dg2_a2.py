"""Test cho analysis/dg2_a2.py (số phụ của mục 5.3, ĐG2).

Khái niệm: Ngoài các hàm thuần, test dựng một phiên GIẢ runs/<phiên>/ đúng định dạng runner và build_tables
    ghi (tables/runs.csv, <run_id>/attempt-1/{loadgen.json, requests.csv, metrics.csv.gz, events.jsonl,
    logs/vllm-<pod>.log}). Lượt A2-KB2-1 có pod cũ `old00` từ đầu và pod mới `new11` Ready lúc 320 s; pod cũ
    giữ hàng đợi 50 request tới 640 s, nên các số cần kiểm đều tính tay được.
Mục đích: Kiểm cách đọc mốc (events, giờ trong access log với phần lẻ nano giây), cách cộng tín hiệu A2
    và cách tách request xấu trước / sau lúc pod mới Ready, mà không cần dữ liệu V2 thật.
"""

from __future__ import annotations

import csv
import gzip
import json
from datetime import UTC, datetime
from pathlib import Path

import pytest

from analysis import dg2_a2 as dg
from analysis import metrics as m

T0 = 1_800_000_000.25  # t0_unix: có phần lẻ để kiểm việc làm tròn mốc về giây
KB2_PHASES = {"pre": [120.0, 240.0], "spike": [240.0, 840.0], "drop": [840.0, 1440.0]}
OLD, NEW = "vllm-5d8f9-old00", "vllm-5d8f9-new11"


def _iso(t: float, *, frac: str = "") -> str:
    """Giây UNIX → giờ UTC dạng Kubernetes; `frac` thêm phần lẻ như kubectl --timestamps (".250000000")."""
    return datetime.fromtimestamp(int(t), UTC).strftime("%Y-%m-%dT%H:%M:%S") + frac + "Z"


def _req(i: int, t: float, ttft: float) -> dict:
    return {"id": i, "t_sched": t, "t_send": t, "t_first": t + ttft, "t_last": t + ttft + 15 * 0.02,
            "n_out": 16, "error": ""}  # fmt: skip


# ── Hàm thuần ─────────────────────────────────────────────────────────────────────────────────────────


def test_rescales_reads_new_size_in_time_order_and_skips_other_events():
    events = [
        {
            "time": _iso(T0 + 300),
            "reason": "SuccessfulRescale",
            "message": "New size: 4; reason: above target",
        },
        {"time": _iso(T0 + 100), "reason": "ScalingReplicaSet", "message": "Scaled up to 2"},
        {
            "time": _iso(T0 + 260),
            "reason": "SuccessfulRescale",
            "message": "New size: 2; reason: above target",
        },
        {"time": _iso(T0 + 270), "reason": "FailedGetExternalMetric", "message": "New size: 9"},
    ]
    got = dg.rescales(events, T0)
    assert [n for _, n in got] == [2, 4]
    assert got[0][0] == pytest.approx(260 - 0.25)  # event chỉ có giờ tới giây


def test_log_time_keeps_nanosecond_fraction_and_rejects_lines_without_time():
    base = datetime(2026, 11, 18, 10, 41, 57, tzinfo=UTC).timestamp()
    line = (
        '2026-11-18T10:41:57.435498299Z INFO:     10.42.0.43:33064 - "POST /v1/chat/completions HTTP/1.1" 200'
    )
    assert dg.log_time(line) == pytest.approx(base + 0.435498299, abs=1e-6)
    assert dg.log_time("2026-11-18T10:41:57.5Z x") == pytest.approx(base + 0.5)  # phần lẻ ngắn
    assert dg.log_time("2026-11-18T10:41:57Z x") == pytest.approx(base)
    assert dg.log_time("    at Traceback line") is None


def test_arrivals_counts_only_chat_posts_relative_to_t0():
    lines = [
        f'{_iso(T0 + 10, frac=".750000000")} INFO: "POST /v1/chat/completions HTTP/1.1" 200 OK',
        f'{_iso(T0 + 11)} INFO: "GET /metrics HTTP/1.1" 200 OK',
        f'{_iso(T0 - 50)} INFO: "POST /v1/chat/completions HTTP/1.1" 200 OK',  # warm-up, trước t0
        "Traceback (most recent call last):",
    ]
    assert dg.arrivals(lines, T0) == pytest.approx([10.5, -50.25])


def test_positive_span_and_value_near():
    s = {0: 0.0, 5: 3.0, 10: 7.0, 15: 0.0}
    assert dg.positive_span(s) == (7.0, 5, 10)
    assert dg.positive_span({0: 0.0, 5: 0.0}) == (0.0, None, None)
    assert dg.value_near(s, 11.0) == 7.0
    assert dg.pod_suffix(OLD) == "old00"


def test_signal_sums_running_and_waiting_over_pods_missing_metric_counts_zero():
    met = {
        "vllm_running": [
            (T0 + 5, {"pod": OLD}, 10.0),
            (T0 + 5, {"pod": NEW}, 4.0),
            (T0 + 10, {"pod": OLD}, 9.0),
        ],
        "vllm_waiting": [(T0 + 5, {"pod": OLD}, 30.0)],
    }
    assert dg.signal(met, T0) == {5: 44.0, 10: 9.0}


def test_signal_stats_fraction_below_level_and_gap_between_samples_above():
    sig = {t: 100.0 for t in range(700, 840, 5)} | {720: 120.0, 760: 115.0, 840: 500.0}  # 840: ngoài [a, b)
    s = dg.signal_stats(sig, 700, 840, 111)
    assert s["n"] == 28
    assert s["frac_le"] == pytest.approx(26 / 28)
    assert (s["last_above"], s["max_gap_above"], s["max"]) == (760, 40, 120.0)
    assert dg.signal_stats({t: 50.0 for t in range(0, 20, 5)}, 0, 20, 111)["last_above"] is None


def test_bad_split_counts_bad_requests_sent_before_and_after_ready():
    # Mỗi 0,5 s một request; TTFT 5 s (xấu) khi gửi trong [240, 400), còn lại 0,2 s
    rows = [_req(i, i * 0.5, 5.0 if 240 <= i * 0.5 < 400 else 0.2) for i in range(2880)]
    reqs = [m.parse_request({k: str(v) for k, v in r.items()}, T0) for r in rows]
    s = dg.bad_split(reqs, T0 + 240, T0 + 840, T0 + 320)
    assert (s["n"], s["before"], s["after"]) == (1200, 160, 160)
    assert s["slo"] == pytest.approx(1 - 320 / 1200)


# ── Tích hợp: phiên giả ───────────────────────────────────────────────────────────────────────────────


def _write_csv(path: Path, rows: list[dict]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w", encoding="utf-8", newline="") as fh:
        w = csv.DictWriter(fh, fieldnames=list(rows[0]))
        w.writeheader()
        w.writerows(rows)


def _metrics(path: Path, series: dict[tuple[str, str], dict[int, float]]) -> None:
    with gzip.open(path, "wt", encoding="utf-8", newline="") as fh:
        w = csv.writer(fh)
        w.writerow(["ts", "name", "labels", "value"])
        for (name, pod), s in series.items():
            for t, v in s.items():
                w.writerow([T0 + t, name, json.dumps({"pod": pod}), v])


def _run_row(run_id: str, config: str, scenario: str, **kw: str) -> dict:
    row = {"run_id": run_id, "attempt": "attempt-1", "config": config, "scenario": scenario,
           "counted": "True", "t0_unix": str(T0), "duration_s": "1440.0", "n_sent": "2560", "react_s": "",
           "threshold": "", "max_replicas": "", "config_type": "static"}  # fmt: skip
    return row | kw


def _session(tmp_path: Path) -> Path:
    sess = tmp_path / "v2-dg2"
    _write_csv(
        sess / "tables" / "runs.csv",
        [
            _run_row("S4-KB2-1", "S4", "KB2"),
            _run_row(
                "A2-KB2-1",
                "A2",
                "KB2",
                react_s="80.0",
                threshold="37",
                max_replicas="4",
                config_type="scaledobject",
            ),  # fmt: skip
            _run_row("A2-KB1-1", "A2", "KB1", threshold="37", max_replicas="4", config_type="scaledobject")
            | {"counted": "False"},  # lần thử không được tính: bỏ
        ],
    )
    grid = range(0, 1440, 5)
    # Lượt tĩnh S4: chỉ cần loadgen.json và hàng đợi bằng 0
    s4 = sess / "S4-KB2-1" / "attempt-1"
    s4.mkdir(parents=True)
    (s4 / "loadgen.json").write_text(json.dumps({"phases_s": KB2_PHASES}), encoding="utf-8")
    _metrics(s4 / "metrics.csv.gz", {("vllm_waiting", "vllm-s4-aaaaa"): dict.fromkeys(grid, 0.0)})

    d = sess / "A2-KB2-1" / "attempt-1"
    (d / "logs").mkdir(parents=True)
    (d / "loadgen.json").write_text(json.dumps({"phases_s": KB2_PHASES}), encoding="utf-8")
    rows = [_req(i, i * 0.5, 5.0 if 240 <= i * 0.5 < 400 else 0.2) for i in range(2880)]
    _write_csv(d / "requests.csv", rows)
    new = range(320, 1440, 5)
    waiting_old = {t: 50.0 if 265 <= t <= 640 else 0.0 for t in grid} | {720: 100.0, 760: 100.0}
    _metrics(
        d / "metrics.csv.gz",
        {
            ("vllm_waiting", OLD): waiting_old,
            ("vllm_waiting", NEW): dict.fromkeys(new, 0.0),
            ("vllm_running", OLD): dict.fromkeys(grid, 10.0),
            ("vllm_running", NEW): dict.fromkeys(new, 10.0),
            ("vllm_success_total", OLD): {t: 3.0 * t for t in grid},
            ("vllm_success_total", NEW): {t: 2.0 * (t - 320) for t in new},
        },
    )
    post = '"POST /v1/chat/completions HTTP/1.1" 200 OK'
    for pod, first, frac in ((OLD, -10, ".500000000"), (NEW, 320, ".750000000")):
        # Giờ trong log = T0 + i + phần lẻ; T0 có phần lẻ 0,25, nên mốc từ t0 là i + 0,25 (OLD), i + 0,5 (NEW)
        lines = [f"{_iso(T0 + i, frac=frac)} INFO: 10.0.0.1:1 - {post}" for i in range(first, 1440)]
        (d / "logs" / f"{pod}.log").write_text("\n".join(lines) + "\n", encoding="utf-8")
    events = [
        {"time": _iso(T0 + 256), "reason": "SuccessfulRescale", "message": "New size: 2; reason: x"},
        {"time": _iso(T0 + 271), "reason": "SuccessfulRescale", "message": "New size: 4; reason: x"},
    ]
    (d / "events.jsonl").write_text("".join(json.dumps(e) + "\n" for e in events), encoding="utf-8")
    return sess


def test_request_share_counts_arrivals_from_logs_and_completions_from_counter(tmp_path):
    run = next(r for r in dg.load_runs(_session(tmp_path)) if r.run_id == "A2-KB2-1")
    sh = dg.request_share(run)
    assert sh["sent"] == 480  # 2 request mỗi giây trong [360, 600)
    assert (sh["log_total"], sh["n_sent"]) == (1440 + 1120, 2560)  # warm-up của OLD bị lọc
    old, new = sh["pods"]  # pod cũ đứng đầu
    assert (old["pod"], old["arrived"], old["done"], old["wait_start"], old["wait_end"]) == (
        OLD,
        240,
        720,
        50,
        50,
    )
    assert (new["pod"], new["arrived"], new["done"], new["wait_start"]) == (NEW, 240, 480, 0)


def test_report_on_synthetic_session(tmp_path):
    out = dg.report(_session(tmp_path)).splitlines()
    # Phần 1: chỉ lượt có ScaledObject; lượt không được tính (A2-KB1-1) bị bỏ
    assert "A2-KB2-1 duration 1440.0 : 256->2 271->4" in out
    assert not any(line.startswith(("S4-KB2-1 duration", "A2-KB1-1")) for line in out)
    # Phần 2: hàng đợi pod cũ > 0 trong [265; 640] (mẫu 720, 760 kéo dài khoảng), lượt S4 cũng được in
    assert "A2-KB2-1 old00 max=100 >0 trong [265;760] = 495 s ; new11 max=0" in out
    assert "S4-KB2-1 aaaaa max=0" in out
    share = next(line for line in out if line.startswith("A2-KB2-1 gửi"))
    assert "old00: đến 240 (50.0%), xong 720 (3.00 req/s), đến/xong 33.3%, chờ 50->50" in share
    # Phần 4: tín hiệu 20 ở [700, 840), riêng 720 và 760 là 120 > 111 = (4 − 1) × 37
    sig = next(line for line in out if line.startswith("A2-KB2-1 [700;840)"))
    assert "n=28 min=20 tb=27.1 max=120 tỷ lệ mẫu ≤ 111: 93%; mẫu > 111 cuối 760 s" in sig
    assert sig.endswith("khoảng cách lớn nhất giữa hai mẫu > 111: 40 s")
    # Phần 5: pod mới Ready lúc 240 + 80 = 320 s
    assert (
        "A2-KB2-1 pod mới Ready lúc 320.0 s; n=1200 SLO=0.7333; không đạt: trước 160 (50.0%), sau 160 (50.0%)"
        in out
    )


def test_main_requires_tables(tmp_path, capsys):
    with pytest.raises(SystemExit):
        dg.main([str(tmp_path)])
    assert "build_tables" in capsys.readouterr().err
