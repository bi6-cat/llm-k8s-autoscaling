"""Dòng lệnh của máy tạo tải: `python -m loadgen ...` (chạy từ gốc repo).

Khái niệm: `python -m <gói>` chạy file __main__.py của gói đó.
Mục đích: Một lệnh cho một lượt tải: chọn kịch bản và C, sinh lịch từ seed, gửi, rồi ghi vào thư mục
    `--out`:
      requests.csv  mỗi request một dòng (Môi trường §14.2)
      loadgen.json  tham số, seed, mốc t0_unix, pha của kịch bản, kết quả tự kiểm tra (§17)
    `--workers k` chia lịch cho k tiến trình (workers.py) khi một event loop không đủ CPU; lịch và các file
    kết quả không đổi.
    Khoá API đọc từ biến môi trường LOADGEN_API_KEY, không nhận qua tham số dòng lệnh vì tham số hiện ra
    trong `ps` và trong log của shell.

Ví dụ:
    # Xem trước lịch của KB2 với C = 1,2 req/s, không gửi gì
    uv run --project loadgen python -m loadgen --scenario KB2 --capacity 1.2 --dry-run
    # Chạy thật tới vLLM qua port-forward, lượt số 1
    LOADGEN_API_KEY=... uv run --project loadgen python -m loadgen --url http://localhost:8000 \\
        --model qwen2.5-1.5b --scenario KB2 --capacity 1.2 --run-index 1 --out runs/kb2-a2-1
"""

from __future__ import annotations

import argparse
import json
import os
import sys
import time
from pathlib import Path
from typing import Any

from loadgen import checks, scenarios, sender, workers
from loadgen.schedule import PROMPT_MAX, PROMPT_MIN, build_plan, derive_seed


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    p = argparse.ArgumentParser(prog="python -m loadgen", description="Máy tạo tải open-loop cho vLLM")
    p.add_argument("--scenario", choices=scenarios.SCENARIOS, required=True)
    p.add_argument("--capacity", type=float, help="C: năng lực một replica, req/s (KB1–KB3)")
    p.add_argument("--replicas", type=int, default=4, help="N cho KB3: đỉnh = 0,75 × N × C (mặc định 4)")
    p.add_argument("--rate", type=float, help="Tốc độ cố định, req/s (CONST, dùng cho ĐG1)")
    p.add_argument("--duration", type=float, help="Thời lượng, giây (CONST)")
    p.add_argument(
        "--run-index", type=int, default=0, help="Số thứ tự lượt; cùng kịch bản + số này = cùng lịch"
    )
    p.add_argument("--url", help="Địa chỉ gốc của vLLM, ví dụ http://localhost:8000")
    p.add_argument("--model", help="Tên model, trùng --served-model-name của vLLM")
    p.add_argument("--max-tokens", type=int, default=256)
    p.add_argument("--timeout", type=float, default=120.0, help="Timeout cả request, giây")
    p.add_argument(
        "--no-ignore-eos", action="store_true", help="Không gửi ignore_eos (server không phải vLLM)"
    )
    p.add_argument(
        "--workers",
        type=int,
        default=1,
        help="Số tiến trình gửi tải, mỗi tiến trình một event loop dùng tối đa 1 lõi (mặc định 1)",
    )
    p.add_argument("--out", type=Path, help="Thư mục kết quả (tạo nếu chưa có; không ghi đè requests.csv)")
    p.add_argument("--dry-run", action="store_true", help="Chỉ in thống kê lịch, không gửi")
    args = p.parse_args(argv)

    if args.scenario == "CONST":
        if args.rate is None or args.duration is None:
            p.error("CONST cần --rate và --duration")
    elif args.capacity is None:
        p.error(f"{args.scenario} cần --capacity (C, req/s)")
    if args.workers < 1:
        p.error("--workers phải ≥ 1")
    if not args.dry_run and (args.url is None or args.model is None or args.out is None):
        p.error("chạy thật cần --url, --model, --out (hoặc dùng --dry-run)")
    return args


def make_scenario(args: argparse.Namespace) -> scenarios.Scenario:
    if args.scenario == "KB1":
        return scenarios.kb1(args.capacity)
    if args.scenario == "KB2":
        return scenarios.kb2(args.capacity)
    if args.scenario == "KB3":
        return scenarios.kb3(args.capacity, args.replicas)
    return scenarios.constant(args.rate, args.duration)


def plan_summary(scenario: scenarios.Scenario, plan: list[Any]) -> str:
    """Số request theo từng phút: đủ để mắt thường thấy hình dạng λ(t) trước khi chạy thật."""
    per_min: dict[int, int] = {}
    for r in plan:
        per_min[int(r.t_sched // 60)] = per_min.get(int(r.t_sched // 60), 0) + 1
    lines = [f"{scenario.name}: {len(plan)} request trong {scenario.duration_s / 60:.1f} phút"]
    lines += [f"  phút {m:>2}: {n:>5} request ({n / 60:.2f} req/s)" for m, n in sorted(per_min.items())]
    return "\n".join(lines)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    scenario = make_scenario(args)
    plan = build_plan(scenario, args.run_index)
    if args.dry_run:
        print(plan_summary(scenario, plan))
        return 0

    target = sender.Target(
        base_url=args.url,
        model=args.model,
        api_key=os.environ.get("LOADGEN_API_KEY") or None,
        max_tokens=args.max_tokens,
        timeout_s=args.timeout,
        ignore_eos=not args.no_ignore_eos,
    )
    prompt_seed = derive_seed(scenario.name, args.run_index, "text")
    args.out.mkdir(parents=True, exist_ok=True)

    try:
        fh = sender.open_csv(args.out / "requests.csv")
    except FileExistsError:
        print(
            f"Lỗi: {args.out / 'requests.csv'} đã có. Chọn --out khác để không ghi đè lượt cũ.",
            file=sys.stderr,
        )
        return 1
    # cpu.stat là của cả cgroup (cả pod), nên đọc một lần ở tiến trình cha là đủ cho mọi tiến trình con
    cg_before, cg_t0 = checks.read_cgroup_cpu_stat(), time.perf_counter()
    with fh:
        result = workers.run_load(plan, target, sender.CsvSink(fh), prompt_seed, args.workers)
    cg_after, cg_t1 = checks.read_cgroup_cpu_stat(), time.perf_counter()
    failed = [w for w in result.workers if w.error]
    summary = checks.summarize(
        result.records_by_worker,
        [w.loop_lags_s for w in result.workers],
        max(w.cpu_max_fraction for w in result.workers),
        cg_before,
        cg_after,
        cgroup_elapsed_s=cg_t1 - cg_t0,
        n_planned=len(plan),
        workers_failed=len(failed),
    )

    records = result.records
    n_err = sum(1 for r in records if r["error"])
    meta = {
        "scenario": scenario.name,
        "capacity_rps": args.capacity,
        "replicas": args.replicas if scenario.name == "KB3" else None,
        "rate_rps": args.rate,
        "run_index": args.run_index,
        "seeds": {s: derive_seed(scenario.name, args.run_index, s) for s in ("time", "prompt", "text")},
        "prompt_words": [PROMPT_MIN, PROMPT_MAX],
        "target": {
            "url": args.url,
            "model": args.model,
            "max_tokens": args.max_tokens,
            "timeout_s": args.timeout,
            "ignore_eos": target.ignore_eos,
        },
        "t0_unix": result.t0_unix,
        "duration_s": scenario.duration_s,
        "wall_s": result.wall_s,
        "phases_s": scenario.phases,
        "n_planned": len(plan),
        "n_done": len(records),
        "n_error": n_err,
        "workers": args.workers,
        # Số đo của từng tiến trình, để biết tiến trình nào kéo `checks` xuống
        "worker_stats": [
            {
                "n_done": w.n_done,
                "wall_s": w.wall_s,
                "cpu_max_pct": round(w.cpu_max_fraction * 100, 1),
                "send_lag_ms": checks.lag_stats_ms(checks.send_lags_ms(rs)),
                "loop_lag_ms": checks.lag_stats_ms([x * 1000 for x in w.loop_lags_s]),
                "error": w.error,
            }
            for w, rs in zip(result.workers, result.records_by_worker, strict=True)
        ],
        "checks": summary,
    }
    (args.out / "loadgen.json").write_text(json.dumps(meta, indent=2, ensure_ascii=False), encoding="utf-8")

    lag_p99 = summary["send_lag_ms"]["p99"]
    print(
        f"{scenario.name}: {len(records)}/{len(plan)} request, {n_err} lỗi, "
        f"lệch lịch p99 {'–' if lag_p99 is None else f'{lag_p99:.1f}'} ms, "
        f"CPU tối đa {summary['cpu_max_pct']}% ({args.workers} tiến trình), hợp lệ: {summary['valid']}"
    )
    if not summary["valid"]:
        print(
            "CẢNH BÁO: máy tạo tải không đạt tự kiểm tra, lượt này không hợp lệ (Môi trường §17)",
            file=sys.stderr,
        )
    if failed:
        for j, w in enumerate(result.workers):
            if w.error:
                print(f"Lỗi: tiến trình gửi tải {j} dừng giữa chừng: {w.error}", file=sys.stderr)
        return 1  # thiếu request: runner đánh dấu lượt invalid theo mã thoát
    return 0


if __name__ == "__main__":
    sys.exit(main())
