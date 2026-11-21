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
      - độ trễ page − vi phạm;
      - tỷ lệ xấu lớn nhất trên cửa sổ 1 phút (τ − 60, τ], với τ chạy mỗi giây từ mốc vi phạm tới mốc page,
        cùng quy ước cửa sổ với mốc vi phạm. Số này cho biết lúc cảnh báo còn chờ thì lỗi đã nặng tới đâu;
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
from analysis.build_tables import _json

PAGE_ALERT = "LLMSLOBurnFast"


def _csv(path: Path) -> list[dict[str, str]]:
    with open(path, encoding="utf-8", newline="") as fh:
        return list(csv.DictReader(fh))


def _num(s: str) -> float | None:
    return float(s) if s not in ("", "nan") else None


def _opt(x: float | None, spec: str) -> str:
    """Số → chuỗi theo `spec`; None (không có giá trị) → "-"."""
    return "-" if x is None else format(x, spec)


def max_bad_ratio(
    reqs: Sequence[m.Request], start: float, end: float, *, window_s: float = m.VIOLATION_WINDOW_S
) -> tuple[float | None, float | None]:
    """Tỷ lệ xấu lớn nhất trên cửa sổ (τ − window_s, τ], τ = start, start + 1, …, ≤ end (giây UNIX), và mốc
    τ đầu tiên đạt giá trị đó. Cùng cách chọn request (theo t_sched) với metrics.slo_violation_start.
    Không cửa sổ nào có request → (None, None)."""
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


def _own(path: Path, session: Path) -> list[dict[str, str]]:
    """Dòng của chính phiên này: build_tables chạy trên nhiều phiên thì ghi dòng của mọi phiên vào bảng của
    phiên đầu tiên, và hai phiên có thể trùng run_id."""
    return [r for r in _csv(path) if r["session"] == session.name]


def report(session: Path) -> str:
    tables = session / "tables"
    runs = {r["run_id"]: r for r in _own(tables / "runs.csv", session) if r["counted"] == "True"}
    pages = [
        a
        for a in _own(tables / "alerts.csv", session)
        if a["alertname"] == PAGE_ALERT
        and a["firing_at_start"] == "False"  # đợt đang kêu từ lượt trước: không phải page của lượt này
        and a["run_id"] in runs
        and a["attempt"] == runs[a["run_id"]]["attempt"]
    ]
    phases = _own(tables / "phases.csv", session)
    out = []
    for a in pages:
        rid = a["run_id"]
        d = session / rid / a["attempt"]
        lg = _json(d / "loadgen.json")
        t0 = lg["t0_unix"]
        with open(d / "requests.csv", encoding="utf-8", newline="") as fh:
            reqs = [m.parse_request(r, t0) for r in csv.DictReader(fh)]
        # Lượt có page nhưng không có mốc vi phạm (slo_violation_s rỗng) là page giả tiềm năng: in để thấy
        v = _num(runs[rid]["slo_violation_s"])
        p = float(a["first_s"])
        best, at = max_bad_ratio(reqs, t0 + (p if v is None else v), t0 + p)
        b5 = m.bad_ratio(reqs, t0 + p - m.PAGE_WINDOW_S, t0 + p)
        ph = [
            f"{x['phase']}={1 - float(x['slo_attainment']):.3f}"
            for x in phases
            if x["run_id"] == rid
            and x["attempt"] == a["attempt"]
            and x["phase"] != "main"
            and x["slo_attainment"] not in ("", "nan")
        ]
        out.append(
            f"{rid:9s} vi_pham={_opt(v, '6.1f')} page={p:6.1f} "
            f"tre={_opt(None if v is None else p - v, '6.1f')} | "
            f"max1m={_opt(best, '.3f')} @tau={_opt(None if at is None else at - t0, '.1f')} | "
            f"bad5m_truoc_page={_opt(b5, '.3f')} (alerts.csv {_opt(_num(a['client_bad_ratio']), '.3f')}) | "
            f"phases(bad) {' '.join(ph)} | phases={lg['phases_s']}"
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
    print(report(args.session))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
