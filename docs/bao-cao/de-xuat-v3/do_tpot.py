# ──────────────────────────────────────────────────────────────────────────────
# docs/bao-cao/de-xuat-v3/do_tpot.py
# Khái niệm: TPOT (time per output token) = thời gian giữa hai token ra liên tiếp của một request. Với
#            continuous batching, mỗi bước decode phục vụ mọi request đang chạy, nên TPOT tăng theo số request
#            đồng thời n. Đo "closed-loop": n client, mỗi client xong request này gửi ngay request kế, nên số
#            request trong vLLM luôn ≈ n.
# Mục đích:  Hướng 1: đo lại TPOT(n) trên GPU khác (5060 Ti) để kiểm công thức ngưỡng chỉ từ số đo:
#            fit TPOT = a + b·n → X(n) = n ÷ (256·TPOT) → sức chứa theo SLO TTFT → ngưỡng.
# Chạy:      (trên máy có vLLM đang phục vụ ở :8000)
#            python3 do_tpot.py http://localhost:8000 qwen2.5-3b ket-qua-tpot.json
# ──────────────────────────────────────────────────────────────────────────────
from __future__ import annotations

import asyncio
import json
import random
import statistics as st
import sys
import time

import aiohttp  # có sẵn trong môi trường vLLM

LEVELS = (1, 8, 16, 32, 48, 64, 80, 96)   # 80, 96 > max-num-seqs 64 → đo được hàng chờ và TTFT
WARM, MEASURE = 20.0, 60.0                # giây bỏ đầu, giây đo
OUT_TOK = 256
WORDS = "the of and to in is was for on that with as by at from his her an which".split()


def prompt(rng):
    n = rng.randint(256, 1024)  # như loadgen: 256–1024 từ
    return " ".join(rng.choice(WORDS) for _ in range(n)) + "\nSummarize the text above."


async def one(sess, url, model, rng, rec):
    body = {"model": model, "prompt": prompt(rng), "max_tokens": OUT_TOK, "ignore_eos": True,
            "stream": True, "temperature": 0}
    t0 = time.monotonic()
    first = last = None
    ntok = 0
    async with sess.post(url + "/v1/completions", json=body) as r:
        async for line in r.content:
            if not line.startswith(b"data: ") or line.startswith(b"data: [DONE]"):
                continue
            now = time.monotonic()
            if first is None:
                first = now
            last = now
            ntok += 1
    if first and ntok > 1:
        rec.append((t0, first - t0, (last - first) / (ntok - 1), last))


async def level(url, model, n):
    rec, stop = [], time.monotonic() + WARM + MEASURE
    rng = random.Random(n)
    conn = aiohttp.TCPConnector(limit=0)
    async with aiohttp.ClientSession(connector=conn, timeout=aiohttp.ClientTimeout(total=600)) as sess:
        async def worker():
            while time.monotonic() < stop:
                await one(sess, url, model, rng, rec)
        t_start = time.monotonic()
        await asyncio.gather(*(worker() for _ in range(n)))
    win = [r for r in rec if r[0] >= t_start + WARM and r[3] <= t_start + WARM + MEASURE]
    done = [r for r in rec if t_start + WARM <= r[3] <= t_start + WARM + MEASURE]
    q = lambda xs, p: sorted(xs)[min(len(xs) - 1, int(p * len(xs)))]
    ttft = [r[1] for r in win]
    tpot = [r[2] for r in win]
    return {"n": n, "count": len(win), "throughput_rps": round(len(done) / MEASURE, 3),
            "tpot_ms_mean": round(1000 * st.mean(tpot), 2), "tpot_ms_p90": round(1000 * q(tpot, .9), 2),
            "ttft_s_mean": round(st.mean(ttft), 3), "ttft_s_p90": round(q(ttft, .9), 3)}


def fit(rows):
    pts = [(r["n"], r["tpot_ms_mean"]) for r in rows if r["n"] <= 64]
    mx, my = st.mean(p[0] for p in pts), st.mean(p[1] for p in pts)
    b = sum((x - mx) * (y - my) for x, y in pts) / sum((x - mx) ** 2 for x, _ in pts)
    return my - b * mx, b


if __name__ == "__main__":
    url, model, dst = sys.argv[1], sys.argv[2], sys.argv[3]
    rows = []
    for n in LEVELS:
        r = asyncio.run(level(url, model, n))
        rows.append(r)
        print(json.dumps(r), flush=True)
    a, b = fit(rows)
    x64 = 64 / (OUT_TOK * (a + 64 * b) / 1000)
    wait = 2.5 - 0.1 - 0.006 * 64          # ngân sách chờ trong hàng để TTFT ≤ 2,5 s (cùng mô hình mô phỏng)
    cap = 64 + int(wait * x64)              # sức chứa theo SLO: chạy + chờ
    out = {"rows": rows, "fit_ms": {"a": round(a, 2), "b": round(b, 3)}, "x64_rps": round(x64, 2),
           "capacity": cap}
    print(json.dumps({k: v for k, v in out.items() if k != "rows"}))
    with open(dst, "w") as fh:
        json.dump(out, fh)
