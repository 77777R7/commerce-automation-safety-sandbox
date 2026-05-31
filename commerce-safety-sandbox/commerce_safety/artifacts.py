from __future__ import annotations

import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


ARTIFACT_SCHEMA_VERSION = "commerce_safety.artifacts.v1"
RUN_MANIFEST_SCHEMA_VERSION = "commerce_safety.run_manifest.v1"

TRACE_SCHEMA_VERSION = "commerce_safety.trace.v1"
POLICY_REPORT_SCHEMA_VERSION = "commerce_safety.policy_report.v1"
STATE_DIFF_SCHEMA_VERSION = "commerce_safety.state_diff.v1"
PATCH_HINTS_SCHEMA_VERSION = "commerce_safety.patch_hints.v1"


ARTIFACT_CONTRACT: dict[str, dict[str, Any]] = {
    "scenario.yaml": {
        "artifact_type": "scenario",
        "schema_id": "commerce_safety.scenario_yaml.v1",
        "content_type": "application/x-yaml",
        "required": True,
    },
    "trace.json": {
        "artifact_type": "trace",
        "schema_id": TRACE_SCHEMA_VERSION,
        "content_type": "application/json",
        "required": True,
    },
    "policy_report.json": {
        "artifact_type": "policy_report",
        "schema_id": POLICY_REPORT_SCHEMA_VERSION,
        "content_type": "application/json",
        "required": True,
    },
    "state_diff.json": {
        "artifact_type": "state_diff",
        "schema_id": STATE_DIFF_SCHEMA_VERSION,
        "content_type": "application/json",
        "required": True,
    },
    "report.md": {
        "artifact_type": "operator_report",
        "schema_id": "commerce_safety.report_markdown.v1",
        "content_type": "text/markdown",
        "required": True,
    },
    "patch_hints.json": {
        "artifact_type": "patch_hints",
        "schema_id": PATCH_HINTS_SCHEMA_VERSION,
        "content_type": "application/json",
        "required": False,
    },
    "patch_hints.md": {
        "artifact_type": "patch_hints_markdown",
        "schema_id": "commerce_safety.patch_hints_markdown.v1",
        "content_type": "text/markdown",
        "required": False,
    },
    "agent_summary.md": {
        "artifact_type": "agent_summary",
        "schema_id": "commerce_safety.agent_summary_markdown.v1",
        "content_type": "text/markdown",
        "required": False,
    },
    "failure_explain.md": {
        "artifact_type": "failure_explain",
        "schema_id": "commerce_safety.failure_explain_markdown.v1",
        "content_type": "text/markdown",
        "required": False,
    },
}


def add_schema_version(payload: dict[str, Any], schema_version: str) -> dict[str, Any]:
    return {"schema_version": schema_version, **payload}


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as file:
        for chunk in iter(lambda: file.read(65536), b""):
            digest.update(chunk)
    return digest.hexdigest()


def artifact_entry(run_path: Path, relative_path: str) -> dict[str, Any]:
    metadata = ARTIFACT_CONTRACT[relative_path]
    path = run_path / relative_path
    entry = {
        "path": relative_path,
        "artifact_type": metadata["artifact_type"],
        "schema_id": metadata["schema_id"],
        "content_type": metadata["content_type"],
        "required": bool(metadata["required"]),
        "bytes": path.stat().st_size,
        "sha256": sha256_file(path),
        "pii_status": "redacted",
    }
    return entry


def build_run_manifest(
    *,
    run_path: Path,
    run_id: str,
    scenario_id: str,
    scenario_name: str,
    runner: str,
    status: str,
    artifacts: list[str],
    session_id: str | None = None,
    workspace_id: str | None = None,
    retention_expires_at: str | None = None,
) -> dict[str, Any]:
    retention = None
    if retention_expires_at is not None:
        retention = {
            "expires_at": retention_expires_at,
            "delete_after_expiry": True,
        }
    return {
        "schema_version": RUN_MANIFEST_SCHEMA_VERSION,
        "artifact_schema_version": ARTIFACT_SCHEMA_VERSION,
        "producer": "commerce-safety",
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "run_id": run_id,
        "session_id": session_id,
        "workspace_id": workspace_id,
        "scenario_id": scenario_id,
        "scenario_name": scenario_name,
        "runner": runner,
        "status": status,
        "retention": retention,
        "artifacts": [artifact_entry(run_path, path) for path in artifacts],
    }


def write_run_manifest(
    *,
    run_path: Path,
    run_id: str,
    scenario_id: str,
    scenario_name: str,
    runner: str,
    status: str,
    artifacts: list[str],
    session_id: str | None = None,
    workspace_id: str | None = None,
    retention_expires_at: str | None = None,
) -> dict[str, Any]:
    manifest = build_run_manifest(
        run_path=run_path,
        run_id=run_id,
        session_id=session_id,
        workspace_id=workspace_id,
        scenario_id=scenario_id,
        scenario_name=scenario_name,
        runner=runner,
        status=status,
        retention_expires_at=retention_expires_at,
        artifacts=artifacts,
    )
    path = run_path / "run_manifest.json"
    path.write_text(json.dumps(manifest, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    return manifest


def validate_run_manifest(run_path: Path | str) -> list[dict[str, Any]]:
    root = Path(run_path)
    manifest_path = root / "run_manifest.json"
    findings: list[dict[str, Any]] = []
    if not manifest_path.is_file():
        return [
            {
                "code": "run_manifest_missing",
                "path": "run_manifest.json",
                "message": "run_manifest.json is missing.",
            }
        ]

    try:
        manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as error:
        return [
            {
                "code": "run_manifest_invalid_json",
                "path": "run_manifest.json",
                "message": error.msg,
            }
        ]
    if not isinstance(manifest, dict):
        return [
            {
                "code": "run_manifest_invalid_shape",
                "path": "run_manifest.json",
                "message": "run_manifest.json must be a JSON object.",
            }
        ]

    required_fields = {
        "schema_version",
        "artifact_schema_version",
        "producer",
        "generated_at",
        "run_id",
        "scenario_id",
        "scenario_name",
        "runner",
        "status",
        "artifacts",
    }
    for field in sorted(required_fields - set(manifest)):
        findings.append(
            {
                "code": "run_manifest_required_field_missing",
                "path": "run_manifest.json",
                "message": f"run_manifest.json is missing required field: {field}.",
            }
        )
    if manifest.get("schema_version") != RUN_MANIFEST_SCHEMA_VERSION:
        findings.append(
            {
                "code": "run_manifest_schema_mismatch",
                "path": "run_manifest.json",
                "message": "run_manifest.json has an unsupported schema_version.",
            }
        )
    if manifest.get("artifact_schema_version") != ARTIFACT_SCHEMA_VERSION:
        findings.append(
            {
                "code": "artifact_schema_mismatch",
                "path": "run_manifest.json",
                "message": "run_manifest.json has an unsupported artifact_schema_version.",
            }
        )
    if manifest.get("producer") != "commerce-safety":
        findings.append(
            {
                "code": "run_manifest_producer_mismatch",
                "path": "run_manifest.json",
                "message": "run_manifest.json has an unsupported producer.",
            }
        )
    if manifest.get("status") not in {"passed", "failed"}:
        findings.append(
            {
                "code": "run_manifest_status_invalid",
                "path": "run_manifest.json",
                "message": "run_manifest.json status must be passed or failed.",
            }
        )
    generated_at = manifest.get("generated_at")
    if isinstance(generated_at, str):
        try:
            datetime.fromisoformat(generated_at)
        except ValueError:
            findings.append(
                {
                    "code": "run_manifest_generated_at_invalid",
                    "path": "run_manifest.json",
                    "message": "run_manifest.json generated_at must be ISO-8601.",
                }
            )
    elif "generated_at" in manifest:
        findings.append(
            {
                "code": "run_manifest_generated_at_invalid",
                "path": "run_manifest.json",
                "message": "run_manifest.json generated_at must be a string.",
            }
        )

    artifacts = manifest.get("artifacts", [])
    if not isinstance(artifacts, list):
        findings.append(
            {
                "code": "run_manifest_artifacts_invalid",
                "path": "run_manifest.json",
                "message": "run_manifest.json artifacts must be a list.",
            }
        )
        return findings

    seen_paths: set[str] = set()
    for artifact in artifacts:
        if not isinstance(artifact, dict):
            findings.append(
                {
                    "code": "artifact_entry_invalid",
                    "path": "run_manifest.json",
                    "message": "Artifact entries must be JSON objects.",
                }
            )
            continue
        relative = artifact.get("path")
        if not isinstance(relative, str):
            findings.append(
                {
                    "code": "artifact_path_missing",
                    "path": "run_manifest.json",
                    "message": "Artifact entry is missing a string path.",
                }
            )
            continue
        if Path(relative).is_absolute() or ".." in Path(relative).parts:
            findings.append(
                {
                    "code": "artifact_path_invalid",
                    "path": relative,
                    "message": "Manifest artifact paths must stay inside the run directory.",
                }
            )
            continue
        if relative in seen_paths:
            findings.append(
                {
                    "code": "artifact_path_duplicate",
                    "path": relative,
                    "message": "Manifest artifact path is listed more than once.",
                }
            )
            continue
        seen_paths.add(relative)
        if relative not in ARTIFACT_CONTRACT:
            findings.append(
                {
                    "code": "artifact_path_unknown",
                    "path": relative,
                    "message": "Manifest artifact path is not part of the artifact contract.",
                }
            )
            continue
        contract = ARTIFACT_CONTRACT[relative]
        for key in ["artifact_type", "schema_id", "content_type", "required"]:
            if artifact.get(key) != contract[key]:
                findings.append(
                    {
                        "code": "artifact_metadata_mismatch",
                        "path": relative,
                        "message": f"Manifest artifact {key} does not match the contract.",
                    }
                )
        path = root / relative
        if not path.is_file():
            findings.append(
                {
                    "code": "artifact_missing",
                    "path": relative,
                    "message": "Manifest-listed artifact is missing.",
                }
            )
            continue
        actual_size = path.stat().st_size
        if artifact.get("bytes") != actual_size:
            findings.append(
                {
                    "code": "artifact_size_mismatch",
                    "path": relative,
                    "message": "Manifest byte size does not match artifact.",
                }
            )
        sha256 = artifact.get("sha256")
        if not isinstance(sha256, str) or len(sha256) != 64:
            findings.append(
                {
                    "code": "artifact_hash_invalid",
                    "path": relative,
                    "message": "Manifest sha256 must be a 64-character hex digest.",
                }
            )
        actual_hash = sha256_file(path)
        if sha256 != actual_hash:
            findings.append(
                {
                    "code": "artifact_hash_mismatch",
                    "path": relative,
                    "message": "Manifest sha256 does not match artifact.",
                }
            )
        if artifact.get("content_type") == "application/json":
            try:
                payload = json.loads(path.read_text(encoding="utf-8"))
            except json.JSONDecodeError as error:
                findings.append(
                    {
                        "code": "artifact_invalid_json",
                        "path": relative,
                        "message": error.msg,
                    }
                )
                continue
            expected_schema = artifact.get("schema_id")
            if payload.get("schema_version") != expected_schema:
                findings.append(
                    {
                        "code": "artifact_schema_version_mismatch",
                        "path": relative,
                        "message": "Artifact schema_version does not match manifest schema_id.",
                    }
                )
    for relative, contract in ARTIFACT_CONTRACT.items():
        if contract["required"] and relative not in seen_paths:
            findings.append(
                {
                    "code": "artifact_required_missing_from_manifest",
                    "path": relative,
                    "message": "Required artifact is missing from run_manifest.json.",
                }
            )
    return findings
