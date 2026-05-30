from __future__ import annotations

import argparse
import json
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


def cmd_live_serve(args: argparse.Namespace) -> int:
    from .live.http_api import serve_live_http

    return serve_live_http(
        host=args.host,
        port=args.port,
        runs_dir=Path(args.runs_dir),
    )


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

    run_parser = subparsers.add_parser("run", help="Run one scenario.")
    run_parser.add_argument("scenario", help="Path to scenario YAML.")
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
    replay_parser.set_defaults(func=cmd_replay)

    report_parser = subparsers.add_parser("report", help="Print a run report.")
    report_parser.add_argument("run", help="Run directory or run id.")
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
