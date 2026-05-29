from __future__ import annotations

import re
from pathlib import Path
from shutil import copy2
from typing import Any

from .io import load_yaml, read_json, write_text


def slugify_name(name: str) -> str:
    slug = re.sub(r"[^a-zA-Z0-9]+", "-", name.strip().lower()).strip("-")
    return slug or "regression"


def find_scenario_file(run_path: Path, scenario_dir: Path) -> Path:
    captured = run_path / "scenario.yaml"
    if captured.exists():
        return captured

    trace = read_json(run_path / "trace.json")
    scenario_id = trace["scenario_id"]
    for candidate in sorted(scenario_dir.glob("*.yaml")):
        try:
            scenario = load_yaml(candidate)
        except Exception:
            continue
        if scenario.get("id") == scenario_id:
            return candidate
    raise FileNotFoundError(
        f"Could not find scenario.yaml for scenario id {scenario_id!r}."
    )


def build_regression_summary(
    *,
    name: str,
    slug: str,
    trace: dict[str, Any],
    policy_report: dict[str, Any],
) -> str:
    findings = policy_report["findings"]
    lines = [
        f"# Regression Scenario: {name}",
        "",
        "This regression was captured from a failed commerce safety run.",
        "",
        "## Source Run",
        "",
        f"- Run ID: `{trace['run_id']}`",
        f"- Scenario ID: `{trace['scenario_id']}`",
        f"- Scenario name: `{trace['scenario_name']}`",
        f"- Runner: `{trace['runner']}`",
        f"- Original status: `{trace['status']}`",
        f"- Regression directory: `regressions/{slug}`",
        "",
        "## Why This Must Stay In The Gate",
        "",
        (
            "Future automation should rerun this scenario and produce zero policy "
            "findings before it is considered safe to ship."
        ),
        "",
        "## Policy Findings",
        "",
    ]
    for finding in findings:
        lines.extend(
            [
                f"### {finding['policy_id']}",
                "",
                f"- Severity: `{finding['severity']}`",
                f"- Status: `{finding['status']}`",
                f"- Business impact: {finding['business_impact']}",
                f"- Recommendation: {finding['recommendation']}",
                "",
            ]
        )

    lines.extend(
        [
            "## Incident Timeline",
            "",
        ]
    )
    for event in trace["timeline"]:
        lines.append(f"{event['step']}. {event['message']}")

    lines.extend(
        [
            "",
            "## Regression Gate",
            "",
            "A safe runner should pass this scenario with no policy findings:",
            "",
            "```bash",
            f"./commerce-safety run regressions/{slug}/scenario.yaml --runner good_runner",
            "```",
            "",
            "The captured unsafe behavior can be replayed from the saved trace:",
            "",
            "```bash",
            f"./commerce-safety replay regressions/{slug}",
            "```",
            "",
            "## Saved Artifacts",
            "",
            "- `scenario.yaml`",
            "- `trace.json`",
            "- `policy_report.json`",
            "- `state_diff.json`",
            "- `summary.md`",
        ]
    )
    return "\n".join(lines)


def save_regression(
    *,
    run_path: Path,
    name: str,
    regressions_dir: Path,
    scenario_dir: Path,
) -> dict[str, Any]:
    trace_path = run_path / "trace.json"
    policy_path = run_path / "policy_report.json"
    state_diff_path = run_path / "state_diff.json"
    report_path = run_path / "report.md"
    for required in (trace_path, policy_path, state_diff_path):
        if not required.exists():
            raise FileNotFoundError(f"Missing run artifact: {required}")

    trace = read_json(trace_path)
    policy_report = read_json(policy_path)
    findings = policy_report.get("findings", [])
    if not findings:
        raise ValueError("Only failed runs with policy findings can be saved.")

    slug = slugify_name(name)
    target_dir = regressions_dir / slug
    target_dir.mkdir(parents=True, exist_ok=True)

    scenario_path = find_scenario_file(run_path, scenario_dir)
    copy2(scenario_path, target_dir / "scenario.yaml")
    copy2(trace_path, target_dir / "trace.json")
    copy2(policy_path, target_dir / "policy_report.json")
    copy2(state_diff_path, target_dir / "state_diff.json")
    if report_path.exists():
        copy2(report_path, target_dir / "source_report.md")

    summary = build_regression_summary(
        name=name,
        slug=slug,
        trace=trace,
        policy_report=policy_report,
    )
    write_text(target_dir / "summary.md", summary)
    return {
        "name": name,
        "slug": slug,
        "path": str(target_dir),
        "findings": findings,
        "artifacts": [
            "scenario.yaml",
            "trace.json",
            "policy_report.json",
            "state_diff.json",
            "summary.md",
        ],
    }
