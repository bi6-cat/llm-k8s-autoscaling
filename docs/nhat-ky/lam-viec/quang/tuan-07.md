# Nhật ký làm việc – Quang – Tuần 07 (16–22/11/2026)

## 2026-11-16 – Rà tiến độ đầu tuần; chặn suspend trên PC

- **Task:** chung · **Environment:** home
- **Done:** `git pull` (`main` ở PR #38, không có gì mới). Rà mốc, nhật ký hai người, PR đang mở. Chặn tắt màn hình và suspend trên PC đến 22:00 bằng `gnome-session-inhibit --inhibit idle:suspend` (tiến trình nền, tự hết hạn, không sửa cài đặt GNOME).
- **Results:** M1 7/7; M2 2/8 theo checklist (chưa cập nhật sau PR #37, #38); M3 0/6. **V2 (lịch 14–15/11) chưa chạy**: không có thư mục `runs/` nào của V2, `van-hanh.md` dừng ở 09/11. Phiên cloud dời sang tối 16/11. PR #39 (TR1, app `autoscaling` + `observability`) đang mở, CI đạt 6 job.
- **Decision:** trong ngày làm các việc không cần cloud trên PC nhà; phiên cloud để tối.
- **Thesis:** không.

## 2026-11-16 – Argo CD ở nhà mất đồng bộ sau refactor #34: áp lại root-app

- **Task:** Q1 · **Environment:** home
- **Incidents:** cả 7 Application ở trạng thái Sync `Unknown` (Health vẫn `Healthy`). Nguyên nhân: `root-home` trên cluster còn trỏ `platform/argocd/apps/home`, thư mục này đã chuyển thành `envs/home/argocd/apps` ở PR #34 (merge 15/11); Argo CD báo `ComparisonError: … platform/argocd/apps/home: app path does not exist`. Root không tự quản lý chính nó nên phải áp tay; việc này đã ghi trong `viec-sap-lam.md` ngày 13/11 nhưng chưa làm sau khi merge.
- **Done:** trước khi áp, kiểm bằng `kubectl diff`: `root-home` chỉ đổi dòng `path`; 6 app con trong Git trùng tên 6 app trên cluster (prune không xoá app nào); ba app kustomize (`serving`, `gpu-exporter`, `monitoring-extras`) chỉ lệch annotation tracking do Argo CD tự gắn. Ba app Helm chưa diff được bằng cách này. Rồi `kubectl apply -f envs/home/argocd/root-app.yaml` và refresh.
- **Results:** sau dưới 3 phút cả 7 app `Synced`/`Healthy`. Deployment `vllm` giữ nguyên 0 replica (Git không đặt `replicas`). Node báo `nvidia.com/gpu: 2`.
- **Links:** `envs/home/argocd/root-app.yaml`; `envs/home/README.md` mục "Một lần sau khi đổi cấu trúc repo".
- **Thesis:** §GitOps, mục hạn chế của App-of-Apps: Application gốc nằm ngoài vòng tự đồng bộ, đổi đường dẫn repo phải áp tay.

## 2026-11-16 – Review PR #39 (TR1) và làm các bước trước khi merge trên cluster nhà

- **Task:** TR1 (review) · **Environment:** home
- **Done:** đọc toàn bộ diff code và manifest của PR #39. Chạy pytest `experiments` trên nhánh. Làm ba bước "trước khi merge" trong `envs/home/README.md` của PR: (1) không có runner hay `make ops-tests` đang chạy; (2) không có ScaledObject nào trên cluster; (3) áp `root-app.yaml` của nhánh (thêm `ignoreDifferences` và `RespectIgnoreDifferences=true`).
- **Results:** pytest **152 passed** trên Linux (PR ghi 147 đạt + 4 lỗi `test_backup_notify` chỉ có trên Windows). `kubectl kustomize envs/home/autoscaling` cho `maxReplicaCount: 2`, `fallback.replicas: 2`, `threshold: "23"`, `minReplicaCount: 1`. Áp root-app của nhánh: `kubectl diff` chỉ thêm hai khối mới; sau 20 s cả 7 app vẫn `Synced`/`Healthy`, đúng như PR mô tả ("không đổi gì trên cluster").
- **Incidents:** không tìm thấy lỗi trong diff. **Chưa merge**: lệnh `gh pr merge` bị chặn quyền trong phiên làm việc, để Quang merge tay. Các bước kiểm sau merge (ScaledObject `vllm-a2`, 5 chuỗi `kube_scaledobject_status_condition`, `Watchdog` có nhãn `env="home"`, 3 dashboard) **chưa làm**.
- **Deviations:** root-app trên cluster hiện là bản của nhánh PR #39, đi trước `main`. Vô hại (khối `ignoreDifferences` chỉ nhắc tới app `autoscaling` chưa tồn tại), nhưng nếu PR không merge thì áp lại bản `main`.
- **Lưu ý cho lúc merge:** (a) chưa có `.env` trên PC nên `make alertmanager-secret CTX=llm-home` chưa tạo được Secret bot; Alertmanager vẫn chạy, chỉ không gửi được tin. (b) Merge xong A2 có `minReplicaCount: 1`, nên vLLM sẽ tự lên 1 pod (≈ 3,6 GB RAM, ≈ 3,2 GB VRAM) và khi fallback sẽ lên 2 pod; xem mục RAM bên dưới.
- **Links:** PR #39.

## 2026-11-16 – Runner trên GPU nhà sau refactor; image vLLM biến mất khỏi node

- **Task:** Q6, Q4 · **Environment:** home
- **Done:** chạy `experiments.runner` với `envs/home/experiments/matrix.yaml` (S1, CONST 2 req/s × 180 s) hai lần; đọc log khởi động bằng `experiments.runner.vllm_log`.
- **Incidents:** lượt đầu (12:44) **invalid**. Triệu chứng: runner báo `quá 900 s: spec=1 ready=0`, rồi vẫn gửi tải; 123/357 request lỗi (`ConnectError` 75, `ConnectTimeout` 48), tất cả trong 68 s đầu của pha đo; thêm khoảng trống scrape 71 s. Nguyên nhân: image `vllm/vllm-openai:v0.31.0` không còn trên node, kubelet kéo lại mất **14 phút 52 giây** (event `Successfully pulled … in 14m52.179s`); container chỉ bắt đầu chạy lúc 12:58:55, pod Ready 13:01:37, sau khi pha đo đã bắt đầu (13:00:24). Vì sao image mất: **chưa xác định**. Giả thuyết: kubelet image GC xoá image không dùng (vLLM đang ở 0 replica) khi đĩa vượt ngưỡng 85 %; đĩa `/` hiện 80 % (75/99 GB) sau khi đã kéo lại. Journal của k3s không còn dòng nào về việc xoá image, và không có sudo trong phiên để xem `crictl`.
- **Results:** lượt hai (13:04, image đã có) **done, hợp lệ**: 357 request, 0 lỗi; TTFT p50 30 ms, p95 40 ms, p99 49 ms; TPOT p50 3,7 ms, p95 4,0 ms; E2E p50 0,99 s. Máy tạo tải gọi thẳng Service (không qua Ingress). `vllm_log` đọc log vLLM thật lần đầu: `complete: true`, `missing: []`, `warnings: []` ở cả hai pod.
- **Decision:** không sửa runner: lượt bị đánh dấu invalid đúng thiết kế. Không đổi ngưỡng image GC (cần sudo và là quyết định về đĩa của PC).
- **Deviations:** docstring `vllm_log.py` (điểm 3) ghi rằng khi compile cache ấm thì log **không** có dòng `torch.compile took`. Log thật ngày 16/11 có **cả hai** dòng `Directly load AOT compilation` và `torch.compile took 0.90 s in total`; bộ đọc vẫn cho `compile_cache: hit` và `torch_compile_s: 0.9`. Cần Trình xem lại câu chú thích (code chạy đúng).
- **Links:** `runs/home-smoke/S1-CONST2-1/attempt-1` (invalid), `attempt-2` (hợp lệ); `runs/` không nằm trong Git.
- **Thesis:** §5 cold start: kéo image là pha có thể lớn hơn mọi pha khác cộng lại (892 s so với 162 s), lý do của pre-pull (L2). §Hạn chế: image có thể bị GC khi scale về 0 trên node ít đĩa.

## 2026-11-16 – LT4: phân rã cold start ở nhà, hai lần khởi động (page cache nguội và ấm)

- **Task:** Q8, Q4 · **Environment:** home
- **Done:** đo tốc độ đọc tuần tự của phân vùng NVMe chứa `/var/lib/llm-cache` bằng `fio` (file 1 GB trong `~/.cache`, cùng phân vùng). Lần khởi động A = pod của lượt runner đầu (PC boot 11:45, weights chưa được đọc từ lúc boot → page cache nguội). Lần B = `kubectl delete pod` lúc 13:10:08 rồi chờ pod thay thế Ready (weights vừa được đọc → page cache ấm). Chi tiết và bảng pha ở `van-hanh.md` mục LT4.
- **Results:** `fio` direct 1 MiB, QD1: 367 MB/s; buffered 128 KiB: 1.202 MB/s. Nạp weights (0,92 GiB): A **11,67 s**, B **3,08 s**. Container bắt đầu → Ready: A 162 s, B 155 s. Pha lớn nhất ở cả hai lần là chụp CUDA graph lúc profiling: 97 s và 100 s (≈ 60–64 %).
- **Incidents:** không dùng được `drop_caches` (cần sudo), nên ca "nguội" lấy từ lần khởi động đầu sau boot, chỉ có 1 mẫu. Dự đoán từ `fio` được tính **sau** khi đã có số đo lần A, không phải trước như mẫu LT yêu cầu.
- **Deviations:** Môi trường §19 yêu cầu đo khi scale 1 → 2; ở đây đo 0 → 1 và thay pod, vì RAM không đủ an toàn cho 2 pod lâu dài (mục dưới).
- **Thesis:** §5 cold start, bảng 8 pha ở nhà; LT4: dự đoán "nạp weights ≈ dung lượng ÷ tốc độ đĩa" lệch 4–14 lần, và nạp weights không phải pha chi phối.

## 2026-11-16 – Quan sát RAM và graceful shutdown khi thay pod; trả cluster về trạng thái đầu

- **Task:** Q5, Q1 · **Environment:** home
- **Results:** một pod vLLM 0,5B dùng **3.644 Mi** RAM (`kubectl top pod`) và ≈ 3,2 GB VRAM (GPU 3.964 MiB khi 1 pod, 7.111 MiB khi 2 pod). Khi thay pod, pod cũ và pod mới cùng tồn tại khoảng 3 phút: RAM khả dụng còn 2,7 GB, swap dùng 4,3 GB (trước đó 2,9 GB), không OOM, pod mới vẫn Ready sau 157 s. Pod cũ còn `Terminating` ở giây 157 và đã biến mất ở giây 193 sau lệnh xoá (13:10:08), khớp với grace period 180 s, tức vLLM 0.31.0 vẫn không thoát khi nhận SIGTERM và giữ GPU hết grace period, giống kết quả 06/11.
- **Decision:** không chạy VH1–VH4 ở nhà trong phiên này: các kịch bản cần 2 replica chạy dưới tải nhiều phút, trong khi desktop (Chrome, VS Code) đang chiếm ≈ 9 GB và máy đã phải swap. Cần đóng ứng dụng desktop hoặc chạy lúc không dùng máy.
- **Done:** scale `vllm` về 0 như trước phiên. Kết thúc: 7 app `Synced`/`Healthy`, không có ScaledObject, `llm-serving` không còn pod. Mục "Dọn 5 pod vLLM cũ" trong `viec-sap-lam.md` không còn cần: namespace đã sạch từ trước phiên.
- **Links:** `docs/nhat-ky/van-hanh.md` (mục 16/11 và LT4); `viec-sap-lam.md`.
- **Thesis:** §Hạn chế: grace 180 s giữ GPU; RAM 16 GB là giới hạn của môi trường nhà khi chạy 2 GPU replica.

## 2026-11-16 – Thử kết nối máy thuê 4 × RTX 5060 Ti (Trung Quốc)

- **Task:** Q2 · **Environment:** V2 (máy thử, chưa cài gì)
- **Done:** SSH từ PC nhà vào máy thuê, đọc cấu hình, thử mạng tới các nguồn mà bước dựng cluster cần. Chỉ đọc, không cài hay sửa gì trên máy.
- **Results:** SSH vào được (14:17 giờ VN, máy vừa boot 9 phút). VM KVM, 4 × RTX 5060 Ti 16 GB, driver 580.95.05, 61 vCPU, RAM 123 GB, đĩa 126 GB (trống 119 GB), chưa có Docker hay k3s. Mạng: `docker.m.daocloud.io`, `ghcr.nju.edu.cn`, `mirrors.aliyun.com`, `pypi.tuna.tsinghua.edu.cn`, ModelScope trả lời trong 0,2–1,4 s; tải từ mirror Tsinghua ≈ 7,9 MB/s. `registry-1.docker.io`, `huggingface.co`, `hf-mirror.com`, `github.com`, `ghcr.io`, `get.k3s.io` đều timeout 20 s.
- **Incidents:** resolver mặc định của máy (`127.0.0.53`) không phân giải được các tên miền trên; hỏi thẳng 114.114.114.114 hoặc 1.1.1.1 thì có trả IP, riêng `huggingface.co` trả IP khác nhau ở mỗi DNS (dấu hiệu bị chặn). Chưa thử kết nối bằng IP sau khi đổi DNS, nên chưa biết `hf-mirror.com` và `github.com` có dùng được không.
- **Decision:** chưa quyết định dùng máy này cho V2; cùng loại rủi ro với máy Trung Quốc ngày 08/11 (Docker Hub bị chặn, cold start chậm).

## 2026-11-16 – Ba máy Vast thử trong buổi chiều: hai máy không lên SSH

- **Task:** Q2 · **Environment:** V2 (máy thử)
- **Done:** thử SSH từ PC nhà vào ba VM thuê qua giao diện web của Vast; tra offer 2 GPU bằng `vast.sh find` và một truy vấn nới tiêu chí. Không cài hay sửa gì trên máy nào; chưa sửa code.
- **Results:**
  - Máy 1 (4 × RTX 5060 Ti, Trung Quốc): vào được, mục trên. Sau khi hỏi DNS 223.5.5.5: `ghcr.io`, `quay.io`, `registry.k8s.io`, GitHub Pages, `get.helm.sh`, `astral.sh`, `hf-mirror.com`, mirror k3s của Rancher vào được; Docker Hub, `mirror.gcr.io`, `huggingface.co`, `github.com`, `get.k3s.io`, PyPI không vào được. Mirror `docker.1ms.run` và `docker.1panel.live` trả đúng manifest image vLLM đã ghim. **Chưa đo** tốc độ tải image và model (lệnh đo bị dừng giữa chừng).
  - Máy 2 (2 GPU): 13 lần thử trong khoảng 8 phút, TCP tới cổng SSH thành công nhưng không nhận được banner SSH.
  - Máy 3 (2 GPU, Bulgaria): TCP tới cổng SSH timeout suốt 5 phút, ping mất 100 %; mạng nhà bình thường.
  - Offer 2 GPU, VM, verified, VRAM ≥ 15 GB, ≤ 1,2 USD/giờ lúc 14:45: 5 máy, từ 0,455 (2 × RTX 4000 Ada, driver host 535) tới 1,111 USD/giờ (2 × RTX 3090). Bộ lọc `v2` mặc định với `NGPU=2` chỉ ra 3 máy 2 × RTX 3090.
- **Incidents:** hai trong ba máy không lên SSH; cùng triệu chứng với máy 4 × 5060 Ti ngày 14/11. Nguyên nhân phía Vast chưa rõ. Quang đã tắt cả ba máy.
- **Decision:** nếu dùng máy Trung Quốc thì code hiện tại hỏng ở 5 chỗ (DNS của VM, script cài k3s, registry mirror, tải model và `uv`/PyPI, chart Helm và `git clone` của runner); chưa sửa, vì chuyển hướng sang máy 2 GPU ngoài Trung Quốc.
- **Thesis:** §4.1 chọn GPU thuê, §Hạn chế: độ tin cậy của máy chợ (marketplace); bước `wait`/`probe` ngay sau khi thuê là cần thiết.

## 2026-11-16 – Dọn đĩa PC nhà, nâng ngưỡng image GC của kubelet, bật lại vLLM

- **Task:** Q1 · **Environment:** home
- **Done:** đo đĩa `/` (99 GB) bằng `du` có sudo; dọn phần an toàn; thêm `k3s_kubelet_args` vào `group_vars/home.yaml`; áp cấu hình k3s; scale vLLM lên 1 pod.
- **Results:**
  - Đĩa `/` 75/99 GB (80 %). Chiếm chỗ: containerd của k3s 36 GB (snapshot đã giải nén 26 GB + blob nén 9,8 GB, không có bản tải dở; image vLLM 9,04 GB nén là phần lớn), `/usr` 9,4 GB, home 12 GB, swap file 8,1 GB, snap ≈ 6 GB, flatpak 4,4 GB, PVC Prometheus 0,9 GB.
  - Dọn được **0,66 GB** (`apt-get clean`, `journalctl --vacuum-size=50M` giải phóng 157 MB, xoá 4 bản snap đã disabled, crash report). Không có rác lớn; đĩa vẫn 80 % (74/99 GB).
  - Sau khi áp: `configz` của kubelet báo `imageGCHighThresholdPercent: 95`, `imageGCLowThresholdPercent: 90`; node `Ready`; pod vLLM không bị khởi động lại.
  - vLLM 0 → 1 (image đã có): Ready sau 151 s; API qua Ingress `llm.home` trả lời đúng.
- **Decision:** Quang chọn chỉ nâng ngưỡng GC (85/80 → 95/90), không đụng phân vùng `sda5`. Phương án không chọn: chuyển dữ liệu k3s sang `sda5` (đĩa `/` về ~45 % nhưng phải dừng cluster và image nằm trên SATA), format `sda5`.
- **Incidents:** `ansible-playbook … --check --diff` cho cả playbook nhà báo 5 thay đổi, trong đó có **comment dòng `/swap.img` trong fstab** (role `common` tắt swap) và áp lại `root-app.yaml` bản `main`. PC đang dùng 3–4 GB swap, và root-app trên cluster đang là bản của PR #39, nên không chạy cả playbook. Thay vào đó chạy một playbook tạm chỉ render `roles/k3s-server/templates/config.yaml.j2` vào `/etc/rancher/k3s/config.yaml` rồi restart k3s; kết quả trùng với thứ role sẽ sinh ra.
- **Deviations:** swap đang bật trên PC nhà, trái với role `common` (tắt swap). Chưa xử lý: tắt swap lúc này dễ làm máy hết RAM khi mở desktop cùng vLLM. Cần quyết định riêng.
- **Ghi chú:** `sda5` (131 GB, ext4, không mount) là bản Ubuntu cũ trước lần cài lại 06/11: dùng 85 GB, gồm dữ liệu k3s cũ 34 GB và home cũ 18 GB. Sau đó, theo yêu cầu của Quang, đã **format `sda5`** (`mkfs.ext4`, nhãn `llm-data`) sau khi kiểm rằng nó không được mount, không có trong fstab, không phải swap và hệ thống boot từ `nvme0n1p6`. Phân vùng trống 125 GB, **chưa mount và chưa dùng**; đĩa `/` vẫn 80 %. Các phân vùng khác của ổ SATA (EFI cũ, NTFS) không đụng tới.
- **Links:** `ansible/inventory/group_vars/home.yaml`, `ansible/roles/k3s-server/templates/config.yaml.j2`, `envs/home/README.md`.
- **Thesis:** §Hạn chế và §Vận hành: image GC của kubelet trên node ít đĩa; scale về 0 làm image mất quyền được giữ.

## 2026-11-16 – `vast.sh attach`: dựng trọn cluster trên máy thuê qua web (2 × RTX 4000 Ada), ĐG1 rút gọn

- **Task:** Q2, Q6, Q7 · **Environment:** V2 (phiên thử code, N = 2; không phải phiên đo chính thức)
- **Done:**
  1. Máy thứ tư trong ngày (Vast, VM, Budapest): SSH vào được. Thêm vào `vast.sh` lệnh `attach <host> <port>` / `detach` và `make attach`: ghi "host port" vào `.vast/target` (gitignore), `ssh_target` đọc file này trước khi hỏi API Vast. Lý do: máy thuê qua web không có `.vast/instance_id`, và PC không có API key, nên trước đó `probe`, `inventory`, `platform`, `tunnel`, `runner-start` đều không chạy được.
  2. `make probe` → `make bootstrap` → `make cloud-platform` → `vast.sh tunnel` → runner từ PC qua tunnel (`--no-backup`).
  3. Viết `matrix-dg1-n2.yaml` (ĐG1 rút gọn: 4 mức λ × 240 s) và `matrix-try-n2.yaml` (A2 × KB2, A1 × KB3 với N = 2).
  4. Trong lúc chờ: `vast.sh wait` giới hạn chờ SSH 10 phút (trước là vòng lặp vô hạn); `runner-start` không còn hỏng khi máy dev thiếu `.env`; README cloud thêm quy trình cho máy thuê qua web; sửa chú thích điểm 3 của `vllm_log.py`.
- **Results:** (máy: 2 × RTX 4000 Ada 20 GB, driver 580.95.05 trong VM, 11 vCPU, RAM 49 GB, đĩa 126 GB, Ubuntu 22.04)
  - `probe`: CUDA 13.0; tải từ Hugging Face 53,7 MB/s; ghi đĩa tuần tự 545 MB/s; Docker Hub trả 401 sau 0,36 s (thông). CPU 11 < mức cần 8 + 3 × 2 = 14.
  - `bootstrap` từ máy trắng: **9 phút 12 giây** (`real 9m11.948s`), 38 ok, 16 changed, 0 failed; gồm tải model 3B và kéo image vLLM.
  - `cloud-platform`: **99 s** (script tự in), node báo 2 GPU, 7 CPU cấp phát được.
  - vLLM 3B: pod tạo 15:30:00, Ready 15:31:30 (**90 s**). Từ lúc bắt đầu `bootstrap` (15:18:36) tới vLLM Ready: **12 phút 54 giây** (08/11 trên 4 × A4000: 12,5 phút).
  - Cold start 3B đọc bằng `vllm_log` (`complete: true`, không cảnh báo): nạp weights 1,48 s cho 5,75 GiB; `torch.compile` 17,18 s (compile cache nguội); chụp CUDA graph lúc profiling 2 s, chụp thật 2 s; khởi tạo engine 30,8 s; KV-cache 315.600 token.
  - ĐG1 rút gọn (S1, đo 180 s mỗi mức, cả 4 lượt hợp lệ):

    | λ (req/s) | Đạt SLO | TTFT p95 | TPOT p95 | B server |
    |---|---|---|---|---|
    | 3 | 100 % | 0,21 s | 29,4 ms | 21,7 |
    | 5 | 100 % | 0,88 s | 43,2 ms | 48,9 |
    | 7 | 0 % | 47,5 s | 44,9 ms | 237 |
    | 9 | 0 % | 105,5 s | 44,7 ms | 519 |

    `capacity.py`: **C = 5,0 req/s** (sơ bộ, điểm gãy nằm giữa 5 và 7), B\* = 48,9, threshold A2 = 39. So với A4000 ngày 08/11: C = 4,5.
- **Decision:** dùng máy 2 GPU để thử code vì trong ngày không có máy 4 GPU dùng được. Máy tạo tải đặt `loadgen_cpu: 500m` cho các lượt 2 replica (node chỉ còn khoảng nửa lõi), chấp nhận khả năng tự kiểm báo invalid.
- **Incidents:** không có lỗi nào ở `probe`, `bootstrap`, `cloud-platform`, `tunnel`. Chưa thử `runner-start` (runner chạy bằng systemd trên VM): cần `.env` có khoá R2 và commit đã push.
- **Deviations:** N = 2 thay cho N = 4 (ADR-006 C2 phương án b); ĐG1 240 s mỗi mức thay cho 300 s; runner chạy từ PC qua tunnel thay cho systemd trên VM; không sao lưu R2.
- **Links:** `envs/cloud/provision/vast.sh`, `Makefile`, `envs/cloud/README.md`, `envs/cloud/experiments/matrix-dg1-n2.yaml`, `matrix-try-n2.yaml`, `experiments/runner/vllm_log.py`; `runs/dg1-try-4000ada/` (không nằm trong Git). Nhánh `feat/q2-vast-attach`, chưa commit.
- **Thesis:** §4 (tự động hoá dựng cluster, VH5: thời gian từ máy trắng); §5 cold start: so 3B trên máy thuê (chụp CUDA graph lúc profiling 2 s) với 0,5B ở nhà (97–100 s), cho thấy độ chậm ở nhà là do môi trường PC; §Hạn chế: máy chợ thiếu CPU so với tiêu chí.

## 2026-11-16 – Hai lượt autoscaling N = 2 trên máy thuê: runner chạy trọn, invalid vì CPU máy tạo tải

- **Task:** Q6 · **Environment:** V2 (phiên thử code, 2 × RTX 4000 Ada)
- **Done:** chạy `matrix-try-n2.yaml` bằng runner từ PC qua tunnel, `--no-backup`: A1 × KB3 (16:03–16:30) rồi A2 × KB2 (16:30–16:58). C = 5,0, threshold A2 = 39, `loadgen_cpu: 500m`.
- **Results:**

  | Lượt | Số replica | Cold start pod mới (tạo → Ready) | Request / lỗi | TTFT p50 / p95 | TTFT ≤ 2,5 s |
  |---|---|---|---|---|---|
  | A1 × KB3 | 1 → 2, không về 1 trong lượt | 69 s | 6.797 / 0 | 0,15 / 0,27 s | 100 % |
  | A2 × KB2 | 1 → 2 → 1 | 66 s | 6.612 / 0 | 0,15 / 12,40 s | 91,0 % (598 request trễ, trong khoảng 2 phút quanh lúc tải tăng) |

  Runner kiểm được tín hiệu scale trước phiên (`nvidia_smi_utilization_gpu_ratio`: 2 chuỗi; `vllm:num_requests_running`: 1 chuỗi), đồng hồ Prometheus lệch +0,3 s.
- **Incidents:** cả hai lượt **invalid**: `máy tạo tải không đạt tự kiểm: send_lag_ok, throttle_ok`. Số đo: `send_lag` p99 51,8 ms và 67,2 ms, max 80 và 150 ms; bị throttle 6,3 % và 2,1 % số chu kỳ; CPU max ≈ 49 % của một lõi (đúng giới hạn 500m). Nguyên nhân: node 11 vCPU, 4 lõi reserved, 2 pod vLLM giữ 6 lõi, máy tạo tải chỉ còn nửa lõi. Không phải lỗi runner.
- **Decision:** không sửa; ghi nhận rằng máy cho phiên chính thức với N = 2 cần ≥ 14 vCPU (8 + 3N), đúng tiêu chí trong `vast.sh query`.
- **Links:** `runs/try-n2-4000ada/` (không nằm trong Git).
- **Thesis:** §Hạn chế hoặc §5 phương pháp: tự kiểm của máy tạo tải bắt được lượt đo bị nhiễu do thiếu CPU; ví dụ cho tiêu chí chọn máy.

## 2026-11-16 – Bốn kịch bản VH trên máy thuê 2 GPU; merge `main` (TR7, LT7) vào nhánh

- **Task:** Q6 (VH), Q2 · **Environment:** cloud thử (2 × RTX 4000 Ada, N = 2, Qwen2.5-3B, A2 threshold 39), không phải V2
- **Done:**
  1. Chạy nối tiếp `python -m experiments.ops.vh <kịch bản> --matrix envs/cloud/experiments/matrix-try-n2.yaml --rate 2.5` cho vh3-delete, vh3-kill, vh4, vh2a (16:59–17:56). Tải 2,5 req/s = một nửa C sơ bộ (5,0), nên A2 giữ 1 pod trong suốt các kịch bản.
  2. Sau khi VH xong mới merge `origin/main` (PR #40 TR7, PR #41 LT7 của Trình) vào nhánh, để code runner không đổi giữa phiên đo.
- **Results:**

  | Kịch bản | Chấm | Request / lỗi | Số đo |
  |---|---|---|---|
  | vh3-delete | **không đạt** | 1.942 / 90 | pod thay thế Ready sau 61,3 s |
  | vh3-kill | đạt | 1.481 / 168 | container restart, Ready lại sau 69,4 s |
  | vh4 | đạt | 1.771 / 0 | chặn Prometheus → KEDA vào fallback sau 17,2 s (lên max 2 pod); mở lại thì tín hiệu về bình thường |
  | vh2a | đạt | 2.948 / 0 | lên 2 pod mất 68,2 s; rolling update 2 pod mất 181,6 s |

  - Test sau merge: `experiments` 150 passed, `analysis` 51 passed.
- **Incidents:**
  - vh3-delete không đạt: tiêu chí là 0 request lỗi, nhưng lúc xoá chỉ có **1 pod** (tải thấp nên A2 không scale lên), nên suốt 61 s không còn pod nào phục vụ → 90 lỗi (ConnectError 36, ConnectTimeout 32, HTTPStatus 21, ReadError 1). Không phải lỗi code; tiêu chí 0 lỗi chỉ có nghĩa khi còn ≥ 1 pod khác đang Ready. Chưa sửa script; lần chạy chính thức cần giữ ≥ 2 pod trước khi xoá (tải cao hơn hoặc `minReplicaCount` 2), hoặc cho script từ chối chạy khi chỉ có 1 pod.
  - vh3-kill có 168 lỗi nhưng vẫn "đạt", vì kịch bản này chỉ chấm việc tự hồi phục, không đòi 0 lỗi. Cùng nguyên nhân: chỉ có 1 pod.
  - vh2a: rolling update 181,6 s ≈ `terminationGracePeriodSeconds` 180 s, khớp với sự cố đã biết (vLLM không dừng khi nhận SIGTERM, ghi 06/11). Với N = 2 thì pod mới phải chờ pod cũ nhả GPU.
  - Merge: xung đột ở `Makefile` (dòng `.PHONY`: mình thêm `attach`, Trình thêm `sim-lt7`; giữ cả hai). `van-hanh.md` Git tự ghép nhưng đặt mục LT4 xuống dưới nhóm LT5–LT8 của Trình; đã chuyển về nhóm LT1–LT4.
- **Decision:** không chạy vh2b, vh2c, vh3-drain ở phiên này: drain cần ≥ 2 node, còn vh2b/vh2c để dành cho máy chính thức.
- **Links:** `runs/ops-vh3-delete-20261116-095917`, `runs/ops-vh3-kill-20261116-101256`, `runs/ops-vh4-20261116-102333`, `runs/ops-vh2a-20261116-103604` (không commit, `runs/` nằm trong `.gitignore`).
- **Thesis:** chương vận hành (VH2–VH4): bảng trên chỉ là số thử trên N = 2, dùng để kiểm script; số chính thức lấy ở phiên V2.

## 2026-11-16 – CI của `main` đỏ sau khi merge PR #44: test loadgen phụ thuộc tốc độ máy

- **Task:** chung (CI), Q4 (loadgen) · **Environment:** none (GitHub Actions)
- **Incidents:** sau khi PR #44 được merge, CI trên `main` đỏ ở `loadgen/tests/test_workers.py::test_two_workers_share_t0_and_write_one_csv`: request 0 tới server giả trễ 148 ms so với `t0_unix + t_sched`, dung sai là 100 ms. CI của chính PR #44 (cùng code) trước đó xanh, và PR #44 không sửa gì trong `loadgen/`, nên đây là test không ổn định, không phải lỗi do PR. Trong log, `t_send` của request 0 chỉ lệch lịch 1 ms: loadgen gửi đúng giờ; phần trễ nằm ở việc mở kết nối TCP đầu tiên và tạo luồng ở server giả trên runner CI.
- **Decision:** nới dung sai lên `START_MARGIN_S / 2` (0,5 s). Phép so này tồn tại để bắt lỗi "một tiến trình tự lấy mốc t0 riêng", khi đó lệch cỡ 1 s, nên 0,5 s vẫn bắt được. Độ đúng lịch (< 50 ms, Môi trường §17) vẫn được kiểm ở dòng `lags` bằng `t_send`. Không chọn cách chạy lại CI cho xanh: test sẽ đỏ lại ngẫu nhiên.
- **Results:** `uv run --project loadgen pytest loadgen` 3 lần liên tiếp: 55 passed. `ruff check`, `ruff format --check` sạch.
- **Links:** `loadgen/tests/test_workers.py`; CI run 43870125040.

## 2026-11-16 – Review PR #39 của Trình (A2 và observability ở nhà); sửa `make home-eval-end`

- **Task:** TR1 (review), chung · **Environment:** home (chỉ đọc và dry-run, không đổi cluster)
- **Done:**
  1. Checkout nhánh PR ở một worktree riêng. `pytest experiments` đạt; `kubectl kustomize envs/home/autoscaling` ra min 1, max 2, fallback 2, threshold 23; `kubectl apply --dry-run=server` lên cluster nhà cho A2 và `common/observability` đều được chấp nhận; `kubectl diff` cho `root-app.yaml`: không lệch.
  2. Merge `main` vào nhánh của Trình (xung đột dòng `.PHONY` với PR #44, giữ cả hai) và đẩy một commit sửa `home-eval-end`.
  3. Cài yq bản mikefarah v4.54.1 vào `~/.local/bin` trên PC nhà, kiểm sha256 giống CI.
- **Incidents:** `make home-eval-end` gọi `yq -o json -I0`, cú pháp của yq bản mikefarah. PC nhà có `yq 3.4.3` bản Python: lệnh in ra rỗng. Target cũ khi đó vẫn xoá ScaledObject khác A2, rồi gửi patch JSON hỏng, nên auto-sync của `autoscaling` không được bật lại sau phiên. Sửa: đọc khối `automated` trước, kiểm là JSON object, sai thì dừng khi chưa đổi gì. Thử cả hai nhánh bằng `kubectl` giả (in lại tham số): yq sai → rc 2, không gọi `kubectl`; yq đúng → gọi đúng hai lệnh `get scaledobject` và `patch`.
- **Decision:** sửa thẳng trên nhánh của Trình thay vì chỉ nhận xét, theo yêu cầu của Quang. Nhật ký này nằm ở PR #45 chứ không ở PR #39, để hai PR không cùng thêm vào cuối một file.
- **Results:** sau merge: `experiments` 157, `loadgen` 55, `analysis` 85 passed.
- **Deviations:** chưa kiểm lại `helm template` với bốn lớp values của nhà. Điểm còn mở: RAM PC nhà khi fallback lên 2 pod (1 pod 3.644 Mi, còn khả dụng khoảng 4 GB, swap đang dùng 2,5 GB).
- **Links:** PR #39, commit `5014d84` (merge), `e83a505` (sửa `home-eval-end`); nhận xét review trên PR #39.

## 2026-11-18 – V2: thuê 4 × RTX 4060 Ti, dựng từ máy trắng 8 phút 22 giây, ĐG1 chính thức C = 3,5, bắt đầu ma trận 17 lượt

- **Task:** Q2, Q6, Q7 · **Environment:** V2 (phiên đo chính thức, N = 4)
- **Done:**
  1. Máy đầu (4 × RTX 4090, 1,5 USD/giờ theo Quang báo) không lên SSH: cổng timeout ở 5 lần thử trong khoảng 15 phút, trong khi mạng của máy dev vẫn thông (`github.com:22` mở được).
  2. Máy thứ hai: `make attach` → `make probe` → `make bootstrap` → `make cloud-platform` → `vast.sh tunnel` (chạy nền) → chờ vLLM Ready.
  3. Viết `matrix-dg1-v2.yaml` (session `dg1-v2-4060ti`, λ = 2, 3, 4, 5, rồi thêm 3,5), chạy runner từ PC qua tunnel với `--no-backup`, tính `capacity.py`.
  4. Điền khối `x-adr003` của `matrix-v2.yaml` (C = 3,5, threshold A2 = 37). `--dry-run`: 17 lượt.
  5. Chép repo lên VM bằng rsync (bỏ `runs/`, `.env`, `.vast/`), `chown -R root` (git trên VM từ chối repo của uid khác: "dubious ownership"), chạy runner trong tmux trên VM với `--no-backup`, log vào `runs/v2-dg2-console.log`. Một vòng lặp trên PC kéo `runs/` của VM về `runs/v2-vm/` mỗi 30 phút.
- **Decision:**
  - Dùng 4 × RTX 4060 Ti 16 GB thay cho 4 × A4000 của ADR-006 C2: hôm đó không có máy A4000, máy 4090 không lên SSH, còn máy này đạt mọi tiêu chí khác và vượt xa về CPU, mạng, đĩa. Quang chọn "dùng, bootstrap ngay".
  - Chạy runner trên VM trong tmux thay cho systemd + R2: PC chưa có `.env`, nên `runner-start` sẽ dừng vì thiếu `R2_REMOTE`. Chạy trên VM để ma trận 8 giờ không phụ thuộc tunnel; dữ liệu có bản thứ hai trên PC nhờ kéo định kỳ. Bỏ phương án chạy từ PC qua tunnel (tunnel đứt là hỏng lượt).
- **Results:**
  - `probe`: 4 × RTX 4060 Ti 16 GB, driver 580.95.05, CUDA 13.0; 61 vCPU (EPYC 7713), RAM 197 GB, đĩa 120 GB trống; Hugging Face 222,3 MB/s; ghi đĩa tuần tự 972 MB/s; Docker Hub thông; vị trí Canada; không có unattended-upgrades.
  - `bootstrap` từ máy trắng: **5 phút 8 giây** (`real 5m8.294s`), 38 ok, 16 changed, 0 failed. `cloud-platform`: **82 s**, node báo 4 GPU, 57 CPU cấp phát được. vLLM 3B: pod tạo 08:49:00Z, Ready 08:50:30Z (**90 s**). Từ đầu `bootstrap` (15:42:08) tới vLLM Ready (15:50:30): **8 phút 22 giây** (16/11 trên 2 × RTX 4000 Ada: 12 phút 54 giây). Số này đo bằng tay, chưa phải `make vh5`.
  - ĐG1 (S1, CONST, 300 s mỗi mức, cả 5 lượt hợp lệ):

    | λ (req/s) | Đạt SLO | TTFT p95 | TPOT p95 | B server (Little) | waiting |
    |---|---|---|---|---|---|
    | 2 | 100 % | 0,314 s | 36,4 ms | 16,4 (16,5) | 0 |
    | 3 | 100 % | 0,454 s | 51,7 ms | 32,7 (32,5) | 0 |
    | 3,5 | 100 % | 1,216 s | 61,3 ms | 46,3 (46,4) | 0,4 |
    | 4 | 28,5 % | 7,321 s | 64,5 ms | 75,9 (79,0) | 12,4 |
    | 5 | 0 % | 69,7 s | 64,3 ms | 232 (291,8) | 168,4 |

    `capacity.py`: **C = 3,5 req/s, B\* = 46,3, threshold A2 = 37**, A3 KV = 0,14. Dự đoán trước khi đo: 3–4 req/s (băng thông bộ nhớ 288 so với 448 GB/s của A4000); tỉ lệ băng thông thuần cho 4,5 × 288/448 ≈ 2,9, đo được cao hơn.
  - Giá thuê: 1,5 USD/giờ cả máy (Quang báo theo trang Vast); ĐG1 + ma trận ước khoảng 9–10 giờ ≈ 14–15 USD.
  - Runner trên VM: đồng hồ Prometheus lệch +0,1 s; `nvidia_smi_utilization_gpu_ratio` 4 chuỗi, `vllm:num_requests_running` 1 chuỗi; lượt đầu A1-KB3-1 bắt đầu 16:30 (giờ VN). Kết quả ma trận: chưa có.
- **Incidents:** git trên VM báo "dubious ownership" vì rsync giữ uid của máy dev → `chown -R root:root /opt/llm-v2`.
- **Deviations:** GPU 4060 Ti thay cho A4000 (ADR-006 C2); runner chạy trong tmux trên VM với `--no-backup` thay cho systemd + R2; code trên VM là commit `10c0527` cộng hai file ma trận chưa commit, nên `metadata.json` ghi commit `10c0527` dù tree đang dirty. Chưa có ADR-003.
- **Links:** `envs/cloud/experiments/matrix-dg1-v2.yaml` (mới), `envs/cloud/experiments/matrix-v2.yaml` (khối `x-adr003`); `runs/dg1-v2-4060ti/`, `runs/v2-vm/` (không nằm trong Git). Bằng chứng phiên: `runs/v2-evidence/` (log Ansible và runner ghi trực tiếp; output `probe`, `cloud-platform` chép lại từ terminal, có ghi chú; `vm-identity.txt` với UUID 4 GPU và `systemd-detect-virt` = kvm; sha256 ma trận trên VM trùng bản trên PC; `SHA256SUMS` 125 file lúc 16:35).
- **Thesis:** §5 năng lực (bảng ĐG1, C = 3,5); LT1 (C theo băng thông bộ nhớ, so A4000 4,5 và 4060 Ti 3,5); LT5 phần V2 (B đo và B Little lệch < 1 % khi chưa quá tải); §4 VH5 (8 phút 22 giây từ máy trắng); §Hạn chế (card 4060 Ti thay cho A4000, không sao lưu R2 trong phiên).

## 2026-11-18 – V2: ma trận ĐG2 17/17 lượt hợp lệ, số tổng hợp đầu tiên

- **Task:** Q6, TR7 (bảng) · **Environment:** V2 (VM 4 × RTX 4060 Ti, N = 4, C = 3,5, threshold A2 = 37)
- **Done:**
  1. Runner trong tmux trên VM chạy `matrix-v2.yaml` từ 16:30 tới 23:44 (+07), 17 lượt theo thứ tự xáo của seed 20261114, không cần can thiệp.
  2. Kiểm mỗi giờ bằng lịch hẹn của phiên Claude; phiên khởi động lại lúc khoảng 23:15 làm mất lịch hẹn, vòng kéo `runs/` và tunnel (runner trên VM không bị ảnh hưởng). Vòng chờ thay thế đầu tiên lỗi vì zsh không tách biến `$S` thành lệnh, chạy lại bằng `bash -c`.
  3. Kéo `runs/` về `runs/v2-vm/`, chép console runner vào `runs/v2-evidence/console/05-matrix-runner-console.log`, tính lại `SHA256SUMS` (525 file).
  4. `analysis.build_tables runs/v2-vm/v2-dg2 --baseline S4` → `runs/v2-vm/v2-dg2/tables/` (17 lần thử, 11 ô).
- **Results:** 17/17 lượt `valid: true`, mỗi lượt khoảng 24 phút (tổng 7 giờ 14 phút). Trung bình theo ô (GPU-giờ so với S4 cùng kịch bản):

  | Ô | Số lượt | SLO đạt | TTFT p95 | Lỗi | GPU-giờ | so với S4 |
  |---|---|---|---|---|---|---|
  | S4 × KB1 / KB2 / KB3 | 1 / 1 / 1 | 100 % cả ba | 0,22 / 0,38 / 0,40 s | 0 | 0,80 / 1,60 / 1,13 | – |
  | S1 × KB2 / KB3 | 1 / 1 | 12,5 % / 0 % | 93,1 s / – | 5.659 / 8.008 | 0,40 / 0,28 | – |
  | A1 × KB1 | 2 | 100 % | 0,23 s | 0 | 0,72 | −10 % |
  | A1 × KB2 | 2 | 100 % | 0,39 s | 0 | 1,52 | −5 % |
  | A1 × KB3 | 1 | 100 % | 0,40 s | 0 | 1,05 | −7 % |
  | A2 × KB1 | 2 | 100 % | 0,32 s | 0 | 0,20 | −75 % |
  | A2 × KB2 | 3 | 79,4–80,7 % | 73–79 s | 37 / 82 / 93 | 1,15–1,20 | −25 đến −28 % |
  | A2 × KB3 | 2 | 100 % | 0,40 s | 0 | 1,04 | −8 % |

  - A2 × KB2: thời gian phản ứng 80–82 s, hồi phục 409–430 s, mỗi lượt 1 page cảnh báo (0 page giả). Ba lượt lặp cho số rất gần nhau.
  - A1 lên 4 replica ở cả KB1 (tải 0,5 C), nên tiết kiệm GPU chỉ 5–10 %: khớp LT6 (GPU utilization không phân biệt được tải vừa với quá tải).
  - Đây là số đọc thẳng từ `build_tables`, **chưa phân tích nguyên nhân** của lỗi và TTFT cao ở A2 × KB2 (giả thuyết: spike vượt năng lực trước khi pod mới Ready, cold start khoảng 60–90 s; chưa kiểm).
- **Incidents:** mất lịch hẹn và tunnel khi phiên Claude khởi động lại (xem bước 2); lỗi zsh word splitting ở vòng chờ.
- **Links:** `runs/v2-vm/v2-dg2/` (không nằm trong Git), `runs/v2-vm/v2-dg2/tables/cells.csv`, `runs/v2-evidence/SHA256SUMS`.
- **Thesis:** §5.3 (bảng ĐG2, biểu đồ C1–C4 vẽ lại trên `runs/v2-vm/v2-dg2`); §5 đóng góp 2 (A2 so với A1); LT6 phần V2 (A1 lên max ở tải thấp); §Hạn chế (A2 không đạt SLO dưới spike KB2).

## 2026-11-18 – V2: chạy VH2–VH4 trên N = 4, viết `dg3.sh` cho cold start L0/L2

- **Task:** Q4, Q5 · **Environment:** V2 (cùng VM 4 × RTX 4060 Ti)
- **Done:**
  1. Lấy `experiments/ops/vh.py` từ nhánh PR #46 (`fix/vh3-delete-needs-two-pods`, chưa merge) đặt lên VM; sha256 trên VM trùng bản của nhánh (`runs/v2-evidence/config/vh.py-pr46`, `pr46-commit.txt`).
  2. Chạy trong tmux `vh` trên VM, từ 23:46 (+07): vh2a, vh2b, vh2c, vh3-delete, vh3-kill, vh4, mỗi kịch bản `--matrix envs/cloud/experiments/matrix-v2.yaml --rate 1.75` (0,5 C), console tee ra `runs/ops-console-<s>.log`.
  3. Viết `envs/cloud/provision/dg3.sh`: một lần đo cold start ở L0 hoặc L2, ghi `pod.json`, `events.json`, `vllm.log` (có mốc kubelet), `vllm_log.json`, danh sách image và dung lượng cache trước/sau, `summary.txt`, và toàn bộ console. Kiểm `bash -n`; sha256 trên VM trùng bản trên PC.
  4. Xếp tmux `dg3` tự chạy sau khi `vh` xong: xoá ScaledObject còn lại, rồi L2 × 3, L0 × 2.
- **Decision:** L0 đo **0 → 1** thay vì 1 → 2 như Môi trường §12, vì containerd không cho xoá image đang có container dùng; L2 đo đúng 1 → 2. Chạy L2 trước (compile cache còn ấm sau cả ngày chạy ma trận), L0 sau, vì L0 xoá cache.
- **Results:** chưa có (đang chạy).
- **Deviations:** L0 0 → 1 (lý do ở trên); `vh.py` là bản của PR #46 chưa merge. 00:30 ngày 19/11 (trước khi vh2c bắt đầu): hạ thời lượng tải của vh2c từ 3000 s xuống 1200 s trên VM, vì rollout 4 pod ở vh2b chỉ mất 371,6 s (mặc định đặt theo ước tính khoảng 20 phút trên A4000); vh2c cần khoảng 60 s nền + 300 s chờ kẹt + khoảng 6–7 phút khôi phục. Diff ở `runs/v2-evidence/config/vh.py-vh2c-duration.diff`.
- **Links:** `envs/cloud/provision/dg3.sh` (mới), PR #46; dữ liệu `runs/v2-vm/ops-*`, `runs/v2-vm/dg3-v2-4060ti/` sau khi kéo về.
- **Thesis:** §5.4 cold start (C5, N5); chương vận hành VH2–VH4 trên N = 4.

## 2026-11-19 – V2: tự tắt VM sau khi kéo dữ liệu (Quang đi ngủ)

- **Task:** Q7 (chi phí) · **Environment:** V2
- **Decision:** Quang đồng ý (00:45) cho tắt VM bằng `poweroff` từ bên trong ngay khi VH và ĐG3 xong, để ngừng tính tiền GPU qua đêm; máy thuê qua web nên không có API key để `vast.sh release`. Điều kiện tắt: kéo `runs/` của VM về `runs/v2-vm/` và sha256 của **mọi file** trên PC trùng bản trên VM (thử tối đa 3 lần; lệch thì không tắt). Hạn cứng 04:30: nếu VH/ĐG3 còn chạy (nghi treo) thì vẫn kéo dữ liệu, kiểm checksum rồi tắt. Trước khi tắt lưu trạng thái cuối (`kubectl get pods -A`, `nvidia-smi`, `tmux ls`) vào `runs/v2-evidence/vm-final-state.txt` và danh sách sha256 trên VM vào `vm-runs-sha256-before-poweroff.txt`.
- **Results:** chưa có (chờ VH, ĐG3).
- **Links:** `runs/v2-evidence/`.

## 2026-11-19 – V2: VH 6/6 đạt; ĐG3 hỏng 3/5 lượt do lỗi `dg3.sh`, đo lại; báo động nhầm lúc 01:54

- **Task:** Q4, Q5, Q7 · **Environment:** V2 (VM 4 × RTX 4060 Ti)
- **Results:**
  - VH (tải 1,75 req/s, `matrix-v2.yaml`), mọi kịch bản rc = 0: vh2a (23:46–00:07), vh2b (rollout 4 pod `maxSurge: 0` trong 371,6 s), vh2c (thời lượng 1200 s), vh3-delete (2 pod Ready trước khi xoá nhờ bản sửa PR #46, pod thay thế Ready sau 67,4 s, đạt 0 lỗi; lần thử 16/11 trên N = 2 không đạt), vh3-kill, vh4 (chặn rồi gỡ chặn KEDA → Prometheus, tín hiệu về `ok`). Số chi tiết trong `runs/v2-vm/ops-vh*/summary.json`: chưa đọc hết.
  - ĐG3 lượt đúng: **L2-2: 76 s** từ lệnh scale tới pod Ready (image có sẵn); **L0-2: 300 s** (kéo lại image 9.035.266.183 byte mất 2 phút 34 giây, tải lại model, compile cache nguội).
- **Incidents:**
  1. L2-1, L2-3, L0-1 dừng vài giây sau `kubectl scale`: hàm `wait_count` của `dg3.sh` kết thúc vòng lặp bằng `[ $t -gt 900 ] && { … }`; điều kiện sai trả 1, nên hàm trả 1 và `set -e` dừng script mỗi khi phải chờ ít nhất một vòng. L2-2 và L0-2 không phải chờ nên chạy đúng. Sửa: `if … fi` và `return 0`. Thư mục hỏng đổi tên thành `<lượt>-failed-wait-count-bug` (giữ làm bằng chứng), đo lại 3 lượt từ 01:55 trong tmux `dg3b`. Lượt L2 đo lại chạy sau L0-2, tức compile cache được tạo lại bởi pod của L0-2.
  2. 01:54: bước kiểm trước khi tắt VM báo checksum lệch ở cả 3 lần, nên không tắt VM và chuông báo động trên PC kêu, đánh thức Quang. Nguyên nhân: so hai danh sách bằng `diff` nên lệch do thứ tự `sort` giữa hai máy và do `runs/v2-vm/v2-dg2/tables/` chỉ có trên PC; thực tế 474/474 file trên VM có trên PC với cùng sha256 (`comm -23` sau `sort`: 0 dòng thiếu). Sửa: so bằng `comm -23` sau `LC_ALL=C sort`, chỉ đòi mọi file của VM có trên PC.
- **Decision:** sau khi đo lại xong và kiểm đúng, tự `poweroff` VM rồi tắt PC sau 10 phút (Quang đồng ý); chuông chỉ kêu khi VM vẫn trả lời SSH sau poweroff hoặc dữ liệu thiếu.
- **Links:** `envs/cloud/provision/dg3.sh`, `runs/v2-evidence/config/dg3.sh-fixed`, `runs/v2-vm/dg3-v2-4060ti/`.
- **Thesis:** §5.4 cold start (L2 76 s so với L0 300 s; phần kéo image 154 s); chương vận hành VH2–VH4 trên N = 4; §Hạn chế (L0 đo 0 → 1).

## 2026-11-19 – V2: ĐG3 đo lại xong, VM đã tắt; phân tích lỗi A2 × KB2 và vh3-kill; xoá VM

- **Task:** Q4, Q5, Q6, Q7 · **Environment:** V2 (dữ liệu trên PC), none (phân tích)
- **Done:**
  1. Đo lại 3 lượt ĐG3 hỏng (tmux `dg3b`, 01:55–02:04 +07). Kiểm trước khi tắt đạt: mọi file của VM có trên PC với cùng sha256. Lưu `runs/v2-evidence/vm-final-state.txt`, `vm-runs-sha256-before-poweroff.txt`; VM nhận `poweroff` lúc 19:05:02Z (02:05 +07).
  2. Đọc `summary.json` của 6 kịch bản VH và bảng `phases.csv`, `alerts.csv`, `metrics.csv.gz` của ĐG2 để xem lỗi A2 × KB2 nằm ở đâu.
  3. Quang xoá instance trên Vast (thao tác qua web) sau khi kết luận không cần đo thêm.
- **Decision:** không giữ VM để đo thêm. Mọi phép đo trên GPU thuê của kế hoạch đã có dữ liệu (ĐG1, ĐG2 17/17, ĐG3 L0 × 2 + L2 × 3, VH2–VH4). Lỗi ở A2 × KB2 là hạn chế của thiết kế (xem Results), không phải lỗi cần sửa rồi chạy lại; thử cấu hình mới (routing theo hàng đợi, sửa vh3-kill) là thêm phạm vi khi còn 3 ngày tới mốc đóng băng 22/11. Giữ VM cũng không giúp gì cho ĐG1 nếu cần máy khác, vì C = 3,5 gắn với chính máy này.
- **Results:**
  - ĐG3 (từ lệnh scale tới pod Ready, `summary.txt` từng lượt): **L2 = 76 / 76 / 81 s** (trung bình 77,7 s); **L0 = 311 / 300 s** (kéo image 9.035.266.183 byte mất 2 phút 36 giây / 2 phút 34 giây). Ba lượt L2 đo sau L0-2 nên compile cache do pod của L0-2 tạo lại.
  - A2 × KB2, cả 37 / 82 / 93 lỗi đều là `Timeout`, đều ở pha `spike`, gửi trong khoảng 60–120 s đầu của spike. Pha `drop` của 5 lượt A1/A2 × KB2: **0 lỗi, SLO 100 %** → N4 (scale-down) đạt.
  - Nguyên nhân SLO spike chỉ khoảng 75 %: pod có sẵn (`7krwm`) có hàng đợi vLLM tối đa **416 / 425 / 428** request, kéo dài khoảng 385–390 s; ba pod mới có tối đa 0–9 request chờ. Hàng đợi đã nằm trong vLLM của pod cũ thì không chuyển sang pod mới, còn Service vẫn chia đều request mới nên khoảng 1/4 request tiếp tục xếp sau hàng đợi đó. Ở S4 × KB2, 4 pod có 0 request chờ suốt lượt.
  - Chỉ tiêu: N1 (A2 KB1, KB3 SLO 100 %) đạt; N2a (phản ứng 80–82 s ≤ 2 phút) đạt; N3 KB1 (A2 dùng 25 % GPU-giờ của S4, SLO kém 0 điểm) đạt; N2b hồi phục 409–430 s (dự kiến ≤ 5 phút, chỉ báo cáo).
  - VH: vh2a rollout 141,4 s (từ 1 replica), vh2b 371,6 s, vh2c kẹt có pod Pending đúng như dự đoán, vh3-delete thay pod 67,4 s 0 lỗi, vh4 fallback **16,8 s** (N6 ≤ 30 s), cả 5 kịch bản 0 lỗi.
  - vh3-kill: container restart, Ready lại sau 67,4 s, nhưng 129 lỗi / 1.041 request (ConnectError 70, ConnectTimeout 47, StreamError 11, HTTPStatus 1). 117 lỗi kết nối ≈ 67,4 s × 1,75 req/s, nên khả năng cao lúc kill chỉ có 1 pod (tải 0,5 C, A2 giữ 1 replica): cả cluster không có pod phục vụ trong 67 s. Suy luận này chưa kiểm bằng số pod lúc kill (console không in); `vh3_kill` trong PR #46 chưa có bước bảo đảm 2 pod như `vh3_delete`.
  - Chi phí thực tế: chưa có (chờ Quang đọc trang Billing của Vast).
- **Incidents:** suốt mọi lượt ĐG2 có `AlertmanagerFailedToSendAlerts` firing từ trước khi bắt đầu (Alertmanager không gửi được tới receiver); không ảnh hưởng `LLMSLOBurnFast` (đọc từ `ALERTS` của Prometheus), chưa tìm nguyên nhân.
- **Deviations:** vh3-kill chạy khi (có lẽ) chỉ 1 pod, khác ý của VH3 ("chỉ lỗi các request đang chạy trên pod đó").
- **Links:** `runs/v2-vm/dg3-v2-4060ti/*/summary.txt`, `runs/v2-vm/ops-vh*/summary.json`, `runs/v2-vm/v2-dg2/tables/`; báo cáo tổng hợp V2 (Artifact, link trong phiên Claude).
- **Thesis:** §5.3 (A2 × KB2: hàng đợi kẹt ở pod cũ, hình hàng đợi theo pod), §5.4 cold start (L2 77,7 s, L0 305,5 s), §Hạn chế (load balancing không biết hàng đợi; vh3-kill 1 pod), chương vận hành (VH2–VH4 trên N = 4).

## 2026-11-20 – Rà tiến độ sau V2, đẩy dữ liệu V2 cho Trình, file nguồn tư liệu luận văn

- **Task:** Q6, chung (luận văn) · **Environment:** none
- **Done:**
  1. Rà tiến độ theo Kế hoạch §3: M1 7/7; M2 còn T6, T7, bảo mật, Telegram, VH6 ở nhà; M3 đã có dữ liệu ĐG1, ĐG2, ĐG3, VH2–VH4 nhưng còn thiếu ADR-003, bảng nghiệm thu, chi phí thực tế, bản sao lưu thứ hai; M4 mới có bản nháp 3.4 của Trình.
  2. Merge `origin/main` (PR #50, #51) vào `feat/v2-results-1911`, không conflict. Nhánh trước đó có 4 commit chưa push.
  3. Chép `runs/dg1-v2-4060ti/capacity.json` vào `envs/cloud/experiments/capacity.json`; chỉ đặt `status` = `v2-official` và `note`, mọi trường số giữ nguyên (so bằng script: chỉ 2 khoá khác).
  4. Kiểm `runs/v2-evidence/SHA256SUMS`: 638/639 khớp; file lệch là `vm-final-state.txt`, ghi lúc 02:05:02, sau khi lập danh sách lúc 02:04:59 ngày 19/11, nên không phải hỏng dữ liệu.
  5. Nén `runs/dg1-v2-4060ti`, `runs/v2-vm`, `runs/v2-evidence` thành `runs/_share/v2-data-20261119.tar.gz` (9.975.434 byte, 835 mục) kèm file `.sha256`, để Quang gửi Trình.
  6. Chạy thử `analysis.charts runs/v2-vm/v2-dg2` (ra thư mục tạm): ra 6 hình C1 (3 lượt KB2), C2, C3, C4, không lỗi. Chưa xem bố cục, chưa commit (việc của TR7).
  7. Viết `docs/luan-van/nguon-tu-lieu.md`: bản đồ nguồn, nguồn cho từng mục luận văn theo §5.1, bảng số liệu đã chốt kèm nơi gốc, danh sách chưa có số, cách lấy dữ liệu V2, các hạn chế đã biết, link 12 trang artifact.
- **Decision:** gửi dữ liệu V2 cho Trình bằng file nén thay vì commit vào Git (`runs/` bị gitignore, 36 MB) hay R2 (PC chưa có `.env`). Không commit hình C1–C4: thuộc TR7, Trình xem bố cục rồi commit.
- **Incidents:** CI của PR #52 không chạy: cả 6 job dừng sau 1–2 s với "account is locked due to a billing issue" (tài khoản GitHub `bi6-cat`), nên lychee và pytest chưa chạy trên PR. Các trang artifact mặc định chỉ Quang xem được; Trình chỉ mở được sau khi Quang bấm Share. Repo công khai, nên không chia sẻ kiểu ai có link cũng xem.
- **Links:** PR #52 (nhánh `feat/v2-results-1911`, reviewer Trình); `envs/cloud/experiments/capacity.json`, `docs/luan-van/nguon-tu-lieu.md`, `docs/luan-van/README.md`.
- **Thesis:** dùng cho mọi chương (file nguồn); §5.2 (`capacity.json` trong Git).

## 2026-11-20 – Sửa 2 test Python đỏ trên PR #52; quy tắc viết luận văn chung

- **Task:** Q6, chung (luận văn) · **Environment:** none
- **Done:**
  1. Sau khi tài khoản GitHub hết bị khoá, CI của PR #52 chạy: 4 job đạt, `python (3.11)` và `python (3.15)` đỏ ở 2 test trong `experiments/tests/test_runner.py`. Nguyên nhân: hai test giả định `matrix-v2.yaml` còn để `null` (bản nháp chờ ADR-003), còn commit `a44ae71` đã điền C = 3,5 và threshold 37. Sửa: test "từ chối khi chưa điền" dựng lại bản nháp bằng cách thay hai số về `null`; test cấu trúc kiểm file thật và so C, threshold với `envs/cloud/experiments/capacity.json` thay cho số giả 5 và 24. `pytest experiments`: 168 passed trên Python mặc định và 3.11; `ruff check`, `ruff format --check` đạt. Sửa trong worktree riêng vì thư mục làm việc chính đang ở `main`.
  2. Viết `docs/luan-van/quy-tac-viet.md`: thứ tự ưu tiên (khuôn trường > README > file này), vai trò từng chương, khung 6 bước cho chương 4 (tránh R21), văn phong và ba mức chắc chắn, bảng thuật ngữ và tên gọi thống nhất, quy tắc số liệu và nhãn nguồn gốc, hình/bảng/mã, trích dẫn, phối hợp và review, dùng AI agent, checklist trước PR. Thêm dòng vào bảng file của README.
- **Decision:** phần định dạng (phông, lề, giãn dòng) để trống chờ khuôn của trường, không tự đặt số; chỉ ghi các thông lệ không phụ thuộc khuôn.
- **Links:** PR #52; `experiments/tests/test_runner.py`, `docs/luan-van/quy-tac-viet.md`, `docs/luan-van/README.md`.
- **Thesis:** quy tắc chung cho mọi chương.

## 2026-11-20 – Khung luận văn trên Google Docs

- **Task:** chung (luận văn) · **Environment:** none
- **Done:**
  1. Đề xuất khung luận văn (trang artifact riêng tư): 6 chương, đầu quyển, phụ lục; mỗi mục có người viết, số trang, trạng thái tư liệu, nguồn. Tổng đề xuất khoảng 60 trang thân bài (Quang khoảng 31, Trình khoảng 29). Quang đồng ý 5 điểm chốt: LT1–LT8 thành mục 5.6 (5.6a Quang, 5.6b Trình); chủ chương viết mở đầu và kết chương (chương 1, 2, 4 Quang; 3, 5, 6 Trình); 5.8 Trình, 5.9 Quang; đầu quyển và danh mục chữ viết tắt Trình; danh mục tài liệu đứng trước phụ lục.
  2. Theo yêu cầu của Quang, thêm mục 4.12 "Tổng hợp khó khăn và cách vượt qua" và phần khó khăn trong từng mục chương 4. Bảng tư liệu 14 dòng lọc từ `van-hanh.md` và nhật ký tuần 05–07 (triệu chứng, nguyên nhân, cách vượt qua, bài học, nguồn); giả thuyết chưa kiểm ghi rõ "chưa kiểm".
  3. Tạo thư mục Drive "Luận văn vLLM autoscaling" và một Google Doc khung cho cả quyển (tạo từ HTML: chương là Heading 1, mục là Heading 2). Mỗi mục: ghi chú xám (người viết, trang, trạng thái, câu hỏi phải trả lời, nguồn) và dòng [Chưa viết]. Đọc lại doc sau khi tạo: đủ mọi mục và bảng.
- **Decision:** Quang chọn viết trên Google Docs để hai người sửa chung, thay cho Markdown trong `docs/luan-van/` + pandoc (D70 của Trình, 18/11). Một doc cho cả quyển để mục lục và dẫn chéo tự động. Nguồn của số liệu ghi bằng chữ xám "[nguồn: …]" sau đoạn, xoá trước khi nộp; góp ý mục của người kia bằng Comment/Suggesting. `quy-tac-viet.md` và `nguon-tu-lieu.md` vẫn ở repo. Cần Trình đồng ý, sau đó sửa README của `docs/luan-van/` cho khớp; mục 3.4 (Markdown, đã merge) Trình chép sang doc.
- **Deviations:** lệch D70 và README `docs/luan-van/` (Markdown mỗi mục một file). Doc chưa chia sẻ cho Trình (cần email của Trình).
- **Links:** PR #52; Google Doc trong thư mục Drive của Quang (không ghi link vào repo công khai).
- **Thesis:** khung cho mọi chương; 4.12.
