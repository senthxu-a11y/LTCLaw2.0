from __future__ import annotations

import asyncio
from fnmatch import fnmatch
import json
import threading
import time
import tempfile
import uuid
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from pydantic import BaseModel, Field

from .canonical_facts_committer import CanonicalFactsCommitter
from .config import (
    load_project_docs_source_config,
    load_project_scripts_source_config,
    load_project_tables_source_config,
)
from .knowledge_formal_map_store import load_formal_knowledge_map
from .knowledge_source_candidate_store import save_latest_source_candidate
from .knowledge_map_candidate import (
    build_map_candidate_from_canonical_facts,
    build_map_diff_review,
    resolve_map_diff_base,
)
from .models import KnowledgeMap
from .paths import (
    get_project_docs_source_path,
    get_project_canonical_tables_dir,
    get_project_key,
    get_project_raw_table_indexes_path,
    get_project_runtime_build_job_path,
    get_project_runtime_build_jobs_dir,
    get_project_scripts_source_path,
    get_project_tables_source_path,
)
from .raw_index_rebuild import rebuild_raw_table_indexes
from .source_discovery import discover_table_sources


_ACTIVE_JOB_STATUSES = {"pending", "running"}
_TERMINAL_JOB_STATUSES = {"succeeded", "failed", "cancelled"}
_MAX_JOB_HISTORY = 20
_DEFAULT_TIMEOUT_SECONDS = 300
_ACTIVE_JOB_HANDLES: dict[str, "_JobHandle"] = {}
_JOB_LOCK = threading.Lock()


class ColdStartJobCounts(BaseModel):
    discovered_table_count: int = 0
    discovered_doc_count: int = 0
    discovered_script_count: int = 0
    raw_table_index_count: int = 0
    canonical_table_count: int = 0
    candidate_table_count: int = 0


class ColdStartJobError(BaseModel):
    stage: str | None = None
    error: str
    source_path: str | None = None


class ColdStartJobState(BaseModel):
    job_id: str
    project_key: str
    project_root: str
    status: str
    stage: str
    progress: int
    message: str
    current_file: str | None = None
    counts: ColdStartJobCounts = Field(default_factory=ColdStartJobCounts)
    warnings: list[str] = Field(default_factory=list)
    errors: list[ColdStartJobError] = Field(default_factory=list)
    next_action: str | None = None
    partial_outputs: dict[str, Any] = Field(default_factory=dict)
    timeout_seconds: int = _DEFAULT_TIMEOUT_SECONDS
    timed_out: bool = False
    candidate_refs: list[str] = Field(default_factory=list)
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    started_at: datetime | None = None
    finished_at: datetime | None = None


class ColdStartJobCreateResponse(BaseModel):
    reused_existing: bool = False
    job: ColdStartJobState


@dataclass(slots=True)
class _JobHandle:
    project_key: str
    job_id: str
    cancel_requested: threading.Event
    thread: threading.Thread


class _CancelledJobError(RuntimeError):
    pass


class _TimedOutJobError(RuntimeError):
    pass


def _now() -> datetime:
    return datetime.now(timezone.utc)


def _write_json_atomic(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.NamedTemporaryFile('w', encoding='utf-8', dir=path.parent, delete=False) as handle:
        handle.write(json.dumps(payload, ensure_ascii=False, indent=2) + "\n")
        temp_path = Path(handle.name)
    temp_path.replace(path)


def _serialize_candidate_refs(candidate_map: KnowledgeMap | None) -> list[str]:
    if candidate_map is None:
        return []
    return sorted(f"table:{table.table_id}" for table in candidate_map.tables)


def load_cold_start_job(project_root: Path, job_id: str) -> ColdStartJobState | None:
    job_path = get_project_runtime_build_job_path(project_root, job_id)
    if not job_path.exists():
        return None
    return ColdStartJobState.model_validate_json(job_path.read_text(encoding="utf-8"))


def load_cold_start_job_with_stale_check(project_root: Path, job_id: str) -> ColdStartJobState | None:
    state = load_cold_start_job(project_root, job_id)
    if state is None:
        return None
    if state.status not in _ACTIVE_JOB_STATUSES:
        return state

    handle = _active_handle(state.project_key)
    if handle is not None and handle.job_id == job_id:
        return state

    state.status = "failed"
    state.stage = "stale"
    state.message = "Cold-start job became stale after runtime restart."
    state.next_action = "retry_cold_start_job"
    state.finished_at = _now()
    _append_error(state, stage="stale", error="cold_start_job_handle_missing")
    return save_cold_start_job(project_root, state)


def save_cold_start_job(project_root: Path, state: ColdStartJobState) -> ColdStartJobState:
    state.updated_at = _now()
    _write_json_atomic(
      get_project_runtime_build_job_path(project_root, state.job_id),
      state.model_dump(mode="json"),
    )
    _prune_old_jobs(project_root)
    return state


def _list_cold_start_jobs(project_root: Path) -> list[ColdStartJobState]:
    jobs_dir = get_project_runtime_build_jobs_dir(project_root)
    if not jobs_dir.exists() or not jobs_dir.is_dir():
        return []
    states: list[ColdStartJobState] = []
    for job_file in sorted(jobs_dir.glob("*.json")):
        try:
            states.append(ColdStartJobState.model_validate_json(job_file.read_text(encoding="utf-8")))
        except Exception:
            continue
    states.sort(key=lambda item: item.updated_at, reverse=True)
    return states


def _prune_old_jobs(project_root: Path) -> None:
    jobs = _list_cold_start_jobs(project_root)
    for stale_job in jobs[_MAX_JOB_HISTORY:]:
        get_project_runtime_build_job_path(project_root, stale_job.job_id).unlink(missing_ok=True)


def _active_handle(project_key: str) -> _JobHandle | None:
    with _JOB_LOCK:
        handle = _ACTIVE_JOB_HANDLES.get(project_key)
        if handle is None:
            return None
        if handle.thread.is_alive():
            return handle
        _ACTIVE_JOB_HANDLES.pop(project_key, None)
        return None


def create_or_get_cold_start_job(project_root: Path, *, timeout_seconds: int = _DEFAULT_TIMEOUT_SECONDS) -> tuple[ColdStartJobState, bool]:
    project_root = Path(project_root).expanduser()
    project_key = get_project_key(project_root)
    existing_handle = _active_handle(project_key)
    if existing_handle is not None:
        existing_state = load_cold_start_job(project_root, existing_handle.job_id)
        if existing_state is not None and existing_state.status in _ACTIVE_JOB_STATUSES:
            return existing_state, True

    created_at = _now()
    state = ColdStartJobState(
        job_id=uuid.uuid4().hex,
        project_key=project_key,
        project_root=str(project_root),
        status="pending",
        stage="checking_project_root",
        progress=0,
        message="Cold-start job queued.",
        next_action="checking_project_root",
        timeout_seconds=max(1, int(timeout_seconds or _DEFAULT_TIMEOUT_SECONDS)),
        created_at=created_at,
        updated_at=created_at,
    )
    save_cold_start_job(project_root, state)

    cancel_requested = threading.Event()
    thread = threading.Thread(
        target=_run_cold_start_job,
        args=(project_root, state.job_id, cancel_requested),
        name=f"cold-start-job-{state.job_id}",
        daemon=True,
    )
    with _JOB_LOCK:
        _ACTIVE_JOB_HANDLES[project_key] = _JobHandle(
            project_key=project_key,
            job_id=state.job_id,
            cancel_requested=cancel_requested,
            thread=thread,
        )
    thread.start()
    return state, False


def cancel_cold_start_job(project_root: Path, job_id: str) -> ColdStartJobState | None:
    project_root = Path(project_root).expanduser()
    state = load_cold_start_job(project_root, job_id)
    if state is None:
        return None
    if state.status in _TERMINAL_JOB_STATUSES:
        return state

    handle = _active_handle(state.project_key)
    if handle is not None and handle.job_id == job_id:
        handle.cancel_requested.set()

    state.status = "cancelled"
    state.stage = "cancelled"
    state.message = "Cold-start job cancelled."
    state.next_action = None
    state.finished_at = _now()
    save_cold_start_job(project_root, state)
    return state


def _load_state_or_raise(project_root: Path, job_id: str) -> ColdStartJobState:
    state = load_cold_start_job(project_root, job_id)
    if state is None:
        raise FileNotFoundError(f"Cold-start job not found: {job_id}")
    return state


def _ensure_not_cancelled(state: ColdStartJobState, cancel_requested: threading.Event) -> None:
    if cancel_requested.is_set() or state.status == "cancelled":
        raise _CancelledJobError("cold_start_job_cancelled")


def _ensure_not_timed_out(state: ColdStartJobState, started_at: float) -> None:
    if time.monotonic() - started_at > state.timeout_seconds:
        raise _TimedOutJobError("cold_start_job_timed_out")


def _update_job_state(
    project_root: Path,
    job_id: str,
    cancel_requested: threading.Event,
    started_at: float,
    **changes: Any,
) -> ColdStartJobState:
    state = _load_state_or_raise(project_root, job_id)
    _ensure_not_cancelled(state, cancel_requested)
    _ensure_not_timed_out(state, started_at)
    for key, value in changes.items():
        setattr(state, key, value)
    return save_cold_start_job(project_root, state)


def _append_warning(state: ColdStartJobState, warning: str) -> ColdStartJobState:
    if warning and warning not in state.warnings:
        state.warnings.append(warning)
    return state


def _append_error(state: ColdStartJobState, *, stage: str, error: str, source_path: str | None = None) -> ColdStartJobState:
    state.errors.append(ColdStartJobError(stage=stage, error=error, source_path=source_path))
    return state


def _normalize_match_path(path: str) -> str:
    return path.replace("\\", "/").strip("/")


def _matches_any(path: str, patterns: list[str]) -> bool:
    normalized_path = _normalize_match_path(path).lower()
    return any(fnmatch(normalized_path, _normalize_match_path(pattern).lower()) for pattern in patterns)


def _scan_optional_sources(
    project_root: Path,
    *,
    label: str,
    config_path: Path,
    config: Any,
) -> dict[str, Any]:
    if not config_path.exists():
        return {
            "configured": False,
            "available_count": 0,
            "warnings": [],
            "errors": [],
            "roots": [],
        }
    if config is None:
        return {
            "configured": True,
            "available_count": 0,
            "warnings": [f"{label}_skipped_invalid_config"],
            "errors": [f"{label}_config_invalid"],
            "roots": [],
        }

    include_patterns = [str(pattern or "").strip() for pattern in getattr(config, "include", []) if str(pattern or "").strip()]
    exclude_patterns = [str(pattern or "").strip() for pattern in getattr(config, "exclude", []) if str(pattern or "").strip()]
    warnings: list[str] = []
    errors: list[str] = []
    resolved_roots: list[dict[str, Any]] = []
    available_paths: list[str] = []

    for root in getattr(config, "roots", []) or []:
        configured_root = str(root or "").strip()
        if not configured_root:
            continue
        root_path = Path(configured_root.replace("\\", "/")).expanduser()
        if not root_path.is_absolute():
            root_path = project_root / configured_root
        root_entry = {
            "configured_root": configured_root,
            "resolved_root": root_path.as_posix(),
            "exists": root_path.exists(),
            "is_directory": root_path.is_dir(),
        }
        resolved_roots.append(root_entry)
        if not root_path.exists():
            warnings.append(f"{label}_skipped_missing_root:{configured_root}")
            continue
        if not root_path.is_dir():
            warnings.append(f"{label}_skipped_root_not_directory:{configured_root}")
            continue
        try:
            for file_path in root_path.rglob("*"):
                if not file_path.is_file():
                    continue
                try:
                    relative_path = file_path.relative_to(project_root).as_posix()
                except ValueError:
                    relative_path = file_path.as_posix()
                if exclude_patterns and _matches_any(relative_path, exclude_patterns):
                    continue
                if include_patterns and not _matches_any(relative_path, include_patterns):
                    continue
                available_paths.append(relative_path)
        except Exception as exc:  # noqa: BLE001
            errors.append(f"{label}_scan_error:{configured_root}:{exc}")

    if resolved_roots and not available_paths:
        warnings.append(f"{label}_skipped_no_available_sources")

    return {
        "configured": True,
        "available_count": len(available_paths),
        "warnings": warnings,
        "errors": errors,
        "roots": resolved_roots,
        "available_paths": sorted(set(available_paths)),
    }


def _run_cold_start_job(project_root: Path, job_id: str, cancel_requested: threading.Event) -> None:
    started_at = time.monotonic()
    current_stage = "checking_project_root"
    try:
        state = _load_state_or_raise(project_root, job_id)
        state.status = "running"
        state.started_at = _now()
        state.message = "Checking local project root."
        state.progress = 5
        save_cold_start_job(project_root, state)

        if not project_root.exists() or not project_root.is_dir():
            state.status = "failed"
            state.stage = current_stage
            state.message = "Local project root is missing."
            state.next_action = "set_project_root"
            _append_error(state, stage=current_stage, error="project_root_missing", source_path=str(project_root))
            state.finished_at = _now()
            save_cold_start_job(project_root, state)
            return

        tables_config = load_project_tables_source_config(project_root)
        if tables_config is None:
            state.status = "failed"
            state.stage = "discovering_sources"
            state.progress = 20
            state.message = "Tables source is not configured."
            state.next_action = "configure_tables_source"
            state.partial_outputs["tables_config_path"] = str(get_project_tables_source_path(project_root))
            _append_error(state, stage="discovering_sources", error="tables_source_not_configured")
            state.finished_at = _now()
            save_cold_start_job(project_root, state)
            return

        docs_scan = _scan_optional_sources(
            project_root,
            label="docs",
            config_path=get_project_docs_source_path(project_root),
            config=load_project_docs_source_config(project_root),
        )
        scripts_scan = _scan_optional_sources(
            project_root,
            label="scripts",
            config_path=get_project_scripts_source_path(project_root),
            config=load_project_scripts_source_config(project_root),
        )
        state.counts.discovered_doc_count = int(docs_scan.get("available_count") or 0)
        state.counts.discovered_script_count = int(scripts_scan.get("available_count") or 0)
        state.partial_outputs["optional_sources"] = {
            "docs": docs_scan,
            "scripts": scripts_scan,
        }
        for warning in docs_scan.get("warnings", []):
            _append_warning(state, warning)
        for warning in scripts_scan.get("warnings", []):
            _append_warning(state, warning)
        for error in docs_scan.get("errors", []):
            _append_error(state, stage="discovering_sources", error=error, source_path=str(get_project_docs_source_path(project_root)))
        for error in scripts_scan.get("errors", []):
            _append_error(state, stage="discovering_sources", error=error, source_path=str(get_project_scripts_source_path(project_root)))
        save_cold_start_job(project_root, state)

        current_stage = "discovering_sources"
        state = _update_job_state(
            project_root,
            job_id,
            cancel_requested,
            started_at,
            stage=current_stage,
            progress=20,
            message="Discovering table sources.",
            next_action="run_source_discovery",
            partial_outputs={**state.partial_outputs, "tables_config_path": str(get_project_tables_source_path(project_root))},
        )
        discovery = discover_table_sources(project_root, tables_config)
        state = _load_state_or_raise(project_root, job_id)
        _ensure_not_cancelled(state, cancel_requested)
        _ensure_not_timed_out(state, started_at)
        available_tables = [item for item in discovery["table_files"] if item.get("status") == "available"]
        state.counts.discovered_table_count = len(available_tables)
        state.current_file = available_tables[0]["source_path"] if available_tables else None
        state.partial_outputs["discovery_summary"] = discovery["summary"]
        for item in discovery.get("unsupported_files", []):
            _append_warning(state, f"unsupported:{item.get('source_path')}")
        for item in discovery.get("excluded_files", []):
            _append_warning(state, f"excluded:{item.get('source_path')}")
        if discovery.get("errors"):
            for item in discovery["errors"]:
                _append_error(
                    state,
                    stage=current_stage,
                    error=str(item.get("reason") or "source_discovery_error"),
                    source_path=item.get("source_path"),
                )
        if not available_tables:
            state.status = "failed"
            state.message = "No available table sources were discovered."
            state.next_action = str(discovery.get("next_action") or "configure_tables_source")
            state.finished_at = _now()
            save_cold_start_job(project_root, state)
            return
        save_cold_start_job(project_root, state)

        current_stage = "building_raw_index"
        state = _update_job_state(
            project_root,
            job_id,
            cancel_requested,
            started_at,
            stage=current_stage,
            progress=40,
            message="Building raw table indexes.",
            next_action="run_raw_index_rebuild",
            current_file=available_tables[0]["source_path"],
        )
        raw_result = asyncio.run(rebuild_raw_table_indexes(project_root, tables_config))
        state = _load_state_or_raise(project_root, job_id)
        _ensure_not_cancelled(state, cancel_requested)
        _ensure_not_timed_out(state, started_at)
        state.counts.raw_table_index_count = int(raw_result.get("raw_table_index_count") or 0)
        state.partial_outputs["raw_table_indexes_path"] = str(get_project_raw_table_indexes_path(project_root))
        for item in raw_result.get("errors", []):
            error_text = str(item.get("error") or "raw_index_error")
            if state.counts.raw_table_index_count > 0:
                _append_warning(state, error_text)
            else:
                _append_error(state, stage=current_stage, error=error_text, source_path=item.get("source_path"))
        if state.counts.raw_table_index_count <= 0:
            state.status = "failed"
            state.message = "Raw table index rebuild failed."
            state.next_action = str(raw_result.get("next_action") or "run_raw_index_rebuild")
            state.finished_at = _now()
            save_cold_start_job(project_root, state)
            return
        save_cold_start_job(project_root, state)

        current_stage = "building_canonical_facts"
        state = _update_job_state(
            project_root,
            job_id,
            cancel_requested,
            started_at,
            stage=current_stage,
            progress=60,
            message="Building canonical facts.",
            next_action="run_canonical_rebuild",
            current_file=get_project_raw_table_indexes_path(project_root).name,
        )
        canonical_result = CanonicalFactsCommitter(project_root).rebuild_tables(force=False)
        state = _load_state_or_raise(project_root, job_id)
        _ensure_not_cancelled(state, cancel_requested)
        _ensure_not_timed_out(state, started_at)
        state.counts.canonical_table_count = canonical_result.canonical_table_count
        state.partial_outputs["canonical_tables_dir"] = str(get_project_canonical_tables_dir(project_root))
        for item in canonical_result.errors:
            error_text = str(item.error)
            if canonical_result.canonical_table_count > 0:
                _append_warning(state, error_text)
            else:
                _append_error(state, stage=current_stage, error=error_text, source_path=item.table_id)
        if canonical_result.canonical_table_count <= 0:
            state.status = "failed"
            state.message = "Canonical facts rebuild failed."
            state.next_action = "run_canonical_rebuild"
            state.finished_at = _now()
            save_cold_start_job(project_root, state)
            return
        save_cold_start_job(project_root, state)

        current_stage = "building_candidate_map"
        state = _update_job_state(
            project_root,
            job_id,
            cancel_requested,
            started_at,
            stage=current_stage,
            progress=80,
            message="Building candidate map from canonical facts.",
            next_action="build_candidate_from_source",
            current_file=None,
        )
        existing_formal_map = None
        record = load_formal_knowledge_map(project_root)
        if record is not None:
            existing_formal_map = record.knowledge_map
        candidate_result = build_map_candidate_from_canonical_facts(project_root, existing_formal_map=existing_formal_map)
        state = _load_state_or_raise(project_root, job_id)
        _ensure_not_cancelled(state, cancel_requested)
        _ensure_not_timed_out(state, started_at)
        state.warnings.extend([item for item in candidate_result.warnings if item not in state.warnings])
        state.counts.candidate_table_count = len(candidate_result.map.tables) if candidate_result.map is not None else 0
        state.candidate_refs = _serialize_candidate_refs(candidate_result.map)
        state.partial_outputs["candidate_mode"] = candidate_result.mode
        if candidate_result.map is None or candidate_result.mode == "no_canonical_facts":
            state.status = "failed"
            state.message = "Candidate map build failed."
            state.next_action = "run_canonical_rebuild"
            _append_error(state, stage=current_stage, error="no_canonical_facts")
            state.finished_at = _now()
            save_cold_start_job(project_root, state)
            return
        save_cold_start_job(project_root, state)

        current_stage = "generating_diff_review"
        state = _update_job_state(
            project_root,
            job_id,
            cancel_requested,
            started_at,
            stage=current_stage,
            progress=90,
            message="Generating diff review.",
            next_action="review_candidate_map",
        )
        diff_base, base_map_source = resolve_map_diff_base(project_root, existing_formal_map=existing_formal_map)
        diff_review = build_map_diff_review(
            diff_base,
            candidate_result.map,
            candidate_source=candidate_result.candidate_source,
            base_map_source=base_map_source,
            warnings=candidate_result.warnings,
        )

        current_stage = "persisting_candidate_map"
        state = _update_job_state(
            project_root,
            job_id,
            cancel_requested,
            started_at,
            stage=current_stage,
            progress=95,
            message="Persisting source candidate map.",
            next_action="review_candidate_map",
        )
        candidate_result.diff_review = diff_review
        candidate_path = save_latest_source_candidate(project_root, candidate_result, job_id=job_id)

        state = _load_state_or_raise(project_root, job_id)
        _ensure_not_cancelled(state, cancel_requested)
        _ensure_not_timed_out(state, started_at)
        state.partial_outputs["candidate_map_path"] = str(candidate_path)
        state.partial_outputs["diff_review"] = diff_review.model_dump(mode="json")
        state.status = "succeeded"
        state.stage = "done"
        state.progress = 100
        state.message = "Cold-start job completed successfully."
        state.next_action = "review_candidate_map"
        state.finished_at = _now()
        save_cold_start_job(project_root, state)
    except _CancelledJobError:
        state = _load_state_or_raise(project_root, job_id)
        if state.status != "cancelled":
            state.status = "cancelled"
            state.stage = "cancelled"
            state.message = "Cold-start job cancelled."
            state.next_action = None
            state.finished_at = _now()
            save_cold_start_job(project_root, state)
    except _TimedOutJobError as exc:
        state = _load_state_or_raise(project_root, job_id)
        state.status = "failed"
        state.timed_out = True
        state.stage = current_stage
        state.message = "Cold-start job timed out."
        state.next_action = "retry_cold_start_job"
        _append_error(state, stage=current_stage, error=str(exc), source_path=state.current_file)
        state.finished_at = _now()
        save_cold_start_job(project_root, state)
    except Exception as exc:  # noqa: BLE001
        state = _load_state_or_raise(project_root, job_id)
        state.status = "failed"
        state.stage = current_stage
        state.message = "Cold-start job failed."
        state.next_action = state.next_action or "inspect_error"
        _append_error(state, stage=current_stage, error=str(exc), source_path=state.current_file)
        state.finished_at = _now()
        save_cold_start_job(project_root, state)
    finally:
        project_key = get_project_key(project_root)
        with _JOB_LOCK:
            handle = _ACTIVE_JOB_HANDLES.get(project_key)
            if handle is not None and handle.job_id == job_id:
                _ACTIVE_JOB_HANDLES.pop(project_key, None)