from __future__ import annotations

from pathlib import Path

from .change_proposal import ChangeProposal
from .svn_client import SvnClient


class CommitError(Exception):
    pass


class SvnCommitter:
    def __init__(self, svn_client: SvnClient, svn_root: Path):
        self.svn_client = svn_client
        self.svn_root = Path(svn_root)

    async def commit_proposal(
        self,
        proposal: ChangeProposal,
        changed_files: list[str],
        message_template: str | None = None,
        expected_revision: int | None = None,
        max_retries: int = 5,
    ) -> int:
        paths = [self.svn_root / relative_path for relative_path in changed_files]
        message = self._build_message(proposal, message_template)
        try:
            if expected_revision is not None:
                info = await self.svn_client.info()
                current = int(info.get("revision", 0) or 0)
                if current > expected_revision:
                    raise CommitError(
                        f"local revision {current} is ahead of expected {expected_revision}; "
                        "refusing to commit to avoid clobbering newer work"
                    )
            await self.svn_client.add(paths)
            return await self.svn_client.commit_with_retry(
                paths, message, max_retries=max_retries
            )
        except CommitError:
            raise
        except Exception as exc:
            raise CommitError(str(exc)) from exc

    async def revert_local_changes(self, paths: list[Path]) -> None:
        await self.svn_client.revert(paths)

    def _build_message(
        self,
        proposal: ChangeProposal,
        message_template: str | None = None,
    ) -> str:
        template = message_template or "[ltclaw][proposal:{id}] {title}\n\n{description}"
        return template.format(
            id=proposal.id[:8],
            title=proposal.title,
            description=proposal.description,
        )