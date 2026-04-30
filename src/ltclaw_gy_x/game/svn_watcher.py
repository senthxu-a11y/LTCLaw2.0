"""
SVN变更监控器: 定时拉取 SVN 当前 revision 并触发 ChangeSet 回调。
"""

import asyncio
import logging
from datetime import datetime
from typing import Any, Awaitable, Callable, Dict, List, Optional

from .config import ProjectConfig
from .models import ChangeSet
from .svn_client import SvnClient

logger = logging.getLogger(__name__)


class SvnWatcher:
    def __init__(self, project: ProjectConfig, svn_client: SvnClient,
                 change_callback: Optional[Callable[[ChangeSet], Awaitable[None]]] = None,
                 poll_interval: Optional[int] = None,
                 watch_paths: Optional[List[str]] = None):
        self.project = project
        self.svn = svn_client
        self.change_callback = change_callback
        self.poll_interval = poll_interval if poll_interval is not None else int(getattr(project.svn, "poll_interval_seconds", 300))
        self.watch_paths = watch_paths or []
        self._running = False
        self._task: Optional[asyncio.Task] = None
        self._last_checked_revision: Optional[int] = None
        self._last_check_time: Optional[datetime] = None
        self._check_count = 0
        self._change_count = 0
        self._error_count = 0

    async def start(self) -> None:
        if self._running:
            return
        self._running = True
        try:
            self._last_checked_revision = await self._get_current_revision()
            self._last_check_time = datetime.now()
        except Exception as e:
            logger.error(f"获取初始revision失败: {e}")
            self._last_checked_revision = 0
        self._task = asyncio.create_task(self._watch_loop())

    async def stop(self) -> None:
        if not self._running:
            return
        self._running = False
        if self._task and not self._task.done():
            self._task.cancel()
            try:
                await self._task
            except asyncio.CancelledError:
                pass
        self._task = None

    async def _watch_loop(self) -> None:
        try:
            while self._running:
                try:
                    await self._check_for_changes()
                    self._check_count += 1
                    await asyncio.sleep(self.poll_interval)
                except asyncio.CancelledError:
                    break
                except Exception as e:
                    self._error_count += 1
                    logger.error(f"SVN检查失败: {e}")
                    await asyncio.sleep(min(self.poll_interval, 30))
        except Exception as e:
            logger.error(f"SVN监控循环异常退出: {e}")

    async def _check_for_changes(self) -> None:
        current_revision = await self._get_current_revision()
        if (self._last_checked_revision is not None and
                current_revision > self._last_checked_revision):
            try:
                changeset = await self.svn.diff_paths(self._last_checked_revision + 1, current_revision)
                filtered = self._filter_changeset(changeset)
                if filtered and self.change_callback:
                    await self._trigger_change_callback(filtered)
                    self._change_count += 1
            except Exception as e:
                logger.error(f"获取变更集失败: {e}")
        self._last_checked_revision = current_revision
        self._last_check_time = datetime.now()

    def _filter_changeset(self, cs: ChangeSet) -> Optional[ChangeSet]:
        if not self.watch_paths:
            if not (cs.added or cs.modified or cs.deleted):
                return None
            return cs

        def keep(p: str) -> bool:
            return any(p.startswith(w) or w in p for w in self.watch_paths)

        added = [p for p in cs.added if keep(p)]
        modified = [p for p in cs.modified if keep(p)]
        deleted = [p for p in cs.deleted if keep(p)]
        if not (added or modified or deleted):
            return None
        return ChangeSet(from_rev=cs.from_rev, to_rev=cs.to_rev,
                          added=added, modified=modified, deleted=deleted)

    async def _get_current_revision(self) -> int:
        info = await self.svn.info()
        return int(info.get("revision", 0))

    async def _trigger_change_callback(self, cs: ChangeSet) -> None:
        if not self.change_callback:
            return
        try:
            if asyncio.iscoroutinefunction(self.change_callback):
                await self.change_callback(cs)
            else:
                loop = asyncio.get_event_loop()
                await loop.run_in_executor(None, self.change_callback, cs)
        except Exception as e:
            logger.error(f"变更回调执行失败: {e}")

    async def trigger_now(self) -> Optional[ChangeSet]:
        """手动触发一次完整同步: svn update -> diff -> 返回 ChangeSet"""
        from_rev = self._last_checked_revision
        try:
            await self.svn.update()
        except Exception as e:
            logger.error(f"svn update 失败: {e}")
            self._error_count += 1
            raise
        try:
            current_revision = await self._get_current_revision()
        except Exception as e:
            logger.error(f"获取当前revision失败: {e}")
            self._error_count += 1
            raise
        cs: Optional[ChangeSet] = None
        if from_rev is not None and current_revision > from_rev:
            try:
                cs = await self.svn.diff_paths(from_rev + 1, current_revision)
                cs = self._filter_changeset(cs)
                if cs and self.change_callback:
                    await self._trigger_change_callback(cs)
                    self._change_count += 1
            except Exception as e:
                logger.error(f"获取变更集失败: {e}")
        self._last_checked_revision = current_revision
        self._last_check_time = datetime.now()
        self._check_count += 1
        if cs is None:
            from .models import ChangeSet as _CS
            cs = _CS(from_rev=from_rev or current_revision, to_rev=current_revision,
                     added=[], modified=[], deleted=[])
        return cs

    async def force_check(self) -> Optional[ChangeSet]:
        try:
            await self._check_for_changes()
        except Exception as e:
            logger.error(f"强制检查失败: {e}")
        return None

    async def update_working_copy(self) -> bool:
        try:
            await self.svn.update()
            self._last_checked_revision = await self._get_current_revision()
            self._last_check_time = datetime.now()
            return True
        except Exception as e:
            logger.error(f"更新工作副本失败: {e}")
            return False

    def get_status(self) -> Dict[str, Any]:
        uptime = None
        if self._last_check_time:
            uptime = (datetime.now() - self._last_check_time).total_seconds()
        return {
            "running": self._running,
            "poll_interval": self.poll_interval,
            "watch_paths": self.watch_paths,
            "last_checked_revision": self._last_checked_revision,
            "last_check_time": self._last_check_time.isoformat() if self._last_check_time else None,
            "uptime_seconds": uptime,
            "stats": {
                "check_count": self._check_count,
                "change_count": self._change_count,
                "error_count": self._error_count,
            },
            "has_callback": self.change_callback is not None,
        }

    def set_change_callback(self, callback) -> None:
        self.change_callback = callback

    def update_config(self, poll_interval: Optional[int] = None,
                      watch_paths: Optional[List[str]] = None) -> None:
        if poll_interval is not None:
            self.poll_interval = poll_interval
        if watch_paths is not None:
            self.watch_paths = watch_paths