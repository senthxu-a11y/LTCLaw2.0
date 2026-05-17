from pathlib import Path

from ltclaw_gy_x.game.config import UserGameConfig, save_user_config
from ltclaw_gy_x.game.paths import (
    get_current_release_path,
    get_formal_map_path,
    get_project_tables_source_path,
    get_project_bundle_project_dir,
    get_release_dir,
)


def test_maprag_bundle_root_overrides_maprag_paths_only(monkeypatch, tmp_path):
    working_root = tmp_path / "working-root"
    project_root = tmp_path / "project-root"
    bundle_root = tmp_path / "maprag bundle 中文"
    project_root.mkdir()
    bundle_root.mkdir()
    monkeypatch.setenv("LTCLAW_WORKING_DIR", str(working_root))

    save_user_config(UserGameConfig(maprag_bundle_root=str(bundle_root)))

    assert get_current_release_path(project_root) == bundle_root / "releases" / "current.json"
    assert get_release_dir(project_root, "r1") == bundle_root / "releases" / "r1"
    assert get_formal_map_path(project_root) == bundle_root / "working" / "formal_map.json"
    assert get_project_tables_source_path(project_root) == (
        get_project_bundle_project_dir(project_root) / "sources" / "tables.yaml"
    )


def test_maprag_bundle_root_empty_uses_project_bundle(monkeypatch, tmp_path):
    working_root = tmp_path / "working-root"
    project_root = tmp_path / "project-root"
    project_root.mkdir()
    monkeypatch.setenv("LTCLAW_WORKING_DIR", str(working_root))

    save_user_config(UserGameConfig(maprag_bundle_root=""))

    project_dir = get_project_bundle_project_dir(project_root)
    assert get_current_release_path(project_root) == project_dir / "releases" / "current.json"
    assert get_formal_map_path(project_root) == project_dir / "working" / "formal_map.json"
