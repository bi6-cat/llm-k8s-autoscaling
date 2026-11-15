# ──────────────────────────────────────────────────────────────────────────────
# docs/bao-cao/de-xuat-v3/do_chu_ky.py
# Khái niệm: Độ mạnh mùa vụ (seasonal strength, Hyndman & Athanasopoulos, FPP3 §4.3):
#              F_s = max(0, 1 − Var(phần dư) / Var(mùa vụ + phần dư)), 0 = không có chu kỳ, 1 = chu kỳ hoàn hảo.
#            Tính trên chuỗi số request theo giờ (đã bỏ mức trung bình từng ngày), cho chu kỳ 24 h và chu kỳ tuần.
#            Thêm tự tương quan (ACF) ở độ trễ 24 h và 168 h.
# Mục đích:  Định lượng nhận xét "chu kỳ ngày của BurstGPT yếu" ở hướng 3 (cac-huong-nang-cap.html).
# Chạy:      python3 -I do_chu_ky.py <BurstGPT_1.csv> ket-qua-chu-ky.json
# ──────────────────────────────────────────────────────────────────────────────
from __future__ import annotations

import csv
import json
import statistics as st
import sys


def hourly(path):
    c = {}
    with open(path) as f:
        r = csv.reader(f)
        next(r)
        for t, _m, _rq, rs, _tot, _log in r:
            if int(rs):
                c[int(t) // 3600] = c.get(int(t) // 3600, 0) + 1
    n = (max(c) // 24) * 24  # chỉ lấy ngày trọn
    return [c.get(h, 0) for h in range(n)]


def strength(y, period):
    """Mùa vụ = trung bình theo vị trí trong chu kỳ (sau khi bỏ mức từng chu kỳ lớn hơn nếu có)."""
    seas = [st.mean(y[k::period]) for k in range(period)]
    s = [seas[i % period] for i in range(len(y))]
    rem = [a - b for a, b in zip(y, s)]
    return max(0.0, 1 - st.pvariance(rem) / st.pvariance(y))


def acf(y, lag):
    m = st.mean(y)
    num = sum((y[i] - m) * (y[i + lag] - m) for i in range(len(y) - lag))
    return num / sum((v - m) ** 2 for v in y)


if __name__ == "__main__":
    y = hourly(sys.argv[1])
    days = len(y) // 24
    # bỏ mức từng ngày để chỉ đo hình dạng trong ngày
    dm = [st.mean(y[d * 24:(d + 1) * 24]) for d in range(days)]
    yd = [y[i] - dm[i // 24] for i in range(len(y))]
    daily_tot = [sum(y[d * 24:(d + 1) * 24]) for d in range(days)]
    out = {
        "days": days,
        "F_daily_shape": round(strength(yd, 24), 3),       # chu kỳ 24 h sau khi bỏ mức ngày
        "F_daily_raw": round(strength(y, 24), 3),          # chu kỳ 24 h trên chuỗi thô
        "F_weekly_raw": round(strength(y, 168), 3),        # chu kỳ 168 h trên chuỗi thô
        "acf_1h": round(acf(y, 1), 3), "acf_24h": round(acf(y, 24), 3), "acf_168h": round(acf(y, 168), 3),
        "cv_daily_total": round(st.pstdev(daily_tot) / st.mean(daily_tot), 3),
        "hour_profile_mean": [round(st.mean(y[h::24]), 1) for h in range(24)],
        "hour_profile_cv": [round(st.pstdev(y[h::24]) / max(1e-9, st.mean(y[h::24])), 2) for h in range(24)],
    }
    print(json.dumps({k: v for k, v in out.items() if not k.startswith("hour_")}, indent=1))
    print("profile", out["hour_profile_mean"]); print("cv     ", out["hour_profile_cv"])
    with open(sys.argv[2], "w") as fh:
        json.dump(out, fh)
