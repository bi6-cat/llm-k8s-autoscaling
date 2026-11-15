# ──────────────────────────────────────────────────────────────────────────────
# docs/bao-cao/de-xuat-v3/chuan_bi_trace.py
# Khái niệm: Trace = log thật của một dịch vụ LLM: thời điểm gửi và số token vào/ra của từng request.
#            BurstGPT (HPMLL, CC-BY-4.0) là log 61 ngày của dịch vụ Azure OpenAI GPT ở một trường đại học.
# Mục đích:  Trích các cửa sổ 30 phút có đỉnh tải từ BurstGPT_1.csv, chia train (ngày 0–39) để chọn tham số
#            planner và test (ngày 40–60) để đánh giá, rồi co giãn tốc độ cho vừa cụm 4 × A4000.
#            Ghi kết quả gọn (tốc độ theo thùng 10 s) ra JSON để mô phỏng đọc.
# Chạy:      curl -L -o /tmp/BurstGPT_1.csv \
#              https://github.com/HPMLL/BurstGPT/releases/download/v1.1/BurstGPT_1.csv
#            python3 -I chuan_bi_trace.py /tmp/BurstGPT_1.csv cua-so-trace.json
# ──────────────────────────────────────────────────────────────────────────────
"""Chọn cửa sổ trace và thống kê độ dài đỉnh.

Cách co giãn: giữ nguyên hình dạng theo thời gian (độ dài đỉnh là thứ quyết định autoscaling có kịp hay
không, nên KHÔNG được nén thời gian), chỉ nhân tốc độ với một hệ số sao cho phút bận nhất của cửa sổ đạt
0,9 × năng lực 4 GPU = 0,9 × 4 × C, C = 4,5 req/s (ĐG1 08/11).
Chỉ lấy NHỊP THỜI GIAN từ trace. Kích thước request giữ như bộ đo đã hiệu chỉnh (256 token ra, prompt
256–1024): request trong BurstGPT ngắn hơn nhiều (trung vị 34 token ra), mà mô hình mô phỏng chỉ hiệu chỉnh
với 256 token và không mô hình hoá prefill tranh GPU; dùng token thật sẽ cho số đẹp giả.
"""
from __future__ import annotations

import csv
import json
import statistics as st
import sys

BIN = 10                 # giây mỗi thùng
WIN = 30 * 60            # độ dài cửa sổ
SPLIT_DAY = 40           # ngày 0–39: train, 40–60: test
PER_SPLIT = 8            # số cửa sổ mỗi phần
CAP_REQ = 4 * 4.5  # năng lực 4 GPU, request mỗi giây
TARGET = 0.9             # phút bận nhất = 90 % năng lực
OUT_MAX, IN_MAX = 1024, 4000  # giới hạn theo context 8192 của cấu hình vLLM


def load(path):
    rows = []
    with open(path) as f:
        r = csv.reader(f)
        next(r)
        for t, _model, rq, rs, _tot, _log in r:
            rs = int(rs)
            if rs == 0:  # request lỗi phía dịch vụ gốc (README của BurstGPT), bỏ
                continue
            rows.append((int(t), min(int(rq), IN_MAX), min(rs, OUT_MAX)))
    return rows


def bursts(cnt):
    """Đỉnh = đoạn mà trung bình trượt 30 s vượt 2 lần mức nền (trung vị 10 phút trước), tối thiểu 0,2 req/s."""
    sm = [sum(cnt[max(0, i - 2):i + 1]) / (3 * BIN) for i in range(len(cnt))]
    out, i, w = [], 60, 60
    while i < len(sm):
        thr = max(2 * st.median(sm[i - w:i]), 0.2)
        if sm[i] > thr:
            j = i
            while j < len(sm) and sm[j] > thr:
                j += 1
            out.append((i * BIN, (j - i) * BIN))
            i = j + 1
        else:
            i += 1
    return out


def main(src, dst):
    rows = load(src)
    T = rows[-1][0] + 1
    nb = T // BIN + 1
    cnt = [0] * nb
    tok = [0] * nb
    for t, _rq, rs in rows:
        cnt[t // BIN] += 1
        tok[t // BIN] += rs
    eps = bursts(cnt)

    # chấm điểm cửa sổ: tổng token ra vượt mức nền trong các đỉnh nằm trọn trong cửa sổ
    def score(a):
        b = a + WIN
        return sum(sum(tok[x // BIN:(x + d) // BIN]) for x, d in eps if a <= x and x + d <= b)

    out = {"nguon": "BurstGPT_1.csv (HPMLL, CC-BY-4.0)", "bin_s": BIN, "win_s": WIN, "train": [], "test": []}
    for split, lo, hi in (("train", 0, SPLIT_DAY * 86400), ("test", SPLIT_DAY * 86400, T - WIN)):
        cands = sorted(((score(a), a) for a in range(lo, hi - WIN, 600)), reverse=True)
        chosen = []
        for sc, a in cands:
            if sc <= 0 or len(chosen) == PER_SPLIT:
                break
            if all(abs(a - c) >= WIN for c in chosen):
                chosen.append(a)
        for a in sorted(chosen):
            b0 = a // BIN
            nbin = WIN // BIN
            # phút bận nhất theo số request → hệ số co giãn
            per_min = [sum(cnt[b0 + k:b0 + k + 6]) / 60 for k in range(nbin - 5)]
            f = TARGET * CAP_REQ / max(per_min)
            rate = [round(cnt[b0 + k] / BIN * f, 4) for k in range(nbin)]
            durs = [d for x, d in eps if a <= x < a + WIN]
            out[split].append({
                "start_s": a, "day": round(a / 86400, 2), "scale": round(f, 3), "rate": rate,
                "mean_C": round(sum(rate) / len(rate) / 4.5, 3),
                "bursts_s": durs,
            })
        print(f"{split}: {[(w['day'], w['scale'], w['mean_C'], len(w['bursts_s'])) for w in out[split]]}")

    # trọn ngày tải (giữ nhịp ngày đêm) để thấy phần tiết kiệm lúc vắng: hai ngày bận nhất của phần test,
    # co giãn cùng quy tắc (phút bận nhất = 0,9 × năng lực 4 GPU)
    per_day = [sum(cnt[d * 8640:(d + 1) * 8640]) for d in range(T // 86400)]
    busiest = sorted(range(SPLIT_DAY, len(per_day)), key=lambda d: -per_day[d])[:2]
    out["days"] = []
    for d in sorted(busiest):
        b0, nbin = d * 8640, 8640
        per_min = [sum(cnt[b0 + k:b0 + k + 6]) / 60 for k in range(nbin - 5)]
        f = TARGET * CAP_REQ / max(per_min)
        rate = [round(cnt[b0 + k] / BIN * f, 4) for k in range(nbin)]
        out["days"].append({"day": d, "scale": round(f, 3), "rate": rate, "mean_C": round(sum(rate) / nbin / 4.5, 3)})
    print(f"days: {[(w['day'], w['scale'], w['mean_C']) for w in out['days']]}")

    # thống kê độ dài đỉnh (dùng trong tờ trình)
    stats = {}
    # phần tải vượt nền theo độ dài đỉnh, cả 61 ngày
    vol = {"lt120": 0.0, "120_300": 0.0, "300_900": 0.0, "ge900": 0.0}
    num = dict.fromkeys(vol, 0)
    sm = [sum(cnt[max(0, i - 2):i + 1]) / (3 * BIN) for i in range(len(cnt))]
    for x, d in eps:
        i = x // BIN
        base = st.median(sm[max(0, i - 60):i])
        ex = sum(max(0.0, cnt[k] - base * BIN) for k in range(i, i + d // BIN))
        key = "lt120" if d < 120 else "120_300" if d < 300 else "300_900" if d < 900 else "ge900"
        vol[key] += ex
        num[key] += 1
    tot_v, tot_n = sum(vol.values()), sum(num.values())
    stats["by_duration"] = {k: {"bursts": round(num[k] / tot_n, 3), "excess": round(vol[k] / tot_v, 3)} for k in vol}
    for split, cond in (("train", lambda x: x < SPLIT_DAY * 86400), ("test", lambda x: x >= SPLIT_DAY * 86400)):
        d = [dd for x, dd in eps if cond(x)]
        stats[split] = {
            "n": len(d),
            "lt120": round(sum(x < 120 for x in d) / len(d), 3),
            # P(đỉnh còn kéo dài thêm ≥ D + 60 s | đã kéo dài a), D = cold start
            "persist": {str(D): {str(a): round(sum(x >= a + D + 60 for x in d if x > a) / max(1, sum(x > a for x in d)), 3)
                                 for a in (0, 15, 30, 45, 60, 90, 120)} for D in (110, 15)},
        }
    out["stats"] = stats
    with open(dst, "w") as fh:
        json.dump(out, fh)
    print(json.dumps(stats, indent=1))


if __name__ == "__main__":
    main(sys.argv[1], sys.argv[2])
