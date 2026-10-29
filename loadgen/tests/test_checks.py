"""Test cho checks.py.

Mục đích: Phân vị tính đúng; lượt bị đánh dấu không hợp lệ khi lệch lịch, CPU hoặc throttle vượt ngưỡng.
"""

from __future__ import annotations

import pytest

from loadgen.checks import percentile, read_cgroup_cpu_stat, summarize


def _records(lags_ms):
    return [{"t_sched": 1.0, "t_send": 1.0 + x / 1000} for x in lags_ms]


def test_percentile_linear_interpolation():
    assert percentile([4, 1, 3, 2], 50) == pytest.approx(2.5)
    assert percentile([1, 2, 3, 4], 100) == 4
    assert percentile([], 99) is None


def test_summarize_valid_when_all_within_limits():
    s = summarize(_records([1, 2, 3] * 100), [0.001] * 10, 0.3, None, None)
    assert s["send_lag_ok"] and s["cpu_ok"]
    assert s["throttle_ok"] is None  # không chạy trong container: không đo được, không tính là trượt
    assert s["valid"] is True


def test_summarize_invalid_when_send_lag_p99_too_high():
    s = summarize(_records([1] * 90 + [120] * 10), [], 0.1, None, None)
    assert s["send_lag_ms"]["p99"] > 50
    assert s["valid"] is False


def test_summarize_invalid_when_cpu_too_high():
    assert summarize(_records([1]), [], 0.85, None, None)["valid"] is False


def test_summarize_detects_throttling():
    before = {"nr_periods": 100, "nr_throttled": 2, "throttled_usec": 500}
    after = {"nr_periods": 900, "nr_throttled": 5, "throttled_usec": 9000}
    s = summarize(_records([1]), [], 0.1, before, after)
    assert s["cgroup_throttle"]["nr_throttled"] == 3
    assert s["throttle_ok"] is False and s["valid"] is False


def test_read_cgroup_cpu_stat(tmp_path):
    f = tmp_path / "cpu.stat"
    f.write_text("usage_usec 123\nnr_periods 10\nnr_throttled 1\nthrottled_usec 40\n")
    assert read_cgroup_cpu_stat(f) == {"nr_periods": 10, "nr_throttled": 1, "throttled_usec": 40}
    assert read_cgroup_cpu_stat(tmp_path / "khong-co") is None
