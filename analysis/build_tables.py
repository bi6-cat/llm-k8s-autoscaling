"""Bảng phân tích từ dữ liệu của runner: mỗi lượt một dòng (Môi trường §14.2, §15, §16).

Khái niệm: Runner (experiments/runner) ghi mỗi lần chạy một lượt vào runs/<phiên>/<run_id>/attempt-<n>/:
    requests.csv (log máy tạo tải), loadgen.json (t0, các pha), metrics.csv.gz (chuỗi Prometheus),
    pods_timeline.json (mọi pod vLLM kèm mốc thời gian), alerts.jsonl, checks.json, metadata.json.
    "Lượt" = một ô cấu hình × kịch bản × số lần lặp (ví dụ A2-KB2-1); "lần thử" = một lần chạy lượt đó.
    Lần thử không hợp lệ được runner chạy lại thành attempt-2; dữ liệu attempt-1 vẫn giữ (Môi trường §17).
Mục đích: Tạo các bảng CSV để điền bảng nghiệm thu (Môi trường §16); charts.py vẽ C1–C4 từ cùng các số
    này. Mọi công thức nằm ở metrics.py (có unit test), file này chỉ đọc dữ liệu, ghép và ghi bảng:
      runs.csv    mỗi lần thử một dòng, cả lần không hợp lệ (cột `valid`); `counted` = lần thử hợp lệ
                  cuối cùng của lượt, là lần được đưa vào kết quả
      phases.csv  mỗi lần thử × pha của kịch bản một dòng (steady; pre, spike, drop; ramp, sustain)
      cells.csv   mỗi ô môi trường × cấu hình × kịch bản một dòng: số lượt, số lượt trượt N2a/N2b (KB2),
                  trung bình, min, max của các chỉ số chính, chỉ tính lần thử `counted` (§16: báo cáo trung
                  bình kèm min–max)
      alerts.csv  mỗi ĐỢT KÊU của mỗi chuỗi cảnh báo một dòng (một chuỗi kêu hai lần = hai dòng), kèm tỷ lệ
                  request xấu theo log client và cờ đợt đã kêu từ trước pha chính (N7, VH6)

Chạy (từ gốc repo):
    uv run --project analysis python -m analysis.build_tables runs/<phiên> [runs/<phiên 2> …] \\
        [--out <thư mục>] [--baseline S4]
"""

from __future__ import annotations

import argparse
import csv
import gzip
import json
import math
from collections import defaultdict
from collections.abc import Iterable, Mapping, Sequence
from pathlib import Path
from typing import Any

from analysis import metrics as m

STEP_S = m.STEP_S  # bước query_range của runner (một nguồn ở metrics.py)

# Pha được chấm SLO của từng kịch bản (Thông số §4, §7). Hai phút đầu của KB1, KB2 để ổn định, không tính;
# KB3 chỉ tính pha `sustain` vì trong pha `ramp` pod đầu tiên chắc chắn quá tải lúc chờ cold start. KB2
# không có chỉ tiêu N1 ("chỉ báo cáo"), nên báo cáo trên cả pre + spike + drop. Các pha ghép lại liền nhau.
SCORED_PHASES = {
    "KB1": ("steady",),
    "KB2": ("pre", "spike", "drop"),
    "KB3": ("sustain",),
    "CONST": ("steady",),
}

# Cảnh báo luôn kêu của kube-prometheus-stack (heartbeat để biết Alertmanager còn sống), không mang thông tin
IGNORED_ALERTS = frozenset({"Watchdog"})

RUN_COLUMNS = [
    # ── định danh lượt ──
    "session", "env", "run_id", "attempt", "config", "config_type", "scenario", "repeat",
    "capacity_rps", "rate_rps", "n_peak", "threshold", "max_replicas",
    "valid", "counted", "invalid_reasons", "git_commit", "git_dirty", "git_runner_commit", "vllm_image",
    "t0_unix", "duration_s",
    # ── tải và hiệu năng (log máy tạo tải); scored_* = các pha được chấm của kịch bản ──
    "n_planned", "n_sent", "n_error", "error_ratio", "error_types",
    "scored_phases", "scored_start_s", "scored_end_s",
    "slo_attainment", "ttft_p50_s", "ttft_p95_s", "ttft_p99_s", "tpot_p50_s", "tpot_p95_s",
    "throughput_tok_s", "tokens_out",
    # ── tài nguyên (cả pha chính) ──
    "has_timeline", "gpu_s", "gpu_h", "gpu_s_ksm", "gpu_vs_baseline", "slo_delta_vs_baseline_pp",
    "tokens_per_gpu_h",
    "gpu_util_mean", "vllm_cpu_cores_mean", "vllm_mem_bytes_max",
    # ── autoscaling ──
    "replicas_max", "replicas_ready_mean", "scale_changes", "scale_ups", "scale_downs", "flaps",
    "replicas_at_rise", "detect_s", "create_to_ready_s", "react_s", "recovery_s", "n_error_drop",
    "cooldown_s",
    # ── cảnh báo (N7) ──
    "alertnames", "alerts_at_start", "pages", "tickets", "false_pages",
    "slo_violation_s", "slo_alert_s", "slo_alert_at_start", "time_to_alert_s",
]  # fmt: skip

PHASE_COLUMNS = [
    "session", "env", "run_id", "attempt", "config", "scenario", "repeat", "valid", "counted",
    "phase", "start_s", "end_s", "n_sent", "n_error", "error_ratio", "error_types", "slo_attainment",
    "ttft_p50_s", "ttft_p95_s", "ttft_p99_s", "tpot_p50_s", "tpot_p95_s", "tokens_out", "throughput_tok_s",
    "gpu_s", "replicas_ready_mean",
]  # fmt: skip

ALERT_COLUMNS = [
    "session", "env", "run_id", "attempt", "config", "scenario", "repeat", "valid", "counted",
    "alertname", "severity", "first_s", "last_s", "firing_at_start", "client_bad_ratio", "false_page",
]  # fmt: skip

# Chỉ số gộp theo ô trong cells.csv (mỗi chỉ số ra ba cột _mean, _min, _max)
CELL_METRICS = [
    "slo_attainment", "ttft_p95_s", "tpot_p95_s", "error_ratio", "gpu_h", "gpu_vs_baseline",
    "slo_delta_vs_baseline_pp", "tokens_per_gpu_h", "replicas_ready_mean", "scale_changes", "flaps",
    "detect_s", "create_to_ready_s", "react_s", "recovery_s", "n_error_drop", "pages", "false_pages",
    "time_to_alert_s",
]  # fmt: skip


# ── Đọc dữ liệu một lần thử ─────────────────────────────────────────────────────────────────────────────


def _json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def read_metrics(path: Path) -> dict[str, list[tuple[float, dict[str, str], float]]]:
    """metrics.csv.gz (dạng dài: ts, name, labels JSON, value) → {name: [(ts, labels, value)]}.

    Dòng `_error_<name>` (truy vấn lỗi lúc thu) bị bỏ: chuỗi đó coi như rỗng. Runner v1 không ghi
    metrics.parquet như thiết kế ban đầu (collect.py), nên chỉ đọc CSV nén.
    """
    out: dict[str, list[tuple[float, dict[str, str], float]]] = defaultdict(list)
    if not path.exists():
        return out
    with gzip.open(path, "rt", newline="", encoding="utf-8") as fh:
        for r in csv.DictReader(fh):
            if r["name"].startswith("_error_"):
                continue
            v = float(r["value"])
            if not math.isnan(v):
                out[r["name"]].append((float(r["ts"]), json.loads(r["labels"]), v))
    return out


def max_by_ts(rows: Iterable[tuple[float, dict[str, str], float]]) -> list[tuple[float, float]]:
    """Gộp các chuỗi cùng tên về một giá trị mỗi mốc (lấy max), sắp theo thời gian.

    Dùng cho chuỗi cấp Deployment (số replica): bình thường chỉ có một chuỗi, nhưng kube-state-metrics khởi
    động lại giữa lượt thì chuỗi mới mang nhãn `pod` khác; cộng hai chuỗi ở mốc chồng nhau sẽ ra gấp đôi.
    """
    best: dict[float, float] = {}
    for ts, _, v in rows:
        best[ts] = max(v, best.get(ts, v))
    return sorted(best.items())


def _within(samples: Sequence[tuple[float, float]], start: float, end: float) -> list[tuple[float, float]]:
    return [(t, v) for t, v in samples if start <= t <= end]


def _time_mean(samples: Sequence[tuple[float, float]], start: float, end: float) -> float:
    """Trung bình theo thời gian trên [start, end] của chuỗi lấy mẫu đều STEP_S."""
    return m.integrate_steps(samples, start, end, STEP_S) / (end - start) if end > start else m.NAN


def analyze_attempt(d: Path) -> tuple[dict[str, Any], list[dict[str, Any]], list[dict[str, Any]]]:
    """Một thư mục attempt-<n> → (dòng runs.csv, các dòng phases.csv, các dòng alerts.csv)."""
    meta, lg = _json(d / "metadata.json"), _json(d / "loadgen.json")
    checks = (
        _json(d / "checks.json")
        if (d / "checks.json").exists()
        else {"valid": False, "reasons": ["thiếu checks.json"]}
    )
    spec = meta.get("spec", {})
    cfg = spec.get("config", {})
    t0, duration = float(lg["t0_unix"]), float(lg["duration_s"])
    w0, w1 = t0, t0 + duration  # cửa sổ pha chính, giây UNIX
    scenario = lg.get("scenario") or spec.get("scenario")
    phases = {k: (t0 + float(a), t0 + float(b)) for k, (a, b) in lg.get("phases_s", {}).items()}

    with (d / "requests.csv").open(newline="", encoding="utf-8") as fh:
        reqs = [m.parse_request(r, t0) for r in csv.DictReader(fh)]
    met = read_metrics(d / "metrics.csv.gz")
    # pods_timeline.json có từ 09/11 (PR #25). Lượt cũ hơn không có thì GPU-giờ chính xác để trống (NaN),
    # không ghi 0; vẫn còn GPU-giờ xấp xỉ từ kube-state-metrics (gpu_s_ksm).
    has_timeline = (d / "pods_timeline.json").exists()
    pods = _json(d / "pods_timeline.json").get("pods", []) if has_timeline else []
    start_names = (
        {p["name"] for p in _json(d / "pods_start.json")} if (d / "pods_start.json").exists() else set()
    )

    ident = {
        "session": meta.get("session"),
        "env": meta.get("env"),
        "run_id": meta.get("run_id"),
        "attempt": meta.get("attempt_dir", d.name),
        "config": cfg.get("id"),
        "scenario": scenario,
        "repeat": spec.get("repeat"),
        "valid": bool(checks.get("valid")),
    }

    # ── Hiệu năng trên các pha được chấm ──
    names = [p for p in SCORED_PHASES.get(scenario, ()) if p in phases] or list(phases)
    s0 = min(phases[p][0] for p in names) if names else w0
    s1 = max(phases[p][1] for p in names) if names else w1
    scored = m.phase_stats(reqs, s0, s1)
    whole = m.phase_stats(reqs, w0, w1)

    # ── Số replica (Deployment spec = desiredReplicas mà HPA đặt; ready = đang phục vụ) ──
    spec_s = max_by_ts(met.get("replicas_spec", []))
    ready_s = max_by_ts(met.get("replicas_ready", []))
    # Lấy thêm một mẫu ngay trước mép đầu để bắt được lần đổi xảy ra đúng lúc pha chính bắt đầu
    changes = m.scale_changes(_within(spec_s, w0 - STEP_S, w1))
    in_main = _within(spec_s, w0, w1)

    # ── GPU-giờ: chính xác từ mốc pod; xấp xỉ từ kube_deployment_status_replicas (không tính pod đang tắt) ──
    gpu_s = m.gpu_seconds(pods, w0, w1) if has_timeline else m.NAN
    gpu_ksm = m.integrate_steps(max_by_ts(met.get("replicas", [])), w0, w1, STEP_S)

    def container(name: str, c: str) -> list[float]:
        return [v for ts, lab, v in met.get(name, []) if lab.get("container") == c and w0 <= ts <= w1]

    gpu_util = [
        v for ts, _, v in met.get("gpu_util", []) if w0 <= ts <= w1
    ]  # mọi GPU của node, kể cả GPU rảnh

    # ── Từng pha của kịch bản (phases.csv) ──
    phase_rows = [
        {
            **ident,
            "phase": name,
            "start_s": a - t0,
            "end_s": b - t0,
            **m.phase_stats(reqs, a, b),
            "gpu_s": m.gpu_seconds(pods, a, b) if has_timeline else m.NAN,
            "replicas_ready_mean": _time_mean(_within(ready_s, a - STEP_S, b), a, b),
        }
        for name, (a, b) in sorted(phases.items(), key=lambda kv: kv[1][0])
    ]
    by_phase = {p["phase"]: p for p in phase_rows}

    # ── KB2: phản ứng (N2a), hồi phục (N2b), lỗi khi scale-down (N4) ──
    kb2: dict[str, Any] = {}
    if "spike" in phases:
        t_rise, t_spike_end = phases["spike"]
        kb2 = m.reaction(pods, start_names, t_rise)
        kb2["recovery_s"] = m.slo_recovery_s(reqs, t_rise, t_spike_end)
        # Số replica (spec) ở mẫu cuối trước lúc tải tăng. Lớn hơn 1 nghĩa là đã scale-up ngay ở mức nền 0,5 C
        # (dao động Poisson vượt threshold): pod đó không tính vào N2a (metrics.reaction), nên cần cột này để
        # đọc N2a đúng ngữ cảnh.
        before = [v for t, v in spec_s if t <= t_rise]
        kb2["replicas_at_rise"] = before[-1] if before else None
    if "drop" in by_phase:
        kb2["n_error_drop"] = by_phase["drop"]["n_error"]

    # ── Cảnh báo (N7) ──
    raw_alerts = []
    if (d / "alerts.jsonl").exists():
        lines = (d / "alerts.jsonl").read_text(encoding="utf-8").splitlines()
        raw_alerts = [
            a
            for a in map(json.loads, filter(None, lines))
            if a["labels"].get("alertname") not in IGNORED_ALERTS
        ]
    # Đợt kêu đã có từ trước pha chính (firing_at_start, xem metrics.classify_alerts) không do pha chính gây
    # ra: không đếm vào pages, false_pages, không dùng cho thời gian tới cảnh báo; tên ghi ở alerts_at_start.
    # Mốc đầu pha chính là t0 của máy tạo tải (w0), không phải t_main_start của metadata: runner ghi
    # t_main_start ngay sau khi apply Job, trước khi pod được xếp lịch và cài thư viện (kind 16/11: sớm hơn
    # t0 11 s). Đợt bắt đầu kêu trong khoảng đó không do tải của pha chính, và 5 phút trước nó không có
    # request nào nên sẽ bị chấm nhầm là page giả.
    alerts = m.classify_alerts(raw_alerts, reqs, main_start=w0, step_s=STEP_S)
    alert_rows = [
        {
            **ident,
            **{
                k: a[k]
                for k in ("alertname", "severity", "client_bad_ratio", "false_page", "firing_at_start")
            },
            "first_s": a["first"] - t0,
            "last_s": a["last"] - t0,
        }
        for a in alerts
    ]
    ours_all = [a for a in alerts if a["severity"] in ("page", "ticket")]
    ours = [a for a in ours_all if not a["firing_at_start"]]
    violation = m.slo_violation_start(reqs, w0, w1)
    # Đợt LLMSLOBurnFast ứng với lần vi phạm: đợt đầu tiên còn kêu tới lúc vi phạm hoặc sau đó. Đợt đã tắt
    # trước khi vi phạm bắt đầu không báo cho lần vi phạm này. Đợt kêu sớm rồi kêu tiếp qua mốc vi phạm thì
    # được dùng (time_to_alert_s âm), và vẫn có thể là page giả ở lúc firing (metrics.classify_alerts): hai
    # cột trả lời hai câu hỏi khác nhau của N7.
    burn = [
        a
        for a in alerts
        if a["alertname"] == "LLMSLOBurnFast" and violation is not None and a["last"] >= violation
    ]
    # Đợt đã kêu từ trước pha chính mà vẫn còn kêu lúc vi phạm bắt đầu (lượt trước quá tải, cửa sổ 5 phút
    # chưa sạch): người trực đã được báo, nhưng không đo được thời gian tới cảnh báo. Ghi cờ riêng để lượt đó
    # không bị đếm là "vi phạm mà không có cảnh báo" ở cells.csv, và không dùng đợt kêu sau đó (nếu có).
    slo_alert_at_start = any(a["firing_at_start"] for a in burn)
    fresh = [a["first"] for a in burn if not a["firing_at_start"]]
    slo_alert = min(fresh) if fresh and not slo_alert_at_start else None

    ov = cfg.get("overrides") or {}
    tokens_main = whole["tokens_out"]
    row = {
        **ident,
        "config_type": cfg.get("type"),
        "capacity_rps": lg.get("capacity_rps"),
        "rate_rps": lg.get("rate_rps"),
        "n_peak": spec.get("replicas_for_kb3") if scenario in ("KB2", "KB3") else None,
        "threshold": ov.get("threshold"),
        "max_replicas": ov.get("max_replicas"),
        "invalid_reasons": "; ".join(checks.get("reasons") or []),
        "git_commit": (meta.get("git") or {}).get("commit"),
        "git_dirty": (meta.get("git") or {}).get("dirty"),
        # Commit của code runner (đọc lúc runner khởi động, có từ 16/11). git_commit ở trên đọc lúc chạy lượt,
        # ứng với loadgen, uv.lock, file ScaledObject mà runner đọc lại từ đĩa ở mỗi lượt. Hai số khác nhau =
        # có commit giữa phiên.
        "git_runner_commit": (meta.get("git_runner") or {}).get("commit"),
        "vllm_image": (meta.get("vllm") or {}).get("image"),
        "t0_unix": t0,
        "duration_s": duration,
        "n_planned": lg.get("n_planned"),
        "n_sent": whole["n_sent"],
        "n_error": whole["n_error"],
        "error_ratio": whole["error_ratio"],
        "error_types": whole["error_types"],
        "scored_phases": "+".join(names),
        "scored_start_s": s0 - t0,
        "scored_end_s": s1 - t0,
        **{
            k: scored[k]
            for k in (
                "slo_attainment",
                "ttft_p50_s",
                "ttft_p95_s",
                "ttft_p99_s",
                "tpot_p50_s",
                "tpot_p95_s",
                "throughput_tok_s",
                "tokens_out",
            )
        },
        # Không có pods_timeline.json (lượt trước 09/11): gpu_s và react_s trống vì THIẾU DỮ LIỆU, không phải
        # vì không có pod mới; cells() dựa vào cột này để không đếm nhầm là trượt N2a.
        "has_timeline": has_timeline,
        "gpu_s": gpu_s,
        "gpu_h": gpu_s / 3600,
        "gpu_s_ksm": gpu_ksm,
        "tokens_per_gpu_h": tokens_main / (gpu_s / 3600) if gpu_s else m.NAN,
        "gpu_util_mean": m.mean(gpu_util),
        # Trung bình MỖI POD (mọi mẫu của mọi pod), dùng để chọn CPU request của pod vLLM; không phải tổng
        # CPU của cả cấu hình (S4 có N pod).
        "vllm_cpu_cores_mean": m.mean(container("cpu_cores", "vllm")),
        "vllm_mem_bytes_max": max(container("mem_bytes", "vllm"), default=m.NAN),
        "replicas_max": max((v for _, v in in_main), default=m.NAN),
        "replicas_ready_mean": _time_mean(_within(ready_s, w0 - STEP_S, w1), w0, w1),
        "scale_changes": len(changes),
        "scale_ups": sum(1 for _, a, b in changes if b > a),
        "scale_downs": sum(1 for _, a, b in changes if b < a),
        "flaps": m.count_flaps(changes),
        **kb2,
        "cooldown_s": meta.get("cooldown_s"),
        "alertnames": " ".join(sorted({a["alertname"] for a in ours})),
        "alerts_at_start": " ".join(sorted({a["alertname"] for a in ours_all if a["firing_at_start"]})),
        "pages": sum(1 for a in ours if a["severity"] == "page"),
        "tickets": sum(1 for a in ours if a["severity"] == "ticket"),
        "false_pages": sum(1 for a in ours if a["false_page"]),
        "slo_violation_s": None if violation is None else violation - t0,
        "slo_alert_s": None if slo_alert is None else slo_alert - t0,
        "slo_alert_at_start": slo_alert_at_start,
        "time_to_alert_s": None if violation is None or slo_alert is None else slo_alert - violation,
    }
    return row, phase_rows, alert_rows


# ── Ghép nhiều lần thử ────────────────────────────────────────────────────────────────────────────────


def find_attempts(session_dir: Path) -> tuple[list[Path], list[str]]:
    """Mọi thư mục <run_id>/attempt-<n> có đủ file để phân tích, và danh sách thư mục bị bỏ kèm lý do
    (lần thử lỗi giữa chừng chỉ có error.txt; máy tạo tải không chạy nên thiếu requests.csv)."""
    ok, skipped = [], []
    for d in sorted(session_dir.glob("*/attempt-*"), key=lambda p: (p.parent.name, _attempt_no(p))):
        missing = [f for f in ("metadata.json", "loadgen.json", "requests.csv") if not (d / f).exists()]
        if missing:
            skipped.append(f"{d}: thiếu {', '.join(missing)}")
        else:
            ok.append(d)
    return ok, skipped


def _attempt_no(d: Path) -> int:
    try:
        return int(d.name.split("-", 1)[1])
    except (IndexError, ValueError):
        return 0


def mark_counted(rows: list[dict[str, Any]]) -> None:
    """`counted` = lần thử hợp lệ có số thứ tự lớn nhất của mỗi lượt (session, run_id). Runner chỉ chạy lại
    lượt không hợp lệ, nên bình thường mỗi lượt có nhiều nhất một lần thử hợp lệ."""
    best: dict[tuple[str, str], tuple[int, dict[str, Any]]] = {}
    for r in rows:
        r["counted"] = False
        if r["valid"]:
            key, no = (r["session"], r["run_id"]), _attempt_no(Path(str(r["attempt"])))
            if key not in best or no > best[key][0]:
                best[key] = (no, r)
    for _, r in best.values():
        r["counted"] = True


def add_baseline(rows: list[dict[str, Any]], baseline: str) -> None:
    """GPU-giờ so với cấu hình tĩnh cấp theo đỉnh (S4 = S_N) và chênh lệch SLO attainment (N3).

    So trong cùng môi trường và cùng kịch bản, với trung bình các lần thử `counted` của `baseline`. Không có
    lượt baseline nào thì để trống. Chênh lệch SLO tính bằng điểm phần trăm (Thông số §6: ngưỡng thực tiễn
    5 điểm phần trăm).
    """
    ref: dict[tuple[Any, Any], list[dict[str, Any]]] = defaultdict(list)
    for r in rows:
        if r["counted"] and r["config"] == baseline:
            ref[(r["env"], r["scenario"])].append(r)
    for r in rows:
        base = ref.get((r["env"], r["scenario"]))
        gpu, slo = m.mean(b["gpu_s"] for b in base or []), m.mean(b["slo_attainment"] for b in base or [])
        r["gpu_vs_baseline"] = r["gpu_s"] / gpu if base and gpu else m.NAN
        r["slo_delta_vs_baseline_pp"] = (r["slo_attainment"] - slo) * 100 if base else m.NAN


def cells(rows: Sequence[dict[str, Any]]) -> list[dict[str, Any]]:
    """Gộp các lần thử `counted` theo ô môi trường × cấu hình × kịch bản: số lượt, trung bình, min, max.

    Môi trường §16: mỗi ô có 1–3 lượt; chỉ viết "A khác B" khi MỌI lượt cùng chiều và vượt ngưỡng thực tiễn,
    nên giữ cả min và max (và từng lượt ở runs.csv) thay vì chỉ trung bình.
    Ô trống (None, NaN) bị bỏ khi tính trung bình. Với KB2, trống ở react_s hay recovery_s lại là ca TRƯỢT
    (không có pod mới Ready, không hồi phục trước hết spike), nên đếm riêng ở n_no_new_ready và
    n_not_recovered; không thì ô 3 lượt có 1 lượt không hồi phục vẫn chỉ hiện trung bình của 2 lượt tốt.
    """
    groups: dict[tuple[Any, Any, Any], list[dict[str, Any]]] = defaultdict(list)
    for r in rows:
        if r["counted"]:
            groups[(r["env"], r["config"], r["scenario"])].append(r)
    out = []
    for (env, config, scenario), rs in sorted(groups.items(), key=lambda kv: tuple(map(str, kv[0]))):
        cell: dict[str, Any] = {
            "env": env,
            "config": config,
            "scenario": scenario,
            "n_runs": len(rs),
            "run_ids": " ".join(sorted(f"{r['session']}/{r['run_id']}" for r in rs)),
            # Cấu hình tĩnh (S1, S4) không tạo pod mới theo thiết kế: không đếm là "trượt". Lượt không có
            # pods_timeline.json (has_timeline) hay không có pha spike thì ô trống là do thiếu dữ liệu.
            "n_no_new_ready": sum(1 for r in rs if r.get("has_timeline") and r.get("react_s") is None)
            if scenario == "KB2" and all(r.get("config_type") == "scaledobject" for r in rs)
            else None,
            "n_not_recovered": sum(1 for r in rs if "recovery_s" in r and r["recovery_s"] is None)
            if scenario == "KB2"
            else None,
            # N7: SLO bị vi phạm (theo log client) mà LLMSLOBurnFast không kêu trong lượt. Trừ lượt mà cảnh
            # báo đã kêu sẵn từ trước pha chính (slo_alert_at_start): khi đó người trực đã được báo.
            "n_violation_no_alert": sum(
                1
                for r in rs
                if r.get("slo_violation_s") is not None
                and r.get("slo_alert_s") is None
                and not r.get("slo_alert_at_start")
            ),
        }
        for k in CELL_METRICS:
            vals = [float(v) for r in rs if (v := r.get(k)) is not None and not _isnan(v)]
            cell[f"{k}_mean"] = m.mean(vals)
            cell[f"{k}_min"] = min(vals, default=m.NAN)
            cell[f"{k}_max"] = max(vals, default=m.NAN)
        out.append(cell)
    return out


def _isnan(v: Any) -> bool:
    return isinstance(v, float) and math.isnan(v)


def _cell_value(v: Any) -> str:
    """Giá trị → chuỗi CSV. None, NaN → rỗng (pandas đọc thành NaN); số thực giữ 6 chữ số thập phân."""
    if v is None or _isnan(v):
        return ""
    if isinstance(v, float):
        return repr(v) if math.isinf(v) else repr(round(v, 6))  # repr giữ dấu: 'inf', '-inf'
    return str(v)


def write_csv(path: Path, rows: Iterable[Mapping[str, Any]], columns: Sequence[str]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as fh:
        w = csv.writer(fh, lineterminator="\n")
        w.writerow(columns)
        for r in rows:
            w.writerow([_cell_value(r.get(c)) for c in columns])


def build(session_dirs: Sequence[Path], baseline: str = "S4") -> dict[str, Any]:
    """Đọc mọi lần thử của các phiên, trả {runs, phases, cells, alerts, skipped}."""
    runs, phases, alerts, skipped = [], [], [], []
    seen_dirs: set[Path] = set()
    seen: set[tuple[Any, Any, Any]] = set()
    for sd in session_dirs:
        if sd.resolve() in seen_dirs:  # cùng thư mục truyền hai lần: mọi dòng sẽ bị nhân đôi
            skipped.append(f"{sd}: trùng thư mục đã đọc")
            continue
        seen_dirs.add(sd.resolve())
        found, skip = find_attempts(sd)
        skipped += skip
        for d in found:
            try:
                r, ps, al = analyze_attempt(d)
            except (KeyError, ValueError, OSError, EOFError, csv.Error) as e:
                # File hỏng hoặc ghi dở (chép bị ngắt, đầy đĩa): bỏ lần thử này, vẫn ghi bảng cho phần còn lại
                # ValueError gồm cả JSON lỗi; OSError, EOFError gồm cả gzip hỏng hoặc bị cắt.
                skipped.append(f"{d}: không đọc được ({type(e).__name__}: {e})")
                continue
            key = (r["session"], r["run_id"], r["attempt"])
            if key in seen:  # thư mục phiên được chép sang chỗ khác mà giữ tên phiên
                skipped.append(f"{d}: trùng lần thử {'/'.join(map(str, key))} đã đọc")
                continue
            seen.add(key)
            r["path"] = d  # thư mục lần thử, cho charts.py đọc lại chuỗi thời gian (không ghi vào runs.csv)
            runs.append(r)
            phases += ps
            alerts += al
    mark_counted(runs)
    add_baseline(runs, baseline)
    counted = {(r["session"], r["run_id"], r["attempt"]): r["counted"] for r in runs}
    for x in (*phases, *alerts):
        x["counted"] = counted[(x["session"], x["run_id"], x["attempt"])]
    return {"runs": runs, "phases": phases, "cells": cells(runs), "alerts": alerts, "skipped": skipped}


def _fmt(v: Any, spec: str) -> str:
    return "-" if v is None or _isnan(v) else format(v, spec)


def main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    p.add_argument("sessions", type=Path, nargs="+", help="thư mục phiên runs/<phiên> (một hoặc nhiều)")
    p.add_argument("--out", type=Path, help="thư mục ghi bảng (mặc định: <phiên đầu tiên>/tables)")
    p.add_argument("--baseline", default="S4", help="cấu hình tĩnh cấp theo đỉnh để so GPU-giờ (mặc định S4)")
    a = p.parse_args(argv)

    res = build(a.sessions, a.baseline)
    out = a.out or a.sessions[0] / "tables"
    write_csv(out / "runs.csv", res["runs"], RUN_COLUMNS)
    write_csv(out / "phases.csv", res["phases"], PHASE_COLUMNS)
    write_csv(out / "alerts.csv", res["alerts"], ALERT_COLUMNS)
    cell_cols = ["env", "config", "scenario", "n_runs", "run_ids"]
    cell_cols += ["n_no_new_ready", "n_not_recovered", "n_violation_no_alert"]
    cell_cols += [f"{k}_{s}" for k in CELL_METRICS for s in ("mean", "min", "max")]
    write_csv(out / "cells.csv", res["cells"], cell_cols)

    for s in res["skipped"]:
        print(f"bỏ qua {s}")
    for r in res["runs"]:
        flag = "" if r["valid"] else f"  [không hợp lệ: {r['invalid_reasons']}]"
        print(
            f"{r['session']}/{r['run_id']}/{r['attempt']}: SLO {_fmt(r['slo_attainment'], '.3f')}"
            f"  TTFT p95 {_fmt(r['ttft_p95_s'], '.2f')} s  lỗi {r['n_error']}/{r['n_sent']}"
            f"  GPU-giờ {_fmt(r['gpu_h'], '.3f')}  replica max {_fmt(r['replicas_max'], 'g')}"
            f"  phản ứng {_fmt(r.get('react_s'), '.0f')} s  hồi phục {_fmt(r.get('recovery_s'), '.0f')} s"
            f"  page {r['pages']} (giả {r['false_pages']}){flag}"
        )
    print(f"đã ghi {len(res['runs'])} lần thử, {len(res['cells'])} ô vào {out}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
