"""LT7: kiểm chứng thuật toán HPA và trễ phản ứng trên simulator (Môi trường §19, Kiến thức nền §3.1).

Khái niệm:
    Với metric External kiểu AverageValue, mỗi lần sync HPA tính tỷ lệ r = tổng ÷ (target × số replica hiện
    có). Nếu 0,9 ≤ r ≤ 1,1 (tolerance 10%, tính cả hai đầu) thì giữ nguyên, ngược lại desired =
    ⌈tổng ÷ target⌉, rồi kẹp vào [min, max] (GetExternalPerPodMetricReplicas và Tolerances.isWithin trong
    pkg/controller/podautoscaler/replica_calculator.go, Kubernetes v1.37.0, bản của node kind).
    Khi tải tăng đột ngột, trễ từ lúc tải tới đến lúc pod mới Ready gồm các chặng nối tiếp:
      d_scrape  hey bắt đầu → lần scrape đầu tiên thấy tổng vượt (1 + tolerance) × target: chờ chu kỳ scrape
                (PodMonitor 5 s), nên nằm trong [0; 5) s.
      d_sync    lần scrape đó → HPA ghi log "Successfully rescaled", gồm hai phần:
        d_visible  scrape → giây tròn kế tiếp: KEDA hỏi Prometheus với `time=` làm tròn XUỐNG giây
                   (time.Now().UTC().Format(time.RFC3339), pkg/scalers/prometheus_scaler.go v2.21.0), nên
                   mẫu scrape lúc x,138 s chỉ được thấy từ giây x + 1: trong [0; 1) s.
        d_wait     giây đó → HPA đổi replica: chờ lần sync kế tiếp rồi xử lý xong một lần (hỏi metric qua
                   KEDA, cập nhật Deployment). HPA hẹn lần sync sau 5 s KỂ TỪ LÚC lần trước xử lý xong
                   (AddRateLimited với FixedItemIntervalRateLimiter, horizontal.go v1.37.0), nên trong
                   [0; 5 s + thời gian xử lý), với thời gian xử lý cỡ vài chục ms.
      d_create  HPA đổi số replica → pod mới được tạo (Deployment controller rồi ReplicaSet controller).
      d_ready   HPA đổi số replica → pod mới cuối cùng Ready (khởi động simulator, startupProbe chu kỳ 5 s).
    KEDA pollingInterval không nằm trên đường này: khi minReplicaCount ≥ 1, KEDA chạy câu PromQL ngay lúc HPA
    hỏi (KEDA v2.21.0 in cảnh báo này khi áp ScaledObject). Vì vậy dự đoán ≤ ~15 s của Môi trường §19, vốn
    cộng cả polling 5 s, thu lại thành d_decide = d_scrape + d_visible + d_wait < 5 + 1 + 5 = 11 s.
Mục đích: Đọc dữ liệu thô của envs/sim/tests/lt7-hpa.sh (runs/sim/lt7-<giờ>/c<C>-r<lần>/), tạo bảng mỗi lượt
    một dòng (CSV) và in bảng tóm tắt theo mức tải và theo chặng, để chép vào docs/nhat-ky/van-hanh.md.
Đồng hồ: mọi mốc thô là giờ thực (hey, Prometheus, log kube-controller-manager, pod), nhưng trên WSL2 giờ
    thực bị kéo lùi theo Windows khoảng mỗi 32 s (bước 0,5–1 s), nên hiệu hai mốc giờ thực sai đúng bằng
    các bước rơi vào giữa. Script đo lưu các lần chỉnh giờ từ journal (clock-changes.jsonl); MonoClock đổi mọi
    mốc sang đồng hồ đơn điệu, là đồng hồ HPA dùng để hẹn sync và Prometheus dùng để hẹn scrape. Kiểm cách
    đổi: sau khi đổi, hai lần scrape liền nhau của một pod phải cách đúng chu kỳ (cột scrape_gap_err, so với
    scrape_gap_err_wall trước khi đổi). Cột clock: "mono" (đã đổi), "mono?" (mốc 0, lần scrape hoặc quyết
    định của HPA rơi vào khoảng giờ thực bị lặp lại ngay sau một bước lùi, không biết thuộc đoạn nào; lượt
    đó không tính vào thống kê), "wall"
    (không có journal: máy không bị chỉnh giờ, hoặc dữ liệu cũ). Đồng hồ đơn điệu của VM chạy nhanh hơn giờ
    thật 1,6 % (đo 07/11), tức 0,08 s trên 5 s: bỏ qua.
Độ phân giải: hey và Prometheus tới ms, log kube-controller-manager tới µs (giờ UTC, như node kind); mốc của
    pod (tạo, Ready) và event chỉ tới giây (làm tròn xuống), nên d_create, d_ready sai số tới 1 s.

Chạy (từ gốc repo):
    uv run --project analysis python -m analysis.lt7_hpa runs/sim/lt7-<giờ> \\
        [--out analysis/figures/lt7-hpa.csv]
"""

from __future__ import annotations

import argparse
import json
import math
import re
from collections.abc import Sequence
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from analysis.build_tables import _json, write_csv
from analysis.metrics import mean

TOLERANCE = 0.1  # --horizontal-pod-autoscaler-tolerance, mặc định của kube-controller-manager
# systemd-resolved ghi "Clock change detected" ngay khi được báo giờ bị chỉnh (timerfd), journald đóng dấu lúc
# nhận dòng đó: chậm hơn lần chỉnh thật vài ms. Dư ra 50 ms; scrape_gap_err kiểm lại giả định này.
CHANGE_LAG_S = 0.05
DRAIN_S = 15.0  # sau hạn dừng, hey còn chờ request dở (tới ~10 s); cửa sổ của một lượt kéo thêm chừng này

COLUMNS = [
    "c",
    "rep",
    "threshold",
    "max_replicas",
    "predicted",
    "desired_end",
    "rescale_sizes",
    "total_hpa",
    "restarted",
    "formula_ok",
    "hpa_time_source",
    "d_scrape",
    "d_sync",
    "d_visible",
    "d_wait",
    "d_decide",
    "d_create",
    "d_ready",
    "clock",
    "clock_step_s",
    "scrape_gap_err_wall",
    "scrape_gap_err",
]

_KLOG = re.compile(
    r'^I(\d{2})(\d{2}) (\d{2}):(\d{2}):(\d{2})\.(\d{6}) .*"Successfully rescaled"'
    r' HPA="[^"]+" currentReplicas=(\d+) desiredReplicas=(\d+)'
)
_NEW_SIZE = re.compile(r"New size: (\d+)")


def predict_replicas(
    total: float, target: float, lo: int, hi: int, start: int = 1, tol: float = TOLERANCE
) -> int:
    """Số replica HPA dừng lại khi tổng metric giữ cố định ở `total`, bắt đầu từ `start` replica.

    Lặp đúng phép tính của mỗi lần sync tới khi không đổi nữa. Không mô phỏng giới hạn tốc độ scale-up (thêm
    100% hoặc 4 pod mỗi 15 s): với max ≤ 5 nó không bao giờ chặn bước 1 → max.
    """
    r = start
    for _ in range(hi + 2):
        ratio = total / (target * r)
        new = r if (1 - tol) <= ratio <= (1 + tol) else math.ceil(total / target)
        new = max(lo, min(hi, new))
        if new == r:
            return r
        r = new
    return r


def parse_duration(s: str | None) -> float | None:
    """'5s' → 5.0; '15s (mặc định)' → 15.0; không đọc được → None."""
    m = re.match(r"\s*(\d+(?:\.\d+)?)s", s or "")
    return float(m.group(1)) if m else None


def parse_quantity(q: str | None) -> float | None:
    """Số lượng kiểu Kubernetes: '8334m' (m = mili) → 8.334; '15' → 15.0."""
    if q is None:
        return None
    return float(q[:-1]) / 1000 if q.endswith("m") else float(q)


def parse_k8s_time(s: str) -> float:
    """'2026-11-16T09:23:56Z' → giây Unix (mốc của Kubernetes chỉ tới giây)."""
    return datetime.fromisoformat(s.replace("Z", "+00:00")).timestamp()


def rescales_from_log(lines: Sequence[str], year: int) -> list[tuple[float, int, int]]:
    """Các dòng "Successfully rescaled" của kube-controller-manager → [(mốc, replica cũ, replica mới)].

    Đầu dòng klog là `Immdd hh:mm:ss.uuuuuu`, không có năm; năm lấy từ mốc 0 của lượt, giờ là UTC.
    """
    out = []
    for line in lines:
        m = _KLOG.match(line)
        if not m:
            continue
        mo, dd, hh, mi, ss, us, cur, des = (int(g) for g in m.groups())
        t = datetime(year, mo, dd, hh, mi, ss, us, tzinfo=UTC).timestamp()
        out.append((t, cur, des))
    return sorted(out)


def rescales_from_events(doc: dict[str, Any]) -> list[tuple[float, int]]:
    """Event SuccessfulRescale của HPA → [(mốc tới giây, replica mới)], mỗi lần đổi một phần tử."""
    out = []
    for e in doc.get("items", []):
        if e.get("reason") != "SuccessfulRescale":
            continue
        m = _NEW_SIZE.search(e.get("message", ""))
        ts = e.get("firstTimestamp") or e.get("eventTime")
        if m and ts:
            # Event giống hệt nhau được gộp (count > 1); chỉ biết mốc đầu, nên nhân bản theo count
            out += [(parse_k8s_time(ts), int(m.group(1)))] * int(e.get("count") or 1)
    return sorted(out)


def a2_samples(running: dict[str, Any], waiting: dict[str, Any]) -> dict[str, list[tuple[float, float]]]:
    """Mẫu thô running + waiting của mỗi pod: {pod: [(mốc scrape, giá trị)]}.

    Hai metric lấy trong cùng một lần scrape nên cùng mốc; ghép theo bộ nhãn (trừ __name__) và mốc.
    """

    def series(doc: dict[str, Any]) -> dict[tuple, dict[float, float]]:
        out = {}
        for r in doc.get("data", {}).get("result", []):
            key = tuple(sorted((k, v) for k, v in r["metric"].items() if k != "__name__"))
            out[key] = {float(t): float(v) for t, v in r.get("values", [])}
        return out

    run, wait = series(running), series(waiting)
    out: dict[str, list[tuple[float, float]]] = {}
    for key, pts in run.items():
        w = wait.get(key, {})
        pod = dict(key).get("pod", "?")
        out.setdefault(pod, []).extend((t, v + w[t]) for t, v in pts.items() if t in w)
    return {pod: sorted(pts) for pod, pts in out.items()}


def first_above(samples: dict[str, list[tuple[float, float]]], t0: float, level: float) -> float | None:
    """Mốc của lần scrape đầu tiên (từ t0) mà một pod có running + waiting > level.

    Trước quyết định scale-up chỉ có một pod, nên giá trị một pod chính là tổng HPA thấy.
    """
    hits = [t for pts in samples.values() for t, v in pts if t >= t0 and v > level]
    return min(hits) if hits else None


class MonoClock:
    """Đổi giờ thực của VM sang đồng hồ đơn điệu (CLOCK_MONOTONIC), từ các lần chỉnh giờ ghi trong journal.

    Giữa hai lần chỉnh, giờ thực và giờ đơn điệu chạy cùng nhịp nên hiệu số (offset) không đổi. Mỗi dòng
    "Clock change detected" có cặp (giờ thực, giờ đơn điệu) lúc ghi, ngay SAU một lần chỉnh, tức offset của
    đoạn mới. Một bước lùi làm khoảng giờ thực dài bằng bước đó xuất hiện hai lần (trước và sau lần chỉnh):
    mốc rơi vào đó thì không biết thuộc đoạn nào, to_mono trả cờ chắc chắn = False.
    """

    def __init__(self, changes: Sequence[tuple[float, float]]) -> None:
        # (giờ đơn điệu đầu đoạn, offset = giờ thực − giờ đơn điệu của đoạn)
        self.seg = sorted((mono, wall - mono) for wall, mono in changes)

    @classmethod
    def from_jsonl(cls, path: Path) -> MonoClock | None:
        """Đọc clock-changes.jsonl (mỗi dòng {wall_us, mono_us}, từ journalctl -o json); rỗng → None."""
        if not path.exists():
            return None
        pairs = [
            (int(e["wall_us"]) / 1e6, int(e["mono_us"]) / 1e6)
            for e in map(json.loads, filter(str.strip, path.read_text(encoding="utf-8").splitlines()))
        ]
        return cls(pairs) if pairs else None

    def to_mono(self, wall: float) -> tuple[float | None, bool]:
        """→ (giờ đơn điệu, chắc chắn). None khi mốc nằm trước lần chỉnh đầu tiên có trong journal.

        Dòng journal được ghi sau lần chỉnh thật một chút (CHANGE_LAG_S), nên một mốc mà theo offset của đoạn
        mới thì rơi ngay trước đầu đoạn đó cũng có thể thuộc đoạn mới: coi là không chắc chắn.
        """
        hits, near = [], []
        for i, (m0, off) in enumerate(self.seg):
            m = wall - off
            m1 = self.seg[i + 1][0] if i + 1 < len(self.seg) else math.inf
            if m0 <= m < m1:
                hits.append(m)
            elif m0 - CHANGE_LAG_S <= m < m0:
                near.append(m)
        cands = hits or near
        return (cands[0], len(hits) == 1 and not near) if cands else (None, False)


def max_gap_error(times: Sequence[tuple[float | None, bool]], interval: float) -> float | None:
    """Lệch lớn nhất của khoảng cách giữa hai lần scrape liền nhau so với chu kỳ.

    `times` là [(mốc, chắc chắn)] theo thứ tự scrape; bỏ cặp có mốc không chắc chắn (không bỏ riêng mốc đó,
    vì như thế hai mốc kề nó trông như cách nhau hai chu kỳ).
    """
    gaps = [b - a for (a, ok_a), (b, ok_b) in zip(times, times[1:], strict=False) if ok_a and ok_b]
    return max(abs(g - interval) for g in gaps) if gaps else None


def _rnd(x: float | None, nd: int = 3) -> float | None:
    return None if x is None else round(x, nd)


def analyze_run(d: Path) -> dict[str, Any]:
    """Một lượt (thư mục c<C>-r<lần>/) → một dòng của bảng."""
    meta = _json(d / "meta.json")
    c, t0, dur = meta["c"], float(meta["t0"]), float(meta["dur_s"])
    thr, lo, hi = meta["threshold"], meta["min_replicas"], meta["max_replicas"]
    scrape_s = parse_duration(meta.get("scrape_interval")) or 5.0
    pred = predict_replicas(c, thr, lo, hi)
    end = t0 + dur + DRAIN_S

    # Quyết định của HPA: ưu tiên log kube-controller-manager (µs). Không có file, hoặc file không có dòng nào
    # trong cửa sổ của lượt (lượt không scale, hoặc `kubectl logs` lỗi lúc đo) thì dùng event (giây), vì
    # event lọc theo UID của HPA lượt này. Cả hai cùng rỗng = HPA không đổi replica.
    log_path = d / "hpa-rescale.log"
    rescales: list[tuple[float, int]] = []
    if log_path.exists():
        year = datetime.fromtimestamp(t0, UTC).year
        lines = log_path.read_text(encoding="utf-8").splitlines()
        rescales = [(t, des) for t, _, des in rescales_from_log(lines, year) if t0 - 1 <= t <= end]
    source = "log"
    if not rescales:
        rescales, source = rescales_from_events(_json(d / "events.json")), "event"

    status = _json(d / "hpa.json").get("status", {})
    desired_end, current_end = status.get("desiredReplicas"), status.get("currentReplicas")
    metrics = status.get("currentMetrics") or [{}]
    metric_end = parse_quantity(metrics[0].get("external", {}).get("current", {}).get("averageValue"))
    total_hpa = metric_end * current_end if metric_end is not None and current_end else None
    restarted = meta.get("restarts_after", 0) > meta.get("restarts_before", 0)

    sizes = [size for _, size in rescales]
    formula_ok = (not restarted) and desired_end == pred and sizes == ([pred] if pred != lo else [])

    row: dict[str, Any] = {
        "c": c,
        "rep": meta["rep"],
        "threshold": thr,
        "max_replicas": hi,
        "predicted": pred,
        "desired_end": desired_end,
        "rescale_sizes": " ".join(map(str, sizes)),
        "total_hpa": _rnd(total_hpa),
        "restarted": restarted,
        "formula_ok": formula_ok,
        "hpa_time_source": source,
    }
    keys = ["d_scrape", "d_sync", "d_visible", "d_wait", "d_decide", "d_create", "d_ready"]
    keys += ["clock", "clock_step_s", "scrape_gap_err_wall", "scrape_gap_err"]
    row.update(dict.fromkeys(keys))

    clock = MonoClock.from_jsonl(d / "clock-changes.jsonl")
    samples = a2_samples(_json(d / "prom-running.json"), _json(d / "prom-waiting.json"))
    # Kiểm cách đổi giờ trên các lần scrape trong cửa sổ của lượt (mọi pod, kể cả lượt không scale)
    errs_wall, errs_mono = [], []
    for pts in samples.values():
        ts = [t for t, _ in pts if t0 - scrape_s <= t <= end]
        errs_wall.append(max_gap_error([(t, True) for t in ts], scrape_s))
        if clock:
            errs_mono.append(max_gap_error([clock.to_mono(t) for t in ts], scrape_s))
    row["scrape_gap_err_wall"] = _rnd(max((e for e in errs_wall if e is not None), default=None))
    row["scrape_gap_err"] = _rnd(max((e for e in errs_mono if e is not None), default=None))
    if not rescales:
        return row

    t_hpa = rescales[0][0]
    t_scrape = first_above(samples, t0, (1 + TOLERANCE) * thr)
    # Pod mới = tạo từ giây của mốc 0 trở đi (creationTimestamp làm tròn xuống giây)
    created, ready = [], []
    for p in _json(d / "pods.json").get("items", []):
        ct = parse_k8s_time(p["metadata"]["creationTimestamp"])
        if ct < math.floor(t0):
            continue
        created.append(ct)
        for cond in p.get("status", {}).get("conditions", []):
            if cond.get("type") == "Ready" and cond.get("status") == "True":
                ready.append(parse_k8s_time(cond["lastTransitionTime"]))
    # Chỉ tính d_ready khi mọi pod mới đã Ready (mỗi pod một mốc Ready)
    all_ready = bool(ready) and len(ready) == len(created)
    walls = {
        "t0": t0,
        "scrape": t_scrape,
        # Lúc KEDA bắt đầu thấy mẫu đó: giây tròn kế tiếp theo giờ thực (KEDA gửi `time=` làm tròn xuống giây)
        "visible": float(math.ceil(t_scrape)) if t_scrape is not None else None,
        "hpa": t_hpa,
        "hpa_s": float(math.floor(t_hpa)),  # cùng độ phân giải giây với mốc của pod
        "created": min(created) if created else None,
        "ready": max(ready) if all_ready else None,
    }
    # Đổi sang đồng hồ đơn điệu; thiếu journal, hoặc có mốc nằm trước lần chỉnh đầu tiên, thì giữ giờ thực
    t, mode = dict(walls), "wall"
    if clock:
        conv = {k: clock.to_mono(w) if w is not None else (None, True) for k, w in walls.items()}
        if all(m is not None for k, (m, _) in conv.items() if walls[k] is not None):
            t = {k: m for k, (m, _) in conv.items()}
            # Chỉ xét ba mốc tới ms. Mốc của pod vốn sai số 1 s, lệch thêm một bước lùi (< 1 s) không đáng kể.
            mode = "mono" if all(conv[k][1] for k in ("t0", "scrape", "visible", "hpa")) else "mono?"

    def diff(a: str, b: str) -> float | None:
        return _rnd(t[a] - t[b]) if t[a] is not None and t[b] is not None else None

    row.update(
        d_scrape=diff("scrape", "t0"),
        d_sync=diff("hpa", "scrape"),
        d_visible=diff("visible", "scrape"),
        d_wait=diff("hpa", "visible"),
        d_decide=diff("hpa", "t0"),
        d_create=diff("created", "hpa_s"),
        d_ready=diff("ready", "hpa_s"),
        clock=mode,
        # Giờ thực − đơn điệu trên khoảng mốc 0 → quyết định; âm = đo bằng giờ thực thì ngắn đi chừng đó
        clock_step_s=_rnd((walls["hpa"] - walls["t0"]) - (t["hpa"] - t["t0"])) if mode != "wall" else None,
    )
    return row


def find_runs(session: Path) -> list[Path]:
    return sorted(p.parent for p in session.glob("c*-r*/meta.json"))


def _stats(values: Sequence[float]) -> str:
    if not values:
        return "– | – | –"
    return f"{min(values):g} | {mean(values):.2f} | {max(values):g}"


def summary(rows: Sequence[dict[str, Any]], session: Path) -> str:
    """Bảng tóm tắt dạng Markdown: số replica theo mức tải, rồi trễ theo chặng."""
    out = []
    if not rows:
        return "Không có lượt nào."
    thr, hi = rows[0]["threshold"], rows[0]["max_replicas"]
    out.append(f"Số replica theo mức tải (threshold {thr}, min 1, max {hi}):\n")
    out.append("| C | ⌈C ÷ threshold⌉ | Dự đoán (kẹp, tolerance) | desired đo được | Các lần đổi | Đúng |")
    out.append("|---|---|---|---|---|---|")
    for c in sorted({r["c"] for r in rows}):
        rs = [r for r in rows if r["c"] == c]
        des = ", ".join(str(r["desired_end"]) for r in rs)
        ch = ", ".join(r["rescale_sizes"] or "không" for r in rs)
        ok = sum(r["formula_ok"] for r in rs)
        out.append(f"| {c} | {math.ceil(c / thr)} | {rs[0]['predicted']} | {des} | {ch} | {ok}/{len(rs)} |")
    scaled = [r for r in rows if r["d_decide"] is not None and not r["restarted"]]
    up = [r for r in scaled if r["clock"] != "mono?"]
    clocks = sorted({r["clock"] for r in up})
    out.append(f"\nTrễ theo chặng, các lượt có scale-up (n = {len(up)}), giây, đồng hồ {'/'.join(clocks)}:\n")
    out.append("| Chặng | min | trung bình | max |")
    out.append("|---|---|---|---|")
    for col, name in [
        ("d_scrape", "tải tới → scrape thấy tải (d_scrape)"),
        ("d_sync", "scrape → HPA đổi replica (d_sync = d_visible + d_wait)"),
        ("d_visible", "  scrape → KEDA thấy mẫu, giây tròn kế tiếp (d_visible)"),
        ("d_wait", "  KEDA thấy mẫu → HPA đổi replica (d_wait)"),
        ("d_decide", "tải tới → HPA đổi replica (d_decide)"),
        ("d_create", "HPA đổi → pod được tạo (d_create, ±1 s)"),
        ("d_ready", "HPA đổi → pod mới Ready (d_ready, ±1 s)"),
    ]:
        out.append(f"| {name} | {_stats([r[col] for r in up if r[col] is not None])} |")
    skipped = [r for r in scaled if r["clock"] == "mono?"]
    if skipped:
        out.append(
            "\nKhông tính (mốc rơi vào khoảng giờ thực bị lặp sau một bước lùi): "
            + ", ".join(f"C={r['c']} lần {r['rep']}" for r in skipped)
        )
    stepped = [r for r in up if r["clock_step_s"]]
    if stepped:
        out.append(
            f"\n{len(stepped)}/{len(up)} lượt có bước lùi đồng hồ trong khoảng mốc 0 → quyết định "
            "(đo bằng giờ thực thì ngắn đi chừng này): "
            + ", ".join(f"C={r['c']} lần {r['rep']}: {r['clock_step_s']:+g} s" for r in stepped)
        )
    wall_err = [r["scrape_gap_err_wall"] for r in rows if r["scrape_gap_err_wall"] is not None]
    mono_err = [r["scrape_gap_err"] for r in rows if r["scrape_gap_err"] is not None]
    if mono_err:
        out.append(
            "\nKiểm cách đổi giờ: khoảng cách hai lần scrape liền nhau lệch khỏi chu kỳ tối đa "
            f"{max(wall_err) * 1000:.0f} ms theo giờ thực, "
            f"{max(mono_err) * 1000:.0f} ms sau khi đổi sang đơn điệu."
        )
    bad = [r for r in rows if r["restarted"]]
    if bad:
        out.append(
            "\nLượt không hợp lệ (pod restart giữa chừng): "
            + ", ".join(f"C={r['c']} lần {r['rep']}" for r in bad)
        )
    keda = session / "keda.json"
    if keda.exists():
        # Script đo ghi null cho metric không đọc được; in phần nào có phần đó
        k = _json(keda)
        parts = []
        if k.get("grpc_mean_s") is not None:
            parts.append(
                "KEDA xử lý mỗi lần HPA hỏi metric (gRPC GetMetrics): trung bình "
                f"{k['grpc_mean_s'] * 1000:.1f} ms ({k.get('grpc_count') or 0:.0f} lần)"
            )
        if k.get("scaler_latency_max_s") is not None:
            parts.append(f"Prometheus trả lời KEDA chậm nhất {k['scaler_latency_max_s'] * 1000:.1f} ms")
        if parts:
            out.append("\n" + "; ".join(parts) + ".")
    return "\n".join(out)


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("session", type=Path, help="thư mục runs/sim/lt7-<giờ>")
    ap.add_argument("--out", type=Path, help="ghi bảng mỗi lượt một dòng ra CSV này")
    args = ap.parse_args(argv)
    runs = find_runs(args.session)
    if not runs:
        ap.error(f"không thấy lượt nào (c<C>-r<lần>/meta.json) trong {args.session}")
    rows = [analyze_run(d) for d in runs]
    rows.sort(key=lambda r: (r["c"], r["rep"]))
    if args.out:
        write_csv(args.out, rows, COLUMNS)
    print(summary(rows, args.session))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
