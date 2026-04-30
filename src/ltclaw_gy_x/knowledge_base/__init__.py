"""Local knowledge base — zero-dep vector index + JSONL persistence."""
from .local_vector_store import LocalVectorStore
from .kb_store import KnowledgeBaseEntry, KnowledgeBaseStore, get_kb_store

__all__ = [
    "LocalVectorStore",
    "KnowledgeBaseEntry",
    "KnowledgeBaseStore",
    "get_kb_store",
]