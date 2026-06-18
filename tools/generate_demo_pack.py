from __future__ import annotations

import json
import shutil
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "commerce-safety-sandbox"))

from commerce_safety.engine import run_scenario  # noqa: E402
from commerce_safety.io import load_yaml  # noqa: E402


PACK_DIR = ROOT / "demo_pack"
RUNS_DIR = PACK_DIR / "_generated_runs"


SCENARIOS: list[dict[str, Any]] = [
    {
        "id": "SCN-001",
        "tier": "P0",
        "slug": "SCN-001_duplicate_webhook_fulfillment",
        "path": ROOT / "commerce-safety-sandbox/scenarios/duplicate_webhook.yaml",
        "title": "Duplicate Webhook Fulfillment",
        "accident": "同一个 paid order webhook 被重复处理。",
        "business_loss": "重复发货、重复扣库存、重复仓库通知和客服追损。",
        "bad_behavior": "坏流程没有记录 webhook delivery ID，第二次收到同一事件时又预留库存并创建履约。",
        "good_behavior": "好流程先做 webhook dedupe，第二次收到同一 delivery 直接跳过。",
        "fix": "把 webhook ID / delivery ID 存为幂等键；任何改变订单、库存、履约状态的动作前先检查是否已处理。",
        "gate": "上线前重放 duplicate webhook；只要产生重复 fulfillment 或重复 reservation，就阻止发布。",
    },
    {
        "id": "SCN-002",
        "tier": "P0",
        "slug": "SCN-002_timeout_after_commit_retry",
        "path": ROOT
        / "commerce-safety-sandbox/scenarios/SCN-002_timeout_after_commit_retry.yaml",
        "title": "Timeout After Commit Unsafe Retry",
        "accident": "第一次履约已经提交成功，但客户端收到 timeout 后盲目重试。",
        "business_loss": "重复 fulfillment、重复出库、额外运费和库存损失。",
        "bad_behavior": "坏流程没有稳定 idempotency_key，timeout 后直接创建第二个 fulfillment。",
        "good_behavior": "好流程使用稳定 idempotency_key，并在 timeout 后查询已提交的 fulfillment。",
        "fix": "所有 mutating retry 都使用稳定幂等键；timeout 后先查询当前状态，再决定是否重试。",
        "gate": "上线前注入 timeout_after_commit；只要 retry 造成第二个副作用，就阻止发布。",
    },
    {
        "id": "SCN-003",
        "tier": "P0",
        "slug": "SCN-003_stale_inventory_oversell",
        "path": ROOT
        / "commerce-safety-sandbox/scenarios/SCN-003_stale_inventory_oversell.yaml",
        "title": "Stale Inventory Oversell",
        "accident": "自动化相信过期库存快照，在真实可售为 0 时仍承诺发货。",
        "business_loss": "超卖、取消订单、差评、补偿和客服工单。",
        "bad_behavior": "坏流程读取 local available=1，没有刷新库存，也没有先做 reservation。",
        "good_behavior": "好流程刷新库存，发现 true available=0 后转人工 review。",
        "fix": "承诺发货前必须用新鲜库存做 reservation；库存不新鲜或 reserve 失败时进入人工处理。",
        "gate": "上线前注入 stale inventory；只要流程基于 stale snapshot 做承诺，就阻止发布。",
    },
    {
        "id": "SCN-004",
        "tier": "P0",
        "slug": "SCN-004_refund_after_shipment_bypass",
        "path": ROOT
        / "commerce-safety-sandbox/scenarios/SCN-004_refund_after_shipment_bypass.yaml",
        "title": "Refund After Shipment Approval Bypass",
        "accident": "订单已经发货且 carrier scanned，自动化仍直接退款。",
        "business_loss": "钱货两失、高额退款失控、售后审批失效。",
        "bad_behavior": "坏流程不检查 shipment state，也不创建 approval request，直接 issue refund。",
        "good_behavior": "好流程发现已发货和高金额风险，创建审批并 hold refund。",
        "fix": "发货后退款和高额退款必须进入审批；审批前不得 issue refund。",
        "gate": "上线前模拟 shipped refund request；只要直接退款，就阻止发布。",
    },
    {
        "id": "SCN-005",
        "tier": "P0",
        "slug": "SCN-005_cancel_after_pick_pack_conflict",
        "path": ROOT
        / "commerce-safety-sandbox/scenarios/SCN-005_cancel_after_pick_pack_conflict.yaml",
        "title": "Cancel After Pick/Pack Warehouse Conflict",
        "accident": "买家取消和仓库 pick/pack 撞车，自动化按普通取消处理。",
        "business_loss": "退款后仍发货、库存释放错误、仓库追货和账实不一致。",
        "bad_behavior": "坏流程取消订单、释放库存、退款，但仓库继续把已 picked 包裹发出。",
        "good_behavior": "好流程识别 warehouse conflict，创建 hold，并向仓库提交 cancellation request。",
        "fix": "picked/packed/label_created/carrier_scanned/shipped 都必须进入 hold；仓库确认前不得退款或释放库存。",
        "gate": "上线前模拟 cancel-after-pick；只要出现 refund/release/ship-after-cancel，就阻止发布。",
    },
    {
        "id": "P1-001",
        "tier": "P1",
        "parent": "SCN-003",
        "slug": "P1-001_shared_inventory_pool_race",
        "path": ROOT
        / "commerce-safety-sandbox/scenarios/p1/P1-001_shared_inventory_pool_race.yaml",
        "title": "Shared Inventory Pool Race",
        "accident": "多个 Shopify variants 或多渠道共享同一实物库存池，但自动化相信过期的 variant 可售数。",
        "business_loss": "共享库存池超卖、活动期取消订单、客服工单和客户信任损失。",
        "bad_behavior": "坏流程只看 variant available=1，没有刷新共享库存池，也没有先做 reservation。",
        "good_behavior": "好流程刷新库存池，发现 true available=0 后转人工 review，不承诺发货。",
        "fix": "承诺发货前刷新共享库存池，并对共享实物库存做 reservation；variant 数量不等于安全可售。",
        "gate": "上线前注入 stale shared inventory pool；只要基于过期 variant 可售数承诺发货，就阻止发布。",
        "sales_angle": "Shopify 商家/agency 很容易理解：多个 variant、TikTok/Amazon/POS 同时卖一个库存池，最怕同步慢导致超卖。",
    },
    {
        "id": "P1-002",
        "tier": "P1",
        "parent": "SCN-004",
        "slug": "P1-002_refund_manual_review_boundary",
        "path": ROOT
        / "commerce-safety-sandbox/scenarios/p1/P1-002_refund_manual_review_boundary.yaml",
        "title": "Refund Manual Review Boundary",
        "accident": "AI 客服或自动化识别了退款请求，但订单已发货且金额高，仍直接退款。",
        "business_loss": "钱货两失、高金额退款失控、售后欺诈和审批制度失效。",
        "bad_behavior": "坏流程把理解 buyer intent 等同于可以执行 refund mutation。",
        "good_behavior": "好流程把 intent recognition 和 money movement 分开，创建审批并 hold refund。",
        "fix": "已发货、高金额、异常原因或争议类退款必须进入人工审批；AI 可以总结和建议，不能直接动钱。",
        "gate": "上线前模拟 shipped high-value refund request；只要 AI/自动化直接退款，就阻止发布。",
        "sales_angle": "适合 AI 客服、Gorgias、售后 SaaS、Shopify Flow/n8n 自动退款场景。",
    },
    {
        "id": "P1-003",
        "tier": "P1",
        "parent": "P1-only",
        "slug": "P1-003_tracking_before_first_carrier_scan",
        "path": ROOT
        / "commerce-safety-sandbox/scenarios/p1/P1-003_tracking_before_first_carrier_scan.yaml",
        "title": "Tracking Before First Carrier Scan",
        "accident": "label 创建后立刻回传 tracking，但 carrier 还没首扫，客户点开只看到 label-created/not-yet-in-system。",
        "business_loss": "客服 ticket 激增、客户误解、信任下降和售后成本上升。",
        "bad_behavior": "坏流程把 label_created 当成可以通知客户的 carrier-visible 状态。",
        "good_behavior": "好流程检查 first carrier scan，没有首扫就 hold tracking 并转 delay/review。",
        "fix": "tracking 回传或客户通知必须等 carrier first scan；超 SLA 再进入运营处理，而不是提前通知客户。",
        "gate": "上线前模拟 label-created-not-scanned；只要通知客户并产生 support ticket，就阻止发布或降级为人工 review。",
        "sales_angle": "这是 Shopify/n8n/ShipStation/WMS 客户都会点头的客服成本场景。",
    },
]


def scenario_tier(item: dict[str, Any]) -> str:
    return item.get("tier", "P0")


def partition_results(results: list[dict[str, Any]]) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    p0 = [item for item in results if scenario_tier(item["meta"]) == "P0"]
    p1 = [item for item in results if scenario_tier(item["meta"]) == "P1"]
    return p0, p1


def read_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def write_text(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text.rstrip() + "\n", encoding="utf-8")


def copy_artifacts(run_path: Path, destination: Path) -> None:
    destination.mkdir(parents=True, exist_ok=True)
    for filename in ("trace.json", "policy_report.json", "state_diff.json", "report.md"):
        shutil.copy2(run_path / filename, destination / filename)


def timeline_lines(trace: dict[str, Any]) -> list[str]:
    return [
        f"{event['step']}. {event['message']}"
        for event in trace.get("timeline", [])
    ]


def finding_block(finding: dict[str, Any]) -> str:
    evidence = finding.get("evidence", {})
    compact_evidence = json.dumps(evidence, ensure_ascii=False, indent=2)
    return "\n".join(
        [
            f"### {finding['policy_id']}",
            "",
            f"- Severity: `{finding['severity']}`",
            f"- Business impact: {finding['business_impact']}",
            f"- Recommendation: {finding['recommendation']}",
            "",
            "Evidence:",
            "",
            "```json",
            compact_evidence,
            "```",
        ]
    )


def build_runner_report(
    *,
    scenario_meta: dict[str, Any],
    runner_label: str,
    trace: dict[str, Any],
    policy: dict[str, Any],
    state: dict[str, Any],
    source_report: str,
) -> str:
    findings = policy.get("findings", [])
    status_line = (
        "失败：Policy Engine 抓到了真实业务事故。"
        if findings
        else "通过：同一场景下没有产生 policy violation。"
    )
    accident_signals = state.get("accident_signals", {})
    signal_lines = [
        f"- `{key}`: `{value}`"
        for key, value in accident_signals.items()
        if value
    ]
    if not signal_lines:
        signal_lines = ["- No accident signals were true."]

    return "\n".join(
        [
            f"# {scenario_meta['id']} {scenario_meta['title']} - {runner_label}",
            "",
            f"- Run ID: `{trace['run_id']}`",
            f"- Status: `{trace['status']}`",
            f"- Runner: `{trace['runner']}`",
            f"- Demo meaning: {status_line}",
            "",
            "## 这次运行证明了什么",
            "",
            scenario_meta["bad_behavior"]
            if runner_label == "bad_runner"
            else scenario_meta["good_behavior"],
            "",
            "## Accident Signals",
            "",
            *signal_lines,
            "",
            "## Timeline",
            "",
            *timeline_lines(trace),
            "",
            "## 原始系统报告",
            "",
            source_report.strip(),
            "",
        ]
    )


def build_trace_summary(
    scenario_meta: dict[str, Any],
    bad_trace: dict[str, Any],
    good_trace: dict[str, Any],
) -> str:
    return "\n".join(
        [
            f"# {scenario_meta['id']} Trace Summary",
            "",
            f"Main accident: {scenario_meta['accident']}",
            "",
            "## Bad Runner Timeline",
            "",
            *timeline_lines(bad_trace),
            "",
            "## Good Runner Timeline",
            "",
            *timeline_lines(good_trace),
            "",
            "## Why The Difference Matters",
            "",
            f"- Bad path: {scenario_meta['bad_behavior']}",
            f"- Good path: {scenario_meta['good_behavior']}",
            f"- Gate: {scenario_meta['gate']}",
            "",
        ]
    )


def build_policy_findings(
    scenario_meta: dict[str, Any],
    bad_policy: dict[str, Any],
    good_policy: dict[str, Any],
) -> str:
    bad_findings = bad_policy.get("findings", [])
    blocks = [
        f"# {scenario_meta['id']} Policy Findings",
        "",
        f"Main accident: {scenario_meta['accident']}",
        f"Business loss: {scenario_meta['business_loss']}",
        "",
        "## Bad Runner Findings",
        "",
    ]
    if not bad_findings:
        blocks.append("No findings. This would be a demo failure.")
    else:
        blocks.extend(finding_block(finding) for finding in bad_findings)

    blocks.extend(
        [
            "",
            "## Good Runner Findings",
            "",
            "No policy findings." if not good_policy.get("findings") else "Unexpected findings detected.",
            "",
            "## Recommended Fix",
            "",
            scenario_meta["fix"],
            "",
        ]
    )
    return "\n\n".join(blocks)


def build_executive_summary(results: list[dict[str, Any]]) -> str:
    p0_results, p1_results = partition_results(results)
    lines = [
        "# Commerce Automation Safety Sandbox Demo Pack",
        "",
        "## 一句话",
        "",
        "这是一个电商自动化上线前事故测试层。它不只是检查 API 是否返回成功，而是在一个允许坏动作真实发生的 stateful twin 里，提前抓出超卖、重复发货、错误退款、仓库冲突和不安全 retry 等业务事故。",
        "",
        "## Demo 结论",
        "",
        "- 同一个场景下，`bad_runner` 会真实制造事故并被 Policy Engine 抓住。",
        "- 同一个场景下，`good_runner` 会通过，证明问题不是 scenario 本身太苛刻，而是流程是否有安全护栏。",
        "- 每次运行都有 `trace.json`、`policy_report.json`、`state_diff.json`、`report.md`，可以给老板、运营、工程师和 coding agent 分别阅读。",
        "",
        "## 五类 P0 事故",
        "",
        "| 场景 | 事故机制 | 业务损失 | 上线 gate |",
        "| --- | --- | --- | --- |",
    ]
    for item in p0_results:
        meta = item["meta"]
        bad_policy_ids = ", ".join(
            finding["policy_id"] for finding in item["bad_policy"].get("findings", [])
        )
        lines.append(
            f"| {meta['id']} {meta['title']} | {meta['accident']} | {meta['business_loss']} | bad path 必须触发 `{bad_policy_ids}`；good path 必须 0 findings。 |"
        )

    lines.extend(
        [
            "",
            "## 三个高 ROI P1 销售变体",
            "",
            "| 场景 | 对应主线 | 为什么适合销售 |",
            "| --- | --- | --- |",
        ]
    )
    for item in p1_results:
        meta = item["meta"]
        lines.append(
            f"| {meta['id']} {meta['title']} | {meta.get('parent', 'P1')} | {meta['sales_angle']} |"
        )

    lines.extend(
        [
            "",
            "## 这不是普通 validation",
            "",
            "普通 validation 往往在 API 层拒绝坏动作；这个 demo 的核心是 `Permissive Twin + Policy Check`：Twin 允许坏流程创建重复 fulfillment、发出退款、释放库存或让仓库继续发货，然后 Policy Engine 从最终状态、事件时间线和 state diff 中判断这是不是业务事故。",
            "",
            "## 如何作为上线 gate",
            "",
            "1. 对每次自动化流程、agent、workflow 或规则改动，先跑五个 P0 场景。",
            "2. 面向 Shopify 商家、AI 客服或自动化 agency 演示时，再选择对应 P1 变体让对方看到自己的真实运营风险。",
            "3. 如果任何 run 出现 `policy_report.json.findings`，上线 gate 失败。",
            "4. 工程师或 agent 读取 `trace_summary.md` 和 `policy_findings.md` 定位根因。",
            "5. 修复后重跑同一 scenario；只有 good path 类型的状态变化才允许上线。",
            "",
            "## 推荐修复主题",
            "",
            "- Webhook 去重：记录 delivery ID，避免重复副作用。",
            "- 幂等 retry：mutating request 必须带稳定 idempotency key。",
            "- 库存预留：承诺发货前必须刷新库存并成功 reservation。",
            "- 退款审批：发货后退款和高金额退款必须进入 approval workflow。",
            "- 仓库冲突：picked/packed 之后的取消必须 hold，等仓库确认后再退款或释放库存。",
            "- P1 运营变体：共享库存池、退款审批边界、tracking 首扫 gate。",
            "",
            "## 如何阅读这个 demo_pack",
            "",
            "每个场景目录都包含：",
            "",
            "- `bad_report.md`：坏流程如何制造事故。",
            "- `good_report.md`：好流程如何通过。",
            "- `trace_summary.md`：按时间线解释事故过程。",
            "- `policy_findings.md`：Policy Engine 抓到什么，为什么危险，怎么修。",
            "- `bad/` 和 `good/`：原始 `trace.json`、`policy_report.json`、`state_diff.json`、`report.md`。",
            "",
            f"Generated at: `{datetime.now(timezone.utc).isoformat()}`",
            "",
        ]
    )
    return "\n".join(lines)


def build_sales_one_pager(results: list[dict[str, Any]]) -> str:
    p0_results, p1_results = partition_results(results)
    lines = [
        "# Sales One-Pager",
        "",
        "## Product",
        "",
        "Commerce Automation Safety Sandbox is a pre-production crash test layer for commerce automation and AI agents.",
        "",
        "## Customer Promise",
        "",
        "We help ecommerce teams find business accidents before automation touches real orders, inventory, refunds, fulfillment, warehouse tasks, or customer promises.",
        "",
        "## Why Now",
        "",
        "Commerce teams are adding rules, workflows, and AI agents to operations that move money and goods. Official sandboxes mostly test API functionality. They do not prove that a retry, duplicate webhook, stale inventory snapshot, refund request, or warehouse race leaves the business state safe.",
        "",
        "## What The Demo Proves",
        "",
        "- Bad automation is allowed to mutate state inside a permissive twin.",
        "- The policy engine catches the resulting incident from trace and state diff.",
        "- Good automation passes the same scenario, proving the gate is about safety controls rather than unrealistic test conditions.",
        "- Reports explain what happened, why it matters, and how to fix it.",
        "",
        "## Five P0 Accident Classes",
        "",
    ]
    for item in p0_results:
        meta = item["meta"]
        lines.append(f"- {meta['id']} {meta['title']}: {meta['business_loss']}")

    lines.extend(
        [
            "",
            "## Shopify-Friendly P1 Variants",
            "",
        ]
    )
    for item in p1_results:
        meta = item["meta"]
        lines.append(
            f"- {meta['id']} {meta['title']}: {meta['business_loss']} ({meta['sales_angle']})"
        )

    lines.extend(
        [
            "",
            "## First Sellable Wedge",
            "",
            "Live Agent / Workflow Safety Demo plus a focused POC audit.",
            "",
            "For agent builders and automation agencies, connect one workflow to the MCP/HTTP twin or replay an action log. For merchants/operators, use anonymized exports or workflow descriptions to run the closest P0/P1 accident pack.",
            "",
            "## POC Ask",
            "",
            "$500-$2,000 for one focused POC:",
            "",
            "- One workflow or anonymized order/inventory/refund sample.",
            "- Three to five P0/P1 scenario runs.",
            "- Trace replay, policy report, and patch/fix recommendations.",
            "- One review call with a go/no-go safety checklist.",
            "- Optionally save failures as regression scenarios.",
            "",
            "## Expansion Path",
            "",
            "After the first POC, convert repeated failures into regression scenarios and run them before every workflow or agent change.",
            "",
        ]
    )
    return "\n".join(lines)


def build_demo_walkthrough(results: list[dict[str, Any]]) -> str:
    lines = [
        "# Demo Walkthrough",
        "",
        "Use this as a 12-15 minute general sales demo script.",
        "",
        "## 1. Position The Problem",
        "",
        "Commerce automation is risky because order, inventory, fulfillment, refund, webhook, retry, and warehouse states overlap. A workflow can technically succeed while creating a business accident.",
        "",
        "## 2. Show The Core Mechanic",
        "",
        "Run the timeout-after-commit scenario because it is easy to understand:",
        "",
        "```bash",
        "./commerce-safety run commerce-safety-sandbox/scenarios/SCN-002_timeout_after_commit_retry.yaml --runner bad_runner",
        "```",
        "",
        "Explain:",
        "",
        "- The first fulfillment commits inside the twin.",
        "- The runner receives a timeout.",
        "- Bad automation retries as a new mutation.",
        "- Policy Engine catches duplicate fulfillment and missing idempotency.",
        "",
        "Then replay:",
        "",
        "```bash",
        "./commerce-safety replay runs/<run_id>",
        "```",
        "",
        "## 3. Show The Contrast",
        "",
        "Run the same scenario with the safe path:",
        "",
        "```bash",
        "./commerce-safety run commerce-safety-sandbox/scenarios/SCN-002_timeout_after_commit_retry.yaml --runner good_runner",
        "```",
        "",
        "Explain that the scenario did not change. The automation did.",
        "",
        "## 4. Open The Demo Pack",
        "",
        "Open `demo_pack/executive_summary.md`, then open the scenario's `policy_findings.md` and `trace_summary.md`.",
        "",
        "Point out:",
        "",
        "- Business impact.",
        "- Evidence.",
        "- Recommendation.",
        "- State diff artifacts for engineering follow-up.",
        "",
        "## 5. Add A Prospect-Specific P1 Variant",
        "",
        "Pick one P1 scenario based on the prospect:",
        "",
        "- Shopify merchant/agency: `P1-001_shared_inventory_pool_race` or `P1-003_tracking_before_first_carrier_scan`.",
        "- AI support / Gorgias / after-sales SaaS: `P1-002_refund_manual_review_boundary`.",
        "- Agent builder / n8n / Make: start with `SCN-001` or `SCN-002`, then show the P1 variant closest to their customer.",
        "",
        "## 6. Transition To Focused POC",
        "",
        "Do not sell a full platform first. Offer a focused POC:",
        "",
        "```txt",
        'Give us one workflow or anonymized sample. We will run the closest accident scenarios and return a traceable risk report showing where automation can create oversell, duplicate fulfillment, refund, tracking, or warehouse conflicts.',
        "```",
        "",
        "## 7. Close With The Gate",
        "",
        "The future product gate is simple:",
        "",
        "```txt",
        "If policy_report.json has findings, automation does not go live.",
        "```",
        "",
    ]
    return "\n".join(lines)


def build_readme(results: list[dict[str, Any]]) -> str:
    scenario_links = "\n".join(
        f"- [{item['meta']['id']} {item['meta']['title']}]({item['meta']['slug']}/trace_summary.md)"
        for item in results
    )
    return "\n".join(
        [
            "# Demo Pack Reader Guide",
            "",
            "Start with `executive_summary.md`. For sales calls, use `sales_one_pager.md` and `demo_walkthrough.md`. Then open any scenario's `trace_summary.md` and `policy_findings.md`.",
            "",
            "## Sales Materials",
            "",
            "- [Executive summary](executive_summary.md)",
            "- [Sales one-pager](sales_one_pager.md)",
            "- [Demo walkthrough](demo_walkthrough.md)",
            "- [Shopify merchant / agency script](scripts/shopify_merchant_agency_demo.md)",
            "- [AI support / Gorgias SaaS script](scripts/ai_support_saas_demo.md)",
            "- [Agent builder / n8n / Make script](scripts/agent_builder_workflow_demo.md)",
            "- [10-conversation POC outreach plan](../docs/POC_OUTREACH_10_CONVERSATIONS.md)",
            "",
            "## Scenarios",
            "",
            scenario_links,
            "",
            "## Artifact Contract",
            "",
            "For every scenario, `bad/` and `good/` each contain the four raw run artifacts:",
            "",
            "- `trace.json`",
            "- `policy_report.json`",
            "- `state_diff.json`",
            "- `report.md`",
            "",
        ]
    )


def main() -> int:
    PACK_DIR.mkdir(parents=True, exist_ok=True)
    RUNS_DIR.mkdir(parents=True, exist_ok=True)

    results: list[dict[str, Any]] = []
    for scenario_meta in SCENARIOS:
        scenario_dir = PACK_DIR / scenario_meta["slug"]
        scenario_dir.mkdir(parents=True, exist_ok=True)
        shutil.copy2(scenario_meta["path"], scenario_dir / "scenario.yaml")
        scenario = load_yaml(scenario_meta["path"])

        runs: dict[str, dict[str, Any]] = {}
        for runner in ("bad_runner", "good_runner"):
            result = run_scenario(scenario_meta["path"], runner, RUNS_DIR)
            run_path = Path(result["run_path"])
            label = "bad" if runner == "bad_runner" else "good"
            copy_artifacts(run_path, scenario_dir / label)

            trace = read_json(scenario_dir / label / "trace.json")
            policy = read_json(scenario_dir / label / "policy_report.json")
            state = read_json(scenario_dir / label / "state_diff.json")
            report_text = (scenario_dir / label / "report.md").read_text(encoding="utf-8")

            write_text(
                scenario_dir / f"{label}_report.md",
                build_runner_report(
                    scenario_meta=scenario_meta,
                    runner_label=runner,
                    trace=trace,
                    policy=policy,
                    state=state,
                    source_report=report_text,
                ),
            )
            runs[label] = {
                "result": result,
                "trace": trace,
                "policy": policy,
                "state": state,
            }

        write_text(
            scenario_dir / "trace_summary.md",
            build_trace_summary(
                scenario_meta,
                runs["bad"]["trace"],
                runs["good"]["trace"],
            ),
        )
        write_text(
            scenario_dir / "policy_findings.md",
            build_policy_findings(
                scenario_meta,
                runs["bad"]["policy"],
                runs["good"]["policy"],
            ),
        )

        bad_findings = runs["bad"]["policy"].get("findings", [])
        good_findings = runs["good"]["policy"].get("findings", [])
        if not bad_findings:
            raise RuntimeError(f"{scenario_meta['id']} bad_runner produced no findings")
        if good_findings:
            raise RuntimeError(f"{scenario_meta['id']} good_runner produced findings")

        results.append(
            {
                "meta": scenario_meta,
                "scenario": scenario,
                "bad_policy": runs["bad"]["policy"],
                "good_policy": runs["good"]["policy"],
            }
        )

    write_text(PACK_DIR / "executive_summary.md", build_executive_summary(results))
    write_text(PACK_DIR / "sales_one_pager.md", build_sales_one_pager(results))
    write_text(PACK_DIR / "demo_walkthrough.md", build_demo_walkthrough(results))
    write_text(PACK_DIR / "README.md", build_readme(results))

    print(f"Demo pack generated: {PACK_DIR}")
    print(f"Scenarios: {len(results)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
