"""Wrapper mỏng quanh `kubectl`, và truy vấn Prometheus qua API server proxy.

Khái niệm: API server proxy = API server của Kubernetes chuyển tiếp request HTTP tới một Service trong
    cluster: `kubectl get --raw /api/v1/namespaces/<ns>/services/<svc>:<port>/proxy/<đường dẫn>`.
    Runner dùng cách này để gọi API của Prometheus, nên không cần port-forward (hay đứt, và không cân bằng
    tải) hay mở Prometheus ra ngoài.
Mục đích: Gom mọi lời gọi `kubectl` vào một chỗ: luôn có timeout (cluster quá tải thì `kubectl` có thể treo,
    như sự cố hết RAM ngày 06/11), luôn trả lỗi rõ ràng kèm lệnh đã chạy. Kubeconfig lấy từ biến môi
    trường KUBECONFIG như `kubectl` bình thường; `context` chọn cluster nếu file có nhiều cluster.
"""

from __future__ import annotations

import json
import subprocess
import urllib.parse
from dataclasses import dataclass
from typing import Any


class KubeError(RuntimeError):
    """`kubectl` trả mã lỗi khác 0 hoặc quá thời gian."""


@dataclass
class Kube:
    context: str | None = None  # None = context hiện tại của kubeconfig
    timeout_s: float = 60  # timeout mặc định cho một lệnh kubectl

    def _base(self) -> list[str]:
        return ["kubectl"] + (["--context", self.context] if self.context else [])

    def run(
        self, *args: str, stdin: str | None = None, timeout_s: float | None = None, check: bool = True
    ) -> subprocess.CompletedProcess[str]:
        """Chạy `kubectl <args>`. check=True: mã lỗi khác 0 thì raise KubeError."""
        cmd = self._base() + list(args)
        try:
            proc = subprocess.run(
                cmd, input=stdin, capture_output=True, text=True, timeout=timeout_s or self.timeout_s
            )
        except subprocess.TimeoutExpired as e:
            raise KubeError(f"quá {e.timeout:.0f} s: {' '.join(cmd)}") from e
        if check and proc.returncode != 0:
            raise KubeError(f"{' '.join(cmd)} → {proc.returncode}: {proc.stderr.strip()[:500]}")
        return proc

    def get_json(self, *args: str) -> dict[str, Any]:
        """`kubectl get ... -o json` → dict."""
        return json.loads(self.run("get", *args, "-o", "json").stdout)

    def apply(self, manifest: str) -> None:
        """Áp manifest (YAML hoặc JSON) từ chuỗi, qua stdin."""
        self.run("apply", "-f", "-", stdin=manifest)


@dataclass
class Prometheus:
    """Gọi HTTP API của Prometheus qua API server proxy."""

    kube: Kube
    service: str  # "<namespace>/<service>:<port>", ví dụ "monitoring/kps-prometheus:9090"

    def _path(self, api: str, params: dict[str, str]) -> str:
        ns, svc = self.service.split("/", 1)
        q = urllib.parse.urlencode(params)
        return f"/api/v1/namespaces/{ns}/services/{svc}/proxy/api/v1/{api}?{q}"

    def _get(self, api: str, params: dict[str, str]) -> Any:
        out = self.kube.run("get", "--raw", self._path(api, params)).stdout
        body = json.loads(out)
        if body.get("status") != "success":
            raise KubeError(f"Prometheus {api} lỗi: {body.get('error')}")
        return body["data"]

    def query(self, expr: str, at: float | None = None) -> list[dict[str, Any]]:
        """Truy vấn tức thời (instant query). Trả danh sách series `{metric, value}`."""
        params = {"query": expr}
        if at is not None:
            params["time"] = f"{at:.3f}"
        return self._get("query", params)["result"]

    def scalar(self, expr: str) -> float | None:
        """Giá trị đầu tiên của truy vấn tức thời, None nếu rỗng."""
        res = self.query(expr)
        return float(res[0]["value"][1]) if res else None

    def query_range(self, expr: str, start: float, end: float, step_s: float) -> list[dict[str, Any]]:
        """Truy vấn theo khoảng (range query). Trả danh sách series `{metric, values: [[ts, "v"], …]}`."""
        params = {"query": expr, "start": f"{start:.3f}", "end": f"{end:.3f}", "step": f"{step_s:g}"}
        return self._get("query_range", params)["result"]
