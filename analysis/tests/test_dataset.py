"""Test cho analysis/dataset.py (đóng gói bộ dữ liệu P4).

Khái niệm: Dựng một runs/ GIẢ gồm đủ các phiên trong dataset.SESSIONS (mỗi phiên vài file nhỏ, một lượt runner
    có metadata.json, checks.json và metrics.csv.gz), cùng các file phải bị bỏ (figures/, .lock, log Ansible).
Mục đích: Kiểm (1) mẫu bí mật khớp đúng chỗ và không khớp nhầm tên Secret, IP nội bộ hay giờ; (2) gặp bí
    mật, kể cả trong file .gz, hoặc gặp file nhị phân thì dừng mà không chép; (3) đóng gói bỏ đúng file;
    INDEX.csv và SHA256SUMS chỉ gồm file đã đóng gói; checksum kiểm lại khớp (cả dạng `sha256sum -b`) và phát
    hiện file bị sửa.
"""

from __future__ import annotations

import csv
import gzip
import json
from pathlib import Path

import pytest

from analysis import dataset as ds

RUN = "v2-vm/v2-dg2/A2-KB2-1/attempt-1"


@pytest.mark.parametrize(
    ("line", "expected"),
    [
        ("connect 8.8.8.8:22", ["public_ipv4"]),
        ('"instance": "10.42.0.12:8080"', []),  # IP nội bộ của pod
        ("version 0.31.0.1 and 127.0.0.1", []),
        ("--api-key=abcdefgh123", ["key_value"]),
        ('"api_key_secret": "vllm-api-key"', []),  # tên Secret, không phải khoá
        ("token 1234567890:" + "A" * 35, ["telegram_bot_token"]),
        ("HF_TOKEN=hf_" + "a" * 34, ["huggingface_token"]),
        ("-----BEGIN OPENSSH PRIVATE KEY-----", ["private_key"]),
        ("    client-key-data: LS0t", ["kubeconfig_credential"]),
        ("mail me@example.com", ["email"]),
        ("image=vllm/vllm-openai:v0.31.0@sha256:c1c9f6fd", []),
        ("https://api.telegram.org/bot1234567890:" + "A" * 34 + "-/sendMessage", ["telegram_bot_token"]),
        ("VLLM_API_KEY=abcdefgh1234", ["key_value"]),
        ("R2_SECRET_ACCESS_KEY: abcdefgh12345", ["key_value"]),
        ("ssh: connect to host 8.8.8.8.", ["public_ipv4"]),
        ("addr 2001:4860:4860::8888 up", ["public_ipv6"]),
        ("fe80::1 and 2026-11-18T18:59:11Z at 18:59:11", []),  # IPv6 link-local, giờ
        ("token: eyJhbGciOiJSUzI1.eyJpc3MiOiJrdWJl.c2lnbmF0dXJlXw", ["jwt"]),
    ],
)
def test_scan_line(line, expected):
    assert ds.scan_line(line) == expected


def test_scan_line_env_literal_reports_key_not_value():
    assert ds.scan_line("x s3cr3t-value-123 y", {"R2_SECRET": "s3cr3t-value-123"}) == ["env:R2_SECRET"]


def test_env_values_skips_comments_and_short_values(tmp_path: Path):
    env = tmp_path / ".env"
    env.write_text(
        "# c\nA=1\nexport B='longvalue99' # q\nC = \"another-long\"\nD=plainvalue1  # khoá R2\n\n",
        encoding="utf-8",
    )
    assert ds.env_values(env) == {"B": "longvalue99", "C": "another-long", "D": "plainvalue1"}


def _runs(tmp_path: Path) -> Path:
    src = tmp_path / "runs"
    for s in ds.SESSIONS:
        (src / s).mkdir(parents=True)
        (src / s / "note.txt").write_text("ok\n", encoding="utf-8")
    run = src / RUN
    run.mkdir(parents=True)
    meta = {
        "session": "v2-dg2", "env": "cloud", "run_id": "A2-KB2-1", "attempt_dir": "attempt-1",
        "spec": {"config": {"id": "A2"}, "scenario": "KB2", "capacity": 3.5, "rate": None},
        "t_begin": 1794998575.4, "target": {"model": "qwen2.5-3b"},
    }  # fmt: skip
    (run / "metadata.json").write_text(json.dumps(meta), encoding="utf-8")
    (run / "checks.json").write_text('{"valid": true}', encoding="utf-8")
    (run / "metrics.csv.gz").write_bytes(gzip.compress(b"ts,name,labels,value\n1,x,{},1\n"))
    (src / "v2-vm/v2-dg2/figures").mkdir()
    (src / "v2-vm/v2-dg2/figures/c1.svg").write_text("<svg/>", encoding="utf-8")
    (src / "v2-vm/v2-dg2/.lock").write_text("", encoding="utf-8")
    (src / "v2-evidence/console").mkdir()
    (src / "v2-evidence/console/01-bootstrap-ansible.log").write_text("ok\n", encoding="utf-8")
    return src


def test_package_copies_indexes_and_checksums(tmp_path: Path):
    src, out = _runs(tmp_path), tmp_path / "dataset"
    out.mkdir()
    (out / "README.md").write_text("# x\n", encoding="utf-8")
    assert ds.package(src, out) == 0
    assert (out / RUN / "metrics.csv.gz").is_file()
    assert not (out / "v2-vm/v2-dg2/figures").exists()
    assert not (out / "v2-vm/v2-dg2/.lock").exists()
    assert not (out / "v2-evidence/console/01-bootstrap-ansible.log").exists()
    with (out / "INDEX.csv").open(encoding="utf-8") as f:
        rows = list(csv.DictReader(f))
    assert rows == [
        {
            "path": RUN, "session": "v2-dg2", "env": "cloud", "run_id": "A2-KB2-1", "attempt": "attempt-1",
            "config": "A2", "scenario": "KB2", "rate_rps": "", "capacity_rps": "3.5",
            "t_begin_local": "2026-11-18T17:42+07:00", "model": "qwen2.5-3b", "valid": "true",
        }
    ]  # fmt: skip
    sums = (out / "SHA256SUMS").read_text(encoding="utf-8")
    assert "  README.md\n" in sums and "  INDEX.csv\n" in sums and "SHA256SUMS" not in sums
    assert ds.check_sums(out) == []
    (out / RUN / "checks.json").write_text('{"valid": false}', encoding="utf-8")
    (out / "note-moi.txt").write_text("", encoding="utf-8")  # file thêm sau không có trong SHA256SUMS: bỏ qua
    assert ds.check_sums(out) == [f"{RUN}/checks.json"]
    assert ds.package(src, out) == 1  # thư mục đích đã có các phiên: không ghi đè


def test_package_checksums_only_packaged_files_and_reads_binary_mode_lines(tmp_path: Path):
    src, out = _runs(tmp_path), tmp_path / "dataset"
    (out / "cu").mkdir(parents=True)
    (out / "cu/metadata.json").write_text("{}", encoding="utf-8")  # file lạ có sẵn trong out
    assert ds.package(src, out) == 0
    assert "cu/metadata.json" not in (out / "SHA256SUMS").read_text(encoding="utf-8")
    with (out / "INDEX.csv").open(encoding="utf-8") as f:
        assert [r["path"] for r in csv.DictReader(f)] == [RUN]
    sums = out / "SHA256SUMS"
    sums.write_text("\n" + sums.read_text(encoding="utf-8").replace("  ", " *"), encoding="utf-8")
    assert ds.check_sums(out) == []


def test_package_stops_on_binary_file(tmp_path: Path, capsys):
    src, out = _runs(tmp_path), tmp_path / "dataset"
    (src / "v2-evidence/anh.png").write_bytes(b"\x89PNG\r\n\x1a\n\0\0")
    assert ds.package(src, out) == 1
    assert "v2-evidence/anh.png:0: binary_unscanned" in capsys.readouterr().err


def test_main_check_without_sums_fails_cleanly(tmp_path: Path, capsys):
    assert ds.main(["--check", str(tmp_path)]) == 1
    assert "không có" in capsys.readouterr().err


def test_package_stops_on_secret_in_gz_without_copying(tmp_path: Path, capsys):
    src, out = _runs(tmp_path), tmp_path / "dataset"
    (src / RUN / "metrics.csv.gz").write_bytes(gzip.compress(b"ts\nhost 8.8.4.4\n"))
    assert ds.package(src, out) == 1
    assert not out.exists()
    err = capsys.readouterr().err
    assert f"{RUN}/metrics.csv.gz:2: public_ipv4" in err and "8.8.4.4" not in err


def test_collect_fails_on_missing_session(tmp_path: Path):
    with pytest.raises(FileNotFoundError):
        ds.collect(tmp_path, ["khong-co"])
