# ──────────────────────────────────────────────────────────────────────────────
# docs/bao-cao/de-xuat-v3/du_bao_mua_vu.py
# Khái niệm: Dự báo mùa vụ (seasonal forecasting): tải LLM lặp theo chu kỳ 24 h (ngày/đêm, giờ làm việc).
#            Holt-Winters cộng tính giữ hai thành phần: mức ℓ (trung bình hiện tại) và mùa vụ s_k (lệch của
#            từng khung 10 phút trong ngày so với mức), cập nhật dần theo hệ số α (mức) và γ (mùa vụ).
#            Planner hybrid: desired = max(reactive A2, proactive từ dự báo). Dự báo chỉ được BẬT SỚM.
# Mục đích:  Hướng 3. Fit trên ngày 0–39 của BurstGPT (chọn α, γ trên ngày 30–39), dự báo 2 ngày test
#            (41, 59) với dữ liệu tới hết ngày trước đó, báo MAPE so với dự báo ngây thơ (cùng khung hôm qua),
#            rồi mô phỏng A2+G thuần và hybrid trên 2 ngày đó, cold start 110 / 15 s.
# Chạy:      python3 -I du_bao_mua_vu.py <repo> <BurstGPT_1.csv> cua-so-trace.json ket-qua-du-bao.json
# ──────────────────────────────────────────────────────────────────────────────
"""Chuyển dự báo tốc độ λ̂ (req/s) sang số pod theo định luật Little: tải đồng thời ≈ λ̂ × E2E (9 s),
pod cần = ⌈tải ÷ thr⌉. Vì pod mới cần `cold + trễ` giây mới Ready, proactive tại t lấy max của λ̂ trên
[t, t + cold + 20 s]. Tốc độ trace được nhân cùng hệ số co giãn f của ngày test (cua-so-trace.json)."""
from __future__ import annotations

import csv
import json
import math
import os
import sys

# chạy với -I (đọc CSV tải về) nên thư mục script không tự có trong sys.path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, sys.argv[1])
import mo_phong_thuc_te as mp  # noqa: E402

SLOT = 600                  # 10 phút
PER_DAY = 86400 // SLOT     # 144 khung mỗi ngày
SPLIT_DAY = 40


def load_counts(path):
    cnt = {}
    with open(path) as f:
        r = csv.reader(f)
        next(r)
        for t, _m, _rq, rs, _tot, _log in r:
            if int(rs) == 0:
                continue
            k = int(t) // SLOT
            cnt[k] = cnt.get(k, 0) + 1
    n = max(cnt) + 1
    return [cnt.get(k, 0) / SLOT for k in range(n)]  # req/s mỗi khung


def holt_winters(y, alpha, gamma, upto):
    """Chạy HW cộng tính (không trend) qua y[:upto]; trả (ℓ, s) tại cuối đoạn."""
    lvl = sum(y[:PER_DAY]) / PER_DAY
    s = [y[k] - lvl for k in range(PER_DAY)]
    for k in range(PER_DAY, upto):
        yk, sk = y[k], s[k % PER_DAY]
        new_lvl = alpha * (yk - sk) + (1 - alpha) * lvl
        s[k % PER_DAY] = gamma * (yk - new_lvl) + (1 - gamma) * sk
        lvl = new_lvl
    return lvl, s


def forecast_day(y, alpha, gamma, day):
    lvl, s = holt_winters(y, alpha, gamma, day * PER_DAY)
    return [max(0.0, lvl + s[k]) for k in range(PER_DAY)]


def mape(pred, true):
    pairs = [(p, a) for p, a in zip(pred, true) if a > 0.01]
    return sum(abs(p - a) / a for p, a in pairs) / len(pairs)


if __name__ == "__main__":
    y = load_counts(sys.argv[2])
    with open(sys.argv[3]) as fh:
        traces = json.load(fh)
    out = {"slot_s": SLOT}

    # 1) chọn α, γ trên ngày 30–39 (validation nằm trong train)
    best = None
    for alpha in (0.05, 0.1, 0.2, 0.4):
        for gamma in (0.05, 0.1, 0.2, 0.4):
            errs = [mape(forecast_day(y, alpha, gamma, d), y[d * PER_DAY:(d + 1) * PER_DAY]) for d in range(30, SPLIT_DAY)]
            e = sum(errs) / len(errs)
            if best is None or e < best[0]:
                best = (e, alpha, gamma)
    _, alpha, gamma = best
    out["fit"] = {"alpha": alpha, "gamma": gamma, "mape_val": round(best[0], 4)}
    print(f"chọn α={alpha} γ={gamma}, MAPE validation {best[0]:.1%}", flush=True)

    # 2) dự báo 2 ngày test + MAPE so với ngây thơ (hôm qua) và với trung vị 7 ngày trước cùng khung
    out["days"] = []
    pro_series = {}
    for w in traces["days"]:
        d, f = w["day"], w["scale"]
        true = y[d * PER_DAY:(d + 1) * PER_DAY]
        hw = forecast_day(y, alpha, gamma, d)
        naive = y[(d - 1) * PER_DAY:d * PER_DAY]
        rec = {"day": d, "mape_hw": round(mape(hw, true), 4), "mape_naive": round(mape(naive, true), 4),
               "hw_scaled": [round(v * f, 3) for v in hw], "true_scaled": [round(v * f, 3) for v in true]}
        print(f"ngày {d}: MAPE HW {rec['mape_hw']:.1%}, ngây thơ {rec['mape_naive']:.1%}", flush=True)
        out["days"].append(rec)
        pro_series[d] = [v * f for v in hw]

    # 3) mô phỏng: A2+G thuần vs hybrid, 2 ngày, cold 110 và 15
    def to_pods(hw_scaled, cold, thr=mp.A2_T, lead_extra=20.0):
        lead = cold + lead_extra
        pods = []
        for k in range(8640):  # thùng 10 s
            t = k * 10
            a, b = int(t // SLOT), int((t + lead) // SLOT) + 1
            lam = max(hw_scaled[min(i, PER_DAY - 1)] for i in range(a, b))
            pods.append(max(1, min(mp.N, math.ceil(lam * mp.E2E_EST / thr))))
        return pods

    out["sim"] = {}
    for cold in (110.0, 15.0):
        for name, hyb in (("A2+G", False), ("hybrid", True)):
            rs = []
            for i, w in enumerate(traces["days"]):
                for seed in range(2):
                    job = {"scn": f"days:{i}", "seed": seed, "cfg": "P", "jsq": True, "adm": None, "tau": 0,
                           "cancel": False, "cold": cold, "hold": 300.0}
                    if hyb:
                        job["_pro"] = to_pods(pro_series[w["day"]], cold)
                    rs.append(job)
            res = mp.agg(mp.batch(rs, traces))
            out["sim"][f"{name}|{cold:.0f}"] = res
            print(f"cold={cold:.0f} {name:7s} SLO {res['slo']:.1%} ({res['slo_min']:.1%}–{res['slo_max']:.1%}) "
                  f"GPU {res['gpu_pct']:.1%} starts {res['starts']:.1f}", flush=True)
    with open(sys.argv[4], "w") as fh:
        json.dump(out, fh)
