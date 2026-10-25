"""Test cho sender.py với một vLLM giả.

Khái niệm: httpx.MockTransport = "mạng giả" của httpx: thay vì gửi request ra ngoài, httpx gọi hàm
    `handler` của test và trả về Response do hàm đó tạo. Nhờ vậy test được cả stream SSE, lỗi HTTP,
    timeout mà không cần server thật. Test async chạy bằng asyncio.run, không cần plugin pytest-asyncio.
Mục đích: Đọc stream đúng (t_first, t_last, usage), phân loại lỗi đúng (HTTP, stream bị cắt, timeout),
    và quan trọng nhất: open-loop thật sự, tức là server chậm không làm máy tạo tải gửi chậm theo.
"""

from __future__ import annotations

import asyncio
import csv
import io
import json

import httpx

from loadgen import sender
from loadgen.schedule import PlannedRequest

TARGET = sender.Target(base_url="http://vllm.test", model="qwen2.5-1.5b", api_key="k-test")


def _sse(chunks, first_delay=0.0, gap=0.0, done=True):
    """Body SSE giống vLLM: mỗi chunk một dòng `data: {...}` kèm một dòng trống."""

    async def gen():
        await asyncio.sleep(first_delay)
        for c in chunks:
            yield f"data: {json.dumps(c)}\n\n".encode()
            await asyncio.sleep(gap)
        if done:
            yield b"data: [DONE]\n\n"

    return gen()


ROLE = {"choices": [{"index": 0, "delta": {"role": "assistant"}}], "usage": None}
TOKEN = {"choices": [{"index": 0, "delta": {"content": "x"}}], "usage": None}
USAGE = {"choices": [], "usage": {"prompt_tokens": 300, "completion_tokens": 3}}


def _run(handler, plan, target=TARGET):
    out = io.StringIO()
    result = asyncio.run(sender.run(plan, target, out, prompt_seed=1, transport=httpx.MockTransport(handler)))
    return result, out.getvalue()


def _plan(n=1, spacing=0.0):
    return [PlannedRequest(id=i, t_sched=i * spacing, n_in_target=20) for i in range(n)]


def test_happy_path_records_ttft_usage_and_request_body():
    seen = {}

    async def handler(request: httpx.Request) -> httpx.Response:
        seen["body"] = json.loads(request.content)
        seen["auth"] = request.headers.get("authorization")
        seen["path"] = request.url.path
        # Chunk `role` (chưa có token) tới ngay; sau đó cứ 50 ms một chunk: token đầu ở ~50 ms
        return httpx.Response(200, content=_sse([ROLE, TOKEN, TOKEN, TOKEN, USAGE], gap=0.05))

    result, csv_text = _run(handler, _plan())
    (rec,) = result.records
    assert rec["status"] == 200 and rec["error"] == ""
    assert rec["n_in"] == 300 and rec["n_out"] == 3
    # TTFT tính từ chunk có nội dung, không phải chunk `role`. Chừa 20 ms vì asyncio.sleep(0.05) của
    # server giả có thể dậy sớm một khoảng bằng độ phân giải đồng hồ (~15 ms trên Windows).
    assert rec["t_first"] - rec["t_send"] >= 0.03
    assert rec["t_last"] - rec["t_first"] >= 0.07  # 3 token cách nhau ~50 ms
    # Body đúng Thông số §7: stream + usage, output cố định, ignore_eos
    body = seen["body"]
    assert body["stream"] is True and body["stream_options"] == {"include_usage": True}
    assert body["max_tokens"] == 256 and body["ignore_eos"] is True and body["model"] == "qwen2.5-1.5b"
    assert body["messages"][0]["content"].startswith("Request 0: ")
    assert seen["auth"] == "Bearer k-test" and seen["path"] == "/v1/chat/completions"
    # CSV: header đúng thứ tự cột và một dòng dữ liệu
    rows = list(csv.DictReader(io.StringIO(csv_text)))
    assert tuple(rows[0].keys()) == sender.FIELDS and len(rows) == 1


def test_stream_without_usage_is_an_error():
    async def handler(request):
        return httpx.Response(200, content=_sse([ROLE, TOKEN, TOKEN], done=False))

    (rec,) = _run(handler, _plan())[0].records
    assert rec["status"] == 200 and rec["error"] == "IncompleteStream"
    assert rec["t_first"] is not None  # vẫn có token, nhưng request bị tính là lỗi (Thông số §6)


def test_http_503_is_an_error():
    async def handler(request):
        return httpx.Response(503, text="no available server")

    (rec,) = _run(handler, _plan())[0].records
    assert rec["status"] == 503 and rec["error"] == "HTTPStatus"


def test_error_chunk_inside_stream():
    async def handler(request):
        return httpx.Response(200, content=_sse([ROLE, {"error": {"message": "boom"}}]))

    (rec,) = _run(handler, _plan())[0].records
    assert rec["error"] == "StreamError"


def test_whole_request_timeout():
    async def handler(request):
        await asyncio.sleep(2)  # server không trả lời trong thời hạn
        return httpx.Response(200, content=_sse([USAGE]))

    target = sender.Target(base_url="http://vllm.test", model="m", timeout_s=0.2)
    result, _ = _run(handler, _plan(), target)
    (rec,) = result.records
    assert rec["error"] == "Timeout"
    assert result.wall_s < 1.0


def test_open_loop_slow_server_does_not_delay_sends():
    # 20 request cách nhau 20 ms; server mất 0,5 s cho mỗi request. Closed-loop sẽ mất ~10 s và gửi trễ
    # dần; open-loop phải gửi đúng lịch và xong trong khoảng 0,4 s + 0,5 s.
    async def handler(request):
        return httpx.Response(200, content=_sse([ROLE, TOKEN, USAGE], first_delay=0.5))

    result, _ = _run(handler, _plan(n=20, spacing=0.02))
    assert len(result.records) == 20
    assert all(r["error"] == "" for r in result.records)
    lags = [r["t_send"] - r["t_sched"] for r in result.records]
    assert min(lags) >= 0  # không bao giờ gửi trước lịch
    assert max(lags) < 0.05  # Môi trường §17: lệch lịch p99 < 50 ms
    assert result.wall_s < 2.0


def test_never_sends_before_schedule_even_if_sleep_wakes_early(monkeypatch):
    # Giả lập asyncio.sleep dậy sớm 20 ms (chuyện có thật khi đồng hồ phân giải thấp). Bộ điều phối phải
    # ngủ tiếp cho tới đúng giờ, không được gửi trước lịch.
    real_sleep = asyncio.sleep

    async def early_sleep(delay, *args, **kwargs):
        await real_sleep(max(0.0, delay - 0.02), *args, **kwargs)

    monkeypatch.setattr(sender.asyncio, "sleep", early_sleep)

    async def handler(request):
        return httpx.Response(200, content=_sse([ROLE, TOKEN, USAGE]))

    result, _ = _run(handler, _plan(n=10, spacing=0.05))
    assert min(r["t_send"] - r["t_sched"] for r in result.records) >= 0


SERVER_HOLD_S = 1.0  # server giả giữ mỗi request bao lâu trước khi trả lời


async def _slow_sse_server(reader: asyncio.StreamReader, writer: asyncio.StreamWriter) -> None:
    """Server HTTP tối giản qua socket thật: đọc request, giữ SERVER_HOLD_S giây, trả SSE rồi đóng kết nối."""
    head = await reader.readuntil(b"\r\n\r\n")
    length = next(
        int(h.split(b":")[1]) for h in head.split(b"\r\n") if h.lower().startswith(b"content-length")
    )
    await reader.readexactly(length)
    await asyncio.sleep(SERVER_HOLD_S)
    body = b"".join(f"data: {json.dumps(c)}\n\n".encode() for c in (ROLE, TOKEN, USAGE)) + b"data: [DONE]\n\n"
    # Không có Content-Length + "connection: close": body kết thúc khi server đóng kết nối (HTTP/1.1)
    writer.write(b"HTTP/1.1 200 OK\r\ncontent-type: text/event-stream\r\nconnection: close\r\n\r\n" + body)
    await writer.drain()
    writer.close()


def test_no_client_side_connection_limit():
    # 150 request gần như cùng lúc, server giữ mỗi request 1 s. Nếu httpx giữ giới hạn mặc định 100 kết
    # nối, 50 request cuối phải chờ trong pool của client: t_send vẫn đúng lịch (nên kiểm tra lệch lịch
    # KHÔNG phát hiện được), nhưng TTFT của chúng dài thêm ~1 s. Test này dùng socket thật, vì
    # MockTransport bỏ qua pool kết nối.
    # So độ chênh TTFT (lớn nhất − nhỏ nhất) chứ không so TTFT tuyệt đối: trên Windows + Python 3.11, kết
    # nối loopback đầu tiên mất ~0,35 s, làm mọi TTFT cùng tăng (đo 25/10: 0,65–0,88 s), nhưng độ chênh
    # vẫn chỉ ~0,2 s. Có giới hạn pool thì độ chênh ≈ SERVER_HOLD_S.
    async def scenario():
        server = await asyncio.start_server(_slow_sse_server, "127.0.0.1", 0, backlog=512)
        port = server.sockets[0].getsockname()[1]
        target = sender.Target(base_url=f"http://127.0.0.1:{port}", model="m")
        async with server:
            return await sender.run(_plan(n=150, spacing=0.001), target, io.StringIO(), prompt_seed=1)

    result = asyncio.run(scenario())
    assert all(r["error"] == "" for r in result.records), {r["error"] for r in result.records}
    ttft = sorted(r["t_first"] - r["t_send"] for r in result.records)
    spread = ttft[-1] - ttft[0]
    assert spread < SERVER_HOLD_S / 2, f"TTFT chênh {spread:.2f} s: có request phải chờ kết nối ở client"
