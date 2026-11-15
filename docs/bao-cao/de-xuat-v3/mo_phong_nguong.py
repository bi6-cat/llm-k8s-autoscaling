# ──────────────────────────────────────────────────────────────────────────────
# docs/bao-cao/de-xuat-v3/mo_phong_nguong.py
# Khái niệm: Ngưỡng scale (thr) = số request (chạy + chờ) mỗi pod mà khi vượt thì autoscaler thêm pod.
#            Hướng 1: ngưỡng không chọn tay mà suy từ sức chứa theo SLO (định luật Little + TPOT(n) đo thật)
#            trừ phần tải dồn tới trong thời gian phản ứng (trễ metric + chu kỳ HPA + cold start).
# Mục đích:  Quét thr cho ba mức cold start, planner thuần (H = 300 s, không chặn 429), trên cửa sổ TEST và
#            2 ngày trọn BurstGPT, để kiểm dự đoán của công thức: cold start càng ngắn thì ngưỡng tối ưu
#            càng dịch lên gần sức chứa 74 (tiết kiệm GPU mà SLO không đổi).
# Chạy:      python3 mo_phong_nguong.py <repo> cua-so-trace.json ket-qua-nguong.json   (~3–5 phút, 12 lõi)
# ──────────────────────────────────────────────────────────────────────────────
from __future__ import annotations

import json
import sys

sys.path.insert(0, sys.argv[1])
import mo_phong_thuc_te as mp  # noqa: E402

THRS = (16, 24, 32, 42, 52, 64)
COLDS = (110.0, 60.0, 15.0)

if __name__ == "__main__":
    with open(sys.argv[2]) as fh:
        traces = json.load(fh)
    te = [f"test:{w}" for w in range(len(traces["test"]))]
    days = [f"days:{d}" for d in range(len(traces["days"]))]
    out = {"thrs": THRS, "colds": COLDS, "test": {}, "days": {}}
    for cold in COLDS:
        for thr in THRS:
            cfg = {"cfg": "P", "jsq": True, "adm": None, "tau": 0, "cancel": False, "cold": cold, "hold": 300.0, "thr": thr}
            a = mp.run_set(cfg, te, 3, traces)
            d = mp.run_set(cfg, days, 1, traces)
            out["test"][f"{cold:.0f}|{thr}"] = a
            out["days"][f"{cold:.0f}|{thr}"] = d
            print(f"cold={cold:3.0f} thr={thr:2d}  test SLO {a['slo']:.1%} GPU {a['gpu_pct']:.1%} | "
                  f"days SLO {d['slo']:.1%} GPU {d['gpu_pct']:.1%}", flush=True)
    with open(sys.argv[3], "w") as fh:
        json.dump(out, fh)
