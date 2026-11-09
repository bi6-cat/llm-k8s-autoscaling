"""Chấm điểm kịch bản vận hành: đúng tiêu chí của Môi trường §13.

Khái niệm: analyze_requests và grade là hàm thuần nên kiểm được không cần cluster.
Mục đích: Tránh báo "đạt" oan: stream bị cắt có status 200, kịch bản không có request nào không được coi là
    0 lỗi, và vh3-kill được phép có lỗi nhưng phải thật sự restart.
"""

from __future__ import annotations

from experiments.ops.vh import analyze_requests, grade

CLEAN = {"requests": 100, "errors": 0, "by_error": {}}
DIRTY = {"requests": 100, "errors": 2, "by_error": {"IncompleteStream": 2}}


def test_cut_stream_with_status_200_counts_as_error():
    rows = [{"status": "200", "error": ""}, {"status": "200", "error": "IncompleteStream"}]
    assert analyze_requests(rows) == {"requests": 2, "errors": 1, "by_error": {"IncompleteStream": 1}}


def test_no_requests_is_not_a_pass():
    assert grade("vh3-delete", {"requests": 0, "errors": 0}, {"recovered": True})


def test_delete_needs_zero_errors():
    assert not grade("vh3-delete", CLEAN, {"recovered": True})
    assert grade("vh3-delete", DIRTY, {"recovered": True})


def test_kill_allows_errors_but_needs_restart():
    assert not grade("vh3-kill", DIRTY, {"recovered": True, "restarted": True})
    assert grade("vh3-kill", CLEAN, {"recovered": True, "restarted": False})


def test_vh4_enforces_the_30_second_limit():
    ok = {
        "recovered": True,
        "fallback_s": 23.0,
        "unblocked_ok": True,
        "replicas_before": 1,
        "max_replicas": 3,
    }
    assert not grade("vh4", CLEAN, ok)
    assert grade("vh4", CLEAN, {**ok, "fallback_s": 31.0})
    assert grade("vh4", CLEAN, {**ok, "fallback_s": None})
    assert grade("vh4", CLEAN, {**ok, "unblocked_ok": False})


def test_vh2c_must_get_stuck():
    assert not grade("vh2c", DIRTY, {"recovered": True, "rollout_stuck": True})
    assert grade("vh2c", CLEAN, {"recovered": True, "rollout_stuck": False})


def test_vh4_starting_at_max_proves_nothing():
    # 09/11: tải đã đẩy lên max trước khi chặn, script báo fallback sau 0,09 s và "đạt" oan
    facts = {
        "recovered": True,
        "fallback_s": 0.1,
        "unblocked_ok": True,
        "replicas_before": 3,
        "max_replicas": 3,
    }
    assert grade("vh4", CLEAN, facts)


def test_vh2a_must_start_from_one_replica():
    assert not grade("vh2a", CLEAN, {"recovered": True, "replicas_before": 1})
    assert grade("vh2a", CLEAN, {"recovered": True, "replicas_before": 3})
