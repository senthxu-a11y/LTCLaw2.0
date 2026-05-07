from __future__ import annotations

import json
import shutil
import tempfile
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Mapping

from .knowledge_release_builders import validate_knowledge_manifest, validate_knowledge_map, validate_release_id
from .models import KnowledgeManifest, KnowledgeMap, KnowledgeReleasePointer
from .paths import get_current_release_path, get_knowledge_releases_dir, get_release_dir


class KnowledgeReleaseStoreError(RuntimeError):
    pass


class KnowledgeReleaseNotFoundError(KnowledgeReleaseStoreError):
    pass


class CurrentKnowledgeReleaseNotSetError(KnowledgeReleaseStoreError):
    pass


IndexPayload = bytes | str | Any


def create_release(
    project_root: Path,
    manifest: KnowledgeManifest,
    knowledge_map: KnowledgeMap,
    indexes: Mapping[str, IndexPayload] | None = None,
    release_notes: str = '',
) -> Path:
    release_id = validate_release_id(manifest.release_id)
    validate_knowledge_map(knowledge_map)
    validate_knowledge_manifest(manifest)
    if knowledge_map.release_id != release_id:
        raise ValueError('Manifest and knowledge map must use the same release id')

    releases_dir = get_knowledge_releases_dir(project_root)
    releases_dir.mkdir(parents=True, exist_ok=True)
    final_dir = get_release_dir(project_root, release_id)
    if final_dir.exists():
        raise FileExistsError(f'Knowledge release already exists: {release_id}')

    staging_dir = releases_dir / f'.{release_id}.tmp'
    if staging_dir.exists():
        shutil.rmtree(staging_dir)

    try:
        staging_dir.mkdir(parents=True, exist_ok=False)
        _atomic_write_json(staging_dir / 'manifest.json', manifest.model_dump(mode='json'))
        _atomic_write_json(staging_dir / 'map.json', knowledge_map.model_dump(mode='json'))
        _atomic_write_text(staging_dir / 'release_notes.md', release_notes)
        _write_indexes(staging_dir / 'indexes', indexes or {})
        staging_dir.replace(final_dir)
    except Exception:
        shutil.rmtree(staging_dir, ignore_errors=True)
        raise

    return final_dir


def list_releases(project_root: Path) -> list[KnowledgeManifest]:
    releases_dir = get_knowledge_releases_dir(project_root)
    if not releases_dir.exists():
        return []

    manifests: list[KnowledgeManifest] = []
    for candidate in sorted(releases_dir.iterdir(), key=lambda item: item.name):
        if not candidate.is_dir() or candidate.name.startswith('.'):
            continue
        manifest_path = candidate / 'manifest.json'
        if not manifest_path.exists():
            continue
        manifests.append(_read_model(manifest_path, KnowledgeManifest))
    return manifests


def load_manifest(project_root: Path, release_id: str) -> KnowledgeManifest:
    release_dir = get_release_dir(project_root, validate_release_id(release_id))
    manifest_path = release_dir / 'manifest.json'
    if not manifest_path.exists():
        raise KnowledgeReleaseNotFoundError(f'Knowledge release manifest not found: {release_id}')
    return _read_model(manifest_path, KnowledgeManifest)


def load_knowledge_map(project_root: Path, release_id: str) -> KnowledgeMap:
    release_dir = get_release_dir(project_root, validate_release_id(release_id))
    map_path = release_dir / 'map.json'
    if not map_path.exists():
        raise KnowledgeReleaseNotFoundError(f'Knowledge release map not found: {release_id}')
    return _read_model(map_path, KnowledgeMap)


def set_current_release(project_root: Path, release_id: str) -> KnowledgeReleasePointer:
    manifest = load_manifest(project_root, release_id)
    pointer = KnowledgeReleasePointer(
        release_id=manifest.release_id,
        updated_at=datetime.now(timezone.utc),
    )
    _atomic_write_json(get_current_release_path(project_root), pointer.model_dump(mode='json'))
    return pointer


def get_current_release(project_root: Path) -> KnowledgeManifest:
    current_path = get_current_release_path(project_root)
    if not current_path.exists():
        raise CurrentKnowledgeReleaseNotSetError('No current knowledge release is set')
    pointer = _read_model(current_path, KnowledgeReleasePointer)
    return load_manifest(project_root, pointer.release_id)


def get_current_release_map(project_root: Path) -> KnowledgeMap:
    current_path = get_current_release_path(project_root)
    if not current_path.exists():
        raise CurrentKnowledgeReleaseNotSetError('No current knowledge release is set')
    pointer = _read_model(current_path, KnowledgeReleasePointer)
    return load_knowledge_map(project_root, pointer.release_id)


def _read_model(path: Path, model_type: type[KnowledgeManifest] | type[KnowledgeMap] | type[KnowledgeReleasePointer]):
    return model_type.model_validate(json.loads(path.read_text(encoding='utf-8')))


def _write_indexes(indexes_dir: Path, indexes: Mapping[str, IndexPayload]) -> None:
    indexes_dir.mkdir(parents=True, exist_ok=True)
    for relative_path, payload in indexes.items():
        target_path = indexes_dir / _normalize_relative_path(relative_path)
        if isinstance(payload, bytes):
            _atomic_write_bytes(target_path, payload)
        elif isinstance(payload, str):
            _atomic_write_text(target_path, payload)
        else:
            _atomic_write_json(target_path, payload)


def _normalize_relative_path(relative_path: str) -> Path:
    candidate = Path(str(relative_path or '').strip())
    if not candidate.parts or candidate.is_absolute():
        raise ValueError(f'Invalid release asset path: {relative_path!r}')
    normalized_parts = [part for part in candidate.parts if part not in ('', '.')]
    if not normalized_parts or any(part == '..' for part in normalized_parts):
        raise ValueError(f'Invalid release asset path: {relative_path!r}')
    return Path(*normalized_parts)


def _atomic_write_json(path: Path, payload: Any) -> None:
    text = json.dumps(payload, ensure_ascii=False, indent=2) + '\n'
    _atomic_write_text(path, text)


def _atomic_write_text(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.NamedTemporaryFile('w', encoding='utf-8', dir=path.parent, delete=False) as handle:
        handle.write(content)
        tmp_path = Path(handle.name)
    try:
        tmp_path.replace(path)
    except Exception:
        tmp_path.unlink(missing_ok=True)
        raise


def _atomic_write_bytes(path: Path, content: bytes) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.NamedTemporaryFile('wb', dir=path.parent, delete=False) as handle:
        handle.write(content)
        tmp_path = Path(handle.name)
    try:
        tmp_path.replace(path)
    except Exception:
        tmp_path.unlink(missing_ok=True)
        raise