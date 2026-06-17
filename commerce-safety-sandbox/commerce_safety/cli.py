from __future__ import annotations

import argparse
import importlib.util
import json
import os
import subprocess
import sys
from pathlib import Path

from .engine import run_scenario
from .io import read_json
from .offline_audit import run_offline_audit
from .regressions import save_regression


def resolve_run_path(value: str, runs_dir: Path) -> Path:
    path = Path(value)
    if path.exists():
        return path
    candidate = runs_dir / value
    if candidate.exists():
        return candidate
    raise FileNotFoundError(f"Run not found: {value}")


def repo_root_from_context() -> Path:
    cwd = Path.cwd().resolve()
    if (cwd / "commerce-safety-sandbox" / "commerce_safety").exists():
        return cwd
    return Path(__file__).resolve().parents[2]


def mcp_config_payload(
    *,
    repo_root: Path,
    python_path: str,
    runs_dir: str,
    transport: str,
) -> dict:
    args = [
        "-m",
        "commerce_safety.live.mcp_server",
        "--runs-dir",
        runs_dir,
    ]
    if transport != "stdio":
        args.extend(["--transport", transport])
    return {
        "mcpServers": {
            "commerce-safety": {
                "command": python_path,
                "args": args,
                "env": {
                    "PYTHONPATH": str(repo_root / "commerce-safety-sandbox"),
                },
            }
        }
    }


def mcp_client_config_path(client: str) -> Path:
    if client == "codex":
        return Path.home() / ".config" / "codex" / "mcp.json"
    if client == "claude":
        return Path.home() / ".claude" / "mcp.json"
    raise ValueError(f"Unsupported MCP client: {client}")


def merge_mcp_config(existing: dict, commerce_config: dict) -> dict:
    if not isinstance(existing, dict):
        raise ValueError("MCP config must be a JSON object.")
    existing_servers = existing.get("mcpServers", {})
    if not isinstance(existing_servers, dict):
        raise ValueError("MCP config field 'mcpServers' must be a JSON object.")
    commerce_servers = commerce_config.get("mcpServers", {})
    if not isinstance(commerce_servers, dict):
        raise ValueError("Commerce MCP config field 'mcpServers' must be a JSON object.")

    merged = dict(existing)
    merged["mcpServers"] = {**existing_servers, **commerce_servers}
    return merged


def install_mcp_config(
    commerce_config: dict,
    *,
    config_path: Path,
) -> dict:
    if config_path.exists():
        existing_text = config_path.read_text(encoding="utf-8")
        backup_path = config_path.with_name(f"{config_path.name}.backup")
        backup_path.write_text(existing_text, encoding="utf-8")
        existing = json.loads(existing_text)
    else:
        existing = {}
    merged = merge_mcp_config(existing, commerce_config)
    config_path.parent.mkdir(parents=True, exist_ok=True)
    config_path.write_text(
        json.dumps(merged, indent=2, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )
    return merged


def build_scn002_agent_demo(
    *,
    repo_root: Path,
    python_path: str,
    runs_dir: str,
) -> str:
    config = mcp_config_payload(
        repo_root=repo_root,
        python_path=python_path,
        runs_dir=runs_dir,
        transport="stdio",
    )
    return "\n".join(
        [
            "# Commerce Safety Demo: SCN-002 MCP Agent",
            "",
            "Goal: prove the sandbox catches unsafe retry behavior before production.",
            "",
            "## 1. Check Local Readiness",
            "",
            "```bash",
            "./commerce-safety doctor --mcp-smoke",
            "```",
            "",
            "## 2. MCP Config",
            "",
            "Generate this again any time with:",
            "",
            "```bash",
            f"./commerce-safety mcp-config --python {python_path}",
            "```",
            "",
            "Paste this config into the agent client:",
            "",
            "```json",
            json.dumps(config, indent=2),
            "```",
            "",
            "## 3. Agent Prompt",
            "",
            "Use this prompt file:",
            "",
            "```txt",
            "demo_pack/prompts/scn002_mcp_agent_test.md",
            "```",
            "",
            "## 4. Expected Result",
            "",
            "- Unsafe run fails with `idempotency_required_for_mutating_retries`.",
            "- Unsafe run also fails with `no_duplicate_fulfillment`.",
            "- Safe run passes with zero policy findings.",
            "",
            "## 5. Validation Checklist",
            "",
            "- [ ] Unsafe run fails.",
            "- [ ] Safe run passes.",
            "- [ ] Patch hints mention stable idempotency keys.",
            "- [ ] Patch hints mention checking existing fulfillment after timeout.",
            "- [ ] No real Shopify, Amazon, or customer data was used.",
            "",
        ]
    )


def build_saas001_agent_demo(
    *,
    repo_root: Path,
    python_path: str,
    runs_dir: str,
) -> str:
    config = mcp_config_payload(
        repo_root=repo_root,
        python_path=python_path,
        runs_dir=runs_dir,
        transport="stdio",
    )
    return "\n".join(
        [
            "# Agent Integration Safety Demo: SAAS-001",
            "",
            "Goal: crash-test a billing upgrade agent before it touches Stripe, Slack, or GitHub.",
            "",
            "## 1. Five-Minute Story",
            "",
            "SAAS-001 injects a failed Stripe initial payment and a Slack private-channel delivery failure. The unsafe agent still publishes downstream success state. The safe agent keeps the workflow in billing recovery and writes review artifacts.",
            "",
            "## 2. Local Readiness",
            "",
            "```bash",
            "./commerce-safety doctor",
            "```",
            "",
            "## 3. MCP Config",
            "",
            "Generate this again any time with:",
            "",
            "```bash",
            f"./commerce-safety mcp-config --python {python_path}",
            "```",
            "",
            "Paste this config into the agent client:",
            "",
            "```json",
            json.dumps(config, indent=2),
            "```",
            "",
            "## 4. Agent Prompt",
            "",
            "Use this prompt file:",
            "",
            "```txt",
            "demo_pack/prompts/saas001_mcp_agent_test.md",
            "```",
            "",
            "## 5. HTTP Path",
            "",
            "If the tester does not use MCP, start the HTTP Twin API and follow:",
            "",
            "```txt",
            "demo_pack/saas_agent_validation/http_curl_bad_good.md",
            "```",
            "",
            "## 6. Expected Unsafe Findings",
            "",
            "- `no_success_state_after_failed_payment`",
            "- `billing_failure_must_trigger_alert`",
            "- `slack_permission_failure_must_not_be_silent`",
            "- `github_check_must_match_policy_status`",
            "",
            "## 7. Expected Safe Result",
            "",
            "- Billing failure alert is delivered to a reachable fallback channel.",
            "- GitHub issue/comment/check run keep the workflow in action-required state.",
            "- Policy report has zero findings.",
            "",
            "## 8. Reader Materials",
            "",
            "- `demo_pack/saas_agent_validation/README.md`",
            "- `demo_pack/saas_agent_validation/demo_walkthrough.md`",
            "- `demo_pack/saas_agent_validation/investor_demo_script.md`",
            "- `demo_pack/saas_agent_validation/sample_outputs/`",
            "",
            "No production Stripe keys, Slack tokens, GitHub installation tokens, customer PII, real refunds, or real PR writes are used.",
            "",
        ]
    )


def build_init_guide(path: str) -> str:
    guides = {
        "saas-mcp-agent": [
            "# SaaS MCP Agent Path",
            "",
            "Use this for Codex, Claude, Cursor, or another MCP client testing the Stripe/Slack/GitHub hero demo.",
            "",
            "1. Run `./commerce-safety doctor`.",
            "2. Run `./commerce-safety mcp-config --python \"$PWD/.venv/bin/python\"`.",
            "3. Add the config to the MCP client.",
            "4. Paste `demo_pack/prompts/saas001_mcp_agent_test.md` into the agent.",
            "5. Compare `demo_pack/saas_agent_validation/sample_outputs/failed` with `sample_outputs/passed`.",
        ],
        "saas-http-workflow": [
            "# SaaS HTTP Workflow Path",
            "",
            "Use this when the tester has a custom agent, workflow runner, or simple curl setup.",
            "",
            "1. Run `PYTHONPATH=\"$PWD/commerce-safety-sandbox\" ./commerce-safety live serve`.",
            "2. Create a session with `POST /sessions` and `scenario_id=SAAS-001`.",
            "3. Call the Stripe, Slack, and GitHub twin actions under `/sessions/{session_id}/twin/...`.",
            "4. Complete the session and inspect policy findings.",
            "5. Follow `demo_pack/saas_agent_validation/http_curl_bad_good.md`.",
        ],
        "mcp-agent": [
            "# MCP Agent Path",
            "",
            "Use this when the tester has Codex, Claude, Cursor, or another MCP client.",
            "",
            "1. Run `./commerce-safety doctor --mcp-smoke`.",
            "2. Run `./commerce-safety mcp-config --python \"$PWD/.venv/bin/python\"`.",
            "3. Add the config to the MCP client.",
            "4. Paste `demo_pack/prompts/scn002_mcp_agent_test.md` into the agent.",
        ],
        "http-workflow": [
            "# HTTP Workflow Path",
            "",
            "Use this when the tester has a custom script, workflow runner, or non-MCP agent.",
            "",
            "1. Run `PYTHONPATH=\"$PWD/commerce-safety-sandbox\" ./commerce-safety live serve`.",
            "2. Create a session with `POST /sessions`.",
            "3. Call the Twin API actions under `/sessions/{session_id}/twin/...`.",
            "4. Complete the session and inspect policy findings.",
            "5. See `docs/HTTP_N8N_QUICKSTART.md` for curl examples.",
        ],
        "n8n": [
            "# n8n Path",
            "",
            "Use this when the tester thinks in workflow nodes instead of code.",
            "",
            "1. Start the local HTTP Twin API.",
            "2. Add HTTP Request nodes for session, task, fulfillment, completion.",
            "3. Run the unsafe branch once, then the safe branch.",
            "4. Compare policy report and patch hints.",
            "5. See `docs/HTTP_N8N_QUICKSTART.md` for node mapping.",
        ],
    }
    return "\n".join(guides[path]) + "\n"


def check_mark(ok: bool) -> str:
    return "OK" if ok else "FAIL"


def python_supports_agent_interfaces(version: tuple[int, int, int] | tuple[int, int]) -> bool:
    return version >= (3, 10)


def require_agent_interface_python(command_name: str) -> None:
    if python_supports_agent_interfaces(tuple(sys.version_info[:3])):
        return
    raise RuntimeError(
        f"{command_name} requires Python 3.10+ because it runs MCP/API hardening "
        f"dependencies. Current Python: {sys.version.split()[0]} at {sys.executable}."
    )


def print_status(
    status: str,
    label: str,
    detail: str = "",
    fix: str = "",
    hint_label: str = "Fix",
) -> None:
    print(f"[{status}] {label}")
    if detail:
        print(f"     {detail}")
    if fix:
        print(f"     {hint_label}: {fix}")


def print_check(ok: bool, label: str, detail: str = "", fix: str = "") -> None:
    print_status(check_mark(ok), label, detail, fix if not ok else "")


def print_warn(label: str, detail: str = "", fix: str = "") -> None:
    print_status("WARN", label, detail, fix, "Tip")


def add_runs_dir_argument(command_parser: argparse.ArgumentParser) -> None:
    command_parser.add_argument(
        "--runs-dir",
        default=argparse.SUPPRESS,
        help="Directory where run artifacts are written or read.",
    )


def cmd_run(args: argparse.Namespace) -> int:
    result = run_scenario(
        scenario_path=Path(args.scenario),
        runner_name=args.runner,
        runs_dir=Path(args.runs_dir),
    )
    print(f"Run ID: {result['run_id']}")
    print(f"Status: {result['status']}")
    print(f"Artifacts: {result['run_path']}")
    if result["findings"]:
        print("Findings:")
        for finding in result["findings"]:
            print(f"- {finding['policy_id']} ({finding['severity']})")
    else:
        print("Findings: none")
    return 1 if result["findings"] else 0


def cmd_replay(args: argparse.Namespace) -> int:
    run_path = resolve_run_path(args.run, Path(args.runs_dir))
    trace = read_json(run_path / "trace.json")
    print(f"Replay from trace.json: {trace['run_id']}")
    print(f"Scenario: {trace['scenario_name']}")
    print(f"Runner: {trace['runner']}")
    print(f"Status: {trace['status']}")
    print("")
    for event in trace["timeline"]:
        print(f"Step {event['step']}: {event['message']}")
    return 0


def cmd_report(args: argparse.Namespace) -> int:
    run_path = resolve_run_path(args.run, Path(args.runs_dir))
    report_path = run_path / "report.md"
    if args.format != "markdown":
        raise ValueError("Only markdown format is supported in the MVP.")
    print(report_path.read_text(encoding="utf-8"))
    return 0


def cmd_save_regression(args: argparse.Namespace) -> int:
    run_path = resolve_run_path(args.run, Path(args.runs_dir))
    try:
        result = save_regression(
            run_path=run_path,
            name=args.name,
            regressions_dir=Path(args.regressions_dir),
            scenario_dir=Path(args.scenario_dir),
        )
    except (FileNotFoundError, ValueError) as error:
        print(f"Error: {error}", file=sys.stderr)
        return 1
    print(f"Regression saved: {result['path']}")
    print(f"Name: {result['name']}")
    print(f"Policy findings: {len(result['findings'])}")
    print("Artifacts:")
    for artifact in result["artifacts"]:
        print(f"- {artifact}")
    return 0


def cmd_offline_audit(args: argparse.Namespace) -> int:
    try:
        result = run_offline_audit(
            orders_path=Path(args.orders),
            inventory_path=Path(args.inventory),
            fulfillments_path=Path(args.fulfillments),
            refunds_path=Path(args.refunds),
            output_dir=Path(args.output_dir),
            mapping_path=Path(args.mapping) if args.mapping else None,
            sheet_names={
                "orders": args.orders_sheet,
                "inventory": args.inventory_sheet,
                "fulfillments": args.fulfillments_sheet,
                "refunds": args.refunds_sheet,
            },
        )
    except (FileNotFoundError, ValueError) as error:
        print(f"Error: {error}", file=sys.stderr)
        return 1
    print(f"Audit ID: {result['audit_id']}")
    print(f"Status: {result['status']}")
    print(f"Risk score: {result['risk_score']}/100")
    print(f"Artifacts: {result['audit_path']}")
    if result["findings"]:
        print("Findings:")
        for finding in result["findings"]:
            print(f"- {finding['policy_id']} ({finding['severity']})")
    else:
        print("Findings: none")
    return 1 if result["findings"] else 0


def cmd_doctor(args: argparse.Namespace) -> int:
    repo_root = repo_root_from_context()
    python_version = sys.version_info
    checks: list[bool] = []

    print("Commerce Safety Doctor")
    print("======================")
    print("This checks local readiness for the MCP/agent demo.")
    print("No Shopify, Amazon, or customer data is used.")
    print("")

    python_ok = python_version >= (3, 10)
    checks.append(python_ok)
    print_check(
        python_ok,
        "Python 3.10+",
        f"Current: {sys.executable} ({python_version.major}.{python_version.minor}.{python_version.micro})",
        "Use Python 3.10+ or create a venv, then run python -m pip install -r requirements.txt",
    )

    requirements_ok = (repo_root / "requirements.txt").exists()
    checks.append(requirements_ok)
    print_check(
        requirements_ok,
        "requirements.txt found",
        str(repo_root / "requirements.txt"),
        "Run doctor from the repository root or pass through the repo wrapper ./commerce-safety",
    )

    package_ok = (repo_root / "commerce-safety-sandbox" / "commerce_safety").exists()
    checks.append(package_ok)
    print_check(
        package_ok,
        "commerce_safety package found",
        str(repo_root / "commerce-safety-sandbox" / "commerce_safety"),
        "Check that commerce-safety-sandbox/commerce_safety exists in this repo.",
    )

    scenario = repo_root / "commerce-safety-sandbox" / "scenarios" / "SCN-002_timeout_after_commit_retry.yaml"
    scenario_ok = scenario.exists()
    checks.append(scenario_ok)
    print_check(
        scenario_ok,
        "SCN-002 demo scenario found",
        str(scenario),
        "Restore commerce-safety-sandbox/scenarios/SCN-002_timeout_after_commit_retry.yaml",
    )

    mcp_ok = importlib.util.find_spec("mcp") is not None
    checks.append(mcp_ok)
    print_check(
        mcp_ok,
        "MCP SDK installed",
        "Python import: mcp",
        "python -m pip install -r requirements.txt",
    )

    pythonpath = os.environ.get("PYTHONPATH", "")
    expected_path = str(repo_root / "commerce-safety-sandbox")
    pythonpath_ok = expected_path in pythonpath.split(os.pathsep)
    if pythonpath_ok:
        print_check(
            True,
            "PYTHONPATH already points to commerce-safety-sandbox",
            expected_path,
        )
    else:
        print_warn(
            "PYTHONPATH not set for external MCP clients",
            "This is fine for ./commerce-safety. Your MCP client config must set it.",
            f"Use ./commerce-safety mcp-config --python {sys.executable}",
        )

    if args.mcp_smoke:
        print("")
        print("Running MCP SCN-002 smoke...")
        smoke = repo_root / "tools" / "smoke_stage9_real_mcp.sh"
        smoke_ok = smoke.exists()
        if smoke_ok:
            env = os.environ.copy()
            env["PYTHON"] = sys.executable
            completed = subprocess.run(
                [str(smoke)],
                cwd=repo_root,
                env=env,
                text=True,
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                check=False,
            )
            smoke_ok = completed.returncode == 0
            if args.verbose or not smoke_ok:
                print(completed.stdout.rstrip())
        checks.append(smoke_ok)
        print_check(
            smoke_ok,
            "MCP unsafe/safe SCN-002 smoke",
            "Unsafe path should fail; safe path should pass.",
            "Install dependencies and rerun: python -m pip install -r requirements.txt",
        )

    print("")
    if all(checks):
        print("Ready to connect an agent.")
        print("Next:")
        print(f"  ./commerce-safety mcp-config --python {sys.executable}")
        print("  Use demo_pack/prompts/scn002_mcp_agent_test.md as the agent prompt.")
        return 0

    print("Not ready yet. Fix the FAIL items above, then rerun:")
    print("  ./commerce-safety doctor --mcp-smoke")
    return 1


def cmd_mcp_config(args: argparse.Namespace) -> int:
    repo_root = Path(args.repo_root).expanduser().resolve() if args.repo_root else repo_root_from_context()
    if args.python:
        python_candidate = Path(args.python).expanduser()
        if not python_candidate.is_absolute():
            python_candidate = Path.cwd() / python_candidate
        python_path = str(python_candidate.absolute())
    else:
        python_path = sys.executable
    config = mcp_config_payload(
        repo_root=repo_root,
        python_path=python_path,
        runs_dir=args.runs_dir,
        transport=args.transport,
    )
    if args.install:
        config_path = (
            Path(args.config_path).expanduser()
            if args.config_path
            else mcp_client_config_path(args.install)
        )
        installed = install_mcp_config(config, config_path=config_path)
        print(f"Installed Commerce Safety MCP server into: {config_path}")
        print("Configured servers:")
        for server_name in sorted(installed.get("mcpServers", {})):
            print(f"- {server_name}")
        return 0

    if args.format == "json":
        print(json.dumps(config, indent=2))
        return 0

    print("Commerce Safety MCP config")
    print("==========================")
    print("Paste this into your MCP client config.")
    print("")
    print(json.dumps(config, indent=2))
    print("")
    print("After adding it, paste this prompt into your agent:")
    print("  demo_pack/prompts/scn002_mcp_agent_test.md")
    print("")
    print("No real Shopify, Amazon, or customer data is required.")
    return 0


def cmd_demo_scn002_agent(args: argparse.Namespace) -> int:
    repo_root = Path(args.repo_root).expanduser().resolve() if args.repo_root else repo_root_from_context()
    if args.python:
        python_candidate = Path(args.python).expanduser()
        if not python_candidate.is_absolute():
            python_candidate = Path.cwd() / python_candidate
        python_path = str(python_candidate.absolute())
    else:
        python_path = sys.executable
    print(
        build_scn002_agent_demo(
            repo_root=repo_root,
            python_path=python_path,
            runs_dir=args.runs_dir,
        )
    )
    return 0


def cmd_demo_saas001_agent(args: argparse.Namespace) -> int:
    repo_root = Path(args.repo_root).expanduser().resolve() if args.repo_root else repo_root_from_context()
    if args.python:
        python_candidate = Path(args.python).expanduser()
        if not python_candidate.is_absolute():
            python_candidate = Path.cwd() / python_candidate
        python_path = str(python_candidate.absolute())
    else:
        python_path = sys.executable
    print(
        build_saas001_agent_demo(
            repo_root=repo_root,
            python_path=python_path,
            runs_dir=args.runs_dir,
        )
    )
    return 0


def cmd_init(args: argparse.Namespace) -> int:
    selected_path = args.path
    if not selected_path and sys.stdin.isatty():
        print("Choose a tester path:")
        print("1. mcp-agent")
        print("2. http-workflow")
        print("3. n8n")
        choice = input("Path [1]: ").strip() or "1"
        selected_path = {
            "1": "mcp-agent",
            "2": "http-workflow",
            "3": "n8n",
        }.get(choice, "mcp-agent")
    selected_path = selected_path or "mcp-agent"

    print("Commerce Safety Init")
    print("====================")
    print("No production store or customer data is required.")
    print("")
    print(build_init_guide(selected_path))
    print("Recommended first command:")
    print("  ./commerce-safety doctor --mcp-smoke")
    return 0


def cmd_live_serve(args: argparse.Namespace) -> int:
    from .live.http_api import serve_live_http
    from .live.security import LiveSecurityError

    try:
        return serve_live_http(
            host=args.host,
            port=args.port,
            runs_dir=Path(args.runs_dir),
            api_token=args.api_token,
        )
    except LiveSecurityError as error:
        print(str(error), file=sys.stderr)
        return 2


def cmd_live_mcp(args: argparse.Namespace) -> int:
    from .live.mcp_server import main as mcp_main

    return mcp_main(
        [
            "--runs-dir",
            args.runs_dir,
            "--transport",
            args.transport,
        ]
    )


def _print_gate_result(result: dict, *, as_json: bool) -> None:
    if as_json:
        print(json.dumps(result, indent=2, ensure_ascii=False))
        return
    print(f"Status: {result['status']}")
    print(f"Artifacts: {result['run_path']}")
    print(f"Actions replayed: {result['actions_replayed']}")
    if result["findings"]:
        print("Findings:")
        for finding in result["findings"]:
            print(f"- {finding['policy_id']} ({finding['severity']})")
    else:
        print("Findings: none")


def _run_action_log_from_args(args: argparse.Namespace) -> dict:
    from .live.action_log import run_action_log

    return run_action_log(
        scenario_path=Path(args.scenario),
        action_log_path=Path(args.action_log),
        runs_dir=Path(args.runs_dir),
        runner_name=args.runner_name,
    )


def cmd_live_from_action_log(args: argparse.Namespace) -> int:
    try:
        result = _run_action_log_from_args(args)
    except (FileNotFoundError, KeyError, ValueError) as error:
        print(f"Error: {error}", file=sys.stderr)
        return 1
    _print_gate_result(result, as_json=args.json)
    return 1 if result["findings"] else 0


def cmd_gate(args: argparse.Namespace) -> int:
    try:
        result = _run_action_log_from_args(args)
    except (FileNotFoundError, KeyError, ValueError) as error:
        print(f"Error: {error}", file=sys.stderr)
        return 1
    _print_gate_result(result, as_json=args.json)
    return 1 if result["findings"] else 0


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="commerce-safety",
        description="Commerce Automation Safety Sandbox MVP CLI.",
    )
    parser.add_argument(
        "--runs-dir",
        default="runs",
        help="Directory where run artifacts are written or read.",
    )
    subparsers = parser.add_subparsers(dest="command", required=True)

    doctor_parser = subparsers.add_parser(
        "doctor",
        help="Check local readiness for external MCP/agent demos.",
    )
    doctor_parser.add_argument(
        "--mcp-smoke",
        action="store_true",
        help="Run the SCN-002 real MCP unsafe/safe smoke after basic checks.",
    )
    doctor_parser.add_argument(
        "--verbose",
        action="store_true",
        help="Print smoke output even when it succeeds.",
    )
    doctor_parser.set_defaults(func=cmd_doctor)

    mcp_config_parser = subparsers.add_parser(
        "mcp-config",
        help="Print a ready-to-paste MCP client config for this repo.",
    )
    mcp_config_parser.add_argument(
        "--repo-root",
        help="Repository root. Defaults to the current repo.",
    )
    mcp_config_parser.add_argument(
        "--python",
        help="Python executable for the MCP server. Defaults to the current Python.",
    )
    add_runs_dir_argument(mcp_config_parser)
    mcp_config_parser.add_argument(
        "--transport",
        default="stdio",
        choices=["stdio", "streamable-http"],
        help="MCP transport. Local agent clients usually use stdio.",
    )
    mcp_config_parser.add_argument(
        "--format",
        default="pretty",
        choices=["pretty", "json"],
        help="Output format.",
    )
    mcp_config_parser.add_argument(
        "--install",
        choices=["codex", "claude"],
        help="Merge the generated server into a local MCP client config.",
    )
    mcp_config_parser.add_argument(
        "--config-path",
        help="Override the MCP client config path used by --install.",
    )
    mcp_config_parser.set_defaults(func=cmd_mcp_config)

    demo_parser = subparsers.add_parser(
        "demo",
        help="Print guided demo packs for external testers.",
    )
    demo_subparsers = demo_parser.add_subparsers(
        dest="demo_command",
        required=True,
    )
    scn002_demo_parser = demo_subparsers.add_parser(
        "scn002-agent",
        help="Print the SCN-002 MCP agent demo checklist.",
    )
    scn002_demo_parser.add_argument(
        "--repo-root",
        help="Repository root. Defaults to the current repo.",
    )
    scn002_demo_parser.add_argument(
        "--python",
        help="Python executable for the MCP server. Defaults to the current Python.",
    )
    add_runs_dir_argument(scn002_demo_parser)
    scn002_demo_parser.set_defaults(func=cmd_demo_scn002_agent)

    saas001_demo_parser = demo_subparsers.add_parser(
        "saas001-agent",
        help="Print the SAAS-001 Stripe/Slack/GitHub agent demo checklist.",
    )
    saas001_demo_parser.add_argument(
        "--repo-root",
        help="Repository root. Defaults to the current repo.",
    )
    saas001_demo_parser.add_argument(
        "--python",
        help="Python executable for the MCP server. Defaults to the current Python.",
    )
    add_runs_dir_argument(saas001_demo_parser)
    saas001_demo_parser.set_defaults(func=cmd_demo_saas001_agent)

    for command_name in ("init", "wizard"):
        init_parser = subparsers.add_parser(
            command_name,
            help="Guide an external tester through the right setup path.",
        )
        init_parser.add_argument(
            "--path",
            choices=[
                "saas-mcp-agent",
                "saas-http-workflow",
                "mcp-agent",
                "http-workflow",
                "n8n",
            ],
            help="Tester path to show. Defaults to mcp-agent in non-interactive shells.",
        )
        init_parser.set_defaults(func=cmd_init)

    run_parser = subparsers.add_parser("run", help="Run one scenario.")
    run_parser.add_argument("scenario", help="Path to scenario YAML.")
    add_runs_dir_argument(run_parser)
    run_parser.add_argument(
        "--runner",
        choices=["bad_runner", "good_runner"],
        required=True,
        help="Automation runner to test.",
    )
    run_parser.set_defaults(func=cmd_run)

    replay_parser = subparsers.add_parser(
        "replay",
        help="Replay a run from trace.json without rerunning the scenario.",
    )
    replay_parser.add_argument("run", help="Run directory or run id.")
    add_runs_dir_argument(replay_parser)
    replay_parser.set_defaults(func=cmd_replay)

    report_parser = subparsers.add_parser("report", help="Print a run report.")
    report_parser.add_argument("run", help="Run directory or run id.")
    add_runs_dir_argument(report_parser)
    report_parser.add_argument(
        "--format",
        default="markdown",
        choices=["markdown"],
        help="Report format.",
    )
    report_parser.set_defaults(func=cmd_report)

    save_parser = subparsers.add_parser(
        "save-regression",
        help="Save a failed run as a reusable regression scenario.",
    )
    save_parser.add_argument("run", help="Run directory or run id.")
    save_parser.add_argument(
        "--name",
        required=True,
        help="Human-readable regression name; used to create a stable slug.",
    )
    add_runs_dir_argument(save_parser)
    save_parser.add_argument(
        "--regressions-dir",
        default="regressions",
        help="Directory where regression scenarios are written.",
    )
    save_parser.add_argument(
        "--scenario-dir",
        default="commerce-safety-sandbox/scenarios",
        help="Fallback directory for source scenarios when a run lacks scenario.yaml.",
    )
    save_parser.set_defaults(func=cmd_save_regression)

    audit_parser = subparsers.add_parser(
        "offline-audit",
        help="Run a CSV-first Offline Fulfillment Automation Audit.",
    )
    audit_parser.add_argument(
        "--orders", required=True, help="Path to orders CSV or XLSX file."
    )
    audit_parser.add_argument(
        "--inventory", required=True, help="Path to inventory CSV or XLSX file."
    )
    audit_parser.add_argument(
        "--fulfillments",
        required=True,
        help="Path to fulfillments CSV or XLSX file.",
    )
    audit_parser.add_argument(
        "--refunds", required=True, help="Path to refunds CSV or XLSX file."
    )
    audit_parser.add_argument(
        "--mapping",
        help="Optional YAML mapping from canonical fields to source table headers.",
    )
    audit_parser.add_argument(
        "--orders-sheet",
        help="Worksheet name when --orders points to an .xlsx workbook.",
    )
    audit_parser.add_argument(
        "--inventory-sheet",
        help="Worksheet name when --inventory points to an .xlsx workbook.",
    )
    audit_parser.add_argument(
        "--fulfillments-sheet",
        help="Worksheet name when --fulfillments points to an .xlsx workbook.",
    )
    audit_parser.add_argument(
        "--refunds-sheet",
        help="Worksheet name when --refunds points to an .xlsx workbook.",
    )
    audit_parser.add_argument(
        "--output-dir",
        default="offline_audits",
        help="Directory where offline audit artifacts are written.",
    )
    add_runs_dir_argument(audit_parser)
    audit_parser.set_defaults(func=cmd_offline_audit)

    live_parser = subparsers.add_parser(
        "live",
        help="Run Live Agent Sandbox commands.",
    )
    live_subparsers = live_parser.add_subparsers(
        dest="live_command",
        required=True,
    )
    serve_parser = live_subparsers.add_parser(
        "serve",
        help="Start the local HTTP Twin API server.",
    )
    serve_parser.add_argument(
        "--host",
        default="127.0.0.1",
        help="Host interface for the local live server.",
    )
    serve_parser.add_argument(
        "--port",
        type=int,
        default=8765,
        help="Port for the local live server.",
    )
    serve_parser.add_argument(
        "--api-token",
        help=(
            "Optional local auth token. When set, requests must include "
            "Authorization: Bearer <token> or X-Commerce-Safety-Token."
        ),
    )
    add_runs_dir_argument(serve_parser)
    serve_parser.set_defaults(func=cmd_live_serve)

    mcp_parser = live_subparsers.add_parser(
        "mcp",
        help="Start the real MCP server using modelcontextprotocol/python-sdk.",
    )
    mcp_parser.add_argument(
        "--transport",
        default="stdio",
        choices=["stdio", "streamable-http"],
        help="MCP transport to run.",
    )
    add_runs_dir_argument(mcp_parser)
    mcp_parser.set_defaults(func=cmd_live_mcp)

    action_log_parser = live_subparsers.add_parser(
        "from-action-log",
        help="Replay a JSONL action log into a live session.",
    )
    action_log_parser.add_argument("--scenario", required=True, help="Scenario YAML path.")
    action_log_parser.add_argument("--action-log", required=True, help="JSONL action log path.")
    action_log_parser.add_argument(
        "--runner-name",
        default="logged_agent",
        help="Runner name to record in generated artifacts.",
    )
    add_runs_dir_argument(action_log_parser)
    action_log_parser.add_argument(
        "--json",
        action="store_true",
        help="Print machine-readable JSON output.",
    )
    action_log_parser.set_defaults(func=cmd_live_from_action_log)

    gate_parser = subparsers.add_parser(
        "gate",
        help="Run an action log as a CI-style commerce safety gate.",
    )
    gate_parser.add_argument("--scenario", required=True, help="Scenario YAML path.")
    gate_parser.add_argument("--action-log", required=True, help="JSONL action log path.")
    gate_parser.add_argument(
        "--runner-name",
        default="logged_agent",
        help="Runner name to record in generated artifacts.",
    )
    add_runs_dir_argument(gate_parser)
    gate_parser.add_argument(
        "--json",
        action="store_true",
        help="Print machine-readable JSON output.",
    )
    gate_parser.set_defaults(func=cmd_gate)
    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    return args.func(args)
