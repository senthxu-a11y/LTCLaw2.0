# -*- coding: utf-8 -*-
"""Workspace: Encapsulates a complete independent agent runtime."""
import logging
from pathlib import Path
from typing import Optional

from ltclaw_gy_x.config.utils import load_config

from .service_manager import ServiceDescriptor, ServiceManager
from .service_factories import (
    create_mcp_service,
    create_chat_service,
    create_channel_service,
    create_agent_config_watcher,
    create_mcp_config_watcher,
    resolve_game_service_class,
)
from ..runner import AgentRunner
from ..runner.task_tracker import TaskTracker
from ..mcp import MCPClientManager
from ..crons.manager import CronManager
from ..crons.repo.json_repo import JsonJobRepository
from ...config.config import load_agent_config

logger = logging.getLogger(__name__)


class Workspace:
    def __init__(self, agent_id: str, workspace_dir: str):
        self.agent_id = agent_id
        self.workspace_dir = Path(workspace_dir).expanduser()
        self.workspace_dir.mkdir(parents=True, exist_ok=True)
        self._service_manager = ServiceManager(self)
        self._config = None
        self._started = False
        self._manager = None
        self._task_tracker = TaskTracker()
        self._register_services()
        logger.debug(f"Created Workspace: {agent_id} at {self.workspace_dir}")

    @property
    def service_manager(self) -> ServiceManager:
        return self._service_manager

    @property
    def runner(self) -> Optional[AgentRunner]:
        return self._service_manager.services.get("runner")

    @property
    def memory_manager(self):
        return self._service_manager.services.get("memory_manager")

    @property
    def context_manager(self):
        return self._service_manager.services.get("context_manager")

    @property
    def mcp_manager(self):
        return self._service_manager.services.get("mcp_manager")

    @property
    def chat_manager(self):
        return self._service_manager.services.get("chat_manager")

    @property
    def channel_manager(self):
        return self._service_manager.services.get("channel_manager")

    @property
    def cron_manager(self):
        return self._service_manager.services.get("cron_manager")

    @property
    def game_service(self):
        return self._service_manager.services.get("game_service")

    @property
    def task_tracker(self) -> TaskTracker:
        return self._task_tracker

    @property
    def config(self):
        if self._config is None:
            self._config = load_agent_config(self.agent_id)
        return self._config

    def set_manager(self, manager) -> None:
        self._manager = manager
        if self.runner is not None:
            self.runner._manager = manager

    def _register_services(self) -> None:
        from ...agents.memory.base_memory_manager import (
            get_memory_manager_backend,
        )
        from ...agents.context.base_context_manager import (
            get_context_manager_backend,
        )

        sm = self._service_manager

        sm.register(ServiceDescriptor(
            name="runner",
            service_class=AgentRunner,
            init_args=lambda ws: {
                "agent_id": ws.agent_id,
                "workspace_dir": ws.workspace_dir,
                "task_tracker": ws._task_tracker,
            },
            stop_method="stop",
            priority=10,
            concurrent_init=False,
        ))

        sm.register(ServiceDescriptor(
            name="memory_manager",
            service_class=lambda ws: get_memory_manager_backend(
                ws._config.running.memory_manager_backend,
            ),
            init_args=lambda ws: {
                "working_dir": str(ws.workspace_dir),
                "agent_id": ws.agent_id,
            },
            post_init=lambda ws, mm: setattr(
                ws._service_manager.services["runner"],
                "memory_manager",
                mm,
            ),
            start_method="start",
            stop_method="close",
            reusable=True,
            priority=20,
            concurrent_init=True,
        ))

        sm.register(ServiceDescriptor(
            name="context_manager",
            service_class=lambda ws: get_context_manager_backend(
                ws._config.running.context_manager_backend,
            ),
            init_args=lambda ws: {
                "working_dir": str(ws.workspace_dir),
                "agent_id": ws.agent_id,
            },
            post_init=lambda ws, cm: setattr(
                ws._service_manager.services["runner"],
                "context_manager",
                cm,
            ),
            start_method="start",
            stop_method="close",
            reusable=True,
            priority=20,
            concurrent_init=True,
        ))

        sm.register(ServiceDescriptor(
            name="mcp_manager",
            service_class=MCPClientManager,
            post_init=create_mcp_service,
            stop_method="close_all",
            priority=20,
            concurrent_init=True,
        ))

        sm.register(ServiceDescriptor(
            name="chat_manager",
            service_class=None,
            post_init=create_chat_service,
            reusable=True,
            priority=20,
            concurrent_init=True,
        ))

        sm.register(ServiceDescriptor(
            name="runner_start",
            service_class=None,
            post_init=lambda ws, _: ws._service_manager.services["runner"].start(),
            priority=25,
            concurrent_init=False,
        ))

        sm.register(ServiceDescriptor(
            name="channel_manager",
            service_class=None,
            post_init=create_channel_service,
            start_method="start_all",
            stop_method="stop_all",
            priority=30,
            concurrent_init=False,
        ))

        sm.register(ServiceDescriptor(
            name="cron_manager",
            service_class=CronManager,
            init_args=lambda ws: {
                "repo": JsonJobRepository(
                    str(ws.workspace_dir / "jobs.json"),
                ),
                "runner": ws._service_manager.services["runner"],
                "channel_manager": ws._service_manager.services.get(
                    "channel_manager",
                ),
                "timezone": load_config().user_timezone or "UTC",
                "agent_id": ws.agent_id,
            },
            start_method="start",
            stop_method="stop",
            priority=40,
            concurrent_init=False,
        ))

        sm.register(ServiceDescriptor(
            name="agent_config_watcher",
            service_class=None,
            post_init=create_agent_config_watcher,
            start_method="start",
            stop_method="stop",
            priority=50,
            concurrent_init=False,
        ))

        sm.register(ServiceDescriptor(
            name="mcp_config_watcher",
            service_class=None,
            post_init=create_mcp_config_watcher,
            start_method="start",
            stop_method="stop",
            priority=51,
            concurrent_init=False,
        ))

        # Priority 60: Game Service (after channel_manager so we can reference it)
        sm.register(ServiceDescriptor(
            name="game_service",
            service_class=resolve_game_service_class,
            init_args=lambda ws: {
                "workspace_dir": ws.workspace_dir,
                "runner": ws._service_manager.services.get("runner"),
                "channel_manager": ws._service_manager.services.get("channel_manager"),
            },
            start_method="start",
            stop_method="stop",
            reusable=False,
            priority=60,
            concurrent_init=False,
        ))

    async def set_reusable_components(self, components: dict) -> None:
        if self._started:
            logger.warning(
                f"Cannot set reusable components for already started "
                f"workspace: {self.agent_id}",
            )
            return
        for name, component in components.items():
            await self._service_manager.set_reusable(name, component)

    async def start(self):
        if self._started:
            logger.debug(f"Workspace already started: {self.agent_id}")
            return
        logger.info(f"Starting workspace: {self.agent_id}")

        from ...agents.skills_manager import ensure_skill_pool_initialized
        try:
            ensure_skill_pool_initialized()
        except Exception as e:
            logger.warning(f"Skill pool initialization failed (non-fatal): {e}")

        try:
            self._config = load_agent_config(self.agent_id)
            await self._service_manager.start_all()
            self._started = True
            logger.info(f"Workspace started successfully: {self.agent_id}")
        except Exception as e:
            logger.error(f"Failed to start agent instance {self.agent_id}: {e}")
            await self.stop()
            raise

    async def stop(self, final: bool = True):
        if not self._started:
            logger.debug(f"Workspace not started: {self.agent_id}")
            return
        logger.info(f"Stopping agent instance: {self.agent_id} (final={final})")
        await self._service_manager.stop_all(final=final)
        self._started = False
        logger.info(f"Workspace stopped: {self.agent_id}")

    def __repr__(self) -> str:
        status = "started" if self._started else "stopped"
        return (
            f"Workspace(id={self.agent_id}, "
            f"workspace={self.workspace_dir}, "
            f"status={status})"
        )