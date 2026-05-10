"""
???????????

????????????pydantic?????/??/?????
"""

import os
import tempfile
import yaml
from datetime import datetime
from pathlib import Path
from typing import Any, Literal, Union
from pydantic import BaseModel, Field

from .paths import (
    get_legacy_project_config_path,
    get_legacy_user_config_path,
    get_project_config_path,
    get_user_config_path,
)


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


class ProjectConfig(BaseModel):
    """????"""
    schema_version: Literal["project-config.v1"] = Field(default="project-config.v1")
    project: ProjectMeta
    svn: SvnConfig
    paths: list[PathRule] = Field(default_factory=list)
    filters: FilterConfig = Field(default_factory=FilterConfig)
    table_convention: TableConvention = Field(default_factory=TableConvention)
    doc_templates: dict[str, str] = Field(default_factory=dict, description="??????")
    models: dict[str, ModelSlotRef] = Field(default_factory=dict, description="AI????")
    external_provider_config: dict[str, Any] | None = Field(default=None, description="Backend-owned RAG provider config")


class UserGameConfig(BaseModel):
    """??????"""
    my_role: Literal["maintainer", "consumer"] = Field(default="consumer", description="????")
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
