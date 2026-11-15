# ──────────────────────────────────────────────────────────────────────────────
# docs/bao-cao/de-xuat-v3/mo_phong_thuc_te.py
# Khái niệm: Mô phỏng (KHÔNG phải số đo) vòng autoscaling vLLM trên 4 GPU, kế thừa mo_phong_v3.py (cùng tham
#            số hiệu chỉnh theo số đo 08/11). Thêm những thứ làm kết quả sát thực tế hơn:
#              - tải theo nhịp thời gian của trace thật BurstGPT (cua-so-trace.json, chuan_bi_trace.py);
#              - kịch bản "đỉnh ngắn": vọt lên 3 C trong 60 s rồi về ngay (ngắn hơn cold start);
#              - client thử lại khi bị từ chối (như SDK OpenAI: 2 lần, backoff mũ 0,5 s → 1 s, có jitter);
#              - planner: chỉ scale khi quá tải kéo dài ≥ τ giây, huỷ pod đang khởi động khi đỉnh tắt,
#                giữ pod H giây sau khi hết cần; tính cả request bị từ chối vào nhu cầu;
#              - biến thể cold start 15 s (khôi phục từ snapshot thay vì khởi động lại).
# Mục đích:  Chọn τ, H trên cửa sổ TRAIN (ngày 0–39), rồi so các cấu hình trên cửa sổ TEST (ngày 40–60)
#            và trên KB2, KB3, KB-ngắn. Kết quả ghi vào ket-qua-thuc-te.json cho tờ trình.
# Chạy:      python3 mo_phong_thuc_te.py <repo> cua-so-trace.json ket-qua-thuc-te.json   (~5–10 phút, 12 lõi)
# ──────────────────────────────────────────────────────────────────────────────
"""Mô phỏng theo bước 0,1 s. Tham số lấy từ đo thật (giống mo_phong_v3.py):
  - TPOT ≈ 18,5 + 0,49·n ms với n request đang chạy; tối đa 64 request chạy mỗi pod (--max-num-seqs);
  - TTFT = chờ trong hàng + prefill (0,1 s cho prompt trung bình 640 token, tỉ lệ theo độ dài) + 0,006·n;
  - output 256 token; SLO: TTFT ≤ 2,5 s và TPOT ≤ 100 ms, tính từ lúc người dùng gửi LẦN ĐẦU;
  - client huỷ sau 120 s; cold start 110 s; metric trễ 5 s; HPA chạy mỗi 15 s;
  - pod bị tắt giữ GPU thêm 180 s (vLLM bỏ qua SIGTERM, ADR-006 C8). Pod bị HUỶ khi chưa Ready giữ 5 s:
    giả định có preStop hook kill ngay pod chưa Ready (một phần của đề xuất).
Những gì CHƯA mô hình hoá: prefill tranh GPU với decode ở tải rất cao, prefix cache, độ dài output thay đổi.
"""
from __future__ import annotations

import bisect
import heapq
import itertools
import json
import math
import random
import sys
from concurrent.futures import ProcessPoolExecutor

C, N, A2_T = 4.5, 4, 42
N_DEFAULT = N
COLD, GRACE, TIMEOUT, OUT_TOK, MAXSEQ = 110.0, 180.0, 120.0, 256, 64
LAG, DT, HPA_EVERY = 5.0, 0.1, 15.0
E2E_EST = 9.0  # giây, thời gian một request ở tải vừa (đo 08/11: 6,1–11,5 s); dùng quy đổi từ chối → nhu cầu


def tpot(n: int) -> float:
    return (18.5 + 0.49 * n) / 1000


# ── kịch bản tải ──────────────────────────────────────────────────────────────
def piecewise(points):
    def f(t):
        if t <= points[0][0]:
            return points[0][1]
        for (t0, v0), (t1, v1) in itertools.pairwise(points):
            if t0 <= t <= t1:
                return v1 if t1 == t0 else v0 + (v1 - v0) * (t - t0) / (t1 - t0)
        return points[-1][1]
    return f


def scenario(name, traces):
    """Trả (λ(t), thời lượng, số pod ban đầu). Thời gian giây, λ request/giây."""
    if name == "KB2":   # Thông số §7: 0,5 C → 3 C trong 30 s ở phút 4, giữ tới phút 14, về 0,5 C
        pts = [(0, .5), (240, .5), (270, 3), (840, 3), (870, .5), (1440, .5)]
        return piecewise([(t, v * C) for t, v in pts]), 1440.0, 1
    if name == "KB3":   # tăng dần 0,5 C → 3 C trong 5 phút, giữ tới phút 17
        return piecewise([(0, .5 * C), (300, 3 * C), (1020, 3 * C)]), 1020.0, 1
    if name == "KBngan":  # ĐỈNH NGẮN: ba lần vọt lên 3 C trong 60 s rồi về ngay, cách nhau 6 phút
        pts = [(0, .5)]
        for m in (4, 10, 16):
            a = m * 60
            pts += [(a, .5), (a + 10, 3), (a + 70, 3), (a + 80, .5)]
        pts.append((1320, .5))
        return piecewise([(t, v * C) for t, v in pts]), 1320.0, 1
    split, i = name.split(":")
    w = traces[split][int(i)]
    rate, b = w["rate"], traces["bin_s"]
    n0 = max(1, min(N, math.ceil(sum(rate[:6]) / 6 * 6.0 / A2_T)))  # trạng thái ổn định theo phút đầu
    return (lambda t: rate[min(int(t // b), len(rate) - 1)]), float(len(rate) * b), n0


# ── pod ──────────────────────────────────────────────────────────────────────
class Pod:
    __slots__ = ("born", "cancelled", "dead_at", "q", "qh", "ready_at", "run", "v")

    def __init__(self, ready_at, born):
        self.born, self.ready_at, self.dead_at, self.cancelled = born, ready_at, None, False
        self.v, self.run, self.q, self.qh = 0.0, [], [], 0

    def ready(self, t):
        return self.dead_at is None and t >= self.ready_at

    def load(self):
        return len(self.run) + len(self.q) - self.qh


# ── một lượt ─────────────────────────────────────────────────────────────────
def simulate(job):
    """job: dict(scn, cfg, seed, + tuỳ chọn). cfg:
         S4 | A2 | A3 (A2 + predict_linear) | P (planner)
       tuỳ chọn: jsq (gateway LeastRequest), adm (giới hạn request mỗi pod, quá thì 429), cold, tau, hold,
       thr (ngưỡng request mỗi pod, mặc định 42; nhỏ hơn = để dư năng lực), cancel (planner huỷ pod chưa Ready)."""
    # số GPU của cụm; job có thể đặt khác (du_bao_quy_mo.py). Gán vào biến module vì worker có thể là
    # forkserver (Python ≥ 3.14) nên không kế thừa thay đổi của tiến trình cha.
    global N
    N = job.get("_N", N_DEFAULT)
    traces = job.get("_traces")
    lam_f, dur, n0 = scenario(job["scn"], traces)
    cfg, rng = job["cfg"], random.Random(job["seed"])
    cold, jsq, adm = job.get("cold", COLD), job.get("jsq", False), job.get("adm")
    tau, hold = job.get("tau", 0.0), job.get("hold", 300.0)
    thr, cancel = job.get("thr", A2_T), job.get("cancel", True)
    gone = []            # pod đã tắt hẳn (chỉ còn dùng để tính GPU-giờ)
    pods = [Pod(0.0, -1e9) for _ in range(N if cfg == "S4" else n0)]
    reqs = []            # [t_gửi_đầu, prompt, ok, xong, số lần bị từ chối]
    retry = []           # heap (t, id, lần)
    rej_log = []         # thời điểm bị từ chối (cho nhu cầu của planner)
    metric_log = []      # (t, tải thô)
    mt = []              # thời điểm của metric_log, để tìm bằng bisect
    hist, last_down = [], -1e9
    over_since = under_since = down_since = None
    slope = 0.0
    starts = cancels = 0
    t, next_hpa, t_end = 0.0, 0.0, dur + 600

    def route(i, now):
        rp = [p for p in pods if p.ready(now)]
        if not rp:
            rp = [p for p in pods if p.dead_at is None]
        pod = min(rp, key=Pod.load) if jsq else rng.choice(rp)
        if adm is not None and pod.ready(now) and pod.load() >= adm:
            r = reqs[i]
            r[4] += 1
            rej_log.append(now)
            if r[4] <= 2:  # SDK thử lại 2 lần: 0,5 s rồi 1 s, jitter −25 %
                heapq.heappush(retry, (now + 0.5 * 2 ** (r[4] - 1) * (1 - 0.25 * rng.random()), i))
            return
        pod.q.append((reqs[i][0], i))

    while t < t_end:
        lam = lam_f(t) if t < dur else 0.0
        x, L, p, k = lam * DT, 0, 1.0, -1
        L = math.exp(-x)
        while p > L:
            p *= rng.random()
            k += 1
        for _ in range(k):
            reqs.append([t, rng.randint(256, 1024), False, False, 0])
            route(len(reqs) - 1, t)
        while retry and retry[0][0] <= t:
            _, i = heapq.heappop(retry)
            route(i, t)
        # pod xử lý
        for pod in pods:
            if pod.cancelled or (not pod.ready(t) and pod.dead_at is None):
                continue
            while pod.qh < len(pod.q) and t - pod.q[pod.qh][0] > TIMEOUT:
                reqs[pod.q[pod.qh][1]][3] = True
                pod.qh += 1
            while len(pod.run) < MAXSEQ and pod.qh < len(pod.q):
                ta, i = pod.q[pod.qh]
                pod.qh += 1
                ttft = (t - ta) + 0.1 * reqs[i][1] / 640 + 0.006 * len(pod.run)
                heapq.heappush(pod.run, (pod.v + OUT_TOK, i, ttft))
            if pod.run:
                tp = tpot(len(pod.run))
                pod.v += DT / tp
                while pod.run and pod.run[0][0] <= pod.v:
                    _, i, ttft = heapq.heappop(pod.run)
                    r = reqs[i]
                    r[3] = True
                    r[2] = ttft <= 2.5 and tp <= 0.1 and (t - r[0]) <= TIMEOUT
        # metric: tổng request đang chạy + chờ ở các pod Ready (vLLM chỉ báo khi Ready)
        live = [p_ for p_ in pods if p_.ready(t)]
        m = sum(p_.load() for p_ in live)
        if int(t / DT) % 10 == 0:
            metric_log.append((t, m))
            mt.append(t)
        # quyết định mỗi 15 s, nhìn metric trễ 5 s
        if cfg != "S4" and t >= next_hpa:
            next_hpa += HPA_EVERY
            j = bisect.bisect_right(mt, t - LAG)
            mv = metric_log[j - 1][1] if j else m
            alive = [p_ for p_ in pods if p_.dead_at is None]
            ready = [p_ for p_ in alive if t >= p_.ready_at]
            starting = [p_ for p_ in alive if t < p_.ready_at]
            if cfg == "A3":  # predict_linear trên 120 s, ngưỡng chết 10 (như tờ trình bản 1)
                pts = metric_log[bisect.bisect_left(mt, t - LAG - 120):j]
                if len(pts) > 20:
                    tbar = sum(a for a, _ in pts) / len(pts)
                    mvv = sum(b for _, b in pts) / len(pts)
                    den = sum((a - tbar) ** 2 for a, _ in pts)
                    slope = sum((a - tbar) * (b - mvv) for a, b in pts) / den if den else 0.0
                ext = max(0.0, slope) * cold
                mv = mv + (ext if ext > 10 else 0.0)
            if cfg == "P":  # nhu cầu bị chặn ở cửa: tốc độ từ chối × thời gian một request (định lý Little)
                rj = sum(1 for x in rej_log[-2000:] if x >= t - LAG - 15)
                mv = mv + rj / 15 * E2E_EST
            want = max(1, min(N, math.ceil(mv / thr)))
            # hướng 3 (planner hybrid): chuỗi proactive từ dự báo mùa vụ, theo thùng 10 s, CHỈ được nâng
            # desired (bật sớm), không được hạ (reactive vẫn là sàn) → sai dự báo chỉ tốn GPU, không phá SLO
            pro = job.get("_pro")
            if pro:
                want = max(want, min(N, pro[min(len(pro) - 1, int(t // 10))]))
            if cfg in ("A2", "A3"):
                hist.append((t, want))
                if want > len(alive):
                    for _ in range(want - len(alive)):
                        pods.append(Pod(t + cold, t))
                        starts += 1
                else:
                    rec = max(w for (tt, w) in hist if tt >= t - 300)
                    if rec < len(alive) and t - last_down >= 60:
                        victim = max(alive, key=lambda p_: p_.born)  # ReplicaSet xoá pod chưa Ready/trẻ nhất
                        victim.dead_at = t
                        if t < victim.ready_at:
                            victim.cancelled = True
                        last_down = t
            else:  # planner
                over_since = (over_since if over_since is not None else t) if want > len(ready) else None
                if want > len(alive) and over_since is not None and t - over_since >= tau:
                    for _ in range(want - len(alive)):
                        pods.append(Pod(t + cold, t))
                        starts += 1
                # đỉnh đã tắt trong lúc pod mới đang khởi động: huỷ pod chưa Ready (2 lần đọc liên tiếp)
                under_since = (under_since if under_since is not None else t) if (starting and want <= len(ready)) else None
                if cancel and starting and under_since is not None and t - under_since >= HPA_EVERY:
                    for p_ in starting[: len(alive) - max(want, len(ready))]:
                        p_.dead_at, p_.cancelled = t, True
                        cancels += 1
                    under_since = None
                # bớt pod Ready khi đã không cần trong `hold` giây; mỗi 60 s bớt 1
                down_since = (down_since if down_since is not None else t) if want < len(ready) else None
                if down_since is not None and t - down_since >= hold and t - last_down >= 60:
                    victim = max(ready, key=lambda p_: p_.born)
                    victim.dead_at = t
                    last_down = t
        # pod đã tắt: phục vụ nốt trong grace rồi mất; pod đã hết grace chuyển sang `gone`
        if int(t / DT) % 10 == 0:
            keep = []
            for p_ in pods:
                if p_.dead_at is not None and (p_.cancelled or t - p_.dead_at >= GRACE):
                    for _, i, _ in p_.run:
                        reqs[i][2] = False
                        reqs[i][3] = True
                    p_.run, p_.q, p_.qh = [], [], 0
                    gone.append(p_)
                else:
                    keep.append(p_)
            pods[:] = keep
        t += DT

    # tổng hợp trong đúng thời lượng lượt
    sel = [r for r in reqs if r[0] < dur]
    n = len(sel)
    ok = sum(1 for r in sel if r[2])
    rej_final = sum(1 for r in sel if r[4] > 2)
    gpu_s = 0.0
    for p_ in pods + gone:
        start = max(0.0, p_.born)
        if p_.dead_at is None:
            end = dur
        else:
            end = p_.dead_at + (5.0 if p_.cancelled else GRACE)
        gpu_s += max(0.0, min(dur, end) - start)
    return {"slo": ok / n, "rej": rej_final / n, "retried": sum(1 for r in sel if r[4] > 0) / n,
            "gpu_h": gpu_s / 3600, "s4_h": N * dur / 3600, "starts": starts, "cancels": cancels, "n": n}


# ── chạy hàng loạt ───────────────────────────────────────────────────────────
def batch(jobs, traces):
    for j in jobs:
        j["_traces"] = traces
    with ProcessPoolExecutor() as ex:
        return list(ex.map(simulate, jobs, chunksize=1))


def agg(rs):
    k = len(rs)
    o = {key: sum(r[key] for r in rs) / k for key in ("slo", "rej", "retried", "gpu_h", "s4_h", "starts", "cancels")}
    o["gpu_pct"] = o["gpu_h"] / o["s4_h"]
    o["slo_min"], o["slo_max"] = min(r["slo"] for r in rs), max(r["slo"] for r in rs)
    return {key: round(v, 4) for key, v in o.items()}


CONFIGS = {
    "S4":            {"cfg": "S4"},
    "A2":            {"cfg": "A2"},
    "A2+G":          {"cfg": "A2", "jsq": True},
    "A3+G":          {"cfg": "A3", "jsq": True},
    "A2+G+chặn":     {"cfg": "A2", "jsq": True, "adm": 75},
    "P":             {"cfg": "P", "jsq": True, "adm": 75},           # τ, hold, cancel lấy từ bước train
    "A2+G snap15":   {"cfg": "A2", "jsq": True, "cold": 15.0},
    "P snap15":      {"cfg": "P", "jsq": True, "adm": 75, "cold": 15.0},
}


def run_set(cfg, scns, seeds, traces):
    rs = batch([{"scn": sc, "seed": s, **cfg} for sc in scns for s in range(seeds)], traces)
    return agg(rs)


if __name__ == "__main__":
    sys.path.insert(0, sys.argv[1])
    with open(sys.argv[2]) as fh:
        traces = json.load(fh)
    out = {"stats": traces["stats"]}
    tr = [f"train:{w}" for w in range(len(traces["train"]))]
    te = [f"test:{w}" for w in range(len(traces["test"]))]

    # 1) TRAIN: chọn τ, hold, có huỷ pod chưa Ready hay không (3 seed mỗi cửa sổ)
    out["train"] = {}
    for cold in (110.0, 15.0):
        rows = []
        for tau in (0, 30, 60, 90):
            for hold in (120, 300):
                for cancel in (True, False):
                    a = run_set({"cfg": "P", "jsq": True, "adm": 75, "cold": cold, "tau": tau, "hold": hold,
                                 "cancel": cancel}, tr, 3, traces)
                    rows.append({"tau": tau, "hold": hold, "cancel": cancel, **a})
                    print(f"train cold={cold:.0f} τ={tau:3d} hold={hold:3d} huỷ={cancel!s:5s} SLO {a['slo']:.1%} "
                          f"GPU {a['gpu_pct']:.1%} starts {a['starts']:.1f} cancels {a['cancels']:.1f}", flush=True)
        best = max(r["slo"] for r in rows)
        # luật chọn: rẻ nhất trong các bộ tham số có SLO cách tốt nhất ≤ 1 điểm (ưu tiên chất lượng)
        pick = min((r for r in rows if r["slo"] >= best - 0.01), key=lambda r: r["gpu_pct"])
        out["train"][str(int(cold))] = {"rows": rows, "pick": pick}
        print(f"  → chọn τ={pick['tau']} hold={pick['hold']} huỷ={pick['cancel']}", flush=True)
    for name, key in (("P", "110"), ("P snap15", "15")):
        pk = out["train"][key]["pick"]
        CONFIGS[name].update(tau=pk["tau"], hold=pk["hold"], cancel=pk["cancel"])

    # 2) Bảng chính: test (5 seed), KB2, KB3, KB-ngắn (5 seed), hai ngày trọn (2 seed)
    out["eval"] = {}
    days = [f"days:{d}" for d in range(len(traces["days"]))]
    for name, cfg in CONFIGS.items():
        e = {"test": run_set(cfg, te, 5, traces)}
        for sc in ("KB2", "KB3", "KBngan"):
            e[sc] = run_set(cfg, [sc], 5, traces)
        e["days"] = run_set(cfg, days, 2, traces)
        out["eval"][name] = e
        print(f"{name:13s} TEST {e['test']['slo']:.1%}/{e['test']['gpu_pct']:.0%} rej {e['test']['rej']:.1%} | "
              f"KB2 {e['KB2']['slo']:.1%}/{e['KB2']['gpu_pct']:.0%} KB3 {e['KB3']['slo']:.1%}/{e['KB3']['gpu_pct']:.0%} "
              f"ngắn {e['KBngan']['slo']:.1%}/{e['KBngan']['gpu_pct']:.0%} | NGÀY {e['days']['slo']:.1%}/"
              f"{e['days']['gpu_pct']:.0%} starts {e['days']['starts']:.0f}", flush=True)

    # 3) Đường đánh đổi trên test: hạ ngưỡng = để dư năng lực; cold 110 s và 15 s
    out["frontier"] = {}
    for cold in (110.0, 15.0):
        for fam, base in (("A2+G", {"cfg": "A2", "jsq": True}), ("P", dict(CONFIGS["P" if cold > 20 else "P snap15"]))):
            for thr in (42, 32, 24, 16):
                cfg = {**base, "cold": cold, "thr": thr}
                a = run_set(cfg, te, 3, traces)
                out["frontier"][f"{fam}|{int(cold)}|{thr}"] = a
                print(f"frontier {fam:5s} cold={cold:.0f} thr={thr}: SLO {a['slo']:.1%} GPU {a['gpu_pct']:.1%}", flush=True)

    # 4) Biến thể phụ: cold start 60 s = ƯỚC LƯỢNG khi có compile cache + ít CUDA graph + CPU mới (chưa đo)
    out["cold60"] = {}
    for name, cfg in (("A2+G cold60", {**CONFIGS["A2+G"], "cold": 60.0}), ("P cold60", {**CONFIGS["P"], "cold": 60.0})):
        e = {"test": run_set(cfg, te, 5, traces), "days": run_set(cfg, days, 2, traces)}
        for sc in ("KB2", "KB3", "KBngan"):
            e[sc] = run_set(cfg, [sc], 5, traces)
        out["cold60"][name] = e
        print(f"{name:12s} TEST {e['test']['slo']:.1%}/{e['test']['gpu_pct']:.0%} KB2 {e['KB2']['slo']:.1%} "
              f"ngắn {e['KBngan']['slo']:.1%}/{e['KBngan']['gpu_pct']:.0%} NGÀY {e['days']['slo']:.1%}/"
              f"{e['days']['gpu_pct']:.0%}", flush=True)
    out["configs"] = CONFIGS
    with open(sys.argv[3], "w") as fh:
        json.dump(out, fh, indent=1, ensure_ascii=False)

