from __future__ import annotations

import asyncio
import logging
from concurrent.futures import ThreadPoolExecutor
from dataclasses import dataclass
from typing import Any

from .config import DEFAULT_MODEL_TYPE, SUPPORTED_MODEL_TYPES, ModelSlotRef, ProjectConfig

logger = logging.getLogger(__name__)


@dataclass(frozen=True)
class UnifiedModelResult:
    ok: bool
    model_type: str
    text: str = ""
    error_code: str | None = None
    message: str | None = None
    provider_id: str | None = None
    model_id: str | None = None


class UnifiedModelRouter:
    def __init__(
        self,
        *,
        provider_manager: Any = None,
        project_config: ProjectConfig | None = None,
        compatibility_router: Any = None,
    ) -> None:
        self._pm = provider_manager
        self._project_config = project_config
        self._compatibility_router = compatibility_router

    async def call_model(self, prompt: str, model_type: str = DEFAULT_MODEL_TYPE) -> str:
        result = await self.call_model_result(prompt, model_type=model_type)
        return result.text if result.ok else ""

    async def call_model_result(self, prompt: str, model_type: str = DEFAULT_MODEL_TYPE) -> UnifiedModelResult:
        normalized_model_type = _normalize_model_type(model_type)
        if self._compatibility_router is not None and hasattr(self._compatibility_router, "call_model_result"):
            try:
                result = await self._compatibility_router.call_model_result(prompt, model_type=normalized_model_type)
                if isinstance(result, UnifiedModelResult):
                    return result
            except Exception as exc:  # noqa: BLE001
                logger.warning("Compatibility router call_model_result failed (%s): %s", normalized_model_type, exc)
        if self._compatibility_router is not None and hasattr(self._compatibility_router, "call_model"):
            try:
                text = await self._compatibility_router.call_model(prompt, model_type=normalized_model_type)
                cleaned = str(text or "").strip()
                if not cleaned:
                    return UnifiedModelResult(
                        ok=False,
                        model_type=normalized_model_type,
                        error_code="empty_response",
                        message="Compatibility router returned an empty response.",
                    )
                return UnifiedModelResult(ok=True, model_type=normalized_model_type, text=cleaned)
            except Exception as exc:  # noqa: BLE001
                return UnifiedModelResult(
                    ok=False,
                    model_type=normalized_model_type,
                    error_code="provider_exception",
                    message=str(exc) or exc.__class__.__name__,
                )

        provider, provider_id, model_id = self._resolve_model_binding(normalized_model_type)
        if provider is None:
            if provider_id or model_id:
                return UnifiedModelResult(
                    ok=False,
                    model_type=normalized_model_type,
                    error_code="provider_not_configured",
                    message="Resolved model binding does not include a configured provider.",
                    provider_id=provider_id,
                    model_id=model_id,
                )
            return UnifiedModelResult(
                ok=False,
                model_type=normalized_model_type,
                error_code="no_active_model",
                message="No active model is configured for the requested model type.",
                provider_id=provider_id,
                model_id=model_id,
            )
        if not model_id:
            return UnifiedModelResult(
                ok=False,
                model_type=normalized_model_type,
                error_code="provider_not_configured",
                message="Resolved model binding does not include a model id.",
                provider_id=provider_id,
                model_id=model_id,
            )

        try:
            text = await _invoke_provider(provider, model_id, prompt)
        except Exception as exc:  # noqa: BLE001
            error_code = "provider_exception"
            message = str(exc) or exc.__class__.__name__
            if isinstance(exc, RuntimeError) and "not configured" in message.lower():
                error_code = "provider_not_configured"
            return UnifiedModelResult(
                ok=False,
                model_type=normalized_model_type,
                error_code=error_code,
                message=message,
                provider_id=provider_id,
                model_id=model_id,
            )

        cleaned = str(text or "").strip()
        if not cleaned:
            return UnifiedModelResult(
                ok=False,
                model_type=normalized_model_type,
                error_code="empty_response",
                message="Model returned an empty response.",
                provider_id=provider_id,
                model_id=model_id,
            )

        return UnifiedModelResult(
            ok=True,
            model_type=normalized_model_type,
            text=cleaned,
            provider_id=provider_id,
            model_id=model_id,
        )

    def call_model_blocking(self, prompt: str, model_type: str = DEFAULT_MODEL_TYPE) -> UnifiedModelResult:
        normalized_model_type = _normalize_model_type(model_type)
        try:
            asyncio.get_running_loop()
        except RuntimeError:
            return _run_call_model_result_blocking(
                self.call_model_result,
                prompt,
                normalized_model_type,
            )

        with ThreadPoolExecutor(max_workers=1) as executor:
            future = executor.submit(
                _run_call_model_result_blocking,
                self.call_model_result,
                prompt,
                normalized_model_type,
            )
            return future.result()

    def _resolve_model_binding(self, model_type: str) -> tuple[Any, str | None, str | None]:
        slot = self._project_model_slot(model_type)
        if slot is not None:
            provider = self._pm.get_provider(slot.provider_id) if self._pm is not None else None
            return provider, slot.provider_id, slot.model_id

        active = _resolve_active_model(self._pm)
        if active is None or self._pm is None:
            return None, None, None
        provider_id = getattr(active, "provider_id", None)
        provider = self._pm.get_provider(provider_id) if provider_id else None
        model_id = getattr(active, "model_id", None) or getattr(active, "model", None)
        return provider, provider_id, model_id

    def _project_model_slot(self, model_type: str) -> ModelSlotRef | None:
        project_models = getattr(self._project_config, "models", None) or {}
        slot = project_models.get(model_type)
        if slot is not None:
            return slot
        if model_type != DEFAULT_MODEL_TYPE:
            return project_models.get(DEFAULT_MODEL_TYPE)
        return None


def _normalize_model_type(model_type: str | None) -> str:
    normalized = str(model_type or "").strip() or DEFAULT_MODEL_TYPE
    if normalized in SUPPORTED_MODEL_TYPES:
        return normalized
    return DEFAULT_MODEL_TYPE


def _resolve_active_model(provider_manager: Any) -> Any:
    if provider_manager is None:
        return None
    active = getattr(provider_manager, "active_model", None)
    if active is None:
        getter = getattr(provider_manager, "get_active_model", None)
        if callable(getter):
            active = getter()
    return active


def _run_call_model_result_blocking(call_model_result: Any, prompt: str, model_type: str) -> UnifiedModelResult:
    policy = asyncio.get_event_loop_policy()
    previous_loop = _get_policy_loop(policy)
    loop = asyncio.new_event_loop()
    coroutine = None
    try:
        policy.set_event_loop(loop)
        coroutine = call_model_result(prompt, model_type=model_type)
        return loop.run_until_complete(coroutine)
    except Exception as exc:  # noqa: BLE001
        logger.warning("Blocking model bridge failed (%s): %s", model_type, exc)
        return UnifiedModelResult(
            ok=False,
            model_type=model_type,
            error_code="provider_exception",
            message="Blocking model bridge failed.",
        )
    finally:
        if asyncio.iscoroutine(coroutine):
            coroutine.close()
        try:
            loop.run_until_complete(loop.shutdown_asyncgens())
        except Exception:  # noqa: BLE001
            pass
        shutdown_default_executor = getattr(loop, "shutdown_default_executor", None)
        if callable(shutdown_default_executor):
            try:
                loop.run_until_complete(shutdown_default_executor())
            except Exception:  # noqa: BLE001
                pass
        policy.set_event_loop(previous_loop)
        loop.close()


def _get_policy_loop(policy: Any) -> Any:
    local_state = getattr(policy, "_local", None)
    if local_state is None:
        return None
    return getattr(local_state, "_loop", None)


async def _invoke_provider(provider: Any, model_id: str, prompt: str) -> str:
    provider_type = type(provider).__name__
    if provider_type == "AnthropicProvider":
        client = provider._client(timeout=60)
        resp = await client.messages.create(
            model=model_id,
            max_tokens=16384,
            messages=[{"role": "user", "content": prompt}],
        )
        parts = []
        for blk in (getattr(resp, "content", []) or []):
            tx = getattr(blk, "text", None)
            if tx:
                parts.append(tx)
        return "".join(parts)

    base_url = getattr(provider, "base_url", None)
    api_key = getattr(provider, "api_key", None)
    if not (base_url and api_key):
        raise RuntimeError("Provider is not configured with base_url/api_key")

    from openai import AsyncOpenAI

    client = AsyncOpenAI(base_url=base_url, api_key=api_key, timeout=60)
    resp = await client.chat.completions.create(
        model=model_id,
        messages=[{"role": "user", "content": prompt}],
        temperature=0.2,
    )
    choice = resp.choices[0] if resp.choices else None
    if choice and choice.message and choice.message.content:
        return choice.message.content
    return ""