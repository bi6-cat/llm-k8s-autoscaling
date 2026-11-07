"""Chạy máy tạo tải (loadgen) thành một Job trong cluster, rồi lấy kết quả về máy chạy runner.

Khái niệm:
    Job = tài nguyên Kubernetes chạy một pod tới khi xong (khác Deployment chạy mãi).
    ConfigMap = chỗ cất file cấu hình hoặc file nhỏ trong cluster; ở đây chứa mã nguồn loadgen/*.py để pod
    dùng được mà không cần build image riêng (image riêng ghim digest là việc còn lại của TR5).
Mục đích:
    Máy tạo tải phải chạy TRONG cluster và gọi Service: `kubectl port-forward` dồn mọi request vào một pod
    (đo ngày 04/11), và độ trễ mạng từ ngoài vào làm sai TTFT (Môi trường §3.6).
    Pod Guaranteed (request = limit, 1 CPU) để không tranh CPU với thứ khác; loadgen tự kiểm throttle.
    Pod ghi kết quả vào /out rồi tạo file DONE và ngủ; runner thấy DONE thì `kubectl cp` thư mục về, rồi
    xoá Job. (Không đọc được file từ pod đã kết thúc, nên pod phải còn sống lúc runner chép.)
"""

from __future__ import annotations

import json
import time
import tomllib
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from experiments.runner.kube import Kube, KubeError
from experiments.runner.matrix import Target

# python:3.12-slim, bản index đa kiến trúc, kéo ngày 06/11/2026 (Python 3.12.16, có sẵn tar cho kubectl cp).
LOADGEN_IMAGE = "python@sha256:4840d514c583a4d3d8cad3940e68dee6f0f6f3635c12fcd0a3d74c21a5b93a54"
CODE_CONFIGMAP = "loadgen-code"


def pinned_requirements(lock_path: Path, root: str = "loadgen") -> list[str]:
    """Danh sách `tên==phiên bản` mà gói `root` cần lúc chạy, đọc từ uv.lock. Hàm thuần, có unit test.

    Đi theo `dependencies` (không theo nhóm dev) từ gói gốc. Lấy cả phụ thuộc có marker (ví dụ
    typing-extensions chỉ cần khi Python < 3.15): cài thừa vô hại, thiếu thì loadgen không chạy.
    """
    lock = tomllib.loads(lock_path.read_text(encoding="utf-8"))
    pkgs = {p["name"]: p for p in lock["package"]}
    seen: dict[str, str] = {}
    stack = [d["name"] for d in pkgs[root].get("dependencies", [])]
    while stack:
        name = stack.pop()
        if name in seen:
            continue
        p = pkgs[name]
        seen[name] = p["version"]
        stack.extend(d["name"] for d in p.get("dependencies", []))
    return [f"{n}=={v}" for n, v in sorted(seen.items())]


def loadgen_args(
    scenario: str,
    *,
    capacity: float | None,
    rate: float | None,
    duration: float | None,
    kb3_replicas: int,
    run_index: int,
    url: str,
    model: str,
    out: str,
) -> list[str]:
    """Tham số dòng lệnh của `python -m loadgen` cho một pha. Hàm thuần."""
    args = [
        "--scenario",
        scenario,
        "--run-index",
        str(run_index),
        "--url",
        url,
        "--model",
        model,
        "--out",
        out,
    ]
    if scenario == "CONST":
        args += ["--rate", f"{rate:g}", "--duration", f"{duration:g}"]
    else:
        args += ["--capacity", f"{capacity:g}"]
        if scenario == "KB3":
            args += ["--replicas", str(kb3_replicas)]
    return args


def job_manifest(
    name: str,
    target: Target,
    run_id: str,
    phase: str,
    args: list[str],
    requirements: list[str],
    deadline_s: int,
) -> dict[str, Any]:
    """Manifest Job cho một pha (warmup hoặc main). Hàm thuần."""
    # Lệnh shell trong pod: cài đúng phiên bản thư viện, chép mã nguồn từ ConfigMap thành gói loadgen,
    # chạy, ghi mã thoát vào /out/rc, tạo DONE rồi ngủ chờ runner chép kết quả và xoá Job.
    script = "\n".join(
        [
            "set -u",
            f"pip install --no-cache-dir --quiet --disable-pip-version-check {' '.join(requirements)}",
            "mkdir -p /app/loadgen && cp /code/*.py /app/loadgen/ && cd /app",
            "rc=0",
            f"python -m loadgen {' '.join(args)} > /out/{phase}.log 2>&1 || rc=$?",
            "echo $rc > /out/rc",
            "touch /out/DONE",
            "sleep 86400",
        ]
    )
    env: list[dict[str, Any]] = []
    if target.api_key_secret:
        # optional: true → Secret không có thì pod vẫn chạy (server không cần key, ví dụ simulator)
        env.append(
            {
                "name": "LOADGEN_API_KEY",
                "valueFrom": {
                    "secretKeyRef": {"name": target.api_key_secret, "key": "key", "optional": True}
                },
            }
        )
    labels = {"app": "loadgen", "experiment/run": run_id, "experiment/phase": phase}
    return {
        "apiVersion": "batch/v1",
        "kind": "Job",
        "metadata": {"name": name, "namespace": target.namespace, "labels": labels},
        "spec": {
            "backoffLimit": 0,  # lỗi thì không chạy lại: runner tự quyết lượt hỏng
            "activeDeadlineSeconds": deadline_s,  # chặn trên: Job tự dừng nếu runner chết giữa chừng
            "ttlSecondsAfterFinished": 3600,  # Job xong tự dọn sau 1 giờ nếu runner không xoá được
            "template": {
                "metadata": {"labels": labels},
                "spec": {
                    "restartPolicy": "Never",
                    "enableServiceLinks": False,  # như vLLM: tránh biến môi trường thừa từ Service
                    "containers": [
                        {
                            "name": "loadgen",
                            "image": LOADGEN_IMAGE,
                            "command": ["/bin/bash", "-c", script],
                            "env": env,
                            # request = limit → QoS Guaranteed: có CPU riêng, không bị pod khác chen
                            "resources": {
                                "requests": {"cpu": target.loadgen_cpu, "memory": "512Mi"},
                                "limits": {"cpu": target.loadgen_cpu, "memory": "512Mi"},
                            },
                            "volumeMounts": [
                                {"name": "code", "mountPath": "/code"},
                                {"name": "out", "mountPath": "/out"},
                            ],
                        }
                    ],
                    "volumes": [
                        {"name": "code", "configMap": {"name": CODE_CONFIGMAP}},
                        {"name": "out", "emptyDir": {}},
                    ],
                },
            },
        },
    }


@dataclass
class LoadJob:
    kube: Kube
    target: Target
    repo_root: Path

    def sync_code(self) -> None:
        """Tạo hoặc cập nhật ConfigMap chứa loadgen/*.py (bỏ tests)."""
        files = sorted((self.repo_root / "loadgen").glob("*.py"))
        cm = {
            "apiVersion": "v1",
            "kind": "ConfigMap",
            "metadata": {"name": CODE_CONFIGMAP, "namespace": self.target.namespace},
            "data": {f.name: f.read_text(encoding="utf-8") for f in files},
        }
        self.kube.apply(json.dumps(cm))

    def run(
        self, run_id: str, phase: str, args: list[str], expected_s: float, out_dir: Path
    ) -> dict[str, Any]:
        """Chạy một pha tới khi xong, chép /out về out_dir. Trả {rc, pod, started, finished}."""
        name = f"loadgen-{run_id.lower()}-{phase}"
        ns = self.target.namespace
        reqs = pinned_requirements(self.repo_root / "loadgen" / "uv.lock")
        deadline = int(expected_s + 1800)
        manifest = job_manifest(name, self.target, run_id, phase, args, reqs, deadline)
        self.kube.run("delete", "job", name, "-n", ns, "--ignore-not-found", "--wait=true", timeout_s=120)
        self.kube.apply(json.dumps(manifest))
        started = time.time()

        pod = self._wait_pod(name, timeout_s=600)
        # Chờ DONE: thời lượng kịch bản + 10 phút dư (cài thư viện, request cuối chạy tới timeout 120 s).
        limit = started + expected_s + 600
        while True:
            phase_now = self.kube.run(
                "get", "pod", pod, "-n", ns, "-o", "jsonpath={.status.phase}", check=False
            ).stdout
            if phase_now == "Failed":
                raise RuntimeError(f"pod {pod} thất bại trước khi xong (xem `kubectl logs -n {ns} {pod}`)")
            done = self.kube.run("exec", pod, "-n", ns, "--", "test", "-f", "/out/DONE", check=False)
            if done.returncode == 0:
                break
            if time.time() > limit:
                raise RuntimeError(f"máy tạo tải pha {phase} quá {limit - started:.0f} s chưa xong")
            time.sleep(10)
        finished = time.time()

        # `kubectl cp` cần tar trong container (python:slim có sẵn). out_dir CHƯA được tồn tại: khi đó
        # kubectl chép NỘI DUNG /out vào out_dir; nếu đã tồn tại thì nó tạo thêm out_dir/out.
        out_dir.parent.mkdir(parents=True, exist_ok=True)
        self.kube.run("cp", f"{ns}/{pod}:/out", str(out_dir), timeout_s=300)
        rc = int((out_dir / "rc").read_text().strip() or "1")
        self.kube.run("delete", "job", name, "-n", ns, "--wait=false", check=False)
        return {"rc": rc, "pod": pod, "started": started, "finished": finished}

    def _wait_pod(self, job: str, timeout_s: float) -> str:
        """Chờ pod của Job chạy (Running). Lâu nhất là lần đầu kéo image python và cài thư viện."""
        ns = self.target.namespace
        end = time.time() + timeout_s
        while time.time() < end:
            try:
                pods = self.kube.get_json("pods", "-n", ns, "-l", f"job-name={job}")["items"]
            except KubeError:
                pods = []
            for p in pods:
                if p["status"].get("phase") in ("Running", "Succeeded", "Failed"):
                    return p["metadata"]["name"]
            time.sleep(5)
        raise RuntimeError(f"pod của Job {job} không chạy sau {timeout_s:.0f} s")
