"""LT5: kiểm chứng định luật Little trên dữ liệu đã đo (Môi trường §19, Kiến trúc §10.2).

Khái niệm:
    Định luật Little: ở trạng thái dừng, số request trung bình đang nằm trong hệ thống L bằng tốc độ đến λ
    nhân thời gian lưu lại trung bình W, tức L = λ × W. Ở đây "hệ thống" là mọi pod vLLM cộng lại, "nằm
    trong hệ thống" là đang chạy (running) hoặc đang xếp hàng (waiting), W là E2E = t_last − t_send.
    A2 dùng chính L (tổng running + waiting) làm tín hiệu scale, nên LT5 kiểm hai điều: Prometheus đo đúng L
    (so với log máy tạo tải), và L tỷ lệ với λ theo đúng W đo được.

    Trên một cửa sổ hữu hạn [a, b), T = b − a, với mỗi request i có khoảng [s_i, e_i] (gửi → xong), đẳng
    thức sau đúng tuyệt đối, không cần trạng thái dừng:
        L_client = λ × W + edge,   edge = (vào − tràn) ÷ T
      L_client  trung bình theo thời gian của số request đang bay phía client = Σ_i |[s_i, e_i] ∩ [a, b)| ÷ T
      λ         λ_thực = số request gửi trong cửa sổ ÷ T (không dùng λ danh định: ở λ = 1 trong 120 s, dao
                động Poisson đã là ±9 %)
      W         E2E trung bình của chính các request đó
      vào       tổng thời gian mà các request gửi trước a còn nằm lại trong cửa sổ
      tràn      tổng thời gian mà các request gửi trong cửa sổ còn nằm lại sau b
    Ở trạng thái dừng, vào ≈ tràn nên L ≈ λW. Khi hàng đợi đang tăng thì tràn > vào, nên L < λW (edge âm).

    L_server = trung bình các mẫu Σ_pod (vllm:num_requests_running + vllm:num_requests_waiting), mỗi mẫu
    cách nhau 5 s (query_range của runner). L_server lệch L_client vì hai nguồn:
      - Lấy mẫu: cứ 5 s mới có một ảnh chụp. L_client_sampled đếm request đang bay phía client ĐÚNG tại
        các mốc mẫu đó, nên L_client_sampled − L_client là sai số thuần tuý do lấy mẫu. Sai số chuẩn dự
        đoán (se_sampling) lấy theo hàng đợi M/G/∞ (chưa xếp hàng): số request trong hệ thống có phân phối
        Poisson, phương sai bằng trung bình λW, và khi thời gian phục vụ gần như cố định thì hiệp phương
        sai ở độ trễ τ là λ·(W − τ)+. Trung bình n mẫu cách nhau `step` có
        Var ≈ (λ ÷ n) × Σ_k (W − |k|·step)+, với k chạy trên mọi số nguyên.
        Khi W < step, công thức thu về L ÷ n: mẫu gần như độc lập.
      - Định nghĩa và thời điểm: server bắt đầu đếm khi request vào engine (sau HTTP, port-forward,
        tokenize) và thôi đếm khi sinh xong token cuối. Mẫu query_range là giá trị của lần scrape gần nhất
        trước mốc, nên trễ tới 5 s. L_server − L_client_sampled là phần chênh này.

    Request lỗi (timeout, bị từ chối kết nối) không cho biết lúc nó thật sự rời server, nên mọi cửa sổ từ
    request lỗi đầu tiên của lượt trở đi bị đánh dấu applicable = False. W và L_client chỉ tính trên request
    thành công.
Đồng hồ: máy tạo tải đo mốc request bằng đồng hồ đơn điệu kể từ t0_unix, còn Prometheus đóng dấu mẫu bằng
    giờ thực. Trên WSL2 (simulator kind ở máy Trình), đồng hồ đơn điệu chạy nhanh hơn giờ thực k lần, với
    k đổi theo mỗi lần VM khởi động (1,0162 ngày 07/11; 1,0188 chiều 16/11; 1,028–1,038 sáng 16/11), nên
    sau 24 phút log client đã lệch (k − 1) × 1440 s = 23–55 s so với Prometheus. λ × W không đổi (W dài
    ra k lần, λ nhỏ đi k lần), nhưng cửa sổ client và cửa sổ server không còn trùng nhau, nên pha chuyển
    tiếp (đầu pha `drop`) lệch mạnh. Hậu tố `@k` của nguồn đổi mốc client sang giờ thực (to_wall). Cận
    của k cho từng lượt (clock_rate_bounds) lấy từ mốc của runner, không dùng Prometheus, nên không bị lập
    luận vòng.
Mục đích: Tạo bảng LT5, mỗi cửa sổ một dòng (CSV), từ hai loại nguồn:
    - thư mục phiên runner (runs/<phiên>/<run_id>/attempt-<n>/): đủ dữ liệu thô, mỗi pha của kịch bản một
      dòng (KB2 thêm dòng `main` cho cả pha chính);
    - file capacity-*.json của ĐG1 (envs/<env>/experiments/): chỉ có bản tóm tắt mỗi mức λ, nên chỉ tính
      lại được λ_thực = n_measured ÷ độ dài cửa sổ, L_pred và độ lệch; edge và L_client_sampled để trống.
    Rồi in bảng tóm tắt để chép vào docs/nhat-ky/van-hanh.md.

Chạy (từ gốc repo):
    uv run --project analysis python -m analysis.lt5_little runs/<phiên>[@k] \\
        envs/home/experiments/capacity.json [--capacity-window-s 120] [--out analysis/figures/lt5-little.csv]
"""

from __future__ import annotations

import argparse
import bisect
import csv
import math
from collections import defaultdict
from collections.abc import Iterable, Sequence
from dataclasses import replace
from pathlib import Path
from typing import Any

from analysis import metrics as m
from analysis.build_tables import _json, find_attempts, read_metrics, write_csv

STEP_S = m.STEP_S  # bước query_range của runner (5 s, một nguồn ở metrics.py)
LITTLE_TOL = 0.15  # Môi trường §19 LT5: lệch < 15 %
NAN = m.NAN
# Runner hỏi file DONE của máy tạo tải theo vòng: `kubectl get` + `kubectl exec` rồi ngủ 10 s
# (experiments/runner/loadjob.py). Ca chậm nhất: DONE xuất hiện ngay sau một lần `exec`, nên runner chỉ thấy
# nó sau 10 s ngủ cộng một lượt get + exec nữa; lấy dư 5 s mỗi lần gọi kubectl (kind trong WSL2 lúc tải
# cao), cộng thời gian máy tạo tải ghi file kết quả sau khi đo xong wall_s (< 1 s).
DONE_POLL_MAX_S = 20.0
CLOCK_MARGIN_S = 1.0  # giờ thực của pod máy tạo tải và của runner có thể lệch nhau cỡ 1 s (WSL2 kéo giờ)
# waiting trung bình từ 1 trở lên = đã có hàng đợi: M/G/∞ không còn đúng, nên không tính se_sampling và z
QUEUE_MIN = 1.0

COLUMNS = [
    "source", "env", "run_id", "attempt", "valid", "window", "start_s", "end_s", "lambda_nominal",
    "clock_rate", "clock_rate_min", "clock_rate_max",
    "n_sent", "n_error", "applicable",
    "lambda_real", "e2e_mean_s", "L_pred",
    "L_client", "edge", "L_client_sampled", "L_server", "waiting_mean", "n_samples",
    "se_sampling", "dev_client", "dev_server", "z_server",
]  # fmt: skip


# ── Công thức (hàm thuần) ─────────────────────────────────────────────────────────────────────────────


def occupancy_se(lam: float, w: float, n: int, step_s: float = STEP_S) -> float:
    """Sai số chuẩn của trung bình n mẫu số request trong hệ thống, theo M/G/∞ với thời gian phục vụ ≈ W.

    Var = (λ ÷ n) × Σ_k (W − |k|·step)+ (xem docstring đầu file). Chỉ đúng khi chưa xếp hàng (waiting ≈ 0)
    và cửa sổ dài hơn W nhiều. Khi có hàng đợi, số này chỉ cho biết bậc độ lớn.
    """
    if n <= 0 or not lam > 0 or not w > 0:
        return NAN
    s = w + 2 * sum(w - k * step_s for k in range(1, int(w // step_s) + 1) if w > k * step_s)
    return math.sqrt(lam * s / n)


def client_occupancy(intervals: Sequence[tuple[float, float]], a: float, b: float) -> dict[str, float]:
    """Các thành phần của đẳng thức L_client = λ × W + (vào − tràn) ÷ T trên cửa sổ [a, b).

    intervals: [(s_i, e_i)] của các request đã xong (giây UNIX). Trả n (số request gửi trong cửa sổ),
    lam, w, L_client, edge, carry_in (vào), spill_out (tràn).
    """
    t = b - a
    arrived = [(s, e) for s, e in intervals if a <= s < b]
    carry_in = sum(max(0.0, min(e, b) - a) for s, e in intervals if s < a)
    spill_out = sum(max(0.0, e - b) for _, e in arrived)
    busy = sum(max(0.0, min(e, b) - max(s, a)) for s, e in intervals)
    n = len(arrived)
    return {
        "n": n,
        "lam": n / t if t > 0 else NAN,
        "w": m.mean(e - s for s, e in arrived),
        "L_client": busy / t if t > 0 else NAN,
        "edge": (carry_in - spill_out) / t if t > 0 else NAN,
        "carry_in": carry_in,
        "spill_out": spill_out,
    }


def in_flight(intervals: Sequence[tuple[float, float]], ts: Iterable[float]) -> list[int]:
    """Số request đang bay phía client (s ≤ t < e) tại từng mốc t: #(s ≤ t) − #(e ≤ t), vì luôn có s ≤ e."""
    starts = sorted(s for s, _ in intervals)
    ends = sorted(e for _, e in intervals)
    return [bisect.bisect_right(starts, t) - bisect.bisect_right(ends, t) for t in ts]


def server_series(met: dict[str, list[tuple[float, dict[str, str], float]]]) -> list[tuple[float, float]]:
    """Σ_pod (running + waiting) tại mỗi mốc query_range, sắp theo thời gian.

    Mỗi pod là một chuỗi riêng (nhãn `pod`). Pod chưa có hoặc đã bị xoá thì không có mẫu ở mốc đó, tức
    đóng góp 0; Prometheus vẫn trả mẫu cũ trong 5 phút nếu một lần scrape bị lỡ, nên không có lỗ giả.
    """
    total: dict[float, float] = defaultdict(float)
    for name in ("vllm_running", "vllm_waiting"):
        for ts, _, v in met.get(name, []):
            total[ts] += v
    return sorted(total.items())


def little_window(
    reqs: Sequence[m.Request],
    server: Sequence[tuple[float, float]],
    waiting: Sequence[tuple[float, float]],
    a: float,
    b: float,
    *,
    first_error_send: float | None,
) -> dict[str, Any]:
    """Một cửa sổ [a, b) (giây UNIX) → các cột LT5. Hàm thuần.

    server: chuỗi Σ_pod (running + waiting); waiting: chuỗi Σ_pod waiting (để biết có hàng đợi không).
    first_error_send: lúc gửi của request lỗi đầu tiên trong lượt (None nếu không có).
    """
    ok = [r for r in reqs if not r.error and r.t_send is not None and r.t_last is not None]
    intervals = [(r.t_send, r.t_last) for r in ok]
    c = client_occupancy(intervals, a, b)
    samples = [(t, v) for t, v in server if a <= t < b]
    sampled = in_flight(intervals, (t for t, _ in samples))
    l_server = m.mean(v for _, v in samples)
    pred = c["lam"] * c["w"]
    wait = m.mean(v for t, v in waiting if a <= t < b)
    se = occupancy_se(c["lam"], c["w"], len(samples)) if not wait >= QUEUE_MIN else NAN
    return {
        "n_sent": sum(1 for r in reqs if r.t_send is not None and a <= r.t_send < b),
        "n_error": sum(1 for r in reqs if r.error and r.t_send is not None and a <= r.t_send < b),
        "applicable": first_error_send is None or first_error_send >= b,
        "lambda_real": c["lam"],
        "e2e_mean_s": c["w"],
        "L_pred": pred,
        "L_client": c["L_client"],
        "edge": c["edge"],
        "L_client_sampled": m.mean(float(x) for x in sampled),
        "L_server": l_server,
        "waiting_mean": wait,
        "n_samples": len(samples),
        "se_sampling": se,
        **_deviations(c["L_client"], l_server, pred, se),
    }


def _deviations(l_client: float, l_server: float, pred: float, se: float) -> dict[str, float]:
    ok = pred > 0 and not math.isnan(pred)
    return {
        "dev_client": l_client / pred - 1 if ok else NAN,
        "dev_server": l_server / pred - 1 if ok else NAN,
        "z_server": (l_server - pred) / se if ok and se > 0 else NAN,
    }


# ── Đọc nguồn ─────────────────────────────────────────────────────────────────────────────────────────


def clock_rate_bounds(wall_s: float, t0_unix: float, t_main_end: float) -> tuple[float, float]:
    """Cận của tốc độ đồng hồ máy tạo tải (k) từ một lượt runner, không dùng dữ liệu Prometheus.

    Máy tạo tải tự đo cả lượt bằng đồng hồ đơn điệu được wall_s, nên thật ra nó chạy wall_s ÷ k giây theo
    giờ thực, từ t0_unix tới lúc tạo DONE. Runner ghi t_main_end (giờ thực) khi thấy DONE, chậm hơn từ 0
    tới DONE_POLL_MAX_S. Vậy wall_s ÷ k ≤ t_main_end − t0 ≤ wall_s ÷ k + DONE_POLL_MAX_S, cộng trừ
    CLOCK_MARGIN_S. Trên máy Linux thật, khoảng này phải chứa 1.
    """
    span = t_main_end - t0_unix
    lo = wall_s / (span + CLOCK_MARGIN_S)
    hi = (
        wall_s / (span - DONE_POLL_MAX_S - CLOCK_MARGIN_S) if span > DONE_POLL_MAX_S + CLOCK_MARGIN_S else NAN
    )
    return lo, hi


def to_wall(r: m.Request, t0: float, rate: float) -> m.Request:
    """Đổi mốc của một request từ đồng hồ của máy tạo tải sang giờ thực (đồng hồ của Prometheus).

    Máy tạo tải đo mọi mốc bằng perf_counter (đồng hồ đơn điệu) tính từ t0, rồi cộng t0_unix (loadgen/
    sender.py). Nếu đồng hồ đơn điệu chạy nhanh gấp `rate` lần giờ thực thì sự kiện xảy ra sau Δ giây thật
    được ghi là t0 + rate × Δ, nên mốc thật là t0 + (t − t0) ÷ rate.
    """
    if rate == 1.0:
        return r

    def f(t: float | None) -> float | None:
        return None if t is None else t0 + (t - t0) / rate

    return replace(
        r, t_sched=t0 + (r.t_sched - t0) / rate, t_send=f(r.t_send), t_first=f(r.t_first), t_last=f(r.t_last)
    )


def analyze_attempt(d: Path, clock_rate: float = 1.0) -> list[dict[str, Any]]:
    """Một thư mục attempt-<n> của runner → mỗi pha một dòng; nhiều pha thì thêm dòng `main` (cả pha chính).

    clock_rate: tốc độ đồng hồ đơn điệu của máy tạo tải so với giờ thực (xem to_wall). Mốc của request và
    biên pha đều được đổi sang giờ thực trước khi so với Prometheus; start_s, end_s vẫn ghi theo lịch.
    """
    meta, lg = _json(d / "metadata.json"), _json(d / "loadgen.json")
    # Lần thử runner đánh dấu không hợp lệ (pod restart, máy tạo tải bị throttle…) vẫn được tính, vì Little
    # không phụ thuộc các điều kiện đó, nhưng ghi cột `valid` để bảng tách được (như build_tables).
    checks = _json(d / "checks.json") if (d / "checks.json").exists() else {"valid": False}
    t0, duration = float(lg["t0_unix"]), float(lg["duration_s"])
    with (d / "requests.csv").open(newline="", encoding="utf-8") as fh:
        reqs = [to_wall(m.parse_request(r, t0), t0, clock_rate) for r in csv.DictReader(fh)]
    met = read_metrics(d / "metrics.csv.gz")
    server = server_series(met)
    waiting = server_series({"vllm_waiting": met.get("vllm_waiting", [])})
    errs = [r.t_send for r in reqs if r.error and r.t_send is not None]
    first_err = min(errs) if errs else None

    windows = sorted(lg.get("phases_s", {}).items(), key=lambda kv: kv[1][0])
    if len(windows) != 1:
        windows.append(("main", [0.0, duration]))
    ident = {
        "source": str(d.parent.parent.name),
        "env": meta.get("env"),
        "run_id": meta.get("run_id"),
        "attempt": meta.get("attempt_dir", d.name),
        "valid": bool(checks.get("valid")),
        "lambda_nominal": lg.get("rate_rps"),
        "clock_rate": clock_rate,
    }
    if meta.get("t_main_end") and lg.get("wall_s"):
        ident["clock_rate_min"], ident["clock_rate_max"] = clock_rate_bounds(
            float(lg["wall_s"]), t0, float(meta["t_main_end"])
        )
    return [
        {
            **ident,
            "window": name,
            "start_s": float(s0),
            "end_s": float(s1),
            **little_window(
                reqs,
                server,
                waiting,
                t0 + float(s0) / clock_rate,
                t0 + float(s1) / clock_rate,
                first_error_send=first_err,
            ),
        }
        for name, (s0, s1) in windows
    ]


def from_capacity(path: Path, window_s: float) -> list[dict[str, Any]]:
    """capacity-*.json của ĐG1 → mỗi mức λ một dòng, từ bản tóm tắt (không có dữ liệu thô).

    Từ 16/11, capacity.py ghi sẵn `lambda_real_rps` (request thành công gửi trong cửa sổ ÷ độ dài cửa sổ)
    và `window_s`; file cũ hơn thì tính λ_thực = n_measured ÷ window_s, với window_s lấy từ tham số (ĐG1-mini
    ở nhà: 120 s; ĐG1 trên V2: 240 s). capacity.py đếm request có t_sched trong cửa sổ đo, gần trùng lúc gửi
    vì máy tạo tải chạy vòng hở (open loop). B_server là trung bình các mẫu running + waiting trong cửa
    sổ, B_client là L_client (request lỗi tính tới hết cửa sổ). File không có số mẫu thật, nên se_sampling
    giả định window_s ÷ 5 mẫu.
    """
    d = _json(path)
    rows = []
    for c in d.get("curves", []):
        win = float(c.get("window_s") or window_s)
        n_samples = int(win // STEP_S)
        lam = c["lambda_real_rps"] if c.get("lambda_real_rps") is not None else c["n_measured"] / win
        pred = lam * c["e2e_mean_s"]
        queued = c.get("waiting_mean", 0.0) >= QUEUE_MIN
        se = NAN if queued else occupancy_se(lam, c["e2e_mean_s"], n_samples)
        rows.append(
            {
                "source": path.name,
                "env": d.get("env"),
                "run_id": c.get("run_id") or f"lambda-{c['lambda_rps']:g}",
                "attempt": NAN,
                "valid": bool(c.get("valid", c.get("loadgen_valid", True))),
                "window": "measure",
                "start_s": NAN,
                "end_s": NAN,
                "lambda_nominal": c["lambda_rps"],
                "n_sent": c["n_measured"],
                "n_error": c.get("n_error", 0),
                "applicable": not c.get("n_error", 0),
                "lambda_real": lam,
                "e2e_mean_s": c["e2e_mean_s"],
                "L_pred": pred,
                "L_client": c["B_client"],
                "edge": NAN,
                "L_client_sampled": NAN,
                "L_server": c["B_server"],
                "waiting_mean": c.get("waiting_mean", NAN),
                "n_samples": n_samples,
                "se_sampling": se,
                **_deviations(c["B_client"], c["B_server"], pred, se),
            }
        )
    return rows


def parse_source(arg: str) -> tuple[Path, float]:
    """`<đường dẫn>` hoặc `<đường dẫn>@<k>` → (đường dẫn, k). Mỗi phiên runner có k riêng, vì tốc độ đồng
    hồ của VM WSL2 đổi sau mỗi lần VM khởi động lại (1,0162 ngày 07/11; 1,0188 chiều 16/11)."""
    path, sep, rate = arg.rpartition("@")
    if sep:
        try:
            return Path(path), float(rate)
        except ValueError:
            pass
    return Path(arg), 1.0


def collect(
    sources: Sequence[tuple[Path, float]], capacity_window_s: float
) -> tuple[list[dict[str, Any]], list[str]]:
    """Mọi nguồn (đường dẫn, k) → (các dòng, các lần thử bị bỏ kèm lý do). k chỉ áp cho phiên runner."""
    rows: list[dict[str, Any]] = []
    skipped: list[str] = []
    for src, rate in sources:
        if src.is_file():
            rows += from_capacity(src, capacity_window_s)
            continue
        attempts, skip = find_attempts(src)
        skipped += skip
        for d in attempts:
            rows += analyze_attempt(d, rate)
    return rows, skipped


# ── In bảng ───────────────────────────────────────────────────────────────────────────────────────────


def _f(v: Any, spec: str) -> str:
    return "–" if v is None or (isinstance(v, float) and math.isnan(v)) else format(v, spec)


# Cột số của bảng chữ: (tiêu đề, khoá, định dạng, độ rộng)
_CELLS = [
    ("λ_dn", "lambda_nominal", "5.2f", 5), ("λ_thực", "lambda_real", "7.3f", 7),
    ("W(s)", "e2e_mean_s", "6.2f", 6), ("λW", "L_pred", "7.2f", 7), ("L_cli", "L_client", "7.2f", 7),
    ("edge", "edge", "6.2f", 6), ("L_cs", "L_client_sampled", "7.2f", 7), ("L_srv", "L_server", "7.2f", 7),
    ("wait", "waiting_mean", "6.1f", 6), ("dev_c", "dev_client", "+6.1%", 6),
    ("dev_s", "dev_server", "+6.1%", 6), ("z", "z_server", "+5.1f", 5),
]  # fmt: skip


def summary(rows: Sequence[dict[str, Any]]) -> str:
    """Bảng chữ: mỗi cửa sổ một dòng, đánh dấu dòng lệch quá LITTLE_TOL."""
    cols = " ".join(f"{title:>{width}}" for title, _, _, width in _CELLS)
    head = f"{'nguồn':<22} {'lượt':<14} {'cửa sổ':<8} {cols}  ghi chú"
    out = [head, "-" * len(head)]
    for r in rows:
        notes = []
        if not r["valid"]:
            notes.append("lượt không hợp lệ")
        if not r["applicable"]:
            notes.append("có request lỗi: không áp được")
        dev = r["dev_server"]
        if r["applicable"] and not math.isnan(dev) and abs(dev) > LITTLE_TOL:
            notes.append(f"lệch > {LITTLE_TOL:.0%}")
        nums = " ".join(f"{_f(r[key], spec):>{width}}" for _, key, spec, width in _CELLS)
        name = f"{r['source'][:22]:<22} {str(r['run_id'])[:14]:<14} {r['window'][:8]:<8}"
        out.append(f"{name} {nums}  {'; '.join(notes)}")
    runs = {(r["source"], r["run_id"], r["attempt"]): r for r in rows if "clock_rate_min" in r}
    if runs:
        out.append("")
        out.append("Tốc độ đồng hồ máy tạo tải k (cận từ t_main_end của runner và wall_s của loadgen):")
        for (src, run, att), r in runs.items():
            out.append(
                f"  {src} {run}/{att}: k ∈ [{_f(r['clock_rate_min'], '.4f')}; "
                f"{_f(r['clock_rate_max'], '.4f')}], đang dùng {r['clock_rate']:g}"
            )
    return "\n".join(out)


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument(
        "sources",
        type=parse_source,
        nargs="+",
        help="thư mục phiên runner (thêm @k nếu đồng hồ máy tạo tải chạy nhanh k lần, ví dụ "
        "runs/sim/x@1.031) hoặc file capacity-*.json",
    )
    ap.add_argument(
        "--capacity-window-s",
        type=float,
        default=120.0,
        help="độ dài cửa sổ đo của file capacity (ĐG1-mini ở nhà: 120 s)",
    )
    ap.add_argument("--out", type=Path, help="ghi bảng mỗi cửa sổ một dòng ra CSV này")
    args = ap.parse_args(argv)
    rows, skipped = collect(args.sources, args.capacity_window_s)
    for s in skipped:
        print(f"bỏ qua {s}")
    if not rows:
        ap.error("không có cửa sổ nào để tính")
    if args.out:
        write_csv(args.out, rows, COLUMNS)
    print(summary(rows))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
