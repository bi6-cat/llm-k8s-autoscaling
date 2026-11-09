"""Sao lưu dữ liệu một phiên lên Cloudflare R2 bằng rclone (Môi trường §3.8).

Khái niệm: R2 = kho lưu trữ đối tượng của Cloudflare, tương thích S3. rclone = công cụ đồng bộ file với kho
    đó. `rclone copy --checksum` so nội dung thay vì thời gian sửa, nên chạy lại chỉ gửi phần còn thiếu, và
    không bao giờ xoá gì trên R2 (khác `rclone sync`). `rclone check --one-way` xác nhận mọi file trên máy
    đều đã có trên R2 với cùng checksum.
Mục đích: V2 không có phiên dự phòng, và dữ liệu trên VM thuê mất khi trả máy. Sau mỗi lượt đẩy cả thư mục
    phiên. Sao lưu lỗi KHÔNG dừng phiên (đo tiếp có giá trị hơn, lần sau đẩy bù), nhưng báo Telegram; trước
    khi huỷ máy, `check` phải đạt (`make release`).

Chạy:
    # Đẩy và xác nhận toàn bộ runs/ (make backup)
    uv run --project experiments python -m experiments.runner.backup push --remote "$R2_REMOTE"
    # Chỉ xác nhận; mã thoát khác 0 nếu còn thiếu file (make backup-check)
    uv run --project experiments python -m experiments.runner.backup check --remote "$R2_REMOTE"
"""

from __future__ import annotations

import argparse
import os
import subprocess
import sys
from dataclasses import dataclass
from pathlib import Path

# .lock: khoá file của runner, không phải dữ liệu. *.secret, *.bak: thư mục phiên từng chứa API key và bản sao
# inventory có IP công khai (runs/vast-v2b-20261108/); không để bí mật rời máy (CONTRIBUTING §2).
EXCLUDES = ["--exclude", ".lock", "--exclude", "*.secret", "--exclude", "*.bak"]


@dataclass
class Result:
    ok: bool
    detail: str  # dòng lỗi cuối của rclone, để đọc được trong tin báo; rỗng nếu đạt


def _run(args: list[str], timeout_s: float) -> Result:
    """Chạy rclone, không raise: thiếu rclone hay quá giờ đều là kết quả 'không đạt', phiên vẫn chạy tiếp."""
    try:
        proc = subprocess.run(["rclone", *args], capture_output=True, text=True, timeout=timeout_s)
    except FileNotFoundError:
        return Result(False, "không tìm thấy rclone trong PATH")
    except subprocess.TimeoutExpired:
        return Result(False, f"rclone quá {timeout_s:.0f} s")
    if proc.returncode == 0:
        return Result(True, "")
    lines = proc.stderr.strip().splitlines()
    return Result(False, f"rclone thoát {proc.returncode}: {lines[-1][:300] if lines else ''}")


def push(local: Path, remote: str, timeout_s: float = 900) -> Result:
    """Đẩy `local` lên `remote` (ví dụ r2:bucket/runs/v2-dg2). 900 s: một lượt vài MB, dư cho mạng xấu."""
    return _run(["copy", "--checksum", *EXCLUDES, str(local), remote], timeout_s)


def check(local: Path, remote: str, timeout_s: float = 900) -> Result:
    """--one-way: mọi file ở `local` phải có trên `remote`; R2 có thêm file phiên khác thì không sao."""
    return _run(["check", "--one-way", *EXCLUDES, str(local), remote], timeout_s)


def main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser(
        prog="python -m experiments.runner.backup", description="Sao lưu runs/ lên R2"
    )
    p.add_argument("action", choices=["push", "check"])
    p.add_argument(
        "--remote", default=os.environ.get("R2_REMOTE"), help="Ví dụ r2:llm-thesis/runs (hoặc R2_REMOTE)"
    )
    p.add_argument("--runs-dir", type=Path, default=Path("runs"))
    args = p.parse_args(argv)
    if not args.remote:
        print("Thiếu --remote hoặc biến R2_REMOTE (xem .env.example)", file=sys.stderr)
        return 2
    if not args.runs_dir.is_dir():
        print(f"Không có {args.runs_dir}: không có gì để sao lưu", file=sys.stderr)
        return 0 if args.action == "check" else 2
    results = [push(args.runs_dir, args.remote)] if args.action == "push" else []
    results.append(check(args.runs_dir, args.remote))
    for r in results:
        if not r.ok:
            print(f"Sao lưu KHÔNG đạt: {r.detail}", file=sys.stderr)
            return 1
    print(f"Sao lưu đạt: mọi file trong {args.runs_dir} đã có trên {args.remote}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
