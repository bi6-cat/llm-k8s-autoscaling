"""Sao lưu và báo tin không được làm mất lượt đo, và phải báo đúng khi hỏng.

Khái niệm: Dùng rclone giả (script trong PATH) để kiểm đúng tham số và cách xử lý mã lỗi, không cần R2 thật.
Mục đích: Bảo vệ ba tính chất: `check` phát hiện thiếu file; lỗi sao lưu hay Telegram không dừng phiên;
    token Telegram không lọt vào log.
"""

from __future__ import annotations

import os
import stat
import urllib.error
from pathlib import Path

import pytest

from experiments.runner import backup
from experiments.runner.notify import Notifier


@pytest.fixture
def fake_rclone(tmp_path, monkeypatch):
    """Tạo `rclone` giả ghi tham số ra file; biến FAKE_RC đặt mã thoát."""
    bin_dir = tmp_path / "bin"
    bin_dir.mkdir()
    calls = tmp_path / "calls.txt"
    script = bin_dir / "rclone"
    script.write_text(
        f'#!/bin/sh\necho "$*" >> {calls}\necho "boom line" >&2\nexit ${{FAKE_RC:-0}}\n', encoding="utf-8"
    )
    script.chmod(script.stat().st_mode | stat.S_IEXEC)
    monkeypatch.setenv("PATH", f"{bin_dir}{os.pathsep}{os.environ['PATH']}")
    return calls


def test_push_uses_checksum_copy_and_never_sync(fake_rclone, tmp_path):
    assert backup.push(tmp_path, "r2:b/s").ok
    line = fake_rclone.read_text(encoding="utf-8")
    assert line.startswith("copy --checksum --exclude .lock")
    assert "sync" not in line  # sync xoá file trên đích khi máy thiếu


def test_secrets_never_leave_the_machine(fake_rclone, tmp_path):
    backup.push(tmp_path, "r2:b/s")
    assert "--exclude *.secret" in fake_rclone.read_text(encoding="utf-8")


def test_check_is_one_way_and_reports_failure(fake_rclone, tmp_path, monkeypatch):
    monkeypatch.setenv("FAKE_RC", "1")
    r = backup.check(tmp_path, "r2:b/s")
    assert not r.ok and "boom line" in r.detail
    assert "--one-way" in fake_rclone.read_text(encoding="utf-8")


def test_missing_rclone_is_a_result_not_a_crash(tmp_path, monkeypatch):
    monkeypatch.setenv("PATH", str(tmp_path))
    r = backup.push(tmp_path, "r2:b/s")
    assert not r.ok and "rclone" in r.detail


def test_cli_returns_nonzero_when_check_fails(fake_rclone, tmp_path, monkeypatch):
    monkeypatch.setenv("FAKE_RC", "1")
    assert backup.main(["check", "--remote", "r2:b", "--runs-dir", str(tmp_path)]) == 1


def test_cli_needs_a_remote(tmp_path, monkeypatch):
    monkeypatch.delenv("R2_REMOTE", raising=False)
    assert backup.main(["check", "--runs-dir", str(tmp_path)]) == 2


def test_notifier_without_token_does_nothing():
    assert Notifier(None, None).send("x") is False


def test_notifier_failure_does_not_raise_or_leak_token(monkeypatch):
    def boom(*_a, **_k):
        raise urllib.error.URLError("network down")

    monkeypatch.setattr("urllib.request.urlopen", boom)
    logged: list[str] = []
    assert Notifier("SECRET-TOKEN", "1", logged.append).send("x") is False
    assert logged and "SECRET-TOKEN" not in logged[0]


def test_after_run_keeps_session_alive_when_backup_fails(fake_rclone, tmp_path, monkeypatch):
    from types import SimpleNamespace

    from experiments.runner import session

    monkeypatch.setenv("FAKE_RC", "1")
    sent: list[str] = []
    ctx = session.Context(
        matrix=SimpleNamespace(session="s"),  # type: ignore[arg-type]
        kube=None,  # type: ignore[arg-type]
        prom=None,  # type: ignore[arg-type]
        repo_root=Path("."),
        runs_dir=tmp_path,
        backup_remote="r2:b/runs/",
    )
    monkeypatch.setattr(ctx, "notify", sent.append, raising=False)
    session.after_run(ctx, tmp_path, "A1-KB1-1", "done", "")  # không raise
    assert "r2:b/runs/s" in fake_rclone.read_text(encoding="utf-8")  # không có `//` khi gốc kết thúc bằng `/`
    assert any("sao lưu lỗi" in m for m in sent)
