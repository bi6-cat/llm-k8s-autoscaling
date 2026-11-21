"""Biểu đồ C1–C4 của chương 5 từ dữ liệu runner (Môi trường §16, §15).

Khái niệm:
    C1 = chuỗi thời gian của KB2 (tải tăng đột ngột) cho từng cấu hình, bốn ô xếp dọc chung trục thời gian:
        λ(t) theo lịch gửi, số replica, TTFT p95 trượt 30 s, độ dài hàng đợi. Đây là biểu đồ trung tâm: nó
        cho thấy HPA phản ứng bao lâu (N2a), SLO hồi phục bao lâu (N2b) và vì sao A2 tốt hơn A1.
    C2 = SLO attainment theo cấu hình × kịch bản; C3 = GPU-giờ so với S4 (cấu hình tĩnh cấp theo đỉnh);
    C4 = trade-off giữa hai số đó, mỗi kịch bản một ô. Ba hình này vẽ cột hoặc điểm = trung bình các lượt
        `counted`, kèm một chấm cho từng lượt (§16: 1–3 lượt mỗi ô nên phải thấy được độ phân tán).
    "Lượt counted" = lần thử hợp lệ cuối cùng của lượt (build_tables.mark_counted).
Mục đích: Vẽ từ đúng các số mà build_tables tính cho bảng nghiệm thu (gọi build_tables.build, không đọc lại
    CSV), nên hình và bảng không thể lệch nhau. Đường TTFT p95 của C1 dùng metrics.sliding_ttft_p95, cùng
    hàm với N2b. Quy ước §16: không dùng hai trục tung; màu gắn cố định với từng cấu hình (CONFIG_STYLE),
    kèm hình dạng marker và nhãn chữ để không phải phân biệt chỉ bằng màu; hình nào cũng ghi số lượt.
    C5 (cold start 8 pha) và C6 (rolling update VH2) chưa có ở đây: cần dữ liệu ĐG3 và VH2.
Hạn chế: trên kind trong WSL2, mốc của requests.csv theo đồng hồ đơn điệu, chạy nhanh hơn giờ thực khoảng
    1,6 %, còn metric theo giờ thực, nên ô số replica và ô hàng đợi lệch dần so với ô λ và ô TTFT (khoảng
    20 s cuối lượt 24 phút). Không hiệu chỉnh: VM thuê của V2 không bị lệch này (nhật ký vận hành, LT5).

Chạy (từ gốc repo):
    uv run --project analysis python -m analysis.charts runs/<phiên> [runs/<phiên 2> …] \\
        [--out <thư mục>] [--baseline S4] [--formats svg,png]
"""

from __future__ import annotations

import argparse
import csv
import math
from collections import defaultdict
from collections.abc import Iterable, Mapping, Sequence
from pathlib import Path
from typing import Any, NamedTuple

import matplotlib

matplotlib.use("Agg")  # vẽ thẳng ra file, không cần màn hình (VM thuê, CI)

import matplotlib.pyplot as plt  # noqa: E402  (phải chọn backend trước khi nạp pyplot)
from matplotlib.lines import Line2D  # noqa: E402
from matplotlib.ticker import FixedLocator, FuncFormatter, MaxNLocator, NullFormatter  # noqa: E402
from matplotlib.transforms import Bbox  # noqa: E402

from analysis import build_tables as bt  # noqa: E402
from analysis import metrics as m  # noqa: E402

RATE_BIN_S = 30.0  # ô λ(t): đếm request theo lịch gửi trong từng khoảng 30 s, cùng cửa sổ với TTFT p95
DEFAULT_TIMEOUT_S = 120.0  # timeout của máy tạo tải nếu loadgen.json không ghi (Môi trường §14.2)

# Màu theo thứ tự 4 ô đầu của bảng màu phân loại mặc định (skill dataviz, đã chạy validate_palette): cấu hình
# chính A2 lấy ô 1. C1 chỉ có 3 cấu hình (S4, A1, A2), là 3 ô đầu, đạt ngưỡng phân biệt cho người mù màu
# với MỌI cặp. S1 (ô 4, vàng) chỉ xuất hiện ở C2–C4, nơi mỗi cột hoặc điểm luôn có nhãn chữ và marker riêng.
CONFIG_STYLE = {
    "A2": ("#2a78d6", "o"),
    "S4": ("#eb6834", "s"),
    "A1": ("#1baf7a", "^"),
    "S1": ("#eda100", "D"),
}
OTHER_STYLE = ("#8a8984", "X")  # cấu hình ngoài 4 mã trên (thử nghiệm riêng): xám, không lấy màu ô 5+
CONFIG_ORDER = ["S1", "S4", "A1", "A2"]  # thấp → cao về mức "thông minh", đọc từ trái sang phải
SCENARIO_ORDER = ["KB1", "KB2", "KB3"]
# C1 so ba cấu hình đáng so về hành vi theo thời gian (Môi trường §16): tĩnh cấp theo đỉnh và hai cách scale.
# S1 quá tải suốt pha spike nên chỉ thêm một đường TTFT nằm ở trần; đổi bằng --c1-configs khi cần.
C1_CONFIGS = ("S4", "A1", "A2")
# C4: các vị trí thử cho nhãn của điểm trung bình, theo thứ tự ưu tiên: (dx, dy) tính bằng point so với tâm
# điểm, căn ngang, căn dọc. Vòng hai xa điểm gấp 2,5 lần, cho khi các điểm chụm lại. _place_labels đo nhãn
# thật và chọn vị trí ít va chạm nhất. Hướng cố định theo cấu hình (bản trước) đè lên vạch N1 và lên nhãn
# khác khi dữ liệu V2 có các điểm sát nhau (A1, A2 cùng ≈ 92 % GPU-giờ ở KB3).
LABEL_TRIES = [
    (k * dx, k * dy, ha, va)
    for k in (1.0, 2.5)
    for dx, dy, ha, va in (
        (6, 4, "left", "bottom"),
        (-6, 4, "right", "bottom"),
        (6, -4, "left", "top"),
        (-6, -4, "right", "top"),
        (0, 7, "center", "bottom"),
        (0, -7, "center", "top"),
    )
]
MEAN_SIZE, RUN_SIZE = 64.0, 16.0  # diện tích marker (point²) của điểm trung bình và của chấm từng lượt
# Hai điểm trung bình cách nhau dưới 4 point (nửa cỡ marker, mức mà điểm trên che gần hết điểm dưới) coi như
# trùng: chung một nhãn, điểm sau vẽ nhỏ hơn. Xa hơn thì hai marker chỉ chạm nhau, vẫn nhận ra từng cái.
NEAR_PT = 4.0
HEADROOM = 0.14  # C4 chừa 14 % chiều cao trục tung phía trên mức 100 % để đặt nhãn của các điểm ở 100 %
INK, INK_2, INK_3, GRID, PHASE_FILL = "#0b0b0b", "#52514e", "#8a8984", "#e4e3df", "#f1f0ed"


def style(config: str) -> tuple[str, str]:
    """(màu, marker) cố định của một cấu hình."""
    return CONFIG_STYLE.get(config, OTHER_STYLE)


def _ordered(keys: Iterable[Any], order: Sequence[str]) -> list[Any]:
    """Khoá theo thứ tự `order`, khoá lạ xếp sau theo bảng chữ cái (so dạng chuỗi, nên None không làm lỗi)."""
    ks = set(keys)
    return [k for k in order if k in ks] + sorted(ks - set(order), key=str)


def _isnum(v: Any) -> bool:
    return isinstance(v, (int, float)) and not isinstance(v, bool) and not math.isnan(v)


# ── Chuẩn bị dữ liệu (hàm thuần, có test) ──────────────────────────────────────────────────────────────


def kb2_series(d: Path) -> dict[str, Any]:
    """Một thư mục attempt-<n> → các chuỗi của C1, thời gian tính bằng giây kể từ t0 của máy tạo tải.

    rate:       (mép các khoảng RATE_BIN_S, số request ÷ độ dài khoảng) = λ(t) THEO LỊCH GỬI (t_sched), giống
                nhau ở mọi cấu hình cùng lượt; máy tạo tải gửi trễ so với lịch thì đã bị loại ở checks
                (send_lag_ok, Môi trường §9), nên không cần vẽ λ theo lúc gửi thật
    ttft_p95:   [(t, p95)] trên lưới STEP_S; inf = cửa sổ có request lỗi chiếm phần p95; None = cửa sổ rỗng
    replicas_spec, replicas_ready: [(t, n)] số replica HPA đặt và số replica đang phục vụ (kube-state-metrics)
    queue:      [(t, tổng vllm:num_requests_waiting của mọi pod)] = request đã nhận mà chưa được xử lý
    """
    lg = bt._json(d / "loadgen.json")
    t0, dur = float(lg["t0_unix"]), float(lg["duration_s"])
    with (d / "requests.csv").open(newline="", encoding="utf-8") as fh:
        reqs = [m.parse_request(r, t0) for r in csv.DictReader(fh)]
    met = bt.read_metrics(d / "metrics.csv.gz")

    n_bins = max(1, math.ceil(dur / RATE_BIN_S))
    counts = [0] * n_bins
    for r in reqs:
        i = int((r.t_sched - t0) // RATE_BIN_S)
        if 0 <= i < n_bins:
            counts[i] += 1
    edges = [min(i * RATE_BIN_S, dur) for i in range(n_bins + 1)]  # khoảng cuối có thể ngắn hơn 30 s

    grid = [t0 + i * bt.STEP_S for i in range(int(dur // bt.STEP_S) + 1)]
    p95 = m.sliding_ttft_p95(reqs, grid, m.RECOVERY_WINDOW_S)

    def rel(samples: Iterable[tuple[float, float]]) -> list[tuple[float, float]]:
        # Lấy cả một mẫu trước t0 để đường bậc thang có giá trị ngay từ đầu trục
        return [(t - t0, v) for t, v in samples if t0 - bt.STEP_S <= t <= t0 + dur]

    queue: dict[float, float] = defaultdict(float)
    for ts, _, v in met.get("vllm_waiting", []):
        queue[ts] += v  # mỗi pod một chuỗi; query_range trả mẫu đúng lưới bước nên cộng theo mốc được

    return {
        "t0_unix": t0,
        "duration_s": dur,
        "timeout_s": float((lg.get("target") or {}).get("timeout_s") or DEFAULT_TIMEOUT_S),
        "phases": {k: (float(a), float(b)) for k, (a, b) in (lg.get("phases_s") or {}).items()},
        "rate": (edges, [c / (b - a) for c, a, b in zip(counts, edges, edges[1:], strict=False)]),
        "ttft_p95": [(t - t0, v) for t, v in zip(grid, p95, strict=True)],
        "replicas_spec": rel(bt.max_by_ts(met.get("replicas_spec", []))),
        "replicas_ready": rel(bt.max_by_ts(met.get("replicas_ready", []))),
        "queue": rel(sorted(queue.items())),
    }


def c1_groups(
    rows: Sequence[Mapping[str, Any]], configs: Sequence[str] = C1_CONFIGS
) -> tuple[dict[tuple[Any, Any], dict[str, Any]], list[str]]:
    """Lần thử counted của KB2 thuộc `configs` → {(env, repeat, C): {config: dòng runs}}, kèm cảnh báo. Lịch
    gửi do kịch bản, số thứ tự lượt và năng lực C quyết định (Môi trường §14.2, §9), nên mỗi nhóm là một
    hình C1 so được từng giây giữa các cấu hình; phiên đo trước và sau khi hiệu chỉnh lại C thì tách hình.
    Hai phiên cùng có một lượt (chạy lại cả phiên) thì giữ phiên đọc trước và báo lại."""
    out: dict[tuple[Any, Any], dict[str, Any]] = defaultdict(dict)
    warn = []
    for r in rows:
        if not (r.get("counted") and r.get("scenario") == "KB2" and r.get("config") in configs):
            continue
        g = out[(r["env"], r["repeat"], r.get("capacity_rps"))]
        if r["config"] in g:
            warn.append(
                f"C1: bỏ {r['session']}/{r['run_id']}, đã có {g[r['config']]['session']}/{r['run_id']}"
            )
            continue
        g[r["config"]] = r
    return dict(out), warn


def cell_values(
    rows: Sequence[Mapping[str, Any]], key: str, scale: float = 1.0
) -> dict[str, dict[str, list]]:
    """{kịch bản: {cấu hình: [giá trị × scale của từng lượt counted]}}, bỏ ô trống. Môi trường gộp chung
    (giống cells.csv thì tách env): biểu đồ của chương 5 chỉ vẽ một môi trường, do người gọi lọc trước."""
    out: dict[str, dict[str, list]] = defaultdict(lambda: defaultdict(list))
    for r in rows:
        v = r.get(key)
        if r.get("counted") and _isnum(v):
            out[r["scenario"]][r["config"]].append(float(v) * scale)
    return {s: dict(c) for s, c in out.items()}


def paired_values(rows: Sequence[Mapping[str, Any]], xkey: str, ykey: str) -> dict[str, dict[str, list]]:
    """Như cell_values nhưng mỗi lượt là một cặp (x, y), chỉ lấy lượt có đủ cả hai (cho C4)."""
    out: dict[str, dict[str, list]] = defaultdict(lambda: defaultdict(list))
    for r in rows:
        x, y = r.get(xkey), r.get(ykey)
        if r.get("counted") and _isnum(x) and _isnum(y):
            out[r["scenario"]][r["config"]].append((float(x) * 100, float(y) * 100))
    return {s: dict(c) for s, c in out.items()}


# ── Vẽ ──────────────────────────────────────────────────────────────────────────────────────────────────


def _setup() -> None:
    plt.rcParams.update(
        {
            "font.size": 9,
            "axes.edgecolor": INK_3,
            "axes.labelcolor": INK,
            "axes.titlesize": 10,
            "axes.spines.top": False,
            "axes.spines.right": False,
            "axes.grid": True,
            "grid.color": GRID,
            "grid.linewidth": 0.6,
            "xtick.color": INK_2,
            "ytick.color": INK_2,
            "legend.frameon": False,
            "svg.hashsalt": "llm-k8s-analysis",  # id cố định trong SVG: chạy lại ra đúng cùng file
        }
    )


def _comma(ax: Any, axes: str = "xy") -> None:
    """Dấu phẩy thập phân kiểu Việt Nam trên nhãn trục (2,5 thay vì 2.5), như phần còn lại của luận văn."""
    fmt = FuncFormatter(lambda v, _: f"{v:g}".replace(".", ","))
    for a in axes:
        (ax.xaxis if a == "x" else ax.yaxis).set_major_formatter(fmt)


def _phase_spans(ax: Any, phases: Mapping[str, tuple[float, float]], label: bool) -> None:
    for i, (name, (a, b)) in enumerate(sorted(phases.items(), key=lambda kv: kv[1][0])):
        if i % 2 == 0:
            ax.axvspan(a / 60, b / 60, color=PHASE_FILL, lw=0, zorder=0)
        if label:
            ax.text((a + b) / 120, 1.02, name, transform=ax.get_xaxis_transform(), ha="center", color=INK_2)


def plot_c1(series: Mapping[str, Mapping[str, Any]], title: str) -> Any:
    """{config: kb2_series(...)} → Figure bốn ô xếp dọc chung trục thời gian (phút)."""
    fig, axes = plt.subplots(4, 1, sharex=True, figsize=(7.2, 8.6), layout="constrained")
    ax_rate, ax_rep, ax_ttft, ax_q = axes
    first = next(iter(series.values()))
    for i, ax in enumerate(axes):
        _phase_spans(ax, first["phases"], label=i == 0)
    ceiling = max(s["timeout_s"] for s in series.values())

    for cfg in _ordered(series, CONFIG_ORDER):
        s, (color, _) = series[cfg], style(cfg)
        edges, rate = s["rate"]
        ax_rate.stairs(rate, [e / 60 for e in edges], color=color, lw=1.5)
        for key, ls, lw in (("replicas_ready", "-", 1.6), ("replicas_spec", "--", 1.0)):
            pts = s[key]
            if pts:
                # Mẫu query_range ở t = giá trị mới nhất tại t, giữ tới mẫu sau: bậc thang kiểu "post"
                ax_rep.step(
                    [t / 60 for t, _ in pts], [v for _, v in pts], where="post", color=color, ls=ls, lw=lw
                )
        # Cửa sổ có request lỗi chiếm phần p95 (inf) vẽ ở trần = timeout: request đó chờ ít nhất ngần ấy
        ys = [math.nan if v is None else min(v, ceiling) for _, v in s["ttft_p95"]]
        ax_ttft.plot([t / 60 for t, _ in s["ttft_p95"]], ys, color=color, lw=1.5)
        if s["queue"]:
            ax_q.plot([t / 60 for t, _ in s["queue"]], [v for _, v in s["queue"]], color=color, lw=1.5)

    ax_ttft.set_yscale("log")
    # Mốc cố định dễ đọc thay cho 2×10⁰, 3×10⁰ của trục log mặc định; mốc phụ không ghi chữ
    ax_ttft.yaxis.set_major_locator(FixedLocator([0.05, 0.1, 0.2, 0.5, 1, 2, 5, 10, 20, 50, 100, 200]))
    ax_ttft.yaxis.set_minor_formatter(NullFormatter())
    ax_ttft.axhline(m.TTFT_SLO_S, color=INK_2, lw=1, ls="--")
    ax_ttft.text(0.995, m.TTFT_SLO_S, "SLO 2,5 s", transform=ax_ttft.get_yaxis_transform(), ha="right",
                 va="bottom", color=INK_2)  # fmt: skip
    ax_rep.yaxis.set_major_locator(MaxNLocator(integer=True))
    ax_rep.set_ylim(bottom=0)
    ax_q.set_ylim(bottom=0)
    ax_rate.set_ylim(bottom=0)
    ax_rate.set_ylabel(f"λ theo lịch (req/s)\ntrung bình {RATE_BIN_S:g} s")
    ax_rep.set_ylabel("Số replica")
    ax_ttft.set_ylabel(f"TTFT p95 (s)\ncửa sổ {m.RECOVERY_WINDOW_S:g} s")
    ax_q.set_ylabel("Hàng đợi\n(request chờ)")
    ax_q.set_xlabel("Thời gian từ đầu pha chính (phút)")
    ax_q.set_xlim(0, max(s["duration_s"] for s in series.values()) / 60)
    for ax in axes:
        _comma(ax)

    # Một legend chung dưới đáy (constrained layout chừa chỗ, không đè dữ liệu hay tiêu đề); tiêu đề của
    # legend mang chú thích, vì chữ đặt tự do bằng fig.text không được layout tính tới.
    handles = [Line2D([], [], color=style(c)[0], lw=2, label=c) for c in _ordered(series, CONFIG_ORDER)]
    handles += [
        Line2D([], [], color=INK_2, lw=1.6, label="replica Ready"),
        Line2D([], [], color=INK_2, lw=1.0, ls="--", label="replica spec (HPA đặt)"),
    ]
    fig.legend(handles=handles, loc="outside lower center", ncols=len(handles), title_fontsize=7.5,
               title=f"TTFT của request lỗi hoặc timeout vẽ ở trần {ceiling:g} s")  # fmt: skip
    fig.suptitle(title)
    return fig


def plot_bars(
    vals: Mapping[str, Mapping[str, list]], ylabel: str, refs: Sequence[tuple[float, str]], title: str
) -> Any:
    """Cột = trung bình các lượt, chấm = từng lượt; nhóm theo kịch bản; nhãn dưới cột = cấu hình, số lượt."""
    scen = _ordered(vals, SCENARIO_ORDER)
    xs, labels, centers, x = [], [], [], 0.0
    for s in scen:
        cfgs = _ordered(vals[s], CONFIG_ORDER)
        centers.append((s, x + (len(cfgs) - 1) / 2))
        for c in cfgs:
            xs.append((x, s, c))
            x += 1
        x += 0.6  # khoảng trống giữa hai kịch bản
    fig, ax = plt.subplots(figsize=(max(4.0, 0.62 * len(xs) + 1.6), 3.6), layout="constrained")
    for xi, s, c in xs:
        v = vals[s][c]
        color, marker = style(c)
        ax.bar(xi, m.mean(v), width=0.72, color=color, edgecolor="white", lw=1, zorder=2)
        ax.scatter([xi] * len(v), v, s=22, marker=marker, color=INK, edgecolor="white", lw=0.6, zorder=3)
        labels.append(f"{c}\nn={len(v)}")
    for y, text in refs:
        ax.axhline(y, color=INK_2, lw=1, ls="--", zorder=1)
        ax.text(1.0, y, f" {text}", transform=ax.get_yaxis_transform(), va="center", color=INK_2)
    ax.set_xticks([xi for xi, _, _ in xs], labels)
    for s, cx in centers:
        ax.annotate(s, (cx, 0), xycoords=("data", "axes fraction"), xytext=(0, -30), 
                    textcoords="offset points",
                    ha="center", va="top", fontweight="bold", annotation_clip=False)  # fmt: skip
    ax.grid(axis="x", visible=False)
    ax.set_ylim(bottom=0)
    ax.set_ylabel(ylabel)
    ax.set_title(title, loc="left")
    _comma(ax, "y")
    return fig


def _overlap(a: Any, b: Any) -> float:
    """Diện tích phần giao (pixel²) của hai Bbox; 0 nếu rời nhau."""
    w = min(a.x1, b.x1) - max(a.x0, b.x0)
    h = min(a.y1, b.y1) - max(a.y0, b.y0)
    return w * h if w > 0 and h > 0 else 0.0


def _place_labels(
    ax: Any, labels: Sequence[tuple[float, float, str]], obstacles: Sequence[Any], lines: Sequence[Any]
) -> None:
    """Đặt từng nhãn (x, y theo dữ liệu, chữ) vào vị trí trong LABEL_TRIES có điểm phạt thấp nhất. Phạt theo
    diện tích giao, nặng tới nhẹ: đè nhãn đã đặt hoặc dấu điểm (obstacles, ×100) > phần tràn ra ngoài ô vẽ
    (×10) > cắt vạch tham chiếu (lines, ×1). Đo bằng kích thước chữ thật (renderer) nên không phải đoán độ dài
    nhãn. Gọi khi layout đã chốt (xem plot_c4), để toạ độ pixel là toạ độ cuối cùng.
    Hạn chế: nếu mọi vị trí thử đều tràn khỏi ô, nhãn vẫn đặt ở vị trí tràn ít nhất và không được so với nhãn
    của ô bên cạnh. Với nhãn chỉ gồm tên cấu hình thì chưa gặp (V2, dữ liệu sim)."""
    renderer = ax.figure.canvas.get_renderer()
    frame = ax.get_window_extent(renderer)
    placed: list[Any] = []
    for x, y, text in labels:
        # Một Annotation cho mỗi nhãn, chỉ đổi vị trí và căn lề khi thử: không tạo rồi xoá artist
        ann = ax.annotate(text, (x, y), xytext=(0, 0), textcoords="offset points", color=INK)
        ann.set_in_layout(False)
        best: tuple[float, tuple[float, float, str, str], Any] | None = None
        for dx, dy, ha, va in LABEL_TRIES:
            ann.xyann = (dx, dy)
            ann.set_horizontalalignment(ha)
            ann.set_verticalalignment(va)
            bb = ann.get_window_extent(renderer)
            cost = (
                100 * sum(_overlap(bb, o) for o in [*placed, *obstacles])
                + 10 * (bb.width * bb.height - _overlap(bb, frame))
                + sum(_overlap(bb, ln) for ln in lines)
            )
            if best is None or cost < best[0]:  # bằng điểm thì giữ vị trí ưu tiên hơn (thử trước)
                best = (cost, (dx, dy, ha, va), bb)
            if cost == 0:
                break
        assert best is not None  # LABEL_TRIES không rỗng
        dx, dy, ha, va = best[1]
        ann.xyann = (dx, dy)
        ann.set_horizontalalignment(ha)
        ann.set_verticalalignment(va)
        placed.append(best[2])


class _Mean(NamedTuple):
    """Điểm trung bình của một cấu hình trong một ô C4."""

    config: str
    x: float
    y: float
    xy_px: tuple[float, float]  # toạ độ pixel sau khi layout đã chốt


def _near_groups(means: Sequence[_Mean], limit_px: float) -> list[list[_Mean]]:
    """Gom các điểm cách nhau dưới limit_px thành nhóm, có bắc cầu: A gần B, B gần C thì A, B, C chung một
    nhóm dù A xa C (nếu không, C sẽ có marker đủ cỡ và nhãn riêng đè ngay cạnh nhãn của nhóm A, B). Trong
    nhóm và giữa các nhóm giữ thứ tự của `means`."""
    order = {mm.config: i for i, mm in enumerate(means)}
    groups: list[list[_Mean]] = []
    for mm in means:
        near = [g for g in groups if any(math.dist(o.xy_px, mm.xy_px) < limit_px for o in g)]
        merged = sorted([*(o for g in near for o in g), mm], key=lambda o: order[o.config])
        groups = [g for g in groups if all(g is not n for n in near)] + [merged]
    return sorted(groups, key=lambda g: order[g[0].config])


def plot_c4(pairs: Mapping[str, Mapping[str, list]], title: str, baseline: str = "S4") -> Any:
    """Mỗi kịch bản một ô: trục hoành GPU-giờ (% S4), trục tung SLO attainment (%); điểm lớn = trung bình,
    chấm nhạt = từng lượt, nhãn chữ cạnh mỗi điểm (đặt tránh va chạm, xem _place_labels). Các điểm trung
    bình gần như trùng nhau (dưới NEAR_PT) dùng chung một nhãn, điểm vẽ sau nhỏ dần để vẫn thấy điểm dưới."""
    scen = _ordered(pairs, SCENARIO_ORDER)
    fig, axes = plt.subplots(1, len(scen), sharey=True, figsize=(2.9 * len(scen) + 0.8, 3.5),
                             layout="constrained",
                             squeeze=False)  # fmt: skip
    seen: set[str] = set()
    for ax, s in zip(axes[0], scen, strict=True):
        for c in _ordered(pairs[s], CONFIG_ORDER):
            pts, (color, marker) = pairs[s][c], style(c)
            ax.scatter([p[0] for p in pts], [p[1] for p in pts], s=RUN_SIZE, marker=marker, color=color,
                       alpha=0.4, lw=0, zorder=2)  # fmt: skip
            seen.add(c)
        ax.axhline(m.ATTAINMENT * 100, color=INK_2, lw=1, ls="--", zorder=1)
        ax.axvline(100, color=INK_3, lw=0.8, zorder=1)
        # Số lượt ghi ở tiêu đề ô, không ở nhãn cạnh điểm: nhãn "S4 (n=1)" quá dài để nằm bên phải điểm 100 %,
        # nên bị đẩy xuống dưới vạch N1, sát điểm của cấu hình khác (dễ đọc nhầm)
        ns = ", ".join(f"{c} {len(pairs[s][c])}" for c in _ordered(pairs[s], CONFIG_ORDER))
        ax.set_title(f"{s}  (n: {ns})", loc="left")
        ax.set_xlabel(f"GPU-giờ (% so với {baseline})")
        # Chừa 25 % bên phải cho nhãn của điểm xa nhất; luôn thấy mốc 100 % (bằng baseline)
        xmax = max([100.0, *(p[0] for pts in pairs[s].values() for p in pts)])
        ax.set_xlim(0, xmax * 1.25)
        _comma(ax)
    # Trục tung: cận dưới không cao hơn 90 %, vì để tự co thì chênh 0,3 điểm phần trăm trông như rất lớn,
    # trong khi ngưỡng thực tiễn là 5 điểm (Thông số §6). Phía trên 100 % chừa HEADROOM cho nhãn (nhiều cấu
    # hình đạt đúng 100 %), nhưng không ghi vạch chia nào trên 100 %, vì attainment không vượt được 100 %.
    ys = [p[1] for c in pairs.values() for pts in c.values() for p in pts]
    lo = min([90.0, *ys]) - 2
    axes[0][0].set_ylim(lo, 100 + HEADROOM * (100 - lo))
    ticks = MaxNLocator(nbins=6, steps=[1, 2, 2.5, 5, 10]).tick_values(lo, 100)
    axes[0][0].yaxis.set_major_locator(FixedLocator([t for t in ticks if lo <= t <= 100]))
    axes[0][0].set_ylabel("SLO attainment (%)")
    handles = [
        Line2D([], [], ls="", marker=style(c)[1], color=style(c)[0], markersize=7, label=c)
        for c in _ordered(seen, CONFIG_ORDER)
    ]
    handles.append(Line2D([], [], color=INK_2, lw=1, ls="--", label=f"mục tiêu N1 {m.ATTAINMENT * 100:g} %"))
    fig.legend(handles=handles, loc="outside lower center", ncols=len(handles))
    fig.suptitle(title)

    # Điểm trung bình và nhãn vẽ sau cùng: cần toạ độ pixel cuối cùng (sau constrained layout) để biết điểm
    # nào trùng điểm nào và nhãn nào đè lên gì. draw_without_rendering chạy layout mà không vẽ raster.
    fig.draw_without_rendering()
    px = fig.dpi / 72  # 1 point = px pixel

    def box(ax: Any, x: float, y: float, size: float) -> Any:
        """Hộp vuông (pixel) bao một marker diện tích `size` point² của ô `ax`, kể cả viền trắng 1,2 pt."""
        cx, cy = ax.transData.transform((x, y))
        r = (math.sqrt(size) / 2 + 0.6) * px
        return Bbox.from_extents(cx - r, cy - r, cx + r, cy + r)

    for ax, s in zip(axes[0], scen, strict=True):
        means = []
        for c in _ordered(pairs[s], CONFIG_ORDER):
            pts = pairs[s][c]
            mx, my = m.mean(p[0] for p in pts), m.mean(p[1] for p in pts)
            cx, cy = ax.transData.transform((mx, my))
            means.append(_Mean(c, mx, my, (float(cx), float(cy))))
        groups = _near_groups(means, NEAR_PT * px)
        # Vật cản của nhãn: mọi điểm trung bình (đúng cỡ đã vẽ) và mọi chấm từng lượt
        obstacles = [box(ax, x, y, RUN_SIZE) for pts in pairs[s].values() for x, y in pts]
        for g in groups:
            for i, mm in enumerate(g):
                color, marker = style(mm.config)
                # Điểm sau nhỏ còn 1/4 diện tích (1/2 đường kính): giảm ít hơn thì chấm tròn vẫn che gần hết
                # tam giác bên dưới
                size = MEAN_SIZE / 4**i
                ax.scatter([mm.x], [mm.y], s=size, marker=marker, color=color, edgecolor="white",
                           lw=1.2, zorder=3 + i / 10).set_in_layout(False)  # fmt: skip
                obstacles.append(box(ax, mm.x, mm.y, size))
        frame = ax.get_window_extent()
        yn = ax.transData.transform((0, m.ATTAINMENT * 100))[1]
        xb = ax.transData.transform((100, 0))[0]
        lines = [
            Bbox.from_extents(frame.x0, yn - px, frame.x1, yn + px),  # vạch N1
            Bbox.from_extents(xb - px, frame.y0, xb + px, frame.y1),  # mốc 100 % GPU-giờ
        ]
        labels = [(g[0].x, g[0].y, ", ".join(mm.config for mm in g)) for g in groups]
        _place_labels(ax, labels, obstacles, lines)
    # Chốt layout: _save lưu ở dpi khác (PNG 200, SVG 72) và constrained layout chạy lại thì các ô dời khoảng
    # 1 pt, trong khi nhãn đã được kiểm va chạm theo vị trí cũ. Không còn layout engine thì vị trí các ô giữ
    # nguyên (theo tỷ lệ của hình), nên mọi khoảng cách tính bằng point giữ nguyên ở mọi dpi.
    fig.set_layout_engine("none")
    return fig


def _save(fig: Any, base: Path, formats: Sequence[str]) -> list[Path]:
    out = []
    base.parent.mkdir(parents=True, exist_ok=True)
    for f in formats:
        p = base.with_suffix(f".{f}")
        # Bỏ ngày giờ khỏi metadata để chạy lại trên cùng dữ liệu ra đúng cùng file (dễ so trong Git)
        meta = {"Date": None} if f == "svg" else {"Software": None} if f == "png" else {}
        fig.savefig(p, dpi=200, metadata=meta)
        out.append(p)
    plt.close(fig)
    return out


def draw_all(
    rows: Sequence[Mapping[str, Any]],
    out: Path,
    baseline: str,
    formats: Sequence[str],
    c1_configs: Sequence[str] = C1_CONFIGS,
) -> list[str]:
    """Vẽ mọi hình có đủ dữ liệu vào `out`, mỗi môi trường một bộ. Trả các dòng báo cáo (file đã ghi, hình bỏ
    qua và lý do)."""
    _setup()
    log: list[str] = []
    groups, warn = c1_groups(rows, c1_configs)
    log += warn
    n_cap: dict[tuple[Any, Any], int] = defaultdict(int)  # số mức C khác nhau của mỗi (env, repeat)
    for env, rep, _ in groups:
        n_cap[(env, rep)] += 1
    for (env, rep, cap), runs in sorted(groups.items(), key=lambda kv: tuple(map(str, kv[0]))):
        series = {c: kb2_series(Path(r["path"])) for c, r in runs.items()}
        if len({tuple(sorted(s["phases"].items())) for s in series.values()}) > 1:
            log.append(
                f"C1 ({env}, lượt {rep}): các cấu hình có pha khác nhau, nền xám theo {next(iter(series))}"
            )
        c_txt = f"{cap:g}".replace(".", ",") if _isnum(cap) else "?"
        name = f"c1-kb2-{env}-r{rep}" + (f"-c{c_txt}" if n_cap[(env, rep)] > 1 else "")
        title = f"C1 – KB2, lượt {rep} ({env}, C = {c_txt} req/s), cùng lịch gửi cho mọi cấu hình"
        log += [f"ghi {p}" for p in _save(plot_c1(series, title), out / name, formats)]

    for env in sorted({str(r["env"]) for r in rows if r.get("counted")}):
        er = [r for r in rows if str(r["env"]) == env]
        slo = cell_values(er, "slo_attainment", 100)
        if slo:
            fig = plot_bars(slo, "SLO attainment (%)", [(m.ATTAINMENT * 100, "N1 95 %")],
                            f"C2 – SLO attainment ({env})")  # fmt: skip
            log += [f"ghi {p}" for p in _save(fig, out / f"c2-slo-{env}", formats)]
        gpu = cell_values(er, "gpu_vs_baseline", 100)
        if not gpu:
            log.append(
                f"C3, C4 ({env}): bỏ qua, không có lượt {baseline} counted hoặc thiếu pods_timeline.json"
            )
            continue
        fig = plot_bars(gpu, f"GPU-giờ (% so với {baseline})", [(100, baseline), (50, "N3 50 %")],
                        f"C3 – GPU-giờ so với {baseline} ({env})")  # fmt: skip
        log += [f"ghi {p}" for p in _save(fig, out / f"c3-gpu-{env}", formats)]
        pairs = paired_values(er, "gpu_vs_baseline", "slo_attainment")
        fig = plot_c4(pairs, f"C4 – Trade-off GPU-giờ và SLO ({env})", baseline)
        log += [f"ghi {p}" for p in _save(fig, out / f"c4-tradeoff-{env}", formats)]
    return log


def main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    p.add_argument("sessions", type=Path, nargs="+", help="thư mục phiên runs/<phiên> (một hoặc nhiều)")
    p.add_argument("--out", type=Path, help="thư mục ghi hình (mặc định: <phiên đầu tiên>/figures)")
    p.add_argument("--baseline", default="S4", help="cấu hình tĩnh cấp theo đỉnh để so GPU-giờ (mặc định S4)")
    p.add_argument("--formats", default="svg,png", help="định dạng, cách nhau dấu phẩy (mặc định svg,png)")
    p.add_argument("--c1-configs", default=",".join(C1_CONFIGS), help="cấu hình vẽ ở C1 (mặc định S4,A1,A2)")
    a = p.parse_args(argv)

    res = bt.build(a.sessions, a.baseline)
    for s in res["skipped"]:
        print(f"bỏ qua {s}")
    if not any(r["counted"] for r in res["runs"]):
        print("không có lần thử hợp lệ nào để vẽ")
        return 1
    formats = [f.strip() for f in a.formats.split(",") if f.strip()]
    c1 = [c.strip() for c in a.c1_configs.split(",") if c.strip()]
    for line in draw_all(res["runs"], a.out or a.sessions[0] / "figures", a.baseline, formats, c1):
        print(line)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
