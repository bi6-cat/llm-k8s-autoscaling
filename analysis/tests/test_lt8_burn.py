"""Test cho analysis/lt8_burn.py (LT8, Môi trường §19).

Khái niệm: Ngoài các hàm thuần, test dựng một lượt TỔNG HỢP runs/sim/lt8-<giờ>/rep1/ đúng định dạng mà
    experiments/ops/lt8_burn.py ghi, bằng cách mô phỏng lại cơ chế của Prometheus: request đều 2 req/s, bộ đếm
    histogram TTFT được scrape mỗi 5 s, recording rule tính tỷ lệ xấu trên cửa sổ 1m và 5m mỗi 15 s, nhóm
    cảnh báo tính mỗi 15 s (lệch pha 5 s) với `for: 1m`. Mốc của loadgen ghi theo đồng hồ chạy nhanh k lần.
Mục đích: Kiểm cách đọc mốc và cách đổi đồng hồ, đồng thời kiểm rằng các công thức dự đoán (θ·300/x + 60 s
    cho firing, θ·240/x + 60 s cho thời gian tới cảnh báo của N7) vẫn đúng khi có rời rạc hoá (scrape, chu
    kỳ tính rule), chỉ cộng thêm một khoảng trễ nhỏ và bị chặn.
"""

from __future__ import annotations

import csv
import json
import math
from pathlib import Path

import pytest

from analysis import lt8_burn as lt
from analysis import metrics as m

T0 = 1_794_830_000.0  # giờ thực lúc loadgen bắt đầu
K = 1.03  # đồng hồ đơn điệu của loadgen chạy nhanh 3 % (như WSL2)
SLOW_TTFT, FAST_TTFT = 3.0, 0.2  # giây, theo đồng hồ của simulator
DECODE_S = 0.75  # 16 token: 15 khoảng × 50 ms


def test_bad_fraction_matches_normal_tail_and_clipping():
    assert lt.bad_fraction(2.5, 0.75) == pytest.approx(0.5)
    # Các cặp (μ, σ) mà bộ đo chọn cho x = 0,1 / 0,3 / 0,6 (σ = ⌊0,3 μ⌋ ms)
    assert lt.bad_fraction(1.806, 0.541) == pytest.approx(0.10, abs=0.002)
    assert lt.bad_fraction(2.160, 0.648) == pytest.approx(0.30, abs=0.002)
    assert lt.bad_fraction(2.706, 0.811) == pytest.approx(0.60, abs=0.002)
    assert lt.bad_fraction(0.2, 0) == 0.0  # độ trễ nền: không request nào xấu
    assert lt.bad_fraction(1.4, 0.42) == 0.0  # 1,7 μ = 2,38 < 2,5: mọi mẫu bị cắt dưới ngưỡng
    assert lt.bad_fraction(9.0, 2.7) == 1.0  # 0,3 μ = 2,7 > 2,5


def test_predict_long_window_binds_on_the_way_up_short_window_on_the_way_down():
    p = lt.predict(0.3)
    assert p == pytest.approx({"cond_s": 200, "fire_s": 260, "clear_s": 20, "viol_s": 40, "detect_s": 220})
    assert lt.predict(0.6)["fire_s"] == pytest.approx(160)
    assert lt.predict(0.2) == dict.fromkeys(p)  # cần > 20 %, không phải ≥
    assert lt.predict(0.1)["fire_s"] is None


def test_n7_detection_time_stays_under_five_minutes_only_just():
    # θ·240/x + 60 < 300 với mọi x > θ, và tiến tới 300 khi x → θ: mức 5 phút của N7 vừa khít cửa sổ 5m
    assert lt.predict(0.2001)["detect_s"] == pytest.approx(300, abs=0.5)
    assert all(lt.predict(x)["detect_s"] < 300 for x in (0.21, 0.3, 0.6, 1.0))


def test_shift_keeps_ttft_and_moves_request_to_wall_clock():
    row = {"id": "1", "t_sched": f"{100 * K}", "t_send": f"{100 * K}", "t_first": f"{100 * K + 2.55}",
           "t_last": f"{100 * K + 3.3}", "n_out": "16", "error": ""}  # fmt: skip
    r = lt.shift_to_wall(m.parse_request(row, T0), T0, K)
    assert r.t_sched == pytest.approx(T0 + 100)  # 100 s thực sau t0
    assert r.ttft == pytest.approx(2.55)  # giữ theo đồng hồ simulator: vẫn xấu (co theo k thì 2,48 s, tốt)
    assert not r.good


def test_counter_increase_refuses_reset_and_missing_start():
    smp = [(0.0, 10.0), (5.0, 12.0), (10.0, 15.0), (15.0, 15.0)]
    assert lt.counter_increase(smp, 4.0, 12.0) == 5.0  # mẫu cuối ≤ 4 là 10, mẫu cuối ≤ 12 là 15
    assert lt.counter_increase(smp, -1.0, 12.0) is None  # chưa có mẫu ở đầu khoảng
    assert lt.counter_increase([(0.0, 10.0), (5.0, 2.0), (10.0, 4.0)], 0.0, 10.0) is None  # pod restart


def test_episodes_split_when_one_evaluation_is_missing():
    assert lt.episodes([0, 15, 30, 90, 105]) == [(0, 30), (90, 105)]
    assert lt.episodes([0, 15, 45, 60]) == [(0, 15), (45, 60)]  # một lần tính sai ở giữa = hai đợt
    assert lt.episodes([0, 14.6, 30.4]) == [(0, 30.4)]  # chu kỳ lệch chút vì đồng hồ WSL
    assert lt.episodes([]) == []


def test_go_duration_and_applied_latency_check():
    assert lt.go_duration_ms("1.806s") == pytest.approx(1806)
    assert lt.go_duration_ms("541ms") == 541 and lt.go_duration_ms("0s") == 0
    assert lt.go_duration_ms("1m2s") is None and lt.go_duration_ms("ms") is None
    ok = {"pods": [{"pod": "a", "ttft": "2.16s", "sd": "648ms"}]}
    assert lt.applied_mismatch(ok, 2160, 648) == ""
    assert lt.applied_mismatch(ok, 2706, 811) == "a"
    assert lt.applied_mismatch({"pods": []}, 2160, 648) == "không pod nào nhận"
    assert lt.applied_mismatch({}, 2160, 648) == "không pod nào nhận"


def _pod(mu_ms: int, sd_ms: int) -> dict:
    """Mục `pods` của mốc inject/recover, theo dạng simulator trả về (time.Duration.String() của Go)."""
    return {
        "pod": "vllm-0",
        "ttft": f"{mu_ms / 1000}s" if mu_ms >= 1000 else f"{mu_ms}ms",
        "sd": f"{sd_ms}ms",
    }


def _simulate(tmp: Path, every: int, t_inj: float = 400.0, inj_s: float = 360.0, end: float = 1000.0) -> Path:
    """Dựng rep1/ cho một lần bơm: trong [t_inj, t_inj + inj_s), cứ `every` request thì một request xấu."""
    d = tmp / "lt8-test" / "rep1"
    (d / "load").mkdir(parents=True)
    reqs = []  # (gửi, quan sát, xấu), giờ thực tính từ T0
    for i in range(int(end * 2)):
        t = i * 0.5
        bad = t_inj <= t < t_inj + inj_s and i % every == 0
        reqs.append((t, bad))
    with (d / "load" / "requests.csv").open("w", newline="", encoding="utf-8") as fh:
        w = csv.writer(fh)
        w.writerow(["id", "t_sched", "t_send", "t_first", "t_last", "n_out", "error"])
        for i, (t, bad) in enumerate(reqs):  # mốc theo đồng hồ loadgen (×k); TTFT theo đồng hồ simulator
            ttft = SLOW_TTFT if bad else FAST_TTFT
            w.writerow([i, t * K, t * K, t * K + ttft, t * K + ttft + DECODE_S, 16, ""])
    (d / "load" / "loadgen.json").write_text(json.dumps({"t0_unix": T0, "checks": {"valid": True}}))

    obs = [(T0 + t + (SLOW_TTFT if b else FAST_TTFT) / K, b) for t, b in reqs]  # lúc server có token đầu
    scrapes = [T0 - 60 + 5 * j for j in range(int((end + 120) / 5))]
    count = [(s, float(sum(1 for o, _ in obs if o <= s))) for s in scrapes]
    good = [(s, float(sum(1 for o, b in obs if o <= s and not b))) for s in scrapes]

    def ratio(e: float, w: float) -> float:
        win = [j for j, s in enumerate(scrapes) if e - w <= s <= e]  # rate() chỉ dùng mẫu trong cửa sổ
        dc = count[win[-1]][1] - count[win[0]][1]
        dg = good[win[-1]][1] - good[win[0]][1]
        return (dc - dg) / dc if dc else math.nan

    evals = [T0 + 2 + 15 * j for j in range(int(end / 15))]
    r1 = [(e, ratio(e, 60)) for e in evals]
    r5 = [(e, ratio(e, 300)) for e in evals]
    pending, firing, active = [], [], None
    for a in (T0 + 7 + 15 * j for j in range(int(end / 15))):  # nhóm cảnh báo lệch pha 5 s
        if lt.both_above(r1, r5, a):
            active = a if active is None else active
            (firing if a - active >= 60 else pending).append(a)
        else:
            active = None

    def series(values: list[tuple[float, float]], **labels: str) -> dict:
        return {"metric": labels, "values": [[t, str(v)] for t, v in values]}

    prom = {
        "alerts": [series([(t, 1) for t in pending], alertstate="pending")]
        + [series([(t, 1) for t in firing], alertstate="firing")],
        "r1": [series(r1)],
        "r5": [series(r5)],
        "count": [series(count)],
        "good": [series(good)],
    }
    (d / "prom.json").write_text(json.dumps(prom))
    x = 1 / every
    mu, sd = (2706, 811) if x > 0.2 else (1806, 541)  # chỉ để ghi vào bảng; x_pred tính từ đây
    timeline = [
        {"event": "load_submitted", "wall": T0 - 5},
        {"event": "traffic_seen", "wall": T0 + 3},
        {"event": "inject", "wall": T0 + t_inj, "x": x, "mu_ms": mu, "sd_ms": sd, "pods": [_pod(mu, sd)]},
        {"event": "recover", "wall": T0 + t_inj + inj_s, "x": x, "pods": [_pod(200, 0)]},
        {"event": "load_done", "wall": T0 + end},
    ]
    (d / "timeline.json").write_text(json.dumps(timeline))
    meta = {"rep": 1, "k_mono_per_wall": K, "restarts": 0, "load": {"rc": 0}}
    (d / "meta.json").write_text(json.dumps(meta))
    return d


def test_step_of_half_bad_requests_fires_where_the_formula_says(tmp_path):
    [row] = lt.analyze_rep(_simulate(tmp_path, every=2))  # x = 0,5 → điều kiện 120 s, firing 180 s, hết 36 s
    assert row["valid"], row["note"]
    assert row["warm_s"] == pytest.approx(400)
    assert row["x_client"] == pytest.approx(0.5, abs=0.005)
    assert row["x_server"] == pytest.approx(0.5, abs=0.01)
    # Trễ cộng thêm bị chặn: token đầu 3 s + chờ scrape < 5 s + một chu kỳ tính < 15 s
    assert 120 <= row["cond_s"] <= 120 + 3 + 5 + 15
    assert 0 <= row["cond_to_pending_s"] < 15
    assert row["pending_to_fire_s"] == pytest.approx(60)
    assert 0 <= row["fire_s"] - 180 <= 3 + 5 + 15 + 15
    assert 36 - 5 <= row["clear_s"] <= 36 + 3 + 5 + 15
    assert row["last_fire_s"] < row["clear_s"]  # mẫu firing cuối có trước lần tính thấy điều kiện sai
    # N7: log client thấy vi phạm (cửa sổ 1 phút > 20 %) sau θ·60/x = 24 s; cảnh báo kêu sau đó 156 s + trễ
    assert row["viol_s"] == pytest.approx(24, abs=1)
    assert 156 <= row["detect_s"] <= 156 + 3 + 5 + 15 + 15 + 1
    assert row["false_page"] == 0 and row["pending_only"] == 0


def test_ten_percent_bad_never_pages(tmp_path):
    [row] = lt.analyze_rep(_simulate(tmp_path, every=10))
    assert row["cond_s"] is None and row["pending_s"] is None and row["fire_s"] is None
    assert row["clear_s"] is None and row["false_page"] == 0
    assert row["x_client"] == pytest.approx(0.1, abs=0.005)
    assert row["viol_s"] is None  # đều đặn 1/10 thì cửa sổ 1 phút cũng không vượt 20 %


def test_missing_rules_or_unapplied_latency_is_invalid_not_silent(tmp_path):
    d = _simulate(tmp_path, every=2)
    prom = json.loads((d / "prom.json").read_text())
    prom["r5"] = []
    (d / "prom.json").write_text(json.dumps(prom))
    tl = json.loads((d / "timeline.json").read_text())
    tl[2]["pods"] = []  # lúc bơm không có pod Ready nào
    (d / "timeline.json").write_text(json.dumps(tl))
    [row] = lt.analyze_rep(d)
    assert not row["valid"]
    assert (
        "thiếu mẫu recording rule" in row["note"]
        and "bơm không đúng độ trễ: không pod nào nhận" in row["note"]
    )


def test_skipped_evaluation_does_not_split_firing(tmp_path):
    d = _simulate(tmp_path, every=2)
    prom = json.loads((d / "prom.json").read_text())
    firing = prom["alerts"][1]["values"]
    del firing[len(firing) // 2]  # một lần tính bị bỏ giữa đợt firing: hở 30 s
    (d / "prom.json").write_text(json.dumps(prom))
    [row] = lt.analyze_rep(d)
    assert row["valid"], row["note"]
    assert row["pending_only"] == 0 and row["false_page"] == 0


def test_short_warm_up_is_flagged(tmp_path):
    [row] = lt.analyze_rep(_simulate(tmp_path, every=2, t_inj=200))  # chỉ 200 s nền: cửa sổ 5m chưa đầy
    assert not row["valid"] and "nền trước lần bơm chỉ 200 s" in row["note"]


def test_main_writes_csv_and_summary(tmp_path, capsys):
    d = _simulate(tmp_path, every=2)
    out = tmp_path / "lt8.csv"
    assert lt.main([str(d.parent), "--out", str(out)]) == 0
    with out.open(encoding="utf-8") as fh:
        rows = list(csv.DictReader(fh))
    assert len(rows) == 1 and rows[0]["x_target"] == "0.5" and rows[0]["valid"] == "True"
    text = capsys.readouterr().out
    assert "1/1 lần bơm hợp lệ" in text and "| 0.5 |" in text


def test_rep_without_load_files_is_skipped_not_fatal(tmp_path, capsys):
    good = _simulate(tmp_path, every=2)
    bad = good.parent / "rep2"
    bad.mkdir()
    (bad / "meta.json").write_text(json.dumps({"rep": 2, "load": {"error": "RuntimeError: pod Failed"}}))
    assert lt.main([str(good.parent)]) == 0
    assert "Bỏ rep2: thiếu load/loadgen.json, load/requests.csv" in capsys.readouterr().out
