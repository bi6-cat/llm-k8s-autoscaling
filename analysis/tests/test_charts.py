"""Test cho analysis/charts.py (biểu đồ C1–C4).

Khái niệm: Dùng lại thư mục lượt giả của test_build_tables (đúng định dạng runner ghi, Môi trường §14.2).
Mục đích: Kiểm phần chuẩn bị dữ liệu bằng số cụ thể (λ(t), TTFT p95 trượt, hàng đợi cộng theo pod, chọn lượt
    counted), và kiểm phần vẽ ở mức "chạy hết, ghi đủ file, chạy lại ra đúng cùng file" (không so pixel).
"""

from __future__ import annotations

import csv
import gzip
import json
import math
from pathlib import Path

import pytest

from analysis import build_tables as bt
from analysis import charts as ch
from analysis.tests.test_build_tables import T0, _a2_scaled, _requests, write_attempt


def _add_waiting(d: Path, rows: list[tuple[float, str, float]]) -> None:
    """Thêm mẫu vllm_waiting vào metrics.csv.gz. Ghi thành member gzip thứ hai: gzip đọc nối liền nên
    DictReader thấy các dòng này ngay sau phần đã có (header chỉ ở member đầu)."""
    with gzip.open(d / "metrics.csv.gz", "at", newline="", encoding="utf-8") as fh:
        w = csv.writer(fh)
        for ts, pod, v in rows:
            w.writerow([ts, "vllm_waiting", json.dumps({"pod": pod}), v])


def test_kb2_series_rate_ttft_replicas_queue(tmp_path):
    # _requests: request i lúc i + 0,5 s; TTFT 5 s trong [240, 300), còn lại 0,2 s; request 880–899 lỗi
    d = _a2_scaled(tmp_path, requests=_requests(errors=set(range(880, 900))))
    _add_waiting(d, [(T0 + 250, "vllm-a", 3), (T0 + 250, "vllm-b", 2), (T0 + 255, "vllm-a", 1)])
    s = ch.kb2_series(d)

    edges, rate = s["rate"]
    assert edges[0] == 0 and edges[-1] == 1440 and len(rate) == 48
    assert all(math.isclose(v, 1.0) for v in rate)  # 30 request mỗi 30 s

    p95 = dict(s["ttft_p95"])
    assert p95[200.0] == pytest.approx(0.2)  # requests.csv ghi 6 chữ số, cộng t0 lệch ~1e-7
    assert p95[290.0] == 5.0  # cửa sổ (260, 290] nằm trọn trong đoạn quá tải
    # Cửa sổ (290, 320]: 10 request 5 s trên 30, phần tử p95 (thứ 28 khi sắp tăng, đếm từ 0) vẫn là 5 s;
    # cửa sổ 30 s kéo dài đoạn xấu thêm tới 30 s, giống N2b
    assert p95[320.0] == 5.0
    assert p95[330.0] == pytest.approx(0.2)
    assert p95[900.0] == math.inf  # 20/30 request lỗi: lỗi tính như TTFT vô hạn (cùng định nghĩa với N2b)
    assert s["timeout_s"] == ch.DEFAULT_TIMEOUT_S

    ready = dict(s["replicas_ready"])
    assert ready[-5.0] == 1.0 and ready[260.0] == 2.0 and ready[1195.0] == 1.0
    assert min(ready) == -5.0 and max(ready) == 1440.0  # một mẫu trước t0, không quá hết pha chính

    assert dict(s["queue"]) == {250.0: 5.0, 255.0: 1.0}  # cộng mọi pod cùng mốc
    assert s["phases"]["spike"] == (240.0, 840.0)


def test_kb2_series_last_rate_bin_uses_its_own_width(tmp_path):
    # Thời lượng 1445 s: khoảng cuối [1440, 1445] dài 5 s, có 5 request → vẫn là 1 req/s, không phải 1/6
    d = write_attempt(tmp_path, requests=_requests(n=1445))
    lg = json.loads((d / "loadgen.json").read_text(encoding="utf-8"))
    (d / "loadgen.json").write_text(json.dumps({**lg, "duration_s": 1445.0}), encoding="utf-8")
    edges, rate = ch.kb2_series(d)["rate"]
    assert edges[-2:] == [1440.0, 1445.0]
    assert rate[-1] == pytest.approx(1.0) and len(rate) == 49


def test_c1_groups_take_counted_kb2_and_report_duplicates():
    def row(counted, scen, rep, cfg, session, cap=1.0):
        run_id = f"{cfg}-{scen}-{rep}"
        return {"counted": counted, "scenario": scen, "env": "sim", "repeat": rep, "config": cfg,
                "session": session, "run_id": run_id, "capacity_rps": cap}  # fmt: skip

    rows = [
        row(True, "KB2", 1, "A2", "a"),
        row(True, "KB2", 1, "S4", "a"),
        row(False, "KB2", 2, "A2", "a"),  # không counted
        row(True, "KB1", 1, "A2", "a"),  # không phải KB2
        row(True, "KB2", 1, "A2", "b"),  # trùng lượt ở phiên thứ hai
        row(True, "KB2", 1, "S1", "a"),  # không thuộc C1_CONFIGS (Môi trường §16: C1 vẽ S4, A1, A2)
        row(True, "KB2", 1, "A1", "c", cap=2.0),  # C khác = lịch gửi khác: hình riêng
    ]
    groups, warn = ch.c1_groups(rows)
    assert sorted(groups) == [("sim", 1, 1.0), ("sim", 1, 2.0)]
    assert sorted(groups[("sim", 1, 1.0)]) == ["A2", "S4"]
    assert groups[("sim", 1, 1.0)]["A2"]["session"] == "a"
    assert list(groups[("sim", 1, 2.0)]) == ["A1"]
    assert len(warn) == 1 and "b/A2-KB2-1" in warn[0]


def test_cell_and_paired_values_skip_uncounted_and_empty():
    nan = float("nan")
    rows = [
        {"counted": True, "scenario": "KB1", "config": "A2", "slo_attainment": 0.97, "gpu_vs_baseline": 0.4},
        {"counted": True, "scenario": "KB1", "config": "A2", "slo_attainment": 0.95, "gpu_vs_baseline": nan},
        {"counted": False, "scenario": "KB1", "config": "A2", "slo_attainment": 0.10, "gpu_vs_baseline": 0.9},
        {"counted": True, "scenario": "KB1", "config": "S4", "slo_attainment": None, "gpu_vs_baseline": 1.0},
    ]
    slo = ch.cell_values(rows, "slo_attainment", 100)
    assert slo == {"KB1": {"A2": [97.0, 95.0]}}
    assert ch.paired_values(rows, "gpu_vs_baseline", "slo_attainment") == {"KB1": {"A2": [(40.0, 97.0)]}}


def test_style_and_order_are_fixed_per_config():
    assert ch.style("A2") != ch.style("S4")
    assert ch.style("X9") == ch.OTHER_STYLE  # cấu hình lạ: xám, không lấy màu của cấu hình khác
    assert ch._ordered(["A2", "Z", "S1", "B"], ch.CONFIG_ORDER) == ["S1", "A2", "B", "Z"]
    assert ch._ordered(["A2", None, "X9"], ch.CONFIG_ORDER) == ["A2", None, "X9"]  # metadata thiếu id


def _session(root: Path) -> Path:
    """Đủ 4 cấu hình × KB1, KB2 (lượt 1), cộng A2 × KB1 lượt 2, để mọi hình C1–C4 đều có dữ liệu."""
    for cfg in ("S1", "S4", "A1", "A2"):
        for scen in ("KB1", "KB2"):
            kw = {"run_id": f"{cfg}-{scen}-1", "config": cfg, "scenario": scen}
            d = _a2_scaled(root, **kw) if cfg.startswith("A") else write_attempt(root, **kw)
            _add_waiting(d, [(T0 + 300, "vllm-a", 4.0)])
    write_attempt(root, run_id="A2-KB1-2", config="A2", scenario="KB1")
    return root / "s"


def test_main_writes_every_chart_and_is_reproducible(tmp_path, capsys):
    sess = _session(tmp_path / "runs")
    out = tmp_path / "fig"
    assert ch.main([str(sess), "--out", str(out)]) == 0
    names = sorted(p.name for p in out.iterdir())
    assert names == sorted(
        f"{b}.{f}"
        for b in ("c1-kb2-sim-r1", "c2-slo-sim", "c3-gpu-sim", "c4-tradeoff-sim")
        for f in ("svg", "png")
    )
    svg = (out / "c1-kb2-sim-r1.svg").read_bytes()
    assert "Số replica".encode() in svg  # chữ có dấu được giữ (font mặc định có đủ glyph tiếng Việt)

    # Chạy lại trên cùng dữ liệu: SVG giống từng byte (không có ngày giờ, id cố định), nên commit hình vào Git
    # chỉ tạo diff khi dữ liệu hoặc code đổi
    out2 = tmp_path / "fig2"
    assert ch.main([str(sess), "--out", str(out2), "--formats", "svg"]) == 0
    for p in out2.iterdir():
        assert p.read_bytes() == (out / p.name).read_bytes(), p.name


def test_main_skips_c3_c4_without_baseline(tmp_path, capsys):
    root = tmp_path / "runs"
    _a2_scaled(root)
    assert ch.main([str(root / "s"), "--out", str(tmp_path / "fig"), "--formats", "svg"]) == 0
    assert sorted(p.name for p in (tmp_path / "fig").iterdir()) == ["c1-kb2-sim-r1.svg", "c2-slo-sim.svg"]
    assert "C3, C4 (sim): bỏ qua" in capsys.readouterr().out


def test_main_fails_when_nothing_is_counted(tmp_path, capsys):
    root = tmp_path / "runs"
    write_attempt(root, valid=False)
    assert ch.main([str(root / "s"), "--out", str(tmp_path / "fig")]) == 1
    assert not (tmp_path / "fig").exists()


def test_build_keeps_attempt_path_out_of_runs_csv(tmp_path):
    _a2_scaled(tmp_path)
    (row,) = bt.build([tmp_path / "s"])["runs"]
    assert row["path"] == tmp_path / "s" / "A2-KB2-1" / "attempt-1"
    assert "path" not in bt.RUN_COLUMNS
