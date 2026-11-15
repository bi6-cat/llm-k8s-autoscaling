# ──────────────────────────────────────────────────────────────────────────────
# docs/bao-cao/de-xuat-v3/mo_phong_cua_so.py
# Khái niệm: Cửa sổ scale-down (hold, H) = thời gian pod đã không còn cần vẫn được giữ lại trước khi tắt.
#            Đây là bài ski-rental (rent-or-buy): giữ pod tốn 1 GPU-giây mỗi giây ("thuê"); tắt rồi phải bật
#            lại tốn trọn một cold start không phục vụ được ai ("mua lại"). Lý thuyết (Karlin 1988): thuật toán
#            deterministic tối ưu giữ đúng bằng chi phí mua lại, tỉ số cạnh tranh 2.
# Mục đích:  Quét H cho ba mức cold start, trên cửa sổ TEST và 2 ngày trọn của BurstGPT, để kiểm xem điểm
#            tối ưu thực nghiệm có nằm quanh "chi phí mua lại" như lý thuyết nói không. KHÔNG dùng chặn 429
#            (adm=None) để tách riêng hiệu ứng của H. Kết quả cho hướng 2 của cac-huong-nang-cap.html.
# Chạy:      python3 mo_phong_cua_so.py <repo> cua-so-trace.json ket-qua-cua-so.json   (~3–5 phút, 12 lõi)
# ──────────────────────────────────────────────────────────────────────────────
"""Chi phí "mua lại" tính bằng GPU-giây không phục vụ: cold start (pod mới chiếm GPU nhưng chưa Ready)
cộng grace 180 s (pod bị tắt vẫn giữ GPU vì vLLM bỏ qua SIGTERM, ADR-006 C8). Với cold 110 s: B ≈ 290 s.
Ski-rental dự đoán H* ≈ B; nếu H nhỏ hơn nhiều thì vừa mất SLO (bật lại trễ) vừa tốn GPU hơn (trả grace
nhiều lần)."""
from __future__ import annotations

import json
import sys

sys.path.insert(0, sys.argv[1])
import mo_phong_thuc_te as mp  # noqa: E402

HOLDS = (0, 60, 120, 180, 300, 450, 600, 900)
COLDS = (110.0, 60.0, 15.0)
GRACE = mp.GRACE

if __name__ == "__main__":
    with open(sys.argv[2]) as fh:
        traces = json.load(fh)
    te = [f"test:{w}" for w in range(len(traces["test"]))]
    days = [f"days:{d}" for d in range(len(traces["days"]))]
    out = {"grace_s": GRACE, "holds": HOLDS, "colds": COLDS, "test": {}, "days": {}}
    for cold in COLDS:
        for hold in HOLDS:
            cfg = {"cfg": "P", "jsq": True, "adm": None, "tau": 0, "cancel": False, "cold": cold, "hold": float(hold)}
            a = mp.run_set(cfg, te, 3, traces)
            d = mp.run_set(cfg, days, 1, traces)
            out["test"][f"{cold:.0f}|{hold}"] = a
            out["days"][f"{cold:.0f}|{hold}"] = d
            print(f"cold={cold:3.0f} B≈{cold + GRACE:3.0f}  H={hold:3d}  test SLO {a['slo']:.1%} GPU {a['gpu_pct']:.1%} "
                  f"starts {a['starts']:.1f} | days SLO {d['slo']:.1%} GPU {d['gpu_pct']:.1%} starts {d['starts']:.1f}",
                  flush=True)
    with open(sys.argv[3], "w") as fh:
        json.dump(out, fh)
