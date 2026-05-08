from __future__ import annotations

from collections.abc import Iterable, Mapping
from typing import Any

from fastapi import HTTPException, Request


def require_capability(request: Request, capability: str) -> None:
    """Require a capability when explicit capability context is available.

    In local trusted mode there may be no auth or capability context at all.
    When no capability context is present, this helper intentionally allows the
    request so existing single-user and local-dev flows keep working.
    """

    capabilities = _resolve_request_capabilities(request)
    if capabilities is None:
        return
    if capability in capabilities or '*' in capabilities:
        return
    raise HTTPException(status_code=403, detail=f'Missing capability: {capability}')


def _resolve_request_capabilities(request: Request) -> set[str] | None:
    state_caps = _normalize_capabilities(getattr(request.state, 'capabilities', None))
    if state_caps is not None:
        return state_caps

    user = getattr(request.state, 'user', None)
    user_caps = _normalize_capabilities(_extract_capabilities_attr(user))
    if user_caps is not None:
        return user_caps

    app_caps = _normalize_capabilities(getattr(request.app.state, 'capabilities', None))
    if app_caps is not None:
        return app_caps

    return None


def _extract_capabilities_attr(value: Any) -> Any:
    if value is None:
        return None
    if isinstance(value, Mapping):
        return value.get('capabilities')
    return getattr(value, 'capabilities', None)


def _normalize_capabilities(value: Any) -> set[str] | None:
    if value is None:
        return None
    if isinstance(value, str):
        return {value}
    if isinstance(value, Mapping):
        return {str(key) for key, enabled in value.items() if enabled}
    if isinstance(value, Iterable):
        return {str(item) for item in value}
    return {str(value)}
