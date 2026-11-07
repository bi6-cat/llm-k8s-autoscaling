"""Tự kiểm tra của máy tạo tải: số đo có đáng tin không.

Khái niệm: Máy tạo tải cũng có thể là nút thắt. Nếu nó gửi trễ hơn lịch, hoặc event loop bị nghẽn khi
    đọc stream, thì TTFT đo được là của máy tạo tải chứ không phải của hệ thống. Event loop = vòng lặp
    của asyncio chạy mọi coroutine trên MỘT luồng; một đoạn code chạy lâu làm mọi request khác bị chờ.
Mục đích: Đo các tiêu chí ở Môi trường §17 cho mỗi lượt: độ lệch lịch gửi p99 < 50 ms, CPU < 70%, thời
    gian bị giới hạn CPU (throttle) < 0,1% thời gian lượt, độ trễ event loop p99 < 50 ms và không lần nào
    quá 500 ms. Không đạt thì lượt đó không hợp lệ.
"""

from __future__ import annotations

import asyncio
import math
import time
from collections.abc import Sequence
from pathlib import Path
from typing import Any

SEND_LAG_P99_MAX_MS = 50.0  # Môi trường §17
CPU_MAX_FRACTION = 0.70  # Môi trường §17; tính trên MỘT lõi, vì event loop chỉ chạy trên một luồng
# Độ trễ event loop (Môi trường §17). p99 dùng cùng ngưỡng với lệch lịch gửi: cả hai đo cùng một sai số
# (loop bận nên việc đến hạn bị làm muộn), một bên lúc gửi, một bên lúc nhận chunk. Mức max bắt một lần nghẽn
# dài mà p99 không thấy (1% của 25 phút là 15 s): 500 ms = 20% ngưỡng TTFT 2,5 s, gấp 10 lần ngưỡng p99.
LOOP_LAG_P99_MAX_MS = 50.0
LOOP_LAG_MAX_MS = 500.0
# Tỷ lệ thời gian bị throttle (Môi trường §17). Thay cho `nr_throttled == 0`: một chu kỳ throttle 1,4–4,4 ms
# trong mức ĐG1-mini ~3 phút (≤ 0,0025%) đã loại cả lượt ngày 05/11 mà số đo không đổi (lệch lịch p99 2 ms).
# 0,1% = 0,18 s trong lượt 3 phút, 1,5 s trong lượt 25 phút.
THROTTLE_MAX_FRACTION = 0.001
CGROUP_CPU_STAT = Path("/sys/fs/cgroup/cpu.stat")  # cgroup v2 (k3s trên Ubuntu 24.04); không có trên Windows


def percentile(values: Sequence[float], q: float) -> float | None:
    """Phân vị q (0–100), nội suy tuyến tính giữa hai giá trị kề nhau (giống numpy mặc định)."""
    if not values:
        return None
    xs = sorted(values)
    pos = (len(xs) - 1) * q / 100.0
    lo, hi = math.floor(pos), math.ceil(pos)
    return xs[lo] + (xs[hi] - xs[lo]) * (pos - lo)


class LoopLagMonitor:
    """Đo độ trễ event loop: một tác vụ nền hẹn ngủ `interval` giây rồi đo nó dậy muộn bao nhiêu.

    Event loop rảnh thì dậy gần đúng hẹn (vài ms). Nếu có đoạn code chặn loop (ví dụ phân tích JSON quá
    nhiều chunk cùng lúc), tác vụ này dậy muộn, và mọi `t_first` ghi trong lúc đó cũng bị muộn theo:
    kiểm tra phía gửi không thấy được lỗi này (Môi trường §9).
    """

    def __init__(self, interval_s: float = 0.01) -> None:
        self.interval_s = interval_s
        self.lags_s: list[float] = []

    async def run(self) -> None:
        while True:
            expected = time.perf_counter() + self.interval_s
            await asyncio.sleep(self.interval_s)
            self.lags_s.append(max(0.0, time.perf_counter() - expected))


class CpuMonitor:
    """CPU của chính tiến trình loadgen, theo từng cửa sổ `window_s` giây; giữ giá trị lớn nhất.

    time.process_time() = thời gian CPU tiến trình đã dùng (mọi luồng). Chia cho thời gian thực trôi qua
    ra tỷ lệ của một lõi: 0,7 nghĩa là luồng event loop bận 70% thời gian.
    """

    def __init__(self, window_s: float = 5.0) -> None:
        self.window_s = window_s
        self.max_fraction = 0.0

    async def run(self) -> None:
        cpu0, wall0 = time.process_time(), time.perf_counter()
        while True:
            await asyncio.sleep(self.window_s)
            cpu1, wall1 = time.process_time(), time.perf_counter()
            if wall1 > wall0:
                self.max_fraction = max(self.max_fraction, (cpu1 - cpu0) / (wall1 - wall0))
            cpu0, wall0 = cpu1, wall1


def read_cgroup_cpu_stat(path: Path = CGROUP_CPU_STAT) -> dict[str, int] | None:
    """Đọc bộ đếm throttle của cgroup v2. None nếu không chạy trong container Linux.

    Throttle = kernel tạm dừng container vì đã dùng hết hạn mức CPU (limits.cpu) trong chu kỳ 100 ms.
    nr_throttled = số chu kỳ bị dừng. throttled_usec = thời gian bị dừng (µs), kernel cộng dồn theo TỪNG CPU
    bị dừng, nên khi nhiều luồng cùng bị dừng thì số này lớn hơn thời gian thực: dùng làm cận trên, tiêu chí
    vì vậy chỉ chặt hơn chứ không lỏng hơn. loadgen chủ yếu chạy một luồng (event loop) nên hai số gần bằng
    nhau. Trong lúc bị dừng thì lịch gửi và việc đọc stream đều trễ theo.
    """
    try:
        lines = path.read_text().splitlines()
    except OSError:
        return None
    stat = {}
    for line in lines:
        key, _, value = line.partition(" ")
        if key in ("nr_periods", "nr_throttled", "throttled_usec"):
            stat[key] = int(value)
    return stat


CHECK_KEYS = ("send_lag_ok", "loop_lag_ok", "cpu_ok", "throttle_ok")


def summarize(
    records: Sequence[dict[str, Any]],
    loop_lags_s: Sequence[float],
    cpu_max_fraction: float,
    cgroup_before: dict[str, int] | None,
    cgroup_after: dict[str, int] | None,
    cgroup_elapsed_s: float | None = None,
) -> dict[str, Any]:
    """Gộp các số đo thành một dict cho loadgen.json; `valid` = mọi tiêu chí có ngưỡng đều đạt.

    `cgroup_elapsed_s`: thời gian thực giữa hai lần đọc cpu.stat, mẫu số của tỷ lệ throttle.
    """
    send_lags_ms = [(r["t_send"] - r["t_sched"]) * 1000 for r in records if r.get("t_send") is not None]
    lag_p99 = percentile(send_lags_ms, 99)
    loop_ms = [x * 1000 for x in loop_lags_s]
    loop_p99, loop_max = percentile(loop_ms, 99), max(loop_ms, default=None)

    throttle: dict[str, int] | None = None
    throttled_fraction: float | None = None
    throttle_ok: bool | None = None  # None = không đo được (chạy ngoài container); không tính là trượt
    if cgroup_before is not None and cgroup_after is not None:
        throttle = {k: cgroup_after.get(k, 0) - cgroup_before.get(k, 0) for k in cgroup_after}
        if "throttled_usec" in throttle and cgroup_elapsed_s:
            throttled_fraction = throttle["throttled_usec"] / (cgroup_elapsed_s * 1e6)
            throttle_ok = throttled_fraction < THROTTLE_MAX_FRACTION
        elif "nr_throttled" in throttle:
            # Không tính được tỷ lệ: quay về tiêu chí cũ, chặt hơn, thay vì bỏ qua kiểm tra
            throttle_ok = throttle["nr_throttled"] == 0

    checks: dict[str, Any] = {
        "send_lag_ms": {
            "p50": percentile(send_lags_ms, 50),
            "p99": lag_p99,
            "max": max(send_lags_ms, default=None),
        },
        "send_lag_ok": lag_p99 is not None and lag_p99 < SEND_LAG_P99_MAX_MS,
        "loop_lag_ms": {"p99": loop_p99, "max": loop_max},
        # None = không có mẫu nào (lượt quá ngắn để tác vụ đo kịp chạy); không tính là trượt
        "loop_lag_ok": None
        if loop_p99 is None
        else loop_p99 < LOOP_LAG_P99_MAX_MS and loop_max < LOOP_LAG_MAX_MS,
        "cpu_max_pct": round(cpu_max_fraction * 100, 1),
        "cpu_ok": cpu_max_fraction < CPU_MAX_FRACTION,
        "cgroup_throttle": throttle,
        "throttled_pct": None if throttled_fraction is None else round(throttled_fraction * 100, 4),
        "throttle_ok": throttle_ok,
    }
    checks["valid"] = all(checks[k] is not False for k in CHECK_KEYS)
    return checks
