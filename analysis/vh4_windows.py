"""VH4: SLO của một lượt VH4 theo ba khoảng (trước khi chặn, đang chặn, sau khi gỡ) và theo từng phút.

Khái niệm:
    VH4 (Môi trường §13) kiểm hệ thống khi mất nguồn metric: lúc đang có tải, áp một NetworkPolicy chặn KEDA
    gọi Prometheus, 5 phút sau thì gỡ. KEDA không truy vấn được thì dùng `fallback` của ScaledObject, tức
    đưa Deployment lên số replica tối đa (N6: trong ≤ 30 s). experiments/ops/vh.py ghi các mốc vào
    timeline.json, theo giây UNIX:
      block_prometheus  áp NetworkPolicy chặn
      fallback_reached  ScaledObject báo Fallback VÀ số replica đã lên tối đa
      unblocked         gỡ chặn
      signal_back       ScaledObject hết báo Fallback, tức KEDA đọc lại được Prometheus
    Tiêu chí "SLO không bị ảnh hưởng" được kiểm bằng cách so ba khoảng [t0, chặn), [chặn, gỡ), [gỡ, hết tải),
    rồi từng phút. Chỉ số tính bằng metrics.phase_stats, nên cùng định nghĩa TTFT, TPOT và request đạt SLO
    như bảng ĐG2. Request xếp vào khoảng theo lịch gửi (t_sched).
    Lưu ý: trên simulator chạy trong WSL2, đồng hồ đơn điệu của máy tạo tải chạy nhanh hơn giờ thực
    (lt5_little), nên ranh giới khoảng lệch vài giây so với mốc của timeline.json. Lượt trên VM thuê (V2)
    không bị lệch này.
Mục đích: Tái lập các số VH4 trong nháp mục 5.5 (SLO theo từng khoảng, TPOT theo phút). Trước đây các số
    này tính bằng một script chỉ có trên máy của Trình.
Tham khảo: Môi trường §13 (VH4); Thông số §4 (N6)

Chạy (từ gốc repo):
    uv run --project analysis python -m analysis.vh4_windows runs/v2-vm/ops-vh4-<giờ> [runs/ops-vh4-<giờ> …]
"""

from __future__ import annotations

import argparse
import csv
from collections.abc import Mapping
from pathlib import Path
from typing import Any

from analysis import metrics as m
from analysis.build_tables import _json

MINUTE_S = 60.0


def windows(t0: float, end: float, marks: Mapping[str, float]) -> list[tuple[str, float, float]]:
    """Ba khoảng quanh lúc chặn và gỡ, cộng cả lượt, theo giây UNIX. Thiếu mốc chặn hoặc gỡ → KeyError."""
    tb, tu = marks["block_prometheus"], marks["unblocked"]
    return [("truoc_chan", t0, tb), ("dang_chan", tb, tu), ("sau_go", tu, end), ("ca_luot", t0, end)]


def minutes(t0: float, end: float, step_s: float = MINUTE_S) -> list[tuple[float, float]]:
    """Các khoảng 1 phút liên tiếp từ t0; khoảng cuối bị cắt ở `end` nếu thời lượng không chia hết."""
    out, t = [], t0
    while t < end:
        out.append((t, min(t + step_s, end)))
        t += step_s
    return out


def fmt(s: Mapping[str, Any]) -> str:
    """Một dòng chỉ số. p99 là NaN khi khoảng có ít hơn metrics.MIN_SAMPLES_P99 request thành công."""
    return (
        f"n={s['n_sent']:5d} err={s['n_error']:3d} SLO={s['slo_attainment'] * 100:6.2f}% "
        f"TTFT p50={s['ttft_p50_s']:.3f} p95={s['ttft_p95_s']:.3f} p99={s['ttft_p99_s']:.3f} s "
        f"TPOT p50={s['tpot_p50_s'] * 1000:.1f} p95={s['tpot_p95_s'] * 1000:.1f} ms"
    )


def report(run: Path) -> str:
    """Báo cáo cho một thư mục lượt VH4 (timeline.json, load/loadgen.json, load/requests.csv)."""
    lg = _json(run / "load" / "loadgen.json")
    t0, end = lg["t0_unix"], lg["t0_unix"] + lg["duration_s"]
    # Mỗi mốc chỉ ghi một lần trong một lượt; nếu có trùng thì lấy lần cuối
    marks = {e["event"]: e["t"] for e in _json(run / "timeline.json")}
    with open(run / "load" / "requests.csv", encoding="utf-8", newline="") as fh:
        reqs = [m.parse_request(r, t0) for r in csv.DictReader(fh)]
    out = [
        f"##### {run.as_posix()}",
        f"t0={t0:.1f} dur={lg['duration_s']} rate={lg['rate_rps']} n={len(reqs)}",
    ]
    out += [f"  {k:18s} rel_t0={t - t0:8.1f} s" for k, t in marks.items()]
    for name, a, b in windows(t0, end, marks):
        out.append(f"{name:11s} [{a - t0:6.1f}, {b - t0:6.1f}) {fmt(m.phase_stats(reqs, a, b))}")
    out.append("theo phut (t tu t0):")
    for a, b in minutes(t0, end):
        out.append(f"  [{a - t0:5.0f},{b - t0:5.0f}) {fmt(m.phase_stats(reqs, a, b))}")
    return "\n".join(out)


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("runs", type=Path, nargs="+", help="thư mục lượt VH4, ví dụ runs/v2-vm/ops-vh4-<giờ>")
    args = ap.parse_args(argv)
    for run in args.runs:
        missing = [
            f for f in ("timeline.json", "load/loadgen.json", "load/requests.csv") if not (run / f).exists()
        ]
        if missing:
            ap.error(f"{run}: thiếu {', '.join(missing)}")
    print("\n".join(report(run) for run in args.runs))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
