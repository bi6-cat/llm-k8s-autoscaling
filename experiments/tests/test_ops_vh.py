"""Chấm điểm kịch bản vận hành: đúng tiêu chí của Môi trường §13.

Khái niệm: analyze_requests và grade là hàm thuần nên kiểm được không cần cluster.
Mục đích: Tránh báo "đạt" oan: stream bị cắt có status 200, kịch bản không có request nào không được coi là
    0 lỗi, và vh3-kill được phép có lỗi nhưng phải thật sự restart.
"""

from __future__ import annotations

import pytest

from experiments.ops.vh import (
    REPO,
    SIM_A2_KUSTOMIZATION,
    SIM_SERVING_PATCH,
    analyze_requests,
    argocd_problem,
    grade,
    with_min_replicas,
    with_ttft,
)

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


def test_delete_with_a_single_pod_is_not_a_pass():
    # Xoá pod duy nhất thì không còn pod phục vụ: dù không ghi nhận lỗi cũng không kết luận được
    assert grade("vh3-delete", CLEAN, {"recovered": True, "ready_before": 1})
    assert not grade("vh3-delete", CLEAN, {"recovered": True, "ready_before": 2})


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


def test_git_update_needs_zero_errors_sync_and_both_versions():
    phases = {"min2": {"sync_s": 90.0}, "update": {"sync_s": 120.0}}
    good = {"recovered": True, "replicas_before": 1, "new_version_seen": True, "old_version_back": True}
    assert not grade("vh2-git", CLEAN, {**good, "phases": phases})
    assert grade("vh2-git", DIRTY, {**good, "phases": phases})
    # Argo CD không sync một commit: không kết luận được về vòng Git
    assert grade("vh2-git", CLEAN, {**good, "phases": {**phases, "rollback": {"sync_s": None}}})
    # Rollout xong nhưng tham số không đổi: cập nhật không thật sự đi qua Git
    assert grade("vh2-git", CLEAN, {**good, "new_version_seen": False, "phases": phases})
    assert grade("vh2-git", CLEAN, {**good, "replicas_before": 2, "phases": phases})


def test_min_replicas_patch_is_inserted_once_and_reverts_cleanly():
    text = (REPO / SIM_A2_KUSTOMIZATION).read_text(encoding="utf-8")
    new = with_min_replicas(text, 2)
    assert new.count("path: /spec/minReplicaCount\n        value: 2\n") == 1
    # Chỉ thêm dòng, không sửa dòng cũ: `git revert` trả lại đúng file ban đầu
    assert (
        new.replace("      - op: replace\n        path: /spec/minReplicaCount\n        value: 2\n", "")
        == text
    )
    with pytest.raises(ValueError):
        with_min_replicas("resources: []\n", 2)


def test_ttft_flag_is_changed_exactly_once():
    text = (REPO / SIM_SERVING_PATCH).read_text(encoding="utf-8")
    assert "--time-to-first-token=300ms" in with_ttft(text, 300)
    with pytest.raises(ValueError):
        with_ttft(text + "    - --time-to-first-token=1ms\n", 300)


def test_argocd_must_autosync_from_the_given_branch():
    app = {
        "metadata": {"name": "serving"},
        "spec": {"source": {"targetRevision": "feat/x"}, "syncPolicy": {"automated": {}}},
    }
    assert argocd_problem(app, "feat/x") is None
    assert "main" in argocd_problem(
        {**app, "spec": {**app["spec"], "source": {"targetRevision": "main"}}}, "feat/x"
    )
    assert argocd_problem({**app, "spec": {**app["spec"], "syncPolicy": {}}}, "feat/x")
