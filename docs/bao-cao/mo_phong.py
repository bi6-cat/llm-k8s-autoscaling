"""Mô phỏng ma trận V2 (S1, S4, A1, A2 × KB1–KB3) và các bản A2 cải tiến, cho báo cáo kỹ thuật.

Khái niệm: Mô phỏng theo bước thời gian 0,1 s: request đến theo Poisson với λ(t) lấy thẳng từ
           loadgen.scenarios; mỗi pod là một hàng đợi có tối đa 64 request chạy; HPA và KEDA mô phỏng
           theo tham số thật. Hiệu chỉnh bằng 2 lượt V1 (lệch ≤ 9 điểm SLO, xem mục 08 của báo cáo).
Mục đích:  Ước lượng các ô ma trận chưa chạy (mục 08) và định lượng hướng nâng cấp (mục 10). Đây là
           MÔ HÌNH, không phải số đo; V2 thay thế. Dùng: python3 docs/bao-cao/mo_phong.py . /tmp/sim.json

Tham số lấy từ đo thật: Tham số lấy từ đo thật:
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


def simulate(cfg: str, kb: str, seed: int, cold: float = COLD, jsq: bool = False, pred: bool = False):
    """jsq: định tuyến tới pod ít việc nhất thay vì ngẫu nhiên. pred: A2 dự báo (ngoại suy xu hướng metric
    thêm `cold` giây để pod mới kịp Ready lúc tải tới)."""
    sc = {"KB1": scenarios.kb1(C), "KB2": scenarios.kb2(C, N), "KB3": scenarios.kb3(C, N)}[kb]
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
            if pred:
                old = [mm for (tt, _, mm) in metric_log if t - 30 <= tt <= t - 25]
                slope = (m - old[0]) / 30 if old else 0.0
                m = m + max(0.0, slope) * cold
            want = math.ceil(m / A2_T)
        elif cfg == "A1":
            m = sum(100 for p_ in live if p_.run)
            want = math.ceil(m / A1_T)
        else:
            want = fixed
        metric_log.append((t, want, m if cfg in ('A1', 'A2') else 0))
        if fixed is None and t >= next_hpa:
            next_hpa += 15
            seen = [w for (tt, w, _) in metric_log if tt <= t - LAG]
            raw = max(1, min(N, seen[-1] if seen else 1))
            hist.append((t, raw))
            cur = sum(1 for p_ in pods if p_.dead_at is None)
            if raw > cur:
                for _ in range(raw - cur):
                    pods.append(Pod(t + cold, t))
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
    # SLO theo pha
    phase = {}
    for name, (a, b) in sc.phases.items():
        sel = [r for r in reqs.values() if a <= r[0] < b]
        phase[name] = round(sum(r[3] for r in sel) / len(sel), 4) if sel else None
    return {"slo": round(ok / n, 4), "n": n, "gpu_h": round(gpu_s / 3600, 3), "phase": phase,
            "series": series}


if __name__ == "__main__":
    out = {}

    def run(key, cfg, kb, **kw):
        rs = [simulate(cfg, kb, seed, **kw) for seed in range(5)]
        avg = lambda k: round(sum(r[k] for r in rs) / len(rs), 4)
        ph = {name: round(sum(r["phase"][name] for r in rs) / len(rs), 4) for name in rs[0]["phase"]}
        out[key] = {"slo": avg("slo"), "gpu_h": avg("gpu_h"), "phase": ph,
                    "slo_min": min(r["slo"] for r in rs), "slo_max": max(r["slo"] for r in rs),
                    "series": rs[0]["series"]}
        print(f"{key}: SLO {out[key]['slo']:.1%} ({out[key]['slo_min']:.1%}–{out[key]['slo_max']:.1%})"
              f"  GPU-h {out[key]['gpu_h']:.2f}  pha {ph}")

    for cfg in ("S1", "S4", "A1", "A2"):
        for kb in ("KB1", "KB2", "KB3"):
            run(f"{cfg}-{kb}", cfg, kb)
    for kb in ("KB1", "KB2", "KB3"):
        run(f"A2pred-{kb}", "A2", kb, pred=True)
        run(f"A2jsq-{kb}", "A2", kb, jsq=True)
        run(f"A2cold60-{kb}", "A2", kb, cold=60.0)
        run(f"A2best-{kb}", "A2", kb, pred=True, jsq=True)
    json.dump(out, open(sys.argv[2], "w"))
