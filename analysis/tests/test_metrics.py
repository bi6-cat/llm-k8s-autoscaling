"""Unit test cho analysis/metrics.py.

Khái niệm: Mỗi test dựng vài request hoặc pod giả có số liệu tính tay được (giây tròn, TTFT 0,2 s hoặc 5 s),
    không cần cluster hay dữ liệu thật.
Mục đích: Giữ đúng các công thức của Môi trường §15 (SLO attainment, phân vị, N2a, N2b, N7, GPU-giờ,
    flapping) và các ca biên đã gặp, để số trong luận văn không đổi lặng lẽ khi sửa code.
"""

from __future__ import annotations

import math

import pytest

from analysis import metrics as m


def req(t, ttft=0.2, tpot=0.05, n_out=256, error="", i=0) -> m.Request:
    """Request thành công gửi đúng lịch lúc t, với TTFT và TPOT cho trước."""
    if error and ttft is None:
        return m.Request(i, t, t, None, None, None, error)
    first = t + ttft
    return m.Request(i, t, t, first, first + tpot * (n_out - 1), n_out, error)


# ── Request ──


def test_parse_request_converts_to_unix_and_keeps_empty_fields():
    row = {
        "id": "3",
        "t_sched": "1.5",
        "t_send": "1.6",
        "t_first": "",
        "t_last": "",
        "n_out": "",
        "error": "Timeout",
    }
    r = m.parse_request(row, t0_unix=1000.0)
    assert (r.id, r.t_first, r.n_out, r.error) == (3, None, None, "Timeout")
    assert (r.t_sched, r.t_send) == pytest.approx((1001.5, 1001.6))
    assert r.ttft is None and r.tpot is None and not r.good


def test_good_needs_no_error_and_both_slos():
    assert req(0).good
    assert req(0, ttft=2.5).good  # ≤ 2,5 s: đúng biên bucket le="2.5"
    assert not req(0, ttft=2.51).good
    assert not req(0, tpot=0.11).good
    assert not req(0, error="IncompleteStream").good  # có token nhưng stream bị cắt: vẫn là lỗi
    assert not req(0, n_out=1).good  # n_out < 2: không tính được TPOT


def test_tpot_divides_by_n_out_minus_one():
    r = req(0, ttft=1.0, tpot=0.04, n_out=11)
    assert r.tpot == pytest.approx(0.04)
    assert r.ttft == pytest.approx(1.0)


# ── Phân vị và thống kê pha ──


def test_quantile_matches_capacity_formula():
    vals = list(range(1, 21))  # 1..20
    assert m.quantile(vals, 0.95) == 19  # phần tử thứ round(0,95 × 19) = 18 (đếm từ 0)
    assert m.quantile(vals, 0.5) == 11
    assert math.isnan(m.quantile([], 0.95))


def test_phase_stats_counts_errors_in_denominator_and_hides_small_p99():
    reqs = [req(t) for t in range(10)] + [req(10, ttft=None, error="Timeout"), req(11, ttft=3.0)]
    s = m.phase_stats(reqs, 0, 12)
    assert s["n_sent"] == 12 and s["n_error"] == 1
    assert s["error_types"] == "Timeout=1"
    assert s["slo_attainment"] == pytest.approx(10 / 12)  # Timeout và TTFT 3 s đều không đạt
    assert math.isnan(s["ttft_p99_s"])  # < 200 request
    assert s["tokens_out"] == 11 * 256
    assert s["throughput_tok_s"] == pytest.approx(11 * 256 / 12)


def test_phase_stats_window_is_half_open_by_schedule():
    reqs = [req(t) for t in (0, 5, 10)]
    assert m.phase_stats(reqs, 0, 10)["n_sent"] == 2  # [0, 10): request lúc 10 thuộc pha sau


def test_phase_stats_reports_p99_with_enough_samples():
    s = m.phase_stats([req(t * 0.1) for t in range(250)], 0, 30)
    assert s["ttft_p99_s"] == pytest.approx(0.2)


# ── N2b: hồi phục SLO ──


def _bad_until(t_bad_end: float, n: int = 400) -> list[m.Request]:
    """Mỗi giây một request lúc x,5; TTFT 5 s (xấu) trước t_bad_end, 0,2 s sau đó."""
    return [req(t + 0.5, ttft=5.0 if t + 0.5 < t_bad_end else 0.2) for t in range(n)]


def test_recovery_waits_for_window_to_clear_and_hold():
    # Request xấu cuối cùng lúc 99,5. Cửa sổ 30 request chịu được 1 request xấu ở p95, nên τ = 129 là mốc
    # đầu tiên (cửa sổ (99, 129] chỉ còn 99,5 xấu); τ = 128 còn 98,5 và 99,5. Giữ tới 189 ≤ t_end.
    assert m.slo_recovery_s(_bad_until(100), t_rise=0, t_end=300) == pytest.approx(129)


def test_recovery_zero_when_never_violated_and_none_when_not_recovered():
    assert m.slo_recovery_s(_bad_until(0), t_rise=0, t_end=300) == 0
    assert m.slo_recovery_s(_bad_until(1000), t_rise=0, t_end=300) is None
    # Hồi phục ở 129 nhưng pha hết trước khi giữ đủ 60 s
    assert m.slo_recovery_s(_bad_until(100), t_rise=0, t_end=150) is None


def test_recovery_starts_from_first_violation():
    # Hàng đợi dồn dần: 70 s đầu sau t_rise vẫn đạt, rồi xấu tới 299,5. Tìm từ t_rise thì ra 0 (sai).
    reqs = [req(t + 0.5, ttft=5.0 if 70 <= t + 0.5 < 300 else 0.2) for t in range(600)]
    assert m.slo_recovery_s(reqs, t_rise=0, t_end=600) == pytest.approx(329)


def _bad_pairs(starts, n: int = 600) -> list[m.Request]:
    """Mỗi giây một request lúc x,5; TTFT 5 s ở hai request liền nhau bắt đầu từ mỗi mốc trong `starts`.
    Cửa sổ 30 request chịu được 1 request xấu, nên mỗi cặp làm p95 vi phạm đúng 29 điểm lưới."""
    bad = {s + k for s in starts for k in (0.5, 1.5)}
    return [req(t + 0.5, ttft=5.0 if t + 0.5 in bad else 0.2) for t in range(n)]


def test_recovery_ignores_short_blip_before_real_violation():
    # Cặp request chậm lúc 40,5–41,5 (vi phạm 29 s), đạt hơn 60 s, rồi quá tải thật 150,5–249,5. Tìm từ điểm
    # xấu đầu tiên thì ra 71 (sau cặp chậm); đúng là 279 (cửa sổ (249, 279] chỉ còn 249,5 xấu).
    reqs = [r if not (150 <= r.t_sched < 250) else req(r.t_sched, ttft=5.0) for r in _bad_pairs([40])]
    assert m.slo_recovery_s(reqs, t_rise=0, t_end=400) == pytest.approx(279)


def test_recovery_counts_total_not_consecutive_violation():
    # p95 dao động quanh ngưỡng: mỗi 31 s một cặp chậm → xấu 29 điểm, đạt 2 điểm, lặp lại. Không đợt nào đủ
    # 30 s liên tục, nhưng đó vẫn là quá tải: phải ra "không hồi phục", không phải 0.
    assert m.slo_recovery_s(_bad_pairs(range(40, 330, 31)), t_rise=0, t_end=300) is None
    # Cặp cuối lúc 164,5–165,5: cửa sổ (165, 195] chỉ còn một request xấu → hồi phục ở 195
    assert m.slo_recovery_s(_bad_pairs(range(40, 165, 31)), t_rise=0, t_end=300) == pytest.approx(195)


def test_recovery_counts_errors_as_infinite_ttft():
    reqs = [req(t + 0.5) if t >= 100 else req(t + 0.5, ttft=None, error="Timeout") for t in range(400)]
    assert m.slo_recovery_s(reqs, t_rise=0, t_end=300) == pytest.approx(129)


# ── N7: vi phạm SLO, page giả ──


def test_violation_start_uses_full_one_minute_window():
    # Xấu từ 100,5. Ở τ = 113, cửa sổ (53, 113] có 60 request, 13 xấu = 21,7 % > 20 %; ở τ = 112 đúng 20 %.
    reqs = [req(t + 0.5, ttft=0.2 if t + 0.5 < 100 else 5.0) for t in range(300)]
    assert m.slo_violation_start(reqs, 0, 300) == pytest.approx(113)
    # Xấu ngay từ đầu: chỉ chấm khi cửa sổ đã đủ 60 s
    assert m.slo_violation_start([req(t + 0.5, ttft=5.0) for t in range(300)], 0, 300) == pytest.approx(60)
    assert m.slo_violation_start([req(t + 0.5) for t in range(300)], 0, 300) is None


def test_classify_alerts_judges_each_episode():
    # Cùng một chuỗi: kêu đúng lúc quá tải (330 s), tắt, kêu lại lúc 1300 s khi không còn request xấu
    reqs = [req(t + 0.5, ttft=5.0 if 100 <= t < 400 else 0.2) for t in range(1500)]
    a = {"labels": {"alertname": "LLMSLOBurnFast", "severity": "page"}, "first": 330, "last": 1310}
    a["episodes"] = [[330, 400], [1300, 1310]]
    rows = m.classify_alerts([a], reqs)
    assert [(r["first"], r["false_page"]) for r in rows] == [(330, False), (1300, True)]


def test_classify_alerts_false_page_rule():
    reqs = [req(t + 0.5, ttft=5.0 if t >= 100 else 0.2) for t in range(400)]
    alerts = [
        {"labels": {"alertname": "LLMSLOBurnFast", "severity": "page"}, "first": 350, "last": 380},
        {"labels": {"alertname": "LLMSLOBurnFast", "severity": "page"}, "first": 90, "last": 95},
        {"labels": {"alertname": "LLMAtMaxReplicas", "severity": "ticket"}, "first": 90, "last": 95},
        {"labels": {"alertname": "LLMPodNotReady", "severity": "page"}, "first": 2000, "last": 2010},
    ]
    rows = m.classify_alerts(alerts, reqs)
    assert [r["false_page"] for r in rows] == [False, True, False, True]
    assert rows[0]["client_bad_ratio"] == pytest.approx(250 / 300)  # [50, 350): 50,5…349,5, xấu từ 100,5
    assert rows[1]["client_bad_ratio"] == pytest.approx(0.0)
    assert math.isnan(rows[3]["client_bad_ratio"])  # không có request nào trong 5 phút trước


# ── Khớp với runner ──


def test_constants_and_quantile_match_runner():
    # analysis chép tay ngưỡng SLO và công thức phân vị của capacity.py (chỗ tính C): lệch là số không còn
    # so được với ĐG1. Runner chỉ dùng thư viện chuẩn nên import được từ môi trường của analysis.
    from experiments.runner import capacity, collect

    from analysis import build_tables

    assert (m.TTFT_SLO_S, m.TPOT_SLO_S, m.ATTAINMENT) == (
        capacity.TTFT_SLO_S,
        capacity.TPOT_SLO_S,
        capacity.ATTAINMENT,
    )
    assert m.STEP_S == build_tables.STEP_S == collect.STEP_S
    for vals in ([3.0], [2.0, 1.0], [float(x) for x in range(37)]):
        for p in (0.5, 0.95, 0.99):
            assert m.quantile(vals, p) == capacity._q(vals, p)


# ── GPU-giờ ──


def test_gpu_seconds_clips_to_window_and_skips_unscheduled():
    pods = [
        {"marks": {"scheduled": 0.0}, "gone_at": None},  # có từ trước lượt, còn sống: cả cửa sổ
        {"marks": {"scheduled": 150.0}, "gone_at": 250.0},  # scale-up rồi bị xoá giữa lượt
        {"marks": {"scheduled": 280.0}, "gone_at": 500.0},  # sống quá mép cuối: cắt ở 300
        {"marks": {"scheduled": None}, "gone_at": 200.0},  # Pending vì hết GPU: không giữ GPU
    ]
    assert m.gpu_seconds(pods, 100.0, 300.0) == pytest.approx(200 + 100 + 20)


def test_integrate_steps_clips_partial_steps():
    samples = [(0.0, 1.0), (5.0, 2.0), (10.0, 3.0)]
    assert m.integrate_steps(samples, 2.0, 12.0, 5.0) == pytest.approx(1 * 3 + 2 * 5 + 3 * 2)


def test_integrate_steps_carries_value_over_gaps():
    # kube-state-metrics khởi động lại: mất mẫu 10–25 s. 2 replica suốt 30 s, không phải 2 × 15 s.
    samples = [(0.0, 2.0), (5.0, 2.0), (25.0, 2.0)]
    assert m.integrate_steps(samples, 0.0, 30.0, 5.0) == pytest.approx(60)


# ── Autoscaling ──


def test_scale_changes_and_flaps():
    samples = [(0, 1), (5, 1), (10, 3), (15, 3), (700, 2), (760, 1), (800, 2)]
    ch = m.scale_changes(samples)
    assert ch == [(10, 1, 3), (700, 3, 2), (760, 2, 1), (800, 1, 2)]
    # 3→2 cách 1→3 tới 690 s: bình thường. 1→2 lúc 800, 40 s sau 2→1: một lần đổi chiều trong 5 phút.
    assert m.count_flaps(ch) == 1


def test_reaction_splits_detection_and_create_to_ready():
    pods = [
        {"name": "old", "marks": {"created": 0.0, "ready": 10.0}},
        {"name": "new-a", "marks": {"created": 260.0, "ready": 340.0}},
        {"name": "new-b", "marks": {"created": 265.0, "ready": 330.0}},  # Ready trước dù tạo sau
        {"name": "early", "marks": {"created": 100.0, "ready": 160.0}},  # tạo trước khi tải tăng: bỏ
    ]
    r = m.reaction(pods, {"old"}, t_rise=240.0)
    # create_to_ready = react − detect để hai phần cộng lại đúng N2a. Pod tạo sau nhưng Ready trước vẫn tính,
    # nên 70 s ở đây không phải cold start của pod nào (cold start từng pod lấy từ pods_timeline và log).
    assert r == {"detect_s": 20.0, "create_to_ready_s": 70.0, "react_s": 90.0}
    none = {"detect_s": None, "create_to_ready_s": None, "react_s": None}
    assert m.reaction(pods[:1], {"old"}, 240.0) == none
