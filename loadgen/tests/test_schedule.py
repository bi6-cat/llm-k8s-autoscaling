"""Test cho schedule.py.

Khái niệm: Kiểm định thống kê đơn giản: số request trong một cửa sổ của quá trình Poisson có trung bình
    μ = ∫λ(t)dt và độ lệch chuẩn √μ. Lệch quá 5√μ thì gần như chắc chắn (xác suất < 1/1.000.000) là
    code sai chứ không phải do ngẫu nhiên.
Mục đích: Lịch tái lập được theo seed, đúng hình dạng λ(t), và độ dài prompt nằm trong 256–1024.
"""

from __future__ import annotations

import math

from loadgen import scenarios
from loadgen.schedule import PROMPT_MAX, PROMPT_MIN, build_plan, derive_seed

M = 60.0


def _count(plan, t0, t1):
    return sum(1 for r in plan if t0 <= r.t_sched < t1)


def _assert_poisson_count(n, mu):
    assert abs(n - mu) < 5 * math.sqrt(mu), f"đếm được {n}, kỳ vọng {mu:.0f} ± {5 * math.sqrt(mu):.0f}"


def test_derive_seed_is_stable_across_versions():
    # Giá trị ghi cứng: nếu ai đó đổi cách sinh seed, lịch của mọi lượt cũ không tái lập được nữa.
    assert derive_seed("KB2", 1, "time") == 5680469916185402054
    assert derive_seed("KB1", 0, "prompt") == 8335992527661694558


def test_same_scenario_and_run_index_gives_same_plan():
    assert build_plan(scenarios.kb2(1.0), 3) == build_plan(scenarios.kb2(1.0), 3)


def test_different_run_index_gives_different_plan():
    a = [r.t_sched for r in build_plan(scenarios.kb1(1.0), 1)]
    b = [r.t_sched for r in build_plan(scenarios.kb1(1.0), 2)]
    assert a != b


def test_prompt_range_does_not_change_send_times():
    # Hai luồng ngẫu nhiên tách biệt: đổi độ dài prompt không được làm đổi lịch gửi
    sc = scenarios.kb2(1.0)
    a = [r.t_sched for r in build_plan(sc, 1)]
    b = [r.t_sched for r in build_plan(sc, 1, prompt_min=10, prompt_max=20)]
    assert a == b


def test_times_sorted_within_duration_and_ids_sequential():
    sc = scenarios.kb3(1.0)
    plan = build_plan(sc, 0)
    ts = [r.t_sched for r in plan]
    assert ts == sorted(ts)
    assert 0 < ts[0] and ts[-1] < sc.duration_s
    assert [r.id for r in plan] == list(range(len(plan)))


def test_kb1_count_matches_rate():
    plan = build_plan(scenarios.kb1(2.0), 0)  # 1 req/s × 1200 s
    _assert_poisson_count(len(plan), 1200)


def test_kb2_shape_low_then_spike_then_low():
    c = 1.0
    plan = build_plan(scenarios.kb2(c), 0)
    _assert_poisson_count(_count(plan, 0, 5 * M), 0.5 * c * 300)
    _assert_poisson_count(_count(plan, 5.5 * M, 15 * M), 3.0 * c * 570)
    _assert_poisson_count(_count(plan, 15.5 * M, 25 * M), 0.5 * c * 570)


def test_prompt_lengths_uniform_in_range():
    plan = build_plan(scenarios.kb1(2.0), 0)
    lengths = [r.n_in_target for r in plan]
    assert min(lengths) >= PROMPT_MIN and max(lengths) <= PROMPT_MAX
    # ~1200 mẫu đều trên [256, 1024]: phải chạm gần cả hai đầu và trung bình gần 640
    assert min(lengths) < PROMPT_MIN + 20 and max(lengths) > PROMPT_MAX - 20
    assert abs(sum(lengths) / len(lengths) - 640) < 20


def test_zero_rate_gives_empty_plan():
    assert build_plan(scenarios.constant(0.0, 60), 0) == []
