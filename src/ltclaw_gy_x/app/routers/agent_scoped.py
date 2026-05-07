# -*- coding: utf-8 -*-
"""Agent-scoped router that wraps existing routers under /agents/{agentId}/

This provides agent isolation by injecting agentId into request.state,
allowing downstream APIs to access the correct agent context.
"""
from fastapi import APIRouter, Request
from starlette.middleware.base import (
    BaseHTTPMiddleware,
    RequestResponseEndpoint,
)
from starlette.responses import Response


class AgentContextMiddleware(BaseHTTPMiddleware):
    """Middleware to inject agentId into request.state."""

    async def dispatch(
        self,
        request: Request,
        call_next: RequestResponseEndpoint,
    ) -> Response:
        """Extract agentId and root_session_id from path/headers."""
        import logging
        from ..agent_context import set_current_agent_id

        logger = logging.getLogger(__name__)
        agent_id = None

        # Priority 1: Extract agentId from path: /api/agents/{agentId}/...
        path_parts = request.url.path.split("/")
        if len(path_parts) >= 4 and path_parts[1] == "api":
            if path_parts[2] == "agents":
                agent_id = path_parts[3]
                request.state.agent_id = agent_id
                logger.debug(
                    "AgentContextMiddleware: agent_id=%s from path=%s",
                    agent_id,
                    request.url.path,
                )

        # Priority 2: Check X-Agent-Id header
        if not agent_id:
            agent_id = request.headers.get("X-Agent-Id")

        if agent_id:
            set_current_agent_id(agent_id)

        # Extract X-Root-Session-Id header for cross-session approval routing
        root_session_id = request.headers.get("X-Root-Session-Id")
        if root_session_id:
            if not hasattr(request, "request_context"):
                request.request_context = {}
            request.request_context["root_session_id"] = root_session_id
            logger.debug(
                "AgentContextMiddleware: root_session_id=%s",
                root_session_id[:12],
            )

        response = await call_next(request)
        return response


def create_agent_scoped_router() -> APIRouter:
    """Create router that wraps all existing routers under /agents/{agentId}/."""
    from .skills import router as skills_router
    from .tools import router as tools_router
    from .config import router as config_router
    from .mcp import router as mcp_router
    from .workspace import router as workspace_router
    from ..crons.api import router as cron_router
    from ..runner.api import router as chats_router
    from .console import router as console_router
    from .plugins import router as plugins_router
    from .plan import router as plan_router
    from .game_project import router as game_project_router
    from .game_index import router as game_index_router
    from .game_doc_library import router as game_doc_library_router
    from .game_knowledge_base import router as game_knowledge_base_router
    from .game_knowledge_release import router as game_knowledge_release_router
    from .game_knowledge_release_candidates import router as game_knowledge_release_candidates_router
    from .game_knowledge_test_plans import router as game_knowledge_test_plans_router
    from .game_knowledge_map import router as game_knowledge_map_router
    from .game_knowledge_query import router as game_knowledge_query_router
    from .game_knowledge_rag import router as game_knowledge_rag_router
    from .game_change import router as game_change_router
    from .game_svn import router as game_svn_router
    from .game_workbench import router as game_workbench_router
    from .game_workbench_cards import router as game_workbench_cards_router

    router = APIRouter(prefix="/agents/{agentId}", tags=["agent-scoped"])

    router.include_router(chats_router)
    router.include_router(config_router)
    router.include_router(cron_router)
    router.include_router(mcp_router)
    router.include_router(skills_router)
    router.include_router(tools_router)
    router.include_router(workspace_router)
    router.include_router(console_router)
    router.include_router(plugins_router)
    router.include_router(plan_router)
    router.include_router(game_project_router)
    router.include_router(game_index_router)
    router.include_router(game_doc_library_router)
    router.include_router(game_knowledge_base_router)
    router.include_router(game_knowledge_release_router)
    router.include_router(game_knowledge_release_candidates_router)
    router.include_router(game_knowledge_test_plans_router)
    router.include_router(game_knowledge_map_router)
    router.include_router(game_knowledge_query_router)
    router.include_router(game_knowledge_rag_router)
    router.include_router(game_change_router)
    router.include_router(game_svn_router)
    router.include_router(game_workbench_router)
    router.include_router(game_workbench_cards_router)

    return router
