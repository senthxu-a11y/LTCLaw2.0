from __future__ import annotations

from ltclaw_gy_x.app.routers import router as api_router
from ltclaw_gy_x.app.routers.agent_scoped import create_agent_scoped_router


def test_agent_scoped_router_includes_knowledge_release_and_rag_routes():
    router = create_agent_scoped_router()
    paths = {getattr(route, 'path', '') for route in router.routes}

    assert '/agents/{agentId}/game/knowledge/releases' in paths
    assert '/agents/{agentId}/game/knowledge/releases/build-from-current-indexes' in paths
    assert '/agents/{agentId}/game/knowledge/release-candidates' in paths
    assert '/agents/{agentId}/game/knowledge/test-plans' in paths
    assert '/agents/{agentId}/game/knowledge/query' in paths
    assert '/agents/{agentId}/game/knowledge/rag/context' in paths
    assert '/agents/{agentId}/game/knowledge/rag/answer' in paths
    assert '/agents/{agentId}/game/knowledge/map' in paths
    assert '/agents/{agentId}/game/knowledge/map/build-readiness' in paths
    assert '/agents/{agentId}/game/knowledge/map/candidate' in paths
    assert '/agents/{agentId}/game/knowledge/map/candidate/from-source' in paths
    assert '/agents/{agentId}/game/knowledge/map/cold-start-jobs' in paths
    assert '/agents/{agentId}/game/knowledge/map/cold-start-jobs/{job_id}' in paths
    assert '/agents/{agentId}/game/knowledge/map/cold-start-jobs/{job_id}/cancel' in paths
    assert '/agents/{agentId}/game/knowledge/canonical/rebuild' in paths


def test_api_router_includes_canonical_rebuild_route():
    paths = {getattr(route, 'path', '') for route in api_router.routes}

    assert '/game/knowledge/canonical/rebuild' in paths


def test_api_router_does_not_mount_p0_04_map_routes_at_top_level():
    paths = {getattr(route, 'path', '') for route in api_router.routes}

    assert '/game/knowledge/map/build-readiness' not in paths
    assert '/game/knowledge/map/candidate/from-source' not in paths
    assert '/game/knowledge/map/cold-start-jobs' not in paths
