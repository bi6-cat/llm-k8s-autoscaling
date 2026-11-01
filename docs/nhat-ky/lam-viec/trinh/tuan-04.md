# Nhật ký làm việc – Trình – Tuần 04 (26/10–01/11/2026)

## 2026-11-01 – TR2: simulator trên kind (WSL2 trên máy Trình), chạy T1–T5

- **Mã việc:** TR2 · **Môi trường:** simulator (kind trong WSL2, laptop Windows của Trình)
- **Đã làm:**
  1. Máy của Quang đang trục trặc nên chưa vào được cluster nhà; dựng simulator ngay trên máy Trình. Cài WSL2 Ubuntu 24.04 vào `D:\WSL\Ubuntu-24.04` (`wsl --install -d Ubuntu-24.04 --location … --no-launch --web-download`). Trong Ubuntu, bằng root: Docker Engine 29.9.2 (kho apt của Docker), kind v0.33.0, kubectl v1.36.5, helm v4.3.1, kubeconform v0.8.0 (file tải về đều kiểm sha256), `hey` từ apt, giới hạn inotify như w1 §5.3. `.wslconfig` có sẵn trên máy giới hạn WSL ở 6 GB RAM, 6 CPU.
  2. Nhánh `feat/tr2-sim` từ `origin/main`. Viết lại phần của Trình dựa trên bản nháp của Quang (`temp/w2-scaffold`, `12c4e27`), ghi nguồn ở header: `infra/kind/kind-config.yaml`, `platform/keda/values.yaml`, `platform/kube-prometheus-stack/values.yaml` và `values-sim.yaml`, `autoscaling/official/{base,overlays/sim}/`, `autoscaling/tests/` (body request, NetworkPolicy của T4). `serving/` của Quang lấy từ `feat/serving` (`dbc72b0`) bằng `git archive` ra `/opt/llm-sim/serving`, không commit; Makefile thêm biến `SIM_SERVING` để `make sim-up` dùng thư mục đó.
  3. Đối chiếu từng key trong values với `helm show values` của đúng bản chart đã ghim (kube-prometheus-stack 92.1.1, KEDA 2.21.0), render thử bằng `helm template`; `kubectl kustomize | kubeconform -strict` như job `manifests` của CI.
  4. `make sim-up SIM_SERVING=/opt/llm-sim/serving/overlays/sim`, rồi kiểm điều kiện trước khi thử: kube-controller-manager có `--horizontal-pod-autoscaler-sync-period=5s`; target `podMonitor/llm-serving/vllm/0` up, chu kỳ 5 s; câu PromQL của A2 trả 0; APIService `v1beta1.external.metrics.k8s.io` True.
  5. Chạy T1–T5 bằng một script nháp ghi trạng thái HPA mỗi giây (lần 1). Sửa theo kết quả, đưa vào repo thành `autoscaling/tests/run-t1-t5.sh` (gọi bằng `make sim-test`, tự chấm đạt/trượt theo bảng w2 §9.3), chạy lại cả 5 bài (lần 2).
- **Quyết định và lý do:**
  - WSL2 + Docker Engine, không dùng Docker Desktop (bạn chọn): môi trường Linux giống cluster thật và CI, nhẹ hơn, sau này chạy được cả Ansible.
  - Lấy code như TR1 (bạn chọn): nhánh mới từ `main`, viết lại, ghi nguồn. Không commit `serving/` để không đụng phần của Quang.
  - `platform/keda/values.yaml` thêm `cpu: null`. Helm gộp values vào mặc định của chart, mà mặc định có `limits.cpu: 1`; bản nháp chỉ ghi `limits.memory` nên limit CPU vẫn còn, trái với comment "không đặt limit CPU". `helm template` xác nhận: có `cpu: null` thì cả 3 Deployment của KEDA chỉ còn limit bộ nhớ.
  - Ghim node image theo digest (`kindest/node:v1.37.0@sha256:a1ed56cf…0ae5`, lấy từ release notes kind v0.33.0), theo CONTRIBUTING §2.
  - kubectl v1.36.5, trùng CI, để `kubectl kustomize` cho cùng kết quả. helm v4.3.1, bản chính hiện tại; hai chart đã ghim cài được bằng bản này.
  - kube-prometheus-stack thêm `scrapeConfigSelectorNilUsesHelmValues: false` cho đủ bộ "nhận mọi CR, không đòi label".
- **Kết quả và số đo:**
  - `make sim-up` lần đầu (kéo node image và mọi image): **501 s**, mã thoát 0. Kết quả đúng như w2 §9.2: 1 pod `vllm-…` Ready, `vllm-a2` `READY=True`, HPA `0/10 (avg)`. `keda-operator` khởi động lại 1 lần (`Completed`, exit 0, log không có dòng lỗi).
  - RAM khi chạy T3 (3 pod simulator): 3 container node của kind tổng khoảng 2,39 GiB (914 + 813 + 666 MiB); VM WSL 2,8 GB (`vmmemWSL`). Khớp ước tính "kind + giám sát + simulator khoảng 3 GB" (w1 §5.1). Ổ của WSL dùng 8,5 GB.
  - Lần 1 (script nháp, 21:45–22:01):
    - T1: `desired=1`, metric 0 suốt 120 s. Đạt.
    - T2 (hey C=25, 180 s): `desired=3` sau **1 s**; pod thứ 2 Ready sau 7 s, pod thứ 3 sau 16 s kể từ lúc HPA quyết định; metric HPA ở 3 replica là `8334m` ≈ 25 ÷ 3. hey: 750 request, cả 750 trả 200, 3,92 request/s. Đạt (tiêu chí ≤ 15 s). 1 s là do lần scrape và lần sync HPA cùng rơi ngay sau lúc bắt đầu tải; trường hợp xấu nhất theo lý thuyết khoảng 10 s (scrape 5 s + sync 5 s).
    - T3: về 2 sau 301 s tính từ hạn dừng của hey, về 1 sau thêm 61 s. Đạt.
    - T4: áp NetworkPolicy 120 s, `numberOfFailures` vẫn 0, không fallback. Trượt; nguyên nhân ở mục Sự cố.
    - T5: KEDA xoá HPA khoảng 1 s sau khi gắn annotation; `ready=1` ở cả 83 lần đọc trong lúc có tải; hey 257/257 request trả 200. Gỡ annotation thì HPA được tạo lại. Đạt.
  - Lần 2 (`make sim-test`, script trong repo, 22:01–22:20, mã thoát 0): cả 5 bài đạt.
    - T1: `desired=1` suốt 120 s.
    - T2: `desired=3` sau **6 s**; metric HPA ở 3 replica 8,334 ≈ 25 ÷ 3. hey 760/760 request trả 200.
    - T3: giữ 3 trong 302 s tính từ hạn dừng của hey, về 1 sau thêm 60 s.
    - T4 (có bước xoá pod keda-operator): operator mới Ready sau 23 s; KEDA báo lỗi lần 1, 2, 3 ở giây +4, +10, +12; fallback ở +18 s (`desired=3`, metric 30 = 3 × threshold 10, `Fallback=True`), tổng **19 s** kể từ lúc operator Ready, `numberOfFailures=4` (tiêu chí ≤ 30 s). Gỡ policy thì lần hỏi kế tiếp thành công, `numberOfFailures` về 0, rồi scale-down như T3.
    - T5: `spec.replicas=1` ở cả 71 lần đọc trong lúc tạm dừng có tải; hey 255/255 request trả 200.
- **Sự cố:**
  - T4 không fallback. Pod busybox mới trong ns `keda` gọi Prometheus thì `download timed out`, ở ns `default` thì gọi được: kindnet có thực thi NetworkPolicy. Nhưng KEDA dùng lại kết nối keep-alive đã mở (hỏi mỗi 5 s nên kết nối không bao giờ rảnh để đóng), còn NetworkPolicy chỉ chặn kết nối mới (conntrack cho kết nối đã mở đi qua). Sửa: sau khi áp policy thì `kubectl -n keda delete pod -l app=keda-operator`; không dùng `rollout restart`, vì Argo CD ở nhà sẽ hoàn tác thay đổi template. Lệnh kiểm tra cũ ở w2 §9.3 (`kubectl exec deploy/keda-operator -- wget`) không chạy được vì image không có `wget`; đổi sang pod busybox. VH4 (TR6) gây sự cố bằng cùng policy nên cũng cần bước này.
  - WSL tự tắt distro khi không còn phiên `wsl.exe` nào (sau khi lệnh chạy nền kết thúc), làm Docker dừng giữa chừng. Lần mở sau, `llm-sim-control-plane` `Exited (128)`: `runc` không tạo được unit `docker-<id>.scope`. Sửa: `systemctl reset-failed` rồi `docker start llm-sim-control-plane`; API server sẵn sàng sau khoảng 2 s; vài pod báo `CreateContainerConfigError` ("services have not yet been read at least once") rồi tự hết sau khoảng 2 phút. Tránh: giữ một phiên WSL mở khi dùng simulator (phiên này giữ bằng `sleep infinity`); xong thì `make sim-down`. Đã ghi vào bảng lỗi w2 §13.
  - Script nháp đo T3 từ lúc tiến trình hey thoát nên ra 291 s, trông như trượt tiêu chí 300 s. Tới hạn, hey thôi gửi request mới nhưng còn chờ request dở dang khoảng 10 s; cửa sổ 300 s tính từ lần cuối HPA còn muốn 3 replica (21:51:01 + 300 s = 21:56:01, đúng lúc về 2). Sửa mốc 0 thành hạn dừng của hey.
  - Thêm `platform/`, `infra/` một phần làm job `docs` của PR #5 báo 31 link hỏng; sửa trên `feat/tr1-ci` (mục TR1 cùng ngày, nhánh đó).
- **Khác thiết kế:**
  - Simulator chạy trên laptop Windows của Trình qua WSL2, không phải laptop Ubuntu của Quang (w1 §5.1), vì máy Quang đang trục trặc và TR2 là việc của Trình. Thiết kế loại WSL2 vì không hợp Kubernetes có GPU (Môi trường §2.1); simulator không cần GPU.
  - `serving/` chưa có trên nhánh: `make sim-up` cần `SIM_SERVING` tới khi `feat/serving` merge.
  - T4 thêm bước xoá pod keda-operator; w2 §9.3 và file NetworkPolicy đã sửa theo.
  - T1–T5 chạy tự động bằng `make sim-test`; hướng dẫn gốc chạy tay bằng ba terminal (vẫn giữ trong w2 §9.3).
- **Liên kết:** nhánh `feat/tr2-sim` (commit cùng mục này); log thô ở `runs/sim/` trên máy Trình (không commit).
- **Dùng cho luận văn:** chương "Triển khai và vận hành" (Kiến trúc §15): bảng T1–T5 kèm số đo; hình số replica theo thời gian ở T2–T3 vẽ từ log mỗi giây (chưa vẽ); sự cố T4 (NetworkPolicy và conntrack) là ví dụ "cách gây sự cố cũng phải được kiểm chứng". LT7 (TR8, Môi trường §19) cần T2 chạy 5 lần; hiện có 2 lần: quyết định scale sau 1 s và 6 s (dự đoán ≤ ~15 s).
