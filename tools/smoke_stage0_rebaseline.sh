#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"

cd "$ROOT_DIR"

python3 - <<'PY'
from pathlib import Path

required_files = [
    Path("README.md"),
    Path("ROADMAP.md"),
    Path("MVP_ACCEPTANCE.md"),
    Path("AGENTS.md"),
]

missing = [str(path) for path in required_files if not path.is_file()]
if missing:
    raise SystemExit("Missing source-of-truth files:\n" + "\n".join(missing))

docs = {str(path): path.read_text(encoding="utf-8") for path in required_files}
combined = "\n".join(docs.values())

required_global_snippets = [
    "Live Agent Sandbox-first",
    "MCP is not optional for V3.5",
    "External Agent -> MCP/HTTP Twin -> Scenario Fault -> Policy Finding -> Patch Hints",
]

missing_snippets = []
for snippet in required_global_snippets:
    if snippet not in combined:
        missing_snippets.append(f"missing required phrase: {snippet}")

offline_support_count = sum(
    1
    for text in docs.values()
    if "Offline" in text and ("supporting" in text or "secondary" in text)
)
if offline_support_count < 3:
    missing_snippets.append(
        "Offline Audit must be described as supporting/secondary in at least 3 source-of-truth docs"
    )

roadmap = docs["ROADMAP.md"]
for stage in range(0, 13):
    if f"## Stage {stage}:" not in roadmap:
        missing_snippets.append(f"ROADMAP.md missing Stage {stage} section")

stage_gate_snippets = [
    "./tools/smoke_stage0_rebaseline.sh",
    "./tools/smoke_stage1_live_session.sh",
    "./tools/smoke_stage2_http_scn002.sh",
    "./tools/smoke_stage3_mcp_scn002.sh",
    "./tools/smoke_live_all.sh",
    "./tools/smoke_stage5_action_log_gate.sh",
    "./tools/smoke_stage6_repair_loop.sh",
    "./tools/smoke_stage7_demo_pack.sh",
    "./tools/smoke_stage9_real_mcp.sh",
    "./tools/smoke_stage9_api_hardening.sh",
    "./tools/smoke_stage10_mcp_p0_all.sh",
    "./tools/smoke_stage10_http_p0_all.sh",
    "./tools/smoke_stage11_openapi_contract.sh",
    "./tools/smoke_stage12_shopify_skin_v0.sh",
    "./tools/smoke_v35.sh",
]
for snippet in stage_gate_snippets:
    if snippet not in roadmap:
        missing_snippets.append(f"ROADMAP.md missing stage gate: {snippet}")

agents = docs["AGENTS.md"]
for stale_snippet in [
    "Offline Fulfillment Automation Audit\n```",
    "- MCP server",
    "- API server",
]:
    if stale_snippet in agents:
        missing_snippets.append(f"AGENTS.md still contains stale non-goal/mainline text: {stale_snippet}")

if missing_snippets:
    raise SystemExit("Stage 0 rebaseline gate failed:\n" + "\n".join(missing_snippets))

print("Stage 0 rebaseline gate passed.")
PY
