"""Sơ đồ bổ sung cho các tài liệu chuyên sâu trong docs/chi-tiet/ (Hình 10–16).

Được gọi từ build_diagrams.py; dùng chung lớp Svg và bảng màu.
"""
import math

from build_diagrams import (AQUA, AXIS, BLUE, BLUE_T, CRIT, GOOD, GRAY_T, GREEN_T, GRID, INK, INK2, MONO,
                            MUTED, ORANGE, ORANGE_T, SURFACE, VIOLET, VIOLET_T, WARN, WHITE, YELLOW, YELLOW_T,
                            Svg, f, smooth, text_width)

AQUA_T = "#e6f6f0"


def _dec(v):
    """Số thập phân kiểu Việt Nam: 2.5 → '2,5'."""
    return f"{v:g}".replace(".", ",")


# ======================================================================
# Hình 10 — Độ trễ theo mức tải (đầu gối của đường cong hàng đợi)
# ======================================================================
def fig_knee():
    W, H = 1100, 450
    s = Svg(W, H, "TTFT theo tốc độ request trên một replica: tăng chậm khi tải thấp, tăng vọt khi gần thông lượng "
                  "tối đa μ; C là tốc độ lớn nhất còn đạt SLO")
    s.header("Vì sao không thể cho GPU chạy sát 100% tải",
             "TTFT p95 theo tốc độ request trên 1 replica — mô hình hàng đợi minh hoạ: T ≈ T₀ + k·ρ/(1 − ρ), với ρ = λ/μ")
    x0, top, pw, ph = 96, 110, 900, 240
    y1 = top + ph
    lmax, ymax, mu, C = 3.0, 8.0, 2.4, 1.99
    X = lambda l: x0 + l / lmax * pw
    Y = lambda v: y1 - v / ymax * ph
    ttft = lambda l: 0.3 + 0.35 * (l / mu) / (1 - l / mu)

    s.rect(X(C), top, X(mu) - X(C), ph, fill=WARN, stroke=None, rx=0, opacity=0.16)
    s.rect(X(mu), top, X(lmax) - X(mu), ph, fill=CRIT, stroke=None, rx=0, opacity=0.12)
    for v in (2, 4, 6, 8):
        s.line(x0, Y(v), x0 + pw, Y(v), stroke=GRID)
    for v in (0, 2, 4, 6, 8):
        s.text(x0 - 10, Y(v) + 4, str(v), size=11, fill=MUTED, anchor="end")
    for l in (0, 0.5, 1.0, 1.5, 2.0, 2.5, 3.0):
        s.text(X(l), y1 + 18, _dec(l), size=11, fill=MUTED, anchor="middle")
    s.text(x0 + pw, y1 + 38, "tốc độ request đến λ (req/s)", size=11.5, fill=INK2, anchor="end")
    s.text(x0, top - 12, "TTFT p95 (s)", size=11.5, fill=INK2)

    pts = []
    l = 0.0
    while l < mu:
        v = ttft(l)
        if v > ymax:
            break
        pts.append((X(l), Y(v)))
        l += 0.005
    s.polyline(pts, BLUE, sw=2.6)
    s.arrow([pts[-1], (pts[-1][0] + 2, top + 2)], BLUE, sw=2.6, r=0)
    s.line(x0, y1, x0 + pw, y1, stroke=AXIS)

    s.line(x0, Y(2), x0 + pw, Y(2), stroke=INK2, sw=1.3, dash="6 4")
    s.label(x0 + 8, Y(2) - 6, "SLO: TTFT p95 ≤ 2 s", anchor="start", fill=INK)
    for lv, lab in ((C, "C ≈ 2,0"), (mu, "μ = 2,4")):
        s.line(X(lv), top, X(lv), y1, stroke=INK, sw=1.2, dash="3 3")
        s.text(X(lv), top - 12, lab, size=12, weight=650, anchor="middle")
    s.text(X(1.0), Y(7.1), "đạt SLO", size=12.5, weight=650, anchor="middle")
    s.text(X(1.0), Y(7.1) + 18, "vùng vận hành an toàn", size=11.5, fill=INK2, anchor="middle")
    s.text((X(C) + X(mu)) / 2, Y(1.25), "vi phạm SLO", size=12, weight=650, anchor="middle")
    s.text((X(C) + X(mu)) / 2, Y(1.25) + 18, "dù vẫn chạy", size=11.5, fill=INK2, anchor="middle")
    s.text((X(mu) + X(lmax)) / 2, Y(7.1), "quá tải", size=12, weight=650, anchor="middle")
    s.text((X(mu) + X(lmax)) / 2, Y(7.1) + 18, "hàng đợi tăng mãi", size=11.5, fill=INK2, anchor="middle")
    s.text(X(0.3), Y(3.9), "đầu gối: thêm một chút tải → độ trễ tăng mạnh", size=12, fill=INK)
    s.arrow([(X(1.45), Y(3.75)), (X(1.78), Y(1.45))], INK2, sw=1.3, r=0)
    s.text(x0, 418, "ρ = 0,5 → TTFT ≈ 0,65 s   ·   ρ = 0,8 → ≈ 1,7 s   ·   ρ = 0,9 → ≈ 3,5 s   "
                    "(tăng ρ từ 0,8 lên 0,9 làm TTFT gấp đôi)", size=12, fill=INK2)
    s.save("10-do-tre-theo-muc-tai.svg")


# ======================================================================
# Hình 11 — Static batching và continuous batching
# ======================================================================
def fig_batching():
    W, H = 1240, 424
    s = Svg(W, H, "So sánh static batching và continuous batching: static để slot trống chờ request dài nhất, "
                  "continuous chèn request mới ngay khi có slot trống")
    s.header("Static batching và continuous batching",
             "Mỗi hàng là một slot trong batch, mỗi cột là một bước decode (sinh 1 token cho mọi request đang chạy) — "
             "đơn giản hoá, bỏ qua prefill")
    x = 32
    x = s.legend_swatch(x, 92, "request đang sinh token", BLUE_T, stroke=BLUE)
    s.legend_swatch(x, 92, "slot trống (GPU làm ít việc hơn khả năng)", s.hatch(), stroke=MUTED)
    step = 38
    panels = [
        ("Static batching", 100, [
            [(0, 10, "R1"), (10, 12, "R5 …")],
            [(0, 3, "R2"), (3, 10, None), (10, 12, "R6 …")],
            [(0, 6, "R3"), (6, 10, None), (10, 12, "R7 …")],
            [(0, 8, "R4"), (8, 10, None), (10, 12, "R8 …")]],
         ["• Batch chỉ kết thúc khi request dài nhất (R1) xong",
          "• R5–R8 phải chờ tới bước 10 mới được chạy",
          "Hoàn thành trong 12 bước: 4 request"]),
        ("Continuous batching (cách vLLM làm)", 700, [
            [(0, 10, "R1"), (10, 12, "R9 …")],
            [(0, 3, "R2"), (3, 8, "R5"), (8, 12, "R7")],
            [(0, 6, "R3"), (6, 10, "R6"), (10, 12, "R10 …")],
            [(0, 8, "R4"), (8, 12, "R8 …")]],
         ["• Request mới được chèn vào ngay khi một slot trống",
          "• Slot luôn có việc → thông lượng cao hơn",
          "Hoàn thành trong 12 bước: 7 request"]),
    ]
    for title, x0, rows, notes in panels:
        s.text(x0, 124, title, size=14, weight=700)
        for t in range(13):
            s.line(x0 + t * step, 136, x0 + t * step, 312, stroke=GRID)
        for i, row in enumerate(rows):
            y = 140 + i * 44
            s.text(x0 - 10, y + 22, f"slot {i + 1}", size=11.5, fill=INK2, anchor="end")
            for a, b, lab in row:
                bx, bw = x0 + a * step + 1.5, (b - a) * step - 3
                if lab is None:
                    s.rect(bx, y, bw, 34, fill=s.hatch(), stroke=MUTED, sw=1, dash="3 3", rx=5)
                else:
                    s.rect(bx, y, bw, 34, fill=BLUE_T, stroke=BLUE, sw=1.2, rx=5)
                    s.text(bx + bw / 2, y + 21.5, lab, size=12, weight=650, anchor="middle")
        for t in (0, 3, 6, 9, 12):
            s.text(x0 + t * step, 332, str(t), size=11, fill=MUTED, anchor="middle")
        s.text(x0 + 12 * step, 348, "bước decode", size=11, fill=MUTED, anchor="end")
        for j, ln in enumerate(notes):
            last = j == len(notes) - 1
            s.text(x0, 372 + j * 20, ln, size=12.5 if last else 12, weight=700 if last else 400,
                   fill=INK if last else INK2)
    s.save("11-batching.svg")


# ======================================================================
# Hình 12 — Tám pha cold start
# ======================================================================
def fig_coldstart_detail():
    W, H = 1240, 528
    s = Svg(W, H, "Tám pha khởi động một pod vLLM: scheduling, chuẩn bị pod, pull image, khởi động tiến trình, "
                  "tải model, nạp weights, compile và CUDA graph, probe; pod giữ GPU suốt quá trình")
    s.header("Tám pha khởi động (cold start) một pod vLLM",
             "Ước lượng cho model 7–8B ở mức L0 (chưa tối ưu); nhãn dưới mỗi pha cho biết pha đó có tránh được không")
    cats = {"skip": ("bỏ qua được", AQUA, AQUA_T), "short": ("rút ngắn được", "#c98500", YELLOW_T),
            "none": ("không tránh được", MUTED, GRAY_T)}
    x = 32
    for key in ("skip", "short", "none"):
        name, c, t = cats[key]
        x += s.status_pill(x, 80, name, c, t) + 16
    phases = [
        ("Scheduling", "≈ 1–2 s", ["chọn node còn GPU trống;", "GPU bị giữ từ thời điểm này"], "none", None),
        ("Chuẩn bị pod", "≈ 2–5 s", ["cấp IP, mount volume,", "device plugin gán GPU cụ thể"], "none", None),
        ("Pull image", "≈ 60–180 s", ["tải và giải nén image", "vLLM cỡ ~10 GB"], "skip", "nhờ pre-pull image"),
        ("Khởi động tiến trình", "≈ 5–15 s", ["import torch, vllm;", "khởi tạo CUDA context"], "none", None),
        ("Tải model", "≈ 150 s", ["tải ~15 GB safetensors", "từ Hugging Face"], "skip", "nhờ model cache"),
        ("Nạp weights → GPU", "≈ 10–60 s", ["đĩa → RAM → VRAM;", "NVMe nhanh, ổ mạng chậm"], "short", "nhờ NVMe cục bộ"),
        ("Compile · KV · graph", "≈ 20–60 s", ["torch.compile, đo bộ nhớ,", "cấp KV-cache, capture graph"],
         "short", "nhờ compile cache"),
        ("Probe → Ready", "≈ 5–10 s", ["mở cổng 8000, probe OK,", "pod vào Endpoints"], "none", None),
    ]
    bw, bh, gap = 274, 138, 24
    pos = []
    for i, (title, dur, lines, cat, how) in enumerate(phases):
        row, col = divmod(i, 4)
        x, y = 32 + col * (bw + gap), 110 + row * 196
        pos.append((x, y))
        name, c, t = cats[cat]
        s.rect(x, y, bw, bh, fill=WHITE, stroke=AXIS, rx=10)
        s.add(f'<circle cx="{f(x + 24)}" cy="{f(y + 25)}" r="12" fill="{INK2}"/>')
        s.text(x + 24, y + 29.5, str(i + 1), size=12.5, weight=700, fill=WHITE, anchor="middle")
        s.text(x + 44, y + 30, title, size=13.5, weight=650)
        s.text(x + 16, y + 58, dur, size=13, weight=700)
        for j, ln in enumerate(lines):
            s.text(x + 16, y + 78 + j * 17, ln, size=11.5, fill=INK2)
        s.status_pill(x + 16, y + 108, name + (f" {how}" if how else ""), c, t)
    for i in (0, 1, 2, 4, 5, 6):
        x, y = pos[i]
        s.arrow([(x + bw, y + bh / 2), (x + bw + gap, y + bh / 2)], INK2, sw=1.8)
    x3, y3 = pos[3]
    x4, y4 = pos[4]
    s.arrow([(x3 + bw / 2, y3 + bh), (x3 + bw / 2, y3 + bh + 29), (x4 + bw / 2, y3 + bh + 29), (x4 + bw / 2, y4)],
            INK2, sw=1.8)
    yb = pos[7][1] + bh + 24
    s.line(32, yb, 1200, yb, stroke=INK, sw=1.3)
    s.line(32, yb - 6, 32, yb + 6, stroke=INK, sw=1.3)
    s.line(1200, yb - 6, 1200, yb + 6, stroke=INK, sw=1.3)
    s.label(616, yb + 4, "từ pha 1: pod đã giữ GPU (tính vào GPU-giờ) nhưng chưa phục vụ request nào",
            fill=INK, size=12, weight=600)
    s.rich(32, yb + 42, [("Tổng (ước lượng): ", 650, INK), ("L0 ≈ 4–8 phút · L1 ≈ 2,5–7 phút · L2 ≈ 0,5–1,5 phút", 400, INK2),
                         ("  — sẽ được thay bằng số đo thực tế", 400, MUTED)], size=12.5)
    s.save("12-cold-start-chi-tiet.svg")


# ======================================================================
# Hình 13 — Graceful shutdown khi scale-down
# ======================================================================
def fig_shutdown():
    W, H = 1240, 528
    s = Svg(W, H, "Scale-down an toàn: khi không có preStop, request đến trong lúc Endpoints chưa cập nhật bị từ chối; "
                  "có preStop sleep 20 giây thì request đó vẫn được phục vụ")
    s.header("Scale-down an toàn: vì sao cần preStop",
             "Khi pod bị xoá, việc gỡ pod khỏi Endpoints và việc gửi SIGTERM chạy song song — "
             "thiếu preStop, request đến muộn sẽ lỗi")
    X = lambda t: 250 + (t + 10) * 15
    s.line(X(0), 96, X(0), 424, stroke=INK2, sw=1.2, dash="4 4")
    s.text(X(0) + 6, 92, "t = 0: HPA giảm replicas, pod chuyển sang Terminating", size=11.5, weight=600)

    def bar(t0, t1, y, h, label, fill, stroke, weight=400):
        s.rect(X(t0), y, X(t1) - X(t0), h, fill=fill, stroke=stroke, sw=1, rx=5)
        if label:
            s.text((X(t0) + X(t1)) / 2, y + h / 2 + 4, label, size=11, weight=weight, anchor="middle")

    def tag(t, y, label):
        w = text_width(label, 10.5, 700) + 12
        s.rect(X(t) - w / 2, y - 9, w, 17, fill=INK, stroke=None, rx=4)
        s.text(X(t), y + 3.5, label, size=10.5, weight=700, fill=WHITE, anchor="middle")

    def exit_mark(t, y):
        s.add(f'<circle cx="{f(X(t))}" cy="{f(y)}" r="5" fill="{INK}"/>')
        s.text(X(t) + 9, y + 4, "thoát", size=11, fill=INK)

    for k, (title, top, prestop) in enumerate((("Không có preStop", 112, False),
                                               ("Có preStop: sleep 20 s", 284, True))):
        s.text(32, top, title, size=14, weight=700)
        le, lv, lr = top + 12, top + 50, top + 88
        for y, name, h in ((le, "Endpoints", 30), (lv, "Tiến trình vLLM", 30), (lr, "Request", 44)):
            s.text(40, y + h / 2 + 4, name, size=12, fill=INK2)
        bar(-10, 0, le, 30, "trong Endpoints", BLUE_T, "#c9dcf3")
        bar(0, 4, le, 30, "đang gỡ", YELLOW_T, "#c98500")
        bar(4, 50, le, 30, "đã gỡ khỏi Endpoints: không nhận request mới", GRAY_T, AXIS)
        t_term, t_exit = (20, 34) if prestop else (0, 22)
        bar(-10, t_term, lv, 30, "vẫn phục vụ (preStop đang sleep)" if prestop else "phục vụ", BLUE_T, "#c9dcf3")
        bar(t_term, t_exit, lv, 30, "drain: làm nốt request đang chạy" if not prestop else "drain",
            ORANGE_T, ORANGE)
        tag(t_term, lv, "SIGTERM")
        exit_mark(t_exit, lv + 15)
        s.text(X(-8) - 6, lr + 14, "R_a", size=11, weight=650, anchor="end")
        bar(-8, 18, lr + 6, 10, None, BLUE, None)
        s.status_pill(X(18) + 6, lr + 2, "xong", GOOD, GREEN_T)
        s.text(X(2) - (6 if prestop else 12), lr + 36, "R_b", size=11, weight=650, anchor="end")
        if prestop:
            bar(2, 30, lr + 28, 10, None, BLUE, None)
            s.status_pill(X(30) + 6, lr + 24, "đến lúc 2 s — vẫn được phục vụ, xong", GOOD, GREEN_T)
        else:
            s.add(f'<circle cx="{f(X(2))}" cy="{f(lr + 33)}" r="6" fill="{CRIT}"/>')
            s.status_pill(X(2) + 12, lr + 24, "đến lúc 2 s — pod đã ngừng nhận: lỗi", CRIT, "#fbe9e8")
    ya = 432
    s.line(X(-10), ya, X(50), ya, stroke=AXIS)
    for t in range(-10, 51, 10):
        s.line(X(t), ya, X(t), ya + 5, stroke=AXIS)
        s.text(X(t), ya + 19, f"{t} s", size=11, fill=MUTED, anchor="middle")
    s.text(32, 482, "• preStop giữ tiến trình chạy đến khi kube-proxy và Ingress đều đã ngừng gửi request mới tới pod.",
           size=12, fill=INK2)
    s.text(32, 504, "• terminationGracePeriodSeconds tính từ t = 0 (gồm cả preStop) phải lớn hơn preStop + request dài nhất; "
                    "quá hạn → SIGKILL, request dở dang bị cắt.", size=12, fill=INK2)
    s.save("13-graceful-shutdown.svg")


# ======================================================================
# Hình 14 — Flapping khi scale chỉ theo hàng đợi
# ======================================================================
def fig_flapping():
    W, H = 1240, 452
    s = Svg(W, H, "Scale chỉ theo hàng đợi làm số replica dao động và quá tải lặp lại; scale theo running cộng waiting "
                  "giữ số replica ổn định")
    s.header("Vì sao không scale chỉ theo hàng đợi",
             "Tải tăng lên 2,5C rồi giữ nguyên; so sánh số replica khi dùng A4 (chỉ waiting) và A2 (running + waiting) "
             "— minh hoạ")
    x = 32
    x = s.legend_swatch(x, 94, "Tải", "#dcdbd5", stroke=INK2)
    x = s.legend_line(x, 94, "Năng lực phục vụ (số replica × C)", BLUE, sw=2.4)
    s.legend_swatch(x, 94, "Quá tải → vi phạm SLO", CRIT, opacity=0.35)
    load = lambda t: 0.5 + 2.0 * smooth((t - 2) / 0.3)
    sched = {
        "a4": [(0, 1), (5, 3), (11, 2), (13.5, 3), (19.5, 2), (22, 3), (28, 2)],
        "a2": [(0, 1), (5, 3)],
    }

    def cap(key, t):
        r = 1
        for t0, n in sched[key]:
            if t >= t0:
                r = n
        return r

    panels = [("a4", "A4 · chỉ num_requests_waiting", 84,
               [("Số lần scale:", "6"), ("Thời gian quá tải:", "~10 phút / 30 phút")]),
              ("a2", "A2 · running + waiting", 704,
               [("Số lần scale:", "1"), ("Thời gian quá tải:", "~3 phút (chỉ lúc chờ cold start)")])]
    pw, ph, top, ymax = 470, 200, 150, 4.2
    ts = [i * 0.02 for i in range(0, 1501)]
    for key, title, x0, verdict in panels:
        y1 = top + ph
        X = lambda t: x0 + t / 30 * pw
        Y = lambda v: y1 - v / ymax * ph
        s.text(x0, top - 16, title, size=14, weight=700)
        for v in range(1, 5):
            s.line(x0, Y(v), x0 + pw, Y(v), stroke=GRID)
        for v in range(0, 5):
            s.text(x0 - 8, Y(v) + 4, "0" if v == 0 else f"{v}C", size=11, fill=MUTED, anchor="end")
        for t in (0, 10, 20, 30):
            s.text(X(t), y1 + 17, str(t), size=11, fill=MUTED, anchor="middle")
        s.text(x0 + pw, y1 + 33, "phút", size=11, fill=MUTED, anchor="end")
        lp = [(X(t), Y(load(t))) for t in ts]
        s.polygon([(X(0), y1)] + lp + [(X(30), y1)], fill="#dcdbd5", opacity=0.75)
        s.polyline(lp, INK2, sw=1.5)
        up = [(X(t), Y(max(load(t), cap(key, t)))) for t in ts]
        low = [(X(t), Y(cap(key, t))) for t in reversed(ts)]
        s.polygon(up + low, fill=CRIT, opacity=0.35)
        s.polyline([(X(t), Y(cap(key, t))) for t in ts], BLUE, sw=2.4)
        s.line(x0, y1, x0 + pw, y1, stroke=AXIS)
        if key == "a4":
            s.label(X(8), Y(3.75), "hàng đợi = 0 → desired = 1", fill=INK, size=11.5)
            s.arrow([(X(9.5), Y(3.5)), (X(10.8), Y(2.25))], INK2, sw=1.2, r=0)
        else:
            s.label(X(17), Y(3.75), "running vẫn ≈ 2,5 × B* → giữ 3 replica", fill=INK, size=11.5)
        for j, (k, v) in enumerate(verdict):
            s.rich(x0, y1 + 58 + j * 19, [(k + " ", 650, INK), (v, 400, INK2)], size=12.5)
    s.save("14-flapping.svg")


# ======================================================================
# Hình 15 — Hiệu chỉnh năng lực một replica
# ======================================================================
def fig_calibration():
    W, H = 1240, 452
    s = Svg(W, H, "Hiệu chỉnh năng lực: quét tốc độ request trên một replica; TTFT chạm ngưỡng SLO trước ITL; "
                  "C bằng 2,0 req/s, B* bằng 30 request đồng thời")
    s.header("Hiệu chỉnh năng lực một replica (calibration)",
             "Quét tốc độ λ trên 1 replica; C = λ lớn nhất mà mọi SLO còn đạt — số liệu minh hoạ")
    x = 32
    s.add(f'<circle cx="{x + 6}" cy="92" r="5.5" fill="{BLUE}"/>')
    s.text(x + 18, 96, "đạt mọi SLO", size=12, fill=INK2)
    x += 18 + text_width("đạt mọi SLO", 12) + 26
    s.add(f'<circle cx="{x + 6}" cy="92" r="5.5" fill="{CRIT}"/>')
    s.text(x + 18, 96, "vi phạm SLO (ở bất kỳ chỉ số nào)", size=12, fill=INK2)
    x += 18 + text_width("vi phạm SLO (ở bất kỳ chỉ số nào)", 12) + 26
    s.legend_line(x, 92, "ngưỡng SLO · C · B*", INK2, dash="6 4", sw=1.3)

    lams = [0.5, 1.0, 1.5, 1.75, 2.0, 2.25, 2.5]
    mu = 2.6
    ttft = [0.25 + 0.3 * (l / mu) / (1 - l / mu) for l in lams]
    itl = [30 + 45 * (l / mu) for l in lams]
    conc = [4.5, 9.5, 15.5, 19.5, 30, 44, 85]
    ok = [t <= 2 and i <= 100 for t, i in zip(ttft, itl)]
    panels = [
        ("TTFT p95 (s)", ttft, 8, [0, 2, 4, 6, 8], [(2, "SLO 2 s", -5)]),
        ("ITL p95 (ms)", itl, 120, [0, 30, 60, 90, 120], [(100, "SLO 100 ms", -5)]),
        ("Request đồng thời B (trung bình)", conc, 90, [0, 30, 60, 90], [(30, "B* = 30 (tại C)", -5),
                                                                          (24, "target A2 = 0,8·B* = 24", 16)]),
    ]
    pw, ph, top = 320, 210, 150
    for p, (title, ys, ymax, ticks, refs) in enumerate(panels):
        x0 = 84 + p * 404
        y1 = top + ph
        X = lambda l: x0 + l / 2.75 * pw
        Y = lambda v: y1 - min(v, ymax) / ymax * ph
        s.text(x0 - 40, top - 16, title, size=13.5, weight=700)
        for v in ticks:
            if v:
                s.line(x0, Y(v), x0 + pw, Y(v), stroke=GRID)
            s.text(x0 - 8, Y(v) + 4, str(v), size=11, fill=MUTED, anchor="end")
        for l in (0, 0.5, 1.0, 1.5, 2.0, 2.5):
            s.text(X(l), y1 + 17, _dec(l), size=11, fill=MUTED, anchor="middle")
        s.text(x0 + pw, y1 + 33, "λ (req/s)", size=11, fill=MUTED, anchor="end")
        s.line(x0, y1, x0 + pw, y1, stroke=AXIS)
        for v, lab, dy in refs:
            s.line(x0, Y(v), x0 + pw, Y(v), stroke=INK2, sw=1.2, dash="6 4")
            s.label(x0 + 6, Y(v) + dy, lab, anchor="start", fill=INK, size=11)
        s.line(X(2.0), top, X(2.0), y1, stroke=INK, sw=1.1, dash="3 3")
        s.text(X(2.0) + 5, top + 12, "C = 2,0", size=11.5, weight=650)
        pts = [(X(l), Y(v)) for l, v in zip(lams, ys)]
        s.add('<polyline points="' + " ".join(f"{f(a)},{f(b)}" for a, b in pts) +
              f'" fill="none" stroke="{BLUE}" stroke-opacity="0.45" stroke-width="1.6"/>')
        for (px, py), good in zip(pts, ok):
            s.add(f'<circle cx="{f(px)}" cy="{f(py)}" r="6" fill="{BLUE if good else CRIT}" '
                  f'stroke="{SURFACE}" stroke-width="2"/>')
    s.text(32, 424, "TTFT chạm ngưỡng trước (≈ 2,2 req/s) trong khi ITL còn xa ngưỡng → C = mức quét lớn nhất còn đạt = 2,0 req/s. "
                    "Định luật Little: B* ≈ C × E2E ≈ 2,0 × 15 s = 30.", size=12, fill=INK2)
    s.save("15-hieu-chinh-nang-luc.svg")


# ======================================================================
# Hình 16 — Nguồn dữ liệu và luồng xử lý
# ======================================================================
def fig_data():
    W, H = 1240, 548
    s = Svg(W, H, "Dữ liệu một lượt chạy: sáu nguồn, thu thập qua ghi trực tiếp, Prometheus và runner, lưu thành một "
                  "thư mục cho mỗi lượt, rồi căn thời gian và tổng hợp")
    s.header("Dữ liệu của một lượt chạy: thu thập → lưu trữ → tổng hợp",
             "Mọi nguồn đều mang timestamp (các máy đồng bộ giờ bằng NTP); runner gom về một thư mục cho mỗi lượt")
    for x, lab in ((32, "NGUỒN"), (330, "THU THẬP"), (628, "LƯU TRỮ (mỗi lượt)"), (956, "XỬ LÝ")):
        s.text(x, 100, lab, size=12, weight=700, fill=INK2)
    sources = [("Máy tạo tải", "1 dòng / request: TTFT, E2E…"),
               ("vLLM /metrics", "hàng đợi, running, KV-cache"),
               ("DCGM exporter", "GPU util, SM active, VRAM"),
               ("kube-state-metrics", "replicas, trạng thái pod, HPA"),
               ("Kubernetes API", "pod conditions, events"),
               ("Log vLLM", "thời gian nạp model, compile")]
    for i, (t, l) in enumerate(sources):
        y = 112 + i * 64
        s.box(32, y, 250, 52, t, [l], tsize=13, align="start")
        tgt_y = y + 26
        s.arrow([(282, tgt_y), (330, tgt_y)], INK2 if i in (0, 4, 5) else VIOLET, sw=1.5,
                dash=None if i in (0, 4, 5) else "5 4")
    s.box(330, 112, 250, 52, "Ghi trực tiếp", ["CSV append theo request"], tsize=13, align="start")
    s.box(330, 176, 250, 180, "Prometheus", ["scrape mỗi 5 s", "runner gọi query_range", "theo cửa sổ lượt chạy",
                                             "→ xuất Parquet"], tsize=13, align="start", fill=VIOLET_T, stroke="#d6d1ef")
    s.box(330, 368, 250, 116, "Runner theo dõi", ["watch pod conditions", "và events; lấy log vLLM"], tsize=13,
          align="start")
    for y in (138, 266, 426):
        s.arrow([(580, y), (628, y)], INK2, sw=1.6)
    s.rect(628, 112, 280, 372, fill=WHITE, stroke=INK2, sw=1.3, rx=10)
    s.text(644, 138, "runs/<run-id>/", size=12.5, weight=700, family=MONO)
    files = [("metadata.json", "cấu hình, phiên bản, seed"),
             ("phases.json", "mốc bắt đầu/kết thúc pha"),
             ("requests.csv", "log từng request"),
             ("metrics.parquet", "chuỗi Prometheus"),
             ("events.jsonl", "sự kiện pod, HPA"),
             ("vllm-logs/", "log từng pod"),
             ("checks.json", "kết quả kiểm tra hợp lệ")]
    for i, (fn, d) in enumerate(files):
        y = 170 + i * 44
        s.text(652, y, fn, size=12, fill=INK, family=MONO)
        s.text(652, y + 17, d, size=11, fill=INK2)
    steps = [("Căn thời gian, cắt pha", "bỏ warm-up; gắn nhãn pha KB"),
             ("Bảng theo request", "TTFT, TPOT, E2E, đạt SLO?"),
             ("Bảng theo pha / lượt", "p95, SLO attainment, GPU-giờ"),
             ("Bảng theo ô ma trận", "trung bình ± CI qua 3 lượt")]
    for i, (t, l) in enumerate(steps):
        y = 112 + i * 96
        s.box(956, y, 252, 76, t, [l], tsize=13, align="start")
        if i < 3:
            s.arrow([(1082, y + 76), (1082, y + 96)], INK2, sw=1.6)
    s.arrow([(908, 150), (956, 150)], INK2, sw=1.6)
    s.text(956, 512, "→ biểu đồ, kiểm định, bảng trong luận văn", size=12, fill=INK2)
    s.save("16-nguon-du-lieu.svg")


def build_all():
    fig_knee()
    fig_batching()
    fig_coldstart_detail()
    fig_shutdown()
    fig_flapping()
    fig_calibration()
    fig_data()
