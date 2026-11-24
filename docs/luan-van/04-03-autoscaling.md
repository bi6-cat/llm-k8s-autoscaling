<!-- Mục đích: mục 4.3 của luận văn, triển khai autoscaling (HG1), bản base lượt 1. Người viết: Trình. Nháp ngày 24/11/2026 từ nhật ký Trình tuần 04 (01/11: simulator, T1–T5, keep-alive), tuần 05 (07/11: timeout 1 s), tuần 06 và nhật ký Quang tuần 06 (09/11: sửa truy vấn A1), nhật ký Quang tuần 05 (04/11: vòng autoscaling đầu tiên trên kind), Kiến trúc §13–§15, Kiến thức nền §9 (vì sao KEDA), mã common/autoscaling/, envs/*/autoscaling/, envs/sim/; Trình chưa đọc lại. Quy ước: docs/luan-van/README.md, docs/luan-van/quy-tac-viet.md -->
<!-- Thông điệp: (1) autoscaling được dựng và kiểm trọn trên simulator trước khi dùng GPU thuê: năm bài T1–T5 tự chấm, đạt cả năm; (2) đường fallback chỉ đáng tin khi chính cách gây sự cố đã được kiểm: hai lỗi (kết nối keep-alive, timeout 3 s) làm T4 trượt và được sửa trước phiên đo V2; (3) GPU utilization phải làm mượt mới dùng được làm tín hiệu đối chứng. -->
<!-- Ngân sách (D99): 3 trang. Số bảng tạm theo mục (Bảng 4.3a), đánh lại khi ghép chương. Ý không đưa vào, để chỗ khác: tách trễ phản ứng theo chặng của LT7 (tải tới → HPA đổi replica 3,61–10,21 s, 7 lượt, trên simulator; nhật ký Trình tuần 07 mục 16/11) để bảng LT ở 5.6 hoặc Phụ lục E; kiểm tín hiệu scale trong runner (signal_gap, tiêu chí hợp lệ 5) để 4.7; tắt auto-sync của Argo CD và ignoreDifferences cho replicas trong đợt đánh giá để 4.1; cảnh báo KedaScalerErrors để 4.6; sự cố tải đi qua kubectl port-forward ở lượt thử đầu trên kind (357 request vào một pod dù HPA đã lên 3 replica, TTFT p50 47 s, 5 timeout; nhật ký Quang tuần 05 mục 04/11) để 4.7, vì cách sửa là chạy máy tạo tải trong cluster; đồng hồ của VM WSL2 chạy nhanh 1,6% làm T3 có lần đo 292 s, sửa bằng đồng hồ đơn điệu (nhật ký Trình tuần 05 mục 07/11; bỏ vì là sự cố của công cụ thử, không của hệ thống); T6 (chuyển A2 → A1 ở nhà) và T7 (A4 dưới tải) chưa chạy, cơ chế của T6 (đổi cấu hình thì chỉ còn một HPA) đã thấy trên kind (nhật ký Trình tuần 05 mục 07/11). -->
<!-- Soát số: chưa · Soát văn phong: chưa · Người viết đọc lại: chưa -->

## 4.3. Autoscaling

Autoscaling được triển khai bằng một ScaledObject của KEDA dùng chung cho simulator, máy nhà và VM thuê. Mỗi môi trường chỉ đổi số replica tối đa (kèm số replica khi fallback) và threshold. Phần khó không nằm ở manifest mà ở việc kiểm được nó trước khi thuê GPU, nhất là đường fallback khi mất tín hiệu. Số đo trên GPU thật được trình bày ở mục 5.3 và 5.5.

### 4.3.1. Vấn đề và lựa chọn

HPA của Kubernetes chỉ đọc sẵn CPU và bộ nhớ, còn tín hiệu của A2 nằm trong Prometheus (mục 3.3). Mỗi giờ của VM 4 GPU đều tốn tiền, nên một lỗi cấu hình chỉ lộ ra trên VM là lỗi đắt. Máy nhà chỉ có một card, chia thành 2 GPU replica bằng time-slicing (mục 4.2), nên không thử được hành vi 3–4 replica. Fallback lại chỉ chạy khi có sự cố, nên nhóm phải gây được sự cố một cách lặp lại.

<!-- nguồn: Kiến thức nền §3 (thuật toán HPA, nguồn metric); envs/cloud/experiments/matrix-v2.yaml (N = 4); ADR-004 K3 (máy nhà chỉ là môi trường chức năng) -->

Nhóm cân nhắc KEDA và prometheus-adapter, vì cả hai đều cấp external metric cho HPA. KEDA được chọn vì một ScaledObject gom truy vấn, threshold và tham số hành vi vào một chỗ, và có sẵn fallback cùng annotation tạm dừng `paused-replicas` [@keda-scaledobject-spec]. Runner dùng annotation này để đặt lại số replica giữa các lượt (mục 4.7), còn đánh đổi là thêm một thành phần cần giám sát (mục 4.6).

Để phát triển mà không cần GPU, nhóm chạy simulator llm-d-inference-sim trên cluster kind 3 node. Simulator trả lời theo API của vLLM và xuất metric cùng tên, với độ trễ giả 200 ms cho token đầu và 50 ms cho mỗi token sau. Vì độ trễ là giả, simulator không cho số hiệu năng, mà chỉ kiểm đường đi từ metric qua KEDA, HPA tới Deployment.

<!-- nguồn: envs/sim/serving/patch-sim.yaml (--time-to-first-token=200ms, --inter-token-latency=50ms, --max-num-seqs=16); envs/sim/kind-config.yaml (3 node); image llm-d-inference-sim v0.12.0 (docs/phien-ban.md) -->

### 4.3.2. Cách làm

Manifest gốc của A2 nằm ở `common/autoscaling/a2/` (Phụ lục A). Trên simulator, overlay đặt tối đa 3 replica vì kind có 3 node, và threshold 10 để bài thử tính tay được. Máy nhà dùng 2 replica và threshold 23, bằng 0,8 B\* đo với model 0,5B. Trên VM thuê, runner đặt threshold 37 (0,8 × 46,3) và tối đa 4 replica theo ma trận đánh giá (mục 5.2).

<!-- nguồn: envs/sim/autoscaling/kustomization.yaml (max 3, threshold 10); envs/home/autoscaling/kustomization.yaml (max 2, threshold 23 = 0,8 × 28,4, ĐG1-mini 06/11 với Qwen2.5-0.5B); common/autoscaling/eval/ (A1, chỉ runner áp); envs/cloud/experiments/matrix-v2.yaml (A2_threshold 37 = 0,8 × 46,3, overrides threshold và max_replicas) -->

Chu kỳ scrape của Prometheus và chu kỳ sync của HPA cùng được đặt 5 s. Chu kỳ sync là cờ của kube-controller-manager, nên phải đặt lúc dựng cluster, trong cấu hình kind và trong template k3s của Ansible (mục 4.1). KEDA truy vấn Prometheus mỗi khi HPA hỏi, không theo `pollingInterval` (mục 2.4). Tắt keep-alive và timeout 1 s là hai tham số được thêm sau khi thử (mục 4.3.4).

<!-- nguồn: envs/sim/kind-config.yaml và ansible/roles/k3s-server/templates/config.yaml.j2 (horizontal-pod-autoscaler-sync-period=5s); common/autoscaling/a2/scaledobject-a2.yaml (pollingInterval 5, timeout 1000); nhật ký Quang tuần 05 mục 04/11 (cảnh báo pollingInterval của KEDA khi áp A2) -->

Năm bài thử T1–T5 của thiết kế được viết thành script `run-t1-t5.sh`, chạy bằng `make sim-test` và tự chấm đạt hay trượt. Script đọc số replica tối đa, fallback, threshold và truy vấn từ chính ScaledObject, nên khi overlay đổi thì bài thử đổi theo. T4 gây mất tín hiệu bằng một NetworkPolicy chặn KEDA gọi Prometheus.

<!-- nguồn: envs/sim/tests/run-t1-t5.sh; nhật ký Trình tuần 04 mục 01/11 (đọc max, fallback, threshold, truy vấn từ ScaledObject); nhật ký Trình tuần 05 mục 07/11 (đo bằng đồng hồ đơn điệu /proc/uptime sau khi đồng hồ của VM WSL2 chạy nhanh 1,6%) -->

### 4.3.3. Kiểm chứng trên simulator

Bảng 4.3a tổng hợp các lần chạy T1–T5 trên simulator. Kết quả mong đợi của mỗi bài tính tay được từ threshold và số replica tối đa. Riêng T4 chỉ lấy các lần chạy sau khi sửa hai lỗi ở mục 4.3.4.

<!-- nguồn: như comment nguồn của Bảng 4.3a; T4 sau khi sửa: nhật ký Trình tuần 05 mục 07/11 -->

**Bảng 4.3a.** Kết quả các bài thử autoscaling T1–T5 trên simulator (kind 3 node, threshold 10, tối đa 3 replica). T2 tính từ lúc bắt đầu tải tới lúc HPA đặt 3 replica

| Bài | Thao tác | Tiêu chí | Kết quả |
|---|---|---|---|
| T1 | Không có tải | Giữ 1 replica | 1 replica suốt 120 s |
| T2 | 25 request đồng thời, khoảng 2,5 × threshold | HPA đặt 3 replica trong ≤ 15 s | 1–9 s (7 lần chạy) |
| T3 | Tắt tải | Giữ 3 replica 300 s, rồi bớt 1 pod mỗi 60 s | Giữ 301–304 s, về 1 sau thêm 58–61 s |
| T4 | Chặn KEDA gọi Prometheus | Fallback lên tối đa trong ≤ 30 s | 17–23 s (8/8 lần chạy) |
| T5 | Tạm dừng bằng annotation | Giữ 1 replica dù có tải | 1 replica ở mọi lần đọc |

<!-- nguồn: nhật ký Trình tuần 04 mục 01/11 (lần 2 sau khi tắt keep-alive: T1 120 s; T2 8 s; T3 304 s rồi 61 s; T5 KEDA xoá HPA, ready = 1 ở 83 lần đọc; lần 1: T2 1 s, T3 301 s rồi 61 s; lần với xoá pod: T2 6 s, T3 302 s rồi 60 s, T5 71 lần đọc), nhật ký Trình tuần 05 mục 07/11 (lần 1 bản gộp: T2 8 s, T3 304 s rồi 58 s; T4 đo lặp với timeout 1000 ms: 20, 19, 20, 19, 19 s, 5/5; cộng các lần 2–4 của make sim-test: tổng 17–23 s, 8/8 theo 00-thong-so.md §9.3 và ADR-006 C6); T2: ba mẫu ngày 01/11 (1, 6, 8 s) tính từ lúc gọi load-sim.sh, gồm khoảng 1 s mở port-forward, các mẫu từ 07/11 tính từ lúc hey chạy (nhật ký Trình tuần 05 mục 07/11); pod thứ 2, 3 Ready sau 7 s và 16 s kể từ quyết định (nhật ký Trình tuần 04 mục 01/11), nhật ký Trình tuần 07 mục 16/11 (7 mẫu T2 trong runs/sim/: 1, 6, 8, 8, 9, 4, 5 s); tiêu chí T2 ≤ 15 s và T4 ≤ 30 s (N6) theo nhật ký Trình tuần 04; metric HPA ở 3 replica 8,334 ≈ 25 ÷ 3 -->

Cả năm bài đều đạt tiêu chí. Ở T2, giá trị HPA thấy khi đã có 3 replica là 8,33, đúng bằng 25 chia 3, nên truy vấn cộng đúng tín hiệu của mọi pod. T6 (đổi cấu hình ở máy nhà) mới được kiểm cơ chế trên simulator, còn T7 (mức ưu tiên thấp nhất) chưa chạy. Trên GPU thật, A2 scale từ 1 lên 4 replica rồi giảm lại (mục 5.3), và fallback bật trong kịch bản VH4 (mục 5.5).

<!-- nguồn: nhật ký Trình tuần 04 mục 01/11 (metric HPA ở 3 replica 8334m, 8,334); nhật ký Trình tuần 05 mục 07/11 (T6 ở nhà chưa chạy, cơ chế thấy trên kind; T7 chưa chạy); Môi trường §16 bảng nghiệm thu (F2: T6 mới kiểm trên simulator; T7 Could chưa làm); kết quả trên V2: mục 5.3 (A2 × KB2 lên 4 replica), mục 5.5 (VH4) -->

### 4.3.4. Sự cố và điểm lệch

**T4 không fallback.** Ở lần chạy đầu, NetworkPolicy đã áp 120 s mà KEDA vẫn không ghi nhận lỗi nào. Một pod mới trong namespace của KEDA thì bị chặn ngay. Nguyên nhân là KEDA dùng lại một kết nối keep-alive không bao giờ rảnh để đóng, còn NetworkPolicy chỉ chặn kết nối mới. Nhóm đối chiếu mã nguồn KEDA v2.21.0 rồi đặt biến `KEDA_HTTP_DISABLE_KEEP_ALIVE=true`, nên mỗi lần hỏi mở kết nối mới và policy có tác dụng ngay từ lần hỏi kế tiếp.

<!-- nguồn: nhật ký Trình tuần 04 mục 01/11 (T4 lần 1: policy 120 s, numberOfFailures 0; busybox trong ns keda bị chặn, ns default thì không; keep-alive và conntrack; KEDA_HTTP_DISABLE_KEEP_ALIVE đọc ở pkg/util/http.go của KEDA v2.21.0, scaler Prometheus dùng kedautil.CreateHTTPClient; sau khi sửa: lỗi 1 ở +11 s, fallback ở +24 s) -->

**T4 chậm quá 30 s.** Sau khi gộp nhánh, T4 trượt với 38 s. Fallback chỉ bật ở lần lỗi thứ tư, và với timeout mặc định 3 s, mỗi lần hỏi bị chặn mất trọn 3 s. Gộp mọi lần chạy, timeout 3 s cho 24–38 s và 3/7 lần vượt 30 s, còn timeout 1 s cho 17–23 s và đạt cả 8 lần. Nhóm chọn timeout 1 s và giữ `failureThreshold` bằng 3. Phương án hạ `failureThreshold` xuống 2 bị loại vì dễ lên tối đa oan khi Prometheus chập chờn ngắn, còn nới chỉ tiêu lên 45 s thì làm yêu cầu yếu đi. Rủi ro còn lại là truy vấn chậm quá 1 s bị tính là lỗi, nhưng trên kind mọi truy vấn đều xong dưới 0,1 s.

<!-- nguồn: nhật ký Trình tuần 05 mục 07/11 (T4 38 s, 6 lỗi; đo lặp 3000 ms: 26, 26, 35, 26, 32 s, 3/5; 1000 ms: 20, 19, 20, 19, 19 s, 5/5; gộp mọi lần chạy theo 00-thong-so.md §9.3 và ADR-006 C6: 3000 ms 24–38 s, 3/7 vượt N6; 1000 ms 17–23 s, 8/8; fallback khi NumberOfFailures > FailureThreshold, pkg/fallback/fallback.go:144; timeout mặc định 3000 ms, cmd/operator/main.go:236; 459 truy vấn < 0,1 s; phương án bỏ: failureThreshold 2, nới N6 lên 45 s) -->

**Tín hiệu của A1 bị kẹt.** Khi xem lại một lượt A1 của phiên đo thử trên VM, nhóm thấy một mẫu 100% đơn lẻ sau khi tải dừng đủ giữ HPA ở 2 replica. Exporter GPU không có nhãn pod nên không lọc được theo pod. Truy vấn được đổi sang trung bình 15 s trên từng GPU trước khi cộng, và tín hiệu sau tải còn lớn nhất 33,3, dưới threshold 70. Đánh đổi là tín hiệu phản ứng chậm hơn truy vấn cũ tối đa khoảng 20 s. Mọi lượt của phiên đo chính dùng truy vấn này (Bảng 3.3a).

<!-- nguồn: nhật ký Quang tuần 06 mục 09/11 (A1-KB3-1 của V1: tín hiệu lớn nhất sau tải gốc 100, avg 15 s 33,3; chỉ bản gốc cho desired = 2 với threshold 70; mốc desired 2/3/4 trễ 10/5/20 s so với gốc; exporter không có label pod); nhật ký Trình tuần 06 mục 09/11; query hiện tại trong common/autoscaling/eval/A1.yaml -->

Bài học thứ nhất là cách gây sự cố cũng phải được kiểm chứng trước khi dùng để đo. Nếu T4 không trượt trên simulator, lỗi keep-alive nhiều khả năng đã làm kịch bản VH4 trên VM thuê không gây được mất tín hiệu. Bài học thứ hai là bài thử nên đọc tham số từ chính manifest, để không lệch khỏi cấu hình đang chạy.

<!-- nguồn: suy từ mục 4.3.4 (T4) và kịch bản VH4 áp cùng NetworkPolicy (experiments/ops/vh.py, BLOCK_FILE = common/autoscaling/tests/block-keda-to-prometheus.yaml) -->
