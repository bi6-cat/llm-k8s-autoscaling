"""Prompt tổng hợp: văn bản ngẫu nhiên có độ dài (số token) biết trước.

Khái niệm: Token = đơn vị văn bản mà model xử lý (một từ, một phần của từ, hoặc dấu câu), do tokenizer
    của model quyết định. Chi phí prefill (tính KV-cache cho prompt) tỷ lệ với số token đầu vào.
Mục đích: Sinh prompt dài 256–1024 token (Thông số §7) mà KHÔNG cần tải tokenizer (thư viện transformers
    rất nặng): mọi từ trong WORDS đã được kiểm là đúng 1 token khi đứng sau một dấu cách, với tokenizer
    của Qwen2.5-1.5B-Instruct và Qwen2.5-7B-Instruct (hai model dùng chung một tokenizer.json, cùng
    sha256). Kiểm ngày 25/10/2026: n từ + phần đầu "Request <id>:" cho ra n + 8 token.
    Số token thật (gồm cả chat template) vẫn được ghi lại từ `usage.prompt_tokens` của server.
    Mỗi request mở đầu bằng id riêng và các từ khác nhau, nên vLLM không dùng lại được prefix cache giữa
    hai request (ngoài phần chat template chung), giống tải thật.
"""

from __future__ import annotations

import random

WORDS: tuple[str, ...] = tuple(
    """
    time year people way day man thing woman life child world school state family student group country
    problem hand part place case week company system program question work government number night point home
    water room mother area money story fact month lot right study book eye job word business issue side kind
    head house service friend father power hour game line end member law car city community name president
    team minute idea kid body information back parent face others level office door health person art
    history party result change morning reason research girl guy moment air teacher force education foot boy
    age policy music market sense nation plan college interest experience effect class control care
    field development role effort rate heart show leader light voice wife police mind price report
    decision son view relationship town road arm difference value building action model season society tax
    director position player record paper space ground form event official matter center couple site project
    activity star table need court oil situation cost industry figure street image phone data picture
    practice piece land product doctor wall patient worker news test movie north love support technology step
    baby computer type attention film tree source organization hair window evidence population truth song
    energy period river garden cloud stone bridge forest island mountain ocean village kitchen letter train
    simple quick bright quiet happy small large early late green blue red black white warm cold strong soft
    open clear deep long short high low new old good great little young important public different possible
    run walk write read speak listen build carry bring keep hold turn move live believe happen provide sit
    stand lose pay meet include continue set learn lead understand watch follow stop create spend grow offer
    remember consider appear buy wait serve send expect stay fall cut reach remain suggest raise
    pass sell require decide pull
    """.split()
)


def make_prompt(request_id: int, n_words: int, run_seed: int) -> str:
    """Prompt của một request: phần đầu chứa id, tiếp theo là `n_words` từ ngẫu nhiên.

    Sinh lúc gửi (không giữ sẵn cả nghìn prompt trong RAM). random.Random với seed là chuỗi thì tái lập
    được giữa các lần chạy (Python băm chuỗi seed bằng SHA-512, không phụ thuộc PYTHONHASHSEED).
    """
    rng = random.Random(f"{run_seed}:{request_id}")
    body = " ".join(rng.choice(WORDS) for _ in range(n_words))
    return f"Request {request_id}: {body}"
