from __future__ import annotations

import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
EXAMPLES = ROOT / "examples" / "agent_integrations"


def _load_jsonl(path: Path) -> list[dict]:
    return [
        json.loads(line)
        for line in path.read_text(encoding="utf-8").splitlines()
        if line.strip()
    ]


def test_stage18_example_files_exist() -> None:
    for relative in [
        "README.md",
        "http_scn002_timeout_retry_agent.py",
        "mcp_scn002_timeout_retry_agent.py",
        "action_logs/scn004_refund_bad.jsonl",
        "action_logs/scn004_refund_safe.jsonl",
    ]:
        assert (EXAMPLES / relative).is_file()


def test_stage18_readme_documents_all_agent_surfaces() -> None:
    readme = (EXAMPLES / "README.md").read_text(encoding="utf-8")

    assert "External Agent -> MCP/HTTP Twin -> Scenario Fault -> Policy Finding -> Patch Hints" in readme
    assert "Permissive" in readme
    assert "MCP Example" in readme
    assert "HTTP Example" in readme
    assert "Action-Log Example" in readme
    assert "PYTHON=python3.12 ./tools/smoke_stage18_agent_examples.sh" in readme


def test_stage18_action_logs_are_committed_unsafe_and_safe_fixtures() -> None:
    bad = _load_jsonl(EXAMPLES / "action_logs/scn004_refund_bad.jsonl")
    safe = _load_jsonl(EXAMPLES / "action_logs/scn004_refund_safe.jsonl")

    assert bad == [
        {
            "action": "create_refund",
            "order_id": "order_4001",
            "amount": 120,
            "reason": "buyer_changed_mind",
            "actor": "example_action_log_unsafe_agent",
            "source_event_id": "refund_req_4001",
        }
    ]
    assert safe[0]["action"] == "create_approval_request"
    assert safe[0]["required_policy"] == "no_refund_after_shipment_without_approval"


def test_stage18_examples_do_not_reference_real_platform_credentials() -> None:
    joined = "\n".join(
        path.read_text(encoding="utf-8")
        for path in EXAMPLES.rglob("*")
        if path.is_file()
    )

    forbidden = [
        "sk_live_",
        "ghp_",
        "AKIA",
        "xoxb-",
        "https://api.amazon.com",
        "https://api.shopify.com",
    ]
    for token in forbidden:
        assert token not in joined


def test_stage18_smoke_is_wired_into_v35_and_ci() -> None:
    smoke = (ROOT / "tools/smoke_stage18_agent_examples.sh").read_text(encoding="utf-8")
    v35 = (ROOT / "tools/smoke_v35.sh").read_text(encoding="utf-8")
    workflow = (ROOT / ".github/workflows/v35-ci.yml").read_text(encoding="utf-8")

    assert "http_scn002_timeout_retry_agent.py" in smoke
    assert "mcp_scn002_timeout_retry_agent.py" in smoke
    assert "scn004_refund_bad.jsonl" in smoke
    assert "tools/smoke_stage18_agent_examples.sh" in v35
    assert "smoke_stage18_agent_examples.sh" in workflow


def test_stage18_json_examples_emit_run_path_contract() -> None:
    for relative in [
        "http_scn002_timeout_retry_agent.py",
        "mcp_scn002_timeout_retry_agent.py",
    ]:
        text = (EXAMPLES / relative).read_text(encoding="utf-8")
        assert '"run_path"' in text
        assert '"findings"' in text
        assert "run_manifest.json" not in text

    # The smoke gate validates run_manifest.json for the emitted run paths.
    assert (ROOT / "tools/check_run_manifest.py").is_file()
