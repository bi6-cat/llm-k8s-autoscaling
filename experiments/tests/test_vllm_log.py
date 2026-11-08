"""Unit test cho bộ đọc log khởi động vLLM (experiments/runner/vllm_log.py).

Mục đích: Kiểm các mẫu regex và cách chia pha cold start trên log mẫu, không cần GPU.
    Log mẫu DỰNG TAY từ đúng câu chữ trong mã nguồn vLLM v0.31.0 (vị trí ghi ở vllm_log.PATTERNS) và
    uvicorn 0.54.0, theo định dạng dòng của vllm/logger.py và tiền tố của `kubectl logs --timestamps`.
    Đây KHÔNG phải log thật, và các con số (giây, GiB, token) là số bịa cho dễ tính, không phải số đo. Khi
    có log thật từ máy nhà hay V0, thêm một test đọc log đó.
"""

from __future__ import annotations

import io
import json
import re
import sys
from datetime import UTC, datetime

import pytest

from experiments.runner import vllm_log
from experiments.runner.vllm_log import REQUIRED, parse_vllm_log, phases

DAY = "2026-11-08"


def _hms_frac(t: str) -> tuple[str, str]:
    hms, _, frac = t.partition(".")
    return hms, frac


def ts(t: str) -> float:
    """'10:02:58.5' → giây UNIX của 2026-11-08 10:02:58.5 UTC."""
    hms, frac = _hms_frac(t)
    return datetime.fromisoformat(f"{DAY}T{hms}.{frac.ljust(6, '0')}+00:00").timestamp()


def kubelet(t: str) -> str:
    """Tiền tố của `kubectl logs --timestamps`, tới nano giây: '2026-11-08T10:02:58.500000000Z'."""
    hms, frac = _hms_frac(t)
    return f"{DAY}T{hms}.{frac.ljust(9, '0')}Z"


def V(t: str, msg: str, proc: str = "EngineCore", src: str = "core.py:1") -> str:
    """Một dòng log vLLM: '<kubelet> (EngineCore pid=150) INFO 11-08 10:02:58 [file:dòng] <msg>'."""
    pid = 1 if proc == "APIServer" else 150
    return f"{kubelet(t)} ({proc} pid={pid}) INFO 11-08 {_hms_frac(t)[0]} [{src}] {msg}"


def A(t: str, msg: str, src: str = "entry.py:1") -> str:
    return V(t, msg, proc="APIServer", src=src)


def U(t: str, msg: str) -> str:
    """Một dòng log uvicorn: không có giờ riêng, chỉ có tiền tố kubelet."""
    return f"{kubelet(t)} INFO:     {msg}"


def RAW(t: str, text: str) -> str:
    return f"{kubelet(t)} {text}"


CONFIG_7B = (
    "model='Qwen/Qwen2.5-7B-Instruct', speculative_config=None, tokenizer='Qwen/Qwen2.5-7B-Instruct', "
    "dtype=torch.bfloat16, max_seq_len=4096, download_dir=None, load_format=auto, "
    "tensor_parallel_size=1, quantization=None, enforce_eager=False, kv_cache_dtype=auto, seed=0"
)

# L0: model tải từ Hugging Face, compile cache lạnh, V2 model runner (mặc định trên CUDA ở v0.31.0)
L0_LINES = [
    # Logo nhiều dòng: NewLineFormatter gắn lại tiền tố cho từng dòng của một bản ghi
    A("10:00:05.1", "", src="api_utils.py:347"),
    A("10:00:05.1001", "       █     █     █▄   ▄█", src="api_utils.py:347"),
    A("10:00:05.1002", " ▄▄ ▄█ █     █     █ ▀▄▀ █  version 0.31.0", src="api_utils.py:347"),
    A(
        "10:00:05.1003",
        "  █▄█▀ █     █     █     █  model   Qwen/Qwen2.5-7B-Instruct",
        src="api_utils.py:347",
    ),
    A("10:00:05.1004", "   ▀▀  ▀▀▀▀▀ ▀▀▀▀▀ ▀     ▀", src="api_utils.py:347"),
    A(
        "10:00:05.2",
        "non-default args: {'model_tag': 'Qwen/Qwen2.5-7B-Instruct', 'port': 8000}",
        src="api_utils.py:286",
    ),
    V("10:00:12", f"Initializing a V1 LLM engine (v0.31.0) with config: {CONFIG_7B}", src="core.py:130"),
    V("10:00:15", "Using V2 Model Runner", src="gpu_worker.py:479"),
    V("10:00:16", "Loading model from scratch...", src="model_runner.py:375"),
    # Thanh tiến trình của huggingface_hub (tqdm): không phải dòng log, phải bị bỏ qua
    RAW("10:01:00", "Downloading shards:  50%|█████     | 2/4 [01:15<01:15, 37.6s/it]"),
    V(
        "10:02:46.5",
        "Time spent downloading weights for Qwen/Qwen2.5-7B-Instruct: 150.250000 seconds",
        src="weight_utils.py:523",
    ),
    V(
        "10:02:46.6",
        "Filesystem type for checkpoints: EXT4. Checkpoint size: 14.19 GiB. Available RAM: 60.00 GiB.",
        src="weight_utils.py:1063",
    ),
    # tqdm vẽ lại bằng "\r": các mảnh sau "\r" không có tiền tố kubelet
    RAW(
        "10:02:50",
        "Loading safetensors checkpoint shards:   0% Completed | 0/4 [00:00<?, ?it/s]\r"
        "Loading safetensors checkpoint shards:  25% Completed | 1/4 [00:02<00:08,  2.80s/it]",
    ),
    V("10:02:58", "Loading weights took 11.20 seconds", src="default_loader.py:484"),
    V("10:02:59", "Model loading took 14.25 GiB memory and 163.000000 seconds", src="model_runner.py:407"),
    V(
        "10:03:00",
        "Using cache directory: /cache/vllm/torch_compile_cache/1a2b3c/rank_0_0/backbone "
        "for vLLM's torch.compile",
        src="backends.py:1090",
    ),
    V("10:03:08", "Dynamo bytecode transform time: 8.00 s", src="backends.py:1151"),
    V("10:03:20", "Compiling a graph for compile range (1, 2048) takes 12.00 s", src="backends.py:391"),
    V("10:03:30", "Compiling a graph for compile range (2049, 8192) takes 9.50 s", src="backends.py:391"),
    V("10:03:31", "torch.compile took 31.00 s in total", src="monitor.py:53"),
    V("10:03:33", "Initial profiling/warmup run took 1.50 s", src="monitor.py:81"),
    # Lần chụp graph THỬ (profile_only) khi đo bộ nhớ, trước dòng KV cache size
    V("10:03:53", "Graph capturing finished in 20 secs, took 0.45 GiB", src="model_runner.py:1087"),
    V("10:03:53.2", "Available KV cache memory: 5.10 GiB", src="gpu_worker.py:692"),
    V(
        "10:03:53.3",
        "GPU KV cache size: 95,456 tokens, Maximum concurrency for 4,096 tokens per request: 23.30x",
        src="kv_cache_utils.py:2465",
    ),
    # Lần chụp graph THẬT (pha 7c)
    V("10:04:15", "Graph capturing finished in 21 secs, took 0.45 GiB", src="model_runner.py:1087"),
    V(
        "10:04:16",
        "init engine (profile, create kv cache, warmup model) took 76.50 s (compilation: 31.00 s)",
        src="core.py:374",
    ),
    A("10:04:17", "Supported tasks: ['generate']", src="entry.py:132"),
    A("10:04:17.5", "Starting vLLM server on http://0.0.0.0:8000", src="entry.py:136"),
    A("10:04:17.51", "Available routes are:", src="launcher.py:60"),
    A("10:04:17.52", "Route: /health, Methods: GET", src="launcher.py:69"),
    U("10:04:17.6", "Started server process [1]"),
    U("10:04:17.61", "Waiting for application startup."),
    U("10:04:17.7", "Application startup complete."),
    U("10:04:18", '10.42.0.1:40312 - "GET /metrics HTTP/1.1" 200 OK'),
    U("10:04:20", '10.42.0.1:51234 - "GET /health HTTP/1.1" 200 OK'),
    U("10:04:22", '10.42.0.1:51240 - "GET /health HTTP/1.1" 200 OK'),
]
L0 = "\n".join(L0_LINES) + "\n"

# L2: model trên đĩa cục bộ, compile cache ấm (AOT), startup plan đã lưu, logo tắt
CONFIG_LOCAL = CONFIG_7B.replace("Qwen/Qwen2.5-7B-Instruct", "/models/qwen2.5-7b")
L2_LINES = [
    A("11:00:04", "vLLM server version 0.31.0, serving model /models/qwen2.5-7b", src="api_utils.py:347"),
    V("11:00:10", f"Initializing a V1 LLM engine (v0.31.0) with config: {CONFIG_LOCAL}", src="core.py:130"),
    V("11:00:13", "Using V2 Model Runner", src="gpu_worker.py:479"),
    V("11:00:14", "Loading model from scratch...", src="model_runner.py:375"),
    V(
        "11:00:14.2",
        "Filesystem type for checkpoints: EXT4. Checkpoint size: 14.19 GiB. Available RAM: 60.00 GiB.",
        src="weight_utils.py:1063",
    ),
    V("11:00:19", "Loading weights took 4.10 seconds", src="default_loader.py:484"),
    V("11:00:19.5", "Model loading took 14.25 GiB memory and 5.500000 seconds", src="model_runner.py:407"),
    V(
        "11:00:20",
        "Applying persisted startup plan (fingerprint 0123456789abcdef): kv_cache_memory_bytes=5476083302 "
        "(5.10 GiB), recorded free-memory baseline 22.80 GiB, current 22.80 GiB. Memory profiling will be "
        "skipped.",
        src="startup_plan.py:153",
    ),
    V(
        "11:00:21",
        "Directly load AOT compilation from path /cache/vllm/torch_compile_cache/torch_aot_compile/9f8e7d/"
        "rank_0_0/model",
        src="decorators.py:312",
    ),
    V("11:00:22", "Initial profiling/warmup run took 0.80 s", src="monitor.py:81"),
    V(
        "11:00:22.1",
        "Initial free memory 22.8 GiB, reserved 5.1 GiB memory for KV Cache as specified by "
        "kv_cache_memory_bytes config and skipped memory profiling.",
        src="gpu_worker.py:603",
    ),
    V(
        "11:00:22.2",
        "GPU KV cache size: 95,456 tokens, Maximum concurrency for 4,096 tokens per request: 23.30x",
        src="kv_cache_utils.py:2465",
    ),
    V("11:00:44", "Graph capturing finished in 21 secs, took 0.45 GiB", src="model_runner.py:1087"),
    V("11:00:45", "init engine (profile, create kv cache, warmup model) took 25.00 s", src="core.py:381"),
    A("11:00:46", "Starting vLLM server on http://0.0.0.0:8000", src="entry.py:136"),
    U("11:00:46.2", "Application startup complete."),
]
L2 = "\n".join(L2_LINES) + "\n"


def test_l0_marks_reported_and_info():
    r = parse_vllm_log(L0)
    assert r["complete"] is True and r["missing"] == [] and r["warnings"] == []
    assert r["schema"] == vllm_log.SCHEMA and r["time_source"] == "kubelet" and r["starts"] == 1
    m = r["marks"]
    assert m["api_server_start"] == pytest.approx(ts("10:00:05.1002"))  # dòng logo có chữ "version"
    assert m["engine_init_start"] == pytest.approx(ts("10:00:12"))
    assert m["model_load_start"] == pytest.approx(ts("10:00:16"))
    assert m["weights_download_end"] == pytest.approx(ts("10:02:46.5"))
    assert m["model_load_end"] == pytest.approx(ts("10:02:59"))
    assert m["kv_cache_ready"] == pytest.approx(ts("10:03:53.3"))
    # Lấy lần chụp thật (sau dòng KV cache size), không lấy lần chụp thử
    assert m["graph_capture_end"] == pytest.approx(ts("10:04:15"))
    assert m["engine_init_end"] == pytest.approx(ts("10:04:16"))
    assert m["server_start"] == pytest.approx(ts("10:04:17.5"))
    assert m["port_open"] == pytest.approx(ts("10:04:17.7"))
    assert m["first_health_ok"] == pytest.approx(ts("10:04:20"))  # /metrics trước đó không tính

    assert r["reported"] == {
        "weights_download_s": 150.25,
        "weights_load_s": 11.2,
        "model_load_s": 163.0,
        "torch_compile_s": 31.0,
        "graph_compile_s": 21.5,  # 12,00 + 9,50
        "profiling_run_s": 1.5,
        "graph_profile_s": 20.0,
        "graph_capture_s": 21.0,
        "engine_init_s": 76.5,
        "engine_init_compile_s": 31.0,
    }
    assert r["info"] == {
        "vllm_version": "0.31.0",
        "model": "Qwen/Qwen2.5-7B-Instruct",
        "model_runner": "v2",
        "max_model_len": 4096,
        "enforce_eager": False,
        "filesystem": "EXT4",
        "checkpoint_gib": 14.19,
        "model_gib": 14.25,
        "available_kv_cache_gib": 5.1,
        "kv_cache_tokens": 95456,  # bỏ dấu phẩy ngăn nghìn
        "max_concurrency": 23.3,
        "graph_gib": 0.45,
        "compile_cache": "miss",
        "torch_compile_includes_profiling": False,
        "startup_plan_applied": False,
    }


def test_l0_phases_from_log_only():
    p = parse_vllm_log(L0)["phases_s"]
    assert p["p5_download"] == pytest.approx(150.25)
    assert p["p6_load_weights"] == pytest.approx(163.0 - 150.25)  # đồng hồ nạp model trừ phần tải về
    assert p["p7_engine_init"] == pytest.approx(77.0)
    assert p["p7a_profile_compile"] == pytest.approx(54.3)
    assert p["p7c_graph_capture"] == pytest.approx(21.0)
    assert p["p7b_kv_cache"] == pytest.approx(22.7 - 21.0)
    assert p["p7a_profile_compile"] + p["p7b_kv_cache"] + p["p7c_graph_capture"] == pytest.approx(
        p["p7_engine_init"]
    )
    assert p["p8_server_start"] == pytest.approx(1.7)
    # Cần mốc phía Kubernetes nên chưa có
    assert p["p4_process_start"] is None and p["p8_ready"] is None and p["p8_probe"] is None


def test_l0_phases_with_kubernetes_marks_add_up():
    r = parse_vllm_log(L0)
    started, ready = ts("10:00:00"), ts("10:04:23")
    p = phases(r, container_started=started, pod_ready=ready)
    assert p["p4_process_start"] == pytest.approx(16.0)
    assert p["p4_imports"] == pytest.approx(5.1, abs=1e-3)
    assert p["p8_ready"] == pytest.approx(7.0)
    assert p["p8_probe"] == pytest.approx(5.3)
    # Pha 4–8 nối tiếp nhau, cộng lại đúng bằng từ lúc container chạy tới lúc Ready
    total = sum(
        p[k] for k in ("p4_process_start", "p5_download", "p6_load_weights", "p7_engine_init", "p8_ready")
    )
    assert total == pytest.approx(ready - started)


def test_l2_warm_cache_startup_plan():
    r = parse_vllm_log(L2)
    assert r["complete"] is True and r["warnings"] == []
    info, rep, p = r["info"], r["reported"], r["phases_s"]
    assert info["compile_cache"] == "hit" and info["startup_plan_applied"] is True
    assert info["model"] == "/models/qwen2.5-7b" and info["vllm_version"] == "0.31.0"
    assert info["available_kv_cache_gib"] is None  # startup plan bỏ qua đo bộ nhớ nên không có dòng này
    # Cache AOT ấm: không có dòng torch.compile, dòng init engine không có phần "(compilation: …)",
    # và không có lần chụp graph thử
    assert rep["torch_compile_s"] is None and rep["engine_init_compile_s"] is None
    assert rep["graph_profile_s"] is None and rep["graph_capture_s"] == 21.0
    assert rep["weights_download_s"] is None
    assert p["p5_download"] == 0.0  # không có dòng tải về: model có sẵn
    assert p["p6_load_weights"] == pytest.approx(5.5)
    assert p["p7a_profile_compile"] == pytest.approx(2.7)
    assert p["p7b_kv_cache"] == pytest.approx(22.8 - 21.0)
    assert p["p8_server_start"] == pytest.approx(1.2)
    assert r["marks"]["first_health_ok"] is None  # log cắt trước lần probe đầu: không bắt buộc


def test_crlf_and_ansi_colors_give_same_result():
    colored = L0.replace(" INFO ", " \x1b[32mINFO\x1b[0m ").replace("\n", "\r\n")
    assert parse_vllm_log(colored) == parse_vllm_log(L0)


def test_without_kubelet_timestamps_falls_back_to_vllm_clock():
    bare = re.sub(r"^\S+Z ", "", L0, flags=re.M)  # như `kubectl logs` không có --timestamps
    r = parse_vllm_log(bare, year=2026)
    assert r["time_source"] == "vllm"
    assert r["marks"]["model_load_start"] == ts("10:00:16")
    assert r["marks"]["kv_cache_ready"] == ts("10:03:53")  # giờ vLLM chỉ tới giây
    # Dòng uvicorn không tự in giờ nên không có mốc mở cổng
    assert r["marks"]["port_open"] is None and r["missing"] == ["port_open"] and r["complete"] is False
    assert r["phases_s"]["p6_load_weights"] == pytest.approx(12.75)
    assert r["phases_s"]["p7a_profile_compile"] == pytest.approx(54.0)


def test_restarted_container_reads_last_start_only():
    crashed = "\n".join(L0_LINES[:13]) + "\n"  # chết giữa lúc nạp weights (sau thanh tqdm)
    r = parse_vllm_log(crashed + L2)
    assert r["starts"] == 2 and any("2 lần khởi động" in w for w in r["warnings"])
    assert r["marks"]["model_load_start"] == pytest.approx(ts("11:00:14"))
    assert r["reported"]["weights_download_s"] is None  # dòng tải về thuộc lần khởi động trước
    assert r["complete"] is True


def test_v1_runner_and_older_phrasing():
    lines = [
        A("09:00:00", "vLLM server version 0.31.0, serving model Qwen/Qwen2.5-0.5B-Instruct"),
        V("09:00:10", "Starting to load model Qwen/Qwen2.5-0.5B-Instruct...", src="gpu_model_runner.py:5256"),
        V("09:00:12", "Loading weights took 1.05 seconds"),
        V("09:00:13", "Model loading took 0.93 GiB memory and 3.000000 seconds"),
        V(
            "09:00:14",
            "Directly load the compiled graph(s) for compile range (1, 2048) from the cache, took 0.512 s",
            src="backends.py:291",
        ),
        V("09:00:15", "torch.compile and initial profiling/warmup run together took 1.41 s in total"),
        V(
            "09:00:16",
            "CPU KV cache size: 1,000 tokens, Maximum concurrency for 2,048 tokens per request: 0.49x",
        ),
        V("09:00:40", "Graph capturing finished in 24 secs, took 0.20 GiB"),
        V("09:00:41", "init engine (profile, create kv cache, warmup model) took 28.00 seconds"),
        U("09:00:42", "Application startup complete."),
    ]
    r = parse_vllm_log("\n".join(lines))
    info = r["info"]
    assert info["model_runner"] == "v1" and info["model"] == "Qwen/Qwen2.5-0.5B-Instruct"
    assert info["compile_cache"] == "hit" and info["torch_compile_includes_profiling"] is True
    assert info["kv_cache_tokens"] == 1000 and info["max_concurrency"] == 0.49
    assert r["reported"]["engine_init_s"] == 28.0 and r["reported"]["torch_compile_s"] == 1.41
    assert r["complete"] is True


def test_enforce_eager_has_no_graph_capture():
    lines = [line.replace("enforce_eager=False", "enforce_eager=True") for line in L2_LINES]
    lines = [line for line in lines if "Graph capturing" not in line]
    r = parse_vllm_log("\n".join(lines))
    assert r["info"]["enforce_eager"] is True
    assert r["phases_s"]["p7c_graph_capture"] == 0.0
    assert r["phases_s"]["p7b_kv_cache"] == pytest.approx(22.8)
    assert r["warnings"] == []


def test_truncated_log_leaves_later_marks_empty():
    cut = next(i for i, line in enumerate(L0_LINES) if "Available KV cache memory" in line)
    r = parse_vllm_log("\n".join(L0_LINES[:cut]))  # có lần chụp thử nhưng chưa tới dòng KV cache size
    assert r["complete"] is False
    assert r["missing"] == ["kv_cache_ready", "engine_init_end", "port_open"]
    assert r["marks"]["graph_capture_end"] is None and r["reported"]["graph_profile_s"] is None
    assert any("thiếu dòng KV cache size" in w for w in r["warnings"])
    p = r["phases_s"]
    assert p["p6_load_weights"] == pytest.approx(12.75)
    assert p["p7_engine_init"] is None and p["p7a_profile_compile"] is None and p["p7b_kv_cache"] is None


def test_simulator_log_gives_empty_result():
    """Log của llm-d-inference-sim trên kind (định dạng klog): không có mốc nào, nhưng không lỗi."""
    sim = "\n".join(
        [
            RAW(
                "14:14:52.301972312",
                'I1107 14:14:52.301457       1 cmd.go:60] "Starting inference simulator"',
            ),
            RAW("14:14:52.303140035", 'I1107 14:14:52.302922       1 config.go:1229] "Configuration:" =<'),
            RAW("14:14:52.303151313", '\t  "DevMode": false,'),
        ]
    )
    r = parse_vllm_log(sim)
    assert r["complete"] is False and r["missing"] == list(REQUIRED)
    assert all(v is None for v in r["marks"].values())
    assert all(v is None for v in r["phases_s"].values())
    assert r["time_source"] == "kubelet" and r["starts"] == 0
    assert parse_vllm_log("")["time_source"] is None


def test_other_version_warns():
    r = parse_vllm_log(L2.replace("0.31.0", "0.32.1"))
    assert r["info"]["vllm_version"] == "0.32.1"
    assert any("0.32.1" in w and "PATTERNS" in w for w in r["warnings"])
    assert parse_vllm_log(L2.replace("0.31.0", "0.31.0+cu130"))["warnings"] == []
    assert parse_vllm_log(L2.replace("0.31.0", "0.31.01"))["warnings"] != []


def test_kubelet_timestamp_keeps_microseconds():
    line = (
        "2026-11-08T10:02:58.123456789Z (EngineCore pid=150) INFO 11-08 10:02:58 [x.py:1] "
        "Loading weights took 1.00 seconds"
    )
    r = parse_vllm_log(line)
    expected = datetime(2026, 11, 8, 10, 2, 58, 123456, tzinfo=UTC).timestamp()
    assert r["marks"]["weights_load_end"] == pytest.approx(expected, abs=1e-6)


def test_uvicorn_lines_with_process_prefix_from_older_versions():
    """Các bản vLLM cũ bọc cả stdout nên dòng uvicorn cũng có "(APIServer pid=1) ". v0.31.0 thì không."""
    prefixed = L0.replace(" INFO:     ", " (APIServer pid=1) INFO:     ")
    r = parse_vllm_log(prefixed)
    assert r["marks"]["port_open"] == pytest.approx(ts("10:04:17.7"))
    assert r["marks"]["first_health_ok"] == pytest.approx(ts("10:04:20"))


def test_record_after_carriage_return_keeps_kubelet_time():
    """Bản ghi vLLM nằm sau "\\r" trên cùng một dòng kubelet vẫn dùng mốc kubelet (nano giây) của dòng đó."""
    line = (
        f"{kubelet('10:02:58.75')} shards: 25%|██▌       | 1/4\r"
        "(EngineCore pid=150) INFO 11-08 10:02:58 [x.py:1] Loading weights took 11.20 seconds"
    )
    r = parse_vllm_log(line)
    assert r["marks"]["weights_load_end"] == pytest.approx(ts("10:02:58.75"))
    assert r["time_source"] == "kubelet"


def test_invalid_vllm_date_does_not_raise():
    line = "(EngineCore pid=150) INFO 02-29 10:00:00 [x.py:1] Loading weights took 1.00 seconds"
    assert parse_vllm_log(line, year=2027)["marks"]["weights_load_end"] is None  # 2027 không nhuận
    assert parse_vllm_log(line, year=2028)["marks"]["weights_load_end"] is not None


def test_graph_rounding_does_not_make_p7b_negative():
    """vLLM in 7c làm tròn tới giây ("22 secs" cho 21,6 s), nên 7b tính ra có thể âm một chút."""
    lines = [line.replace("finished in 21 secs", "finished in 23 secs") for line in L2_LINES]
    r = parse_vllm_log("\n".join(lines))
    assert r["phases_s"]["p7b_kv_cache"] == 0.0  # 22,8 − 23 = −0,2: trong sai số làm tròn
    assert r["warnings"] == []
    far = parse_vllm_log(
        "\n".join(line.replace("finished in 21 secs", "finished in 25 secs") for line in L2_LINES)
    )
    assert far["phases_s"]["p7b_kv_cache"] == pytest.approx(-2.2)  # ngoài sai số: giữ số âm và cảnh báo
    assert any("p7b_kv_cache" in w for w in far["warnings"])


def test_other_loader_without_loading_weights_line():
    """Loader khác (runai_streamer, tensorizer…) không in "Loading weights took": pha 5 = 0, pha 6 là cả
    lần nạp."""
    lines = [line for line in L2_LINES if "Loading weights took" not in line]
    p = parse_vllm_log("\n".join(lines))["phases_s"]
    assert p["p5_download"] == 0.0 and p["p6_load_weights"] == pytest.approx(5.5)


def test_cli_prints_json_per_file(tmp_path, capsysbinary):
    log = tmp_path / "vllm-abc.log"
    log.write_text(L0, encoding="utf-8")
    assert vllm_log.main([str(log)]) == 0
    out = json.loads(capsysbinary.readouterr().out.decode("utf-8"))
    assert out[str(log)]["complete"] is True
    assert out[str(log)]["phases_s"]["p7c_graph_capture"] == 21.0


def test_cli_reads_stdin_as_utf8(monkeypatch, capsysbinary):
    """`kubectl logs … | python -m experiments.runner.vllm_log -`: stdin đọc bằng UTF-8 dù máy dùng cp1252."""
    stdin = io.TextIOWrapper(io.BytesIO(L0.encode("utf-8")), encoding="cp1252")
    monkeypatch.setattr(sys, "stdin", stdin)
    assert vllm_log.main(["-"]) == 0
    out = json.loads(capsysbinary.readouterr().out.decode("utf-8"))
    assert out["-"]["complete"] is True and out["-"]["marks"]["api_server_start"] is not None
