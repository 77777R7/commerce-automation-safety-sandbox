#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
from pathlib import Path

import yaml

from commerce_safety.live.schemathesis_fixtures import (
    SchemathesisFixtureValues,
    build_schemathesis_fixture_spec,
)


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Build a Schemathesis-only OpenAPI fixture spec."
    )
    parser.add_argument("--source", required=True, type=Path)
    parser.add_argument("--output", required=True, type=Path)
    parser.add_argument("--fixtures-json", required=True, type=Path)
    args = parser.parse_args()

    source = yaml.safe_load(args.source.read_text(encoding="utf-8"))
    fixture_payload = json.loads(args.fixtures_json.read_text(encoding="utf-8"))
    fixture_spec = build_schemathesis_fixture_spec(
        source,
        SchemathesisFixtureValues(
            sessions=fixture_payload["sessions"],
            feed_id=fixture_payload["feed_id"],
        ),
    )

    args.output.write_text(
        yaml.safe_dump(fixture_spec, sort_keys=False),
        encoding="utf-8",
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
