"""Hình của LT7 (thuật toán HPA) và LT8 (cảnh báo burn rate) cho chương 5 (Môi trường §19, §16).

Khái niệm:
    Hình LT7 có hai ô. Ô trái: số replica HPA dừng lại theo số request đồng thời C. Đường bậc thang là dự
        đoán ⌈C ÷ threshold⌉ (có tolerance 10 %, kẹp ở max), chấm là từng lượt đo. Ô phải: mỗi lượt scale-up
        một thanh ngang, chia theo các chặng trễ nối tiếp (lt7_hpa: d_scrape, d_visible, d_wait, d_ready),
        kèm vạch cận trên 11 s của thời gian quyết định.
    Hình LT8: mỗi mức tỷ lệ xấu x một ô, trục hoành tính từ lúc bơm. Vẽ r_1m, r_5m đo được của từng lần bơm
        (mẫu recording rule, bậc thang) đè lên đường dự đoán r_w(τ) = x · |[τ − w; τ] ∩ [0; D]| ÷ w (vạch
        rộng, nhạt), ngưỡng θ = 0,2, và khoảng cảnh báo kêu: từ lúc firing tới lần tính đầu tiên sau khi gỡ
        mà điều kiện đã sai, đo (mỗi lần bơm một vạch) so với dự đoán (lt8_groups).
Mục đích: Cho thấy bằng hình điều bảng ở van-hanh.md đã nói bằng số: công thức đúng về hình dạng, lệch
    dương vài giây ở mỗi mốc. Dùng lại style của charts.py (màu, font, dấu phẩy thập phân, lưu file không
    kèm ngày giờ) để mọi hình của chương 5 trông như một bộ. Hình LT7 vẽ từ CSV đã commit
    (analysis/figures/lt7-hpa.csv), nên ai cũng vẽ lại được; hình LT8 cần dữ liệu thô của phiên lt8
    (prom.json, timeline.json), chỉ có trên máy đã đo. Lần bơm không hợp lệ theo lt8_burn.analyze_rep thì
    không vẽ.
Hạn chế: Màu ở đây gắn với chuỗi đo (r_5m, r_1m, các chặng trễ), không gắn với cấu hình A2, S4…, vì LT7 và
    LT8 không so cấu hình. Mốc của LT8 theo giờ thực, sai dưới 1 s do WSL kéo giờ (lt8_burn, "Đồng hồ").

Chạy (từ gốc repo):
    uv run --project analysis python -m analysis.lt_charts [--lt7 analysis/figures/lt7-hpa.csv] \\
        [--lt8 runs/sim/lt8-<giờ>] [--out analysis/figures] [--formats svg]
"""

from __future__ import annotations

import argparse
import csv
import math
from collections import defaultdict
from collections.abc import Mapping, Sequence
from pathlib import Path
from typing import Any

from matplotlib.lines import Line2D
from matplotlib.patches import Patch
from matplotlib.ticker import MultipleLocator

from analysis import charts as ch
from analysis import lt7_hpa as l7
from analysis import lt8_burn as l8
from analysis import metrics as m
from analysis.build_tables import _json

plt = ch.plt  # pyplot đã nạp với backend Agg trong charts.py
INK, INK_2, INK_3, PHASE_FILL = ch.INK, ch.INK_2, ch.INK_3, ch.PHASE_FILL

# 4 ô đầu của bảng màu phân loại (giống charts.py, đã chạy validate_palette): thứ tự cố định theo chặng
SERIES_COLORS = ("#2a78d6", "#eb6834", "#1baf7a", "#eda100")
R5_COLOR, R1_COLOR = SERIES_COLORS[0], SERIES_COLORS[1]
LT7_STAGES = (
    ("d_scrape", "tải tới → scrape thấy tải"),
    ("d_visible", "scrape → KEDA thấy mẫu"),
    ("d_wait", "KEDA thấy → HPA đổi replica"),
    ("d_ready", "HPA đổi → pod mới Ready (±1 s)"),
)
CLOCK_NAME = {"mono": "đơn điệu", "wall": "giờ thực"}  # cột clock của lt7_hpa
DECIDE_BOUND_S = 11.0  # cận trên của d_decide = 5 (scrape) + 1 (KEDA làm tròn giây) + 5 (sync), lt7_hpa
PRE_S, POST_S = 60.0, 120.0  # LT8: vẽ từ 60 s trước lúc bơm tới 120 s sau lúc gỡ (hết cảnh báo ≤ ~60 s)
# Vị trí (theo trục tung) của các vạch firing ở LT8, trên mọi đường tỷ lệ (≤ 0,62 ở x = 0,6)
FIRE_Y_PRED, FIRE_Y0, FIRE_DY, Y_TOP = 0.86, 0.81, 0.045, 0.92


def _num(v: str) -> float | None:
    return None if v in ("", "None", "nan") else float(v)


# ── Chuẩn bị dữ liệu (hàm thuần hoặc chỉ đọc file, có test) ────────────────────────────────────────────


def lt7_rows(path: Path) -> list[dict[str, Any]]:
    """Đọc CSV của lt7_hpa: cột số thành float (ô trống → None), clock giữ chuỗi, cờ thành bool."""
    with path.open(newline="", encoding="utf-8") as fh:
        rows = list(csv.DictReader(fh))
    out = []
    for r in rows:
        d: dict[str, Any] = {}
        for k, v in r.items():
            if k in ("clock", "hpa_time_source", "rescale_sizes"):
                d[k] = v
            elif k in ("restarted", "formula_ok"):
                d[k] = v == "True"
            else:
                d[k] = _num(v)
        out.append(d)
    return out


def lt7_stage_runs(rows: Sequence[Mapping[str, Any]]) -> tuple[list[Mapping[str, Any]], int, int]:
    """Lượt vẽ được thanh trễ, sắp theo (C, lần), kèm số lượt bị bỏ vì hai lý do khác nhau:
    (mốc rơi vào khoảng giờ thực bị lặp, clock = "mono?"), (thiếu một chặng, thường là chưa có pod Ready).
    Lọc giống bảng trễ của lt7_hpa.summary (có quyết định, không restart, clock khác "mono?"), nên số lượt
    trên hình khớp n của bảng, trừ lượt thiếu chặng (bảng vẫn tính các chặng còn lại của lượt đó)."""
    scaled = [r for r in rows if r.get("d_decide") is not None and not r.get("restarted")]
    up = [r for r in scaled if r["clock"] != "mono?"]
    ok = [r for r in up if all(r[k] is not None for k, _ in LT7_STAGES)]
    return sorted(ok, key=lambda r: (r["c"], r["rep"])), len(scaled) - len(up), len(up) - len(ok)


def window_pred(tau: float, x: float, w: float, dur: float) -> float:
    """Tỷ lệ xấu dự đoán trên cửa sổ w kết thúc ở τ (giây từ lúc bơm), khi tỷ lệ xấu là x trong [0; dur) và
    0 ở ngoài: x · độ dài phần giao của [τ − w; τ] với [0; dur], chia w. Hàm thuần."""
    return x * max(0.0, min(tau, dur) - max(tau - w, 0.0)) / w


def lt8_injections(d: Path) -> list[dict[str, Any]]:
    """Một lượt rep<r>/ → mỗi lần bơm: x, μ, chuỗi r_1m và r_5m tính bằng giây từ lúc bơm, trong
    [−PRE_S; D + POST_S] với D là độ dài bơm. Không xét hợp lệ, không tính mốc (xem lt8_groups)."""
    meta, tl, prom = _json(d / "meta.json"), _json(d / "timeline.json"), _json(d / "prom.json")
    injects = [e for e in tl if e["event"] == "inject"]
    recovers = [e for e in tl if e["event"] == "recover"]
    r1, r5 = l8.samples(prom["r1"]), l8.samples(prom["r5"])
    out = []
    for i, (inj, rec) in enumerate(zip(injects, recovers, strict=False)):
        t0, dur = inj["wall"], rec["wall"] - inj["wall"]

        def rel(smp: Sequence[tuple[float, float]], t0: float = t0, dur: float = dur) -> list:
            return [(t - t0, v) for t, v in smp if -PRE_S <= t - t0 <= dur + POST_S and not math.isnan(v)]

        out.append({"rep": meta["rep"], "order": i + 1, "x": inj["x"], "mu_ms": inj["mu_ms"],
                    "r1": rel(r1), "r5": rel(r5)})  # fmt: skip
    return out


def lt8_groups(session: Path) -> tuple[dict[float, list[dict[str, Any]]], list[str]]:
    """Phiên lt8 → {x: [lần bơm hợp lệ]}, kèm các dòng báo lần bơm hoặc lượt bị bỏ.

    Hợp lệ, x dự đoán, độ dài bơm và các mốc lấy thẳng từ dòng của lt8_burn.analyze_rep (cùng nguồn với
    bảng ở van-hanh.md), nên hình không vẽ lần bơm mà bảng đã loại và không tự tính lại mốc nào. Vạch firing
    đo đi từ mẫu firing đầu (fire_s) tới lần tính đầu tiên sau khi gỡ mà điều kiện đã sai (inject_s +
    clear_s), cùng định nghĩa với vạch dự đoán [θ·300/x + 60; D + 60·(1 − θ/x)]. Chưa hết trong cửa sổ
    phân tích (clear_s trống) thì kéo tới hết trục. Một lần bơm có nhiều đợt firing thì chỉ thấy một vạch;
    cột pending_only của bảng báo trường hợp đó (dữ liệu 16/11: 0)."""
    groups: dict[float, list[dict[str, Any]]] = defaultdict(list)
    log = []
    for d in l8.find_reps(session):
        if not all((d / "load" / f).exists() for f in ("loadgen.json", "requests.csv")):
            log.append(f"LT8: bỏ {d.name}, thiếu dữ liệu máy tạo tải")
            continue
        rows = {r["order"]: r for r in l8.analyze_rep(d)}
        for inj in lt8_injections(d):
            row = rows.get(inj["order"])
            if row is None or not row["valid"]:
                log.append(f"LT8: bỏ {d.name} lần {inj['order']}: {row['note'] if row else 'không có dòng'}")
                continue
            dur, fire, clear = row["inject_s"], row["fire_s"], row["clear_s"]
            inj.update(
                x_pred=row["x_pred"],
                dur=dur,
                firing=None if fire is None else (fire, None if clear is None else dur + clear),
            )
            groups[inj["x"]].append(inj)
    return dict(groups), log


# ── Vẽ ──────────────────────────────────────────────────────────────────────────────────────────────────


def plot_lt7(rows: Sequence[Mapping[str, Any]]) -> Any:
    """Ô trái: replica theo C (dự đoán và đo). Ô phải: các chặng trễ của từng lượt scale-up. Mọi lượt cùng
    threshold và max (một phiên của lt7-hpa.sh), nên đọc từ dòng đầu, như lt7_hpa.summary."""
    fig, (ax_a, ax_b) = plt.subplots(1, 2, figsize=(7.6, 3.7), layout="constrained", width_ratios=(1, 1.55))
    thr, hi = rows[0]["threshold"], int(rows[0]["max_replicas"])
    title = f"LT7 – Thuật toán HPA trên simulator (threshold {thr:g}, max {hi})"
    cmax = max(r["c"] for r in rows) * 1.15
    cs = [i / 10 for i in range(1, int(cmax * 10) + 1)]
    ax_a.plot(cs, [max(1, math.ceil(c / thr)) for c in cs], color=INK_3, lw=1, ls="--", zorder=1)
    ax_a.plot(cs, [l7.predict_replicas(c, thr, 1, hi) for c in cs], color=INK, lw=1.6, zorder=2)
    # Các lượt cùng C nằm chồng lên nhau: dàn ngang ±0,8 để thấy đủ số chấm
    by_c: dict[float, list] = defaultdict(list)
    for r in rows:
        by_c[r["c"]].append(r)
    for c, rs in by_c.items():
        for j, r in enumerate(sorted(rs, key=lambda r: r["rep"])):
            if r["desired_end"] is None:  # HPA chưa có status: không có gì để chấm (bảng ghi Đúng = sai)
                continue
            dx = (j - (len(rs) - 1) / 2) * 0.8
            ax_a.scatter(c + dx, r["desired_end"], s=30, color=SERIES_COLORS[0], edgecolor="white", lw=0.8,
                         zorder=3)  # fmt: skip
    n_ok = sum(1 for r in rows if r["formula_ok"])
    ax_a.set_title(f"Số replica cuối lượt ({n_ok}/{len(rows)} lượt đúng)", loc="left")
    ax_a.set_xlabel("Số request đồng thời C")
    ax_a.set_ylabel("Số replica")
    ax_a.set_xlim(0, cmax)
    ax_a.set_ylim(0, hi + 2)  # chừa chỗ cho legend ở góc trên trái
    ax_a.yaxis.set_major_locator(MultipleLocator(1))
    ax_a.xaxis.set_major_locator(MultipleLocator(thr))
    ax_a.legend(
        handles=[
            Line2D([], [], color=INK, lw=1.6, label=f"dự đoán (kẹp max = {hi})"),
            Line2D([], [], color=INK_3, lw=1, ls="--", label=f"⌈C ÷ {thr:g}⌉ chưa kẹp"),
            Line2D([], [], ls="", marker="o", color=SERIES_COLORS[0], markersize=6, label="đo, từng lượt"),
        ],
        loc="upper left",
    )

    runs, n_unsure, n_partial = lt7_stage_runs(rows)
    ys = list(range(len(runs)))[::-1]  # lượt đầu ở trên
    for y, r in zip(ys, runs, strict=True):
        left = 0.0
        for (key, _), color in zip(LT7_STAGES, SERIES_COLORS, strict=True):
            ax_b.barh(y, r[key], left=left, height=0.62, color=color, edgecolor="white", lw=1, zorder=2)
            left += r[key]
    # Cận chỉ áp cho ba chặng đầu (thời gian quyết định): mép phải của đoạn xanh lá phải nằm bên trái vạch
    ax_b.axvline(DECIDE_BOUND_S, color=INK_2, lw=1, ls="--", zorder=1)
    ax_b.set_yticks(ys, [f"C = {r['c']:g}, lần {r['rep']:g}" for r in runs])
    ax_b.grid(axis="y", visible=False)
    ax_b.set_xlim(0, max([DECIDE_BOUND_S, *(sum(r[k] for k, _ in LT7_STAGES) for r in runs)]) + 1)
    ax_b.set_title(f"Các chặng trễ khi scale-up ({len(runs)} lượt)", loc="left")
    clocks = "/".join(sorted({CLOCK_NAME.get(r["clock"], r["clock"]) for r in runs})) or "đơn điệu"
    skip = [f"bỏ {n_unsure} lượt có mốc rơi vào bước lùi của giờ thực"] if n_unsure else []
    skip += [f"bỏ {n_partial} lượt thiếu chặng"] if n_partial else []
    ax_b.set_xlabel("\n".join([f"Giây từ lúc tải tới (đồng hồ {clocks})", *skip]))
    handles = [Patch(color=c, label=label) for (_, label), c in zip(LT7_STAGES, SERIES_COLORS, strict=True)]
    bound = f"cận trên thời gian quyết định {DECIDE_BOUND_S:g} s"
    handles.append(Line2D([], [], color=INK_2, lw=1, ls="--", label=bound))
    fig.legend(handles=handles, loc="outside lower center", ncols=2)
    for ax in (ax_a, ax_b):
        ch._comma(ax, "x")
    fig.suptitle(title)
    return fig


def plot_lt8(groups: Mapping[float, Sequence[Mapping[str, Any]]], title: str) -> Any:
    """Mỗi mức x một ô xếp dọc, chung trục thời gian (giây từ lúc bơm)."""
    xs = sorted(groups)
    fig, axes = plt.subplots(len(xs), 1, sharex=True, sharey=True, figsize=(7.2, 2.3 * len(xs) + 1.0),
                             layout="constrained", squeeze=False)  # fmt: skip
    t_max = max(i["dur"] for g in groups.values() for i in g) + POST_S
    for ax, x in zip(axes[:, 0], xs, strict=True):
        injs = sorted(groups[x], key=lambda i: i["rep"])
        dur, x_pred = m.mean(i["dur"] for i in injs), injs[0]["x_pred"]
        ax.axvspan(0, dur, color=PHASE_FILL, lw=0, zorder=0)
        grid = [-PRE_S + s for s in range(int(t_max + PRE_S) + 1)]
        for w, color in ((l8.LONG_W, R5_COLOR), (l8.SHORT_W, R1_COLOR)):
            ys = [window_pred(t, x_pred, w, dur) for t in grid]
            ax.plot(grid, ys, color=color, lw=5, alpha=0.28, solid_capstyle="butt", zorder=1)
        for inj in injs:
            for key, color in (("r5", R5_COLOR), ("r1", R1_COLOR)):
                pts = inj[key]
                # Giá trị của recording rule giữ nguyên tới lần tính sau (15 s): bậc thang kiểu "post"
                ax.step([t for t, _ in pts], [v for _, v in pts], where="post", color=color, lw=1, zorder=2)
        ax.axhline(l8.THETA, color=INK_2, lw=1, ls="--", zorder=1)
        # Nhãn ở mép trái: trước lúc bơm mọi đường gần 0, nên không đè dữ liệu
        ax.text(-PRE_S + 2, l8.THETA, f"θ = {l8.THETA:g}".replace(".", ","), va="bottom", color=INK_2)
        p = l8.predict(x_pred)
        if p["fire_s"] is not None:
            ax.hlines(FIRE_Y_PRED, p["fire_s"], dur + p["clear_s"], color=INK_3, lw=3)
        n_fire = 0
        for j, inj in enumerate(injs):
            if inj["firing"] is not None:
                a, b = inj["firing"]
                ax.hlines(FIRE_Y0 - j * FIRE_DY, a, t_max if b is None else b, color=INK, lw=3)
                n_fire += 1
        if p["fire_s"] is None and n_fire == 0:
            ax.text(0.5 * dur, FIRE_Y0, f"không kêu ở cả {len(injs)} lần bơm (đúng dự đoán)", ha="center",
                    va="center", color=INK_2)  # fmt: skip
        x_txt, xp_txt = f"{x:g}".replace(".", ","), f"{x_pred:.3f}".replace(".", ",")
        ax.set_title(f"x = {x_txt} (dự đoán {xp_txt}, μ = {injs[0]['mu_ms']:g} ms), n = {len(injs)} lần bơm",
                     loc="left")  # fmt: skip
        ax.set_ylabel("Tỷ lệ TTFT > 2,5 s")
        ch._comma(ax)
    ax.set_ylim(0, Y_TOP)
    ax.set_xlim(-PRE_S, t_max)
    ax.xaxis.set_major_locator(MultipleLocator(60))
    ax.set_xlabel("Giây từ lúc bơm (nền xám: đang bơm)")
    handles = [
        Line2D([], [], color=R5_COLOR, lw=1, label="r_5m đo"),
        Line2D([], [], color=R1_COLOR, lw=1, label="r_1m đo"),
        Line2D([], [], color=INK_2, lw=5, alpha=0.28, label="dự đoán (cùng màu)"),
        Line2D([], [], color=INK, lw=3, label="firing đo (mỗi lần bơm một vạch)"),
        Line2D([], [], color=INK_3, lw=3, label="firing dự đoán"),
    ]
    fig.legend(handles=handles, loc="outside lower center", ncols=3)
    fig.suptitle(title)
    return fig


def main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    p.add_argument("--lt7", type=Path, help="CSV của lt7_hpa, ví dụ analysis/figures/lt7-hpa.csv")
    p.add_argument("--lt8", type=Path, help="thư mục phiên runs/sim/lt8-<giờ>")
    p.add_argument("--out", type=Path, default=Path("analysis/figures"), help="thư mục ghi hình")
    p.add_argument("--formats", default="svg", help="định dạng, cách nhau dấu phẩy (mặc định svg)")
    a = p.parse_args(argv)
    if not a.lt7 and not a.lt8:
        p.error("cần ít nhất một trong --lt7, --lt8")
    formats = [f.strip() for f in a.formats.split(",") if f.strip()]
    ch._setup()
    log: list[str] = []
    if a.lt7:
        rows = lt7_rows(a.lt7)
        if not rows:
            print(f"LT7: {a.lt7} không có dòng nào")
            return 1
        fig = plot_lt7(rows)
        log += [f"ghi {f}" for f in ch._save(fig, a.out / "lt7-hpa", formats)]
    if a.lt8:
        groups, skipped = lt8_groups(a.lt8)
        log += skipped
        if not groups:
            print("\n".join(log))
            print(f"LT8: không có lần bơm hợp lệ nào trong {a.lt8}")
            return 1
        fig = plot_lt8(groups, "LT8 – r_1m, r_5m và LLMSLOBurnFast quanh lúc bơm lỗi (simulator)")
        log += [f"ghi {f}" for f in ch._save(fig, a.out / "lt8-burn", formats)]
    for line in log:
        print(line)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
