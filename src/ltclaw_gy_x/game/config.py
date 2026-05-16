"""
???????????

????????????pydantic?????/??/?????
"""

import os
import tempfile
import yaml
from datetime import datetime
from pathlib import Path
from typing import Literal, Union
from pydantic import BaseModel, ConfigDict, Field

from .paths import (
    get_legacy_project_config_path,
    get_legacy_user_config_path,
    get_project_config_path,
    get_project_docs_source_path,
    get_project_scripts_source_path,
    get_project_tables_source_path,
    get_user_config_path,
)


DEFAULT_MODEL_TYPE = "default"
FIELD_DESCRIBER_MODEL_TYPE = "field_describer"
TABLE_SUMMARIZER_MODEL_TYPE = "table_summarizer"
MAP_BUILDER_MODEL_TYPE = "map_builder"
MAP_DIFF_EXPLAINER_MODEL_TYPE = "map_diff_explainer"
RAG_ANSWER_MODEL_TYPE = "rag_answer"
WORKBENCH_SUGGEST_MODEL_TYPE = "workbench_suggest"
DEPENDENCY_ANALYZER_MODEL_TYPE = "dependency_analyzer"

SUPPORTED_MODEL_TYPES = (
    DEFAULT_MODEL_TYPE,
    FIELD_DESCRIBER_MODEL_TYPE,
    TABLE_SUMMARIZER_MODEL_TYPE,
    MAP_BUILDER_MODEL_TYPE,
    MAP_DIFF_EXPLAINER_MODEL_TYPE,
    RAG_ANSWER_MODEL_TYPE,
    WORKBENCH_SUGGEST_MODEL_TYPE,
    DEPENDENCY_ANALYZER_MODEL_TYPE,
)

DEFAULT_TABLES_INCLUDE_PATTERNS = ["**/*.csv", "**/*.xlsx", "**/*.txt"]
DEFAULT_TABLES_EXCLUDE_PATTERNS = ["**/~$*", "**/.backup/**"]
DEFAULT_TABLES_PRIMARY_KEY_CANDIDATES = ["ID", "Id", "id"]
DEFAULT_DOCS_INCLUDE_PATTERNS = ["**/*.md"]
DEFAULT_DOCS_EXCLUDE_PATTERNS = ["**/~$*", "**/.backup/**"]
DEFAULT_SCRIPTS_INCLUDE_PATTERNS = ["**/*.cs", "**/*.lua", "**/*.py"]
DEFAULT_SCRIPTS_EXCLUDE_PATTERNS = ["**/~$*", "**/.backup/**", "**/__pycache__/**"]


class ProjectMeta(BaseModel):
    """??????"""
    name: str = Field(description="????")
    engine: str = Field(description="???? (?Unity, Unreal?)")
    language: str = Field(default="zh", description="??????")


class SvnConfig(BaseModel):
    """SVN??"""
    root: str = Field(description="SVN?????????")
    poll_interval_seconds: int = Field(default=300, description="??????")
    jitter_seconds: int = Field(default=30, description="???????????????")


class PathRule(BaseModel):
    """?????????????????"""
    path: str = Field(description="???? (??glob)")
    semantic: Literal["table", "doc", "template"] = Field(description="????")
    system: Union[str, None] = Field(default=None, description="??????")


class FilterConfig(BaseModel):
    """????"""
    include_ext: list[str] = Field(default_factory=lambda: [".xlsx", ".xls", ".csv", ".md", ".txt", ".docx"],
                                   description="????????")
    exclude_glob: list[str] = Field(default_factory=lambda: ["**/temp/**", "**/.svn/**", "**/~$*"],
                                    description="???glob??")


class IDRange(BaseModel):
    """ID????"""
    type: str = Field(description="???? (?????)")
    start: int = Field(description="??ID")
    end: int = Field(description="??ID (??)")


class LocalAgentProfile(BaseModel):
    """Local capability profile for a single agent.

    This profile is a local safety boundary to reduce accidental misuse. It is
    not a server-side authentication or authorization system.
    """

    agent_id: str = Field(description="Local agent identifier")
    display_name: str = Field(default="", description="Display name shown in local UI")
    role: Literal["viewer", "planner", "source_writer", "admin"] = Field(
        default="viewer",
        description="Local role template name",
    )
    capabilities: list[str] = Field(
        default_factory=list,
        description="Explicit capability override list. Empty means use the role template.",
    )


class TableConvention(BaseModel):
    """????"""
    header_row: int = Field(default=1, description="????(1-based)")
    comment_row: Union[int, None] = Field(default=None, description="????(1-based)")
    primary_key_field: str = Field(default="ID", description="????? (project ??)")
    per_table_primary_keys: dict[str, str] = Field(
        default_factory=dict,
        description="???????????? {\"??\": \"??id\"}",
    )
    auto_detect_primary_key: bool = Field(
        default=True,
        description="?????/???????????? 'id' ??????????",
    )
    id_ranges: list[IDRange] = Field(default_factory=list, description="ID????")

    def resolve_primary_key(
        self,
        table_name: str | None = None,
        headers: list[str] | None = None,
    ) -> str:
        """?? per-table ?? + ??????????????

        ????
          1) per_table_primary_keys[table_name]
          2) project ?? primary_key_field??? headers ?????
          3) auto_detect_primary_key=True ?? headers ?
             "id" ??? (??????, ???? "id"/"??"/"??") ??
          4) ??? project ?? primary_key_field
        """
        if table_name and table_name in self.per_table_primary_keys:
            override = self.per_table_primary_keys[table_name]
            if override:
                return override
        default_key = self.primary_key_field
        if not headers:
            return default_key
        lowered = [str(h or "").strip() for h in headers]
        lower_set = {h.lower(): h for h in lowered if h}
        if default_key and default_key.lower() in lower_set:
            return lower_set[default_key.lower()]
        if not self.auto_detect_primary_key:
            return default_key
        # ??????? "id" / "??" / "??"??????? "id" ???
        sniff_exact = ("id", "\u7f16\u53f7", "\u7de8\u865f", "??", "??")
        for h in lowered:
            if h.lower() in sniff_exact:
                return h
        for h in lowered:
            if "id" in h.lower() or "\u7f16\u53f7" in h or "\u7de8\u865f" in h or "??" in h or "??" in h:
                return h
        return default_key


class ModelSlotRef(BaseModel):
    """?????"""
    provider_id: str = Field(description="Provider ID")
    model_id: str = Field(description="Model ID")


class ExternalProviderEnvProjectConfig(BaseModel):
    """Backend-owned env metadata for the RAG external provider."""

    model_config = ConfigDict(extra="ignore")

    api_key_env_var: str | None = Field(default=None, description="Env var name for backend-owned API key lookup")


class ExternalProviderProjectConfig(BaseModel):
    """Backend-owned RAG external provider config persisted in project config."""

    model_config = ConfigDict(extra="ignore")

    enabled: bool = Field(default=False)
    transport_enabled: bool = Field(default=False)
    provider_name: str = Field(default="future_external")
    model_name: str | None = Field(default=None)
    allowed_providers: list[str] | None = Field(default=None)
    allowed_models: list[str] | None = Field(default=None)
    base_url: str | None = Field(default=None)
    timeout_seconds: float = Field(default=15.0)
    max_output_tokens: int | None = Field(default=None)
    max_prompt_chars: int = Field(default=12000)
    max_output_chars: int = Field(default=2000)
    env: ExternalProviderEnvProjectConfig | None = Field(default=None)


class ProjectConfig(BaseModel):
    """????"""
    schema_version: Literal["project-config.v1"] = Field(default="project-config.v1")
    project: ProjectMeta
    svn: SvnConfig
    paths: list[PathRule] = Field(default_factory=list)
    filters: FilterConfig = Field(default_factory=FilterConfig)
    table_convention: TableConvention = Field(default_factory=TableConvention)
    doc_templates: dict[str, str] = Field(default_factory=dict, description="??????")
    models: dict[str, ModelSlotRef] = Field(default_factory=dict, description="Unified model router slot mapping by model_type")
    external_provider_config: ExternalProviderProjectConfig | None = Field(
        default=None,
        description="Legacy compatibility config. Formal model calls must go through the unified model router.",
    )


class ProjectTablesSourceConfig(BaseModel):
    """Project-local table source config persisted under the project bundle."""

    roots: list[str] = Field(default_factory=list)
    include: list[str] = Field(default_factory=lambda: list(DEFAULT_TABLES_INCLUDE_PATTERNS))
    exclude: list[str] = Field(default_factory=lambda: list(DEFAULT_TABLES_EXCLUDE_PATTERNS))
    header_row: int = Field(default=1)
    primary_key_candidates: list[str] = Field(
        default_factory=lambda: list(DEFAULT_TABLES_PRIMARY_KEY_CANDIDATES)
    )


class ProjectDocsSourceConfig(BaseModel):
    """Project-local docs source config persisted under the project bundle."""

    roots: list[str] = Field(default_factory=list)
    include: list[str] = Field(default_factory=lambda: list(DEFAULT_DOCS_INCLUDE_PATTERNS))
    exclude: list[str] = Field(default_factory=lambda: list(DEFAULT_DOCS_EXCLUDE_PATTERNS))


class ProjectScriptsSourceConfig(BaseModel):
    """Project-local scripts source config persisted under the project bundle."""

    roots: list[str] = Field(default_factory=list)
    include: list[str] = Field(default_factory=lambda: list(DEFAULT_SCRIPTS_INCLUDE_PATTERNS))
    exclude: list[str] = Field(default_factory=lambda: list(DEFAULT_SCRIPTS_EXCLUDE_PATTERNS))


class UserGameConfig(BaseModel):
    """??????"""
    my_role: Literal["maintainer", "planner", "consumer"] = Field(default="consumer", description="Legacy local role shortcut")
    agent_profiles: dict[str, LocalAgentProfile] = Field(
        default_factory=dict,
        description="Local agent capability boundary profiles. This is a local safety boundary, not a server auth system.",
    )
    svn_local_root: Union[str, None] = Field(default=None, description="??SVN???????")
    svn_url: Union[str, None] = Field(default=None, description="SVN??URL")
    svn_username: Union[str, None] = Field(default=None, description="SVN???")
    svn_password: Union[str, None] = Field(default=None, description="SVN??(????)")
    svn_trust_cert: bool = Field(default=False, description="??????")


class ValidationIssue(BaseModel):
    """??????"""
    severity: Literal["error", "warning"]
    path: str = Field(description="????")
    message: str = Field(description="????")


def load_project_config(svn_root: Path) -> Union[ProjectConfig, None]:
    """????????????None"""
    config_paths = [
        get_project_config_path(svn_root),
        get_legacy_project_config_path(svn_root),
    ]
    for config_path in config_paths:
        if not config_path.exists():
            continue
        try:
            with open(config_path, "r", encoding="utf-8") as f:
                data = yaml.safe_load(f)
            return ProjectConfig.model_validate(data)
        except Exception:
            continue
    return None


def load_project_tables_source_config(project_root: Path) -> ProjectTablesSourceConfig | None:
    """Load project-local tables source config from the project bundle."""
    config_path = get_project_tables_source_path(project_root)
    if not config_path.exists():
        return None
    try:
        with open(config_path, "r", encoding="utf-8") as f:
            data = yaml.safe_load(f) or {}
        return ProjectTablesSourceConfig.model_validate(data)
    except Exception:
        return None


def load_project_docs_source_config(project_root: Path) -> ProjectDocsSourceConfig | None:
    """Load project-local docs source config from the project bundle."""
    config_path = get_project_docs_source_path(project_root)
    if not config_path.exists():
        return None
    try:
        with open(config_path, "r", encoding="utf-8") as f:
            data = yaml.safe_load(f) or {}
        return ProjectDocsSourceConfig.model_validate(data)
    except Exception:
        return None


def load_project_scripts_source_config(project_root: Path) -> ProjectScriptsSourceConfig | None:
    """Load project-local scripts source config from the project bundle."""
    config_path = get_project_scripts_source_path(project_root)
    if not config_path.exists():
        return None
    try:
        with open(config_path, "r", encoding="utf-8") as f:
            data = yaml.safe_load(f) or {}
        return ProjectScriptsSourceConfig.model_validate(data)
    except Exception:
        return None


def save_project_config(svn_root: Path, cfg: ProjectConfig) -> None:
    """???????????"""
    config_path = get_project_config_path(svn_root)
    config_path.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.NamedTemporaryFile(
        mode="w",
        encoding="utf-8",
        dir=config_path.parent,
        delete=False,
        suffix=".tmp"
    ) as tmp:
        yaml.dump(
            cfg.model_dump(exclude_defaults=False),
            tmp,
            allow_unicode=True,
            default_flow_style=False,
            sort_keys=True
        )
        tmp_path = tmp.name
    Path(tmp_path).replace(config_path)


def save_project_tables_source_config(project_root: Path, cfg: ProjectTablesSourceConfig) -> None:
    """Persist project-local tables source config under the project bundle."""
    config_path = get_project_tables_source_path(project_root)
    config_path.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.NamedTemporaryFile(
        mode="w",
        encoding="utf-8",
        dir=config_path.parent,
        delete=False,
        suffix=".tmp"
    ) as tmp:
        yaml.dump(
            cfg.model_dump(exclude_defaults=False),
            tmp,
            allow_unicode=True,
            default_flow_style=False,
            sort_keys=True
        )
        tmp_path = tmp.name
    Path(tmp_path).replace(config_path)


def save_project_docs_source_config(project_root: Path, cfg: ProjectDocsSourceConfig) -> None:
    """Persist project-local docs source config under the project bundle."""
    config_path = get_project_docs_source_path(project_root)
    config_path.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.NamedTemporaryFile(
        mode="w",
        encoding="utf-8",
        dir=config_path.parent,
        delete=False,
        suffix=".tmp"
    ) as tmp:
        yaml.dump(
            cfg.model_dump(exclude_defaults=False),
            tmp,
            allow_unicode=True,
            default_flow_style=False,
            sort_keys=True
        )
        tmp_path = tmp.name
    Path(tmp_path).replace(config_path)


def save_project_scripts_source_config(project_root: Path, cfg: ProjectScriptsSourceConfig) -> None:
    """Persist project-local scripts source config under the project bundle."""
    config_path = get_project_scripts_source_path(project_root)
    config_path.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.NamedTemporaryFile(
        mode="w",
        encoding="utf-8",
        dir=config_path.parent,
        delete=False,
        suffix=".tmp"
    ) as tmp:
        yaml.dump(
            cfg.model_dump(exclude_defaults=False),
            tmp,
            allow_unicode=True,
            default_flow_style=False,
            sort_keys=True
        )
        tmp_path = tmp.name
    Path(tmp_path).replace(config_path)


def validate_project_config(cfg: ProjectConfig) -> list[ValidationIssue]:
    """??????"""
    issues = []
    svn_root_str = cfg.svn.root or ""
    is_remote = any(svn_root_str.startswith(p) for p in ("svn://", "svn+ssh://", "http://", "https://", "file://"))
    if not is_remote:
        svn_root = Path(svn_root_str)
        if svn_root_str and not svn_root.exists():
            issues.append(ValidationIssue(
                severity="warning",
                path="svn.root",
                message=f"SVN??????: {svn_root}",
            ))
        elif svn_root_str and not (svn_root / ".svn").exists():
            issues.append(ValidationIssue(
                severity="warning",
                path="svn.root",
                message=f"????SVN????: {svn_root}",
            ))
    id_ranges = cfg.table_convention.id_ranges
    for i, range1 in enumerate(id_ranges):
        for j, range2 in enumerate(id_ranges[i+1:], i+1):
            if (range1.start <= range2.end and range2.start <= range1.end):
                issues.append(ValidationIssue(
                    severity="warning",
                    path=f"table_convention.id_ranges[{i}]",
                    message=f"ID????: {range1.type}({range1.start}-{range1.end}) ? {range2.type}({range2.start}-{range2.end})"
                ))
    for i, rule in enumerate(cfg.paths):
        try:
            if not rule.path.strip():
                issues.append(ValidationIssue(
                    severity="error",
                    path=f"paths[{i}].path",
                    message="??????"
                ))
        except Exception as e:
            issues.append(ValidationIssue(
                severity="error",
                path=f"paths[{i}]",
                message=f"????????: {e}"
            ))
    return issues


_USER_SECRET_FIELDS: frozenset[str] = frozenset({"svn_password"})


def load_user_config() -> UserGameConfig:
    """?????????????"""
    config_paths = [get_user_config_path(), get_legacy_user_config_path()]
    for config_path in config_paths:
        if not config_path.exists():
            continue
        try:
            with open(config_path, "r", encoding="utf-8") as f:
                data = yaml.safe_load(f) or {}
            try:
                from ltclaw_gy_x.security.secret_store import decrypt_dict_fields
                data = decrypt_dict_fields(dict(data), _USER_SECRET_FIELDS)
            except Exception:
                pass
            return UserGameConfig.model_validate(data)
        except Exception:
            continue
    return UserGameConfig()


def save_user_config(cfg: UserGameConfig) -> None:
    """??????????????????"""
    config_path = get_user_config_path()
    config_path.parent.mkdir(parents=True, exist_ok=True)
    payload = cfg.model_dump(exclude_defaults=False)
    try:
        from ltclaw_gy_x.security.secret_store import encrypt_dict_fields
        payload = encrypt_dict_fields(payload, _USER_SECRET_FIELDS)
    except Exception:
        pass
    with tempfile.NamedTemporaryFile(
        mode="w",
        encoding="utf-8",
        dir=config_path.parent,
        delete=False,
        suffix=".tmp"
    ) as tmp:
        yaml.dump(
            payload,
            tmp,
            allow_unicode=True,
            default_flow_style=False,
            sort_keys=True
        )
        tmp_path = tmp.name
    Path(tmp_path).replace(config_path)
