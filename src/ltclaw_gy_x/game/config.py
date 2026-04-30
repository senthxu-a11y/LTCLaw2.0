"""
游戏策划工作台配置管理

提供项目配置和用户配置的pydantic模型、加载/保存/校验功能。
"""

import os
import tempfile
import yaml
from datetime import datetime
from pathlib import Path
from typing import Literal, Union
from pydantic import BaseModel, Field

from .paths import get_project_config_path, get_user_config_path


class ProjectMeta(BaseModel):
    """项目基本信息"""
    name: str = Field(description="项目名称")
    engine: str = Field(description="游戏引擎 (如Unity, Unreal等)")
    language: str = Field(default="zh", description="主要语言代码")


class SvnConfig(BaseModel):
    """SVN配置"""
    root: str = Field(description="SVN工作副本根目录路径")
    poll_interval_seconds: int = Field(default=300, description="轮询间隔秒数")
    jitter_seconds: int = Field(default=30, description="随机抖动秒数，避免多机同时提交")


class PathRule(BaseModel):
    """路径规则：定义哪些路径包含哪类资源"""
    path: str = Field(description="路径模式 (支持glob)")
    semantic: Literal["table", "doc", "template"] = Field(description="语义类型")
    system: Union[str, None] = Field(default=None, description="所属系统名称")


class FilterConfig(BaseModel):
    """过滤配置"""
    include_ext: list[str] = Field(default_factory=lambda: [".xlsx", ".xls", ".csv", ".md", ".txt", ".docx"],
                                   description="包含的文件扩展名")
    exclude_glob: list[str] = Field(default_factory=lambda: ["**/temp/**", "**/.svn/**", "**/~$*"],
                                    description="排除的glob模式")


class IDRange(BaseModel):
    """ID范围定义"""
    type: str = Field(description="范围类型 (如系统名称)")
    start: int = Field(description="起始ID")
    end: int = Field(description="结束ID (包含)")


class TableConvention(BaseModel):
    """表格约定"""
    header_row: int = Field(default=1, description="表头行号(1-based)")
    comment_row: Union[int, None] = Field(default=None, description="注释行号(1-based)")
    primary_key_field: str = Field(default="ID", description="主键字段名 (project 默认)")
    per_table_primary_keys: dict[str, str] = Field(
        default_factory=dict,
        description="按表名覆盖主键字段，例如 {\"道具\": \"道具id\"}",
    )
    auto_detect_primary_key: bool = Field(
        default=True,
        description="未命中默认/覆盖时，按表头自动嗅探含 'id' 的字段（支持中英文）",
    )
    id_ranges: list[IDRange] = Field(default_factory=list, description="ID分段规则")

    def resolve_primary_key(
        self,
        table_name: str | None = None,
        headers: list[str] | None = None,
    ) -> str:
        """根据 per-table 覆盖 + 自动嗅探返回最终主键字段名。

        优先级：
          1) per_table_primary_keys[table_name]
          2) project 默认 primary_key_field（若在 headers 中能匹配）
          3) auto_detect_primary_key=True 时按 headers 中
             "id" 关键字 (大小写不敏感, 支持中文 "id"/"编号"/"序号") 嗅探
          4) 回退到 project 默认 primary_key_field
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
        # 嗅探：优先精确 "id" / "编号" / "序号"，再退化到包含 "id" 的字段
        sniff_exact = ("id", "编号", "序号")
        for h in lowered:
            if h.lower() in sniff_exact:
                return h
        for h in lowered:
            if "id" in h.lower() or "编号" in h or "序号" in h:
                return h
        return default_key


class ModelSlotRef(BaseModel):
    """模型槽引用"""
    provider_id: str = Field(description="Provider ID")
    model_id: str = Field(description="Model ID")


class ProjectConfig(BaseModel):
    """项目配置"""
    schema_version: Literal["project-config.v1"] = Field(default="project-config.v1")
    project: ProjectMeta
    svn: SvnConfig
    paths: list[PathRule] = Field(default_factory=list)
    filters: FilterConfig = Field(default_factory=FilterConfig)
    table_convention: TableConvention = Field(default_factory=TableConvention)
    doc_templates: dict[str, str] = Field(default_factory=dict, description="文档模板映射")
    models: dict[str, ModelSlotRef] = Field(default_factory=dict, description="AI模型配置")


class UserGameConfig(BaseModel):
    """用户游戏配置"""
    my_role: Literal["maintainer", "consumer"] = Field(default="consumer", description="我的角色")
    svn_local_root: Union[str, None] = Field(default=None, description="本地SVN工作副本根目录")
    svn_url: Union[str, None] = Field(default=None, description="SVN远端URL")
    svn_username: Union[str, None] = Field(default=None, description="SVN用户名")
    svn_password: Union[str, None] = Field(default=None, description="SVN密码(落盘加密)")
    svn_trust_cert: bool = Field(default=False, description="信任自签证书")


class ValidationIssue(BaseModel):
    """配置校验问题"""
    severity: Literal["error", "warning"]
    path: str = Field(description="问题路径")
    message: str = Field(description="问题描述")


def load_project_config(svn_root: Path) -> Union[ProjectConfig, None]:
    """加载项目配置，不存在返回None"""
    config_path = get_project_config_path(svn_root)
    if not config_path.exists():
        return None
    try:
        with open(config_path, "r", encoding="utf-8") as f:
            data = yaml.safe_load(f)
        return ProjectConfig.model_validate(data)
    except Exception:
        return None


def save_project_config(svn_root: Path, cfg: ProjectConfig) -> None:
    """保存项目配置，原子写入"""
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
    """校验项目配置"""
    issues = []
    svn_root_str = cfg.svn.root or ""
    is_remote = any(svn_root_str.startswith(p) for p in ("svn://", "svn+ssh://", "http://", "https://", "file://"))
    if not is_remote:
        svn_root = Path(svn_root_str)
        if svn_root_str and not svn_root.exists():
            issues.append(ValidationIssue(
                severity="warning",
                path="svn.root",
                message=f"SVN根目录不存在: {svn_root}",
            ))
        elif svn_root_str and not (svn_root / ".svn").exists():
            issues.append(ValidationIssue(
                severity="warning",
                path="svn.root",
                message=f"目录不是SVN工作副本: {svn_root}",
            ))
    id_ranges = cfg.table_convention.id_ranges
    for i, range1 in enumerate(id_ranges):
        for j, range2 in enumerate(id_ranges[i+1:], i+1):
            if (range1.start <= range2.end and range2.start <= range1.end):
                issues.append(ValidationIssue(
                    severity="warning",
                    path=f"table_convention.id_ranges[{i}]",
                    message=f"ID范围重叠: {range1.type}({range1.start}-{range1.end}) 与 {range2.type}({range2.start}-{range2.end})"
                ))
    for i, rule in enumerate(cfg.paths):
        try:
            if not rule.path.strip():
                issues.append(ValidationIssue(
                    severity="error",
                    path=f"paths[{i}].path",
                    message="路径不能为空"
                ))
        except Exception as e:
            issues.append(ValidationIssue(
                severity="error",
                path=f"paths[{i}]",
                message=f"路径规则校验失败: {e}"
            ))
    return issues


_USER_SECRET_FIELDS: frozenset[str] = frozenset({"svn_password"})


def load_user_config() -> UserGameConfig:
    """加载用户配置，解密敏感字段"""
    config_path = get_user_config_path()
    if not config_path.exists():
        return UserGameConfig()
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
        return UserGameConfig()


def save_user_config(cfg: UserGameConfig) -> None:
    """保存用户配置，原子写入；敏感字段加密"""
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