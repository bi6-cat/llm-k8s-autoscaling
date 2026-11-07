"""Chạy lịch gửi trên nhiều tiến trình, gom kết quả về một requests.csv.

Khái niệm:
    Event loop của asyncio chạy trên MỘT luồng, và GIL của Python cũng chỉ cho một luồng chạy mã Python
    tại một thời điểm, nên một tiến trình loadgen dùng tối đa một lõi dù pod có bao nhiêu lõi. Mỗi chunk
    SSE tốn khoảng 0,2 ms CPU, phần lớn ở httpx và asyncio cho mỗi lần đọc mạng (json.loads chỉ ~2 µs). Đo
    07/11 trên laptop: 10 req/s × 256 token (~2.560 chunk/s) tốn 53–58% một lõi, 20 req/s lên 87–88%, vượt
    ngưỡng CPU 70%. Muốn gửi nhiều hơn thì phải thêm TIẾN TRÌNH, mỗi tiến trình một event loop.
    multiprocessing "spawn": tiến trình con là một trình thông dịch Python mới, import lại module, không
    thừa kế trạng thái của cha (khác "fork"). Khởi động chậm hơn (~0,3 s) nhưng an toàn, và giống nhau
    trên Linux lẫn Windows (máy dev).
    Pipe: kênh hai chiều giữa hai tiến trình; `send` gửi một đối tượng Python (đóng gói bằng pickle).
Mục đích:
    Chia lịch theo `id % k` cho k tiến trình con. Lịch gộp lại vẫn đúng là lịch của một tiến trình (cùng
    seed, cùng `id`, cùng `t_sched`), nên số tiến trình không làm đổi tải mà hệ thống nhận (Môi trường §9).
    Các bước:
      1. Cha tạo k tiến trình con; mỗi con báo "ready" khi đã import xong.
      2. Cha đặt mốc chung t0 = giờ hiện tại + START_MARGIN_S rồi gửi cho mọi con: mọi `t_send`, `t_first`
         của các con tính từ cùng một mốc, ghép được vào một requests.csv.
      3. Mỗi request xong, con gửi dòng kết quả về cha; cha ghi CSV và flush ngay, như khi chạy một tiến
         trình (sender.CsvSink).
      4. Hết lịch, con gửi số đo tự kiểm của nó (độ trễ event loop, CPU); cha chấm theo tiến trình tệ nhất
         (checks.summarize).
      5. Một con lỗi thì lượt đã hỏng: cha dừng ngay các con còn lại, không chạy nốt phần lịch còn lại (trên
         máy thuê, phần đó là tiền thuê GPU bỏ phí), rồi trả kết quả để ghi loadgen.json.
"""

from __future__ import annotations

import asyncio
import multiprocessing
import time
import traceback
from collections.abc import Sequence
from dataclasses import dataclass
from multiprocessing.connection import Connection, wait
from typing import Any

from loadgen import sender
from loadgen.schedule import PlannedRequest

READY_TIMEOUT_S = 60.0  # chờ tiến trình con import xong (httpx…); VM chậm vẫn dư nhiều
# Khoảng từ lúc mọi con đã sẵn sàng tới t = 0: đủ để con nhận mốc và tạo HTTP client. Không ảnh hưởng số
# đo, vì `t0_unix` ghi đúng mốc này.
START_MARGIN_S = 1.0


@dataclass
class WorkerStats:
    """Số đo tự kiểm của một tiến trình (một event loop)."""

    n_done: int
    wall_s: float
    loop_lags_s: list[float]
    cpu_max_fraction: float
    error: str | None = None  # dòng cuối traceback nếu tiến trình con lỗi, hoặc lý do bị cha dừng

    @classmethod
    def from_run(cls, r: sender.RunResult) -> WorkerStats:
        return cls(len(r.records), r.wall_s, r.loop_lags_s, r.cpu_max_fraction)


@dataclass
class LoadResult:
    records_by_worker: list[list[dict[str, Any]]]  # dòng kết quả theo tiến trình, theo thứ tự nhận được
    t0_unix: float
    wall_s: float  # thời gian thực của cả lượt: tiến trình xong muộn nhất
    workers: list[WorkerStats]

    @property
    def records(self) -> list[dict[str, Any]]:
        return [rec for rs in self.records_by_worker for rec in rs]


def split_plan(plan: Sequence[PlannedRequest], k: int) -> list[list[PlannedRequest]]:
    """Chia lịch cho k tiến trình theo `id % k` (xoay vòng). Hàm thuần.

    Xoay vòng thay vì chia theo khúc thời gian: mọi tiến trình cùng bận suốt lượt, mỗi tiến trình nhận
    khoảng 1/k số request ở MỌI pha của λ(t). Mỗi request đều sinh 256 token (ignore_eos), nên số chunk/s
    cũng chia đều.
    """
    return [[r for r in plan if r.id % k == j] for j in range(k)]


class _PipeSink:
    """RecordSink của tiến trình con: gửi từng dòng kết quả về cha qua Pipe."""

    def __init__(self, conn: Connection) -> None:
        self._conn = conn

    def write(self, rec: dict[str, Any]) -> None:
        # send() chặn event loop trong lúc ghi vào pipe, nhưng một dòng chỉ vài trăm byte (vài µs) và cha
        # đọc liên tục, nên pipe không đầy.
        self._conn.send(("rec", rec))


def _worker(plan: list[PlannedRequest], target: sender.Target, prompt_seed: int, conn: Connection) -> None:
    """Thân tiến trình con: báo sẵn sàng, chờ mốc t0, chạy phần lịch của mình, gửi số đo về cha."""
    try:
        conn.send(("ready", None))
        t0_unix = conn.recv()
        r = asyncio.run(sender.run(plan, target, _PipeSink(conn), prompt_seed, t0_unix=t0_unix))
        conn.send(("done", WorkerStats.from_run(r)))
    except BaseException:
        # Báo lỗi cho cha rồi ném lại để traceback đầy đủ vẫn in ra stderr (vào log của pha)
        try:
            conn.send(("error", traceback.format_exc()))
        except OSError:
            pass  # cha đã đóng kênh
        raise
    finally:
        conn.close()


def _last_line(text: str) -> str:
    lines = [ln for ln in text.strip().splitlines() if ln.strip()]
    return lines[-1] if lines else text


def run_load(
    plan: Sequence[PlannedRequest],
    target: sender.Target,
    sink: sender.RecordSink,
    prompt_seed: int,
    n_workers: int = 1,
) -> LoadResult:
    """Chạy cả lượt với n_workers tiến trình. n_workers = 1: chạy ngay trong tiến trình này, như trước."""
    if n_workers == 1:
        r = asyncio.run(sender.run(plan, target, sink, prompt_seed))
        return LoadResult([r.records], r.t0_unix, r.wall_s, [WorkerStats.from_run(r)])

    ctx = multiprocessing.get_context("spawn")
    procs: list[Any] = []
    conns: list[Connection] = []
    try:
        for j, part in enumerate(split_plan(plan, n_workers)):
            parent_end, child_end = ctx.Pipe()
            p = ctx.Process(
                target=_worker,
                args=(part, target, prompt_seed, child_end),
                name=f"loadgen-{j}",
                daemon=True,  # cha thoát thì con bị dừng theo, không để lại tiến trình mồ côi gửi tải
            )
            p.start()
            # Cha không dùng đầu này. Phải đóng nó, để khi con chết thì đầu của cha đọc được EOF thay vì
            # chờ mãi (đầu của con vẫn mở trong chính cha thì pipe chưa bao giờ "đóng hết").
            child_end.close()
            procs.append(p)
            conns.append(parent_end)

        for j, c in enumerate(conns):
            if not c.poll(READY_TIMEOUT_S):
                raise RuntimeError(f"tiến trình con {j} chưa sẵn sàng sau {READY_TIMEOUT_S:.0f} s")
            try:
                kind, payload = c.recv()
            except EOFError:
                raise RuntimeError(f"tiến trình con {j} thoát khi đang khởi động (xem stderr)") from None
            if kind != "ready":
                raise RuntimeError(f"tiến trình con {j} lỗi khi khởi động:\n{payload}")

        t0_unix = time.time() + START_MARGIN_S
        for c in conns:
            c.send(t0_unix)

        by_worker: list[list[dict[str, Any]]] = [[] for _ in conns]
        stats: dict[int, WorkerStats] = {}
        pending = {c: j for j, c in enumerate(conns)}
        while pending:
            # wait() trả về các đầu pipe đang có dữ liệu (hoặc EOF), nên cha nhận từ k con mà không bận chờ
            for c in wait(list(pending)):
                j = pending[c]
                try:
                    kind, payload = c.recv()
                except EOFError:
                    payload, kind = "tiến trình con thoát mà không gửi kết quả", "error"
                if kind == "rec":
                    sink.write(payload)
                    by_worker[j].append(payload)
                    continue
                del pending[c]
                if kind == "done":
                    stats[j] = payload
                    continue
                stats[j] = WorkerStats(len(by_worker[j]), 0.0, [], 0.0, error=_last_line(str(payload)))
                for j2 in pending.values():
                    procs[j2].terminate()
                    stats[j2] = WorkerStats(
                        len(by_worker[j2]), 0.0, [], 0.0, error=f"bị dừng vì tiến trình {j} lỗi"
                    )
                pending.clear()
                break
    finally:
        for c in conns:
            c.close()
        for p in procs:
            p.join(timeout=10)
            if p.is_alive():
                p.terminate()

    workers = [stats[j] for j in range(n_workers)]
    return LoadResult(by_worker, t0_unix, max(w.wall_s for w in workers), workers)
