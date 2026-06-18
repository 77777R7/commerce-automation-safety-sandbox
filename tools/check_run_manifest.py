#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "commerce-safety-sandbox"))

from commerce_safety.artifacts import validate_run_manifest  # noqa: E402


def main() -> int:
    parser = argparse.ArgumentParser(description="Validate Commerce Safety run manifests.")
    parser.add_argument("run_paths", nargs="+", type=Path)
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args()

    results = []
    for run_path in args.run_paths:
        findings = validate_run_manifest(run_path)
        results.append(
            {
                "run_path": str(run_path),
                "ok": not findings,
                "findings": findings,
            }
        )

    ok = all(result["ok"] for result in results)
    if args.json:
        print(json.dumps({"ok": ok, "runs": results}, indent=2))
    elif ok:
        print("Run manifest validation passed.")
    else:
        print("Run manifest validation failed:")
        for result in results:
            for finding in result["findings"]:
                print(
                    f"- {result['run_path']}/{finding.get('path', '<run>')}: "
                    f"{finding['code']} {finding['message']}"
                )
    return 0 if ok else 1


if __name__ == "__main__":
    raise SystemExit(main())

