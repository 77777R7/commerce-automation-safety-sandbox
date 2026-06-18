from __future__ import annotations

import json
import sys
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "tools"))

from generate_demo_pack import SCENARIOS, read_json  # noqa: E402


VIEWER_DIR = ROOT / "demo_viewer"


def write_text(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content.rstrip() + "\n", encoding="utf-8")


def true_signals(state_diff: dict[str, Any]) -> dict[str, Any]:
    return {
        key: value
        for key, value in state_diff.get("accident_signals", {}).items()
        if value
    }


def compact_counts(state_diff: dict[str, Any]) -> dict[str, Any]:
    return {
        "fulfillments": {
            "before": state_diff["before"]["fulfillments"],
            "after": state_diff["after"]["fulfillments"],
        },
        "promises": {
            "before": state_diff["before"]["fulfillment_promises"],
            "after": state_diff["after"]["fulfillment_promises"],
        },
        "refunds": {
            "before": state_diff["before"]["refunds"],
            "after": state_diff["after"]["refunds"],
        },
        "trackingUploads": {
            "before": state_diff["before"].get("tracking_uploads", 0),
            "after": state_diff["after"].get("tracking_uploads", 0),
        },
        "supportTickets": {
            "before": state_diff["before"].get("support_tickets", 0),
            "after": state_diff["after"].get("support_tickets", 0),
        },
        "approvalRequests": {
            "before": state_diff["before"]["approval_requests"],
            "after": state_diff["after"]["approval_requests"],
        },
        "inventoryReleases": {
            "before": state_diff["before"]["inventory_releases"],
            "after": state_diff["after"]["inventory_releases"],
        },
        "workflowHolds": {
            "before": state_diff["before"]["workflow_holds"],
            "after": state_diff["after"]["workflow_holds"],
        },
        "warehouseCancellationRequests": {
            "before": state_diff["before"]["warehouse_cancellation_requests"],
            "after": state_diff["after"]["warehouse_cancellation_requests"],
        },
    }


def scenario_payload(meta: dict[str, Any]) -> dict[str, Any]:
    base = ROOT / "demo_pack" / meta["slug"]
    bad_policy = read_json(base / "bad" / "policy_report.json")
    good_policy = read_json(base / "good" / "policy_report.json")
    bad_trace = read_json(base / "bad" / "trace.json")
    good_trace = read_json(base / "good" / "trace.json")
    bad_state = read_json(base / "bad" / "state_diff.json")
    good_state = read_json(base / "good" / "state_diff.json")
    primary_finding = (bad_policy.get("findings") or [{}])[0]

    return {
        "id": meta["id"],
        "slug": meta["slug"],
        "title": meta["title"],
        "tier": meta.get("tier", "P0"),
        "parent": meta.get("parent"),
        "accident": meta["accident"],
        "businessLoss": meta["business_loss"],
        "badBehavior": meta["bad_behavior"],
        "goodBehavior": meta["good_behavior"],
        "fix": meta["fix"],
        "gate": meta["gate"],
        "risk": primary_finding.get(
            "policy_id", "policy_check_required"
        ),
        "impact": primary_finding.get("business_impact", meta["business_loss"]),
        "recommendation": primary_finding.get("recommendation", meta["fix"]),
        "bad": {
            "status": bad_policy["status"],
            "runId": bad_trace["run_id"],
            "findings": bad_policy.get("findings", []),
            "timeline": bad_trace.get("timeline", []),
            "signals": true_signals(bad_state),
            "counts": compact_counts(bad_state),
        },
        "good": {
            "status": good_policy["status"],
            "runId": good_trace["run_id"],
            "findings": good_policy.get("findings", []),
            "timeline": good_trace.get("timeline", []),
            "signals": true_signals(good_state),
            "counts": compact_counts(good_state),
        },
    }


def build_data() -> dict[str, Any]:
    scenarios = [scenario_payload(meta) for meta in SCENARIOS]
    total_findings = sum(len(item["bad"]["findings"]) for item in scenarios)
    return {
        "generatedAt": "static-demo-viewer",
        "summary": {
            "scenarioCount": len(scenarios),
            "badFailures": sum(
                1 for item in scenarios if item["bad"]["status"] == "failed"
            ),
            "goodPasses": sum(
                1 for item in scenarios if item["good"]["status"] == "passed"
            ),
            "totalFindings": total_findings,
        },
        "offlineAudit": {
            "title": "Offline Fulfillment Automation Audit",
            "riskScore": "100/100",
            "cleanScore": "0/100",
            "findings": [
                "offline_duplicate_fulfillment",
                "offline_negative_available_inventory",
                "offline_paid_order_inventory_shortage",
                "offline_cancel_after_pick_pack_conflict",
                "offline_refund_after_shipment_without_approval",
            ],
            "ask": "Send four exports: orders, inventory, fulfillments, refunds. No API keys, no live store access.",
        },
        "scenarios": scenarios,
    }


INDEX_HTML = """<!doctype html>
<html lang="en">
  <head>
    <meta charset="utf-8" />
    <meta name="viewport" content="width=device-width, initial-scale=1" />
    <title>Commerce Safety Demo Viewer</title>
    <link rel="preconnect" href="https://cdn.jsdelivr.net" />
    <link rel="stylesheet" href="styles.css" />
  </head>
  <body>
    <a class="skip-link" href="#main">Skip to demo</a>
    <header class="topbar" aria-label="Demo navigation">
      <div class="brand-lockup" aria-label="Commerce Safety Demo Viewer">
        <span class="brand-mark" aria-hidden="true"></span>
        <span>Commerce Safety</span>
      </div>
      <nav class="top-actions" aria-label="Sections">
        <a href="#scenarios">Scenarios</a>
        <a href="#offline-audit">Offline Audit</a>
        <a href="#gate">Gate</a>
      </nav>
    </header>

    <main id="main">
      <section class="hero" aria-labelledby="hero-title">
        <div class="hero-copy">
          <p class="eyebrow">Pre-production crash test layer</p>
          <h1 id="hero-title">Commerce Automation Safety Sandbox</h1>
          <p class="hero-subtitle">
            A boardroom-readable demo of five P0 commerce automation accidents
            plus three Shopify-friendly P1 variants: duplicate fulfillment,
            unsafe retry, oversell, refund bypass, warehouse conflict, shared
            inventory, refund approval boundaries, and tracking visibility.
            Each case uses the same scenario to compare a bad automation path
            against a safe one.
          </p>
          <div class="hero-actions">
            <a class="button primary" href="#scenarios">Review accidents</a>
            <a class="button secondary" href="#offline-audit">See POC audit</a>
          </div>
        </div>
        <div class="hero-visual" aria-label="Demo health overview">
          <div class="signal-strip">
            <span class="status-dot failed"></span>
            <span>Bad automation fails safely in test</span>
          </div>
          <div class="hero-metrics" id="heroMetrics"></div>
          <div class="state-flow" aria-hidden="true">
            <span>Webhook</span>
            <i></i>
            <span>Twin state</span>
            <i></i>
            <span>Policy finding</span>
          </div>
        </div>
      </section>

      <section class="viewer-shell" id="scenarios" aria-label="Scenario viewer">
        <aside class="scenario-rail" aria-label="P0 and P1 scenarios">
          <p class="section-label">P0 core + P1 variants</p>
          <div id="scenarioNav" class="scenario-nav"></div>
        </aside>

        <section class="case-workspace" aria-live="polite">
          <div class="case-header">
            <div>
              <p class="case-kicker" id="caseId"></p>
              <h2 id="caseTitle"></h2>
            </div>
            <div class="runner-toggle" role="group" aria-label="Timeline runner">
              <button type="button" class="toggle active" data-runner="bad">Bad runner</button>
              <button type="button" class="toggle" data-runner="good">Good runner</button>
            </div>
          </div>

          <div class="comparison-grid" id="comparisonGrid"></div>

          <section class="risk-panel" aria-labelledby="risk-title">
            <p class="section-label">Business risk summary</p>
            <h3 id="risk-title"></h3>
            <p id="riskPolicy" class="policy-chip"></p>
            <p id="riskImpact"></p>
            <p id="riskRecommendation"></p>
          </section>

          <div class="detail-grid">
            <section class="timeline-panel" aria-labelledby="timeline-title">
              <div class="panel-heading">
                <p class="section-label">Replay timeline</p>
                <h3 id="timeline-title">Recorded state sequence</h3>
              </div>
              <ol id="timelineList" class="timeline-list"></ol>
            </section>

            <section class="findings-panel" aria-labelledby="findings-title">
              <div class="panel-heading">
                <p class="section-label">Policy engine</p>
                <h3 id="findings-title">Findings and evidence</h3>
              </div>
              <div id="findingsList" class="findings-list"></div>
            </section>
          </div>

          <section class="state-panel" aria-labelledby="state-title">
            <div class="panel-heading">
              <p class="section-label">State diff</p>
              <h3 id="state-title">What changed in the commerce twin</h3>
            </div>
            <div id="stateDiff" class="state-diff"></div>
          </section>
        </section>
      </section>

      <section class="offline-band" id="offline-audit" aria-labelledby="offline-title">
        <div>
          <p class="section-label">First sellable wedge</p>
          <h2 id="offline-title">Offline Fulfillment Automation Audit</h2>
          <p id="offlineAsk"></p>
        </div>
        <div class="audit-proof" id="auditProof"></div>
      </section>

      <section class="gate-band" id="gate" aria-labelledby="gate-title">
        <p class="section-label">Launch gate</p>
        <h2 id="gate-title">If policy findings exist, automation does not go live.</h2>
        <p>
          This viewer is generated from the same raw artifacts as the CLI:
          trace, policy report, state diff, and markdown report.
        </p>
      </section>
    </main>

    <script src="https://cdn.jsdelivr.net/npm/gsap@3.12.5/dist/gsap.min.js"></script>
    <script src="demo-data.js"></script>
    <script src="app.js"></script>
  </body>
</html>
"""


STYLES_CSS = """:root {
  color-scheme: light;
  --ink: #17202a;
  --muted: #607080;
  --subtle: #eef2f6;
  --surface: #f7f8fa;
  --paper: #ffffff;
  --line: #dce3ea;
  --accent: #0f766e;
  --accent-ink: #063c38;
  --danger: #b42318;
  --danger-soft: #fff0ed;
  --success: #087443;
  --success-soft: #ebf8ef;
  --warning: #a65f00;
  --warning-soft: #fff6df;
  --shadow: 0 22px 70px rgba(22, 32, 29, 0.12);
  --radius: 8px;
}

* {
  box-sizing: border-box;
}

html {
  scroll-behavior: smooth;
}

body {
  margin: 0;
  background: var(--surface);
  color: var(--ink);
  font-family: Inter, ui-sans-serif, system-ui, -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif;
  line-height: 1.5;
}

button,
a {
  -webkit-tap-highlight-color: transparent;
}

button:focus-visible,
a:focus-visible {
  outline: 3px solid rgba(15, 118, 110, 0.35);
  outline-offset: 3px;
}

.skip-link {
  position: fixed;
  left: 16px;
  top: 12px;
  z-index: 1000;
  transform: translateY(-150%);
  background: var(--ink);
  color: white;
  padding: 10px 14px;
  border-radius: var(--radius);
}

.skip-link:focus {
  transform: translateY(0);
}

.topbar {
  position: sticky;
  top: 0;
  z-index: 20;
  display: flex;
  align-items: center;
  justify-content: space-between;
  min-height: 64px;
  padding: 12px clamp(18px, 4vw, 56px);
  background: rgba(251, 252, 249, 0.88);
  border-bottom: 1px solid var(--line);
  backdrop-filter: blur(16px);
}

.brand-lockup {
  display: inline-flex;
  align-items: center;
  gap: 10px;
  min-height: 44px;
  font-weight: 800;
}

.brand-mark {
  width: 22px;
  height: 22px;
  border: 2px solid var(--accent);
  border-radius: 5px;
  position: relative;
}

.brand-mark::after {
  content: "";
  position: absolute;
  width: 8px;
  height: 8px;
  right: -5px;
  bottom: -5px;
  background: var(--danger);
  border: 2px solid var(--surface);
  border-radius: 50%;
}

.top-actions {
  display: flex;
  align-items: center;
  gap: 8px;
}

.top-actions a {
  color: var(--muted);
  min-height: 44px;
  display: inline-flex;
  align-items: center;
  padding: 0 12px;
  text-decoration: none;
  font-weight: 700;
  font-size: 14px;
}

.top-actions a:hover {
  color: var(--ink);
}

.hero {
  min-height: calc(100svh - 64px);
  display: grid;
  grid-template-columns: minmax(0, 0.92fr) minmax(360px, 1.08fr);
  gap: clamp(28px, 6vw, 80px);
  align-items: center;
  padding: clamp(44px, 8vw, 96px) clamp(18px, 4vw, 56px);
  border-bottom: 1px solid var(--line);
}

.hero-copy {
  max-width: 760px;
}

.eyebrow,
.section-label,
.case-kicker {
  color: var(--accent);
  font-size: 12px;
  font-weight: 900;
  letter-spacing: 0.08em;
  margin: 0 0 12px;
  text-transform: uppercase;
}

h1,
h2,
h3,
p {
  letter-spacing: 0;
}

h1 {
  font-size: clamp(48px, 7vw, 104px);
  line-height: 0.92;
  margin: 0;
  max-width: 860px;
}

.hero-subtitle {
  color: var(--muted);
  font-size: clamp(18px, 2vw, 23px);
  margin: 26px 0 0;
  max-width: 700px;
}

.hero-actions {
  display: flex;
  flex-wrap: wrap;
  gap: 12px;
  margin-top: 32px;
}

.button {
  min-height: 48px;
  display: inline-flex;
  align-items: center;
  justify-content: center;
  padding: 0 18px;
  border-radius: var(--radius);
  text-decoration: none;
  font-weight: 800;
  border: 1px solid var(--line);
}

.button.primary {
  background: var(--ink);
  color: white;
  border-color: var(--ink);
}

.button.secondary {
  color: var(--ink);
  background: white;
}

.hero-visual {
  background: #111827;
  color: white;
  min-height: 520px;
  border-radius: var(--radius);
  padding: clamp(22px, 4vw, 40px);
  display: grid;
  align-content: space-between;
  box-shadow: var(--shadow);
  overflow: hidden;
  position: relative;
}

.hero-visual::before {
  content: "";
  position: absolute;
  inset: 0;
  background:
    linear-gradient(rgba(255, 255, 255, 0.05) 1px, transparent 1px),
    linear-gradient(90deg, rgba(255, 255, 255, 0.04) 1px, transparent 1px);
  background-size: 28px 28px;
  opacity: 0.5;
}

.hero-visual > * {
  position: relative;
}

.signal-strip {
  display: inline-flex;
  align-items: center;
  gap: 10px;
  color: rgba(255, 255, 255, 0.78);
  font-weight: 800;
}

.status-dot {
  width: 10px;
  height: 10px;
  border-radius: 999px;
  display: inline-block;
  flex: 0 0 auto;
}

.status-dot.failed {
  background: #ff6b5f;
}

.status-dot.passed {
  background: #4ade80;
}

.hero-metrics {
  display: grid;
  grid-template-columns: repeat(2, minmax(0, 1fr));
  gap: 1px;
  background: rgba(255, 255, 255, 0.14);
  border: 1px solid rgba(255, 255, 255, 0.14);
}

.metric {
  padding: 22px;
  background: rgba(17, 24, 39, 0.82);
}

.metric strong {
  display: block;
  font-size: clamp(32px, 4vw, 56px);
  line-height: 1;
}

.metric span {
  color: rgba(255, 255, 255, 0.68);
  display: block;
  font-weight: 700;
  margin-top: 8px;
}

.state-flow {
  display: grid;
  grid-template-columns: auto 1fr auto 1fr auto;
  align-items: center;
  gap: 14px;
  color: rgba(255, 255, 255, 0.72);
  font-size: 13px;
  font-weight: 800;
}

.state-flow i {
  height: 1px;
  background: rgba(255, 255, 255, 0.24);
}

.viewer-shell {
  display: grid;
  grid-template-columns: 320px minmax(0, 1fr);
  gap: 0;
  border-bottom: 1px solid var(--line);
}

.scenario-rail {
  padding: 28px;
  border-right: 1px solid var(--line);
  background: #f1f4f7;
  min-height: 100svh;
  position: sticky;
  top: 64px;
  align-self: start;
}

.scenario-nav {
  display: grid;
  gap: 8px;
}

.scenario-button {
  min-height: 64px;
  width: 100%;
  border: 1px solid var(--line);
  background: transparent;
  border-radius: var(--radius);
  text-align: left;
  padding: 12px;
  cursor: pointer;
  display: grid;
  gap: 5px;
  color: var(--ink);
}

.scenario-button:hover,
.scenario-button.active {
  background: white;
  border-color: rgba(15, 118, 110, 0.45);
}

.scenario-button strong {
  font-size: 14px;
}

.scenario-button span {
  color: var(--muted);
  font-size: 12px;
  font-weight: 700;
}

.case-workspace {
  padding: clamp(22px, 4vw, 48px);
  display: grid;
  gap: 24px;
}

.case-header {
  display: flex;
  justify-content: space-between;
  gap: 18px;
  align-items: end;
}

.case-header h2,
.offline-band h2,
.gate-band h2 {
  font-size: clamp(32px, 4vw, 58px);
  line-height: 1;
  margin: 0;
}

.runner-toggle {
  display: inline-flex;
  gap: 4px;
  padding: 4px;
  border: 1px solid var(--line);
  border-radius: var(--radius);
  background: white;
  min-height: 52px;
}

.toggle {
  border: 0;
  background: transparent;
  border-radius: 6px;
  padding: 0 14px;
  min-height: 44px;
  font-weight: 900;
  color: var(--muted);
  cursor: pointer;
}

.toggle.active {
  background: var(--ink);
  color: white;
}

.comparison-grid {
  display: grid;
  grid-template-columns: repeat(2, minmax(0, 1fr));
  gap: 1px;
  background: var(--line);
  border: 1px solid var(--line);
}

.comparison-cell {
  background: white;
  padding: 18px;
  min-height: 132px;
}

.comparison-cell h3 {
  margin: 0 0 10px;
  font-size: 16px;
}

.comparison-cell p {
  margin: 0;
  color: var(--muted);
}

.comparison-cell a {
  color: var(--accent);
  display: inline-flex;
  font-size: 13px;
  font-weight: 900;
  margin-top: 14px;
  min-height: 44px;
  align-items: center;
  text-decoration: none;
}

.comparison-cell a:hover {
  color: var(--accent-ink);
  text-decoration: underline;
}

.badge {
  display: inline-flex;
  align-items: center;
  min-height: 28px;
  padding: 0 10px;
  border-radius: 999px;
  font-size: 12px;
  font-weight: 900;
  margin-bottom: 14px;
}

.badge.failed {
  background: var(--danger-soft);
  color: var(--danger);
}

.badge.passed {
  background: var(--success-soft);
  color: var(--success);
}

.risk-panel,
.timeline-panel,
.findings-panel,
.state-panel,
.offline-band,
.gate-band {
  background: white;
  border: 1px solid var(--line);
  border-radius: var(--radius);
}

.risk-panel {
  padding: 24px;
  border-left: 5px solid var(--danger);
}

.risk-panel h3 {
  font-size: clamp(22px, 3vw, 34px);
  margin: 0 0 14px;
}

.risk-panel p {
  color: var(--muted);
  margin: 10px 0 0;
  max-width: 900px;
}

.risk-panel .policy-chip {
  color: var(--accent-ink);
  display: inline-flex;
  min-height: 32px;
  align-items: center;
  padding: 0 10px;
  border-radius: 999px;
  background: var(--subtle);
  font-size: 13px;
  font-weight: 900;
}

.detail-grid {
  display: grid;
  grid-template-columns: minmax(0, 1.1fr) minmax(320px, 0.9fr);
  gap: 24px;
}

.timeline-panel,
.findings-panel,
.state-panel {
  padding: 22px;
}

.panel-heading h3 {
  margin: 0 0 18px;
  font-size: 22px;
}

.timeline-list {
  margin: 0;
  padding: 0;
  list-style: none;
  display: grid;
  gap: 10px;
}

.timeline-list li {
  display: grid;
  grid-template-columns: 34px minmax(0, 1fr);
  gap: 12px;
  align-items: start;
  color: var(--muted);
}

.timeline-list b {
  width: 34px;
  height: 34px;
  border-radius: 999px;
  display: inline-flex;
  align-items: center;
  justify-content: center;
  background: var(--subtle);
  color: var(--ink);
  font-size: 12px;
  font-variant-numeric: tabular-nums;
}

.findings-list {
  display: grid;
  gap: 12px;
}

.finding {
  border-top: 1px solid var(--line);
  padding-top: 14px;
}

.finding:first-child {
  border-top: 0;
  padding-top: 0;
}

.finding h4 {
  margin: 0 0 8px;
  font-size: 16px;
}

.finding p {
  color: var(--muted);
  margin: 8px 0 0;
}

.state-diff {
  display: grid;
  grid-template-columns: repeat(4, minmax(0, 1fr));
  gap: 1px;
  background: var(--line);
  border: 1px solid var(--line);
}

.state-item {
  background: white;
  padding: 16px;
}

.state-item span {
  color: var(--muted);
  font-size: 12px;
  font-weight: 900;
  text-transform: uppercase;
}

.state-item strong {
  display: block;
  font-size: 28px;
  margin-top: 8px;
  font-variant-numeric: tabular-nums;
}

.offline-band,
.gate-band {
  margin: clamp(22px, 4vw, 56px);
  padding: clamp(24px, 4vw, 44px);
}

.offline-band {
  display: grid;
  grid-template-columns: minmax(0, 1fr) minmax(320px, 0.8fr);
  gap: 28px;
  align-items: center;
}

.offline-band p,
.gate-band p {
  color: var(--muted);
  max-width: 820px;
}

.audit-proof {
  display: grid;
  gap: 1px;
  background: var(--line);
  border: 1px solid var(--line);
}

.audit-row {
  background: white;
  padding: 16px;
  display: flex;
  justify-content: space-between;
  gap: 14px;
}

.audit-row strong {
  font-variant-numeric: tabular-nums;
}

.empty-state {
  color: var(--muted);
  margin: 0;
}

@media (max-width: 980px) {
  .hero,
  .viewer-shell,
  .detail-grid,
  .offline-band {
    grid-template-columns: 1fr;
  }

  .scenario-rail {
    position: static;
    min-height: auto;
    border-right: 0;
    border-bottom: 1px solid var(--line);
  }

  .scenario-nav {
    grid-template-columns: repeat(2, minmax(0, 1fr));
  }

  .case-header {
    align-items: start;
    flex-direction: column;
  }

  .state-diff {
    grid-template-columns: repeat(2, minmax(0, 1fr));
  }
}

@media (max-width: 640px) {
  .topbar {
    position: static;
  }

  .top-actions {
    display: none;
  }

  .hero {
    min-height: auto;
  }

  .hero-visual {
    min-height: 420px;
  }

  .hero-metrics,
  .comparison-grid,
  .scenario-nav,
  .state-diff {
    grid-template-columns: 1fr;
  }

  .state-flow {
    grid-template-columns: 1fr;
    gap: 8px;
  }

  .state-flow i {
    display: none;
  }
}

@media (prefers-reduced-motion: reduce) {
  *,
  *::before,
  *::after {
    animation-duration: 0.001ms !important;
    scroll-behavior: auto !important;
    transition-duration: 0.001ms !important;
  }
}
"""


APP_JS = """const data = window.DEMO_VIEWER_DATA;

let activeScenario = 1;
let activeRunner = "bad";
const reduceMotion = window.matchMedia("(prefers-reduced-motion: reduce)").matches;

const el = (id) => document.getElementById(id);

function statusLabel(status) {
  return status === "passed" ? "Passed" : "Failed";
}

function escapeHtml(value) {
  return String(value)
    .replaceAll("&", "&amp;")
    .replaceAll("<", "&lt;")
    .replaceAll(">", "&gt;")
    .replaceAll('"', "&quot;")
    .replaceAll("'", "&#039;");
}

function titleCase(text) {
  return String(text)
    .replaceAll("_", " ")
    .replace(/\\b\\w/g, (match) => match.toUpperCase());
}

function metricHtml(value, label) {
  return `<div class="metric"><strong>${value}</strong><span>${label}</span></div>`;
}

function renderHero() {
  el("heroMetrics").innerHTML = [
    metricHtml(data.summary.scenarioCount, "P0/P1 demo scenarios"),
    metricHtml(data.summary.badFailures, "bad flows caught"),
    metricHtml(data.summary.goodPasses, "good flows passed"),
    metricHtml(data.summary.totalFindings, "policy findings"),
  ].join("");
}

function renderNav() {
  el("scenarioNav").innerHTML = data.scenarios
    .map((scenario, index) => `
      <button class="scenario-button ${index === activeScenario ? "active" : ""}" type="button" data-index="${index}" aria-current="${index === activeScenario ? "true" : "false"}">
        <strong>${escapeHtml(scenario.id)} ${escapeHtml(scenario.title)}</strong>
        <span>${escapeHtml(scenario.tier)}${scenario.parent ? ` · ${escapeHtml(scenario.parent)}` : ""}</span>
        <span>${escapeHtml(scenario.businessLoss)}</span>
      </button>
    `)
    .join("");

  document.querySelectorAll(".scenario-button").forEach((button) => {
    button.addEventListener("click", () => {
      activeScenario = Number(button.dataset.index);
      activeRunner = "bad";
      renderScenario();
    });
  });
}

function renderComparison(scenario) {
  el("comparisonGrid").innerHTML = `
    <article class="comparison-cell">
      <span class="badge failed">${statusLabel(scenario.bad.status)}</span>
      <h3>Bad runner</h3>
      <p>${escapeHtml(scenario.badBehavior)}</p>
      <p>${scenario.bad.findings.length} policy findings</p>
      <a href="../demo_pack/${scenario.slug}/bad_report.md">Open bad report</a>
    </article>
    <article class="comparison-cell">
      <span class="badge passed">${statusLabel(scenario.good.status)}</span>
      <h3>Good runner</h3>
      <p>${escapeHtml(scenario.goodBehavior)}</p>
      <p>${scenario.good.findings.length} policy findings</p>
      <a href="../demo_pack/${scenario.slug}/good_report.md">Open good report</a>
    </article>
  `;
}

function renderTimeline(scenario) {
  const run = scenario[activeRunner];
  el("timelineList").innerHTML = run.timeline
    .map((event) => `<li><b>${escapeHtml(event.step)}</b><span>${escapeHtml(event.message)}</span></li>`)
    .join("");
}

function renderFindings(scenario) {
  const run = scenario[activeRunner];
  if (!run.findings.length) {
    el("findingsList").innerHTML = `<p class="empty-state">No policy findings for this runner.</p>`;
    return;
  }

  el("findingsList").innerHTML = run.findings
    .map((finding) => `
      <article class="finding">
        <span class="badge failed">${escapeHtml(finding.severity)}</span>
        <h4>${escapeHtml(finding.policy_id)}</h4>
        <p>${escapeHtml(finding.business_impact)}</p>
        <p><strong>Fix:</strong> ${escapeHtml(finding.recommendation)}</p>
      </article>
    `)
    .join("");
}

function renderStateDiff(scenario) {
  const counts = scenario[activeRunner].counts;
  const rows = [
    ["Fulfillments", counts.fulfillments.before, counts.fulfillments.after],
    ["Promises", counts.promises.before, counts.promises.after],
    ["Refunds", counts.refunds.before, counts.refunds.after],
    ["Tracking uploads", counts.trackingUploads.before, counts.trackingUploads.after],
    ["Support tickets", counts.supportTickets.before, counts.supportTickets.after],
    ["Approvals", counts.approvalRequests.before, counts.approvalRequests.after],
    ["Inventory releases", counts.inventoryReleases.before, counts.inventoryReleases.after],
    ["Workflow holds", counts.workflowHolds.before, counts.workflowHolds.after],
    ["Warehouse cancels", counts.warehouseCancellationRequests.before, counts.warehouseCancellationRequests.after],
  ];

  el("stateDiff").innerHTML = rows
    .map(([label, before, after]) => `
      <div class="state-item">
        <span>${escapeHtml(label)}</span>
        <strong>${escapeHtml(before)} → ${escapeHtml(after)}</strong>
      </div>
    `)
    .join("");
}

function renderAudit() {
  el("offlineAsk").textContent = data.offlineAudit.ask;
  el("auditProof").innerHTML = `
    <div class="audit-row"><span>Risk sample score</span><strong>${data.offlineAudit.riskScore}</strong></div>
    <div class="audit-row"><span>Clean sample score</span><strong>${data.offlineAudit.cleanScore}</strong></div>
    <div class="audit-row"><span>Detected policy classes</span><strong>${data.offlineAudit.findings.length}</strong></div>
  `;
}

function setRunnerButtons() {
  document.querySelectorAll(".toggle").forEach((button) => {
    const active = button.dataset.runner === activeRunner;
    button.classList.toggle("active", active);
    button.setAttribute("aria-pressed", String(active));
  });
}

function renderScenario() {
  const scenario = data.scenarios[activeScenario];
  renderNav();
  setRunnerButtons();
  el("caseId").textContent = `${scenario.id} · ${scenario.tier}${scenario.parent ? ` / ${scenario.parent}` : ""} / ${activeRunner === "bad" ? "Failure path" : "Safe path"}`;
  el("caseTitle").textContent = scenario.title;
  el("risk-title").textContent = scenario.accident;
  el("riskPolicy").textContent = `Primary policy: ${scenario.risk}`;
  el("riskImpact").textContent = `Possible impact: ${scenario.businessLoss}`;
  el("riskRecommendation").textContent = `Recommended control: ${scenario.recommendation}`;
  renderComparison(scenario);
  renderTimeline(scenario);
  renderFindings(scenario);
  renderStateDiff(scenario);

  if (window.gsap && !reduceMotion) {
    window.gsap.fromTo(
      ".case-workspace > *",
      { y: 18, opacity: 0 },
      { y: 0, opacity: 1, duration: 0.42, stagger: 0.045, ease: "power2.out" }
    );
  }
}

function bindRunnerToggle() {
  document.querySelectorAll(".toggle").forEach((button) => {
    button.addEventListener("click", () => {
      activeRunner = button.dataset.runner;
      renderScenario();
    });
  });
}

function introMotion() {
  if (!window.gsap || reduceMotion) return;
  const gsap = window.gsap;
  gsap.from(".topbar", { y: -18, opacity: 0, duration: 0.45, ease: "power2.out" });
  gsap.from(".hero-copy > *", { y: 24, opacity: 0, duration: 0.64, stagger: 0.08, ease: "power3.out", delay: 0.08 });
  gsap.from(".hero-visual", { y: 28, opacity: 0, duration: 0.72, ease: "power3.out", delay: 0.2 });
  gsap.from(".metric", { y: 16, opacity: 0, duration: 0.42, stagger: 0.05, ease: "power2.out", delay: 0.56 });
}

renderHero();
renderAudit();
bindRunnerToggle();
renderScenario();
introMotion();
"""


def main() -> int:
    data = build_data()
    write_text(VIEWER_DIR / "index.html", INDEX_HTML)
    write_text(VIEWER_DIR / "styles.css", STYLES_CSS)
    write_text(VIEWER_DIR / "app.js", APP_JS)
    write_text(
        VIEWER_DIR / "demo-data.js",
        "window.DEMO_VIEWER_DATA = "
        + json.dumps(data, ensure_ascii=False, indent=2)
        + ";",
    )
    print(f"Demo viewer generated: {VIEWER_DIR / 'index.html'}")
    print(f"Scenarios: {len(data['scenarios'])}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
