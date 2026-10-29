"""Lịch gửi: thời điểm gửi và độ dài prompt của từng request, sinh từ seed.

Khái niệm: Quá trình Poisson = mô hình chuẩn cho "người dùng độc lập gửi request": khoảng cách giữa hai
    request liên tiếp có phân phối mũ, trung bình 1/λ. Khi λ thay đổi theo thời gian (KB2, KB3), dùng
    phép "thinning" (Lewis–Shedler): sinh ứng viên với tốc độ cố định λ_max, rồi giữ mỗi ứng viên ở thời
    điểm t với xác suất λ(t)/λ_max. Kết quả đúng là một quá trình Poisson có tốc độ λ(t).
Mục đích: Lịch được sinh TRƯỚC khi gửi (open-loop) và chỉ phụ thuộc vào (kịch bản, số thứ tự lượt), nên
    mọi cấu hình (S1, S4, A1, A2…) nhận đúng cùng một chuỗi request, so sánh mới công bằng (Môi trường §9).
"""

from __future__ import annotations

import hashlib
import random
from dataclasses import dataclass

from loadgen.scenarios import Scenario

# Độ dài prompt, phân phối đều (Thông số §7). Đơn vị là số từ; mỗi từ trong prompts.WORDS là đúng 1 token
# của tokenizer Qwen2.5, nên số từ ≈ số token (xem prompts.py).
PROMPT_MIN = 256
PROMPT_MAX = 1024


@dataclass(frozen=True)
class PlannedRequest:
    id: int
    t_sched: float  # thời điểm phải gửi, giây tính từ lúc bắt đầu lượt
    n_in_target: int  # số từ của prompt (≈ số token văn bản, chưa tính chat template)


def derive_seed(scenario: str, run_index: int, stream: str) -> int:
    """Seed cố định cho (kịch bản, số thứ tự lượt, luồng ngẫu nhiên).

    Dùng SHA-256 thay cho hash() có sẵn của Python, vì hash() của chuỗi đổi giá trị giữa các lần chạy
    (PYTHONHASHSEED), làm lịch không tái lập được.
    Mỗi `stream` ("time", "prompt") một seed riêng: đổi khoảng độ dài prompt không làm đổi thời điểm gửi.
    """
    digest = hashlib.sha256(f"{scenario}:{run_index}:{stream}".encode()).digest()
    return int.from_bytes(digest[:8], "big")


def poisson_times(scenario: Scenario, rng: random.Random) -> list[float]:
    """Thời điểm gửi theo quá trình Poisson có tốc độ scenario.rate(t), bằng phép thinning."""
    if scenario.rate_max <= 0:
        return []
    times: list[float] = []
    t = 0.0
    while True:
        # Ứng viên kế tiếp của quá trình Poisson tốc độ λ_max: cách ứng viên trước một khoảng ~ Exp(λ_max)
        t += rng.expovariate(scenario.rate_max)
        if t >= scenario.duration_s:
            return times
        # Giữ ứng viên với xác suất λ(t)/λ_max. Luôn rút số ngẫu nhiên (kể cả khi λ = λ_max) để chuỗi số
        # ngẫu nhiên không phụ thuộc vào hình dạng λ(t).
        if rng.random() * scenario.rate_max < scenario.rate(t):
            times.append(t)


def build_plan(
    scenario: Scenario,
    run_index: int,
    prompt_min: int = PROMPT_MIN,
    prompt_max: int = PROMPT_MAX,
) -> list[PlannedRequest]:
    """Toàn bộ lịch của một lượt: id tăng dần theo thời điểm gửi."""
    rng_time = random.Random(derive_seed(scenario.name, run_index, "time"))
    rng_len = random.Random(derive_seed(scenario.name, run_index, "prompt"))
    return [
        PlannedRequest(id=i, t_sched=t, n_in_target=rng_len.randint(prompt_min, prompt_max))
        for i, t in enumerate(poisson_times(scenario, rng_time))
    ]
