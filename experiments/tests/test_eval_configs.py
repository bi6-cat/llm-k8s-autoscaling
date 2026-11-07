"""Kiểm các file cấu hình đánh giá autoscaling/eval/<ID>.yaml theo hợp đồng với runner (Kế hoạch §6).

Khái niệm:
    Runner đọc từng file eval như một ScaledObject đơn rồi ghi đè threshold, max replica
    (experiments/runner/configs.py). Hợp đồng: tên `vllm-<id>` (runner nhận ScaledObject theo tên), trigger
    đầu tiên có `metadata.threshold`. Nhãn `experiment/config: <ID>` là quy ước để người vận hành thấy
    cấu hình đang áp (`kubectl get scaledobject -L experiment/config`); runner không đọc nhãn này.
Mục đích:
    - So sánh công bằng: A1, A3, A4 chỉ được khác A2 chính thức ở tín hiệu (`query`, `threshold`). Mọi
      trường khác (min/max, fallback, behavior, timeout trigger) phải giống hệt, nên sửa A2 mà quên eval
      thì test này đỏ (Kiến trúc §13.3).
    - CI chỉ kiểm schema những file có trong kustomization.yaml của thư mục, nên mọi file phải có tên ở đó.
"""

from __future__ import annotations

import copy
from pathlib import Path
from typing import Any

import pytest
import yaml

from experiments.runner import configs

REPO = Path(__file__).resolve().parents[2]
EVAL_DIR = REPO / "autoscaling" / "eval"
A2_FILE = REPO / "autoscaling" / "official" / "base" / "scaledobject-a2.yaml"
EVAL_FILES = sorted(EVAL_DIR.glob("A*.yaml"))


def _load(path: Path) -> dict[str, Any]:
    return yaml.safe_load(path.read_text(encoding="utf-8"))


def _without_signal(doc: dict[str, Any]) -> dict[str, Any]:
    """Bỏ phần được phép khác nhau giữa các cấu hình: tên, nhãn, `query` và `threshold` của trigger."""
    d = copy.deepcopy(doc)
    d["metadata"].pop("name")
    d["metadata"].pop("labels")
    for trigger in d["spec"]["triggers"]:
        trigger["metadata"].pop("query")
        trigger["metadata"].pop("threshold")
    return d


def test_eval_dir_has_a1():
    # A1 là cấu hình Must của ma trận ĐG2 (Thông số §8.2); A3, A4 là Could. Test này cũng chặn trường hợp
    # glob không thấy file nào, khi đó hai test parametrize bên dưới bị bỏ qua thay vì đỏ.
    assert "A1" in {p.stem for p in EVAL_FILES}


@pytest.mark.parametrize("path", EVAL_FILES, ids=lambda p: p.stem)
def test_eval_config_follows_runner_contract(path: Path):
    doc = _load(path)
    cid = path.stem
    assert doc["kind"] == "ScaledObject"
    assert doc["metadata"]["name"] == f"vllm-{cid.lower()}"
    assert doc["metadata"]["labels"] == {"experiment/config": cid}
    # Runner ghi đè threshold và max replica như với A2 ở kind (matrix-sim.yaml)
    so = configs.render_scaledobject(doc, {"threshold": 10, "max_replicas": 3}, paused=True)
    assert so["spec"]["triggers"][0]["metadata"]["threshold"] == "10"
    assert so["spec"]["maxReplicaCount"] == 3 and so["spec"]["fallback"]["replicas"] == 3


@pytest.mark.parametrize("path", EVAL_FILES, ids=lambda p: p.stem)
def test_eval_config_differs_from_a2_only_in_signal(path: Path):
    a2 = _load(A2_FILE)
    doc = _load(path)
    assert len(doc["spec"]["triggers"]) == len(a2["spec"]["triggers"]) == 1
    assert doc["spec"]["triggers"][0]["metadata"]["query"] != a2["spec"]["triggers"][0]["metadata"]["query"]
    assert _without_signal(doc) == _without_signal(a2)


def test_eval_kustomization_lists_every_file():
    kust = _load(EVAL_DIR / "kustomization.yaml")
    assert sorted(kust["resources"]) == [p.name for p in EVAL_FILES]
