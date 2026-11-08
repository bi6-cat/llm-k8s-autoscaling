"""Đọc log khởi động của vLLM, lấy mốc thời gian các pha cold start (Kiến trúc §7.2). Hàm thuần, có unit test.

Khái niệm: Cold start = thời gian từ lúc có pod mới tới lúc pod nhận được request. Kiến trúc §7.2 chia thành
    8 pha. Pha 1–3 (xếp lịch, chuẩn bị pod, kéo image) và đoạn cuối pha 8 (probe đạt → pod Ready) chỉ thấy
    ở phía Kubernetes (pod conditions, event). Pha 4–7 diễn ra bên trong tiến trình vLLM, nên chỉ log của
    vLLM cho biết: khi nào bắt đầu nạp model, tải và nạp weights mất bao lâu, compile, cấp phát KV-cache,
    chụp CUDA graph (ghi sẵn chuỗi lệnh GPU cho từng cỡ batch để lúc chạy khỏi phải phát lại từng lệnh).
Mục đích: `parse_vllm_log(text) → dict` là hook phân tích log của runner (Kế hoạch §6). Đầu vào là file
    `logs/<pod>.log` runner thu bằng `kubectl logs --timestamps` (collect.write_logs). Đầu ra gồm mốc tuyệt
    đối (giây UNIX), số giây vLLM tự báo trong log, độ dài các pha 4–8 lấy được từ log, và vài thông số
    khởi động (KV-cache, dung lượng checkpoint). `phases()` nhận thêm hai mốc phía Kubernetes (container
    bắt đầu chạy, pod Ready) để tính đủ pha 4 và pha 8.

Câu chữ log đối chiếu với mã nguồn vLLM v0.31.0 (tag v0.31.0, commit db9527a) và uvicorn 0.54.0. Câu chữ
đổi theo phiên bản, nên mọi mẫu regex nằm chung trong bảng PATTERNS để dễ sửa (Kiến trúc §7.2).
Ba chỗ dễ đọc sai (đều đã kiểm trong mã nguồn v0.31.0):
    1. Dòng "Graph capturing finished" có HAI lần. Lần đầu là chụp thử để đo bộ nhớ CUDA graph trong lúc
       profiling, trước dòng "GPU KV cache size" (v1/worker/gpu/cudagraph_utils.py:928). Lần sau mới là
       chụp thật (pha 7c). Lấy dòng đầu tiên thì pha 7c sai.
    2. Thời gian tải weights từ Hugging Face (pha 5) KHÔNG nằm trong "Loading weights took": vLLM tải xong
       file rồi mới bấm giờ (model_executor/model_loader/default_loader.py:347). Dòng "Time spent downloading
       weights" chỉ in khi tải mất hơn 0,5 s (model_executor/model_loader/weight_utils.py:522).
    3. Compile cache đã ấm (mức L2): torch 2.13 dùng AOT compile (biên dịch trước, lưu kết quả ra đĩa), log
       có "Directly load AOT compilation" và KHÔNG có dòng "torch.compile took"
       (compilation/decorators.py:565).

Chạy tay trên một hoặc nhiều file log (từ gốc repo); "-" = đọc từ stdin:
    uv run --project experiments python -m experiments.runner.vllm_log runs/<phiên>/<lượt>/logs/*.log
    kubectl logs --timestamps <pod> -n llm-serving \\
        | uv run --project experiments python -m experiments.runner.vllm_log -
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

SCHEMA = 1  # tăng khi đổi cấu trúc dict trả về, để bảng phân tích (TR7) biết đang đọc bản nào
CHECKED_VERSION = "0.31.0"  # bản vLLM đã đối chiếu câu chữ log; bản khác thì vẫn đọc nhưng thêm cảnh báo

_NUM = r"-?\d+(?:\.\d+)?"  # số thập phân vLLM in bằng %.2f, %.6f…; có dấu trừ vì vài số GiB có thể âm

# Bảng mẫu: tên → (nguồn, regex). Regex áp lên PHẦN NỘI DUNG của dòng, tức phần sau tiền tố
# "(EngineCore pid=150) INFO 11-08 10:02:58 [default_loader.py:484] " của vLLM, hoặc sau "INFO:     " của
# uvicorn (web server mà vLLM dùng để phục vụ HTTP). Nhóm có tên (?P<…>) là số cần lấy.
# Thứ tự dưới đây là thứ tự xuất hiện khi khởi động (V2 model runner, mặc định trên CUDA ở v0.31.0).
PATTERNS: dict[str, tuple[str, re.Pattern[str]]] = {
    # Dòng đầu tiên của API server, in ngay sau khi import xong torch và vllm. Có hai dạng: logo nhiều dòng
    # (dòng chứa "version") hoặc một dòng chữ khi đặt VLLM_DISABLE_LOG_LOGO=1 (serve/utils/api_utils.py:325).
    "api_server_start": (
        "vllm",
        re.compile(r"(?:[█▄▀].*\bversion\s+|^vLLM server version\s+)(?P<version>\d+\.\d+\.\d+[^\s,]*)"),
    ),
    # Tiến trình EngineCore bắt đầu; dòng này in kèm toàn bộ cấu hình (v1/engine/core.py:130)
    "engine_init_start": (
        "vllm",
        re.compile(r"^Initializing a V1 LLM engine \(v(?P<version>[^)]+)\) with config: (?P<config>.*)$"),
    ),
    # Bắt đầu nạp model = hết pha 4. V2 runner: "Loading model from scratch..." (v1/worker/gpu/
    # model_runner.py:375); V1 runner (khi tính năng nào đó buộc dùng V1): "Starting to load model <tên>...".
    "model_load_start": (
        "vllm",
        re.compile(r"^(?:Loading model from scratch\.\.\.|Starting to load model (?P<model>.+)\.\.\.)$"),
    ),
    # Pha 5: chỉ in khi tải từ Hugging Face mất hơn 0,5 s
    "weights_download_end": (
        "vllm",
        re.compile(rf"^Time spent downloading weights for \S+: (?P<s>{_NUM}) seconds$"),
    ),
    # Loại hệ thống file (EXT4, NFS4…) và dung lượng checkpoint: số liệu cho LT4 (thời gian nạp ≈ dung lượng
    # ÷ tốc độ đọc). Trên NFS, vLLM tự đọc trước file vào page cache, làm pha 6 trông nhanh hơn.
    "checkpoint_info": (
        "vllm",
        re.compile(
            rf"^Filesystem type for checkpoints: (?P<fs>[^.]+)\. Checkpoint size: (?P<gib>{_NUM}) GiB\."
        ),
    ),
    # Pha 6: đọc safetensors từ đĩa và chép vào VRAM (không gồm thời gian tải về, xem điểm 2 ở đầu file)
    "weights_load_end": ("vllm", re.compile(rf"^Loading weights took (?P<s>{_NUM}) seconds$")),
    # Hết nạp model (gồm tạo model, tải về, nạp weights, xử lý sau nạp) = hết pha 6
    "model_load_end": (
        "vllm",
        re.compile(rf"^Model loading took (?P<gib>{_NUM}) GiB memory and (?P<s>{_NUM}) seconds$"),
    ),
    # Tính năng lưu kết quả profiling giữa các lần khởi động (VLLM_ENABLE_STARTUP_PLAN=1, mặc định tắt):
    # khi áp dụng được thì bỏ qua đo bộ nhớ và lần chụp graph thử (v1/worker/startup_plan.py:154)
    "startup_plan_applied": ("vllm", re.compile(r"^Applying persisted startup plan\b")),
    # Pha 7a, compile cache ấm: nạp kết quả compile từ VLLM_CACHE_ROOT thay vì compile lại
    "compile_cache_hit": (
        "vllm",
        re.compile(r"^Directly load (?:AOT compilation from path|the compiled graph\(s\) for compile range)"),
    ),
    # Pha 7a, compile cache lạnh: Inductor (bộ sinh kernel của torch.compile) biên dịch từng đoạn đồ thị
    "compile_cache_miss": (
        "vllm",
        re.compile(rf"^Compiling a graph for compile range .* takes (?P<s>{_NUM}) s$"),
    ),
    # Tổng thời gian torch.compile. Đường AOT in dòng ngắn; đường cũ gộp cả lượt chạy profiling.
    "torch_compile_end": (
        "vllm",
        re.compile(
            rf"^torch\.compile (?P<with_profiling>and initial profiling/warmup run together )?"
            rf"took (?P<s>{_NUM}) s in total$"
        ),
    ),
    # Lượt forward chạy thử bằng dữ liệu giả để đo bộ nhớ đỉnh (compilation/monitor.py:82)
    "profiling_run_end": ("vllm", re.compile(rf"^Initial profiling/warmup run took (?P<s>{_NUM}) s$")),
    # Có hai dòng, xem điểm 1 ở đầu file. "%.0f secs": vLLM làm tròn tới giây.
    "graph_capture_end": (
        "vllm",
        re.compile(rf"^Graph capturing finished in (?P<s>{_NUM}) secs, took (?P<gib>{_NUM}) GiB$"),
    ),
    # Phần VRAM còn lại dành cho KV-cache sau profiling (không in khi đặt --kv-cache-memory hay startup plan)
    "available_kv_cache": ("vllm", re.compile(rf"^Available KV cache memory: (?P<gib>{_NUM}) GiB$")),
    # Đã tính xong dung lượng KV-cache = hết pha 7a; ngay sau đó vLLM cấp phát KV-cache (7b) rồi chụp
    # graph (7c).
    # Số token có dấu phẩy ngăn nghìn ("95,456"). (v1/core/kv_cache_utils.py:2465)
    "kv_cache_ready": (
        "vllm",
        re.compile(
            rf"^[A-Z]+ KV cache size: (?P<tokens>[\d,]+) tokens, "
            rf"Maximum concurrency for (?P<len>[\d,]+) tokens per request: (?P<conc>{_NUM})x$"
        ),
    ),
    # Hết pha 7: dòng tổng của cả profiling, KV-cache, warm-up (v1/engine/core.py:364–381). Phần
    # "(compilation: …)" chỉ có khi có compile thật; "seconds" là câu chữ của các bản cũ.
    "engine_init_end": (
        "vllm",
        re.compile(
            rf"^init engine \(profile, create kv cache, warmup model\) took (?P<s>{_NUM}) (?:s|seconds)\b"
            rf"(?: \(compilation: (?P<compile_s>{_NUM}) s)?"
        ),
    ),
    # API server dựng xong app FastAPI, sắp giao socket cho uvicorn (launchers/api_server/entry.py:136)
    "server_start": ("vllm", re.compile(r"^Starting vLLM server on (?P<addr>\S+)$")),
    # uvicorn in dòng này ngay trước khi gọi listen() trên socket cổng 8000 (uvicorn/server.py, startup()).
    # Trước đó socket chỉ mới bind, nên probe bị từ chối kết nối; sau đó probe mới được trả lời.
    "port_open": ("uvicorn", re.compile(r"^Application startup complete\.$")),
    # Access log của uvicorn: kubelet gọi /health (startup/readiness probe) và nhận 200
    "health_ok": ("uvicorn", re.compile(r'"GET /health HTTP/[\d.]+" 200\b')),
}

# Mốc tuyệt đối trả về trong "marks", theo thứ tự thời gian
MARKS = (
    "api_server_start",
    "engine_init_start",
    "model_load_start",
    "weights_download_end",
    "weights_load_end",
    "model_load_end",
    "kv_cache_ready",
    "graph_capture_end",
    "engine_init_end",
    "server_start",
    "port_open",
    "first_health_ok",
)
# Thiếu một trong các mốc này thì không tính được pha 4–8 từ log: log bị cắt, pod chết giữa chừng, hay
# không phải log của vLLM (ví dụ simulator trên kind)
REQUIRED = (
    "api_server_start",
    "model_load_start",
    "model_load_end",
    "kv_cache_ready",
    "engine_init_end",
    "port_open",
)

_ANSI = re.compile(r"\x1b\[[0-9;]*m")  # mã màu terminal; vLLM chỉ tô màu khi chạy trong tty, bỏ cho chắc
# Tiền tố kubelet của `kubectl logs --timestamps`: RFC 3339 tới nano giây, theo UTC ("Z"). Đây là lúc
# container runtime nhận dòng log, chính xác hơn giờ vLLM tự in (chỉ tới giây, không có năm).
_KUBELET_TS = re.compile(r"^(?P<ts>\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}(?:\.\d+)?(?:Z|[+-]\d{2}:\d{2})) ")
# Tiền tố tên tiến trình "(EngineCore pid=150) ". Ở v0.31.0 chỉ dòng log của vLLM có nó; các bản cũ bọc
# cả stdout nên dòng uvicorn cũng có, vì vậy cả hai regex dưới đều cho phép.
_PROC = r"(?:\([^()\s]+ pid=\d+\) )?"
# Dòng log của vLLM (vllm/logger.py:27):
#   "[tiền tố VLLM_LOGGING_PREFIX](<tiến trình> pid=<số>) <MỨC> <MM-DD HH:MM:SS> [file:dòng] <nội dung>"
# Dùng search thay vì match để chịu được tiền tố tuỳ chọn ở đầu dòng.
_VLLM_LINE = re.compile(
    _PROC + r"(?:DEBUG|INFO|WARNING|ERROR|CRITICAL) "
    r"(?P<ts>\d{2}-\d{2} \d{2}:\d{2}:\d{2})(?:\.\d+)? \[[^\]]*\] ?(?P<msg>.*)$"
)
# Dòng log của uvicorn: "INFO:     Application startup complete." (mức + ":" + dấu cách cho thẳng cột)
_UVICORN_LINE = re.compile("^" + _PROC + r"(?:DEBUG|INFO|WARNING|ERROR|CRITICAL):\s+(?P<msg>.*)$")


def _vllm_ts(text: str, year: int) -> float | None:
    """Giờ vLLM tự in ("11-08 10:02:58") không có năm và theo giờ địa phương của container. Image vLLM
    không đặt TZ nên là UTC. Năm lấy từ tham số; log vắt qua giao thừa thì lệch một năm (không gặp trong
    đồ án). Ngày không hợp lệ với năm đó (29/02 năm không nhuận) thì trả None thay vì lỗi."""
    try:
        return datetime.strptime(f"{year}-{text}", "%Y-%m-%d %H:%M:%S").replace(tzinfo=UTC).timestamp()
    except ValueError:
        return None


def _num(s: str | None) -> float | None:
    return None if s is None else float(s.replace(",", ""))


def parse_vllm_log(text: str, *, year: int | None = None) -> dict[str, Any]:
    """Đọc log của MỘT container vLLM, trả dict (xem `_empty_result` cho cấu trúc).

    `year`: chỉ dùng khi log không có mốc kubelet (ví dụ `docker logs`, hay `kubectl logs` thiếu
    `--timestamps`); mặc định là năm hiện tại theo UTC. Dòng không nhận ra (tqdm, NCCL, log simulator…)
    được bỏ qua, nên log thiếu hay lạ không làm hàm lỗi: mốc nào không thấy thì là None.
    """
    if year is None:
        year = datetime.now(UTC).year
    result = _empty_result()
    hits: list[tuple[int, str, float | None, dict[str, str | None]]] = []  # (số mảnh, tên mẫu, mốc, nhóm)
    sources: set[str] = set()
    by_source: dict[str, list[tuple[str, re.Pattern[str]]]] = {"vllm": [], "uvicorn": []}
    for name, (source, rx) in PATTERNS.items():
        by_source[source].append((name, rx))

    i = 0  # số thứ tự mảnh, để biết dòng nào đứng trước dòng nào
    for physical in text.split("\n"):
        line = _ANSI.sub("", physical)
        kubelet_ts: float | None = None
        if k := _KUBELET_TS.match(line):
            kubelet_ts = datetime.fromisoformat(k["ts"]).timestamp()  # Python ≥ 3.11 nhận "Z" và nano giây
            line = line[k.end() :]
            sources.add("kubelet")
        # Một dòng vật lý có thể gồm nhiều mảnh ngăn bởi "\r": tqdm vẽ lại thanh tiến trình bằng "\r", vLLM
        # xuống dòng trong một bản ghi bằng "\r\n". Mọi mảnh dùng chung mốc kubelet của dòng chứa nó.
        for frag in line.split("\r"):
            i += 1
            if v := _VLLM_LINE.search(frag):
                source, msg = "vllm", v["msg"]
            elif u := _UVICORN_LINE.match(frag):
                source, msg = "uvicorn", u["msg"]  # uvicorn không tự in giờ: chỉ có mốc nhờ tiền tố kubelet
            else:
                continue  # tqdm, NCCL, log của simulator…
            for name, rx in by_source[source]:
                if m := rx.search(msg):
                    ts = kubelet_ts
                    if ts is None and v is not None:  # không có tiền tố kubelet: dùng giờ vLLM tự in
                        ts = _vllm_ts(v["ts"], year)
                        sources.add("vllm")
                    hits.append((i, name, ts, m.groupdict()))

    result["time_source"] = "kubelet" if "kubelet" in sources else ("vllm" if sources else None)

    # Log có nhiều lần khởi động (docker logs qua nhiều lần restart): chỉ đọc lần cuối, giống `kubectl logs`
    # vốn chỉ trả log của container hiện tại.
    starts = [i for i, name, _, _ in hits if name == "api_server_start"]
    result["starts"] = len(starts)
    if len(starts) > 1:
        hits = [h for h in hits if h[0] >= starts[-1]]
        result["warnings"].append(f"log có {len(starts)} lần khởi động; chỉ đọc lần cuối")

    by_name: dict[str, list[tuple[int, float | None, dict[str, str | None]]]] = {}
    for i, name, ts, groups in hits:
        by_name.setdefault(name, []).append((i, ts, groups))

    def first(name: str) -> tuple[int, float | None, dict[str, str | None]] | None:
        return by_name[name][0] if name in by_name else None

    marks, reported, info = result["marks"], result["reported"], result["info"]
    # Mốc = dòng đầu tiên khớp mẫu cùng tên. Riêng graph_capture_end tính ở dưới, first_health_ok lấy từ
    # mẫu health_ok.
    for name in MARKS:
        if name != "graph_capture_end" and (h := first(name)) is not None:
            marks[name] = h[1]
    if (h := first("health_ok")) is not None:
        marks["first_health_ok"] = h[1]

    # Hai dòng "Graph capturing finished" (điểm 1 ở đầu file): dòng trước "KV cache size" là chụp thử khi
    # profiling, dòng sau là chụp thật. Không thấy dòng KV-cache thì không phân biệt được, nên bỏ trống.
    graphs = by_name.get("graph_capture_end", [])
    kv = first("kv_cache_ready")
    if kv is not None:
        before = [g for g in graphs if g[0] < kv[0]]
        after = [g for g in graphs if g[0] > kv[0]]
        if before:
            reported["graph_profile_s"] = _num(before[-1][2]["s"])
        if after:
            marks["graph_capture_end"] = after[-1][1]
            reported["graph_capture_s"] = _num(after[-1][2]["s"])
            info["graph_gib"] = _num(after[-1][2]["gib"])
    elif graphs:
        result["warnings"].append("có dòng Graph capturing nhưng thiếu dòng KV cache size: bỏ qua pha 7c")

    # Số giây vLLM tự báo trong nội dung dòng log
    for key, name in (
        ("weights_download_s", "weights_download_end"),
        ("weights_load_s", "weights_load_end"),
        ("model_load_s", "model_load_end"),
        ("profiling_run_s", "profiling_run_end"),
        ("torch_compile_s", "torch_compile_end"),
        ("engine_init_s", "engine_init_end"),
    ):
        if (h := first(name)) is not None:
            reported[key] = _num(h[2]["s"])
    if (h := first("engine_init_end")) is not None:
        reported["engine_init_compile_s"] = _num(h[2]["compile_s"])
    if "compile_cache_miss" in by_name:
        reported["graph_compile_s"] = round(
            sum(_num(g[2]["s"]) or 0.0 for g in by_name["compile_cache_miss"]), 3
        )

    # Thông số khởi động
    if (h := first("api_server_start")) is not None:
        info["vllm_version"] = h[2]["version"]
    if (h := first("engine_init_start")) is not None:
        info["vllm_version"] = info["vllm_version"] or h[2]["version"]
        config = h[2]["config"] or ""
        if m := re.search(r"\bmodel='([^']*)'", config):
            info["model"] = m[1]
        if m := re.search(r"\bmax_seq_len=(\d+)", config):
            info["max_model_len"] = int(m[1])
        if m := re.search(r"\benforce_eager=(True|False)", config):
            info["enforce_eager"] = m[1] == "True"
    if (h := first("model_load_start")) is not None:
        # V1 runner in tên model trong dòng này, V2 thì không
        info["model_runner"] = "v1" if h[2]["model"] else "v2"
        info["model"] = info["model"] or h[2]["model"]
    if (h := first("model_load_end")) is not None:
        info["model_gib"] = _num(h[2]["gib"])
    if (h := first("checkpoint_info")) is not None:
        info["filesystem"] = h[2]["fs"]
        info["checkpoint_gib"] = _num(h[2]["gib"])
    if (h := first("available_kv_cache")) is not None:
        info["available_kv_cache_gib"] = _num(h[2]["gib"])
    if kv is not None:
        info["kv_cache_tokens"] = int(_num(kv[2]["tokens"]) or 0)
        info["max_concurrency"] = _num(kv[2]["conc"])
    if (h := first("torch_compile_end")) is not None:
        info["torch_compile_includes_profiling"] = h[2]["with_profiling"] is not None
    if "compile_cache_hit" in by_name:
        info["compile_cache"] = "hit"
    elif "compile_cache_miss" in by_name:
        info["compile_cache"] = "miss"
    info["startup_plan_applied"] = "startup_plan_applied" in by_name

    # So phần X.Y.Z: bản build có hậu tố (ví dụ "0.31.0+cu130") vẫn tính là cùng bản
    base = re.match(r"\d+\.\d+\.\d+", info["vllm_version"] or "")
    if info["vllm_version"] is not None and (base is None or base[0] != CHECKED_VERSION):
        result["warnings"].append(
            f"vLLM {info['vllm_version']}: câu chữ log mới đối chiếu với {CHECKED_VERSION}, kiểm lại PATTERNS"
        )
    if kv is not None and marks["graph_capture_end"] is None and info["enforce_eager"] is not True:
        result["warnings"].append("thấy dòng KV cache size nhưng không thấy lần chụp CUDA graph thật")

    result["missing"] = [m for m in REQUIRED if marks[m] is None]
    result["complete"] = not result["missing"]
    result["phases_s"] = phases(result)
    negative = [k for k, s in result["phases_s"].items() if s is not None and s < 0]
    if negative:
        result["warnings"].append(
            f"pha có độ dài âm (log lộn xộn hay mốc chỉ tới giây): {', '.join(negative)}"
        )
    return result


def phases(
    parsed: dict[str, Any], *, container_started: float | None = None, pod_ready: float | None = None
) -> dict[str, float | None]:
    """Độ dài (giây) các pha 4–8 của Kiến trúc §7.2 từ kết quả `parse_vllm_log`. None = không đủ mốc.

    Hai mốc phía Kubernetes, giây UNIX, không bắt buộc:
        container_started  containerStatuses[].state.running.startedAt: container bắt đầu chạy = đầu pha 4
        pod_ready          lastTransitionTime của condition Ready: hết pha 8
    Không truyền thì các pha cần chúng là None. Hai mốc này chỉ chính xác tới giây (định dạng của API).
    Pha 1–3 lấy hoàn toàn từ phía Kubernetes (PodScheduled, event Pulling/Pulled), không nằm ở đây.
    """
    m, r = parsed["marks"], parsed["reported"]

    def span(a: float | None, b: float | None) -> float | None:
        return None if a is None or b is None else round(b - a, 3)

    # Pha 5 không có mốc bắt đầu riêng trong log, nên lấy số vLLM tự báo. Không có dòng đó mà vẫn nạp
    # model xong thì coi là 0: tải dưới 0,5 s (đã có cache), model là đường dẫn cục bộ, hoặc loader khác
    # (runai_streamer, tensorizer…) gộp tải và nạp, khi đó cả hai tính vào pha 6.
    p5 = r["weights_download_s"]
    if p5 is None and m["model_load_end"] is not None:
        p5 = 0.0
    load = span(m["model_load_start"], m["model_load_end"])  # pha 5 + pha 6, theo đồng hồ
    # Pha 7c theo số tự báo (làm tròn tới giây). --enforce-eager: không chụp graph nên là 0.
    p7c = r["graph_capture_s"]
    if p7c is None and parsed["info"]["enforce_eager"] is True:
        p7c = 0.0
    kv_to_end = span(m["kv_cache_ready"], m["engine_init_end"])  # 7b + 7c
    p7b = None if kv_to_end is None or p7c is None else round(kv_to_end - p7c, 3)
    if p7b is not None and -0.5 <= p7b < 0:
        p7b = 0.0  # 7c làm tròn tới giây nên 7b sai số ±0,5 s; âm trong khoảng đó chỉ do làm tròn
    return {
        # Pha 4: container chạy → bắt đầu nạp model (import torch/vllm, đọc cấu hình, tạo EngineCore, CUDA)
        "p4_process_start": span(container_started, m["model_load_start"]),
        "p4_imports": span(container_started, m["api_server_start"]),  # riêng phần import trước dòng log đầu
        "p5_download": p5,
        "p6_load_weights": None if load is None or p5 is None else round(load - p5, 3),
        # Pha 7: hết nạp model → hết khởi tạo engine. Tổng 7a + 7b + 7c.
        "p7_engine_init": span(m["model_load_end"], m["engine_init_end"]),
        # 7a: compile hoặc nạp compile cache, lượt chạy profiling, chụp graph thử để đo bộ nhớ
        "p7a_profile_compile": span(m["model_load_end"], m["kv_cache_ready"]),
        # 7b: cấp phát KV-cache và warm-up kernel, tức phần còn lại sau khi trừ 7c (sai số ±0,5 s vì 7c
        # làm tròn tới giây, nên 7a + 7b + 7c có thể lệch pha 7 tới 0,5 s)
        "p7b_kv_cache": p7b,
        "p7c_graph_capture": p7c,
        # Pha 8: engine xong → pod Ready. Tách: dựng API server tới lúc mở cổng; rồi chờ probe kế tiếp đạt
        # (periodSeconds 5) và kubelet cập nhật condition Ready.
        "p8_ready": span(m["engine_init_end"], pod_ready),
        "p8_server_start": span(m["engine_init_end"], m["port_open"]),
        "p8_probe": span(m["port_open"], pod_ready),
    }


def _empty_result() -> dict[str, Any]:
    """Cấu trúc kết quả: mọi khoá luôn có mặt (None khi log không có) để bảng phân tích đọc ổn định."""
    return {
        "schema": SCHEMA,
        "complete": False,  # đủ mọi mốc trong REQUIRED
        "missing": [],  # mốc REQUIRED không tìm thấy
        # "kubelet" (mốc nano giây của kubectl --timestamps) | "vllm" (giờ vLLM tự in, chỉ tới giây)
        "time_source": None,
        "starts": 0,  # số lần API server khởi động trong log
        "marks": dict.fromkeys(MARKS),  # giây UNIX (UTC)
        "reported": {  # giây, vLLM tự báo trong nội dung log
            "weights_download_s": None,
            "weights_load_s": None,
            "model_load_s": None,
            "torch_compile_s": None,
            "graph_compile_s": None,  # tổng các dòng "Compiling a graph … takes" (chỉ khi cache lạnh)
            "profiling_run_s": None,
            "graph_profile_s": None,  # lần chụp graph thử để đo bộ nhớ, nằm trong pha 7a
            "graph_capture_s": None,  # lần chụp thật, pha 7c
            "engine_init_s": None,
            "engine_init_compile_s": None,
        },
        "info": {
            "vllm_version": None,
            "model": None,
            "model_runner": None,  # "v2" | "v1"
            "max_model_len": None,
            "enforce_eager": None,
            "filesystem": None,  # nơi để checkpoint: EXT4, NFS4…
            "checkpoint_gib": None,
            "model_gib": None,  # VRAM của weights
            "available_kv_cache_gib": None,
            "kv_cache_tokens": None,
            "max_concurrency": None,  # số request max_model_len token chạy đồng thời được
            "graph_gib": None,  # VRAM của CUDA graph (lần chụp thật)
            "compile_cache": None,  # "hit" | "miss"
            "torch_compile_includes_profiling": None,
            "startup_plan_applied": False,
        },
        "phases_s": {},
        "warnings": [],
    }


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description="Đọc log khởi động vLLM, in mốc và các pha cold start (JSON).")
    ap.add_argument("logs", nargs="+", help="file log (kubectl logs --timestamps); '-' = đọc từ stdin")
    ap.add_argument("--year", type=int, help="năm cho log không có mốc kubelet (mặc định: năm hiện tại)")
    args = ap.parse_args(argv)
    out = {}
    for path in args.logs:
        # Đọc bytes rồi tự giải mã UTF-8: stdin trên Windows mặc định giải mã theo cp1252, làm hỏng ký tự
        # logo (█▄▀) và thanh tqdm. errors="replace": byte lỗi thành "�" thay vì dừng cả lần đọc.
        data = sys.stdin.buffer.read() if path == "-" else Path(path).read_bytes()
        out[path] = parse_vllm_log(data.decode("utf-8", errors="replace"), year=args.year)
    # Ghi bytes UTF-8: console Windows mặc định không phải UTF-8, in chữ có dấu sẽ lỗi
    sys.stdout.buffer.write((json.dumps(out, ensure_ascii=False, indent=2) + "\n").encode("utf-8"))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
