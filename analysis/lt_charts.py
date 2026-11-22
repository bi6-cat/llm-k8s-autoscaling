"""Hình của LT5–LT8 (Little, GPU util, thuật toán HPA, burn rate) cho chương 5 (Môi trường §19, §16).

Khái niệm:
    Hình LT5 có hai ô, chung trục hoành λ_thực × W (thang log). Ô trái: L_server (trung bình Σ_pod running +
        waiting) theo λ_thực × W, với đường y = x (định luật Little L = λW) và dải ±15 % (tiêu chí của
        Môi trường §19). Ô phải: độ lệch L_server ÷ (λ_thực × W) − 1, kèm thanh ±1 SE do lấy mẫu 5 s
        (se_sampling của lt5_little, chỉ có khi chưa xếp hàng). Chấm rỗng là cửa sổ có hàng đợi (waiting
        trung bình ≥ lt5_little.QUEUE_MIN), hình thoi là lượt mà runner đánh dấu không hợp lệ.
    Hình LT6 có hai ô, chung trục hoành λ ÷ C (C: λ lớn nhất còn đạt SLO, từ ĐG1). Ô trái: GPU util (tín hiệu
        A1) đo, so với dự đoán 1 − e^(−L), và mức util mà trên đó A1 thêm pod khi đang có 1 replica (target ×
        (1 + tolerance)). Ô phải: running + waiting (tín hiệu A2, thang log) và threshold A2 của từng model.
        Dải nền là tải vừa (0,3–0,7 C), vạch đứng là λ = C. Tiêu đề mỗi ô ghi kết luận "tách được tải vừa
        khỏi quá tải hay không", tính bằng lt6_gpu_util.separation (cùng phép kiểm với bảng ở van-hanh.md).
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
    kèm ngày giờ) để mọi hình của chương 5 trông như một bộ. Hình LT5, LT6, LT7 vẽ từ CSV đã commit
    (analysis/figures/lt5-little.csv, lt6-gpu-util.csv, lt7-hpa.csv), nên ai cũng vẽ lại được; hình LT8 cần
    dữ liệu thô của phiên lt8 (prom.json, timeline.json), chỉ có trên máy đã đo. Lần bơm không hợp lệ theo
    lt8_burn.analyze_rep thì không vẽ.
Hạn chế: Màu ở LT7, LT8 gắn với chuỗi đo (r_5m, r_1m, các chặng trễ), ở LT5, LT6 gắn với nguồn dữ liệu (model
    ở nhà, simulator, V2), không gắn với cấu hình A2, S4…, vì LT không so cấu hình. Nhóm của mỗi nguồn tra
    bảng SOURCE_GROUP theo (env, session), vì CSV không có cột model; nguồn chưa có trong bảng (ví dụ V1)
    thì vẽ màu xám, ghi tên phiên và in cảnh báo, cần thêm vào bảng. LT5 bỏ cửa sổ có request lỗi (không
    áp được định luật) và cửa sổ `main` của kịch bản nhiều pha (KB2, KB3: chồng lên các pha), số cửa sổ bị
    bỏ ghi dưới trục.
    Mốc của LT8 theo giờ thực, sai dưới 1 s do WSL kéo giờ (lt8_burn, "Đồng hồ").

Chạy (từ gốc repo):
    uv run --project analysis python -m analysis.lt_charts [--lt5 analysis/figures/lt5-little.csv] \\
        [--lt6 analysis/figures/lt6-gpu-util.csv] [--lt7 analysis/figures/lt7-hpa.csv] \\
        [--lt8 runs/sim/lt8-<giờ>] [--out analysis/figures] [--formats svg]
"""

from __future__ import annotations

import argparse
import csv
import math
import textwrap
from collections import defaultdict
from collections.abc import Callable, Mapping, Sequence
from pathlib import Path
from typing import Any

from matplotlib.lines import Line2D
from matplotlib.patches import Patch
from matplotlib.ticker import FuncFormatter, MultipleLocator

from analysis import charts as ch
from analysis import lt5_little as l5
from analysis import lt6_gpu_util as l6
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

# LT5, LT6: màu theo nguồn dữ liệu, thứ tự cố định (màu đi theo nguồn, không theo thứ hạng; nhóm thêm sau
# xếp cuối để màu nhóm cũ không đổi). Model chỉ ghi trong JSON (capacity-1.5b.json: trường `model` =
# Qwen2.5-1.5B-Instruct; capacity.json ở nhà: ghi chú "ĐG1-mini ở nhà với Qwen2.5-0.5B"; V2: cờ --model của
# vLLM = Qwen2.5-3B-Instruct), CSV thì có env và session, nên tra ở đây theo cả hai. Không tra theo tên file:
# ĐG1 ở nhà (0,5B), trên V1 (A4000), lượt thử 4000 Ada và V2 đều ghi ra capacity.json, ba file sau cùng env
# cloud. session của file capacity là trường `session` trong JSON (file cũ không có thì là tên file), của
# phiên runner là tên phiên, nên ĐG1 V2 có cùng session ở LT5 (dữ liệu thô) và LT6 (capacity.json).
V2_GROUP = "V2, model 3B"
SOURCE_GROUP = {
    ("home", "capacity-1.5b.json"): "nhà, model 1,5B",  # file cũ, không ghi session
    ("home", "dg1-home-05b"): "nhà, model 0,5B",
    ("cloud", "dg1-v2-4060ti"): V2_GROUP,  # ĐG1 V2 (1 replica): phiên runner ở LT5, capacity.json ở LT6
    ("cloud", "v2-dg2"): V2_GROUP,  # ĐG2 V2 (1–4 replica), LT5
}
ENV_NAME = {"home": "nhà", "sim": "simulator", "cloud": "VM thuê"}
GROUP_ORDER = ("nhà, model 1,5B", "nhà, model 0,5B", "simulator", V2_GROUP)
GROUP_COLOR = dict(zip(GROUP_ORDER, SERIES_COLORS, strict=False))
OTHER_COLOR = ch.OTHER_STYLE[0]  # nguồn chưa có trong GROUP_ORDER: xám, không lấy màu ô 4+
LT5_TEXT = ("source", "session", "env", "run_id", "attempt", "window")
LT6_TEXT = ("source", "session", "env", "run_id", "band")


def _num(v: str) -> float | None:
    return None if v in ("", "None", "nan") else float(v)


# ── Chuẩn bị dữ liệu (hàm thuần hoặc chỉ đọc file, có test) ────────────────────────────────────────────


def read_rows(path: Path, text: Sequence[str] = (), flags: Sequence[str] = ()) -> list[dict[str, Any]]:
    """Đọc CSV của các script LT: cột trong `text` giữ chuỗi, cột trong `flags` thành bool ("True"), các cột
    còn lại thành float (ô trống → None)."""
    with path.open(newline="", encoding="utf-8") as fh:
        rows = list(csv.DictReader(fh))
    return [
        {k: v if k in text else (v == "True") if k in flags else _num(v) for k, v in r.items()} for r in rows
    ]


def lt7_rows(path: Path) -> list[dict[str, Any]]:
    """Đọc CSV của lt7_hpa: cột số thành float (ô trống → None), clock giữ chuỗi, cờ thành bool."""
    return read_rows(path, ("clock", "hpa_time_source", "rescale_sizes"), ("restarted", "formula_ok"))


def source_group(r: Mapping[str, Any]) -> str:
    """Nhóm (và màu) của một dòng LT5: nguồn có trong SOURCE_GROUP theo bảng (ở nhà theo model, V2 gộp ĐG1 và
    ĐG2), mọi phiên simulator chung một nhóm (cùng cấu hình patch-sim.yaml), nguồn khác thì ghi môi trường và
    tên phiên (mỗi phiên một nhóm, không gộp hai máy khác nhau)."""
    known = SOURCE_GROUP.get((r["env"], _session(r)))
    if known:
        return known
    return "simulator" if r["env"] == "sim" else f"{ENV_NAME.get(r['env'], r['env'])}, {_session(r)}"


def _session(r: Mapping[str, Any]) -> str:
    """session của dòng; CSV cũ (trước 21/11) không có cột này thì dùng source."""
    return r.get("session") or r["source"]


def lt6_group(r: Mapping[str, Any]) -> str:
    """Nhóm của một mức λ ở LT6: như source_group, nhưng mỗi phiên simulator một nhóm riêng, vì phép kiểm
    "tách được" và đường nối các mức λ chỉ có nghĩa trong một lượt ĐG1 (lt6_gpu_util.summary cũng kiểm
    theo từng nguồn)."""
    g = source_group(r)
    return f"{g} ({_session(r)})" if g == "simulator" else g


def _ordered_groups(rows: Sequence[Mapping[str, Any]], group: Callable[..., str] = source_group) -> list[str]:
    """Các nhóm có trong dữ liệu: nhóm đã biết theo GROUP_ORDER, nhóm lạ theo tên, xếp sau."""
    have = {group(r) for r in rows}
    return [g for g in GROUP_ORDER if g in have] + sorted(have - set(GROUP_ORDER))


def unmapped(rows: Sequence[Mapping[str, Any]]) -> list[str]:
    """Nhóm vẽ màu xám vì nguồn chưa có trong SOURCE_GROUP (trừ simulator), để main in cảnh báo: phiên mới
    hoặc đổi tên (ví dụ chạy lại V2) không lặng lẽ tách khỏi nhóm của nó."""
    return [g for g in _ordered_groups(rows) if g not in GROUP_ORDER]


def queued(r: Mapping[str, Any]) -> bool:
    """Cửa sổ hoặc mức λ đã có hàng đợi: waiting trung bình ≥ QUEUE_MIN, hoặc không có số liệu waiting. Cùng
    quy ước với lt5_little.capacity_level (khi đó lt5_little không tính se_sampling)."""
    w = r.get("waiting_mean")
    return w is None or w >= l5.QUEUE_MIN


def lt5_points(rows: Sequence[Mapping[str, Any]]) -> tuple[list[Mapping[str, Any]], dict[str, int]]:
    """Cửa sổ vẽ được trên hình LT5, kèm số cửa sổ bị bỏ theo lý do (chỉ lý do có ít nhất một cửa sổ).

    Bỏ: (có request lỗi) applicable = False, vì không biết request lỗi rời server lúc nào; (cửa sổ `main`)
    cửa sổ cả pha chính của kịch bản nhiều pha (KB2: pre, spike, drop; KB3: ramp, sustain), chồng lên các
    pha, nên mỗi request bị tính hai lần; (thiếu số liệu) không có λ_thực × W dương hoặc L_server;
    (L_server = 0) mọi mẫu server bằng 0, không đặt được lên thang log. Bảng ở van-hanh.md cũng không ghi
    dòng `main`."""
    main, zero = "main (chồng lên các pha)", "có L_server = 0 (thang log)"
    skipped = {"có request lỗi": 0, main: 0, "thiếu số liệu": 0, zero: 0}
    pts = []
    for r in rows:
        if not r["applicable"]:
            skipped["có request lỗi"] += 1
        elif r["window"] == "main":
            skipped[main] += 1
        elif not r["L_pred"] or r["L_server"] is None or r["dev_server"] is None:
            skipped["thiếu số liệu"] += 1
        elif r["L_server"] <= 0:
            skipped[zero] += 1
        else:
            pts.append(r)
    return pts, {k: n for k, n in skipped.items() if n}


def separation_text(
    rows: Sequence[Mapping[str, Any]], key: str, group: Callable[..., str] = lt6_group
) -> str:
    """Kết luận ngắn (cho tiêu đề ô) của phép kiểm "tách được tải vừa khỏi quá tải" trên một tín hiệu, mỗi
    nhóm một phép kiểm lt6_gpu_util.separation (cùng phép kiểm với bảng ở van-hanh.md). "hở" là khoảng hở
    min(quá tải) ÷ max(vừa). Nhóm thiếu một trong hai dải thì bỏ; không nhóm nào kiểm được thì trả "".
    Một nhóm tách được, nhóm kia không thì ghi riêng từng nhóm, để không đọc nhầm thành "tách được"."""
    res = []
    for g in _ordered_groups(rows, group):
        sel = [{**r, key: math.nan if r[key] is None else r[key]} for r in rows if group(r) == g]
        s = l6.separation(sel, key)
        if s["separable"] is not None:
            res.append((g.split("model ")[-1], s))
    if not res:
        return ""

    def gap(s: Mapping[str, Any]) -> str:
        return "∞" if math.isinf(s["gap"]) else f"{s['gap']:.1f}×".replace(".", ",")

    if not any(s["separable"] for _, s in res):
        return "không tách được tải vừa / quá tải"
    if all(s["separable"] for _, s in res):
        return "tách được, hở " + ", ".join(f"{gap(s)} ({name})" for name, s in res)
    return "; ".join(f"{name}: {'hở ' + gap(s) if s['separable'] else 'không tách được'}" for name, s in res)


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


def _pct(ax: Any) -> None:
    """Nhãn trục tung theo phần trăm, dấu phẩy thập phân (0,15 → "15 %")."""
    ax.yaxis.set_major_formatter(FuncFormatter(lambda v, _: f"{v * 100:g} %".replace(".", ",")))


def _comma_log(ax: Any, axes: str = "xy") -> None:
    """Trục log, dấu phẩy thập phân như charts._comma. Vạch chính (1, 10, 100…) luôn có nhãn. Vạch phụ chỉ
    ghi nhãn ở hệ số 2, 3, 5 và khi trục hẹp hơn một bậc 10 (lúc đó vạch chính quá ít), thay cho formatter
    mặc định của matplotlib, vốn ghi "3e−01" hoặc dấu chấm."""

    def minor(v: float, _: Any, axis: Any) -> str:
        lo, hi = sorted(axis.get_view_interval())
        if v <= 0 or lo <= 0 or hi / lo >= 10:
            return ""
        coeff = round(v / 10 ** math.floor(math.log10(v) + 1e-9))
        return f"{v:g}".replace(".", ",") if coeff in (2, 3, 5) else ""

    for a in axes:
        axis = ax.xaxis if a == "x" else ax.yaxis
        axis.set_major_formatter(FuncFormatter(lambda v, _: f"{v:g}".replace(".", ",")))
        axis.set_minor_formatter(FuncFormatter(lambda v, pos, axis=axis: minor(v, pos, axis)))


def _dot(ax: Any, x: float, y: float, color: str, hollow: bool, valid: bool) -> None:
    """Một chấm đo: đặc là chưa xếp hàng, rỗng là có hàng đợi; tròn là lượt hợp lệ, thoi là không hợp lệ.
    Viền trắng quanh chấm đặc để các chấm chồng nhau vẫn tách được."""
    ax.scatter(x, y, s=34, marker="o" if valid else "D", facecolor="white" if hollow else color,
               edgecolor=color if hollow else "white", lw=1.3 if hollow else 0.8, zorder=3)  # fmt: skip


def _state_handles(
    rows: Sequence[Mapping[str, Any]], group: Callable[..., str] = source_group
) -> list[Line2D]:
    """Mục legend chung của LT5, LT6: màu từng nhóm, rồi ý nghĩa chấm rỗng và hình thoi (nếu có)."""
    out = [
        Line2D([], [], ls="", marker="o", color=GROUP_COLOR.get(g, OTHER_COLOR), markersize=6, label=g)
        for g in _ordered_groups(rows, group)
    ]
    wait = f"{l5.QUEUE_MIN:g}".replace(".", ",")
    out.append(Line2D([], [], ls="", marker="o", markerfacecolor="white", markeredgecolor=INK_2, markersize=6,
                      label=f"rỗng: có hàng đợi (waiting TB ≥ {wait})"))  # fmt: skip
    if not all(r["valid"] for r in rows):
        out.append(Line2D([], [], ls="", marker="D", color=INK_2, markersize=5,
                          label="thoi: lượt bị đánh dấu không hợp lệ"))  # fmt: skip
    return out


def _envs(rows: Sequence[Mapping[str, Any]]) -> str:
    return ", ".join(dict.fromkeys(ENV_NAME.get(r["env"], r["env"]) for r in rows))


def plot_lt5(points: Sequence[Mapping[str, Any]], skipped: Mapping[str, int]) -> Any:
    """Ô trái: L_server theo λ_thực × W, y = x và dải ±LITTLE_TOL. Ô phải: độ lệch, thanh ±1 SE lấy mẫu."""
    fig, (ax_a, ax_b) = plt.subplots(1, 2, figsize=(7.6, 4.0), layout="constrained", sharex=True)
    tol = l5.LITTLE_TOL
    tol_txt = f"±{tol * 100:g} %"
    lo = min(min(r["L_pred"], r["L_server"]) for r in points) / 1.4
    hi = max(max(r["L_pred"], r["L_server"]) for r in points) * 1.4
    grid = [lo * (hi / lo) ** (i / 200) for i in range(201)]
    ax_a.fill_between(grid, [g * (1 - tol) for g in grid], [g * (1 + tol) for g in grid], color=PHASE_FILL,
                      lw=0, zorder=0)  # fmt: skip
    ax_a.plot(grid, grid, color=INK, lw=1, zorder=1)
    ax_b.axhspan(-tol, tol, color=PHASE_FILL, lw=0, zorder=0)
    ax_b.axhline(0, color=INK, lw=1, zorder=1)
    for r in points:
        color, hollow = GROUP_COLOR.get(source_group(r), OTHER_COLOR), queued(r)
        x, dev = r["L_pred"], r["dev_server"]
        _dot(ax_a, x, r["L_server"], color, hollow, r["valid"])
        _dot(ax_b, x, dev, color, hollow, r["valid"])
        if r.get("se_sampling"):  # chỉ có khi chưa xếp hàng (M/G/∞); SE tương đối = SE ÷ (λ_thực × W)
            ax_b.errorbar(x, dev, yerr=r["se_sampling"] / x, fmt="none", ecolor=color, elinewidth=1, zorder=2)
        if abs(dev) > tol:  # nhãn trực tiếp chỉ cho cửa sổ nằm ngoài dải
            name = r["run_id"] if r["window"] == "measure" else f"{r['run_id']}, {r['window']}"
            ax_b.annotate(name, (x, dev), xytext=(-7, 0), textcoords="offset points", ha="right", va="center",
                          color=INK_2)  # fmt: skip
    n_in = sum(1 for r in points if abs(r["dev_server"]) <= tol)
    ax_a.set_xscale("log")
    ax_a.set_yscale("log")
    ax_a.set_xlim(lo, hi)
    ax_a.set_ylim(lo, hi)
    ax_a.set_title(f"L_server theo λ_thực × W ({len(points)} cửa sổ)", loc="left")
    ax_a.set_ylabel("L_server = running + waiting (request)")
    ax_b.set_title(f"Độ lệch: {n_in}/{len(points)} cửa sổ trong {tol_txt}", loc="left")
    ax_b.set_ylabel("L_server ÷ (λ_thực × W) − 1")
    ax_a.set_xlabel("λ_thực × W (request)")
    notes = [f"bỏ {n} cửa sổ {why}" for why, n in skipped.items()]
    ax_b.set_xlabel("\n".join(["λ_thực × W (request)", *notes]))
    _comma_log(ax_a)
    _comma_log(ax_b, "x")
    _pct(ax_b)
    handles = [
        *_state_handles(points),
        Line2D([], [], color=INK, lw=1, label="y = x (L = λW)"),
        Patch(color=PHASE_FILL, label=f"dải {tol_txt}"),
        Line2D([], [], ls="", marker="|", color=INK_2, markersize=9, label="±1 SE lấy mẫu (chưa xếp hàng)"),
    ]
    fig.legend(handles=handles, loc="outside lower center", ncols=3)
    fig.suptitle(f"LT5 – Định luật Little: L_server so với λ_thực × W ({_envs(points)})")
    return fig


def plot_lt6(rows: Sequence[Mapping[str, Any]]) -> Any:
    """Ô trái: GPU util theo λ ÷ C, dự đoán 1 − e^(−L), mức A1 thêm pod. Ô phải: running + waiting (log) và
    threshold A2. Target A1 và tolerance lấy như lt6_gpu_util; mỗi giá trị target khác nhau một vạch (ở nhà
    chỉ có một: 70 %)."""
    fig, (ax_u, ax_l) = plt.subplots(1, 2, figsize=(7.6, 4.0), layout="constrained", sharex=True)
    groups = _ordered_groups(rows, lt6_group)
    tol = l6.TOLERANCE
    targets = sorted({r["a1_target_pct"] for r in rows if r["a1_target_pct"] is not None})
    ups = [t / 100 * (1 + tol) for t in targets]  # trên mức này A1 đòi 1 → 2 replica
    for ax in (ax_u, ax_l):
        ax.axvspan(*l6.MODERATE, color=PHASE_FILL, lw=0, zorder=0)
        ax.axvline(1.0, color=INK_3, lw=1, zorder=1)
        # Nhãn ở đáy ô: ở đó không có điểm nào (util thấp và L nhỏ chỉ có ở tải nhẹ, bên trái dải)
        ax.text(sum(l6.MODERATE) / 2, 0.03, "tải vừa", transform=ax.get_xaxis_transform(), ha="center",
                color=INK_2)  # fmt: skip
        ax.text(1.02, 0.03, "λ = C", transform=ax.get_xaxis_transform(), color=INK_2)
    for up in ups:
        ax_u.axhline(up, color=INK_2, lw=1, ls="--", zorder=1)
    thresholds = []
    for g in groups:
        rs = sorted((r for r in rows if lt6_group(r) == g), key=lambda r: r["load"])
        color = GROUP_COLOR.get(g, OTHER_COLOR)
        for ax, key in ((ax_u, "gpu_util"), (ax_l, "L_server")):
            pts = [r for r in rs if r[key] is not None]
            ax.plot([r["load"] for r in pts], [r[key] for r in pts], color=color, lw=1, zorder=2)
            for r in pts:
                _dot(ax, r["load"], r[key], color, queued(r), r["valid"])
        for r in rs:
            # lt6_gpu_util chỉ tính khi chưa xếp hàng. Vạch cùng màu model: hai model có mức λ ÷ C gần nhau
            if r["util_pred"] is not None:
                ax_u.scatter(r["load"], r["util_pred"], marker="_", s=110, color=color, lw=1.8, zorder=4)
        thr = next((r["a2_target"] for r in rs if r["a2_target"] is not None), None)
        if thr is not None:
            ax_l.axhline(thr, color=color, lw=1, ls=(0, (2, 2)), zorder=1)  # nét ngắn: khác vạch A1 (--)
            thresholds.append(f"{thr:g}".replace(".", ","))
    ys = [r[k] for r in rows for k in ("gpu_util", "util_pred") if r[k] is not None]
    ax_u.set_ylim(min([*ys, *ups]) - 0.04, 1.02)
    ax_l.set_yscale("log")
    ax_u.set_xlim(0, max(r["load"] for r in rows) * 1.08)
    ax_u.xaxis.set_major_locator(MultipleLocator(0.2))
    # Kết luận dài (3 model trở lên) thì xuống dòng, để không tràn khỏi ô (ô rộng ~3,7 inch, vừa ~44 ký tự;
    # lấy 40 để chừa lề)
    s_u, s_l = (
        textwrap.fill(separation_text(rows, k), 40, break_on_hyphens=False) for k in ("gpu_util", "L_server")
    )
    ax_u.set_title("GPU util (tín hiệu A1)" + (f"\n{s_u}" if s_u else ""), loc="left")
    ax_l.set_title("running + waiting (tín hiệu A2), thang log" + (f"\n{s_l}" if s_l else ""), loc="left")
    ax_u.set_ylabel("GPU util")
    ax_l.set_ylabel("running + waiting (request)")
    for ax in (ax_u, ax_l):
        ax.set_xlabel("λ ÷ C (C: λ lớn nhất còn đạt SLO)")
        ch._comma(ax, "x")
    _pct(ax_u)
    _comma_log(ax_l, "y")

    def vn(v: float) -> str:
        return f"{v:g}".replace(".", ",")

    pred_txt = "dự đoán 1 − e^(−L), cùng màu model"
    handles = [
        *_state_handles(rows, lt6_group),
        Line2D([], [], ls="", marker="_", color=INK_2, markersize=10, mew=1.8, label=pred_txt),
    ]
    if targets:
        base = f"{vn(targets[0])} %" if len(targets) == 1 else "target"
        ups_txt = "; ".join(f"{vn(u * 100)} %" for u in ups)
        a1_txt = f"A1 thêm pod khi util > {ups_txt} ({base} × {vn(1 + tol)})"
        handles.append(Line2D([], [], color=INK_2, lw=1, ls="--", label=a1_txt))
    if thresholds:
        handles.append(Line2D([], [], color=INK_2, lw=1, ls=(0, (2, 2)),
                              label=f"threshold A2, cùng màu model ({'; '.join(thresholds)})"))  # fmt: skip
    fig.legend(handles=handles, loc="outside lower center", ncols=2)
    fig.suptitle(f"LT6 – GPU util và running + waiting theo tải ({_envs(rows)})")
    return fig


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
    p.add_argument("--lt5", type=Path, help="CSV của lt5_little, ví dụ analysis/figures/lt5-little.csv")
    p.add_argument("--lt6", type=Path, help="CSV của lt6_gpu_util, ví dụ analysis/figures/lt6-gpu-util.csv")
    p.add_argument("--lt7", type=Path, help="CSV của lt7_hpa, ví dụ analysis/figures/lt7-hpa.csv")
    p.add_argument("--lt8", type=Path, help="thư mục phiên runs/sim/lt8-<giờ>")
    p.add_argument("--out", type=Path, default=Path("analysis/figures"), help="thư mục ghi hình")
    p.add_argument("--formats", default="svg", help="định dạng, cách nhau dấu phẩy (mặc định svg)")
    a = p.parse_args(argv)
    if not (a.lt5 or a.lt6 or a.lt7 or a.lt8):
        p.error("cần ít nhất một trong --lt5, --lt6, --lt7, --lt8")
    formats = [f.strip() for f in a.formats.split(",") if f.strip()]
    ch._setup()
    log: list[str] = []
    # Hình nào không vẽ được thì ghi lỗi, các hình còn lại vẫn vẽ; luôn in đủ các file đã ghi rồi mới báo lỗi
    errors: list[str] = []
    if a.lt5:
        points, skipped5 = lt5_points(read_rows(a.lt5, LT5_TEXT, ("valid", "applicable")))
        log += [f"cảnh báo LT5: nguồn chưa có trong SOURCE_GROUP, vẽ màu xám: {g}" for g in unmapped(points)]
        if points:
            log += [f"ghi {f}" for f in ch._save(plot_lt5(points, skipped5), a.out / "lt5-little", formats)]
        else:
            errors.append(f"LT5: {a.lt5} không có cửa sổ nào vẽ được")
    if a.lt6:
        rows6 = [r for r in read_rows(a.lt6, LT6_TEXT, ("valid",)) if r["load"] is not None]
        log += [f"cảnh báo LT6: nguồn chưa có trong SOURCE_GROUP, vẽ màu xám: {g}" for g in unmapped(rows6)]
        if rows6:
            log += [f"ghi {f}" for f in ch._save(plot_lt6(rows6), a.out / "lt6-gpu-util", formats)]
        else:
            errors.append(f"LT6: {a.lt6} không có mức λ nào vẽ được")
    if a.lt7:
        rows7 = lt7_rows(a.lt7)
        if rows7:
            log += [f"ghi {f}" for f in ch._save(plot_lt7(rows7), a.out / "lt7-hpa", formats)]
        else:
            errors.append(f"LT7: {a.lt7} không có dòng nào")
    if a.lt8:
        groups, skipped8 = lt8_groups(a.lt8)
        log += skipped8
        if groups:
            fig = plot_lt8(groups, "LT8 – r_1m, r_5m và LLMSLOBurnFast quanh lúc bơm lỗi (simulator)")
            log += [f"ghi {f}" for f in ch._save(fig, a.out / "lt8-burn", formats)]
        else:
            errors.append(f"LT8: không có lần bơm hợp lệ nào trong {a.lt8}")
    for line in [*log, *errors]:
        print(line)
    return 1 if errors else 0


if __name__ == "__main__":
    raise SystemExit(main())
