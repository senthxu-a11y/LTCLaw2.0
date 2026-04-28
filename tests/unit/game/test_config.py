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


def test_project_config_serialization(sample_project_config):
    """Test ProjectConfig serialization round-trip"""
    data = sample_project_config.model_dump()
    restored = ProjectConfig.model_validate(data)
    assert restored == sample_project_config


def test_save_and_load_project_config(fake_svn_root, sample_project_config):
    """Test save and load project config from YAML"""
    save_project_config(fake_svn_root, sample_project_config)
    config_path = fake_svn_root / ".ltclaw_index" / "project_config.yaml"
    assert config_path.exists()
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
