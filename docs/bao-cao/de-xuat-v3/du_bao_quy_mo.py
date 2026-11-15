# ──────────────────────────────────────────────────────────────────────────────
# docs/bao-cao/de-xuat-v3/du_bao_quy_mo.py
# Khái niệm: Cận trên oracle = planner biết trước tốc độ thật trung bình 10 phút tới (bộ dự báo hoàn hảo ở độ
#            phân giải 10 phút). Nếu ngay cả oracle cũng không lợi thì kết luận âm của hướng 3 không phải do
#            Holt-Winters kém mà do bản chất tải.
# Mục đích:  Hướng 3, việc còn lại: so A2+G, hybrid-HW, hybrid-oracle ở hai quy mô: 4 GPU (nền ≈ 1 pod) và
#            16 GPU với tải ×4 (nền ≈ 2–3 pod, mỗi đỉnh cần nhiều pod hơn).
# Chạy:      python3 -I du_bao_quy_mo.py <repo> <BurstGPT_1.csv> cua-so-trace.json ket-qua-du-bao-quy-mo.json
# ──────────────────────────────────────────────────────────────────────────────
from __future__ import annotations

import copy
import json
import math
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, sys.argv[1])
import du_bao_mua_vu as hw  # noqa: E402
import mo_phong_thuc_te as mp  # noqa: E402


def to_pods(lam10, cold, n, thr=mp.A2_T):
    """lam10: tốc độ theo khung 10 phút; proactive tại t = số pod cho max λ trên [t, t + cold + 20]."""
    out = []
    for k in range(8640):
        t = k * 10
        a, b = int(t // hw.SLOT), int((t + cold + 20) // hw.SLOT) + 1
        lam = max(lam10[min(i, hw.PER_DAY - 1)] for i in range(a, b))
        out.append(max(1, min(n, math.ceil(lam * mp.E2E_EST / thr))))
    return out


if __name__ == "__main__":
    y = hw.load_counts(sys.argv[2])
    with open(sys.argv[3]) as fh:
        traces0 = json.load(fh)
    alpha, gamma = 0.4, 0.05  # chọn trên ngày 30–39 ở du_bao_mua_vu.py
    res = {}
    for n, mult in ((4, 1), (16, 4)):
        traces = copy.deepcopy(traces0)
        for w in traces["days"]:
            w["rate"] = [r * mult for r in w["rate"]]
        for cold in (110.0, 15.0):
            for name in ("A2+G", "hybrid-HW", "hybrid-oracle"):
                jobs = []
                for i, w in enumerate(traces["days"]):
                    d, f = w["day"], traces0["days"][i]["scale"] * mult
                    if name == "hybrid-HW":
                        lam10 = [v * f for v in hw.forecast_day(y, alpha, gamma, d)]
                    elif name == "hybrid-oracle":
                        r = w["rate"]  # thùng 10 s → trung bình 10 phút
                        lam10 = [sum(r[k * 60:(k + 1) * 60]) / 60 for k in range(hw.PER_DAY)]
                    for seed in range(2):
                        j = {"scn": f"days:{i}", "seed": seed, "cfg": "P", "jsq": True, "adm": None, "tau": 0,
                             "cancel": False, "cold": cold, "hold": 300.0, "_N": n}
                        if name != "A2+G":
                            j["_pro"] = to_pods(lam10, cold, n)
                        jobs.append(j)
                a = mp.agg(mp.batch(jobs, traces))
                res[f"{n}|{cold:.0f}|{name}"] = a
                print(f"N={n:2d} ×{mult} cold={cold:3.0f} {name:13s} SLO {a['slo']:.1%} GPU {a['gpu_pct']:.1%} "
                      f"starts {a['starts']:.0f}", flush=True)
    with open(sys.argv[4], "w") as fh:
        json.dump(res, fh)
