"""Test cho checks.py.

Mục đích: Phân vị tính đúng; lượt bị đánh dấu không hợp lệ khi lệch lịch, event loop, CPU hoặc throttle
    vượt ngưỡng.
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
    s = summarize([_records([1, 2, 3] * 100)], [[0.001] * 10], 0.3, None, None)
    assert s["send_lag_ok"] and s["loop_lag_ok"] and s["cpu_ok"]
    assert s["throttle_ok"] is None  # không chạy trong container: không đo được, không tính là trượt
    assert s["valid"] is True


@pytest.mark.parametrize(
    "lags_s, ok",
    [
        ([0.002] * 1000, True),
        ([0.002] * 980 + [0.080] * 20, False),  # p99 80 ms > 50 ms: loop bận kéo dài
        ([0.002] * 999 + [0.700], False),  # một lần nghẽn 700 ms > 500 ms: p99 không thấy, max bắt
        ([0.002] * 999 + [0.300], True),  # 300 ms lẻ (ví dụ một lần GC) vẫn đạt
        ([], None),  # không có mẫu: không chấm
    ],
)
def test_summarize_loop_lag(lags_s, ok):
    s = summarize([_records([1])], [lags_s], 0.1, None, None)
    assert s["loop_lag_ok"] is ok
    assert s["valid"] is (ok is not False)


def test_summarize_invalid_when_send_lag_p99_too_high():
    s = summarize([_records([1] * 90 + [120] * 10)], [[]], 0.1, None, None)
    assert s["send_lag_ms"]["p99"] > 50
    assert s["valid"] is False


def test_summarize_invalid_when_cpu_too_high():
    assert summarize([_records([1])], [[]], 0.85, None, None)["valid"] is False


def test_summarize_throttle_by_time_fraction():
    before = {"nr_periods": 100, "nr_throttled": 2, "throttled_usec": 500}
    # Ca ĐG1-mini 05/11: 1 chu kỳ, 4,4 ms trong mức ~180 s (~0,0024%): đạt
    after = {"nr_periods": 1900, "nr_throttled": 3, "throttled_usec": 4900}
    s = summarize([_records([1])], [[]], 0.1, before, after, cgroup_elapsed_s=180.0)
    assert s["cgroup_throttle"]["nr_throttled"] == 1
    assert s["throttled_pct"] == pytest.approx(0.0024, abs=1e-4)
    assert s["throttle_ok"] is True and s["valid"] is True
    # 0,3 s bị dừng trong 180 s (~0,17% > 0,1%): trượt
    after = {**after, "nr_throttled": 12, "throttled_usec": 500 + 300_000}
    s = summarize([_records([1])], [[]], 0.1, before, after, cgroup_elapsed_s=180.0)
    assert s["throttle_ok"] is False and s["valid"] is False


def test_summarize_throttle_falls_back_to_count_without_time():
    # Không tính được tỷ lệ (thiếu thời gian đo hoặc thiếu throttled_usec): dùng tiêu chí cũ, không bỏ qua
    before, after = {"nr_throttled": 2, "throttled_usec": 0}, {"nr_throttled": 3, "throttled_usec": 100}
    assert summarize([_records([1])], [[]], 0.1, before, after)["throttle_ok"] is False
    s = summarize([_records([1])], [[]], 0.1, {"nr_throttled": 2}, {"nr_throttled": 2}, cgroup_elapsed_s=60.0)
    assert s["throttle_ok"] is True and s["throttled_pct"] is None


def test_read_cgroup_cpu_stat(tmp_path):
    f = tmp_path / "cpu.stat"
    f.write_text("usage_usec 123\nnr_periods 10\nnr_throttled 1\nthrottled_usec 40\n")
    assert read_cgroup_cpu_stat(f) == {"nr_periods": 10, "nr_throttled": 1, "throttled_usec": 40}
    assert read_cgroup_cpu_stat(tmp_path / "khong-co") is None


def test_summarize_loop_lag_takes_worst_worker():
    # 4 tiến trình, một tiến trình p99 80 ms. Gộp mẫu thì nó chỉ là 0,25% mẫu chung, p99 chung ~2 ms
    # (trông như đạt); chấm theo từng loop thì thấy.
    busy = [0.002] * 980 + [0.080] * 20
    s = summarize([_records([1])], [[0.002] * 1000] * 3 + [busy], 0.1, None, None)
    assert s["loop_lag_ms"]["p99"] == pytest.approx(80.0)
    assert s["loop_lag_ok"] is False and s["valid"] is False
    # Tiến trình không có mẫu nào (không được chia request) thì bỏ qua, không làm hỏng kết quả
    assert summarize([_records([1])], [[0.002] * 10, []], 0.1, None, None)["loop_lag_ok"] is True


def test_summarize_send_lag_takes_worst_worker():
    # 3 tiến trình, một tiến trình gửi trễ 2% request (> 50 ms). Gộp lại chỉ còn ~0,67% mẫu, p99 chung ~1 ms
    # (trông như đạt); chấm theo từng tiến trình thì thấy.
    late = _records([1] * 98 + [80] * 2)
    s = summarize([_records([1] * 100), _records([1] * 100), late], [[0.001]], 0.1, None, None)
    assert s["send_lag_ms"]["p99"] > 50 and s["send_lag_ok"] is False and s["valid"] is False
    # Tiến trình không có request nào thì bỏ qua
    assert summarize([_records([1] * 10), []], [[0.001]], 0.1, None, None)["send_lag_ok"] is True


def test_summarize_complete_requires_every_planned_request_and_worker():
    s = summarize([_records([1] * 10)], [[0.001]], 0.1, None, None, n_planned=10)
    assert s["complete_ok"] is True and s["valid"] is True
    # Thiếu 1 dòng (ví dụ ghi CSV lỗi): không hợp lệ, dù mọi số đo khác đạt
    s = summarize([_records([1] * 9)], [[0.001]], 0.1, None, None, n_planned=10)
    assert s["complete_ok"] is False and s["valid"] is False
    s = summarize([_records([1] * 10)], [[0.001]], 0.1, None, None, n_planned=10, workers_failed=1)
    assert s["complete_ok"] is False and s["valid"] is False
