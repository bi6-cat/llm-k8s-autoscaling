"""Kiểm điều kiện hợp lệ của một lượt (Môi trường §17). Hàm thuần, có unit test.

Khái niệm: Lượt "không hợp lệ" = số đo có thể sai vì lý do ngoài cấu hình đang so sánh (máy tạo tải bị
    nghẽn, pod vLLM bị thay giữa chừng, Prometheus mất mẫu). Lượt đó vẫn giữ dữ liệu nhưng phải chạy lại.
Mục đích: Gom mọi tiêu chí thành checks.json `{valid, reasons, details}`, để ai đọc cũng biết vì sao một
    lượt bị loại. Phần tự kiểm của máy tạo tải (lệch lịch, CPU, throttle) đã có trong loadgen.json;
    ở đây chỉ đọc kết quả `valid` của nó, không kiểm lại.
"""

from __future__ import annotations

from typing import Any

SCRAPE_GAP_MAX_S = 15.0  # Môi trường §17: khoảng trống scrape ≤ 15 s


def evaluate(
    *,
    loadgen_rc: int,
    loadgen_checks: dict[str, Any] | None,
    initial_ok: bool,
    initial_note: str,
    pods_start: list[dict[str, Any]],
    pods_end: list[dict[str, Any]],
    scrape_gaps: dict[str, float | None],
) -> dict[str, Any]:
    reasons: list[str] = []

    # 1) Máy tạo tải chạy xong và tự kiểm đạt
    if loadgen_rc != 0:
        reasons.append(f"loadgen thoát với mã {loadgen_rc}")
    if loadgen_checks is None:
        reasons.append("không có loadgen.json (máy tạo tải không ghi kết quả)")
    elif loadgen_checks.get("valid") is not True:
        failed = [k for k in ("send_lag_ok", "cpu_ok", "throttle_ok") if loadgen_checks.get(k) is False]
        reasons.append(f"máy tạo tải không đạt tự kiểm: {', '.join(failed) or 'không rõ'}")

    # 2) Trạng thái đầu đúng (1 replica, hàng đợi trống; S4: N replica)
    if not initial_ok:
        reasons.append(f"trạng thái đầu sai: {initial_note}")

    # 3) Pod vLLM có mặt lúc đầu lượt phải còn nguyên tới cuối: không bị thay, không restart, không OOM.
    #    Pod MỚI do scale-up rồi bị scale-down thì không tính: đó chính là hành vi đang đo.
    end_by_name = {p["name"]: p for p in pods_end}
    for p in pods_start:
        e = end_by_name.get(p["name"])
        if e is None or e.get("deleting"):
            reasons.append(f"pod {p['name']} có từ đầu lượt đã bị thay hoặc xoá giữa lượt")
            continue
        if e["restarts"] > p["restarts"]:
            reasons.append(f"pod {p['name']} restart {e['restarts'] - p['restarts']} lần trong lượt")
    for e in pods_end:
        if "OOMKilled" in e.get("last_terminated", []):
            reasons.append(f"pod {e['name']} từng bị OOMKilled")

    # 4) Prometheus không mất mẫu quá lâu
    for target, gap in scrape_gaps.items():
        if gap is not None and gap > SCRAPE_GAP_MAX_S:
            reasons.append(f"khoảng trống scrape {gap:.0f} s ở {target} (> {SCRAPE_GAP_MAX_S:.0f} s)")

    return {
        "valid": not reasons,
        "reasons": reasons,
        "details": {
            "loadgen_rc": loadgen_rc,
            "loadgen": loadgen_checks,
            "initial_ok": initial_ok,
            "initial_note": initial_note,
            "scrape_gap_max_s": scrape_gaps,
            "pods_start": [p["name"] for p in pods_start],
            "pods_end": [p["name"] for p in pods_end],
        },
    }
