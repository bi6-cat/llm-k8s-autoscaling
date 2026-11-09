"""Dòng lệnh của runner: `python -m experiments.runner ...` (chạy từ gốc repo).

Ví dụ:
    # Xem trước danh sách lượt, không đụng cluster
    uv run --project experiments python -m experiments.runner --matrix experiments/matrix-sim.yaml --dry-run
    # Chạy phiên trên kind (context kind-llm-sim); bị ngắt thì chạy lại đúng lệnh này để chạy tiếp
    uv run --project experiments python -m experiments.runner --matrix experiments/matrix-sim.yaml \\
        --context kind-llm-sim
    # Chỉ chạy một lượt
    ... --only A2-CONST2-1
"""

from __future__ import annotations

import argparse
import os
import sys
from pathlib import Path

from experiments.runner import matrix as matrix_mod
from experiments.runner.kube import Kube, Prometheus
from experiments.runner.notify import Notifier
from experiments.runner.session import Context, log, run_session


def main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser(
        prog="python -m experiments.runner", description="Runner đánh giá autoscaling"
    )
    p.add_argument("--matrix", type=Path, required=True, help="File ma trận YAML")
    p.add_argument("--runs-dir", type=Path, default=Path("runs"), help="Thư mục gốc dữ liệu (gitignore)")
    p.add_argument("--context", help="Context kubectl (mặc định: context hiện tại của kubeconfig)")
    p.add_argument("--only", action="append", help="Chỉ chạy run_id này (lặp lại được)")
    p.add_argument("--max-attempts", type=int, default=2, help="Số lần thử tối đa mỗi lượt (mặc định 2)")
    p.add_argument("--dry-run", action="store_true", help="Chỉ in danh sách lượt")
    p.add_argument(
        "--backup-remote",
        default=os.environ.get("R2_REMOTE"),
        help="Gốc rclone để sao lưu sau mỗi lượt, ví dụ r2:llm-thesis/runs (mặc định: biến R2_REMOTE)",
    )
    p.add_argument("--no-backup", action="store_true", help="Cho phép chạy phiên cloud mà không sao lưu")
    args = p.parse_args(argv)

    try:
        m = matrix_mod.load(args.matrix)
    except matrix_mod.MatrixError as e:
        print(f"Lỗi file ma trận {args.matrix}: {e}", file=sys.stderr)
        return 2

    log(f"phiên {m.session} ({m.env}): {len(m.runs)} lượt")
    for r in m.runs:
        if r.scenario == "CONST":
            what = f"{r.rate:g} req/s × {r.duration:g} s"
        else:
            what = f"C = {r.capacity:g} req/s"
        log(f"  {r.run_id:<16} {r.config.id} ({r.config.type}) × {r.scenario}, {what}")
    if args.dry_run:
        return 0

    # Dữ liệu trên VM thuê mất khi trả máy và V2 không có phiên dự phòng: phiên cloud phải tự chọn bỏ sao lưu.
    if m.env == "cloud" and not args.backup_remote and not args.no_backup:
        print("Phiên cloud cần --backup-remote hoặc R2_REMOTE (hoặc --no-backup nếu cố ý)", file=sys.stderr)
        return 2
    notifier = Notifier.from_env(log)
    if not notifier.enabled:
        log("không có TELEGRAM_BOT_TOKEN/TELEGRAM_CHAT_ID: sẽ không báo Telegram")

    kube = Kube(context=args.context)
    ctx = Context(
        matrix=m,
        kube=kube,
        prom=Prometheus(kube, m.target.prometheus_service),
        repo_root=Path.cwd(),
        runs_dir=args.runs_dir,
        backup_remote=None if args.no_backup else args.backup_remote,
        notifier=notifier,
    )
    final = run_session(ctx, set(args.only) if args.only else None, args.max_attempts)
    log("kết quả: " + ", ".join(f"{k}={v}" for k, v in final.items()))
    return 0 if all(v == "done" for k, v in final.items() if not args.only or k in args.only) else 1


if __name__ == "__main__":
    sys.exit(main())
