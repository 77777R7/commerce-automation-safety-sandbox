from __future__ import annotations

import argparse
import subprocess
from pathlib import Path
from typing import Any

import yaml


ROOT = Path(__file__).resolve().parents[1]


def _load_manifest(path: Path) -> dict[str, Any]:
    return yaml.safe_load(path.read_text(encoding="utf-8"))


def _is_executable(path: Path) -> bool:
    return path.exists() and path.stat().st_mode & 0o111 != 0


def _git_status_paths() -> list[str]:
    try:
        result = subprocess.run(
            ["git", "status", "--short"],
            cwd=ROOT,
            check=True,
            text=True,
            capture_output=True,
        )
    except Exception:
        return []
    paths: list[str] = []
    for line in result.stdout.splitlines():
        if not line:
            continue
        # Handles normal porcelain and rename lines well enough for this gate.
        path = line[3:].strip()
        if " -> " in path:
            path = path.split(" -> ", 1)[1].strip()
        paths.append(path)
    return paths


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--manifest",
        default="stage19_release_candidate.yaml",
        help="Stage 19 release candidate manifest.",
    )
    parser.add_argument(
        "--strict-status",
        action="store_true",
        help="Fail if dirty files exist outside the Stage 19 manifest or deferred prefixes.",
    )
    args = parser.parse_args()

    manifest_path = ROOT / args.manifest
    manifest = _load_manifest(manifest_path)
    required_paths = [str(path) for path in manifest["required_paths"]]
    deferred_prefixes = tuple(str(prefix) for prefix in manifest["generated_or_deferred_prefixes"])

    findings: list[str] = []
    for relative in required_paths:
        path = ROOT / relative
        if not path.exists():
            findings.append(f"missing_required_path: {relative}")
        if relative.startswith("tools/smoke_") and relative.endswith(".sh"):
            if not _is_executable(path):
                findings.append(f"smoke_not_executable: {relative}")

    required_text = {
        "docs/STAGE19_RELEASE_CANDIDATE.md": [
            "Exclude From Stage 19 Review",
            "Stop Line",
        ],
        "docs/PR_STAGE19_DESCRIPTION.md": [
            "Review Scope",
            "Test Plan",
        ],
        "docs/STAGE19_HOSTED_DESIGN_PARTNER_TRUST_GATE.md": [
            "No-Real-Store Boundary",
            "Stage 19 Gate",
        ],
        "ROADMAP.md": [
            "## Stage 19: Hosted Design Partner Trust Gate",
        ],
        "tools/smoke_v35.sh": [
            "smoke_stage19_hosted_enterprise_poc.sh",
        ],
    }
    for relative, snippets in required_text.items():
        text = (ROOT / relative).read_text(encoding="utf-8")
        for snippet in snippets:
            if snippet not in text:
                findings.append(f"missing_snippet: {relative}: {snippet}")

    release_paths = set(required_paths)
    generated_in_manifest = [
        path for path in release_paths if path.startswith(deferred_prefixes)
    ]
    for path in sorted(generated_in_manifest):
        findings.append(f"generated_path_in_release_manifest: {path}")

    if args.strict_status:
        allowed = set(required_paths)
        noisy = []
        for path in _git_status_paths():
            if path in allowed or path.startswith(deferred_prefixes):
                continue
            noisy.append(path)
        for path in noisy:
            findings.append(f"dirty_path_outside_stage19_manifest: {path}")

    if findings:
        for finding in findings:
            print(finding)
        return 1

    print("Stage 19 release candidate manifest is reviewable.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
