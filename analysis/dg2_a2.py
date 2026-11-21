"""ĐG2: các số phụ về hành vi của A2 mà bảng của build_tables không có (chương 5, mục 5.3).

Khái niệm:
    build_tables cho mỗi lượt một dòng tóm tắt (runs.csv, phases.csv). Mục 5.3 cần thêm vài số tính thẳng
    từ dữ liệu thô của runner để giải thích vì sao A2 vẫn trượt SLO ở pha spike của KB2 dù đã lên đủ 4
    replica sau khoảng 30 s. Mọi mốc tính bằng giây kể từ t0_unix của lượt (đầu pha chính). Module in 5 phần:
      1. Mốc scale của HPA (Horizontal Pod Autoscaler): sự kiện Kubernetes `SuccessfulRescale` trong
         events.jsonl, message dạng "New size: <n>; reason: …". In cho mọi lượt có ScaledObject (A1, A2).
      2. Hàng đợi vLLM theo pod ở KB2 (cột vllm_waiting = vllm:num_requests_waiting): giá trị lớn nhất và
         khoảng thời gian có mẫu > 0. Pod mới không có hàng đợi, còn hàng đợi dồn ở pod cũ thì tồn lâu.
      3. Phần request MỚI mỗi pod nhận trong SHARE_WINDOW_S của A2 × KB2. Service của Kubernetes chọn pod
         không theo độ dài hàng đợi, nên pod cũ vẫn nhận khoảng 1/4 số request mới dù đang có hàng trăm
         request chờ. Số "đến" đếm từ access log của vLLM (logs/vllm-<pod>.log, mỗi request một dòng
         "POST /v1/chat/completions"); số "xong" = Δ vllm_success_total. Kèm phép kiểm: tổng số dòng của
         mọi pod trong [0, duration) phải bằng đúng n_sent.
         Lưu ý: không ước lượng số đến bằng Δ success + Δ(running + waiting), vì success_total không đếm
         request bị client cắt khi quá timeout, nên ước lượng đó lệch (phát hiện khi đối chiếu 21/11).
      4. Tín hiệu của A2 (tổng running + waiting của mọi pod, đúng câu PromQL của
         common/autoscaling/a2/scaledobject-a2.yaml) so với mức (max_replicas − 1) × threshold, ví dụ
         3 × 37 = 111. Ở max_replicas pod, HPA tính desired = ⌈tổng ÷ threshold⌉, nên tín hiệu ≤ mức này
         thì HPA muốn bớt 1 pod. Cửa sổ ổn định scale-down 300 s lấy desired LỚN NHẤT trong 5 phút gần nhất
         (Thông số §9.3), nên chỉ cần một mẫu vượt mức là việc bớt pod bị lùi lại. In tỷ lệ mẫu ≤ mức, mẫu
         vượt mức cuối cùng và khoảng cách lớn nhất giữa hai mẫu vượt mức liên tiếp.
      5. Request không đạt SLO trong pha spike của A2 × KB2, tách theo lúc gửi: trước hay sau lúc pod mới
         đầu tiên Ready (đầu pha spike + react_s của runs.csv). Cho biết bao nhiêu phần request xấu là do
         chờ pod mới, bao nhiêu xảy ra khi đã đủ pod. "Đạt SLO" lấy đúng metrics.Request.good.
Mục đích: Tái lập được các số trong phần nguồn của nháp mục 5.3. Trước đây các số này tính bằng một script
    chỉ có trên máy của Trình, nên Quang không kiểm lại được.
Tham khảo: Môi trường §14.2 (định dạng runs/), §15; Thông số §7 (KB2, KB3), §9.3 (behavior của HPA)

Chạy (từ gốc repo):
    uv run --project analysis python -m analysis.dg2_a2 runs/v2-vm/v2-dg2
"""

from __future__ import annotations

import argparse
import csv
import json
import math
import re
from collections import defaultdict
from collections.abc import Iterable, Mapping, Sequence
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Any

from analysis import metrics as m
from analysis.build_tables import _json, read_metrics

CONFIG = "A2"  # cấu hình được phân tích ở phần 3–5
# Phần 3, KB2: từ lúc cả 4 pod đã Ready (≈ 320 s) tới trước lúc hàng đợi của pod cũ tan (≈ 640–650 s, phần 2)
SHARE_WINDOW_S = (360.0, 600.0)
# Phần 4: KB2 lấy đoạn cuối pha spike, sau khi hàng đợi cũ đã tan, tới lúc tải giảm (840 s); KB3 lấy cả pha
# sustain [300; 1020) s (Thông số §7). Đây là các đoạn mà A2 đã ở 4 replica và tải không đổi.
SIGNAL_WINDOWS_S = {"KB2": (700.0, 840.0), "KB3": (300.0, 1020.0)}
NEW_SIZE = re.compile(r"New size: (\d+)")
CHAT_POST = "POST /v1/chat/completions"
# Giờ ở đầu mỗi dòng `kubectl logs --timestamps`: RFC 3339, UTC, phần lẻ tới nano giây
# (2026-11-18T10:41:57.435498299Z). Tách phần lẻ riêng vì datetime chỉ giữ tới micro giây.
LOG_TIME = re.compile(r"(\d{4}-\d\d-\d\dT\d\d:\d\d:\d\d)(?:\.(\d+))?Z")


@dataclass(frozen=True)
class Run:
    """Một lượt đã được tính (`counted`) trong runs.csv, kèm các pha trong loadgen.json."""

    run_id: str
    config: str
    config_type: str  # "scaledobject" (A1, A2) hoặc "static" (S1, S4)
    scenario: str
    dir: Path  # <phiên>/<run_id>/attempt-<n>
    t0: float  # t0_unix: giây UNIX lúc bắt đầu pha chính
    duration_s: float
    n_sent: int
    react_s: float | None  # N2a: từ lúc tải tăng tới khi pod mới đầu tiên Ready (chỉ KB2)
    threshold: float | None  # threshold của ScaledObject; A1 (GPU util) không có trong runs.csv
    max_replicas: int | None
    phases: dict[str, tuple[float, float]]


def _num(s: str) -> float | None:
    return float(s) if s not in ("", "nan") else None


def load_runs(session: Path) -> list[Run]:
    """tables/runs.csv của build_tables (chỉ lần thử `counted`) + phases_s của loadgen.json, theo run_id."""
    with open(session / "tables" / "runs.csv", encoding="utf-8", newline="") as fh:
        rows = [r for r in csv.DictReader(fh) if r["counted"] == "True"]
    out = []
    for r in sorted(rows, key=lambda r: r["run_id"]):
        d = session / r["run_id"] / r["attempt"]
        mx = _num(r["max_replicas"])
        out.append(
            Run(
                run_id=r["run_id"],
                config=r["config"],
                config_type=r["config_type"],
                scenario=r["scenario"],
                dir=d,
                t0=float(r["t0_unix"]),
                duration_s=float(r["duration_s"]),
                n_sent=int(r["n_sent"]),
                react_s=_num(r["react_s"]),
                threshold=_num(r["threshold"]),
                max_replicas=None if mx is None else int(mx),
                phases={k: (a, b) for k, (a, b) in _json(d / "loadgen.json")["phases_s"].items()},
            )
        )
    return out


def _ratio(num: float, den: float) -> float:
    return num / den if den else m.NAN


def pod_suffix(pod: str) -> str:
    """vllm-757d499694-7krwm → 7krwm: phần ngẫu nhiên cuối tên pod, đủ phân biệt các pod của một lượt."""
    return pod.rsplit("-", 1)[-1]


def iso_unix(s: str) -> float:
    """Giờ ISO 8601 của Kubernetes ("2026-11-18T10:51:01Z") → giây UNIX."""
    return datetime.fromisoformat(s.replace("Z", "+00:00")).timestamp()


# ── 1. Mốc scale ──────────────────────────────────────────────────────────────────────────────────────


def rescales(events: Iterable[Mapping[str, Any]], t0: float) -> list[tuple[float, int]]:
    """Sự kiện SuccessfulRescale → [(giây từ t0, số replica mới)], theo thời gian."""
    out = []
    for e in events:
        hit = NEW_SIZE.search(e.get("message", "")) if e.get("reason") == "SuccessfulRescale" else None
        if hit:
            out.append((iso_unix(e["time"]) - t0, int(hit.group(1))))
    return sorted(out)


# ── 2 và 4. Chuỗi metric theo pod ─────────────────────────────────────────────────────────────────────


def by_pod(rows: Iterable[tuple[float, dict[str, str], float]], t0: float) -> dict[str, dict[int, float]]:
    """Các mẫu của một metric (một dòng read_metrics) → {pod: {giây từ t0: giá trị}}.

    Làm tròn tới giây: query_range của runner trả mọi chuỗi trên cùng lưới 5 s, nên làm tròn chỉ để các pod
    và các metric khớp mốc với nhau khi cộng, và in gọn. Hai mẫu không thể rơi vào cùng một giây."""
    out: dict[str, dict[int, float]] = defaultdict(dict)
    for ts, labels, v in rows:
        out[labels.get("pod", "?")][round(ts - t0)] = v
    return out


def positive_span(series: Mapping[int, float]) -> tuple[float, int | None, int | None]:
    """(giá trị lớn nhất, mốc đầu và mốc cuối có giá trị > 0); không mẫu nào > 0 thì hai mốc là None."""
    pos = [t for t, v in series.items() if v > 0]
    return max(series.values(), default=m.NAN), min(pos, default=None), max(pos, default=None)


def value_near(series: Mapping[int, float], t: float) -> float:
    """Giá trị của mẫu gần mốc t nhất (chuỗi lấy mẫu 5 s nên lệch tối đa 2,5 s)."""
    return series[min(series, key=lambda x: abs(x - t))]


def signal(met: Mapping[str, Sequence[tuple[float, dict[str, str], float]]], t0: float) -> dict[int, float]:
    """Tín hiệu A2 mỗi mốc = Σ_pod (running + waiting). Pod thiếu một trong hai metric ở mốc đó thì tính 0,
    như `or vector(0)` trong câu PromQL của A2."""
    total: dict[int, float] = defaultdict(float)
    for name in ("vllm_running", "vllm_waiting"):
        for series in by_pod(met.get(name, []), t0).values():
            for t, v in series.items():
                total[t] += v
    return dict(total)


def signal_stats(sig: Mapping[int, float], a: float, b: float, level: float) -> dict[str, Any]:
    """Thống kê tín hiệu trên [a, b) so với mức `level` (phần 4)."""
    ts = sorted(t for t in sig if a <= t < b)
    v = [sig[t] for t in ts]
    hi = [t for t in ts if sig[t] > level]
    return {
        "n": len(v),
        "min": min(v, default=m.NAN),
        "mean": _ratio(sum(v), len(v)),
        "max": max(v, default=m.NAN),
        "frac_le": _ratio(sum(1 for x in v if x <= level), len(v)),
        "last_above": hi[-1] if hi else None,
        "max_gap_above": max((y - x for x, y in zip(hi, hi[1:], strict=False)), default=None),
    }


# ── 3. Request mới mỗi pod nhận ───────────────────────────────────────────────────────────────────────


def log_time(line: str) -> float | None:
    """Giờ ở đầu một dòng log → giây UNIX; dòng không bắt đầu bằng giờ (log nhiều dòng) → None."""
    hit = LOG_TIME.match(line)
    if not hit:
        return None
    return iso_unix(hit.group(1) + "Z") + float("0." + (hit.group(2) or "0"))


def arrivals(lines: Iterable[str], t0: float) -> list[float]:
    """Mốc (giây từ t0) của mọi request chat vào một pod, theo access log của uvicorn (server HTTP của vLLM).

    Với stream, uvicorn ghi dòng này lúc gửi header phản hồi, trước token đầu tiên, nên mốc này gần lúc
    request vào pod chứ không phải lúc xong. Request warm-up (trước t0) vẫn có trong log; lọc theo cửa sổ."""
    out = []
    for line in lines:
        if CHAT_POST in line and (t := log_time(line)) is not None:
            out.append(t - t0)
    return out


def request_share(run: Run, window: tuple[float, float] = SHARE_WINDOW_S) -> dict[str, Any]:
    """Phần 3 cho một lượt: số request gửi trong cửa sổ; mỗi pod: số đến, số xong, hàng đợi đầu và cuối."""
    a, b = window
    with open(run.dir / "requests.csv", encoding="utf-8", newline="") as fh:
        reqs = [m.parse_request(r, run.t0) for r in csv.DictReader(fh)]
    sent = sum(1 for r in reqs if r.t_send is not None and a <= r.t_send - run.t0 < b)
    arr: dict[str, list[float]] = {}
    for p in sorted((run.dir / "logs").glob("vllm-*.log")):
        with open(p, encoding="utf-8", errors="replace") as fh:
            arr[p.stem] = arrivals(fh, run.t0)
    met = read_metrics(run.dir / "metrics.csv.gz")
    done = by_pod(met.get("vllm_success_total", []), run.t0)
    wait = by_pod(met.get("vllm_waiting", []), run.t0)

    def first_sample(p: str) -> float:
        return min(done[p], default=math.inf) if p in done else math.inf

    pods = []
    # Xếp pod theo mẫu metric đầu tiên: pod cũ (có từ trước pha chính) đứng đầu, rồi tới các pod mới
    for pod in sorted(set(arr) | set(done), key=lambda p: (first_sample(p), p)):
        n_arr = sum(1 for t in arr[pod] if a <= t < b) if pod in arr else None
        n_done = value_near(done[pod], b) - value_near(done[pod], a) if pod in done else None
        w = wait.get(pod)
        pods.append(
            {
                "pod": pod,
                "arrived": n_arr,
                "done": n_done,
                "wait_start": value_near(w, a) if w else None,
                "wait_end": value_near(w, b) if w else None,
            }
        )
    total = sum(sum(1 for t in ts if 0 <= t < run.duration_s) for ts in arr.values())
    return {"sent": sent, "log_total": total, "n_sent": run.n_sent, "window_s": b - a, "pods": pods}


# ── 5. Request xấu trước và sau lúc pod mới Ready ─────────────────────────────────────────────────────


def bad_split(reqs: Sequence[m.Request], start: float, end: float, ready: float) -> dict[str, Any]:
    """Request có lịch gửi trong [start, end) (giây UNIX, như metrics.in_window): số request, SLO attainment,
    và số request xấu gửi trước / từ mốc `ready`. Request không gửi được (t_send rỗng) xếp theo t_sched."""
    sel = m.in_window(reqs, start, end)
    bad = [r for r in sel if not r.good]
    before = sum(1 for r in bad if (r.t_sched if r.t_send is None else r.t_send) < ready)
    return {
        "n": len(sel),
        "slo": _ratio(len(sel) - len(bad), len(sel)),
        "before": before,
        "after": len(bad) - before,
    }


# ── In báo cáo ────────────────────────────────────────────────────────────────────────────────────────


def _pct(x: float | None) -> str:
    return "?" if x is None else f"{x:.1%}"


def _n(x: float | None) -> str:
    return "?" if x is None else f"{x:.0f}"


def report(session: Path) -> str:
    runs = load_runs(session)
    out = ["## 1. SuccessfulRescale (mốc s -> replica)"]
    for r in runs:
        if r.config_type == "scaledobject":
            with open(r.dir / "events.jsonl", encoding="utf-8") as fh:
                ev = rescales((json.loads(line) for line in fh if line.strip()), r.t0)
            out.append(
                f"{r.run_id} duration {r.duration_s} : " + (" ".join(f"{t:.0f}->{n}" for t, n in ev) or "-")
            )

    out.append("\n## 2. vllm_waiting theo pod (KB2)")
    for r in (r for r in runs if r.scenario == "KB2"):
        parts = []
        for pod, s in by_pod(read_metrics(r.dir / "metrics.csv.gz").get("vllm_waiting", []), r.t0).items():
            mx, lo, hi = positive_span(s)
            span = f" >0 trong [{lo};{hi}] = {hi - lo} s" if lo is not None and hi is not None else ""
            parts.append(f"{pod_suffix(pod)} max={mx:.0f}{span}")
        out.append(f"{r.run_id} " + " ; ".join(parts))

    a, b = SHARE_WINDOW_S
    out.append(f"\n## 3. Phần request mới mỗi pod nhận, [{a:.0f}; {b:.0f}) s, {CONFIG} × KB2")
    for r in (r for r in runs if r.config == CONFIG and r.scenario == "KB2"):
        sh = request_share(r)
        parts = []
        for p in sh["pods"]:
            arr, done = p["arrived"], p["done"]
            rate = "?" if done is None else f"{done / sh['window_s']:.2f}"
            parts.append(
                f"{pod_suffix(p['pod'])}: đến {_n(arr)} ({_pct(None if arr is None else arr / sh['sent'])}), "
                f"xong {_n(done)} ({rate} req/s), "
                f"đến/xong {_pct(None if arr is None or not done else arr / done)}, "
                f"chờ {_n(p['wait_start'])}->{_n(p['wait_end'])}"
            )
        out.append(
            f"{r.run_id} gửi {sh['sent']} (log cả lượt {sh['log_total']} = n_sent {sh['n_sent']} ) | "
            + " ; ".join(parts)
        )

    out.append("\n## 4. Tín hiệu A2 = tổng running + waiting")
    for r in runs:
        win = SIGNAL_WINDOWS_S.get(r.scenario)
        if r.config != CONFIG or win is None or r.threshold is None or r.max_replicas is None:
            continue
        level = (r.max_replicas - 1) * r.threshold
        s = signal_stats(signal(read_metrics(r.dir / "metrics.csv.gz"), r.t0), *win, level)
        out.append(
            f"{r.run_id} [{win[0]:.0f};{win[1]:.0f}) n={s['n']} min={s['min']:.0f} tb={s['mean']:.1f} "
            f"max={s['max']:.0f} tỷ lệ mẫu ≤ {level:.0f}: {s['frac_le']:.0%}; mẫu > {level:.0f} cuối "
            f"{'-' if s['last_above'] is None else s['last_above']} s, khoảng cách lớn nhất giữa hai mẫu "
            f"> {level:.0f}: {s['max_gap_above']} s"
        )

    out.append(
        f"\n## 5. Request không đạt SLO trong pha spike, {CONFIG} × KB2: "
        "gửi trước / sau lúc pod mới đầu tiên Ready"
    )
    for r in (r for r in runs if r.config == CONFIG and r.scenario == "KB2"):
        if r.react_s is None:
            out.append(f"{r.run_id} không có react_s (chưa có pod mới Ready): bỏ")
            continue
        a, b = r.phases["spike"]
        ready = a + r.react_s
        with open(r.dir / "requests.csv", encoding="utf-8", newline="") as fh:
            reqs = [m.parse_request(x, r.t0) for x in csv.DictReader(fh)]
        s = bad_split(reqs, r.t0 + a, r.t0 + b, r.t0 + ready)
        nb = s["before"] + s["after"]
        out.append(
            f"{r.run_id} pod mới Ready lúc {ready:.1f} s; n={s['n']} SLO={s['slo']:.4f}; không đạt: "
            f"trước {s['before']} ({_pct(_ratio(s['before'], nb))}), "
            f"sau {s['after']} ({_pct(_ratio(s['after'], nb))})"
        )
    return "\n".join(out)


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument(
        "session", type=Path, help="thư mục phiên ĐG2 đã chạy build_tables, ví dụ runs/v2-vm/v2-dg2"
    )
    args = ap.parse_args(argv)
    if not (args.session / "tables" / "runs.csv").exists():
        ap.error(f"không thấy {args.session}/tables/runs.csv: chạy analysis.build_tables trước")
    print(report(args.session))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
