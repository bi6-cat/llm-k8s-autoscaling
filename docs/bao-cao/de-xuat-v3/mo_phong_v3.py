# ──────────────────────────────────────────────────────────────────────────────
# docs/bao-cao/de-xuat-v3/mo_phong_v3.py
# Khái niệm: Mô phỏng (KHÔNG phải số đo) vòng autoscaling, dựa trên mo_phong.py của báo cáo kỹ thuật.
# Mục đích:  Ước lượng lợi ích các nâng cấp trong tờ trình V3: định tuyến theo tải (jsq), autoscaling dự báo
#            bằng hồi quy tuyến tính 120 s + ngưỡng chết (pred, dead), chặn quá tải mỗi pod (shed), pool pod
#            ngủ sẵn (warm), và kịch bản quá tải (kbn > N). Sửa lỗi của bản cũ: metric lưu vào lịch sử là
#            giá trị THÔ, không phải giá trị đã ngoại suy (bản cũ tạo vòng phản hồi dương).
# Chạy:      python3 mo_phong_v3.py <repo> ket-qua-mo-phong.json   (~15 phút, 5 seed mỗi biến thể)
# ──────────────────────────────────────────────────────────────────────────────
"""Mô phỏng ma trận V2 (S1, S4, A1, A2 × KB1–KB3) cho báo cáo, hiệu chỉnh bằng số đo 08/11 trên 4 × A4000.

Đây là MÔ HÌNH, không phải số đo. Tham số lấy từ đo thật:
  - TPOT theo số request đang chạy n (ĐG1 08/11, B = λ × E2E): TPOT ≈ 18,5 + 0,49·n ms → C ≈ 4,5–5 req/s.
  - mỗi pod tối đa 64 request chạy (--max-num-seqs), hàng đợi FIFO nằm trong pod;
  - request mới chia ngẫu nhiên cho pod Ready (Service của Kubernetes), không chuyển hàng đợi giữa pod;
  - máy tạo tải huỷ request quá 120 s; output 256 token; SLO: TTFT ≤ 2,5 s và TPOT ≤ 100 ms;
  - cold start 110 s từ lúc HPA tăng tới lúc pod Ready (V1 đo được 105–120 s);
  - A2: desired = ⌈(chạy + chờ) ÷ 42⌉; A1: desired = ⌈Σ GPU util ÷ 70⌉, pod có ≥ 1 request coi là 100 %;
  - HPA mỗi 15 s, metric trễ 5 s (scrape + poll của KEDA đều 5 s); tăng ngay; giảm theo cửa sổ 300 s, mỗi 60 s bớt 1 pod;
  - pod bị tắt giữ GPU thêm 180 s (ADR-006 C8), tính vào GPU-giờ.
"""
from __future__ import annotations

import heapq
import json
import math
import random
import sys

sys.path.insert(0, sys.argv[1])
from loadgen import scenarios  # noqa: E402

C, N, A2_T, A1_T = 4.5, 4, 42, 70
COLD, GRACE, TIMEOUT, OUT_TOK, MAXSEQ = 110.0, 180.0, 120.0, 256, 64
LAG = 5.0
DT = 0.1


def tpot(n: int) -> float:
    return (18.5 + 0.49 * n) / 1000


class Pod:
    def __init__(self, ready_at: float, born: float):
        self.ready_at, self.born, self.dead_at = ready_at, born, None
        self.v = 0.0            # đồng hồ token ảo: mọi request đang chạy tiến cùng tốc độ
        self.run: list = []     # heap (v_kết_thúc, id)
        self.q: list = []       # hàng đợi FIFO: (t_đến, id)
        self.qh = 0

    def ready(self, t):
        return self.dead_at is None and t >= self.ready_at


def simulate(cfg: str, kb: str, seed: int, cold: float = COLD, jsq: bool = False, pred: bool = False, dead: float = 0.0,
             shed: int | None = None, warm: int = 0, kbn: float | None = None):
    """jsq: định tuyến tới pod ít việc nhất thay vì ngẫu nhiên. pred: A2 dự báo (ngoại suy xu hướng metric
    thêm `cold` giây để pod mới kịp Ready lúc tải tới)."""
    sc = {"KB1": scenarios.kb1(C), "KB2": scenarios.kb2(C, kbn or N), "KB3": scenarios.kb3(C, kbn or N)}[kb]
    rejected = 0
    pod_slope = [0.0]
    woken = 0
    rng = random.Random(seed)
    fixed = {"S1": 1, "S4": N}.get(cfg)
    pods = [Pod(0.0, -1e9) for _ in range(fixed or 1)]  # trạng thái đầu: đã Ready (runner reset trước lượt)
    reqs = {}   # id → [t_đến, t_first, tpot, ok]
    hist = []   # (t, desired) cho cửa sổ scale-down
    metric_log = []  # (t, giá trị metric) để mô phỏng trễ 10 s
    last_down = -1e9
    desired = len(pods)
    nid = 0
    t_end = sc.duration_s + 600
    series = []
    t = 0.0
    next_hpa = 0.0
    while t < t_end:
        # 1) request đến (Poisson theo λ(t))
        lam = sc.rate(t) if t < sc.duration_s else 0.0
        k = 0
        x = lam * DT
        # số request trong DT ~ Poisson(x)
        L, p, k = math.exp(-x), 1.0, -1
        while p > L:
            p *= rng.random(); k += 1
        rp = [p_ for p_ in pods if p_.ready(t)]
        for _ in range(k):
            if jsq and rp:
                pod = min(rp, key=lambda p_: len(p_.run) + len(p_.q) - p_.qh)
            else:
                pod = rng.choice(rp) if rp else rng.choice([p_ for p_ in pods if p_.dead_at is None])
            reqs[nid] = [t, None, None, False]
            if shed is not None and pod.ready(t) and len(pod.run) + len(pod.q) - pod.qh >= shed:
                rejected += 1; nid += 1
                continue
            pod.q.append((t, nid)); nid += 1
        # 2) mỗi pod: nhận request từ hàng đợi, tiến token, trả request xong
        for pod in pods:
            if not pod.ready(t) and pod.dead_at is None:
                continue
            # huỷ request quá hạn trong hàng đợi
            while pod.qh < len(pod.q) and t - pod.q[pod.qh][0] > TIMEOUT:
                pod.qh += 1
            while len(pod.run) < MAXSEQ and pod.qh < len(pod.q):
                ta, i = pod.q[pod.qh]; pod.qh += 1
                ttft = (t - ta) + 0.1 + 0.006 * len(pod.run)
                reqs[i][1] = ttft
                heapq.heappush(pod.run, (pod.v + OUT_TOK, i))
            if pod.run:
                tp = tpot(len(pod.run))
                pod.v += DT / tp
                while pod.run and pod.run[0][0] <= pod.v:
                    _, i = heapq.heappop(pod.run)
                    r = reqs[i]; r[2] = tp
                    r[3] = r[1] <= 2.5 and tp <= 0.1 and (t - r[0]) <= TIMEOUT
        # 3) metric (được scrape) và HPA mỗi 15 s
        live = [p_ for p_ in pods if p_.ready(t)]
        if cfg == "A2":
            m = sum(len(p_.run) + len(p_.q) - p_.qh for p_ in live)
            m_raw = m
            if pred:
                # hồi quy bình phương tối thiểu trên 120 s gần nhất, lấy mẫu mỗi 1 s (như predict_linear)
                if int(t / DT) % 10 == 0:
                    pts = [(tt, mm) for (tt, _, mm) in metric_log[-1200::10]]
                    if len(pts) > 20:
                        mt = sum(a for a, _ in pts) / len(pts); mv = sum(b for _, b in pts) / len(pts)
                        den = sum((a - mt) ** 2 for a, _ in pts)
                        pod_slope[0] = sum((a - mt) * (b - mv) for a, b in pts) / den if den else 0.0
                slope = pod_slope[0]
                ext = max(0.0, slope) * cold
                m = m + (ext if ext > dead else 0.0)
            want = math.ceil(m / A2_T)
        elif cfg == "A1":
            m = sum(100 for p_ in live if p_.run)
            want = math.ceil(m / A1_T)
        else:
            want = fixed
        metric_log.append((t, want, (m_raw if cfg == 'A2' else m) if cfg in ('A1', 'A2') else 0))
        if fixed is None and t >= next_hpa:
            next_hpa += 15
            seen = [w for (tt, w, _) in metric_log if tt <= t - LAG]
            raw = max(1, min(N, seen[-1] if seen else 1))
            hist.append((t, raw))
            cur = sum(1 for p_ in pods if p_.dead_at is None)
            if raw > cur:
                for _ in range(raw - cur):
                    fast = sum(1 for p_ in pods if p_.dead_at is None) < 1 + warm
                    pods.append(Pod(t + (5.0 if fast else cold), t))
                desired = raw
            else:
                rec = max(w for (tt, w) in hist if tt >= t - 300)
                if rec < cur and t - last_down >= 60:
                    # tắt pod mới nhất (HPA xoá pod theo thứ tự ReplicaSet: pod chưa Ready / trẻ nhất trước)
                    victim = max((p_ for p_ in pods if p_.dead_at is None), key=lambda p_: p_.born)
                    victim.dead_at = t
                    # request đang chờ trong pod bị tắt: theo graceful shutdown, pod vẫn làm nốt (grace 180 s)
                    last_down = t
                    desired = cur - 1
                else:
                    desired = cur
        # pod đã tắt vẫn phục vụ nốt request trong grace period rồi mất
        for p_ in pods:
            if p_.dead_at is not None and t - p_.dead_at >= GRACE:
                for _, i in p_.run:
                    reqs[i][3] = False
                p_.run = []; p_.q = p_.q[:p_.qh]
        if int(t / DT) % 50 == 0:
            series.append({"t": round(t), "desired": desired,
                           "ready": sum(1 for p_ in pods if p_.ready(t)),
                           "lam": round(lam, 2)})
        t += DT
    # tổng hợp
    ok = sum(1 for r in reqs.values() if r[3]); n = len(reqs)
    gpu_s = 0.0
    for p_ in pods:
        start = max(0.0, p_.born)
        # GPU-giờ tính trong đúng thời lượng lượt [0, duration), như S1/S4; pod bị tắt trong lượt
        # vẫn giữ GPU thêm GRACE giây (nhưng không vượt quá cuối lượt).
        end = min(sc.duration_s, (p_.dead_at + GRACE) if p_.dead_at is not None else sc.duration_s)
        gpu_s += max(0.0, end - start)
    # pod ngủ (warm pool) giữ GPU suốt lượt: cộng phần GPU chờ chưa được dùng
    if warm and fixed is None:
        idle = 0.0
        for k in range(int(sc.duration_s)):
            act = sum(1 for p_ in pods if p_.born <= k and (p_.dead_at is None or k < p_.dead_at + GRACE))
            idle += max(0, min(N, 1 + warm) - act)
        gpu_s += idle
    # SLO theo pha
    phase = {}
    for name, (a, b) in sc.phases.items():
        sel = [r for r in reqs.values() if a <= r[0] < b]
        phase[name] = round(sum(r[3] for r in sel) / len(sel), 4) if sel else None
    adm = n - rejected
    return {"slo": round(ok / n, 4), "n": n, "rej": round(rejected / n, 4), "slo_adm": round(ok / adm, 4) if adm else 0, "gpu_h": round(gpu_s / 3600, 3), "phase": phase,
            "series": series}


if __name__ == "__main__":
    out = {}
    def run(key, cfg, kb, **kw):
        rs = [simulate(cfg, kb, seed, **kw) for seed in range(5)]
        avg = lambda k: round(sum(r[k] for r in rs) / len(rs), 4)
        o = {k: avg(k) for k in ("slo", "gpu_h", "rej", "slo_adm")}
        o["slo_min"] = min(r["slo"] for r in rs); o["slo_max"] = max(r["slo"] for r in rs)
        out[key] = o
        print(f"{key:28s} SLO(all) {o['slo']:.1%} [{o['slo_min']:.1%}-{o['slo_max']:.1%}]  adm {o['slo_adm']:.1%}  rej {o['rej']:.1%}  GPU-h {o['gpu_h']:.2f}", flush=True)
    for kb in ("KB1","KB2","KB3"):
        run(f"A2-{kb}", "A2", kb)
        run(f"A2jsq-{kb}", "A2", kb, jsq=True)
        run(f"A3-{kb}", "A2", kb, pred=True, dead=10)
        run(f"A3jsq-{kb}", "A2", kb, pred=True, dead=10, jsq=True)
        run(f"A3jsqshed-{kb}", "A2", kb, pred=True, dead=10, jsq=True, shed=75)
    for tag,kbn in (("4C",16/3),("5C",20/3)):
        run(f"S4-{tag}", "S4", "KB3", kbn=kbn)
        run(f"S4shed-{tag}", "S4", "KB3", kbn=kbn, shed=75)
        run(f"A2-{tag}", "A2", "KB3", kbn=kbn)
        run(f"A2shed-{tag}", "A2", "KB3", kbn=kbn, shed=75)
        run(f"A3jsqshed-{tag}", "A2", "KB3", kbn=kbn, pred=True, dead=10, jsq=True, shed=75)
    json.dump(out, open(sys.argv[2], "w"), indent=1)
