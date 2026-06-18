#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import re
from pathlib import Path
from typing import Any

import yaml


Finding = dict[str, Any]
APPLE_DATALLESS_FLAG = 1 << 30


def load_config(path: Path | str) -> dict[str, Any]:
    return yaml.safe_load(Path(path).read_text(encoding="utf-8"))


def normalize_path(path: Path | str) -> str:
    normalized = str(path).replace("\\", "/")
    if normalized.startswith("./"):
        return normalized[2:]
    return normalized


def has_prefix(path: str, prefixes: list[str]) -> bool:
    normalized = normalize_path(path)
    for prefix in prefixes:
        normalized_prefix = normalize_path(prefix)
        if normalized == normalized_prefix.rstrip("/") or normalized.startswith(
            normalized_prefix
        ):
            return True
    return False


def iter_scan_paths(root: Path, config: dict[str, Any]) -> list[str]:
    source_scan = config.get("source_scan", {})
    candidate_paths = source_scan.get("candidate_paths", [])
    if not source_scan.get("repo_wide", False):
        return [normalize_path(path) for path in candidate_paths]

    prefixes = source_scan.get("prefixes", [])
    ignored_prefixes = source_scan.get("ignored_prefixes", [])
    exempt_paths = {normalize_path(path) for path in source_scan.get("exempt_paths", [])}
    text_extensions = set(source_scan.get("text_extensions", []))
    paths: list[str] = []
    for prefix in prefixes:
        candidate = root / normalize_path(prefix)
        if not candidate.exists():
            continue
        if candidate.is_file():
            relative = normalize_path(candidate.relative_to(root))
            if relative not in exempt_paths and Path(relative).suffix in text_extensions:
                paths.append(relative)
            continue
        for file_path in candidate.rglob("*"):
            if not file_path.is_file():
                continue
            relative = normalize_path(file_path.relative_to(root))
            if relative in exempt_paths:
                continue
            if has_prefix(relative, ignored_prefixes):
                continue
            if Path(relative).suffix in text_extensions:
                paths.append(relative)
    return sorted(set(paths))


def is_dataless_placeholder(path: Path) -> bool:
    try:
        return bool(getattr(path.stat(), "st_flags", 0) & APPLE_DATALLESS_FLAG)
    except OSError:
        return False


def scan_file_patterns(
    root: Path,
    paths: list[str],
    patterns: list[dict[str, str]],
    *,
    code: str,
    skip_unreadable: bool = False,
) -> list[Finding]:
    findings: list[Finding] = []
    compiled = [
        (item["id"], re.compile(item["pattern"]))
        for item in patterns
    ]
    for raw_path in paths:
        relative = normalize_path(raw_path)
        full_path = root / relative
        if not full_path.is_file():
            findings.append(
                {
                    "code": "security_scan_path_missing",
                    "path": relative,
                    "message": "Configured Stage 16 scan path is missing.",
                }
            )
            continue
        if skip_unreadable and is_dataless_placeholder(full_path):
            continue
        try:
            text = full_path.read_text(encoding="utf-8", errors="ignore")
        except (OSError, TimeoutError):
            if skip_unreadable:
                continue
            raise
        for line_number, line in enumerate(text.splitlines(), start=1):
            for pattern_id, pattern in compiled:
                if pattern.search(line):
                    findings.append(
                        {
                            "code": code,
                            "id": pattern_id,
                            "path": relative,
                            "line": line_number,
                            "message": f"Matched security hardening pattern: {pattern_id}",
                        }
                    )
    return findings


def check_required_snippets(root: Path, requirements: list[dict[str, Any]]) -> list[Finding]:
    findings: list[Finding] = []
    for requirement in requirements:
        relative = normalize_path(requirement["path"])
        full_path = root / relative
        if not full_path.is_file():
            findings.append(
                {
                    "code": "required_security_file_missing",
                    "path": relative,
                    "message": "Required Stage 16 source file is missing.",
                }
            )
            continue
        text = full_path.read_text(encoding="utf-8", errors="ignore")
        for snippet in requirement.get("snippets", []):
            if snippet not in text:
                findings.append(
                    {
                        "code": "required_security_snippet_missing",
                        "path": relative,
                        "snippet": snippet,
                        "message": "Required Stage 16 hardening snippet is missing.",
                    }
                )
    return findings


def run_checks(root: Path, config: dict[str, Any]) -> list[Finding]:
    paths = iter_scan_paths(root, config)
    skip_unreadable = bool(config.get("source_scan", {}).get("skip_unreadable", False))
    findings: list[Finding] = []
    findings.extend(
        scan_file_patterns(
            root,
            paths,
            config.get("secret_patterns", []),
            code="secret_pattern_detected",
            skip_unreadable=skip_unreadable,
        )
    )
    findings.extend(
        scan_file_patterns(
            root,
            paths,
            config.get("banned_response_fragments", []),
            code="banned_response_fragment",
            skip_unreadable=skip_unreadable,
        )
    )
    findings.extend(check_required_snippets(root, config.get("required_source_snippets", [])))
    return findings


def main() -> int:
    parser = argparse.ArgumentParser(description="Run Stage 16 security hardening checks.")
    parser.add_argument("--root", type=Path, default=Path("."))
    parser.add_argument("--config", type=Path, default=Path("security_hardening.yaml"))
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args()

    findings = run_checks(args.root, load_config(args.config))
    if args.json:
        print(json.dumps({"ok": not findings, "findings": findings}, indent=2))
    elif findings:
        print("Stage 16 security hardening failed:")
        for finding in findings:
            location = finding.get("path", "<repo>")
            if finding.get("line"):
                location = f"{location}:{finding['line']}"
            print(f"- {finding['code']} {location}: {finding['message']}")
    else:
        print("Stage 16 security hardening checks passed.")
    return 1 if findings else 0


if __name__ == "__main__":
    raise SystemExit(main())
