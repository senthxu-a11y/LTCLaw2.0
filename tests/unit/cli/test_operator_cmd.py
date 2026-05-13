import json

from click.testing import CliRunner

from ltclaw_gy_x.cli.main import cli
from ltclaw_gy_x.cli.operator_cmd import (
    RAG_API_KEY_ENV_VAR,
    build_project_config_payload,
    build_deepseek_preflight_report,
    build_secret_shape_report,
)


def test_secret_shape_report_contains_only_booleans():
    report = build_secret_shape_report("sk-test-secret-value-long-enough")

    assert report == {
        "exists": True,
        "length_gt_20": True,
        "starts_with_sk": True,
        "header_starts_with_bearer_sk": True,
        "header_length_gt_env_length": True,
    }
    assert all(isinstance(value, bool) for value in report.values())


def test_rag_secret_check_does_not_echo_secret_value(monkeypatch):
    monkeypatch.setenv(RAG_API_KEY_ENV_VAR, "sk-real-looking-secret-value")

    result = CliRunner().invoke(cli, ["operator", "rag-secret-check"])

    assert result.exit_code == 0
    assert "sk-real-looking-secret-value" not in result.output
    payload = json.loads(result.output)
    assert payload["exists"] is True
    assert payload["starts_with_sk"] is True


def test_rag_secret_check_can_fail_on_missing(monkeypatch):
    monkeypatch.delenv(RAG_API_KEY_ENV_VAR, raising=False)

    result = CliRunner().invoke(cli, ["operator", "rag-secret-check", "--fail-on-missing"])

    assert result.exit_code != 0
    assert "RAG provider secret shape check failed" in result.output
    assert RAG_API_KEY_ENV_VAR not in result.output


def test_deepseek_config_template_has_env_var_name_without_secret(monkeypatch):
    monkeypatch.setenv(RAG_API_KEY_ENV_VAR, "sk-real-looking-secret-value")

    result = CliRunner().invoke(cli, ["operator", "deepseek-config-template"])

    assert result.exit_code == 0
    assert "sk-real-looking-secret-value" not in result.output
    payload = json.loads(result.output)
    external = payload["external_provider_config"]
    assert external["provider_name"] == "future_external"
    assert external["model_name"] == "deepseek-chat"
    assert external["env"]["api_key_env_var"] == RAG_API_KEY_ENV_VAR
    assert "api_key" not in external
    assert "api_key" not in external["env"]


def test_deepseek_preflight_reports_paths_and_never_secret_value(tmp_path):
    secret = "sk-real-looking-secret-value"
    report = build_deepseek_preflight_report(
        env={
            RAG_API_KEY_ENV_VAR: secret,
            "QWENPAW_WORKING_DIR": str(tmp_path),
            "QWENPAW_CONSOLE_STATIC_DIR": str(tmp_path),
        },
    )

    dumped = json.dumps(report)
    assert secret not in dumped
    assert report["secret"]["exists"] is True
    assert report["paths"]["QWENPAW_WORKING_DIR"]["exists"] is True
    assert report["paths"]["QWENPAW_CONSOLE_STATIC_DIR"]["exists"] is True
    assert report["provider_config"]["api_key_env_var"] == RAG_API_KEY_ENV_VAR
    assert report["provider_config"]["contains_secret_value"] is False


def test_build_project_config_payload_preserves_full_config_shape():
    current_config = {
        "schema_version": "project-config.v1",
        "project": {"name": "Windows Operator Validation"},
        "svn": {"root": "E:/example"},
        "external_provider_config": None,
    }

    payload = build_project_config_payload(current_config, mode="apply")

    assert payload["project"] == current_config["project"]
    assert payload["svn"] == current_config["svn"]
    assert payload["external_provider_config"]["provider_name"] == "future_external"
    assert payload["external_provider_config"]["model_name"] == "deepseek-chat"
    assert payload["external_provider_config"]["env"]["api_key_env_var"] == RAG_API_KEY_ENV_VAR
    assert "api_key" not in payload["external_provider_config"]


def test_build_project_config_payload_cleanup_restores_null():
    current_config = {
        "project": {"name": "Windows Operator Validation"},
        "svn": {"root": "E:/example"},
        "external_provider_config": {"enabled": True},
    }

    payload = build_project_config_payload(current_config, mode="cleanup")

    assert payload["external_provider_config"] is None
    assert payload["project"] == current_config["project"]
    assert payload["svn"] == current_config["svn"]


def test_deepseek_project_config_payload_cli_merges_input_without_secret(tmp_path):
    input_file = tmp_path / "project_config.json"
    input_file.write_text(
        json.dumps(
            {
                "schema_version": "project-config.v1",
                "project": {"name": "Windows Operator Validation"},
                "svn": {"root": "E:/example"},
                "external_provider_config": None,
            }
        ),
        encoding="utf-8",
    )

    result = CliRunner().invoke(
        cli,
        [
            "operator",
            "deepseek-project-config-payload",
            "--mode",
            "disable",
            "--input-file",
            str(input_file),
        ],
    )

    assert result.exit_code == 0
    payload = json.loads(result.output)
    external = payload["external_provider_config"]
    assert external["transport_enabled"] is False
    assert external["env"]["api_key_env_var"] == RAG_API_KEY_ENV_VAR
    assert "api_key" not in external
