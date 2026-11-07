"""Test cho workers.py: chia lịch và chạy nhiều tiến trình thật.

Khái niệm: Test chạy nhiều tiến trình phải dùng server qua socket thật, vì tiến trình con không nhận được
    MockTransport của tiến trình test. Server giả chạy trong một luồng của tiến trình test
    (ThreadingHTTPServer, mỗi request một luồng) và ghi lại giờ hệ thống lúc mỗi request tới.
Mục đích: Lịch gộp từ k tiến trình đúng bằng lịch gốc; mọi tiến trình gửi theo CÙNG một mốc t0 (so giờ
    request tới server với t0_unix + t_sched); một tiến trình chết giữa chừng thì lượt bị đánh dấu lỗi
    chứ không treo.
"""

from __future__ import annotations

import csv
import io
import json
import threading
import time
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

import pytest

from loadgen import sender, workers
from loadgen.schedule import PlannedRequest

ROLE = {"choices": [{"index": 0, "delta": {"role": "assistant"}}], "usage": None}
TOKEN = {"choices": [{"index": 0, "delta": {"content": "x"}}], "usage": None}
USAGE = {"choices": [], "usage": {"prompt_tokens": 30, "completion_tokens": 2}}


def _plan(n, spacing):
    return [PlannedRequest(id=i, t_sched=i * spacing, n_in_target=20) for i in range(n)]


def test_split_plan_round_robin_keeps_every_request_once():
    plan = _plan(10, 0.1)
    parts = workers.split_plan(plan, 3)
    assert [[r.id for r in p] for p in parts] == [[0, 3, 6, 9], [1, 4, 7], [2, 5, 8]]
    # Gộp lại đúng bằng lịch gốc: số tiến trình không làm đổi tải
    assert sorted((r for p in parts for r in p), key=lambda r: r.id) == plan
    assert workers.split_plan(plan[:1], 3) == [plan[:1], [], []]  # ít request hơn tiến trình


class _SseHandler(BaseHTTPRequestHandler):
    """vLLM giả: trả một stream SSE ngắn; ghi (id, giờ hệ thống lúc request tới) vào server.arrivals."""

    def do_POST(self):  # tên do http.server quy định
        t_arrive = time.time()
        body = json.loads(self.rfile.read(int(self.headers["Content-Length"])))
        rid = int(body["messages"][0]["content"].split(":")[0].removeprefix("Request "))
        with self.server.lock:
            self.server.arrivals[rid] = t_arrive
        self.send_response(200)
        self.send_header("content-type", "text/event-stream")
        self.end_headers()
        # HTTP/1.0 (mặc định của BaseHTTPRequestHandler): body kết thúc khi server đóng kết nối
        for c in (ROLE, TOKEN, TOKEN, USAGE):
            self.wfile.write(f"data: {json.dumps(c)}\n\n".encode())
        self.wfile.write(b"data: [DONE]\n\n")

    def log_message(self, *args):
        pass  # không in mỗi request ra stderr


@pytest.fixture
def sse_server():
    srv = ThreadingHTTPServer(("127.0.0.1", 0), _SseHandler)
    srv.daemon_threads = True
    srv.lock, srv.arrivals = threading.Lock(), {}
    th = threading.Thread(target=srv.serve_forever, daemon=True)
    th.start()
    yield srv
    srv.shutdown()
    srv.server_close()


def _target(srv):
    return sender.Target(base_url=f"http://127.0.0.1:{srv.server_address[1]}", model="m")


def test_two_workers_share_t0_and_write_one_csv(sse_server):
    plan = _plan(30, 0.02)
    out = io.StringIO()
    result = workers.run_load(plan, _target(sse_server), sender.CsvSink(out), prompt_seed=1, n_workers=2)

    assert sorted(r["id"] for r in result.records) == list(range(30))
    assert all(r["error"] == "" for r in result.records), {r["error"] for r in result.records}
    assert [w.n_done for w in result.workers] == [15, 15] and all(w.error is None for w in result.workers)
    assert all(w.loop_lags_s for w in result.workers)  # mỗi tiến trình tự đo event loop của nó
    # Một requests.csv, mỗi request đúng một dòng, ghi ngay khi tiến trình con báo về
    rows = list(csv.DictReader(io.StringIO(out.getvalue())))
    assert sorted(int(r["id"]) for r in rows) == list(range(30))
    # Mốc chung: request tới server đúng lúc t0_unix + t_sched, dù do tiến trình nào gửi. Nếu một tiến
    # trình tự lấy mốc riêng thì lệch cả giây (START_MARGIN_S). Chừa 100 ms cho đồng hồ Windows và loopback.
    for rid, t_arrive in sse_server.arrivals.items():
        assert abs(t_arrive - (result.t0_unix + plan[rid].t_sched)) < 0.1, rid
    lags = [r["t_send"] - r["t_sched"] for r in result.records]
    assert min(lags) >= 0 and max(lags) < 0.05  # Môi trường §17: lệch lịch < 50 ms


def test_worker_crash_stops_the_others_and_is_reported(sse_server):
    # Request id 1 (của tiến trình 1) có t_sched hỏng: sender.run của tiến trình đó ném TypeError ngay khi
    # nhận t0. Tiến trình 0 còn một request ở giây thứ 30: cha phải dừng nó ngay vì lượt đã hỏng, không chờ
    # nó chạy hết lịch, và vẫn trả kết quả (không treo).
    plan = [
        PlannedRequest(id=0, t_sched=30.0, n_in_target=20),
        PlannedRequest(id=1, t_sched=None, n_in_target=20),
    ]
    t_start = time.monotonic()
    result = workers.run_load(plan, _target(sse_server), sender.CsvSink(io.StringIO()), 1, n_workers=2)

    assert time.monotonic() - t_start < 15
    stopped, bad = result.workers
    assert bad.error is not None and "TypeError" in bad.error
    assert stopped.error == "bị dừng vì tiến trình 1 lỗi"
    assert result.records == []


def test_worker_without_requests_reports_zero_wall_time(sse_server):
    # 1 request, 2 tiến trình: tiến trình 1 không có gì để gửi, xong trước cả t0 (t0 ở tương lai 1 s)
    result = workers.run_load(
        _plan(1, 0.0), _target(sse_server), sender.CsvSink(io.StringIO()), 1, n_workers=2
    )
    assert [w.n_done for w in result.workers] == [1, 0]
    assert result.workers[1].wall_s == 0.0 and result.wall_s > 0
