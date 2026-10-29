"""Test cho prompts.py.

Mục đích: Prompt có đúng số từ yêu cầu, tái lập được, và mỗi request một nội dung khác nhau.
"""

from __future__ import annotations

from loadgen.prompts import WORDS, make_prompt


def test_prompt_has_requested_word_count():
    p = make_prompt(request_id=7, n_words=300, run_seed=1)
    head, _, body = p.partition(": ")
    assert head == "Request 7"
    assert len(body.split()) == 300
    assert all(w in WORDS for w in body.split())


def test_prompt_is_reproducible():
    assert make_prompt(3, 50, 99) == make_prompt(3, 50, 99)


def test_prompts_differ_by_request_and_by_run():
    assert make_prompt(1, 50, 99) != make_prompt(2, 50, 99)
    assert make_prompt(1, 50, 99) != make_prompt(1, 50, 100)


def test_word_list_has_no_duplicates():
    assert len(WORDS) == len(set(WORDS)) > 200
