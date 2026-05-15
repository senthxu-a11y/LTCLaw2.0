"""单元测试: GameService 启停与未配置态。"""
import gc
import warnings
from datetime import datetime
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from ltclaw_gy_x.game.config import (
    FilterConfig,
    ProjectConfig,
    ProjectMeta,
    SvnConfig,
    TableConvention,
    UserGameConfig,
    save_project_config,
)
from ltclaw_gy_x.game.models import ChangeSet, DependencyGraph, TableIndex
from ltclaw_gy_x.game.service import GameService, SimpleModelRouter, SVN_RUNTIME_DISABLED_REASON
from ltclaw_gy_x.game.config import ModelSlotRef


@pytest.fixture
def isolated_home(tmp_path, monkeypatch):
    monkeypatch.setenv("LTCLAW_WORKING_DIR", str(tmp_path / "qpw"))
    yield tmp_path


@pytest.fixture
def service(tmp_path, isolated_home):
    workspace = tmp_path / "workspace"
    workspace.mkdir()
    return GameService(workspace_dir=workspace, runner=None, channel_manager=None)


def test_initial_state_unconfigured(service):
    assert service.configured is False
    assert service.config is service.project_config
    assert service.config_generation == 0
    assert service.project_config is None
    assert service.svn is None
    assert service.table_indexer is None
    assert service.dependency_resolver is None
    assert service.index_committer is None
    assert service.svn_watcher is None
    assert service.query_router is None
    assert service.proposal_store is None
    assert service.change_applier is None
    assert service.svn_committer is None


def test_workspace_game_dir_created(service, tmp_path):
    expected = tmp_path / "qpw" / "game_data" / "agents" / "workspace" / "sessions" / "default" / "workbench"
    assert expected.exists()


@pytest.mark.asyncio
async def test_start_without_config_completes(service):
    await service.start()
    assert service._started is True
    assert service.configured is False
    assert service.query_router is not None
    assert service.proposal_store is not None
    assert service.change_applier is None
    assert service.svn_committer is None
    await service.stop()
    assert service._started is False


@pytest.mark.asyncio
async def test_double_start_is_idempotent(service):
    await service.start()
    started_at = service._started
    await service.start()
    assert service._started == started_at
    await service.stop()


@pytest.mark.asyncio
async def test_stop_without_start_is_safe(service):
    await service.stop()


@pytest.mark.asyncio
async def test_index_tables_raises_without_indexer(service):
    with pytest.raises(RuntimeError):
        await service.index_tables(["foo.xlsx"])


def _project_config(svn_root: Path) -> ProjectConfig:
    return ProjectConfig(
        project=ProjectMeta(name="Test Game", engine="Unity", language="zh-CN"),
        svn=SvnConfig(root=str(svn_root), poll_interval_seconds=300, jitter_seconds=30),
        paths=[],
        filters=FilterConfig(include_ext=[".xlsx", ".csv"], exclude_glob=[]),
        table_convention=TableConvention(),
        doc_templates={},
        models={},
    )


def test_project_config_external_provider_config_defaults_to_none():
    config = ProjectConfig(
        project=ProjectMeta(name="Test Game", engine="Unity", language="zh-CN"),
        svn=SvnConfig(root='/tmp/svn', poll_interval_seconds=300, jitter_seconds=30),
        paths=[],
        filters=FilterConfig(include_ext=[".xlsx", ".csv"], exclude_glob=[]),
        table_convention=TableConvention(),
        doc_templates={},
        models={},
    )

    assert config.external_provider_config is None


def test_game_service_config_property_returns_project_config(service, tmp_path):
    project_config = _project_config(tmp_path / 'svn')
    service._project_config = project_config

    assert service.config is project_config


@pytest.mark.asyncio
async def test_reload_config_loads_file_backed_external_provider_config(tmp_path, monkeypatch):
    monkeypatch.setenv('LTCLAW_WORKING_DIR', str(tmp_path / 'ltclaw-data'))
    workspace = tmp_path / 'workspace'
    workspace.mkdir()
    svn_root = tmp_path / 'svn'
    svn_root.mkdir()
    save_project_config(
        svn_root,
        ProjectConfig(
            project=ProjectMeta(name='Test Game', engine='Unity', language='zh-CN'),
            svn=SvnConfig(root=str(svn_root), poll_interval_seconds=300, jitter_seconds=30),
            paths=[],
            filters=FilterConfig(include_ext=['.xlsx'], exclude_glob=[]),
            table_convention=TableConvention(),
            doc_templates={},
            models={},
            external_provider_config={
                'enabled': True,
                'transport_enabled': True,
                'provider_name': 'future_external',
                'model_name': 'backend-model',
                'allowed_providers': ['future_external'],
                'allowed_models': ['backend-model'],
                'base_url': 'http://127.0.0.1:8765/v1/chat/completions',
                'timeout_seconds': 15.0,
                'max_output_tokens': 256,
                'max_prompt_chars': 12000,
                'max_output_chars': 2000,
                'api_key': 'REQUEST_SECRET_SHOULD_BE_STRIPPED',
                'env': {'api_key_env_var': 'QWENPAW_RAG_API_KEY'},
            },
        ),
    )
    service = GameService(workspace_dir=workspace, runner=None, channel_manager=None)

    with patch(
        'ltclaw_gy_x.game.service.load_user_config',
        return_value=UserGameConfig(my_role='consumer', svn_local_root=str(svn_root)),
    ):
        generation_before = service.config_generation
        await service.reload_config()

    assert service.project_config is not None
    assert service.config_generation == generation_before + 1
    assert service.project_config.external_provider_config is not None
    assert service.project_config.external_provider_config.enabled is True
    assert service.project_config.external_provider_config.transport_enabled is True
    assert service.project_config.external_provider_config.provider_name == 'future_external'
    assert service.project_config.external_provider_config.model_name == 'backend-model'
    assert service.project_config.external_provider_config.base_url == 'http://127.0.0.1:8765/v1/chat/completions'
    assert service.project_config.external_provider_config.env is not None
    assert service.project_config.external_provider_config.env.api_key_env_var == 'QWENPAW_RAG_API_KEY'
    assert not hasattr(service.project_config.external_provider_config, 'api_key')


@pytest.mark.asyncio
async def test_start_with_consumer_config_creates_proposal_store_and_change_applier(tmp_path, isolated_home):
    workspace = tmp_path / "workspace"
    workspace.mkdir()
    svn_root = tmp_path / "svn"
    svn_root.mkdir()
    service = GameService(workspace_dir=workspace, runner=None, channel_manager=None)

    with patch("ltclaw_gy_x.game.service.load_user_config", return_value=UserGameConfig(my_role="consumer", svn_local_root=str(svn_root))), \
         patch("ltclaw_gy_x.game.service.load_project_config", return_value=_project_config(svn_root)):
        await service.start()

    assert service.proposal_store is not None
    assert service.change_applier is not None
    assert service.svn_committer is None
    await service.stop()


@pytest.mark.asyncio
async def test_start_with_maintainer_config_keeps_svn_runtime_frozen(tmp_path, isolated_home):
    workspace = tmp_path / "workspace"
    workspace.mkdir()
    svn_root = tmp_path / "svn"
    svn_root.mkdir()
    service = GameService(workspace_dir=workspace, runner=None, channel_manager=None)

    with patch("ltclaw_gy_x.game.service.load_user_config", return_value=UserGameConfig(my_role="maintainer", svn_local_root=str(svn_root))), \
         patch("ltclaw_gy_x.game.service.load_project_config", return_value=_project_config(svn_root)):
        await service.start()

    assert service.proposal_store is not None
    assert service.change_applier is not None
    assert service.svn_committer is None
    assert service.svn_watcher is None
    assert await service.start_svn_monitoring() is False
    assert await service.stop_svn_monitoring() is False
    assert service.get_svn_monitoring_status() == {
        "disabled": True,
        "running": False,
        "configured": True,
        "reason": SVN_RUNTIME_DISABLED_REASON,
        "my_role": "maintainer",
    }
    await service.stop()


@pytest.mark.asyncio
async def test_start_with_local_root_and_no_project_config_still_builds_change_applier(tmp_path, isolated_home):
    workspace = tmp_path / "workspace"
    workspace.mkdir()
    svn_root = tmp_path / "svn"
    svn_root.mkdir()
    table_dir = svn_root / "Tables"
    table_dir.mkdir()
    (table_dir / "HeroTable.csv").write_text("ID,Name,HP\n1,HeroA,100\n", encoding="utf-8")
    service = GameService(workspace_dir=workspace, runner=None, channel_manager=None)

    with patch(
        "ltclaw_gy_x.game.service.load_user_config",
        return_value=UserGameConfig(my_role="maintainer", svn_local_root=str(svn_root)),
    ), patch("ltclaw_gy_x.game.service.load_project_config", return_value=None):
        await service.start()

    assert service.configured is False
    assert service.query_router is not None
    assert service.change_applier is not None
    assert service.change_applier.read_rows("HeroTable")["rows"] == [["1", "HeroA", "100"]]
    await service.stop()


@pytest.mark.asyncio
async def test_start_and_stop_svn_monitoring_do_not_touch_watcher(service):
    watcher = SimpleNamespace(start=AsyncMock(), stop=AsyncMock())
    service._svn_watcher = watcher

    assert await service.start_svn_monitoring() is False
    assert await service.stop_svn_monitoring() is False

    watcher.start.assert_not_called()
    watcher.stop.assert_not_called()


def test_model_router_falls_back_to_simple_router(service):
    router = service._model_router()
    assert isinstance(router, SimpleModelRouter)


@pytest.mark.asyncio
async def test_model_router_uses_project_model_slot_for_requested_model_type(service):
    provider = SimpleNamespace(base_url="https://provider.example/v1", api_key="secret")
    active_model = SimpleNamespace(provider_id="provider-default", model_id="model-default")
    provider_manager = SimpleNamespace(
        active_model=active_model,
        get_provider=lambda provider_id: provider if provider_id == "provider-slot" else provider,
    )
    service._project_config = _project_config(Path("/tmp/svn"))
    service._project_config.models = {
        "rag_answer": ModelSlotRef(provider_id="provider-slot", model_id="rag-model")
    }

    with patch("ltclaw_gy_x.providers.provider_manager.ProviderManager.get_instance", return_value=provider_manager), \
         patch("ltclaw_gy_x.game.unified_model_router._invoke_provider", AsyncMock(return_value="ok")) as invoke_provider:
        router = service._model_router()
        result = await router.call_model_result("prompt", model_type="rag_answer")

    assert result.ok is True
    assert result.model_id == "rag-model"
    invoke_provider.assert_awaited_once()
    assert invoke_provider.await_args.args[1] == "rag-model"


@pytest.mark.parametrize(
    ("model_type", "slot_model_id"),
    [
        ("field_describer", "field-model"),
        ("table_summarizer", "summary-model"),
        ("workbench_suggest", "suggest-model"),
    ],
)
@pytest.mark.asyncio
async def test_model_router_uses_project_model_slot_for_supported_game_model_types(service, model_type, slot_model_id):
    provider = SimpleNamespace(base_url="https://provider.example/v1", api_key="secret")
    active_model = SimpleNamespace(provider_id="provider-default", model_id="model-default")
    provider_manager = SimpleNamespace(
        active_model=active_model,
        get_provider=lambda provider_id: provider if provider_id == "provider-slot" else provider,
    )
    service._project_config = _project_config(Path("/tmp/svn"))
    service._project_config.models = {
        model_type: ModelSlotRef(provider_id="provider-slot", model_id=slot_model_id)
    }

    with patch("ltclaw_gy_x.providers.provider_manager.ProviderManager.get_instance", return_value=provider_manager), \
         patch("ltclaw_gy_x.game.unified_model_router._invoke_provider", AsyncMock(return_value="ok")) as invoke_provider:
        router = service._model_router()
        result = await router.call_model_result("prompt", model_type=model_type)

    assert result.ok is True
    assert result.model_type == model_type
    assert result.model_id == slot_model_id
    invoke_provider.assert_awaited_once()
    assert invoke_provider.await_args.args[1] == slot_model_id


@pytest.mark.asyncio
async def test_model_router_returns_structured_no_active_model_error(service):
    provider_manager = SimpleNamespace(active_model=None, get_active_model=lambda: None)
    with patch("ltclaw_gy_x.providers.provider_manager.ProviderManager.get_instance", return_value=provider_manager):
        router = service._model_router()
        result = await router.call_model_result("prompt", model_type="rag_answer")

    assert result.ok is False
    assert result.error_code == "no_active_model"
    assert await router.call_model("prompt", model_type="rag_answer") == ""


@pytest.mark.asyncio
async def test_model_router_returns_structured_provider_not_configured_when_provider_missing(service):
    active_model = SimpleNamespace(provider_id="provider-default", model_id="model-default")
    provider_manager = SimpleNamespace(
        active_model=active_model,
        get_provider=lambda provider_id: None,
    )
    project_config = _project_config(Path("/tmp/svn"))
    project_config.models = {
        "rag_answer": ModelSlotRef(provider_id="provider-missing", model_id="model-default")
    }

    router = SimpleModelRouter(provider_manager, project_config=project_config)
    result = await router.call_model_result("prompt", model_type="rag_answer")

    assert result.ok is False
    assert result.error_code == "provider_not_configured"
    assert result.provider_id == "provider-missing"
    assert result.model_id == "model-default"


@pytest.mark.asyncio
async def test_model_router_returns_structured_provider_exception(service):
    provider = SimpleNamespace(base_url="https://provider.example/v1", api_key="secret")
    active_model = SimpleNamespace(provider_id="provider-default", model_id="model-default")
    provider_manager = SimpleNamespace(
        active_model=active_model,
        get_provider=lambda provider_id: provider,
    )

    with patch("ltclaw_gy_x.providers.provider_manager.ProviderManager.get_instance", return_value=provider_manager), \
         patch("ltclaw_gy_x.game.unified_model_router._invoke_provider", AsyncMock(side_effect=RuntimeError("Provider invocation failed."))):
        router = service._model_router()
        result = await router.call_model_result("prompt", model_type="rag_answer")

    assert result.ok is False
    assert result.error_code == "provider_exception"
    assert result.message == "Provider invocation failed."


@pytest.mark.asyncio
async def test_model_router_returns_structured_empty_response(service):
    provider = SimpleNamespace(base_url="https://provider.example/v1", api_key="secret")
    active_model = SimpleNamespace(provider_id="provider-default", model_id="model-default")
    provider_manager = SimpleNamespace(
        active_model=active_model,
        get_provider=lambda provider_id: provider,
    )

    with patch("ltclaw_gy_x.providers.provider_manager.ProviderManager.get_instance", return_value=provider_manager), \
         patch("ltclaw_gy_x.game.unified_model_router._invoke_provider", AsyncMock(return_value="   ")):
        router = service._model_router()
        result = await router.call_model_result("prompt", model_type="rag_answer")

    assert result.ok is False
    assert result.error_code == "empty_response"
    assert await router.call_model("prompt", model_type="rag_answer") == ""


@pytest.mark.asyncio
async def test_model_router_unknown_model_type_falls_back_to_default_slot(service):
    provider = SimpleNamespace(base_url="https://provider.example/v1", api_key="secret")
    active_model = SimpleNamespace(provider_id="provider-default", model_id="model-default")
    provider_manager = SimpleNamespace(
        active_model=active_model,
        get_provider=lambda provider_id: provider,
    )
    service._project_config = _project_config(Path("/tmp/svn"))
    service._project_config.models = {
        "default": ModelSlotRef(provider_id="provider-default", model_id="default-model")
    }

    with patch("ltclaw_gy_x.providers.provider_manager.ProviderManager.get_instance", return_value=provider_manager), \
         patch("ltclaw_gy_x.game.unified_model_router._invoke_provider", AsyncMock(return_value="ok")) as invoke_provider:
        router = service._model_router()
        result = await router.call_model_result("prompt", model_type="unknown_model_type")

    assert result.ok is True
    assert result.model_type == "default"
    assert result.model_id == "default-model"
    invoke_provider.assert_awaited_once()
    assert invoke_provider.await_args.args[1] == "default-model"


@pytest.mark.asyncio
async def test_model_router_call_model_blocking_inside_running_loop_emits_no_runtime_warnings(service):
    provider = SimpleNamespace(base_url="https://provider.example/v1", api_key="secret")
    active_model = SimpleNamespace(provider_id="provider-default", model_id="model-default")
    provider_manager = SimpleNamespace(
        active_model=active_model,
        get_provider=lambda provider_id: provider,
    )

    with patch("ltclaw_gy_x.providers.provider_manager.ProviderManager.get_instance", return_value=provider_manager), \
         patch("ltclaw_gy_x.game.unified_model_router._invoke_provider", AsyncMock(return_value="ok")):
        router = service._model_router()
        with warnings.catch_warnings(record=True) as caught:
            warnings.simplefilter("always")
            result = router.call_model_blocking("prompt", model_type="rag_answer")
            gc.collect()

    assert result.ok is True
    assert [warning for warning in caught if issubclass(warning.category, RuntimeWarning)] == []


@pytest.mark.asyncio
async def test_start_with_watcher_patch_does_not_start_polling_when_runtime_frozen(tmp_path, isolated_home):
    workspace = tmp_path / "workspace"
    workspace.mkdir()
    svn_root = tmp_path / "svn"
    svn_root.mkdir()
    service = GameService(workspace_dir=workspace, runner=None, channel_manager=None)
    watcher = MagicMock()
    watcher.start = AsyncMock()
    watcher.stop = AsyncMock()

    with patch("ltclaw_gy_x.game.service.load_user_config", return_value=UserGameConfig(my_role="maintainer", svn_local_root=str(svn_root))), \
         patch("ltclaw_gy_x.game.service.load_project_config", return_value=_project_config(svn_root)), \
         patch("ltclaw_gy_x.game.service.SvnWatcher", return_value=watcher):
        await service.start()

    watcher.start.assert_not_called()
    assert service.svn_watcher is None
    await service.stop()


@pytest.mark.asyncio
async def test_handle_svn_change_rebuilds_snapshot(service, tmp_path):
    svn_root = tmp_path / "svn"
    table_dir = svn_root / "Assets" / "Data" / "Tables"
    table_dir.mkdir(parents=True)
    (table_dir / "SkillTable.csv").write_text("ID,Damage\n1,100\n", encoding="utf-8")
    service._project_config = _project_config(svn_root)
    service._table_indexer = MagicMock()
    service._dependency_resolver = MagicMock()
    service._index_committer = MagicMock()

    existing_table = TableIndex(
        table_name="OldTable",
        source_path="Assets/Data/Tables/OldTable.csv",
        source_hash="sha256:old",
        svn_revision=1,
        row_count=1,
        primary_key="ID",
        ai_summary="old",
        ai_summary_confidence=0.5,
        fields=[],
        last_indexed_at=datetime.now(),
        indexer_model="m",
    )
    updated_table = TableIndex(
        table_name="SkillTable",
        source_path="Assets/Data/Tables/SkillTable.csv",
        source_hash="sha256:new",
        svn_revision=2,
        row_count=1,
        primary_key="ID",
        ai_summary="new",
        ai_summary_confidence=0.8,
        fields=[],
        last_indexed_at=datetime.now(),
        indexer_model="m",
    )
    service._index_committer.load_table_indexes.return_value = [existing_table]
    service._index_committer.load_dependency_graph.return_value = DependencyGraph(edges=[], last_updated=datetime.now())
    service.index_tables = AsyncMock(return_value=[updated_table])
    service.resolve_dependencies = AsyncMock(return_value=DependencyGraph(edges=[], last_updated=datetime.now()))
    service.commit_indexes = AsyncMock(return_value=True)

    await service._handle_svn_change(ChangeSet(
        from_rev=1,
        to_rev=2,
        added=[],
        modified=["Assets/Data/Tables/SkillTable.csv"],
        deleted=[],
    ))

    service.index_tables.assert_awaited_once()
    committed_tables = service.commit_indexes.await_args.kwargs["tables"]
    assert {table.table_name for table in committed_tables} == {"OldTable", "SkillTable"}
    assert service._recent_changes_buffer[0]["revision"] == 2