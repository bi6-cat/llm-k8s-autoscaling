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
