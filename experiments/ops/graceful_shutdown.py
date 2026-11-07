"""Test graceful shutdown của vLLM trên k8s: xoá pod giữa lúc đang có nhiều stream, đếm stream bị cắt.

Khái niệm: Graceful shutdown = khi pod bị tắt (scale-down, rolling update, drain node), các request đang
    chạy dở được chạy xong thay vì bị cắt. Trình tự khi xoá pod (Kiến trúc §8.2, Hình 13):
      1. Pod bị gỡ khỏi Service (không nhận request mới), đồng thời kubelet chạy preStop `sleep 20`.
      2. Hết preStop, kubelet gửi SIGTERM. vLLM với `--shutdown-timeout=150` chuyển sang "drain": không
         nhận request mới, chạy nốt request đang có (tối đa 150 s) rồi thoát.
      3. Quá `terminationGracePeriodSeconds` (180 s, tính từ bước 1) mà chưa thoát thì bị SIGKILL.
    Ca đối chứng: Deployment riêng `vllm-gs-control`, sinh từ overlay home nhưng BỎ preStop và đặt
    `--shutdown-timeout=0` → SIGTERM đến ngay, vLLM huỷ mọi request ("abort").
Mục đích: Kiểm chứng N4 ở nhà (Kiến trúc §8.3, mốc M2): cấu hình chính → 0 stream bị cắt trong 3 lần thử;
    ca đối chứng → có stream bị cắt, chứng minh 0 lỗi là nhờ cấu hình.
    Chọn 48 stream × ~1900 token (thay vì "khoảng 30" của §8.3): ở nhà model 0,5B sinh ~5 ms/token và chỉ
    16 request chạy cùng lúc (`--max-num-seqs 16`), mỗi stream ~10 s; 48 stream chạy thành 3 đợt (~30 s),
    nên khi SIGTERM đến ở giây thứ 20 vẫn còn stream đang chạy → bước drain (2) thật sự được thử, không chỉ
    preStop (1).
    Client chạy trên PC (cũng là node k3s), gọi thẳng ClusterIP của Service, nên request đi qua đúng cơ chế
    định tuyến của Service như trong cluster. Không dùng port-forward: port-forward nối thẳng vào một pod,
    bỏ qua Service, nên không thấy bước 1.
    Ca đối chứng dùng Deployment riêng (Argo CD không quản lý) nên không phải tắt auto-sync của `serving`.

Chạy (KUBECONFIG trỏ cluster nhà; tự scale vLLM lên rồi về 0 khi xong):
    uv run --project experiments python -m experiments.ops.graceful_shutdown --trials 3 --control-trials 1
Kết quả: runs/graceful-<thời điểm>/ (gitignore): mỗi lần thử một thư mục có streams.json, vllm.log,
    timeline.json; summary.json cho cả phiên.
"""

from __future__ import annotations

import argparse
import base64
import http.client
import json
import subprocess
import threading
import time
from dataclasses import asdict, dataclass, field
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

import yaml

from experiments.runner.kube import Kube

NS = "llm-serving"
MAIN = "vllm"  # Deployment chính, do Argo CD quản lý (replicas không nằm trong Git nên scale tay được)
CONTROL = "vllm-gs-control"  # Deployment đối chứng, script tạo rồi xoá
MODEL = "qwen2.5-0.5b"  # --served-model-name của overlay home
PORT = 8000
# Prompt tiếng Anh ngắn (~25 token): model 1,5B/0,5B hay trả lời tiếng Việt bằng tiếng Trung (nhật ký W1).
# Nội dung không quan trọng vì ignore_eos ép sinh đủ max_tokens.
PROMPT = "Write a very long story about a robot who learns to cook. Describe every step in detail."


# ── Phân loại kết quả một stream (hàm thuần, có unit test) ────────────────────────────────────────────


@dataclass
class StreamResult:
    idx: int
    t_start: float  # epoch giây lúc gửi request
    t_first: float | None = None  # lúc nhận chunk văn bản đầu tiên
    t_end: float | None = None  # lúc kết thúc (nhận [DONE], đứt kết nối hoặc lỗi)
    status: int | None = None  # mã HTTP; None = chưa nhận được header (kết nối lỗi)
    chunks: int = 0  # số chunk có văn bản
    completion_tokens: int | None = None  # từ chunk usage cuối cùng
    done: bool = False  # có nhận "data: [DONE]"
    error: str | None = None


def classify(r: StreamResult, max_tokens: int) -> str:
    """ok: đủ token và có [DONE]. cut: đã nhận 200 (stream đã bắt đầu) nhưng thiếu [DONE] hoặc thiếu token,
    tức người dùng thấy câu trả lời đứt giữa chừng: đây là lỗi N4 cần bằng 0. rejected: không nhận được
    200 (kết nối bị từ chối, 5xx…), request chưa từng được phục vụ."""
    if r.status != 200:
        return "rejected"
    if r.done and r.completion_tokens == max_tokens:
        return "ok"
    return "cut"


# ── Client streaming (chỉ dùng thư viện chuẩn) ────────────────────────────────────────────────────────


def stream_once(host: str, api_key: str, max_tokens: int, r: StreamResult, timeout_s: float) -> None:
    """Gửi một request /v1/completions dạng stream, đọc từng dòng SSE (Server-Sent Events: mỗi sự kiện là
    một dòng `data: <json>`, kết thúc bằng `data: [DONE]`), ghi kết quả vào r."""
    body = json.dumps(
        {
            "model": MODEL,
            "prompt": PROMPT,
            "max_tokens": max_tokens,
            "ignore_eos": True,  # không dừng ở token kết thúc: mọi stream dài đúng max_tokens
            "stream": True,
            "stream_options": {"include_usage": True},  # chunk cuối có số token đã sinh
            "temperature": 0.8,
        }
    )
    conn = http.client.HTTPConnection(host, PORT, timeout=timeout_s)
    try:
        conn.request(
            "POST",
            "/v1/completions",
            body=body,
            headers={"Content-Type": "application/json", "Authorization": f"Bearer {api_key}"},
        )
        resp = conn.getresponse()
        r.status = resp.status
        if resp.status != 200:
            r.error = f"HTTP {resp.status}: {resp.read(300)!r}"
            return
        for raw in resp:  # HTTPResponse đọc được từng dòng; hết dòng = server đóng kết nối
            line = raw.decode("utf-8", "replace").strip()
            if not line.startswith("data:"):
                continue
            data = line[5:].strip()
            if data == "[DONE]":
                r.done = True
                break
            obj = json.loads(data)
            if obj.get("usage"):
                r.completion_tokens = obj["usage"].get("completion_tokens")
            if obj.get("choices") and obj["choices"][0].get("text"):
                r.chunks += 1
                if r.t_first is None:
                    r.t_first = time.time()
    # Đứt kết nối, timeout, JSON hỏng… đều là kết quả cần ghi lại, không phải lỗi của script
    except Exception as e:
        r.error = f"{type(e).__name__}: {e}"
    finally:
        r.t_end = time.time()
        conn.close()


# ── Thao tác trên cluster ─────────────────────────────────────────────────────────────────────────────


def ready_pod(kube: Kube, app: str, exclude: set[str]) -> str | None:
    """Tên một pod Ready, chưa bị xoá, có nhãn app=<app>, không nằm trong exclude."""
    pods = kube.get_json("pods", "-n", NS, "-l", f"app={app}")["items"]
    for p in pods:
        name = p["metadata"]["name"]
        if name in exclude or p["metadata"].get("deletionTimestamp"):
            continue
        conds = {c["type"]: c["status"] for c in p.get("status", {}).get("conditions", [])}
        if conds.get("Ready") == "True":
            return name
    return None


def wait_ready(kube: Kube, app: str, exclude: set[str], timeout_s: float = 900) -> str:
    """Chờ có pod Ready mới (cold start ở nhà ~150–400 s, nên mặc định chờ tối đa 15 phút)."""
    end = time.time() + timeout_s
    while time.time() < end:
        name = ready_pod(kube, app, exclude)
        if name:
            return name
        time.sleep(3)
    raise TimeoutError(f"không có pod app={app} Ready sau {timeout_s:.0f} s")


def wait_gone(kube: Kube, pod: str, timeout_s: float = 300) -> float | None:
    """Chờ pod biến mất hẳn khỏi API server; trả thời điểm (epoch giây), None nếu quá hạn."""
    end = time.time() + timeout_s
    while time.time() < end:
        if kube.run("get", "pod", pod, "-n", NS, check=False).returncode != 0:
            return time.time()
        time.sleep(0.5)
    return None


def control_manifest(kube: Kube, repo: Path, grace_s: int | None = None) -> str:
    """Sinh Deployment + Service đối chứng từ overlay home (luôn khớp cấu hình trong Git), chỉ đổi 3 thứ:
    tên/nhãn, bỏ preStop, --shutdown-timeout=0. safe_load_all đọc từng object trong YAML nhiều tài liệu
    (ngăn bởi `---`) mà kustomize in ra."""
    rendered = kube.run("kustomize", str(repo / "serving/overlays/home")).stdout
    out = []
    for o in yaml.safe_load_all(rendered):
        if not o:
            continue
        if o["kind"] == "Deployment" and o["metadata"]["name"] == MAIN:
            o["metadata"]["name"] = CONTROL
            o["metadata"]["labels"] = {"app": CONTROL}
            o["spec"]["replicas"] = 1
            o["spec"]["selector"]["matchLabels"] = {"app": CONTROL}
            tpl = o["spec"]["template"]
            # Khác nhãn → Service `vllm` không gửi request vào pod đối chứng
            tpl["metadata"]["labels"] = {"app": CONTROL}
            c = tpl["spec"]["containers"][0]
            c.pop("lifecycle", None)  # bỏ preStop
            # grace_s: đặt terminationGracePeriodSeconds ngắn để SIGKILL đến sớm (ca đối chứng 2). Cần vì
            # (06/11) vLLM 0.31.0 không dừng engine khi nhận SIGTERM, nên chỉ bỏ preStop và đặt
            # --shutdown-timeout=0 thì request vẫn chạy xong nhờ pod còn sống tới giây 180.
            if grace_s is not None:
                tpl["spec"]["terminationGracePeriodSeconds"] = grace_s
            c["args"] = [
                "--shutdown-timeout=0" if a.startswith("--shutdown-timeout") else a for a in c["args"]
            ]
            out.append(o)
        elif o["kind"] == "Service" and o["metadata"]["name"] == MAIN:
            o["metadata"]["name"] = CONTROL
            o["metadata"]["labels"] = {"app": CONTROL}
            o["spec"]["selector"] = {"app": CONTROL}
            o["spec"].pop("clusterIP", None)
            o["spec"].pop("clusterIPs", None)
            out.append(o)
    if len(out) != 2:
        raise RuntimeError("overlay home không có đủ Deployment và Service tên vllm")
    return json.dumps({"apiVersion": "v1", "kind": "List", "items": out})


# ── Một lần thử ───────────────────────────────────────────────────────────────────────────────────────


@dataclass
class Trial:
    name: str
    app: str
    pod: str
    streams: int
    max_tokens: int
    t_delete: float = 0.0
    t_gone: float | None = None
    counts: dict[str, int] = field(default_factory=dict)
    in_flight_at_delete: int = 0  # stream đã bắt đầu và chưa xong lúc xoá pod
    finished_after_delete_20s: int = 0  # stream xong SAU thời điểm dự kiến của SIGTERM (xoá + preStop 20 s)
    drain_log: list[str] = field(default_factory=list)  # dòng log vLLM về shutdown


def run_trial(kube: Kube, t: Trial, svc_ip: str, api_key: str, out: Path) -> Trial:
    out.mkdir(parents=True, exist_ok=True)
    # Ghi log pod từ trước khi xoá (sau khi pod mất thì không lấy log được nữa). --timestamps: mỗi dòng có
    # giờ của kubelet, cùng đồng hồ với PC nên so được với giờ của client.
    logf = (out / "vllm.log").open("w")
    logp = subprocess.Popen(
        ["kubectl", "logs", "-f", "--timestamps", "-n", NS, t.pod], stdout=logf, stderr=subprocess.STDOUT
    )
    # Làm nóng: 1 request ngắn để lần gọi đầu (khởi tạo phía server) không lẫn vào phép đo
    stream_once(svc_ip, api_key, 16, StreamResult(-1, time.time()), 60)

    results = [StreamResult(i, 0.0) for i in range(t.streams)]
    threads = []
    for r in results:
        r.t_start = time.time()
        th = threading.Thread(target=stream_once, args=(svc_ip, api_key, t.max_tokens, r, 300), daemon=True)
        th.start()
        threads.append(th)
    # Chờ đợt đầu (16 slot) đã nhận token rồi mới xoá pod, để chắc chắn đang có stream chạy dở
    end = time.time() + 60
    while time.time() < end and sum(r.t_first is not None for r in results) < min(16, t.streams):
        time.sleep(0.2)
    t.t_delete = time.time()
    kube.run("delete", "pod", t.pod, "-n", NS, "--wait=false")
    t.t_gone = wait_gone(kube, t.pod)
    for th in threads:
        th.join(timeout=320)
    logp.terminate()
    logf.close()

    t.counts = {k: 0 for k in ("ok", "cut", "rejected")}
    for r in results:
        t.counts[classify(r, t.max_tokens)] += 1
    t.in_flight_at_delete = sum(1 for r in results if r.t_end and r.t_end > t.t_delete)
    t.finished_after_delete_20s = sum(1 for r in results if r.done and r.t_end and r.t_end > t.t_delete + 20)
    t.drain_log = [
        ln.strip()
        for ln in (out / "vllm.log").read_text(errors="replace").splitlines()
        if any(k in ln.lower() for k in ("shutdown", "drain", "abort", "shutting down", "sigterm"))
    ][:20]
    (out / "streams.json").write_text(json.dumps([asdict(r) for r in results], indent=1))
    (out / "timeline.json").write_text(json.dumps(asdict(t), indent=1))
    return t


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("--trials", type=int, default=3, help="số lần thử với cấu hình chính")
    ap.add_argument("--control-trials", type=int, default=1, help="số lần thử ca đối chứng")
    ap.add_argument("--control-grace", type=int, default=None, help="grace period (s) của ca đối chứng")
    ap.add_argument("--streams", type=int, default=48)
    ap.add_argument("--max-tokens", type=int, default=1900, help="≤ max-model-len 2048 trừ độ dài prompt")
    ap.add_argument("--out", type=Path, default=None)
    a = ap.parse_args()

    repo = Path(__file__).resolve().parents[2]
    out = a.out or repo / "runs" / f"graceful-{datetime.now().strftime('%Y%m%d-%H%M')}"
    kube = Kube(timeout_s=120)
    key_b64 = kube.get_json("secret", "vllm-api-key", "-n", NS)["data"]["key"]
    api_key = base64.b64decode(key_b64).decode()
    trials: list[Trial] = []
    try:
        # Cấu hình chính: Deployment vllm, 1 replica. Mỗi lần xoá pod, Deployment tự tạo pod thay thế
        # (time-slicing ở nhà có 2 GPU replica nên pod mới xếp lịch được ngay); chờ nó Ready rồi thử tiếp.
        if a.trials:
            ip = kube.get_json("svc", MAIN, "-n", NS)["spec"]["clusterIP"]
            kube.run("scale", "deploy", MAIN, "-n", NS, "--replicas=1")
            used: set[str] = set()
            for i in range(1, a.trials + 1):
                pod = wait_ready(kube, MAIN, used)
                used.add(pod)
                print(f"[main {i}] pod {pod} Ready, mở {a.streams} stream", flush=True)
                t = run_trial(
                    kube,
                    Trial(f"main-{i}", MAIN, pod, a.streams, a.max_tokens),
                    ip,
                    api_key,
                    out / f"main-{i}",
                )
                trials.append(t)
                print(
                    f"[main {i}] {t.counts}, đang chạy lúc xoá {t.in_flight_at_delete}, "
                    f"xong sau giây 20: {t.finished_after_delete_20s}",
                    flush=True,
                )
            kube.run("scale", "deploy", MAIN, "-n", NS, "--replicas=0")
            kube.run(
                "wait",
                "--for=delete",
                "pod",
                "-n",
                NS,
                "-l",
                f"app={MAIN}",
                "--timeout=300s",
                check=False,
                # Timeout của Kube phải > --timeout của kubectl. Lưu ý (06/11): vLLM 0.31.0 không tự thoát
                # sau SIGTERM, pod chỉ mất khi bị SIGKILL ở giây 180; mặc định 120 s của Kube cắt ngang.
                timeout_s=320,
            )
        # Ca đối chứng
        if a.control_trials:
            kube.apply(control_manifest(kube, repo, a.control_grace))
            ip = kube.get_json("svc", CONTROL, "-n", NS)["spec"]["clusterIP"]
            used = set()
            for i in range(1, a.control_trials + 1):
                pod = wait_ready(kube, CONTROL, used)
                used.add(pod)
                print(f"[control {i}] pod {pod} Ready, mở {a.streams} stream", flush=True)
                t = run_trial(
                    kube,
                    Trial(f"control-{i}", CONTROL, pod, a.streams, a.max_tokens),
                    ip,
                    api_key,
                    out / f"control-{i}",
                )
                trials.append(t)
                print(f"[control {i}] {t.counts}, đang chạy lúc xoá {t.in_flight_at_delete}", flush=True)
    finally:
        # Luôn dọn: xoá đối chứng, đưa vLLM chính về 0 để trả RAM/GPU cho PC
        kube.run("delete", "deploy,svc", CONTROL, "-n", NS, "--ignore-not-found", check=False)
        kube.run("scale", "deploy", MAIN, "-n", NS, "--replicas=0", check=False)
        out.mkdir(parents=True, exist_ok=True)
        summary: dict[str, Any] = {
            "at": datetime.now(UTC).isoformat(),
            "streams": a.streams,
            "max_tokens": a.max_tokens,
            "trials": [asdict(t) for t in trials],
        }
        (out / "summary.json").write_text(json.dumps(summary, indent=1))
        print(f"Kết quả: {out}")


if __name__ == "__main__":
    main()
