#!/usr/bin/env node

import { copyFile, mkdir, rm } from "node:fs/promises";
import path from "node:path";
import { fileURLToPath } from "node:url";

const __dirname = path.dirname(fileURLToPath(import.meta.url));
const siteRoot = path.resolve(__dirname, "..");
const repoRoot = path.resolve(siteRoot, "..");
const sourceRoot = path.join(repoRoot, "demo_pack/saas003_duplicate_webhook");
const outputRoot = path.join(siteRoot, "public/artifacts/saas-003");

const files = [
  ["external_agent_prompt.md", "external_agent_prompt.md"],
  ["runbook.md", "runbook.md"],
  ["investor_demo_script.md", "investor_demo_script.md"],
  ["design_partner_walkthrough.md", "design_partner_walkthrough.md"],
  ["sample_outputs/summary.json", "summary.json"],
  ["sample_outputs/failed/github_check_summary.md", "failed/github_check_summary.md"],
  ["sample_outputs/failed/patch_hints.md", "failed/patch_hints.md"],
  ["sample_outputs/failed/policy_report.json", "failed/policy_report.json"],
  ["sample_outputs/failed/state_diff.json", "failed/state_diff.json"],
  ["sample_outputs/failed/trace_excerpt.json", "failed/trace_excerpt.json"],
  ["sample_outputs/failed/run_manifest.json", "failed/run_manifest.json"],
  ["sample_outputs/failed/scenario.yaml", "failed/scenario.yaml"],
  ["sample_outputs/passed/github_check_summary.md", "passed/github_check_summary.md"],
  ["sample_outputs/passed/patch_hints.md", "passed/patch_hints.md"],
  ["sample_outputs/passed/policy_report.json", "passed/policy_report.json"],
  ["sample_outputs/passed/state_diff.json", "passed/state_diff.json"],
  ["sample_outputs/passed/trace_excerpt.json", "passed/trace_excerpt.json"],
  ["sample_outputs/passed/run_manifest.json", "passed/run_manifest.json"],
];

await rm(outputRoot, { force: true, recursive: true });

for (const [source, destination] of files) {
  const sourcePath = path.join(sourceRoot, source);
  const destinationPath = path.join(outputRoot, destination);
  await mkdir(path.dirname(destinationPath), { recursive: true });
  await copyFile(sourcePath, destinationPath);
}

console.log(`Synced ${files.length} SAAS-003 artifacts to ${path.relative(siteRoot, outputRoot)}`);
