"""Game project HTTP API."""
import logging
from pathlib import Path
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException

from ltclaw_gy_x.app.agent_context import get_agent_for_request
from ltclaw_gy_x.game.config import (
    ProjectConfig,
    UserGameConfig,
    ValidationIssue,
    save_project_config,
    save_user_config,
    validate_project_config,
)
from ltclaw_gy_x.game.models import CommitResult
from ltclaw_gy_x.game.paths import get_project_config_path

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/game/project", tags=["game-project"])


def _game_service_or_404(workspace):
    svc = workspace.service_manager.services.get("game_service")
    if svc is None:
        raise HTTPException(status_code=404, detail="Game service not available")
    return svc


@router.get("/config", response_model=Optional[ProjectConfig])
async def get_project_config(workspace=Depends(get_agent_for_request)):
    return _game_service_or_404(workspace).project_config


@router.put("/config")
async def save_project_config_api(config: ProjectConfig, workspace=Depends(get_agent_for_request)):
    game_service = _game_service_or_404(workspace)
    user_config = game_service.user_config
    # SVN working copy path: prefer user_config.svn_local_root, fallback to config.svn.root
    svn_local_root = user_config.svn_local_root or config.svn.root
    if not svn_local_root:
        raise HTTPException(
            status_code=400,
            detail="\u672a\u914d\u7f6eSVN\u5de5\u4f5c\u526f\u672c\u8def\u5f84\uff1a\u8bf7\u5728\u201c\u672c\u5730\u5de5\u4f5c\u526f\u672c\u8def\u5f84\u201d\u586b\u5199\u5df2checkout\u7684\u672c\u5730\u76ee\u5f55"
        )
    svn_root = Path(svn_local_root)
    if not svn_root.exists():
        raise HTTPException(
            status_code=400,
            detail=f"\u672c\u5730\u5de5\u4f5c\u526f\u672c\u8def\u5f84\u4e0d\u5b58\u5728: {svn_root}\uff0c\u8bf7\u5148\u8fd0\u884c svn checkout"
        )
    issues = validate_project_config(config)
    errors = [i for i in issues if i.severity == "error"]
    if errors:
        msgs = [f"{i.path}: {i.message}" for i in errors]
        raise HTTPException(status_code=400, detail=f"\u914d\u7f6e\u9a8c\u8bc1\u5931\u8d25: {'; '.join(msgs)}")
    save_project_config(svn_root, config)
    if not user_config.svn_local_root:
        user_config.svn_local_root = str(svn_root)
        save_user_config(user_config)
    await game_service.reload_config()
    return {"message": "\u914d\u7f6e\u4fdd\u5b58\u6210\u529f"}


@router.post("/config/commit", response_model=CommitResult)
async def commit_project_config(
    commit_request: dict = None,
    workspace=Depends(get_agent_for_request),
):
    game_service = _game_service_or_404(workspace)
    user_config = game_service.user_config
    if user_config.my_role != "maintainer":
        return CommitResult(revision=None, files_committed=0, skipped_reason="not maintainer")
    if not game_service.svn:
        raise HTTPException(status_code=400, detail="SVN\u672a\u914d\u7f6e\u6216\u4e0d\u53ef\u7528")
    message = "Update project config"
    if commit_request and "message" in commit_request:
        message = commit_request["message"] or message
    svn_root = Path(user_config.svn_local_root)
    config_path = get_project_config_path(svn_root)
    if not config_path.exists():
        raise HTTPException(status_code=400, detail="\u9879\u76ee\u914d\u7f6e\u6587\u4ef6\u4e0d\u5b58\u5728")
    await game_service.svn.add([config_path])
    revision = await game_service.svn.commit([config_path], message)
    return CommitResult(revision=revision, files_committed=1, skipped_reason=None)


@router.get("/user_config", response_model=UserGameConfig)
async def get_user_config(workspace=Depends(get_agent_for_request)):
    return _game_service_or_404(workspace).user_config


@router.put("/user_config")
async def save_user_config_api(config: UserGameConfig, workspace=Depends(get_agent_for_request)):
    save_user_config(config)
    game_service = _game_service_or_404(workspace)
    await game_service.reload_config()
    return {"message": "\u7528\u6237\u914d\u7f6e\u4fdd\u5b58\u6210\u529f"}


@router.get("/validate", response_model=list[ValidationIssue])
async def validate_config(workspace=Depends(get_agent_for_request)):
    game_service = _game_service_or_404(workspace)
    project_config = game_service.project_config
    if project_config is None:
        return []
    return validate_project_config(project_config)


@router.delete("/config")
async def delete_project_config(workspace=Depends(get_agent_for_request)):
    game_service = _game_service_or_404(workspace)
    user_config = game_service.user_config
    if user_config.my_role != "maintainer":
        raise HTTPException(status_code=403, detail="Only maintainers can delete project config")
    if not user_config.svn_local_root:
        raise HTTPException(status_code=400, detail="SVN root not configured")
    svn_root = Path(user_config.svn_local_root)
    config_path = get_project_config_path(svn_root)
    if config_path.exists():
        config_path.unlink()
    await game_service.reload_config()
    return {"message": "\u9879\u76ee\u914d\u7f6e\u5df2\u5220\u9664"}