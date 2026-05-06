# -*- coding: utf-8 -*-
"""
Tests for game configuration module
"""
import pytest
from pathlib import Path
from ltclaw_gy_x.game.config import (
    ProjectConfig, UserGameConfig, load_project_config,
    save_project_config, validate_project_config,
    load_user_config, save_user_config
)
from ltclaw_gy_x.game.paths import (
    get_legacy_user_config_path,
    get_project_config_path,
    get_storage_summary,
    get_user_config_path,
)


def test_project_config_serialization(sample_project_config):
    """Test ProjectConfig serialization round-trip"""
    data = sample_project_config.model_dump()
    restored = ProjectConfig.model_validate(data)
    assert restored == sample_project_config


def test_save_and_load_project_config(fake_svn_root, sample_project_config, monkeypatch, tmp_path):
    """Test save and load project config from YAML"""
    monkeypatch.setenv("LTCLAW_GAME_PROJECTS_DIR", str(tmp_path / "game-projects"))
    save_project_config(fake_svn_root, sample_project_config)
    config_path = get_project_config_path(fake_svn_root)
    assert config_path.exists()
    assert config_path.is_relative_to(tmp_path / "game-projects")
    loaded = load_project_config(fake_svn_root)
    assert loaded is not None
    assert loaded.project.name == sample_project_config.project.name


def test_load_project_config_falls_back_to_legacy_path(
    fake_svn_root,
    sample_project_config,
    monkeypatch,
    tmp_path,
):
    monkeypatch.setenv("LTCLAW_GAME_PROJECTS_DIR", str(tmp_path / "game-projects"))
    legacy_path = fake_svn_root / ".ltclaw_index" / "project_config.yaml"
    legacy_path.write_text(sample_project_config.model_dump_json(), encoding="utf-8")

    loaded = load_project_config(fake_svn_root)

    assert loaded is not None
    assert loaded.project.name == sample_project_config.project.name


def test_load_nonexistent_config(fake_svn_root):
    """Test loading non-existent config returns None"""
    result = load_project_config(fake_svn_root)
    assert result is None


def test_validate_project_config(sample_project_config):
    """Test project config validation"""
    issues = validate_project_config(sample_project_config)
    assert len(issues) == 0


def test_user_config_operations(tmp_path, monkeypatch):
    """Test user config save and load"""
    user_config_path = tmp_path / "game_user.yaml"
    monkeypatch.setattr("ltclaw_gy_x.game.paths.get_user_config_path", lambda: user_config_path)
    user_config = UserGameConfig(
        my_role="maintainer",
        svn_local_root="C:/workspace/game",
        svn_username="testuser"
    )
    save_user_config(user_config)
    loaded = load_user_config()
    assert loaded.my_role == "maintainer"
    assert loaded.svn_local_root == "C:/workspace/game"
    assert loaded.svn_username == "testuser"


if __name__ == "__main__":
    pytest.main([__file__])


def test_user_config_path_moves_under_game_data(monkeypatch, tmp_path):
    monkeypatch.setenv("LTCLAW_WORKING_DIR", str(tmp_path / "data-root"))
    config_path = get_user_config_path()
    assert config_path == tmp_path / "data-root" / "game_data" / "user" / "game_user.yaml"


def test_load_user_config_falls_back_to_legacy_path(monkeypatch, tmp_path):
    monkeypatch.setenv("LTCLAW_WORKING_DIR", str(tmp_path / "data-root"))
    legacy_path = get_legacy_user_config_path()
    legacy_path.parent.mkdir(parents=True, exist_ok=True)
    legacy_path.write_text("svn_local_root: C:/legacy\n", encoding="utf-8")
    loaded = load_user_config()
    assert loaded.svn_local_root == "C:/legacy"


def test_storage_summary_uses_unified_game_data_tree(monkeypatch, tmp_path):
    working_root = tmp_path / "ltclaw-data"
    workspace_dir = tmp_path / "workspaces" / "agent-alpha"
    svn_root = tmp_path / "projects" / "demo-project"
    monkeypatch.setenv("LTCLAW_WORKING_DIR", str(working_root))

    summary = get_storage_summary(workspace_dir, svn_root=svn_root, session_id="chat-42")

    assert summary["working_root"] == str(working_root)
    assert summary["game_data_root"] == str(working_root / "game_data")
    assert summary["project_store_dir"] is not None
    assert summary["project_store_dir"].startswith(str(working_root / "game_data" / "projects"))
    assert summary["agent_store_dir"].startswith(summary["project_store_dir"])
    assert Path(summary["session_store_dir"]).parts[-2:] == ("sessions", "chat-42")
    assert Path(summary["workbench_dir"]).parts[-3:] == ("sessions", "chat-42", "workbench")
    assert Path(summary["llm_cache_dir"]).parts[-3:] == ("chat-42", "caches", "llm")
    assert Path(summary["code_index_dir"]).parts[-3:] == ("chat-42", "databases", "code_index")
