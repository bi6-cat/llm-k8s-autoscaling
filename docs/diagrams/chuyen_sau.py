"""Sơ đồ bổ sung cho các tài liệu chuyên sâu trong docs/chi-tiet/ (Hình 10–17).

Được gọi từ build_diagrams.py; dùng chung lớp Svg và bảng màu.
"""
import math

from build_diagrams import (AQUA, AXIS, BLUE, BLUE_T, CRIT, GOOD, GRAY_T, GREEN_T, GRID, INK, INK2, MONO,
                            MUTED, ORANGE, ORANGE_T, OWNER, SURFACE, VIOLET, VIOLET_T, WARN, WHITE, YELLOW,
                            YELLOW_T, Svg, f, smooth, text_width)

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
# Hình 15 — Đo năng lực một replica
# ======================================================================
def fig_calibration():
    W, H = 1240, 452
    s = Svg(W, H, "Đo năng lực: quét tốc độ request trên một replica; TTFT chạm ngưỡng SLO trước ITL; "
                  "C bằng 2,0 req/s, B* bằng 30 request đồng thời")
    s.header("Đo năng lực một replica (capacity planning)",
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
# Hình 16 — Rolling update khi không còn GPU trống
# ======================================================================
def fig_rolling_update():
    W, H = 1240, 596
    s = Svg(W, H, "Rolling update khi cả 4 GPU đều có pod: cấu hình maxSurge 1 maxUnavailable 0 bị kẹt vì pod mới "
                  "không có GPU; cấu hình maxSurge 0 maxUnavailable 1 xoá pod cũ trước, năng lực còn 3/4 "
                  "trong suốt lần cập nhật")
    s.header("Cập nhật phiên bản khi mọi GPU đều đang có pod",
             "4 GPU, HPA đang chạy 4 replica; so sánh hai cách đặt maxSurge / maxUnavailable — thời gian minh hoạ")
    X = lambda t: 200 + t * 120
    x = 32
    x = s.legend_swatch(x, 92, "pod cũ (v1)", BLUE_T, stroke=BLUE)
    x = s.legend_swatch(x, 92, "drain (preStop, làm nốt request)", ORANGE_T, stroke=ORANGE)
    x = s.legend_swatch(x, 92, "cold start pod mới", YELLOW_T, stroke="#c98500")
    x = s.legend_swatch(x, 92, "pod mới (v2) Ready", GREEN_T, stroke=GOOD)
    s.legend_swatch(x, 92, "Pending: không còn GPU trống", s.hatch(CRIT), stroke=CRIT)

    def seg(t0, t1, y, fill, stroke, label=None, h=20):
        s.rect(X(t0), y, X(t1) - X(t0), h, fill=fill, stroke=stroke, sw=1, rx=4)
        if label and X(t1) - X(t0) > text_width(label, 11) + 10:
            s.text((X(t0) + X(t1)) / 2, y + 14, label, size=11, anchor="middle", fill=INK)

    def grid(y0, y1):
        for m in range(0, 9):
            s.line(X(m), y0, X(m), y1, stroke=GRID)

    # (a) kiểu web
    s.rich(32, 130, [("(a) maxSurge: 1 · maxUnavailable: 0", 700, INK), ("  cấu hình quen thuộc của web", 400, INK2)],
           size=13.5)
    grid(140, 278)
    for i in range(4):
        y = 148 + i * 26
        s.text(40, y + 15, f"GPU {i}", size=12, fill=INK2)
        seg(0, 8, y, BLUE_T, BLUE, "v1 · vẫn phục vụ, không được xoá vì maxUnavailable = 0")
    s.text(40, 252 + 15, "pod mới (v2)", size=12, fill=INK2)
    seg(0.1, 8, 252, s.hatch(CRIT), CRIT)
    s.label(X(4.05), 252 + 15, "Pending: Insufficient nvidia.com/gpu", size=11, fill=INK)
    s.text(200, 300, "→ Kẹt cho tới khi tải giảm và HPA tự scale-down. Sau 600 s, Deployment báo "
                     "ProgressDeadlineExceeded và cảnh báo LLMPodPending kêu.", size=12, fill=INK)

    # (b) cho GPU
    s.rich(32, 338, [("(b) maxSurge: 0 · maxUnavailable: 1", 700, INK), ("  đồ án chọn", 400, INK2)], size=13.5)
    grid(348, 478)
    starts, drain, cold = [0.25, 2.0, 3.75, 5.5], 0.5, 1.25
    for i, st in enumerate(starts):
        y = 352 + i * 26
        s.text(40, y + 15, f"GPU {i}", size=12, fill=INK2)
        seg(0, st, y, BLUE_T, BLUE, "v1")
        seg(st, st + drain, y, ORANGE_T, ORANGE, "drain")
        seg(st + drain, st + drain + cold, y, YELLOW_T, "#c98500", "cold start")
        seg(st + drain + cold, 8, y, GREEN_T, GOOD, "v2 Ready")
    end = starts[-1] + drain + cold
    s.text(40, 456 + 15, "Năng lực", size=12, weight=650, fill=INK)
    seg(0, starts[0], 456, GREEN_T, GOOD, "4/4")
    seg(starts[0], end, 456, "#fbe9e8", CRIT, "3/4 trong suốt lần cập nhật (≈ 4 × (drain + cold start))")
    seg(end, 8, 456, GREEN_T, GOOD, "4/4")

    ya = 486
    s.line(X(0), ya, X(8), ya, stroke=AXIS)
    for m in range(0, 9):
        s.line(X(m), ya, X(m), ya + 5, stroke=AXIS)
        s.text(X(m), ya + 19, str(m), size=11, fill=MUTED, anchor="middle")
    s.text(X(8) + 10, ya + 19, "phút", size=11, fill=MUTED)
    for i, ln in enumerate([
            "• (a) chỉ chạy được khi còn GPU trống: lúc tải thấp HPA chỉ chạy 1–2 replica nên không kẹt; lúc tải cao thì kẹt.",
            "• (b) không bao giờ kẹt, đổi lại năng lực còn 3/4 trong lúc cập nhật; nên cập nhật lúc tải thấp "
            "(sync window của Argo CD).",
            "• (c) giữ một GPU trống (maxReplicaCount = 3) để dùng (a) mà không giảm năng lực; đổi lại mất 25% năng lực "
            "tối đa."]):
        s.text(32, 532 + i * 22, ln, size=12, fill=INK2)
    s.save("16-rolling-update-gpu.svg")


# ======================================================================
# Hình 17 — Quy trình một đợt đánh giá trên GPU thuê
# ======================================================================
def fig_eval_pipeline():
    W, H = 1240, 620
    s = Svg(W, H, "Quy trình một đợt đánh giá: thuê và dựng từ máy trắng, triển khai, đo năng lực, vòng lặp 28 lượt, "
                  "cold start và kịch bản vận hành, sao lưu, huỷ máy và phân tích")
    s.header("Quy trình tự động của một đợt đánh giá trên GPU thuê",
             "Mọi bước chạy bằng script để dựng lại được và rút ngắn thời gian thuê GPU; nhãn màu = người phụ trách")
    x = 760
    for o in ("Trình", "Quang", "Cả nhóm"):
        s.add(f'<circle cx="{x}" cy="57" r="5" fill="{OWNER[o]}"/>')
        s.text(x + 10, 61, o, size=12, fill=INK2)
        x += text_width(o, 12) + 34
    xs = [32, 448, 864]
    row1 = [(1, "Thuê máy & dựng từ đầu", ["vastai: thuê VM 4 GPU, burn-in", "Ansible + Argo CD; đo thời gian (VH5)"],
             "Quang"),
            (2, "Triển khai nền tảng", ["Argo CD sync: giám sát, cảnh báo,", "KEDA, vLLM; tắt auto-sync autoscaling"],
             "Cả nhóm"),
            (3, "Đo năng lực", ["quét tốc độ → tìm C của 1 replica", "chốt SLO, target A1, A2 (ADR-003)"], "Trình")]
    for i, (n, t, ls, o) in enumerate(row1):
        s.step_box(xs[i], 86, 344, 100, n, t, ls, INK2, owner=o)
    s.arrow([(376, 136), (448, 136)], INK2, sw=1.8)
    s.arrow([(792, 136), (864, 136)], INK2, sw=1.8)
    s.arrow([(1036, 186), (1036, 234)], INK2, sw=1.8)

    s.rect(32, 234, 1176, 216, fill=GRAY_T, stroke=AXIS, rx=14)
    s.add(f'<circle cx="56" cy="259" r="12" fill="{INK2}"/>')
    s.text(56, 263.5, "4", size=12.5, weight=700, fill=WHITE, anchor="middle")
    s.rich(76, 264, [("Vòng lặp đánh giá autoscaling", 650, INK),
                     ("  4 cấu hình × 3 kịch bản, 2–3 lượt mỗi ô = 28 lượt · runner (Python)", 400, INK2)],
           size=13.5)
    s.owner_pill(1194, 248, "Quang")
    steps = [("a", "Áp cấu hình", ["S1, S4 hoặc", "ScaledObject A1/A2"]),
             ("b", "Reset", ["về 1 replica,", "chờ hệ thống ổn định"]),
             ("c", "Warm-up", ["2 phút tải nhẹ", "(không tính kết quả)"]),
             ("d", "Chạy kịch bản", ["λ(t) theo KB1–KB3,", "log từng request"]),
             ("e", "Thu thập", ["CSV, Prometheus,", "sự kiện pod, cảnh báo"]),
             ("f", "Cooldown", ["chờ scale-down,", "kiểm tra dữ liệu"])]
    for i, (k, t, ls) in enumerate(steps):
        bx = 52 + i * 194
        s.rect(bx, 286, 172, 96, fill=WHITE, stroke=AXIS, rx=10)
        s.text(bx + 14, 310, f"{k}. {t}", size=13.5, weight=650)
        for j, ln in enumerate(ls):
            s.text(bx + 14, 334 + j * 18, ln, size=11.5, fill=INK2)
        if i < 5:
            s.arrow([(bx + 172, 334), (bx + 194, 334)], INK2, sw=1.6)
    s.arrow([(1108, 382), (1108, 424), (138, 424), (138, 382)], INK2, sw=1.6, dash="5 4")
    s.label(623, 428, "lượt tiếp theo", bg=GRAY_T, fill=INK)
    s.arrow([(1036, 450), (1036, 494)], INK2, sw=1.8)

    row3 = [(864, 5, "Cold start & vận hành", ["L0/L2; rolling update, xoá pod,", "mất Prometheus, kiểm tra cảnh báo"],
             "Cả nhóm"),
            (448, 6, "Sao lưu, huỷ máy, phân tích", ["đẩy dữ liệu lên R2; huỷ instance;", "pandas: bảng và biểu đồ"],
             "Quang")]
    for bx, n, t, ls, o in row3:
        s.step_box(bx, 494, 344, 100, n, t, ls, INK2, owner=o)
    s.arrow([(864, 544), (792, 544)], INK2, sw=1.8)
    s.rect(32, 494, 344, 100, fill=SURFACE, stroke=INK2, dash="5 4", rx=10)
    s.text(48, 524, "Kết quả", size=13.5, weight=650)
    s.text(48, 550, "bảng nghiệm thu N1–N8,", size=11.5, fill=INK2)
    s.text(48, 567.5, "khuyến nghị cấu hình vận hành", size=11.5, fill=INK2)
    s.arrow([(448, 544), (376, 544)], INK2, sw=1.8)
    s.save("17-quy-trinh-danh-gia.svg")


def build_all():
    fig_knee()
    fig_batching()
    fig_coldstart_detail()
    fig_shutdown()
    fig_flapping()
    fig_calibration()
    fig_rolling_update()
    fig_eval_pipeline()
