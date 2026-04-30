"""
游戏策划工作台业务模型

定义所有跨模块流转的数据结构，包括表索引、文档索引、依赖关系等核心业务对象。
"""

from datetime import datetime, timezone
from enum import Enum
from typing import Literal, Optional, Union
from pydantic import BaseModel, Field


class FieldConfidence(str, Enum):
    """字段信息置信度"""
    CONFIRMED = "confirmed"
    HIGH_AI = "high_ai"
    LOW_AI = "low_ai"


class FieldInfo(BaseModel):
    """字段信息"""
    name: str = Field(description="字段名")
    type: str = Field(description="数据类型")
    description: str = Field(description="字段描述")
    confidence: FieldConfidence = Field(description="置信度")
    confirmed_by: Union[str, None] = Field(default=None, description="确认人")
    confirmed_at: Union[datetime, None] = Field(default=None, description="确认时间")
    ai_raw_description: Union[str, None] = Field(default=None, description="AI原始描述")
    references: list[str] = Field(default_factory=list, description="引用关系")
    tags: list[str] = Field(default_factory=list, description="标签")


class TableIndex(BaseModel):
    """表索引"""
    schema_version: Literal["table-index.v1"] = Field(default="table-index.v1")
    table_name: str = Field(description="表名")
    source_path: str = Field(description="源文件路径(相对svn_root)")
    source_hash: str = Field(description="源文件hash(sha256:xxx)")
    svn_revision: int = Field(description="SVN版本号")
    system: Union[str, None] = Field(default=None, description="所属系统")
    row_count: int = Field(description="数据行数")
    header_row: int = Field(default=1, description="表头行号")
    primary_key: str = Field(default="ID", description="主键字段名")
    ai_summary: str = Field(description="AI生成的表概要")
    ai_summary_confidence: float = Field(description="概要置信度")
    fields: list[FieldInfo] = Field(default_factory=list, description="字段列表")
    id_ranges: list[dict] = Field(default_factory=list, description="ID分段信息")
    last_indexed_at: datetime = Field(description="最后索引时间")
    indexer_model: str = Field(description="索引使用的模型")


class DocIndex(BaseModel):
    """文档索引"""
    schema_version: Literal["doc-index.v1"] = Field(default="doc-index.v1")
    source_path: str = Field(description="源文件路径(相对svn_root)")
    source_hash: str = Field(description="源文件hash")
    svn_revision: int = Field(description="SVN版本号")
    doc_type: str = Field(description="文档类型")
    title: str = Field(description="文档标题")
    summary: str = Field(description="文档摘要")
    related_tables: list[str] = Field(default_factory=list, description="关联表列表")
    last_indexed_at: datetime = Field(description="最后索引时间")


class DependencyEdge(BaseModel):
    """依赖边"""
    from_table: str = Field(description="源表名")
    from_field: str = Field(description="源字段名")
    to_table: str = Field(description="目标表名")
    to_field: str = Field(description="目标字段名")
    confidence: FieldConfidence = Field(description="置信度")
    inferred_by: Literal["rule", "llm", "manual", "code_regex"] = Field(description="推断方式")


class DependencyGraph(BaseModel):
    """依赖关系图"""
    schema_version: Literal["dep-graph.v1"] = Field(default="dep-graph.v1")
    edges: list[DependencyEdge] = Field(default_factory=list, description="依赖边列表")
    last_updated: datetime = Field(description="最后更新时间")


class SystemGroup(BaseModel):
    """系统分组"""
    name: str = Field(description="系统名称")
    tables: list[str] = Field(default_factory=list, description="包含的表列表")
    description: Union[str, None] = Field(default=None, description="系统描述")
    source: Literal["config", "ai", "manual"] = Field(description="分组来源")


class ChangeSet(BaseModel):
    """变更集"""
    from_rev: int = Field(description="起始版本号")
    to_rev: int = Field(description="目标版本号")
    added: list[str] = Field(default_factory=list, description="新增文件(相对svn_root)")
    modified: list[str] = Field(default_factory=list, description="修改文件")
    deleted: list[str] = Field(default_factory=list, description="删除文件")


class CommitResult(BaseModel):
    """提交结果"""
    revision: Union[int, None] = Field(default=None, description="新版本号(失败为None)")
    files_committed: int = Field(default=0, description="已提交文件数")
    skipped_reason: Union[str, None] = Field(default=None, description="跳过原因")


class FieldPatch(BaseModel):
    """字段修补信息"""
    description: Union[str, None] = Field(default=None, description="新的字段描述")
    confidence: Union[FieldConfidence, None] = Field(default=None, description="新的置信度")
    confirmed_by: Union[str, None] = Field(default=None, description="确认人")


class SvnStatus(BaseModel):
    """SVN状态"""
    current_revision: int = Field(description="当前版本号")
    last_polled_at: Union[datetime, None] = Field(default=None, description="最后轮询时间")
    next_poll_at: Union[datetime, None] = Field(default=None, description="下次轮询时间")
    running: bool = Field(default=False, description="是否正在运行")
    my_role: str = Field(description="我的角色")
    configured: bool = Field(description="是否已配置")


class TablePage(BaseModel):
    """表分页结果"""
    total: int = Field(description="总数")
    page: int = Field(description="当前页")
    size: int = Field(description="页大小")
    items: list[TableIndex] = Field(default_factory=list, description="表列表")


class DependencySnapshot(BaseModel):
    """依赖快照"""
    upstream: list[DependencyEdge] = Field(default_factory=list, description="上游依赖")
    downstream: list[DependencyEdge] = Field(default_factory=list, description="下游依赖")


# ============ 代码索引模型 (.cs regex.v1) ============

class CodeSymbolReference(BaseModel):
    """代码中对表/字段或其他符号的引用"""
    target_kind: Literal["table", "field", "symbol"] = Field(description="引用类型")
    target_table: Optional[str] = Field(default=None, description="目标表名")
    target_field: Optional[str] = Field(default=None, description="目标字段名")
    target_symbol: Optional[str] = Field(default=None, description="目标代码符号名")
    line: int = Field(description="行号(0-based)")
    snippet: str = Field(default="", description="代码片段(≤80字)")
    confidence: Literal["confirmed", "inferred"] = Field(default="inferred", description="置信度")


class CodeSymbol(BaseModel):
    """代码符号(类/方法/字段等)"""
    name: str = Field(description="符号名")
    kind: Literal["class", "interface", "struct", "enum", "method", "field", "property"] = Field(description="符号类型")
    parent: Optional[str] = Field(default=None, description="父类名(嵌套)")
    signature: str = Field(default="", description="方法签名/声明行")
    line_start: int = Field(default=0, description="起始行(0-based)")
    line_end: int = Field(default=0, description="结束行(0-based)")
    references: list[CodeSymbolReference] = Field(default_factory=list, description="符号内部引用")
    summary: str = Field(default="", description="单行摘要(取自上方注释)")


class CodeFileIndex(BaseModel):
    """单个 .cs 文件的索引描述符"""
    schema_version: Literal["code-index.v1"] = Field(default="code-index.v1")
    source_path: str = Field(description="源文件路径(相对svn_root)")
    source_hash: str = Field(description="源文件hash(sha256:xxx)")
    svn_revision: int = Field(default=0, description="SVN版本号")
    namespace: Optional[str] = Field(default=None, description="C# 命名空间")
    using: list[str] = Field(default_factory=list, description="using 语句")
    symbols: list[CodeSymbol] = Field(default_factory=list, description="符号列表")
    references: list[CodeSymbolReference] = Field(default_factory=list, description="文件级引用")
    last_indexed_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc), description="最后索引时间")
    indexer_version: str = Field(default="regex.v1", description="索引器版本")
