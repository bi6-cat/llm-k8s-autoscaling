"""Test cho scenarios.py.

Khái niệm: Mỗi test là một hàm `test_*`; pytest tự tìm và chạy, `assert` sai thì test đỏ.
Mục đích: λ(t) của KB1–KB3 khớp từng con số ở Thông số §7 (sai một hệ số là cả ma trận đánh giá sai).
"""

from __future__ import annotations

import pytest

from loadgen import scenarios

M = 60.0  # một phút, giây


def test_piecewise_linear_interpolates_and_clamps():
    f = scenarios.piecewise_linear([(0, 1.0), (10, 3.0)])
    assert f(-5) == 1.0
    assert f(5) == pytest.approx(2.0)
    assert f(20) == 3.0


def test_piecewise_linear_rejects_unsorted_points():
    with pytest.raises(ValueError):
        scenarios.piecewise_linear([(10, 1.0), (0, 3.0)])


def test_kb1_is_constant_half_c():
    sc = scenarios.kb1(c=2.0)
    assert sc.duration_s == 12 * M
    assert sc.rate(0) == sc.rate(11 * M) == 1.0
    assert sc.phases == {"steady": (2 * M, 12 * M)}


@pytest.mark.parametrize(
    ("t_min", "k"),
    [
        (0, 0.5),  # pre
        (3.9, 0.5),
        (4.25, 1.75),  # giữa đoạn tăng 30 s: (0,5 + 3,0) / 2
        (4.5, 3.0),
        (8, 3.0),  # spike
        (11.25, 1.75),  # giữa đoạn giảm
        (16, 0.5),  # drop
    ],
)
def test_kb2_rate_matches_spec(t_min, k):
    c = 1.2
    assert scenarios.kb2(c).rate(t_min * M) == pytest.approx(k * c)


def test_kb2_duration_and_phases():
    sc = scenarios.kb2(1.0)
    assert sc.duration_s == 21 * M
    assert sc.rate_max == 3.0
    assert sc.phases == {"pre": (2 * M, 4 * M), "spike": (4 * M, 11 * M), "drop": (11 * M, 21 * M)}


def test_kb2_peak_follows_n():
    # Cùng quy tắc với KB3: N = 4 → 3 C (như thiết kế cũ), N = 2 → 1,5 C
    assert scenarios.kb2(c=1.0, n_replicas=2).rate(8 * M) == pytest.approx(1.5)
    assert scenarios.kb2(c=1.0, n_replicas=2).rate_max == pytest.approx(1.5)


def test_kb3_peak_is_075_times_n():
    sc = scenarios.kb3(c=1.0, n_replicas=4)
    assert sc.rate(0) == pytest.approx(0.5)
    assert sc.rate(2.5 * M) == pytest.approx((0.5 + 3.0) / 2)
    assert sc.rate(5 * M) == sc.rate(16 * M) == pytest.approx(3.0)
    assert sc.duration_s == 17 * M
    assert sc.phases == {"ramp": (0.0, 5 * M), "sustain": (5 * M, 17 * M)}
    assert sc.rate_max == pytest.approx(3.0)
    assert scenarios.kb3(c=1.0, n_replicas=2).rate(10 * M) == pytest.approx(1.5)


def test_rate_max_is_upper_bound():
    # Thinning chỉ đúng khi λ(t) ≤ λ_max ở mọi t
    for sc in (
        scenarios.kb1(1.0),
        scenarios.kb2(1.0),
        scenarios.kb2(1.0, 2),
        scenarios.kb2(1.0, 1),
        scenarios.kb3(1.0),
        scenarios.kb3(1.0, 1),
    ):
        assert all(sc.rate(t) <= sc.rate_max + 1e-12 for t in range(0, int(sc.duration_s) + 1, 5))


def test_constant():
    sc = scenarios.constant(rate=2.5, duration_s=300)
    assert sc.rate(0) == sc.rate(299) == 2.5
    assert sc.phases == {"steady": (0.0, 300)}
