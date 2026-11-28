<!-- Mục đích: danh mục thuật ngữ, chữ viết tắt và mã định danh ở phần đầu quyển. Người viết: Trình. -->
<!-- Chỉ giữ mục có dùng trong thân bài (đếm trên bản ghép ngày 27/11/2026 từ main và các nhánh luận văn còn PR mở). Thêm thuật ngữ hay chữ viết tắt mới vào thân bài thì thêm dòng ở đây, theo quy tắc viết §4. Không đưa vào: đơn vị đo (GB, GiB, MiB), tên sản phẩm và tên hãng (NVIDIA, RTX, KServe), tên resource Kubernetes viết theo kind (Deployment, ScaledObject). -->

# Danh mục thuật ngữ, chữ viết tắt và mã định danh {.unnumbered}

Danh mục gồm bốn phần: chữ viết tắt, thuật ngữ, mã định danh do nhóm đặt và ký hiệu. Trong mỗi phần, các mục xếp theo thứ tự chữ cái; ký hiệu Hy Lạp đứng sau ký hiệu Latin.

**Chữ viết tắt**

| Viết tắt | Tiếng Anh | Nghĩa trong luận văn |
|---|---|---|
| ADR | Architecture Decision Record | Bản ghi quyết định kiến trúc, nêu các phương án đã cân nhắc và lý do chọn |
| API | Application Programming Interface | Giao diện lập trình ứng dụng |
| BF16 | Brain Floating Point 16 | Định dạng số thực 16 bit, 2 byte mỗi tham số |
| CI | Continuous Integration | Kiểm tra tự động mỗi thay đổi trước khi merge |
| CPU | Central Processing Unit | Bộ xử lý trung tâm |
| CRD | Custom Resource Definition | Khai báo một loại object mới cho Kubernetes |
| CSV | Comma-Separated Values | File dạng bảng, các cột ngăn bằng dấu phẩy |
| CUDA | Compute Unified Device Architecture | Nền tảng lập trình GPU của NVIDIA |
| DCGM | Data Center GPU Manager | Bộ công cụ giám sát GPU của NVIDIA |
| DHCP | Dynamic Host Configuration Protocol | Giao thức cấp địa chỉ IP tự động |
| E2E | End-to-End | Độ trễ toàn trình, từ khi gửi request tới khi nhận token cuối |
| GC | Garbage Collection | Dọn rác; ở đây là kubelet tự xoá image khi ổ gần đầy |
| GPU | Graphics Processing Unit | Bộ xử lý đồ hoạ, nơi model chạy |
| GQA | Grouped-Query Attention | Nhiều query head dùng chung một KV head, giảm kích thước KV cache |
| HPA | Horizontal Pod Autoscaler | Bộ điều khiển của Kubernetes tính số replica từ metric |
| HTTP | HyperText Transfer Protocol | Giao thức truyền request và phản hồi |
| IP | Internet Protocol | Giao thức mạng; địa chỉ IP |
| ITL | Inter-Token Latency | Thời gian giữa hai token liên tiếp |
| JSON | JavaScript Object Notation | Định dạng dữ liệu dạng văn bản |
| KEDA | Kubernetes Event-driven Autoscaling | Thành phần đưa metric bên ngoài, ở đây từ Prometheus, vào HPA |
| KV | Key–Value | Cặp key và value của attention; KV cache |
| LAN | Local Area Network | Mạng cục bộ |
| LLM | Large Language Model | Mô hình ngôn ngữ lớn |
| LoRA | Low-Rank Adaptation | Tinh chỉnh model bằng ma trận hạng thấp; đồ án không dùng |
| MPS | Multi-Process Service | Chế độ chia một GPU cho nhiều tiến trình của NVIDIA |
| MTU | Maximum Transmission Unit | Kích thước lớn nhất của một gói mạng |
| NVMe | Non-Volatile Memory Express | Chuẩn ổ SSD nối qua PCIe |
| OOM | Out Of Memory | Hết bộ nhớ; tiến trình hoặc container bị dừng vì vượt giới hạn bộ nhớ |
| PC | Personal Computer | Máy tính cá nhân, ở đây là máy nhà |
| PR | Pull Request | Đề nghị gộp một nhánh vào nhánh chính trên GitHub |
| PVC | PersistentVolumeClaim | Yêu cầu cấp volume lưu trữ bền trong Kubernetes |
| QoS | Quality of Service | Lớp chất lượng dịch vụ của pod (Guaranteed, Burstable, BestEffort) |
| RAM | Random-Access Memory | Bộ nhớ chính |
| RPS | Requests Per Second | Số request mỗi giây |
| SATA | Serial AT Attachment | Chuẩn giao tiếp ổ đĩa |
| SHA | Secure Hash Algorithm | Thuật toán băm; mã commit và digest của image |
| SIGKILL, SIGTERM | Signal kill, signal terminate | Tín hiệu buộc dừng ngay và tín hiệu đề nghị dừng một tiến trình |
| SLI | Service Level Indicator | Chỉ số đo chất lượng dịch vụ |
| SLO | Service Level Objective | Mục tiêu mức dịch vụ: mức SLI phải đạt trong một khoảng thời gian |
| SRE | Site Reliability Engineering | Thực hành vận hành hệ thống tin cậy |
| SSD | Solid-State Drive | Ổ thể rắn |
| SSE | Server-Sent Events | Cách server gửi dần từng phần phản hồi trên một kết nối HTTP |
| SSH | Secure Shell | Giao thức đăng nhập từ xa |
| TPOT | Time Per Output Token | Thời gian trung bình sinh mỗi token ra, sau token đầu |
| TTFT | Time To First Token | Thời gian từ khi gửi request tới khi nhận token đầu |
| USD | United States Dollar | Đô la Mỹ |
| vCPU | Virtual CPU | Lõi CPU ảo của VM |
| VM | Virtual Machine | Máy ảo; ở đây là VM thuê trên Vast.ai |
| VRAM | Video RAM | Bộ nhớ của GPU |
| WSL2 | Windows Subsystem for Linux 2 | Môi trường Linux chạy trong Windows |
| YAML | YAML Ain't Markup Language | Định dạng file cấu hình |

<!-- nguồn: chữ viết tắt đếm trên bản ghép 27/11/2026 (bỏ comment, khối code và `code`); nghĩa theo định nghĩa trong thân bài: TTFT, TPOT, E2E ở 2.1.2; SLI, SLO ở 2.5.1; ADR ở 1.2; SRE ở 2.5 -->

**Thuật ngữ**

| Thuật ngữ | Nghĩa |
|---|---|
| autoscaling | Tự động điều chỉnh số replica theo tải |
| batch, static batching, continuous batching | Nhóm request xử lý chung trên GPU; static batching chờ cả nhóm xong mới nhận nhóm mới, continuous batching thêm và bớt request ở từng bước sinh token |
| burn rate | Tốc độ tiêu hao error budget so với mức vừa hết đúng cuối kỳ |
| chunked prefill | Chia prefill của prompt dài thành nhiều phần, xen với decode |
| cold start | Thời gian từ khi tạo pod tới khi pod phục vụ được |
| closed-loop | Cách sinh tải: mỗi người dùng giả chờ phản hồi rồi mới gửi request tiếp, nên tải giảm khi hệ thống chậm |
| counter, gauge, histogram | Ba loại metric của Prometheus: bộ đếm chỉ tăng; giá trị tức thời; số lần đo rơi vào từng khoảng giá trị (bucket) |
| CUDA graph | Chuỗi kernel GPU ghi sẵn một lần rồi chạy lại, giảm chi phí gọi kernel |
| decode | Pha sinh lần lượt từng token ra |
| device plugin | Thành phần công bố tài nguyên phần cứng như GPU cho Kubernetes |
| digest | Mã băm định danh đúng một bản image |
| error budget (ngân sách lỗi) | 1 − SLO: phần request không đạt được phép có trong kỳ |
| exporter | Chương trình xuất metric theo định dạng của Prometheus |
| fallback | Chế độ dự phòng khi mất tín hiệu scale: giữ số replica ở mức tối đa |
| flapping | Số replica dao động lên xuống liên tục |
| GitOps | Khai báo trạng thái hệ thống trong Git; bộ điều khiển đưa cluster về đúng trạng thái đó |
| GPU replica | Một phần GPU chia bằng time-slicing, chỉ dùng ở máy nhà |
| GPU-giờ | Số GPU bị giữ nhân thời gian giữ; đại diện cho chi phí |
| graceful shutdown | Tắt pod mà không cắt request đang xử lý |
| kernel | Một hàm chạy trên GPU |
| KV cache | Bộ nhớ trên GPU giữ key và value của các token đã xử lý |
| lượt (đánh giá) | Một lần chạy một cấu hình với một kịch bản tải |
| manifest | File khai báo object Kubernetes |
| máy nhà, VM thuê | PC có RTX 5060 của nhóm; VM thuê theo giờ trên Vast.ai |
| máy tạo tải (*load generator*) | Chương trình gửi request theo lịch định trước |
| open-loop | Cách sinh tải: request gửi theo lịch, không chờ phản hồi của request trước |
| overlay | Phần cấu hình Kustomize riêng của một môi trường, đặt lên base dùng chung |
| p50, p95, p99 | Phân vị 50, 95, 99 |
| page, ticket | Hai mức cảnh báo: gọi người trực ngay; xử lý trong giờ làm việc |
| PagedAttention | Cách vLLM cấp KV cache theo từng khối nhỏ, như trang bộ nhớ |
| phiên đo | Một lần thuê máy và chạy loạt lượt đo |
| pod, node, cluster | Đơn vị chạy nhỏ nhất của Kubernetes; một máy; tập các máy do Kubernetes quản lý |
| preemption | Tạm dừng request đang chạy khi hết KV cache |
| prefill | Pha xử lý toàn bộ prompt, tạo token đầu |
| prefix caching | Dùng lại KV cache của phần đầu prompt giống nhau |
| probe | Phép kiểm tra định kỳ của kubelet; readiness probe quyết định pod có nhận request hay không |
| PromQL | Ngôn ngữ truy vấn của Prometheus |
| recording rule | Quy tắc của Prometheus tính trước một biểu thức và lưu kết quả thành metric mới |
| replica | Một bản sao pod vLLM, mỗi bản dùng 1 GPU |
| rollback | Quay lại phiên bản trước |
| rolling update | Thay dần pod cũ bằng pod mới khi cập nhật |
| runbook | Hướng dẫn xử lý cho một cảnh báo cụ thể |
| runner | Chương trình chạy tự động các lượt đánh giá |
| scale-to-zero | Tắt hẳn mọi replica khi không có tải |
| scale-up, scale-down | Thêm, bớt replica |
| scrape | Một lần Prometheus gọi endpoint `/metrics` để thu metric, lặp theo chu kỳ |
| self-heal | Chế độ của Argo CD đưa mọi thay đổi làm tay trên cluster về đúng trạng thái trong Git |
| simulator | Cluster Kubernetes không có GPU, chạy phần mềm giả lập API và metric của vLLM |
| SLO attainment | Tỷ lệ request đạt SLO |
| stabilization window | Cửa sổ thời gian HPA xét các đề xuất số replica gần nhất; khi scale-down, HPA lấy đề xuất cao nhất trong cửa sổ (mặc định 300 s) |
| streaming | Gửi dần câu trả lời về theo từng phần |
| sync | Argo CD áp trạng thái khai báo trong Git vào cluster |
| threshold | Giá trị mục tiêu của metric mỗi replica, dùng để tính số replica |
| throughput | Thông lượng: số request hoặc token xử lý được mỗi giây |
| time-slicing | Chia một GPU theo thời gian cho nhiều pod |
| token | Đơn vị văn bản mà model xử lý |
| Watchdog | Cảnh báo luôn kêu, để biết chính hệ thống cảnh báo còn hoạt động (*dead man's switch*) |
| weights | Trọng số của model, nằm trong VRAM suốt thời gian phục vụ |

<!-- nguồn: docs/chi-tiet/02-kien-thuc-nen.md §7 (bảng thuật ngữ); docs/luan-van/quy-tac-viet.md §4 (bảng tên gọi thống nhất: replica, GPU replica, cold start, graceful shutdown, page/ticket, GPU-giờ, máy tạo tải, runner, lượt, phiên đo, máy nhà/VM thuê); simulator ở 1.2; Watchdog ở 4.6 và 6.3; fallback lên tối đa ở Bảng 4.3 -->

**Mã định danh**

| Mã | Nghĩa | Định nghĩa ở |
|---|---|---|
| A1 | Autoscaling theo GPU utilization của node | Mục 3.3 |
| A2 | Autoscaling theo số request đang xử lý và đang chờ | Mục 3.3 |
| ĐG1–ĐG3 | Ba đánh giá: năng lực một replica, autoscaling so với cấu hình tĩnh, cold start | Mục 3.6 |
| F1–F7 | Yêu cầu chức năng | Mục 3.1 |
| KB1–KB3 | Ba kịch bản tải: thấp và ổn định; tăng đột ngột rồi giảm; cao và kéo dài | Mục 3.6 |
| L0, L1, L2 | Mức cold start: node trắng; model trên ổ mạng (không dùng); cấu hình chạy thật | Mục 3.4 |
| LT1–LT8 | Kiểm chứng lý thuyết | Mục 3.6 |
| N1–N8 | Chỉ tiêu nghiệm thu; N2a và N2b là hai vế của N2 | Mục 3.1 |
| S1, S4 | Cấu hình tĩnh: luôn 1 replica, luôn 4 replica | Mục 3.3 |
| T1–T7 | Bài kiểm thử autoscaling | Mục 4.3 |
| V0, V1 | Hai phiên thử trên VM thuê, trước phiên đo chính | Phụ lục C, F |
| V2 | Phiên đo chính, trên VM thuê 4 × RTX 4060 Ti | Mục 5.1 |
| VH1–VH6 | Kịch bản vận hành | Mục 3.6 |

<!-- nguồn: docs/luan-van/quy-tac-viet.md §4 (bảng mã định danh); cấu hình ở Bảng 3.3; mức cold start ở Bảng 3.6 và mục 3.4 (L1 không dùng); kịch bản tải ở Bảng 3.8; ĐG, VH, LT ở 3.6; T1–T5 ở Bảng 4.4, T6 và T7 ở 4.3 và 5.6; V2 ở 5.1 -->

**Ký hiệu**

| Ký hiệu | Nghĩa |
|---|---|
| B\* | Số request đồng thời của một replica ở mức năng lực C |
| C | Năng lực một replica (req/s): tốc độ đến lớn nhất mà ít nhất 95% request còn đạt SLO |
| N | Số GPU, cũng là số replica tối đa (N = 4) |
| λ | Tốc độ đến của request (req/s) |
| μ | Tốc độ phục vụ lớn nhất của một replica khi luôn có việc (req/s) |
| ρ | Mức sử dụng, ρ = λ/μ |

<!-- nguồn: docs/luan-van/quy-tac-viet.md §4 (ký hiệu C, B*, λ, N); μ và ρ = λ/μ ở 2.2; định nghĩa C ở 3.6 (ĐG1: mức λ lớn nhất còn ít nhất 95% request đạt SLO) -->
