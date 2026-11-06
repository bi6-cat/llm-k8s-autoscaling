"""Tính năng lực một replica (ĐG1, Môi trường §8) từ một phiên runner quét nhiều mức λ.

Khái niệm: ĐG1 chạy S1 (cố định 1 replica) với tải CONST ở các mức λ tăng dần. Với mỗi mức, lấy cửa sổ đo
    (bỏ `skip_s` giây đầu của phase chính, khi hàng đợi còn đang hình thành) rồi tính:
    - SLO attainment = tỉ lệ request có TTFT ≤ SLO và TPOT ≤ SLO (request lỗi tính là không đạt);
    - B = số request đồng thời trung bình: B_server từ `vllm:num_requests_running + waiting` (Prometheus),
      B_client từ log máy tạo tải (tổng thời gian các request nằm trong cửa sổ ÷ độ dài cửa sổ);
    - KV-cache, GPU util trung bình.
    C = mức λ lớn nhất còn đạt SLO (và lượt hợp lệ). B*, KV*, UTIL* là giá trị tại C.
    Kiểm tra bằng định luật Little: B ≈ λ × E2E trung bình; lệch > 15 % thì xem lại cách đo (bước 6).
Mục đích: Sinh `capacity-*.json` (C, B*, threshold A1–A3, curves) mà runner và file ma trận dùng làm target.
    Thay script tạm `runs/dg1-mini-home-20261105/dg1_fix.py`. Hàm `summarize_run` thuần, có unit test.

Chạy:
    uv run --project experiments python -m experiments.runner.capacity runs/dg1-home-05b \\
        --out experiments/capacity-home.json
"""

from __future__ import annotations

import argparse
import csv
import gzip
import json
import math
import time
from pathlib import Path
from typing import Any

TTFT_SLO_S = 2.5  # Thông số §6: TTFT ≤ 2,5 s
TPOT_SLO_S = 0.100  # Thông số §6: TPOT ≤ 100 ms
ATTAINMENT = 0.95  # N1: ≥ 95 % request đạt SLO
LITTLE_TOL = 0.15  # Môi trường §8 bước 6
A1_TARGET_PCT = 70  # Thông số §8.1: A1 cố định 70 %


def _q(a: list[float], p: float) -> float:
    """Phân vị p (0–1) theo nearest-rank; danh sách rỗng → NaN."""
    a = sorted(a)
    return a[min(len(a) - 1, int(p * (len(a) - 1) + 0.5))] if a else float("nan")


def _mean(a: list[float]) -> float:
    return sum(a) / len(a) if a else float("nan")


def summarize_run(
    requests: list[dict[str, str]],
    metrics: list[tuple[float, str, float]],
    *,
    t0_unix: float,
    rate: float,
    skip_s: float,
    duration_s: float,
) -> dict[str, Any]:
    """Thống kê một mức λ. Hàm thuần.

    requests: các dòng requests.csv (thời gian tính bằng giây kể từ đầu phase chính).
    metrics: (ts_unix, name, value) từ metrics.csv.gz.
    """
    ws, we = skip_s, duration_s
    meas = [r for r in requests if ws <= float(r["t_sched"]) < we]
    ok = [r for r in meas if not r["error"] and r["t_first"] and int(r["n_out"] or 0) > 1]
    ttft = [float(r["t_first"]) - float(r["t_send"]) for r in ok]
    tpot = [(float(r["t_last"]) - float(r["t_first"])) / (int(r["n_out"]) - 1) for r in ok]
    e2e = [float(r["t_last"]) - float(r["t_send"]) for r in ok]
    good = sum(1 for a, b in zip(ttft, tpot, strict=True) if a <= TTFT_SLO_S and b <= TPOT_SLO_S)

    # B phía client: request lỗi không có t_last thì coi như nằm trong hệ thống tới hết cửa sổ (chặn trên)
    busy = 0.0
    for r in requests:
        if not r["t_send"]:
            continue
        a = float(r["t_send"])
        b = float(r["t_last"]) if r["t_last"] else we
        busy += max(0.0, min(b, we) - max(a, ws))

    def series(name: str) -> list[float]:
        lo, hi = t0_unix + ws, t0_unix + we
        return [v for ts, n, v in metrics if n == name and lo <= ts <= hi and not math.isnan(v)]

    running, waiting = _mean(series("vllm_running")), _mean(series("vllm_waiting"))
    b_server = running + waiting
    e2e_mean = _mean(e2e)
    little = rate * e2e_mean
    return {
        "lambda_rps": rate,
        "n_measured": len(meas),
        "n_error": sum(1 for r in meas if r["error"]),
        "ttft_p50_s": _q(ttft, 0.5),
        "ttft_p95_s": _q(ttft, 0.95),
        "tpot_p50_s": _q(tpot, 0.5),
        "tpot_p95_s": _q(tpot, 0.95),
        "e2e_mean_s": e2e_mean,
        "B_client": busy / (we - ws),
        "B_server": b_server,
        "B_little": little,
        "little_ok": abs(b_server - little) <= LITTLE_TOL * max(little, 1e-9),
        "waiting_mean": waiting,
        "kv_cache_usage": _mean(series("vllm_kv_cache")),
        "gpu_util": _mean(series("gpu_util")),
        "slo_attainment": good / len(meas) if meas else float("nan"),
    }


def capacity(curves: list[dict[str, Any]]) -> dict[str, Any]:
    """C, B*, KV*, UTIL* và threshold từ các mức đã đo. Hàm thuần."""
    passing = [c for c in curves if c["valid"] and c["slo_attainment"] >= ATTAINMENT]
    if not passing:
        return {"C": None, "note": "không mức nào đạt SLO"}
    at_c = max(passing, key=lambda c: c["lambda_rps"])
    b_star, kv_star = at_c["B_server"], at_c["kv_cache_usage"]
    return {
        "C": at_c["lambda_rps"],
        "B_star": round(b_star, 1),
        "UTIL_star": round(at_c["gpu_util"], 3),
        "KV_star": round(kv_star, 3),
        "threshold": {
            "A1_gpu_util_percent": A1_TARGET_PCT,
            "A2_concurrency": round(0.8 * b_star),  # Thông số §8.1: 0,8 × B*
            "A3_kv_usage": round(0.8 * kv_star, 3),
        },
    }


def _read_metrics(path: Path) -> list[tuple[float, str, float]]:
    with gzip.open(path, "rt", newline="") as fh:
        return [(float(r["ts"]), r["name"], float(r["value"])) for r in csv.DictReader(fh)]


def load_session(session_dir: Path, skip_s: float) -> tuple[list[dict[str, Any]], dict[str, Any]]:
    """Đọc mọi lượt S1 × CONST đã `done` hoặc `invalid` (lần thử cuối) trong phiên."""
    prog = json.loads((session_dir / "progress.json").read_text(encoding="utf-8"))
    curves, meta = [], {}
    for run_id, entry in prog["runs"].items():
        if entry["status"] not in ("done", "invalid"):
            continue
        d = session_dir / run_id / entry["attempts"][-1]["dir"]
        lg = json.loads((d / "loadgen.json").read_text(encoding="utf-8"))
        if lg["scenario"] != "CONST":
            continue
        meta = meta or json.loads((d / "metadata.json").read_text(encoding="utf-8"))
        with (d / "requests.csv").open(newline="") as fh:
            reqs = list(csv.DictReader(fh))
        s = summarize_run(
            reqs,
            _read_metrics(d / "metrics.csv.gz"),
            t0_unix=lg["t0_unix"],
            rate=float(lg["rate_rps"]),
            skip_s=skip_s,
            duration_s=float(lg["duration_s"]),
        )
        checks = json.loads((d / "checks.json").read_text(encoding="utf-8"))
        s.update(run_id=run_id, valid=checks["valid"], invalid_reasons=checks["reasons"])
        curves.append(s)
    curves.sort(key=lambda c: c["lambda_rps"])
    return curves, meta


def main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    p.add_argument("session_dir", type=Path)
    p.add_argument("--out", type=Path, required=True)
    p.add_argument("--skip-s", type=float, default=60, help="bỏ N giây đầu của phase chính (mặc định 60)")
    p.add_argument("--status", default="provisional-home")
    a = p.parse_args(argv)

    curves, meta = load_session(a.session_dir, a.skip_s)
    result = {
        "status": a.status,
        "measured_at": time.strftime("%Y-%m-%d"),
        "session": a.session_dir.name,
        "env": meta.get("env"),
        "vllm": meta.get("vllm"),
        "slo": {"ttft_s": TTFT_SLO_S, "tpot_s": TPOT_SLO_S, "attainment": ATTAINMENT},
        "window": {"skip_s": a.skip_s},
        **capacity(curves),
        "curves": curves,
    }
    a.out.write_text(json.dumps(result, indent=1, ensure_ascii=False) + "\n", encoding="utf-8")
    for c in curves:
        flag = "" if c["valid"] else "  [không hợp lệ]"
        print(
            f"λ={c['lambda_rps']:>5g}  SLO {c['slo_attainment']:.3f}  TTFT p95 {c['ttft_p95_s']:.3f} s  "
            f"TPOT p95 {c['tpot_p95_s'] * 1000:.1f} ms  B {c['B_server']:.1f} (Little {c['B_little']:.1f})"
            f"  waiting {c['waiting_mean']:.1f}{flag}"
        )
    print(f"C = {result.get('C')}  B* = {result.get('B_star')}  threshold = {result.get('threshold')}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
