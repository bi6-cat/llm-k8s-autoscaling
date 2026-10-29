"""Máy tạo tải open-loop cho vLLM.

Khái niệm: Open-loop = thời điểm gửi từng request được sinh TRƯỚC theo tốc độ λ(t), không phụ thuộc
    vào việc hệ thống trả lời nhanh hay chậm. Ngược lại, closed-loop (N người dùng, mỗi người chờ trả lời
    xong mới gửi tiếp) tự giảm tốc độ gửi khi hệ thống chậm, nên che mất tình trạng quá tải.
Mục đích: Sinh tải theo kịch bản KB1–KB3 (Thông số §7) hoặc tốc độ cố định (ĐG1), ghi mỗi request một
    dòng vào requests.csv và tự kiểm tra độ tin cậy của chính mình (Môi trường §9, §17).

Các module:
    scenarios  λ(t) và các pha của từng kịch bản
    schedule   lịch gửi (quá trình Poisson) và độ dài prompt, sinh từ seed
    prompts    văn bản prompt tổng hợp
    sender     gửi request, đọc stream, ghi CSV
    checks     tự kiểm tra: độ lệch lịch gửi, độ trễ event loop, CPU
    __main__   dòng lệnh: python -m loadgen
"""
