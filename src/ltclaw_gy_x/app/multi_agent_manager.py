# -*- coding: utf-8 -*-
"""MultiAgentManager: manages the lifecycle of multiple agent Workspaces.

Lazy-loads, reloads and shuts down per-agent Workspace instances, while
keeping concurrent ``get_agent`` calls coordinated via an internal lock plus
per-agent pending-start events.
"""
from __future__ import annotations

import asyncio
import logging
from typing import Dict, Optional, Set

from fastapi import HTTPException

from ..config.utils import load_config

logger = logging.getLogger(__name__)


class MultiAgentManager:
    """Owns the per-agent Workspace map and lifecycle."""

    def __init__(self) -> None:
        self._agents = {}
        self._lock = asyncio.Lock()
        self._pending_starts: Dict[str, asyncio.Event] = {}
        self._cleanup_tasks: Set[asyncio.Task] = set()

    @property
    def agents(self):
        return self._agents

    # ------------------------------------------------------------------
    # Lookup / lazy start
    # ------------------------------------------------------------------
    async def get_agent(self, agent_id):
        """Return the Workspace for *agent_id*, starting it on first use."""
        # Fast path: already loaded.
        ws = self._agents.get(agent_id)
        if ws is not None:
            return ws

        async with self._lock:
            ws = self._agents.get(agent_id)
            if ws is not None:
                return ws

            pending = self._pending_starts.get(agent_id)
            if pending is not None:
                # Another coroutine is bringing this agent up; wait outside
                # the lock and re-check.
                event = pending
            else:
                config = load_config()
                profile = config.agents.profiles.get(agent_id)
                if profile is None:
                    raise HTTPException(
                        status_code=404,
                        detail=f"Agent profile not found: {agent_id}",
                    )
                if not profile.enabled:
                    raise HTTPException(
                        status_code=403,
                        detail=f"Agent is disabled: {agent_id}",
                    )

                event = asyncio.Event()
                self._pending_starts[agent_id] = event
                pending = None

        if pending is not None:
            await event.wait()
            ws = self._agents.get(agent_id)
            if ws is None:
                raise HTTPException(
                    status_code=500,
                    detail=f"Failed to start agent: {agent_id}",
                )
            return ws

        # We are the first coroutine: actually create + start the workspace.
        try:
            config = load_config()
            agent_ref = config.agents.profiles[agent_id]
            from .workspace.workspace import Workspace
            workspace = Workspace(
                agent_id=agent_id,
                workspace_dir=agent_ref.workspace_dir,
            )
            workspace.set_manager(self)
            await workspace.start()
        except Exception:
            async with self._lock:
                self._pending_starts.pop(agent_id, None)
            event.set()
            raise

        async with self._lock:
            self._agents[agent_id] = workspace
            self._pending_starts.pop(agent_id, None)
        event.set()
        logger.info("Started agent workspace: %s", agent_id)
        return workspace

    # ------------------------------------------------------------------
    # Bulk start
    # ------------------------------------------------------------------
    async def start_all_configured_agents(self) -> None:
        """Eagerly start every enabled profile in config.agents.profiles."""
        config = load_config()
        agent_ids = [
            aid for aid, ref in config.agents.profiles.items() if ref.enabled
        ]
        if not agent_ids:
            logger.info("No enabled agent profiles configured")
            return

        logger.info("Starting %d configured agent(s): %s", len(agent_ids), agent_ids)
        results = await asyncio.gather(
            *(self.get_agent(aid) for aid in agent_ids),
            return_exceptions=True,
        )
        for aid, res in zip(agent_ids, results):
            if isinstance(res, Exception):
                logger.error("Failed to start agent %s: %s", aid, res)

    # ------------------------------------------------------------------
    # Reload
    # ------------------------------------------------------------------
    async def reload_agent(self, agent_id: str) -> bool:
        """Reload an agent's workspace, reusing reusable services where safe.

        Returns ``True`` on success, ``False`` if the agent is not currently
        loaded or reload failed.
        """
        old_ws = self._agents.get(agent_id)
        if old_ws is None:
            logger.warning("reload_agent: agent not loaded: %s", agent_id)
            return False

        try:
            config = load_config()
            agent_ref = config.agents.profiles.get(agent_id)
            if agent_ref is None:
                logger.error("reload_agent: profile vanished: %s", agent_id)
                return False

            from .workspace.workspace import Workspace
            new_ws = Workspace(
                agent_id=agent_id,
                workspace_dir=agent_ref.workspace_dir,
            )
            new_ws.set_manager(self)
            try:
                reusable = old_ws.service_manager.get_reusable_services()
                if reusable:
                    await new_ws.set_reusable_components(reusable)
            except Exception as e:
                logger.warning(
                    "reload_agent: failed to transfer reusable services: %s",
                    e,
                )
            await new_ws.start()
        except Exception as e:
            logger.error("reload_agent: failed to start new workspace: %s", e)
            return False

        async with self._lock:
            self._agents[agent_id] = new_ws

        # Stop the old workspace (graceful when active tasks present).
        task = asyncio.create_task(self._graceful_stop_old_instance(old_ws))
        self._cleanup_tasks.add(task)
        task.add_done_callback(self._cleanup_tasks.discard)

        logger.info("Reloaded agent workspace: %s", agent_id)
        return True

    async def _graceful_stop_old_instance(self, old_ws):
        try:
            tracker = old_ws.task_tracker
            if tracker.has_active_tasks():
                logger.info(
                    "Old workspace %s has active tasks; waiting up to 60s",
                    old_ws.agent_id,
                )
                try:
                    await tracker.wait_all_done(timeout=60)
                except Exception as e:
                    logger.warning("wait_all_done failed: %s", e)
                await old_ws.stop(final=False)
            else:
                await old_ws.stop(final=False)
        except Exception as e:
            logger.error(
                "Error while stopping old workspace %s: %s",
                old_ws.agent_id, e,
            )

    # ------------------------------------------------------------------
    # Stop
    # ------------------------------------------------------------------
    async def stop_agent(self, agent_id: str) -> None:
        async with self._lock:
            ws = self._agents.pop(agent_id, None)
        if ws is None:
            return
        try:
            await ws.stop(final=True)
            logger.info("Stopped agent workspace: %s", agent_id)
        except Exception as e:
            logger.error("Error stopping agent %s: %s", agent_id, e)

    async def stop_all(self) -> None:
        async with self._lock:
            agents = list(self._agents.items())
            self._agents.clear()
        for agent_id, ws in agents:
            try:
                await ws.stop(final=True)
            except Exception as e:
                logger.error("Error stopping agent %s: %s", agent_id, e)

        # Wait briefly for any in-flight cleanup tasks
        if self._cleanup_tasks:
            try:
                await asyncio.wait_for(
                    asyncio.gather(*self._cleanup_tasks, return_exceptions=True),
                    timeout=5,
                )
            except asyncio.TimeoutError:
                logger.warning("Some cleanup tasks did not finish within timeout")
        self._cleanup_tasks.clear()

    # ------------------------------------------------------------------
    # Misc
    # ------------------------------------------------------------------
    def get_loaded_agent_ids(self) -> list[str]:
        return list(self._agents.keys())

    def __repr__(self) -> str:
        loaded = list(self._agents.keys())
        return f"MultiAgentManager(loaded_agents={loaded})"

# Module-level singleton accessor used by tools that don't receive the
# FastAPI request directly (e.g. agent tool functions). The active manager
# is registered at app startup via ``set_active_manager``.
_ACTIVE_MANAGER: Optional["MultiAgentManager"] = None


def set_active_manager(manager: "MultiAgentManager") -> None:
    global _ACTIVE_MANAGER
    _ACTIVE_MANAGER = manager


def get_active_manager() -> Optional["MultiAgentManager"]:
    return _ACTIVE_MANAGER