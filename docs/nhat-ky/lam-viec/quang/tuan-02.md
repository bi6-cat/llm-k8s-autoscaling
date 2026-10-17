# Nhật ký làm việc – Quang – Tuần 02 (12–18/10)

## 2026-10-15 – Chốt phân công và quy tắc nhật ký

- **Mã việc:** chung · **Môi trường:** không
- **Đã làm:** rà phần code W2 chưa commit (khung repo theo `docs/huong-dan/w2.md`, chưa chạy trên cluster); chốt phân công; thêm `AGENTS.md`, `CLAUDE.md` để AI agent của mỗi người tự ghi nhật ký.
- **Quyết định và lý do:** chia theo tính năng dọc, hai người cùng vai trò. Quang nhận phần "chạy được trên GPU" (Q1–Q7) vì PC 5060 và laptop 4050 ở chỗ Quang; Trình nhận phần "tự scale và đo được" (TR1–TR7), làm qua Tailscale với quyền đầy đủ. Không chia theo tầng vì muốn mỗi người đều chạm cả hạ tầng lẫn code. Không tính bù giờ W1–W2 vì code W2 chưa chạy thật. Luận văn: mỗi người viết mục về tính năng mình làm, lấy từ nhật ký cá nhân.
- **Kết quả và số đo:** ước lượng Quang 57–83 giờ, Trình 60–88 giờ (chưa tính luận văn và trực V2).
- **Liên kết:** `docs/chi-tiet/06-ke-hoach-quan-ly.md` §5.1, `AGENTS.md`.
- **Dùng cho luận văn:** phần phân công và đóng góp từng thành viên; Kế hoạch §7.

## 2026-10-16 – Thêm quy ước code và thư mục

- **Mã việc:** chung · **Môi trường:** không
- **Đã làm:** thêm `CONTRIBUTING.md` gom quy ước đang rải rác (Kế hoạch §10.2–§10.3) và quy ước ngầm của code W2 (header file, `.yml` cho Ansible, namespace, đặt tên cảnh báo); link từ README, AGENTS.md, Kế hoạch §10.3.
- **Quyết định và lý do:** `CONTRIBUTING.md` là trạng thái thực tế của repo, ưu tiên hơn cây thư mục thiết kế ở Kế hoạch §10.2 (đã lệch: thiếu overlay `sim`, `infra/kind/`). Commit tiếng Anh dạng `<phạm vi>: <mô tả>`, khớp các commit đã có.
- **Liên kết:** `CONTRIBUTING.md`.

## 2026-10-16 – Giảm "thuần cài đặt": thêm kiểm chứng lý thuyết LT1–LT8

- **Mã việc:** chung (tạo Q8, TR8) · **Môi trường:** không
- **Đã làm:** thêm Môi trường §19 (LT1–LT8); thêm Q8/TR8 vào phân công và lịch W3–W4; thêm mục vào checklist M2; sửa thứ tự cắt giảm (§8) và rủi ro R21.
- **Quyết định và lý do:** muốn đồ án bớt giống "đã cài X, đã cài Y" nhưng số liệu phải dễ lấy. Chọn cách: dùng lý thuyết đã có ở Kiến thức nền để dự đoán, rồi đo ở nhà hoặc trên simulator từ nguồn có sẵn (Prometheus, log vLLM, event, `requests.csv`). Không thêm cơ chế mới (ví dụ A3) vì thời gian còn ~7 tuần. Sửa §8: trước đây khi runner chậm thì cắt A1 và L0, mà đó lại chính là đối chứng cho đóng góp 2 và 3; nay giảm số lượt lặp thay vì cắt đối chứng.
- **Kết quả và số đo:** chưa đo. Dự đoán ban đầu: TPOT batch 1 của Qwen2.5-1.5B ≥ ~7 ms trên 5060, ≥ ~16 ms trên 4050; KV ≈ 28 KB/token (cần kiểm tra lại bằng `nvidia-smi -q` và `config.json`).
- **Liên kết:** `docs/chi-tiet/05-moi-truong-danh-gia.md` §19, `docs/chi-tiet/06-ke-hoach-quan-ly.md` §5.1, §8, R21.
- **Dùng cho luận văn:** chương 4–5, mỗi LT một đoạn theo mẫu lý thuyết → dự đoán → số đo → giải thích; trả lời câu hỏi "đồ án có phải chỉ là cài đặt".

## 2026-10-16 – Dọn và thống nhất toàn bộ tài liệu và code trước khi bắt đầu code

- **Mã việc:** chung · **Môi trường:** không
- **Đã làm:**
  - Khôi phục `docs/adr/` (ADR-001, 002, 004, 005) từ Thùng rác: bị xoá nhầm lúc tái cấu trúc 08/10 nhưng tài liệu link tới 43 lần. Bỏ báo cáo review (nội bộ), sửa các link tới nó. ADR-004 thêm §7 ghi các quyết định sau 08/10 (phân công, GVHD không cần duyệt, LT1–LT8, giữ ca đối chứng).
  - Bỏ các mục "chờ GVHD trả lời" ở kế hoạch, mô tả, w2.md; hạ R25.
  - `w2.md` từ 2.123 xuống ~760 dòng: thay 57 khối "nội dung file" bằng link tới file thật (đã so khớp từng khối trước khi thay). Thêm bảng nhánh/người/điều kiện đạt cho W2.
  - Sửa tài liệu thiết kế cho khớp code: cache ở nhà là hostPath `/var/lib/llm-cache` (không phải PVC), cache trên VM là `/mnt/nvme/cache`, có overlay `sim`, `autoscaling/official` có base + overlays, cây App-of-Apps thật. Kiến trúc §3.2 thay manifest mẫu (đã lệch) bằng link + bảng điểm then chốt. Kế hoạch §10.2 trỏ sang CONTRIBUTING §1 (một nguồn duy nhất về thư mục).
  - Comment lại toàn bộ 55 file code theo mức "vừa học" (CONTRIBUTING §2).
  - Sửa code: bỏ biến `repo_url` không dùng; ghim `kindest/node:v1.37.0` trong kind-config; CI kiểm link cả CONTRIBUTING.md, AGENTS.md; `make help` liệt kê lệnh chưa làm; `.gitignore` thêm `.vscode/` và gỡ `.vscode/settings.json` khỏi Git.
- **Kết quả và số đo:** link Markdown 0 lỗi (kể cả anchor); `yamllint -s .` sạch; `ansible-playbook --syntax-check` đạt; `kubectl kustomize` cả 6 thư mục build được. So "nghĩa" của code trước/sau (bỏ comment): chỉ khác đúng các chỗ sửa có chủ đích ở trên.
- **Sự cố:** lần đầu viết comment cuối dòng trong `.gitignore`, mà Git không hỗ trợ (`abc  # x` thành một mẫu) → chuyển comment lên dòng riêng, kiểm bằng `git check-ignore`. Ghi thành quy tắc ở CONTRIBUTING §6.
- **Liên kết:** `docs/adr/`, `docs/huong-dan/w2.md`, `CONTRIBUTING.md`, toàn bộ `infra/`, `platform/`, `serving/`, `autoscaling/`.
- **Dùng cho luận văn:** §4.2 (GitOps, quy ước repo, CI); phần "Quy trình làm việc" (một nguồn sự thật cho code và tài liệu).
