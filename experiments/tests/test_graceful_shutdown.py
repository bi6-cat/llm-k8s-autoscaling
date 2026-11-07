"""Unit test cho cách phân loại stream của experiments/ops/graceful_shutdown.py.

Khái niệm: classify() quyết định một stream là ok / cut / rejected; kết luận "0 stream bị cắt" (N4) dựa hoàn
    toàn vào hàm này, nên mỗi nhánh có một test.
Mục đích: Bắt lỗi phân loại sai trước khi dùng số liệu cho luận văn.
"""

from __future__ import annotations

from experiments.ops.graceful_shutdown import StreamResult, classify

MAX = 100


def _r(**kw: object) -> StreamResult:
    return StreamResult(idx=0, t_start=0.0, **kw)  # type: ignore[arg-type]


def test_ok_needs_done_and_all_tokens() -> None:
    assert classify(_r(status=200, done=True, completion_tokens=MAX), MAX) == "ok"


def test_cut_when_stream_ends_without_done() -> None:
    # Server đóng kết nối giữa chừng (vLLM abort): đã nhận 200, có văn bản, nhưng không có [DONE]
    assert classify(_r(status=200, chunks=10, done=False, error="IncompleteRead"), MAX) == "cut"


def test_cut_when_done_but_tokens_missing() -> None:
    # Có [DONE] nhưng thiếu token: request bị huỷ phía server rồi kết thúc stream "êm"
    assert classify(_r(status=200, done=True, completion_tokens=40), MAX) == "cut"


def test_rejected_when_no_http_200() -> None:
    assert classify(_r(status=None, error="ConnectionRefusedError"), MAX) == "rejected"
    assert classify(_r(status=503), MAX) == "rejected"
