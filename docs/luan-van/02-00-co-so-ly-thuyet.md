<!-- Mục đích: tiêu đề và đoạn mở đầu chương 2 của luận văn (Cơ sở lý thuyết và giải pháp liên quan), bản base lượt 1. Người viết: Trình. Viết ngày 27/11/2026 theo dàn ý ở docs/chi-tiet/06-ke-hoach-quan-ly.md §11.1. Quy ước: docs/luan-van/README.md, docs/luan-van/quy-tac-viet.md -->
<!-- Soát số: chưa · Soát văn phong: kiem_van 27/11 · Người viết đọc lại: chưa -->
# Chương 2. Cơ sở lý thuyết và giải pháp liên quan

Chương này trình bày các kiến thức mà chương 3–5 dùng thẳng, không giải thích lại. Mục 2.1 nói cách một LLM sinh token trên GPU và cách vLLM xếp nhiều request vào cùng một GPU, kèm các chỉ số đo chất lượng phục vụ. Mục 2.2 nhìn một replica như một hàng đợi, để giải thích vì sao số request đồng thời phản ánh tải và vì sao không thể cho GPU chạy sát giới hạn. Mục 2.3 nói cách Kubernetes cấp GPU cho pod và vì sao chỉ số GPU utilization bão hoà sớm. Mục 2.4 trình bày cơ chế autoscaling của Kubernetes và KEDA. Mục 2.5 trình bày vận hành theo SLO, hệ thống giám sát và cách triển khai qua Git. Mục 2.6 điểm qua các giải pháp liên quan và vị trí của đồ án giữa chúng.

<!-- nguồn: docs/chi-tiet/06-ke-hoach-quan-ly.md §11.1 (dòng chương 2: 2.1–2.6 và tiểu mục); docs/luan-van/quy-tac-viet.md §2 (chương 2: kiến thức chung người đọc cần, giải pháp liên quan; chương 3–6 dùng thẳng, không giải thích lại) -->
