"""
游戏策划工作台路径管理

提供标准化的文件路径获取函数，支持SVN工作副本、索引输出、本地缓存等目录结构。
"""

from pathlib import Path
import os


def get_index_dir(svn_root: Path) -> Path:
    """获取索引输出根目录: <svn>/.ltclaw_index"""
    return svn_root / ".ltclaw_index"


def get_tables_dir(svn_root: Path) -> Path:
    """获取表索引目录: <svn>/.ltclaw_index/tables"""
    return get_index_dir(svn_root) / "tables"


def get_docs_dir(svn_root: Path) -> Path:
    """获取文档索引目录: <svn>/.ltclaw_index/docs"""
    return get_index_dir(svn_root) / "docs"


def get_project_config_path(svn_root: Path) -> Path:
    """获取项目配置文件路径: <svn>/.ltclaw_index/project_config.yaml"""
    return get_index_dir(svn_root) / "project_config.yaml"


def get_user_config_path() -> Path:
    """获取用户配置文件路径: ~/.ltclaw_gy_x/game_user.yaml"""
    working_dir = Path.home() / ".ltclaw_gy_x"
    if "QWENPAW_WORKING_DIR" in os.environ:
        working_dir = Path(os.environ["QWENPAW_WORKING_DIR"])
    elif "COPAW_WORKING_DIR" in os.environ:
        working_dir = Path(os.environ["COPAW_WORKING_DIR"])
    return working_dir / "game_user.yaml"


def get_workspace_game_dir(workspace_dir: Path) -> Path:
    """获取workspace下游戏相关目录: <ws>/game_index"""
    return workspace_dir / "game_index"


def get_chroma_dir(workspace_dir: Path) -> Path:
    """获取Chroma向量数据库目录: <ws>/game_index/chroma"""
    return get_workspace_game_dir(workspace_dir) / "chroma"


def get_llm_cache_dir(workspace_dir: Path) -> Path:
    """获取LLM调用缓存目录: <ws>/game_index/llm_cache"""
    return get_workspace_game_dir(workspace_dir) / "llm_cache"


def get_svn_cache_dir(workspace_dir: Path) -> Path:
    """获取SVN状态缓存目录: <ws>/game_index/svn_cache"""
    return get_workspace_game_dir(workspace_dir) / "svn_cache"


def get_proposals_dir(workspace_dir: Path) -> Path:
    """获取变更草案目录: <ws>/game_index/proposals"""
    return get_workspace_game_dir(workspace_dir) / "proposals"
