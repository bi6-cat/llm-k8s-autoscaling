# Tuần 1 (08–11/10/2026)

> Phần vLLM trên RTX 5060 làm bù ngày 23/10 (tuần 03). Chi tiết từng bước: [nhật ký Quang tuần 03](lam-viec/quang/tuan-03.md).

## Đã làm
- Kiểm tra lại PC: driver, kernel module open, Docker, NVIDIA Container Toolkit (đã có sẵn từ trước).
- Chạy thử vLLM trên RTX 5060: **chạy được** với image `v0.31.0` (CUDA 13). Image `v0.31.0-cu129` theo hướng dẫn **không khởi động được** (lỗi đóng gói, xem dưới).
- Kiểm tra API, streaming, metric, bucket TTFT, cờ; đo nhanh bằng `vllm bench serve`; thử `--shutdown-timeout` có ca đối chứng.

## Kết quả kiểm tra vLLM trên RTX 5060
| Mục | Giá trị |
|---|---|
| Driver / compute_cap | 595.99.02 (open, `Dual MIT/GPL`) / 12.0; CUDA tối đa 13.2 |
| Image dùng được | `vllm/vllm-openai:v0.31.0@sha256:c1c9f6fd5c109ba7f0546a59f5b2f15fb87f64c77782e90a27b648b42a8e67c3` (CUDA 13.0, torch 2.13.0+cu130) |
| Image không dùng được | `vllm/vllm-openai:v0.31.0-cu129@sha256:ff29e51a9457f191deb332b96fa6440584fa941aa2a548449b604e2b1e5e1eeb`: có `sm_120` nhưng vLLM chết lúc import vì `torchcodec` build cho CUDA 13 (`libnvrtc.so.13` không có) |
| Model | `Qwen/Qwen2.5-1.5B-Instruct@989aa7980e4cf806f80c7fef2b1adb7bc71aa306` (khớp HF ngày 23/10) |
| GPU KV cache size / Maximum concurrency | 101.120 tokens / 24,69 x (4096 token/request) |
| VRAM khi chạy | 6864 / 8151 MiB (desktop chiếm sẵn ~610 MiB) |
| Khởi động (lần đầu / có cache model) | 486 s (tải model 327 s) / 167 s |
| Bucket TTFT có le="2.5" | có |
| Cờ `--shutdown-timeout`, `--no-enable-prefix-caching`, `--api-key` | có cả ba |
| --shutdown-timeout 150 drain được stream | có: stream 1000/1000 token, có `[DONE]`; container thoát sau 14,1 s |
| Đối chứng --shutdown-timeout 0 | stream bị cắt sau 10 chunk, không có `[DONE]` |
| vllm bench (c=8, in 512, out 256, 64 prompt) | TTFT p50 249 ms / p99 344 ms; TPOT p50 9,3 ms; 782 tok/s output; 0 lỗi |

## Máy và mạng
- PC: `zett-ubuntu-pc`, LAN 192.168.0.100 (chưa kiểm tra là IP tĩnh hay DHCP reservation), Tailscale đã chạy (cùng tailnet với máy `quangnv3-d8-u`).
- Laptop: chưa làm trong phiên này.

## Vast
- Chưa làm (không có bảng offer 10/10, 11/10).

## Vướng mắc / rủi ro
- **Đã chọn image `v0.31.0` (CUDA 13)** thay cho `-cu129` (ADR-004 §7, 23/10). Rủi ro mới: laptop và template VM Vast phải có driver ≥ 580; chưa kiểm tra laptop.
- `serving/base/kustomization.yaml` (đang ở nhánh `temp/w2-scaffold`) vẫn ghim `-cu129`; sửa khi tách nhánh serving (Q3).
- Ổ PC còn ~31 GB trống, dưới mức 100 GB của W1 §1.
- Chưa làm: laptop, kind + simulator, offer Vast, quota GCP.

## Tuần sau
- Tiếp W2: Q1 k3s trên PC; khi tách serving (Q3) thì sửa ghim image trong `serving/base/kustomization.yaml` và mount thêm cache compile `/root/.cache/vllm`.
