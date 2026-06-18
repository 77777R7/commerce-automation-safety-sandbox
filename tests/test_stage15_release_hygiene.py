from __future__ import annotations

import importlib.util
from pathlib import Path

import yaml


ROOT = Path(__file__).resolve().parents[1]
CONFIG_PATH = ROOT / "release_hygiene.yaml"
CI_PATH = ROOT / ".github/workflows/v35-ci.yml"
CHECKER_PATH = ROOT / "tools/check_release_hygiene.py"


def _load_checker():
    spec = importlib.util.spec_from_file_location("check_release_hygiene", CHECKER_PATH)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_stage15_release_hygiene_artifacts_exist() -> None:
    assert CONFIG_PATH.exists()
    assert CHECKER_PATH.exists()
    assert (ROOT / "tools/smoke_stage15_release_hygiene.sh").exists()
    assert (ROOT / "docs/STAGE15_RELEASE_HYGIENE_CI_GATE.md").exists()
    assert CI_PATH.exists()


def test_release_hygiene_config_defines_source_and_generated_split() -> None:
    config = yaml.safe_load(CONFIG_PATH.read_text(encoding="utf-8"))

    source_prefixes = set(config["source_pr"]["allowed_prefixes"])
    generated_prefixes = set(config["generated_artifacts"]["prefixes"])

    assert "commerce-safety-sandbox/commerce_safety/" in source_prefixes
    assert "examples/" in source_prefixes
    assert "tests/" in source_prefixes
    assert ".github/workflows/" in source_prefixes
    assert "demo_pack/" in generated_prefixes
    assert "demo_viewer/" in generated_prefixes
    assert not source_prefixes & generated_prefixes
    assert "/Users/" in config["banned_local_path_fragments"]
    assert "/private/var/folders/" in config["banned_local_path_fragments"]
    assert config["local_path_scan"]["repo_wide"] is True


def test_release_hygiene_checker_rejects_generated_artifact_in_source_pr() -> None:
    checker = _load_checker()
    config = checker.load_config(CONFIG_PATH)

    findings = checker.check_source_pr_paths(
        ["demo_pack/SCN-002_timeout_after_commit_retry/bad/report.md"],
        config,
    )

    assert findings
    assert findings[0]["code"] == "generated_artifact_in_source_pr"


def test_release_hygiene_checker_detects_local_paths(tmp_path: Path) -> None:
    checker = _load_checker()
    config = checker.load_config(CONFIG_PATH)
    source_file = tmp_path / "docs" / "note.md"
    source_file.parent.mkdir()
    source_file.write_text("bad path: /Users/howard07/private.txt\n", encoding="utf-8")

    findings = checker.scan_banned_local_paths(
        tmp_path,
        config,
        candidate_paths=["docs/note.md"],
    )

    assert findings
    assert findings[0]["code"] == "banned_local_path"


def test_ci_workflow_runs_release_hygiene_and_v35_gates() -> None:
    workflow = yaml.safe_load(CI_PATH.read_text(encoding="utf-8"))
    all_run_blocks = "\n".join(
        step.get("run", "")
        for job in workflow["jobs"].values()
        for step in job.get("steps", [])
    )

    assert "tools/smoke_stage15_release_hygiene.sh" in all_run_blocks
    assert "python -m pytest" in all_run_blocks
    assert "tools/smoke_stage9_api_hardening.sh" in all_run_blocks
    assert "tools/smoke_stage11_openapi_contract.sh" in all_run_blocks
    assert "tools/smoke_stage10_mcp_p0_all.sh" in all_run_blocks
    assert "tools/smoke_stage10_http_p0_all.sh" in all_run_blocks
    assert "tools/smoke_stage12_shopify_skin_v0.sh" in all_run_blocks
    assert "tools/smoke_stage13_amazon_skin_v0.sh" in all_run_blocks
    assert "tools/smoke_stage13_amazon_mcp_v0.sh" in all_run_blocks
    assert "tools/smoke_stage18_agent_examples.sh" in all_run_blocks
    assert "--source-pr-paths" in all_run_blocks


def test_requirements_are_pinned_for_ci_repeatability() -> None:
    requirement_lines = [
        line.strip()
        for line in (ROOT / "requirements.txt").read_text(encoding="utf-8").splitlines()
        if line.strip() and not line.startswith("#")
    ]

    assert requirement_lines
    assert all("==" in line for line in requirement_lines)
    assert any(line.startswith("schemathesis==") for line in requirement_lines)
    assert any(line.startswith("mcp==") for line in requirement_lines)
