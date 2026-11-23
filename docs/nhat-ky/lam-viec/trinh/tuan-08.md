# Nhật ký làm việc – Trình – Tuần 08 (23–29/11/2026)

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
- **Links:** `docs/chi-tiet/06-ke-hoach-quan-ly.md` (§3 M4, M5; §5.1; §11.1; §11.4); `docs/chi-tiet/01`, `03`, `04`, `05` (phần đầu; 05 dòng F4); `docs/luan-van/quy-tac-viet.md`, `nguon-tu-lieu.md`, `README.md`, `03-05-giam-sat-slo-canh-bao.md`.
- **Thesis:** dàn ý toàn bộ; 1.4 (cách trình bày quy trình); Lời cam đoan (khai báo công cụ AI).

## 2026-11-23 – Đưa bộ soát văn phong luận văn vào repo (`analysis/kiem_van.py`)

- **Task:** TR8 · **Environment:** none
- **Done:**
  1. Chuyển bộ soát văn phong (trước đó chỉ có trên máy của Trình) vào `analysis/kiem_van.py`: docstring theo CONTRIBUTING §2, type hint, tên mỗi luật kèm § của `quy-tac-viet.md` hoặc README; tách hàm thuần `check_text()` trả về danh sách điểm để test được; CLI bằng `argparse`, bỏ trống thì soát mọi file mục `docs/luan-van/CC-SS-*.md`, mã thoát 0 (sạch), 1 (còn điểm), 2 (không đọc được file) như ruff.
  2. Thêm 3 luật có sẵn trong `quy-tac-viet.md` mà bản cũ chưa đếm: đường dẫn `docs/` và link Markdown tương đối trong thân bài (§3.5); nhãn dàn ý TĐ/HG và mã biểu đồ C1–C6 (§4); cụm "với mục tiêu" (§3.4).
  3. Sửa 3 chỗ bắt sai của bản cũ: tách câu ngắt nhầm trước chữ thường có dấu (khoảng `À-Ỹ` của regex cũ gồm cả chữ thường như "ở"); đoạn dẫn và mục danh sách bị báo thiếu nguồn dù comment nguồn đặt sau cả danh sách; công thức riêng dòng `$$…$$` bị đếm như đoạn văn một câu. Luật nguồn cũng chặt hơn: comment nguồn phải đứng ngay sau khối (chỉ cách bởi dòng trống, comment khác hoặc danh sách đi liền), không còn được tính khi nằm sau đoạn kế tiếp trong cửa sổ 3 dòng.
  4. `analysis/tests/test_kiem_van.py`: 38 cặp ca vi phạm/viết đúng phủ mọi luật (một test kiểm mỗi luật khai báo đều có ca), cùng test cho tách khối, tách câu, tìm nguồn, thống kê, giới hạn 5 điểm mỗi luật và mã thoát.
  5. Thêm dòng chạy `kiem_van` vào checklist `quy-tac-viet.md` §10; cập nhật cây thư mục ở CONTRIBUTING §1 và header `analysis/pyproject.toml`.
  6. Việc làm trong lượt tự chạy 23/11; PR chờ Trình xem, chưa merge.
- **Decision:** (D91)
  - Đặt trong gói `analysis/` thay cho gói Python riêng: module chỉ dùng thư viện chuẩn, gói `analysis` đã phục vụ luận văn, và job `python` của CI đã chạy pytest, ruff cho gói này trên 3.11 và 3.15, nên không phải thêm `pyproject.toml`, `uv.lock` và bước CI mới. Bỏ phương án đặt cạnh `docs/diagrams/build_diagrams.py` vì chỗ đó không có test và lint.
  - CI chỉ chạy test của module, không chạy soát trên `docs/luan-van/`: vài luật chỉ là gợi ý cần người đọc lại (từ nối, dấu hai chấm, chữ "agent" của k3s), nên nếu chặn merge thì sẽ đỏ giả. Mã thoát 1 dành cho người viết và người soát trước khi mở PR.
- **Results:**
  - `uv run --project analysis --locked pytest analysis`: 198 passed (47 của `kiem_van`) trên Python 3.15; test `kiem_van` trên Python 3.11: 47 passed. `ruff check`, `ruff format --check`, `yamllint -s .`: đạt. lychee 0.24.2 (offline, kèm anchor, bỏ qua đường dẫn cũ như job `docs`): 0 lỗi.
  - So bản cũ với bản mới trên 4 file nháp (03-05, 05-03, 05-05b, 05-06): số điểm giống nhau ở mọi luật, trừ "đoạn ngoài 3–7 câu" của 03-05 (8 xuống 6, hai dòng công thức `$$`) và "thiếu nguồn" của 05-05b (4 xuống 2) và 05-06 (4 xuống 3), đều là đoạn dẫn hoặc mục danh sách có nguồn đặt sau cả danh sách. Tổng: 52 → 50, 29 → 29, 46 → 44, 13 → 12.
- **Links:** `analysis/kiem_van.py`, `analysis/tests/test_kiem_van.py`, `docs/luan-van/quy-tac-viet.md` §10, `CONTRIBUTING.md` §1, `analysis/pyproject.toml`.
- **Thesis:** không vào thân bài; công cụ dùng ở bước soát mọi mục (quy-tac-viet.md §10).
