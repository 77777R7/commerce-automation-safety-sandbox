from __future__ import annotations

import json
from pathlib import Path

from commerce_safety.artifacts import (
    ARTIFACT_SCHEMA_VERSION,
    RUN_MANIFEST_SCHEMA_VERSION,
    validate_run_manifest,
)
from commerce_safety.engine import run_scenario
from commerce_safety.live.sessions import SessionManager


SCN002 = Path("commerce-safety-sandbox/scenarios/SCN-002_timeout_after_commit_retry.yaml")


def _read_json(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def test_cli_run_writes_versioned_manifest_and_artifact_schemas(tmp_path: Path) -> None:
    result = run_scenario(SCN002, "bad_runner", tmp_path)
    run_path = Path(result["run_path"])

    manifest = _read_json(run_path / "run_manifest.json")
    assert manifest["schema_version"] == RUN_MANIFEST_SCHEMA_VERSION
    assert manifest["artifact_schema_version"] == ARTIFACT_SCHEMA_VERSION
    assert manifest["run_id"] == result["run_id"]
    assert manifest["scenario_id"] == "SCN-002"
    assert manifest["runner"] == "bad_runner"
    assert manifest["status"] == "failed"
    assert manifest["product_name"] == "Agent Integration Safety Sandbox"
    assert manifest["product_surface"] == "Legacy Commerce Safety Sandbox"
    assert manifest["artifact_schema_alias"] == "agent_validation.artifacts.v1"

    artifacts_by_path = {artifact["path"]: artifact for artifact in manifest["artifacts"]}
    for required_path, schema_id in {
        "trace.json": "commerce_safety.trace.v1",
        "policy_report.json": "commerce_safety.policy_report.v1",
        "state_diff.json": "commerce_safety.state_diff.v1",
    }.items():
        assert required_path in artifacts_by_path
        assert artifacts_by_path[required_path]["schema_id"] == schema_id
        assert _read_json(run_path / required_path)["schema_version"] == schema_id
        assert artifacts_by_path[required_path]["sha256"]
        assert artifacts_by_path[required_path]["bytes"] > 0

    assert "report.md" in artifacts_by_path
    assert artifacts_by_path["report.md"]["content_type"] == "text/markdown"
    assert validate_run_manifest(run_path) == []


def test_live_session_manifest_includes_agent_repair_artifacts(tmp_path: Path) -> None:
    manager = SessionManager(runs_dir=tmp_path)
    session = manager.create_session(scenario_id="SCN-002")
    task = manager.get_next_task(session.session_id)
    assert task

    try:
        session.twin.create_fulfillment(
            order_id=task["order_id"],
            sku="sku_retry_1",
            quantity=1,
            actor="stage17_bad_agent",
            webhook_id=None,
            idempotency_key=None,
            request_id="stage17_attempt_1",
            source_event_id=task["id"],
            fault_type=task["fault"]["type"],
        )
    except Exception:
        pass
    session.twin.create_fulfillment(
        order_id=task["order_id"],
        sku="sku_retry_1",
        quantity=1,
        actor="stage17_bad_agent",
        webhook_id=None,
        idempotency_key=None,
        request_id="stage17_attempt_2",
        source_event_id=task["id"],
    )

    result = manager.complete_session(session.session_id, runner_name="stage17_bad_agent")
    run_path = Path(result["run_path"])
    manifest = _read_json(run_path / "run_manifest.json")
    artifacts_by_path = {artifact["path"]: artifact for artifact in manifest["artifacts"]}

    for path in [
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
    ]:
        assert path in artifacts_by_path

    assert _read_json(run_path / "patch_hints.json")["schema_version"] == (
        "commerce_safety.patch_hints.v1"
    )
    assert _read_json(run_path / "github_check_summary.json")["schema_version"] == (
        "commerce_safety.github_check_summary.v1"
    )
    assert validate_run_manifest(run_path) == []


def test_manifest_validation_detects_tampered_artifact(tmp_path: Path) -> None:
    result = run_scenario(SCN002, "bad_runner", tmp_path)
    run_path = Path(result["run_path"])
    trace_path = run_path / "trace.json"
    trace = _read_json(trace_path)
    trace["status"] = "tampered"
    trace_path.write_text(json.dumps(trace, indent=2) + "\n", encoding="utf-8")

    findings = validate_run_manifest(run_path)

    assert findings
    assert any(
        finding["code"] == "artifact_hash_mismatch" and finding["path"] == "trace.json"
        for finding in findings
    )


def test_manifest_validation_enforces_required_contract_artifacts(tmp_path: Path) -> None:
    result = run_scenario(SCN002, "bad_runner", tmp_path)
    run_path = Path(result["run_path"])
    manifest_path = run_path / "run_manifest.json"
    manifest = _read_json(manifest_path)
    manifest["artifacts"] = [
        artifact
        for artifact in manifest["artifacts"]
        if artifact["path"] != "state_diff.json"
    ]
    manifest_path.write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")

    findings = validate_run_manifest(run_path)

    assert any(
        finding["code"] == "artifact_required_missing_from_manifest"
        and finding["path"] == "state_diff.json"
        for finding in findings
    )


def test_manifest_validation_rejects_unknown_and_traversal_artifact_paths(tmp_path: Path) -> None:
    result = run_scenario(SCN002, "bad_runner", tmp_path)
    run_path = Path(result["run_path"])
    manifest_path = run_path / "run_manifest.json"
    manifest = _read_json(manifest_path)
    trace_entry = dict(manifest["artifacts"][0])
    trace_entry["path"] = "../trace.json"
    unknown_entry = dict(manifest["artifacts"][0])
    unknown_entry["path"] = "debug.log"
    manifest["artifacts"].extend([trace_entry, unknown_entry])
    manifest_path.write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")

    findings = validate_run_manifest(run_path)
    codes = {finding["code"] for finding in findings}

    assert "artifact_path_invalid" in codes
    assert "artifact_path_unknown" in codes


def test_manifest_validation_rejects_bad_identity_fields(tmp_path: Path) -> None:
    result = run_scenario(SCN002, "bad_runner", tmp_path)
    run_path = Path(result["run_path"])
    manifest_path = run_path / "run_manifest.json"
    manifest = _read_json(manifest_path)
    manifest["producer"] = "other"
    manifest["status"] = "unknown"
    manifest["generated_at"] = "not-a-date"
    manifest_path.write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")

    findings = validate_run_manifest(run_path)
    codes = {finding["code"] for finding in findings}

    assert "run_manifest_producer_mismatch" in codes
    assert "run_manifest_status_invalid" in codes
    assert "run_manifest_generated_at_invalid" in codes
