# -*- coding: utf-8 -*-
"""Console APIs: push messages, chat, and file upload for chat."""
from __future__ import annotations

import json
import logging
import re
import uuid
from pathlib import Path
from typing import AsyncGenerator, Union

from fastapi import APIRouter, File, HTTPException, Query, Request, UploadFile
from starlette.responses import StreamingResponse

from agentscope_runtime.engine.schemas.agent_schemas import AgentRequest
from ...game.knowledge_rag_context import build_current_release_context
from ...utils.logging import LOG_FILE_PATH
from ..agent_context import get_agent_for_request


logger = logging.getLogger(__name__)

router = APIRouter(prefix="/console", tags=["console"])

MAX_UPLOAD_BYTES = 10 * 1024 * 1024
MAX_DEBUG_LOG_LINES = 1000


def _safe_filename(name: str) -> str:
    """Safe basename, alphanumeric/./-/_, max 200 chars."""
    base = Path(name).name if name else "file"
    return re.sub(r"[^\w.\-]", "_", base)[:200] or "file"


def _normalize_content_parts(content_parts: list) -> list:
    """Convert plain frontend text payloads into runtime TextContent."""
    try:
        from agentscope_runtime.engine.schemas.agent_schemas import (
            ContentType,
            TextContent,
        )
    except Exception:
        return content_parts

    normalized = []
    for part in content_parts:
        if isinstance(part, str):
            normalized.append(TextContent(type=ContentType.TEXT, text=part))
            continue
        if isinstance(part, dict):
            text = part.get("text")
            if isinstance(text, str):
                normalized.append(TextContent(type=ContentType.TEXT, text=text))
                continue
        normalized.append(part)
    return normalized


def _extract_session_and_payload(request_data: Union[AgentRequest, dict]):
    """Extract run_key (ChatSpec.id), session_id, and native payload.

    run_key must be ChatSpec.id (chat_id) so it matches list_chats/get_chat.
    """
    if isinstance(request_data, AgentRequest):
        channel_id = getattr(request_data, "channel", None) or "console"
        sender_id = request_data.user_id or "default"
        session_id = request_data.session_id or "default"
        content_parts = (
            list(request_data.input[0].content) if request_data.input else []
        )
    else:
        channel_id = request_data.get("channel", "console")
        sender_id = request_data.get("user_id", "default")
        session_id = request_data.get("session_id", "default")
        input_data = request_data.get("input", [])
        content_parts = []
        for content_part in input_data:
            if hasattr(content_part, "content"):
                content_parts.extend(list(content_part.content or []))
            elif isinstance(content_part, dict) and "content" in content_part:
                content_parts.extend(content_part["content"] or [])
        content_parts = _normalize_content_parts(content_parts)

    native_payload = {
        "channel_id": channel_id,
        "sender_id": sender_id,
        "content_parts": content_parts,
        "meta": {
            "session_id": session_id,
            "user_id": sender_id,
        },
    }
    return native_payload


# Chat mode prefix injected into the first text part when X-Chat-Mode is set.
# Keep aligned with console/src/pages/Chat/components/ChatModeToolbar.tsx
_CHAT_MODE_PREFIX: dict[str, str] = {
    "free": "",
    "design": (
        "[????]??????????????/??/??/??????????????"
    ),
    "numeric": (
        "[????]????????????/??/???????????????? changeset ???"
    ),
    "doc": (
        "[????]?????????????? Markdown ???frontmatter????????????"
    ),
    "kb": (
        "[?????]?????????????????????????????????????"
    ),
}


def _inject_chat_mode_prefix(request: "Request", native_payload: dict) -> None:
    """Prepend a mode prefix to the first text content based on X-Chat-Mode."""
    mode = (request.headers.get("X-Chat-Mode") or "").strip().lower()
    if not mode or mode == "free":
        return
    prefix = _CHAT_MODE_PREFIX.get(mode)
    if not prefix:
        return
    parts = native_payload.get("content_parts") or []
    for i, part in enumerate(parts):
        text = getattr(part, "text", None)
        if isinstance(text, str):
            try:
                part.text = f"{prefix}\n\n{text}" if text else prefix
                return
            except Exception:
                pass
        if isinstance(part, dict):
            t = part.get("text")
            if isinstance(t, str):
                part["text"] = f"{prefix}\n\n{t}" if t else prefix
                return
        if isinstance(part, str):
            parts[i] = f"{prefix}\n\n{part}" if part else prefix
            return
    try:
        from agentscope_runtime.engine.schemas.agent_schemas import TextContent

        parts.insert(0, TextContent(text=prefix))
        native_payload["content_parts"] = parts
    except Exception:
        parts.insert(0, prefix)
        native_payload["content_parts"] = parts


def _extract_text_query(native_payload: dict) -> str:
    parts = native_payload.get("content_parts") or []
    texts: list[str] = []
    for part in parts:
        text = getattr(part, "text", None)
        if isinstance(text, str) and text.strip():
            texts.append(text.strip())
            continue
        if isinstance(part, dict):
            candidate = part.get("text")
            if isinstance(candidate, str) and candidate.strip():
                texts.append(candidate.strip())
                continue
        if isinstance(part, str) and part.strip():
            texts.append(part.strip())
    return "\n".join(texts).strip()


def _project_root_for_chat(game_service) -> Path | None:
    runtime_root = getattr(game_service, "_runtime_svn_root", None)
    if callable(runtime_root):
        root = runtime_root()
        if root is not None:
            return Path(root)

    user_config = getattr(game_service, "user_config", None)
    local_root = getattr(user_config, "svn_local_root", None)
    if local_root:
        return Path(local_root).expanduser()

    project_config = getattr(game_service, "project_config", None)
    svn_config = getattr(project_config, "svn", None)
    project_root = getattr(svn_config, "root", None)
    if project_root and "://" not in str(project_root):
        return Path(project_root).expanduser()
    return None


def _record_formal_knowledge_status(native_payload: dict, context_payload: dict, *, status: str) -> None:
    meta = native_payload.setdefault("meta", {})
    meta["formal_knowledge"] = {
        "source": "current_release",
        "status": status,
        "query": context_payload.get("query", ""),
        "release_id": context_payload.get("release_id"),
        "built_at": context_payload.get("built_at"),
        "chunk_count": len(context_payload.get("chunks") or []),
        "citation_count": len(context_payload.get("citations") or []),
        "legacy_fallback_used": False,
    }


def _build_formal_chat_context_block(context_payload: dict, *, max_items: int) -> str:
    chunks = list(context_payload.get("chunks") or [])[:max_items]
    if not chunks:
        return ""

    citations_by_id = {
        citation.get("citation_id"): citation
        for citation in context_payload.get("citations") or []
        if citation.get("citation_id")
    }
    lines = [
        "[Formal Knowledge Context] Current-release evidence only. No legacy KB/retrieval fallback.",
        f"release_id={context_payload.get('release_id') or 'unknown'}",
    ]
    for index, chunk in enumerate(chunks, start=1):
        citation = citations_by_id.get(chunk.get("citation_id"), {})
        title = citation.get("title") or chunk.get("source_type") or "context"
        source_path = citation.get("source_path") or citation.get("artifact_path") or ""
        text = str(chunk.get("text") or "").strip()
        if len(text) > 280:
            text = text[:280].rstrip() + "..."
        lines.append(f"{index}. [{chunk.get('source_type')}] {title} :: {source_path}")
        if text:
            lines.append(text)
    return "\n".join(lines)


async def _augment_chat_mode_context(request: "Request", workspace, native_payload: dict) -> None:
    mode = (request.headers.get("X-Chat-Mode") or "").strip().lower()
    native_payload.setdefault("meta", {})["chat_mode"] = mode or "free"
    if mode not in {"kb", "doc", "numeric"}:
        return
    game_service = workspace.service_manager.services.get("game_service")
    if game_service is None or not getattr(game_service, "configured", False):
        _record_formal_knowledge_status(native_payload, {"query": _extract_text_query(native_payload)}, status="service_unavailable")
        return
    query = _extract_text_query(native_payload)
    if not query:
        return
    top_k = 6 if mode == "numeric" else 8
    project_root = _project_root_for_chat(game_service)
    if project_root is None:
        _record_formal_knowledge_status(native_payload, {"query": query}, status="no_project_root")
        return

    payload = build_current_release_context(project_root, query, max_chunks=top_k, max_chars=12000)
    if payload.get("mode") != "context":
        _record_formal_knowledge_status(native_payload, payload, status=str(payload.get("mode") or "no_current_release"))
        return

    context_block = _build_formal_chat_context_block(payload, max_items=top_k)
    if not context_block:
        _record_formal_knowledge_status(native_payload, payload, status="insufficient_context")
        return
    _record_formal_knowledge_status(native_payload, payload, status="context")
    parts = native_payload.get("content_parts") or []
    for i, part in enumerate(parts):
        text = getattr(part, "text", None)
        if isinstance(text, str):
            try:
                part.text = f"{context_block}\n\n{text}" if text else context_block
                return
            except Exception:
                pass
        if isinstance(part, dict):
            candidate = part.get("text")
            if isinstance(candidate, str):
                part["text"] = f"{context_block}\n\n{candidate}" if candidate else context_block
                return
        if isinstance(part, str):
            parts[i] = f"{context_block}\n\n{part}" if part else context_block
            return
    try:
        from agentscope_runtime.engine.schemas.agent_schemas import TextContent

        parts.insert(0, TextContent(text=context_block))
        native_payload["content_parts"] = parts
    except Exception:
        parts.insert(0, context_block)
        native_payload["content_parts"] = parts


def _tail_text_file(
    path: Path,
    *,
    lines: int = 200,
    max_bytes: int = 512 * 1024,
) -> str:
    """Read the last N lines from a text file with bounded memory."""
    path = Path(path)
    if not path.exists() or not path.is_file():
        return ""
    try:
        size = path.stat().st_size
        if size == 0:
            return ""
        with open(path, "rb") as f:
            if size <= max_bytes:
                data = f.read()
            else:
                f.seek(max(size - max_bytes, 0))
                data = f.read()
        text = data.decode("utf-8", errors="replace")
        return "\n".join(text.splitlines()[-lines:])
    except Exception:
        logger.exception("Failed to read backend debug log file")
        return ""


@router.post(
    "/chat",
    status_code=200,
    summary="Chat with console (streaming response)",
    description="Agent API Request Format. See runtime.agentscope.io. "
    "Use body.reconnect=true to attach to a running stream.",
)
async def post_console_chat(
    request_data: Union[AgentRequest, dict],
    request: Request,
) -> StreamingResponse:
    """Stream agent response. Run continues in background after disconnect.
    Stop via POST /console/chat/stop. Reconnect with body.reconnect=true.
    """
    workspace = await get_agent_for_request(request)
    console_channel = await workspace.channel_manager.get_channel("console")
    if console_channel is None:
        raise HTTPException(
            status_code=503,
            detail="Channel Console not found",
        )
    try:
        native_payload = _extract_session_and_payload(request_data)
        _inject_chat_mode_prefix(request, native_payload)
        await _augment_chat_mode_context(request, workspace, native_payload)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e)) from e
    session_id = console_channel.resolve_session_id(
        sender_id=native_payload["sender_id"],
        channel_meta=native_payload["meta"],
    )
    name = "New Chat"
    if len(native_payload["content_parts"]) > 0:
        content = native_payload["content_parts"][0]
        if content:
            if isinstance(content, str):
                name = content[:10]
            elif hasattr(content, "text"):
                name = content.text[:10]
            else:
                name = str(content)[:10]
        else:
            name = "Media Message"
    chat = await workspace.chat_manager.get_or_create_chat(
        session_id,
        native_payload["sender_id"],
        native_payload["channel_id"],
        name=name,
    )
    tracker = workspace.task_tracker

    is_reconnect = False
    if isinstance(request_data, dict):
        is_reconnect = request_data.get("reconnect") is True

    if is_reconnect:
        queue = await tracker.attach(chat.id)
        if queue is None:
            return
    else:
        queue, _ = await tracker.attach_or_start(
            chat.id,
            native_payload,
            console_channel.stream_one,
        )

    async def event_generator() -> AsyncGenerator[str, None]:
        # Hold iterator so finally can aclose(); guarantees stream_from_queue's
        # finally (detach_subscriber) on client abort / generator teardown.
        stream_it = tracker.stream_from_queue(queue, chat.id)
        try:
            try:
                async for event_data in stream_it:
                    yield event_data
            except Exception as e:
                logger.exception("Console chat stream error")
                yield f"data: {json.dumps({'error': str(e)})}\n\n"
        finally:
            await stream_it.aclose()

    return StreamingResponse(
        event_generator(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
        },
    )


@router.post(
    "/chat/stop",
    status_code=200,
    summary="Stop running console chat",
)
async def post_console_chat_stop(
    request: Request,
    chat_id: str = Query(..., description="Chat id (ChatSpec.id) to stop"),
) -> dict:
    """Stop the running chat. Only stops when called."""
    logger.debug("[STOP API] Received stop request for chat_id=%s", chat_id)
    workspace = await get_agent_for_request(request)

    # Try to stop with the provided chat_id first
    logger.debug(
        "[STOP API] Got workspace, calling task_tracker.request_stop...",
    )
    stopped = await workspace.task_tracker.request_stop(chat_id)

    # If not found, the chat_id might be a session_id (timestamp)
    # Try to resolve it to the actual chat UUID
    if not stopped:
        logger.debug(
            "[STOP API] chat_id not found in tracker, trying to resolve "
            "from session_id...",
        )
        chat_manager = getattr(workspace.runner, "_chat_manager", None)
        if chat_manager:
            resolved_chat_id = await chat_manager.get_chat_id_by_session(
                session_id=chat_id,
                channel="console",
            )
            if resolved_chat_id:
                logger.debug(
                    "[STOP API] Resolved session_id=%s to chat_id=%s",
                    chat_id[:12] if len(chat_id) >= 12 else chat_id,
                    resolved_chat_id,
                )
                stopped = await workspace.task_tracker.request_stop(
                    resolved_chat_id,
                )

    logger.debug(
        "[STOP API] task_tracker.request_stop returned: stopped=%s",
        stopped,
    )
    return {"stopped": stopped}


@router.post("/upload", response_model=dict, summary="Upload file for chat")
async def post_console_upload(
    request: Request,
    file: UploadFile = File(..., description="File to attach"),
) -> dict:
    """Save to console channel media_dir."""

    workspace = await get_agent_for_request(request)
    console_channel = await workspace.channel_manager.get_channel("console")
    if console_channel is None:
        raise HTTPException(
            status_code=503,
            detail="Channel Console not found",
        )
    media_dir = console_channel.media_dir
    media_dir.mkdir(parents=True, exist_ok=True)
    data = await file.read()
    if len(data) > MAX_UPLOAD_BYTES:
        raise HTTPException(
            status_code=400,
            detail="File too large (max "
            f"{MAX_UPLOAD_BYTES // (1024 * 1024)} MB)",
        )
    safe_name = _safe_filename(file.filename or "file")
    stored_name = f"{uuid.uuid4().hex}_{safe_name}"

    path = (media_dir / stored_name).resolve()
    path.write_bytes(data)
    return {
        "url": path,
        "file_name": safe_name,
        "size": len(data),
    }


@router.get(
    "/debug/backend-logs",
    response_model=dict,
    summary="Read backend daemon logs for debug page",
)
async def get_backend_debug_logs(
    lines: int = Query(
        200,
        ge=20,
        le=MAX_DEBUG_LOG_LINES,
        description="Number of trailing log lines to return",
    ),
) -> dict:
    """Return the tail of the project log file for the debug UI."""
    log_path = LOG_FILE_PATH.resolve()
    try:
        st = log_path.stat()
        return {
            "path": str(log_path),
            "exists": True,
            "lines": lines,
            "updated_at": st.st_mtime,
            "size": st.st_size,
            "content": _tail_text_file(log_path, lines=lines),
        }
    except FileNotFoundError:
        return {
            "path": str(log_path),
            "exists": False,
            "lines": lines,
            "updated_at": None,
            "size": 0,
            "content": "",
        }


@router.get("/push-messages")
async def get_push_messages(
    session_id: str | None = Query(None, description="Optional session id"),
):
    """
    Return pending push messages and ALL approval requests.

    Messages:
    - With session_id: consumed messages for that session
    - Without session_id: recent messages (all sessions, last 60s)

    Approvals:
    - Always returns ALL pending approvals across all sessions
    - Frontend filters by current session_id for display
    - Includes session_id in each approval for filtering
    """
    from ..console_push_store import get_recent, take
    from ..approvals import get_approval_service

    # Get messages (session-specific or global)
    if session_id:
        messages = await take(session_id)
    else:
        messages = await get_recent()

    # Get ALL pending approvals (not filtered by session)
    approval_svc = get_approval_service()
    # pylint: disable=protected-access
    async with approval_svc._lock:
        all_pending = list(approval_svc._pending.values())

    # Serialize approval data with root_session_id for frontend filtering
    approvals_data = [
        {
            "request_id": p.request_id,
            "session_id": p.session_id,
            "root_session_id": p.root_session_id,
            "agent_id": p.agent_id,
            "tool_name": p.tool_name,
            "severity": p.severity,
            "findings_count": p.findings_count,
            "findings_summary": p.result_summary,
            "tool_params": p.extra.get("tool_call", {}).get("input", {}),
            "created_at": p.created_at,
            "timeout_seconds": p.timeout_seconds,
        }
        for p in all_pending
    ]

    return {"messages": messages, "pending_approvals": approvals_data}
