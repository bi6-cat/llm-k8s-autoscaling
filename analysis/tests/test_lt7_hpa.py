"""Test cho analysis/lt7_hpa.py (LT7, Môi trường §19).

Khái niệm: Dựng thư mục lượt giả runs/sim/lt7-<giờ>/c<C>-r<lần>/ đúng định dạng envs/sim/tests/lt7-hpa.sh ghi:
    meta.json, hpa.json, events.json, pods.json, prom-running.json, prom-waiting.json, hpa-rescale.log.
    Số liệu lấy từ lượt chạy thử C = 15 trên kind ngày 16/11/2026: hey bắt đầu 09:23:46,605 UTC, lần scrape
    đầu thấy tải lúc +4,573 s, HPA đổi 1 → 2 lúc 09:23:56,463061, pod mới Ready lúc 09:24:01.
Mục đích: Kiểm công thức dự đoán (kẹp, tolerance) và cách tách trễ theo chặng, mà không cần cluster.
"""

from __future__ import annotations

import csv
import json
from datetime import UTC, datetime
from pathlib import Path

import pytest

from analysis import lt7_hpa as lt

T0 = 1_794_821_026.605  # 2026-11-16 09:23:46,605 UTC
# Mốc scrape thật của pod gốc trong lượt đó: cách nhau 5 s, trừ 036,177 → 040,440 (đồng hồ thực lùi 0,737 s)
SCRAPES = [
    1_794_821_000 + s for s in (16.177, 21.177, 26.177, 31.178, 36.177, 40.44, 45.44, 50.44, 55.441, 60.439)
]
LOG_LINE = (
    'I1116 09:23:56.463061       1 horizontal.go:1032] "Successfully rescaled"'
    ' HPA="llm-serving/keda-hpa-vllm-a2" currentReplicas=1 desiredReplicas=2'
    ' reason="external metric s0-prometheus(...) above target"'
)


def _prom(points: dict[str, list[tuple[float, float]]], name: str) -> dict:
    return {
        "status": "success",
        "data": {
            "resultType": "matrix",
            "result": [
                {
                    "metric": {"__name__": name, "namespace": "llm-serving", "pod": pod},
                    "values": [[t, str(v)] for t, v in pts],
                }
                for pod, pts in points.items()
            ],
        },
    }


def _pod(name: str, created: str, ready: str | None) -> dict:
    conds = [{"type": "PodScheduled", "status": "True", "lastTransitionTime": created}]
    if ready:
        conds.append({"type": "Ready", "status": "True", "lastTransitionTime": ready})
    return {"metadata": {"name": name, "creationTimestamp": created}, "status": {"conditions": conds}}


def _run(
    root: Path,
    *,
    c: int = 15,
    rep: int = 1,
    desired: int = 2,
    log: list[str] | None = None,
    events: list[dict] | None = None,
    new_pods: int = 1,
    restarts: tuple[int, int] = (12, 12),
    scrapes: list[float] = SCRAPES,
    pod_times: tuple[str, str] = ("2026-11-16T09:23:56Z", "2026-11-16T09:24:01Z"),
    clock: list[tuple[float, float]] | None = None,
) -> Path:
    """Một lượt giả. log=None: không có hpa-rescale.log (dữ liệu cũ), analysis phải dùng event."""
    d = root / f"c{c}-r{rep}"
    d.mkdir(parents=True)
    meta = {
        "c": c,
        "rep": rep,
        "t0": T0,
        "dur_s": 30,
        "threshold": 10,
        "min_replicas": 1,
        "max_replicas": 3,
        "hpa_uid": "u",
        "scrape_interval": "5s",
        "hpa_sync_period": "5s",
        "restarts_before": restarts[0],
        "restarts_after": restarts[1],
    }
    (d / "meta.json").write_text(json.dumps(meta), encoding="utf-8")
    avg = f"{-(-c * 1000 // desired)}m"  # HPA làm tròn LÊN tổng ÷ số replica, đơn vị mili
    hpa = {
        "status": {
            "desiredReplicas": desired,
            "currentReplicas": desired,
            "currentMetrics": [{"external": {"current": {"averageValue": avg}}}],
        }
    }
    (d / "hpa.json").write_text(json.dumps(hpa), encoding="utf-8")
    (d / "events.json").write_text(json.dumps({"items": events or []}), encoding="utf-8")
    pods = [_pod("old", "2026-11-07T14:29:47Z", "2026-11-16T09:18:23Z")]
    pods += [_pod(f"new{i}", *pod_times) for i in range(new_pods)]
    (d / "pods.json").write_text(json.dumps({"items": pods}), encoding="utf-8")
    # Pod gốc: 0 trước mốc 0, c trong lúc có tải (từ lần scrape thứ 4); pod mới: 0
    run = {"old": [(t, c if T0 < t < T0 + 30 else 0) for t in scrapes]}
    if new_pods:
        run["new0"] = [(1_794_821_042.531 + 5 * i, 0) for i in range(5)]
    if clock is not None:  # như journalctl -o json: số nguyên µs dạng chuỗi
        lines = [
            json.dumps({"wall_us": str(round(w * 1e6)), "mono_us": str(round(m * 1e6))}) for w, m in clock
        ]
        (d / "clock-changes.jsonl").write_text("\n".join(lines) + "\n", encoding="utf-8")
    wait = {pod: [(t, 0) for t, _ in pts] for pod, pts in run.items()}
    (d / "prom-running.json").write_text(
        json.dumps(_prom(run, "vllm:num_requests_running")), encoding="utf-8"
    )
    (d / "prom-waiting.json").write_text(
        json.dumps(_prom(wait, "vllm:num_requests_waiting")), encoding="utf-8"
    )
    if log is not None:
        (d / "hpa-rescale.log").write_text("\n".join(log) + "\n", encoding="utf-8")
    return d


@pytest.mark.parametrize(
    ("total", "start", "want"),
    [
        (5, 1, 1),  # dưới ngưỡng
        (15, 1, 2),  # ⌈1,5⌉; ở 2 replica tỷ lệ 0,75 → ⌈1,5⌉ = 2, đứng yên
        (25, 1, 3),
        (35, 1, 3),  # ⌈3,5⌉ = 4, kẹp ở max 3
        (11, 1, 1),  # tỷ lệ 1,1 nằm TRONG tolerance (so ≤, như Tolerances.isWithin), không scale
        (12, 1, 2),
        (23, 2, 3),  # ở 2 replica: tỷ lệ 1,15 → ⌈2,3⌉ = 3
        (19, 2, 2),  # ở 2 replica: tỷ lệ 0,95 → trong tolerance, giữ 2
    ],
)
def test_predict_replicas(total, start, want):
    assert lt.predict_replicas(total, 10, 1, 3, start=start) == want


def test_parse_helpers():
    assert lt.parse_quantity("8334m") == pytest.approx(8.334)
    assert lt.parse_quantity("15") == 15.0
    assert lt.parse_quantity(None) is None
    assert lt.parse_duration("5s") == 5.0
    assert lt.parse_duration("15s (mặc định)") == 15.0
    assert lt.parse_duration("") is None
    assert lt.parse_k8s_time("2026-11-16T09:23:56Z") == pytest.approx(1_794_821_036.0)


def test_rescales_from_log_reads_microseconds_and_skips_other_lines():
    lines = ['I1116 09:18:38.954222       1 horizontal.go:228] "Starting HPA controller"', LOG_LINE]
    got = lt.rescales_from_log(lines, 2026)
    want = datetime(2026, 11, 16, 9, 23, 56, 463061, tzinfo=UTC).timestamp()
    assert got == [(pytest.approx(want), 1, 2)]


def test_analyze_run_splits_delay_into_stages(tmp_path):
    row = lt.analyze_run(_run(tmp_path, log=[LOG_LINE]))
    assert row["hpa_time_source"] == "log"
    assert row["predicted"] == 2 and row["desired_end"] == 2 and row["rescale_sizes"] == "2"
    assert row["formula_ok"] is True
    assert row["total_hpa"] == pytest.approx(15.0)  # 7500m × 2
    assert row["d_scrape"] == pytest.approx(4.573)  # 09:23:51,178 − 09:23:46,605
    assert row["d_sync"] == pytest.approx(5.285)  # 09:23:56,463 − 09:23:51,178
    # KEDA hỏi với time= làm tròn xuống giây: mẫu lúc :51,178 chỉ thấy được từ :52
    assert row["d_visible"] == pytest.approx(0.822) and row["d_wait"] == pytest.approx(4.463)
    assert row["d_decide"] == pytest.approx(9.858)
    assert row["d_create"] == 0 and row["d_ready"] == 5
    # Không có journal: giữ giờ thực. Scrape 09:23:56,177 → 09:24:00,440 chỉ cách 4,263 s (lùi 0,737 s)
    assert row["clock"] == "wall" and row["clock_step_s"] is None
    assert row["scrape_gap_err_wall"] == pytest.approx(0.737) and row["scrape_gap_err"] is None


def test_mono_clock_maps_segments_and_flags_repeated_wall_times(tmp_path):
    # Hai lần chỉnh: offset 100 từ mono 0, rồi lùi 0,7 s (offset 99,3) từ mono 50
    clock = lt.MonoClock([(100.0, 0.0), (149.3, 50.0)])
    assert clock.to_mono(120.0) == (pytest.approx(20.0), True)
    assert clock.to_mono(151.0) == (pytest.approx(51.7), True)
    # Giờ thực 149,5 có hai lần: mono 49,5 (trước bước lùi) và 50,2 (sau): không chắc
    assert clock.to_mono(149.5) == (pytest.approx(49.5), False)
    assert clock.to_mono(99.0) == (None, False)  # trước lần chỉnh đầu tiên có trong journal
    assert clock.to_mono(149.0) == (pytest.approx(49.0), True)
    # 149,29: theo đoạn mới là mono 49,99, 10 ms trước dòng journal (ghi trễ hơn lần chỉnh thật): không chắc
    assert clock.to_mono(149.29) == (pytest.approx(49.29), False)
    p = tmp_path / "clock-changes.jsonl"
    p.write_text(
        '{"wall_us": "100000000", "mono_us": "0"}\n\n{"wall_us": "149300000", "mono_us": "50000000"}\n'
    )
    seg = lt.MonoClock.from_jsonl(p).seg
    assert [m for m, _ in seg] == [0.0, 50.0] and [o for _, o in seg] == pytest.approx([100.0, 99.3])
    assert lt.MonoClock.from_jsonl(tmp_path / "khong-co.jsonl") is None


def test_analyze_run_corrects_a_clock_step_between_scrape_and_decision(tmp_path):
    # Sự kiện thật theo đồng hồ đơn điệu: mốc 0 ở 987,868; scrape mỗi 5 s từ 977,44; HPA ở 997,726. Giờ thực
    # = đơn điệu + offset; offset lùi 0,737 s lúc mono 995 (giữa scrape 992,44 và quyết định của HPA).
    off1, off2 = 1_794_820_038.737, 1_794_820_038.0
    scrapes = [m + (off1 if m < 995 else off2) for m in (977.44 + 5 * i for i in range(10))]
    log = LOG_LINE.replace("09:23:56.463061", "09:23:55.726000")  # 997,726 + off2
    run = _run(
        tmp_path,
        log=[log],
        scrapes=scrapes,
        pod_times=("2026-11-16T09:23:55Z", "2026-11-16T09:24:00Z"),
        clock=[(960 + off1, 960.0), (995 + off2, 995.0)],
    )
    row = lt.analyze_run(run)
    assert row["clock"] == "mono"
    assert row["d_scrape"] == pytest.approx(4.572)
    assert row["d_sync"] == pytest.approx(5.286)  # giờ thực chỉ ra 4,549
    # Giây tròn kế tiếp của scrape (giờ thực …032,0) nằm trước bước lùi: mono 993,263
    assert row["d_visible"] == pytest.approx(0.823) and row["d_wait"] == pytest.approx(4.463)
    assert row["d_decide"] == pytest.approx(9.858)
    assert row["d_create"] == 0 and row["d_ready"] == 5
    assert row["clock_step_s"] == pytest.approx(-0.737)
    assert row["scrape_gap_err_wall"] == pytest.approx(0.737) and row["scrape_gap_err"] < 0.001


def test_analyze_run_falls_back_to_events_without_log(tmp_path):
    ev = {
        "reason": "SuccessfulRescale",
        "message": "New size: 2; reason: above target",
        "firstTimestamp": "2026-11-16T09:23:56Z",
        "count": 1,
    }
    row = lt.analyze_run(_run(tmp_path, events=[ev]))
    assert row["hpa_time_source"] == "event"
    assert row["d_sync"] == pytest.approx(4.822)  # mốc event làm tròn xuống giây
    assert row["formula_ok"] is True


def test_analyze_run_empty_log_falls_back_to_events(tmp_path):
    # `kubectl logs` lỗi lúc đo: file log rỗng nhưng HPA có scale; không được báo là "không đổi replica"
    ev = {
        "reason": "SuccessfulRescale",
        "message": "New size: 2; reason: above target",
        "firstTimestamp": "2026-11-16T09:23:56Z",
        "count": 1,
    }
    row = lt.analyze_run(_run(tmp_path, log=[], events=[ev]))
    assert row["hpa_time_source"] == "event" and row["rescale_sizes"] == "2" and row["formula_ok"] is True


def test_analyze_run_without_scale_up(tmp_path):
    row = lt.analyze_run(_run(tmp_path, c=5, desired=1, log=[], new_pods=0))
    assert row["predicted"] == 1 and row["rescale_sizes"] == "" and row["formula_ok"] is True
    assert row["d_decide"] is None and row["d_scrape"] is None


def test_analyze_run_flags_wrong_size_and_restart(tmp_path):
    # Lên 3 thay vì 2: sai công thức
    wrong = LOG_LINE.replace("desiredReplicas=2", "desiredReplicas=3")
    assert lt.analyze_run(_run(tmp_path / "a", desired=3, log=[wrong]))["formula_ok"] is False
    # Pod restart giữa lượt: không hợp lệ dù số replica đúng
    row = lt.analyze_run(_run(tmp_path / "b", log=[LOG_LINE], restarts=(12, 13)))
    assert row["restarted"] is True and row["formula_ok"] is False


def test_analyze_run_ignores_log_lines_outside_the_run(tmp_path):
    # Dòng của lượt trước (sớm hơn mốc 0) không được tính là quyết định của lượt này
    old = LOG_LINE.replace("09:23:56.463061", "09:20:00.000000")
    row = lt.analyze_run(_run(tmp_path, log=[old, LOG_LINE]))
    assert row["rescale_sizes"] == "2" and row["d_decide"] == pytest.approx(9.858)


def test_main_writes_csv_and_summary(tmp_path, capsys):
    session = tmp_path / "lt7-x"
    _run(session, log=[LOG_LINE])
    _run(session, c=5, desired=1, log=[], new_pods=0)
    (session / "keda.json").write_text(
        json.dumps({"grpc_mean_s": 0.0042, "grpc_count": 300, "scaler_latency_max_s": 0.012}),
        encoding="utf-8",
    )
    out = tmp_path / "lt7.csv"
    assert lt.main([str(session), "--out", str(out)]) == 0
    rows = list(csv.DictReader(out.open(encoding="utf-8")))
    assert [r["c"] for r in rows] == ["5", "15"]
    assert rows[0]["d_decide"] == "" and rows[1]["d_decide"] == "9.858"
    text = capsys.readouterr().out
    assert "| 15 | 2 | 2 | 2 | 2 | 1/1 |" in text
    assert "trung bình 4.2 ms" in text
