"""Model và image tải sẵn trên VM thuê phải trùng cái pod vLLM sẽ dùng.

Khái niệm: Cold start mức L2 = model và image đã có trên ổ. Ansible tải theo group_vars/cloud.yaml, còn pod
    đọc theo overlay serving: hai nơi khai báo độc lập nên có thể lệch.
Mục đích: Lệch revision hoặc digest thì pod tải lại giữa lúc đo, làm sai số cold start mà không báo lỗi.
"""

from __future__ import annotations

from pathlib import Path

import yaml

REPO = Path(__file__).resolve().parents[2]


def _vars() -> dict:
    path = REPO / "infra" / "ansible" / "inventory" / "group_vars" / "cloud.yaml"
    return yaml.safe_load(path.read_text(encoding="utf-8"))


def test_model_matches_cloud_3b_overlay():
    patch = (REPO / "serving" / "overlays" / "cloud-3b" / "patch-vllm.yaml").read_text(encoding="utf-8")
    ops = [op for op in yaml.safe_load(patch) if op["op"] == "replace"]
    values = [op["value"] for op in ops if isinstance(op["value"], str)]
    v = _vars()
    assert f"--model={v['cloud_model_repo']}" in values
    assert f"--revision={v['cloud_model_revision']}" in values


def test_image_matches_serving_digest():
    kust = yaml.safe_load((REPO / "serving" / "base" / "kustomization.yaml").read_text(encoding="utf-8"))
    image = next(i for i in kust["images"] if i["name"] == "vllm/vllm-openai")
    assert _vars()["cloud_vllm_image"] == f"docker.io/vllm/vllm-openai@{image['digest']}"
