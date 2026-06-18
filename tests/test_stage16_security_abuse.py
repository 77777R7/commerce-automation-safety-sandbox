from __future__ import annotations

from io import BytesIO
import importlib.util
from pathlib import Path

import yaml

from commerce_safety.live.action_log import load_action_log
from commerce_safety.live.errors import LiveHTTPError
from commerce_safety.live.http_api import (
    LiveAPI,
    read_json_object_from_stream,
    security_headers,
)
from commerce_safety.live.mcp_tools import CommerceMCPTools
from commerce_safety.live.security import (
    LiveSecurityError,
    validate_live_server_security,
)


ROOT = Path(__file__).resolve().parents[1]
CHECKER_PATH = ROOT / "tools/check_security_hardening.py"


def _request(
    api: LiveAPI,
    method: str,
    path: str,
    payload: dict | None = None,
    headers: dict | None = None,
):
    return api.handle(method, path, payload or {}, headers=headers or {})


def _load_checker():
    spec = importlib.util.spec_from_file_location("check_security_hardening", CHECKER_PATH)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_public_http_bind_requires_token() -> None:
    validate_live_server_security("127.0.0.1", None)
    validate_live_server_security("localhost", None)
    validate_live_server_security("0.0.0.0", "local-dev-token")

    try:
        validate_live_server_security("0.0.0.0", None)
    except LiveSecurityError as error:
        assert "api token" in str(error)
    else:
        raise AssertionError("public bind without token should be rejected")


def test_http_auth_uses_constant_time_token_path(tmp_path: Path) -> None:
    api = LiveAPI(runs_dir=tmp_path, api_token="stage16-secret-token")

    status, rejected = _request(
        api,
        "POST",
        "/sessions",
        {"scenario_id": "SCN-002"},
        headers={"Authorization": "Bearer wrong-token"},
    )
    assert status == 401
    assert rejected["error"]["code"] == "unauthorized"

    status, created = _request(
        api,
        "POST",
        "/sessions",
        {"scenario_id": "SCN-002"},
        headers={"Authorization": "Bearer stage16-secret-token"},
    )
    assert status == 201
    assert created["scenario_id"] == "SCN-002"


def test_http_json_body_has_size_limit() -> None:
    payload = b'{"ok": true}'
    assert read_json_object_from_stream(BytesIO(payload), len(payload), max_bytes=64) == {
        "ok": True
    }

    too_large = b'{"blob": "' + (b"x" * 128) + b'"}'
    try:
        read_json_object_from_stream(BytesIO(too_large), len(too_large), max_bytes=32)
    except LiveHTTPError as error:
        assert error.status_code == 413
        assert error.code == "request_body_too_large"
    else:
        raise AssertionError("oversized JSON body should be rejected")


def test_http_security_headers_are_no_store_and_no_sniff() -> None:
    headers = security_headers()

    assert headers["X-Content-Type-Options"] == "nosniff"
    assert headers["Cache-Control"] == "no-store"
    assert "Access-Control-Allow-Origin" not in headers


def test_scenario_registry_does_not_leak_local_paths(tmp_path: Path) -> None:
    api = LiveAPI(runs_dir=tmp_path)
    outside = tmp_path / "outside.yaml"
    outside.write_text(
        Path("commerce-safety-sandbox/scenarios/SCN-002_timeout_after_commit_retry.yaml").read_text(
            encoding="utf-8"
        ),
        encoding="utf-8",
    )

    status, rejected = _request(
        api,
        "POST",
        "/sessions",
        {"scenario_path": str(outside)},
    )

    assert status == 400
    assert rejected["error"]["code"] == "scenario_not_allowed"
    message = rejected["error"]["message"]
    assert "/Users/" not in message
    assert str(tmp_path) not in message


def test_action_log_has_abuse_limits(tmp_path: Path) -> None:
    log = tmp_path / "too_many.jsonl"
    log.write_text(
        "\n".join('{"action": "create_refund"}' for _ in range(4)) + "\n",
        encoding="utf-8",
    )

    try:
        load_action_log(log, max_actions=3)
    except ValueError as error:
        assert "too many actions" in str(error)
    else:
        raise AssertionError("oversized action log should be rejected")


def test_stage16_security_artifacts_and_ci_wiring_exist() -> None:
    doc = ROOT / "docs/STAGE16_SECURITY_ABUSE_HARDENING.md"
    config = ROOT / "security_hardening.yaml"
    smoke = ROOT / "tools/smoke_stage16_security_abuse.sh"
    checker = ROOT / "tools/check_security_hardening.py"
    ci = ROOT / ".github/workflows/v35-ci.yml"

    assert doc.exists()
    assert config.exists()
    assert smoke.exists()
    assert checker.exists()

    config_body = yaml.safe_load(config.read_text(encoding="utf-8"))
    assert config_body["source_scan"]["repo_wide"] is True
    assert "secret_patterns" in config_body
    assert "banned_response_fragments" in config_body

    ci_text = ci.read_text(encoding="utf-8")
    assert "tools/smoke_stage16_security_abuse.sh" in ci_text


def test_security_checker_detects_high_confidence_secret(tmp_path: Path) -> None:
    checker = _load_checker()
    config = checker.load_config(ROOT / "security_hardening.yaml")
    source_file = tmp_path / "app.py"
    fake_secret = "sk_live_" + "1234567890abcdefghijklmnop"
    source_file.write_text(f'token = "{fake_secret}"\n', encoding="utf-8")

    findings = checker.scan_file_patterns(
        tmp_path,
        ["app.py"],
        config["secret_patterns"],
        code="secret_pattern_detected",
    )

    assert findings
    assert findings[0]["code"] == "secret_pattern_detected"
    assert findings[0]["id"] == "stripe_live_secret_key"


def test_mcp_scenario_path_errors_do_not_leak_local_paths(tmp_path: Path) -> None:
    outside = tmp_path / "outside.yaml"
    outside.write_text(
        Path("commerce-safety-sandbox/scenarios/SCN-002_timeout_after_commit_retry.yaml").read_text(
            encoding="utf-8"
        ),
        encoding="utf-8",
    )
    tools = CommerceMCPTools(runs_dir=tmp_path / "runs")

    try:
        tools.call_tool(
            "commerce.start_session",
            {"scenario_path": str(outside)},
        )
    except Exception as error:
        message = str(error)
    else:
        raise AssertionError("MCP start_session should reject non-allowlisted paths")

    assert "/Users/" not in message
    assert str(tmp_path) not in message
    assert "allowlisted scenario" in message


def test_mcp_streamable_http_transport_disablement_is_source_scanned() -> None:
    config_body = yaml.safe_load((ROOT / "security_hardening.yaml").read_text(encoding="utf-8"))
    requirements = {
        item["path"]: item.get("snippets", [])
        for item in config_body["required_source_snippets"]
    }

    assert "commerce-safety-sandbox/commerce_safety/live/mcp_server.py" in requirements
    assert "streamable-http transport is disabled" in requirements[
        "commerce-safety-sandbox/commerce_safety/live/mcp_server.py"
    ]
