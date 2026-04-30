"""Unit tests for `_inject_chat_mode_prefix` in routers/console.py.

Verifies that the X-Chat-Mode header reliably prepends the configured
prefix to the first text part of the native payload, across the three
supported part shapes (TextContent-like / dict / str), and is a no-op
for `free` / unknown / missing modes.
"""

from __future__ import annotations

from types import SimpleNamespace

import pytest

from ltclaw_gy_x.app.routers.console import (
    _CHAT_MODE_PREFIX,
    _inject_chat_mode_prefix,
)


class _FakeRequest:
    def __init__(self, mode: str | None) -> None:
        self.headers = {} if mode is None else {"X-Chat-Mode": mode}


def _payload_with(parts):
    return {"content_parts": list(parts)}


def test_no_header_is_noop():
    parts = [{"text": "hello"}]
    payload = _payload_with(parts)
    _inject_chat_mode_prefix(_FakeRequest(None), payload)
    assert payload["content_parts"][0]["text"] == "hello"


def test_free_mode_is_noop():
    payload = _payload_with([{"text": "hi"}])
    _inject_chat_mode_prefix(_FakeRequest("free"), payload)
    assert payload["content_parts"][0]["text"] == "hi"


def test_unknown_mode_is_noop():
    payload = _payload_with([{"text": "hi"}])
    _inject_chat_mode_prefix(_FakeRequest("nope"), payload)
    assert payload["content_parts"][0]["text"] == "hi"


@pytest.mark.parametrize("mode", ["design", "numeric", "doc", "kb"])
def test_dict_part_gets_prefix(mode):
    payload = _payload_with([{"text": "原文"}])
    _inject_chat_mode_prefix(_FakeRequest(mode), payload)
    expected = f"{_CHAT_MODE_PREFIX[mode]}\n\n原文"
    assert payload["content_parts"][0]["text"] == expected


def test_textcontent_object_part_gets_prefix():
    obj = SimpleNamespace(text="数值表问题")
    payload = _payload_with([obj])
    _inject_chat_mode_prefix(_FakeRequest("numeric"), payload)
    assert payload["content_parts"][0].text.startswith(
        _CHAT_MODE_PREFIX["numeric"]
    )
    assert payload["content_parts"][0].text.endswith("数值表问题")


def test_string_part_gets_prefix():
    payload = _payload_with(["写一份背景"])
    _inject_chat_mode_prefix(_FakeRequest("design"), payload)
    assert payload["content_parts"][0].startswith(_CHAT_MODE_PREFIX["design"])
    assert payload["content_parts"][0].endswith("写一份背景")


def test_only_first_text_part_is_modified():
    payload = _payload_with([{"text": "first"}, {"text": "second"}])
    _inject_chat_mode_prefix(_FakeRequest("kb"), payload)
    assert payload["content_parts"][0]["text"].startswith(
        _CHAT_MODE_PREFIX["kb"]
    )
    assert payload["content_parts"][1]["text"] == "second"


def test_no_text_parts_inserts_synthetic_part():
    payload = _payload_with([{"image_url": "x"}])
    _inject_chat_mode_prefix(_FakeRequest("doc"), payload)
    head = payload["content_parts"][0]
    head_text = getattr(head, "text", head if isinstance(head, str) else None)
    assert head_text is not None
    assert _CHAT_MODE_PREFIX["doc"] in head_text


def test_mode_header_is_case_insensitive():
    payload = _payload_with([{"text": "x"}])
    _inject_chat_mode_prefix(_FakeRequest("KB"), payload)
    assert payload["content_parts"][0]["text"].startswith(
        _CHAT_MODE_PREFIX["kb"]
    )