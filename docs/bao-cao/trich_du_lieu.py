"""Trích chuỗi thời gian của 2 lượt V1 cho báo cáo kỹ thuật.

Khái niệm: Gom requests.csv (từng request) và metrics.csv.gz (metric Prometheus runner thu) của
           runs/v1-a4000/{A1-KB3-1,A2-KB2-1} thành khung 15 s: tải gửi, % đạt SLO, số pod desired/Ready,
           hàng đợi tách pod cũ / pod mới, tổng GPU util.
Mục đích:  Số liệu cho mục 07 của bao-cao-ky-thuat.html. SLO định nghĩa như runs/vast-v2b-20261108/analyze_v1.py:
           TTFT = t_first − t_send ≤ 2,5 s, TPOT = (t_last − t_first) ÷ (n_out − 1) ≤ 100 ms, HTTP 200.
Dùng:      python3 docs/bao-cao/trich_du_lieu.py . /tmp/v1.json   (từ gốc repo; cần runs/ trên máy)
"""
import csv, gzip, json, sys, collections
R = sys.argv[1]; BIN = 15
out = {}
for run in ("A1-KB3-1", "A2-KB2-1"):
    d = f"{R}/runs/v1-a4000/{run}/attempt-1"
    lg = json.load(open(f"{d}/loadgen.json")); t0 = lg["t0_unix"]; dur = lg["duration_s"]
    reqs = list(csv.DictReader(open(f"{d}/requests.csv")))
    rows = list(csv.DictReader(gzip.open(f"{d}/metrics.csv.gz", "rt")))
    # Khung thời gian phủ cả cooldown sau tải (metric vẫn được thu tới khi lượt kết thúc)
    nb = int(max(dur, max(float(r["ts"]) - t0 for r in rows)) // BIN) + 1
    cnt = [0]*nb; ok = [0]*nb; ttfts = [[] for _ in range(nb)]; to = [0]*nb
    for r in reqs:
        b = int(float(r["t_sched"]) // BIN)
        if b >= nb: continue
        cnt[b] += 1
        if r["status"] != "200" or not r["t_first"]:
            to[b] += 1; continue
        tf = float(r["t_first"]) - float(r["t_send"]); n = int(r["n_out"] or 0)
        tp = (float(r["t_last"]) - float(r["t_first"])) / (n - 1) if n > 1 else 0
        ttfts[b].append(tf); ok[b] += (tf <= 2.5 and tp <= 0.1)
    med = lambda a: sorted(a)[len(a)//2] if a else None
    series = {"t": [i*BIN for i in range(nb)],
              "rate": [round(c/BIN, 2) for c in cnt],
              "slo": [round(o/c, 3) if c else None for o, c in zip(ok, cnt)],
              "ttft_p50": [round(med(x), 2) if x else None for x in ttfts],
              "fail": to}
    step = collections.defaultdict(lambda: [None]*nb)
    wait_pod = collections.defaultdict(lambda: [0]*nb); seen_pod = collections.defaultdict(lambda: [False]*nb)
    gpu = collections.defaultdict(dict)
    first_ts = {}
    for r in rows:
        ts = float(r["ts"]) - t0; b = int(ts // BIN)
        if b < 0 or b >= nb: continue
        nm = r["name"]; v = float(r["value"])
        if nm in ("hpa_desired", "replicas_ready"):
            step[nm][b] = v
        elif nm == "vllm_waiting":
            pod = json.loads(r["labels"]).get("pod", "?")
            first_ts.setdefault(pod, ts)
            wait_pod[pod][b] = max(wait_pod[pod][b], v); seen_pod[pod][b] = True
        elif nm == "gpu_util":
            g = json.loads(r["labels"]).get("uuid") or json.loads(r["labels"]).get("gpu", "?")
            gpu[b].setdefault(round(ts), {})[g] = v
    for nm in ("hpa_desired", "replicas_ready"):
        a = step[nm]; last = None
        for i in range(nb):
            if a[i] is None: a[i] = last
            last = a[i]
        series[nm] = a
    # GPU util tổng (tín hiệu A1 cũ): lớn nhất trong khung, mỗi mẫu = tổng trên mọi GPU × 100
    series["gpu_sum"] = [round(max((sum(s.values()) for s in gpu[i].values()), default=0)*100, 1) for i in range(nb)]
    pods = sorted(first_ts, key=first_ts.get)
    if pods:
        old = pods[0]
        series["wait_old"] = wait_pod[old]
        series["wait_new"] = [sum(wait_pod[p][i] for p in pods[1:]) for i in range(nb)]
    series["phases"] = lg.get("phases_s"); series["n_req"] = len(reqs)
    out[run] = series
    print(run, "n", len(reqs), "bins", nb, "pods", len(pods), "maxwait_old", max(series.get("wait_old",[0])),
          "max gpu_sum", max(series["gpu_sum"]), "desired max", max(x or 0 for x in series["hpa_desired"]))
json.dump(out, open(sys.argv[2], "w"))
