"""Sơ đồ cho các hướng dẫn theo tuần trong docs/huong-dan/ (Hình 18–19).

Được gọi từ build_diagrams.py; dùng chung lớp Svg và bảng màu.
"""
from build_diagrams import (AXIS, BLUE, BLUE_T, CRIT, GOOD, GREEN_T, INK, INK2, MONO, MUTED,
                            ORANGE, ORANGE_T, WHITE, Svg)


# ======================================================================
# Hình 18 — W1: quy trình kiểm tra vLLM trên RTX 5060
# ======================================================================
def fig_w1_vllm():
    W, H = 1240, 470
    s = Svg(W, H, "Sáu bước kiểm tra vLLM trên RTX 5060 trong W1, mỗi bước có lệnh kiểm tra đạt hay không; "
                  "nhánh xử lý khi hỏng và điểm dừng sau 4 giờ")
    s.header("W1 · Kiểm tra vLLM trên RTX 5060",
             "Mỗi bước có một lệnh cho biết đạt hay không; hỏng thì thử theo nhánh bên dưới, tổng thời gian thử ≤ 4 giờ")
    steps = [
        ("Driver", ["nvidia-smi: ≥ 575, bản open", "compute_cap = 12.0"]),
        ("Toolkit", ["docker run --gpus all", "thấy RTX 5060"]),
        ("Image sm_120", ["torch arch list có sm_120", "ghim digest -cu129"]),
        ("Chạy 1,5B", ["log: GPU KV cache size", "ghi VRAM, thời gian"]),
        ("API + metric", ["stream có usage, [DONE]", "bucket TTFT le=\"2.5\""]),
        ("Drain khi tắt", ["--shutdown-timeout 150", "stream chạy hết"]),
    ]
    x0, y0, bw, bh, gap = 32, 96, 178, 104, 21.6
    for i, (title, lines) in enumerate(steps):
        x = x0 + i * (bw + gap)
        s.step_box(x, y0, bw, bh, i + 1, title, lines, BLUE)
        if i < len(steps) - 1:
            s.arrow([(x + bw + 2, y0 + bh / 2), (x + bw + gap - 3, y0 + bh / 2)], INK2, sw=1.6, r=0)

    # nhánh khi hỏng
    fy = 262
    fails = [
        (0, 3, "Hỏng ở bước 1–3", ["nâng driver ≥ 580 (dùng được image CUDA 13)",
                                   "thử image NGC nvcr.io/nvidia/vllm hoặc bản vLLM mới hơn"]),
        (3, 4, "OOM / lỗi compile", ["--gpu-memory-utilization", "0.80; --enforce-eager"]),
        (4, 6, "Đạt", ["ghi digest, revision, KV cache vào nhật ký", "W2 dùng đúng image này trong k3s"]),
    ]
    for a, b, title, lines in fails:
        xa = x0 + a * (bw + gap)
        xb = x0 + b * (bw + gap) - gap
        ok = title == "Đạt"
        fill, stroke = (GREEN_T, GOOD) if ok else (ORANGE_T, ORANGE)
        s.rect(xa, fy, xb - xa, 86, fill=fill, stroke=stroke, sw=1.3, rx=10)
        s.text(xa + 14, fy + 26, title, size=13.5, weight=650)
        for j, ln in enumerate(lines):
            s.text(xa + 14, fy + 50 + j * 18, ln, size=11.5, fill=INK2)
        xm = (xa + xb) / 2 if not ok else x0 + 5 * (bw + gap) + bw / 2
        s.arrow([(xm, y0 + bh + 2), (xm, fy - 3)], stroke if not ok else GOOD, sw=1.5, dash=None if ok else "5 4", r=0)

    # điểm dừng
    s.rect(x0, 372, W - 2 * x0, 70, fill=WHITE, stroke=CRIT, sw=1.4, rx=10)
    s.text(x0 + 16, 400, "Hết 4 giờ vẫn hỏng → điểm dừng", size=13.5, weight=650)
    s.text(x0 + 16, 422, "Ghi biên bản (log, các cách đã thử). Từ W2, laptop RTX 4050 là node GPU chính cho vLLM; "
                         "PC vẫn là k3s server (control plane, Argo CD, Prometheus).", size=12, fill=INK2)
    s.save("18-w1-vllm-5060.svg")


# ======================================================================
# Hình 19 — W2: trạng thái hệ thống ở mốc M1
# ======================================================================
def _items(s, x, y, items, size=12):
    for i, (txt, mono) in enumerate(items):
        s.add(f'<circle cx="{x + 4}" cy="{y + i * 21 - 4}" r="2.6" fill="{MUTED}"/>')
        s.text(x + 14, y + i * 21, txt, size=size, fill=INK, family=MONO if mono else None)


def fig_w2_state():
    W, H = 1240, 640
    s = Svg(W, H, "Trạng thái cuối W2: cluster nhà gồm PC (k3s server) và laptop (k3s agent, máy làm việc, cluster "
                  "simulator); Argo CD kéo cấu hình từ GitHub; VM Vast cho phiên V0; Mac chỉ để xem giao diện")
    s.header("W2 · Trạng thái hệ thống ở mốc M1 (18/10)",
             "Mọi lệnh gõ trên laptop Ubuntu; cluster nhà tự kéo cấu hình từ Git; VM thuê chỉ sống vài giờ")

    # GitHub
    gx, gy, gw, gh = 420, 84, 400, 100
    s.rect(gx, gy, gw, gh, fill=WHITE, stroke=INK2, sw=1.4, rx=12)
    s.rich(gx + 16, gy + 26, [("GitHub", 650, INK), ("  bi6-cat/llm-k8s-autoscaling · main", 400, INK2)], size=13.5)
    s.text(gx + 16, gy + 52, "platform/  serving/  autoscaling/  infra/", size=11.5, family=MONO)
    s.text(gx + 16, gy + 74, "CI: yamllint · kubeconform · ansible --syntax-check", size=11.5, fill=INK2)

    # cluster nhà
    cx, cy, cw, ch = 32, 236, 728, 364
    s.group(cx, cy, cw, ch, "Cluster nhà", "k3s v1.36.5 · cùng LAN")
    # PC
    px, py, pw, ph = 50, 272, 318, 290
    s.rect(px, py, pw, ph, fill=WHITE, stroke=AXIS, rx=10)
    s.text(px + 14, py + 24, "PC · k3s server", size=13.5, weight=650)
    s.text(px + 14, py + 42, "luôn bật · RAM 16 GB", size=11.5, fill=INK2)
    _items(s, px + 16, py + 70, [("Argo CD core · App-of-Apps", False), ("kube-prometheus-stack", False),
                                 ("KEDA (chưa có ScaledObject)", False), ("Traefik (có sẵn trong k3s)", False),
                                 ("device plugin + GPU exporter", False), ("vLLM 1,5B · 1 replica", False)])
    s.gpu_chip(px + 16, py + 210, pw - 32, 34, "RTX 5060 · 8 GB")
    s.text(px + 16, py + 274, "Argo CD đồng bộ 6 app từ Git", size=11.5, fill=INK2)
    # laptop
    lx, ly, lw, lh = 424, 272, 318, 290
    s.rect(lx, ly, lw, lh, fill=WHITE, stroke=BLUE, sw=1.5, rx=10)
    s.text(lx + 14, ly + 24, "Laptop · k3s agent + máy làm việc", size=13.5, weight=650)
    s.text(lx + 14, ly + 42, "Ubuntu · gõ mọi lệnh ở đây", size=11.5, fill=INK2)
    _items(s, lx + 16, ly + 70, [("Ansible · kubectl · helm · vastai", False), ("device plugin + GPU exporter", False),
                                 ("vLLM khi scale lên 2 replica", False)])
    s.rect(lx + 14, ly + 128, lw - 28, 72, fill=BLUE_T, stroke="#c9dcf3", sw=1.2, rx=8, dash="5 4")
    s.text(lx + 26, ly + 150, "kind llm-sim (tách biệt)", size=12.5, weight=650)
    s.text(lx + 26, ly + 170, "Prometheus · KEDA · simulator", size=11.5, fill=INK2)
    s.text(lx + 26, ly + 188, "A2 scale 1 → 3 · bài kiểm thử T1–T5", size=11.5, fill=INK2)
    s.gpu_chip(lx + 16, ly + 210, lw - 32, 34, "RTX 4050 · 6 GB")
    s.text(lx + 16, ly + 274, "Ansible: local trên laptop, SSH tới PC", size=11.5, fill=INK2)
    # SSH laptop → PC
    s.arrow([(lx - 2, ly + 120), (px + pw + 3, ly + 120)], BLUE, sw=1.8, r=0)
    s.text((px + pw + lx) / 2, ly + 112, "SSH", size=11, weight=650, fill=BLUE, anchor="middle")

    # GitHub ↔ cluster
    s.arrow([(gx + 60, gy + gh), (gx + 60, 212), (px + 300, 212), (px + 300, py - 3)], INK2, sw=1.6)
    s.label(gx - 60, 207, "Argo CD kéo cấu hình (pull)", fill=INK)
    s.arrow([(lx + 250, ly - 2), (lx + 250, 222), (gx + gw - 60, 222), (gx + gw - 60, gy + gh + 3)], BLUE, sw=1.6)
    s.label(gx + gw - 48, 214, "git push · PR", fill=BLUE, anchor="start")

    # V0
    vx, vy, vw, vh = 784, 236, 424, 214
    s.group(vx, vy, vw, vh, "V0 · VM Vast", "17–18/10 · 3–4 giờ · ~1–2 USD", fill=ORANGE_T, stroke=ORANGE)
    _items(s, vx + 20, vy + 54, [("k3s single-node (cùng Ansible)", False), ("device plugin (Helm) · vLLM 7B", False),
                                 ("đo: bootstrap, fio, TPOT batch 1/16/32", False)])
    s.gpu_chip(vx + 20, vy + 128, vw - 40, 34, "RTX 4090 · 24 GB")
    s.text(vx + 20, vy + 194, "kubectl qua SSH tunnel 127.0.0.1:16443", size=11.5, fill=INK2, family=MONO)
    s.arrow([(lx + lw + 2, ly + 60), (vx - 3, ly + 60)], ORANGE, sw=1.8, r=0)
    s.text((lx + lw + vx) / 2, ly + 52, "SSH", size=11, weight=650, fill=ORANGE, anchor="middle")

    # Mac
    mx, my, mw, mh = 784, 470, 424, 92
    s.rect(mx, my, mw, mh, fill=WHITE, stroke=MUTED, sw=1.2, rx=10, dash="5 4")
    s.text(mx + 16, my + 26, "Mac (phụ)", size=13.5, weight=650)
    s.text(mx + 16, my + 48, "SSH vào laptop; mở Grafana, Argo CD, Prometheus", size=11.5, fill=INK2)
    s.text(mx + 16, my + 68, "trong trình duyệt qua ssh -L (port-forward)", size=11.5, fill=INK2)
    s.arrow([(mx - 2, my + 46), (lx + lw + 3, my + 46)], MUTED, sw=1.5, dash="5 4", r=0)

    s.text(cx, 624, "Không vẽ: Tailscale (truy cập từ xa vào PC và laptop), Secret tạo tay (grafana-admin, "
                    "vllm-api-key) cho tới khi có Sealed Secrets ở W4.", size=11.5, fill=MUTED)
    s.save("19-w2-trang-thai-m1.svg")


def build_all():
    fig_w1_vllm()
    fig_w2_state()
