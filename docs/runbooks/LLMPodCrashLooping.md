<!-- Mục đích: runbook cho cảnh báo LLMPodCrashLooping (observability/alerts/llm.yaml). Mẫu: Vận hành §4.1. -->
# LLMPodCrashLooping

**Mức:** page · **Quy tắc:** [observability/alerts/llm.yaml](../../observability/alerts/llm.yaml)

**Ý nghĩa.** Container vLLM liên tục thoát với lỗi rồi bị khởi động lại (CrashLoopBackOff) hơn 5 phút. Kubernetes chờ lâu dần giữa các lần thử (10 s, 20 s, 40 s… tối đa 5 phút).

**Ảnh hưởng.** Pod không bao giờ Ready. Nếu mọi pod đều crash (thường gặp sau một lần cập nhật sai) thì dịch vụ ngừng hoàn toàn.

**Chẩn đoán nhanh (≤ 5 phút).**
```bash
kubectl -n llm-serving get pods                                   # cột RESTARTS tăng dần
kubectl -n llm-serving logs <pod> --previous --tail=80            # log của lần chạy vừa crash
kubectl -n llm-serving describe pod <pod> | grep -A5 'Last State' # Reason: OOMKilled / Error, Exit Code
```

**Xử lý.**

| Dấu hiệu | Hành động |
|---|---|
| `Reason: OOMKilled` | Container dùng quá `limits.memory`: tăng limit hoặc giảm `--max-num-seqs` |
| `CUDA out of memory` trong log | Giảm `--gpu-memory-utilization` hoặc `--max-model-len` |
| `libnvrtc`, `CUDA driver version is insufficient` | Image không hợp driver của node (xem `docs/phien-ban.md`, yêu cầu driver ≥ 580) |
| Lỗi tham số (`unrecognized arguments`, `ValueError`) | Vừa đổi tham số hoặc phiên bản: rollback bằng `git revert` |
| Không tìm thấy model | Kiểm tra revision và đường dẫn model trong overlay |

**Leo thang.** Mọi pod cùng crash thì gọi người thứ hai ngay và rollback trước, điều tra sau.

**Sau sự cố.** Ghi vào `docs/nhat-ky/van-hanh.md` (thông báo lỗi, nguyên nhân); bổ sung bảng dấu hiệu ở trên nếu gặp lỗi mới.
