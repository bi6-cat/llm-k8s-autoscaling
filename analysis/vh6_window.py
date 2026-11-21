"""VH6: tỷ lệ request xấu theo log client quanh mốc vi phạm SLO và mốc page, cho các lượt ĐG2 có page.

Khái niệm:
    N7 (Thông số §4): cảnh báo SLO phải kêu ≤ 5 phút sau khi SLO bị vi phạm thật, và không có page giả. Page
    giả là page trong lúc tỷ lệ request xấu theo log client, trên cùng cửa sổ, < 20 %. build_tables đã tính:
      - mốc vi phạm: runs.csv slo_violation_s, lần đầu tỷ lệ xấu trên cửa sổ 1 phút (τ − 60, τ] vượt 20 %
        (metrics.slo_violation_start);
      - mốc page: alerts.csv first_s, lúc một đợt LLMSLOBurnFast (cảnh báo burn rate, severity page) bắt
        đầu firing;
      - client_bad_ratio: tỷ lệ xấu trong 5 phút trước mốc page, dùng để chấm page giả.
    Module này in thêm, cho mỗi đợt page bắt đầu TRONG lượt (bỏ đợt có firing_at_start = True, tức đang kêu
    từ lượt trước):
      - độ trễ page − vi phạm, chỉ cho đợt mà build_tables dùng làm slo_alert_s (đợt mới đầu tiên còn kêu
        tới lúc vi phạm); có thể âm nếu đợt đó kêu trước mốc vi phạm;
      - tỷ lệ xấu lớn nhất trên cửa sổ 1 phút (τ − 60, τ], cùng quy ước với mốc vi phạm. Với đợt ứng với
        slo_alert_s mà page sau mốc vi phạm, τ chạy mỗi giây từ mốc vi phạm tới mốc page: cho biết lúc cảnh
        báo còn chờ thì lỗi đã nặng tới đâu. Với đợt khác (kêu lại về sau, page trước mốc vi phạm, lượt không
        có mốc vi phạm), τ chạy trong 5 phút trước page và dòng được đánh dấu ở cuối (scan_range). τ luôn
        ≥ t0 + 60 s để cửa sổ đủ 1 phút, như metrics.slo_violation_start;
      - tỷ lệ xấu 5 phút trước page, tính lại để đối chiếu với client_bad_ratio;
      - tỷ lệ xấu của từng pha (1 − slo_attainment ở phases.csv), bỏ pha `main` (cả pha chính).
Mục đích: Tái lập các số VH6 trong nháp mục 5.5 (cột "tỷ lệ xấu lớn nhất trên 1 phút"). Trước đây các số
    này tính bằng một script chỉ có trên máy của Trình.
Tham khảo: Môi trường §13 (VH6); Thông số §4 (N7); Kiến thức nền §5.2 (burn rate)

Chạy (từ gốc repo):
    uv run --project analysis python -m analysis.vh6_window runs/v2-vm/v2-dg2
"""

from __future__ import annotations

import argparse
import bisect
import csv
from collections.abc import Sequence
from pathlib import Path

from analysis import metrics as m
from analysis.build_tables import _fmt, _json, read_session_table, session_name

PAGE_ALERT = "LLMSLOBurnFast"
MATCH_TOL_S = 0.001  # first_s (alerts.csv) và slo_alert_s (runs.csv) cùng làm tròn 6 chữ số thập phân


def _csv(path: Path) -> list[dict[str, str]]:
    with open(path, encoding="utf-8", newline="") as fh:
        return list(csv.DictReader(fh))


def max_bad_ratio(
    reqs: Sequence[m.Request], start: float, end: float, *, window_s: float = m.VIOLATION_WINDOW_S
) -> tuple[float | None, float | None]:
    """Tỷ lệ xấu lớn nhất trên cửa sổ (τ − window_s, τ], τ = start, start + 1, …, ≤ end (giây UNIX), và mốc
    τ đầu tiên đạt giá trị đó. Cùng cách chọn request (theo t_sched) với metrics.slo_violation_start.
    Không cửa sổ nào có request, hoặc start > end → (None, None)."""
    rs = sorted(reqs, key=lambda r: r.t_sched)
    ts = [r.t_sched for r in rs]
    best, at = None, None
    tau = start
    while tau <= end:
        lo, hi = bisect.bisect_right(ts, tau - window_s), bisect.bisect_right(ts, tau)
        sel = rs[lo:hi]
        if sel:
            bad = 1 - sum(r.good for r in sel) / len(sel)
            if best is None or bad > best:
                best, at = bad, tau
        tau += 1.0
    return best, at


def scan_range(violation: float | None, page: float, scored: bool) -> tuple[float, float, str]:
    """Khoảng τ (giây từ t0) để tìm tỷ lệ xấu lớn nhất của một đợt page, và nhãn in ở cuối dòng.

    `scored`: đợt này là đợt build_tables dùng làm slo_alert_s. Chỉ khi đó, và page sau mốc vi phạm, mới
    quét từ mốc vi phạm. Mọi trường hợp khác quét 5 phút trước page (cửa sổ dài của LLMSLOBurnFast), vì mốc
    vi phạm của lượt không ứng với đợt đó. Cận dưới t0 + 60 s: cửa sổ đầu tiên đủ 1 phút."""
    floor = m.VIOLATION_WINDOW_S
    if scored and violation is not None and page >= violation:
        return max(violation, floor), page, ""
    label = "page trước mốc vi phạm" if scored else "đợt khác, không ứng với slo_alert_s"
    return (
        max(page - m.PAGE_WINDOW_S + m.VIOLATION_WINDOW_S, floor),
        page,
        f" ({label}: quét 5 phút trước page)",
    )


def report(session: Path) -> str:
    name, tables = session_name(session), session / "tables"
    # runs.csv phải có dòng của phiên này (read_session_table báo lỗi nếu không); alerts.csv thì có thể không
    # có đợt nào, nên lọc tay theo cùng tên phiên
    runs = {r["run_id"]: r for r in read_session_table(session, "runs") if r["counted"] == "True"}
    pages = [
        a
        for a in _csv(tables / "alerts.csv")
        if a["session"] == name
        and a["alertname"] == PAGE_ALERT
        and a["firing_at_start"] == "False"  # đợt đang kêu từ lượt trước: không phải page của lượt này
        and a["run_id"] in runs
        and a["attempt"] == runs[a["run_id"]]["attempt"]
    ]
    phases = [x for x in _csv(tables / "phases.csv") if x["session"] == name]
    loaded: dict[tuple[str, str], tuple[dict, list[m.Request]]] = {}  # mỗi lượt chỉ đọc requests.csv một lần
    out = []
    for a in pages:
        rid, att = a["run_id"], a["attempt"]
        if (rid, att) not in loaded:
            d = session / rid / att
            lg = _json(d / "loadgen.json")
            with open(d / "requests.csv", encoding="utf-8", newline="") as fh:
                loaded[rid, att] = lg, [m.parse_request(r, lg["t0_unix"]) for r in csv.DictReader(fh)]
        lg, reqs = loaded[rid, att]
        t0 = lg["t0_unix"]
        # Lượt có page mà không có mốc vi phạm (slo_violation_s rỗng) là page giả tiềm năng: vẫn in để thấy
        v = m._float(runs[rid]["slo_violation_s"])
        sa = m._float(runs[rid].get("slo_alert_s"))
        p = float(a["first_s"])
        scored = sa is not None and abs(p - sa) < MATCH_TOL_S
        lo, hi, label = scan_range(v, p, scored)
        best, at = max_bad_ratio(reqs, t0 + lo, t0 + hi)
        b5 = m.bad_ratio(reqs, t0 + p - m.PAGE_WINDOW_S, t0 + p)
        cbr = m._float(a["client_bad_ratio"])  # build_tables tính cùng cửa sổ: hai số phải trùng nhau
        ph = [
            f"{x['phase']}={1 - float(x['slo_attainment']):.3f}"
            for x in phases
            if x["run_id"] == rid
            and x["attempt"] == att
            and x["phase"] != "main"
            and m._float(x["slo_attainment"]) is not None
        ]
        out.append(
            f"{rid:9s} vi_pham={_fmt(v, '6.1f')} page={p:6.1f} "
            f"tre={_fmt(p - v if scored and v is not None else None, '6.1f')} | "
            f"max1m={_fmt(best, '.3f')} @tau={_fmt(None if at is None else at - t0, '.1f')} | "
            f"bad5m_truoc_page={_fmt(b5, '.3f')} (alerts.csv {_fmt(cbr, '.3f')}) | "
            f"phases(bad) {' '.join(ph)} | phases={lg['phases_s']}{label}"
        )
    return "\n".join(out) if out else f"Không có đợt {PAGE_ALERT} nào bắt đầu trong các lượt của {session}"


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument(
        "session", type=Path, help="thư mục phiên ĐG2 đã chạy build_tables, ví dụ runs/v2-vm/v2-dg2"
    )
    args = ap.parse_args(argv)
    missing = [
        f for f in ("runs.csv", "alerts.csv", "phases.csv") if not (args.session / "tables" / f).exists()
    ]
    if missing:
        ap.error(f"{args.session}/tables thiếu {', '.join(missing)}: chạy analysis.build_tables trước")
    try:
        print(report(args.session))
    except ValueError as e:  # runs.csv không có dòng nào của phiên này (read_session_table)
        ap.error(str(e))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
