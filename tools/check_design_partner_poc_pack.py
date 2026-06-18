from __future__ import annotations

import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
PACKAGE = ROOT / "docs/design_partner_poc"
BANNED_LOCAL_PATH_FRAGMENTS = (
    "/" + "Users" + "/",
    "/" + "private" + "/" + "var" + "/" + "folders" + "/",
    "/" + "var" + "/" + "folders" + "/",
)

REQUIRED = {
    "README.md": [
        "Design Partner POC Package",
        "POC Flow",
        "Permissive Twin + Policy Check",
        "External Agent or Workflow -> MCP/HTTP Twin -> Scenario Fault -> Policy Finding -> Patch Hints",
    ],
    "hosted_boundary.md": [
        "Hosted Boundary",
        "Kill Switch",
    ],
    "no_real_store_boundary.md": [
        "Not Allowed",
        "Lightweight PII / Secret Checks",
    ],
    "integration_steps.md": [
        "MCP/HTTP Integration Steps",
        "Option A: MCP",
        "Option B: HTTP",
    ],
    "p0_scenarios.md": [
        "SCN-001",
        "SCN-002",
        "SCN-003",
        "SCN-004",
        "SCN-005",
    ],
    "artifact_report_examples.md": [
        "trace.json",
        "policy_report.json",
        "state_diff.json",
        "report.md",
        "run_manifest.json",
        "samples/trace_excerpt.json",
    ],
    "poc_success_criteria.md": [
        "Technical Success",
        "Business Success",
        "Commercial Success",
    ],
    "one_pager.md": [
        "The Problem",
        "What We Do",
        "Safety Boundary",
    ],
    "samples/report_excerpt.md": [
        "Business Risk Summary",
        "Permissive Twin + Policy Check",
    ],
}

SAMPLE_JSON = [
    "samples/trace_excerpt.json",
    "samples/policy_report_excerpt.json",
    "samples/state_diff_excerpt.json",
]

MANIFEST = ROOT / "design_partner_poc_package.yaml"


def main() -> int:
    findings: list[str] = []
    if not MANIFEST.is_file():
        findings.append("missing_manifest: design_partner_poc_package.yaml")

    for filename, snippets in REQUIRED.items():
        path = PACKAGE / filename
        if not path.is_file():
            findings.append(f"missing_file: {path.relative_to(ROOT)}")
            continue
        text = path.read_text(encoding="utf-8")
        for snippet in snippets:
            if snippet not in text:
                findings.append(f"missing_snippet: {path.relative_to(ROOT)}: {snippet}")
        for fragment in BANNED_LOCAL_PATH_FRAGMENTS:
            if fragment in text:
                findings.append(
                    f"banned_local_path: {path.relative_to(ROOT)}: {fragment}"
                )

    for filename in SAMPLE_JSON:
        path = PACKAGE / filename
        if not path.is_file():
            findings.append(f"missing_sample_json: {path.relative_to(ROOT)}")
            continue
        try:
            json.loads(path.read_text(encoding="utf-8"))
        except json.JSONDecodeError as error:
            findings.append(f"invalid_sample_json: {path.relative_to(ROOT)}: {error}")

    readme = (PACKAGE / "README.md").read_text(encoding="utf-8")
    for filename in REQUIRED:
        if filename == "README.md":
            continue
        if filename not in readme:
            findings.append(f"readme_missing_link_text: {filename}")

    if findings:
        for finding in findings:
            print(finding)
        return 1
    print("Design Partner POC package is complete.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
