"""Test cho analysis/lt6_gpu_util.py (LT6, Môi trường §19).

Khái niệm: Các giá trị kỳ vọng tính tay từ mô hình util = 1 − e^(−L) và phép tính của HPA (threshold 70 %,
    tolerance 10 %). File capacity giả có đúng các trường mà experiments/runner/capacity.py ghi.
Mục đích: Kiểm mô hình util, số replica A1 leo tới, cách chia nhóm tải vừa và quá tải, phép kiểm "tách được",
    và đường đi từ file capacity tới CSV, mà không cần cluster.
"""

from __future__ import annotations

import csv
import json
import math
from pathlib import Path

import pytest

from analysis import lt6_gpu_util as lt


def test_util_pred_and_inverse() -> None:
    assert lt.util_pred(0.0) == 0.0
    assert lt.util_pred(2.0) == pytest.approx(1 - math.exp(-2))  # 0,865
    assert lt.l_for_util(lt.util_pred(1.3)) == pytest.approx(1.3)
    # Dải giữ nguyên của A1 70 %: util ∈ [63 %; 77 %] ⇔ L mỗi pod ∈ [0,994; 1,470]
    assert lt.l_for_util(0.77) == pytest.approx(1.470, abs=1e-3)
    assert lt.l_for_util(0.63) == pytest.approx(0.994, abs=1e-3)


@pytest.mark.parametrize(
    ("l_total", "hi", "expected"),
    [
        (0.5, 4, 1),  # util 0,39 → tổng 39 < 70: không lên
        # r = 1: util 0,865 → tỷ lệ 1,24 → ⌈1,24⌉ = 2; r = 2: util(1,0) = 0,632 → tỷ lệ 0,90 → giữ 2
        (2.0, 4, 2),
        # r = 1 → 2; r = 2: util(2,0) = 0,865 → ⌈2,47⌉ = 3; r = 3: util(1,33) = 0,736 → tỷ lệ 1,05 → giữ 3
        (4.0, 4, 3),
        # 1 → 2 → 3 → 4: ở r = 3, util(1,77) = 0,829 → ⌈3,55⌉ = 4 = max
        (5.3, 4, 4),
        (100.0, 1, 1),
    ],
)
def test_a1_replicas_hand_computed(l_total: float, hi: int, expected: int) -> None:
    assert lt.a1_replicas(l_total, 70.0, hi) == expected


def test_a1_replicas_stops_inside_tolerance_band() -> None:
    # Không kẹp max: A1 dừng khi util mỗi pod rơi vào [63 %; 77 %], tức L mỗi pod ≤ 1,47, còn A2
    # (threshold 21) dừng ở ⌈100 ÷ 21⌉ = 5 replica: A1 cần nhiều hơn A2 trên 10 lần.
    r = lt.a1_replicas(100.0, 70.0, 1000)
    assert 0.9 <= lt.util_pred(100.0 / r) / 0.7 <= 1.1
    assert 100.0 / r <= lt.l_for_util(0.77)
    assert r > 10 * lt.predict_replicas(100.0, 21.0, 1, 1000)


@pytest.mark.parametrize(
    ("load", "slo", "expected"),
    [
        (0.3, 1.0, "vừa"),
        (0.7, 1.0, "vừa"),
        (0.17, 1.0, "khác"),
        (1.0, 1.0, "khác"),  # đúng bằng C
        (1.04, 0.99, "khác"),  # trên C nhưng SLO vẫn đạt: không gọi là quá tải
        (1.17, 0.28, "quá tải"),
    ],
)
def test_band(load: float, slo: float, expected: str) -> None:
    assert lt.band(load, slo) == expected


def test_separation() -> None:
    rows = [
        {"band": "vừa", "gpu_util": 0.96, "L": 4.0},
        {"band": "vừa", "gpu_util": 1.0, "L": 9.0},
        {"band": "khác", "gpu_util": 1.0, "L": 27.0},
        {"band": "quá tải", "gpu_util": 0.9996, "L": 68.0},
        {"band": "quá tải", "gpu_util": 1.0, "L": 182.0},
    ]
    util = lt.separation(rows, "gpu_util")
    assert util["separable"] is False
    assert util["moderate"] == (0.96, 1.0)
    assert util["gap"] == pytest.approx(0.9996)
    conc = lt.separation(rows, "L")
    assert conc["separable"] is True
    assert conc["gap"] == pytest.approx(68.0 / 9.0)
    assert lt.separation(rows[:2], "L")["separable"] is None  # thiếu nhóm quá tải


def _curve(lam: float, n: int, b: float, wait: float, util: float, slo: float) -> dict:
    return {
        "lambda_rps": lam, "n_measured": n, "n_error": 0, "e2e_mean_s": 2.0, "B_client": b, "B_server": b,
        "waiting_mean": wait, "kv_cache_usage": 0.05, "gpu_util": util, "slo_attainment": slo,
        "loadgen_valid": True,
    }  # fmt: skip


@pytest.fixture
def capacity_file(tmp_path: Path) -> Path:
    doc = {
        "env": "home",
        "C": 6.0,
        "threshold": {"A1_gpu_util_percent": 70, "A2_concurrency": 21},
        "curves": [
            _curve(3.0, 360, 2.0, 0.0, 0.9, 1.0),
            _curve(7.0, 840, 53.7, 21.8, 1.0, 0.28),
        ],
    }
    p = tmp_path / "capacity-test.json"
    p.write_text(json.dumps(doc), encoding="utf-8")
    return p


def test_from_capacity(capacity_file: Path) -> None:
    mod, over = lt.from_capacity(capacity_file, window_s=120.0, max_replicas=4)
    assert mod["band"] == "vừa" and over["band"] == "quá tải"
    assert mod["lambda_real"] == pytest.approx(3.0)  # 360 ÷ 120 s, file cũ không ghi lambda_real_rps
    assert mod["util_pred"] == pytest.approx(1 - math.exp(-2))
    assert mod["util_dev"] == pytest.approx(0.9 - (1 - math.exp(-2)))
    p = 1 - math.exp(-2)
    assert mod["util_se"] == pytest.approx(math.sqrt(p * (1 - p) / 24))  # 120 s ÷ 5 s = 24 mẫu
    # Ở nhà exporter thấy 1 GPU: tổng 90 → ⌈90 ÷ 70⌉ = 2. A2: 2 ÷ 21 → 1; 53,7 ÷ 21 → ⌈2,56⌉ = 3
    assert (mod["a1_desired_1"], mod["a2_desired_1"]) == (2, 1)
    assert (over["a1_desired_1"], over["a2_desired_1"]) == (2, 3)
    assert (mod["a1_replicas"], mod["a2_replicas"]) == (2, 1)
    # Mức đã xếp hàng: M/G/∞ không đúng nữa, nên không dự đoán util và số replica
    for key in ("util_pred", "util_z", "a1_replicas", "a2_replicas"):
        assert math.isnan(over[key])


def test_main_writes_csv_and_summary(
    capacity_file: Path, tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    out = tmp_path / "lt6.csv"
    assert lt.main([str(capacity_file), "--out", str(out)]) == 0
    with out.open(encoding="utf-8") as fh:
        rows = list(csv.reader(fh))
    assert rows[0] == lt.COLUMNS
    assert len(rows) == 3
    text = capsys.readouterr().out
    assert "A1 gpu_util" in text and "A2 L_server" in text
