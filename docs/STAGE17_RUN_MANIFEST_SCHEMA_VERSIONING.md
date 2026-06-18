# Stage 17: Run Manifest + Artifact Schema Versioning

Stage 17 makes Commerce Safety run outputs stable enough for CI systems,
external agents, and future hosted sessions to consume without guessing artifact
shape.

## Contract

Every completed run writes:

```txt
run_manifest.json
```

The manifest contains:

- `schema_version`: `commerce_safety.run_manifest.v1`
- `artifact_schema_version`: `commerce_safety.artifacts.v1`
- run identity: `run_id`, optional `session_id`, `scenario_id`, `runner`, status
- an artifact inventory with relative path, artifact type, schema id, content
  type, byte size, and SHA-256 hash

Versioned JSON artifacts:

- `trace.json`: `commerce_safety.trace.v1`
- `policy_report.json`: `commerce_safety.policy_report.v1`
- `state_diff.json`: `commerce_safety.state_diff.v1`
- `patch_hints.json`: `commerce_safety.patch_hints.v1`

Markdown artifacts are listed in the manifest with their own schema ids and
hashes, but do not carry embedded JSON `schema_version` fields.

## Why This Matters

Before Stage 17, a client could see that files existed, but could not know which
artifact contract it was reading or whether a generated artifact had been
modified after completion.

After Stage 17:

- CI can validate artifact integrity.
- Codex/Claude can check schema ids before reading policy reports or patch
  hints.
- Demo packs and future hosted sessions can evolve artifact formats without
  silently breaking older clients.
- A tampered artifact is detected by manifest hash validation.

## Gate

Run:

```bash
PYTHON=python3.12 ./tools/smoke_stage17_run_manifest.sh
```

The full V3.5 gate includes Stage 17:

```bash
PYTHON=python3.12 ./tools/smoke_v35.sh
```

## Non-Goals

- No JSON Schema runtime validator dependency.
- No hosted artifact registry.
- No artifact migration engine.
- No change to the core `Permissive Twin + Policy Check` behavior.

