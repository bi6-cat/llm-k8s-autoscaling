"""Test phần hàm thuần của experiments/ops/lt8_burn.py (LT8, Môi trường §19).

Khái niệm: latency_for chọn (μ, σ) để P(TTFT > 2,5 s) = x với σ = 0,3 μ; plan và rotate dựng lịch bơm.
Mục đích: Bắt lỗi chọn tham số khiến simulator từ chối (σ > 0,3 μ) hoặc cho tỷ lệ xấu khác x, và lịch bơm
    không chừa đủ 5 phút nền trước mỗi lần bơm.
"""

from __future__ import annotations

from statistics import NormalDist

import pytest

from experiments.ops.lt8_burn import latency_for, plan, rotate


@pytest.mark.parametrize("x", [0.1, 0.3, 0.6])
def test_latency_gives_target_bad_fraction_within_simulator_limits(x):
    mu, sd = latency_for(x)
    assert sd <= 0.3 * mu  # simulator trả 400 nếu σ > 0,3 μ
    assert 0.3 * mu < 2500 < 1.7 * mu  # ngưỡng nằm trong khoảng không bị cắt
    assert 1 - NormalDist(mu, sd).cdf(2500) == pytest.approx(x, abs=0.002)


def test_known_values_used_on_kind():
    assert latency_for(0.6) == (2706, 811)  # giá trị lượt chạy thử 16/11


@pytest.mark.parametrize("x", [0, 1, 0.001])
def test_unreachable_levels_are_rejected(x):
    with pytest.raises(ValueError):
        latency_for(x)  # 0,001: μ ≈ 1,3 s, 1,7 μ < 2,5 s nên mọi mẫu bị cắt dưới ngưỡng


def test_plan_keeps_five_minutes_of_clean_traffic_before_each_injection():
    sched, total = plan([0.1, 0.3, 0.6], warm_s=330, inject_s=360, gap_s=330, tail_s=120)
    assert [(s["start"], s["end"]) for s in sched] == [(330, 690), (1020, 1380), (1710, 2070)]
    assert total == 2190
    gaps = [sched[0]["start"]] + [b["start"] - a["end"] for a, b in zip(sched, sched[1:], strict=False)]
    assert min(gaps) >= 300


def test_rotate_puts_each_level_first_once():
    assert [rotate([1, 2, 3], k)[0] for k in range(3)] == [1, 2, 3]
    assert rotate([1, 2, 3], 4) == [2, 3, 1]
