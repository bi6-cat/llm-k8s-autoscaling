# Nhật ký làm việc – Trình – Tuần 08 (23–29/11/2026)

## 2026-11-23 – Luận văn: chốt bố cục

- **Task:** chung (luận văn) · **Environment:** none
- **Done:**
  1. Đọc lại các nguồn quyết định giá trị của luận văn: Bài toán §5–§9, §12–§13; ADR-002; Thông số §3–§5; Môi trường §7–§19; Kế hoạch §11–§12 và R21; nguồn tư liệu §2–§6 (bản trong PR #52).
  2. Đề xuất bố cục mới, rồi giao một agent độc lập soát với các nguồn đó. Agent trả 17 điểm (3 cao, 10 vừa, 4 thấp). Phiên chính kiểm lại các khẳng định chính với nguồn gốc (ADR-002 Q13, Bài toán §9, mô tả đồ án Phụ lục A, Kế hoạch §12.1, Môi trường §13, các cột của `runs.csv`). Áp 16 điểm, bác 1.
- **Decision:** D87: bố cục dựng quanh ba thông điệp và năm hướng giải của Bài toán §6, mỗi hướng giải đi qua đủ thiết kế, triển khai, đánh giá, kết luận. Giữ khung yêu cầu F/N và bảng nghiệm thu của ADR-002, không quay lại câu hỏi nghiên cứu và giả thuyết.
  - Ba thông điệp: (T1) scale theo tải đồng thời của vLLM, không theo GPU utilization; (T2) autoscaling tiết kiệm nhiều ở tải thấp ổn định, còn dưới tải tăng đột ngột có giới hạn với nguyên nhân đo được; (T3) nền tảng vận hành được.
  - Chương 4 gom từ 11 mục còn 7, mỗi mục đủ dày cho khung sáu bước (rủi ro R21). Chương 3 có mục 3.6 Thiết kế đánh giá, kèm các chỉ số của đề cương; chương 2 có mục Hàng đợi và năng lực phục vụ; chương 5 có mục 5.7 Hạn chế và bảng tổng hợp LT1–LT8.
  - Số trang: 4–5 / 8–10 / 10–12 / 16–20 / 12–14 / 2–3. Chương 5 nằm trong mức 12–15 trang của ADR-002 Q13.
  - Bỏ: giữ 11 mục ở chương 4 (mỏng); viết mỗi hướng giải thành một chương (lệch chuẩn trình bày, hội đồng khó theo); tách mục 4.1 theo người viết (không còn áp dụng, vì Trình viết toàn bộ bản base).
- **Results:** bản soát phát hiện các điểm có căn cứ:
  - thiếu bảng ánh xạ bảy mục tiêu của đề cương và thiếu các chỉ số P95/P99, throughput, token/GPU-giờ (`runs.csv` đã có đủ các cột này);
  - giá trị SLO được dùng ở 3.1 nhưng đến 3.5 mới định nghĩa;
  - scale-down được đặt ở hai chỗ;
  - chưa có chỗ cho ca đối chứng graceful shutdown và VH2c;
  - ba số trong thông điệp lệch nguồn: A1 ở KB1 dùng khoảng 90% GPU-giờ của S4, không phải "chỉ tiết kiệm 5–10%"; thời gian phản ứng 79,7–81,5 s; câu "mọi thay đổi đi qua Git" chỉ đúng ở cluster nhà, vì trên VM thuê nền tảng được cài bằng Helm.
- **Deviations:** mục 1.5 Đóng góp được nêu 2–3 số chính kèm dẫn chéo tới chương 5, lệch `quy-tac-viet.md` §2 (chương 1 không đặt số đo).
- **Links:** nhánh `docs/tr8-thesis-ch5-drafts`.
- **Thesis:** toàn bộ bố cục; cần sửa theo Kế hoạch §11.1, `quy-tac-viet.md` §2 và §8, `nguon-tu-lieu.md` §2.

## 2026-11-23 – Merge PR #46, #52 của Quang; gộp xung đột nhật ký qua PR #58

- **Task:** chung · **Environment:** none
- **Done:**
  - Trình merge PR #46 (Q6, `vh3-delete` giữ pod thứ hai trước khi xoá) bằng merge commit: CI 6/6 xanh, đã Approve 21/11, không có commit sau lần duyệt.
  - Sau đó #52 chuyển sang `CONFLICTING`, vì #46 và #52 cùng thêm mục vào cuối `docs/nhat-ky/lam-viec/quang/tuan-07.md`.
  - Tạo nhánh `fix/tr8-pr52-sync-main` từ đầu nhánh #52 (`72e83f5`), merge `origin/main`, gộp nhật ký theo thứ tự ngày: hai mục 16/11 của #46 đặt trước tám mục 18–20/11 của #52. Mở PR #58; CI 6/6 xanh; merge. GitHub tự đánh dấu #52 là merged.
  - Merge `main` vào `docs/tr8-thesis-ch5-drafts`: không xung đột.
- **Decision:** D88. Không đẩy commit lên nhánh của Quang; dùng PR thay thế bằng merge commit để giữ nguyên 15 commit và tác giả. Bỏ: chờ Quang tự merge `main` vào nhánh (chặn thêm), squash (mất lịch sử, #52 không tự thành merged).
- **Results:** diff của #58 so với `main`: 11 file, +944 −16, khớp từng file với #52. Nhật ký sau gộp không còn marker; tập dòng khác rỗng bằng đúng hợp của hai phía (367 dòng). CI của `main` sau #46 (`adc80b1`) xanh.
- **Incidents:** lệnh `git switch -c` thất bại khi đang merge dở ("cannot switch branch while merging"), nên commit gộp được tạo trên HEAD tách rời trước rồi mới đặt tên nhánh. Không có gì bị đẩy lên sai nhánh.
- **Links:** PR #46, #52, #58 (merge commit `6482406`).
## 2026-11-23 – Luận văn: đưa bố cục mới vào Kế hoạch §11.1 và quy tắc viết

- **Task:** TR8 · **Environment:** none
- **Done:**
  1. Thay dàn ý ở Kế hoạch §11.1 bằng bố cục chốt ngày 23/11: xương sống gồm ba thông điệp TĐ1–TĐ3 và năm hướng giải HG1–HG5; chương 4 gom 11 mục còn 7; thêm 1.4 Phương pháp và tổ chức thực hiện, 2.2 Hàng đợi và năng lực phục vụ, 3.6 Thiết kế đánh giá, 5.7 Hạn chế của phép đo, Phụ lục F; bảng truy vết yêu cầu → mục; người viết và lộ trình. Sửa §5.1 (câu phân công, bảng luận văn theo số mục mới) và tiêu chí M4, M5 cho khớp.
  2. `quy-tac-viet.md`: gộp quy tắc văn phong (giọng văn, người đọc, 20/80, mật độ gọn, câu và đoạn, cụm sáo và dấu hiệu văn do máy sinh, mã định danh, làm tròn số); thêm §2.2 trình bày quy trình và con người; §8 viết lại theo cách làm bản base, bảng ranh giới theo số mục mới; §9 khai báo công cụ AI một lần ở Lời cam đoan; cập nhật checklist.
  3. `nguon-tu-lieu.md`: đánh lại số mục ở §1, §2 theo dàn ý mới, bỏ cột người viết; sửa hai chỗ đã cũ (bảng và hình C1–C4 của V2 đã có ở `analysis/figures/v2-dg2/` từ PR #52).
  4. `docs/luan-van/README.md`: dòng người viết; bỏ quy ước tách file `a`, `b` theo người viết.
  5. Chạy `/code-review high` trên nhánh: 10 điểm, sửa cả 10 (Results).
- **Decision:** (D89)
  - Số của TĐ1–TĐ3 được đối chiếu với `analysis/figures/v2-dg2/runs.csv` trước khi ghi vào Kế hoạch. Thời gian phản ứng A2 × KB2 ghi 79,7–81,5 s theo cột `react_s` (79,71; 81,42; 81,53 s), thay cho 80–82 s đã làm tròn trong nhật ký Quang 18–19/11; dòng đó ở `nguon-tu-lieu.md` §3 cũng sửa theo. Chi tiết "A1 thêm replica từ giây 15, lên 4 replica trong 3 phút đầu" không đưa vào Kế hoạch, vì bảng đã commit không có cột để đối chiếu; TĐ1 chỉ giữ số kiểm được (A1 dùng 89,7–90,6% GPU-giờ của S4, A2 dùng 25%).
  - Kế hoạch không dẫn ADR-002 Q13 cho số trang chương 4, 5, vì Q13 đã được ADR-004 K12 thay; chỉ dẫn K12 (55–65 trang).
  - Bỏ cột "Người" ở `nguon-tu-lieu.md` §2: từ 22/11 Trình viết bản base toàn bộ, nên cột người viết không còn đúng; người soát kỹ từng mục lấy theo Kế hoạch §5.1.
  - Chưa đưa công cụ kiểm văn phong vào repo: để PR riêng có test, nên quy tắc viết chưa nhắc tới công cụ đó.
  - Kế hoạch §11.2 (slide) không dẫn số mục luận văn nên giữ nguyên.
  - Nhãn của dàn ý đổi thành TĐ1–TĐ3 (thông điệp) và HG1–HG5 (hướng giải), vì T1–T7 đã là bộ test autoscaling (Thông số F2) và P1–P7 đã là sản phẩm bàn giao (Kế hoạch §10.1). Hai nhãn chỉ dùng trong dàn ý, không vào thân bài (`quy-tac-viet.md` §4).
  - M4 (29/11) đổi thành bản base lượt 1 (mọi mục có mặt, khoảng 60% ngân sách chữ) gửi Quang review; tiêu chí "hai thành viên đã review chéo toàn bộ" chuyển sang M5 thành "Quang đã review toàn bộ bản base". Lý do: Trình viết base, Quang review sau khi base xong, nên tiêu chí cũ không đạt được đúng hạn.
  - Bản nháp `03-04-giam-sat-slo-canh-bao.md` đổi tên thành `03-05-…` ngay trong PR này, đánh lại tiêu đề, số bảng tạm và dẫn chéo theo số mục mới (nội dung giữ nguyên), để không còn hai mục 3.4 khi ghép thử.
- **Results:**
  - lychee 0.24.2 (offline, kèm anchor, bỏ qua đường dẫn cũ như job `docs`): 0 lỗi.
  - `/code-review high` báo 10 điểm, đã kiểm lại từng điểm với file và sửa cả 10:
    - §5.1 (đoạn và bảng luận văn) còn số mục cũ;
    - mã P và T trùng mã đã có;
    - tiêu chí M4 mâu thuẫn với lộ trình;
    - "7 lượt có vi phạm SLO" chưa nói rõ cách đếm: `runs.csv` có 7 lượt có `slo_violation_s`, trong đó A2 × KB3 (2 lượt) vẫn đạt SLO attainment 100% trên cả lượt;
    - quy tắc mã F/N mâu thuẫn với §5 và mục 1.3;
    - cộng khoảng trang chỉ được 52–64 (đã ghi cách đạt 55);
    - LT ở 5.2 lệch §11.1;
    - bản nháp 3.4 chưa đổi số;
    - dòng F4 ở Môi trường §16 ghi "bằng `make`" trong khi nhật ký Quang 18/11 cho thấy chạy tay từng lệnh;
    - phần đầu các tài liệu thiết kế 01, 03, 04, 05 còn dẫn số mục cũ.
- **Deviations:** phần "thay đổi so với dàn ý trước" ở Kế hoạch §11.1 chỉ giữ 6 ý chính, không chép đủ 8 ý của bản nháp bố cục.
- **Links:** PR #59, merge commit `31a3ae5` (CI 6/6 xanh, MERGEABLE, không có review); sau đó merge `origin/main` vào `docs/tr8-thesis-ch5-drafts`, nhật ký tuần 08 gộp đúng thứ tự. `docs/chi-tiet/06-ke-hoach-quan-ly.md` (§3 M4, M5; §5.1; §11.1; §11.4); `docs/chi-tiet/01`, `03`, `04`, `05` (phần đầu; 05 dòng F4); `docs/luan-van/quy-tac-viet.md`, `nguon-tu-lieu.md`, `README.md`, `03-05-giam-sat-slo-canh-bao.md`.
- **Thesis:** dàn ý toàn bộ; 1.4 (cách trình bày quy trình); Lời cam đoan (khai báo công cụ AI).

## 2026-11-23 – TR8: sửa Hình 7 (SLO → cảnh báo → runbook) cho khớp cái đã làm

- **Task:** TR8 (luận văn), TR4 · **Environment:** none
- **Done:**
  1. Đối chiếu `fig_slo_alert()` ở `docs/diagrams/build_diagrams.py` với `common/observability/alerts/llm.yaml`, `rules/slo.yaml`, `common/platform/alertmanager-values.yaml`, `common/platform/gpu-exporter/`, `docs/runbooks/` và `envs/cloud/README.md`, theo 6 điểm lệch ghi ngày 18/11.
  2. Sửa hình: nguồn GPU là `nvidia_gpu_exporter` (đọc nvidia-smi), chỉ vẽ dashboard; bỏ cảnh báo nhiệt độ và XID; ô Alert rule ghi 7 quy tắc (SLO, pod, HPA, KEDA); kube-state-metrics có thêm condition của ScaledObject (nguồn của `KedaScalerErrors`); hành động bỏ "thắt giới hạn tốc độ", thêm "xoá pod chậm" và "đề xuất thêm GPU" theo runbook; ô Git ghi Argo CD chỉ sync ở nhà, VM thuê áp lại bằng `make cloud-platform`.
  3. Sinh lại SVG, xuất PNG, tự xem ảnh PNG để kiểm cả 6 điểm.
  4. `/code-review high`: 8 điểm, sửa cả 8. Đáng kể nhất: nhãn "inhibit mặc định của chart" đặt giữa page và ticket vẫn gợi ý sai, vì inhibit mặc định (critical chặn warning/info) không chạm tới page và ticket, nên bỏ hẳn; ticket ghi "không nhắc lại trong 24 h" thay cho "báo một lần" (cảnh báo mới vào cùng nhóm vẫn có tin sau `group_interval` 5 phút); critical của chart chuyển thành chú thích riêng dưới khung Alertmanager; ô Recording rule tách TTFT (1, 5, 30 phút) và lỗi 5xx (5 phút); script xuất PNG ghi ra file tạm rồi mới thay, để lần xuất hỏng không xoá PNG đã commit.
- **Results:** chỉ `07-slo-canh-bao-runbook.svg` và `.png` đổi; các hình khác sinh lại giống hệt (khác duy nhất ở CRLF, đã đổi về LF). shellcheck đạt. ruff trên `build_diagrams.py` báo 8 lỗi, đúng bằng số lỗi trước khi sửa (thư mục `docs/diagrams/` không nằm trong CI).
- **Incidents:**
  - `export_png.sh` báo xuất xong nhưng không ghi PNG nào: trong Git Bash, `file://$PWD/...` thành `file:///d/Data/...`, Chrome trên Windows không mở được; thêm nữa, `--screenshot` với đường dẫn tương đối không ghi vào thư mục hiện tại; script giấu output của Chrome nên không thấy lỗi. Sửa: đổi đường dẫn bằng `cygpath -m`, ghi `--screenshot` bằng đường dẫn tuyệt đối, tự chọn Chrome của Windows khi có `cygpath`, báo lỗi khi Chrome không ghi được file.
  - `python -I build_diagrams.py` lỗi `No module named 'chuyen_sau'`, vì `-I` bỏ thư mục của script khỏi `sys.path`; chạy không kèm `-I` (code trong repo).
  - Python trên Windows ghi SVG bằng CRLF; chạy `sed -i 's/\r$//'` sau khi sinh.
- **Deviations:** PNG của Hình 7 nay xuất bằng Chrome trên Windows (font Segoe UI), các PNG khác vẫn là bản Quang xuất trên macOS; khác font nhẹ khi đặt cạnh nhau.
- **Links:** nhánh `docs/tr8-fig7-slo-alerts`; `docs/diagrams/build_diagrams.py`, `docs/diagrams/export_png.sh`, `docs/images/07-slo-canh-bao-runbook.svg`, `docs/images/png/07-slo-canh-bao-runbook.png`.
- **Thesis:** Hình 7 dùng được cho §3.5 (chưa chèn vào bản mẫu 3.5, vì bản mẫu đang chờ Trình duyệt).
## 2026-11-23 – Đưa bộ soát văn phong luận văn vào repo (`analysis/kiem_van.py`)

- **Task:** TR8 · **Environment:** none
- **Done:**
  1. Chuyển bộ soát văn phong (trước đó chỉ có trên máy của Trình) vào `analysis/kiem_van.py`: docstring theo CONTRIBUTING §2, type hint, tên mỗi luật kèm § của `quy-tac-viet.md` hoặc README; tách hàm thuần `check_text()` trả về danh sách điểm để test được; CLI bằng `argparse`, bỏ trống thì soát mọi file mục `docs/luan-van/CC-SS-*.md`, mã thoát 0 (sạch), 1 (còn điểm), 2 (không đọc được file) như ruff.
  2. Thêm 3 luật có sẵn trong `quy-tac-viet.md` mà bản cũ chưa đếm: đường dẫn `docs/` và link Markdown tương đối trong thân bài (§3.5); nhãn dàn ý TĐ/HG và mã biểu đồ C1–C6 (§4); cụm "với mục tiêu" (§3.4).
  3. Sửa 3 chỗ bắt sai của bản cũ: tách câu ngắt nhầm trước chữ thường có dấu (khoảng `À-Ỹ` của regex cũ gồm cả chữ thường như "ở"); đoạn dẫn và mục danh sách bị báo thiếu nguồn dù comment nguồn đặt sau cả danh sách; công thức riêng dòng `$$…$$` bị đếm như đoạn văn một câu. Luật nguồn cũng chặt hơn: comment nguồn phải đứng ngay sau khối (chỉ cách bởi dòng trống, comment khác hoặc danh sách đi liền), không còn được tính khi nằm sau đoạn kế tiếp trong cửa sổ 3 dòng.
  4. `analysis/tests/test_kiem_van.py`: 46 cặp ca vi phạm/viết đúng phủ mọi luật (một test kiểm mỗi luật, kể cả luật viết thẳng trong `check_text`, đều có ca), cùng test cho tách khối, tách câu, tìm nguồn, thống kê, giới hạn 5 điểm mỗi luật và mã thoát.
  5. Thêm dòng chạy `kiem_van` vào checklist `quy-tac-viet.md` §10; cập nhật cây thư mục ở CONTRIBUTING §1 và header `analysis/pyproject.toml`.
  6. Việc làm trong lượt tự chạy 23/11. Nhánh `feat/tr8-style-checker` đã push; lệnh tạo PR bị chế độ quyền của lượt tự chạy chặn, nên PR chờ Trình mở.
- **Decision:** (D91)
  - Đặt trong gói `analysis/` thay cho gói Python riêng: module chỉ dùng thư viện chuẩn, gói `analysis` đã phục vụ luận văn, và job `python` của CI đã chạy pytest, ruff cho gói này trên 3.11 và 3.15, nên không phải thêm `pyproject.toml`, `uv.lock` và bước CI mới. Bỏ phương án đặt cạnh `docs/diagrams/build_diagrams.py` vì chỗ đó không có test và lint.
  - CI chỉ chạy test của module, không chạy soát trên `docs/luan-van/`: vài luật chỉ là gợi ý cần người đọc lại (từ nối, dấu hai chấm, chữ "agent" của k3s), nên nếu chặn merge thì sẽ đỏ giả. Mã thoát 1 dành cho người viết và người soát trước khi mở PR.
- **Results:**
  - `uv run --project analysis --locked pytest analysis`: 207 passed (56 của `kiem_van`) trên Python 3.15; test `kiem_van` trên Python 3.11: 56 passed. `ruff check`, `ruff format --check`, `yamllint -s .`: đạt. lychee 0.24.2 (offline, kèm anchor, bỏ qua đường dẫn cũ như job `docs`): 0 lỗi.
  - So bản cũ với bản mới trên 4 file nháp (03-05, 05-03, 05-05b, 05-06): số điểm giống nhau ở mọi luật, trừ "đoạn ngoài 3–7 câu" của 03-05 (8 xuống 6, hai dòng công thức `$$`) và "thiếu nguồn" của 05-05b (4 xuống 2) và 05-06 (4 xuống 3), đều là đoạn dẫn hoặc mục danh sách có nguồn đặt sau cả danh sách. Tổng: 52 → 50, 29 → 29, 46 → 44, 13 → 12.
  - `/code-review high` báo 10 điểm; đã thử lại từng điểm bằng đoạn mẫu và sửa cả 10, mỗi điểm thêm một ca test:
    - "số dính đơn vị" bắt nhầm `k3s`, `K8s`;
    - "prompt" bị coi là chuyện nội bộ, trong khi đó là thuật ngữ của LLM;
    - mã việc Q1–Q8, TR1–TR8 (§3.5) chưa bị bắt;
    - comment mở giữa dòng và đóng ở dòng sau bị đọc như văn xuôi;
    - comment nguồn đặt cuối dòng của đoạn không được tính;
    - "Chương 5", "Mục 3", "§5" bị đòi nguồn;
    - tiêu đề hoặc bảng nằm giữa không ngắt luật "hai đoạn liền mở bằng từ nối";
    - file có BOM làm dòng tiêu đề thành văn xuôi, file không phải UTF-8 gây traceback thay cho mã thoát 2;
    - in đậm ở đầu câu thứ hai bị coi là in đậm giữa câu;
    - test "mọi luật đều có ca" chưa xét luật viết thẳng trong `check_text`; kèm hai lỗi nhỏ cùng loại: rào code `~~~` và "khủng hoảng" bị bắt là văn nói.
  - Sau khi sửa, số điểm trên 4 file nháp không đổi so với dòng trên.
- **Links:** `analysis/kiem_van.py`, `analysis/tests/test_kiem_van.py`, `docs/luan-van/quy-tac-viet.md` §10, `CONTRIBUTING.md` §1, `analysis/pyproject.toml`.
- **Thesis:** không vào thân bài; công cụ dùng ở bước soát mọi mục (quy-tac-viet.md §10).

## 2026-11-24 – kiem_van: độ dài câu và đoạn thành gợi ý đọc lại

- **Task:** TR8 · **Environment:** none
- **Done:** bỏ hai luật "câu > 35 chữ" và "đoạn ngoài 3–7 câu" khỏi `analysis/kiem_van.py`. Thêm bốn luật gợi ý đọc lại, in ở phần riêng sau các điểm và không tính vào mã thoát: câu > 45 chữ, đoạn > 8 câu, 3 đoạn ≤ 2 câu liền nhau (chuỗi ngắt ở tiêu đề, bảng, công thức và mục danh sách; báo một lần mỗi chuỗi), ", nên" hơn một lần trong đoạn. Dòng tổng in thêm số gợi ý. Test thêm ca cho bốn luật gợi ý, ca chuỗi đoạn ngắn, ca in gợi ý sau điểm, và ca mã thoát 0 khi chỉ có gợi ý. Dòng kiem_van ở `quy-tac-viet.md` §10 ghi rõ phần gợi ý không cần về 0.
- **Decision:** theo việc bỏ trần cứng câu và đoạn ở quy tắc viết (PR quy tắc viết theo luận văn ngoài, nhánh `docs/tr8-style-external-theses`). Lý do: khi luật trả mã thoát 1, người viết sửa cho về 0 và văn bị dài đều nhau. Ngưỡng gợi ý (45 chữ, 8 câu) đặt cao hơn ngưỡng cũ, để chỉ báo chỗ thật sự nên đọc lại.
- **Results:** `uv run --project analysis --locked pytest analysis`: 212 passed (Python 3.15); test `kiem_van` trên Python 3.11: 61 passed; `ruff check`, `ruff format --check` đạt. Chạy trên nháp 5.7 (nhánh `docs/tr8-thesis-ch5-drafts`): 0 điểm, 1 gợi ý (đoạn đầu có 3 lần ", nên"), mã thoát 0.
- **Links:** `analysis/kiem_van.py`, `analysis/tests/test_kiem_van.py`, `docs/luan-van/quy-tac-viet.md` §10; PR #61.
## 2026-11-23 – TR8: bản base mục 3.1 (yêu cầu và chỉ tiêu nghiệm thu)

- **Task:** TR8 · **Environment:** none
- **Done:**
  1. Đọc Kế hoạch §11.1 (dàn ý 3.1), `quy-tac-viet.md` §2–§5, §10, Thông số §3–§8, Bài toán §6, §8–§12, ADR-005 T3, ADR-006 §3.1, Môi trường §6.1, §13, §19, Kiến trúc §7.1.
  2. Viết `docs/luan-van/03-01-yeu-cau-chi-tieu.md`: 4 tiểu mục (từ bài toán tới yêu cầu; mã định danh; yêu cầu chức năng; SLO và chỉ tiêu), 5 bảng (truy vết, mã định danh, F1–F7, SLO, N1–N8), comment nguồn sau mỗi đoạn và bảng. Agent viết nháp; Trình chưa đọc lại.
  3. Kiểm: `kiem_van.py` lần đầu 5 điểm (một cụm "việc … việc", 3 đoạn 2 câu, 1 câu 42 chữ), sửa còn 0; lychee 0 lỗi; pandoc ghép được.
  4. `/code-review high`: 10 điểm, sửa cả 10. Chính: ngưỡng 99% không 5xx ở Traefik không có số trong lượt đánh giá (thêm ghi chú vào bảng); câu "mỗi chỉ tiêu có một ngưỡng" sai vì N2b và phần KB2 của N1, N3 chỉ báo cáo; comment nguồn ghi V2 ngày 14–15/11 (kế hoạch) trong khi V2 thật chạy 18–19/11; lý do ngưỡng 30 phút dựng lại tính theo model 7B (khoảng 15 GB) nên thân bài nói rõ; KB2 giữ đỉnh tới phút 14 chứ không "giữ 10 phút"; VH2 cũng chạy trên VM (bằng annotation); "co giãn" thay bằng "tự điều chỉnh số replica"; vai trò A3, A4.
- **Decision:** đặt bảng mã định danh ngay sau bảng truy vết (3.1.2), trước bảng F/N, vì các bảng F/N dùng mã KB, ĐG, VH; bố cục ghi bảng mã ở cuối nhưng không quy định thứ tự. Bảng của 3.1 đánh số chính thức 3.1–3.5 (không dùng số tạm), vì 3.1 là mục đầu chương 3.
- **Results:** 1.181 chữ văn xuôi, 19 đoạn, 62 câu, trung bình 19,0 chữ/câu; kiem_van 0 điểm. `git log -L` trên `00-thong-so.md`: mọi dòng ngưỡng N1–N8, TPOT, 95%, 99% không đổi từ 08/10; dòng TTFT chỉ đổi ghi chú ngày 10/11, giá trị 2,5 s giữ nguyên.
- **Incidents:** câu nháp "histogram TTFT không có biên 2 s" không có nguồn trong repo (ADR-005 T3 chỉ nói ngưỡng 2 s lệch bucket 2,5 của recording rule); thử tìm danh sách bucket trong `vllm/v1/metrics/loggers.py` v0.31.0 thì thấy bucket sinh từ hàm `histogram_buckets()`, chưa đọc tiếp; đã viết lại câu theo đúng ADR-005 T3.
- **Deviations:** mục 3.1 vượt ngân sách lượt 1 (chương 3 lượt 1 khoảng 2.000 chữ, 3.5 đã 1.464 chữ). Chỗ cắt được nếu cần: đoạn lý do ngưỡng chất lượng và thời gian (khoảng 250 chữ) chuyển xuống phụ lục; bảng mã định danh chuyển sang danh mục mã ở phần đầu quyển. `00-thong-so.md` vẫn gắn nhãn "tạm" cho TTFT 2,5 s và N2b vì ADR-003 chưa viết; thân bài 3.1 không nhắc ADR, comment nguồn ghi rõ.
- **Links:** `docs/luan-van/03-01-yeu-cau-chi-tieu.md`, `docs/luan-van/nguon-tu-lieu.md` (dòng 3.1).
- **Thesis:** §3.1; danh mục mã định danh ở phần đầu quyển lấy từ Bảng 3.2.
## 2026-11-23 – Luận văn: viết lại mục 3.5 thành mẫu văn

- **Task:** TR8 · **Environment:** none
- **Done:**
  1. Viết lại `docs/luan-van/03-05-giam-sat-slo-canh-bao.md` theo bố cục mới (Kế hoạch §11.1) và `quy-tac-viet.md`: tiêu đề "Thiết kế giám sát, cảnh báo và xử lý sự cố"; bốn tiểu mục SLI và dashboard, cảnh báo theo burn rate, danh sách cảnh báo và định tuyến, xử lý sự cố và vai trò người trực (mới, theo Vận hành §4, §6 và runbook `LLMSLOBurnFast`). Comment thông điệp và trạng thái soát ở đầu file.
  2. Đối chiếu lại số với `docs/chi-tiet/00-thong-so.md` §3, §4, §6; `04-van-hanh.md` §2.1, §2.2, §3.1–§3.5, §4, §6; `03-kien-truc-autoscaling.md` §13.4; `llm.yaml`, `slo.yaml`, `alertmanager-values.yaml`, `scaledobject-a2.yaml`, ba dashboard.
  3. Bản viết đầu còn 1.854 chữ văn xuôi, nên rút tiếp còn 1.367 chữ. Chạy `/code-review high`, sửa 10 điểm, bản cuối 1.464 chữ.
  4. Cập nhật `nguon-tu-lieu.md` (dòng 2.5, 3.3, 3.5, 4.6, 6.2) để ghi phần đã chuyển ra khỏi 3.5.
- **Decision:** Bản cũ có 2.407 chữ, trong khi trần của cả chương 3 (6 mục) là 3.000–3.600 chữ, nên chỉ giữ những gì phục vụ ba thông điệp của mục. Chuyển sang 4.6: bảng nguồn metric và chu kỳ scrape, retention, NaN khi không có traffic, chuyện chọn lại tín hiệu `KedaScalerErrors`, khuôn tin Telegram. Chuyển sang 6.2 (3.5 chỉ dẫn chéo): điểm yếu `LLMErrorRateHigh`, chưa có dead man's switch. Chuyển sang 3.1: cột giá trị SLO. Chuyển sang 2.5: định nghĩa SLI, SLO, burn rate, vai trò hai cửa sổ, vì sao không dùng ngưỡng p95. Bảng định tuyến chuyển thành văn xuôi. Thân bài không còn mã F/N. Giữ công thức ước tính thời gian báo (dự đoán LT8) ở 3.5.2, vì đó là lý do chọn cặp cửa sổ 5 phút và 1 phút. Giữ tên file để không phải sửa link. Chưa chèn Hình 7, vì hình còn lệch 6 điểm (nhật ký 18/11). Phương án bỏ: chỉ sửa lỗi văn phong của bản cũ (vượt xa ngân sách); cắt còn khoảng 600 chữ (mất phần ước tính và vai trò người trực mà bố cục yêu cầu).
- **Results:** `kiem_van.py`: bản cũ 50 điểm, bản mới 0 điểm (1.464 chữ, 19 đoạn, 71 câu, trung bình 20,6 chữ/câu). `lychee --offline --include-fragments` trên `docs/luan-van/*.md`: 0 lỗi. `pandoc … --citeproc` ra `.docx`: không lỗi, không cảnh báo trích dẫn.
- **Incidents:** `/code-review high` xác nhận 10 điểm, đã sửa cả 10:
  - câu "đã kiểm hai biên 2,5 s và 0,1 s trên `/metrics`" không có nguồn cho biên 0,1 s;
  - mất câu đánh đổi "cửa sổ ngắn nhạy hơn với đợt xấu ngắn", trong khi thông điệp nói "đợt chậm ngắn không page";
  - mất ý tin "đã hết" tới muộn tới 5 phút (`group_interval`);
  - câu "`KedaScalerErrors` page sau 1 phút" đánh giá thấp độ trễ;
  - mốc 20% của cảnh báo và của page giả đo từ hai nguồn khác nhau nhưng không nói ra;
  - câu "dashboard cho cùng một số" không đúng với panel TPOT và panel ngân sách lỗi;
  - con số 12 phút xuất hiện trước công thức dùng để tính nó;
  - các khái niệm 3.5 dùng thẳng chưa được giao cho chương 2;
  - phần chuyển sang 4.6 và 3.3 chưa được ghi lại ở nguồn tư liệu.
- **Links:** nhánh `docs/tr8-thesis-3-5-sample`; `docs/luan-van/03-05-giam-sat-slo-canh-bao.md`, `docs/luan-van/nguon-tu-lieu.md`.
- **Thesis:** §3.5 (mẫu văn, chờ Trình duyệt trước khi viết các mục khác của chương 3).
## 2026-11-23 – TR8: bản base mục 3.6 (thiết kế đánh giá)

- **Task:** TR8 · **Environment:** none
- **Done:**
  - Trình (viết cùng agent, lượt tự chạy) viết bản base `docs/luan-van/03-06-thiet-ke-danh-gia.md` theo dàn ý ở Kế hoạch §11.1. Bản này có 7 tiểu mục và 7 bảng:
    - ba lớp đánh giá;
    - tải và kịch bản tải;
    - ĐG1–ĐG3;
    - chỉ số theo đề cương và quy tắc so sánh;
    - điều kiện hợp lệ của một lượt;
    - VH1–VH6 và cách chấm cảnh báo;
    - LT1–LT8.
  - Phần "Cách đo" của VH6 (mốc vi phạm, page giả, thời gian tới cảnh báo) được viết ở 3.6.6 theo dàn ý. Nhánh nháp chương 5 không bị sửa.
  - Mọi đoạn và bảng có số đều kèm comment nguồn: § của `docs/chi-tiet/`, mã nguồn `analysis/` và `experiments/runner/`, nhật ký vận hành.
- **Decision:**
  - Không chèn Hình 8 và Hình 17, vì Hình 8 còn thời lượng cũ 20/25/25 phút và Hình 17 còn Argo CD trên VM thuê. Bảng 3.6b và 3.6c dùng thay. Hai hình phải vẽ lại trước khi chèn.
  - Số bảng tạm là 3.6a–3.6g, vì mục 3.2–3.4 chưa viết.
  - ĐG3 viết "khi thêm một replica" thay cho "scale 1 → 2" của thiết kế. Lý do: ở V2, mức L0 được đo 0 → 1 vì containerd không xoá được image đang dùng (`van-hanh.md` 19/11), và LT4 ở nhà cũng đo 0 → 1. Mục 5.4 sẽ ghi lệch này; comment nguồn của 3.6 đã nhắc.
  - Phần LT không khẳng định mọi dự đoán đều tính trước khi đo. Theo `van-hanh.md`, dự đoán của LT4 được tính sau khi đã có số đo lần A, nên 3.6 ghi rằng chương 5 nêu rõ các ca như vậy.
  - Không ghi công cụ cụ thể của ĐG1 ở V2, vì chưa đối chiếu được.
- **Results:**
  - `kiem_van.py`: 2.305 chữ văn xuôi, 31 đoạn, 111 câu, 0 điểm cần xem.
  - lychee 0.24.2 (offline, kèm anchor): 0 lỗi. Pandoc ghép thử `docs/luan-van/[0-9]*.md` ra `.docx` được.
  - `/code-review high` báo 10 điểm. Từng điểm được đối chiếu với mã nguồn, git log và nhật ký, và cả 10 đã được sửa:
    - lý do bỏ S1 × KB1 ghi sai thành "autoscaling chạy 1 replica", trong khi A1 scale lên ở KB1 (đúng là A2);
    - "không thể chỉnh theo kết quả" nói quá, vì `analysis/dg2_a2.py` và `vh6_window.py` được thêm ngày 21/11, sau V2; chỉ `metrics.py` (sửa lần cuối 16/11) được chốt trước;
    - ĐG3 1 → 2 khác với cách đo L0 ở V2;
    - định nghĩa thời gian hồi phục SLO chưa khớp `metrics.slo_recovery_s`;
    - phân vị chỉ tính trên request thành công;
    - VH6: độ kịp chỉ chấm ở S1 × KB3;
    - lý do 10 phút của pha tăng đột ngột là cold start đo ngày 08/11, không phải flapping;
    - TTFT/TPOT ánh xạ sai sang P95/P99 của đề cương;
    - chỉ độ lệch lịch gửi, event loop và CPU được chấm theo từng tiến trình;
    - kiểm thử chức năng chỉ chạy trong CI ở phần tự động hoá được.
- **Deviations:** 2.305 chữ văn xuôi, vượt ngân sách chương 3 (10–12 trang cho 6 mục; 3.1 và 3.5 đã khoảng 2.650 chữ). Ba chỗ cắt được: đoạn quy ước tính (chuyển sang 5.1), chi tiết reset, làm ấm và cooldown (sang 4.7), đoạn ca đối chứng (sang 5.5).
- **Links:** PR #64; `docs/luan-van/03-06-thiet-ke-danh-gia.md`.
- **Thesis:** 3.6; dẫn chéo từ 3.1 (mục 3.6), 4.7 (runner kiểm tính hợp lệ), 5.1–5.5.
## 2026-11-23 – Luận văn: đo trang bằng dàn trang thử, chốt ngân sách từng mục chương 3

- **Task:** TR8 · **Environment:** none
- **Done:**
  1. Dàn trang thử bốn bản nháp chương 3 (3.1, 3.3, 3.5, 3.6) bằng pandoc 3.13 và Typst 0.15.1, theo hai khuôn A4 giãn 1,5 dòng: khuôn A Times New Roman 13 pt, lề 2/2/3/2 cm; khuôn B 14 pt, lề 3,5/3/3,5/2 cm. Bảng dùng cỡ chữ nhỏ hơn văn xuôi 1 pt, được ngắt qua trang, cột co theo nội dung.
  2. Ghi vào quy tắc viết: ngân sách theo trang (§1), thứ tự cắt khi vượt ngân sách (§3.1), quy tắc bảng (§6). Thêm ngân sách từng mục chương 3 vào Kế hoạch §11.1.
- **Decision:** Trình giao việc chọn độ dài, yêu cầu nội dung chuyên nghiệp, đúng trọng tâm 20/80 và câu nào cũng có giá trị.
  - Giữ tổng 55–65 trang (ADR-004 K12) và khoảng trang của từng chương. Ngân sách đổi đơn vị từ "300 chữ mỗi trang" sang **trang, gồm cả bảng và hình**.
  - Chương 3 lấy mức trên, 12 trang: mở đầu và kết chương 0,5 · 3.1 1,5 · 3.2 2 · 3.3 2,5 · 3.4 1,5 · 3.5 2 · 3.6 2. Mục 3.3 nhiều nhất vì mang TĐ1.
  - Không chọn nâng chương 3 lên 14–16 trang: phải lấy chỗ của chương 4 hoặc chương 2, trong khi gần một nửa số trang thừa là bảng.
  - Script dàn trang chỉ để trên máy, không đưa vào repo. Khi có khuôn .docx của trường thì đo lại bằng `--reference-doc` và Word.
- **Results:** số trang (mỗi mục dàn riêng, nên trang cuối lẻ tính tròn một trang):

  | Phần | Khuôn A | Khuôn B |
  |---|---|---|
  | 3.1 (1.181 chữ văn xuôi, 5 bảng) | 5 | 7 |
  | 3.3 (1.659 chữ, 3 bảng) | 5 | 6 |
  | 3.5 (1.464 chữ, 2 bảng) | 4 | 5 |
  | 3.6 (2.305 chữ, 7 bảng) | 10 | 13 |
  | Bốn mục ghép liền | 22 | 29 |
  | Chỉ văn xuôi của bốn mục (6.609 chữ) | 13 | 16 |

  Văn xuôi khoảng 510 chữ/trang (A) và 415 chữ/trang (B). Bảng trung bình 0,5–0,75 trang mỗi bảng. Bốn mục mới viết gấp 2,75–3,6 lần ngân sách 8 trang của chính chúng, và đã vượt 10–12 trang của cả sáu mục.
- **Incidents:** lần dàn đầu, bảng không ngắt qua trang (để lại trang gần trống) và cột chia đều, nên số trang bị đội; lần sửa thứ hai đếm số cột từ file Markdown, lệch vì có bảng trong comment. Cuối cùng giữ số cột Pandoc sinh ra, chỉ đổi độ rộng sang `auto`, và soát bằng ảnh trang trước khi lấy số.
- **Links:** `docs/luan-van/quy-tac-viet.md` (§1, §3.1, §6); `docs/chi-tiet/06-ke-hoach-quan-ly.md` (§11.1).
- **Thesis:** áp cho mọi mục; trước mắt là cắt 3.1, 3.3, 3.5, 3.6 về ngân sách, và viết 3.2, 3.4 theo ngân sách.

## 2026-11-24 – Luận văn: đo ba nháp chương 5, chốt ngân sách chương 5, cắt 5.3

- **Task:** TR8 · **Environment:** none
- **Done:**
  1. Đo ba nháp chương 5 bằng dàn trang thử (`.work/tools/do_trang/run.sh`, khuôn B: 14 pt, lề 3,5/3/3,5/2 cm): 5.3 = 8 trang, 5.5b (VH4, VH6) = 8, 5.6 = 8; tổng ba nháp gấp khoảng 4 lần phần ngân sách tương ứng.
  2. Chốt ngân sách chương 5 theo trang và ghi vào Kế hoạch §11.1 (đoạn Cân đối).
  3. Cắt 5.3 (`docs/luan-van/05-03-autoscaling-so-voi-tinh.md`) từ 3.500 xuống khoảng 830 chữ văn xuôi: bảng 11 ô ghi khoảng thấp nhất–cao nhất thay cho số từng lượt; bỏ đoạn mô tả lại kịch bản KB2 (đã có ở 3.6), tốc độ xử lý của pod cũ, chi tiết pha tăng dần và pha duy trì của KB3, thời điểm A1 bớt pod; viết lại theo quy-tac-viet §4 (tối đa 4 mã mỗi đoạn, tên pha tiếng Việt). Các ý đã cắt ghi trong comment đầu file kèm nguồn (`analysis/dg2_a2.py` phần 1–4).
- **Decision:** ngân sách chương 5 = 14 trang (mức trên của 12–14): 5.1 ≈ 1 · 5.2 ≈ 1,5 · 5.3 ≈ 4 · 5.4 ≈ 1,5 · 5.5 ≈ 3 (VH4 và VH6 khoảng 1,25) · 5.6 ≈ 2 · 5.7 ≈ 1. 5.3 tăng từ 3 lên 4 trang vì trả lời câu hỏi chính và hình diễn biến KB2 (518 × 619 pt) chiếm gần trọn một trang; hình SLO attainment theo GPU-giờ chuyển sang Phụ lục E. Phương án bỏ: giữ 5.3 = 3 trang (phải bỏ phân tích hàng đợi, là kết quả chính của mục); đo với hình trôi (lệch với cách đo của chương 3).
- **Results:** 5.3 sau khi cắt: 3,61 trang khuôn A, 3,96 trang khuôn B (ngân sách 4); `kiem_van.py` 0 điểm; lychee 59/59 OK. Không đổi số liệu so với nguồn; hai chỗ diễn đạt lại có tính từ nguồn: A1 × KB2 tiết kiệm 4,6–4,9% GPU-giờ (1 − 0,9537 và 1 − 0,9514), A1 lên 4 replica sau 166–181 s.
- **Deviations:** Kế hoạch §11.1 đổi ngân sách mục của chương 5 (5.1 1,5 → 1; 5.3 3 → 4); tổng chương 5 vẫn trong khoảng 12–14 trang.
- **Links:** nhánh `docs/tr8-thesis-ch5-drafts` (chưa PR); `docs/chi-tiet/06-ke-hoach-quan-ly.md` §11.1.
- **Thesis:** §5.3; chương 2 (mục 2.4) phải định nghĩa flapping, vì 5.3 dùng thẳng thuật ngữ này. Còn cắt: 5.6 (8 → 2 trang), 5.5b (8 → 1,25 trang).

## 2026-11-24 – Luận văn: cắt nháp 5.6 về 2 trang

- **Task:** TR8 · **Environment:** none
- **Done:**
  1. Cắt `docs/luan-van/05-06-bang-nghiem-thu.md` từ 8 trang (khuôn B) về ngân sách 2 trang: gộp hai bảng F1–F7 và N1–N8 thành một Bảng 5.6a 4 cột (yêu cầu/chỉ tiêu, mức, kết quả hoặc phần còn thiếu, kết luận); ngưỡng dẫn chéo sang Bảng 3.1, bảng đầy đủ kèm số từng lượt dành cho Phụ lục E; bỏ đoạn điều kiện đo (đã ở 5.1) và danh sách năm mức kết luận (đưa vào chú thích bảng).
  2. Viết lại văn xuôi theo quy-tac-viet §3–§5: khoảng giá trị kèm số lượt, tối đa 4 mã mỗi đoạn, mỗi đoạn có comment nguồn ngay sau. Ý đã cắt ghi trong comment đầu file kèm nguồn.
  3. Soát độc lập (`/code-review high`): 10 điểm, sửa cả 10 (phạm vi KB1, KB3 của N1; N2b không có ngưỡng ở Bảng 3.1 nên bỏ "dự kiến 5 phút"; thêm bằng chứng phần đã đạt của F1, F5, F7; đủ hai điều kiện của N3 và ba phần của N6; giải thích page ở A2 × KB3 không phải page giả; ghi số lượt; gọi mốc so sánh nhất quán là cấu hình tĩnh; sửa comment số cột và dẫn chéo sang file có trong repo).
- **Results:** 2.463 → 463 chữ văn xuôi, 2 → 1 bảng; đo 1,55 trang khuôn A, 1,95 trang khuôn B (ngân sách 2); `kiem_van.py` còn 1 điểm (đoạn mở mục 2 câu, mâu thuẫn §2 với §3.2 đã biết); lychee đạt. Không đổi số liệu so với nguồn; A2 × KB1 = 0,25 GPU-giờ của S4 đối chiếu lại `analysis/figures/v2-dg2/runs.csv`.
- **Deviations:** mục 5.6 chưa có bảng kiểm chứng LT1–LT8 như Kế hoạch §11.1; 5.6 đã dùng gần hết 2 trang, nên khi thêm bảng LT phải đưa bảng vào Phụ lục E hoặc lấy chỗ từ mục khác của chương 5.
- **Links:** nhánh `docs/tr8-thesis-ch5-drafts` (chưa PR).
- **Thesis:** §5.6. Còn cắt: 5.5b (8 → 1,25 trang).

## 2026-11-24 – Luận văn: cắt nháp 5.5b (VH4, VH6) về 1,25 trang

- **Task:** TR8 · **Environment:** none
- **Done:**
  1. Cắt `docs/luan-van/05-05b-vh4-vh6.md` từ 8 trang (khuôn B) về ngân sách 1,25 trang (D96): bỏ cả ba bảng (thời gian fallback ba lượt, SLO theo ba khoảng, mốc của 7 page), số từng lượt dành cho Phụ lục E; bỏ phần cách đo của VH6 (đã ở 3.6, PR #64), hai cấu hình quyết định fallback (để 4.3), chuỗi cảnh báo `KedaScalerErrors` trên simulator, danh sách cảnh báo khác và hai đoạn giới hạn.
  2. Viết lại văn xuôi theo quy-tac-viet §3–§4: câu đầu đoạn là kết luận, tối đa 4 mã mỗi đoạn, mã N chỉ ở câu so với chỉ tiêu, tên pha tiếng Việt. Ý đã cắt ghi trong comment đầu file kèm nguồn; giới hạn của VH4, VH6 và lỗ hổng "cảnh báo lỗi gửi tin đi qua chính đường đang hỏng" chuyển sang `nguon-tu-lieu.md` §6 cho mục 5.7 và 6.2.
  3. Soát độc lập (`/code-review high`): 10 điểm, sửa cả 10 (bỏ khẳng định "không tin nào tới Telegram", chỉ giữ "không có bằng chứng"; thêm số TPOT so sánh vì 5.3 không còn TPOT; "có cửa sổ 1 phút vi phạm SLO" để không mâu thuẫn với SLO attainment 100% của A2 × KB3; nêu đợt kêu sót từ lượt trước không chấm; mốc bắt đầu của thời gian fallback; "ở tải thấp" trong câu chủ đề; sửa dẫn chéo §3.5.5 và mục 4.3; ghi chi tiết cách chấm VH6 cho 3.6 hoặc Phụ lục E; ghi 300 s chờ scale-down là số tính từ cấu hình, chưa đo).
- **Results:** 4.503 → 512 chữ văn xuôi (đếm của `kiem_van.py`), 3 → 0 bảng; đo 0,96 trang khuôn A, 1,25 trang khuôn B (ngân sách 1,25); `kiem_van.py` 0 điểm; lychee đạt. Không đổi số liệu so với nguồn.
- **Links:** nhánh `docs/tr8-thesis-ch5-drafts` (chưa PR); `docs/luan-van/nguon-tu-lieu.md` §6.
- **Thesis:** §5.5 (VH4, VH6), §5.7, §6.2; Phụ lục E (bảng từng lượt, lấy từ commit `bc49ff6`). Việc đo và cắt ba nháp chương 5 đã xong.

## 2026-11-24 – Luận văn: bản base mục 5.4 Cold start (ĐG3, LT4)

- **Task:** TR8 · **Environment:** none
- **Done:**
  1. Viết `docs/luan-van/05-04-cold-start.md` từ 5 lượt hợp lệ của ĐG3 (`runs/v2-vm/dg3-v2-4060ti/{L0-1,L0-2,L2-1,L2-2,L2-3}`: `summary.txt`, `vllm_log.json`). Bảng 5.4a chia thời gian theo tám pha (mốc kubelet cho pha 1–4, mốc vLLM cho pha 4–8), ghi khoảng giá trị; số từng lượt để trong comment cho Phụ lục E. Câu mở mục ghi rõ L0 đo 0 → 1, L2 đo 1 → 2.
  2. Đọc thêm log vLLM của 9 pod mới trong ba lượt A2 × KB2 bằng `parse_vllm_log` để giải thích vì sao cold start trong ĐG2 (65–66 s) ngắn hơn ĐG3 L2.
  3. Soát độc lập (`/code-review high`): 10 điểm. Sửa 8 điểm ở 5.4: pha 4 tách được bằng mốc `container_started`, `api_server_start`, `engine_init_start`; dòng "nạp weights" của bảng đổi thành "khởi tạo model và nạp weights", thêm dòng con theo log vLLM; hạ mức chắc chắn của giải thích page cache; chỉ dùng tên L0/L2; câu định nghĩa cold start; tổng tính chính xác tới 0,1 s; sửa ghi chú thứ tự lượt; đổi GiB/GB. Hai điểm ngoài 5.4 cũng sửa: câu bước scale-down đầu ở 5.3 thêm "nhiều khả năng" (lượt 2 không khớp với cửa sổ 300 s), Kế hoạch §11.1 "14–16 trang" thành "tối đa 16 trang". Thêm hai dòng hạn chế vào `nguon-tu-lieu.md` §6.
- **Decision:** D97: tổng cold start lấy `ready_seen_unix − trigger_unix` (chính xác tới 0,1 s) thay cho `trigger_to_ready_s` nguyên giây, để bảng cộng đúng từng pha. N5 vì vậy đổi từ 25,4% thành 25,3% ở 5.4 và 5.6; số nguyên giây vẫn ghi trong comment nguồn. Phương án bỏ: giữ số nguyên giây, khi đó tỷ lệ và tổng các pha lệch nhau tới 0,7 s.
- **Results:**
  - Từ lệnh scale tới Ready: L2 75,7–80,8 s (3 lượt), L0 301–311 s (2 lượt). L2 bằng 25,3% L0 theo trung bình, 26,9% ở cặp lượt bất lợi nhất, nên N5 đạt.
  - L0: kéo image 9,04 GB mất 154–156 s (khoảng một nửa), tải model 54,2–56,8 s, torch.compile 18,0–20,2 s (L2: 1,2–1,3 s nhờ compile cache).
  - L2: pha khởi động tiến trình 42,6–43,0 s, chiếm 52,7–56,8%. Trong đó 28,3–28,7 s trôi qua trước dòng log đầu của vLLM. Tài liệu thiết kế ước tính 5–15 s cho pha này.
  - LT4: vLLM báo nạp 5,75 GiB weights mất 7,7–7,8 s ở L2 (khoảng 0,8 GB/s) và 0,99–1,14 s ở L0. Tốc độ đĩa của VM chưa đo, nên chưa kiểm được phần định lượng. Nạp weights chiếm không quá 10,3% cold start.
  - ĐG2 A2 × KB2: 9 pod mới nạp weights 1,01–1,04 s, phù hợp với page cache ấm; phần này giải thích khoảng 6,7 s trong khoảng chênh 10–16 s so với ĐG3.
  - Đo trang: 1,21 trang khuôn A, 1,49 trang khuôn B (ngân sách 1,5); 472 chữ văn xuôi; `kiem_van.py` 0 điểm; lychee `docs/luan-van/` đạt. 5.3 sau khi sửa: 3,99 trang B (ngân sách 4).
- **Incidents:** lần đo trang đầu chạy `run.sh` với biến thư mục rỗng, nên `cat` tạo file `all.md` rỗng ở gốc repo. File đã được xoá trước khi commit. Theo `trigger_unix`, thứ tự đo là L2-2 → L0-2 → L2-1 → L2-3 → L0-1, tức chỉ 2 trong 3 lượt L2 chạy sau L0-2; nhật ký Quang 19/11 ghi "ba lượt".
- **Deviations:** phép so với cluster nhà (LT4 16/11, model 0,5B) bỏ khỏi thân bài để giữ ngân sách. Ý này ghi trong comment đầu file, để dùng cho bảng LT1–LT8 (5.6) hoặc Phụ lục E.
- **Links:** nhánh `docs/tr8-thesis-ch5-drafts` (chưa PR); `docs/luan-van/05-04-cold-start.md`; `nguon-tu-lieu.md` §6.
- **Thesis:** §5.4, §5.6 (N5, LT4), §5.7 (hạn chế ĐG3); Phụ lục E (số từng lượt trong comment đầu 5.4).

## 2026-11-24 – Luận văn: bản base mục 5.1 và 5.2 (môi trường đo, năng lực một replica)

- **Task:** TR8 · **Environment:** none
- **Done:** viết `05-01-moi-truong-dieu-kien-do.md` (phiên V2: phần cứng, phần mềm, tham số request, lý do đổi máy, thứ tự đo, điều kiện hợp lệ, chi phí) và `05-02-nang-luc-mot-replica.md` (ĐG1, Bảng 5.2a, LT1–LT3). Nguồn: `capacity.json`, `matrix-dg1-v2.yaml`, nhật ký Quang tuần 06–07, `van-hanh.md` LT1–LT3, log vLLM và `checks.json` của 22 lượt. Soát số độc lập trên cả hai file, sửa 10 điểm, rồi cắt lại về ngân sách.
- **Decision:** 5.1 chỉ nêu giá trị xấu nhất của các điều kiện hợp lệ, không lập bảng, vì bảng ngưỡng đã có ở 3.6. Chi phí thực tế V2 ghi là chưa có (chưa đối chiếu hoá đơn), so sánh chi phí dùng GPU-giờ theo giả định G1. Giả thuyết "C bám TPOT ở batch lớn" chỉ ghi ở mức "có thể": C ở hai máy chỉ biết với bước 0,5 req/s, nên tỷ lệ C thật nằm trong 1,13–1,43, và phiên A4000 chạy vLLM với 2 lõi CPU.
- **Results:**
  - ĐG1 (RTX 4060 Ti, model 3B): C = 3,5 req/s, B* = 46,3, threshold A2 = 37. Ở λ = 4: SLO attainment 28,5%, đang chờ TB 12,4.
  - LT1: TPOT với 1 request chậm hơn cận dưới weights ÷ băng thông khoảng một phần tư (nhà 8,68 so với 6,9 ms; A4000 17,2 so với 13,8 ms). V2 đo C cao hơn tỷ lệ băng thông thuần (2,893 req/s) 21,0%.
  - LT2: dự đoán 36.864 B/token, V2 đo 36.843 B/token (7,26 GiB cho 211.584 token), lệch 0,06%.
  - LT3: điểm gãy giữa λ = 3,5 và 4, lúc số request đang chạy chạm 64 (63,5 ở λ = 4). Throughput bão hoà suy ra từ TPOT p50 62,6 ms khoảng 4,0 req/s. TPOT p50 tăng 53,6% khi B tăng từ 16 lên 46.
  - Điều kiện hợp lệ, giá trị xấu nhất trên 22 lượt: send lag p99 5,98 ms, CPU máy tạo tải 43,6%, khoảng trống scrape 5,0 s.
  - Đo trang (khuôn B, ngân sách D96): 5.1 0,99 trang (1), 5.2 1,49 trang (1,5). `kiem_van.py`: 5.2 0 điểm; 5.1 1 điểm ngày tháng ở đoạn đầu, chủ ý theo quy-tac-viet §5. lychee hai file đạt.
- **Incidents:**
  - Soát số tìm ra: LT1 ghi "chậm khoảng 20%" trong khi số trong câu cho 25–26%; 5.1 viết `--max-num-seqs` như giới hạn request nhận vào, trong khi đó là giới hạn batch; LT2 viết "lệch dưới 0,1% như ở nhà", nhưng ở nhà vLLM làm tròn tới 0,1 GiB; comment đầu file nêu tên công cụ soát, trái quy-tac-viet §9; thiếu comment thông điệp (§2). Đã sửa cả năm điểm.
  - Hai lần lệnh Bash bị treo vì một lệnh `cat >` thừa chờ stdin. Đã dừng tác vụ và chạy lại.
- **Deviations:** băng thông 288 và 448 GB/s là thông số của NVIDIA, chưa có mục trong `tai-lieu.bib`; ghi trong comment nguồn, thêm khi ghép chương. Các file 5.3–5.6 trên nhánh vẫn dùng dạng comment cũ (nêu tên công cụ soát, thiếu comment thông điệp).
- **Links:** nhánh `docs/tr8-thesis-ch5-drafts` (chưa PR); `docs/luan-van/05-01-moi-truong-dieu-kien-do.md`, `docs/luan-van/05-02-nang-luc-mot-replica.md`.
- **Thesis:** §5.1, §5.2, §5.6 (bảng LT), §5.7 (C thô do bước 0,5; V2 không đo TPOT 1 request; giả thuyết LT1 chưa kiểm).

## 2026-11-24 – Luận văn: bản base đầy đủ mục 5.5 Kịch bản vận hành (VH1–VH6, graceful shutdown)

- **Task:** TR8 · **Environment:** none
- **Done:**
  1. Gộp `05-05b-vh4-vh6.md` vào `05-05-kich-ban-van-hanh.md` (`git mv`), giữ nguyên chữ phần VH4, VH6, thêm đoạn mở mục, VH1 (dẫn chéo 5.3), VH2 kèm ca đối chứng VH2c, VH3, VH5 và tiểu mục 5.5.7 graceful shutdown kèm ca đối chứng grace 5 s. Số tiểu mục theo mã kịch bản (5.5.k = VHk).
  2. Số lấy từ `runs/v2-vm/ops-vh*/summary.json` và `timeline.json`, `experiments/ops/vh.py`, nhật ký Quang tuần 07 (16/11, 18/11, 19/11), `van-hanh.md` (06/11, 09/11, 16/11). Bản nháp do agent soạn; một lượt soát độc lập đối chiếu từng số với nguồn.
  3. Đo trang, cắt về ngân sách, soát văn bằng `kiem_van.py`, soát độc lập rồi sửa, đo lại.
- **Decision:** bỏ bảng kết quả VH2/VH3 (5 dòng) khỏi thân bài, vì với bảng mục 5.5 đo 3,93 trang khuôn B so với ngân sách 3 (D96). Số của bảng đã có trong văn xuôi hoặc comment nguồn, nên bảng chuyển sang Phụ lục E. Số request của VH2, VH3 là của cả lượt tải (1.200–2.400 s), không phải của khoảng rolling update, nên không đặt cạnh thời gian rollout. Kết quả drain trên simulator (22,1 s) bỏ khỏi thân bài vì chỉ kiểm logic script.
- **Results:**
  - VH2 (V2, 1,75 req/s): ca 1 replica rolling update 141 s, ca 4/4 GPU `maxSurge: 0` 372 s, ca đối chứng `maxSurge: 1` kẹt sau 300 s với 1 pod Pending; cả ba 0 lỗi (2.077 / 4.229 / 2.077 request cả lượt).
  - VH3: xoá pod khi có 2 pod, thay thế Ready sau 67,4 s, 0 lỗi / 1.351; kill tiến trình con: Ready lại sau 67,4 s nhưng 129 lỗi / 1.041 (117 lỗi kết nối).
  - VH5: 8 phút 22 giây từ VM trắng (bấm tay, 1 lần). Graceful shutdown ở nhà: 144/144 stream, ca grace 5 s cắt 48/48.
  - Đo trang: 2,41 trang khuôn A, 2,93 trang khuôn B (ngân sách 3); 1.171 chữ văn xuôi, không bảng. `kiem_van.py` 0 điểm; lychee `docs/luan-van/` 0 lỗi.
- **Incidents:** soát độc lập báo 10 điểm, đều đã sửa. Nặng nhất: 5.5.7 khẳng định mỗi lần tắt pod giữ GPU tới 3 phút, trong khi VH2b trên V2 thay 4 pod (`maxSurge: 0`, pod mới phải chờ GPU của pod cũ) trong 371,6 s, khoảng 93 s mỗi pod, gần bằng cold start L2. Như vậy pod cũ trên V2 có lẽ đã thoát sau khoảng 15–20 s, khác với ở nhà. Câu đó giờ chỉ nói về máy nhà và nêu quan sát trên V2 như một suy luận chưa kiểm bằng log. Các điểm khác: rollout được kích hoạt bằng annotation trong pod template, không phải annotation của Deployment; làm tròn thời gian ≥ 100 s về số nguyên (sửa cả 104,5 → 104 s ở 5.6); câu lồng ", tức"; trộn số đo với suy luận trong một câu; đoạn mở mục dạng "Mục này…"; VH4 lặp điều kiện tải của đoạn mở; nhãn simulator cho drain; "mọi tiến trình" sửa thành tiến trình con.
- **Deviations:** SLO trong lúc rolling update (tiêu chí VH2 ở Môi trường §13) chưa tính: chưa có script tính SLO theo mốc của VH2 (`vh4_windows.py` chỉ nhận mốc của VH4). Cảnh báo trong các lượt VH2–VH4 không được lưu, nên vế "có cảnh báo" của VH2c và VH3 chưa kiểm được.
- **Links:** nhánh `docs/tr8-thesis-ch5-drafts` (chưa PR); `docs/luan-van/05-05-kich-ban-van-hanh.md`, `docs/luan-van/05-06-bang-nghiem-thu.md`, `docs/luan-van/nguon-tu-lieu.md`.
- **Thesis:** §5.5; §5.7 (vh3-kill có lẽ chỉ 1 pod; hành vi SIGTERM của vLLM trên V2 khác ở nhà, chưa kiểm bằng log; không lưu cảnh báo trong VH2–VH4); §4.5 (VH2 trên VM kích hoạt qua annotation, không qua Git).

## 2026-11-24 – Luận văn: bản base mục 5.7 Hạn chế của phép đo và kết chương 5

- **Task:** TR8 · **Environment:** none
- **Done:**
  1. Viết `docs/luan-van/05-07-han-che-phep-do.md` từ `nguon-tu-lieu.md` §6 (phần phép đo) và các chỗ ở 5.2, 5.4, 5.5, 5.6 dẫn "(mục 5.7)". Bản nháp do agent soạn; Trình chưa đọc lại.
  2. Đo trang, cắt về ngân sách, soát văn bằng `kiem_van.py`, soát độc lập rồi sửa, đo lại cả mục và cả chương 5.
- **Decision:** 5.7 chỉ nêu hạn chế chưa có ở mục khác: cỡ mẫu (1–3 lượt mỗi ô, 6/11 ô chỉ 1 lượt; hai kết luận chính vẫn giữ vì mọi lượt cùng chiều), bước tải ĐG1 0,5 thay vì 0,25, L0 đo từ 0 lên 1, LT1 chưa đo trên 4060 Ti, VH4 một lượt ở 0,5 C, VH6 chỉ chấm `LLMSLOBurnFast`, bản ghi thiếu của VH2–VH4, kịch bản vận hành chưa chạy ở nhà. Những ý mục khác đã nêu (máy 4060 Ti ở 5.1, page cache và tốc độ đĩa ở 5.4, Telegram ở 5.5.6) và các giới hạn nhỏ (metadata ghi commit khi tree dirty, không sao lưu R2, 2 lõi CPU ở phiên thử A4000) chuyển vào comment "Ý không đưa vào". Hạn chế của hệ thống để 6.2.
- **Results:**
  - 5.7: 405 chữ văn xuôi, không bảng; 0,75 trang khuôn A, 0,96 trang khuôn B (ngân sách 1, gồm kết chương). `kiem_van.py` 0 điểm; lychee 0 lỗi.
  - Cả chương 5 (05-01 tới 05-07, bỏ comment): 11,61 trang khuôn A, 13,68 trang khuôn B, trong ngân sách 14 trang (D96).
- **Incidents:** bản đầu dài 703 chữ (2 trang); cắt ba lần. Soát độc lập báo 10 điểm, đều đã sửa. Các điểm chính: bỏ sót giới hạn VH4, VH6 mà 05-05 hẹn đưa vào 5.7; kết chương chỉ nêu Service chia đều là nguyên nhân KB2, bỏ cold start mà 5.3 nêu ngang hàng; "cảnh báo kêu ở mọi lượt vi phạm" thiếu phạm vi "17 lượt so sánh cấu hình"; giải thích sai nguyên nhân C thô (do bước 0,5, không do mỗi mức 1 lượt); "LT1 chưa kiểm" mâu thuẫn 5.2 (đã kiểm ở nhà và A4000); câu mở "mọi số đo từ một phiên" sai vì chương có số ở nhà và simulator; "khâu gửi tin chưa kiểm" mâu thuẫn 5.5.6 (đã kiểm trên simulator).
- **Links:** nhánh `docs/tr8-thesis-ch5-drafts` (chưa PR); `docs/luan-van/05-07-han-che-phep-do.md`.
- **Thesis:** §5.7, kết chương 5; §6.2 nhận phần hạn chế của hệ thống (ghi trong comment đầu file).

## 2026-11-24 – Luận văn: chuẩn hoá comment đầu các file chương 5, kết thúc lượt tự chạy 4 giờ

- **Task:** TR8 · **Environment:** none
- **Done:** Lượt tự chạy 08:33 xong 7 vòng: cắt 5.3, 5.5b, 5.6 về ngân sách D96; viết base 5.1, 5.2, 5.4, 5.5, 5.7. Vòng 8 hết quota giữa lúc chuẩn hoá comment đầu file 5.3–5.7, để lại phần sửa chưa commit; script thoát mà không ghi dòng dừng. Phiên sau soát và commit phần đó: bỏ tên công cụ soát, thêm `<!-- Thông điệp -->` (5.3, 5.4, 5.6), đưa dòng soát về dạng `Soát số · Soát văn phong · Người viết đọc lại`, đổi câu mở 5.3 và 5.6 khỏi dạng "Mục này…" (quy-tac-viet §2).
- **Results:** đo lại khuôn B: 5.3 = 3,99 trang (bản trước khi sửa cũng 3,99; ngân sách 4), 5.6 = 1,95 trang (ngân sách 2). kiem_van còn 1 điểm ở đoạn mở 5.6 (2 câu), có từ trước, do mâu thuẫn quy-tac-viet §2 (đoạn mở 1–2 câu) với §3.2 (đoạn 3–7 câu), chưa sửa.
- **Links:** `docs/luan-van/05-03-…`, `05-04-…`, `05-06-…`, `05-07-…`; tổng kết lượt `.work/auto/runs/20261124-0833/` (cục bộ).
## 2026-11-24 – Luận văn: bỏ ngân sách trang từng mục, sửa dàn ý và quy tắc đề mục

- **Task:** TR8 · **Environment:** none
- **Done:**
  1. Ghép một bản đọc liền mạch (cục bộ, không commit) từ `main` và 8 nhánh luận văn chưa merge, có khung cho các mục chưa viết, rồi đo số trang từng mục theo khuôn B: đã có 28,4 trang base (chương 3: 11,5; 4.3: 3,05; chương 5: 13,8).
  2. Trình đọc bản ghép và nêu hai vấn đề: (a) độ dài không nên ép theo ngân sách, miễn nội dung có giá trị; (b) đề mục con nhiều mà mỗi mục ngắn, nhìn rời rạc, thiếu chuyên nghiệp.
  3. Đo độ dài từng đề mục của bản base và tìm quy định độ dài của các trường khác; so với một luận văn thạc sĩ cùng chủ đề.
  4. Sửa dàn ý ở Kế hoạch §11.1 (bảng đề mục, đoạn **Độ dài** thay đoạn "Cân đối", lộ trình, lý do), quy tắc viết §1, §2, §2.1, §3.1, §8, §10, nguồn tư liệu §2, ADR-004 K12 và §7.
- **Decision:** Trình đồng ý cả bốn điểm của đề xuất:
  - Độ dài theo nội dung lõi; định hướng 70–90 trang thân bài theo khuôn B, trần 100; bỏ ngân sách trang từng mục. Khoảng theo chương: 1: 5–6 · 2: 12–15 · 3: 15–18 · 4: 22–26 · 5: 16–20 · 6: 3–4. Không chọn giữ 55–65 trang, vì đó là con số nhóm tự đặt ở ADR-004 khi rút gọn phạm vi, không phải quy định của trường, và bản base viết theo ngân sách đó đã mất phần lý do.
  - Quy tắc đề mục: chỉ đặt tiêu đề khi nội dung dài từ khoảng 1 trang; mục dưới 2,5 trang không chia cấp 3; tiêu đề nói nội dung, không nói bước của khung hay mã kịch bản. Chương 1 gộp 6 mục còn 4; 5.3 đưa TĐ1 lên tiểu mục đầu; 5.5 gom 7 tiểu mục theo mã VH thành 3 theo chỉ tiêu N4, N6, N7; scale-down chuyển từ 5.3 sang 5.5.1.
  - Mỗi chương một PR, thay cho các PR từng mục (#62–#64, #66–#69); mốc M4 (29/11) là đủ mục theo dàn ý mới; phần lõi đã cắt ở chương 3, 5 được khôi phục tới trước hạn nộp.
- **Results:**
  - Bản base viết theo ngân sách cũ: phần lớn tiểu mục cấp 3 chỉ có 55–300 chữ (⅛–⅔ trang), ví dụ 3.2.3: 72 chữ, 5.5.1: 55, 5.5.5: 54; tiểu mục TĐ1 ở chương 5 (5.3.4) chỉ 110 chữ. Trước khi cắt, 5.3 có 3.500 chữ, sau khi cắt còn 830.
  - Quy định của các trường khác: ĐH KHTN TP.HCM 50–100 trang; một trường CNTT và Truyền thông 60–80 trang không kể phụ lục, mỗi nhóm tiểu mục ít nhất hai tiểu mục; Khoa CNTT ĐH Kinh tế Quốc dân tối thiểu 50 trang. Chưa tìm thấy quy định công khai của PTIT. Luận văn thạc sĩ Aalto về autoscaling Kubernetes: 54 trang thân bài, mục cấp 2 trung bình 2,5–3 trang.
  - Khuôn ảnh hưởng tới số trang: cả chương 5 (bản base ngày 24/11) đo 11,61 trang khuôn A (13 pt) và 13,68 trang khuôn B (14 pt), B dài hơn khoảng 18%.
  - `lychee --offline --include-fragments` trên `docs/**/*.md` và `*.md`: 719 link, 0 lỗi.
  - `/code-review high` trên diff: 9 điểm (2 quan trọng: tên 4.3.2 trái quy tắc mới; quy tắc 1 trang chưa miễn cho "Kết chương", "Cấu trúc luận văn"), đã sửa cả 9.
- **Deviations:** dàn ý ngày 23/11 (PR #59) và ngân sách trang ngày 23/11 (PR #65) được thay sau một ngày; các bản base 3.1–3.6, 4.3 và chương 5 sẽ phải sửa đề mục.
- **Links:** `docs/chi-tiet/06-ke-hoach-quan-ly.md` (§3 M4, §11.1); `docs/luan-van/quy-tac-viet.md`; `docs/luan-van/nguon-tu-lieu.md`; `docs/luan-van/README.md`; `docs/adr/004-dieu-kien-thuc-te-va-pham-vi-rut-gon.md`.
- **Thesis:** áp cho toàn bộ luận văn; căn cứ về độ dài có thể nêu ngắn khi trả lời hội đồng.

## 2026-11-24 – Luận văn: chọn khuôn trình bày từ hai đồ án mẫu của khoa

- **Task:** TR8 · **Environment:** none
- **Done:**
  1. GVHD gửi hai đồ án tốt nghiệp năm 2025 của Khoa Công nghệ Thông tin 1 làm mẫu: một đồ án chương trình tiên tiến viết tiếng Anh (.docx) và một đồ án hệ chính quy viết tiếng Việt (.pdf). Nhóm thuộc hệ chính quy nên luận văn viết tiếng Việt. Trình dặn hai mẫu chỉ là căn cứ tham khảo vì đề tài khác, không áp dập khuôn.
  2. Trích định dạng và cấu trúc: file .docx đọc style, section, mục lục bằng python-docx và pandoc; file .pdf đo vị trí từng ký tự bằng pdfplumber (khổ giấy, lề, cỡ chữ, khoảng dòng, thụt đầu dòng, vị trí chú thích, đầu trang, chân trang).
  3. Đo số trang bằng Word (COM, trên bản sao, không lưu): áp khuôn B, khuôn của mẫu tiếng Anh và khuôn T đề xuất lên bản đọc gộp ngày 24/11; áp khuôn của mẫu tiếng Anh lên chính file mẫu để kiểm tra cách giả lập.
  4. Ghi khuôn T vào quy tắc viết §1, §2; sửa Kế hoạch (dòng tóm tắt đầu file, §11.1: cột "Trang", đoạn **Phần đầu**, đoạn **Độ dài**, lý do thay đổi), nhật ký thay đổi của ADR-004 (K12) và README luận văn.
- **Decision:**
  - Khuôn T: A4; lề trên 2,5 cm, dưới 2,5 cm, trái 3 cm, phải 2 cm; Times New Roman 13 pt, giãn dòng 1,15, cách sau đoạn 6 pt, thụt đầu dòng 1,27 cm; chương 16 pt đậm căn giữa, sang trang mới; đầu trang và chân trang theo mẫu tiếng Việt. Ba chỗ khác mẫu: khổ A4 thay Letter (mẫu tiếng Việt dùng Letter, có lẽ do mặc định của Word); tên bảng đặt trên bảng theo IEEE và thông lệ tiếng Việt (hai mẫu đặt dưới); giữ cách đánh số `3.4.1.` và "Hình 3.1." vì hai mẫu không thống nhất với nhau.
  - Phần đầu quyển theo hai mẫu (bìa, Lời cảm ơn, hai trang nhận xét, mục lục và ba danh mục), giữ Lời cam đoan (chỗ khai báo dùng công cụ AI) và Tóm tắt 1 trang dù hai mẫu không có; bỏ *Abstract* và trang nhiệm vụ đồ án; không có phần "Mở đầu" riêng vì lặp chương 1.
  - Độ dài đổi đơn vị sang khuôn T, đo bằng Word: định hướng 60–75 trang thân bài, trần 85, cùng nội dung với mốc 70–90 trang, trần 100 theo khuôn B. Không tăng độ dài theo mẫu: phần dài của hai mẫu là sơ đồ và đặc tả use case, đề tài này không có.
  - Không dùng nguyên khuôn của mẫu tiếng Anh (dòng đơn, lề trên 1,5 cm) vì thuộc chương trình khác và lề trên quá hẹp.
  - Việc soát văn phong theo luận văn mẫu thu hẹp lại: không khảo sát thêm 4–6 luận văn bên ngoài trước M4. Hai mẫu cho biết mức GVHD chấp nhận, và văn của chúng không chặt hơn quy tắc hiện có, nên quy tắc văn phong giữ nguyên.
- **Results:**
  - Mẫu tiếng Việt: 125 trang, khổ Letter; Times New Roman 13 pt; khoảng dòng trung vị 17,5 pt (khoảng 1,17 lần dòng đơn), thêm 7,5 pt giữa hai đoạn; thụt đầu dòng 1,27 cm; lề trái 3 cm, phải 2 cm; chú thích hình và bảng 13 pt nghiêng, căn giữa, đặt dưới; 8 chương, chương 2–7 kết bằng mục "Kết luận"; trung vị 521 chữ trên trang chỉ có chữ. Thân bài 113 trang, trong đó chương phân tích và thiết kế 65 trang.
  - Mẫu tiếng Anh: 89 trang, A4, 13 pt dòng đơn, cách 6 pt trước và sau đoạn, lề trên/dưới/trái/phải 1,5/1,7/3,5/2 cm; 5 chương, thân bài 74 trang, chương phân tích và thiết kế 42 trang; 55 ảnh, 35 bảng.
  - Kiểm cách giả lập: áp khuôn của mẫu tiếng Anh lên chính file đó, vị trí các chương lệch bản gốc không quá 0,6 trang trên 89 trang.
  - Bản đọc gộp, chương 1–6 (gồm cả khung chưa viết): khuôn B 41,24 trang, khuôn T 27,67 trang; B dài gấp 1,49 lần T (từng chương 1,41–1,57). Mục 3.1–3.5: Typst cho 9,54 trang khuôn B, Word cho 11,97 trang (Typst thấp hơn khoảng 20%). Suy ra 1 trang khuôn B cũ bằng khoảng 0,85 trang khuôn T.
  - `lychee --offline --include-fragments` trên 4 file đã sửa: 94 link, 0 lỗi.
  - `/code-review high` trên diff: 6 điểm (2 quan trọng: khoảng trang chương 4 và 5 không khớp quy tắc nhân 0,85 rồi làm tròn, nay là 19–22 và 14–17, cộng 63–75 trang; số chữ mỗi trang chỗ ghi 450, chỗ ghi 500), đã sửa cả 6.
- **Incidents:** script Word lần đầu lỗi ở lệnh `Quit(0)` (COM trong PowerShell đòi tham số `[ref]`) và để lại một tiến trình Word chạy ngầm; số liệu của cả 6 lượt đo đã ghi đủ, tiến trình được tắt. Lần chạy sau, PowerShell trải phẳng mảng một phần tử nên đường dẫn file sai; sửa bằng `,@(...)`.
- **Links:** `docs/luan-van/quy-tac-viet.md` (§1, §2); `docs/chi-tiet/06-ke-hoach-quan-ly.md` (§11.1); `docs/adr/004-dieu-kien-thuc-te-va-pham-vi-rut-gon.md`; `docs/luan-van/README.md`.
- **Thesis:** bước định dạng (file `--reference-doc` theo khuôn T); căn cứ về độ dài khi hội đồng hỏi.

## 2026-11-24 – Luận văn: thêm phần Mở đầu, bỏ trang Lời cam đoan

- **Task:** TR8 · **Environment:** none
- **Done:** thêm phần Mở đầu vào thứ tự các phần của quyển (quy tắc viết §1) và vào bảng "mỗi chương nói gì" (§2); thêm dòng Mở đầu vào bảng dàn ý, bỏ mục 1.4 "Cấu trúc luận văn" khỏi chương 1 (Kế hoạch §11.1); cập nhật bảng nguồn tư liệu cho Mở đầu và chương 1. Bỏ trang Lời cam đoan khỏi phần đầu quyển; chuyển khai báo dùng công cụ AI sang đoạn cuối của Mở đầu (quy tắc viết §1, §3.5, §9; Kế hoạch §11.1).
- **Decision:**
  - Trình đề nghị giữ phần Mở đầu để dẫn dắt và mô tả nhanh từng chương, thay cho lựa chọn "không có Mở đầu" ở mục trước. Lý do: đây là thông lệ của đồ án hệ chính quy, mẫu tiếng Việt của khoa có phần này, và hội đồng đọc nó trước để nắm bức tranh chung. Để không lặp với chương 1, hai phần chia vai trò: Mở đầu (không đánh số, 1,5–2 trang) dẫn dắt ở mức người không chuyên và mô tả ngắn từng chương, không có số đo hay chi tiết kỹ thuật; chương 1 giữ bối cảnh, mục tiêu, phạm vi, phương pháp và đóng góp kèm số, còn 3–4 trang. Tóm tắt vẫn giữ vì nêu kết quả kèm số.
  - Trình đề nghị bỏ trang Lời cam đoan vì hai mẫu không có. Lời khai báo dùng công cụ AI vẫn giữ, vì dự án dùng công cụ AI cho cả viết mã, phân tích số liệu và soạn văn bản. Khai báo đặt ở đoạn cuối của Mở đầu: hội đồng đọc phần này trước, nên khai báo không bị khuất như khi để ở phụ lục, và chương 1–6 vẫn không nhắc tới công cụ AI. Nếu GVHD hoặc khoa quy định chỗ khai báo khác thì chuyển sang đó.
- **Results:**
  - Cộng các khoảng trang của chương 1–6 trong bảng dàn ý được 62–74 trang; định hướng chung giữ 60–75 trang thân bài khuôn T, trần 85. Mở đầu (1,5–2 trang) không tính vào thân bài.
  - `/code-review high` trên diff: 6 điểm nhỏ (Mở đầu chưa rõ có tính vào thân bài không, chưa có tên file nên lệnh ghép có thể bỏ sót, chưa có trong thứ tự viết và bảng phân công, ý lý do cũ mâu thuẫn, §3.5 chưa ghi ngoại lệ cho đoạn khai báo), đã sửa cả 6.
- **Links:** `docs/luan-van/quy-tac-viet.md` (§1, §2, §3.5, §9); `docs/chi-tiet/06-ke-hoach-quan-ly.md` (§5.1, §11.1); `docs/luan-van/nguon-tu-lieu.md`; `docs/luan-van/README.md` (tên file `00-00-mo-dau.md`).
- **Thesis:** phần Mở đầu; mục 1.4 cũ không còn.

## 2026-11-24 – Luận văn: bỏ trang Tóm tắt và đoạn khai báo dùng công cụ AI

- **Task:** TR8 · **Environment:** none
- **Done:** bỏ trang Tóm tắt khỏi phần đầu quyển và khỏi thứ tự viết; bỏ đoạn khai báo dùng công cụ AI ở cuối Mở đầu (quy tắc viết §1, §3.5, §9; Kế hoạch §5.1, §11.1). Sửa dòng Mở đầu ở bảng §5.1 thành "cùng soát".
- **Decision:**
  - Trình chọn bỏ trang Tóm tắt vì hai mẫu không có. Khi đã có Mở đầu, Tóm tắt thành phần tóm lược thứ ba cùng với Mở đầu và mục 1.3; 2–3 kết quả chính kèm số vẫn nằm ở mục 1.3.
  - Trình chọn không đưa đoạn khai báo dùng công cụ AI vào luận văn: hai mẫu không có, và nhóm chưa thấy quy định nào của trường. Câu mẫu giữ ở quy tắc viết §9, để thêm vào cuối Mở đầu nếu GVHD hoặc khoa yêu cầu.
  - Bảng §5.1 ghi người sở hữu tính năng để soát nội dung, còn bản base của mọi phần do Trình viết (từ 22/11). Dòng Mở đầu ghi ở PR #72 là "Quang, toàn phần", nay sửa thành cả hai cùng soát, vì Mở đầu tóm lược mọi chương.
- **Results:** `/code-review high` trên diff: 5 điểm nhỏ (§3.5 và §9 nói khác nhau về chỗ ghi việc dùng AI; quy tắc "kết quả cụ thể có số" của Tóm tắt chưa chuyển sang mục 1.3; §1 chưa ghi chỗ đặt đoạn khai báo nếu được yêu cầu; "khuôn T" ở §5.1 chưa có link; thiếu dòng Thesis), đã sửa cả 5.
- **Links:** `docs/luan-van/quy-tac-viet.md` (§1, §3.5, §9); `docs/chi-tiet/06-ke-hoach-quan-ly.md` (§5.1, §11.1).
- **Thesis:** phần đầu quyển (không có Tóm tắt, không có Lời cam đoan); Mở đầu; mục 1.3 Đóng góp.

## 2026-11-27 – Môi trường §3.6, §3.8, §6 ghi theo phiên V2 thật

- **Task:** TR8 · **Environment:** none
- **Done:** sửa `05-moi-truong-danh-gia.md`: §3.6 ghi máy tạo tải gọi thẳng Service (không qua Traefik) và cách runner thực sự chạy ở V2 (ĐG1 từ PC qua tunnel, ĐG2/VH/ĐG3 trong `tmux` trên VM, `--no-backup`); §3.8 ghi việc kéo `runs/` về PC, kiểm sha256 rồi `poweroff` thay cho R2 và `make release`; §6.1 dòng V2 ghi ngày, máy, giờ thực tế; §6.2 thêm tiến trình thực tế 18–19/11 theo giờ và danh sách điểm khác kế hoạch, giữ bản kế hoạch để đối chiếu.
- **Decision:** giữ bản kế hoạch dưới bản thực tế, theo cách "Sửa dd/mm" của các tài liệu thiết kế, vì chú thích Hình 17 (#90) dẫn §6.2 làm mốc so sánh. Không sửa Kế hoạch §9.5 (dòng "Mất SSH tới VM" vẫn ghi `systemd`), vì đó là runbook theo thiết kế, và `make runner-start` vẫn có trong code.
- **Results:** mốc giờ lấy từ `runs/v2-evidence/console/` (bootstrap 15:42:08–15:47:16, ĐG1 15:50:50–16:28:55), `runs/v2-vm/vh-all-console.log` (VH 16:46:53Z–18:43:41Z), `runs/v2-vm/dg3-all-console.log` (ĐG3 18:43:53Z–19:04:22Z), `poweroff` 19:05:02Z (nhật ký Quang tuần 07). Từ bootstrap tới poweroff 10 giờ 23 phút ≈ 41,5 GPU-giờ. Chi phí thực tế: chưa có. lychee trên file: 0 lỗi. `/code-review high`: 8 điểm, đã sửa cả 8 (VH và ĐG3 là script riêng, không phải runner; vòng kéo `runs/` mất lúc khoảng 23:15; ma trận hơn 7 giờ, không phải 8; thêm 4 điểm khác kế hoạch: thứ tự, `vh.py` của PR #46, VH2c 1200 s, compile cache của L2 đo lại; VH1, VH6 ghi là lấy từ dữ liệu các lượt; câu về `vllm bench serve` ghi theo nguồn; §12 thêm ghi chú L0 0 → 1; giờ ở §6.1 ghi là cận dưới).
- **Links:** `docs/chi-tiet/05-moi-truong-danh-gia.md` (§3.6, §3.8, §6.1, §6.2, §12).
- **Thesis:** §3.6 (môi trường đánh giá), §5.7 và §6.2 (Hạn chế: không sao lưu R2, không kiểm năng lực giữa phiên, Alertmanager không gửi được tin trong V2).
## 2026-11-27 – Phụ lục A–C: manifest chính, quy tắc cảnh báo, runbook mẫu

- **Task:** TR8 · **Environment:** none
- **Done:**
  - Viết `docs/luan-van/phu-luc/a-manifest-chinh.md`: trích Deployment vLLM, overlay VM thuê, ScaledObject A2, Application gốc của Argo CD, bảng tám Application con; mỗi đoạn ghi đường dẫn file và commit.
  - Viết `b-quy-tac-canh-bao.md`: quy tắc ghi `llm:ttft_bad_ratio:rate5m`, bảng bảy cảnh báo (mức, `for`, điều kiện), quy tắc `LLMSLOBurnFast` đầy đủ, unit test đầu tiên của nó kèm cách đọc bốn thời điểm kiểm.
  - Viết `c-runbook-mau.md`: runbook `LLMSLOBurnFast`, bỏ dẫn chiếu tới tài liệu thiết kế.
  - Thêm dòng `phu-luc/` vào bảng tổ chức file của `docs/luan-van/README.md`.
- **Decision:** Trình chọn mỗi phụ lục một file trong `phu-luc/`, đánh số theo chữ (A.1, Bảng A.1, Đoạn mã A.1), và ghi commit cạnh mỗi trích đoạn vì phụ lục không thuộc thân bài. Phụ lục A thêm Application gốc vì mục 4.1 dẫn tới nó. Lệnh pandoc trong README để phần 2 sửa, vì PR phần đầu quyển đang sửa cùng dòng.
- **Results:** kiem_van còn 1 điểm (đường dẫn `docs/runbooks/` ở Phụ lục C, giữ vì đó là chỗ người đọc tìm runbook); lychee 0 lỗi; pandoc ghép ba file không cảnh báo; `make alerts-test SHELL=bash` đạt (9 test case, 4 + 5 + 7 quy tắc).
- **Deviations:** threshold trong file ScaledObject là 24 (giá trị tạm), phiên V2 dùng 37 do runner ghi đè từ `matrix-v2.yaml`; Phụ lục A ghi rõ điều này.
- **Links:** `docs/luan-van/phu-luc/a-manifest-chinh.md`, `b-quy-tac-canh-bao.md`, `c-runbook-mau.md`; `docs/luan-van/README.md`.
- **Thesis:** Phụ lục A–C; dẫn từ mục 3.5, 4.1, 4.3, 4.6.

## 2026-11-27 – Phụ lục D–F: phiên bản, số từng lượt của V2, kế hoạch và phân công

- **Task:** TR8 · **Environment:** none
- **Done:**
  - Viết `d-phien-ban.md`: hai bảng phiên bản (nền tảng và tầng phục vụ; công cụ kiểm tra) chép từ `docs/phien-ban.md`, bỏ dòng laptop chưa điền và các dòng thân bài không dẫn.
  - Viết `e-so-lieu-tung-luot.md`: 17 lượt ĐG2 (Bảng E.1) kèm Hình C4 (Hình E.1), phản ứng của A2 × KB2 (E.2), mốc vi phạm và page của 7 lượt (E.3), 8 pha cold start của 5 lượt ĐG3 (E.4), 6 kịch bản vận hành (E.5).
  - Viết `f-ke-hoach-phan-cong.md`: mốc M1–M5, điều chỉnh lịch 04/11, bảng Q1–Q8 và TR1–TR8 kèm giờ công ước lượng, người soát từng chương.
  - Sửa lệnh pandoc trong `docs/luan-van/README.md`: thêm `phu-luc/*.md` và thư mục `phu-luc/` vào `--resource-path` (dấu tách `;` trên Windows).
- **Decision:** Trình chọn ghi đường dẫn hình ở phụ lục tương đối với chính file (lychee và GitHub mở được), thêm `phu-luc/` vào `--resource-path` thay vì viết đường dẫn theo thư mục `docs/luan-van/` như các chương. Bảng nghiệm thu đầy đủ, bảng LT1–LT8 và các lượt chạy thử không đưa vào Phụ lục E.
- **Results:** soát số độc lập (agent Opus, khoảng 320 số): 1 lỗi xác nhận (lượt ĐG3 nào được đo lại), 6 điểm nghi vấn, đã sửa cả 7. `/code-review high`: 10 điểm, sửa 9 (gồm câu "người còn lại review PR" trái với quy tắc viết §2.2, dấu tách `--resource-path` trên Windows, "cửa sổ ổn định" không có ở scale-up, đợt page thứ 8 còn sót từ lượt trước); bỏ qua gợi ý ghim mọi trích đoạn theo một tag (để lúc gắn `v1.0`). lychee 0 lỗi; pandoc ghép toàn bộ `[0-9]*.md` + `phu-luc/*.md` nhúng được Hình E.1 (chỉ cảnh báo thiếu rsvg-convert). Chưa đo khuôn T (phụ lục không tính vào thân bài).
- **Deviations:** tên có dấu của Quang ở Phụ lục F suy từ tên Git; mã sinh viên, lớp chưa điền.
- **Links:** `docs/luan-van/phu-luc/d-phien-ban.md`, `e-so-lieu-tung-luot.md`, `f-ke-hoach-phan-cong.md`; `docs/luan-van/README.md`.
- **Thesis:** Phụ lục D–F; dẫn từ mục 1.2, 4.1, 5.3–5.6.
## 2026-11-27 – Phần đầu quyển: danh mục thuật ngữ, danh mục hình và bảng

- **Task:** TR8 · **Environment:** none
- **Done:**
  - Tạo thư mục `docs/luan-van/phan-dau/` cho các trang trước Mở đầu: `01` khung bìa, Lời cảm ơn (khung, Trình viết), hai trang nhận xét (bước định dạng), Mục lục (trường TOC của Word); `02` danh mục thuật ngữ, chữ viết tắt, mã định danh và ký hiệu; `03` danh mục hình vẽ và bảng biểu (dòng đánh dấu, sinh tự động).
  - Danh mục thuật ngữ chỉ giữ mục có dùng trong thân bài: đếm chữ viết tắt và thuật ngữ trên bản ghép ngày 27/11 (main và các nhánh luận văn còn PR mở, bỏ comment, khối code và `code`), nghĩa đối chiếu với định nghĩa trong thân bài, Kiến thức nền §7 và quy tắc viết §4. Gồm 51 chữ viết tắt, 57 thuật ngữ, 12 nhóm mã, 6 ký hiệu.
  - Công cụ ghép cục bộ: thêm script sinh danh mục hình và bảng từ chú thích, báo số trùng, số tạm, nhảy số, sai chương, số được nhắc mà chưa có chú thích và hình/bảng không được nhắc; công cụ ghép nhận `phan-dau/` và chèn danh mục.
  - Sửa README (bảng "Tổ chức file", lệnh ghép) và quy tắc viết §1 (chỗ đặt các trang đầu).
- **Decision:** các trang đầu đặt trong thư mục con, vì tiền tố `00-0x` sẽ đứng sau `00-00-mo-dau.md`. Danh mục bảng không dùng trường của Word được, vì chú thích bảng là đoạn in đậm chứ không phải chú thích của pandoc; danh mục hình và bảng cùng sinh bằng script để một cơ chế cho cả hai. Tiêu đề Mục lục dùng kiểu TOC Heading của Word (outline level 9) để mục lục không tự liệt kê chính nó.
- **Results:**
  - Bản ghép có 5 hình và 23 bảng có chú thích. Script báo 5 điểm, đều là số tạm ở chương 5: Hình 5.3b → 5.1, Bảng 5.2a → 5.1, 5.3a → 5.2, 5.4a → 5.3, 5.6a → 5.4 khi đánh lại theo thứ tự xuất hiện. Không có số trùng, nhảy số hay số được nhắc mà chưa có chú thích.
  - `pandoc` dựng `.docx` từ `phan-dau/` không lỗi; lychee 0 lỗi; `kiem_van.py` 0 điểm ở danh mục thuật ngữ.
  - `/code-review high`: 9 điểm, sửa 8 (thêm OOM, RPS, vCPU, μ, ρ, các thuật ngữ scrape, histogram, recording rule, sync…; sửa nghĩa stabilization window theo mục 2.4; Mục lục không tự liệt kê; thứ tự chữ cái; README và quy tắc viết §1 nói đúng việc sinh danh mục). Điểm còn lại (dùng trường TOF của Word thay script) chỉ làm được cho hình, ghi lại để xem ở bước dựng bản nộp.
- **Links:** `docs/luan-van/phan-dau/`, `docs/luan-van/README.md`, `docs/luan-van/quy-tac-viet.md` §1.
- **Thesis:** phần đầu quyển (Mục lục, danh mục thuật ngữ, danh mục hình và bảng).
## 2026-11-27 – ADR-003: ghi lại kết quả ĐG1 trên V2 và các giá trị chốt

- **Task:** TR8 (tài liệu; số của Q6) · **Environment:** none
- **Done:**
  1. Viết `docs/adr/003-ket-qua-dg1-va-gia-tri-chot.md` từ `envs/cloud/experiments/capacity.json`, `matrix-v2.yaml` (khối `x-adr003`), `capacity.py`, `analysis/figures/v2-dg2/runs.csv` và nhật ký Quang 18–19/11: bảng 5 mức ĐG1, quyết định G1–G8, các chỗ ĐG1 làm khác quy trình, kiểm tra R12 sau ma trận, hệ quả.
  2. Thông số: bỏ nhãn *tạm* ở SLO TTFT, target A2 (37) và N2b (mức tham chiếu 5 phút); ghi C = 3,5 req/s ở §7. Cập nhật bảng ADR (003 đã viết, 006 C2 bị thay một phần), dòng trạng thái ADR-006, mốc M3 ở Kế hoạch, danh sách ADR ở bản mô tả và nguồn tư liệu luận văn.
  3. Một agent soát số độc lập đối chiếu từng số với nguồn, rồi chạy `/code-review high`.
- **Decision:**
  - D137: N2b giữ "chỉ báo cáo" với mức tham chiếu 5 phút, tức đúng con số "dự kiến ≤ 5 phút" đã ghi trước V2. Hai phương án bị bỏ: bỏ hẳn ngưỡng sau khi thấy số đo 409–430 s (như vậy là né kết quả), và nâng ngưỡng cho vừa số đo (trái Môi trường §7).
  - ADR ghi rõ thời điểm. C, target A2 và SLO đã có trên VM trước lượt đầu của ma trận (16:30 ngày 18/11): sha256 của ma trận trên VM trùng commit `a44ae71` (19/11), và console runner in C = 3,5 ngay từ lượt đầu. File ADR và G5 thì viết ngày 27/11, sau khi đã có kết quả. Điểm này được ghi vào bảng lệch và phần Hạn chế.
  - Không sửa tên máy A4000 ở Thông số §2, §10.2, §11, vì PR #79 đã sửa các chỗ đó, sửa thêm ở đây sẽ gây xung đột. Câu "ADR-003 chưa có" trong comment nguồn của 3.5 cũng đã được PR #80 bỏ.
- **Results:**
  - Soát số độc lập: 4 điểm sai, đã sửa cả 4. (1) Commit `a44ae71` mang ngày 19/11, không phải 18/11. (2) N = 4 đã chốt từ ADR-006 C4. (3) Ổ đĩa máy V2 là 126 GB, dưới tiêu chí 130 GB, và tốc độ đọc tuần tự không được đo. (4) G4 chỉ được bỏ nhãn *tạm* ngày 27/11.
  - `/code-review high`: 8 điểm, sửa 6. Các điểm đã sửa: dòng tóm tắt Thông số nói G5 chốt trước ma trận; bảng lệch thiếu dòng về thời điểm chốt; mục ADR-003 vẫn nằm trong danh sách "chưa có" của nguồn tư liệu; câu "đạt mọi tiêu chí" trong nhật ký 18/11 trái với số đo ổ đĩa; nguồn của B\*; 30 s làm ấm ở 0,3 λ trước mỗi mức. Hai điểm bỏ qua: tên máy (PR #79) và comment ở 3.5 (PR #80).
  - lychee trên các file đã sửa: 0 lỗi; yamllint đạt.
- **Deviations:** ADR-003 được viết ngày 27/11, không phải "ngay trong phiên V2" như Môi trường §8.
- **Links:** `docs/adr/003-ket-qua-dg1-va-gia-tri-chot.md`, `docs/chi-tiet/00-thong-so.md` (§1, §4, §6, §7, §8.1).
- **Thesis:** chương 5, mục năng lực một replica (bảng ĐG1, C cận dưới); bảng nghiệm thu N2b (409–430 s so với mức tham chiếu 5 phút); Hạn chế (card 4060 Ti, ổ đĩa, C có độ phân giải 0,5 req/s, chưa đối chiếu `vllm bench serve`, ADR viết sau kết quả).
## 2026-11-27 – Vẽ lại Hình 8 (kịch bản tải) và Hình 17 (quy trình phiên V2)

- **Task:** TR8 · **Environment:** none
- **Done:** viết lại `fig_scenarios()` (`docs/diagrams/build_diagrams.py`) và `fig_eval_pipeline()` (`docs/diagrams/chuyen_sau.py`), chỉ chạy hai hàm này; xuất SVG và PNG 2x bằng Chrome headless như `export_png.sh`. Sửa chú thích Hình 8 ở `05-moi-truong-danh-gia.md` và `mo-ta-chi-tiet-do-an.md`, chú thích Hình 17, và câu "giảm tải trở lại ở phút 15" thành phút 14 (Môi trường §10).
  - Hình 8 theo Thông số §7 bản 08/11: KB1 12 phút, KB2 24 phút (lên 0,75 × N × C trong [4; 4,5], về 0,5C trong [14; 14,5]), KB3 17 phút (tăng tuyến tính trong 5 phút đầu); λ(t) tuyến tính từng đoạn như `loadgen/scenarios.py`; thêm vùng 2 phút ổn định không tính và ranh giới pha (`steady`, `pre`/`spike`/`drop`, `ramp`/`sustain`); ô kiểm chứng ghi N2a, N2b thay cho N2.
  - Hình 17 theo cách V2 đã chạy (nhật ký Quang tuần 07, van-hanh.md 18–19/11): `make probe`, `make bootstrap` + `make cloud-platform` không Argo CD (ADR-006 §3.1), ĐG1 5 mức λ, 17 lượt ĐG2 bằng runner trong tmux trên VM, VH2–VH4 rồi ĐG3 (L2 × 3, L0 × 2), kéo `runs/` về PC và khớp sha256 rồi tắt máy, phân tích trên PC. Bỏ Argo CD trên VM, burn-in `vllm bench` từng GPU và sao lưu R2.
- **Decision:** Hình 17 vẽ quy trình thực tế của V2 thay cho kế hoạch §6.2 (D136); chú thích nêu chỗ khác §3.6, §3.8, §6.2. Hình không ghi số đo (C, thời gian dựng), để chèn được vào chương 3 luận văn mà không lộ kết quả chương 5. Hình 8 vẽ với N = 4, đỉnh 3C.
- **Results:** `/code-review high` báo 10 điểm, sửa 9: subtitle và ô ĐG1 (ĐG1 chạy runner từ PC qua tunnel, chỉ ĐG2 chạy trong tmux trên VM); bỏ thứ tự "L2 rồi L0" (3 lượt hỏng do lỗi `dg3.sh` được đo lại sau L0-2); chú thích Hình 17 thêm §3.4, §12, GPU 4060 Ti; bỏ "(VH5)" vì thời gian dựng đo bằng tay, không qua `make vh5`; docstring `kb2` trong `loadgen/scenarios.py` ghi "phút 11" sửa thành 14; nhãn KB1 che vùng 2 phút đầu; vạch pha vẽ trùng; nhánh chết trong `scenario()`; nhãn chú giải. Không làm: dựng đường cong từ `loadgen` (script hình chỉ dùng thư viện chuẩn); thay vào đó đối chiếu một lần từng giây của KB1–KB3 với `loadgen.scenarios` (N = 4): 0 điểm lệch, pha trùng. `pytest loadgen` 55 passed, ruff loadgen đạt; `ruff check docs/diagrams` 28 lỗi như trên main (thư mục này không nằm trong phạm vi ruff của CI; 2 lỗi mới do bản đầu đã sửa); lychee offline 40 lỗi như trên main (file chưa có trên nhánh); yamllint đạt.
- **Deviations:** Môi trường §3.6 (gửi request qua Traefik, runner là dịch vụ `systemd`) và §6.2 vẫn ghi kế hoạch cũ; chưa sửa trong PR này.
- **Links:** `docs/diagrams/build_diagrams.py`, `docs/diagrams/chuyen_sau.py`, `docs/images/08-kich-ban-tai.svg`, `docs/images/17-quy-trinh-danh-gia.svg`.
- **Thesis:** Hình 8 và Hình 17 cho mục 3.6 (sau khi PR chương 3 được merge).
## 2026-11-27 – Vẽ lại Hình 2 (kiến trúc tổng thể) theo thiết kế hiện hành

- **Task:** TR8 · **Environment:** none
- **Done:** viết lại `fig_architecture()` trong `docs/diagrams/build_diagrams.py` (chỉ chạy hàm này, không sinh lại các hình khác), xuất SVG và PNG 2x bằng Chrome headless như `export_png.sh`. Đối chiếu với Kiến trúc §2–§5, §18.1, ADR-006 §3.1, Môi trường §3.6, Thông số §7 và manifest `envs/home/serving/`. Sửa chú thích Hình 2 ở `03-kien-truc-autoscaling.md` và `mo-ta-chi-tiet-do-an.md`; sửa dòng "Lưu trữ model" của bảng thành phần (§2) từ "PVC (nhà); Job prefetch, DaemonSet pre-pull" thành `hostPath` ở cả hai môi trường và role Ansible `cloud-prefetch`, đúng như §3.3 và §4.
- **Decision:** Traefik tách sang nhóm `kube-system` (đúng bảng namespace §2), bỏ dòng "giới hạn tốc độ, route riêng cho tải"; máy tạo tải là pod trong `llm-serving` gọi thẳng Service; thêm nhóm `argocd` (ghi "chỉ ở nhà") và hộp Git repository, mũi tên "áp manifest"; số replica ghi "N = số GPU" thay cho "N = 4" vì ở nhà N = 2. Không thêm hộp Telegram để hình không quá dày; chú thích và §17 đã nói cảnh báo đi Telegram.
- **Results:** `lychee --offline --include-fragments` trên hai file đã sửa: 0 lỗi; `yamllint -s .` đạt. Canvas đổi từ 1280 × 730 sang 1440 × 730. `/code-review high`: 6 điểm, đã sửa hết (khoảng hở giữa Service và Deployment cho mũi tên chia tải, "lõi CPU riêng" chỉ ở cloud, nhãn "áp manifest cho mọi namespace", bảng namespace §2 thêm Job máy tạo tải, §3.3 ghi role `cloud-prefetch` thay cho Job `model-prefetch`).
- **Links:** nhánh `docs/tr8-fig2-architecture`; `docs/images/02-kien-truc-tong-the.{svg,png}`.
- **Thesis:** hình kiến trúc cho 3.2 (chèn vào PR chương 3 sau khi PR này merge).
## 2026-11-27 – Luận văn: phần Mở đầu (bản base)

- **Task:** TR8 · **Environment:** none
- **Done:** viết `docs/luan-van/00-00-mo-dau.md` theo Kế hoạch §11.1 (dòng Mở đầu) và quy tắc viết §1, §2: dẫn dắt vấn đề ở mức người không chuyên (GPU tính tiền theo giờ, tải thay đổi theo giờ, ba khác biệt của LLM so với web, yêu cầu vận hành hằng ngày), những gì đồ án làm, cách đánh giá; mỗi chương 2–3 câu, một câu về phụ lục. Không có số đo; "bốn GPU" là cấu hình máy.
- **Decision:** Trình dùng thẳng các thuật ngữ replica, request, autoscaling, GPU-giờ và giải thích ở lần đầu, không đặt từ riêng "bản chạy", vì bảng thuật ngữ của quy tắc viết §4 chỉ cho một dạng. Định nghĩa ở mục 1.1 giữ nguyên để chương 1 đọc được độc lập.
- **Results:** đo bằng Word theo khuôn T (`gop.py`): 1,97 trang (định hướng 1,5–2); thân bài cả bản ghép 71,2 trang. `kiem_van`: 0 điểm cần xem. `/code-review high`: 10 điểm, đã sửa cả 10. Ba điểm chính: tải là tải tổng hợp (Poisson), không phải phát lại tải thật; chỉ cluster nhà tự áp cấu hình từ Git (VM thuê dựng bằng helm); không phải tình huống vận hành nào cũng kiểm cả request rớt lẫn cảnh báo (VH5 đo thời gian dựng lại, cảnh báo kiểm riêng ở VH6). Các điểm còn lại: câu quá 35 chữ, "tự scale" là dạng bị cấm, GPU-giờ chưa giải thích, đường dẫn nguồn sai.
- **Links:** `docs/luan-van/00-00-mo-dau.md`.
- **Thesis:** Mở đầu (không đánh số).
## 2026-11-27 – Luận văn: chương 6, kết luận, hạn chế và hướng phát triển (bản base)

- **Task:** TR8 · **Environment:** none
- **Done:** viết bốn file `06-00` (mở chương), `06-01` Kết luận, `06-02` Hạn chế của hệ thống và phạm vi, `06-03` Hướng phát triển theo dàn ý Kế hoạch §11.1 và §12.2. Mọi số lấy lại từ bản base chương 5 (nhánh `docs/tr8-thesis-ch5-drafts`), không thêm kết quả mới; số mô phỏng ở 6.3 lấy từ `docs/bao-cao/de-xuat-v3/ket-qua-du-bao-quy-mo.json` và đối chiếu với `mo_phong_thuc_te.py`, `du_bao_quy_mo.py`.
- **Decision:**
  - 6.1 viết ba kết luận theo ba thông điệp, thêm một đoạn nói kết luận về vận hành có ít bằng chứng hơn (một lượt mỗi ca, vòng Git trên simulator, chưa có tin Telegram) và một đoạn tách cơ chế khái quát được khỏi con số chỉ đúng cho máy V2.
  - 6.2 nhận các hạn chế mà 3.5 và 5.7 dời sang: chia kết nối gần như ngẫu nhiên của Service, tối đa 4 replica, vLLM không dừng khi nhận SIGTERM (đo ở máy nhà), `LLMErrorRateHigh` nhạy ở tải thấp, chưa có dead man's switch, cảnh báo lỗi gửi tin đi qua chính Alertmanager, bảo mật và GitOps tối thiểu. Viết "chia kết nối mới gần như ngẫu nhiên" thay cho chữ "round-robin" của dàn ý, theo Kiến trúc §3.4 (kube-proxy chế độ iptables).
  - 6.3 chọn định tuyến theo hàng đợi, rút ngắn cold start và scale-to-zero, dự báo và lịch tải, đánh giá mở rộng, cộng một đoạn cải tiến nhỏ; dùng số mô phỏng có nhãn và điều kiện (D133). Định tuyến được nêu phải đi cùng rút cold start, vì 42–44% request trượt SLO được gửi trước khi pod mới đầu tiên Ready.
- **Results:**
  - Độ dài văn xuôi: 06-00 108 chữ, 06-01 693, 06-02 565, 06-03 971; tổng khoảng 2.340 chữ, ước 4,5 trang khuôn T, chưa đo bằng Word (dàn ý định hướng 3 trang).
  - `kiem_van.py`: 0 điểm cần xem. `pandoc … --citeproc` chạy không lỗi, không cảnh báo (chương 6 không có trích dẫn).
  - `/code-review high`: 10 điểm (3 quan trọng: câu "mỗi ca vận hành chỉ một lượt" sai với VH6 17 lượt; trộn cold start 75,7–80,8 s của ĐG3 với thời gian phản ứng của KB2; "một nửa nguyên nhân" không có số đo), đã sửa cả 10, gồm cả mô tả least request của Envoy (power of two choices) và chế độ ngủ của vLLM (pod vẫn giữ GPU).
- **Deviations:** dàn ý ghi 3 trang; bản base dài khoảng 4,5 trang vì 6.3 có bốn hướng kèm số đo và số mô phỏng. Phần cắt được nếu cần: đoạn cải tiến nhỏ cuối 6.3, đoạn đánh giá mở rộng.
- **Links:** `docs/luan-van/06-00-ket-luan-huong-phat-trien.md`, `06-01-ket-luan.md`, `06-02-han-che.md`, `06-03-huong-phat-trien.md`.
- **Thesis:** chương 6 (toàn chương).
## 2026-11-27 – Thông số §9.2: CPU, RAM pod vLLM cloud theo manifest (3 lõi, 16Gi)

- **Task:** TR8 · **Environment:** none
- **Done:** Đối chiếu Thông số §9.2 với `envs/cloud/serving/patch-vllm.yaml` (bản trên main, cũng là bản V2 chạy): tài liệu ghi `cpu: 6`, `memory: 24Gi` (thiết kế 08/10, ADR-001), manifest đặt `cpu: "3"`, `memory: 16Gi` từ ADR-006 C2. Sửa dòng CPU, RAM ở Thông số §9.2; bảng phân bổ lõi ở Môi trường §3.5 (4 × 6 → 4 × 3 lõi, bỏ ví dụ máy 48 và 32 vCPU, thêm phép tính 15 lõi riêng + ~0,4 lõi → máy ≥ 20 vCPU); dòng "CPU 4–6 lõi" ở Kiến trúc đổi thành 3 lõi mỗi pod trên VM thuê. Kiến thức nền §2.6 (khuyến nghị chung 4–6 vCPU) và ADR-001 (tư liệu) giữ nguyên. `/code-review high` 8 điểm: thiếu căn cứ cho 3 lõi (thấp hơn 4–6 vCPU của §2.6), khẳng định "V2 chạy đúng giá trị này" chưa có bằng chứng, máy V2 thật khác máy ADR-006 C2, dấu câu; đã sửa cả 8. Căn cứ V2: `runs/v2-evidence/config/git-head.txt` = `10c0527` (manifest 3 lõi, 16Gi), Node 61 vCPU, allocatable 57.
- **Decision:** D132: tài liệu theo manifest, không ngược lại, vì manifest là thứ V2 đã chạy và số đo chương 5 gắn với nó; ghi chú "Sửa 27/11" tại chỗ để người đọc thấy giá trị cũ.
- **Results:** CPU container vLLM trên V2, đọc `cpu_cores` (rate 1 phút của `container_cpu_usage_seconds_total`) trong mọi `metrics.csv.gz` dưới `runs/v2-vm/` và `runs/dg1-v2-4060ti/` bằng script tạm: `runs/v2-vm` 14.572 mẫu p50 0,27 · p99 1,00 · max 1,26 lõi; `dg1-v2-4060ti` 423 mẫu max 0,44 lõi. So sánh V1 (A4000, 2 lõi): max 1,23 lõi. Throttle của pod vLLM chưa đo. lychee (cách bỏ qua như job `docs` của CI) 0 lỗi.
- **Links:** `docs/chi-tiet/00-thong-so.md`, `05-moi-truong-danh-gia.md`, `03-kien-truc-autoscaling.md`.
- **Thesis:** §4.1 hoặc §5.7 (cấu hình pod vLLM trên V2: 3 lõi CPU, 16Gi RAM).
## 2026-11-27 – Sửa mô tả fallback KEDA theo mã nguồn v2.21.0

- **Task:** TR8 (hỗ trợ TR2) · **Environment:** none
- **Done:** đối chiếu `pkg/fallback/fallback.go` ở tag v2.21.0 và trang "ScaledObject specification" của tài liệu KEDA 2.21; sửa Kiến thức nền §3.3, Kiến trúc §9 và comment trong `common/autoscaling/a2/scaledobject-a2.yaml`, `common/autoscaling/eval/A1.yaml`.
- **Decision:** giữ `metricType: AverageValue` cho mọi trigger; chỉ sửa lý do. Bản cũ ghi "fallback chỉ hỗ trợ AverageValue", nhưng KEDA 2.21 hỗ trợ cả `Value` (trừ CPU, memory). Lý do đúng: với `Value`, giá trị giả `threshold × fallback.replicas` bị chia cho số replica Ready; khi số này bằng 0, KEDA trả lỗi và HPA giữ nguyên số replica, nên fallback phụ thuộc trạng thái pod; `AverageValue` thì không. Bản nháp chương 2 (PR #83) đã viết theo tài liệu 2.21; hai tài liệu thiết kế còn bản cũ. Kiến trúc §13.3 cũng sửa cho tách hai lý do: `AverageValue` để giống A2, `timeout` để kịp N6.
- **Results:** `/code-review high`: 4 điểm nhỏ (§13.3 còn lý do cũ; chưa nói hậu quả khi 0 pod Ready; công thức chỉ đúng với `fallback.behavior: static`; nhật ký dẫn mã quyết định cục bộ), đã sửa cả 4. `yamllint -s` hai file YAML đạt; `lychee --offline --include-fragments` hai tài liệu: 94 link, 0 lỗi. Chỉ đổi comment nên manifest render không đổi.
- **Links:** `docs/chi-tiet/02-kien-thuc-nen.md` §3.3; `docs/chi-tiet/03-kien-truc-autoscaling.md` §9.
- **Thesis:** mục 2.4 (fallback KEDA), 3.3.3 (vì sao dùng AverageValue).
## 2026-11-27 – Luận văn: viết chương 1 (Giới thiệu), bản base

- **Task:** TR8 · **Environment:** none
- **Done:** Viết `01-00` (mở chương), `01-01` (1.1 Bối cảnh và bài toán, kèm Hình 1.1), `01-02` (1.2 Mục tiêu, phạm vi và phương pháp, Bảng 1.1 ánh xạ bảy mục tiêu của đề cương sang yêu cầu và mục), `01-03` (1.3 Đóng góp chính) theo dàn ý Kế hoạch §11.1, nguồn ở `nguon-tu-lieu.md` §2–§3 và bản base chương 5 (PR #82). Soát văn bằng `kiem_van.py` tới 0 điểm; cắt hai lượt để gần khoảng 3–4 trang; chạy `/code-review high`, sửa cả 10 điểm.
- **Decision:** D130: chương 1 chỉ giữ 2–3 số chính, đều ở 1.3; bỏ ví dụ tính tay 96/48 GPU-giờ/ngày; mã F/N chỉ xuất hiện ở Bảng 1.1.
- **Results:** Khuôn T (đo bằng Word qua `gop.py`): 5,21 → 4,65 → 4,67 trang sau khi sửa review (01-00 0,19 · 01-01 1,89 · 01-02 1,73 · 01-03 0,86), gồm Hình 1.1 và Bảng 1.1; vượt định hướng 3–4 trang khoảng 0,7 trang. Thân bài bản ghép 67,1 trang. `lychee --offline` 0 lỗi.
- **Incidents:** `/code-review high` thấy 10 điểm: phần phương pháp mô tả sai các phiên thuê thử (thực tế có các phiên 08/11 và 16/11 trên nhiều loại máy) và sai thời điểm đóng băng dữ liệu; nguyên nhân SLO thấp khi tải tăng đột ngột bị viết thành "hàng đợi dồn vào các replica có sẵn" trong khi chương 5 đo được là dồn vào replica duy nhất, rồi Service chia đều nên hàng đợi rút chậm; Bảng 1.1 thiếu mục 3.4, 3.6, 4.4, 4.5, 5.6; mã F/N còn trong văn xuôi; quá nhiều số ở 1.3; dẫn nguồn `00-thong-so` §10.2 chưa có trên main. Đã sửa hết. Một lần lệnh `git push … 2>&1` bị hook chặn: chạy lại không chuyển hướng.
- **Links:** nhánh `docs/tr8-thesis-ch1`; `docs/luan-van/01-0*.md`.
- **Thesis:** chương 1 (1.1–1.3).
## 2026-11-27 – Luận văn: chương 2 phần 1, mục 2.1 và 2.2

- **Task:** TR8 (luận văn, bản base chương 2) · **Environment:** none
- **Done:**
  1. Tạo nhánh `docs/tr8-thesis-ch2` từ `origin/main`.
  2. Viết `02-00` (mở chương), `02-01` (2.1.1 Sinh token và bộ nhớ GPU, 2.1.2 vLLM: continuous batching và các chỉ số TTFT, TPOT, Bảng 2.1 metric của vLLM, Hình 2.1 batching) và `02-02` (2.2 Hàng đợi và năng lực phục vụ: tải mở và tải đóng, định luật Little áp cho một replica, M/M/1, năng lực dùng được C và B\*, Hình 2.2 độ trễ theo mức tải). Nguồn: Kiến thức nền §1–§2, Bài toán §1, §3, phần lý thuyết LT1–LT6 trong `van-hanh.md`.
  3. Thêm 8 tài liệu vào `tai-lieu.bib`: Vaswani 2017, GQA 2023, Sarathi-Serve 2024, PagedAttention 2023, Orca 2022, Little 1961, Harchol-Balter 2013, Schroeder NSDI 2006. Tên tác giả đối chiếu trên trang arXiv và USENIX, tóm tắt đọc ngày 27/11; Little kiểm qua Crossref.
- **Decision:** chương 2 chỉ dùng số minh hoạ tròn (model 3 tỷ tham số ≈ 6 GB, GPU 300 GB/s), không dùng số đo của đồ án, để không trùng mục 5.2 (quy-tac-viet §2, §5). Mục mới trong `tai-lieu.bib` đặt ở đầu file để tránh xung đột với các nhánh chương 3, 5 (thêm ở cuối). Không đưa mức ρ 0,7–0,85 của Bài toán §3, vì không có nguồn chung; hệ số dư do chương 3 chọn.
- **Results:** đo bằng Word theo khuôn T: mở chương 0,3 tr, 2.1 3,9 tr (1.838 chữ văn xuôi, 1 bảng, 1 hình), 2.2 2,3 tr (1.155 chữ, 1 hình); cộng 6,5 tr. Còn 3,5–6,5 tr cho 2.3–2.6 và kết chương để nằm trong 10–13 tr. `kiem_van` 0 điểm cả ba file; `pandoc --citeproc` không cảnh báo; `lychee --offline` thư mục `docs/luan-van/` 0 lỗi.
- **Deviations:** Harchol-Balter 2013 là giáo trình, chưa đọc trực tiếp trong lần viết này (dẫn cho công thức M/M/1); comment trong bib ghi để người soát đối chiếu trước khi chốt.
- **Links:** `docs/luan-van/02-00-co-so-ly-thuyet.md`, `02-01-phuc-vu-llm-vllm.md`, `02-02-hang-doi-nang-luc.md`, `tai-lieu.bib`.
- **Thesis:** chương 2, mục 2.1, 2.2; Hình 2.1 (`11-batching.png`), Hình 2.2 (`10-do-tre-theo-muc-tai.png`).

## 2026-11-27 – Luận văn: chương 2 phần 2, mục 2.3–2.6 và kết chương

- **Task:** TR8 (luận văn, bản base chương 2) · **Environment:** none
- **Done:**
  1. Viết `02-03` (GPU trên Kubernetes: khái niệm cluster, node, pod, Deployment, Service, readiness probe, controller; device plugin và `nvidia.com/gpu`; time-slicing; vì sao GPU utilization bão hoà, util ≈ 1 − e^(−L)), `02-04` (thuật toán HPA, behavior mặc định, năm loại metric, KEDA, fallback, trễ phản ứng), `02-05` (SLI, SLO, burn rate, page và ticket; Prometheus và Alertmanager; Argo CD; rolling update và graceful shutdown khi GPU đã dùng hết), `02-06` (Bảng 2.2 năm nền tảng, các nghiên cứu, vị trí của đồ án, Kết chương). Rút đoạn mở chương ở `02-00` còn 5 câu.
  2. Đối chiếu giá trị mặc định với tài liệu gốc ở bản ghim: Kubernetes v1.36 (HPA sync 15 s, tolerance 0,1, scale-down stabilization 300 s, scale-up 100% hoặc 4 pod mỗi 15 s; extended resource chỉ nhận số nguyên, không cấp vượt; maxSurge, maxUnavailable 25%; progressDeadlineSeconds 600; thời gian tắt mặc định 30 s), KEDA 2.21 (pollingInterval 30 s, cooldownPeriod 300 s chỉ khi về 0, fallback), Argo CD v3.5.4, NVIDIA device plugin v0.20.1 (time-slicing không cô lập bộ nhớ và lỗi), Prometheus v3.15.0, Alertmanager v0.34.1. Tóm tắt arXiv của DistServe, Splitwise, Llumnix, ServerlessLLM, BurstGPT, AIBrix; README của Production Stack, llm-d; tài liệu KServe KPA, Ray Serve.
  3. Thêm 19 tài liệu vào đầu `tai-lieu.bib` (sau 8 mục của phần 1).
- **Decision:** 2.4, 2.5 viết thành đoạn có cụm in đậm, không chia 2.4.1–2.5.3, vì mỗi mục dưới 2 trang; dẫn chéo ở 2.1, 2.2 đổi thành "mục 2.5". SLI, SLO gọi là "chỉ số/mục tiêu mức dịch vụ" như mục 3.5. Bảng 2.2 bỏ NVIDIA Dynamo vì chưa đọc nguồn gốc. Không viết "các nền tảng đều dựa trên HPA, KEDA" (Kiến thức nền §6) vì chỉ kiểm được KServe dùng Knative; README Production Stack ghi autoscaling theo metric vLLM còn ở lộ trình.
- **Results:** đo bằng Word theo khuôn T: 2.3 1,6 tr, 2.4 1,5 tr, 2.5 1,9 tr, 2.6 và Kết chương khoảng 1,5 tr; cả chương khoảng 12,9 tr (định hướng 10–13), chưa tính danh mục tài liệu. `kiem_van` 0 điểm mọi file `02-*`; `pandoc --citeproc` không cảnh báo trích dẫn; `lychee --offline` thư mục `docs/luan-van/` 0 lỗi. `/code-review high` trên diff so với main: 10 điểm. Đã sửa 8: `maxUnavailable: 1` phải kèm `maxSurge: 0`; SIGTERM và việc bỏ pod khỏi Service chạy song song chứ không nối tiếp; HPA có năm loại metric (thêm ContainerResource); mô hình đóng vẫn có hàng đợi, chỉ không dài quá số người dùng ảo; trích dẫn mô hình kéo và recording rule sang đúng trang tài liệu; ví dụ HPA và trễ phản ứng bỏ số cấu hình của đồ án; "Mục này trình bày", đoạn mở chương 7 câu, "instance", hai cách gọi SLO; dẫn chéo 2.5.1 không tồn tại. Chưa sửa 2 điểm, ghi dưới đây.
- **Deviations:** Tài liệu KEDA 2.21 ghi fallback hỗ trợ cả `Value` và `AverageValue`, khác Kiến thức nền §3.3 ("chỉ hỗ trợ AverageValue") và lý do ở Kiến trúc dòng `metricType: AverageValue … để fallback hoạt động`; mục 2.4 viết theo tài liệu 2.21, hai tài liệu thiết kế chưa sửa. Harchol-Balter 2013 (dẫn ở 2.2 cho công thức M/M/1) vẫn chưa đọc trực tiếp; trang của tác giả chỉ có chương 1. Hình 2.2 (ảnh có sẵn) có thể ghi ngưỡng TTFT của đồ án, chưa kiểm.
- **Links:** `docs/luan-van/02-00-co-so-ly-thuyet.md`, `02-03-gpu-kubernetes.md`, `02-04-autoscaling-kubernetes.md`, `02-05-slo-gitops.md`, `02-06-giai-phap-lien-quan.md`, `tai-lieu.bib`.
- **Thesis:** chương 2, mục 2.3–2.6 và Kết chương; Bảng 2.2.

## 2026-11-27 – Kiểm Hình 2.2 và sửa chú thích

- **Task:** TR8 · **Environment:** none
- **Done:** kiểm ảnh `docs/images/png/10-do-tre-theo-muc-tai.png` dùng làm Hình 2.2 (mục 2.2): ảnh có vẽ đường "SLO: TTFT p95 ≤ 2,5 s", μ = 2,4, C ≈ 2,1 req/s và tiêu đề trong hình "Vì sao không thể cho GPU chạy sát 100% tải". Sửa chú thích: nói đường cong vẽ phác theo dạng trung bình T ≈ T0 + k·ρ/(1 − ρ) và mọi số trên hình chỉ để minh hoạ; comment nguồn ghi cách tính lại C.
- **Decision:** chú thích không dẫn sang mục 3.1 hay 5.2, vì quy-tac-viet §2 không cho chương 2 nói về hệ thống của nhóm. Cách sửa gốc là vẽ lại hình cho luận văn (bỏ tiêu đề trong hình, đường ngưỡng không ghi số); để sau vì lượt tự chạy sắp hết giờ.
- **Results:** tính lại từ dòng chân hình: T0 = 0,3 s, k = 0,35 s, C ≈ 2,07 req/s, khớp nhãn "C ≈ 2,1". `kiem_van` 0 điểm; lychee `docs/luan-van` 0 lỗi. `/code-review high` 8 điểm: sửa 5 (dẫn chéo sang chương 3, nhánh khác, cách tính, dạng trung bình, nhật ký); 2 điểm (vẽ lại hình, tiêu đề "GPU 100% tải" trái với đoạn nói ρ khác GPU utilization) để việc vẽ lại; 1 điểm (SLO theo request khác TTFT p95) hết áp dụng khi bỏ dẫn sang 3.1.
- **Links:** PR #83, `docs/luan-van/02-02-hang-doi-nang-luc.md`.
- **Thesis:** chương 2, Hình 2.2.

## 2026-11-27 – Vẽ lại Hình 2.2 cho luận văn

- **Task:** TR8 · **Environment:** none
- **Done:** thêm `fig_knee_thesis()` vào `docs/diagrams/chuyen_sau.py`, sinh `docs/images/10-do-tre-theo-muc-tai-luan-van.svg`: cùng đường cong và ba vùng như Hình 10 (tham số chung `KNEE_MU`, `KNEE_C`, `knee_ttft`), không tiêu đề trong hình, không lưới, không số trên trục, C, μ; đường ngưỡng ghi "ngưỡng TTFT"; nhãn vùng "dưới ngưỡng", "vượt ngưỡng", "quá tải"; trục ghi "TTFT (s)" và "tốc độ request đến λ (req/s)"; khổ 760 × 392, chữ 14–16 px. Xuất PNG bằng Chrome headless (cùng cờ với `export_png.sh`, chỉ cho file mới). Hình 2.2 ở 02-02 trỏ sang PNG mới; chú thích bỏ câu liệt kê số và chữ SLO. `Svg.save` ghi SVG với `newline="\n"`.
- **Decision:** D135: làm hình riêng thay vì sửa Hình 10, vì Hình 10 phục vụ Bài toán §3 (cần số và SLO của đồ án), còn chương 2 không nói SLO của nhóm (quy-tac-viet §2). Bỏ cả số trên trục, vì giữ trục số thì vẫn đọc được ngưỡng 2,5 s; giữ đơn vị trục theo quy-tac-viet §6. Nhãn vùng nói "ngưỡng" vì mục 2.2 đứng trước chỗ định nghĩa SLO (2.5). Trục ghi TTFT, không ghi p95, vì đường cong là dạng trung bình.
- **Results:** chạy lại `build_diagrams.py`: 19 SVG cũ giữ nguyên từng byte (kể cả Hình 10 sau khi tách tham số chung); trước khi thêm `newline="\n"`, cả 19 file bị ghi CRLF. `kiem_van` 02-02: 0 điểm; lychee `docs/luan-van`: 0 lỗi; ruff trên `chuyen_sau.py` không thêm lỗi so với trước. `/code-review high` 7 điểm, sửa cả 7 (đơn vị trục, chữ SLO trước 2.5, CRLF, chữ quá nhỏ khi thu về bề rộng trang, lưới không số, p95 với đường trung bình, docstring).
- **Links:** PR #83, `docs/diagrams/chuyen_sau.py`, `docs/diagrams/build_diagrams.py`, `docs/images/10-do-tre-theo-muc-tai-luan-van.svg`, `docs/images/png/10-do-tre-theo-muc-tai-luan-van.png`, `docs/luan-van/02-02-hang-doi-nang-luc.md`.
- **Thesis:** chương 2, Hình 2.2.
## 2026-11-26 – Luận văn: chương 5 bước 1, merge main và đổi đề mục theo D101

- **Task:** TR8 · **Environment:** none
- **Done:** trên nhánh `docs/tr8-thesis-ch5-drafts`: merge `origin/main` (xung đột ở Kế hoạch §11.1 lấy bản main, đoạn "Độ dài" thay "Cân đối"; xung đột ở `nguon-tu-lieu.md` lấy bản main theo đề mục mới, giữ lại con trỏ tới bảng từng lượt VH4, VH6 ở commit `bc49ff6`). Đổi đề mục 5.3: TĐ1 (GPU utilization so với tải đồng thời) lên 5.3.1, tải ổn định 5.3.2, tải tăng đột ngột 5.3.3; Bảng 5.3a ở đoạn dẫn. 5.5 gom 7 tiểu mục thành 3 theo N4 (VH1 kèm pha giảm tải KB2 chuyển từ 5.3, VH2, graceful shutdown), N6 (VH3, VH4, VH5), N7 (VH6). Thêm `05-00-danh-gia.md` với đoạn mở chương kèm số chính. Sửa dẫn chéo §5.5.x trong comment của 5.7.
- **Decision:** D124: bảng 5.3a đặt trước 5.3.1 vì phục vụ cả ba tiểu mục; tiêu đề 5.5.x không mang mã VH (quy-tac-viet §2), mã nằm trong câu chủ đề.
- **Results:** `kiem_van.py` 0 điểm cần xem ở 05-00, 05-02 tới 05-07; 05-01 còn 1 điểm "ngày tháng §5" có chủ ý (ngày phiên đo nêu một lần ở 5.1). lychee trên `docs/luan-van/*.md`: 0 lỗi. Chưa đo số trang (để bước 2, sau khi khôi phục phần lõi).
- **Deviations:** nội dung 5.5 chưa theo ADR-007 (PR #75: VH1 lấy từ V2, VH2 qua Git trên kind ở PR #78, N8 ở PR #76), vì các PR đó chưa merge; sửa ở bước 2.
- **Links:** nhánh `docs/tr8-thesis-ch5-drafts`; `docs/luan-van/05-00-danh-gia.md`, `05-03-autoscaling-so-voi-tinh.md`, `05-05-kich-ban-van-hanh.md`.
- **Thesis:** chương 5.

## 2026-11-27 – Luận văn: chương 5 bước 2a, đưa ADR-007, VH2 qua Git và N8 vào 5.5–5.7

- **Task:** TR8 · **Environment:** none
- **Done:** trên nhánh `docs/tr8-thesis-ch5-drafts`, sửa 5.5 theo ADR-007 (PR #75): đoạn mở mục nêu phần nào chạy trên simulator và vì sao; 5.5.1 ghi VH1 lấy từ pha giảm tải của 3 lượt A2 × KB2, không phải lượt riêng; thêm vế chưa có bằng chứng `LLMPodPending` kêu ở ca kẹt Pending (`for: 10m` so với khoảng 300 s chờ); thêm đoạn kết quả vòng Git trên simulator (PR #78), phần cách làm dẫn sang 4.5 để không lặp; thời gian pod cũ giữ GPU trên V2 ghi "chưa đo". 5.5.2 thêm N8 trên simulator (PR #76). 5.5.3 nêu rõ LT8 và VH6 cùng mốc tính. 5.6: dòng F3, N8 và đoạn "phần còn thiếu" theo kết quả mới. 5.7: thêm đoạn hạn chế của phép đo trên simulator (không cold start, commit không qua PR và CI, người dựng lại đã quen hệ thống).
- **Decision:** D125: bằng chứng VH1 chỉ gồm 3 lượt A2 × KB2. Hai lượt A1 × KB2 giữ 4 replica suốt pha giảm (`scale_downs` 0), nên không kiểm được scale-down. F3 chuyển sang "Đạt" (vòng Git kiểm trên simulator theo ADR-007 D2), N8 sang "Đạt một phần" (còn thiếu chi phí).
- **Results:** `analysis/figures/v2-dg2/runs.csv`: 5 lượt KB2 của A1, A2; chỉ 3 lượt A2 có `scale_downs` = 3. Đo khuôn T bằng Word (pandoc → `do_trang_word_T.ps1`): chương 5 = 11,3 tr (5.1 0,8; 5.2 1,0; 5.3 2,1; 5.4 1,1; 5.5 3,0; 5.6 1,9; 5.7 + kết chương 1,0), chưa tính Hình 5.3b, dưới định hướng 14–17 tr. `kiem_van.py` 0 điểm cần xem ở 05-05, 05-06, 05-07. lychee `docs/luan-van/*.md` 0 lỗi.
- **Deviations:** số và khẳng định trong các đoạn sửa dẫn từ nhánh của PR #75, #76, #78 (chưa merge); phần sửa chưa qua soát số độc lập (để bước 3).
- **Links:** `docs/luan-van/05-05-kich-ban-van-hanh.md`, `05-06-bang-nghiem-thu.md`, `05-07-han-che-phep-do.md`.
- **Thesis:** 5.5, 5.6, 5.7.

## 2026-11-27 – Luận văn: chương 5 bước 2b, khôi phục lõi 5.1–5.4

- **Task:** TR8 · **Environment:** none
- **Done:** trên nhánh `docs/tr8-thesis-ch5-drafts`, khôi phục phần lõi đã cắt ngày 24/11 từ các comment "Ý không đưa vào". 5.2: LT2 ở cluster nhà (1,5B) và trên A4000 khớp trong sai số làm tròn; đoạn LT3 ở cluster nhà (điểm gãy khi số request chạy chạm 32); giả thuyết C bám TPOT ở batch lớn ghi rõ "chưa kiểm chứng". 5.3.1 viết lại thành 4 đoạn: mô hình LT6 của GPU utilization, khoảng hở tín hiệu trên V2 (A2 4,6×, KV cache 3,9× nhưng đứng yên khi quá tải), A1 trong ma trận (97–98% GPU-giờ của S4 trong pha ổn định của KB1), pha tăng dần của KB3. 5.3.2: A1 × KB1 tiết kiệm 9,4% và 10,3% (một lượt dưới ngưỡng); vì sao A2 giữ 4 replica suốt pha duy trì của KB3 (mẫu đòi 4 replica cách nhau ≤ 120 s, ngắn hơn cửa sổ ổn định 300 s). 5.3.3: tốc độ xử lý và hàng đợi của pod cũ. 5.4: LT4 ở cluster nhà (pha 7 mất 107–109 s), compile cache của ba lượt L2. 5.7: so C giữa A4000 (2 lõi CPU mỗi pod) và V2 chỉ để tham khảo. Sửa ", nên" lặp ở 05-02, 05-04, 05-07; dòng "Soát văn phong" ở 05-01–05-04 ghi kiem_van. Thêm 2 mục NVIDIA vào `tai-lieu.bib` và dẫn ở 5.1.
- **Decision:** D126: 448 GB/s dẫn datasheet A4000 của NVIDIA; 288 GB/s dẫn bài của NVIDIA về VRAM dòng RTX 40, vì trang sản phẩm 4060 Ti chỉ ghi bus 128-bit. Giữ số pha tăng dần của KB3 ở 5.3.1 dù pha này không được chấm, vì đây là một điểm yếu của A2 (quy-tac-viet §3.3).
- **Results:** chạy lại `analysis.dg2_a2` trên `runs/v2-vm/v2-dg2`: số phần 1, 3, 4, 5 khớp comment nguồn. `phases.csv` pha ramp của KB3: SLO A1 1,0, A2 0,841 và 0,799. Thứ tự đo ĐG3 theo `trigger_unix`: L2-2, L0-2, L2-1, L2-3, L0-1; compile cache hit ở cả 3 lượt L2. Đo khuôn T bằng Word: chương 5 = 13,5 tr (5.1 0,8; 5.2 1,3; 5.3 3,8; 5.4 1,4; 5.5 3,0; 5.6 1,9; 5.7 + kết chương 1,0), chưa tính Hình 5.3b (pandoc thiếu rsvg-convert), cộng hình thì khoảng 14 tr, trong định hướng 14–17. `kiem_van.py`: 0 điểm ở mọi file 05-*, trừ 1 điểm ngày tháng có chủ ý ở 05-01. lychee `docs/luan-van/*.md` 0 lỗi; pandoc `--citeproc` dựng đủ 2 mục mới.
- **Incidents:** trang sản phẩm 4060 Ti và trang A4000 không ghi băng thông; datasheet A4000 phải trích chữ bằng pypdf (bản quét, OCR đọc "4'8GB/s" cạnh "256-bit"). TechPowerUp trả 403.
- **Deviations:** phần thêm chưa qua soát số độc lập (để bước 3).
- **Links:** `docs/luan-van/05-01` đến `05-04`, `05-07`, `tai-lieu.bib`.
- **Thesis:** 5.1–5.4, 5.7.

## 2026-11-27 – Luận văn: chương 5 bước 3, soát số độc lập và soát diff

- **Task:** TR8 · **Environment:** none
- **Done:**
  1. Soát số độc lập 5.0–5.7 (quy-tac-viet §9, lượt khác lượt viết): đối chiếu khoảng 290 khẳng định với nguồn trong comment, `runs/`, `analysis/figures/v2-dg2/` và nhánh của PR #75–#81. Ra 3 lỗi xác nhận và 7 điểm nghi ngờ; đối chiếu lại từng lỗi với nguồn rồi sửa (commit `afeb261`), đánh dấu "Soát số: 27/11/2026" ở cả 8 file.
  2. `/code-review high` trên diff so với `main`: 10 điểm, đều đúng; sửa 9 điểm ở văn bản và comment nguồn, điểm thiếu nhật ký là mục này.
- **Decision:** D127: F2 → Đạt một phần (T7 chưa chạy) cho khớp chú thích Bảng 5.6a; hướng giảm cái giá của tải tăng đột ngột ở 5.3.3 viết cùng cách với 5.6.2 (nâng số replica tối thiểu theo khung giờ).
- **Results:**
  - Lỗi soát số: 5.7 ghi phiên V2 cấp 6 lõi CPU mỗi pod vLLM, cấu hình thật ở commit 10c0527 là 3 lõi (`requests` = `limits` `cpu: "3"`); 5.6.2 gán 100% SLO cho "khi tải tăng dần", trong khi KB3 chỉ chấm pha duy trì (pha tăng dần A2 84,1% và 79,9%); 5.5.1 nêu "máy nhà thiếu RAM" là lý do của ADR-007, trong khi ADR-007 nêu cluster nhà không sẵn sàng trước mốc nộp.
  - Điểm nghi ngờ đã sửa: 93% GPU utilization là của S4 × KB1, không phải A1; A2 đòi 2, 3, 7 replica ở λ = 3,5, 4, 5; bốn commit của vòng Git là nâng min, đổi tham số, hai lần revert; 7 giờ 14 phút gồm cả thời gian chuyển giữa 17 lượt khoảng 24 phút.
  - Lỗi `/code-review`: "3,66–3,73 replica Ready, tức 97–98% GPU-giờ" sai phép suy (GPU-giờ tính từ lúc pod được xếp lịch); TPOT p50 ở nhà tăng 16,7 → 18,1 ms qua điểm gãy rồi mới đứng yên; Bảng 5.6a chưa được nhắc trong bài; công thức chuyển sang `$…$`; các danh sách "Ý không đưa vào" và comment ngân sách cũ sau bước 2b.
  - Đã khớp nguồn: VH1 3 lượt A2; vh2b 371,6 s; VH2 qua Git 0 lỗi / 615 request, sync 138–247 s; N8 1.481 s; Bảng 5.4a từng ô. Băng thông 288 và 448 GB/s chưa mở lại được trang NVIDIA trong lượt soát.
  - Độ dài: 13,5 tr khuôn T (đo ở bước 2b, chưa tính Hình 5.3b); các sửa ở bước này chỉ thay vài câu, chưa đo lại.
- **Incidents:** thứ tự đo ĐG3 theo `trigger_unix` (L2-2 trước L0-2) lệch với câu "ba lượt L2 đo sau L0-2" trong nhật ký Quang tuần 07 mục 19/11; thân bài theo dữ liệu, không đổi kết luận.
- **Deviations:** 00-thong-so §9.1 ghi `cpu: 6`, `memory: 24Gi` cho pod vLLM trên cloud, khác cấu hình đã chạy ở V2 (3 lõi, 16Gi); chưa sửa ở PR này.
- **Links:** `docs/luan-van/05-0*.md`; nhánh `docs/tr8-thesis-ch5-drafts`.
- **Thesis:** chương 5.

## 2026-11-27 – Chốt ba số còn mở ở 4.5, 4.6 và 5.5

- **Task:** TR8 · **Environment:** none
- **Done:** tra `runs/v2-vm/`, `analysis/figures/v2-dg2/tables/runs.csv`, `experiments/ops/vh.py`, `experiments/runner/collect.py`, `analysis/build_tables.py`, `van-hanh.md` mục LT8 để chốt ba số; sửa 4.5, 4.6 (PR #81) và 5.5, 5.7 (PR #82).
- **Decision:**
  1. Thời gian pod cũ trên V2 giữ GPU khi rolling update: giữ "chưa đo". Thư mục `ops-vh2b-20261118-170715` chỉ có `timeline.json` 4 mốc, `summary.json` và `load/`; không có log pod, sự kiện pod hay dữ liệu Prometheus. 371,6 s tính từ lúc patch annotation tới lúc `kubectl rollout status` xong. Vì cả 4 GPU đã có pod và chiến lược là `maxSurge: 0` / `maxUnavailable: 1`, pod được thay lần lượt, nên trung bình mỗi pod cũ giữ GPU dưới 93 s (cận trên, gồm cả cold start). Thân bài 4.5, 5.5.1, 5.7 nay nêu đúng lý do "phiên đo không lưu log hay mốc từng pod" thay cho "chưa đọc log".
  2. Số lượt có pha giảm tải ở KB2: cả hai nguồn đều đúng. 5 lượt A1/A2 × KB2 có pha drop với 0 lỗi, nhưng chỉ 3 lượt A2 bớt pod dưới tải (`scale_downs` 3 mỗi lượt); 2 lượt A1 có `scale_downs` 0.
  3. Mốc tính LT8 cho N7: từ lúc vi phạm theo log client tới lúc `ALERTS` chuyển firing, giống VH6 (`time_to_alert_s`); LT8 cho 159–242 s. Bộ số tính từ lúc bơm (firing 173–286 s) không dùng cho N7. 5.5.3 đổi "page đến sau" thành "chuyển sang firing sau", và ghi rõ số chưa gồm thời gian Alertmanager gom nhóm và gửi tin.
- **Results:** kiem_van 0 điểm ở 4 file; lychee 0 lỗi; `/code-review high` trên phần sửa ch. 5: 8 điểm, 7 điểm đã sửa (câu "chờ thêm ít nhất 30 s" sai vì `group_interval` áp dụng khi nhóm còn tồn tại, nên bỏ; comment nguồn còn lời cũ; 15–20 s sửa thành 12–17 s; thêm nguồn `common/serving/deployment.yaml`), 1 điểm không sửa (đưa cận trên 93 s vào thân bài: 5.5.1 đã nêu "khoảng 93 s mỗi pod").
- **Links:** PR #81 (`0110e59`), PR #82; `docs/luan-van/04-05-scale-down-cap-nhat.md`, `04-06-giam-sat-canh-bao.md`, `05-05-kich-ban-van-hanh.md`, `05-07-han-che-phep-do.md`.
- **Thesis:** §4.5, §5.5.1, §5.5.3, §5.7.
## 2026-11-25 – Luận văn: bản base mục 4.1 và 4.2, đo khuôn T chương 3

- **Task:** TR8 · **Environment:** none
- **Done:**
  1. Viết `docs/luan-van/04-01-ha-tang-trien-khai.md` (4.1.1 Ansible và k3s, 4.1.2 Argo CD và CI, 4.1.3 bí mật, bảo vệ tối thiểu, dựng lại) và `04-02-phuc-vu-vllm.md` theo khung sáu bước của quy tắc viết §2.1 (sáu bước là thứ tự đoạn, không thành tiêu đề).
  2. Đối chiếu từng số với nguồn gốc trước khi viết: mã (`ansible/`, `envs/*/serving/`, `common/serving/deployment.yaml`, `envs/home/argocd/root-app.yaml`, `.github/workflows/ci.yaml`), `van-hanh.md`, nhật ký Quang tuần 03–07, nhật ký Trình tuần 04, 06. Mỗi đoạn có comment nguồn.
  3. Cắt phần ngoại vi khỏi 4.1 (danh sách 8 app đưa Phụ lục A, sự cố yq, đường hầm SSH, chi tiết MTU) và ghi vào comment "Ý không đưa vào".
  4. Đo khuôn T bằng Word (`do_trang_word_T.ps1`): 4.1 = 4,4 tr, 4.2 = 2,6 tr; chương 3 (nhánh của PR #80) = 13,5 tr, trong khoảng 13–15.
- **Decision:** Trình để số dựng lại VH5 (8 phút 22 giây…) ở 5.5, mục 4.1.3 chỉ nêu "ba lần dựng VM gần nhất đều dưới 30 phút", theo bảng ranh giới của quy tắc viết §8 (kịch bản VH: cách làm ở chương 4, kết quả ở 5.5). Câu VH2 qua Git trên kind ở 4.1.2 dẫn sang 4.5 và 5.5, chưa ghi số vì PR của VH2 chưa merge.
- **Results:** `kiem_van.py` 0 điểm cả hai file (2.361 và 1.340 chữ văn xuôi); lychee `docs/luan-van/*.md` 0 lỗi; pandoc dựng `.docx` không lỗi.
- **Deviations:** 4.1 dài 4,4 tr khuôn T, hơi nhiều cho một mục hạ tầng. Nếu chương 4 vượt 22 tr khi ghép thì cắt ở 4.1 trước.
- **Links:** `docs/luan-van/04-01-ha-tang-trien-khai.md`, `docs/luan-van/04-02-phuc-vu-vllm.md`; nhánh `docs/tr8-thesis-ch4`.
- **Thesis:** mục 4.1, 4.2; bản nháp do agent viết từ nguồn trong repo, chưa qua bước soát số độc lập.

## 2026-11-25 – Luận văn: bản base mục 4.3 và 4.4

- **Task:** TR8 · **Environment:** none
- **Done:**
  1. Viết lại 4.3 từ nháp ngày 24/11 (nhánh của PR #69, bốn tiểu mục) thành hai tiểu mục theo dàn ý mới ở Kế hoạch §11.1: 4.3.1 đưa tải đồng thời của vLLM vào HPA qua KEDA, 4.3.2 thử autoscaling và fallback trên simulator. Thêm Bảng 4.3 (giá trị ScaledObject theo môi trường) và kết quả vòng autoscaling đầu tiên trên kind (HPA lên 3 replica ở giây 16, tín hiệu mỗi pod 7–11 so với 8,7 tính trước theo định luật Little; nhật ký Quang tuần 05 mục 04/11).
  2. Viết mới 4.4 (cold start, một mục, không chia cấp 3): volume `hostPath` chung cho model và compile cache, role Ansible thay DaemonSet và Job của thiết kế, Bảng 4.5 so hai VM thử (capture CUDA graph 127 + 121 s so với 4 + 4 s), thử `cudagraph_mode: PIECEWISE` rồi bỏ, cách đo L0/L2 và bộ đọc log tám pha, hai sự cố (image GC ở nhà, lỗi `set -e` của `dg3.sh`).
  3. Dữ kiện 4.4 do agent Explore gom từ `van-hanh.md`, phiên A4000 §9, nhật ký Quang tuần 06–07, `dg3.sh`, `vllm_log.py`; phiên chính đối chiếu lại từng số trước khi viết.
  4. Đổi tên tạm của 4.3.2 trong Kế hoạch §11.1.
- **Decision:** Trình để số ĐG3 từng lượt và tỷ lệ L2/L0 ở 5.4, mục 4.4 chỉ nêu "L2 nhỏ hơn một nửa L0, đạt chỉ tiêu" (quy tắc viết §8). Lý do giữ chế độ CUDA graph mặc định (TPOT chậm hơn 32–45% với PIECEWISE) suy từ bảng benchmark của `van-hanh.md` 08/11, nhật ký không ghi câu lý do riêng; đã ghi rõ trong comment nguồn.
- **Results:** đo khuôn T bằng Word: 4.3 = 3,07 tr (1.541 chữ văn xuôi), 4.4 = 2,10 tr (1.139 chữ). Chương 4 tới 4.4: khoảng 12,2 tr, còn 6,8–9,8 tr cho 4.5–4.7 và kết chương. `kiem_van.py` 0 điểm cả hai file; pandoc `--citeproc` không cảnh báo.
- **Links:** `docs/luan-van/04-03-autoscaling.md`, `docs/luan-van/04-04-cold-start.md`, `docs/chi-tiet/06-ke-hoach-quan-ly.md` §11.1; nhánh `docs/tr8-thesis-ch4`.
- **Thesis:** mục 4.3, 4.4; bản nháp do agent viết từ nguồn trong repo, chưa qua bước soát số độc lập (làm khi mở PR chương 4).

## 2026-11-25 – Luận văn: bản base mục 4.5

- **Task:** TR8 · **Environment:** none
- **Done:**
  1. Viết `docs/luan-van/04-05-scale-down-cap-nhat.md` (một mục, không chia cấp 3) theo khung sáu bước: tham số tắt pod trong Deployment chung và overlay sim; kiểm graceful shutdown ở nhà (48 stream, 144/144); sự cố vLLM không thoát khi nhận SIGTERM và hai ca đối chứng; ba ca VH2 trên V2 qua annotation; sự cố kịch bản đạt oan trên kind và bước kiểm điều kiện đầu vào; vòng Git trên kind (615 request, 0 lỗi, TTFT 206 → 306 → 206 ms); độ trễ push → sync và các điểm khác quy trình.
  2. Dữ kiện do agent Explore gom từ `van-hanh.md` (06/11), nhật ký Quang tuần 05–07, Kiến trúc §8, Vận hành §5, `deployment.yaml`, `vh.py` và mục 25/11 trên nhánh `feat/tr8-vh2-git-run`; phiên chính đối chiếu lại các số then chốt với nguồn trước khi viết.
- **Decision:** Không ghi số lượt của pha giảm tải KB2 ở 4.5, vì hai nguồn lệch nhau: nhật ký Quang tuần 07 (19/11) ghi 5 lượt A1/A2 × KB2, ADR-007 và Môi trường §13 ghi 3 lượt A2 × KB2. Mục 5.5.1 phải chốt số này từ `runs.csv`. Số thời gian của vh2a/b/c và bảng bốn bước VH2 qua Git để ở 5.5.1 (quy tắc viết §8).
- **Results:** đo khuôn T bằng Word: 4.5 = 2,05 tr (1.245 chữ văn xuôi). Chương 4 tới 4.5: khoảng 14,3 tr, còn 4,7–7,7 tr cho 4.6, 4.7 và kết chương. `kiem_van.py` 0 điểm.
- **Links:** `docs/luan-van/04-05-scale-down-cap-nhat.md`; nhánh `docs/tr8-thesis-ch4`.
- **Thesis:** mục 4.5; bản nháp do agent viết từ nguồn trong repo, chưa qua bước soát số độc lập (làm khi mở PR chương 4). Nguồn của đoạn vòng Git trỏ tới nhánh PR vh2-git, sửa sang `main` khi PR đó merge.

## 2026-11-25 – Luận văn: bản base mục 4.6

- **Task:** TR8 · **Environment:** none
- **Done:**
  1. Viết `docs/luan-van/04-06-giam-sat-canh-bao.md` theo khung sáu bước, ba tiểu mục của Kế hoạch §11.1. 4.6.1: đổi từ DCGM sang `nvidia_gpu_exporter`, PodMonitor 5 s, kube-state-metrics đọc condition ScaledObject, tám recording rule, Bảng 4.6 (ba dashboard, 20/9/16 panel), CI kiểm dashboard, hai điểm lệch của simulator (nhãn `finish_reason`, TTFT không gồm thời gian chờ hàng đợi). 4.6.2: 9 test promtool, mutation 11/11, kiểm độ phủ, định tuyến bằng `amtool`, chuỗi `KedaScalerErrors` tới `tg-mock` trên kind, VH6 trên V2, sự cố `KedaScalerErrors` qua hết test mà không kêu được, `AlertmanagerFailedToSendAlerts` trong V2. 4.6.3: khung runbook, VH3 trên V2 và lần thử N = 2, các sự cố thật đều ở tầng host và chưa runbook nào được dùng.
  2. Dữ kiện do agent Explore gom; phiên chính đối chiếu lại các số then chốt (daemonset GPU, nhật ký Trình tuần 05 dòng 403–409, tuần 06 dòng 46 và 114, tuần 07 dòng 533, nhật ký Quang tuần 07 dòng 147–194 và 301–327, `llm-test.yaml`, khung runbook).
- **Decision:** Không lặp lại Bảng 3.7 và lý do thiết kế của 3.5. Thời gian tới firing của LT8 để 5.5, vì nhật ký Trình tuần 07 có hai bộ số LT8 tính từ hai mốc khác nhau (mục 16/11 và mục 21/11). Bỏ câu nói cảnh báo đĩa của chart ở mức warning nên không được gửi, vì chart còn có bản critical và chưa kiểm cảnh báo nào kêu ở mức đĩa 80%.
- **Results:** đo khuôn T bằng Word: 4.6 = 3,9 tr (1.983 chữ văn xuôi). Chương 4 tới 4.6: khoảng 18,2 tr, còn khoảng 3,8 tr cho 4.7 và kết chương (định hướng 19–22 tr). `kiem_van.py` 0 điểm, lychee 0 lỗi.
- **Incidents:** agent gom dữ kiện bị gọi ở chế độ chạy nền thay vì foreground, nên vòng tự chạy trả kết quả "partial" trước khi có dữ kiện; mục được viết ở lượt tiếp theo của cùng vòng, sau khi agent báo về.
- **Links:** `docs/luan-van/04-06-giam-sat-canh-bao.md`; nhánh `docs/tr8-thesis-ch4`.
- **Thesis:** mục 4.6; bản nháp do agent viết từ nguồn trong repo, chưa qua bước soát số độc lập (làm khi mở PR chương 4).

## 2026-11-25 – Luận văn: bản base mục 4.7 và kết chương 4

- **Task:** TR8 · **Environment:** none
- **Done:** viết `docs/luan-van/04-07-cong-cu-danh-gia.md`: 4.7.1 máy tạo tải và runner (CPU theo số chunk SSE, nhiều tiến trình, sự cố port-forward, paused-replicas, thu mốc và log pod trong lúc chạy, điểm lệch sao lưu và annotation pha); 4.7.2 kiểm tính hợp lệ và phân tích (10 tiêu chí, tiêu chí nào được sửa sau lỗi nào, kết quả V2, ba chỗ khác thiết kế, `build_tables`); kết chương với Bảng 4.7 (vấn đề GPU/LLM → cách xử lý → bằng chứng). Dữ kiện gom bằng agent chỉ đọc, số chính đối chiếu lại với nhật ký và mã.
- **Results:** tính lại từ `runs/v2-vm/v2-dg2/*/attempt-1/{loadgen,checks}.json`: 17/17 lượt hợp lệ ở lần thử đầu; lệch lịch gửi p99 lớn nhất 5,98 ms, event loop p99 lớn nhất 4,11 ms, CPU máy tạo tải lớn nhất 43,6 % một lõi, throttle 0, tín hiệu scale mất mẫu tối đa 5,0 s. Chưa đo khuôn T; `kiem_van` còn 10 điểm cần xem (chưa sửa vì vòng dừng do quota).
- **Deviations:** đối chiếu TTFT client với histogram server ở mọi lượt (Môi trường §9) chưa làm trên vLLM thật; chỉ có ở LT8 trên simulator. Ghi ở 4.7.2, để 5.7.
- **Links:** nhánh `docs/tr8-thesis-ch4`.
- **Thesis:** §4.7, kết chương 4.

## 2026-11-26 – Luận văn: soát văn phong 4.7 và đo trang chương 4

- **Task:** TR8 · **Environment:** none
- **Done:**
  1. Sửa 10 điểm `kiem_van` ở `04-07-cong-cu-danh-gia.md`: bỏ tên người và ngày khỏi thân bài (đã có trong comment nguồn), tách câu 46 chữ liệt kê tiêu chí của runner, bỏ hai câu lặp ", nên", đổi "tối ưu" và "chứng minh", thêm comment nguồn cho Bảng 4.7.
  2. Đo khuôn T cả chương bằng Word: gộp 04-01…04-07, bỏ comment, `pandoc` sang .docx, `do_trang_word_T.ps1`. Lần đầu 22,1 tr, vượt trần 22.
  3. Cắt 4.1 (phần ngoại vi): bỏ ý laptop làm node thứ hai (đã có ở 4.2), token Hugging Face, cách runner tắt auto-sync (4.7 đã nêu); rút gọn ba câu khác. Ghi danh sách ý đã cắt ở comment đầu 04-01.
- **Decision:** cắt ở 4.1 trước theo định hướng độ dài chương 4 (phần hạ tầng là ngoại vi so với autoscaling), chỉ bỏ ý đã có ở mục khác hoặc không đổi kết luận.
- **Results:** chương 4 = 21,8 tr khuôn T, chưa có hình (4.1 4,2 · 4.2 2,7 · 4.3 3,1 · 4.4 2,1 · 4.5 2,1 · 4.6 3,9 · 4.7 2,9 · kết chương 0,7). `kiem_van` 0 điểm ở 04-01 và 04-07.
- **Incidents:** lần đo thử đầu ra 45 tr vì dùng `pandoc -f markdown-raw_html`, làm comment nguồn hiện thành chữ và nuốt tiêu đề ngay sau comment; sửa bằng cách xoá comment trước khi chuyển.
- **Links:** `docs/luan-van/04-01-ha-tang-trien-khai.md`, `docs/luan-van/04-07-cong-cu-danh-gia.md`; nhánh `docs/tr8-thesis-ch4`.
- **Thesis:** chương 4; nếu chèn hình vào chương 4 thì phải cắt tiếp để giữ trần 22 tr.

## 2026-11-26 – Luận văn: soát số độc lập và soát diff chương 4

- **Task:** TR8 · **Environment:** none
- **Done:**
  1. Soát số độc lập 4.1–4.7 (quy-tac-viet §9, khác lượt viết nháp): đối chiếu khoảng 240 khẳng định với comment nguồn, ra 20 lỗi xác nhận và 6 điểm nghi ngờ. Trình đối chiếu lại từng lỗi với nguồn rồi sửa cả 20 (commit `82b327c`).
  2. `/code-review high` trên cả diff so với `main`: 10 điểm, đều đúng; sửa 8 điểm ở văn bản, điểm về nguồn nằm trên nhánh chưa merge ghi ở đầu PR, điểm thiếu nhật ký là mục này.
  3. Đánh dấu "Soát số: 26/11/2026" ở comment trạng thái của cả 7 file; đo lại khuôn T bằng Word.
- **Decision:** giữ chương 4 ở 22,1 tr khuôn T (định hướng 19–22 tr), không cắt thêm: phần tăng 0,3 tr là câu điều kiện đo và giới hạn của số liệu do bước soát yêu cầu; D103 coi số trang theo chương là định hướng, trần là 85 tr cả thân bài.
- **Results:** các lỗi đáng kể đã sửa:
  - T3 giữ 298–304 s ở 6 lần, 292 s ở 1 lần (lỗi đồng hồ VM WSL2); tiêu chí đúng của script là 295–330 s.
  - Retention Prometheus ở nhà và VM thuê là 3 ngày, ở simulator 1 ngày.
  - 27 s tải model là lần chạy tay ngày 08/11, trước khi có role tải trước; N8 trên simulator mới là phép thử gần đúng.
  - Ca sai khoá API chỉ thử ở nhà; VH2 qua Git có hai lần `git revert`; ở KB1, A2 giữ 1 replica.
  - Runner thử tối đa hai lần mỗi lượt; ba giá trị tệ nhất của tiêu chí hợp lệ nằm ở ba lượt khác nhau.
  - Câu "mỗi pod giữ GPU đủ 180 s" giới hạn về máy nhà: trên V2, vh2b thay 4 pod trong 371,6 s (< 4 × 180 s), nên câu suy ra từ vh2a (181,6 s) bị bỏ.
  - 4.6 nói đúng là `LLMSLOBurnFast` đã được kiểm trên simulator bằng cách tăng TTFT giả (LT8).
  - Kiểm tra: `kiem_van` 0 điểm cần xem ở cả 7 file; `pandoc --citeproc` không lỗi; `lychee --offline` 0 lỗi. Chương 4 = 22,1 tr khuôn T, chưa có hình.
- **Incidents:** lượt soát số đầu dừng giữa chừng vì hết quota tuần; sau khi quota reset, lượt soát chạy tiếp từ chỗ dừng.
- **Links:** nhánh `docs/tr8-thesis-ch4`; `docs/luan-van/04-0*.md`.
- **Thesis:** chương 4. Chưa rõ vì sao pod trên VM thuê nhả GPU sớm hơn 180 s; nếu cần thì đưa vào 5.5.1 hoặc 5.7.

## 2026-11-27 – Đoạn mở chương 4

- **Task:** TR8 · **Environment:** none
- **Done:** viết `docs/luan-van/04-00-trien-khai-van-hanh.md` (tiêu đề chương và đoạn mở 5 câu) theo mẫu `03-00`, `05-00`: chương trả lời câu hỏi gì, khó khăn chính (mặc định và hành vi không hợp với LLM trên GPU), trình tự sáu bước của mỗi mục, các mục 4.1–4.7 và Bảng 4.7 ở kết chương. Không nêu số đo. Lượt tự chạy, vòng 1 ngày 27/11.
- **Decision:** ví dụ trong đoạn mở lấy từ Bảng 4.7 (rolling update cần GPU trống, vLLM không tự thoát khi nhận SIGTERM), gọi là "mặc định và hành vi", vì vLLM không thoát là hành vi trái giả định thiết kế, không phải một giá trị mặc định.
- **Results:** `kiem_van` 0 điểm cần xem (5 câu, câu dài nhất 34 chữ); `lychee --offline` 0 lỗi; bản gộp `gop.py` không còn khối [CHƯA VIẾT] ở chương 4. Đoạn mở 0,31 tr khuôn T, chương 4 = 22,77 tr (định hướng 19–22; việc cắt trang để ở danh sách việc nhóm C).
- **Incidents:** `/code-review high` ra 9 điểm trên bản đầu, đều sửa: gọi SIGTERM là "cấu hình mặc định" là sai; "hợp với ứng dụng web" vượt quá nguồn; thiếu "điểm lệch" trong sáu bước; hai câu quá 35 chữ; liệt kê mục có "và" lồng nhau; thiếu chỉ tới Bảng 4.7; "trình bày" lặp 4 lần; thiếu "runbook" ở tên 4.6.
- **Links:** nhánh `docs/tr8-thesis-ch4`, PR #81.
- **Thesis:** đoạn mở chương 4.
## 2026-11-24 – Luận văn: cắt mục 3.1 về 1,5 trang

- **Task:** TR8 · **Environment:** none
- **Done:**
  1. Merge `origin/main` vào nhánh `docs/tr8-thesis-3-1-base` (PR #63) để có ngân sách trang (D94).
  2. Viết lại `03-01-yeu-cau-chi-tieu.md`: 5 bảng còn 1 (F1–F7 và N1–N8 gộp, mỗi dòng một cụm ngắn); bỏ 4 tiểu mục; giá trị SLO và lý do của ngưỡng viết thành văn xuôi.
  3. Ghi các ý đã cắt và nơi chứa chúng vào dòng 3.1 của `nguon-tu-lieu.md`, và vào comment nguồn của mục.
- **Decision:** bảng mã định danh đầy đủ (S, A, KB, ĐG, VH, LT, L, V, C, B\*, N) chuyển khỏi 3.1 sang danh mục mã định danh ở phần đầu quyển (quy-tac-viet §1 mục 4, §4). Thân bài 3.1 chỉ giữ bảng F/N và một câu dẫn tới mục 3.3–3.6, nơi từng mã được định nghĩa. Lý do: bảng mã tốn khoảng 0,8 trang (khuôn B), hơn nửa ngân sách 1,5 trang. Không chọn giữ bảng mã và bỏ bảng F/N, vì F/N là nội dung chính của mục. Ma trận truy vết (Bảng 3.1 cũ) bỏ khỏi thân bài; cột "Phép thử" của bảng F/N vẫn nối mỗi yêu cầu tới phép thử.
- **Results:** đo bằng dàn trang thử (pandoc + Typst, hai khuôn như mục 23/11):

  | Bản | Chữ văn xuôi | Bảng | Khuôn A | Khuôn B |
  |---|---|---|---|---|
  | Base (trước khi cắt) | 1.181 | 5 | 5 trang | 7 trang |
  | Lần thử 1 (giữ bảng mã gọn) | 580 | 2 | 2,43 | 3,25 |
  | Lần thử 2 (trước `/code-review`) | 344 | 1 | 1,16 | 1,49 |
  | Bản cuối (sau khi sửa theo review) | 314 | 1 | 1,17 | 1,44 |

  `kiem_van.py` 0 điểm; lychee `docs/luan-van/*.md` 0 lỗi. `/code-review high`: 10 điểm, sửa cả 10. Phần lớn do nén bảng làm mất điều kiện của chỉ tiêu (pha của N1, "so với S4" của N3, ca 1 replica của N4, điều kiện fallback của N6, mốc tính giờ của N2a). Ngoài ra: lý do ngưỡng TTFT bị đảo so với ADR-005 T3, câu chủ đề "mọi ngưỡng tính từ nền tảng" mâu thuẫn với mức 95% theo thông lệ, "tức …" lồng định nghĩa (quy-tac-viet §3.2). Bỏ lý do TPOT 100 ms (ghi ở `nguon-tu-lieu.md`) để giữ trong 1,5 trang.
- **Deviations:** quy-tac-viet §4 trước ghi "mã định danh định nghĩa ở chương 3, gom vào một bảng"; đã sửa thành: mỗi mã định nghĩa ở mục chương 3 dùng nó, bảng gom nằm ở danh mục đầu quyển. Kế hoạch §11.1 (dòng chương 3) bỏ "truy vết, bảng mã định danh" khỏi 3.1.
- **Links:** `docs/luan-van/03-01-yeu-cau-chi-tieu.md`, `docs/luan-van/nguon-tu-lieu.md` (dòng 3.1), `docs/luan-van/quy-tac-viet.md` §4, `docs/chi-tiet/06-ke-hoach-quan-ly.md` §11.1; PR #63.
- **Thesis:** §3.1; danh mục mã định danh ở phần đầu quyển lấy từ bảng mã của bản base (commit `fbe651b`).
## 2026-11-24 – Luận văn: bản base mục 3.2 (Kiến trúc tổng thể)

- **Task:** TR8 · **Environment:** none
- **Done:** viết `docs/luan-van/03-02-kien-truc-tong-the.md` theo bố cục 3.2 (ba luồng: request, autoscaling, thay đổi qua Git; hai tầng môi trường dùng chung base Kustomize; bảo vệ tối thiểu). Đối chiếu từng khẳng định với Kiến trúc §1–§5, §18; Môi trường §1, §2.7; Thông số §3, §9, §10; Vận hành §7–§8; ADR-006 §3, §3.1; `envs/home/argocd/apps/`, `Makefile`, `docs/phien-ban.md`. Thêm `argocd-cluster-bootstrapping` (Argo CD v3.5.4) vào `tai-lieu.bib`. Đo trang, cắt, chạy `/code-review high`, sửa, đo lại.
- **Decision:** chèn tạm hình kiến trúc hiện có (Hình 2 của `docs/chi-tiet/`) làm Hình 3.2a để đo trang có tính hình; hình phải vẽ lại trước khi ghép, vì còn ghi giới hạn tốc độ ở Traefik và chưa có Argo CD. Không chèn Hình 6 (còn A4000, A3/A4): Bảng 3.2a thay cho nó. Giữ cách gọi "hai tầng" của Môi trường §1, bảng vẫn tách ba cột (simulator, máy nhà, VM thuê).
- **Results:** bản đầu khoảng 900 chữ (đếm thô bằng `wc`, gồm tiêu đề và chú thích), bản cuối 505 chữ văn xuôi (kiem_van), 1 bảng, 1 hình. Dàn trang thử có chèn hình: bản đầu 2,87 trang (khuôn B), bản cuối 1,65 trang (khuôn A), 1,98 trang (khuôn B). kiem_van 0 điểm; lychee 0 lỗi.
- **Incidents:** `/code-review high` báo 10 điểm, sửa cả 10: đếm sai số lớp bảo vệ còn giữ (là ba lớp, gồm ghim phiên bản, không phải hai); lý do lược bảo mật viết lệch ADR-006 §3.1; thiếu GPU replica ở máy nhà; `make bootstrap` là Ansible, không phải Helm; "ba môi trường" lệch "hai tầng" của nguồn; thiếu điều kiện self-heal; nói quá về simulator; chú thích hình sai khuôn README; ô tiêu đề bảng trống; "Ba đánh giá" chưa được định nghĩa. Script đo `run.sh` dừng khi `31.md` rỗng (`grep` trả mã 1 dưới `set -e`), nên mục 3.2 được đo ở vị trí của `31.md`.
- **Links:** `docs/luan-van/03-02-kien-truc-tong-the.md`, `docs/luan-van/tai-lieu.bib`.
- **Thesis:** §3.2. Việc kéo theo: chương 2 định nghĩa Kustomize base/overlay, App-of-Apps, k3s, time-slicing, external metric; tên đầy đủ Qwen2.5-0.5B/3B-Instruct xuất hiện lần đầu trước 3.2; mục 6.2 nhận ba lớp bảo vệ bị lược.
## 2026-11-24 – Luận văn: bản base mục 3.3 (thiết kế autoscaling) và cắt về 2,5 trang

- **Task:** TR8 · **Environment:** none
- **Done:**
  1. Bản base 3.3 (commit `28be408`, 23/11): ba tiểu mục tín hiệu, threshold và hành vi, mất tín hiệu; mỗi đoạn có comment nguồn trỏ về `docs/chi-tiet/`, manifest và tài liệu KEDA 2.21.
  2. Merge `origin/main` (có PR #65, ngân sách trang D94), rồi cắt theo thứ tự quy-tac-viet §3.1: Bảng tín hiệu không chọn còn hai câu (TTFT p95, KV cache); bỏ A3/A4, tolerance, ví dụ 3 B\*; gộp 4 tiểu mục thành 3; Bảng 3.3a bỏ cột "Vai trò", Bảng 3.3b bỏ dòng max, scale-up, tolerance.
  3. `/code-review high` báo 10 điểm, sửa 9 (dưới); điểm "vượt ngân sách" không sửa vì reviewer ước theo chữ, còn số đo dàn trang thử đã đạt.
- **Decision:** ý bị cắt chuyển chỗ: exporter GPU không có label pod sang 4.3; cảnh báo `KedaScalerErrors` sang 3.5; Deployment không đặt `replicas` (Argo CD và HPA) sang 3.2; giới hạn "threshold gắn với phân phối độ dài request" sang mục Hạn chế. Comment nguồn của 3.3 ghi lại từng chỗ và § gốc.
- **Results:** đo bằng `.work/tools/do_trang/run.sh` (citation thay tạm bằng `[1]` vì Typst không có nhãn):

  | Bản | Văn xuôi | Bảng | Khuôn A (13 pt) | Khuôn B (14 pt) |
  |---|---|---|---|---|
  | Base 23/11 | 1.715 chữ | 3 | 5 trang | 6 trang |
  | Sau cắt | 809 chữ | 2 | 1,9 trang | 2,5 trang |

  Trang lẻ ước từ toạ độ dòng chữ thấp nhất trên trang cuối. `kiem_van.py` 0 điểm; lychee 0 lỗi.
- **Incidents:** review phát hiện bản base viết sai cơ chế mất metric: văn cũ nói "giữ mặc định ignoreNullValues", nhưng truy vấn của A1 và A2 kết thúc bằng `or vector(0)` nên không bao giờ rỗng; sửa theo manifest. Các điểm khác đã sửa: thời gian phát hiện 10–25 s (Kiến trúc §6, bảng thứ hai, gồm chờ vượt tolerance) thay cho "tối đa 10 s"; lý do loại TTFT p95 theo Kiến trúc §10.5 (prefill, cửa sổ `rate()` 1 phút) thay cho "giảm ngay sau scale-up", vốn mâu thuẫn với đoạn hàng đợi ở pod cũ; KV cache ghi là dự đoán, chưa kiểm chứng; A1 cộng mọi GPU của node chứ không cộng theo pod; `--max-num-seqs` 64 ghi rõ là máy cloud (nhà 16); fallback ghi "khoảng 20 s theo thiết kế", số đo V2 16,8 s để chương 5; công thức trần đổi sang `$…$` theo README.
- **Links:** `docs/luan-van/03-03-thiet-ke-autoscaling.md`; nhánh `docs/tr8-thesis-3-3-base`.
- **Thesis:** §3.3; Hình 4 (vòng lặp autoscaling) còn ghi model 7–8B và sync 15 s, vẽ lại trước khi chèn.
## 2026-11-24 – Luận văn: bản base mục 3.4 (Cold start và thay đổi an toàn)

- **Task:** TR8 · **Environment:** none
- **Done:**
  1. Đọc Kiến trúc §3.1, §7, §8; Vận hành §5; Thông số §9.2–§9.3; ADR-005 T1, T2; ADR-006 C8; quy tắc viết §2–§6.
  2. Viết `docs/luan-van/03-04-cold-start-thay-doi-an-toan.md`, ba tiểu mục: rút ngắn cold start (L0, L2), graceful shutdown cho request streaming, rolling update khi mọi GPU đều có pod. Mỗi đoạn có comment nguồn kèm §.
  3. Đối chiếu hai khẳng định với upstream ở phiên bản ghim: trang Pod Lifecycle của Kubernetes (nhánh `release-1.36`, khớp k3s v1.36.5) cho việc gỡ khỏi EndpointSlice chạy song song với preStop, grace period gồm cả preStop; `VllmConfig.shutdown_timeout` trong vLLM v0.31.0 (`vllm/config/vllm.py`, mặc định 0) cho mô tả của cờ `--shutdown-timeout`. Thêm hai mục vào `tai-lieu.bib`.
  4. Đo trang, cắt ba lần về ngân sách; `kiem_van.py`, lychee; `/code-review high`.
- **Decision:**
  - Bỏ bảng L0/L2 ba dòng, viết thành hai câu: bảng chiếm khoảng 0,3 trang, văn xuôi nói cùng ý trong khoảng 40 chữ.
  - Không chèn hình (Hình 12, 13, 16 của tài liệu thiết kế) để giữ ngân sách 1,5 trang. Hình 13 còn vẽ pha "drain" mà vLLM v0.31.0 không làm, phải sửa trước khi dùng ở 4.5.
  - Điểm lệch của `--shutdown-timeout` chỉ nêu một câu kèm dẫn chéo tới 4.5, vì người đọc thiết kế cần biết grace period mới là thứ giữ request; số đo để 4.5 và 5.5.
  - Bỏ khỏi thân bài, ghi trong comment nơi nên đặt: mức L1, `--enforce-eager`, startup probe 10 phút, sync window, `kubectl rollout undo`.
- **Results:** dàn thử 24/11: 1,15 trang (khuôn A), 1,49 trang (khuôn B), ngân sách 1,5; khoảng 550 chữ văn xuôi, không bảng, không hình. Lần viết đầu 2,31 trang (B). `kiem_van.py` 0 điểm; lychee 0 lỗi. `/code-review high` báo 10 điểm, sửa 9: đếm pha sai (KV cache và CUDA graph cùng pha 7 với compile), thiếu bước nạp weights, rollback phải giữ `minReplicaCount` 2, pod giữ GPU đủ 180 s chứ không phải "tới 180 s", thiếu trích dẫn, số replica tối thiểu khác nhau theo môi trường, thuật ngữ warm pool, ngoặc `{}` trong bib, thiếu nhật ký. Không sửa điểm "đoạn mở mục 3 câu": quy tắc viết §2 cho 1–2 câu, nhưng §3.2 và `kiem_van.py` đòi đoạn 3–7 câu; giữ 3 câu như mục 3.2.
- **Links:** `docs/luan-van/03-04-cold-start-thay-doi-an-toan.md`, `docs/luan-van/tai-lieu.bib`.
- **Thesis:** §3.4. Việc kéo theo: chương 2 định nghĩa probe, EndpointSlice, preStop, SIGTERM/SIGKILL, grace period, torch.compile, CUDA graph, maxSurge/maxUnavailable; 4.5 nhận chi tiết điểm lệch của `--shutdown-timeout`; 5.3 tính phần GPU-giờ do grace 180 s.
## 2026-11-24 – Luận văn: cắt mục 3.5 (mẫu văn) về 2 trang

- **Task:** TR8 · **Environment:** none
- **Done:**
  1. Merge `origin/main` vào nhánh `docs/tr8-thesis-3-5-sample` (PR #62) để có ngân sách trang và thứ tự cắt trong `quy-tac-viet.md`.
  2. Cắt `03-05-giam-sat-slo-canh-bao.md` theo thứ tự §3.1: bảng SLI thành văn xuôi; gộp 3.5.3 và 3.5.4; bảng cảnh báo bỏ cột "Lý do", còn lại hai lý do không hiển nhiên ở văn xuôi; công thức thời gian báo đưa vào câu. Những ý đã bỏ được ghi ở comment đầu file, kèm nơi còn giữ chúng (`docs/chi-tiet/04-van-hanh.md` §2.1, §3.2, §3.5, §4; mục 3.3; mục 4.6; mục 6.2; chương 5).
  3. Đo sau mỗi lượt cắt bằng dàn trang thử, rồi xem ảnh trang cuối để biết dòng nào bị tràn.
  4. Chạy `/code-review high`: 10 điểm, sửa 8.
- **Decision:**
  - Bỏ cột "Lý do" thay vì cắt thêm văn xuôi. Đo riêng bảng: 5 cột chiếm 0,61 trang (khuôn B), 4 cột 0,33 trang.
  - Định nghĩa page/ticket đặt trong chú thích Bảng 3.5a, vì dàn ý chương 2 ở Kế hoạch §11.1 chưa có hai thuật ngữ này.
  - Hai điểm yếu đã biết chuyển sang mục 6.2 (Hạn chế): một đợt lỗi 503 ngắn vẫn gây page, và `Watchdog` chưa được nối ra ngoài. Mục 6.2 phải nhắc lại hai điểm này.
  - Bỏ ý "mất metric nguồn thì kết quả là 0", vì mục 3.3 (PR #66) đã trình bày đúng cơ chế `or vector(0)`.
- **Results:** văn xuôi giảm từ 1.523 xuống khoảng 700 chữ; số bảng từ 2 xuống 1. Đo được 1,62 trang (khuôn A, 13 pt) và 1,97 trang (khuôn B, 14 pt), trước khi cắt là 3,63 và 4,88. Phần trang lẻ = (y thấp nhất trên trang cuối − lề trên) ÷ chiều cao vùng in. Cách đo cho lại đúng số của 3.3 ở vòng trước: 1,90 và 2,52. `kiem_van.py` báo 0 điểm; lychee không báo lỗi ở `docs/luan-van/`.
- **Incidents:**
  - Code review ra 10 điểm, 8 điểm đã sửa:
    - văn bản chưa nói TPOT vẫn được xét khi nghiệm thu;
    - con số 12 phút xuất hiện trước khi nêu ngưỡng;
    - lý do rút cửa sổ lệch với tài liệu nguồn (lượt đánh giá 12–24 phút);
    - thiếu lưu ý về 20 s trễ scrape và tính rule;
    - sau bảng không có câu nhận xét (quy-tac-viet §6);
    - thiếu ánh xạ 7 quy tắc ↔ 6 cảnh báo;
    - page/ticket chưa được định nghĩa;
    - header dẫn mã quyết định riêng và nguồn tên dashboard sai.

    Hai điểm còn lại không cần sửa: ý "mất metric thành 0" đã có ở 3.3; nhật ký được ghi ở mục này.
- **Links:** PR #62; `docs/luan-van/03-05-giam-sat-slo-canh-bao.md`.
- **Thesis:** §3.5. Mục 6.2 phải có hai điểm yếu nêu trên. Hình 7 (vòng vận hành, PR #60) mà chèn vào 3.5.3 thì phải bỏ bớt câu ở đoạn tự xử lý sự cố.
## 2026-11-24 – Luận văn: cắt mục 3.6 về 2 trang

- **Task:** TR8 · **Environment:** none
- **Done:**
  1. Merge `origin/main` vào nhánh `docs/tr8-thesis-3-6-base` để có ngân sách trang (PR #65, D94).
  2. Viết lại 3.6 theo thứ tự cắt của `quy-tac-viet.md` §3.1: bảy bảng còn một (Bảng 3.6a, ba kịch bản tải); ĐG, VH, LT, chỉ số, quy tắc so sánh, điều kiện hợp lệ và cách chấm cảnh báo viết thành văn xuôi ngắn, mỗi đoạn kèm comment nguồn.
  3. Ghi vào dòng 3.6 của `nguon-tu-lieu.md` từng ý đã chuyển ra và nơi chứa nó (`docs/chi-tiet/`, mục 4.7, chương 5, Phụ lục E).
  4. Chạy `/code-review high` trên diff, sửa 10/10 lỗi được báo, rồi cắt lại cho vừa 2 trang.
- **Decision:**
  - Bỏ bảng VH1–VH6 và LT1–LT8 khỏi thân bài: 3.6 chỉ cần nêu có phép thử nào và đạt khi nào; cách làm và kết quả từng VH, LT thuộc 5.2–5.5. Bảng ma trận 17 lượt, bảng chỉ số, bảng điều kiện hợp lệ cũng bỏ, vì dưới 3 cột thông tin riêng hoặc trùng văn xuôi (§6).
  - Không định nghĩa lại C, B\* và threshold 0,8 B\*, vì mục 3.3 đã định nghĩa; 3.6 chỉ dẫn chéo.
  - Giữ trong thân bài các định nghĩa mà 3.1 trỏ tới: KB, ĐG, VH, LT, page giả, pha ổn định của KB1 (D95).
  - Theo review: nêu rõ seed theo kịch bản và lần lặp, mọi lượt ĐG2 ở mức ấm, "đỉnh 3,0 C cần vừa đủ 4 replica" là ước tính của 3.3, thời gian tới cảnh báo chấm ở S1 × KB3, page giả chỉ chấm ở A2 × KB1 và A2 × KB3.
- **Results:** đo bằng dàn trang thử (khuôn A 13 pt, khuôn B 14 pt; đạt khi khuôn B ≤ 2 trang):

  | Bản | Chữ văn xuôi | Bảng | Khuôn A | Khuôn B |
  |---|---|---|---|---|
  | Base 23/11 | 2.305 | 7 | 10 | 13 |
  | Lần cắt 1 | khoảng 1.580 | 3 | 3,04 | 4,05 |
  | Lần cắt 2 | khoảng 900 | 2 | 2,00 | 2,76 |
  | Lần cắt 3 | khoảng 720 | 1 | 1,65 | 2,14 |
  | Sau review, cắt lại | 670 | 1 | 1,63 | 1,99 |

  `kiem_van.py`: 0 điểm cần xem (37 câu, trung bình 18,1 chữ/câu). `lychee --offline --include-fragments 'docs/luan-van/*.md'`: 0 lỗi.
- **Incidents:** sau khi sửa theo review, bản tăng lên 2,14 trang và một đoạn có 5 mã (quá 4, §4). Đã bỏ mã L2 ở câu ĐG2 (thay bằng "mức ấm, mục 3.4"), bỏ câu "hai lượt chỉ khác nhau ở cấu hình" (câu seed ở 3.6.1 đã nói), và rút các dòng cuối đoạn chỉ có 1–2 chữ.
- **Deviations:** ý "LT chạy được ở máy nhà và simulator" và ca đối chứng VH2 không còn trong 3.6; đã ghi nơi chứa ở `nguon-tu-lieu.md`. Chương 5.5 phải nhắc ca đối chứng khi trình bày VH2.
- **Links:** PR #64; `docs/luan-van/03-06-thiet-ke-danh-gia.md`, `docs/luan-van/nguon-tu-lieu.md`.
- **Thesis:** 3.6; dẫn chéo từ 3.1, 3.3; các ý chuyển ra đi vào 4.7, 5.1–5.5, Phụ lục E.

## 2026-11-25 – Luận văn: gom chương 3 vào một nhánh, đổi đề mục theo dàn ý mới (bước 1)

- **Task:** TR8 · **Environment:** none
- **Done:** tạo nhánh `docs/tr8-thesis-ch3` từ `origin/main`; merge 6 nhánh mục (#63 3.1, #67 3.2, #66 3.3, #68 3.4, #62 3.5, #64 3.6), giữ lịch sử và các mục nhật ký 23–24/11 vốn chỉ nằm trên các nhánh đó. Đổi đề mục theo Kế hoạch §11.1: 3.2.3 "Bảo vệ tối thiểu" thành đoạn cuối của 3.2.1 "Thành phần và ba luồng"; 3.4.3 gộp vào 3.4.2 "Tắt pod và cập nhật không rớt request"; 3.5.2 gộp vào 3.5.1 "SLI và cảnh báo theo burn rate", 3.5.3 thành 3.5.2 "Định tuyến cảnh báo, runbook và người trực"; 3.6.2, 3.6.3 đổi tên. Khôi phục phần lõi đã cắt ngày 24/11 ở 3.3 (ba câu hỏi thiết kế, bảng tín hiệu không chọn, điểm yếu của tín hiệu A2, lý do hệ số 0,8, dòng max = N, lý do timeout 1 s, dẫn chéo `KedaScalerErrors`, lấy từ bản base 28be408) và 3.4 (bảng L0/L2 ba dòng, lý do không đo L1, không dùng `--enforce-eager`, startup probe 10 phút, không dùng sync window). Thêm `03-00-yeu-cau-thiet-ke.md`: tiêu đề chương và đoạn mở nêu các lựa chọn thiết kế chính (quy tắc viết §2).
- **Decision:** D118. Gom bằng merge thay vì chép file, để giữ nhật ký của từng PR mục. Xung đột Kế hoạch §11.1 lấy bản main (dàn ý mới); `tai-lieu.bib` giữ cả hai mục; `nguon-tu-lieu.md` giữ dòng mới của cả hai phía, dòng 4.6.x theo đề mục của main. Khôi phục có chọn lọc: chỉ lý do thiết kế và phương án bỏ, không khôi phục phần đã có chỗ ở chương 4, 5 hay phụ lục. Câu "triển khai qua Git chỉ được kiểm ở cluster nhà" ở 3.2 chưa sửa, chờ PR #75 và #78 được duyệt (ghi comment trong file).
- **Results:** văn xuôi theo `kiem_van.py`: 03-00 153 chữ, 3.2 522, 3.3 998, 3.4 668, 3.5 681, 3.6 670; 0 điểm cần xem ở cả 6 file đã sửa. `lychee --offline --include-fragments 'docs/luan-van/*.md'`: 0 lỗi. Chưa đo trang khuôn T.
- **Incidents:** khi chèn comment "Chờ PR #75" vào giữa đoạn cuối 3.2.2, phần sau comment bị tách khỏi đoạn; đã đưa comment xuống sau đoạn.
- **Deviations:** 3.2 (522 chữ) và 3.4 (668 chữ) dưới mức 1.000 chữ mà quy tắc viết §2 đặt cho việc chia cấp 3; vẫn giữ hai tiểu mục theo dàn ý §11.1, xem lại khi đo khuôn T ở bước 2.
- **Links:** nhánh `docs/tr8-thesis-ch3` (chưa PR); `docs/luan-van/03-00-yeu-cau-thiet-ke.md`, `03-02`…`03-06`.
- **Thesis:** chương 3. Còn lại cho bước 2: khôi phục phần lõi 3.1, 3.5, 3.6; kết chương; đánh lại số bảng; đo khuôn T (13–15 tr); `/code-review high`; PR; đóng #62–#64, #66–#68.

## 2026-11-25 – Luận văn: khôi phục phần lõi của 3.1, 3.5, 3.6 (chương 3, bước 1b)

- **Task:** TR8 · **Environment:** none
- **Done:** trên nhánh `docs/tr8-thesis-ch3`, so từng mục với bản base trước lượt cắt 24/11 (3.1: `fbe651b`, 3.5: `d14e6e5`, 3.6: `6e63ad5`) và đưa lại phần lý do. 3.1: ba yêu cầu kéo nhau được nêu tên; sáu việc nền tảng phải làm thành danh sách và cột "Việc" của Bảng 3.1; lý do TPOT 100 ms; lý do giữ một ngưỡng TTFT 2,5 s cho cả cảnh báo và nghiệm thu; lý do không áp 95% cho KB2 và chỉ tính pha duy trì của KB3. 3.5: burn rate 14,4 của SRE Workbook và lý do rút cửa sổ; mốc 20% trùng định nghĩa page giả nhưng khác nguồn; định nghĩa page và ticket; cột "Lý do của điều kiện" của Bảng 3.5a; định tuyến của Alertmanager (page nhắc mỗi giờ, warning/info của chart không gửi); khung runbook; chỉ sửa cấu hình qua Git. 3.6: hai câu hỏi của đánh giá; lý do số đo hiệu năng chỉ lấy từ VM thuê; lý do không dùng closed-loop; độ dài prompt; lý do đỉnh 0,75 × N × C; lý do thời lượng từng pha; hai lượt chỉ khác cấu hình; cách báo chỉ số đề cương; GPU-giờ không thổi phồng mức tiết kiệm; lý do chấm cảnh báo độc lập; lý do LT chạy ở máy nhà và simulator. Cập nhật dòng 3.1, 3.5, 3.6 của `nguon-tu-lieu.md`.
- **Decision:** D119. Không khôi phục bảng truy vết 5 cột và bảng mã định danh của bản base: bảng truy vết đầy đủ đã ở Kế hoạch §11.1, danh mục mã ở phần đầu quyển; cột "Việc" giữ phần truy vết mà dàn ý §11.1 nêu. Không khôi phục các phần đã ghi nơi chứa ở chương 4, 5 và phụ lục (ma trận 17 lượt, bảng chỉ số, bảng VH, bảng LT, chi tiết ĐG3, ví dụ runbook, Watchdog).
- **Results:** văn xuôi theo `kiem_van.py`: 3.1 tăng từ 314 lên 666 chữ, 3.5 từ 681 lên 942, 3.6 từ 670 lên 1.207; 0 điểm cần xem ở cả ba file. `lychee --offline --include-fragments 'docs/luan-van/*.md'`: 0 lỗi. Chưa đo trang khuôn T.
- **Deviations:** dàn ý §11.1 ghi "bảng mã định danh" ở 3.1; bảng này nằm ở danh mục đầu quyển (D119).
- **Links:** nhánh `docs/tr8-thesis-ch3` (chưa PR); `docs/luan-van/03-01-yeu-cau-chi-tieu.md`, `03-05-giam-sat-slo-canh-bao.md`, `03-06-thiet-ke-danh-gia.md`, `nguon-tu-lieu.md`.
- **Thesis:** chương 3. Còn lại cho bước 2: kết chương, đánh lại số bảng, đo khuôn T (13–15 tr), `/code-review high`, PR, đóng #62–#64, #66–#68.

## 2026-11-25 – Luận văn: kết chương 3, đánh lại số bảng, soát và mở PR chương 3 (bước 2)

- **Task:** TR8 · **Environment:** none
- **Done:** viết mục "Kết chương" (một đoạn) ở cuối `03-06-thiet-ke-danh-gia.md`; đánh lại số hình, bảng theo thứ tự xuất hiện (Hình 3.2a → Hình 3.1; Bảng 3.2a, 3.3a–3.3c, 3.4a, 3.5a, 3.6a → Bảng 3.2–3.8) và sửa các comment "Số tạm"; chạy `/code-review high` trên diff chương 3 so với `origin/main`, sửa cả 10 điểm; mở PR chương 3 và đóng các PR mục #62–#64, #66–#68 với ghi chú superseded.
- **Decision:** D120. "Kết chương" đặt ở cuối file mục cuối (3.6), như nhánh nháp chương 5, thay cho file riêng `03-kc`: không cần thêm dòng vào bảng tổ chức file của README; `gop.py` nhận cả hai cách.
- **Results:** văn xuôi theo `kiem_van.py`: 03-00 155 chữ, 3.1 666, 3.2 559, 3.3 1.002, 3.4 668, 3.5 949, 3.6 kèm kết chương 1.474; tổng 5.473 chữ, 8 bảng, 1 hình. Ước tính theo quy ước D103 (khoảng 500 chữ/tr, bảng 0,5–0,8 tr): khoảng 15–18 tr, trên định hướng 13–15 tr; chưa đo khuôn T bằng Word. `kiem_van.py`: 0 điểm cần xem ở cả 7 file. `lychee --offline --include-fragments docs/luan-van/`: 0 lỗi.
- **Incidents:** lệnh đo khuôn T (`powershell.exe -ExecutionPolicy Bypass -File .work/tools/gop_luan_van/do_trang_word_T.ps1`) bị auto mode từ chối trong lượt tự chạy; không thử cách khác, để Trình chạy tay.
  Review phát hiện các lỗi nội dung đã có từ bước 1, 1b, gồm: đoạn mở chương ghi "lên tối đa khi mất tín hiệu" trong khi 3.3.3 nói mất metric nguồn làm số replica về 1; 3.6 nhắc cold start "hơn 6 phút" mà không nói đó là L2 đo trên máy khác (2 × RTX 5060 Ti, 08/11), mâu thuẫn với mức 0,5–1,5 phút dùng để đặt N2a ở 3.1; dẫn sai mục 1.1, 1.2; câu 12 phút của cửa sổ 1 giờ đứng trước ngưỡng burn rate 4 mà nó dựa vào; mục tiêu 99% không 5xx xuất hiện ở Bảng 3.7 mà chưa được định nghĩa; "máy cloud" (từ cấm ở quy tắc viết §4); hình 3.1 và Bảng 3.8 đứng ngay trước tiêu đề.
- **Deviations:** chương 3 có thể vượt định hướng 13–15 tr (ước tính); chưa cắt, chờ số đo khuôn T.
- **Links:** nhánh `docs/tr8-thesis-ch3`; PR chương 3; các PR mục đã đóng #62, #63, #64, #66, #67, #68.
- **Thesis:** chương 3 đủ các mục theo dàn ý §11.1. Còn lại: đo khuôn T; vẽ lại Hình 3.1 (Hình 2 cũ) trước khi chèn; sửa câu Argo CD ở 3.2.2 khi #75, #78 merge.

## 2026-11-25 – Ghi máy V2 thật (4 × RTX 4060 Ti) vào tài liệu thiết kế

- **Task:** TR8 (phần Q2 của Quang, D115 mục 1) · **Environment:** none
- **Done:**
  1. Grep 37 dòng nhắc A4000 trong `docs/chi-tiet/`, đọc từng chỗ, chia hai nhóm: chỗ nói phiên V0+V1 ngày 08/11 hoặc kế hoạch, lựa chọn của ADR-006 C2 (giữ nguyên), và chỗ nói phiên V2 đã chạy (sửa).
  2. Sửa 30 chỗ ở 6 file: Thông số §2, §9.1, §10.2 (thêm đoạn "Máy V2 thực tế"), §11; Bài toán §1.2, §1.3, G2 (§12.2), hạn chế 1 (§12.3); Kiến thức nền §1.4 (ngân sách VRAM), §1.5 (bảng băng thông, đoạn decode 3B); Kiến trúc A1′; Môi trường tóm tắt, §1, §3.1 (thêm dòng RTX 4060 Ti), §6.1 (dòng V2: ngày và máy thật), bảng lớp đánh giá, câu hỏi "vì sao dùng A4000"; Kế hoạch M1 (checklist), §4 phụ thuộc, bảng rủi ro và R2.
- **Decision:**
  - Trình giữ nguyên các câu về A4000 của V0+V1 và về lựa chọn ADR-006 C2, chỉ thêm câu "thực tế V2 chạy trên 4 × RTX 4060 Ti": các số 08/11 (TPOT 17,2 ms, KV-cache 211.936 token, tải model 27 s) đúng là đo trên A4000. ADR-006 không sửa, vì ADR ghi quyết định tại thời điểm đó.
  - Thêm số KV-cache của V2 (211.584–224.336 token, đọc từ log vLLM trong `runs/dg1-v2-4060ti/` và `runs/v2-vm/dg3-v2-4060ti/`) để chứng minh phân bổ VRAM của §1.2 vẫn đúng trên máy V2. Không thêm TPOT ở 1 request cho V2, vì V2 không đo; bước decode tối thiểu 21,4 ms chỉ là tính từ băng thông 288 GB/s.
  - Chi phí V2 ghi "chưa có số": giá 1,5 USD/giờ và ước 14–15 USD là số Quang báo ngày 18/11, chi phí thực đang chờ Quang.
  3. `/code-review high` trên diff: 9 điểm, đã sửa cả 9: câu "băng thông thấp nên C = 3,5" sai với nhật ký (tỉ lệ băng thông thuần dự đoán 2,9 req/s, số đo cao hơn), nay ghi băng thông chỉ giải thích một phần; ngày V2 14–15/11 còn sót ở Kế hoạch (tóm tắt, bảng tuần, §1.1, đường găng) và lịch theo giờ Môi trường §6.2, nay thêm "thực tế 18–19/11"; dòng 4060 Ti ở Môi trường §3.1 để C (req/s) vào cột token/s; câu hỏi "vì sao" trỏ hạn chế về ADR-006 thay vì Bài toán §12.3; tiêu chí GPU ở Thông số §10.2 chưa nhắc máy thật; đoạn DCGM ở Kiến thức nền thiếu 4060 Ti; giá 1,5 USD/giờ ở Môi trường thiếu chú thích "Quang báo theo trang Vast"; số mục sai trong chính mục nhật ký này.
- **Results:** `lychee --offline --include-fragments` trên `docs/chi-tiet/*.md` đạt; trên toàn bộ `docs/` chỉ còn lỗi có sẵn ở `docs/huong-dan/w2.md` (link tới thư mục chưa có trên main, CI loại trừ).
- **Links:** `docs/chi-tiet/00-thong-so.md`, `01-bai-toan-yeu-cau.md`, `02-kien-thuc-nen.md`, `03-kien-truc-autoscaling.md`, `05-moi-truong-danh-gia.md`, `06-ke-hoach-quan-ly.md`; nguồn: nhật ký của Quang tuần 07 (18/11), `docs/nhat-ky/van-hanh.md` (18/11).
- **Thesis:** 5.1 (môi trường đo: máy 4060 Ti thay A4000), 5.7 Hạn chế (C = 3,5 chỉ đúng cho máy V2), 2.x (bảng băng thông GPU).
## 2026-11-24 – VH2 trên kind, bước 1: thêm Argo CD vào simulator

- **Task:** TR8 (F3, VH2 theo D113) · **Environment:** sim
- **Done:**
  1. Thêm `envs/sim/argocd/apps.yaml`: hai Application `serving` (path `envs/sim/serving`) và `autoscaling` (path `envs/sim/autoscaling`), cùng syncPolicy với nhà (automated, prune, selfHeal, retry).
  2. Thêm `make sim-argocd ARGOCD_REV=<nhánh>`: cài Argo CD core `v3.5.4` (server-side apply như role `argocd-bootstrap`), áp AppProject `default` của nhà, áp hai app với `targetRevision` đổi sang `ARGOCD_REV` bằng `sed`, rồi chờ cả hai `Synced Healthy`; thêm `make sim-argocd-down` để gỡ. `ARGOCD_VERSION` ghim trong Makefile, thêm vào `docs/phien-ban.md`.
  3. Thêm mục "VH2 qua Git" vào `envs/sim/README.md`: cách cài, chu kỳ đọc Git, self-heal, runner bị `guard_argocd` chặn, cách gỡ.
  4. Chạy thử trên cụm `llm-sim` với `REV=main`, kiểm self-heal, rồi gỡ đúng theo README.
- **Decision:** Tên app trùng nhà (`serving`, `autoscaling`), để `guard_argocd` của runner và cách tắt auto-sync có cùng ý nghĩa trên kind. Không dựng root App-of-Apps như nhà: VH2 chỉ cần hai app. Nhánh truyền qua `ARGOCD_REV` lúc áp, file trong Git giữ `targetRevision: main`, vì quên biến thì app chỉ theo `main` (an toàn), còn ghi cứng nhánh thử vào Git thì nhánh đó bị xoá là app lỗi.
- **Results:**
  - `make sim-argocd` (nhánh `main`): 142 s tới khi cả hai app `Synced Healthy`, revision `7787de0` (= `origin/main`). Pod simulator giữ nguyên (cùng tên, restarts 0): Argo CD nhận lại tài nguyên `make sim-up` đã tạo, không tạo lại.
  - Log controller: `appResyncPeriod=2m0s, appResyncJitter=1m0s`, tức Argo CD đọc Git mỗi 2–3 phút.
  - Self-heal: patch tay threshold ScaledObject 10 → 11, Argo CD đưa về 10 sau 2 s.
  - Gỡ bằng ba lệnh (nay là `make sim-argocd-down`): 13 s, còn 0 CRD `argoproj.io`; pod simulator và ScaledObject (max 3, threshold 10) giữ nguyên.
  - `/code-review high`: 9 điểm. Đã sửa: (1) runner để ScaledObject tạm dừng thì app `autoscaling` là `Suspended`, vòng chờ không bao giờ thấy `Healthy`: nay nhận `Suspended` và in lệnh gỡ annotation; (2) header gợi ý `make home-eval-begin`, mà target đó mặc định nhắm cluster nhà: bỏ, ghi rõ không dùng; (3) hết hạn thì in condition của app (ví dụ nhánh chưa push); (4, 5) ba lệnh gỡ thành `make sim-argocd-down`, dùng chung `ARGOCD_VERSION`; (6) kiểm dạng tên nhánh trước `sed`; (7) đổi `REV` thành `ARGOCD_REV` để biến `REV` có sẵn trong shell không đổi nhánh; (9) hạn chờ tính bằng `$SECONDS`. Điểm (8), dùng chung AppProject của nhà, giữ nguyên và ghi chú trong Makefile.
  - Chạy lại sau sửa: đặt `paused-replicas=1` rồi `make sim-argocd` → báo "Synced ở main, nhưng ScaledObject vllm-a2 đang tạm dừng" kèm lệnh gỡ; gỡ annotation → `Synced Healthy` trong ≤ 20 s; `make sim-argocd-down` 12 s, còn 0 CRD, pod simulator giữ nguyên; `ARGOCD_REV='a|b'` bị từ chối trước khi cài gì.
  - Kiểm cục bộ: `yamllint -s` đạt; `kubeconform -strict` 2/2 Application hợp lệ (schema CRDs-catalog ở commit ghim của CI); `make -n sim-argocd` thay đúng nhánh; lychee đạt.
- **Incidents:** Việc F6 (cảnh báo thật qua bot Telegram trên kind) dừng ở bước đầu: trong lượt tự chạy, lệnh nạp Secret bot thật từ `.env` vào kind bị chặn. F6 chờ Trình nạp Secret, nên vòng này chuyển sang VH2.
- **Links:** `envs/sim/argocd/apps.yaml`, `Makefile` (`sim-argocd`), `envs/sim/README.md`, `docs/phien-ban.md`.
- **Thesis:** 4.5 (triển khai qua Git); 5.5.1 (VH2 qua Git trên kind, số đo ở bước 2).

## 2026-11-25 – VH2 trên kind, bước 2: cập nhật và `git revert` qua Argo CD dưới tải

- **Task:** TR8 (F3, N4, VH2 theo D113 / ADR-007 D2) · **Environment:** sim
- **Done:**
  1. Thêm kịch bản `vh2-git` vào `experiments/ops/vh.py`, theo đúng Vận hành §5.3, §5.4. Kịch bản push 4 commit lên nhánh thử `feat/tr8-vh2-git-target` từ một git worktree riêng: nâng `minReplicaCount` lên 2; đổi `--time-to-first-token` của simulator 200 → 300 ms; `git revert` commit đổi tham số; `git revert` commit nâng min. Mỗi bước, script chờ Argo CD tự sync đúng commit đó (`operationState.syncResult.revision`), không bấm refresh. Tải do loadgen tạo trong cluster và gọi Service, như các kịch bản VH khác.
  2. Script kiểm trước khi chạy: không chạy trên `main`; worktree sạch và trùng `origin/<nhánh>`; hai Application đọc đúng repo và nhánh, auto-sync bật; ScaledObject không tạm dừng. Một bước lỗi thì revert các commit đã push. Chấm đạt khi có 0 lỗi, bắt đầu từ 1 replica, Argo CD sync cả 4 commit, thấy tham số mới sau cập nhật và đúng tham số cũ sau rollback, và kịch bản xong khi tải còn chạy.
  3. `make sim-argocd ARGOCD_REV=feat/tr8-vh2-git-target` (33 s tới `Synced Healthy`), chạy 2 lượt, rồi `make sim-argocd-down` (13 s).
  4. Ghi cách chạy và số đo vào `envs/sim/README.md`.
- **Decision:** D117. Đo bằng kịch bản trong runner thay vì làm tay theo runbook, để có timeline, `requests.csv` và lặp lại được. Không dùng `hey` qua port-forward, vì port-forward dồn mọi request vào một pod (đo 04/11) nên không thấy được rolling update. Tham số đổi là TTFT giả của simulator, vì nó hiện ra trên TTFT đo được: đó là bằng chứng bản mới thật sự chạy, rồi bản cũ thật sự quay lại. Từ WSL, script gọi `git.exe` của Windows để push bằng credential sẵn có. Bảng nghiệm thu F3 (Môi trường §16) để PR sau, vì PR #75 đang sửa đúng dòng đó.
- **Results:**
  - Lượt chính `runs/ops-vh2-git-20261124-171557` (0,3 req/s, 2.100 s): **đạt**, 615 request, **0 lỗi**, trước đó 1 replica.

    | Bước | Push → Argo CD sync xong | Cả bước |
    |---|---|---|
    | Nâng min lên 2 | 138 s | 146 s (2 pod Ready) |
    | Đổi TTFT 200 → 300 ms | 247 s | 261 s (rollout xong) |
    | `git revert` đổi TTFT | 231 s | 244 s (rollout xong) |
    | `git revert` nâng min | 242 s | 244 s |

    TTFT p50 của request gửi trong từng khoảng: 206 ms trước cập nhật, 306 ms từ lúc rollout tới lúc sync rollback, 206 ms sau rollback (397 request). A2 hạ 2 → 1 replica vài phút sau khi Argo CD sync commit cuối (cửa sổ scale-down 300 s), lúc tải vẫn chạy, không có lỗi.
  - Lượt thử `runs/ops-vh2-git-20261124-164415` (0,5 req/s, 1.800 s): 886 request, 0 lỗi, TTFT 207 → 305 → 206 ms. Script chấm **không đạt**, và chấm đúng: A2 đã tự lên 2 replica lúc 16:45:54, trước commit nâng min lúc 16:46:18, nên lượt này không phải ca 1 replica. Push → sync: 114 / 367 / 115 / 315 s.
  - Push → sync có thể tới khoảng 6 phút. Argo CD so lại với Git mỗi 2–3 phút (`appResyncPeriod=2m0s`, jitter 1 phút), còn repo-server giữ commit của nhánh trong cache 3 phút (`argocd-repo-server --help`: `--revision-cache-expiration` mặc định `3m0s`). Log controller của bước 367 s: lần so lúc 16:50:20 (2 phút sau push) vẫn `Synced` với commit cũ; tới lần so lúc 16:54:24 mới `Initiated automated sync`.
  - Nhánh thử còn trên origin làm bằng chứng: `ae7f31f`, `a100eee`, `b018e12`, `310e172` (lượt thử), rồi `f3e0a44`, `0dd739a`, `34651bf`, `9bc66d0` (lượt chính).
  - Kiểm cục bộ: `ruff check`, `ruff format --check` đạt; `pytest experiments` 168 đạt, 4 hỏng ở `test_backup_notify.py`. 4 test này hỏng cả trước thay đổi, vì `rclone` giả là shell script, không chạy được trên Windows; CI Linux xanh. `/code-review high`: 9 điểm, đã sửa 8 điểm trong code: revert khi lỗi giữa chừng; kiểm worktree trùng origin; bắt lỗi không có lệnh git; chấm không đạt khi kịch bản xong sau lúc tải ngừng; nhận cả annotation `paused`; so đúng giá trị TTFT cũ; kiểm repoURL; ghi rõ `sync_s` tính từ lúc push xong. Điểm thứ 9 (thiếu nhật ký) xử lý bằng mục này. Lượt chính chạy bằng code đã sửa, lượt thử chạy bằng code trước khi sửa.
- **Deviations:** Kịch bản chỉ đổi tham số của simulator; không có GPU, cold start, cache model. Rollout 2 pod xong 10–11 s sau sync, trong khi vLLM thật mất vài phút (ADR-007 §4). Môi trường §13 ghi VH2 "qua PR"; ở đây commit được push thẳng lên nhánh thử, coi như PR đã merge, và không qua CI.
- **Links:** `experiments/ops/vh.py` (`vh2_git`, `GitTarget`, `argocd_problem`), `experiments/tests/test_ops_vh.py`, `envs/sim/README.md`; nhánh `feat/tr8-vh2-git-target`; PR xếp chồng trên #77.
- **Thesis:** 5.5.1 (VH2 qua Git: bảng 4 bước, TTFT 206 → 306 → 206 ms, 0 lỗi); 4.5 (triển khai qua Git: độ trễ push → sync gồm chu kỳ so và cache của repo-server); 5.7 (simulator không có cold start thật; commit không qua PR, CI). Hình C6 có thể vẽ từ `timeline.json` + `requests.csv` của lượt chính.
## 2026-11-24 – N8: dựng lại kind + simulator từ đầu theo README

- **Task:** TR8 (N8) · **Environment:** sim
- **Done:**
  1. `make sim-down` xoá cụm `llm-sim` cũ, rồi làm đúng theo `envs/sim/README.md`: `make sim-up`, kiểm trạng thái, `make sim-test`. Bấm giờ từng bước bằng dấu giờ trên từng dòng output.
  2. Dựng với hai biến Telegram giả trong môi trường, để Alertmanager không gửi tin thật trong lúc thử (`.env` đã có bot thật từ 24/11).
  3. Sửa README ở những chỗ người mới phải tìm ở tài liệu khác: thêm mục "Cần có" (máy, công cụ, mạng, Telegram tuỳ chọn, cách dựng mà không gửi tin), phần kiểm tra sau `make sim-up` (kết quả mong đợi, mở Grafana), mục "Trên Windows (WSL2)", và thời gian `make sim-up` theo số đo.
- **Results:**
  - `make sim-down`: 9,5 s. `make sim-up`: 343 s, mã thoát 0. Theo bước: tạo cluster kind 30 s; khai báo repo Helm 5 s; kube-prometheus-stack 206 s; rule và dashboard dưới 1 s; KEDA 81 s; simulator rollout 16 s; ScaledObject dưới 1 s.
  - Sau `make sim-up`: 1 pod `vllm` 1/1 Running, `vllm-a2` READY=True, HPA `0/10 (avg)`; không pod nào ngoài Running/Completed. Ba node dùng 2,9 GB RAM lúc nghỉ và 3,1 GB khi bơm C=25 với 3 replica (`docker stats`).
  - `make sim-test`: 1.128 s, T1–T5 đều đạt. T2 desired=3 sau 3 s (tiêu chí ≤ 15 s); T3 giữ 3 replica 304 s rồi về 2, về 1 sau thêm 61 s; T4 fallback sau 18 s (tiêu chí ≤ 30 s); T5 giữ 1 replica khi A2 lên 25. Log: `runs/sim/20261124-222049-t1-t5.log`.
  - Tổng từ `make sim-down` đến khi T1–T5 đạt: 1.481 s (khoảng 25 phút), dưới ngưỡng 1 giờ của N8.
  - Log Alertmanager không có lần gửi nào trong lúc T1–T5, nên F6 phải tự kích một cảnh báo.
  - `/code-review high`: 7 điểm, đã sửa cả 7 (README thiếu `jq`, `curl`; W1 không cài `uv`; khối Grafana đặt port-forward trước lệnh lấy mật khẩu; "~6 phút" chưa nói là đã có node image; RAM chưa đo lúc có tải; chưa nói Secret giả ở lại cluster; ô T2 của van-hanh.md dễ đọc nhầm).
- **Deviations:** chưa đúng "người thứ hai" như N8 viết: agent chạy trên máy của Trình, công cụ đã cài sẵn, và node image của kind (1,3 GB) đã có trong cache Docker. Image của chart và simulator thì tải lại. Thời gian cài công cụ theo W1 §4.2 chưa đo.
- **Links:** `envs/sim/README.md`; `docs/nhat-ky/van-hanh.md`.
- **Thesis:** §4 (tái lập môi trường), §5 bảng nghiệm thu N8.
## 2026-11-24 – Nghiệm thu: soát các việc Must còn phụ thuộc cluster nhà

- **Task:** TR8, chung · **Environment:** none
- **Done:** Đối chiếu danh sách Must ([Thông số §5](../../../chi-tiet/00-thong-so.md#5-mức-độ-thành-công)) với bảng nghiệm thu ngày 21/11 ([Môi trường §16](../../../chi-tiet/05-moi-truong-danh-gia.md)) và dữ liệu `runs/ops-vh2a-*`, nhật ký vận hành 19/11. Ước lượng: 10/16 mục Must đạt, 4 đạt một phần (F3, F5, F6, N4), 2 chưa chạy (VH1, VH2 ở nhà). Với từng việc còn lại, xét việc đó có thật sự cần cluster nhà hay không.
- **Decision:**
  - VH1 không chạy lại ở nhà. Bằng chứng scale-down an toàn lấy từ pha `drop` của 3 lượt A2 × KB2 trên V2 (N = 4, 0 lỗi): cùng cơ chế preStop và graceful shutdown, đo trên nhiều GPU hơn KB2-mini ở nhà.
  - VH2 chạy trên kind + simulator có cài Argo CD. Phần F3 còn thiếu chỉ là vòng Git → Argo CD sync → `git revert`, không phụ thuộc GPU. Các ràng buộc GPU của VH2 (ca 1 replica, `maxSurge: 0`, ca kẹt Pending) đã đo trên V2 với 0 lỗi. Application trên kind theo dõi một nhánh riêng, nên không đổi `main` hay cluster nhà.
  - F6 (tin cảnh báo tới Telegram thật) và N8 (người thứ hai dựng lại theo README) làm trên kind + simulator; định nghĩa VH5 ở Môi trường §13 đã cho phép cách này.
  - Ảnh chụp dashboard trên GPU thật (F5) làm trên cluster nhà; nếu không có trước 28/11 thì dùng ảnh trên simulator cộng Hình C3 (GPU từ dữ liệu V2) và ghi vào Hạn chế. Tổng chi phí thuê lấy từ trang thanh toán của Vast.
  - Không sửa `vh3_kill` (thiếu bước bảo đảm ≥ 2 pod), vì dữ liệu đã đóng băng 22/11; nêu ở mục 5.5 và 5.7.
- **Deviations:** Must ở Thông số §5 ghi "VH1, VH2 ở nhà"; nay VH1 dùng kết quả trên GPU thuê và VH2 chạy trên kind. Sửa Thông số §5 và Môi trường §13 trong PR này.
- **Thesis:** 5.5 (VH1, VH2), 5.6 (bảng nghiệm thu), 5.7 (Hạn chế).

## 2026-11-24 – Nghiệm thu: ghi phạm vi Must mới vào ADR-007 và tài liệu thiết kế

- **Task:** TR8, chung · **Environment:** none
- **Done:** Viết [ADR-007](../../../adr/007-doi-vh1-vh2-f6-n8-khoi-cluster-nha.md) cho các quyết định ở mục trước (VH1, VH2, F6, N8 không còn chờ cluster nhà). Sửa theo ADR: Thông số §3 (cách kiểm chứng F3, F6), §5 (dòng Must và Should); Môi trường §13 (cột "Ở đâu" của VH1, VH2, VH6) và ghi chú của N4, N8, F3, F6 trong bảng nghiệm thu §16; ghi chú ngày 24/11 ở mốc M2, mục học chéo và rủi ro R7 của Kế hoạch; bảng ADR.
- **Decision:** Ghi thành ADR mới thay vì thêm mục vào ADR-006, vì README của `docs/adr/` quy định không sửa nội dung ADR cũ. Bảng nghiệm thu chỉ đổi cột ghi chú; cột "Đạt?" giữ nguyên cho tới khi có kết quả trên kind.
- **Results:** lychee offline: không lỗi ngoài các đường dẫn cũ mà CI cũng bỏ qua. `/code-review high`: 10 điểm, đã sửa 9. (1) Ca (c) của VH2 chưa có bằng chứng `LLMPodPending` kêu: `runs/v2-vm/ops-vh2c-20261118-174729/summary.json` chỉ ghi `rollout_stuck: true`, 0 lỗi trên 2.077 request, còn quy tắc có `for: 10m` trong khi lượt chỉ chờ kẹt khoảng 300 s; ADR-007 ghi rõ. (2) Ca (c) không thuộc mức nào, nay xếp vào Should. (3) Trình đã dùng cụm simulator từ 07/11, nên N8 không phải lần dựng của người chưa từng thấy repo; ghi vào Hệ quả và Hạn chế. Các điểm còn lại là câu chữ và danh sách mục bị thay thế. Không sửa mốc M2 (01/11, đã qua), chỉ thêm ghi chú ngày 24/11. Mục trước xếp N4 vào "đạt một phần", còn bảng Môi trường §16 ghi Đạt; theo ADR-007, N4 dùng số đo V2 nên lấy mức Đạt của bảng.
- **Deviations:** Must ở Thông số §5 trước đây ghi "VH1, VH2 ở nhà".
- **Links:** `docs/adr/007-doi-vh1-vh2-f6-n8-khoi-cluster-nha.md`, `docs/chi-tiet/00-thong-so.md`, `docs/chi-tiet/05-moi-truong-danh-gia.md`, `docs/chi-tiet/06-ke-hoach-quan-ly.md`.
- **Thesis:** 5.5 (VH1, VH2), 5.6 (bảng nghiệm thu), 5.7 (Hạn chế: chưa có vòng Git trọn vẹn trên GPU thật).
## 2026-11-24 – Luận văn: soát cách trình bày theo luận văn ngoài cùng đề tài

- **Task:** TR8 · **Environment:** none
- **Done:** Trình đề nghị tìm đồ án được đánh giá cao, cùng chủ đề, để học cách trình bày. Tìm 18 lượt trên web, cả tiếng Anh và tiếng Việt. Tải ba luận văn thạc sĩ công khai, đọc tóm tắt, chương mở đầu, chương đánh giá và kết luận: Henschel (Aalto 2021, autoscaling trên Kubernetes theo hiệu năng và chi phí), Mitra (ĐH Groningen 2021, scale GPU inference theo GPU utilization so với in-flight request), Lim (Aalto 2025, LLM inference qua RabbitMQ và KEDA). Đối chiếu với `docs/luan-van/quy-tac-viet.md` và bản nháp chương 3, 5.
- **Decision:**
  - Chỉ nhận dấu hiệu chất lượng kiểm được (giải thưởng, điểm công khai), vì điểm luận văn gần như không được công bố. Bài duy nhất thoả là van der Wiel (VU Amsterdam 2022, HPA và năng lượng trên Kubernetes), giải nhất VERSEN Best MSc Thesis in Software Engineering 2023. Ba bài đã đọc được chọn vì đề tài gần, không có bằng chứng về điểm.
  - Quy tắc văn phong hiện có đã chặt hơn cả ba bài: cả ba viết kết luận không kèm số, một bài dùng nhiều cụm sáo ở mở bài. Nhóm nhận năm điểm trình bày: đưa hình đánh đổi GPU-giờ và SLO attainment (C4) trở lại thân bài 5.3; đoạn mở chương 3–5 nêu luôn câu trả lời; chỉ số tự định nghĩa kèm một ví dụ số; khuyến nghị viết theo điều kiện, lựa chọn và căn cứ; hạn chế nêu kết luận bị ảnh hưởng và hướng lệch. Thêm một điểm: kết luận chương 6 kèm số.
  - Không lấy khung câu hỏi nghiên cứu (Q1–Q3) của Mitra. Bố cục giữ yêu cầu F/N, bảng nghiệm thu và ba thông điệp TĐ1–TĐ3.
  - Để sau M4, không bắt buộc: tính chỉ số elasticity của SPEC Research Group (θU, θO, τU, τO; Herbst và cộng sự, 2016) từ dữ liệu V2 đã có.
- **Incidents:** bản PDF của van der Wiel trên `research.vu.nl` trả về trang kiểm tra của Cloudflare khi tải bằng `curl`, và lỗi 403 khi tải bằng công cụ fetch; chưa đọc được. Không tìm thấy đồ án tiếng Việt cùng chủ đề nào có công bố điểm hay giải.
- **Links:** [Henschel](https://aaltodoc.aalto.fi/items/6d0f685e-be6f-4bd4-80ea-e2b678651261) · [Mitra](https://fse.studenttheses.ub.rug.nl/26121) · [Lim](https://aaltodoc.aalto.fi/items/bd6736dd-0acb-47ec-b825-2d20db21cb35) · [van der Wiel](https://research.vu.nl/en/publications/the-impact-of-scalability-on-energy-consumption-in-the-cloud/) · [tin giải VERSEN](https://vu.nl/en/news/2023/r-van-der-wiel-receives-the-best-master-thesis-award-in-software-engineering).
- **Thesis:** quy tắc viết §2, §5; mục 3.6 (ví dụ số cho chỉ số), 5.3 (Hình C4), 5.6 (khuyến nghị), 5.7 và 6.2 (hạn chế), chương 6.

## 2026-11-24 – Luận văn: quy tắc viết theo luận văn ngoài, bỏ trần cứng câu và đoạn

- **Task:** TR8 · **Environment:** none
- **Done:**
  - Sửa `docs/luan-van/quy-tac-viet.md` theo mục trên. §2: đoạn mở chương 3–5 nêu luôn câu trả lời, chương 5 kèm số chính; dòng chương 6 đòi mỗi kết luận kèm một số, điều kiện đo và dẫn chéo tới chương 5. §5: chỉ số tự định nghĩa kèm một ví dụ tính (ví dụ 2 GPU replica trong 30 phút là 1,00 GPU-giờ); khuyến nghị theo khuôn điều kiện, lựa chọn, căn cứ; mỗi hạn chế nêu kết luận bị ảnh hưởng và hướng lệch, không biết thì ghi "chưa đo, không suy ra được chiều lệch".
  - Đo 14 bản nháp (3.1–3.6, 4.3, 5.1–5.7, lấy từ các nhánh `docs/tr8-thesis-*`) và so với đồ án mẫu tiếng Việt của khoa (trang 12–48). Phép đo dùng script cục bộ của Trình, chưa đưa vào repo; số dưới chỉ để chẩn đoán, không dùng làm số liệu của luận văn. Văn của nhóm đều hơn: hệ số biến thiên độ dài câu 0,34 so với 0,51; 69,5% số câu dài 15–30 chữ, so với 34,0%; 43/106 đoạn dài đúng 3 câu; ", nên" xuất hiện 12,7 lần trên 100 câu, so với 1,3. Từ đó sửa §3: §3.2 bỏ trần 35 chữ mỗi câu, bỏ mục tiêu trung bình 18–25 chữ và bỏ khoảng 3–7 câu mỗi đoạn, thay bằng tiêu chí "đọc một lần hiểu ngay"; đoạn 1–2 câu được dùng khi mở mục, dẫn vào danh sách, chuyển ý hoặc nhấn một kết luận. §3.1 miễn phần nhắc lại có chủ đích (Mở đầu, mục 1.3, mở chương, Kết chương, chương 6). §3.4 thêm dấu hiệu "lặp một kiểu nối câu". Việc này cũng gỡ mâu thuẫn cũ giữa §2 (mở mục 1–2 câu) và §3.2 (đoạn 3–7 câu).
  - Nhánh của PR #61 (`analysis/kiem_van.py`, có mục nhật ký riêng trên nhánh đó): bỏ hai luật "câu > 35 chữ" và "đoạn ngoài 3–7 câu". Thêm bốn luật gợi ý đọc lại, in ở phần riêng và không tính vào mã thoát: câu > 45 chữ, đoạn > 8 câu, 3 đoạn ≤ 2 câu liền nhau (chuỗi ngắt ở tiêu đề, bảng và danh sách), ", nên" hơn một lần trong đoạn. §10 của quy tắc viết trên nhánh đó ghi phần gợi ý không cần về 0.
- **Decision:** độ dài câu và đoạn chỉ là gợi ý, vì khi luật trả mã thoát 1 thì người viết sửa cho về 0, và văn bị dài đều nhau. Nhóm không đặt chỉ tiêu mới cho độ biến thiên; số đo ở trên chỉ dùng để chẩn đoán. Phương án không chọn: giữ nguyên ngưỡng, vì văn đều dễ bị đọc như văn do máy sinh; bỏ hết luật về độ dài, vì như vậy mất tín hiệu ở câu quá dài. Các bản nháp không viết lại hàng loạt, mà sửa ", nên", gộp hoặc tách đoạn khi làm PR của từng chương.
- **Results:** `pytest analysis` 212 passed (Python 3.15); test `kiem_van` 61 passed (Python 3.11); `ruff check`, `ruff format --check` đạt. Chạy trên nháp 5.7: 0 điểm, 1 gợi ý (đoạn đầu có 3 lần ", nên"), mã thoát 0.
- **Deviations:** chưa đọc được luận văn của van der Wiel (Cloudflare chặn); quy tắc chỉ dựa trên ba bài đã đọc. Điểm "Hình C4 trở lại 5.3" của mục trên chưa làm ở PR này: sẽ sửa dàn ý (Kế hoạch §11.1) và 5.3 trong PR chương 5.
- **Links:** `docs/luan-van/quy-tac-viet.md` §2, §3.1, §3.2, §3.4, §5; PR #61 (`analysis/kiem_van.py`, `analysis/tests/test_kiem_van.py`).
- **Thesis:** áp dụng cho mọi chương khi làm PR chương; mục 3.6, 5.6, 5.7, 6.2.

## 2026-11-27 – Merge PR #74–#78 (quy tắc viết, ADR-007, README simulator, `sim-argocd`, VH2 qua Git)

- **Task:** TR8 · **Environment:** none
- **Done:** lượt tự chạy có cho merge, gỡ hàng đợi PR theo thứ tự phụ thuộc. Mỗi PR kiểm đủ 5 điều kiện merge: CI 6/6 xanh, đã chạy `/code-review high` lúc mở PR, `MERGEABLE`, không có review hay bình luận, không đụng `envs/home/argocd/apps` (thư mục root-app ở nhà theo dõi), base `main`. Merge commit, xoá nhánh head. #78 được đổi base từ `feat/tr8-vh2-sim-argocd` về `main` trước khi merge #77.
- **Results:** #74 `46c17bb`, #75 `2ec55f3`, #76 `2f500f7`, #77 `97213e6`, #78 `5e3c621`. #75, #76, #78 chỉ xung đột ở nhật ký, `git merge origin/main` tự gộp (merge=union), không trùng tiêu đề mục.
- **Incidents:** #77 xung đột thật với #76 ở `docs/nhat-ky/van-hanh.md` và `envs/sim/README.md` (cả hai thêm mục cùng chỗ). Giữ cả hai phía: van-hanh.md xếp mục N8 trước mục Argo CD theo thứ tự đã làm; README đặt mục "VH2 qua Git" trước "Trên Windows (WSL2)", và sửa chú thích "(mục cuối)" ở bảng đầu thành link tới mục đó (`0fbd6e1`). Lệnh mẫu `vh2-git` trong README ghi `--rate 0.5` trong khi câu dưới khuyên dùng 0,3; sửa thành `--rate 0.3` trên nhánh #78 trước khi merge (`012d269`).
- **Links:** PR #74, #75, #76, #77, #78.

## 2026-11-27 – Merge PR #79–#83 (tên máy V2, chương 3, 4, 5, 2 của luận văn)

- **Task:** TR8 · **Environment:** none
- **Done:** lượt tự chạy có cho merge, vòng 2, gỡ tiếp hàng đợi theo thứ tự ở STATE. Mỗi PR kiểm đủ 5 điều kiện merge: CI 6/6 xanh, đã chạy `/code-review high` lúc mở PR, `MERGEABLE`, không có review hay bình luận, chỉ sửa `docs/` (không đụng manifest Argo CD theo dõi), base `main`. Merge commit, xoá nhánh head.
- **Results:** #79 `7942c77`, #80 `d19b3d0`, #81 `eec0222`, #82 `c0a88ab`, #83 `114df6c`. #80 và #83 chỉ xung đột ở nhật ký, `git merge origin/main` tự gộp (merge=union), không trùng tiêu đề mục.
- **Incidents:** #81 xung đột thật ở bảng bố cục luận văn (Kế hoạch §11.1): nhánh ch. 4 đổi tên 4.3.2 thành "Thử autoscaling và fallback trên simulator trước khi thuê GPU", còn main (#75) sửa 5.5.1 thành "thay cho VH1 ở nhà theo ADR-007". Giữ cả hai (`18996b2`). #82 xung đột ở `tai-lieu.bib`: nhánh ch. 5 thêm hai nguồn băng thông bộ nhớ NVIDIA, main thêm nguồn Argo CD Cluster Bootstrapping; giữ cả ba mục, kiểm không trùng khoá (`29225b6`).
- **Links:** PR #79, #80, #81, #82, #83.

## 2026-11-27 – Merge PR #84–#88 (chương 1, fallback KEDA, CPU pod cloud, chương 6, mở đầu)

- **Task:** TR8 · **Environment:** none
- **Done:** lượt tự chạy có cho merge, vòng 3, gỡ tiếp hàng đợi theo thứ tự ở STATE. Mỗi PR kiểm đủ 5 điều kiện merge: CI 6/6 xanh, đã chạy `/code-review high` lúc mở PR, `MERGEABLE`, không có review hay bình luận, chỉ sửa `docs/` (không đụng manifest Argo CD theo dõi), base `main`. Merge commit, xoá nhánh head.
- **Results:** #84 `98aa53b`, #85 `a05f52f`, #86 `0718d30`, #87 `05699bb`, #88 `6254844`. #85–#88 chỉ xung đột ở nhật ký tuần 08, `git merge origin/main` tự gộp (merge=union), không trùng tiêu đề mục; push nhánh rồi chờ CI xanh lại trước khi merge.
- **Links:** PR #84, #85, #86, #87, #88.

## 2026-11-27 – Merge PR #89–#93 (Hình 2, Hình 8 và 17, ADR-003, phần đầu quyển, phụ lục)

- **Task:** TR8 · **Environment:** none
- **Done:** lượt tự chạy có cho merge, vòng 4, gỡ tiếp hàng đợi theo thứ tự ở STATE. Mỗi PR kiểm đủ 5 điều kiện merge: CI 6/6 xanh, đã chạy `/code-review high` lúc mở PR, `MERGEABLE`, không có review hay bình luận, chỉ sửa `docs/` và `loadgen/scenarios.py` (không đụng manifest Argo CD theo dõi), base `main`. Merge commit, xoá nhánh head.
- **Results:** #89 `eeb1930`, #90 `b1b1b43`, #91 `bc998f5`, #92 `a93fc0f`, #93 `5eaae78`. #90 và #92 chỉ xung đột ở nhật ký tuần 08 (merge=union tự gộp). #91 xung đột bảng `docs/adr/README.md`: giữ trạng thái ADR-006 "C2 bị thay một phần bởi 003" của #91 và thêm dòng ADR-007 từ main. #93 xung đột lệnh pandoc trong `docs/luan-van/README.md` với #92: gộp thành `phan-dau/[0-9]*`, `[0-9]*`, `phu-luc/*` cùng biến `SEP`, giữ cả ghi chú danh mục hình và bảng của #92; chạy thử lệnh gộp ra `.docx` được (chỉ cảnh báo thiếu `rsvg-convert` cho hình SVG). Gộp main vào nhánh #94 xung đột ở Môi trường §6.1–6.2 (main có câu V2 thật từ #91): giữ bản chi tiết của #94, chuyển số ước 18/11 (9–10 giờ ≈ 14–15 USD) vào đoạn "V2 thực tế" để không lặp.
- **Incidents:** job `yaml` của #89 và job `manifests` của #91 kết thúc `success` nhưng GitHub vẫn để trạng thái `in_progress`, nên `gh pr checks` báo pending mãi → chạy lại riêng job đó (`gh run rerun --job`), lần sau xanh.
- **Links:** PR #89, #90, #91, #92, #93; `docs/adr/README.md`, `docs/luan-van/README.md`, `docs/chi-tiet/05-moi-truong-danh-gia.md`.

## 2026-11-27 – Merge PR #94 và #61 (Môi trường theo V2 thật, kiem_van)

- **Task:** TR8 · **Environment:** none
- **Done:** lượt tự chạy có cho merge (lượt 20261127-2241, vòng 1), gỡ nốt hàng đợi #94 → #61 → #60. Mỗi PR kiểm đủ 5 điều kiện merge: CI 6/6 xanh, đã chạy `/code-review high` lúc mở PR, `MERGEABLE`, không có review hay bình luận, không đụng manifest Argo CD theo dõi, base `main`. Merge commit, xoá nhánh head.
- **Results:** #94 `5b74c02` (bản gộp xung đột §6.1–6.2 ở `6c24979` đọc lại trước khi merge). #61 xung đột với main ở nhật ký tuần 08 (merge=union tự gộp); sau khi gộp, `uv run --project analysis pytest analysis` 212 test đạt, `ruff check` sạch; merge `dbdbd1d`. Gộp main vào nhánh #60 không còn xung đột ở `build_diagrams.py` (main đã có `Svg.save` ghi LF); dựng lại Hình 7 bằng `fig_slo_alert()` cho SVG giống hệt bản đã commit.
- **Links:** PR #94, #61, #60; `analysis/kiem_van.py`, `docs/diagrams/build_diagrams.py`.

## 2026-11-27 – Merge PR #60; soát số độc lập chương 3 và chương 6

- **Task:** TR8 · **Environment:** none
- **Done:**
  1. Merge PR #60 (Hình 7, cảnh báo SLO) bằng merge commit `f4a0a86` ở lượt tự chạy 20261127-2241 vòng 1; nhật ký của lượt đó đã nằm trong #60, nên phần merge #60 ghi ở đây. Không còn PR mở của Trình.
  2. Soát số độc lập 3.0–3.6 và 6.0–6.3 (quy-tac-viet §9, lượt khác lượt viết): đối chiếu khoảng 230 số và khẳng định với Thông số, ADR-003, ADR-007, manifest, `llm.yaml`, chương 5 (đã soát 27/11) và `tai-lieu.bib`. Không còn giá trị cũ trước ADR-003 (C 3,5; target 37; TTFT 2,5 s; N = 4).
  3. Đối chiếu lại từng lỗi với nguồn rồi sửa trên nhánh mới `docs/tr8-audit-ch3-ch6` (#80, #87 đã merge); đánh dấu "Soát số: 27/11/2026" ở 10 file (3.0–3.6, 6.1–6.3; 6.0 không có số).
- **Results:**
  - 5 lỗi xác nhận, đã sửa cả 5. (1) 3.2 viết vòng Git chỉ kiểm ở cluster nhà, trong khi ADR-007 D2 đã chạy VH2 qua Git trên simulator có Argo CD (05-05: 4 commit, 615 request, 0 lỗi); sửa câu, chú thích Hình 3.1, ô "Dùng cho" của simulator. (2) 3.4 viết mỗi pod giữ GPU đủ 180 s và dẫn tới 5.3; số 180 s chỉ đo ở máy nhà, trên V2 chưa đo (5.5.1). (3) 3.6 viết hai lớp kiểm thử đầu chạy chủ yếu trên simulator và máy nhà, trong khi VH1–VH4 chạy trên V2. (4) VH4 gọi là "mất nguồn metric", dễ lẫn với ca "mất metric nguồn" ở 3.3.3 (exporter ngừng); đổi thành "mất kết nối tới Prometheus" ở 3.6, 6.1 và cả 1.3, 5.0, 5.7 cho thống nhất. (5) 6.2 dẫn "(mục 3.5)" cho đợt 503 và dead man's switch, nhưng thân 3.5 không có hai ý này; đổi thành Bảng 3.7 hoặc bỏ.
  - 9 điểm nghi vấn, sửa 7: "mức tham chiếu" N2b (3.1); mức tham chiếu N2b ghi thành quyết định sau phiên đo (3.1); ước tính 8 phút có nhãn (3.6); image khoảng 9 GB thay 10 GB (3.4, Bảng 5.4a 9,04 GB); "cùng kịch bản và cùng lần lặp" (3.6); VH1 không "lặp lại" trên VM (3.6); threshold A2 là 0,8 × B\* đọc từ vLLM, không suy bằng định luật Little (6.1); "đầu khoảng đó" 370–400 request chờ (6.3); 6.2 nói rõ Argo CD trên simulator chỉ quản lý serving và autoscaling. Sửa thêm 3 comment nguồn lỗi thời (3.1, 3.2, 3.3).
  - Để lại: 5.7 và 6.2 chưa nêu ba điểm ADR-003 §6 yêu cầu (ổ đĩa dưới 130 GB, chưa `vllm bench serve`, ADR-003 viết sau kết quả); thuộc việc nhóm D riêng trong danh sách việc.
  - `kiem_van.py` 0 điểm ở 12 file sửa; lychee: lỗi chỉ còn ở `docs/huong-dan/w2.md` (có sẵn trên main, ngoài diff).
  - `/code-review high`: 10 điểm, sửa 9. Bản sửa đầu viết quá tay: chú thích Hình 3.1 và đoạn App-of-Apps ngụ ý simulator cũng chạy App-of-Apps (thực tế chỉ áp thẳng 2 Application, `envs/sim/argocd/apps.yaml`), câu "chưa kiểm trên GPU thật" mâu thuẫn với máy nhà có GPU, 3.6 bỏ sót graceful shutdown đo ở máy nhà; thêm đường dẫn manifest sai, comment nguồn 6.2 trỏ vào 03-05, comment 5.5 và 3.4 còn chữ cũ, 3.0 chưa đánh dấu soát. Bỏ qua: comment "Giá trị tạm" trong `common/autoscaling/a2/scaledobject-a2.yaml` (manifest, ngoài phạm vi PR tài liệu).
- **Links:** PR #60; nhánh `docs/tr8-audit-ch3-ch6`; `docs/luan-van/03-0*.md`, `06-0*.md`, `01-03`, `05-00`, `05-07`.
- **Thesis:** chương 3, chương 6; các số đã qua soát, còn bước "Người viết đọc lại".

## 2026-11-27 – Merge PR #95; vẽ lại Hình 5 và Hình 15 bằng số đo V2

- **Task:** TR8 · **Environment:** none
- **Done:** (1) Merge PR #95 (soát số chương 3 và 6) bằng merge commit `e03849a` sau khi 6 check CI xanh, `MERGEABLE`, không có review đòi sửa. (2) Vẽ lại Hình 5 (`fig_coldstart` trong `docs/diagrams/build_diagrams.py`) từ số tám pha của ĐG3 trên V2: 5 thanh cho 5 lượt hợp lệ (L0 hai lượt, L2 ba lượt), 6 nhóm pha (1–3 gộp vì kéo image nằm trong đó). (3) Vẽ lại Hình 15 (`fig_calibration` trong `docs/diagrams/chuyen_sau.py`) từ ĐG1 trên V2, đọc thẳng `envs/cloud/experiments/capacity.json`: TTFT p95, TPOT p95 (thay ITL), B trung bình; C = 3,5 req/s, B\* = 46,3, threshold A2 = 37. (4) Sửa chú thích hai hình và bảng §11 ở Kiến trúc (giá trị đo V2 thay "ví dụ 30 / 24 / 0,55"), câu hỏi hội đồng ở Kiến thức nền §8, "TTFT/ITL" → "TTFT/TPOT" ở Bài toán §10, đánh dấu mục Hình 5, 15 trong checklist Kế hoạch §11.4.
- **Decision:** Hình 5 vẽ từng lượt thay vì trung bình, vì chỉ có 2–3 lượt mỗi mức và quy ước đánh giá là vẽ từng lượt (Môi trường §16). Hình 15 đọc `capacity.json` thay vì chép số, để chạy lại ĐG1 thì hình tự theo; số Hình 5 vẫn chép từ comment đầu `05-04-cold-start.md` vì script tính pha chưa có trong `analysis/`. Điểm vượt trục (TTFT 69,7 s, B = 232 ở 5 req/s) vẽ ở mép trên, nối nét đứt, ghi số thật.
- **Results:** Hình 5: L0 310,7 / 300,7 s, L2 75,7 / 75,7 / 80,8 s (tổng theo mốc thật; L2 lượt 3 cộng các pha đã làm tròn ra 80,9 s, ghi trong comment). Hình 15: TPOT p95 36 → 64 ms khi B tăng 16 → 64 (giới hạn `--max-num-seqs`), λ = 4 chỉ 28,5% request đạt SLO. lychee trên ba file `docs/chi-tiet/` đã sửa: 0 lỗi; ruff (E, F, W) trên hai script không thêm lỗi mới so với main. `/code-review high`: 10 điểm, đã sửa cả 10.
- **Links:** `docs/diagrams/build_diagrams.py`, `docs/diagrams/chuyen_sau.py`, `docs/images/05-cold-start.svg`, `docs/images/15-hieu-chinh-nang-luc.svg` (+ PNG), `docs/chi-tiet/01`, `02`, `03`, `06`.
- **Thesis:** Hình 5 dùng được cho 5.4 (cạnh Bảng 5.4a), Hình 15 cho 5.2; chưa chèn vào luận văn.

## 2026-11-27 – Thay nguồn công thức M/M/1 ở mục 2.2 bằng giáo trình mở đã đọc trực tiếp

- **Task:** TR8 · **Environment:** none
- **Done:**
  1. Tìm nguồn công khai cho W = 1/(μ − λ) (mục 2.2 dẫn Harchol-Balter 2013, giáo trình chưa đọc trực tiếp; điểm còn để ngỏ từ code-review của #83).
  2. Đọc bản PDF arXiv:1307.2968v27 (M. Zukerman, *Introduction to Queueing Theory and Stochastic Teletraffic Models*, 15/03/2025): mục 6 giả định dòng đến Poisson, phục vụ IID phân phối mũ, một server; mục 6.3 phương trình (303) cho E[D] = E[Q]/λ = 1/(μ − λ), suy từ E[Q] = ρ/(1 − ρ) bằng định luật Little.
  3. Đổi trích dẫn trong `02-02` thành `[@zukerman-queueing]`, sửa hai comment nguồn; thay mục `harchol-balter-queueing` trong `tai-lieu.bib` bằng `zukerman-queueing` (`@online`, eprint arXiv, URL ghim v27, ngày đọc).
  4. `/code-review high`: 5 điểm (URL chưa ghim v27, design doc còn dẫn sách cũ, locator, trường `howpublished`, comment gán câu λ ≥ μ cho phương trình 303); sửa cả 5.
- **Decision:** thay hẳn, không giữ Harchol-Balter song song: luận văn chỉ dẫn tài liệu đã đọc (quy-tac-viet), và giáo trình mở đủ cho khẳng định đang dẫn. Bỏ phương án dẫn Wikipedia (không phải nguồn học thuật) và bài giảng MIT 2.854 (bản tìm được không nêu trực tiếp 1/(μ − λ)). Tài liệu thiết kế `01-bai-toan-yeu-cau.md` §3 cũng đổi phần đọc thêm sang Zukerman để hai nơi dẫn cùng một nguồn. Số mục để trong comment nguồn, không dùng locator trong `[@…]`, cho giống các trích dẫn khác.
- **Results:** `pandoc … --citeproc` cả quyển: không cảnh báo trích dẫn (chỉ cảnh báo SVG thiếu `rsvg-convert`, có từ trước); câu ra "(Zukerman 2025)". `kiem_van.py` 02-02: 0 điểm.
- **Links:** `docs/luan-van/02-02-hang-doi-nang-luc.md`, `docs/luan-van/tai-lieu.bib`.
- **Thesis:** §2.2, danh mục tài liệu tham khảo.
## 2026-11-27 – Ảnh ba dashboard trên kind làm phương án dự phòng cho F5

- **Task:** TR4 (F5) · **Environment:** sim
- **Done:** (1) Tạm bật anonymous Viewer cho Grafana trên kind bằng `kubectl set env` để Chrome headless mở được dashboard. (2) `make sim-test-load C=25 DUR=240s`, A2 scale 1 → 3. (3) Port-forward Grafana, chụp ba dashboard ở chế độ kiosk, khoảng 15 phút gần nhất, bằng Chrome headless trên Windows. (4) Cắt khoảng trống ở đáy hai ảnh bằng Pillow, đặt ba ảnh ở `docs/images/anh-chup/` (không để chung `docs/images/png/`, nơi chỉ chứa PNG xuất từ SVG và đánh số theo hình). (5) Gỡ hai biến môi trường anonymous, Grafana rollout lại.
- **Decision:** Dùng anonymous Viewer tạm thời trên kind cục bộ (vài phút, rồi gỡ), vì đây là cách ngắn nhất để Chrome headless mở dashboard mà không phải đăng nhập. Không chọn: render API (cần cài plugin grafana-image-renderer), token service account (Chrome headless gọi từ dòng lệnh không gắn được header `Authorization` vào trang), profile Chrome đã đăng nhập (`--user-data-dir`, phải đăng nhập tay một lần). Không lặp lại cách này trên cluster nhà: Grafana nhà do Argo CD quản lý và mở cho cả tailnet; ở đó nên dùng profile Chrome đã đăng nhập. Ảnh đặt tên đuôi `-sim` để không nhầm với ảnh GPU nhà; chưa gắn vào luận văn.
- **Results:** hey 971 response 200, p95 13,2 s ở C = 25 (simulator). Dashboard SLO và chi phí: 972 request đã trả xong trong 15 phút (hơn hey 1 request; chưa kiểm request thừa đến từ đâu, có thể nằm ngoài lượt hey trong cửa sổ 15 phút), TTFT ≤ 2,5 s và TPOT ≤ 100 ms đều 100 %, `LLMAtMaxReplicas` pending, đồng thời cao nhất 25. Dashboard Autoscaling: desired = Ready = max = 3, cold start hai pod mới 6 s. Hàng GPU "No data" (kind không có GPU). Hàng chi phí có số (GPU-giờ 0,38, $0,19, $2,533 / 1 triệu token) chỉ vì panel đếm mỗi pod `vllm-*` đã xếp lên node là một GPU; trên kind đây không phải chi phí thật, không dùng làm số đo.
- **Incidents:** Bảng "Request đang chạy" và "Token/s theo pod" chỉ có số ở pod cũ: `load-sim.sh` gửi tải qua `kubectl port-forward svc/vllm`, mà port-forward chỉ nối tới một pod, nên hai pod mới Ready nhưng không nhận request. Ảnh vẫn đúng cho vòng lặp scale (tín hiệu tổng, HPA, trạng thái pod), nhưng không minh hoạ chia tải giữa các pod. Ngoài ra, trên ảnh, "Request đang chạy" và "Request đang chờ" chỉ có số khoảng 23:24–23:26, trong khi tải chạy tới 23:27:59 và "Token/s theo pod" còn số tới khoảng 23:28; chưa tìm hiểu vì sao. Nếu cần ảnh chia tải thì bơm tải từ một pod trong cluster tới Service.
- **Links:** `docs/images/anh-chup/dashboard-autoscaling-sim.png`, `dashboard-serving-gpu-sim.png`, `dashboard-slo-cost-sim.png`, `docs/nhat-ky/van-hanh.md`.
- **Thesis:** dự phòng cho F5 ở 4.4 hoặc 5.6 nếu không có ảnh dashboard GPU nhà; khi dùng phải ghi rõ là simulator, hạn chế chia tải ở trên và hàng chi phí không phải số thật.

## 2026-11-28 – Merge PR #98 (ảnh dashboard dự phòng F5)

- **Task:** TR4 · **Environment:** none
- **Done:** kiểm #98 đủ 5 điều kiện merge (CI 6/6 pass, MERGEABLE/CLEAN, không bình luận, chỉ thêm ảnh và nhật ký nên Argo CD nhà không đổi, base `main`); merge commit `c1d1756`, xoá nhánh head. Gộp `origin/main` vào nhánh #99: chỉ xung đột nhật ký `tuan-08.md`, `merge=union` tự giữ cả hai mục.
- **Links:** PR #98, PR #99.

## 2026-11-28 – Merge PR #99 (nguồn M/M/1 ở mục 2.2)

- **Task:** TR8 · **Environment:** none
- **Done:** sau khi gộp `origin/main` (có #98) vào nhánh #99 và CI chạy lại, merge commit `4853a39` lúc 07:41, xoá nhánh head. Nhật ký của bước này ghi ở PR kế tiếp vì #99 đã merge.
- **Links:** PR #99.

## 2026-11-28 – `make analysis`: dựng lại bảng và hình chương 5 từ dữ liệu (P5)

- **Task:** TR8 · **Environment:** none
- **Done:**
  1. Tìm lệnh và phiên đã tạo từng file trong `analysis/figures/` (nhật ký tuần 07, `van-hanh.md` mục LT5–LT8, docstring của script). LT7 lấy phiên `runs/sim/lt7-20261116-165323`, LT8 lấy `runs/sim/lt8-20261116-131116`: chạy cả ba phiên LT7 và hai phiên LT8, chỉ hai phiên này ra CSV trùng bản trong Git.
  2. Chạy lại từng script vào thư mục tạm. 4 bảng ĐG2, `lt5-little.csv`, `lt6-gpu-util.csv`, `lt7-hpa.csv`, `lt8-burn.csv` trùng từng byte. 10 SVG chỉ khác ở xuống dòng: matplotlib trên Windows ghi CRLF; bỏ CR thì trùng từng byte.
  3. Sửa `charts._save`: SVG ghi qua file mở với `newline="\n"`, nên chạy trên Windows hay Linux đều ra LF. Thêm một assert vào test sẵn có.
  4. Thêm target `make analysis [DATA=runs] [OUT=analysis/figures]`, bỏ `analysis` khỏi danh sách lệnh đã lược. Target ghi thêm 3 báo cáo số mà chương 5 dẫn làm nguồn: `v2-dg2/dg2-a2.txt` (mục 5.3), `v2-dg2/vh6-window.txt`, `vh4-windows.txt` (mục 5.5). Báo cáo `.txt` đi qua `tr -d '\r'`, vì Python trên Windows in stdout bằng CRLF.
  5. README thêm mục "Tái lập" theo 7 ý của Kế hoạch §10.7; sửa Kế hoạch §10.7 ý 2 và Môi trường §3.7 (dòng `make analysis`).
  6. `/code-review high`: 8 điểm, sửa 5. (a) `dg2_a2`, `vh6_window` đọc bảng ở `<phiên>/tables`, không đọc bảng vừa ghi vào `OUT`, nên có thể tính từ bảng cũ: target nay chạy `build_tables` với thư mục mặc định rồi chép 4 bảng sang `OUT`; README không còn hứa quá mức. (b) Bỏ tiền tố `DATA` bằng `sed` hỏng khi `DATA=./runs`: `vh4_windows` nay chỉ in `<thư mục cha>/<lượt>`. (c) `> /dev/null` giấu dòng "bỏ qua <phiên>": thêm hàm `step` cất output vào file tạm và in lại dòng báo bỏ dữ liệu. (d) Thêm `PYTHONUTF8=1` cho Python dưới 3.15 trên Windows (thử 3.11 trên máy này: không lỗi, vì bảng mã của máy đã là UTF-8). Không sửa: gom CRLF vào Python (`tr` đủ dùng, báo cáo không chứa CR thật), hệ số `@k` ghim trong Makefile (chép đúng lệnh ở `van-hanh.md`, là nguồn của CSV), gộp 10 lần `uv run` (25 s là chấp nhận được).
- **Decision:** D142. Mặc định `OUT=analysis/figures`, tức ghi đè bản trong Git, để phép kiểm tái lập chỉ là `git status` sạch. Commit 3 báo cáo số vào Git vì luận văn đang dẫn chúng làm nguồn. Không chọn: thư mục ra riêng rồi so bằng `diff -r` (thêm một bước, phải sửa `.gitignore`); chỉ in báo cáo ra màn hình (không kiểm được số trong luận văn từ repo).
- **Results:** `make analysis SHELL=bash` trên `runs/` mất 25 s; sau đó `git status` chỉ có 3 file báo cáo mới, không file cũ nào đổi. Sau bản sửa của review: chạy lại, `analysis/figures/` không đổi; `DATA=./runs//` với `OUT` là thư mục tạm cho kết quả trùng `analysis/figures` (`diff -r` rỗng). `DATA=nope` báo thiếu `nope/v2-vm/v2-dg2`, mã thoát 2. Test analysis: 212 passed; ruff check và ruff format đạt; lychee 0 lỗi; yamllint đạt.
- **Deviations:** chưa gồm bảng cold start 8 pha của ĐG3 (đọc `summary.txt` do runner ghi) và hình trong `docs/images/` (`build_diagrams.py`), đã ghi rõ trong README. `dataset/` chưa có (việc P4), nên chưa chạy được với `DATA=dataset`.
- **Links:** `Makefile` (target `analysis`), `analysis/charts.py`, `analysis/tests/test_charts.py`, `README.md` (mục Tái lập), `docs/chi-tiet/06-ke-hoach-quan-ly.md` §10.7, `docs/chi-tiet/05-moi-truong-danh-gia.md` §3.7.
- **Thesis:** 4.6 hoặc 5.1 (HG5 tái lập: một lệnh dựng lại mọi bảng và hình chương 5, kiểm bằng `git status`); Phụ lục.

## 2026-11-28 – Soát 7 runbook với sự cố V1, V2, VH (checklist Kế hoạch §11.4, phần 3)

- **Task:** TR8 · **Environment:** none
- **Done:** đọc 7 runbook trong `docs/runbooks/`, đối chiếu với các mục sự cố của `docs/nhat-ky/van-hanh.md` (06/11 SIGTERM, 08/11 NVML và V1, 16/11 image GC, 16/11 và 18–19/11 VH), nhật ký Quang tuần 07, quy tắc `common/observability/alerts/llm.yaml`, recording rule `llm:error_ratio:rate5m` và probe trong `common/serving/deployment.yaml`. Sửa 6 runbook và đồng bộ Phụ lục C.
- **Results:** 7 cảnh báo, 7 runbook, mỗi quy tắc có `runbook_url` trỏ đúng file. Các điểm sửa:
  - `LLMPodPending`: cỡ image chỉ ghi "~30 GB" (cỡ sau giải nén), thêm cỡ tải về 9–11 GB nén (Thông số §10.2, nhật ký vận hành 23/10; V2 kéo lại 2 phút 34 giây, PC nhà 14 phút 52 giây, đủ làm cảnh báo kêu); thêm Lưu ý vLLM 0.31.0 không thoát khi nhận SIGTERM nên pod cũ giữ GPU đủ 180 s (V2: rollout 4 pod 371,6 s; VH2c Pending 300 s, chưa tới `for: 10m`); thêm ca image mất khỏi node khi vLLM ở 0 replica (nghi kubelet image GC, chưa xác định). Comment quy tắc `LLMPodPending` ghi thêm cỡ nén.
  - `LLMPodNotReady`: thêm số cold start đo được (container chạy → Ready 155–162 s ở nhà; lệnh scale → Ready trên V2 76–81 s L2, 300–311 s L0); startupProbe restart container sau 10 phút nên lúc cảnh báo kêu phải đọc `logs --previous`.
  - `LLMPodCrashLooping`: thêm dòng `StartError` / NVML mismatch (VM Vast 08/11).
  - `LLMErrorRateHigh`: thêm mục Giới hạn: chỉ đếm request qua Traefik, runner gọi thẳng Service nên cảnh báo không kêu được trong mọi lượt đánh giá; gộp vào dòng "Không còn pod Ready" ca pod duy nhất bị xoá/restart (V2 vh3-delete 2 pod 0 lỗi; vh3-kill 129 lỗi, khả năng cao vì chỉ có 1 pod, chưa kiểm).
  - `LLMSLOBurnFast` và Phụ lục C: thêm ca hàng đợi ghim ở pod cũ (V1 A2 × KB2: 1.028 request, xả ~9 phút), kèm cách phân biệt với "một pod chậm"; số cold start L2 trên V2.
  - `/code-review high`: 9 điểm, sửa cả 9 (hai chỗ ghi giả thuyết thành sự thật, cỡ image, cold start trộn hai cách đo, hai dòng bảng mâu thuẫn, Phụ lục C ghim commit).
  - `KedaScalerErrors`: thêm thời gian từ lúc chặn tới fallback (16,8 s V2, 17,2 s N = 2).
  - `LLMAtMaxReplicas`: không cần sửa.
  - Kiểm: `make alerts-test` đạt (7 rule); `yamllint` sạch; `lychee` 27/27 link OK.
- **Deviations:** chưa đánh dấu dòng "runbook được review lần cuối sau phiên V2" ở Kế hoạch §11.4, vì PR #102 sửa dòng ngay dưới (tránh xung đột); đánh dấu sau khi #102 merge.
- **Links:** `docs/runbooks/*.md`, `docs/luan-van/phu-luc/c-runbook-mau.md`, `common/observability/alerts/llm.yaml` (chỉ comment).
- **Thesis:** 4.6 (runbook cập nhật theo sự cố thật), 5.7 Hạn chế (`LLMErrorRateHigh` không đo được trong lượt đánh giá), Phụ lục C.

## 2026-11-28 – Checklist trước khi nộp, lần quét 1: placeholder và bí mật trong lịch sử Git (Kế hoạch §11.4)

- **Task:** TR8 · **Environment:** none
- **Done:**
  1. Quét placeholder trên `origin/main` bằng `git grep` (`TODO`, `FIXME`, `XXX`, `TBD`, `vX.Y.Z`, `<org>`, "chưa viết", `REPLACE_ME`, `changeme`, `<your`, "Giá trị tạm"). Ngoài nhật ký chỉ còn: tên thư mục `shellcheck-vX.Y.Z/` trong `ci.yaml` (đúng nghĩa), chính dòng checklist, và comment "Giá trị tạm" của threshold trong `common/autoscaling/a2/scaledobject-a2.yaml` (lỗi thời sau ADR-003). Câu "chi phí thực tế chưa được…" ở 5.1 chờ số chi phí Vast của Quang (N8).
  2. Sửa comment threshold A2: 24 là giá trị giữ chỗ của base; nhà ghi đè 23, simulator 10, VM thuê lấy `A2_threshold` của ma trận (V1 42, thử N = 2 39, V2 37). Kiểm lại: mọi nơi dùng file (overlay nhà, overlay sim, ba ma trận cloud) đều ghi đè.
  3. Quét bí mật trong lịch sử: không tải được gitleaks (lệnh `gh release download` bị deny rule của lượt tự chạy, không lách), nên dùng script Python cục bộ duyệt mọi blob của `git rev-list --objects --all` qua `git cat-file --batch`, áp các mẫu của script đóng gói bộ dữ liệu (PR #101) cộng thêm token GitHub, Tailscale, `certificate-authority-data`, trường `token:`, khoá Sealed Secrets, hex 64 cạnh chữ secret/R2/AWS, khoá Vast. Output chỉ in mẫu, đường dẫn, độ dài và 2 ký tự đầu, không in giá trị.
  4. Ghi kết quả lần quét vào hai dòng checklist §11.4 (chưa đánh dấu, vì phải quét lại trên bản nộp).
  5. `/code-review high`: 7 điểm. Sửa 5: (a) checklist dẫn `analysis/dataset.py` trong khi file chưa có trên `main`, nay mô tả mẫu bằng lời; (b) ghi rõ hai chỗ khớp còn lại thay vì "không còn chỗ nào"; (c) comment nói rõ threshold VM theo từng ma trận, không chỉ 37; (d) phạm vi quét ghi "ref đã fetch, gồm head của mọi PR" (review kiểm: không có `refs/pull/*/head` nào nằm ngoài nhánh đã fetch), lần quét lại phải fetch `refs/pull/*/head`; (e) thêm mục nhật ký này. Không sửa 2: thư mục `dataset/` chưa track trong cây làm việc là sản phẩm của PR #101, commit này chỉ `git add` từng file; đổi giá trị base từ 24 sang 37 (D144).
- **Decision:** D144. Giữ `threshold: "24"` ở base, chỉ sửa comment. Mọi nơi dùng đều ghi đè, nên đổi giá trị không đổi kết quả nào; đổi sau khi dữ liệu đã đóng băng (22/11) thì base lệch với manifest ở Phụ lục A.3 mà không có lợi đo được. Phương án bỏ: đặt base = 37 (chỉ đúng cho V2, sai cho nhà và sim), thêm test bắt buộc ghi đè (thêm code cho một rủi ro chưa xảy ra).
- **Results:** 1.827 blob, 489 đường dẫn. Tên file đáng ngờ từng có trong lịch sử: chỉ `.env.example`. Khớp mẫu: 7 nhóm, đều không phải bí mật thật: fixture giả trong `analysis/tests/test_dataset.py` (JWT, khoá riêng, khoá = giá trị, kubeconfig), tên mẫu trong `analysis/dataset.py`, tên biến `api_key` và `LOADGEN_API_KEY=...` trong `loadgen/__main__.py`, `experiments/ops/graceful_shutdown.py`. IP công khai: chỉ DNS công cộng (1.1.1.1, 8.8.8.8, 8.8.4.4, 114.114.114.114, 223.5.5.5) trong hướng dẫn W1 và nhật ký, DNS IPv6 của Google `2001:4860:4860::8888` trong test, và hai chuỗi trông như IPv6 trong `Makefile` (`::error file=…::`) và `mo_phong_v3.py` (lát cắt `[-1200::10]`), khớp nhầm. Không có IP máy thuê. Thời gian quét dưới 5 phút.
- **Incidents:** lần chạy đầu treo: script ghi hết danh sách blob vào stdin của `git cat-file --batch` trước khi đọc stdout, pipe đầy nên hai tiến trình chờ nhau. Sửa: ghi stdin ở luồng riêng.
- **Deviations:** không dùng gitleaks (mức Could ở Thông số §5) vì không tải được trong lượt tự chạy. Chưa so với giá trị thật trong file biến môi trường cục bộ (lượt tự chạy không được đọc file đó): Trình nên chạy gitleaks, hoặc chế độ so giá trị của script đóng gói, trước khi nộp. Phần (3) của việc (soát 7 runbook với sự cố V2 và VH) để vòng sau.
- **Links:** `common/autoscaling/a2/scaledobject-a2.yaml`, `docs/chi-tiet/06-ke-hoach-quan-ly.md` §11.4.
- **Thesis:** 6.1 hoặc Phụ lục (checklist bàn giao: repo công khai không chứa bí mật, cách kiểm).
## 2026-11-28 – Bộ dữ liệu `dataset/`: script đóng gói, quét bí mật, checksum (P4)

- **Task:** TR8 (P4, Kế hoạch §10.6) · **Environment:** none
- **Done:** PR #100 (`make analysis`) đã merge vào `main` (`a904353`, CI 6/6). Viết `analysis/dataset.py`: chép 9 phiên chương 5 dùng từ `runs/` sang `dataset/`, giữ nguyên bố cục; trước khi chép quét mọi file (kể cả `.gz`) tìm token Telegram, token Hugging Face, khoá riêng, chứng chỉ kubeconfig, khoá truy cập, IP công khai, email, tuỳ chọn đúng các giá trị của `.env`; thấy chỗ khớp thì dừng và chỉ in file, số dòng, tên mẫu. Sau đó ghi `INDEX.csv` (mỗi lần thử của runner một dòng) và `SHA256SUMS` (định dạng `sha256sum`), có `--check`. Viết `dataset/README.md` (nội dung từng thư mục, ngày, máy, mục luận văn dùng; định dạng file; cách dùng; giấy phép CC BY 4.0). `.gitignore` bỏ `dataset/*` trừ README. Sửa README gốc (Tái lập ý 5) và Kế hoạch §10.6 (dòng "Thực tế 28/11"). 11 test mới.
- **Decision:** D143. `dataset/` giữ bố cục của `runs/` thay cho cây `capacity/`, `coldstart/`, `matrix/`… ở §10.6, để `make analysis DATA=dataset` chạy không cần đổi đường dẫn. Bỏ `figures/` (dựng lại được), file `.lock` của runner, log Ansible của `make bootstrap` (README của `v2-evidence` ghi là có địa chỉ máy thuê; quét không thấy IP công khai nào, vẫn bỏ cho chắc). Giữ log vLLM vì ĐG3 và pha 4–8 cần. Giấy phép CC BY 4.0 theo đề xuất của §10.6. Không đăng lên GitHub Release hay R2 (việc đăng chờ Trình).
- **Results:** đóng gói thật: 851 file dữ liệu, 38,0 MB, 9 phiên; `INDEX.csv` 25 dòng (22 cloud, 3 sim; 1 lần thử sim `valid=false` là S1-KB2 của `tr7-kb2-sim-2`); quét 0 chỗ khớp. `sha256sum -c SHA256SUMS` đạt cho 853 file. `make analysis DATA=dataset OUT=<thư mục tạm>` mất 24 s, `diff -r` với `analysis/figures` rỗng, và `--check` vẫn khớp sau khi lệnh này ghi lại `tables/`. `v2-evidence/vm-runs-sha256-before-poweroff.txt` (checksum gốc trên VM): 504 file khớp, 0 sai, 1 không có (file `.lock` bị bỏ). `/code-review high`: 10 điểm, sửa cả 10: mẫu token Telegram lọt trong URL Bot API; `VLLM_API_KEY=…` không khớp vì `\b` trước `_`; IPv4 có dấu chấm cuối câu bị bỏ qua; thêm IPv6 công khai và JWT; khoá Vast, R2 chỉ là chuỗi hex nên mặc định so với `.env` nếu có (`--no-env-file` để bỏ; lượt tự chạy dùng cờ này vì không được đọc `.env`); `.env` có comment cuối dòng; file nhị phân không quét được nay làm script dừng; `--check` báo rõ khi thiếu SHA256SUMS, đọc được dạng `sha256sum -b`; INDEX.csv và SHA256SUMS chỉ gồm file đã đóng gói; README ghi rõ `v2-evidence` còn nhắc file bị bỏ. Quét lại sau khi sửa: 0 chỗ khớp, `make analysis DATA=dataset` vẫn trùng từng byte. Test analysis 238 passed; ruff check, ruff format đạt; lychee 0 lỗi.
- **Deviations:** bố cục khác cây ở Kế hoạch §10.6 (đã ghi "Thực tế" ở đó). Chưa đăng dữ liệu. Lượt tự chạy không đọc `.env` nên chưa quét theo giá trị trong đó: trước khi đăng, Trình chạy lại lệnh đóng gói không kèm `--no-env-file`.
- **Links:** `analysis/dataset.py`, `analysis/tests/test_dataset.py`, `dataset/README.md`, `.gitignore`, `README.md`, `docs/chi-tiet/06-ke-hoach-quan-ly.md` §10.6.
- **Thesis:** 4.6 hoặc 5.1 (HG5 tái lập: bộ dữ liệu kèm checksum dựng lại đúng từng byte mọi bảng và hình); Phụ lục (mô tả bộ dữ liệu).

## 2026-11-28 – Merge PR #101 (bộ dữ liệu), PR #102 (quét placeholder, bí mật) và PR #103 (runbook)

- **Task:** TR8 · **Environment:** none
- **Done:** kiểm đủ 5 điều kiện merge cho #101, #102, #103 (CI 6/6 pass, MERGEABLE, không review hay bình luận, `/code-review high` đã chạy và sửa, base `main`). Điều kiện 4: #102 và #103 chỉ đổi comment trong `scaledobject-a2.yaml` và `alerts/llm.yaml`; hai file vào kustomize qua `resources:` nên comment bị bỏ khi render, manifest Argo CD áp lên cluster nhà không đổi. Merge #101 (`d26a9ba`, 11:09) trước vì nó thêm quy tắc `.gitignore` cho `dataset/`. Gộp `origin/main` vào nhánh #102: chỉ nhật ký và Kế hoạch §11.4 tự gộp, không xung đột thật; push, CI chạy lại xanh, merge `7086160` (11:10). Gộp `origin/main` vào nhánh #103: `merge=union` đặt hai mục nhật ký sát nhau, thiếu dòng trống, đã thêm. Đánh dấu dòng "runbook được review lần cuối sau phiên V2" ở Kế hoạch §11.4 (để dành từ #103 vì #102 sửa dòng ngay dưới).
- **Results:** merge #103 `2d6c0b6` (11:12, CI 6/6 pass). Sau ba lần merge, `main` sạch và `dataset/` được ignore.
- **Links:** PR #101, PR #102, PR #103, `docs/chi-tiet/06-ke-hoach-quan-ly.md` §11.4.

## 2026-11-28 – Cắt trang nhẹ chương 1, 4, 6 theo D103

- **Task:** TR8 · **Environment:** none
- **Done:** đo khuôn T bằng gop.py (Word COM) trước khi sửa: ch. 1 4,86 tr, ch. 4 22,48, ch. 6 3,91. Chỉ bỏ câu đã nói ở mục khác (GPU utilization ở 1.3 trùng 1.1, chi tiết môi trường ở 1.2 trùng 3.2, số VH3 và VH6 ở 4.6 trùng 5.5, số hàng đợi ở 6.1 trùng 5.3.3), câu lộ trình "Mục 4.x.1 nói…" ở 4.1 và 4.3, câu "Mục này trình bày" ở 4.6 (quy-tac-viet cấm), và vài câu phụ (sleep mode ở 6.3, số máy thử A4000 ở 4.1.1). Câu bỏ được chép nguyên văn vào comment "Ý không đưa vào (cắt 28/11 theo D103…)" ở đầu mỗi file; comment nguồn còn dẫn ý đã cắt thì ghi rõ ý đó nay chỉ ở comment này. Nhánh đặt tên `docs/tr8-thesis-trim-d103` để gop.py nhận và đo được. Sáu lần đo lại sau từng đợt cắt.
- **Decision:** dừng ch. 1 ở 4,24 tr và ch. 6 ở 3,73 tr thay vì ép về 4 và 3,3: phần còn lại là ý chưa có ở chỗ khác (phát biểu bài toán, giả định GPU-giờ, mức bằng chứng của kết luận vận hành, giới hạn mô phỏng), bỏ tiếp là bỏ nội dung chứ không còn là "cắt nhẹ"; để Trình quyết khi đọc lại. Ch. 4 bắt buộc ≤ 22 nên cắt tới khi đạt.
- **Results:** ch. 1 4,86 → 4,24 tr; ch. 4 22,48 → 21,89; ch. 6 3,91 → 3,73; thân bài 71,54 → 70,36 tr khuôn T. Số trang từng mục dao động khoảng ±0,1 tr giữa các lần đo vì cách ngắt trang của bảng (ch. 2 lần cuối đo 13,16 dù không sửa). kiem_van 0 điểm trên mọi file đã sửa; lychee 0 lỗi. `/code-review high` 9 điểm, sửa cả 9: khôi phục đoạn SIGTERM ở 6.2 (bản rút gọn sai quan hệ nhân quả với grace period 180 s), số event loop p99 4,1 ms và "không lượt nào bị throttle" ở 4.7 (mục 5.1 không có hai số này), câu N8 ở 4.1.3 (bảng truy vết Kế hoạch §11.1 trỏ N8 về 4.1); sửa ba câu ở ch. 1 (chủ ngữ, câu ghép dấu phẩy, câu GPU utilization khôi phục bản gốc); sửa lời dẫn của comment cắt (bản trong bài đã viết gọn thì khôi phục bằng cách thay, không chèn thêm), đánh dấu comment nguồn, đặt comment cắt trước dòng "Soát số" cho thống nhất.
- **Links:** nhánh `docs/tr8-thesis-trim-d103`; `docs/luan-van/01-01…01-03`, `04-01`, `04-03`, `04-06`, `04-07`, `06-01…06-03`.
- **Thesis:** cả quyển (độ dài theo D103).

## 2026-11-28 – Soát chính tả và thuật ngữ toàn quyển, lần 1

- **Task:** TR8 · **Environment:** none
- **Done:**
  1. Dựng bản gộp bằng `gop.py`, chia bốn phần (ch. 0–2 và phần đầu; ch. 3; ch. 4; ch. 5–6 và phụ lục), mỗi phần một agent đọc đối chiếu `quy-tac-viet.md` §4–§6, chỉ báo lỗi có dẫn dòng.
  2. Áp khoảng 70 sửa trên 30 file `docs/luan-van/`: thuật ngữ gọi hai kiểu theo bảng `quy-tac-viet.md` §4 (VM thuê, máy nhà, grace period, "lượt" thay "lần chạy", "phiên đo chính"), mã F/N ngoài chỗ được dùng, câu chủ đề mở bằng mã LT/ĐG, giải nghĩa lần đầu (CI, MPS, DCGM, open-loop, SRE), dấu phân cách nghìn (1.024, 1.230), đơn vị giây viết `s`, dấu chấm cuối chú thích Hình 1.1 và 3.1, bỏ dấu chấm thừa ở Bảng 2.1 và 2.2, dẫn chéo ở 5.1 (mục 1.3 → 1.2).
  3. Chạy `kiem_van.py` trên 30 file: một điểm mới do lần sửa (03-06 dòng 39 thành 5 mã/đoạn khi đổi "mức ấm" thành "mức L2"), trả về "mức ấm". Các điểm còn lại (ngày tháng đủ năm ở 05-01, D, E; tên người ở F) đã có từ trước, đúng ngữ cảnh.
  4. `/code-review high` trên diff: 10 điểm. Sửa 8: câu 3.6 dẫn "mức ấm" mà 3.4 không định nghĩa (nay gọi "cấu hình cold start chạy thật", như 3.4); bốn câu mở bằng "Kiểm chứng LTx" (lặp nghĩa của mã, nay mở bằng chủ đề); 4.1 thay N6, N8 bằng "chỉ tiêu nghiệm thu" không chỉ được dòng nào (nay "một chỉ tiêu ở mục 3.1"); 5.1 "lần đo đầu" khác 4.7 "lần thử đầu"; khoảng 409–430 s dẫn Hình 5.3b chỉ vẽ lượt 1; thêm closed-loop vào danh mục; "máy tạo tải" trong danh sách nội dung kho thành "mã nguồn máy tạo tải"; dòng Decision của mục này. Bỏ 2: "lượt thử" của vòng Git ở 4.5, 4.7 đúng nghĩa "lượt" ở §4; viết hoa ở danh mục so với thân bài là quy ước thường gặp.
- **Results:** không có lỗi gõ hay dấu tiếng Việt; số hình, bảng và dẫn chéo khác đều đúng. `lychee --offline --include-fragments` trên `docs/luan-van/`: 0 lỗi. Số trang chưa đo lại (lần sửa chỉ đổi từ, không thêm câu).
- **Decision:** chỉ sửa chỗ đã có quy ước trong `quy-tac-viet.md` §4–§6. Điểm chưa có quy ước để lại lần soát 2, vì mỗi điểm đụng nhiều chương và cần chốt một cách gọi trước khi sửa: "X phút Y giây" so với đơn vị s; "pha" của cold start trùng "pha" của tải; "khoá API" và "API key"; "chu kỳ sync" của HPA trùng "sync" của Argo CD; số cảnh báo của F6 (6 ở Bảng 3.1, bảy quy tắc ở Bảng 3.7); các cặp "LLM serving"/"phục vụ LLM", "repository"/"repo", "rollout"/"rolling update", "8 pha"/"tám pha". Viết hoa phần giải nghĩa từ viết tắt giữ như cũ: danh mục viết hoa (Continuous Integration), thân bài viết thường in nghiêng.
- **Links:** nhánh `docs/tr8-thesis-proofread` (xếp trên `docs/tr8-thesis-trim-d103`, PR #104).
- **Thesis:** cả quyển (chất lượng văn bản trước M4).

## 2026-11-28 – Hạn chế theo ADR-003 §6 và dòng N2b trong bảng nghiệm thu

- **Task:** TR8 · **Environment:** none
- **Done:**
  1. Soát việc nhóm D đầu (số VH2 trên kind ở 4.5, F3 và N4 ở 5.6 theo ADR-007): đã có sẵn trên `main` từ các PR trước (4.5 có 615 request, 0 lỗi, push → sync 138–247 s; 5.6 dòng F3 ghi "trên GPU chỉ qua annotation"), không cần sửa.
  2. Bảng 5.6a dòng N2b: thêm "vượt mức tham chiếu 5 phút" (ADR-003 G5, §5), kết luận vẫn "Báo cáo".
  3. 5.7 thêm các hạn chế ADR-003 §6 yêu cầu: C = 3,5 là cận dưới (so với năng lực thật, tải nhẹ hơn danh nghĩa tối đa gần 12,5%); chưa đối chiếu ĐG1 với `vllm bench serve`; ổ đĩa 126 GB dưới mức 130 GB, tốc độ đọc tuần tự không đo; mức tham chiếu N2b ghi thành quyết định sau khi có kết quả. Nêu rõ `LLMErrorRateHigh` chỉ có unit test vì máy tạo tải gọi thẳng Service, không qua Traefik (ý còn nợ từ #103). Tách đoạn 1 của 5.7 thành hai đoạn (ma trận ĐG2; ĐG1).
  4. 5.1 sửa câu "đạt các tiêu chí lọc còn lại" thành đạt CPU, RAM, mạng, giá; ổ đĩa không đạt, tốc độ đọc chưa đo (ADR-003 G8, `runs/v2-evidence/console/00-probe.txt`: `/dev/root 126G`, 120G trống).
  5. `/code-review high`: 10 điểm, sửa cả 10 (5.1 nói quá về tiêu chí đĩa; tên tài liệu nội bộ "Thông số" lọt vào thân bài; "Cuối cùng" sai cấu trúc; câu 12,5% so sai mốc; "bước cuối của quy trình" chưa giới thiệu trong luận văn; comment ngân sách và dòng "Soát số" chưa cập nhật; nguồn đoạn 1 bị dồn sang comment đoạn sau; câu ổ đĩa thiếu ảnh hưởng; "tiêu chí chọn máy" và "tiêu chí lọc" gọi hai kiểu).
- **Decision:** các hạn chế của ADR-003 §6 đặt ở 5.7 (hạn chế của phép đo), không ở 6.2 (hạn chế của hệ thống), vì đều là điều kiện đo của phiên V2.
- **Results:** kiem_van: 05-06 và 05-07 0 điểm; 05-01 1 điểm có từ trước (ngày đủ năm ở dòng 8). 5.7 tăng 573 → 768 chữ văn xuôi, chưa đo lại khuôn T. Các câu mới do người viết đối chiếu ADR-003 và probe, chưa soát độc lập.
- **Links:** nhánh `docs/tr8-thesis-vh2-acceptance` (xếp trên `docs/tr8-thesis-proofread`, PR #105); `docs/luan-van/05-01`, `05-06`, `05-07`.
- **Thesis:** 5.1, 5.6, 5.7.

## 2026-11-28 – Chèn Hình 3.2 (vòng vận hành theo SLO) vào 3.5

- **Task:** TR8 · **Environment:** none
- **Done:**
  1. Chèn Hình 7 của `docs/chi-tiet/04-van-hanh.md` (vẽ lại ở PR #60) vào 3.5.2 thành Hình 3.2, kèm một câu nhận xét sau hình; sửa comment đánh số ở đầu 03-02…03-06.
  2. Bản đầu chèn cả Hình 8 và Hình 17 vào 3.6 thành Hình 3.3, 3.4. `/code-review high` báo 10 điểm; sửa hoặc xử lý cả 10: bỏ Hình 3.3, 3.4; dời Hình 3.2 xuống sau comment nguồn của đoạn định tuyến; sửa câu ticket cho khớp hình; bỏ cụm "làm theo runbook" lặp ở đoạn tự xử lý; cập nhật dòng Sơ đồ của `nguon-tu-lieu.md`.
- **Decision:** (D146) không chèn Hình 8 (trùng Bảng 3.8, in mã N1–N7 trái quy-tac-viet §4) và Hình 17 (quy trình từng lượt và tên lệnh, phần đã chuyển sang 4.7 khi cắt ngày 24/11). Hình 2 đã có ở 3.2 (Hình 3.1) từ trước. Câu ticket sửa thành "không nhắc lại trong 24 giờ, dài hơn một phiên đo, và không báo lúc đã hết", đúng `repeat_interval: 24h`, `send_resolved: false` trong `common/platform/alertmanager-values.yaml`.
- **Results:** kiem_van 03-05 và 03-06: 0 điểm; lychee offline trên 03-0x và `nguon-tu-lieu.md`: 0 lỗi. Chưa đo lại khuôn T ch. 3 (cần push rồi chạy `gop.py`).
- **Links:** nhánh `docs/tr8-thesis-ch3-figures` (xếp trên `docs/tr8-thesis-vh2-acceptance`, PR #106); `docs/luan-van/03-05-giam-sat-slo-canh-bao.md`, `nguon-tu-lieu.md`.
- **Thesis:** 3.5 (Hình 3.2).
