"""Áp cấu hình scale của một lượt: tĩnh (S1, S4) hoặc ScaledObject của KEDA (A1…A4).

Khái niệm:
    ScaledObject = CRD của KEDA: "scale Deployment X theo metric Y"; KEDA tạo một HPA cho nó.
    Annotation `autoscaling.keda.sh/paused-replicas: "1"` = KEDA giữ Deployment ở đúng 1 replica và tạm
    ngừng scale. Runner pause trong lúc reset và warm-up, rồi bỏ annotation đúng lúc bắt đầu kịch bản
    (Môi trường §14.1), để mọi lượt autoscaling bắt đầu từ cùng một trạng thái.
Mục đích:
    - static: xoá mọi ScaledObject (kéo theo HPA của KEDA), đặt `replicas` của Deployment bằng tay.
    - scaledobject: xoá ScaledObject khác, áp file của cấu hình (đã ghi đè threshold, max replica),
      kèm annotation pause.
    Nếu Argo CD đang tự sync Application `autoscaling` thì dừng ngay: Argo CD sẽ áp lại A2 chính thức
    giữa lượt và làm hỏng cấu hình đang đo (Kiến trúc §18.2).
"""

from __future__ import annotations

import copy
import json
from pathlib import Path
from typing import Any

import yaml

from experiments.runner.kube import Kube, KubeError
from experiments.runner.matrix import Config, Target

PAUSE_ANNOTATION = "autoscaling.keda.sh/paused-replicas"


def render_scaledobject(doc: dict[str, Any], overrides: dict[str, Any], paused: bool) -> dict[str, Any]:
    """Trả bản sao ScaledObject đã ghi đè. Hàm thuần (không gọi cluster), có unit test.

    overrides:
        threshold     → spec.triggers[0].metadata.threshold (chuỗi, KEDA đòi kiểu string)
        max_replicas  → spec.maxReplicaCount và spec.fallback.replicas (fallback = lên max, Kiến trúc §13)
        min_replicas  → spec.minReplicaCount
    """
    so = copy.deepcopy(doc)
    if so.get("kind") != "ScaledObject":
        raise ValueError(f"file cấu hình phải là ScaledObject, gặp kind={so.get('kind')}")
    spec = so["spec"]
    if "threshold" in overrides:
        spec["triggers"][0]["metadata"]["threshold"] = str(overrides["threshold"])
    if "max_replicas" in overrides:
        spec["maxReplicaCount"] = int(overrides["max_replicas"])
        if "fallback" in spec:
            spec["fallback"]["replicas"] = int(overrides["max_replicas"])
    if "min_replicas" in overrides:
        spec["minReplicaCount"] = int(overrides["min_replicas"])
    ann = so.setdefault("metadata", {}).setdefault("annotations", {})
    if paused:
        ann[PAUSE_ANNOTATION] = "1"
    else:
        ann.pop(PAUSE_ANNOTATION, None)
    return so


def guard_argocd(kube: Kube) -> None:
    """Dừng nếu Argo CD đang tự sync Application `autoscaling` (sẽ ghi đè cấu hình đánh giá)."""
    proc = kube.run("get", "application", "autoscaling", "-n", "argocd", "-o", "json", check=False)
    if proc.returncode != 0:
        return  # không có Argo CD hoặc không có app autoscaling: an toàn
    app = json.loads(proc.stdout)
    if app.get("spec", {}).get("syncPolicy", {}).get("automated"):
        raise RuntimeError(
            "Application argocd/autoscaling đang bật auto-sync: Argo CD sẽ áp lại A2 chính thức giữa lượt. "
            "Tắt auto-sync trước phiên đánh giá (Môi trường §14.1) rồi chạy lại runner."
        )


def scaledobject_names(kube: Kube, ns: str) -> list[str]:
    out = kube.run("get", "scaledobject", "-n", ns, "-o", "name", check=False)
    # `-o name` in "scaledobject.keda.sh/<tên>"; lệnh lỗi khi chưa cài KEDA (không có CRD) → coi như rỗng
    if out.returncode != 0:
        return []
    return [line.split("/", 1)[1] for line in out.stdout.split() if "/" in line]


def apply_config(kube: Kube, target: Target, config: Config, repo_root: Path) -> str | None:
    """Áp cấu hình ở trạng thái "đầu lượt". Trả tên ScaledObject đã áp (None với cấu hình tĩnh)."""
    ns = target.namespace
    guard_argocd(kube)
    if config.type == "static":
        for name in scaledobject_names(kube, ns):
            kube.run("delete", "scaledobject", name, "-n", ns, "--wait=true", timeout_s=120)
        # Xoá ScaledObject thì KEDA xoá HPA của nó; sau đó mới đặt replicas, nếu không HPA đặt lại ngay.
        kube.run("scale", f"deployment/{target.deployment}", "-n", ns, f"--replicas={config.replicas}")
        return None

    assert config.file is not None
    doc = yaml.safe_load((repo_root / config.file).read_text(encoding="utf-8"))
    so = render_scaledobject(doc, config.overrides, paused=True)
    name = so["metadata"]["name"]
    so["metadata"]["namespace"] = ns
    for other in scaledobject_names(kube, ns):
        if other != name:
            kube.run("delete", "scaledobject", other, "-n", ns, "--wait=true", timeout_s=120)
    kube.apply(yaml.safe_dump(so, sort_keys=False))
    return name


def set_paused(kube: Kube, ns: str, scaledobject: str, paused: bool) -> None:
    """Bật/tắt pause. `<key>-` trong `kubectl annotate` nghĩa là xoá annotation đó."""
    arg = f"{PAUSE_ANNOTATION}=1" if paused else f"{PAUSE_ANNOTATION}-"
    try:
        kube.run("annotate", "scaledobject", scaledobject, "-n", ns, arg, "--overwrite")
    except KubeError as e:
        action = "pause" if paused else "unpause"
        raise RuntimeError(f"không {action} được ScaledObject {scaledobject}: {e}") from e
