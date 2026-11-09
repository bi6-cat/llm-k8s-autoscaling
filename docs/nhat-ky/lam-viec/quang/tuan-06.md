# Nhật ký làm việc – Quang – Tuần 06 (09–15/11/2026)

## 2026-11-09 – Đưa phần dọn dẹp 08/11 vào `main` sau khi PR #27 merge nhầm base

- **Task:** chung · **Environment:** none
- **Done:** rà công việc đầu tuần, phát hiện `main` thiếu 7 commit; tạo `chore/v2-prep-to-main` từ `origin/feat/v2-prep`, gộp `origin/main`; sửa mục nhánh và PR trong `viec-sap-lam.md`.
- **Results:** gộp không conflict. Trên bản gộp: pytest `experiments` 126 passed, `loadgen` 55 passed.
- **Incidents:** PR #27 có base `feat/v2-prep` (xếp chồng trên PR #26). PR #26 merge trước nên PR #27 merge vào nhánh `feat/v2-prep` và GitHub vẫn báo `MERGED`, trong khi `main` thiếu sửa UTIL của `capacity.py`, đồng bộ tài liệu, handoff mới. Cách tránh: trước khi merge PR dưới, đổi base PR trên về `main`, giống bài học PR #24/#25 của Trình.
- **Links:** nhánh `chore/v2-prep-to-main`; PR #26, #27.
