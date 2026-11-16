"""LT8: kiểm chứng cảnh báo burn rate (LLMSLOBurnFast) trên simulator (Môi trường §19, Kiến thức nền §5.2).

Khái niệm:
    SLI của cảnh báo là r_w(t) = tỷ lệ request có TTFT > 2,5 s trong cửa sổ w kết thúc ở t, tính từ histogram
    TTFT (recording rule llm:ttft_bad_ratio:rate1m và :rate5m, common/observability/rules/slo.yaml).
    LLMSLOBurnFast chuyển sang pending ở lần tính đầu tiên có r_5m > θ VÀ r_1m > θ, với θ = 4 × 5 % = 0,2
    (burn rate 4 của SLO 95 %); đúng liên tục suốt `for` = 60 s thì sang firing; sai ở một lần tính bất kỳ
    thì hết ngay (common/observability/alerts/llm.yaml).
    Dự đoán cho một bước nhảy: λ không đổi, mọi request trước t_inj đều tốt (ít nhất 5 phút), từ t_inj tỷ lệ
    xấu là x. Khi đó
        r_w(t_inj + τ) = x · min(τ, w) / w,
    nên cửa sổ w vượt θ sau τ_w = θ·w/x, và chỉ khi x > θ. Điều kiện cần cả hai cửa sổ, nên đúng từ
        τ_cond = θ · 300 / x        (cửa sổ dài là chặng chậm; cửa sổ 1m đã vượt từ θ · 60 / x)
        τ_fire = τ_cond + 60 s      (`for`)
    x ≤ θ: r_5m tiến tới x ≤ θ và không bao giờ vượt, nên cảnh báo im lặng dù lỗi kéo dài bao lâu.
    Gỡ lỗi ở t_rec: r_w(t_rec + τ) = x · (w − τ) / w. Điều kiện sai ngay khi MỘT cửa sổ xuống dưới θ, tức
    cửa sổ ngắn: τ_clear = 60 · (1 − θ/x). Đây là vai trò của cửa sổ ngắn: nếu chỉ có cửa sổ 5m, cảnh báo
    còn kêu tới 300 · (1 − θ/x).
    N7 (VH6) đo "thời gian tới cảnh báo" từ lúc SLO bị vi phạm thật theo log client, tức lúc tỷ lệ xấu trên
    cửa sổ 1 phút vượt θ (metrics.slo_violation_start): τ_viol = θ · 60 / x. Vậy
        τ_detect = τ_fire − τ_viol = θ · 240 / x + 60 s,
    luôn dưới 300 s khi x > θ và tiến tới 300 s khi x → θ. Nghĩa là mức 5 phút của N7 vừa khít với cửa sổ
    5m: cộng các trễ bên dưới thì N7 chỉ giữ được khi x lớn hơn θ một khoảng.
    x tính trước từ độ trễ đã bơm. Simulator v0.12.0 lấy TTFT ~ N(μ, σ) rồi cắt vào [0,3 μ; 1,7 μ], nên
        x = P(TTFT > 2,5 s) = ½ · erfc((2,5 − μ) / (σ √2))    khi 0,3 μ < 2,5 < 1,7 μ.
    Các trễ cộng thêm không có trong công thức (tổng dự kiến dưới khoảng 30 s): request xấu chỉ được đếm khi
    có token đầu (khoảng μ, 2–3 s, sau khi gửi); chờ lần scrape kế tiếp (5 s); recording rule và alerting
    rule ở hai nhóm tính riêng, mỗi nhóm 15 s, nên pending muộn hơn lúc điều kiện đúng tới 15 s, và mọi mốc
    đo chỉ chính xác tới 15 s.
    Nhiễu: ở 2 req/s, mỗi cửa sổ 5m có khoảng 600 request, nên độ lệch chuẩn của r_5m quanh θ là
    √(θ(1 − θ)/600) ≈ 0,016. r_5m tăng x/300 mỗi giây, nên lúc vượt θ có thể xê dịch cỡ 0,016 · 300 / x
    giây (khoảng 16 s ở x = 0,3, 8 s ở x = 0,6). Một lần tụt dưới θ trong `for` thì pending bị đặt lại
    (cột pending_only).
Mục đích: Đọc runs/sim/lt8-<giờ>/rep<r>/ (do experiments/ops/lt8_burn.py ghi). Mỗi lần bơm một dòng CSV: x
    dự đoán và x đo (theo log client và theo histogram của server); mốc điều kiện đúng, pending, firing, hết,
    so với dự đoán; thời gian tới cảnh báo và page giả theo đúng định nghĩa N7 mà build_tables dùng cho
    chương 5 (metrics.slo_violation_start, metrics.classify_alerts), để số của LT8 so được với VH6.
Đồng hồ: mốc bơm và gỡ (bộ đo) và mẫu Prometheus đều theo giờ thực của cùng một VM. Sai lệch dưới 1 s do WSL
    kéo giờ lùi theo Windows: bỏ qua, vì nhỏ hơn nhiều so với chu kỳ tính rule 15 s. requests.csv ghi theo
    perf_counter, là đồng hồ đơn điệu, mà trên WSL2 đồng hồ này chạy nhanh k lần so với giờ thực (k đo trong
    chính lượt đó, meta.json). Mỗi request được DỜI nguyên khối sang giờ thực (shift_to_wall), không co theo
    k như lt5_little.to_wall: vị trí trên trục thời gian đúng, còn TTFT và TPOT giữ theo đồng hồ của
    simulator. Simulator ngủ và đo TTFT theo chính đồng hồ đơn điệu đó, nên chỉ khi giữ nguyên thì việc so
    TTFT của client với 2,5 s mới cùng thước với histogram của server (co theo k = 1,024 thì ở x = 0,3
    khoảng 3 % request đổi phía ngưỡng).

Chạy (từ gốc repo):
    uv run --project analysis python -m analysis.lt8_burn runs/sim/lt8-<giờ> \\
        [--out analysis/figures/lt8-burn.csv]
"""

from __future__ import annotations

import argparse
import bisect
import csv
import math
from collections.abc import Mapping, Sequence
from dataclasses import replace
from pathlib import Path
from typing import Any

from analysis import metrics as m
from analysis.build_tables import _json, write_csv

NAN = float("nan")
THETA = m.BAD_RATIO_PAGE  # 0,2: ngưỡng của LLMSLOBurnFast, cũng là ngưỡng page giả của N7
LONG_W, SHORT_W = m.PAGE_WINDOW_S, m.VIOLATION_WINDOW_S  # cửa sổ rate5m và rate1m, giây
FOR_S = 60.0
# Hai mẫu ALERTS liền nhau của một đợt cách 15 s (chu kỳ tính rule). Một lần tính sai ở giữa làm hở 30 s,
# nên ngưỡng tách đợt phải nằm giữa hai số đó.
MAX_GAP_S = 22.5
GUARD_S = 5.0  # bỏ request gửi trong 5 s đầu sau lúc bơm: POST mất khoảng 0,3 s, đổi mốc loadgen sai < 1 s

COLUMNS = (
    "rep", "order", "x_target", "mu_ms", "sd_ms", "warm_s", "inject_s", "x_pred", "n_client", "x_client",
    "x_server", "cond_pred_s", "cond_s", "pending_s", "fire_pred_s", "fire_s", "fire_lag_s",
    "cond_to_pending_s", "pending_to_fire_s", "clear_pred_s", "clear_s", "last_fire_s", "viol_pred_s",
    "viol_s", "detect_pred_s", "detect_s", "pending_only", "false_page", "valid", "note",
)  # fmt: skip


def bad_fraction(mu_s: float, sd_s: float, slo_s: float = m.TTFT_SLO_S) -> float:
    """P(TTFT > slo) với TTFT ~ N(μ, σ) cắt vào [0,3 μ; 1,7 μ] (cách simulator lấy mẫu). Hàm thuần."""
    if slo_s >= 1.7 * mu_s:
        return 0.0  # mọi mẫu ≤ 1,7 μ ≤ ngưỡng
    if slo_s < 0.3 * mu_s:
        return 1.0  # mọi mẫu ≥ 0,3 μ > ngưỡng
    if sd_s <= 0:
        return 1.0 if mu_s > slo_s else 0.0
    return 0.5 * math.erfc((slo_s - mu_s) / (sd_s * math.sqrt(2)))


def predict(
    x: float, theta: float = THETA, long_w: float = LONG_W, short_w: float = SHORT_W, for_s: float = FOR_S
) -> dict[str, float | None]:
    """Mốc dự đoán (giây): cond, fire, viol tính từ lúc bơm; clear từ lúc gỡ; detect = fire − viol (N7).
    x ≤ θ: cảnh báo không kêu và log client không thấy vi phạm, mọi mốc None."""
    if x <= theta:
        return dict.fromkeys(("cond_s", "fire_s", "clear_s", "viol_s", "detect_s"))
    cond, viol = theta * long_w / x, theta * short_w / x
    return {
        "cond_s": cond,
        "fire_s": cond + for_s,
        "clear_s": short_w * (1 - theta / x),
        "viol_s": viol,
        "detect_s": cond + for_s - viol,
    }


def shift_to_wall(r: m.Request, t0: float, k: float) -> m.Request:
    """Dời cả request sang giờ thực theo mốc lịch gửi: t_thực = t0 + (t − t0) / k cho t_sched, rồi cộng cùng
    độ dời cho mọi mốc khác, nên TTFT và TPOT giữ nguyên theo đồng hồ của simulator (xem "Đồng hồ")."""
    d = (r.t_sched - t0) / k - (r.t_sched - t0)

    def f(t: float | None) -> float | None:
        return None if t is None else t + d

    return replace(r, t_sched=r.t_sched + d, t_send=f(r.t_send), t_first=f(r.t_first), t_last=f(r.t_last))


def samples(series: Sequence[Mapping[str, Any]], **labels: str) -> list[tuple[float, float]]:
    """Mẫu thô của các chuỗi có đủ các nhãn đã cho, sắp theo thời gian. Giá trị "NaN" giữ là NaN."""
    out = []
    for s in series:
        if all(s["metric"].get(k) == v for k, v in labels.items()):
            out += [(float(t), float(v)) for t, v in s["values"]]
    return sorted(out)


def value_at(smp: Sequence[tuple[float, float]], t: float) -> float:
    """Giá trị của mẫu cuối cùng ở thời điểm ≤ t (NaN nếu chưa có mẫu nào)."""
    i = bisect.bisect_right(smp, (t, math.inf)) - 1
    return smp[i][1] if i >= 0 else NAN


def counter_increase(smp: Sequence[tuple[float, float]], a: float, b: float) -> float | None:
    """Mức tăng của một bộ đếm từ mẫu cuối ≤ a tới mẫu cuối ≤ b. None nếu thiếu mẫu ở đầu, hoặc bộ đếm bị
    reset ở giữa (giá trị giảm, ví dụ pod khởi động lại): khi đó không tính được số request trong khoảng."""
    i = bisect.bisect_right(smp, (a, math.inf)) - 1
    j = bisect.bisect_right(smp, (b, math.inf)) - 1
    if i < 0 or j < i:
        return None
    vals = [v for _, v in smp[i : j + 1]]
    if any(v2 < v1 for v1, v2 in zip(vals, vals[1:], strict=False)):
        return None
    return vals[-1] - vals[0]


def episodes(times: Sequence[float], max_gap: float = MAX_GAP_S) -> list[tuple[float, float]]:
    """Gom mốc mẫu ALERTS thành các đợt liền mạch [(đầu, cuối)]. Hàm thuần."""
    out: list[tuple[float, float]] = []
    for t in sorted(times):
        if out and t - out[-1][1] <= max_gap:
            out[-1] = (out[-1][0], t)
        else:
            out.append((t, t))
    return out


def first_in(times: Sequence[float], a: float, b: float) -> float | None:
    return next((t for t in sorted(times) if a <= t < b), None)


def both_above(r1: Sequence[tuple[float, float]], r5: Sequence[tuple[float, float]], t: float) -> bool:
    """Điều kiện của LLMSLOBurnFast ở lần tính t (hai recording rule cùng nhóm nên cùng mốc). NaN → False."""
    return value_at(r5, t) > THETA and value_at(r1, t) > THETA


def _rel(t: float | None, ref: float | None) -> float | None:
    return None if t is None or ref is None else t - ref


def analyze_rep(d: Path) -> list[dict[str, Any]]:
    """Một lượt (rep<r>/) → mỗi lần bơm một dòng."""
    meta, tl, prom = _json(d / "meta.json"), _json(d / "timeline.json"), _json(d / "prom.json")
    lg = _json(d / "load" / "loadgen.json")
    t0, k = lg["t0_unix"], meta["k_mono_per_wall"]
    with (d / "load" / "requests.csv").open(encoding="utf-8", newline="") as fh:
        reqs = [shift_to_wall(m.parse_request(row, t0), t0, k) for row in csv.DictReader(fh)]
    injects = [e for e in tl if e["event"] == "inject"]
    recovers = [e for e in tl if e["event"] == "recover"]
    t_end = next(e["wall"] for e in tl if e["event"] == "load_done")
    r1, r5 = samples(prom["r1"]), samples(prom["r5"])
    firing = [t for t, _ in samples(prom["alerts"], alertstate="firing")]
    pending = [t for t, _ in samples(prom["alerts"], alertstate="pending")]
    count, good = samples(prom["count"]), samples(prom["good"])
    # Page giả theo N7, chấm từng đợt kêu như build_tables (đợt kêu từ trước t0 của loadgen thì không chấm).
    # Không có đợt nào thì không truyền: classify_alerts coi danh sách đợt rỗng là file cũ, đọc first/last.
    eps, pend_eps = episodes(firing), episodes(pending)
    alerts = [{"labels": {"alertname": "LLMSLOBurnFast", "severity": "page"}, "episodes": eps}] if eps else []
    graded = m.classify_alerts(alerts, reqs, main_start=t0)

    notes = []
    if len(prom["count"]) != 1:
        notes.append(f"{len(prom['count'])} chuỗi bộ đếm TTFT (cần đúng 1 pod)")
    if meta["load"].get("rc") != 0 or "error" in meta["load"]:
        notes.append(f"loadgen lỗi: {meta['load']}")
    if meta["restarts"]:
        notes.append(f"pod restart {meta['restarts']} lần")
    if meta.get("pod_replaced"):  # bộ đo cũ (trước 16/11 tối) không ghi khoá này
        notes.append("pod simulator bị thay giữa lượt (mất độ trễ đã bơm)")
    if not lg["checks"]["valid"]:
        notes.append("loadgen tự kiểm không đạt")
    if n_err := sum(1 for r in reqs if r.error):
        notes.append(f"{n_err} request lỗi")
    if injects and first_in(firing + pending, 0, injects[0]["wall"]) is not None:
        notes.append("có pending/firing trước lần bơm đầu")

    rows = []
    for i, (inj, rec) in enumerate(zip(injects, recovers, strict=False)):
        t_inj, t_rec = inj["wall"], rec["wall"]
        t_next = injects[i + 1]["wall"] if i + 1 < len(injects) else t_end + 30
        # Nền sạch trước lần bơm: từ lúc loadgen bắt đầu, hoặc từ lúc gỡ lần bơm trước. Dự đoán cần ≥ 5 phút.
        warm = t_inj - (recovers[i - 1]["wall"] if i else t0)
        x_pred = bad_fraction(inj["mu_ms"] / 1000, inj["sd_ms"] / 1000)
        pred = predict(x_pred)
        n = len(m.in_window(reqs, t_inj + GUARD_S, t_rec))
        x_client = m.bad_ratio(reqs, t_inj + GUARD_S, t_rec)
        # Server: request có token đầu trong [t_inj + GUARD, t_rec]. Hụt vài request xấu gửi ngay trước t_rec
        # (token đầu ra sau t_rec), nên x_server hơi thấp hơn x thật, cỡ μ / thời gian bơm (dưới 1 %).
        dc = counter_increase(count, t_inj + GUARD_S, t_rec)
        dg = counter_increase(good, t_inj + GUARD_S, t_rec)
        x_server = 1 - dg / dc if dc and dg is not None else NAN
        cond = next((t for t, _ in r5 if t_inj <= t < t_next and both_above(r1, r5, t)), None)
        pend, fire = first_in(pending, t_inj, t_next), first_in(firing, t_inj, t_next)
        n_fire = sum(1 for e in eps if t_inj <= e[0] < t_next)
        n_pend = sum(1 for e in pend_eps if t_inj <= e[0] < t_next)
        last_fire = max((t for t in firing if t_inj <= t < t_next), default=None)
        clear = None
        if cond is not None:  # lần tính đầu tiên từ lúc gỡ mà điều kiện đã sai
            clear = next((t for t, _ in r5 if t_rec <= t < t_next and not both_above(r1, r5, t)), None)
        # N7: tìm từ đúng t_inj (hàm bắt đầu ở start + 60 s, khi cửa sổ 1 phút đã đầy request nền)
        viol = m.slo_violation_start(reqs, t_inj - SHORT_W, t_next)
        row_notes = list(notes)
        if warm < LONG_W:
            row_notes.append(f"nền trước lần bơm chỉ {warm:.0f} s (< {LONG_W:.0f} s)")
        if dc is None or dg is None:
            row_notes.append("bộ đếm TTFT thiếu mẫu hoặc bị reset")
        rows.append(
            {
                "rep": meta["rep"],
                "order": i + 1,
                "x_target": inj["x"],
                "mu_ms": inj["mu_ms"],
                "sd_ms": inj["sd_ms"],
                "warm_s": warm,
                "inject_s": t_rec - t_inj,
                "x_pred": x_pred,
                "n_client": n,
                "x_client": NAN if x_client is None else x_client,
                "x_server": x_server,
                "cond_pred_s": pred["cond_s"],
                "cond_s": _rel(cond, t_inj),
                "pending_s": _rel(pend, t_inj),
                "fire_pred_s": pred["fire_s"],
                "fire_s": _rel(fire, t_inj),
                "fire_lag_s": _rel(_rel(fire, t_inj), pred["fire_s"]),
                "cond_to_pending_s": _rel(pend, cond),
                "pending_to_fire_s": _rel(fire, pend),
                "clear_pred_s": pred["clear_s"],
                "clear_s": _rel(clear, t_rec),
                "last_fire_s": _rel(last_fire, t_rec),
                "viol_pred_s": pred["viol_s"],
                "viol_s": _rel(viol, t_inj),
                "detect_pred_s": pred["detect_s"],
                "detect_s": _rel(fire, viol),
                "pending_only": n_pend - n_fire,
                "false_page": sum(1 for g in graded if g["false_page"] and t_inj <= g["first"] < t_next),
                "valid": not row_notes,
                "note": "; ".join(row_notes),
            }
        )
    return rows


def find_reps(session: Path) -> list[Path]:
    """Các lượt đã chạy xong (có meta.json; lượt dừng giữa chừng không có)."""
    return sorted(p.parent for p in session.glob("rep*/meta.json"))


def _range(values: Sequence[float | None], fmt: str = "{:.0f}") -> str:
    """'min–max (TB)' của các giá trị có số; '–' nếu không có giá trị nào."""
    vals = [v for v in values if v is not None and not math.isnan(v)]
    if not vals:
        return "–"
    lo, hi = fmt.format(min(vals)), fmt.format(max(vals))
    return f"{lo}–{hi} ({fmt.format(m.mean(vals))})" if lo != hi else lo


def summary(rows: Sequence[dict[str, Any]], session: Path) -> str:
    """Bảng markdown theo mức x (để chép vào van-hanh.md), cộng các dòng không hợp lệ."""
    ok = [r for r in rows if r["valid"]]
    lines = [
        f"LT8: {session} — {len(ok)}/{len(rows)} lần bơm hợp lệ",
        "",
        "| x mục tiêu | x dự đoán | x client | x server | điều kiện đúng, s (dự đoán) "
        "| firing, s (dự đoán) | hết sau khi gỡ, s (dự đoán) | N7: vi phạm → firing, s (dự đoán) "
        "| pending không thành firing | page giả |",
        "|---|---|---|---|---|---|---|---|---|---|",
    ]
    for x in sorted({r["x_target"] for r in ok}):
        g = [r for r in ok if r["x_target"] == x]
        p = predict(g[0]["x_pred"])

        def pr(v: float | None) -> str:
            return "không kêu" if v is None else f"{v:.0f}"

        lines.append(
            f"| {x:g} | {g[0]['x_pred']:.3f} | {_range([r['x_client'] for r in g], '{:.3f}')} "
            f"| {_range([r['x_server'] for r in g], '{:.3f}')} "
            f"| {_range([r['cond_s'] for r in g])} ({pr(p['cond_s'])}) "
            f"| {_range([r['fire_s'] for r in g])} ({pr(p['fire_s'])}) "
            f"| {_range([r['clear_s'] for r in g])} ({pr(p['clear_s'])}) "
            f"| {_range([r['detect_s'] for r in g])} ({pr(p['detect_s'])}) "
            f"| {sum(r['pending_only'] for r in g)} | {sum(r['false_page'] for r in g)} |"
        )
    lines += [
        "",
        f"pending → firing, s: {_range([r['pending_to_fire_s'] for r in ok], '{:.1f}')}; "
        f"điều kiện đúng → pending, s: {_range([r['cond_to_pending_s'] for r in ok], '{:.1f}')}; "
        f"firing − dự đoán, s: {_range([r['fire_lag_s'] for r in ok], '{:+.0f}')}; "
        f"vi phạm N7 sau lúc bơm, s: {_range([r['viol_s'] for r in ok])}",
    ]
    for r in rows:
        if not r["valid"]:
            lines.append(f"Không hợp lệ: rep{r['rep']} lần {r['order']} (x = {r['x_target']:g}): {r['note']}")
    return "\n".join(lines)


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("session", type=Path, help="thư mục runs/sim/lt8-<giờ>")
    ap.add_argument("--out", type=Path, help="ghi bảng mỗi lần bơm một dòng ra CSV này")
    args = ap.parse_args(argv)
    reps = find_reps(args.session)
    if not reps:
        ap.error(f"không thấy lượt nào (rep<r>/meta.json) trong {args.session}")
    rows = []
    for d in reps:
        # Máy tạo tải lỗi (pod Failed, kubectl cp hỏng) thì bộ đo vẫn ghi meta.json nhưng không có load/:
        # bỏ lượt đó và báo, không để cả bảng dừng.
        missing = [f for f in ("loadgen.json", "requests.csv") if not (d / "load" / f).exists()]
        if missing:
            print(f"Bỏ {d.name}: thiếu load/{', load/'.join(missing)}")
            continue
        rows += analyze_rep(d)
    if not rows:
        ap.error("không lượt nào đủ dữ liệu")
    rows.sort(key=lambda r: (r["x_target"], r["rep"]))
    if args.out:
        write_csv(args.out, rows, COLUMNS)
    print(summary(rows, args.session))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
