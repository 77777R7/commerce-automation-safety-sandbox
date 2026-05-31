#!/usr/bin/env python3
from __future__ import annotations

import argparse
import fnmatch
import json
from pathlib import Path
from typing import Any

import yaml


Finding = dict[str, Any]
APPLE_DATALLESS_FLAG = 1 << 30


def load_config(path: Path | str) -> dict[str, Any]:
    return yaml.safe_load(Path(path).read_text(encoding="utf-8"))


def normalize_path(path: Path | str) -> str:
    return str(path).replace("\\", "/").lstrip("./")


def has_prefix(path: str, prefixes: list[str]) -> bool:
    normalized = normalize_path(path)
    for prefix in prefixes:
        normalized_prefix = normalize_path(prefix)
        if normalized == normalized_prefix.rstrip("/") or normalized.startswith(
            normalized_prefix
        ):
            return True
    return False


def is_ignored(path: str, config: dict[str, Any]) -> bool:
    return has_prefix(path, config.get("ignored_prefixes", []))


def is_generated_artifact(path: str, config: dict[str, Any]) -> bool:
    return has_prefix(path, config["generated_artifacts"]["prefixes"])


def is_source_allowed(path: str, config: dict[str, Any]) -> bool:
    return has_prefix(path, config["source_pr"]["allowed_prefixes"])


def check_source_pr_paths(paths: list[str], config: dict[str, Any]) -> list[Finding]:
    findings: list[Finding] = []
    for raw_path in paths:
        path = normalize_path(raw_path)
        if not path or is_ignored(path, config):
            continue
        if is_generated_artifact(path, config):
            findings.append(
                {
                    "code": "generated_artifact_in_source_pr",
                    "path": path,
                    "message": (
                        "Generated artifacts belong in the generated artifacts PR, "
                        "not the source PR."
                    ),
                }
            )
            continue
        if not is_source_allowed(path, config):
            findings.append(
                {
                    "code": "path_not_allowed_in_source_pr",
                    "path": path,
                    "message": "Path is not covered by the Stage 15 source PR manifest.",
                }
            )
    return findings


def iter_source_files(root: Path, config: dict[str, Any]) -> list[str]:
    scan_config = config.get("local_path_scan", {})
    candidate_paths = scan_config.get("candidate_paths")
    if candidate_paths and not scan_config.get("repo_wide", False):
        return [
            normalize_path(path)
            for path in candidate_paths
            if (root / normalize_path(path)).is_file()
        ]

    paths: list[str] = []
    for prefix in config["source_pr"]["allowed_prefixes"]:
        candidate = root / normalize_path(prefix)
        if not candidate.exists():
            continue
        if candidate.is_file():
            paths.append(normalize_path(candidate.relative_to(root)))
            continue
        for file_path in candidate.rglob("*"):
            if file_path.is_file():
                relative = normalize_path(file_path.relative_to(root))
                if not is_ignored(relative, config):
                    paths.append(relative)
    return sorted(set(paths))


def should_scan_text(path: str, config: dict[str, Any]) -> bool:
    scan_config = config.get("local_path_scan", {})
    if path in scan_config.get("exempt_paths", []):
        return False
    extensions = set(scan_config.get("text_extensions", []))
    return Path(path).suffix in extensions


def is_dataless_placeholder(path: Path) -> bool:
    try:
        return bool(getattr(path.stat(), "st_flags", 0) & APPLE_DATALLESS_FLAG)
    except OSError:
        return False


def scan_banned_local_paths(
    root: Path | str,
    config: dict[str, Any],
    *,
    candidate_paths: list[str] | None = None,
) -> list[Finding]:
    root_path = Path(root)
    paths = candidate_paths if candidate_paths is not None else iter_source_files(root_path, config)
    fragments = config["banned_local_path_fragments"]
    scan_config = config.get("local_path_scan", {})
    skip_unreadable = bool(scan_config.get("skip_unreadable", False))
    findings: list[Finding] = []

    for relative in paths:
        path = normalize_path(relative)
        if not should_scan_text(path, config):
            continue
        full_path = root_path / path
        if not full_path.is_file():
            continue
        if skip_unreadable and is_dataless_placeholder(full_path):
            continue
        try:
            lines = full_path.read_text(encoding="utf-8", errors="ignore").splitlines()
        except (OSError, TimeoutError) as error:
            if not skip_unreadable:
                findings.append(
                    {
                        "code": "unreadable_source_file",
                        "path": path,
                        "message": str(error),
                    }
                )
            continue
        for line_number, line in enumerate(lines, start=1):
            for fragment in fragments:
                if fragment in line:
                    findings.append(
                        {
                            "code": "banned_local_path",
                            "path": path,
                            "line": line_number,
                            "fragment": fragment,
                            "message": "Source PR files must not expose local machine paths.",
                        }
                    )
    return findings


def check_manifest_split(config: dict[str, Any]) -> list[Finding]:
    source = {normalize_path(path) for path in config["source_pr"]["allowed_prefixes"]}
    generated = {
        normalize_path(path) for path in config["generated_artifacts"]["prefixes"]
    }
    overlap = sorted(source & generated)
    return [
        {
            "code": "manifest_overlap",
            "path": path,
            "message": "A path prefix cannot belong to both source and generated PRs.",
        }
        for path in overlap
    ]


def check_generated_duplicate_artifacts(root: Path | str, config: dict[str, Any]) -> list[Finding]:
    root_path = Path(root)
    findings: list[Finding] = []
    for prefix in config["generated_artifacts"]["prefixes"]:
        candidate = root_path / normalize_path(prefix)
        if not candidate.exists():
            continue
        for file_path in candidate.rglob("*"):
            if not file_path.is_file():
                continue
            relative = normalize_path(file_path.relative_to(root_path))
            if fnmatch.fnmatch(file_path.name, "* 2.*"):
                findings.append(
                    {
                        "code": "duplicate_generated_artifact",
                        "path": relative,
                        "message": (
                            "Duplicate generated artifacts should be cleaned before "
                            "a generated artifacts PR."
                        ),
                    }
                )
    return findings


def run_checks(
    root: Path,
    config: dict[str, Any],
    *,
    source_pr_paths: list[str] | None = None,
    check_generated_duplicates: bool = False,
) -> list[Finding]:
    findings: list[Finding] = []
    findings.extend(check_manifest_split(config))
    if source_pr_paths is not None:
        findings.extend(check_source_pr_paths(source_pr_paths, config))
    findings.extend(scan_banned_local_paths(root, config))
    if check_generated_duplicates:
        findings.extend(check_generated_duplicate_artifacts(root, config))
    return findings


def _read_path_list(path: Path) -> list[str]:
    return [
        line.strip()
        for line in path.read_text(encoding="utf-8").splitlines()
        if line.strip() and not line.strip().startswith("#")
    ]


def main() -> int:
    parser = argparse.ArgumentParser(description="Run Stage 15 release hygiene checks.")
    parser.add_argument("--root", type=Path, default=Path("."))
    parser.add_argument("--config", type=Path, default=Path("release_hygiene.yaml"))
    parser.add_argument("--source-pr-paths", type=Path)
    parser.add_argument("--check-generated-duplicates", action="store_true")
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args()

    config = load_config(args.config)
    source_pr_paths = (
        _read_path_list(args.source_pr_paths) if args.source_pr_paths else None
    )
    findings = run_checks(
        args.root,
        config,
        source_pr_paths=source_pr_paths,
        check_generated_duplicates=args.check_generated_duplicates,
    )

    if args.json:
        print(json.dumps({"ok": not findings, "findings": findings}, indent=2))
    elif findings:
        print("Stage 15 release hygiene failed:")
        for finding in findings:
            location = finding.get("path", "<repo>")
            if finding.get("line"):
                location = f"{location}:{finding['line']}"
            print(f"- {finding['code']} {location}: {finding['message']}")
    else:
        print("Stage 15 release hygiene checks passed.")

    return 1 if findings else 0


if __name__ == "__main__":
    raise SystemExit(main())
