from __future__ import annotations

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
    assert '/agents/{agentId}/game/knowledge/map/candidate' in paths
