from __future__ import annotations

from pathlib import Path


def test_stage7_live_agent_validation_demo_pack_exists():
    root = Path("demo_pack/live_agent_validation")
    docs = [
        Path("docs/LIVE_AGENT_VALIDATION.md"),
        Path("docs/MCP_AGENT_QUICKSTART.md"),
        Path("docs/ACTION_LOG_POC.md"),
    ]

    assert root.is_dir()
    for path in docs:
        assert path.is_file(), path

    combined = "\n".join(path.read_text(encoding="utf-8") for path in docs)
    required = [
        "External Agent -> MCP/HTTP Twin -> Scenario Fault -> Policy Finding -> Patch Hints",
        "Live Agent Sandbox-first",
        "commerce.start_session",
        "commerce.get_patch_hints",
        "commerce-safety gate",
        "Permissive Twin + Policy Check",
    ]
    for snippet in required:
        assert snippet in combined


def test_stage7_demo_narrative_is_agent_sandbox_first():
    readme = Path("demo_pack/live_agent_validation/README.md")
    assert readme.is_file()
    text = readme.read_text(encoding="utf-8")

    assert "not a mock server" in text
    assert "MCP/HTTP Twin" in text
    assert "SCN-002 timeout-after-commit" in text
    assert "patch_hints.json" in text
    assert "Offline Audit" in text
