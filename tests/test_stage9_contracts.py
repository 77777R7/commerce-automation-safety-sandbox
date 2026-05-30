from __future__ import annotations

from pathlib import Path

import yaml


ROOT = Path(__file__).resolve().parents[1]


def test_stage9_mcp_server_declares_exact_core_tools():
    from commerce_safety.live.mcp_server import CORE_MCP_TOOL_NAMES

    assert CORE_MCP_TOOL_NAMES == [
        "commerce.start_session",
        "commerce.get_task",
        "commerce.create_fulfillment",
        "commerce.find_fulfillment",
        "commerce.complete_session",
        "commerce.get_trace",
        "commerce.get_policy_report",
        "commerce.get_patch_hints",
    ]


def test_stage9_openapi_spec_covers_live_http_vertical_slice():
    spec_path = ROOT / "docs" / "openapi" / "live_twin_api.yaml"

    spec = yaml.safe_load(spec_path.read_text(encoding="utf-8"))

    assert spec["openapi"].startswith("3.")
    assert spec["info"]["title"] == "Commerce Safety Live Twin API"
    assert "/sessions" in spec["paths"]
    assert "/sessions/{session_id}/tasks/next" in spec["paths"]
    assert "/sessions/{session_id}/twin/create_fulfillment" in spec["paths"]
    assert "/sessions/{session_id}/trace" in spec["paths"]
    assert "/sessions/{session_id}/complete" in spec["paths"]


def test_stage9_docs_and_smoke_gates_exist():
    required_paths = [
        ROOT / "docs" / "MCP_SERVER_SETUP.md",
        ROOT / "tools" / "smoke_stage9_real_mcp.sh",
        ROOT / "tools" / "smoke_stage9_api_hardening.sh",
    ]

    for path in required_paths:
        assert path.exists(), f"missing Stage 9 artifact: {path}"


def test_stage9_mcp_setup_doc_keeps_scope_narrow():
    doc = (ROOT / "docs" / "MCP_SERVER_SETUP.md").read_text(encoding="utf-8")

    assert "modelcontextprotocol/python-sdk" in doc
    assert "Python 3.10+" in doc
    assert "Permissive Twin + Policy Check" in doc
    assert "Sandbox0" in doc
    assert "Firecracker" in doc
