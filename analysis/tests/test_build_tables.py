"""Test tích hợp cho analysis/build_tables.py.

Khái niệm: Dựng thư mục lượt giả runs/<phiên>/<run_id>/attempt-<n>/ đúng định dạng runner ghi (Môi trường
    §14.2): metadata.json, loadgen.json, requests.csv, metrics.csv.gz, pods_timeline.json, alerts.jsonl…
Mục đích: Kiểm phần ghép dữ liệu (chọn lần thử được tính, so với S4, gộp theo ô, cảnh báo của lượt trước,
    thư mục thiếu file) và CSV ghi ra, mà không cần cluster.
"""

from __future__ import annotations

import csv
import gzip
import json
import math
from pathlib import Path

import pytest

from analysis import build_tables as bt

T0 = 1_800_000_000.0  # t0_unix của máy tạo tải
KB2_PHASES = {"pre": [120.0, 240.0], "spike": [240.0, 840.0], "drop": [840.0, 1440.0]}


def _requests(n: int = 1440, *, bad=(240.0, 300.0), errors=()) -> list[dict]:
    """Mỗi giây một request lúc x,5. TTFT 5 s trong khoảng `bad` (quá tải đầu pha spike), còn lại 0,2 s."""
    rows = []
    for i in range(n):
        t = i + 0.5
        ttft = 5.0 if bad[0] <= t < bad[1] else 0.2
        row = {"id": i, "t_sched": t, "t_send": t, "t_first": t + ttft, "t_last": t + ttft + 0.05 * 255}
        row.update(n_in_target=512, n_in=520, n_out=256, status=200, error="")
        if i in errors:
            row.update(t_first="", t_last="", n_out="", error="Timeout")
        rows.append(row)
    return rows


def _pod(name: str, created: float, ready: float, gone: float | None) -> dict:
    return {
        "name": name,
        "first_seen": created,
        "last_seen": gone - 5 if gone else T0 + 2000,
        "gone_at": gone,
        "marks": {"created": created, "scheduled": created, "ready": ready},
        "log": None,
        "log_error": None,
    }


def write_attempt(
    root: Path,
    *,
    session: str = "s",
    run_id: str = "A2-KB2-1",
    attempt: str = "attempt-1",
    config: str = "A2",
    scenario: str = "KB2",
    valid: bool = True,
    pods: list[dict] | None = None,
    replicas: list[tuple[float, float]] | None = None,
    alerts: list[dict] | None = None,
    requests: list[dict] | None = None,
) -> Path:
    d = root / session / run_id / attempt
    d.mkdir(parents=True)
    pods = pods if pods is not None else [_pod("vllm-a", T0 - 3600, T0 - 3590, None)]
    meta = {
        "session": session,
        "env": "sim",
        "run_id": run_id,
        "attempt_dir": attempt,
        "spec": {
            "config": {"id": config, "type": "scaledobject" if config.startswith("A") else "static"},
            "scenario": scenario,
            "repeat": int(run_id.rsplit("-", 1)[1]),
            "replicas_for_kb3": 3,
        },
        # Runner ghi t_main_start lúc apply Job, trước t0 của máy tạo tải (kind 16/11: 11 s). Đặt cách xa t0
        # để test bắt được lỗi lấy t_main_start làm mốc đầu pha chính.
        "t_main_start": T0 - 30,
        "git": {"commit": "bbb", "dirty": False},
        "git_runner": {"commit": "aaa", "dirty": False},
        "cooldown_s": 400.0,
    }
    lg = {"scenario": scenario, "capacity_rps": 1.0, "t0_unix": T0, "duration_s": 1440.0, "n_planned": 1440}
    lg["phases_s"] = KB2_PHASES
    (d / "metadata.json").write_text(json.dumps(meta), encoding="utf-8")
    (d / "loadgen.json").write_text(json.dumps(lg), encoding="utf-8")
    (d / "checks.json").write_text(
        json.dumps({"valid": valid, "reasons": [] if valid else ["cpu_ok"]}), "utf-8"
    )
    (d / "pods_start.json").write_text(json.dumps([{"name": "vllm-a"}]), "utf-8")
    (d / "pods_timeline.json").write_text(json.dumps({"pods": pods}), "utf-8")
    reqs = requests if requests is not None else _requests()
    with (d / "requests.csv").open("w", newline="", encoding="utf-8") as fh:
        w = csv.DictWriter(fh, fieldnames=list(reqs[0]))
        w.writeheader()
        w.writerows(reqs)
    replicas = replicas if replicas is not None else [(T0 + t, 1.0) for t in range(-30, 1500, 5)]
    with gzip.open(d / "metrics.csv.gz", "wt", newline="", encoding="utf-8") as fh:
        w = csv.writer(fh)
        w.writerow(["ts", "name", "labels", "value"])
        for name in ("replicas_spec", "replicas_ready", "replicas"):
            for ts, v in replicas:
                w.writerow([ts, name, json.dumps({"deployment": "vllm"}), v])
        w.writerow([T0 + 10, "cpu_cores", json.dumps({"container": "vllm", "pod": "vllm-a"}), 0.5])
        w.writerow([T0 + 10, "cpu_cores", json.dumps({"container": "loadgen", "pod": "lg"}), 0.9])
        w.writerow([T0, "_error_gpu_util", "{}", "không có GPU"])
    lines = [json.dumps(a) for a in alerts or []]
    (d / "alerts.jsonl").write_text("".join(x + "\n" for x in lines), encoding="utf-8")
    return d


def _a2_scaled(root: Path, **kw) -> Path:
    """A2 × KB2: pod mới tạo lúc spike + 20 s, Ready lúc + 80 s, bị xoá ở pha drop."""
    pods = [
        _pod("vllm-a", T0 - 3600, T0 - 3590, None),
        _pod("vllm-b", T0 + 260, T0 + 320, T0 + 1200),
    ]
    reps = [(T0 + t, 1.0 if t < 260 or t >= 1195 else 2.0) for t in range(-30, 1500, 5)]
    return write_attempt(root, pods=pods, replicas=reps, **kw)


def test_kb2_row_has_reaction_recovery_and_gpu(tmp_path):
    _a2_scaled(tmp_path, requests=_requests(errors={900}))
    res = bt.build([tmp_path / "s"])
    (row,) = res["runs"]
    assert row["counted"] and row["valid"]
    assert row["scored_phases"] == "pre+spike+drop" and row["scored_start_s"] == 120
    assert (row["detect_s"], row["create_to_ready_s"], row["react_s"]) == (20.0, 60.0, 80.0)
    assert row["replicas_at_rise"] == 1  # mẫu lúc 240 vẫn là 1 replica
    # Xấu tới 299,5 → τ đầu tiên cửa sổ 30 s chỉ còn ≤ 1 request xấu = 329 (như test_metrics), tính từ 240
    assert row["recovery_s"] == pytest.approx(89)
    assert row["n_error_drop"] == 1 and row["n_error"] == 1 and row["error_types"] == "Timeout=1"
    assert row["gpu_s"] == pytest.approx(1440 + (1200 - 260))
    assert row["scale_ups"] == 1 and row["scale_downs"] == 1 and row["flaps"] == 0
    assert row["replicas_max"] == 2
    assert row["vllm_cpu_cores_mean"] == pytest.approx(0.5)  # chỉ container vllm, không lẫn loadgen
    assert math.isnan(row["gpu_util_mean"])  # truy vấn GPU lỗi trên kind: để trống, không phải 0
    assert [p["phase"] for p in res["phases"]] == ["pre", "spike", "drop"]


def test_counted_is_last_valid_attempt_and_baseline_ratio(tmp_path):
    _a2_scaled(tmp_path, attempt="attempt-1", valid=False)
    _a2_scaled(tmp_path, attempt="attempt-2")
    pods_s3 = [_pod(f"vllm-{i}", T0 - 3600, T0 - 3590, None) for i in "abc"]
    write_attempt(tmp_path, run_id="S4-KB2-1", config="S4", pods=pods_s3)
    res = bt.build([tmp_path / "s"], baseline="S4")
    by = {(r["run_id"], r["attempt"]): r for r in res["runs"]}
    assert not by[("A2-KB2-1", "attempt-1")]["counted"]
    a2 = by[("A2-KB2-1", "attempt-2")]
    assert a2["counted"]
    assert a2["gpu_vs_baseline"] == pytest.approx((1440 + 940) / (3 * 1440))
    assert a2["slo_delta_vs_baseline_pp"] == pytest.approx(0.0)  # cùng log request
    cells = {c["config"]: c for c in res["cells"]}
    assert cells["A2"]["n_runs"] == 1 and cells["A2"]["run_ids"] == "s/A2-KB2-1"
    assert cells["S4"]["gpu_vs_baseline_mean"] == pytest.approx(1.0)
    old = [p for p in res["phases"] if (p["run_id"], p["attempt"]) == ("A2-KB2-1", "attempt-1")]
    assert len(old) == 3 and not any(p["counted"] for p in old)


def test_alerts_rows_and_false_pages(tmp_path):
    # LLMSLOBurnFast kêu hai đợt: đợt đầu còn sót từ lượt trước (đã kêu trước pha chính), đợt sau do quá tải
    # thật. LLMPodPending cũng còn sót từ lượt trước. Chỉ đợt sau được đếm và dùng cho thời gian tới cảnh báo.
    burn = {"labels": {"alertname": "LLMSLOBurnFast", "severity": "page"}, "first": T0 - 5, "last": T0 + 400}
    burn["episodes"] = [[T0 - 5, T0 + 30], [T0 + 330, T0 + 400]]
    alerts = [
        {"labels": {"alertname": "Watchdog", "severity": "none"}, "first": T0, "last": T0 + 1500},
        burn,
        {"labels": {"alertname": "LLMPodPending", "severity": "ticket"}, "first": T0 - 5, "last": T0 + 60},
    ]
    write_attempt(tmp_path, alerts=alerts, requests=_requests(bad=(240.0, 400.0)))
    res = bt.build([tmp_path / "s"])
    (row,) = res["runs"]
    names = [(a["alertname"], a["firing_at_start"]) for a in res["alerts"]]  # bỏ Watchdog
    assert names == [("LLMSLOBurnFast", True), ("LLMSLOBurnFast", False), ("LLMPodPending", True)]
    assert row["pages"] == 1 and row["tickets"] == 0 and row["false_pages"] == 0
    assert row["alertnames"] == "LLMSLOBurnFast"
    assert row["alerts_at_start"] == "LLMPodPending LLMSLOBurnFast"
    # Đợt sót lại không bị chấm là page giả (5 phút trước mép đầu không có request nào)
    assert res["alerts"][0]["false_page"] is None and res["alerts"][1]["false_page"] is False
    # Xấu từ 240,5: cửa sổ 1 phút vượt 20 % ở τ = 253 (13/60 xấu); đợt kêu thật lúc 330 → 77 s
    assert row["slo_violation_s"] == pytest.approx(253)
    assert row["time_to_alert_s"] == pytest.approx(77)


def test_violation_without_alert_and_alert_already_firing(tmp_path):
    # Lượt 1: vi phạm (xấu 240–400) mà LLMSLOBurnFast không kêu → trượt N7.
    write_attempt(tmp_path, requests=_requests(bad=(240.0, 400.0)))
    # Lượt 2: LLMSLOBurnFast còn kêu từ lượt trước tới qua mốc vi phạm → đã báo, không đo được thời gian.
    burn = {"labels": {"alertname": "LLMSLOBurnFast", "severity": "page"}, "first": T0 - 40, "last": T0 + 400}
    write_attempt(tmp_path, run_id="A2-KB2-2", alerts=[burn], requests=_requests(bad=(240.0, 400.0)))
    res = bt.build([tmp_path / "s"])
    r1, r2 = res["runs"]
    assert r1["slo_violation_s"] is not None and r1["slo_alert_s"] is None and not r1["slo_alert_at_start"]
    assert r2["slo_alert_at_start"] and r2["slo_alert_s"] is None and r2["time_to_alert_s"] is None
    (cell,) = res["cells"]
    assert cell["n_violation_no_alert"] == 1
    assert (r1["git_commit"], r1["git_runner_commit"]) == ("bbb", "aaa")


def test_build_skips_broken_and_duplicate_inputs(tmp_path):
    write_attempt(tmp_path)
    bad = write_attempt(tmp_path, run_id="A2-KB2-2")
    (bad / "loadgen.json").write_text("{", "utf-8")  # ghi dở
    res = bt.build([tmp_path / "s", tmp_path / "s"])
    assert [r["run_id"] for r in res["runs"]] == ["A2-KB2-1"]
    assert any("JSONDecodeError" in s for s in res["skipped"])
    assert any("trùng thư mục" in s for s in res["skipped"])


def test_cell_value_keeps_sign_of_infinity():
    assert (bt._cell_value(float("inf")), bt._cell_value(float("-inf"))) == ("inf", "-inf")


def test_cells_count_runs_that_did_not_recover(tmp_path):
    _a2_scaled(tmp_path)
    _a2_scaled(tmp_path, run_id="A2-KB2-2", requests=_requests(bad=(240.0, 840.0)))  # xấu suốt spike
    (cell,) = bt.build([tmp_path / "s"])["cells"]
    assert cell["n_runs"] == 2 and cell["n_not_recovered"] == 1 and cell["n_no_new_ready"] == 0
    assert cell["recovery_s_mean"] == pytest.approx(89)  # trung bình chỉ của lượt hồi phục được


def test_skips_incomplete_attempts_and_missing_timeline(tmp_path):
    d = write_attempt(tmp_path)
    (d / "pods_timeline.json").unlink()
    broken = tmp_path / "s" / "S1-KB2-1" / "attempt-1"
    broken.mkdir(parents=True)
    (broken / "error.txt").write_text("Traceback …", "utf-8")
    res = bt.build([tmp_path / "s"])
    assert len(res["runs"]) == 1 and len(res["skipped"]) == 1
    assert "thiếu metadata.json" in res["skipped"][0]
    assert math.isnan(res["runs"][0]["gpu_s"])  # lượt trước PR #25: không ghi 0
    assert res["runs"][0]["gpu_s_ksm"] == pytest.approx(1440)
    assert res["runs"][0]["has_timeline"] is False


def test_cells_do_not_count_missing_timeline_as_no_new_ready(tmp_path):
    # A2 × KB2 trước 09/11: không có pods_timeline.json nên react_s trống vì thiếu dữ liệu, không phải trượt
    (_a2_scaled(tmp_path) / "pods_timeline.json").unlink()
    _a2_scaled(tmp_path, run_id="A2-KB2-2")
    (cell,) = bt.build([tmp_path / "s"])["cells"]
    assert cell["n_runs"] == 2 and cell["n_no_new_ready"] == 0
    assert cell["react_s_min"] == cell["react_s_max"] == pytest.approx(80)  # chỉ lượt có dữ liệu


def test_main_writes_csv_with_empty_nan(tmp_path, capsys):
    _a2_scaled(tmp_path)
    out = tmp_path / "out"
    assert bt.main([str(tmp_path / "s"), "--out", str(out)]) == 0
    with (out / "runs.csv").open(encoding="utf-8") as fh:
        (row,) = list(csv.DictReader(fh))
    assert list(row) == bt.RUN_COLUMNS
    assert row["gpu_util_mean"] == "" and row["gpu_vs_baseline"] == ""  # NaN → rỗng; không có S4
    assert row["react_s"] == "80.0" and row["counted"] == "True"
    assert {p.name for p in out.iterdir()} == {"runs.csv", "phases.csv", "cells.csv", "alerts.csv"}
    assert "s/A2-KB2-1/attempt-1: SLO" in capsys.readouterr().out
