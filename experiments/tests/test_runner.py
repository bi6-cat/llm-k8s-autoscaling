"""Unit test cho các hàm thuần của runner (không cần cluster).

Mục đích: Bắt lỗi logic trước khi chạy trên cluster: đọc ma trận, ghi đè ScaledObject, ghim phiên bản từ
    uv.lock, dựng tham số loadgen và manifest Job, tiêu chí hợp lệ, khoảng trống scrape, checkpoint.
"""

from __future__ import annotations

from pathlib import Path

import pytest
import yaml

from experiments.runner import capacity, checks, collect, configs, loadjob, matrix
from experiments.runner.progress import Progress

REPO = Path(__file__).resolve().parents[2]

BASE = {
    "session": "t",
    "env": "sim",
    "target": {
        "namespace": "llm-serving",
        "deployment": "vllm",
        "service_url": "http://vllm:8000",
        "model": "m",
        "prometheus_service": "monitoring/p:9090",
    },
    "configs": {
        "S1": {"type": "static"},
        "A2": {"type": "scaledobject", "file": "a2.yaml", "overrides": {"threshold": 10}},
    },
    "runs": [
        {"config": "S1", "scenario": "CONST", "rate": 2, "duration": 60},
        {"config": "A2", "scenario": "KB2", "capacity": 1.2, "repeats": 2},
    ],
}


def test_matrix_parse_expands_repeats_and_ids():
    m = matrix.parse(BASE)
    assert [r.run_id for r in m.runs] == ["S1-CONST2-1", "A2-KB2-1", "A2-KB2-2"]
    assert m.runs[2].repeat == 2 and m.runs[2].capacity == 1.2
    assert m.target.api_key_secret is None and m.timing.settle_s == 60
    assert m.target.loadgen_cpu == "1"


def test_matrix_const_rates_get_distinct_ids():
    runs = [{"config": "S1", "scenario": "CONST", "rate": r, "duration": 60} for r in (2, 2.5, 4)]
    m = matrix.parse({**BASE, "runs": runs})
    assert [r.run_id for r in m.runs] == ["S1-CONST2-1", "S1-CONST2.5-1", "S1-CONST4-1"]


@pytest.mark.parametrize(
    "bad, msg",
    [
        ({"runs": [{"config": "X", "scenario": "KB1", "capacity": 1}]}, "chưa khai báo"),
        ({"runs": [{"config": "S1", "scenario": "KB9", "capacity": 1}]}, "không hợp lệ"),
        ({"runs": [{"config": "S1", "scenario": "CONST", "rate": 1}]}, "CONST cần"),
        ({"runs": [{"config": "S1", "scenario": "KB1"}]}, "cần `capacity`"),
        ({"runs": [{"config": "S1", "scenario": "CONST", "rate": 1, "duration": 1}] * 2}, "trùng run_id"),
        ({"env": "prod"}, "env"),
        # Giá trị chưa điền (`null`) hoặc vô nghĩa bị chặn ngay khi đọc file
        ({"runs": [{"config": "S1", "scenario": "KB1", "capacity": None}]}, "`capacity` phải là số dương"),
        ({"runs": [{"config": "S1", "scenario": "CONST", "rate": 0, "duration": 1}]}, "`rate` phải"),
        (
            {"runs": [{"config": "S1", "scenario": "KB3", "capacity": 1, "kb3_replicas": True}]},
            "kb3_replicas",
        ),
        ({"runs": [{"config": "S1", "scenario": "KB1", "capacity": 1, "repeats": 0}]}, "`repeats` phải"),
        (
            {"configs": {"A2": {"type": "scaledobject", "file": "a", "overrides": {"threshold": None}}}},
            "threshold",
        ),
        (
            {"configs": {"A2": {"type": "scaledobject", "file": "a", "overrides": {"max_replicas": 2.5}}}},
            "max_",
        ),
        ({"configs": {"S4": {"type": "static", "replicas": "4"}}}, "`replicas` phải"),
        ({"shuffle_seed": "7"}, "shuffle_seed"),
    ],
)
def test_matrix_errors(bad, msg):
    with pytest.raises(matrix.MatrixError, match=msg):
        matrix.parse({**BASE, **bad})


def test_matrix_shuffle_seed_is_deterministic_and_ignores_row_order():
    rows = [{"config": "S1", "scenario": s, "capacity": 1, "repeats": 2} for s in ("KB1", "KB2", "KB3")]
    grouped = matrix.parse({**BASE, "runs": rows})
    a = matrix.parse({**BASE, "runs": rows, "shuffle_seed": 7})
    b = matrix.parse({**BASE, "runs": rows[::-1], "shuffle_seed": 7})
    ids = [r.run_id for r in a.runs]
    assert sorted(ids) == sorted(r.run_id for r in grouped.runs)
    assert ids == [r.run_id for r in b.runs]
    # Ghim thứ tự của seed 7: CI chạy Python 3.11 và 3.15, nên test này đỏ nếu thứ tự đổi theo phiên bản
    assert ids == ["S1-KB2-1", "S1-KB2-2", "S1-KB1-2", "S1-KB1-1", "S1-KB3-2", "S1-KB3-1"]
    assert a.shuffle_seed == 7 and grouped.shuffle_seed is None
    # Mỗi lượt giữ đúng số thứ tự lặp của nó (= --run-index của loadgen), xáo không làm đổi lịch gửi
    assert all(r.run_id.endswith(f"-{r.repeat}") for r in a.runs)


def test_matrix_sim_file_is_valid():
    m = matrix.load(REPO / "experiments" / "matrix-sim.yaml")
    assert {r.config.id for r in m.runs} == {"S1", "A2"}
    assert (REPO / m.runs[1].config.file).exists()


def test_matrix_v2_draft_refuses_unfilled_values_then_matches_design():
    path = REPO / "experiments" / "matrix-v2.yaml"
    # Bản nháp còn `null` (chờ ADR-003): runner phải từ chối, kể cả --dry-run
    with pytest.raises(matrix.MatrixError, match="số dương"):
        matrix.load(path)
    # Điền thử như ở V2 rồi kiểm cấu trúc theo Thông số §8.2
    text = path.read_text(encoding="utf-8")
    filled = text.replace("&C null", "&C 5").replace("&A2_THRESHOLD null", "&A2_THRESHOLD 24")
    assert filled.count("null") == text.count("null") - 2
    m = matrix.parse(yaml.safe_load(filled))
    cells: dict[tuple[str, str], int] = {}
    for r in m.runs:
        cells[(r.config.id, r.scenario)] = cells.get((r.config.id, r.scenario), 0) + 1
    assert cells == {
        ("S1", "KB2"): 1, ("S1", "KB3"): 1,
        ("S4", "KB1"): 1, ("S4", "KB2"): 1, ("S4", "KB3"): 1,
        ("A1", "KB1"): 2, ("A1", "KB2"): 2, ("A1", "KB3"): 1,
        ("A2", "KB1"): 2, ("A2", "KB2"): 3, ("A2", "KB3"): 2,
    }  # fmt: skip
    assert len(m.runs) == 17 and m.env == "cloud" and m.shuffle_seed is not None
    n = m.runs[0].replicas_for_kb3
    by_id = {r.config.id: r.config for r in m.runs}
    assert by_id["S4"].replicas == n
    for cid in ("A1", "A2"):
        assert by_id[cid].overrides["max_replicas"] == n
        assert (REPO / by_id[cid].file).exists()
    assert by_id["A2"].overrides["threshold"] == 24 and "threshold" not in by_id["A1"].overrides
    assert all(r.capacity == 5 and r.replicas_for_kb3 == n for r in m.runs)


def test_render_scaledobject_overrides_and_pause():
    doc = yaml.safe_load(
        (REPO / "autoscaling/official/base/scaledobject-a2.yaml").read_text(encoding="utf-8")
    )
    so = configs.render_scaledobject(doc, {"threshold": 10, "max_replicas": 3}, paused=True)
    assert so["spec"]["triggers"][0]["metadata"]["threshold"] == "10"  # KEDA đòi string
    assert so["spec"]["maxReplicaCount"] == 3 and so["spec"]["fallback"]["replicas"] == 3
    assert so["metadata"]["annotations"][configs.PAUSE_ANNOTATION] == "1"
    assert doc["spec"]["maxReplicaCount"] == 4  # bản gốc không bị sửa
    unpaused = configs.render_scaledobject(so, {}, paused=False)
    assert configs.PAUSE_ANNOTATION not in unpaused["metadata"]["annotations"]


def test_render_rejects_other_kinds():
    with pytest.raises(ValueError):
        configs.render_scaledobject({"kind": "Deployment", "spec": {}}, {}, paused=False)


def test_pinned_requirements_follow_runtime_deps_only():
    reqs = loadjob.pinned_requirements(REPO / "loadgen" / "uv.lock")
    names = {r.split("==")[0] for r in reqs}
    assert {"httpx", "httpcore", "anyio", "h11", "idna", "certifi"} <= names
    # không lấy nhóm dev, không lấy chính gói loadgen
    assert not names & {"pytest", "ruff", "loadgen"}
    assert all("==" in r for r in reqs)


def test_loadgen_args():
    a = loadjob.loadgen_args(
        "CONST",
        capacity=None,
        rate=2.0,
        duration=120,
        kb3_replicas=0,
        run_index=1,
        url="u",
        model="m",
        out="/out/main",
    )
    assert a[a.index("--rate") + 1] == "2" and a[a.index("--duration") + 1] == "120"
    b = loadjob.loadgen_args(
        "KB3",
        capacity=1.2,
        rate=None,
        duration=None,
        kb3_replicas=4,
        run_index=2,
        url="u",
        model="m",
        out="/o",
    )
    assert b[b.index("--capacity") + 1] == "1.2" and b[b.index("--replicas") + 1] == "4"


def test_job_manifest_is_guaranteed_and_optional_secret():
    t = matrix.parse(BASE).target
    t = matrix.Target(**{**t.__dict__, "api_key_secret": "vllm-api-key", "loadgen_cpu": "2"})
    j = loadjob.job_manifest("j", t, "A2-KB2-1", "main", ["--x"], ["httpx==0.28.1"], 100)
    c = j["spec"]["template"]["spec"]["containers"][0]
    assert c["resources"]["requests"] == c["resources"]["limits"]  # QoS Guaranteed
    assert c["resources"]["limits"]["cpu"] == "2"
    assert c["env"][0]["valueFrom"]["secretKeyRef"]["optional"] is True
    assert "@sha256:" in c["image"] and j["spec"]["backoffLimit"] == 0


def test_max_scrape_gap():
    assert collect.max_scrape_gap([[0, "1"], [5, "1"], [25, "1"], [30, "1"]]) == 20
    assert collect.max_scrape_gap([[0, "1"]]) is None


POD = {"name": "vllm-a", "deleting": False, "restarts": 0, "last_terminated": []}
GOOD_LG = {"valid": True, "send_lag_ok": True, "cpu_ok": True, "throttle_ok": True}


def _eval(**kw):
    args = dict(
        loadgen_rc=0,
        loadgen_checks=GOOD_LG,
        initial_ok=True,
        initial_note="",
        pods_start=[POD],
        pods_end=[POD],
        scrape_gaps={"vllm-a": 5.0},
    )
    args.update(kw)
    return checks.evaluate(**args)


def test_checks_valid_and_scale_down_of_new_pods_is_fine():
    end = [POD, {**POD, "name": "vllm-b"}]  # pod mới do scale-up: không làm lượt hỏng
    assert _eval(pods_end=end)["valid"] is True


@pytest.mark.parametrize(
    "kw, word",
    [
        ({"loadgen_rc": 1}, "mã 1"),
        ({"loadgen_checks": {**GOOD_LG, "valid": False, "throttle_ok": False}}, "throttle_ok"),
        ({"loadgen_checks": None}, "loadgen.json"),
        ({"initial_ok": False, "initial_note": "ready=0"}, "trạng thái đầu"),
        ({"pods_end": [{**POD, "name": "vllm-z"}]}, "bị thay"),
        ({"pods_end": [{**POD, "restarts": 1}]}, "restart"),
        ({"pods_end": [{**POD, "last_terminated": ["OOMKilled"]}]}, "OOMKilled"),
        ({"scrape_gaps": {"vllm-a": 40.0}}, "scrape"),
    ],
)
def test_checks_invalid_reasons(kw, word):
    r = _eval(**kw)
    assert r["valid"] is False and any(word in x for x in r["reasons"])


def test_progress_resume(tmp_path):
    p = Progress(tmp_path / "progress.json")
    assert p.should_run("A", 2)
    p.record("A", "invalid", "attempt-1")
    assert p.should_run("A", 2) and not p.should_run("A", 1)
    p.record("A", "done", "attempt-2")
    p2 = Progress(tmp_path / "progress.json")  # đọc lại từ file: như runner khởi động lại
    assert not p2.should_run("A", 5) and p2.attempts("A") == 2


def _req(i, t_sched, ttft, e2e, n_out=256, error=""):
    t = float(t_sched)
    return {
        "id": str(i),
        "t_sched": str(t),
        "t_send": str(t),
        "t_first": "" if error else str(t + ttft),
        "t_last": "" if error else str(t + e2e),
        "n_out": "0" if error else str(n_out),
        "error": error,
    }


def test_capacity_summarize_window_slo_and_little():
    # 1 req/s trong 100 s, mỗi request 2 s → B ≈ 2. Bỏ 20 s đầu. 1 request chậm (TTFT 3 s) và 1 lỗi.
    reqs = [_req(i, i, 0.1, 2.0) for i in range(100)]
    reqs[50] = _req(50, 50, 3.0, 4.0)
    reqs[60] = _req(60, 60, 0, 0, error="timeout")
    metrics = [(1000.0 + t, "vllm_running", 2.0) for t in range(0, 100, 5)]
    metrics += [(1000.0 + t, "vllm_waiting", 0.0) for t in range(0, 100, 5)]
    s = capacity.summarize_run(reqs, metrics, t0_unix=1000.0, rate=1.0, skip_s=20, duration_s=100)
    assert s["n_measured"] == 80 and s["n_error"] == 1
    assert s["slo_attainment"] == pytest.approx(78 / 80)
    assert s["B_server"] == 2.0 and s["little_ok"] is True
    assert s["tpot_p50_s"] == pytest.approx(1.9 / 255)


def test_capacity_picks_largest_passing_valid_level():
    c = [
        {
            "lambda_rps": 4,
            "valid": True,
            "slo_attainment": 1.0,
            "B_server": 10,
            "kv_cache_usage": 0.1,
            "gpu_util": 1,
        },
        {
            "lambda_rps": 6,
            "valid": False,
            "slo_attainment": 0.99,
            "B_server": 20,
            "kv_cache_usage": 0.2,
            "gpu_util": 1,
        },
        {
            "lambda_rps": 8,
            "valid": True,
            "slo_attainment": 0.5,
            "B_server": 90,
            "kv_cache_usage": 0.3,
            "gpu_util": 1,
        },
    ]
    r = capacity.capacity(c)
    assert r["C"] == 4 and r["threshold"]["A2_concurrency"] == 8
