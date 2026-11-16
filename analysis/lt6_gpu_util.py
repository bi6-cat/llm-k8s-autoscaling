"""LT6: GPU utilization bão hoà, không tách được tải vừa với quá tải (Môi trường §19, Kiến thức nền §4.4).

Khái niệm:
    GPU utilization (cột `utilization.gpu` của nvidia-smi, metric `nvidia_smi_utilization_gpu_ratio` mà A1
    đọc) là tỷ lệ thời gian trong chu kỳ lấy mẫu của driver có ÍT NHẤT MỘT kernel đang chạy. Nó không cho biết
    GPU đang dùng bao nhiêu phần năng lực. vLLM chạy một bước decode chung cho cả batch (continuous batching),
    nên chỉ cần còn một request là GPU đã có kernel chạy liên tục. Vì vậy util ≈ P(N ≥ 1), với N là số request
    đang nằm trong hệ thống.
    Khi chưa xếp hàng, mỗi request được phục vụ song song và gần như không phụ thuộc số request khác (LT3: B
    tăng từ 2 lên 5 thì TPOT chỉ tăng 10 %). Hệ thống khi đó gần với hàng đợi M/G/∞ (vô số server): request
    đến theo Poisson thì N có phân phối Poisson với trung bình L, và L chính là đại lượng của định luật Little
    (LT5). Từ đó:
        util_pred = 1 − P(N = 0) = 1 − e^(−L)
    Công thức không có tham số tự do. Nó cho util 86 % ở L = 2, 95 % ở L = 3, 99 % ở L = 4,6, tức util bão hoà
    khi trong hệ thống mới có vài request, trong khi điểm gãy B* (LT3) ở khoảng 27. Ngược lại, tín hiệu A2 là
    chính L: tăng tuyến tính theo λ, rồi tăng vọt khi quá tải vì hàng đợi dồn lại.
    "Phân biệt được tải vừa với quá tải" nghĩa là có một ngưỡng tách được hai nhóm mức λ, tức
    max(tín hiệu ở tải vừa) < min(tín hiệu ở quá tải). Tải vừa: 0,3 C ≤ λ ≤ 0,7 C. Quá tải: λ > C, SLO không
    đạt. Bốn tín hiệu được so là bốn cấu hình của Kiến trúc §10: A1 gpu_util, A2 L_server (running + waiting),
    A3 kv_cache_usage, A4 waiting.
    Hệ quả cho A1 (threshold 70 %, tolerance 10 %): HPA giữ nguyên số replica khi util mỗi pod nằm trong
    [63 %; 77 %], tức L mỗi pod trong [0,99; 1,47] (1,47 = −ln(1 − 0,77)); trên đó thì thêm pod. Bớt pod
    khó hơn: từ r xuống r − 1 cần ⌈r × util ÷ 0,7⌉ ≤ r − 1 (với r = 4: util ≤ 52,5 %, tức tổng L ≤ 3,0).
    A2 thì dừng ở L mỗi pod ≤ 1,1 × threshold (23,1 và 25,3 với threshold 21 và 23 ở nhà). Giả sử mỗi pod
    chạy trên một GPU riêng và Service chia request ngẫu nhiên (kube-proxy): mỗi pod nhận một dòng Poisson
    λ ÷ N, nên là một M/G/∞ với L ÷ N. Khi đó A1 dừng ở L mỗi pod 1,25–1,47, còn A2 ở L mỗi pod cỡ
    threshold. Ở tổng L = 30–100, A1 cần 23–71 replica so với 2–5 của A2 (gấp 11–14 lần), tức lên tới max
    ngay từ tải nhẹ (a1_replicas).
    Sai số lấy mẫu của util: mỗi mẫu nằm trong [0; 1] nên có phương sai ≤ p(1 − p). Nếu n mẫu độc lập thì
    SE ≤ √(p(1 − p) ÷ n) (util_se), với n = cửa sổ ÷ 5 s = 24 như LT5 (mốc mẫu rơi đúng hai đầu cửa sổ thì
    capacity.py lấy được 25). Thực tế mẫu cách nhau 5 s, còn chu kỳ bận trung bình của M/G/∞ là
    (e^L − 1) ÷ λ (7,5 s ở 1,5B, λ = 1), nên các mẫu liền nhau có tương quan dương và SE thật có thể lớn hơn.
Mục đích: Tạo bảng LT6 từ file capacity-*.json của ĐG1 (envs/<env>/experiments/), mỗi mức λ một dòng (CSV):
    util đo so với util_pred, bốn tín hiệu, lần quyết định đầu tiên của A1 và A2 khi đang có 1 replica, và
    số replica mỗi cấu hình leo tới nếu chạy cùng tải trên node có --max-replicas GPU. Rồi in bảng tóm tắt và
    phép kiểm "tách được", để chép vào docs/nhat-ky/van-hanh.md. File capacity chỉ có bản tóm tắt mỗi mức
    (trung bình 24 mẫu 5 s của Prometheus), nên ở đây không có phân phối của từng mẫu. Dữ liệu thô của lượt
    A1 (V2) để PR sau.

Chạy (từ gốc repo):
    uv run --project analysis python -m analysis.lt6_gpu_util envs/home/experiments/capacity-1.5b.json \\
        envs/home/experiments/capacity.json [--max-replicas 4] [--out analysis/figures/lt6-gpu-util.csv]
"""

from __future__ import annotations

import argparse
import math
from collections.abc import Sequence
from pathlib import Path
from typing import Any

from analysis.build_tables import _json, write_csv
from analysis.lt5_little import _f, capacity_level
from analysis.lt7_hpa import TOLERANCE, hpa_desired, predict_replicas
from analysis.metrics import ATTAINMENT, NAN, STEP_S

MODERATE = (0.3, 0.7)  # dải "tải vừa" theo λ ÷ C (Môi trường §19 LT6: lượt tăng dần 0,3 → 1,5 C)
UNCLAMPED = 10**6  # max replica "vô hạn": để thấy HPA muốn bao nhiêu trước khi bị kẹp
# Tín hiệu của từng cấu hình (Kiến trúc §10): (cột trong bảng, tên cấu hình)
SIGNALS = [("gpu_util", "A1"), ("L_server", "A2"), ("kv_cache_usage", "A3"), ("waiting_mean", "A4")]

COLUMNS = [
    "source", "env", "run_id", "valid", "lambda_nominal", "C", "load", "band", "slo_attainment",
    "lambda_real", "e2e_mean_s", "L_client", "L_server", "waiting_mean", "kv_cache_usage",
    "gpu_util", "util_pred", "util_dev", "util_se", "util_z",
    "a1_target_pct", "a2_target", "a1_desired_1", "a2_desired_1",
    "max_replicas", "a1_replicas", "a2_replicas",
]  # fmt: skip


# ── Công thức (hàm thuần) ─────────────────────────────────────────────────────────────────────────────


def util_pred(l_pod: float) -> float:
    """GPU util dự đoán khi một GPU phục vụ trung bình l_pod request, chưa xếp hàng: 1 − e^(−L)."""
    return 1.0 - math.exp(-l_pod) if l_pod >= 0 else NAN


def l_for_util(u: float) -> float:
    """Nghịch đảo của util_pred: L mỗi pod để util đạt u."""
    return -math.log(1.0 - u)


def a1_replicas(l_total: float, target_pct: float, hi: int, tol: float = TOLERANCE) -> int:
    """Số replica A1 leo tới khi tổng L giữ cố định, mỗi pod một GPU, Service chia đều request.

    Lặp phép tính của mỗi lần sync HPA (lt7_hpa.hpa_desired), nhưng tổng metric đổi theo số replica: với r
    pod, tổng = 100 × r × util_pred(L ÷ r). Vì vậy không dùng được lt7_hpa.predict_replicas, vốn giữ tổng cố
    định và đi cả hai chiều. Dừng ở lần đầu HPA không muốn thêm pod. Không mô phỏng scale-down: sau khi lên,
    cửa sổ ổn định 300 s giữ khuyến nghị lớn nhất (Kiến trúc §12), nên số lớn nhất đã đạt mới là số replica
    giữ lại khi tải không đổi.
    """
    r = 1
    while r < hi:
        new = min(hi, hpa_desired(100.0 * r * util_pred(l_total / r), target_pct, r, tol))
        if new <= r:
            return r
        r = new
    return r


def band(load: float, slo: float) -> str:
    """Nhóm của một mức λ: `vừa` (0,3–0,7 C), `quá tải` (> C và SLO không đạt), còn lại `khác`."""
    if MODERATE[0] <= load <= MODERATE[1]:
        return "vừa"
    if load > 1.0 and slo < ATTAINMENT:
        return "quá tải"
    return "khác"


def separation(rows: Sequence[dict[str, Any]], key: str, valid_only: bool = False) -> dict[str, Any]:
    """Phép kiểm "tách được" của một tín hiệu: (min, max) ở mỗi nhóm, tách được không, và tỷ số
    min(quá tải) ÷ max(vừa), tức khoảng hở giữa hai nhóm (> 1 thì tách được; 0 ÷ 0 cho NaN).

    Mức không có số liệu của tín hiệu (NaN) bị bỏ và đếm ở `n_missing`. valid_only = True: chỉ lấy mức mà
    máy tạo tải đánh dấu hợp lệ, để kiểm kết luận có đổi khi bỏ các mức không hợp lệ hay không.
    """
    sel = [r for r in rows if r["valid"] or not valid_only]
    vals = {b: [r[key] for r in sel if r["band"] == b] for b in ("vừa", "quá tải")}
    n_missing = sum(math.isnan(v) for vs in vals.values() for v in vs)
    mod, over = ([v for v in vals[b] if not math.isnan(v)] for b in ("vừa", "quá tải"))
    if not mod or not over:
        return {"moderate": None, "overload": None, "separable": None, "gap": NAN, "n_missing": n_missing}
    lo, hi = min(over), max(mod)
    gap = lo / hi if hi > 0 else (math.inf if lo > 0 else NAN)
    return {
        "moderate": (min(mod), hi),
        "overload": (lo, max(over)),
        "separable": hi < lo,
        "gap": gap,
        "n_missing": n_missing,
    }


# ── Đọc dữ liệu ───────────────────────────────────────────────────────────────────────────────────────


def from_capacity(path: Path, window_s: float, max_replicas: int) -> list[dict[str, Any]]:
    """capacity-*.json của ĐG1 → mỗi mức λ một dòng.

    Mô hình util dùng L = B_client: trung bình theo thời gian số request đang chờ phía client trong cả cửa
    sổ, tính đúng trên từng request, không có sai số lấy mẫu như B_server (24 mẫu). Cột của A2 dùng B_server
    (running + waiting), vì đó là chuỗi mà A2 đọc. Ở nhà, exporter chỉ thấy 1 GPU vật lý (time-slicing), nên
    lần quyết định đầu của A1 dùng tổng = 100 × gpu_util. a1_replicas và a2_replicas chỉ tính ở mức chưa xếp
    hàng (capacity_level): khi có hàng đợi, L đo với 1 replica gồm cả phần hàng đợi tăng dần, không còn là L
    của hệ đã scale. Tín hiệu nào thiếu (null hay NaN khi chuỗi rỗng) thì các cột suy từ nó để trống.
    """
    d = _json(path)
    c_rps = float(d["C"])
    thr = d.get("threshold", {})
    a1_t = float(thr.get("A1_gpu_util_percent", 70))
    a2_t = float(thr["A2_concurrency"])
    rows = []
    for c in d.get("curves", []):
        lv = capacity_level(c, window_s)
        load = c["lambda_rps"] / c_rps
        l_cli, l_srv, util = _num(c.get("B_client")), _num(c.get("B_server")), _num(c.get("gpu_util"))
        pred = NAN if lv["queued"] else util_pred(l_cli)
        n = int(lv["window_s"] // STEP_S)
        se = math.sqrt(pred * (1 - pred) / n) if n > 0 and not math.isnan(pred) else NAN
        rows.append(
            {
                "source": path.name,
                "env": d.get("env"),
                "run_id": lv["run_id"],
                "valid": lv["valid"],
                "lambda_nominal": c["lambda_rps"],
                "C": c_rps,
                "load": load,
                "band": band(load, c["slo_attainment"]),
                "slo_attainment": c["slo_attainment"],
                "lambda_real": lv["lambda_real"],
                "e2e_mean_s": c["e2e_mean_s"],
                "L_client": l_cli,
                "L_server": l_srv,
                "waiting_mean": _num(c.get("waiting_mean")),
                "kv_cache_usage": _num(c.get("kv_cache_usage")),
                "gpu_util": util,
                "util_pred": pred,
                "util_dev": util - pred,
                "util_se": se,
                "util_z": (util - pred) / se if se > 0 else NAN,
                "a1_target_pct": a1_t,
                "a2_target": a2_t,
                "a1_desired_1": _desired(100.0 * util, a1_t, UNCLAMPED),
                "a2_desired_1": _desired(l_srv, a2_t, UNCLAMPED),
                "max_replicas": max_replicas,
                "a1_replicas": NAN if math.isnan(pred) else a1_replicas(l_cli, a1_t, max_replicas),
                "a2_replicas": NAN if lv["queued"] else _desired(l_srv, a2_t, max_replicas),
            }
        )
    return rows


def _num(v: Any) -> float:
    """Số trong JSON → float; null (thiếu số liệu) → NaN."""
    return NAN if v is None else float(v)


def _desired(total: float, target: float, hi: int) -> int | float:
    """Số replica HPA dừng lại từ 1 replica khi tổng giữ cố định; NaN nếu thiếu tổng."""
    return NAN if math.isnan(total) else predict_replicas(total, target, 1, hi)


# ── In bảng ───────────────────────────────────────────────────────────────────────────────────────────


# Cột số của bảng chữ: (tiêu đề, khoá, định dạng, độ rộng)
_CELLS = [
    ("λ", "lambda_nominal", "5.1f", 5), ("λ/C", "load", "5.2f", 5), ("SLO", "slo_attainment", "5.3f", 5),
    ("L_cli", "L_client", "6.1f", 6), ("L_srv", "L_server", "6.1f", 6), ("wait", "waiting_mean", "6.1f", 6),
    ("KV", "kv_cache_usage", "6.3f", 6), ("util", "gpu_util", "6.3f", 6), ("u_pred", "util_pred", "6.3f", 6),
    ("z", "util_z", "+5.1f", 5),
    ("A1₁", "a1_desired_1", "3d", 3), ("A2₁", "a2_desired_1", "3d", 3),
    ("A1ₙ", "a1_replicas", "3", 3), ("A2ₙ", "a2_replicas", "3", 3),
]  # fmt: skip


def summary(rows: Sequence[dict[str, Any]]) -> str:
    """Bảng chữ mỗi mức λ một dòng, rồi phép kiểm "tách được" của từng tín hiệu theo từng nguồn."""
    cols = " ".join(f"{title:>{width}}" for title, _, _, width in _CELLS)
    head = f"{'nguồn':<20} {'nhóm':<8} {cols}  ghi chú"
    out = [head, "-" * len(head)]
    for r in rows:
        nums = " ".join(f"{_f(r[key], spec):>{width}}" for _, key, spec, width in _CELLS)
        note = "" if r["valid"] else "lượt không hợp lệ"
        out.append(f"{r['source'][:20]:<20} {r['band']:<8} {nums}  {note}")
    out.append("")
    out.append(
        f"A1ₙ, A2ₙ: số replica leo tới nếu cùng tải chạy trên node {rows[0]['max_replicas']} GPU, "
        "mỗi pod một GPU (chỉ tính ở mức chưa xếp hàng)."
    )
    for src in dict.fromkeys(r["source"] for r in rows):
        sel = [r for r in rows if r["source"] == src]
        lam = {b: [r["lambda_nominal"] for r in sel if r["band"] == b] for b in ("vừa", "quá tải")}
        t = sel[0]["a1_target_pct"] / 100
        lo, hi = l_for_util(t * (1 - TOLERANCE)), l_for_util(t * (1 + TOLERANCE))
        out.append("")
        out.append(f"{src}: vừa = λ {lam['vừa']}, quá tải = λ {lam['quá tải']}")
        out.append(
            f"  A1 {t:.0%}: HPA giữ nguyên khi L mỗi pod trong [{lo:.2f}; {hi:.2f}], trên đó thì thêm pod "
            "(mô hình 1 − e^(−L))"
        )
        has_invalid = any(not r["valid"] and r["band"] != "khác" for r in sel)
        for key, cfg in SIGNALS:
            out.append(f"  {cfg} {key:<15} {_verdict(separation(sel, key))}")
            if has_invalid:
                out.append(f"     {'chỉ mức hợp lệ':<15} {_verdict(separation(sel, key, valid_only=True))}")
    return "\n".join(out)


def _verdict(s: dict[str, Any]) -> str:
    """Một dòng kết quả của separation()."""
    miss = f"  (bỏ {s['n_missing']} mức thiếu số liệu)" if s["n_missing"] else ""
    if s["separable"] is None:
        return f"thiếu một trong hai nhóm{miss}"
    (a, b), (c, e) = s["moderate"], s["overload"]
    verdict = "tách được" if s["separable"] else "KHÔNG tách được"
    return (
        f"vừa [{a:.4g}; {b:.4g}]  quá tải [{c:.4g}; {e:.4g}]  "
        f"min(quá tải) ÷ max(vừa) = {_f(s['gap'], '.4g')}  → {verdict}{miss}"
    )


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("sources", type=Path, nargs="+", help="file capacity-*.json của ĐG1")
    ap.add_argument(
        "--capacity-window-s",
        type=float,
        default=120.0,
        help="độ dài cửa sổ đo của file capacity cũ, không ghi window_s (ĐG1-mini ở nhà: 120 s)",
    )
    ap.add_argument(
        "--max-replicas",
        type=int,
        default=4,
        help="số GPU của node giả định cho cột a1_replicas, a2_replicas (VM thuê ở V1: 4)",
    )
    ap.add_argument("--out", type=Path, help="ghi bảng mỗi mức λ một dòng ra CSV này")
    args = ap.parse_args(argv)
    rows = [r for src in args.sources for r in from_capacity(src, args.capacity_window_s, args.max_replicas)]
    if not rows:
        ap.error("không có mức λ nào để tính")
    if args.out:
        write_csv(args.out, rows, COLUMNS)
    print(summary(rows))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
