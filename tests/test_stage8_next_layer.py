from __future__ import annotations

from pathlib import Path


def test_stage8_next_layer_is_split_before_implementation():
    path = Path("docs/ARGA_STYLE_NEXT_LAYER.md")

    assert path.is_file()
    text = path.read_text(encoding="utf-8")
    required = [
        "Stage 8 is planning-only in this branch",
        "GitHub Actions gate",
        "PR check",
        "scenario registry",
        "stub coverage",
        "trace streaming",
        "hosted sessions",
        "team workspace",
        "MCP transport wrapper",
    ]
    for snippet in required:
        assert snippet in text


def test_v35_gate_script_exists_and_references_stage_gates():
    path = Path("tools/smoke_v35.sh")

    assert path.is_file()
    text = path.read_text(encoding="utf-8")
    required = [
        "smoke_stage0_rebaseline.sh",
        "smoke_stage1_live_session.sh",
        "smoke_stage2_http_scn002.sh",
        "smoke_stage3_mcp_scn002.sh",
        "smoke_live_all.sh",
        "smoke_stage5_action_log_gate.sh",
        "smoke_stage6_repair_loop.sh",
        "smoke_stage7_demo_pack.sh",
    ]
    for snippet in required:
        assert snippet in text
