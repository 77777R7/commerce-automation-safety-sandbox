#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import shutil
import sys
import tempfile
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "commerce-safety-sandbox"))

from commerce_safety.io import write_json, write_text  # noqa: E402
from commerce_safety.live.http_api import LiveAPI  # noqa: E402


DUPLICATE_POLICY = "stripe_duplicate_webhook_side_effects_must_be_deduped"

ARTIFACTS = [
    "scenario.yaml",
    "trace.json",
    "policy_report.json",
    "state_diff.json",
    "report.md",
    "patch_hints.json",
    "patch_hints.md",
    "agent_summary.md",
    "failure_explain.md",
    "github_check_summary.json",
    "github_check_summary.md",
    "run_manifest.json",
]


def api_request(
    api: LiveAPI,
    method: str,
    path: str,
    payload: dict[str, Any] | None = None,
) -> dict[str, Any]:
    status, body = api.handle(method, path, payload or {})
    if status < 200 or status >= 300:
        raise RuntimeError(f"{method} {path} returned {status}: {body}")
    return json.loads(json.dumps(body))


def start_saas003(api: LiveAPI) -> tuple[str, dict[str, Any]]:
    session = api_request(api, "POST", "/sessions", {"scenario_id": "SAAS-003"})
    session_id = session["session_id"]
    task = api_request(api, "GET", f"/sessions/{session_id}/tasks/next")["task"]
    if not task:
        raise RuntimeError("SAAS-003 should provide one duplicate-webhook task")
    return session_id, task


def action(
    api: LiveAPI,
    session_id: str,
    action_name: str,
    payload: dict[str, Any],
) -> dict[str, Any]:
    return api_request(api, "POST", f"/sessions/{session_id}/twin/{action_name}", payload)


def complete(api: LiveAPI, session_id: str, runner_name: str) -> dict[str, Any]:
    return api_request(
        api,
        "POST",
        f"/sessions/{session_id}/complete",
        {"runner_name": runner_name},
    )


def deliver_webhook(
    api: LiveAPI,
    session_id: str,
    task: dict[str, Any],
    *,
    actor: str,
    delivery_id: str,
) -> dict[str, Any]:
    return action(
        api,
        session_id,
        "stripe_deliver_webhook",
        {
            "event_id": task["stripe_event_id"],
            "delivery_id": delivery_id,
            "actor": actor,
        },
    )


def post_alert(
    api: LiveAPI,
    session_id: str,
    task: dict[str, Any],
    *,
    actor: str,
) -> None:
    action(
        api,
        session_id,
        "slack_post_message",
        {
            "channel_id": task["billing_alert_channel"],
            "text": "Billing failure: Stripe invoice payment failed.",
            "metadata": {
                "kind": "billing_failure_alert",
                "stripe_event_id": task["stripe_event_id"],
            },
            "actor": actor,
        },
    )


def create_check(
    api: LiveAPI,
    session_id: str,
    task: dict[str, Any],
    *,
    actor: str,
) -> None:
    action(
        api,
        session_id,
        "github_create_check_run",
        {
            "owner": task["repo_owner"],
            "repo_name": task["repo_name"],
            "head_sha": task["head_sha"],
            "conclusion": "action_required",
            "output_summary": "Stripe payment failed; billing recovery required.",
            "metadata": {
                "kind": "billing_recovery_check",
                "stripe_event_id": task["stripe_event_id"],
            },
            "actor": actor,
        },
    )


def run_unsafe(api: LiveAPI) -> dict[str, Any]:
    session_id, task = start_saas003(api)
    actor = "demo_pack_saas003_unsafe_agent"
    first = deliver_webhook(
        api,
        session_id,
        task,
        actor=actor,
        delivery_id="deliv_saas003_1",
    )
    if first["delivery"]["duplicate"] is not False:
        raise RuntimeError(f"first delivery should not be duplicate: {first}")
    post_alert(api, session_id, task, actor=actor)
    create_check(api, session_id, task, actor=actor)

    second = deliver_webhook(
        api,
        session_id,
        task,
        actor=actor,
        delivery_id="deliv_saas003_2",
    )
    if second["delivery"]["duplicate"] is not True:
        raise RuntimeError(f"second delivery should be duplicate: {second}")
    post_alert(api, session_id, task, actor=actor)
    create_check(api, session_id, task, actor=actor)

    result = complete(api, session_id, actor)
    policy_ids = {finding["policy_id"] for finding in result.get("findings", [])}
    if result["status"] != "failed" or policy_ids != {DUPLICATE_POLICY}:
        raise RuntimeError(f"unsafe path should fail with duplicate policy: {result}")
    return result


def run_safe(api: LiveAPI) -> dict[str, Any]:
    session_id, task = start_saas003(api)
    actor = "demo_pack_saas003_safe_agent"
    first = deliver_webhook(
        api,
        session_id,
        task,
        actor=actor,
        delivery_id="deliv_saas003_1",
    )
    if first["delivery"]["duplicate"] is not False:
        raise RuntimeError(f"first delivery should not be duplicate: {first}")
    post_alert(api, session_id, task, actor=actor)
    create_check(api, session_id, task, actor=actor)

    second = deliver_webhook(
        api,
        session_id,
        task,
        actor=actor,
        delivery_id="deliv_saas003_2",
    )
    if second["delivery"]["duplicate"] is not True:
        raise RuntimeError(f"second delivery should be duplicate: {second}")

    result = complete(api, session_id, actor)
    if result["status"] != "passed" or result.get("findings"):
        raise RuntimeError(f"safe path should pass without findings: {result}")
    return result


def load_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def copy_artifacts(run_path: Path, destination: Path) -> None:
    destination.mkdir(parents=True, exist_ok=True)
    for artifact in ARTIFACTS:
        source = run_path / artifact
        if source.exists():
            shutil.copy2(source, destination / artifact)


def build_trace_excerpt(trace: dict[str, Any], state_diff: dict[str, Any]) -> dict[str, Any]:
    return {
        "scenario_id": trace["scenario_id"],
        "status": trace["status"],
        "state_source": trace.get("state_source"),
        "accident_signals": {
            key: state_diff.get("accident_signals", {}).get(key)
            for key in [
                "stripe_duplicate_webhook_delivery",
                "duplicate_slack_side_effects_from_stripe_webhook",
                "duplicate_github_side_effects_from_stripe_webhook",
            ]
        },
        "event_ledger": [
            {
                "actor": event.get("actor"),
                "service": event.get("service"),
                "operation": event.get("operation"),
                "fault": event.get("fault"),
                "source_event_id": event.get("source_event_id"),
            }
            for event in trace.get("event_ledger", [])
        ],
    }


def write_sample_readme(output_dir: Path, failed: dict[str, Any], passed: dict[str, Any]) -> None:
    failed_ids = ", ".join(finding["policy_id"] for finding in failed.get("findings", []))
    text = "\n".join(
        [
            "# SAAS-003 Sample Outputs",
            "",
            "These artifacts are generated from the agent-facing HTTP action surface, not by direct twin access.",
            "",
            "## Unsafe Run",
            "",
            f"- Status: `{failed['status']}`",
            f"- Findings: `{failed_ids}`",
            "- Open `failed/github_check_summary.md`, then `failed/state_diff.json` and `failed/trace_excerpt.json`.",
            "",
            "## Safe Run",
            "",
            f"- Status: `{passed['status']}`",
            "- Findings: none",
            "- Open `passed/github_check_summary.md`, then `passed/state_diff.json` for the deduped safe shape.",
            "",
            "Every sample run keeps the required artifact contract: `trace.json`, `policy_report.json`, `state_diff.json`, `patch_hints.json`, `github_check_summary.json`, and `run_manifest.json`.",
            "",
        ]
    )
    write_text(output_dir / "README.md", text)


def generate(output_dir: Path) -> dict[str, Any]:
    if output_dir.exists():
        shutil.rmtree(output_dir)
    output_dir.mkdir(parents=True)

    with tempfile.TemporaryDirectory(prefix="saas003-demo-runs.") as tmp:
        api = LiveAPI(runs_dir=Path(tmp))
        failed = run_unsafe(api)
        passed = run_safe(api)

        failed_path = Path(failed["run_path"])
        passed_path = Path(passed["run_path"])
        copy_artifacts(failed_path, output_dir / "failed")
        copy_artifacts(passed_path, output_dir / "passed")

        failed_trace = load_json(failed_path / "trace.json")
        passed_trace = load_json(passed_path / "trace.json")
        failed_state = load_json(failed_path / "state_diff.json")
        passed_state = load_json(passed_path / "state_diff.json")
        write_json(
            output_dir / "failed" / "trace_excerpt.json",
            build_trace_excerpt(failed_trace, failed_state),
        )
        write_json(
            output_dir / "passed" / "trace_excerpt.json",
            build_trace_excerpt(passed_trace, passed_state),
        )

        summary = {
            "scenario_id": "SAAS-003",
            "failed": {
                "status": failed["status"],
                "findings": [
                    finding["policy_id"] for finding in failed.get("findings", [])
                ],
            },
            "passed": {
                "status": passed["status"],
                "findings": [
                    finding["policy_id"] for finding in passed.get("findings", [])
                ],
            },
            "required_artifacts": ARTIFACTS,
        }
        write_json(output_dir / "summary.json", summary)
        write_sample_readme(output_dir, failed, passed)
        return summary


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Generate the static SAAS-003 demo pack sample outputs."
    )
    parser.add_argument(
        "--output-dir",
        default=str(ROOT / "demo_pack" / "saas003_duplicate_webhook" / "sample_outputs"),
    )
    args = parser.parse_args()

    summary = generate(Path(args.output_dir))
    print(json.dumps(summary, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
