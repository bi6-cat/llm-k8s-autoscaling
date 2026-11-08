"""Kịch bản tải: tốc độ gửi λ(t) và các pha dùng khi phân tích.

Khái niệm: λ(t) (lambda) = tốc độ gửi trung bình tại thời điểm t, đơn vị request/giây. Kịch bản viết λ
    theo đơn vị C = năng lực một replica (tốc độ lớn nhất mà một replica vẫn đạt SLO, đo ở ĐG1), nên cùng
    một kịch bản dùng được cho cả GPU nhà và GPU thuê, chỉ đổi C.
Mục đích: Định nghĩa KB1, KB2, KB3 đúng như Thông số §7, cộng chế độ tốc độ cố định cho ĐG1 (mỗi mức λ
    chạy một lần). Pha (`steady`, `spike`…) được ghi vào loadgen.json để bước phân tích biết cắt cửa sổ nào.
"""

from __future__ import annotations

import bisect
from collections.abc import Callable, Sequence
from dataclasses import dataclass

MINUTE = 60.0


@dataclass(frozen=True)
class Scenario:
    """Một kịch bản tải đã cụ thể hoá theo C (thời gian tính bằng giây, tốc độ bằng request/giây)."""

    name: str
    duration_s: float
    rate: Callable[[float], float]  # λ(t), t tính từ lúc bắt đầu lượt
    rate_max: float  # cận trên của λ(t), cần cho phép "thinning" ở schedule.py
    phases: dict[str, tuple[float, float]]  # tên pha → [bắt đầu, kết thúc) tính bằng giây


def piecewise_linear(points: Sequence[tuple[float, float]]) -> Callable[[float], float]:
    """Hàm tuyến tính từng đoạn đi qua các điểm (t, giá trị); ngoài khoảng thì giữ giá trị ở đầu mút.

    Dùng cho các đoạn "tăng từ a lên b trong 30 giây" của KB2, KB3.
    """
    ts = [t for t, _ in points]
    vs = [v for _, v in points]
    if ts != sorted(ts):
        raise ValueError("các điểm phải sắp theo thời gian tăng dần")

    def f(t: float) -> float:
        if t <= ts[0]:
            return vs[0]
        if t >= ts[-1]:
            return vs[-1]
        # bisect_right: vị trí của điểm đầu tiên có thời gian > t, nên t nằm trong đoạn [i-1, i]
        i = bisect.bisect_right(ts, t)
        t0, t1, v0, v1 = ts[i - 1], ts[i], vs[i - 1], vs[i]
        if t1 == t0:  # hai điểm cùng thời gian = bước nhảy; lấy giá trị sau bước
            return v1
        return v0 + (v1 - v0) * (t - t0) / (t1 - t0)

    return f


def _minutes(points: Sequence[tuple[float, float]], c: float) -> list[tuple[float, float]]:
    """Đổi (phút, bội số của C) sang (giây, request/giây)."""
    return [(t * MINUTE, k * c) for t, k in points]


def kb1(c: float) -> Scenario:
    """KB1 – thấp, ổn định: 0,5 C trong 12 phút. Hai phút đầu để ổn định, không tính.

    12 phút (trước 08/11 là 20): pha steady còn 10 phút = hai cửa sổ scale-down 300 s, đủ thấy flapping
    (đổi chiều trong 5 phút); ở 0,5 C vẫn có hàng nghìn request cho p95, p99.
    """
    return Scenario(
        name="KB1",
        duration_s=12 * MINUTE,
        rate=lambda _t: 0.5 * c,
        rate_max=0.5 * c,
        phases={"steady": (2 * MINUTE, 12 * MINUTE)},
    )


def kb2(c: float, n_replicas: int = 4) -> Scenario:
    """KB2 – tăng đột ngột rồi giảm: 0,5 C → 0,75 × N × C trong 30 s ở phút 4, giữ tới phút 11, về 0,5 C
    trong 30 s, giữ tới phút 21.

    Đỉnh 0,75 × N × C cùng quy tắc với KB3: HPA cần đúng N replica (= 3 C khi N = 4, như bản cũ; = 1,5 C khi
    N = 2). Giảm trở lại ở phút 11 để cùng một lượt kiểm được cả scale-up (pha spike) lẫn scale-down an toàn
    (pha drop, N4).
    Thời lượng (trước 08/11 là 25 phút, pre [2, 5], spike [5, 15], drop [15, 25]):
      - pre 2 phút: chỉ cần mức nền trước khi tăng.
      - spike 7 phút: dài hơn cold start + thời gian hồi phục (N2a, N2b). Nếu cold start trên VM > 2,5 phút
        thì nới lại (đo ở V0).
      - drop giữ 10 phút: với N = 4, cửa sổ 300 s rồi bớt 1 pod mỗi 60 s, pod cuối bị xoá ở ~8 phút sau
        khi tải giảm; cần thấy trọn các lần xoá này trong pha drop.
    """
    peak = 0.75 * n_replicas
    points = _minutes([(0, 0.5), (4, 0.5), (4.5, peak), (11, peak), (11.5, 0.5), (21, 0.5)], c)
    return Scenario(
        name="KB2",
        duration_s=21 * MINUTE,
        rate=piecewise_linear(points),
        rate_max=max(0.5, peak) * c,
        phases={
            "pre": (2 * MINUTE, 4 * MINUTE),
            "spike": (4 * MINUTE, 11 * MINUTE),
            "drop": (11 * MINUTE, 21 * MINUTE),
        },
    )


def kb3(c: float, n_replicas: int = 4) -> Scenario:
    """KB3 – cao, kéo dài: tăng từ 0,5 C lên 0,75 × N × C trong 5 phút đầu, giữ tới phút 17.

    Dừng ở 0,75 × N (không phải N) để HPA cần đúng N replica, không vượt số GPU (Môi trường §10).
    17 phút (trước 08/11 là 25): pha sustain còn 12 phút, vẫn hơn hai cửa sổ 300 s để thấy flapping.
    """
    peak = 0.75 * n_replicas
    points = _minutes([(0, 0.5), (5, peak), (17, peak)], c)
    return Scenario(
        name="KB3",
        duration_s=17 * MINUTE,
        rate=piecewise_linear(points),
        rate_max=max(0.5, peak) * c,
        phases={"ramp": (0.0, 5 * MINUTE), "sustain": (5 * MINUTE, 17 * MINUTE)},
    )


def constant(rate: float, duration_s: float) -> Scenario:
    """Tốc độ cố định `rate` request/giây trong `duration_s` giây: một mức λ của ĐG1 (Thông số §8.3).

    Đơn vị ở đây là request/giây, không phải C, vì ĐG1 chính là phép đo để tìm ra C.
    """
    return Scenario(
        name="CONST",
        duration_s=duration_s,
        rate=lambda _t: rate,
        rate_max=rate,
        phases={"steady": (0.0, duration_s)},
    )


SCENARIOS = ("KB1", "KB2", "KB3", "CONST")
