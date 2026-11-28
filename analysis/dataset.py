"""Đóng gói bộ dữ liệu (P4): chép các phiên luận văn dùng từ runs/ sang dataset/, quét bí mật, ghi checksum.

Khái niệm:
    runs/ (không nằm trong Git) chứa mọi phiên đo, kể cả lượt thử và lượt hỏng. Bộ dữ liệu chỉ gồm các phiên
    mà chương 5 và `make analysis` dùng (SESSIONS), giữ NGUYÊN bố cục thư mục của runs/, nên
    `make analysis DATA=dataset` chạy được mà không phải đổi đường dẫn nào.
    Trước khi chép, mọi file (kể cả .gz, giải nén trong bộ nhớ) được quét theo SECRET_PATTERNS: token
    Telegram, token Hugging Face, khoá riêng, chứng chỉ kubeconfig, JWT, khoá truy cập, IP công khai (v4, v6),
    địa chỉ email; cộng đúng các giá trị trong .env (mặc định đọc .env nếu có). File nhị phân không quét được
    cũng tính là một chỗ khớp. Thấy chỗ khớp thì dừng, không chép gì, và chỉ in tên file, số dòng, tên mẫu:
    không in giá trị, để output của script không thành chỗ lộ bí mật.
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
from collections.abc import Iterable, Mapping
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
    # Không dùng \b ở hai đầu: token sát chữ trong URL Bot API (`/bot<id>:<khoá>/`), có thể tận cùng bằng -
    "telegram_bot_token": re.compile(r"(?<!\d)\d{8,10}:[A-Za-z0-9_-]{35}(?![A-Za-z0-9_-])"),
    "huggingface_token": re.compile(r"\bhf_[A-Za-z0-9]{30,}\b"),
    "private_key": re.compile(r"-----BEGIN [A-Z ]*PRIVATE KEY-----"),
    "kubeconfig_credential": re.compile(r"\b(?:client-key-data|client-certificate-data|token-data)\b"),
    "aws_access_key": re.compile(r"\b(?:AKIA|ASIA)[A-Z0-9]{16}\b"),
    "bearer_token": re.compile(r"(?i)\bbearer\s+[A-Za-z0-9._~+/=-]{16,}"),
    # JWT, ví dụ token của ServiceAccount
    "jwt": re.compile(r"\beyJ[A-Za-z0-9_-]{10,}\.eyJ[A-Za-z0-9_-]{10,}\.[A-Za-z0-9_-]{10,}"),
    # khoá = giá trị, ví dụ `--api-key=…`, `VLLM_API_KEY=…`, `password: …`. Đầu tên chỉ cấm chữ và số liền
    # trước (cho phép `_`, để khớp tên biến môi trường); `api_key_secret` (tên Secret) không khớp nhờ \b cuối.
    "key_value": re.compile(
        r"(?i)(?<![A-Za-z0-9])(?:api[_-]?key|secret[_-]?access[_-]?key|access[_-]?key[_-]?id|password|passwd)\b"
        r"""\s*["']?\s*[:=]\s*["']?[^\s"',}]{8,}"""
    ),
    "email": re.compile(r"\b[A-Za-z0-9._%+-]+@[A-Za-z0-9-]+(?:\.[A-Za-z0-9-]+)*\.[A-Za-z]{2,}\b"),
}
# Ứng viên IP, sau đó ipaddress lọc lấy địa chỉ công khai. IPv4 được phép có dấu chấm cuối câu.
IPV4 = re.compile(r"(?<!\d)(?<!\d\.)(?:\d{1,3}\.){3}\d{1,3}(?!\.?\d)")
IPV6 = re.compile(r"(?<![\w:])(?:[0-9A-Fa-f]{0,4}:){2,7}[0-9A-Fa-f]{0,4}(?![\w:])")
ENV_MIN_LEN = 8  # giá trị .env ngắn hơn (ví dụ `1`, `true`) khớp quá nhiều, không phải bí mật
BINARY = (
    "binary_unscanned"  # file không phải .gz mà không đọc được như văn bản UTF-8: không quét được, nên dừng
)


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


def _lines(path: Path) -> list[str] | None:
    """Các dòng của file (giải nén .gz); None nếu không phải văn bản UTF-8 (ảnh, tar, zip…)."""
    raw = path.read_bytes()
    if path.suffix == ".gz":
        raw = gzip.decompress(raw)
    if b"\0" in raw:
        return None
    try:
        return raw.decode("utf-8").splitlines()
    except UnicodeDecodeError:
        return None


def env_values(env_file: Path) -> dict[str, str]:
    """KEY → giá trị trong file .env (bỏ comment, cả comment cuối dòng, và giá trị ngắn hơn ENV_MIN_LEN)."""
    out = {}
    for line in env_file.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, _, val = line.removeprefix("export ").partition("=")
        val = val.strip()
        if val[:1] in ("'", '"') and val[0] in val[1:]:
            val = val[1 : val.index(val[0], 1)]  # giá trị trong ngoặc: bỏ mọi thứ sau ngoặc đóng
        else:
            val = re.split(r"\s+#", val, maxsplit=1)[0].strip()  # `KEY=giá trị  # ghi chú`
        if len(val) >= ENV_MIN_LEN:
            out[key.strip()] = val
    return out


def _public_ip(line: str) -> list[str]:
    hits = []
    for name, rx in (("public_ipv4", IPV4), ("public_ipv6", IPV6)):
        for cand in rx.findall(line):
            try:
                if ipaddress.ip_address(cand).is_global:
                    hits.append(name)
                    break
            except ValueError:  # trông giống IP mà không phải, ví dụ 300.1.2.3 hay giờ 12:34:56
                continue
    return hits


def scan_line(line: str, literals: Mapping[str, str] | None = None) -> list[str]:
    """Tên các mẫu bí mật khớp trong một dòng (rỗng = sạch). Không trả giá trị khớp."""
    hits = [name for name, rx in SECRET_PATTERNS.items() if rx.search(line)]
    hits += _public_ip(line)
    hits += [f"env:{k}" for k, v in (literals or {}).items() if v in line]
    return hits


def scan(
    src: Path, files: Iterable[str], literals: Mapping[str, str] | None = None
) -> list[tuple[str, int, str]]:
    """(file, số dòng, tên mẫu) cho mọi chỗ khớp; file nhị phân ghi một dòng BINARY ở dòng 0."""
    found = []
    for rel in files:
        lines = _lines(src / rel)
        if lines is None:
            found.append((rel, 0, BINARY))
            continue
        for no, line in enumerate(lines, 1):
            found += [(rel, no, name) for name in scan_line(line, literals)]
    return found


def sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def write_sums(out: Path, files: Iterable[str]) -> int:
    """Ghi out/SHA256SUMS cho đúng các file đã cho (đường dẫn tương đối so với out), trả số file."""
    files = sorted(files)
    lines = [f"{sha256(out / f)}  {f}\n" for f in files]
    (out / "SHA256SUMS").write_bytes("".join(lines).encode())
    return len(files)


def check_sums(out: Path) -> list[str]:
    """Các file sai checksum hoặc bị mất (rỗng = khớp hết). Không có SHA256SUMS → FileNotFoundError."""
    bad = []
    for line in (out / "SHA256SUMS").read_text(encoding="utf-8").splitlines():
        if not line.strip():
            continue
        digest, _, rel = line.partition(" ")
        rel = rel[1:] if rel[:1] in (" ", "*") else rel  # `  path` (văn bản) hoặc ` *path` (sha256sum -b)
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


def index_rows(out: Path, files: Iterable[str]) -> list[dict[str, str]]:
    """Mỗi metadata.json của runner trong `files` một dòng, theo đường dẫn."""
    rows = []
    for meta in sorted(out / f for f in files if f.rsplit("/", 1)[-1] == "metadata.json"):
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


def write_index(out: Path, files: Iterable[str]) -> int:
    rows = index_rows(out, files)
    with (out / "INDEX.csv").open("w", encoding="utf-8", newline="") as f:
        w = csv.DictWriter(f, fieldnames=INDEX_COLUMNS, lineterminator="\n")
        w.writeheader()
        w.writerows(rows)
    return len(rows)


def package(src: Path, out: Path, literals: Mapping[str, str] | None = None) -> int:
    """Quét rồi chép các phiên sang out, ghi INDEX.csv và SHA256SUMS. Trả 0 nếu xong, 1 nếu thấy bí mật.

    SHA256SUMS gồm đúng các file vừa chép, INDEX.csv và README.md (nếu có trong out), không gồm file lạ khác.
    """
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
    n_index = write_index(out, files)
    n_sums = write_sums(out, [*files, "INDEX.csv", *(["README.md"] if (out / "README.md").is_file() else [])])
    size = sum((out / f).stat().st_size for f in files)
    print(f"Chép {len(files)} file ({size / 1e6:.1f} MB) từ {len(SESSIONS)} phiên; INDEX.csv {n_index} dòng; "
          f"SHA256SUMS {n_sums} file.")  # fmt: skip
    return 0


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("src", nargs="?", type=Path, help="thư mục runs/ (bỏ trống khi dùng --check)")
    ap.add_argument("--out", type=Path, default=Path("dataset"))
    ap.add_argument(
        "--env-file", type=Path, help="quét thêm đúng các giá trị trong file này; mặc định .env nếu có"
    )
    ap.add_argument("--no-env-file", action="store_true", help="không quét giá trị của .env")
    ap.add_argument("--check", type=Path, metavar="DIR", help="chỉ kiểm DIR/SHA256SUMS")
    a = ap.parse_args(argv)
    if a.check:
        if not (a.check / "SHA256SUMS").is_file():
            print(
                f"không có {a.check / 'SHA256SUMS'}: thư mục chưa đóng gói hoặc chưa tải đủ", file=sys.stderr
            )
            return 1
        bad = check_sums(a.check)
        for rel in bad:
            print(f"sai checksum hoặc thiếu: {rel}", file=sys.stderr)
        print("SHA256SUMS: khớp hết" if not bad else f"SHA256SUMS: {len(bad)} file không khớp")
        return 1 if bad else 0
    if a.src is None:
        ap.error("cần thư mục nguồn (runs/) hoặc --check")
    # Khoá Vast và R2 không có dạng nhận ra được bằng mẫu (chuỗi hex), nên mặc định so thêm với .env
    env_file = None if a.no_env_file else a.env_file or (Path(".env") if Path(".env").is_file() else None)
    if env_file is None:
        print("Cảnh báo: không so với .env; khoá chỉ là chuỗi hex (Vast, R2) có thể lọt.", file=sys.stderr)
    literals = env_values(env_file) if env_file else None
    return package(a.src, a.out, literals)


if __name__ == "__main__":
    raise SystemExit(main())
