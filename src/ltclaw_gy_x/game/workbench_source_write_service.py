from __future__ import annotations

import json
from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from pydantic import BaseModel, Field

from ..app.agent_context import get_current_session_id
from .change_applier import ApplyError, ChangeApplier
from .change_proposal import ChangeOp, ChangeProposal
from .knowledge_release_store import (
    CurrentKnowledgeReleaseNotSetError,
    KnowledgeReleaseNotFoundError,
    get_current_release,
)
from .paths import get_workspace_game_dir


class WorkbenchSourceWriteOp(BaseModel):
    op: str
    table: str
    row_id: str | int
    field: str | None = None
    new_value: Any = None
    old_value: Any | None = None


@dataclass
class WorkbenchSourceWriteOutcome:
    ok: bool
    status_code: int
    payload: dict[str, Any]


class _AuditWriteFailure(Exception):
    pass


class WorkbenchSourceWriteService:
    SUPPORTED_WRITE_SUFFIXES = {".csv", ".xlsx", ".txt"}
    SVN_UPDATE_WARNING = (
        "Before source write, manually run SVN Update in your working copy. "
        "The server does not run SVN update, commit, or revert for you."
    )

    def __init__(
        self,
        *,
        change_applier: ChangeApplier,
        workspace_dir: Path,
        agent_id: str,
        session_id: str | None = None,
    ) -> None:
        self.change_applier = change_applier
        self.workspace_dir = Path(workspace_dir)
        self.agent_id = agent_id or ""
        self.session_id = session_id or get_current_session_id() or ""

    async def write(
        self,
        *,
        ops: list[WorkbenchSourceWriteOp],
        reason: str | None = None,
    ) -> WorkbenchSourceWriteOutcome:
        reason_text = (reason or "").strip() or "workbench_source_write"
        audit_context = self._base_audit_payload(reason_text)
        applied_source_files: list[str] = []
        applied_changes: list[dict[str, Any]] = []
        try:
            if not ops:
                raise ValueError("No source write operations were provided")

            preview_records, source_files = await self._prepare_preview_records(ops)
            proposal = ChangeProposal(
                title="__workbench_source_write__",
                description=reason_text,
                ops=[
                    ChangeOp(
                        op=record["op"].op,
                        table=record["op"].table,
                        row_id=record["op"].row_id,
                        field=record["op"].field,
                        old_value=record["op"].old_value,
                        new_value=record["op"].new_value,
                    )
                    for record in preview_records
                ],
                status="approved",
            )
            apply_result = await self.change_applier.apply(proposal)
            applied_source_files = apply_result["changed_files"]
            applied_changes = [record["change"] for record in preview_records]
            payload = {
                "success": True,
                "message": "Source write completed. Rebuild, release, and publish are not triggered automatically.",
                "svn_update_required": True,
                "svn_update_warning": self.SVN_UPDATE_WARNING,
                "release_id_at_write": audit_context["release_id_at_write"],
                "source_files": applied_source_files,
                "changes": applied_changes,
                "audit_recorded": False,
                "audit_file": self._audit_path().as_posix(),
                "summary": apply_result["summary"],
            }
            audit_payload = {
                **audit_context,
                "success": True,
                "failure": None,
                "source_files": applied_source_files,
                "changes": payload["changes"],
            }
            audit_recorded = self._append_audit_record(audit_payload)
            if not audit_recorded:
                raise _AuditWriteFailure
            payload["audit_recorded"] = True
            return WorkbenchSourceWriteOutcome(ok=True, status_code=200, payload=payload)
        except _AuditWriteFailure:
            return WorkbenchSourceWriteOutcome(
                ok=False,
                status_code=500,
                payload={
                    "message": "source write applied but audit failed",
                    "audit_recorded": False,
                    "write_applied": True,
                    "svn_update_required": True,
                    "svn_update_warning": self.SVN_UPDATE_WARNING,
                    "release_id_at_write": audit_context["release_id_at_write"],
                    "source_files": applied_source_files,
                    "changes": applied_changes,
                },
            )
        except Exception as exc:  # noqa: BLE001
            failure_payload = self._build_failure_payload(exc, audit_context)
            failure_payload["audit_recorded"] = self._append_audit_record(
                {
                    **audit_context,
                    "success": False,
                    "failure": failure_payload["message"],
                    "source_files": failure_payload.get("source_files", []),
                    "changes": failure_payload.get("changes", []),
                }
            )
            return WorkbenchSourceWriteOutcome(
                ok=False,
                status_code=failure_payload.pop("status_code", 400),
                payload=failure_payload,
            )

    async def _prepare_preview_records(
        self,
        ops: list[WorkbenchSourceWriteOp],
    ) -> tuple[list[dict[str, Any]], list[str]]:
        source_files = self._resolve_source_files(ops)
        validated_ops: list[WorkbenchSourceWriteOp] = []
        for op in ops:
            self._validate_op(op)
            validated_ops.append(op)

        preview = await self.change_applier.dry_run(
            ChangeProposal(
                title="__workbench_source_write_preview__",
                description="",
                ops=[
                    ChangeOp(
                        op=op.op, table=op.table, row_id=op.row_id, field=op.field, new_value=op.new_value
                    )
                    for op in validated_ops
                ],
                status="approved",
            )
        )
        preview_buckets: dict[tuple[str, str, str, str], list[dict[str, Any]]] = {}
        for item in preview:
            key = self._preview_key(item)
            preview_buckets.setdefault(key, []).append(item)

        preview_records: list[dict[str, Any]] = []
        for op, source_file in zip(validated_ops, source_files):
            key = (op.op, op.table, str(op.row_id), str(op.field or ""))
            matches = preview_buckets.get(key, [])
            preview_item = matches.pop(0) if matches else None
            if preview_item is None:
                raise ValueError("Missing dry-run result for source write operation")
            if not preview_item.get("ok"):
                raise ValueError(str(preview_item.get("reason") or "source write validation failed"))
            preview_records.append(
                {
                    "op": op,
                    "source_file": source_file,
                    "change": {
                        "op": op.op,
                        "table": op.table,
                        "row_id": op.row_id,
                        "field": op.field,
                        "old_value": preview_item.get("before"),
                        "new_value": preview_item.get("after", op.new_value),
                    },
                }
            )
        return preview_records, source_files

    def _resolve_source_files(self, ops: list[WorkbenchSourceWriteOp]) -> list[str]:
        resolved: list[str] = []
        for op in ops:
            try:
                source = self.change_applier.get_source_file(op.table)
            except ApplyError as exc:
                raise ValueError(exc.reason) from exc
            suffix = source.suffix.lower()
            if suffix == ".xls":
                raise ValueError("Workbench source write does not support .xls source tables. Use .csv, .xlsx, or .txt.")
            if suffix not in self.SUPPORTED_WRITE_SUFFIXES:
                raise ValueError("Workbench source write only supports .csv, .xlsx, and .txt source tables.")
            resolved.append(self._relative_source(source))
        return resolved

    def _validate_op(self, op: WorkbenchSourceWriteOp) -> None:
        if op.op == "delete_row":
            raise ValueError("delete_row is blocked in workbench source write")
        if op.op not in {"update_cell", "insert_row"}:
            raise ValueError(f"Schema and unsupported ops are blocked in workbench source write: {op.op}")

        table_rows = self.change_applier.read_rows(op.table, offset=0, limit=1)
        headers = [str(header or "") for header in table_rows.get("headers", [])]
        if not headers:
            raise ValueError(f"Table headers are unavailable for source table: {op.table}")
        primary_key = self.change_applier.project.table_convention.resolve_primary_key(
            table_name=op.table,
            headers=headers,
        )
        header_map = {header: index for index, header in enumerate(headers) if header}
        header_map_ci = {header.lower(): index for index, header in enumerate(headers) if header}

        def _has_field(name: str) -> bool:
            return name in header_map or name.lower() in header_map_ci

        if op.op == "update_cell":
            if not op.field:
                raise ValueError("update_cell requires a target field")
            if not _has_field(op.field):
                raise ValueError(f"Updating unknown fields is blocked in workbench source write: {op.field}")
            if op.field.lower() == primary_key.lower():
                raise ValueError("Changing the primary key is blocked in workbench source write")
            return

        if not isinstance(op.new_value, dict):
            raise ValueError("insert_row requires new_value to be an object")
        for field_name in op.new_value.keys():
            if not _has_field(str(field_name)):
                raise ValueError(f"Adding new fields is blocked in workbench source write: {field_name}")
        pk_value = op.new_value.get(primary_key)
        if pk_value is not None and str(pk_value) != str(op.row_id):
            raise ValueError("Changing the primary key is blocked in workbench source write")

    def _base_audit_payload(self, reason: str) -> dict[str, Any]:
        return {
            "event_type": "workbench.source.write",
            "agent_id": self.agent_id,
            "session_id": self.session_id,
            "time": datetime.now(UTC).isoformat(),
            "release_id_at_write": self._current_release_id(),
            "reason": reason,
        }

    def _build_failure_payload(
        self,
        exc: Exception,
        audit_context: dict[str, Any],
    ) -> dict[str, Any]:
        message = str(exc) or exc.__class__.__name__
        status_code = 500 if isinstance(exc, OSError) else 400
        if isinstance(exc, ApplyError):
            status_code = 400
        return {
            "status_code": status_code,
            "message": message,
            "svn_update_required": True,
            "svn_update_warning": self.SVN_UPDATE_WARNING,
            "release_id_at_write": audit_context["release_id_at_write"],
            "source_files": [],
            "changes": [],
            "write_applied": False,
        }

    def _append_audit_record(self, payload: dict[str, Any]) -> bool:
        try:
            audit_path = self._audit_path()
            line = json.dumps(payload, ensure_ascii=False) + "\n"
            audit_path.parent.mkdir(parents=True, exist_ok=True)
            with audit_path.open("a", encoding="utf-8") as handle:
                handle.write(line)
            return True
        except Exception:  # noqa: BLE001
            return False

    def _audit_path(self) -> Path:
        return (
            get_workspace_game_dir(
                self.workspace_dir,
                self.change_applier.svn_root,
                self.session_id or None,
            )
            / "audit"
            / "workbench_source_write.jsonl"
        )

    def _current_release_id(self) -> str | None:
        try:
            return get_current_release(self.change_applier.svn_root).release_id
        except (CurrentKnowledgeReleaseNotSetError, KnowledgeReleaseNotFoundError, FileNotFoundError, OSError, ValueError):
            return None

    def _relative_source(self, source: Path) -> str:
        try:
            return str(source.relative_to(self.change_applier.svn_root)).replace("\\", "/")
        except ValueError:
            return str(source)

    def _preview_key(self, preview_item: dict[str, Any]) -> tuple[str, str, str, str]:
        raw = preview_item.get("op", {}) or {}
        return (
            str(raw.get("op", "")),
            str(raw.get("table", "")),
            str(raw.get("row_id", "")),
            "" if raw.get("field") is None else str(raw.get("field", "")),
        )
