"""Báo tin vận hành của runner qua Telegram (Môi trường §6.2).

Khái niệm: Bot Telegram nhận tin qua một lời gọi HTTP tới Bot API (`sendMessage`), cần token của bot và id
    của nhóm chat. Bot này riêng với Alertmanager: báo về runner (lượt lỗi, sao lưu lỗi), không về SLO.
Mục đích: Phiên chạy khoảng 10 giờ không người trực, nên phải biết ngay khi có sự cố. Gửi lỗi KHÔNG bao giờ
    làm dừng phiên: Telegram chập chờn không được làm mất lượt đo. Không có token thì chỉ ghi log.
"""

from __future__ import annotations

import json
import os
import urllib.error
import urllib.request
from collections.abc import Callable
from dataclasses import dataclass


@dataclass
class Notifier:
    token: str | None
    chat_id: str | None
    log: Callable[[str], None] = print
    timeout_s: float = 10  # đừng để mạng treo giữ runner quá lâu giữa hai lượt

    @classmethod
    def from_env(cls, log: Callable[[str], None] = print) -> Notifier:
        return cls(os.environ.get("TELEGRAM_BOT_TOKEN"), os.environ.get("TELEGRAM_CHAT_ID"), log)

    @property
    def enabled(self) -> bool:
        return bool(self.token and self.chat_id)

    def send(self, text: str) -> bool:
        """Trả True nếu Telegram nhận tin. Lưu ý: URL chứa token, nên không bao giờ ghi URL vào log."""
        if not self.enabled:
            return False
        req = urllib.request.Request(
            f"https://api.telegram.org/bot{self.token}/sendMessage",
            # 4096 là giới hạn độ dài một tin của Telegram; tin dài hơn sẽ bị từ chối
            data=json.dumps({"chat_id": self.chat_id, "text": text[:4096]}).encode(),
            headers={"Content-Type": "application/json"},
        )
        try:
            with urllib.request.urlopen(req, timeout=self.timeout_s):
                return True
        except (urllib.error.URLError, TimeoutError, OSError) as e:
            # str(HTTPError) chỉ có mã và lý do, str(URLError) chỉ có lý do: đều không chứa URL
            self.log(f"không gửi được Telegram: {type(e).__name__}: {e}")
            return False
