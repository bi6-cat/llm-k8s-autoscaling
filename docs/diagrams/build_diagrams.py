#!/usr/bin/env python3
"""Sinh toàn bộ sơ đồ SVG cho tài liệu mô tả đồ án (chỉ dùng thư viện chuẩn).

Chạy:   python3 docs/diagrams/build_diagrams.py
Kết quả: docs/images/*.svg  (xuất PNG: docs/diagrams/export_png.sh)
"""
import math
import os
from html import escape

OUT = os.path.normpath(os.path.join(os.path.dirname(__file__), "..", "images"))

FONT = "system-ui, -apple-system, 'Segoe UI', Roboto, 'Helvetica Neue', Arial, sans-serif"
MONO = "ui-monospace, SFMono-Regular, Menlo, Consolas, monospace"

# Bảng màu tham chiếu (categorical đã kiểm định CVD) + mực chữ + nền
SURFACE, CARD_BORDER = "#fcfcfb", "#e4e3de"
INK, INK2, MUTED = "#0b0b0b", "#52514e", "#898781"
GRID, AXIS = "#e1e0d9", "#c3c2b7"
BLUE, ORANGE, AQUA, YELLOW = "#2a78d6", "#eb6834", "#1baf7a", "#eda100"
MAGENTA, GREEN, VIOLET = "#e87ba4", "#008300", "#4a3aa7"
GOOD, WARN, CRIT = "#0ca30c", "#fab219", "#d03b3b"
BLUE_T, ORANGE_T, VIOLET_T = "#eef4fc", "#fdf3ee", "#f2f0fa"
GREEN_T, GRAY_T, YELLOW_T = "#edf6ed", "#f4f3ef", "#fdf3dc"
WHITE = "#ffffff"

OWNER = {"Trình": BLUE, "Quang": ORANGE, "Cả nhóm": AQUA}


def f(v):
    return f"{round(v, 1):g}"


def text_width(s, size, weight=400):
    w = 0.0
    for ch in s:
        if ch in "il.,:;'|!()[]{}·•/ ":
            w += 0.30
        elif ch in "fjrt-":
            w += 0.38
        elif ch in "mwMW%@":
            w += 0.86
        elif ch.isupper():
            w += 0.66
        elif ch.isdigit():
            w += 0.57
        else:
            w += 0.54
    return w * size * (1.06 if weight >= 600 else 1.0)


def rounded_path(pts, r=8):
    d = f"M{f(pts[0][0])},{f(pts[0][1])}"
    for i in range(1, len(pts) - 1):
        (x0, y0), (x1, y1), (x2, y2) = pts[i - 1], pts[i], pts[i + 1]
        l1, l2 = math.hypot(x1 - x0, y1 - y0), math.hypot(x2 - x1, y2 - y1)
        rr = min(r, l1 / 2, l2 / 2)
        ax, ay = x1 - (x1 - x0) / l1 * rr, y1 - (y1 - y0) / l1 * rr
        bx, by = x1 + (x2 - x1) / l2 * rr, y1 + (y2 - y1) / l2 * rr
        d += f" L{f(ax)},{f(ay)} Q{f(x1)},{f(y1)} {f(bx)},{f(by)}"
    d += f" L{f(pts[-1][0])},{f(pts[-1][1])}"
    return d


class Svg:
    def __init__(self, w, h, label):
        self.w, self.h, self.aria = w, h, label
        self.defs, self.body, self._ids = [], [], set()

    # ---------- nguyên tố cơ bản ----------
    def add(self, s):
        self.body.append(s)

    def marker(self, color):
        mid = "a" + color.strip("#")
        if mid not in self._ids:
            self._ids.add(mid)
            self.defs.append(
                f'<marker id="{mid}" viewBox="0 0 10 10" refX="9" refY="5" markerUnits="userSpaceOnUse" '
                f'markerWidth="10" markerHeight="10" orient="auto-start-reverse">'
                f'<path d="M0,1 L10,5 L0,9 z" fill="{color}"/></marker>')
        return mid

    def hatch(self, color=MUTED):
        pid = "h" + color.strip("#")
        if pid not in self._ids:
            self._ids.add(pid)
            self.defs.append(
                f'<pattern id="{pid}" width="6" height="6" patternUnits="userSpaceOnUse" '
                f'patternTransform="rotate(45)"><line x1="0" y1="0" x2="0" y2="6" '
                f'stroke="{color}" stroke-width="1.3"/></pattern>')
        return f"url(#{pid})"

    def rect(self, x, y, w, h, fill=WHITE, stroke=AXIS, sw=1.2, rx=10, dash=None, opacity=None):
        a = f' stroke-dasharray="{dash}"' if dash else ""
        o = f' fill-opacity="{opacity}"' if opacity is not None else ""
        st = f' stroke="{stroke}" stroke-width="{sw}"' if stroke else ""
        self.add(f'<rect x="{f(x)}" y="{f(y)}" width="{f(w)}" height="{f(h)}" rx="{rx}" fill="{fill}"{o}{st}{a}/>')

    def line(self, x1, y1, x2, y2, stroke=GRID, sw=1, dash=None):
        a = f' stroke-dasharray="{dash}"' if dash else ""
        self.add(f'<line x1="{f(x1)}" y1="{f(y1)}" x2="{f(x2)}" y2="{f(y2)}" stroke="{stroke}" stroke-width="{sw}"{a}/>')

    def text(self, x, y, s, size=13, weight=400, fill=INK, anchor="start", family=None):
        fam = f' font-family="{family}"' if family else ""
        self.add(f'<text x="{f(x)}" y="{f(y)}" font-size="{size}" font-weight="{weight}" fill="{fill}" '
                 f'text-anchor="{anchor}"{fam}>{escape(s)}</text>')

    def rich(self, x, y, parts, size=13, anchor="start"):
        """parts: [(chuỗi, weight, màu)] nối liền trên một dòng."""
        spans = "".join(f'<tspan font-weight="{w}" fill="{c}">{escape(t)}</tspan>' for t, w, c in parts)
        self.add(f'<text x="{f(x)}" y="{f(y)}" font-size="{size}" text-anchor="{anchor}">{spans}</text>')

    def path(self, d, stroke=INK2, sw=1.6, fill="none", dash=None, head=True, opacity=None):
        a = f' stroke-dasharray="{dash}"' if dash else ""
        m = f' marker-end="url(#{self.marker(stroke)})"' if head else ""
        o = f' fill-opacity="{opacity}"' if opacity is not None else ""
        self.add(f'<path d="{d}" fill="{fill}"{o} stroke="{stroke}" stroke-width="{sw}" '
                 f'stroke-linejoin="round" stroke-linecap="round"{a}{m}/>')

    def arrow(self, pts, color=INK2, sw=1.6, dash=None, head=True, r=8):
        self.path(rounded_path(pts, r), stroke=color, sw=sw, dash=dash, head=head)

    def polygon(self, pts, fill, opacity=None, stroke=None, sw=1):
        o = f' fill-opacity="{opacity}"' if opacity is not None else ""
        st = f' stroke="{stroke}" stroke-width="{sw}"' if stroke else ""
        p = " ".join(f"{f(x)},{f(y)}" for x, y in pts)
        self.add(f'<polygon points="{p}" fill="{fill}"{o}{st}/>')

    def polyline(self, pts, stroke, sw=2, dash=None):
        a = f' stroke-dasharray="{dash}"' if dash else ""
        p = " ".join(f"{f(x)},{f(y)}" for x, y in pts)
        self.add(f'<polyline points="{p}" fill="none" stroke="{stroke}" stroke-width="{sw}" '
                 f'stroke-linejoin="round" stroke-linecap="round"{a}/>')

    # ---------- thành phần ghép ----------
    def label(self, x, y, s, size=11, fill=INK2, anchor="middle", bg=SURFACE, weight=400):
        w = text_width(s, size, weight) * 1.06 + 12
        x0 = x - w / 2 if anchor == "middle" else (x - 5 if anchor == "start" else x - w + 5)
        self.rect(x0, y - size - 1, w, size + 7, fill=bg, stroke=None, rx=4)
        self.text(x, y, s, size=size, fill=fill, anchor=anchor, weight=weight)

    def header(self, title, subtitle=None):
        self.text(32, 38, title, size=19, weight=700)
        if subtitle:
            self.text(32, 61, subtitle, size=13, fill=INK2)

    def box(self, x, y, w, h, title, lines=(), fill=WHITE, stroke=AXIS, dash=None, sw=1.2,
            tsize=13.5, lsize=11.5, rx=10, align="middle"):
        self.rect(x, y, w, h, fill=fill, stroke=stroke, sw=sw, dash=dash, rx=rx)
        block = tsize * 1.1 + len(lines) * lsize * 1.45
        ty = y + (h - block) / 2 + tsize * 0.95
        tx = x + w / 2 if align == "middle" else x + 14
        self.text(tx, ty, title, size=tsize, weight=650, anchor=align if align == "middle" else "start")
        for i, ln in enumerate(lines):
            self.text(tx, ty + (i + 1) * lsize * 1.45 + 1, ln, size=lsize, fill=INK2,
                      anchor=align if align == "middle" else "start")

    def group(self, x, y, w, h, title, sub=None, fill=GRAY_T, stroke=AXIS, dash=None, tsize=12.5, tx=14):
        self.rect(x, y, w, h, fill=fill, stroke=stroke, dash=dash, rx=12)
        parts = [(title, 650, INK)]
        if sub:
            parts.append(("  " + sub, 400, INK2))
        self.rich(x + tx, y + 21, parts, size=tsize)

    def step_box(self, x, y, w, h, num, title, lines, accent, owner=None, fill=WHITE, dash=None):
        self.rect(x, y, w, h, fill=fill, stroke=AXIS, dash=dash, rx=10)
        self.add(f'<circle cx="{f(x + 24)}" cy="{f(y + 25)}" r="12" fill="{accent}"/>')
        self.text(x + 24, y + 29.5, str(num), size=12.5, weight=700, fill=WHITE, anchor="middle")
        self.text(x + 44, y + 30, title, size=13.5, weight=650)
        for i, ln in enumerate(lines):
            self.text(x + 16, y + 56 + i * 17.5, ln, size=11.5, fill=INK2)
        if owner:
            self.owner_pill(x + w - 12, y + 16, owner)

    def owner_pill(self, x_right, y, owner):
        w = text_width(owner, 11, 600) + 26
        self.rect(x_right - w, y, w, 19, fill=WHITE, stroke=AXIS, sw=1, rx=9.5)
        self.add(f'<circle cx="{f(x_right - w + 10)}" cy="{f(y + 9.5)}" r="4" fill="{OWNER[owner]}"/>')
        self.text(x_right - w + 18, y + 13.5, owner, size=11, weight=600, fill=INK2)

    def status_pill(self, x, y, s, color, tint):
        w = text_width(s, 10.5, 600) * 1.1 + 24
        self.rect(x, y, w, 18, fill=tint, stroke=color, sw=1, rx=9)
        self.add(f'<circle cx="{f(x + 9)}" cy="{f(y + 9)}" r="3.5" fill="{color}"/>')
        self.text(x + 16, y + 13, s, size=10.5, weight=600, fill=INK)
        return w

    def gpu_chip(self, x, y, w, h, s):
        for i in range(4):
            px = x + (i + 1) * w / 5
            self.line(px, y - 4, px, y, stroke=GREEN, sw=1.5)
            self.line(px, y + h, px, y + h + 4, stroke=GREEN, sw=1.5)
        self.rect(x, y, w, h, fill=GREEN_T, stroke=GREEN, sw=1.4, rx=5)
        self.text(x + w / 2, y + h / 2 + 4.5, s, size=11.5, weight=650, fill=INK, anchor="middle")

    def legend_line(self, x, y, s, color, dash=None, sw=2):
        a = f' stroke-dasharray="{dash}"' if dash else ""
        self.add(f'<line x1="{f(x)}" y1="{f(y)}" x2="{f(x + 26)}" y2="{f(y)}" stroke="{color}" '
                 f'stroke-width="{sw}"{a} stroke-linecap="round"/>')
        self.text(x + 33, y + 4, s, size=12, fill=INK2)
        return x + 33 + text_width(s, 12) + 26

    def legend_swatch(self, x, y, s, fill, stroke=None, opacity=None):
        self.rect(x, y - 6, 14, 12, fill=fill, stroke=stroke, sw=1, rx=3, opacity=opacity)
        self.text(x + 20, y + 4, s, size=12, fill=INK2)
        return x + 20 + text_width(s, 12) + 24

    def save(self, name):
        os.makedirs(OUT, exist_ok=True)
        svg = (
            f'<svg xmlns="http://www.w3.org/2000/svg" width="{self.w}" height="{self.h}" '
            f'viewBox="0 0 {self.w} {self.h}" role="img" aria-label="{escape(self.aria)}" '
            f'font-family="{FONT}">\n<title>{escape(self.aria)}</title>\n'
            f'<defs>{"".join(self.defs)}</defs>\n'
            f'<rect x="0.5" y="0.5" width="{self.w - 1}" height="{self.h - 1}" rx="14" '
            f'fill="{SURFACE}" stroke="{CARD_BORDER}"/>\n' + "\n".join(self.body) + "\n</svg>\n")
        with open(os.path.join(OUT, name), "w", encoding="utf-8") as fh:
            fh.write(svg)
        print("wrote", name)


# ======================================================================
# Hình 1 — Bài toán trade-off
# ======================================================================
def smooth(x):
    x = max(0.0, min(1.0, x))
    return x * x * (3 - 2 * x)


def demo_load(t):
    return 0.6 + 2.6 * smooth((t - 14) / 3) - 1.8 * smooth((t - 38) / 5)


def demo_auto_cap(t):
    steps = [(0, 1), (18.5, 2), (19.5, 3), (20.5, 4), (48, 3), (49.5, 2)]
    r = 1
    for t0, n in steps:
        if t >= t0:
            r = n
    return r


def fig_tradeoff():
    W, H = 1200, 420
    s = Svg(W, H, "Ba cách cấp phát GPU cho cùng một tải thay đổi: Static-min quá tải, "
                  "Static-max lãng phí, Autoscaling bám theo tải nhưng có độ trễ scale-up")
    s.header("Bài toán: hiệu năng phục vụ ↔ hiệu quả sử dụng GPU",
             "Cùng một tải thay đổi theo thời gian — ba cách cấp phát cho ba kết quả khác nhau")
    x = 32
    x = s.legend_swatch(x, 94, "Tải (nhu cầu)", "#dcdbd5", stroke=INK2)
    x = s.legend_line(x, 94, "Năng lực phục vụ (số replica × C)", BLUE, sw=2.4)
    x = s.legend_swatch(x, 94, "Thiếu năng lực → vi phạm SLO", CRIT, opacity=0.35)
    s.legend_swatch(x, 94, "Dư năng lực → lãng phí GPU", s.hatch(), stroke=MUTED)

    panels = [
        ("Static-min · cố định 1 replica", lambda t: 1.0,
         [("SLO:", "vi phạm nặng khi tải cao"), ("GPU-giờ:", "thấp nhất")]),
        ("Static-max · cố định 4 replica", lambda t: 4.0,
         [("SLO:", "đạt trong mọi pha"), ("GPU-giờ:", "cao nhất (cấp theo đỉnh)")]),
        ("Autoscaling · 1–4 replica", demo_auto_cap,
         [("SLO:", "vi phạm ngắn trong lúc scale-up"), ("GPU-giờ:", "bám theo tải")]),
    ]
    pw, ph, top = 318, 196, 140
    ymax = 4.5
    ts = [i * 0.05 for i in range(0, 1201)]
    for i, (title, cap, verdict) in enumerate(panels):
        x0 = 78 + i * 382
        y1 = top + ph
        X = lambda t: x0 + t / 60 * pw
        Y = lambda v: y1 - v / ymax * ph
        s.text(x0, top - 12, title, size=13.5, weight=650)
        for v in range(1, 5):
            s.line(x0, Y(v), x0 + pw, Y(v), stroke=GRID)
        for v in range(0, 5):
            s.text(x0 - 8, Y(v) + 4, "0" if v == 0 else f"{v}C", size=11, fill=MUTED, anchor="end")
        for t in (0, 15, 30, 45, 60):
            s.text(X(t), y1 + 17, f"{t}", size=11, fill=MUTED, anchor="middle")
        s.text(x0 + pw, y1 + 33, "phút", size=11, fill=MUTED, anchor="end")
        load = [(X(t), Y(demo_load(t))) for t in ts]
        s.polygon([(X(0), y1)] + load + [(X(60), y1)], fill="#dcdbd5", opacity=0.75)
        s.polyline(load, INK2, sw=1.5)
        upper_short = [(X(t), Y(max(demo_load(t), cap(t)))) for t in ts]
        lower_cap = [(X(t), Y(cap(t))) for t in reversed(ts)]
        s.polygon(upper_short + lower_cap, fill=CRIT, opacity=0.35)
        upper_cap = [(X(t), Y(cap(t))) for t in ts]
        lower_waste = [(X(t), Y(min(demo_load(t), cap(t)))) for t in reversed(ts)]
        s.polygon(upper_cap + lower_waste, fill=s.hatch())
        s.polyline([(X(t), Y(cap(t))) for t in ts], BLUE, sw=2.4)
        s.line(x0, y1, x0 + pw, y1, stroke=AXIS, sw=1)
        if i == 0:
            s.label(X(27), Y(2.2), "quá tải", size=11.5, fill=INK, bg="#f4c9c4")
        elif i == 1:
            s.label(X(8), Y(2.6), "lãng phí", size=11.5, fill=INK)
        else:
            s.arrow([(X(8.5), Y(2.9)), (X(15.2), Y(2.2))], color=INK2, sw=1.2, r=0)
            s.text(X(8.2), Y(2.9) - 5, "trễ scale-up", size=11.5, fill=INK, anchor="middle")
            s.arrow([(X(51), Y(2.75)), (X(48.4), Y(3.4))], color=INK2, sw=1.2, r=0)
            s.label(X(60), Y(2.45), "chờ ổn định rồi giảm", size=11.5, fill=INK, anchor="end")
        for j, (k, v) in enumerate(verdict):
            s.rich(x0, y1 + 56 + j * 18, [(k + " ", 650, INK), (v, 400, INK2)], size=12)
    s.save("01-bai-toan-trade-off.svg")


# ======================================================================
# Hình 2 — Kiến trúc tổng thể
# ======================================================================
def fig_architecture():
    W, H = 1280, 730
    s = Svg(W, H, "Kiến trúc tổng thể: client gửi request qua Traefik và Service tới các pod vLLM "
                  "(mỗi pod 1 GPU, kiểm API key); Prometheus thu metric, Alertmanager gửi cảnh báo; "
                  "KEDA và HPA điều chỉnh số replica")
    s.header("Kiến trúc tổng thể nền tảng LLM Serving có Autoscaling",
             "Một Deployment vLLM, mỗi pod dùng 1 GPU; KEDA + HPA điều chỉnh số replica theo metric của chính vLLM")
    x = 32
    x = s.legend_line(x, 86, "Luồng request / token", BLUE, sw=2.2)
    x = s.legend_line(x, 86, "Thu thập metric", VIOLET, dash="5 4")
    x = s.legend_line(x, 86, "Điều khiển scale", ORANGE, sw=2.2)
    s.legend_line(x, 86, "Nạp image / model", INK2, dash="3 4", sw=1.5)

    # cụm Kubernetes
    s.rect(232, 104, 820, 596, fill="#fbfbfa", stroke=INK2, sw=1.4, rx=16)
    s.rich(250, 126, [("Kubernetes cluster", 700, INK), ("  k3s", 400, INK2)], size=13.5)

    # namespace llm-serving
    s.group(252, 138, 780, 318, "namespace: llm-serving", fill=BLUE_T, stroke="#c9dcf3")
    s.box(272, 269, 140, 64, "Traefik", ["giới hạn tốc độ", "route riêng cho tải"])
    s.box(440, 269, 140, 64, "Service vllm", ["ClusterIP · chia tải"])
    s.box(440, 172, 140, 56, "Lưu model", ["NVMe (cloud) · PVC (nhà)"], tsize=12.5, lsize=10.5)

    s.rect(612, 168, 400, 252, fill=ORANGE_T, stroke=ORANGE, sw=1.4, dash="6 4", rx=12)
    s.rich(628, 190, [("Deployment vllm", 650, INK), ("  replicas 1…N (N = 4)", 400, INK2)], size=12.5)
    pods = [("vLLM pod 1", "Ready", "API key · :8000 · /metrics"),
            ("vLLM pod 2", "Ready", "API key · :8000 · /metrics"),
            ("vLLM pod N", "Đang khởi động", "chưa nhận traffic tới khi Ready")]
    for k, (name, st, sub) in enumerate(pods):
        py = 204 + k * 70
        s.rect(628, py, 262, 58, fill=WHITE, stroke=AXIS if k < 2 else INK2, dash=None if k < 2 else "5 4", rx=9)
        s.text(642, py + 24, name, size=13.5, weight=650)
        if k < 2:
            s.status_pill(642 + text_width(name, 13.5, 650) + 10, py + 10, st, GOOD, GREEN_T)
        else:
            s.status_pill(642 + text_width(name, 13.5, 650) + 10, py + 10, st, WARN, YELLOW_T)
        s.text(642, py + 45, sub, size=11.5, fill=INK2)
        s.line(890, py + 29, 906, py + 29, stroke=GREEN, sw=1.5)
        s.gpu_chip(906, py + 10, 90, 38, f"GPU {k if k < 2 else 'N'}")

    # dải dưới: keda / monitoring / gpu-operator
    s.group(252, 496, 250, 176, "namespace: keda", fill=ORANGE_T, stroke="#f3cdb9")
    s.box(266, 532, 222, 50, "KEDA metrics server", ["chạy PromQL, trả external metric"], tsize=13)
    s.box(266, 606, 222, 50, "HPA controller", ["replicas = ceil(Σ metric ÷ target)"], tsize=13)
    s.group(522, 496, 250, 176, "namespace: monitoring", fill=VIOLET_T, stroke="#d6d1ef")
    s.box(536, 532, 222, 50, "Prometheus", ["TSDB · scrape mỗi 5 s"], tsize=13)
    s.box(536, 606, 222, 50, "Grafana · Alertmanager", ["dashboard · cảnh báo → runbook"], tsize=13)
    s.group(792, 496, 240, 176, "namespace: gpu", fill=GREEN_T, stroke="#c4dfc4")
    s.box(806, 532, 212, 50, "Device plugin", ["cấp phát nvidia.com/gpu"], tsize=13)
    s.box(806, 606, 212, 50, "Exporter GPU", ["GPU util · VRAM · nhiệt độ"], tsize=13)

    # ngoài cụm
    s.box(32, 262, 176, 78, "Client", ["người dùng nội bộ (API)", "đánh giá: máy tạo tải"])
    s.box(1084, 120, 168, 60, "Hugging Face Hub", ["tải weights lần đầu"], tsize=13)
    s.box(1084, 341, 168, 60, "Container registry", ["image vllm-openai"], tsize=13)

    # luồng request
    s.arrow([(208, 301), (272, 301)], BLUE, sw=2.2)
    s.arrow([(412, 301), (440, 301)], BLUE, sw=2.2)
    s.arrow([(580, 301), (598, 301), (598, 233), (628, 233)], BLUE, sw=2.2)
    s.arrow([(580, 301), (628, 301)], BLUE, sw=2.2)
    s.arrow([(580, 301), (598, 301), (598, 373), (628, 373)], BLUE, sw=2.2, dash="6 5")
    # nạp image / model
    s.arrow([(1084, 150), (510, 150), (510, 172)], INK2, sw=1.5, dash="3 4")
    s.arrow([(580, 200), (612, 200)], INK2, sw=1.5, dash="3 4")
    s.arrow([(1084, 371), (1012, 371)], INK2, sw=1.5, dash="3 4")
    # metric
    s.arrow([(700, 420), (700, 532)], VIOLET, sw=1.6, dash="5 4")
    s.label(708, 486, "scrape /metrics mỗi 5 s", anchor="start", bg="#fbfbfa")
    s.arrow([(806, 631), (782, 631), (782, 557), (758, 557)], VIOLET, sw=1.6, dash="5 4")
    s.arrow([(647, 582), (647, 606)], INK2, sw=1.3)
    # điều khiển scale
    s.arrow([(488, 557), (536, 557)], ORANGE, sw=2)
    s.arrow([(377, 582), (377, 606)], ORANGE, sw=2)
    s.arrow([(266, 631), (242, 631), (242, 476), (650, 476), (650, 420)], ORANGE, sw=2.2)
    s.text(446, 470, "cập nhật spec.replicas", size=11, fill=INK2, anchor="middle")
    s.save("02-kien-truc-tong-the.svg")


# ======================================================================
# Hình 3 — Vòng đời request & metric độ trễ
# ======================================================================
def fig_request():
    W, H = 1200, 470
    s = Svg(W, H, "Vòng đời một request LLM: chờ trong hàng đợi, prefill, rồi decode từng token; "
                  "TTFT tính đến token đầu, E2E tính đến token cuối")
    s.header("Vòng đời một request LLM và các metric độ trễ",
             "vLLM xử lý 2 pha: prefill (đọc prompt) rồi decode (sinh từng token); nhiều request được gộp chung batch")
    lanes = [("Máy tạo tải", "đo phía client", 100), ("vLLM scheduler", "hàng đợi · waiting", 170),
             ("vLLM engine · GPU", "đang chạy · running", 240)]
    for name, sub, y in lanes:
        s.rect(210, y, 960, 50, fill=GRAY_T, stroke=None, rx=8)
        s.text(32, y + 22, name, size=13.5, weight=650)
        s.text(32, y + 40, sub, size=11.5, fill=INK2)
    t0 = 240
    s.arrow([(t0, 138), (258, 182)], INK2, sw=1.4, r=0)
    s.rect(262, 181, 158, 28, fill=YELLOW_T, stroke="#c98500", sw=1.2, rx=5)
    s.text(341, 199.5, "chờ trong hàng đợi", size=11.5, fill=INK, anchor="middle")
    s.arrow([(420, 209), (430, 250)], INK2, sw=1.4, r=0)
    s.rect(432, 251, 108, 28, fill=BLUE_T, stroke=BLUE, sw=1.2, rx=5)
    s.text(486, 269.5, "prefill", size=11.5, weight=600, fill=INK, anchor="middle")
    ticks = [552]
    for k in range(11):
        bx = 546 + k * 44
        s.rect(bx, 251, 36, 28, fill=VIOLET_T, stroke=VIOLET, sw=1.2, rx=5)
        ticks.append(bx + 36 + 12)
    s.text(784, 309, "decode — mỗi bước sinh 1 token, chạy chung batch với request khác (continuous batching)",
           size=11.5, fill=INK2, anchor="middle")
    for k, tx in enumerate(ticks):
        s.rect(tx - 4, 116, 8, 18, fill=BLUE if k == 0 else VIOLET, stroke=None, rx=3)
    s.arrow([(540, 251), (551, 138)], BLUE, sw=1.4, r=0)
    s.arrow([(ticks[-1] - 12, 251), (ticks[-1] - 1, 138)], VIOLET, sw=1.4, r=0)
    s.text(ticks[-1] + 10, 129, "token cuối", size=11, fill=INK2)
    s.text(544, 129, "token đầu", size=11, fill=INK2, anchor="end")

    def bracket(xa, xb, y, text_):
        s.line(xa, y, xb, y, stroke=INK, sw=1.3)
        s.line(xa, y - 6, xa, y + 6, stroke=INK, sw=1.3)
        s.line(xb, y - 6, xb, y + 6, stroke=INK, sw=1.3)
        s.text((xa + xb) / 2, y - 7, text_, size=12, weight=600, anchor="middle")

    bracket(t0, 420, 350, "Queue time · chờ lập lịch")
    bracket(t0, 552, 390, "TTFT · đến token đầu tiên")
    bracket(t0, ticks[-1], 430, "E2E latency · toàn bộ phản hồi")
    s.line(ticks[3], 94, ticks[4], 94, stroke=INK, sw=1.2)
    s.line(ticks[3], 89, ticks[3], 99, stroke=INK, sw=1.2)
    s.line(ticks[4], 89, ticks[4], 99, stroke=INK, sw=1.2)
    s.text((ticks[3] + ticks[4]) / 2, 86, "ITL", size=12, weight=600, anchor="middle")
    s.line(t0, 96, t0, 440, stroke=AXIS, sw=1, dash="3 3")
    s.text(t0, 458, "gửi request", size=11, fill=INK2, anchor="middle")
    s.text(1170, 458, "TPOT ≈ (E2E − TTFT) ÷ (số token − 1)", size=12, fill=INK2, anchor="end")
    s.save("03-vong-doi-request.svg")


# ======================================================================
# Hình 4 — Vòng lặp autoscaling
# ======================================================================
def fig_loop():
    W, H = 1240, 540
    s = Svg(W, H, "Vòng lặp autoscaling gồm pha phát hiện (metric, Prometheus, KEDA, HPA) và pha thực thi "
                  "(Deployment, Scheduler, Kubelet, Readiness); cold start chiếm phần lớn độ trễ")
    s.header("Vòng lặp autoscaling và nơi phát sinh độ trễ",
             "Thời gian phản ứng = độ trễ phát hiện + độ trễ khởi động pod (cold start)")
    s.group(32, 86, 1176, 176, "PHA PHÁT HIỆN", "tổng ~10–30 s (ước lượng)", fill=VIOLET_T, stroke="#d6d1ef",
            tx=44)
    s.group(32, 318, 1176, 190, "PHA THỰC THI · cold start", "~1–8 phút nếu chưa tối ưu (ước lượng)",
            fill=ORANGE_T, stroke="#f3cdb9", tx=44)
    xs = [76, 360, 644, 928]
    bw = 250
    top = [
        ("vLLM xuất metric", ["/metrics trên mỗi pod:", "num_requests_running/waiting", "kv_cache_usage_perc"]),
        ("Prometheus scrape", ["chu kỳ scrape 5 s", "(mặc định 30 s là quá chậm)", "lưu chuỗi thời gian"]),
        ("KEDA truy vấn", ["chạy khi HPA hỏi metric", "PromQL: sum(metric) mọi pod", "→ external metrics API"]),
        ("HPA tính replicas", ["sync 15 s (k3s chỉnh được 5 s)", "ceil(Σ metric ÷ target)", "stabilization · rate limit"]),
    ]
    bottom = [
        ("Deployment cập nhật", ["spec.replicas tăng", "ReplicaSet tạo pod mới", "pod ở trạng thái Pending"]),
        ("Scheduler gán node", ["tìm node còn GPU trống", "hết GPU → Pending mãi", "(thêm node: ngoài phạm vi)"]),
        ("Kubelet khởi động", ["pull image vLLM (~10 GB)", "nạp model 7–8B (~15 GB)", "torch.compile · CUDA graph"]),
        ("Readiness probe OK", ["/health trả về 200", "pod được thêm vào", "Endpoints của Service"]),
    ]
    for i, (t, ls) in enumerate(top):
        s.step_box(xs[i], 128, bw, 112, i + 1, t, ls, VIOLET)
    for i, (t, ls) in enumerate(bottom):
        s.step_box(xs[3 - i], 356, bw, 128, i + 5, t, ls, ORANGE)
    for i in range(3):
        s.arrow([(xs[i] + bw, 184), (xs[i + 1], 184)], VIOLET, sw=1.8)
        s.arrow([(xs[3 - i], 420), (xs[2 - i] + bw, 420)], ORANGE, sw=1.8)
    s.arrow([(xs[3] + bw / 2, 240), (xs[3] + bw / 2, 356)], ORANGE, sw=1.8)
    s.label(xs[3] + bw / 2 + 10, 302, "desired > hiện tại", anchor="start", bg=SURFACE, fill=INK)
    s.arrow([(76, 430), (54, 430), (54, 184), (76, 184)], BLUE, sw=1.8)
    s.label(70, 294, "pod mới nhận traffic", anchor="start", bg=SURFACE, fill=INK)
    s.label(70, 312, "→ tải trên mỗi pod giảm", anchor="start", bg=SURFACE, fill=INK)
    s.save("04-vong-lap-autoscaling.svg")


# ======================================================================
# Hình 5 — Phân rã cold start (minh hoạ)
# ======================================================================
def fig_coldstart():
    W, H = 1120, 352
    s = Svg(W, H, "Phân rã cold start minh hoạ: pull image và tải model chiếm phần lớn; "
                  "cache model, pre-pull image và compile cache rút từ khoảng 5 phút xuống dưới 1 phút")
    s.header("Phân rã thời gian cold start của một pod vLLM",
             "Số liệu MINH HOẠ (model 7–8B, image ~10 GB) — sẽ được thay bằng kết quả đo thực tế trong đồ án")
    phases = [("Scheduling", BLUE), ("Pull image", ORANGE), ("Tải model", AQUA),
              ("Nạp weight → GPU", YELLOW), ("Compile · CUDA graph", MAGENTA), ("Probe → Ready", GREEN)]
    x = 32
    for name, c in phases:
        x = s.legend_swatch(x, 96, name, c)
    bars = [
        ("Không tối ưu", "image + model tải từ Internet", [2, 90, 150, 25, 45, 10]),
        ("Cache model trên PVC", "image vẫn phải pull", [2, 90, 0, 60, 45, 10]),
        ("Tối ưu đầy đủ", "pre-pull · NVMe cục bộ · compile cache", [2, 0, 0, 20, 15, 6]),
    ]
    x0, scale, top = 320, 2.0, 138
    for v in range(0, 351, 50):
        gx = x0 + v * scale
        s.line(gx, top - 12, gx, top + 3 * 64 - 20, stroke=GRID)
        s.text(gx, top + 3 * 64 - 2, f"{v} s", size=11, fill=MUTED, anchor="middle")
    for i, (name, sub, vals) in enumerate(bars):
        y = top + i * 64
        s.text(x0 - 16, y + 12, name, size=13, weight=650, anchor="end")
        s.text(x0 - 16, y + 29, sub, size=11, fill=INK2, anchor="end")
        cx = x0
        nz = [k for k, v in enumerate(vals) if v > 0]
        for k, v in enumerate(vals):
            if v == 0:
                continue
            w = v * scale
            color = phases[k][1]
            dw = max(w - 2, 1.5)
            if k == nz[-1]:
                r = 4
                s.add(f'<path d="M{f(cx)},{f(y)} h{f(dw - r)} q{r},0 {r},{r} v{f(28 - 2 * r)} '
                      f'q0,{r} -{r},{r} h-{f(dw - r)} z" fill="{color}"/>')
            else:
                s.rect(cx, y, dw, 28, fill=color, stroke=None, rx=0)
            if w >= 34:
                s.text(cx + dw / 2, y + 43, f"{v} s", size=10.5, fill=INK2, anchor="middle")
            cx += w
        total = sum(vals)
        s.rich(cx + 10, y + 19, [(f"{total} s", 700, INK), (f"  ≈ {total / 60:.1f} phút".replace(".", ","), 400, INK2)],
               size=12.5)
    s.save("05-cold-start.svg")


# ======================================================================
# Hình 7 — Vận hành theo SLO: metric → cảnh báo → runbook
# ======================================================================
def fig_slo_alert():
    W, H = 1240, 578
    s = Svg(W, H, "Vận hành theo SLO: Prometheus tính SLI từ metric của vLLM, Traefik, kube-state-metrics và GPU; "
                  "cảnh báo theo burn rate qua Alertmanager tới người trực; người trực làm theo runbook; "
                  "mọi thay đổi đi qua Git và Argo CD")
    s.header("Vận hành theo SLO: từ metric tới cảnh báo và hành động",
             "Mỗi cảnh báo trả lời ba câu: người dùng có bị ảnh hưởng không, gấp tới đâu, và làm gì tiếp theo")
    x = 32
    x = s.legend_line(x, 88, "Metric", VIOLET, dash="5 4")
    x = s.legend_line(x, 88, "Cảnh báo", ORANGE, sw=2)
    s.legend_line(x, 88, "Xử lý và thay đổi", BLUE, sw=2)
    for xx, lab in ((32, "NGUỒN SLI"), (300, "PROMETHEUS"), (608, "ALERTMANAGER"), (906, "XỬ LÝ")):
        s.text(xx, 122, lab, size=12, weight=700, fill=INK2)

    srcs = [("vLLM /metrics", "TTFT, TPOT, hàng đợi"),
            ("Traefik", "số request, mã lỗi 5xx"),
            ("kube-state-metrics", "replicas, pod, HPA"),
            ("DCGM · KEDA", "nhiệt độ, XID, lỗi scaler")]
    for k, (t, ln) in enumerate(srcs):
        y = 134 + k * 66
        s.box(32, y, 220, 54, t, [ln], tsize=13, align="start")
        s.arrow([(252, y + 27), (300, y + 27)], VIOLET, sw=1.5, dash="5 4")

    s.rect(300, 134, 260, 252, fill=VIOLET_T, stroke="#d6d1ef", rx=12)
    s.box(316, 150, 228, 92, "Recording rule", ["tỷ lệ request xấu", "theo cửa sổ 1, 5, 30 phút"], tsize=13)
    s.box(316, 278, 228, 92, "Alert rule", ["burn rate · năng lực · nền tảng", "có unit test (promtool)"], tsize=13)
    s.arrow([(430, 242), (430, 278)], INK2, sw=1.5)

    s.rect(608, 134, 250, 252, fill=ORANGE_T, stroke="#f3cdb9", rx=12)
    s.box(624, 150, 218, 92, "page", ["người dùng đang bị ảnh hưởng", "→ Telegram của người trực"], tsize=13,
          stroke=CRIT)
    s.box(624, 278, 218, 92, "ticket", ["xử lý trong giờ làm việc", "→ Telegram, không nhắc lại"], tsize=13, stroke=WARN)
    s.text(733, 264, "gom nhóm · chặn trùng · silence", size=11, fill=INK2, anchor="middle")
    s.arrow([(544, 312), (584, 312), (584, 196), (624, 196)], ORANGE, sw=2)
    s.arrow([(544, 336), (624, 336)], ORANGE, sw=2)

    s.box(906, 134, 302, 62, "Người trực", ["mở runbook từ link trong cảnh báo"], tsize=13)
    s.box(906, 222, 302, 76, "Runbook", ["docs/runbooks/<cảnh báo>.md:", "ý nghĩa · chẩn đoán · xử lý · leo thang"],
          tsize=13)
    s.box(906, 322, 302, 64, "Hành động", ["chờ pod Ready · thắt giới hạn tốc độ", "xoá pod · rollback bằng git revert"],
          tsize=13)
    s.arrow([(842, 180), (874, 180), (874, 156), (906, 156)], ORANGE, sw=2)
    s.arrow([(842, 324), (888, 324), (888, 176), (906, 176)], ORANGE, sw=2)
    s.arrow([(1057, 196), (1057, 222)], BLUE, sw=1.8)
    s.arrow([(1057, 298), (1057, 322)], BLUE, sw=1.8)
    s.arrow([(1057, 386), (1057, 432)], BLUE, sw=1.8)

    s.box(32, 432, 1176, 64, "Git + Argo CD",
          ["mọi thay đổi để xử lý đi qua PR: rollback, đổi ngưỡng cảnh báo, sửa runbook · "
           "sau sự cố: ghi nhật ký vận hành"], tsize=13, align="start", fill=BLUE_T, stroke="#c9dcf3")
    s.arrow([(430, 432), (430, 386)], BLUE, sw=1.6, dash="5 4")
    s.label(440, 414, "đổi ngưỡng, sửa quy tắc", anchor="start")
    s.rich(32, 528, [("Ví dụ · LLMSLOBurnFast: ", 650, INK),
                     ("hơn 20% request chờ token đầu quá ngưỡng trên cả 5 phút và 1 phút → page → Telegram",
                      400, INK2)], size=12)
    s.rich(32, 552, [("Runbook: ", 650, INK),
                     ("đang cold start? đã chạy tối đa replica? vừa cập nhật? → chờ pod Ready · thắt giới hạn tốc độ · "
                      "git revert", 400, INK2)], size=12)
    s.save("07-slo-canh-bao-runbook.svg")


# ======================================================================
# Hình 8 — Ba kịch bản tải
# ======================================================================
def scenario(k, t):
    if k == 1:
        return 0.5 if t <= 20 else None
    if k == 2:
        return (0.5 + 2.5 * smooth((t - 5) / 0.5) - 2.5 * smooth((t - 15) / 0.5)) if t <= 25 else None
    return (0.5 + 2.5 * smooth(t / 5)) if t <= 25 else None


def fig_scenarios():
    W, H = 1200, 528
    s = Svg(W, H, "Ba kịch bản tải theo đề cương: thấp ổn định, tăng đột ngột rồi giảm, cao kéo dài; "
                  "trục tung tính theo C là năng lực 1 replica")
    s.header("Ba kịch bản tải theo đề cương",
             "Tốc độ gửi request λ(t), đơn vị C = năng lực tối đa của 1 replica mà vẫn đạt SLO (đo ở bước đo năng lực)")
    meta = [
        (1, "KB1 · Thấp, ổn định", "20 phút", [(10, 0.5, "như ban đêm: 1 replica là đủ")]),
        (2, "KB2 · Tăng đột ngột rồi giảm", "25 phút",
         [(10, 3.0, "0,5C → 3C trong 30 s"), (22.5, 0.5, "về 0,5C: scale-down")]),
        (3, "KB3 · Cao, kéo dài", "25 phút", [(15, 3.0, "giữ 3C = 0,75 × N × C")]),
    ]
    pw, ph = 300, 168
    ymax = 4.6
    s.add(f'<line x1="32" y1="90" x2="58" y2="90" stroke="{MUTED}" stroke-width="1.1" stroke-dasharray="4 4"/>')
    s.text(66, 94, "đường tham chiếu: 1C = năng lực 1 replica · 4C = năng lực tối đa (N = 4 replica)",
           size=12, fill=INK2)
    for col, (k, title, dur, notes) in enumerate(meta):
        x0 = 76 + col * 384
        top = 138
        y1 = top + ph
        X = lambda t, x0=x0: x0 + t / 30 * pw
        Y = lambda v, y1=y1: y1 - v / ymax * ph
        s.text(x0 - 40, top - 14, title, size=13.5, weight=650)
        s.text(x0 + pw, top - 14, dur, size=11.5, fill=INK2, anchor="end")
        for v in range(1, 5):
            s.line(x0, Y(v), x0 + pw, Y(v), stroke=GRID)
        for v in range(0, 5):
            s.text(x0 - 8, Y(v) + 4, "0" if v == 0 else f"{v}C", size=11, fill=MUTED, anchor="end")
        for t in (0, 10, 20, 30):
            s.text(X(t), y1 + 17, str(t), size=11, fill=MUTED, anchor="middle")
        s.text(x0 + pw, y1 + 33, "phút", size=11, fill=MUTED, anchor="end")
        s.line(x0, Y(1), x0 + pw, Y(1), stroke=MUTED, sw=1.1, dash="4 4")
        s.line(x0, Y(4), x0 + pw, Y(4), stroke=MUTED, sw=1.1, dash="4 4")
        pts = []
        for i in range(0, 301):
            t = i * 0.1
            v = scenario(k, t)
            if v is None:
                break
            pts.append((X(t), Y(v)))
        s.polygon([(pts[0][0], y1)] + pts + [(pts[-1][0], y1)], fill="#cde2fb", opacity=0.55)
        s.polyline(pts, BLUE, sw=2.2)
        s.line(x0, y1, x0 + pw, y1, stroke=AXIS)
        for at, av, note in notes:
            lab_y = Y(av) - 10 if av < 3.4 else Y(av) + 18
            s.label(X(at), lab_y, note, size=11, fill=INK)
    ny = 360
    s.rect(32, ny, 1136, 140, fill=WHITE, stroke=AXIS, rx=10)
    s.text(48, ny + 28, "Cách sinh tải", size=13.5, weight=650)
    for i, ln in enumerate(["• Open-loop: request đến theo quá trình Poisson với tốc độ λ(t),",
                            "  không chờ request trước xong.",
                            "• Seed cố định: mọi cấu hình nhận đúng cùng một chuỗi request.",
                            "• Prompt 256–1024 token, output cố định 256 token, có streaming."]):
        s.text(48, ny + 54 + i * 20, ln, size=12, fill=INK2)
    s.text(608, ny + 28, "Mỗi kịch bản kiểm chứng gì", size=13.5, weight=650)
    for i, ln in enumerate(["• KB1 (như ban đêm): A2 giữ 1 replica mà vẫn đạt SLO? (N1, N3)",
                            "• KB2 (như 9 giờ sáng): phản ứng mất bao lâu? scale-down có lỗi? (N2, N4)",
                            "• KB3 (cao điểm kéo dài): ổn định ở tối đa replica? cảnh báo đúng? (N1, N7)"]):
        s.text(608, ny + 54 + i * 20, ln, size=12, fill=INK2)
    s.save("08-kich-ban-tai.svg")


# ======================================================================
# Hình 6 — Hai tầng môi trường
# ======================================================================
def fig_envs():
    W, H = 1240, 578
    s = Svg(W, H, "Hai tầng môi trường: máy nhà và simulator để xây dựng và vận hành thử, VM 4 GPU thuê theo giờ "
                  "để đánh giá; cả hai triển khai từ cùng một Git repository")
    s.header("Hai tầng môi trường: xây dựng và vận hành thử ở nhà, đánh giá trên GPU thuê",
             "Cùng một bộ manifest trong Git; mỗi môi trường chỉ khác overlay (model, số replica, tài nguyên)")
    gx, gy, gw, gh = 400, 86, 440, 142
    s.rect(gx, gy, gw, gh, fill=WHITE, stroke=INK2, sw=1.4, rx=12)
    s.rich(gx + 16, gy + 26, [("Git repository", 650, INK), ("  nguồn sự thật duy nhất", 400, INK2)], size=13.5)
    rows = [("serving/base/", "Deployment vLLM, Service, probes"),
            ("serving/overlays/", "home (1,5B) · cloud (7B)"),
            ("autoscaling/", "official: A2 · eval: S1, S4, A1"),
            ("observability/", "dashboard, cảnh báo, runbook"),
            ("infra/", "script vastai + Ansible")]
    for i, (p, d) in enumerate(rows):
        y = gy + 50 + i * 18.5
        s.text(gx + 16, y, p, size=11.5, fill=INK, family=MONO)
        s.text(gx + 206, y, d, size=11.5, fill=INK2)

    # tầng 1
    s.rect(32, 290, 580, 262, fill=GRAY_T, stroke=AXIS, rx=14)
    s.text(50, 318, "Tầng 1 · Xây dựng & vận hành thử", size=14.5, weight=700)
    s.text(50, 338, "Máy nhà + simulator · chi phí ≈ 0 · không dùng số liệu hiệu năng", size=12, fill=INK2)
    nodes = [("PC", "k3s server", "RTX 5060 · 8 GB", None), ("Laptop", "k3s agent (nếu có)", "RTX 4050 · 6 GB", "5 4"),
             ("Máy không GPU", "kind + simulator", None, None)]
    for i, (n, sub, chip, dash) in enumerate(nodes):
        bx = 52 + i * 188
        s.rect(bx, 354, 168, 112, fill=WHITE, stroke=AXIS if not dash else INK2, dash=dash, rx=10)
        s.text(bx + 14, 378, n, size=13.5, weight=650)
        s.text(bx + 14, 396, sub, size=11.5, fill=INK2)
        if chip:
            s.gpu_chip(bx + 14, 418, 140, 32, chip)
        else:
            s.rect(bx + 14, 418, 140, 32, fill=BLUE_T, stroke="#c9dcf3", sw=1.2, rx=5)
            s.text(bx + 84, 438.5, "llm-d-inference-sim", size=11, weight=600, fill=INK, anchor="middle")
    for i, ln in enumerate(["Ubuntu server · k3s (Ansible) · device plugin · vLLM + Qwen2.5-1.5B",
                            "Dùng cho: phát triển, kiểm thử chức năng, kịch bản vận hành",
                            "Simulator: scale 1 → 3, A4, drain node; truy cập cluster nhà qua Tailscale"]):
        s.text(52, 496 + i * 22, ln, size=12, fill=INK2)

    # tầng 2
    s.rect(628, 290, 580, 262, fill=GRAY_T, stroke=AXIS, rx=14)
    s.text(646, 318, "Tầng 2 · Đánh giá trên GPU thật", size=14.5, weight=700)
    s.text(646, 338, "Vast.ai chế độ VM · thuê trọn máy · một lần thuê liền cuối tuần (~20–22 giờ)",
           size=12, fill=INK2)
    s.rect(648, 354, 540, 112, fill=WHITE, stroke=AXIS, rx=10)
    s.text(662, 378, "VM 4 GPU · k3s single-node", size=13.5, weight=650)
    s.text(662, 396, "4× RTX 4090 24 GB · CPU manager static", size=11.5, fill=INK2)
    for i in range(4):
        s.gpu_chip(662 + i * 81, 418, 72, 32, f"GPU {i}")
    s.box(1000, 368, 176, 86, "Máy tạo tải + runner", ["lõi CPU riêng", "không qua mạng ngoài"],
          align="start", tsize=12.5, fill=BLUE_T, stroke="#c9dcf3")
    s.arrow([(1000, 434), (984, 434)], BLUE, sw=2, r=0)
    for i, ln in enumerate(["Qwen2.5-7B-Instruct · ghim digest của vLLM và image",
                            "Dùng cho: đo năng lực, ma trận 17 lượt, cold start, kịch bản vận hành",
                            "Dữ liệu đẩy lên R2 sau mỗi lượt; huỷ instance ngay khi xong"]):
        s.text(648, 496 + i * 22, ln, size=12, fill=INK2)

    s.arrow([(520, 228), (520, 258), (322, 258), (322, 290)], INK2, sw=1.6)
    s.label(421, 252, "Argo CD sync · overlays/home", fill=INK)
    s.arrow([(720, 228), (720, 258), (918, 258), (918, 290)], INK2, sw=1.6)
    s.label(868, 252, "thuê VM (vastai) → Ansible → Argo CD · overlays/cloud", fill=INK)
    s.save("06-moi-truong-trien-khai.svg")


# ======================================================================
# Hình 9 — Kế hoạch đến hạn nộp
# ======================================================================
PLAN_COLORS = {"build": BLUE, "rent": ORANGE, "write": AQUA, "gate": VIOLET}


def fig_gantt():
    phases = [
        ("Chuẩn bị", [
            ("Gửi GVHD; thử vLLM trên 5060; simulator", "gate", 1, 1),
            ("Tìm offer Vast; chốt cloud (18/10)", "gate", 1, 2)]),
        ("Xây dựng và vận hành thử (nhà + simulator)", [
            ("k3s, Argo CD, giám sát, CI; ghim phiên bản", "build", 2, 2),
            ("Autoscaling A1, A2; graceful shutdown", "build", 2, 3),
            ("SLO, 6 cảnh báo, 3 dashboard, máy tạo tải", "build", 3, 3),
            ("Rolling update, L2, runbook, runner", "build", 4, 4),
            ("VH3, VH4 ở nhà; script VH5", "build", 5, 5)]),
        ("Phiên thuê GPU (cuối tuần)", [
            ("V0 smoke · 1 GPU", "rent", 2, 2),
            ("V1 phát triển · 1 GPU", "rent", 4, 4),
            ("V2 đánh giá chính · 4 GPU, ~20–22 giờ", "rent", 5, 5),
            ("V3 dự phòng (chỉ khi cần)", "rent", 6, 6)]),
        ("Phân tích và viết", [
            ("Viết chương 2–4", "write", 5, 7),
            ("Phân tích; chương 5; bảng nghiệm thu", "write", 6, 7),
            ("Chương 1, 6; rà bản thảo; slide", "write", 8, 8),
            ("Sửa theo GVHD; nộp", "write", 9, 9)]),
    ]
    weeks = ["08/10", "12/10", "19/10", "26/10", "02/11", "09/11", "16/11", "23/11", "30/11"]
    rows = sum(1 + len(t) for _, t in phases)
    rh, top = 27, 146
    H = top + rows * rh + 92
    W = 1240
    s = Svg(W, H, "Kế hoạch 9 tuần đến hạn nộp khoảng 08/12/2026: xây dựng và vận hành thử ở nhà W1–W4, "
                  "đánh giá trong một lần thuê liền ở W5, đóng băng dữ liệu 15/11, viết luận văn tới W9")
    s.header("Kế hoạch đến hạn nộp (9 tuần)",
             "Màu thanh = loại việc; dải tuần là thứ Hai đầu tuần; ◆ = mốc kiểm tra với giảng viên hướng dẫn")
    x = 32
    for k, desc in (("gate", "Chuẩn bị, quyết định"), ("build", "Xây dựng, vận hành thử"),
                    ("rent", "Phiên thuê GPU"), ("write", "Phân tích, viết")):
        x = s.legend_swatch(x, 92, desc, PLAN_COLORS[k])
    gx0, ww = 432, 80
    gy1 = top + rows * rh
    for wk in range(9):
        cx = gx0 + wk * ww
        if wk % 2 == 0:
            s.rect(cx, top - 4, ww, rows * rh + 8, fill="#f6f5f2", stroke=None, rx=0)
        s.text(cx + ww / 2, top - 26, f"W{wk + 1}", size=11.5, fill=INK2, anchor="middle", weight=600)
        s.text(cx + ww / 2, top - 11, weeks[wk], size=10.5, fill=MUTED, anchor="middle")
    y = top
    for pname, tasks in phases:
        s.text(32, y + 18, pname, size=12.5, weight=700)
        y += rh
        for name, kind, a, b in tasks:
            s.text(48, y + 18, name, size=12, fill=INK)
            bx = gx0 + (a - 1) * ww + 3
            bw = (b - a + 1) * ww - 6
            s.rect(bx, y + 7, bw, 14, fill=PLAN_COLORS[kind], stroke=None, rx=4)
            y += rh
    miles = [(2, "M1 · 18/10", 0), (4, "M2 · 01/11", 0), (6, "M3 · đóng băng 15/11", 0),
             (8, "M4 · bản thảo 29/11", 1), (9, "M5 · nộp 07–08/12", 0)]
    for wk, lab, lvl in miles:
        mx = gx0 + wk * ww
        s.line(mx, top - 4, mx, gy1 + 14, stroke=INK2, sw=1, dash="3 3")
        my = gy1 + 20
        s.polygon([(mx, my - 7), (mx + 7, my), (mx, my + 7), (mx - 7, my)], fill=INK)
        anchor = "end" if wk == 9 else "middle"
        s.text(mx + (4 if wk == 9 else 0), my + 26 + lvl * 20, lab, size=11.5, weight=600, anchor=anchor)
    s.save("09-ke-hoach.svg")


if __name__ == "__main__":
    import chuyen_sau
    chuyen_sau.build_all()
    fig_tradeoff()
    fig_architecture()
    fig_request()
    fig_loop()
    fig_coldstart()
    fig_envs()
    fig_slo_alert()
    fig_scenarios()
    fig_gantt()
