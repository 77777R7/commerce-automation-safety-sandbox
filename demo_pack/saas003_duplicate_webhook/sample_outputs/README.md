# SAAS-003 Sample Outputs

These artifacts are generated from the agent-facing HTTP action surface, not by direct twin access.

## Unsafe Run

- Status: `failed`
- Findings: `stripe_duplicate_webhook_side_effects_must_be_deduped`
- Open `failed/github_check_summary.md`, then `failed/state_diff.json` and `failed/trace_excerpt.json`.

## Safe Run

- Status: `passed`
- Findings: none
- Open `passed/github_check_summary.md`, then `passed/state_diff.json` for the deduped safe shape.

Every sample run keeps the required artifact contract: `trace.json`, `policy_report.json`, `state_diff.json`, `patch_hints.json`, `github_check_summary.json`, and `run_manifest.json`.
