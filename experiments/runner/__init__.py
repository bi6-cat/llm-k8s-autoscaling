"""Runner đánh giá: tự chạy các lượt (run) của ma trận đánh giá, không cần người can thiệp.

Khái niệm: Một lượt = một cấu hình scale (S1, S4, A1, A2…) gặp một kịch bản tải (KB1–KB3, CONST).
    Runner làm lần lượt 7 bước của Môi trường §14.1 cho mỗi lượt: áp cấu hình, reset, warm-up, chạy,
    thu dữ liệu, cooldown, kiểm hợp lệ; rồi ghi checkpoint `progress.json` để chạy tiếp được nếu bị ngắt.
Mục đích: Phiên V2 có 17 lượt × ~35 phút chạy qua đêm. Runner thay người gõ lệnh, làm mọi lượt theo
    đúng một quy trình, và đánh dấu lượt không hợp lệ (Môi trường §17) để chạy lại.
    Mọi thao tác với cluster đi qua `kubectl` (module kube), nên runner chạy giống nhau trên kind,
    cluster nhà và VM thuê, miễn là có kubeconfig.

Các module:
    matrix    đọc và kiểm tra file ma trận (YAML)
    kube      wrapper `kubectl` và truy vấn Prometheus qua API server proxy
    configs   áp cấu hình tĩnh hoặc ScaledObject, pause/unpause KEDA
    loadjob   chạy máy tạo tải (loadgen) thành Job trong cluster, lấy kết quả về
    collect   thu metric Prometheus, event, log vLLM, cảnh báo
    vllm_log  đọc log khởi động vLLM: mốc và độ dài các pha cold start (parse_vllm_log)
    checks    kiểm điều kiện hợp lệ của một lượt
    progress  checkpoint progress.json
    session   điều phối một lượt và cả phiên
"""
