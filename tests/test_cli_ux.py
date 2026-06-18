from __future__ import annotations

from pathlib import Path

from commerce_safety.cli import (
    build_parser,
    build_saas001_agent_demo,
    build_scn002_agent_demo,
    install_mcp_config,
    mcp_config_payload,
    merge_mcp_config,
)


def test_mcp_config_payload_uses_absolute_package_path() -> None:
    repo_root = Path("/tmp/commerce-safety-demo")
    config = mcp_config_payload(
        repo_root=repo_root,
        python_path="/tmp/commerce-safety-demo/.venv/bin/python",
        runs_dir="runs",
        transport="stdio",
    )

    server = config["mcpServers"]["commerce-safety"]
    assert server["command"] == "/tmp/commerce-safety-demo/.venv/bin/python"
    assert server["args"] == [
        "-m",
        "commerce_safety.live.mcp_server",
        "--runs-dir",
        "runs",
    ]
    assert server["env"]["PYTHONPATH"] == str(repo_root / "commerce-safety-sandbox")


def test_mcp_config_payload_includes_non_stdio_transport() -> None:
    config = mcp_config_payload(
        repo_root=Path("/tmp/repo"),
        python_path="/tmp/repo/.venv/bin/python",
        runs_dir="runs/demo",
        transport="streamable-http",
    )

    assert config["mcpServers"]["commerce-safety"]["args"] == [
        "-m",
        "commerce_safety.live.mcp_server",
        "--runs-dir",
        "runs/demo",
        "--transport",
        "streamable-http",
    ]


def test_runs_dir_can_be_passed_after_nested_live_mcp_command() -> None:
    parser = build_parser()
    args = parser.parse_args(["live", "mcp", "--runs-dir", "runs/test"])

    assert args.runs_dir == "runs/test"


def test_runs_dir_can_be_passed_after_run_command() -> None:
    parser = build_parser()
    args = parser.parse_args(
        [
            "run",
            "commerce-safety-sandbox/scenarios/duplicate_webhook.yaml",
            "--runner",
            "bad_runner",
            "--runs-dir",
            "runs/test",
        ]
    )

    assert args.runs_dir == "runs/test"


def test_scn002_agent_demo_contains_config_prompt_and_checklist() -> None:
    demo = build_scn002_agent_demo(
        repo_root=Path("/tmp/commerce-safety-demo"),
        python_path="/tmp/commerce-safety-demo/.venv/bin/python",
        runs_dir="runs",
    )

    assert "commerce-safety mcp-config" in demo
    assert "demo_pack/prompts/scn002_mcp_agent_test.md" in demo
    assert "idempotency_required_for_mutating_retries" in demo
    assert "no_duplicate_fulfillment" in demo
    assert "Unsafe run fails" in demo
    assert "Safe run passes" in demo


def test_saas001_agent_demo_contains_stripe_slack_github_checklist() -> None:
    demo = build_saas001_agent_demo(
        repo_root=Path("/tmp/commerce-safety-demo"),
        python_path="/tmp/commerce-safety-demo/.venv/bin/python",
        runs_dir="runs",
    )

    assert "SAAS-001" in demo
    assert "demo_pack/prompts/saas001_mcp_agent_test.md" in demo
    assert "demo_pack/saas_agent_validation/http_curl_bad_good.md" in demo
    assert "no_success_state_after_failed_payment" in demo
    assert "slack_permission_failure_must_not_be_silent" in demo
    assert "No production Stripe keys" in demo


def test_demo_scn002_agent_command_parses() -> None:
    parser = build_parser()
    args = parser.parse_args(["demo", "scn002-agent", "--runs-dir", "runs/test"])

    assert args.demo_command == "scn002-agent"
    assert args.runs_dir == "runs/test"


def test_demo_saas001_agent_command_parses() -> None:
    parser = build_parser()
    args = parser.parse_args(["demo", "saas001-agent", "--runs-dir", "runs/test"])

    assert args.demo_command == "saas001-agent"
    assert args.runs_dir == "runs/test"


def test_mcp_config_install_merges_with_existing_servers(tmp_path: Path) -> None:
    config_path = tmp_path / "mcp.json"
    config_path.write_text(
        '{"mcpServers": {"existing": {"command": "node", "args": ["server.js"]}}}',
        encoding="utf-8",
    )
    commerce_config = mcp_config_payload(
        repo_root=Path("/tmp/repo"),
        python_path="/tmp/repo/.venv/bin/python",
        runs_dir="runs",
        transport="stdio",
    )

    installed = install_mcp_config(commerce_config, config_path=config_path)

    assert installed["mcpServers"]["existing"]["command"] == "node"
    assert installed["mcpServers"]["commerce-safety"]["command"] == (
        "/tmp/repo/.venv/bin/python"
    )
    assert config_path.with_name("mcp.json.backup").exists()


def test_merge_mcp_config_rejects_non_object_existing_config() -> None:
    commerce_config = mcp_config_payload(
        repo_root=Path("/tmp/repo"),
        python_path="/tmp/repo/.venv/bin/python",
        runs_dir="runs",
        transport="stdio",
    )

    try:
        merge_mcp_config([], commerce_config)  # type: ignore[arg-type]
    except ValueError as error:
        assert "MCP config must be a JSON object" in str(error)
    else:
        raise AssertionError("Expected ValueError for non-object MCP config")


def test_init_and_wizard_commands_accept_path_selection() -> None:
    parser = build_parser()

    init_args = parser.parse_args(["init", "--path", "n8n"])
    wizard_args = parser.parse_args(["wizard", "--path", "http-workflow"])
    saas_args = parser.parse_args(["init", "--path", "saas-mcp-agent"])

    assert init_args.path == "n8n"
    assert wizard_args.path == "http-workflow"
    assert saas_args.path == "saas-mcp-agent"
