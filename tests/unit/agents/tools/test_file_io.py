# -*- coding: utf-8 -*-

from pathlib import Path

import yaml

from ltclaw_gy_x.agents.tools.file_io import _resolve_file_path
from ltclaw_gy_x.config.context import set_current_workspace_dir


def test_resolve_file_path_falls_back_to_configured_project_root(
    temp_workspace,
    monkeypatch,
):
    workspace_dir = temp_workspace / "agent-workspace"
    project_root = temp_workspace / "project-root"
    config_root = temp_workspace / "config-root"

    workspace_dir.mkdir(parents=True)
    (project_root / "docs").mkdir(parents=True)
    config_root.mkdir(parents=True)

    target = project_root / "docs" / "numeric-workbench-session-ux-plan.md"
    target.write_text("hello", encoding="utf-8")
    user_config_path = config_root / "game_data" / "user" / "game_user.yaml"
    user_config_path.parent.mkdir(parents=True, exist_ok=True)
    user_config_path.write_text(
        yaml.safe_dump(
            {"svn_local_root": str(project_root)},
            allow_unicode=True,
            sort_keys=True,
        ),
        encoding="utf-8",
    )

    monkeypatch.setenv("LTCLAW_WORKING_DIR", str(config_root))
    set_current_workspace_dir(workspace_dir)

    resolved = _resolve_file_path("docs/numeric-workbench-session-ux-plan.md")

    assert Path(resolved) == target
