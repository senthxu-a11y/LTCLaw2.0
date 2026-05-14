"""Unit tests for `_inject_chat_mode_prefix` in routers/console.py.

Verifies that the X-Chat-Mode header reliably prepends the configured
prefix to the first text part of the native payload, across the three
supported part shapes (TextContent-like / dict / str), and is a no-op
for `free` / unknown / missing modes.
"""

from __future__ import annotations

from types import SimpleNamespace

import pytest

from ltclaw_gy_x.app.routers import console as console_router_module
from ltclaw_gy_x.app.routers.console import (
    _CHAT_MODE_PREFIX,
    _augment_chat_mode_context,
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


@pytest.mark.asyncio
async def test_augment_chat_mode_context_uses_current_release_and_not_unified_search(monkeypatch, tmp_path):
    project_root = tmp_path / "project"
    project_root.mkdir()
    service = SimpleNamespace(
        configured=True,
        _runtime_svn_root=lambda: project_root,
        user_config=SimpleNamespace(svn_local_root=None),
        project_config=SimpleNamespace(svn=SimpleNamespace(root=None)),
    )
    workspace = SimpleNamespace(
        service_manager=SimpleNamespace(services={"game_service": service})
    )
    payload = {"content_parts": [{"text": "damage formula"}], "meta": {}}

    monkeypatch.setattr(
        console_router_module,
        "unified_search",
        lambda *args, **kwargs: (_ for _ in ()).throw(AssertionError("should not call unified_search")),
        raising=False,
    )
    monkeypatch.setattr(
        console_router_module,
        "build_current_release_context",
        lambda project_root_arg, query, *, max_chunks, max_chars: {
            "mode": "context",
            "query": query,
            "release_id": "release-001",
            "built_at": None,
            "chunks": [
                {
                    "chunk_id": "chunk-001",
                    "source_type": "doc_knowledge",
                    "text": "Combat damage formula release evidence",
                    "citation_id": "citation-001",
                }
            ],
            "citations": [
                {
                    "citation_id": "citation-001",
                    "title": "Combat Overview",
                    "source_path": "Docs/Combat.md",
                    "artifact_path": "indexes/doc_knowledge.jsonl",
                }
            ],
        },
    )

    await _augment_chat_mode_context(_FakeRequest("kb"), workspace, payload)

    assert payload["meta"]["formal_knowledge"]["status"] == "context"
    assert payload["meta"]["formal_knowledge"]["legacy_fallback_used"] is False
    assert "provider" not in payload["meta"]["formal_knowledge"]
    assert "model" not in payload["meta"]["formal_knowledge"]
    assert "api_key" not in payload["meta"]["formal_knowledge"]
    assert "base_url" not in payload["meta"]["formal_knowledge"]
    assert payload["content_parts"][0]["text"].startswith("[Formal Knowledge Context]")
    assert "damage formula" in payload["content_parts"][0]["text"]


@pytest.mark.asyncio
async def test_augment_chat_mode_context_records_no_current_release_without_injecting_context(monkeypatch, tmp_path):
    project_root = tmp_path / "project"
    project_root.mkdir()
    service = SimpleNamespace(
        configured=True,
        _runtime_svn_root=lambda: project_root,
        user_config=SimpleNamespace(svn_local_root=None),
        project_config=SimpleNamespace(svn=SimpleNamespace(root=None)),
    )
    workspace = SimpleNamespace(
        service_manager=SimpleNamespace(services={"game_service": service})
    )
    payload = {"content_parts": [{"text": "damage formula"}], "meta": {}}

    monkeypatch.setattr(
        console_router_module,
        "unified_search",
        lambda *args, **kwargs: (_ for _ in ()).throw(AssertionError("should not call unified_search")),
        raising=False,
    )
    monkeypatch.setattr(
        console_router_module,
        "build_current_release_context",
        lambda *args, **kwargs: {
            "mode": "no_current_release",
            "query": "damage formula",
            "release_id": None,
            "built_at": None,
            "chunks": [],
            "citations": [],
        },
    )

    await _augment_chat_mode_context(_FakeRequest("doc"), workspace, payload)

    assert payload["meta"]["formal_knowledge"]["status"] == "no_current_release"
    assert payload["meta"]["formal_knowledge"]["legacy_fallback_used"] is False
    assert payload["content_parts"][0]["text"] == "damage formula"
