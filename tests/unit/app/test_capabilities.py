from __future__ import annotations

from types import SimpleNamespace

import pytest
from fastapi import FastAPI, HTTPException
from starlette.requests import Request

from ltclaw_gy_x.app.capabilities import require_capability


_UNSET = object()


def _request(*, state_capabilities=_UNSET, user=_UNSET, app_capabilities=_UNSET) -> Request:
    app = FastAPI()
    if app_capabilities is not _UNSET:
        app.state.capabilities = app_capabilities
    scope = {
        'type': 'http',
        'headers': [],
        'method': 'GET',
        'path': '/',
        'query_string': b'',
        'app': app,
        'state': {},
    }
    request = Request(scope)
    if state_capabilities is not _UNSET:
        request.state.capabilities = state_capabilities
    if user is not _UNSET:
        request.state.user = user
    return request


def test_require_capability_allows_local_trusted_fallback_without_context():
    request = _request()

    assert require_capability(request, 'knowledge.build') is None


def test_require_capability_allows_request_state_capabilities_when_present():
    request = _request(state_capabilities={'knowledge.build'})

    assert require_capability(request, 'knowledge.build') is None


def test_require_capability_rejects_missing_request_state_capability():
    request = _request(state_capabilities={'knowledge.publish'})

    with pytest.raises(HTTPException, match='Missing capability: knowledge.build') as exc_info:
        require_capability(request, 'knowledge.build')

    assert exc_info.value.status_code == 403


def test_require_capability_supports_user_capabilities_as_list_or_set():
    request_from_list = _request(user=SimpleNamespace(capabilities=['knowledge.build']))
    request_from_set = _request(user=SimpleNamespace(capabilities={'knowledge.build'}))

    assert require_capability(request_from_list, 'knowledge.build') is None
    assert require_capability(request_from_set, 'knowledge.build') is None


def test_require_capability_supports_user_dict_capabilities():
    request = _request(user={'capabilities': ['knowledge.build']})

    assert require_capability(request, 'knowledge.build') is None


def test_require_capability_supports_app_state_capabilities_as_set_or_list():
    request_from_set = _request(app_capabilities={'knowledge.build'})
    request_from_list = _request(app_capabilities=['knowledge.build'])

    assert require_capability(request_from_set, 'knowledge.build') is None
    assert require_capability(request_from_list, 'knowledge.build') is None


def test_require_capability_supports_mapping_format_and_filters_false_values():
    request = _request(app_capabilities={'knowledge.build': True, 'knowledge.publish': False})

    assert require_capability(request, 'knowledge.build') is None
    with pytest.raises(HTTPException, match='Missing capability: knowledge.publish') as exc_info:
        require_capability(request, 'knowledge.publish')

    assert exc_info.value.status_code == 403


def test_require_capability_allows_wildcard():
    request = _request(state_capabilities={'*'})

    assert require_capability(request, 'knowledge.build') is None
    assert require_capability(request, 'knowledge.publish') is None


def test_require_capability_prefers_request_state_over_user_and_app():
    request = _request(
        state_capabilities={'knowledge.publish'},
        user=SimpleNamespace(capabilities={'knowledge.build'}),
        app_capabilities={'knowledge.build'},
    )

    with pytest.raises(HTTPException, match='Missing capability: knowledge.build') as exc_info:
        require_capability(request, 'knowledge.build')

    assert exc_info.value.status_code == 403


def test_require_capability_prefers_user_over_app_when_request_state_absent():
    request = _request(
        user=SimpleNamespace(capabilities={'knowledge.publish'}),
        app_capabilities={'knowledge.build'},
    )

    with pytest.raises(HTTPException, match='Missing capability: knowledge.build') as exc_info:
        require_capability(request, 'knowledge.build')

    assert exc_info.value.status_code == 403
