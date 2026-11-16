"""Test cho analysis/lt5_little.py (LT5, Môi trường §19).

Khái niệm: Dựng dữ liệu giả có lời giải tính tay: request đến đều mỗi giây, thời gian phục vụ cố định 3 s,
    nên ở trạng thái dừng có đúng L = λ × W = 1 × 3 = 3 request trong hệ thống ở mọi thời điểm. Thư mục lượt
    giả có đúng các file runner ghi (metadata.json, loadgen.json, requests.csv, metrics.csv.gz).
Mục đích: Kiểm đẳng thức Little trên cửa sổ hữu hạn (phần edge), sai số chuẩn khi lấy mẫu, cách cộng chuỗi
    theo pod, cờ request lỗi, đổi đồng hồ máy tạo tải sang giờ thực, mà không cần cluster.
"""

from __future__ import annotations

import csv
import gzip
import json
import math
import random
from pathlib import Path

import pytest

from analysis import lt5_little as lt
from analysis import metrics as m

T0 = 1_800_000_000.0


def req(i: int, s: float | None, e: float | None, error: str = "") -> m.Request:
    return m.Request(id=i, t_sched=s or 0.0, t_send=s, t_first=s, t_last=e, n_out=256, error=error)


def test_occupancy_se_independent_and_correlated_samples() -> None:
    # W < bước lấy mẫu: các mẫu độc lập, Var = λW ÷ n (phân phối Poisson)
    assert lt.occupancy_se(2.0, 1.0, 24) == pytest.approx(math.sqrt(2.0 / 24))
    # W = 13 s, bước 5 s: Σ_k (W − 5|k|)+ = 13 + 2 × (8 + 3) = 35
    assert lt.occupancy_se(0.5, 13.0, 24) == pytest.approx(math.sqrt(0.5 * 35 / 24))
    assert math.isnan(lt.occupancy_se(0.0, 1.0, 24))
    assert math.isnan(lt.occupancy_se(1.0, 1.0, 0))


def test_little_identity_holds_exactly_on_any_window() -> None:
    rnd = random.Random(1)
    intervals = []
    for _ in range(500):
        s = rnd.uniform(-50, 250)
        intervals.append((s, s + rnd.expovariate(0.2)))
    c = lt.client_occupancy(intervals, 0.0, 200.0)
    assert c["L_client"] == pytest.approx(c["lam"] * c["w"] + c["edge"], abs=1e-9)


def test_stationary_window_has_no_edge_and_matches_samples() -> None:
    intervals = [(i + 0.25, i + 3.25) for i in range(-50, 150)]
    c = lt.client_occupancy(intervals, 0.0, 100.0)
    assert (c["n"], c["lam"], c["w"]) == (100, 1.0, pytest.approx(3.0))
    assert c["L_client"] == pytest.approx(3.0)
    assert c["edge"] == pytest.approx(0.0)  # vào = tràn = 0,25 + 1,25 + 2,25 = 3,75 request·giây
    assert lt.in_flight(intervals, [2.5 + 5 * j for j in range(20)]) == [3] * 20


def test_growing_queue_makes_edge_negative() -> None:
    # E2E tăng dần như khi hàng đợi dài ra: request gửi cuối cửa sổ còn nằm lại lâu sau b
    intervals = [(float(i), i + 1 + 0.5 * i) for i in range(100)]
    c = lt.client_occupancy(intervals, 0.0, 100.0)
    assert c["edge"] < 0
    assert c["L_client"] < c["lam"] * c["w"]


def test_server_series_sums_pods_and_queues() -> None:
    met = {
        "vllm_running": [(10.0, {"pod": "a"}, 3.0), (10.0, {"pod": "b"}, 2.0), (15.0, {"pod": "a"}, 4.0)],
        "vllm_waiting": [(10.0, {"pod": "a"}, 1.0), (15.0, {"pod": "a"}, 0.0)],
    }
    # Mốc 15: pod b đã bị xoá nên không có mẫu, đóng góp 0
    assert lt.server_series(met) == [(10.0, 6.0), (15.0, 4.0)]


def test_error_before_window_end_marks_window_not_applicable() -> None:
    reqs = [req(0, 1.0, 4.0), req(1, 2.0, None, "Timeout"), req(2, 3.0, 9.0)]
    server = [(2.5, 2.0), (7.5, 1.0)]
    row = lt.little_window(reqs, server, [], 0.0, 10.0, first_error_send=2.0)
    assert row["applicable"] is False
    assert (row["n_sent"], row["n_error"]) == (3, 1)
    assert row["e2e_mean_s"] == pytest.approx(4.5)  # chỉ request thành công: (3 + 6) ÷ 2
    later = lt.little_window(reqs, server, [], 0.0, 1.5, first_error_send=2.0)
    assert later["applicable"] is True  # lỗi đầu tiên gửi sau khi cửa sổ đã đóng


def test_queue_disables_sampling_error() -> None:
    reqs = [req(i, float(i), i + 3.0) for i in range(20)]
    server = [(2.5 + 5 * j, 3.0) for j in range(4)]
    waiting = [(2.5 + 5 * j, 2.0) for j in range(4)]
    row = lt.little_window(reqs, server, waiting, 0.0, 20.0, first_error_send=None)
    assert row["waiting_mean"] == 2.0
    assert math.isnan(row["se_sampling"]) and math.isnan(row["z_server"])


def test_to_wall_undoes_fast_monotonic_clock() -> None:
    r = req(0, T0 + 102.0, T0 + 204.0)
    w = lt.to_wall(r, T0, 1.02)
    assert (w.t_send, w.t_last) == (pytest.approx(T0 + 100.0), pytest.approx(T0 + 200.0))
    assert lt.to_wall(req(1, T0 + 5.0, None), T0, 1.02).t_last is None
    assert lt.to_wall(r, T0, 1.0) is r


def test_clock_rate_bounds() -> None:
    lo, hi = lt.clock_rate_bounds(1020.0, T0, T0 + 1000.0)
    assert lo == pytest.approx(1020 / 1001)
    assert hi == pytest.approx(1020 / (1000 - lt.DONE_POLL_MAX_S - lt.CLOCK_MARGIN_S))


def test_parse_source() -> None:
    assert lt.parse_source("runs/sim/x@1.031") == (Path("runs/sim/x"), 1.031)
    assert lt.parse_source("runs/sim/x") == (Path("runs/sim/x"), 1.0)
    assert lt.parse_source("runs/a@b") == (Path("runs/a@b"), 1.0)


def test_capacity_level_treats_missing_waiting_as_queued() -> None:
    base = {"lambda_rps": 2.0, "n_measured": 240}
    assert lt.capacity_level({**base, "waiting_mean": 0.0}, 120.0)["queued"] is False
    assert lt.capacity_level({**base, "waiting_mean": 1.0}, 120.0)["queued"] is True
    assert lt.capacity_level(base, 120.0)["queued"] is True  # file cũ không có trường
    assert lt.capacity_level({**base, "waiting_mean": float("nan")}, 120.0)["queued"] is True
    lv = lt.capacity_level({**base, "loadgen_valid": False}, 120.0)
    assert (lv["run_id"], lv["valid"], lv["lambda_real"]) == ("lambda-2", False, 2.0)


def test_from_capacity_uses_real_arrival_rate(tmp_path: Path) -> None:
    p = tmp_path / "capacity.json"
    curves = [
        {"lambda_rps": 2.0, "n_measured": 243, "e2e_mean_s": 0.918, "B_client": 1.855, "B_server": 2.125,
         "waiting_mean": 0.0, "n_error": 0, "valid": True},
        {"lambda_rps": 14.0, "n_measured": 1696, "e2e_mean_s": 14.911, "B_client": 183.958,
         "B_server": 181.958, "waiting_mean": 166.0, "n_error": 0, "valid": True},
    ]  # fmt: skip
    p.write_text(json.dumps({"env": "home", "curves": curves}), encoding="utf-8")
    low, high = lt.from_capacity(p, 120.0)
    assert low["lambda_real"] == pytest.approx(243 / 120)
    assert low["L_pred"] == pytest.approx(243 / 120 * 0.918)
    assert low["dev_server"] == pytest.approx(2.125 / (243 / 120 * 0.918) - 1)
    assert low["se_sampling"] == pytest.approx(lt.occupancy_se(243 / 120, 0.918, 24))
    assert math.isnan(high["se_sampling"])  # có hàng đợi


def test_from_capacity_prefers_fields_written_by_new_capacity_py(tmp_path: Path) -> None:
    # ĐG1 trên V2 đo 240 s mỗi mức: file mới ghi window_s và lambda_real_rps, không được dùng 120 s mặc định
    p = tmp_path / "capacity-v2.json"
    curve = {
        "lambda_rps": 2.0, "n_measured": 470, "lambda_real_rps": 1.95, "window_s": 240.0, "e2e_mean_s": 6.0,
        "B_client": 11.7, "B_server": 11.9, "waiting_mean": 0.0, "valid": False,
    }  # fmt: skip
    p.write_text(json.dumps({"env": "cloud", "curves": [curve]}), encoding="utf-8")
    (row,) = lt.from_capacity(p, 120.0)
    assert row["lambda_real"] == 1.95 and row["n_samples"] == 48
    assert row["L_pred"] == pytest.approx(1.95 * 6.0)
    assert row["valid"] is False and "lượt không hợp lệ" in lt.summary([row])


def _write_attempt(d: Path, rate: float) -> None:
    """Lượt giả: request mỗi giây trong [0; 100) giây thật, phục vụ 3 s, chia cho 2 pod; máy tạo tải ghi
    mốc theo đồng hồ chạy nhanh `rate` lần, Prometheus ghi theo giờ thực."""
    d.mkdir(parents=True)
    true = [(i + 0.25, i + 3.25) for i in range(100)]
    with (d / "requests.csv").open("w", newline="", encoding="utf-8") as fh:
        w = csv.writer(fh)
        w.writerow(
            [
                "id",
                "t_sched",
                "t_send",
                "t_first",
                "t_last",
                "n_in_target",
                "n_in",
                "n_out",
                "status",
                "error",
            ]
        )
        for i, (s, e) in enumerate(true):
            w.writerow([i, s * rate, s * rate, (s + 0.2) * rate, e * rate, 500, 508, 256, 200, ""])
    with gzip.open(d / "metrics.csv.gz", "wt", newline="", encoding="utf-8") as fh:
        w = csv.writer(fh)
        w.writerow(["ts", "name", "labels", "value"])
        for j in range(21):
            ts = 2.5 + 5 * j
            for pod in ("a", "b"):
                n = sum(1 for i, (s, e) in enumerate(true) if s <= ts < e and (i % 2 == 0) == (pod == "a"))
                lab = json.dumps({"pod": f"vllm-{pod}"})
                w.writerow([T0 + ts, "vllm_running", lab, n])
                w.writerow([T0 + ts, "vllm_waiting", lab, 0])
    wall_s = true[-1][1] * rate
    lg = {"t0_unix": T0, "duration_s": 100.0 * rate, "wall_s": wall_s, "rate_rps": 1.0,
          "phases_s": {"steady": [0.0, 100.0 * rate]}}  # fmt: skip
    (d / "loadgen.json").write_text(json.dumps(lg), encoding="utf-8")
    meta = {"env": "sim", "run_id": "S1-CONST1-1", "t_main_end": T0 + true[-1][1] + 5.0}
    (d / "metadata.json").write_text(json.dumps(meta), encoding="utf-8")
    (d / "checks.json").write_text(json.dumps({"valid": True, "reasons": []}), encoding="utf-8")


@pytest.mark.parametrize("rate", [1.0, 1.03])
def test_analyze_attempt_end_to_end(tmp_path: Path, rate: float) -> None:
    session = tmp_path / "sim-sess"
    _write_attempt(session / "S1-CONST1-1" / "attempt-1", rate)
    rows, skipped = lt.collect([(session, rate)], 120.0)
    assert skipped == [] and len(rows) == 1
    r = rows[0]
    assert r["window"] == "steady" and r["applicable"] is True
    assert r["attempt"] == "attempt-1" and r["valid"] is True
    assert r["lambda_real"] == pytest.approx(1.0) and r["e2e_mean_s"] == pytest.approx(3.0)
    assert r["L_server"] == pytest.approx(3.0) and r["L_client_sampled"] == pytest.approx(3.0)
    assert r["clock_rate_min"] <= rate <= r["clock_rate_max"]
    out = tmp_path / "lt5.csv"
    assert lt.main([f"{session}@{rate}", "--out", str(out)]) == 0
    with out.open(encoding="utf-8") as fh:
        assert float(next(csv.DictReader(fh))["dev_server"]) == pytest.approx(0.0, abs=1e-6)
