# -*- coding: utf-8 -*-
from __future__ import annotations

import json
import os
import copy
from pathlib import Path
from typing import Any

import click


RAG_API_KEY_ENV_VAR = "LTCLAW_RAG_API_KEY"
DEEPSEEK_PROVIDER_CONFIG: dict[str, Any] = {
    "external_provider_config": {
        "enabled": True,
        "transport_enabled": True,
        "provider_name": "future_external",
        "model_name": "deepseek-chat",
        "allowed_providers": ["future_external"],
        "allowed_models": ["deepseek-chat"],
        "base_url": "https://api.deepseek.com/chat/completions",
        "env": {
            "api_key_env_var": RAG_API_KEY_ENV_VAR,
        },
    },
}

PROJECT_CONFIG_UPDATE_MODES = ("apply", "disable", "cleanup")


def build_secret_shape_report(value: str | None) -> dict[str, bool]:
    normalized = (value or "").strip()
    header = f"Bearer {normalized}"
    return {
        "exists": bool(normalized),
        "length_gt_20": len(normalized) > 20,
        "starts_with_sk": normalized.startswith("sk"),
        "header_starts_with_bearer_sk": header.startswith("Bearer sk"),
        "header_length_gt_env_length": len(header) > len(normalized),
    }


def build_project_config_payload(
    current_config: dict[str, Any],
    *,
    mode: str,
) -> dict[str, Any]:
    if mode not in PROJECT_CONFIG_UPDATE_MODES:
        raise ValueError(f"Unsupported project config update mode: {mode}")

    payload = copy.deepcopy(current_config)
    external_provider_config: dict[str, Any] | None
    if mode == "cleanup":
        external_provider_config = None
    else:
        external_provider_config = copy.deepcopy(
            DEEPSEEK_PROVIDER_CONFIG["external_provider_config"]
        )
        if mode == "disable":
            external_provider_config["transport_enabled"] = False

    payload["external_provider_config"] = external_provider_config
    return payload


def _secret_shape_ok(report: dict[str, bool]) -> bool:
    return all(report.values())


def _path_exists(value: str | None) -> bool:
    if not value:
        return False
    return Path(value).expanduser().exists()


def build_deepseek_preflight_report(
    *,
    env: dict[str, str] | None = None,
    working_dir_env_var: str = "QWENPAW_WORKING_DIR",
    console_static_env_var: str = "QWENPAW_CONSOLE_STATIC_DIR",
) -> dict[str, Any]:
    source = env if env is not None else os.environ
    secret_report = build_secret_shape_report(source.get(RAG_API_KEY_ENV_VAR))
    working_dir = source.get(working_dir_env_var)
    console_static_dir = source.get(console_static_env_var)
    provider_config = DEEPSEEK_PROVIDER_CONFIG["external_provider_config"]
    return {
        "secret": secret_report,
        "paths": {
            working_dir_env_var: {
                "set": bool((working_dir or "").strip()),
                "exists": _path_exists(working_dir),
            },
            console_static_env_var: {
                "set": bool((console_static_dir or "").strip()),
                "exists": _path_exists(console_static_dir),
            },
        },
        "provider_config": {
            "enabled": provider_config["enabled"] is True,
            "transport_enabled": provider_config["transport_enabled"] is True,
            "provider_name": provider_config["provider_name"],
            "model_name": provider_config["model_name"],
            "base_url": provider_config["base_url"],
            "api_key_env_var": provider_config["env"]["api_key_env_var"],
            "contains_secret_value": False,
        },
    }


def _preflight_ok(report: dict[str, Any]) -> bool:
    paths = report.get("paths", {})
    path_ok = all(
        bool(item.get("set")) and bool(item.get("exists"))
        for item in paths.values()
        if isinstance(item, dict)
    )
    return _secret_shape_ok(report.get("secret", {})) and path_ok


def _echo_json(payload: dict[str, Any]) -> None:
    click.echo(json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True))


def _load_project_config_payload(input_file: str | None) -> dict[str, Any]:
    if input_file:
        raw = Path(input_file).read_text(encoding="utf-8")
    else:
        raw = click.get_text_stream("stdin").read()

    if not raw.strip():
        raise click.ClickException(
            "Current project config JSON is required via --input-file or stdin."
        )

    try:
        payload = json.loads(raw)
    except json.JSONDecodeError as exc:
        raise click.ClickException(f"Invalid JSON input: {exc}") from exc

    if not isinstance(payload, dict):
        raise click.ClickException("Current project config input must be a JSON object.")

    return payload


@click.group("operator")
def operator_cmd() -> None:
    """Operator-only startup and controlled-pilot utilities."""


@operator_cmd.command("rag-secret-check")
@click.option(
    "--env-var",
    default=RAG_API_KEY_ENV_VAR,
    show_default=True,
    help="Environment variable to inspect without printing its value.",
)
@click.option(
    "--fail-on-missing",
    is_flag=True,
    help="Exit non-zero unless all secret shape checks pass.",
)
def rag_secret_check(env_var: str, fail_on_missing: bool) -> None:
    """Print only boolean shape checks for the RAG provider secret."""
    report = build_secret_shape_report(os.environ.get(env_var))
    _echo_json(report)
    if fail_on_missing and not _secret_shape_ok(report):
        raise click.ClickException("RAG provider secret shape check failed.")


@operator_cmd.command("deepseek-config-template")
def deepseek_config_template() -> None:
    """Print the backend-owned DeepSeek provider config without secrets."""
    _echo_json(DEEPSEEK_PROVIDER_CONFIG)


@operator_cmd.command("deepseek-project-config-payload")
@click.option(
    "--mode",
    type=click.Choice(PROJECT_CONFIG_UPDATE_MODES, case_sensitive=False),
    required=True,
    help="How to update external_provider_config inside the current project config.",
)
@click.option(
    "--input-file",
    type=click.Path(exists=True, dir_okay=False, path_type=Path),
    help="Path to the current full project-config JSON read from GET project/config.",
)
def deepseek_project_config_payload(mode: str, input_file: Path | None) -> None:
    """Merge DeepSeek operator config into a full project-config JSON payload."""
    current_config = _load_project_config_payload(str(input_file) if input_file else None)
    payload = build_project_config_payload(current_config, mode=mode.lower())
    _echo_json(payload)


@operator_cmd.command("deepseek-preflight")
@click.option(
    "--fail-on-missing",
    is_flag=True,
    help="Exit non-zero unless secret and required startup paths are ready.",
)
def deepseek_preflight(fail_on_missing: bool) -> None:
    """Check controlled DeepSeek pilot startup inputs without echoing secrets."""
    report = build_deepseek_preflight_report()
    _echo_json(report)
    if fail_on_missing and not _preflight_ok(report):
        raise click.ClickException("DeepSeek controlled-pilot preflight failed.")
