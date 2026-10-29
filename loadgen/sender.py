"""Gửi request theo lịch, đọc câu trả lời dạng stream, ghi mỗi request một dòng CSV.

Khái niệm: Streaming (SSE, Server-Sent Events) = server trả câu trả lời thành nhiều "chunk", mỗi chunk là
    một dòng `data: {json}`; dòng cuối là `data: [DONE]`. Nhờ đó client đo được TTFT (thời gian tới token
    đầu) và TPOT (thời gian giữa các token). `stream_options.include_usage` yêu cầu server gửi thêm một
    chunk cuối chứa `usage` (số token vào/ra). Không có chunk này nghĩa là stream bị cắt giữa chừng.
Mục đích: Bộ phận chính của máy tạo tải open-loop (Môi trường §9). Hàm `run` ngủ tới đúng `t_sched` của
    từng request rồi tách nó thành một tác vụ riêng, không bao giờ chờ request trước trả lời xong.
"""

from __future__ import annotations

import asyncio
import csv
import json
import time
from collections.abc import Callable, Sequence
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, TextIO

import httpx

from loadgen.checks import CpuMonitor, LoopLagMonitor
from loadgen.prompts import make_prompt
from loadgen.schedule import PlannedRequest

# Cột của requests.csv (Môi trường §14.2), thêm `id`, `n_in_target`. Thời gian tính bằng giây kể từ lúc bắt
# đầu lượt; mốc tuyệt đối (t0_unix) nằm trong loadgen.json để ghép với Prometheus.
FIELDS = ("id", "t_sched", "t_send", "t_first", "t_last", "n_in_target", "n_in", "n_out", "status", "error")
CHAT_PATH = "/v1/chat/completions"


@dataclass(frozen=True)
class Target:
    """Đích gửi tải và tham số của mỗi request (Thông số §7)."""

    base_url: str  # ví dụ http://vllm.llm-serving.svc:8000 hoặc route Traefik riêng cho máy tạo tải
    model: str  # phải trùng --served-model-name của vLLM (qwen2.5-1.5b ở nhà, qwen2.5-7b ở cloud)
    api_key: str | None = None
    max_tokens: int = 256  # output cố định 256 token
    timeout_s: float = 120.0  # quá hạn tính là lỗi
    ignore_eos: bool = True  # tham số riêng của vLLM: sinh đủ max_tokens kể cả khi model muốn dừng


def build_payload(target: Target, prompt: str) -> dict[str, Any]:
    """Body của request chat completions theo chuẩn OpenAI, cộng `ignore_eos` của vLLM.

    ignore_eos + max_tokens cố định: mọi request sinh đúng 256 token, nên thời gian phục vụ chỉ còn phụ
    thuộc độ dài prompt và mức tải, không phụ thuộc model "nói dài hay ngắn".
    """
    payload: dict[str, Any] = {
        "model": target.model,
        "messages": [{"role": "user", "content": prompt}],
        "max_tokens": target.max_tokens,
        "stream": True,
        "stream_options": {"include_usage": True},
    }
    if target.ignore_eos:
        payload["ignore_eos"] = True
    return payload


async def one_request(
    client: httpx.AsyncClient,
    target: Target,
    req: PlannedRequest,
    clock: Callable[[], float],
    prompt_seed: int,
) -> dict[str, Any]:
    """Gửi một request, trả về một dòng cho requests.csv. Không bao giờ ném lỗi: lỗi ghi vào cột `error`."""
    rec: dict[str, Any] = dict.fromkeys(FIELDS)
    rec.update(id=req.id, t_sched=req.t_sched, n_in_target=req.n_in_target, error="")
    payload = build_payload(target, make_prompt(req.id, req.n_in_target, prompt_seed))
    rec["t_send"] = clock()
    try:
        # Timeout cho CẢ request (tới khi đọc xong stream). Cái bẫy: `timeout` của httpx tính cho TỪNG thao
        # tác (kết nối, mỗi lần đọc…), nên một stream nhỏ giọt token có thể kéo dài mãi mà không bao giờ
        # "timeout". asyncio.timeout bao trọn cả khối, hết hạn thì huỷ và ném TimeoutError.
        async with asyncio.timeout(target.timeout_s):
            async with client.stream("POST", CHAT_PATH, json=payload) as resp:
                rec["status"] = resp.status_code
                if resp.status_code != 200:
                    await resp.aread()  # đọc hết body lỗi để trả kết nối về pool
                    rec["error"] = "HTTPStatus"
                    return rec
                async for line in resp.aiter_lines():
                    if not line.startswith("data: "):
                        continue  # dòng trống hoặc comment của SSE
                    data = line[len("data: ") :]
                    if data == "[DONE]":
                        break
                    chunk = json.loads(data)
                    if "error" in chunk:  # vLLM báo lỗi giữa stream (status vẫn là 200)
                        rec["error"] = "StreamError"
                        return rec
                    choices = chunk.get("choices") or []
                    # Chỉ tính chunk có nội dung: chunk đầu tiên thường chỉ có `role`, chưa có token nào
                    if choices and (choices[0].get("delta") or {}).get("content"):
                        t = clock()
                        if rec["t_first"] is None:
                            rec["t_first"] = t
                        rec["t_last"] = t
                    usage = chunk.get("usage")  # vLLM có thể gửi "usage": null ở các chunk giữa
                    if usage:
                        rec["n_in"] = usage.get("prompt_tokens")
                        rec["n_out"] = usage.get("completion_tokens")
        if rec["n_out"] is None:
            rec["error"] = "IncompleteStream"  # không có chunk usage: stream bị cắt (Thông số §6)
    except TimeoutError:
        rec["error"] = "Timeout"
    except Exception as e:  # lỗi mạng, lỗi giao thức, JSON hỏng: ghi tên lỗi rồi đi tiếp
        rec["error"] = type(e).__name__
    return rec


class CsvSink:
    """Ghi requests.csv, flush sau MỖI dòng.

    Flush ngay để: (1) runner phát hiện máy tạo tải treo khi quá 60 s không có dòng mới (Kế hoạch §9.5);
    (2) lượt bị dừng giữa chừng vẫn giữ được các dòng đã xong.
    """

    def __init__(self, fh: TextIO) -> None:
        self._fh = fh
        self._writer = csv.DictWriter(fh, fieldnames=FIELDS)
        self._writer.writeheader()
        fh.flush()

    def write(self, rec: dict[str, Any]) -> None:
        row = {k: (round(v, 6) if isinstance(v, float) else v) for k, v in rec.items()}
        self._writer.writerow(row)
        self._fh.flush()


@dataclass
class RunResult:
    records: list[dict[str, Any]]
    t0_unix: float  # giờ hệ thống (Unix) ứng với t = 0 của lượt
    wall_s: float  # thời gian thực của cả lượt, gồm lúc chờ các request cuối
    loop_lags_s: list[float] = field(default_factory=list)
    cpu_max_fraction: float = 0.0


async def run(
    plan: Sequence[PlannedRequest],
    target: Target,
    out_csv: TextIO,
    prompt_seed: int,
    transport: httpx.AsyncBaseTransport | None = None,  # unit test truyền MockTransport
) -> RunResult:
    """Chạy cả lượt: gửi đúng lịch, chờ mọi request kết thúc, trả về các dòng và số đo tự kiểm tra."""
    headers = {"Authorization": f"Bearer {target.api_key}"} if target.api_key else {}
    # Cái bẫy: httpx mặc định chỉ mở tối đa 100 kết nối. Quá 100 request đồng thời thì request thứ 101 phải
    # chờ trong pool của CLIENT, tức là máy tạo tải lặng lẽ biến thành closed-loop. None = không giới hạn.
    limits = httpx.Limits(max_connections=None, max_keepalive_connections=None)
    # Timeout của httpx chỉ giữ cho bước kết nối; timeout của cả request do asyncio.timeout lo (one_request)
    timeout = httpx.Timeout(None, connect=10.0)
    sink = CsvSink(out_csv)
    records: list[dict[str, Any]] = []
    loop_mon, cpu_mon = LoopLagMonitor(), CpuMonitor()

    async with httpx.AsyncClient(
        base_url=target.base_url, headers=headers, limits=limits, timeout=timeout, transport=transport
    ) as client:
        t0_perf, t0_unix = time.perf_counter(), time.time()

        def clock() -> float:
            return time.perf_counter() - t0_perf  # perf_counter: đồng hồ đơn điệu, không nhảy khi chỉnh giờ

        async def worker(req: PlannedRequest) -> None:
            rec = await one_request(client, target, req, clock, prompt_seed)
            sink.write(rec)
            records.append(rec)

        monitors = [asyncio.create_task(loop_mon.run()), asyncio.create_task(cpu_mon.run())]
        tasks: set[asyncio.Task[None]] = set()
        for req in plan:
            # Ngủ lặp tới khi thật sự đến giờ: asyncio coi một hẹn giờ là "đến hạn" nếu còn cách hiện tại
            # ít hơn độ phân giải đồng hồ, nên có thể dậy SỚM (~15 ms trên Windows, gần 0 trên Linux).
            delay = req.t_sched - clock()
            while delay > 0:
                await asyncio.sleep(delay)
                delay = req.t_sched - clock()
            # Tách thành tác vụ riêng rồi đi tiếp ngay: đây là chỗ làm nên "open-loop".
            # Giữ tham chiếu trong `tasks`, vì asyncio chỉ giữ tham chiếu yếu tới tác vụ đang chạy.
            task = asyncio.create_task(worker(req))
            tasks.add(task)
            task.add_done_callback(tasks.discard)
        if tasks:
            await asyncio.gather(*tasks)
        wall_s = clock()
        for m in monitors:
            m.cancel()
        await asyncio.gather(*monitors, return_exceptions=True)

    return RunResult(
        records=records,
        t0_unix=t0_unix,
        wall_s=wall_s,
        loop_lags_s=loop_mon.lags_s,
        cpu_max_fraction=cpu_mon.max_fraction,
    )


def open_csv(path: Path) -> TextIO:
    """Mở requests.csv để ghi; mode "x" = báo lỗi nếu file đã có, để không ghi đè dữ liệu lượt trước."""
    return path.open("x", newline="", encoding="utf-8")
