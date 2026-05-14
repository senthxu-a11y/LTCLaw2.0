from __future__ import annotations

from dataclasses import dataclass
from collections.abc import Iterable, Mapping
from typing import Any

from fastapi import HTTPException, Request

from ..game.config import LocalAgentProfile

LOCAL_CAPABILITY_CATALOG: tuple[str, ...] = (
    'knowledge.read',
    'knowledge.build',
    'knowledge.publish',
    'knowledge.map.read',
    'knowledge.map.edit',
    'knowledge.candidate.read',
    'knowledge.candidate.write',
    'workbench.read',
    'workbench.test.write',
    'workbench.test.export',
    'workbench.source.write',
)

ROLE_TEMPLATES: dict[str, tuple[str, ...]] = {
    'viewer': (
        'knowledge.read',
        'knowledge.map.read',
        'knowledge.candidate.read',
        'workbench.read',
    ),
    'planner': (
        'knowledge.read',
        'knowledge.map.read',
        'knowledge.candidate.read',
        'workbench.read',
        'workbench.test.write',
        'workbench.test.export',
    ),
    'source_writer': (
        'knowledge.read',
        'knowledge.map.read',
        'knowledge.candidate.read',
        'workbench.read',
        'workbench.test.write',
        'workbench.test.export',
        'workbench.source.write',
    ),
    'admin': ('*',),
}


@dataclass(frozen=True)
class AgentCapabilityProfile:
    """Normalized local agent capability profile.

    This is a local trusted-flow boundary to prevent accidental misuse. It is
    not a server-side security model.
    """

    agent_id: str
    display_name: str
    role: str
    capabilities: tuple[str, ...]


def get_role_template_capabilities(role: str | None) -> tuple[str, ...]:
    normalized_role = str(role or '').strip().lower() or 'viewer'
    return ROLE_TEMPLATES.get(normalized_role, ROLE_TEMPLATES['viewer'])


def map_legacy_my_role(my_role: str | None) -> str:
    normalized_role = str(my_role or '').strip().lower()
    if normalized_role == 'maintainer':
        return 'admin'
    if normalized_role == 'planner':
        return 'planner'
    return 'viewer'


def build_agent_capability_profile(
    *,
    agent_id: str,
    display_name: str,
    local_profile: LocalAgentProfile | Mapping[str, Any] | None = None,
    legacy_my_role: str | None = None,
) -> AgentCapabilityProfile:
    profile_agent_id = agent_id
    profile_display_name = display_name
    profile_role: str | None = None
    explicit_capabilities: set[str] | None = None

    if isinstance(local_profile, LocalAgentProfile):
        profile_agent_id = local_profile.agent_id or agent_id
        profile_display_name = local_profile.display_name or display_name
        profile_role = local_profile.role
        explicit_capabilities = _normalize_capabilities(local_profile.capabilities)
    elif isinstance(local_profile, Mapping):
        profile_agent_id = str(local_profile.get('agent_id') or agent_id)
        profile_display_name = str(local_profile.get('display_name') or display_name)
        profile_role = str(local_profile.get('role') or '') or None
        explicit_capabilities = _normalize_capabilities(local_profile.get('capabilities'))

    role = profile_role or map_legacy_my_role(legacy_my_role)
    if explicit_capabilities:
        capabilities = explicit_capabilities
    else:
        capabilities = set(get_role_template_capabilities(role))

    ordered_capabilities = tuple(sorted(capabilities, key=lambda item: (item != '*', item)))
    return AgentCapabilityProfile(
        agent_id=profile_agent_id,
        display_name=profile_display_name,
        role=role,
        capabilities=ordered_capabilities,
    )


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
