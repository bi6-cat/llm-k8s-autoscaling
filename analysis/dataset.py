"""Đóng gói bộ dữ liệu (P4): chép các phiên luận văn dùng từ runs/ sang dataset/, quét bí mật, ghi checksum.

Khái niệm:
    runs/ (không nằm trong Git) chứa mọi phiên đo, kể cả lượt thử và lượt hỏng. Bộ dữ liệu chỉ gồm các phiên
    mà chương 5 và `make analysis` dùng (SESSIONS), giữ NGUYÊN bố cục thư mục của runs/, nên
    `make analysis DATA=dataset` chạy được mà không phải đổi đường dẫn nào.
    Trước khi chép, mọi file (kể cả .gz, giải nén trong bộ nhớ) được quét theo SECRET_PATTERNS: token
    Telegram, token Hugging Face, khoá riêng, chứng chỉ kubeconfig, khoá truy cập, IP công khai, địa chỉ
    email. Thấy một chỗ khớp thì dừng, không chép gì, và chỉ in tên file, số dòng, tên mẫu: không in giá trị,
    để output của script không thành chỗ lộ bí mật. `--env-file .env` quét thêm đúng các giá trị trong .env.
    SHA256SUMS cùng định dạng với `sha256sum` (`<hex>  <đường dẫn>`), nên kiểm được bằng `sha256sum -c` hoặc
    `--check` của script này.
    INDEX.csv: mỗi lần thử của runner (thư mục có metadata.json) một dòng: phiên, môi trường, cấu hình,
    kịch bản, tải, giờ bắt đầu, model, có hợp lệ không. Các phiên không do runner ghi (VH, ĐG3, LT7, LT8) mô
    tả ở dataset/README.md.
Mục đích: Chuẩn bị dataset/ để công bố cùng luận văn (Kế hoạch §10.6, P4). Script KHÔNG tải lên đâu cả.
Tham khảo: Kế hoạch §10.6, §10.7 ý 5; Môi trường §14.2 (dữ liệu một lượt)

Chạy (từ gốc repo):
    uv run --project analysis python -m analysis.dataset runs --out dataset [--env-file .env]
    uv run --project analysis python -m analysis.dataset --check dataset
"""

from __future__ import annotations

import argparse
import csv
import datetime as dt
import gzip
import hashlib
import ipaddress
import json
import re
import shutil
import sys
from collections.abc import Iterable, Iterator, Mapping
from pathlib import Path

# Các phiên chương 5 dùng, tương đối so với runs/. Target analysis của Makefile đọc đúng các phiên này.
SESSIONS = (
    "dg1-v2-4060ti",  # ĐG1 trên V2: năng lực 1 replica, 5 mức tải (5.2, LT5, LT6)
    "v2-vm",  # bản kéo từ VM V2: ma trận ĐG2 v2-dg2 (5.3, 5.4, VH6), ĐG3 cold start, VH2–VH4, console
    "v2-evidence",  # cấu hình đúng bản đã chạy, console, Node k3s, phần cứng của V2
    "sim/mp-final-w2",  # LT5 trên simulator kind
    "sim/tr7-kb2-sim-2",  # LT5 trên simulator kind (S1 và A2, KB2)
    "sim/lt7-20261116-165323",  # LT7: tốc độ rescale của HPA
    "sim/lt8-20261116-131116",  # LT8: burn rate
    "ops-vh2-git-20261124-164415",  # VH2 qua Git trên kind: lượt thử
    "ops-vh2-git-20261124-171557",  # VH2 qua Git trên kind: lượt chính (4.5, 5.5)
)

# Bỏ khi chép. Tên file hoặc thư mục ở bất kỳ mức nào, hoặc đường dẫn đầy đủ (tương đối so với runs/).
EXCLUDE_NAMES = frozenset({"figures", "__pycache__", ".lock"})  # hình dựng lại được; khoá phiên của runner
EXCLUDE_PATHS = frozenset(
    {
        # Log Ansible của `make bootstrap`: ghi kèm địa chỉ máy thuê (v2-evidence/README.md)
        "v2-evidence/console/01-bootstrap-ansible.log",
    }
)

SECRET_PATTERNS = {
    "telegram_bot_token": re.compile(r"\b\d{8,10}:[A-Za-z0-9_-]{35}\b"),
    "huggingface_token": re.compile(r"\bhf_[A-Za-z0-9]{30,}\b"),
    "private_key": re.compile(r"-----BEGIN [A-Z ]*PRIVATE KEY-----"),
    "kubeconfig_credential": re.compile(r"\b(?:client-key-data|client-certificate-data|token-data)\b"),
    "aws_access_key": re.compile(r"\b(?:AKIA|ASIA)[A-Z0-9]{16}\b"),
    "bearer_token": re.compile(r"(?i)\bbearer\s+[A-Za-z0-9._~+/=-]{16,}"),
    # khoá = giá trị, ví dụ `--api-key=…`, `password: …`; `api_key_secret` (tên Secret) không khớp vì \b
    "key_value": re.compile(
        r"(?i)\b(?:api[_-]?key|secret[_-]?access[_-]?key|access[_-]?key[_-]?id|password|passwd)\b"
        r"""\s*["']?\s*[:=]\s*["']?[^\s"',}]{8,}"""
    ),
    "email": re.compile(r"\b[A-Za-z0-9._%+-]+@[A-Za-z0-9-]+(?:\.[A-Za-z0-9-]+)*\.[A-Za-z]{2,}\b"),
}
IPV4 = re.compile(r"(?<![\d.])(?:\d{1,3}\.){3}\d{1,3}(?![\d.])")
ENV_MIN_LEN = 8  # giá trị .env ngắn hơn (ví dụ `1`, `true`) khớp quá nhiều, không phải bí mật


def _skip(rel: str) -> bool:
    return rel in EXCLUDE_PATHS or any(part in EXCLUDE_NAMES for part in rel.split("/"))


def collect(src: Path, sessions: Iterable[str] = SESSIONS) -> list[str]:
    """Đường dẫn tương đối (dấu /) của mọi file sẽ chép, đã sắp xếp. Thiếu phiên nào → FileNotFoundError."""
    out = []
    for s in sessions:
        root = src / s
        if not root.is_dir():
            raise FileNotFoundError(f"không thấy phiên {root}")
        for f in root.rglob("*"):
            rel = f.relative_to(src).as_posix()
            if f.is_file() and not _skip(rel):
                out.append(rel)
    return sorted(out)


def _lines(path: Path) -> Iterator[str]:
    raw = path.read_bytes()
    if path.suffix == ".gz":
        raw = gzip.decompress(raw)
    yield from raw.decode("utf-8", errors="replace").splitlines()


def env_values(env_file: Path) -> dict[str, str]:
    """KEY → giá trị trong file .env (bỏ comment, dòng trống, giá trị ngắn hơn ENV_MIN_LEN)."""
    out = {}
    for line in env_file.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, _, val = line.removeprefix("export ").partition("=")
        val = val.strip().strip("\"'")
        if len(val) >= ENV_MIN_LEN:
            out[key.strip()] = val
    return out


def scan_line(line: str, literals: dict[str, str] | None = None) -> list[str]:
    """Tên các mẫu bí mật khớp trong một dòng (rỗng = sạch). Không trả giá trị khớp."""
    hits = [name for name, rx in SECRET_PATTERNS.items() if rx.search(line)]
    for ip in IPV4.findall(line):
        try:
            if ipaddress.ip_address(ip).is_global:
                hits.append("public_ipv4")
                break
        except ValueError:  # 4 số nhưng không phải IP, ví dụ 300.1.2.3
            continue
    hits += [f"env:{k}" for k, v in (literals or {}).items() if v in line]
    return hits


def scan(
    src: Path, files: Iterable[str], literals: Mapping[str, str] | None = None
) -> list[tuple[str, int, str]]:
    """(file, số dòng, tên mẫu) cho mọi chỗ khớp trong các file."""
    found = []
    for rel in files:
        for no, line in enumerate(_lines(src / rel), 1):
            found += [(rel, no, name) for name in scan_line(line, literals)]
    return found


def sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def write_sums(out: Path) -> int:
    """Ghi out/SHA256SUMS cho mọi file trong out (trừ chính nó), trả số file."""
    files = sorted(f.relative_to(out).as_posix() for f in out.rglob("*") if f.is_file())
    files = [f for f in files if f != "SHA256SUMS"]
    lines = [f"{sha256(out / f)}  {f}\n" for f in files]
    (out / "SHA256SUMS").write_bytes("".join(lines).encode())
    return len(files)


def check_sums(out: Path) -> list[str]:
    """Các file sai checksum hoặc bị mất (rỗng = khớp hết)."""
    bad = []
    for line in (out / "SHA256SUMS").read_text(encoding="utf-8").splitlines():
        digest, _, rel = line.partition("  ")
        p = out / rel
        if not p.is_file() or sha256(p) != digest:
            bad.append(rel)
    return bad


def _local(ts: float | None) -> str:
    """Giờ Việt Nam (UTC+7) dạng ISO tới phút; nhật ký và luận văn ghi giờ theo múi này."""
    if ts is None:
        return ""
    return dt.datetime.fromtimestamp(ts, dt.timezone(dt.timedelta(hours=7))).isoformat(timespec="minutes")


INDEX_COLUMNS = (
    "path", "session", "env", "run_id", "attempt", "config", "scenario", "rate_rps", "capacity_rps",
    "t_begin_local", "model", "valid",
)  # fmt: skip


def index_rows(out: Path) -> list[dict[str, str]]:
    """Mỗi metadata.json của runner một dòng, theo đường dẫn."""
    rows = []
    for meta in sorted(out.rglob("metadata.json")):
        d = json.loads(meta.read_text(encoding="utf-8"))
        spec = d.get("spec", {})
        checks = meta.with_name("checks.json")
        valid = json.loads(checks.read_text(encoding="utf-8")).get("valid") if checks.is_file() else None
        rows.append(
            {
                "path": meta.parent.relative_to(out).as_posix(),
                "session": d.get("session", ""),
                "env": d.get("env", ""),
                "run_id": d.get("run_id", ""),
                "attempt": d.get("attempt_dir", ""),
                "config": spec.get("config", {}).get("id", ""),
                "scenario": spec.get("scenario", ""),
                "rate_rps": "" if spec.get("rate") is None else spec["rate"],
                "capacity_rps": "" if spec.get("capacity") is None else spec["capacity"],
                "t_begin_local": _local(d.get("t_begin")),
                "model": d.get("target", {}).get("model", ""),
                "valid": "" if valid is None else str(valid).lower(),
            }
        )
    return rows


def write_index(out: Path) -> int:
    rows = index_rows(out)
    with (out / "INDEX.csv").open("w", encoding="utf-8", newline="") as f:
        w = csv.DictWriter(f, fieldnames=INDEX_COLUMNS, lineterminator="\n")
        w.writeheader()
        w.writerows(rows)
    return len(rows)


def package(src: Path, out: Path, literals: dict[str, str] | None = None) -> int:
    """Quét rồi chép các phiên sang out, ghi INDEX.csv và SHA256SUMS. Trả 0 nếu xong, 1 nếu thấy bí mật."""
    files = collect(src)
    found = scan(src, files, literals)
    if found:
        for rel, no, name in found:
            print(f"bí mật? {rel}:{no}: {name}", file=sys.stderr)
        print(f"Dừng: {len(found)} chỗ khớp, chưa chép gì. Sửa hoặc thêm vào EXCLUDE_PATHS.", file=sys.stderr)
        return 1
    clash = [s for s in SESSIONS if (out / s).exists()]
    if clash:
        print(f"Dừng: {out} đã có {', '.join(clash)}; xoá các thư mục đó rồi chạy lại.", file=sys.stderr)
        return 1
    for rel in files:
        (out / rel).parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(src / rel, out / rel)
    n_index = write_index(out)
    n_sums = write_sums(out)
    size = sum((out / f).stat().st_size for f in files)
    print(f"Chép {len(files)} file ({size / 1e6:.1f} MB) từ {len(SESSIONS)} phiên; INDEX.csv {n_index} dòng; "
          f"SHA256SUMS {n_sums} file.")  # fmt: skip
    return 0


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("src", nargs="?", type=Path, help="thư mục runs/ (bỏ trống khi dùng --check)")
    ap.add_argument("--out", type=Path, default=Path("dataset"))
    ap.add_argument("--env-file", type=Path, help="quét thêm đúng các giá trị trong file này (ví dụ .env)")
    ap.add_argument("--check", type=Path, metavar="DIR", help="chỉ kiểm DIR/SHA256SUMS")
    a = ap.parse_args(argv)
    if a.check:
        bad = check_sums(a.check)
        for rel in bad:
            print(f"sai checksum hoặc thiếu: {rel}", file=sys.stderr)
        print("SHA256SUMS: khớp hết" if not bad else f"SHA256SUMS: {len(bad)} file không khớp")
        return 1 if bad else 0
    if a.src is None:
        ap.error("cần thư mục nguồn (runs/) hoặc --check")
    literals = env_values(a.env_file) if a.env_file else None
    return package(a.src, a.out, literals)


if __name__ == "__main__":
    raise SystemExit(main())
