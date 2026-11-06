"""Checkpoint của một phiên: runs/<session>/progress.json.

Khái niệm: Checkpoint = ghi lại tiến độ sau mỗi bước, để chương trình bị ngắt (mất điện, mất SSH, VM khởi
    động lại) thì chạy lại sẽ tiếp từ chỗ dở thay vì làm lại từ đầu.
Mục đích: Sau mỗi lượt ghi trạng thái `done` (hợp lệ), `invalid` (có dữ liệu nhưng phải chạy lại) hoặc
    `error` (runner không chạy được lượt). Khi chạy lại phiên: bỏ qua `done`, chạy lại `invalid`/`error`
    tối đa `max_attempts` lần. Ghi file theo kiểu "ghi file tạm rồi đổi tên" (atomic): bị ngắt giữa lúc
    ghi thì file cũ vẫn nguyên, không bao giờ còn một progress.json ghi dở.
"""

from __future__ import annotations

import json
import os
import time
from pathlib import Path
from typing import Any


class Progress:
    def __init__(self, path: Path) -> None:
        self.path = path
        self.data: dict[str, Any] = {"runs": {}}
        if path.exists():
            self.data = json.loads(path.read_text(encoding="utf-8"))

    def status(self, run_id: str) -> str | None:
        return self.data["runs"].get(run_id, {}).get("status")

    def attempts(self, run_id: str) -> int:
        return len(self.data["runs"].get(run_id, {}).get("attempts", []))

    def should_run(self, run_id: str, max_attempts: int) -> bool:
        """Lượt cần chạy nếu chưa `done` và chưa hết số lần thử. Hàm thuần trên dữ liệu đã nạp."""
        return self.status(run_id) != "done" and self.attempts(run_id) < max_attempts

    def record(self, run_id: str, status: str, attempt_dir: str, note: str = "") -> None:
        entry = self.data["runs"].setdefault(run_id, {"attempts": []})
        entry["status"] = status
        entry["attempts"].append(
            {"dir": attempt_dir, "status": status, "note": note, "at": time.strftime("%Y-%m-%dT%H:%M:%S%z")}
        )
        self.save()

    def save(self) -> None:
        self.path.parent.mkdir(parents=True, exist_ok=True)
        tmp = self.path.with_suffix(".json.tmp")
        tmp.write_text(json.dumps(self.data, indent=2, ensure_ascii=False), encoding="utf-8")
        os.replace(tmp, self.path)  # đổi tên là thao tác nguyên tử trên cùng filesystem
