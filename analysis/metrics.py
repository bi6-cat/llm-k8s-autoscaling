"""Các phép tính của bảng phân tích (Môi trường §15). Hàm thuần, không đọc file, có unit test.

Khái niệm:
    SLO (Service Level Objective) = mục tiêu chất lượng phục vụ. Ở đây một request "đạt SLO" khi không lỗi,
        TTFT ≤ 2,5 s và TPOT ≤ 100 ms (Thông số §6).
    TTFT (time to first token) = thời gian chờ token đầu tiên = t_first − t_send.
    TPOT (time per output token) = thời gian sinh mỗi token sau token đầu = (t_last − t_first) ÷ (n_out − 1).
    SLO attainment = số request đạt SLO ÷ số request ĐÃ GỬI trong pha (request lỗi vẫn ở mẫu số).
    GPU-giờ = tổng thời gian các pod vLLM giữ GPU, tính cả lúc cold start và lúc drain (Môi trường §15).
    Flapping = số replica đổi chiều liên tục (lên rồi xuống rồi lên) trong thời gian ngắn.
Mục đích: Gom mọi công thức vào một chỗ để bảng nghiệm thu, biểu đồ và luận văn dùng cùng một định nghĩa.
    build_tables.py đọc thư mục lượt rồi gọi các hàm ở đây.

Thời gian: request tính bằng giây kể từ t0_unix của máy tạo tải (requests.csv); mốc pod, metric và cảnh báo
tính bằng giây UNIX. build_tables.py đổi tất cả về giây UNIX trước khi gọi. Trên kind và VM thuê, máy tạo
tải, Prometheus và API server chạy cùng một máy nên chung đồng hồ.
"""

from __future__ import annotations

import bisect
import math
from collections import Counter
from collections.abc import Iterable, Mapping, Sequence
from dataclasses import dataclass
from typing import Any

# ── Ngưỡng, chép từ Thông số §6 (nguồn sự thật duy nhất); trùng experiments/runner/capacity.py ──
TTFT_SLO_S = 2.5  # TTFT ≤ 2,5 s, trùng biên bucket le="2.5" của histogram vLLM
TPOT_SLO_S = 0.100  # TPOT ≤ 100 ms
ATTAINMENT = 0.95  # mục tiêu 95 % request đạt SLO (N1)
# Burn rate 4 = tiêu ngân sách lỗi 5 % nhanh gấp 4 lần = 20 % request xấu: ngưỡng của LLMSLOBurnFast
# (common/observability/alerts/llm.yaml) và cũng là ngưỡng "page giả" của N7 (Thông số §4).
BAD_RATIO_PAGE = 4 * (1 - ATTAINMENT)

MIN_SAMPLES_P99 = 200  # Môi trường §15: pha ít hơn khoảng 200 request thì chỉ báo p95
FLAP_WINDOW_S = 300.0  # Môi trường §15: "đổi chiều trong vòng 5 phút" = một cửa sổ scale-down của HPA
RECOVERY_WINDOW_S = 30.0  # N2b: TTFT p95 trên cửa sổ trượt 30 s…
RECOVERY_HOLD_S = 60.0  # …không vượt ngưỡng và giữ được ít nhất 60 s
VIOLATION_WINDOW_S = 60.0  # N7: cửa sổ xác định "SLO bắt đầu bị vi phạm" = cửa sổ ngắn 1 phút của cảnh báo
PAGE_WINDOW_S = 300.0  # N7: cửa sổ dài 5 phút của LLMSLOBurnFast, dùng để chấm page giả

NAN = float("nan")
# Bước query_range của runner (experiments/runner/collect.py STEP_S; test_metrics kiểm hai số trùng nhau).
# Một nguồn cho cả analysis: build_tables dùng lại hằng này.
STEP_S = 5.0


@dataclass(frozen=True)
class Request:
    """Một dòng requests.csv đã đổi kiểu. Thời gian là giây UNIX (build_tables cộng t0_unix vào)."""

    id: int
    t_sched: float  # thời điểm theo lịch gửi: dùng để xếp request vào pha và vào cửa sổ trượt
    t_send: float | None
    t_first: float | None  # chunk có nội dung đầu tiên; None nếu chưa nhận được token nào
    t_last: float | None
    n_out: int | None  # số token output server báo trong `usage`; None nếu stream bị cắt
    error: str  # "" = thành công (Môi trường §14.2); mọi chỉ số lỗi lọc theo cột này, không theo `status`

    @property
    def ttft(self) -> float | None:
        if self.t_first is None or self.t_send is None:
            return None
        return self.t_first - self.t_send

    @property
    def tpot(self) -> float | None:
        # Chia cho n_out − 1 vì token đầu đã tính vào TTFT; một chunk SSE có thể chứa nhiều token nên phải
        # lấy n_out từ `usage`, không đếm chunk.
        if self.t_first is None or self.t_last is None or not self.n_out or self.n_out < 2:
            return None
        return (self.t_last - self.t_first) / (self.n_out - 1)

    @property
    def good(self) -> bool:
        """Đạt SLO: không lỗi, TTFT và TPOT đều trong ngưỡng (Thông số §6)."""
        ttft, tpot = self.ttft, self.tpot
        return (
            not self.error
            and ttft is not None
            and tpot is not None
            and ttft <= TTFT_SLO_S
            and tpot <= TPOT_SLO_S
        )


def _float(s: str | None) -> float | None:
    return float(s) if s not in (None, "") else None


def parse_request(row: Mapping[str, str], t0_unix: float) -> Request:
    """Một dòng csv.DictReader của requests.csv → Request, thời gian đổi sang giây UNIX."""

    def t(key: str) -> float | None:
        v = _float(row.get(key))
        return None if v is None else t0_unix + v

    n_out = _float(row.get("n_out"))
    return Request(
        id=int(row["id"]),
        t_sched=t0_unix + float(row["t_sched"]),
        t_send=t("t_send"),
        t_first=t("t_first"),
        t_last=t("t_last"),
        n_out=None if n_out is None else int(n_out),
        error=row.get("error") or "",
    )


def quantile(values: Iterable[float], p: float) -> float:
    """Phân vị p (0–1), cùng công thức với experiments/runner/capacity.py (chỗ tính ra C), để số trong
    bảng này so được với ĐG1: chọn phần tử thứ round(p × (n − 1)) của dãy đã sắp. Dãy rỗng → NaN."""
    a = sorted(values)
    return a[min(len(a) - 1, int(p * (len(a) - 1) + 0.5))] if a else NAN


def _ratio(num: float, den: float) -> float:
    return num / den if den else NAN


def in_window(reqs: Sequence[Request], start: float, end: float) -> list[Request]:
    """Request có t_sched trong [start, end). Xếp theo LỊCH GỬI (không theo lúc gửi thật hay lúc xong), vì
    pha của kịch bản định nghĩa theo lịch, và mọi cấu hình nhận cùng lịch nên so được từng cửa sổ."""
    return [r for r in reqs if start <= r.t_sched < end]


def phase_stats(reqs: Sequence[Request], start: float, end: float) -> dict[str, Any]:
    """Chỉ số hiệu năng của một pha [start, end) (Môi trường §15, nhóm "Hiệu năng").

    - Phân vị TTFT, TPOT tính trên MỌI request thành công của pha (không lấy trung bình các p95 theo phút
      hay theo pod), giống `vllm bench serve` và capacity.py. Request lỗi không có TTFT đo được, nên được
      đếm riêng (`n_error`) và vẫn bị tính là không đạt trong `slo_attainment`.
    - p99 chỉ báo khi pha có ít nhất MIN_SAMPLES_P99 request thành công; ít hơn thì NaN.
    - Throughput = token output của các request thuộc pha ÷ độ dài pha (xấp xỉ, vì request cuối pha xong
      sau mép pha); đối chiếu `vllm:generation_tokens_total` nếu cần.
    """
    sel = in_window(reqs, start, end)
    ok = [r for r in sel if not r.error]
    ttft = [x for r in ok if (x := r.ttft) is not None]
    tpot = [x for r in ok if (x := r.tpot) is not None]
    tokens = sum(r.n_out or 0 for r in ok)
    errors = Counter(r.error for r in sel if r.error)
    return {
        "n_sent": len(sel),
        "n_error": len(sel) - len(ok),
        "error_ratio": _ratio(len(sel) - len(ok), len(sel)),
        # Ví dụ "IncompleteStream=1 Timeout=3": loại lỗi theo cột `error` (Môi trường §14.2)
        "error_types": " ".join(f"{k}={v}" for k, v in sorted(errors.items())),
        "slo_attainment": _ratio(sum(r.good for r in sel), len(sel)),
        "ttft_p50_s": quantile(ttft, 0.50),
        "ttft_p95_s": quantile(ttft, 0.95),
        "ttft_p99_s": quantile(ttft, 0.99) if len(ttft) >= MIN_SAMPLES_P99 else NAN,
        "tpot_p50_s": quantile(tpot, 0.50),
        "tpot_p95_s": quantile(tpot, 0.95),
        "tokens_out": tokens,
        "throughput_tok_s": _ratio(tokens, end - start),
    }


def _bad_fraction(sel: Sequence[Request]) -> float | None:
    """Tỷ lệ request xấu (không đạt SLO, gồm cả lỗi) trong một nhóm request; nhóm rỗng → None. Một chỗ duy
    nhất định nghĩa "request xấu" cho cả mốc vi phạm và page giả của N7."""
    return 1 - sum(r.good for r in sel) / len(sel) if sel else None


def bad_ratio(reqs: Sequence[Request], start: float, end: float) -> float | None:
    """Tỷ lệ request xấu có lịch gửi trong [start, end). Không có request nào → None."""
    return _bad_fraction(in_window(reqs, start, end))


# ── N2b: thời gian hồi phục SLO ───────────────────────────────────────────────────────────────────────


def _sliding_ttft_p95(reqs: Sequence[Request], grid: Sequence[float], window_s: float) -> list[float | None]:
    """TTFT p95 của các request có lịch gửi trong (τ − window_s, τ], tại mỗi τ của `grid`.

    Request lỗi tính như TTFT vô hạn: người dùng không nhận được câu trả lời, và nếu bỏ đi thì một lượt quá
    tải nặng (nhiều timeout) lại trông như đã hồi phục. Cửa sổ không có request nào → None.
    """
    rs = sorted(reqs, key=lambda r: r.t_sched)
    ts = [r.t_sched for r in rs]
    out: list[float | None] = []
    for tau in grid:
        lo, hi = bisect.bisect_right(ts, tau - window_s), bisect.bisect_right(ts, tau)
        vals = [math.inf if r.error or r.ttft is None else r.ttft for r in rs[lo:hi]]
        out.append(quantile(vals, 0.95) if vals else None)
    return out


def slo_recovery_s(
    reqs: Sequence[Request],
    t_rise: float,
    t_end: float,
    *,
    window_s: float = RECOVERY_WINDOW_S,
    hold_s: float = RECOVERY_HOLD_S,
    step_s: float = 1.0,
) -> float | None:
    """N2b: số giây từ lúc tải tăng (`t_rise`, theo lịch) tới mốc τ đầu tiên, SAU khi SLO đã thật sự bị vi
    phạm, mà TTFT p95 trượt 30 s không vượt ngưỡng tại mọi điểm trong [τ, τ + 60 s] (Môi trường §15). Chỉ tìm
    trong [t_rise, t_end], với t_end = hết pha spike: hồi phục nhờ tải giảm ở pha drop không phải nhờ
    scale-up.

    "Đã thật sự bị vi phạm" = tổng thời gian vi phạm kể từ t_rise đạt một cửa sổ (30 s; mỗi điểm lưới tính
    `step_s` giây). Việc tìm τ bắt đầu từ mốc đó. Lý do:
    - Hàng đợi trên pod cũ dồn dần, nên 60 s đầu sau t_rise có thể vẫn đạt rồi mới vi phạm suốt lúc chờ
      cold start; tìm từ t_rise thì lượt đó ra 0, là kết quả tốt nhất cho đúng lượt tệ nhất.
    - Vài request chậm do dao động trước đợt vi phạm thật không được làm mốc, vì 60 s đạt ngay sau đó lại
      cho kết quả gần 0. Cửa sổ trượt kéo dài mỗi request chậm thêm 30 s, nên hai request chậm đứng riêng
      chỉ gây vi phạm dưới 30 s (p95 của 30 request chịu được một request xấu).
    - Đếm TỔNG chứ không đếm liên tục: p95 dao động quanh ngưỡng (xấu 29 s, đạt 2 s, lặp lại) vẫn là quá
      tải. Đếm liên tục thì không đợt nào đủ 30 s, và lượt đó ra 0 thay vì "không hồi phục".
    Giới hạn còn lại: vi phạm, rồi đạt 60 s, rồi vi phạm lại thì chỉ tính lần hồi phục đầu.
    Tổng thời gian vi phạm chưa tới 30 s → 0. Không hồi phục trước t_end → None. Cửa sổ trống (không có
    request) được coi là không vi phạm. Lưới 1 s: sai số tối đa 1 s, nhỏ hơn nhiều ngưỡng thực tiễn 30 s
    của Thông số §6.
    """
    n = int((t_end - t_rise) // step_s) + 1
    grid = [t_rise + i * step_s for i in range(n)]
    p95 = _sliding_ttft_p95(reqs, grid, window_s)
    ok = [v is None or v <= TTFT_SLO_S for v in p95]
    need_bad = int(math.ceil(window_s / step_s))  # số điểm vi phạm (cộng dồn) để coi là đã vi phạm thật
    n_bad, first_bad = 0, None
    for i, good in enumerate(ok):
        n_bad += not good
        if n_bad >= need_bad:
            first_bad = i
            break
    if first_bad is None:
        return 0.0
    need = int(math.ceil(hold_s / step_s)) + 1  # số điểm lưới trong [τ, τ + hold_s]
    run = 0  # số điểm "đạt" liên tiếp tính tới điểm i
    for i in range(first_bad, len(ok)):
        run = run + 1 if ok[i] else 0
        if run >= need:
            return grid[i - need + 1] - t_rise
    return None


# ── N7: thời điểm SLO bắt đầu bị vi phạm, page giả ───────────────────────────────────────────────────────


def slo_violation_start(
    reqs: Sequence[Request],
    start: float,
    end: float,
    *,
    window_s: float = VIOLATION_WINDOW_S,
    threshold: float = BAD_RATIO_PAGE,
    step_s: float = 1.0,
) -> float | None:
    """Mốc τ đầu tiên trong [start + 60 s, end] mà tỷ lệ request xấu (lịch gửi trong (τ − 60 s, τ]) vượt 20 %.

    Đây là "thời điểm SLO bắt đầu bị vi phạm thật" để tính thời gian tới cảnh báo của N7. Cùng ngưỡng 20 %
    và cùng cửa sổ ngắn 1 phút với LLMSLOBurnFast, nhưng đo bằng log client (chính xác từng request) thay
    vì histogram của server. Vì vậy thời gian tới cảnh báo gồm cả 1–2 phút để cửa sổ 5 phút của cảnh báo
    vượt 20 %, đúng như ước tính trong llm.yaml. Không vi phạm → None.
    Chỉ xét cửa sổ đã đủ 60 s (τ ≥ start + 60 s): ở đầu lượt cửa sổ mới có vài request, vài request chậm
    đầu tiên (hàng đợi đang hình thành) đã đủ vượt 20 % (sim 15/11: CONST 2 req/s "vi phạm" ở giây thứ 10).
    """
    rs = sorted(reqs, key=lambda r: r.t_sched)
    ts = [r.t_sched for r in rs]
    first = start + window_s
    n = int((end - first) // step_s) + 1
    for i in range(max(n, 0)):
        tau = first + i * step_s
        lo, hi = bisect.bisect_right(ts, tau - window_s), bisect.bisect_right(ts, tau)
        bad = _bad_fraction(rs[lo:hi])
        if bad is not None and bad > threshold:
            return tau
    return None


def classify_alerts(
    alerts: Sequence[Mapping[str, Any]],
    reqs: Sequence[Request],
    *,
    main_start: float | None = None,
    step_s: float = STEP_S,
    window_s: float = PAGE_WINDOW_S,
) -> list[dict[str, Any]]:
    """Mỗi đợt kêu của mỗi chuỗi trong alerts.jsonl → một dòng: tên, mức, mốc firing đầu/cuối của đợt, tỷ lệ
    request xấu theo log client trong 5 phút trước lúc firing, có phải page giả không, và đợt đó đã kêu từ
    trước pha chính chưa.

    Một chuỗi có thể kêu nhiều đợt trong một lượt (hết rồi kêu lại): mỗi đợt được chấm riêng, vì đợt sau có
    thể là page giả dù đợt đầu đúng. File cũ (trước 16/11) chưa có `episodes` thì coi [first, last] là một
    đợt.

    `firing_at_start`: đợt bắt đầu trước pha chính (`main_start` = t0 của máy tạo tải), tức `first` ≤
    main_start + một bước query_range (`step_s`). Từ 16/11 runner hỏi ALERTS từ 30 s trước warm-up, nên
    `first` của đợt bắt đầu lúc warm-up là mốc thật. File cũ hỏi từ đầu pha chính, nên `first` bị cắt đúng ở
    mép đầu (sai số một bước). Hai trường hợp đều là đợt kêu do lượt trước để lại hoặc do warm-up, không do
    pha chính, nên `false_page` để None: 5 phút trước đó là lúc reset và warm-up, gần như không có request
    của pha chính, và đợt đó sẽ bị chấm nhầm là page giả.

    Một đợt kêu trước mốc vi phạm theo log client rồi kêu tiếp qua mốc đó vẫn được chấm theo đúng định nghĩa
    tại lúc firing (Thông số N7): nếu khi đó log client chưa thấy 20 % request xấu thì đó là page giả, dù
    build_tables vẫn dùng nó làm cảnh báo của lần vi phạm (thời gian tới cảnh báo âm).

    Page giả (N7) = cảnh báo `severity: page` kêu trong khi tỷ lệ request xấu theo log client, trên cùng
    cửa sổ, < 20 %. "Cùng cửa sổ" = cửa sổ dài 5 phút của LLMSLOBurnFast, kết thúc ở lúc firing. Cửa sổ
    không có request nào (page trong cooldown) cũng tính là page giả: không có bằng chứng người dùng bị
    ảnh hưởng. Định nghĩa này chỉ có nghĩa ở lượt không cố ý gây sự cố (A2 × KB1, KB3): ở VH4,
    KedaScalerErrors kêu đúng dù người dùng chưa bị ảnh hưởng.
    """
    rows = []
    for a in alerts:
        labels = a.get("labels", {})
        severity = labels.get("severity", "")
        for first, last in a.get("episodes") or [[a["first"], a["last"]]]:
            first, last = float(first), float(last)
            ratio = bad_ratio(reqs, first - window_s, first)
            at_start = main_start is not None and first <= main_start + step_s
            false_page = severity == "page" and (ratio is None or ratio < BAD_RATIO_PAGE)
            rows.append(
                {
                    "alertname": labels.get("alertname", ""),
                    "severity": severity,
                    "first": first,
                    "last": last,
                    "client_bad_ratio": NAN if ratio is None else ratio,
                    "false_page": None if at_start else false_page,
                    "firing_at_start": at_start,
                }
            )
    return rows


# ── Tài nguyên: GPU-giờ ───────────────────────────────────────────────────────────────────────────────


def gpu_seconds(pods: Iterable[Mapping[str, Any]], start: float, end: float) -> float:
    """Tổng giây-GPU các pod vLLM giữ trong [start, end], từ pods_timeline.json (Môi trường §14.2).

    Pod giữ GPU từ mốc `scheduled` (scheduler đã gán node, device plugin cấp GPU) tới lúc biến mất, một
    thời điểm trong (last_seen, gone_at]. Lấy cận trên `gone_at` (sai số ≤ 1 chu kỳ hỏi 5 s): ước lượng
    hơi cao cho cấu hình autoscaling, tức bất lợi cho A2, nên kết luận "A2 tiết kiệm" không bị thổi phồng.
    Pod chưa biến mất lúc watcher dừng (`gone_at` rỗng) giữ GPU tới hết cửa sổ. Pod chưa từng được xếp
    lịch (Pending vì hết GPU) không giữ GPU.
    """
    total = 0.0
    for p in pods:
        s = (p.get("marks") or {}).get("scheduled")
        if s is None:
            continue
        e = p.get("gone_at")
        e = end if e is None else float(e)
        total += max(0.0, min(e, end) - max(float(s), start))
    return total


def integrate_steps(samples: Sequence[tuple[float, float]], start: float, end: float, step_s: float) -> float:
    """∫ giá trị dt trên [start, end] cho chuỗi lấy mẫu đều `step_s` (query_range của runner). Dùng cho số
    replica trung bình và GPU-giờ xấp xỉ từ kube_deployment_status_replicas.

    Mỗi mẫu giữ giá trị tới mẫu kế tiếp; mẫu cuối giữ thêm `step_s`. Khi chuỗi đều thì như nhau, mỗi mẫu đại
    diện cho [ts, ts + step_s). Khoảng hở (kube-state-metrics khởi động lại: chuỗi cũ bị stale trước khi chuỗi
    mới có mẫu) được lấp bằng giá trị trước đó, vì số replica không đổi chỉ vì mất mẫu. Tính khoảng hở là 0
    thì số replica và GPU-giờ thấp đi, nghiêng có lợi cho cấu hình autoscaling."""
    ss = sorted(samples)
    total = 0.0
    for i, (ts, v) in enumerate(ss):
        nxt = ss[i + 1][0] if i + 1 < len(ss) else ts + step_s
        total += v * max(0.0, min(nxt, end) - max(ts, start))
    return total


# ── Autoscaling: số lần scale, flapping, thời gian phản ứng ─────────────────────────────────────────────


def scale_changes(samples: Sequence[tuple[float, float]]) -> list[tuple[float, float, float]]:
    """Các lần số replica mong muốn đổi: [(ts, cũ, mới)], từ chuỗi đã sắp theo thời gian."""
    out = []
    for (_, a), (t, b) in zip(samples, samples[1:], strict=False):
        if b != a:
            out.append((t, a, b))
    return out


def count_flaps(changes: Sequence[tuple[float, float, float]], window_s: float = FLAP_WINDOW_S) -> int:
    """Số lần đổi chiều (lên → xuống hoặc xuống → lên) cách lần đổi trước không quá `window_s` giây.

    Ví dụ 1 → 3 (phút 5) rồi 3 → 1 (phút 19) là scale bình thường, không phải flapping; 1 → 2 (phút 5) rồi
    2 → 1 (phút 7) là một lần flapping.
    """
    n = 0
    for (t0, a0, b0), (t1, a1, b1) in zip(changes, changes[1:], strict=False):
        if (b0 > a0) != (b1 > a1) and t1 - t0 <= window_s:
            n += 1
    return n


def reaction(
    pods: Iterable[Mapping[str, Any]], start_names: set[str], t_rise: float
) -> dict[str, float | None]:
    """N2a: từ lúc tải tăng (theo lịch) tới khi replica MỚI đầu tiên Ready, tách hai phần (Môi trường §15).

    - detect_s: t_rise → pod mới đầu tiên được tạo. ReplicaSet tạo pod ngay khi HPA đổi desiredReplicas,
      nên đây là phần phát hiện (KEDA đọc metric, HPA tính, cửa sổ ổn định), chính xác tới 1 s theo đồng
      hồ API server. Không dùng kube_horizontalpodautoscaler_status_desired_replicas vì mẫu chỉ có mỗi chu
      kỳ scrape của kube-state-metrics.
    - react_s: t_rise → pod mới đầu tiên Ready (chỉ tiêu N2a ≤ 2 phút).
    - create_to_ready_s = react_s − detect_s: từ lúc có pod mới đầu tiên tới lúc có pod mới Ready đầu tiên,
      để hai phần cộng lại đúng bằng N2a. Thường bằng cold start (8 pha, Kiến trúc §7.2) của chính pod tạo
      đầu tiên, nhưng KHÔNG gọi là cold start: nếu pod tạo sau lại Ready trước (ví dụ rơi vào node đã có
      image) thì nó không phải cold start của pod nào. Cold start của từng pod (ĐG3, C5) lấy từ
      pods_timeline.json và log (vllm_log.phases).
    "Pod mới" = không có trong pods_start và được tạo từ t_rise − 1 s (mốc API chỉ tới giây) trở đi. Pod tạo
    trước lúc tải tăng (scale-up do dao động ở mức nền) không phải phản ứng với tải tăng nên không tính.
    """
    new = [
        p
        for p in pods
        if p["name"] not in start_names
        and (p.get("marks") or {}).get("created") is not None
        and p["marks"]["created"] >= t_rise - 1
    ]
    created = [p["marks"]["created"] for p in new]
    ready = [p["marks"]["ready"] for p in new if p["marks"].get("ready") is not None]
    detect = min(created) - t_rise if created else None
    react = min(ready) - t_rise if ready else None
    return {
        "detect_s": detect,
        "create_to_ready_s": None if detect is None or react is None else react - detect,
        "react_s": react,
    }


def mean(values: Iterable[float]) -> float:
    vals = [v for v in values if not math.isnan(v)]
    return sum(vals) / len(vals) if vals else NAN
