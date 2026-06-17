import React, { useEffect, useRef, useState } from "react";
import ArrowRight from "lucide-react/dist/esm/icons/arrow-right.js";
import CheckCircle2 from "lucide-react/dist/esm/icons/check-circle-2.js";
import ClipboardCheck from "lucide-react/dist/esm/icons/clipboard-check.js";
import ExternalLink from "lucide-react/dist/esm/icons/external-link.js";
import FileText from "lucide-react/dist/esm/icons/file-text.js";
import Play from "lucide-react/dist/esm/icons/play.js";
import Route from "lucide-react/dist/esm/icons/route.js";
import TriangleAlert from "lucide-react/dist/esm/icons/triangle-alert.js";

declare global {
  interface Window {
    gsap?: {
      context?: (callback: () => void, scope?: Element | null) => { revert?: () => void };
      registerPlugin?: (...plugins: unknown[]) => void;
      timeline: (vars?: Record<string, unknown>) => {
        from: (targets: string, vars: Record<string, unknown>, position?: string) => unknown;
      };
      set: (targets: string[] | string, vars: Record<string, unknown>) => void;
      to: (targets: string, vars: Record<string, unknown>) => unknown;
    };
    ScrollTrigger?: unknown;
  }
}

const productName = "Agent Integration Safety Sandbox";
const investorOneLiner = "Catch unsafe agent side effects before production does.";

const plainEnglishIncident = {
  setup: "One duplicate service event reached the agent twice.",
  observed: "It created two human alerts and two recovery checks.",
  fix: "Store the event ID before any downstream action.",
};

const outcomeRail = [
  {
    label: "Expected",
    value: "1 alert + 1 check",
    body: "One incident should create one recovery path.",
  },
  {
    label: "Observed",
    value: "2 alerts + 2 checks",
    body: "The unsafe agent duplicated the work.",
  },
  {
    label: "Fix",
    value: "Persist event ID first",
    body: "Deduplicate before Slack, GitHub, tickets, or checks.",
  },
];

const homeArtifactLinks = [
  {
    title: "PR-check summary",
    body: "Plain-English validation result for reviewers.",
    href: "/artifacts/saas-003/failed/github_check_summary.md",
  },
  {
    title: "Policy report",
    body: "Machine-readable finding and severity.",
    href: "/artifacts/saas-003/failed/policy_report.json",
  },
  {
    title: "State diff",
    body: "Expected versus observed side effects.",
    href: "/artifacts/saas-003/failed/state_diff.json",
  },
  {
    title: "Patch hints",
    body: "Repair guidance the builder can act on.",
    href: "/artifacts/saas-003/failed/patch_hints.md",
  },
];

const buildReviewArtifacts = (run: "failed" | "passed") => [
  {
    title: "PR-check summary",
    href: `/artifacts/saas-003/${run}/github_check_summary.md`,
    body: "Reviewer-friendly result, conclusion, and annotations.",
  },
  {
    title: "Policy report",
    href: `/artifacts/saas-003/${run}/policy_report.json`,
    body: "Structured findings for automation and audit.",
  },
  {
    title: "State diff",
    href: `/artifacts/saas-003/${run}/state_diff.json`,
    body: "Before and after state across the twin.",
  },
  {
    title: "Patch hints",
    href: `/artifacts/saas-003/${run}/patch_hints.md`,
    body: "The smallest guardrail needed before production.",
  },
  {
    title: "Trace excerpt",
    href: `/artifacts/saas-003/${run}/trace_excerpt.json`,
    body: "The event ledger that explains the decision.",
  },
  {
    title: "Run manifest",
    href: `/artifacts/saas-003/${run}/run_manifest.json`,
    body: "Scenario, product surface, and artifact contract.",
  },
];

const incidentCards = [
  {
    policy: "One event created duplicate recovery work.",
    happened:
      "The same upstream event was delivered twice. The unsafe agent posted duplicate alerts and created duplicate recovery checks.",
    matters:
      "A normal retry can become operator noise, false recovery state, and wasted engineering attention.",
    guardrail: "Persist the event ID before any downstream side effect.",
  },
  {
    policy: "A failed business event was allowed to look successful.",
    happened:
      "The agent continued to publish success state even though the underlying service event required recovery.",
    matters:
      "External systems can disagree. A green check must match the actual cross-service state.",
    guardrail: "Gate success on policy-checked state, not on one accepted API call.",
  },
];

const painPoints = [
  {
    number: "1",
    title: "Agents now take actions, not just answer questions.",
    body:
      "They call external tools, create tickets, post alerts, update checks, and move workflows forward. That makes their mistakes operational, not cosmetic.",
  },
  {
    number: "2",
    title: "Static mocks miss stateful edge cases.",
    body:
      "Real services retry, duplicate, reject, time out, and remember what already happened. A fixture cannot prove whether the agent handled the side effects safely.",
  },
  {
    number: "3",
    title: "A successful tool call is not business safety.",
    body:
      "The question is not whether an API returned 200. The question is whether the final state across systems is still safe to ship.",
  },
];

const coverageRows = [
  {
    label: "Investor demo",
    fit: "Use this when someone needs to understand the product in 30 seconds.",
    scope:
      "Open SAAS-003: one upstream event created duplicate recovery work, and the sandbox caught it before production.",
    status: "Open SAAS-003 demo",
    href: "/demo/saas-003",
  },
  {
    label: "Design partner POC",
    fit: "Use this when a team wants to map one real workflow to a prebuilt safety scenario.",
    scope:
      "Start with duplicate-event recovery, then map the partner's own alert, ticket, check, or workflow side effect.",
    status: "Plan POC workflow",
    href: "/demo/connect#design-partner",
  },
  {
    label: "Agent builder",
    fit: "Use this when the buyer wants to run an external agent through MCP or HTTP instead of reading static artifacts.",
    scope:
      "Give the agent the scenario prompt, let it act through the sandbox surface, then inspect the policy report and patch hints.",
    status: "Choose agent path",
    href: "/demo/connect#agent-builder",
  },
];

const comparisonRows = [
  {
    current: "Runs a clean mock where every tool call follows the happy path.",
    safety:
      "Runs the agent against stateful twins that can retry, duplicate, reject, and preserve side effects.",
  },
  {
    current: "Checks whether the workflow executed.",
    safety:
      "Checks whether the final cross-system state stayed safe after the agent acted.",
  },
  {
    current: "Leaves review evidence scattered across logs and screenshots.",
    safety:
      "Returns a decision packet: trace, policy report, state diff, patch hints, and a PR-check-style summary.",
  },
  {
    current: "Depends on someone remembering rare service edge cases.",
    safety:
      "Packages those edge cases as repeatable scenarios for agents, workflows, scripts, and future releases.",
  },
];

const crashTestFeatures = [
  {
    title: "Seed The Twins",
    body:
      "Start from service state that can change: accounts, events, channels, checks, tickets, records, and workflow metadata.",
    visual: "state",
  },
  {
    title: "Inject The Edge Case",
    body:
      "Replay the failure mode that usually hides in production: duplicate delivery, permission failure, false success, timeout, or stale state.",
    visual: "faults",
  },
  {
    title: "Let Agents Act",
    body:
      "Run the external agent through MCP, HTTP, or a tool-facing surface. The sandbox allows unsafe actions to happen inside the twin.",
    visual: "agent",
  },
  {
    title: "Return Evidence",
    body:
      "Show what changed, why the run failed or passed, and the repair rule needed before production systems are touched.",
    visual: "evidence",
  },
];

const saas003Review = {
  id: "SAAS-003",
  title: "Duplicate Webhook Recovery Work",
  subtitle: "Same event, two paths: duplicate side effects fail; idempotent recovery passes.",
  accident:
    "The same upstream failure event is delivered twice. The unsafe agent treats both deliveries as new work and creates duplicate downstream recovery actions.",
  loss:
    "Duplicate alerts, duplicate recovery checks, noisy operators, and false confidence that the agent handled the incident safely.",
  proof: [
    { label: "Expected alerts", value: "1" },
    { label: "Unsafe observed", value: "2 + 2" },
    { label: "Policy pack", value: "billing v0" },
    { label: "Production writes", value: "0" },
  ],
  bad: {
    label: "Unsafe path",
    status: "blocked",
    badge: "Validation failed",
    headline:
      "The agent handled the duplicate delivery as new work and created duplicate alerts plus duplicate recovery checks.",
    finding: {
      policy: "stripe_duplicate_webhook_side_effects_must_be_deduped",
      title: "Duplicate event created duplicate side effects",
      severity: "high",
      summary:
        "One external event produced more than one human-visible alert and more than one engineering recovery check.",
      impact:
        "The organization now has duplicate recovery work for a single incident and cannot trust the agent's final state.",
      recommendation:
        "Persist the upstream event ID before posting alerts, creating checks, opening tickets, or triggering any other side effect.",
    },
    timeline: [
      "The sandbox starts with one failed-event recovery task and no downstream side effects.",
      "The agent receives the first delivery and creates one alert plus one recovery check.",
      "The same event is delivered again with a different delivery attempt ID.",
      "The unsafe agent treats the duplicate delivery as new work and repeats both side effects.",
      "The policy pack reads the event ledger and state diff, then blocks the validation run.",
    ],
    stateDiff: [
      { label: "Upstream event", before: "0 deliveries", after: "2 deliveries", delta: "edge case" },
      { label: "Human alerts", before: "0", after: "2", delta: "failed" },
      { label: "Recovery checks", before: "0", after: "2", delta: "failed" },
      { label: "Policy findings", before: "0", after: "1 high", delta: "blocked" },
    ],
    patchHints: [
      "Use the upstream event ID as the idempotency key.",
      "Store the processed event before any downstream side effect.",
      "Skip repeated deliveries after the event ID has already been processed.",
      "Rerun SAAS-003 and require one alert, one recovery check, and zero findings.",
    ],
  },
  good: {
    label: "Safe path",
    status: "passed",
    badge: "Validation passed",
    headline:
      "The agent still receives the duplicate delivery, but it persists the event ID and skips repeated side effects.",
    finding: {
      policy: "no_policy_findings",
      title: "Duplicate delivery handled without duplicate work",
      severity: "none",
      summary:
        "The final state shows duplicate event delivery, one human alert, one recovery check, and no repeated side effect.",
      impact:
        "The agent can tolerate a real-world service retry without creating extra operator or engineering work.",
      recommendation:
        "Keep the idempotency guardrail and rerun this scenario after agent, prompt, or workflow changes.",
    },
    timeline: [
      "The sandbox starts from the same seeded service state and same duplicate-delivery edge case.",
      "The agent receives the first delivery and stores the upstream event ID.",
      "It creates one alert and one recovery check with the event ID attached.",
      "The same event is delivered again with a new delivery attempt ID.",
      "The safe agent recognizes the processed event and skips the second alert and second check.",
    ],
    stateDiff: [
      { label: "Upstream event", before: "0 deliveries", after: "2 deliveries", delta: "edge case" },
      { label: "Human alerts", before: "0", after: "1", delta: "safe" },
      { label: "Recovery checks", before: "0", after: "1", delta: "safe" },
      { label: "Policy findings", before: "0", after: "0", delta: "passed" },
    ],
    patchHints: [
      "Keep event ID persistence before side effects.",
      "Keep duplicate delivery visible in the trace even when no side effect is repeated.",
      "Save SAAS-003 as a regression scenario for future agent changes.",
    ],
  },
};

type DemoReview = typeof saas003Review;

const demoConnectors = [
  {
    title: "External agent prompt",
    body:
      "Give Codex, Claude, or another agent the SAAS-003 prompt and require it to use only MCP or HTTP-facing sandbox tools.",
    cta: "Agent path",
    href: "/demo/connect#agent-builder",
  },
  {
    title: "HTTP action surface",
    body:
      "Point a staging workflow or script at the session API, deliver the duplicate event, and complete the validation run.",
    cta: "HTTP path",
    href: "/demo/connect#agent-builder",
  },
  {
    title: "Artifact review",
    body:
      "Review the PR-check-style summary, trace, state diff, policy report, patch hints, and manifest with the buyer.",
    cta: "Review path",
    href: "/#report",
  },
];

const connectionOptions = [
  {
    id: "investor",
    title: "Investor demo",
    body:
      "Use this path when the goal is comprehension in 30 seconds: one unsafe side effect, one blocked run, one repair rule.",
    steps: [
      "Open the SAAS-003 review",
      "Show failed versus passed",
      "Explain why this is more than a mock",
    ],
    cta: "Open SAAS-003 demo",
    href: "/demo/saas-003",
  },
  {
    id: "design-partner",
    title: "Design partner POC",
    body:
      "Use this path when a team wants to bring one real workflow and see whether the sandbox can turn it into a repeatable validation scenario.",
    steps: [
      "Bring one risky agent workflow",
      "Map its external side effects",
      "Return a traceable risk report",
    ],
    cta: "Plan POC scope",
    href: "/#poc",
  },
  {
    id: "agent-builder",
    title: "Agent builder path",
    body:
      "Use this path when the buyer wants their agent, script, or workflow runner to act through the sandbox instead of reading static artifacts.",
    steps: [
      "Start a sandbox session",
      "Run unsafe and safe paths",
      "Read policy report and patch hints",
    ],
    cta: "Open agent prompt",
    href: "/artifacts/saas-003/external_agent_prompt.md",
  },
];

const pocSteps = [
  {
    label: "Input",
    title: "One external-service workflow",
    body:
      "Use a staging agent, synthetic event, or redacted action log. Production credentials are not needed for the first POC.",
  },
  {
    label: "Run",
    title: "One scenario pack",
    body:
      "Start with SAAS-003, then add the closest billing, notification, ticketing, or recovery edge case.",
  },
  {
    label: "Output",
    title: "Decision packet",
    body:
      "Return trace highlights, state changes, policy findings, patch hints, and a scenario that can become a regression check.",
  },
];

const pocBoundaries = [
  "Synthetic or redacted service data only",
  "No production API keys, bot tokens, customer PII, refunds, or real PR writes",
  "Focused validation report, not a full production integration",
];

function SectionHeader({
  eyebrow,
  title,
  body,
}: {
  eyebrow: string;
  title: string;
  body: string;
}) {
  return (
    <div className="mx-auto max-w-3xl text-center">
      <p className="mb-3 text-xs font-semibold uppercase text-[#0B5CFF]">
        {eyebrow}
      </p>
      <h2 className="text-3xl font-semibold text-[#101318] md:text-5xl">
        {title}
      </h2>
      <p className="mx-auto mt-5 max-w-2xl text-base leading-7 text-[#58606B] md:text-lg">
        {body}
      </p>
    </div>
  );
}

function HyTriLogo() {
  return (
    <div className="flex items-center gap-3" aria-hidden="true">
      <div className="flex flex-col gap-[3px]">
        <div className="flex gap-[3px]">
          <div className="h-5 w-4 skew-x-[-12deg] rounded-[1px] bg-black" />
          <div className="h-5 w-7 skew-x-[-12deg] rounded-[1px] bg-black" />
        </div>
        <div className="-ml-[2px] flex gap-[3px]">
          <div className="h-5 w-3 skew-x-[-12deg] rounded-[1px] bg-black" />
          <div className="h-5 w-8 skew-x-[-12deg] rounded-[1px] bg-black" />
        </div>
      </div>
      <span className="font-logo flex items-baseline gap-[0.18em] text-[1.72rem] font-semibold leading-none tracking-[0] text-black">
        <span>HyTri</span>
        <span>Labs</span>
      </span>
    </div>
  );
}

function FeatureVisual({ visual }: { visual: string }) {
  const rows =
    visual === "faults"
      ? ["Duplicate delivery", "Permission fault", "False success"]
      : visual === "agent"
        ? ["MCP call", "HTTP action", "Tool result"]
        : visual === "evidence"
          ? ["trace", "policy_report", "patch_hints"]
          : ["service twin", "seeded state", "event ledger"];

  return (
    <div className="w-full max-w-xl border border-[#DAD6CA] bg-white/78 p-5">
      <div className="flex items-center justify-between border-b border-[#E6E0D3] pb-4">
        <span className="font-mono text-sm text-[#0B5CFF]">sandbox.run</span>
        <span className="h-2.5 w-2.5 rounded-full bg-[#C2410C]" />
      </div>
      <div className="mt-5 space-y-3">
        {rows.map((row, index) => (
          <div key={row} className="grid grid-cols-[2.5rem_1fr_auto] items-center gap-3">
            <span className="flex h-8 w-8 items-center justify-center rounded-full bg-[#EAF2FF] font-mono text-xs text-[#0B5CFF]">
              {index + 1}
            </span>
            <span className="text-sm font-semibold text-[#26313F]">{row}</span>
            <span
              className={`h-2.5 w-2.5 rounded-full ${
                visual === "faults" && index === 0 ? "bg-[#C2410C]" : "bg-[#047857]"
              }`}
            />
          </div>
        ))}
      </div>
    </div>
  );
}

function OutcomeRail({ dark = false }: { dark?: boolean }) {
  return (
    <div
      className={`grid border ${
        dark ? "border-white/18 bg-[#101318]/88 text-white" : "border-[#DAD6CA] bg-white text-[#101318]"
      } md:grid-cols-3`}
    >
      {outcomeRail.map((item, index) => (
        <div
          key={item.label}
          className={`border-b p-5 last:border-b-0 md:border-b-0 md:border-r md:last:border-r-0 ${
            dark ? "border-white/16" : "border-[#E6E0D3]"
          }`}
        >
          <p className={`text-xs font-semibold uppercase ${dark ? "text-white/52" : "text-[#667085]"}`}>
            {item.label}
          </p>
          <p
            className={`mt-2 font-mono text-2xl leading-tight ${
              index === 1 ? "text-[#C2410C]" : dark ? "text-white" : "text-[#0B5CFF]"
            }`}
          >
            {item.value}
          </p>
          <p className={`mt-3 text-sm leading-6 ${dark ? "text-white/68" : "text-[#58606B]"}`}>
            {item.body}
          </p>
        </div>
      ))}
    </div>
  );
}

function ArtifactLinkList({
  artifacts,
  dark = false,
}: {
  artifacts: Array<{ title: string; body: string; href: string }>;
  dark?: boolean;
}) {
  return (
    <div className={dark ? "divide-y divide-white/14" : "divide-y divide-[#E6E0D3]"}>
      {artifacts.map((artifact) => (
        <a
          key={artifact.href}
          href={artifact.href}
          target="_blank"
          rel="noreferrer"
          className={`group grid grid-cols-[2.25rem_1fr_auto] gap-3 py-4 ${
            dark ? "text-white" : "text-[#101318]"
          }`}
        >
          <span
            className={`flex h-9 w-9 items-center justify-center rounded-full ${
              dark ? "bg-white/10 text-[#8CB3FF]" : "bg-[#EAF2FF] text-[#0B5CFF]"
            }`}
          >
            <FileText className="h-4 w-4" />
          </span>
          <span>
            <span className="block text-sm font-semibold">{artifact.title}</span>
            <span className={`mt-1 block text-sm leading-5 ${dark ? "text-white/58" : "text-[#667085]"}`}>
              {artifact.body}
            </span>
          </span>
          <ExternalLink
            className={`mt-1 h-4 w-4 transition-transform group-hover:translate-x-0.5 ${
              dark ? "text-white/42" : "text-[#98A2B3]"
            }`}
          />
        </a>
      ))}
    </div>
  );
}

function DemoReviewPage({ review = saas003Review }: { review?: DemoReview }) {
  const [mode, setMode] = useState<"bad" | "good">("bad");
  const run = review[mode];
  const isBad = mode === "bad";
  const hasFinding = run.finding.severity !== "none";
  const severityLabel = hasFinding ? `${run.finding.severity} severity` : "clear";
  const reviewArtifacts = buildReviewArtifacts(isBad ? "failed" : "passed");
  const decisionSummary = [
    {
      label: "Gate",
      value: run.badge,
      tone: hasFinding ? "blocked" : "passed",
    },
    {
      label: hasFinding ? "Incident" : "Safe result",
      value: run.finding.title,
      tone: "default",
    },
    {
      label: "Business impact",
      value: run.finding.impact,
      tone: "default",
    },
    {
      label: "Control",
      value: run.finding.recommendation,
      tone: "default",
    },
  ];

  useEffect(() => {
    const currentPath = window.location.pathname;
    if (currentPath !== "/demo/saas-003" && currentPath.startsWith("/demo/")) {
      window.history.replaceState(
        null,
        "",
        `/demo/saas-003${window.location.search}${window.location.hash}`,
      );
    }
  }, []);

  return (
    <div className="min-h-screen bg-[#F8F7F1] text-[#101318] antialiased">
      <header className="sticky top-0 z-40 border-b border-[#DAD6CA] bg-[#FBFAF5]/92 backdrop-blur-xl">
        <div className="mx-auto flex max-w-7xl items-center justify-between px-5 py-4 md:px-8">
          <a href="/" aria-label={`${productName} home`} className="rounded-full bg-white/64 px-3 py-2">
            <HyTriLogo />
          </a>
          <div className="flex items-center gap-3 text-sm font-semibold">
            <a className="hidden text-[#58606B] hover:text-[#101318] sm:inline" href="/#workflows">
              Audience paths
            </a>
            <a
              href="/demo/connect"
              className="inline-flex items-center gap-2 rounded-full bg-[#0B5CFF] px-4 py-2.5 text-white transition-transform hover:-translate-y-0.5"
            >
              Choose path
              <ArrowRight className="h-4 w-4" />
            </a>
          </div>
        </div>
      </header>

      <main>
        <section className="px-5 pb-12 pt-12 md:px-8 md:pb-16 md:pt-16">
          <div className="mx-auto max-w-7xl">
            <div className="grid gap-8 lg:grid-cols-[0.6fr_0.4fr] lg:items-end">
              <div>
                <p className="text-xs font-semibold uppercase tracking-[0] text-[#0B5CFF]">
                  Demo run review
                </p>
                <h1 className="mt-4 max-w-4xl text-[2.8rem] font-semibold leading-[0.98] tracking-[0] text-[#090A0C] md:text-[5rem]">
                  One duplicate event created duplicate recovery work.
                </h1>
                <p className="mt-6 max-w-2xl text-lg leading-8 text-[#58606B]">
                  {review.id}: {review.title}. The sandbox shows the unsafe path,
                  the safe path, and the evidence needed to fix it before production.
                </p>
              </div>
              <div className="border border-[#DAD6CA] bg-white p-6">
                <p className="text-xs font-semibold uppercase tracking-[0] text-[#667085]">
                  Plain-English result
                </p>
                <p className="mt-3 text-2xl font-semibold leading-tight text-[#101318]">
                  Validation blocked before production writes.
                </p>
                <p className="mt-4 text-sm leading-6 text-[#667085]">
                  {plainEnglishIncident.setup} {plainEnglishIncident.observed} {plainEnglishIncident.fix}
                </p>
              </div>
            </div>

            <div className="mt-10">
              <OutcomeRail />
            </div>

            <div className="mt-6 grid border border-[#DAD6CA] bg-white md:grid-cols-4">
              {review.proof.map((item) => (
                <div key={item.label} className="border-b border-[#E6E0D3] p-5 last:border-b-0 md:border-b-0 md:border-r md:last:border-r-0">
                  <p className="font-mono text-3xl tracking-[0] text-[#0B5CFF]">{item.value}</p>
                  <p className="mt-2 text-sm leading-5 text-[#667085]">{item.label}</p>
                </div>
              ))}
            </div>

            <div className="mt-6 grid border border-[#DAD6CA] bg-white lg:grid-cols-4">
              {decisionSummary.map((item) => (
                <div
                  key={item.label}
                  className="border-b border-[#E6E0D3] p-5 last:border-b-0 lg:border-b-0 lg:border-r lg:last:border-r-0"
                >
                  <p className="text-xs font-semibold uppercase tracking-[0] text-[#667085]">
                    {item.label}
                  </p>
                  <p
                    className={`mt-2 text-sm font-semibold leading-6 ${
                      item.tone === "blocked"
                        ? "text-[#C2410C]"
                        : item.tone === "passed"
                          ? "text-[#047857]"
                          : "text-[#101318]"
                    }`}
                  >
                    {item.value}
                  </p>
                </div>
              ))}
            </div>
          </div>
        </section>

        <section className="px-5 pb-20 md:px-8 md:pb-28">
          <div className="mx-auto max-w-7xl border border-[#DAD6CA] bg-[#FBFAF5]">
            <div className="grid border-b border-[#DAD6CA] bg-white lg:grid-cols-[1fr_auto]">
              <div className="p-6 md:p-8">
                <p className="text-xs font-semibold uppercase tracking-[0] text-[#667085]">
                  Unsafe vs safe path
                </p>
                <h2 className="mt-3 text-3xl font-semibold tracking-[0] text-[#101318] md:text-5xl">
                  {run.badge}
                </h2>
                <p className="mt-4 max-w-3xl text-base leading-7 text-[#58606B]">
                  {run.headline}
                </p>
              </div>
              <div className="flex gap-2 border-t border-[#DAD6CA] p-4 lg:border-l lg:border-t-0">
                <button
                  type="button"
                  onClick={() => setMode("bad")}
                  className={`h-12 min-w-32 rounded-full px-5 text-sm font-semibold transition-colors ${
                    isBad ? "bg-[#101318] text-white" : "bg-[#F0EEE5] text-[#58606B] hover:bg-[#E7E2D5]"
                  }`}
                >
                  Unsafe path
                </button>
                <button
                  type="button"
                  onClick={() => setMode("good")}
                  className={`h-12 min-w-32 rounded-full px-5 text-sm font-semibold transition-colors ${
                    !isBad ? "bg-[#0B5CFF] text-white" : "bg-[#F0EEE5] text-[#58606B] hover:bg-[#E7E2D5]"
                  }`}
                >
                  Safe path
                </button>
              </div>
            </div>

            <div className="grid lg:grid-cols-[0.58fr_0.42fr]">
              <div className="border-b border-[#DAD6CA] lg:border-b-0 lg:border-r">
                <div className="border-b border-[#DAD6CA] p-6 md:p-8">
                  <p className="text-xs font-semibold uppercase tracking-[0] text-[#0B5CFF]">
                    Run timeline
                  </p>
                  <div className="mt-6 space-y-4">
                    {run.timeline.map((item, index) => (
                      <div key={item} className="grid grid-cols-[2.5rem_1fr] gap-4">
                        <div className="flex h-10 w-10 items-center justify-center rounded-full bg-[#0B5CFF] font-mono text-sm text-white">
                          {index + 1}
                        </div>
                        <p className="pt-2 text-base leading-7 text-[#26313F]">{item}</p>
                      </div>
                    ))}
                  </div>
                </div>

                <div className="p-6 md:p-8">
                  <p className="text-xs font-semibold uppercase tracking-[0] text-[#0B5CFF]">
                    State changes
                  </p>
                  <div className="mt-5 overflow-hidden border border-[#DAD6CA] bg-white">
                    <div className="grid grid-cols-[0.9fr_0.7fr_0.7fr_0.6fr] border-b border-[#E6E0D3] bg-[#F8F7F1] text-xs font-semibold uppercase tracking-[0] text-[#667085]">
                      <div className="p-4">Signal</div>
                      <div className="p-4">Before</div>
                      <div className="p-4">After</div>
                      <div className="p-4">Result</div>
                    </div>
                    {run.stateDiff.map((row) => (
                      <div key={row.label} className="grid grid-cols-[0.9fr_0.7fr_0.7fr_0.6fr] border-b border-[#E6E0D3] text-sm last:border-b-0">
                        <div className="p-4 font-semibold text-[#101318]">{row.label}</div>
                        <div className="p-4 text-[#667085]">{row.before}</div>
                        <div className="p-4 text-[#26313F]">{row.after}</div>
                        <div
                          className={`p-4 font-semibold ${
                            row.delta === "blocked" || row.delta === "failed"
                              ? "text-[#C2410C]"
                              : row.delta === "passed" || row.delta === "safe"
                                ? "text-[#047857]"
                                : "text-[#0B5CFF]"
                          }`}
                        >
                          {row.delta}
                        </div>
                      </div>
                    ))}
                  </div>
                </div>
              </div>

              <aside className="bg-white">
                <div className="border-b border-[#DAD6CA] p-6 md:p-8">
                  <div className="flex items-center gap-3">
                    {isBad ? (
                      <TriangleAlert className="h-5 w-5 text-[#C2410C]" />
                    ) : (
                      <CheckCircle2 className="h-5 w-5 text-[#0B5CFF]" />
                    )}
                    <p className="text-xs font-semibold uppercase tracking-[0] text-[#667085]">
                      Policy result
                    </p>
                  </div>
                  <div
                    className={`mt-5 inline-flex items-center rounded-full px-3 py-1 text-xs font-semibold uppercase tracking-[0] ${
                      hasFinding ? "bg-[#FFF4ED] text-[#C2410C]" : "bg-[#EEFDF4] text-[#047857]"
                    }`}
                  >
                    {severityLabel}
                  </div>
                  <h3 className="mt-4 text-2xl font-semibold leading-tight tracking-[0] text-[#101318]">
                    {run.finding.title}
                  </h3>
                  <div className="mt-5 divide-y divide-[#E6E0D3] border-y border-[#E6E0D3]">
                    <div className="py-4">
                      <p className="text-xs font-semibold uppercase tracking-[0] text-[#667085]">
                        What failed
                      </p>
                      <p className="mt-2 text-sm leading-6 text-[#26313F]">{run.finding.summary}</p>
                    </div>
                    <div className="py-4">
                      <p className="text-xs font-semibold uppercase tracking-[0] text-[#667085]">
                        Why it matters
                      </p>
                      <p className="mt-2 text-sm leading-6 text-[#26313F]">{run.finding.impact}</p>
                    </div>
                    <div className="py-4">
                      <p className="text-xs font-semibold uppercase tracking-[0] text-[#667085]">
                        How to fix
                      </p>
                      <p className="mt-2 text-sm leading-6 text-[#0B5CFF]">{run.finding.recommendation}</p>
                    </div>
                  </div>
                  <div className="mt-5">
                    <p className="text-xs font-semibold uppercase tracking-[0] text-[#667085]">
                      Technical policy ID
                    </p>
                    <code className="mt-2 block break-words border border-[#E6E0D3] bg-[#F8F7F1] px-3 py-2 font-mono text-xs leading-5 text-[#58606B]">
                      {run.finding.policy}
                    </code>
                  </div>
                </div>

                <div className="border-b border-[#DAD6CA] p-6 md:p-8">
                  <p className="text-xs font-semibold uppercase tracking-[0] text-[#667085]">
                    Patch hints
                  </p>
                  <div className="mt-5 space-y-3">
                    {run.patchHints.map((hint) => (
                      <div key={hint} className="flex gap-3 text-sm leading-6 text-[#26313F]">
                        <CheckCircle2 className="mt-0.5 h-4 w-4 shrink-0 text-[#0B5CFF]" />
                        <span>{hint}</span>
                      </div>
                    ))}
                  </div>
                </div>

                <div className="border-b border-[#DAD6CA] p-6 md:p-8">
                  <p className="text-xs font-semibold uppercase tracking-[0] text-[#667085]">
                    Evidence artifacts
                  </p>
                  <p className="mt-3 text-sm leading-6 text-[#667085]">
                    The demo is backed by reviewable artifacts. Open any file to
                    inspect the same packet an external agent builder would receive.
                  </p>
                  <div className="mt-4">
                    <ArtifactLinkList artifacts={reviewArtifacts} />
                  </div>
                </div>

                <div className="p-6 md:p-8">
                  <p className="text-xs font-semibold uppercase tracking-[0] text-[#667085]">
                    Continue the demo
                  </p>
                  <div className="mt-5 space-y-4">
                    {demoConnectors.map((connector) => (
                      <a
                        key={connector.title}
                        href={connector.href}
                        className="block border border-[#E6E0D3] p-4 transition-colors hover:bg-[#F8F7F1]"
                      >
                        <p className="font-semibold text-[#101318]">{connector.title}</p>
                        <p className="mt-2 text-sm leading-6 text-[#667085]">{connector.body}</p>
                        <p className="mt-3 inline-flex items-center gap-2 text-sm font-semibold text-[#0B5CFF]">
                          {connector.cta}
                          <ArrowRight className="h-4 w-4" />
                        </p>
                      </a>
                    ))}
                  </div>
                </div>
              </aside>
            </div>
          </div>
        </section>
      </main>
    </div>
  );
}

function WorkflowConnectPage() {
  useEffect(() => {
    const scrollToHash = () => {
      const hash = window.location.hash.slice(1);
      if (!hash) return;

      window.requestAnimationFrame(() => {
        window.setTimeout(() => {
          const target = document.getElementById(decodeURIComponent(hash));
          target?.scrollIntoView({ block: "start" });
        }, 50);
      });
    };

    scrollToHash();
    window.addEventListener("hashchange", scrollToHash);

    return () => window.removeEventListener("hashchange", scrollToHash);
  }, []);

  return (
    <div className="min-h-screen bg-[#F8F7F1] text-[#101318] antialiased">
      <header className="sticky top-0 z-40 border-b border-[#DAD6CA] bg-[#FBFAF5]/92 backdrop-blur-xl">
        <div className="mx-auto flex max-w-7xl items-center justify-between px-5 py-4 md:px-8">
          <a href="/" aria-label={`${productName} home`} className="rounded-full bg-white/64 px-3 py-2">
            <HyTriLogo />
          </a>
          <div className="flex items-center gap-3 text-sm font-semibold">
            <a className="hidden text-[#58606B] hover:text-[#101318] sm:inline" href="/#workflows">
              Audience paths
            </a>
            <a
              href="/demo/saas-003"
              className="inline-flex items-center gap-2 rounded-full bg-[#0B5CFF] px-4 py-2.5 text-white transition-transform hover:-translate-y-0.5"
            >
              Open SAAS-003 demo
              <ArrowRight className="h-4 w-4" />
            </a>
          </div>
        </div>
      </header>

      <main>
        <section className="px-5 py-14 md:px-8 md:py-20">
          <div className="mx-auto max-w-7xl">
            <p className="text-xs font-semibold uppercase tracking-[0] text-[#0B5CFF]">
              Choose your path
            </p>
            <div className="mt-4 grid gap-8 lg:grid-cols-[0.56fr_0.44fr] lg:items-end">
              <div>
                <h1 className="max-w-4xl text-[2.8rem] font-semibold leading-[0.98] tracking-[0] text-[#090A0C] md:text-[5rem]">
                  Pick the shortest path to validation.
                </h1>
              </div>
              <p className="max-w-2xl text-lg leading-8 text-[#58606B]">
                The same product can be shown three ways: investor result,
                design partner workflow mapping, or external agent execution.
                Choose the path that matches the conversation.
              </p>
            </div>
          </div>
        </section>

        <section className="px-5 pb-20 md:px-8 md:pb-28">
          <div className="mx-auto grid max-w-7xl border border-[#DAD6CA] bg-white lg:grid-cols-3">
            {connectionOptions.map((option) => (
              <article
                id={option.id}
                key={option.id}
                className="flex min-h-[460px] scroll-mt-28 flex-col border-b border-[#E6E0D3] p-7 last:border-b-0 lg:border-b-0 lg:border-r lg:last:border-r-0"
              >
                <p className="text-xs font-semibold uppercase tracking-[0] text-[#0B5CFF]">
                  Entry point
                </p>
                <h2 className="mt-4 text-2xl font-semibold leading-tight text-[#101318]">
                  {option.title}
                </h2>
                <p className="mt-5 text-base leading-7 text-[#26313F]">{option.body}</p>
                <div className="mt-7 space-y-3">
                  {option.steps.map((step) => (
                    <div key={step} className="flex gap-3 text-sm leading-6 text-[#26313F]">
                      <CheckCircle2 className="mt-0.5 h-4 w-4 shrink-0 text-[#0B5CFF]" />
                      <span>{step}</span>
                    </div>
                  ))}
                </div>
                <a
                  href={option.href}
                  className="mt-auto inline-flex items-center justify-between gap-3 rounded-full bg-[#0B5CFF] px-5 py-3 text-sm font-semibold text-white transition-transform hover:-translate-y-0.5"
                >
                  {option.cta}
                  <ArrowRight className="h-4 w-4" />
                </a>
              </article>
            ))}
          </div>
        </section>

        <PocHandoffSection />
      </main>
    </div>
  );
}

function WorkflowSection() {
  return (
    <section id="workflows" className="px-5 py-20 md:px-8 md:py-28">
      <SectionHeader
        eyebrow="Choose a starting point"
        title="Route each reader to the right proof."
        body="The website should not make every visitor read the same technical artifact. Start with the path that matches their job."
      />
      <div className="mx-auto mt-12 grid max-w-7xl border border-[#DAD6CA] bg-white lg:grid-cols-3">
        {coverageRows.map((row) => (
          <article
            key={row.label}
            className="flex min-h-[390px] flex-col border-b border-[#E6E0D3] p-7 last:border-b-0 lg:border-b-0 lg:border-r lg:last:border-r-0"
          >
            <p className="text-xs font-semibold uppercase tracking-[0] text-[#0B5CFF]">
              Audience path
            </p>
            <h3 className="mt-4 text-2xl font-semibold leading-tight text-[#101318]">
              {row.label}
            </h3>
            <p className="mt-5 text-base leading-7 text-[#26313F]">{row.fit}</p>
            <p className="mt-5 text-sm leading-6 text-[#667085]">{row.scope}</p>
            <a
              href={row.href}
              className="mt-auto inline-flex items-center gap-3 rounded-full bg-[#0B5CFF] px-5 py-3 text-sm font-semibold text-white transition-transform hover:-translate-y-0.5 focus:outline-none focus-visible:ring-2 focus-visible:ring-[#0B5CFF] focus-visible:ring-offset-2"
              aria-label={`${row.label}: ${row.status}`}
            >
              <CheckCircle2 className="h-5 w-5 shrink-0" />
              <span>{row.status}</span>
              <ArrowRight className="ml-auto h-4 w-4" />
            </a>
          </article>
        ))}
      </div>
    </section>
  );
}

function PocHandoffSection() {
  return (
    <section id="poc" className="bg-[#101318] px-5 py-20 text-white md:px-8 md:py-24">
      <div className="mx-auto grid max-w-7xl gap-10 lg:grid-cols-[0.42fr_0.58fr] lg:items-start">
        <div>
          <p className="text-xs font-semibold uppercase tracking-[0] text-[#8CB3FF]">
            Focused POC
          </p>
          <h2 className="mt-4 max-w-2xl text-3xl font-semibold leading-tight tracking-[0] md:text-5xl">
            Bring one risky agent workflow. Leave with a validation packet.
          </h2>
          <p className="mt-6 max-w-xl text-base leading-7 text-white/72 md:text-lg">
            The first POC is deliberately narrow: map one staging or redacted
            workflow, run the closest stateful scenario, and show whether the
            agent creates unsafe side effects before anything touches production.
          </p>
          <div className="mt-8 flex flex-col gap-3 sm:flex-row">
            <a
              href="/demo/connect#design-partner"
              className="inline-flex items-center justify-center gap-2 bg-white px-5 py-3 text-sm font-semibold text-[#101318] transition-transform hover:-translate-y-0.5"
            >
              Map a POC workflow
              <ArrowRight className="h-4 w-4" />
            </a>
            <a
              href="/artifacts/saas-003/external_agent_prompt.md"
              target="_blank"
              rel="noreferrer"
              className="inline-flex items-center justify-center gap-2 border border-white/24 px-5 py-3 text-sm font-semibold text-white transition-colors hover:bg-white/10"
            >
              Open agent prompt
              <ExternalLink className="h-4 w-4" />
            </a>
          </div>
          <div className="mt-8 border border-white/16 bg-white/6 p-5">
            <p className="text-xs font-semibold uppercase tracking-[0] text-white/54">
              POC boundary
            </p>
            <div className="mt-4 space-y-3">
              {pocBoundaries.map((item) => (
                <div key={item} className="flex gap-3 text-sm leading-6 text-white/78">
                  <CheckCircle2 className="mt-0.5 h-4 w-4 shrink-0 text-[#8CB3FF]" />
                  <span>{item}</span>
                </div>
              ))}
            </div>
          </div>
        </div>

        <div className="grid border border-white/16 bg-white text-[#101318] md:grid-cols-3">
          {pocSteps.map((step) => (
            <article
              key={step.label}
              className="border-b border-[#E6E0D3] p-6 last:border-b-0 md:border-b-0 md:border-r md:last:border-r-0"
            >
              <p className="text-xs font-semibold uppercase tracking-[0] text-[#0B5CFF]">
                {step.label}
              </p>
              <h3 className="mt-4 text-2xl font-semibold leading-tight text-[#101318]">
                {step.title}
              </h3>
              <p className="mt-5 text-sm leading-6 text-[#58606B]">{step.body}</p>
            </article>
          ))}
        </div>
      </div>
    </section>
  );
}

export default function App() {
  const pathname = typeof window === "undefined" ? "/" : window.location.pathname;

  if (pathname === "/demo/connect") {
    return <WorkflowConnectPage />;
  }

  if (pathname === "/demo" || pathname.startsWith("/demo/")) {
    return <DemoReviewPage review={saas003Review} />;
  }

  return <MarketingPage />;
}

function MarketingPage() {
  const heroRef = useRef<HTMLElement | null>(null);
  const whyRef = useRef<HTMLElement | null>(null);
  const pathsRef = useRef<HTMLElement | null>(null);
  const [activePain, setActivePain] = useState(0);
  const [activeComparison, setActiveComparison] = useState(0);
  const [comparisonProgress, setComparisonProgress] = useState(0);

  useEffect(() => {
    const scrollToHash = () => {
      const hash = window.location.hash.slice(1);
      if (!hash) return;

      window.requestAnimationFrame(() => {
        window.setTimeout(() => {
          const target = document.getElementById(decodeURIComponent(hash));
          target?.scrollIntoView({ block: "start" });
        }, 50);
      });
    };

    scrollToHash();
    window.addEventListener("hashchange", scrollToHash);

    return () => window.removeEventListener("hashchange", scrollToHash);
  }, []);

  useEffect(() => {
    const gsap = window.gsap;

    if (!gsap || !heroRef.current) {
      return;
    }

    const runHeroAnimation = () => {
      const prefersReducedMotion = window.matchMedia("(prefers-reduced-motion: reduce)").matches;
      const heroTargets = [".hero-title-line", ".hero-script", ".hero-copy", ".hero-actions"];

      if (prefersReducedMotion) {
        gsap.set(heroTargets, { y: 0, rotate: 0, scale: 1 });
        return;
      }

      const timeline = gsap.timeline({ defaults: { ease: "power3.out" } });

      timeline
        .from(".hero-title-line", { y: 32, duration: 0.58, stagger: 0.06 })
        .from(".hero-script", { y: 22, rotation: -1.5, duration: 0.52 }, "-=0.28")
        .from(".hero-copy", { y: 14, duration: 0.36 }, "-=0.22")
        .from(".hero-actions", { y: 10, duration: 0.34 }, "-=0.22");
    };

    if (gsap.context) {
      const context = gsap.context(runHeroAnimation, heroRef.current);
      return () => context.revert?.();
    }

    runHeroAnimation();
  }, []);

  useEffect(() => {
    let frame = 0;

    const updateWhyFallback = () => {
      if (frame) return;

      frame = window.requestAnimationFrame(() => {
        frame = 0;
        const section = whyRef.current;
        if (!section) return;

        const rect = section.getBoundingClientRect();
        const scrollableDistance = Math.max(1, rect.height - window.innerHeight);
        const progress = Math.min(1, Math.max(0, -rect.top / scrollableDistance));
        const next = Math.min(2, Math.floor(Math.min(0.999, progress) * 3));

        setActivePain(next);

        const progressBar = section.querySelector<HTMLElement>(".why-progress");
        if (progressBar) {
          progressBar.style.transform = `scaleY(${progress})`;
        }
      });
    };

    updateWhyFallback();
    window.addEventListener("scroll", updateWhyFallback, { passive: true });
    window.addEventListener("resize", updateWhyFallback);

    return () => {
      if (frame) window.cancelAnimationFrame(frame);
      window.removeEventListener("scroll", updateWhyFallback);
      window.removeEventListener("resize", updateWhyFallback);
    };
  }, []);

  useEffect(() => {
    const gsap = window.gsap;
    const ScrollTrigger = window.ScrollTrigger;

    if (!gsap || !ScrollTrigger || !whyRef.current) {
      return;
    }

    gsap.registerPlugin?.(ScrollTrigger);

    const prefersReducedMotion = window.matchMedia("(prefers-reduced-motion: reduce)").matches;
    if (prefersReducedMotion) {
      return;
    }

    const setupWhyScroll = () => {
      const scrollTrigger = {
        trigger: whyRef.current,
        start: "top top",
        end: "bottom bottom",
        scrub: 0.2,
        onUpdate: (self: { progress: number }) => {
          const next = Math.min(2, Math.floor(self.progress * 3));
          setActivePain(next);
        },
      };

      gsap.to(".why-progress", {
        scaleY: 1,
        transformOrigin: "top",
        ease: "none",
        scrollTrigger,
      });
    };

    if (gsap.context) {
      const context = gsap.context(setupWhyScroll, whyRef.current);
      return () => context.revert?.();
    }

    setupWhyScroll();
  }, []);

  useEffect(() => {
    const updateComparisonProgress = () => {
      const section = pathsRef.current;
      if (!section) return;

      const rect = section.getBoundingClientRect();
      const scrollableDistance = Math.max(1, rect.height - window.innerHeight);
      const animationDistance = Math.min(scrollableDistance, Math.max(1, window.innerHeight * 0.72));
      const progress = Math.min(1, Math.max(0, -rect.top / animationDistance));
      const next = Math.min(
        comparisonRows.length - 1,
        Math.floor(Math.min(0.999, progress) * comparisonRows.length),
      );

      setActiveComparison(next);
      setComparisonProgress(progress);
    };

    updateComparisonProgress();
    const interval = window.setInterval(updateComparisonProgress, 120);
    window.addEventListener("scroll", updateComparisonProgress, { passive: true });
    window.addEventListener("resize", updateComparisonProgress);

    return () => {
      window.clearInterval(interval);
      window.removeEventListener("scroll", updateComparisonProgress);
      window.removeEventListener("resize", updateComparisonProgress);
    };
  }, []);

  return (
    <div className="min-h-screen bg-[#F7F5EE] text-[#101318] antialiased">
      <header className="fixed left-0 right-0 top-4 z-50 text-[#0A0D12]">
        <div className="pointer-events-none mx-auto flex max-w-7xl items-center justify-between px-5 md:px-8">
          <a
            href="#top"
            aria-label={`${productName} home`}
            className="pointer-events-auto rounded-full border border-white/28 bg-white/18 px-4 py-3 shadow-[0_10px_35px_rgba(10,13,18,0.08)] backdrop-blur-2xl"
          >
            <HyTriLogo />
          </a>
          <nav className="pointer-events-auto hidden items-center gap-1 rounded-full border border-white/24 bg-[#101318]/24 p-1 text-sm text-white shadow-[0_12px_40px_rgba(10,13,18,0.12)] backdrop-blur-2xl md:flex">
            <a className="rounded-full px-4 py-3 transition-colors hover:bg-white/14" href="#why">
              Problem
            </a>
            <a className="rounded-full px-4 py-3 transition-colors hover:bg-white/14" href="#demo">
              Demo
            </a>
            <a className="rounded-full px-4 py-3 transition-colors hover:bg-white/14" href="#report">
              Evidence
            </a>
            <a className="rounded-full px-4 py-3 transition-colors hover:bg-white/14" href="#workflows">
              Paths
            </a>
          </nav>
          <a
            href="/demo/saas-003"
            className="pointer-events-auto inline-flex items-center gap-2 rounded-full border border-white/26 bg-[#0B5CFF]/94 px-5 py-3 text-sm font-semibold text-white shadow-[0_12px_36px_rgba(11,92,255,0.22)] backdrop-blur-xl transition-transform hover:-translate-y-0.5"
          >
            Start SAAS-003 demo
            <ArrowRight className="h-4 w-4" />
          </a>
        </div>
      </header>

      <main id="top">
        <section
          ref={heroRef}
          className="relative min-h-[100svh] overflow-hidden bg-[#F7F5EE] text-[#0A0D12]"
        >
          <img
            src="/agent-validation-hero.png"
            alt=""
            aria-hidden="true"
            className="absolute inset-0 h-full w-full object-cover object-center"
          />
          <div className="absolute inset-0 bg-gradient-to-r from-[#F8F7F3]/32 via-[#F8F7F3]/8 to-transparent" />

          <div className="relative mx-auto flex min-h-[100svh] max-w-7xl items-start px-5 pb-12 pt-[8.75rem] md:px-8 md:pb-[15rem] md:pt-[10.25rem] lg:pt-[10.75rem] xl:pt-[11.25rem]">
            <div className="max-w-[700px] overflow-visible">
              <p className="hero-copy mb-4 inline-flex rounded-full bg-white/44 px-4 py-2 text-sm font-semibold text-[#0B5CFF] backdrop-blur-md">
                {investorOneLiner}
              </p>
              <h1 className="font-hero max-w-3xl overflow-visible text-[2.85rem] font-normal leading-[0.96] tracking-[0] text-[#090A0C] sm:text-[3.7rem] md:text-[4.65rem] xl:text-[5.2rem]">
                <span className="hero-title-line block">Agent Integration</span>
                <span className="hero-title-line block">Safety Sandbox</span>
                <span className="hero-script hero-handwriting mt-1 block md:mt-2" aria-label="for AI agents">
                  <span className="hero-handwriting-word" aria-hidden="true">for AI agents</span>
                </span>
              </h1>
              <p className="hero-copy mt-5 max-w-[610px] text-base leading-7 text-[#344054] md:mt-6 md:text-lg">
                AI agents are starting to create tickets, alerts, checks, and
                workflow state. HyTri runs them inside stateful twins and returns
                a decision packet before real systems are touched.
              </p>
              <div className="hero-actions mt-8 flex flex-col gap-3 sm:flex-row">
                <a
                  href="/demo/saas-003"
                  className="inline-flex items-center justify-center gap-2 rounded-full bg-[#0B5CFF] px-5 py-3.5 text-sm font-semibold text-white transition-transform hover:-translate-y-0.5"
                >
                  Start SAAS-003 demo
                  <Play className="h-4 w-4" />
                </a>
                <a
                  href="#why"
                  className="inline-flex items-center justify-center gap-2 rounded-full border border-[#0A0D12]/20 bg-white/12 px-5 py-3.5 text-sm font-semibold text-[#0A0D12] backdrop-blur-md transition-colors hover:bg-white/32"
                >
                  See why it matters
                  <Route className="h-4 w-4" />
                </a>
              </div>
              <div className="hero-actions mt-8 md:hidden">
                <OutcomeRail />
              </div>
            </div>
          </div>
          <div className="absolute bottom-5 left-0 right-0 hidden px-5 md:block md:px-8">
            <div className="mx-auto max-w-7xl">
              <OutcomeRail dark />
            </div>
          </div>
        </section>

        <section ref={whyRef} id="why" className="relative min-h-[320svh] bg-[#F8F7F1] text-[#0A0D12]">
          <div className="why-stage sticky top-0 flex min-h-[100dvh] items-start px-5 py-8 md:px-8 lg:items-center">
            <div className="mx-auto grid w-full max-w-7xl items-center gap-1 lg:grid-cols-[0.34fr_0.66fr] lg:gap-8">
              <div className="flex items-center justify-start self-center py-4 lg:min-h-[58svh] lg:py-0">
                <div className="flex items-center gap-5 sm:gap-7 lg:-translate-x-6 lg:gap-8 xl:-translate-x-10">
                  <div className="h-32 w-px shrink-0 overflow-hidden bg-[#DAD6CA] sm:h-40 lg:h-44">
                    <div className="why-progress h-full w-px origin-top scale-y-0 bg-[#0B5CFF]" />
                  </div>
                  <h2 className="font-hero max-w-[520px] text-[3rem] font-normal leading-[0.94] tracking-[0] text-[#090A0C] sm:text-[4rem] md:text-[5rem] lg:text-[5.35rem]">
                    <span className="block">Clean tests</span>
                    <span className="block">can miss</span>
                    <span className="block">agent side effects.</span>
                  </h2>
                </div>
              </div>

              <div className="border-y border-[#DAD6CA]">
                {painPoints.map((pain, index) => {
                  const isActive = activePain === index;
                  return (
                    <article
                      key={pain.number}
                      className={`grid gap-3 border-b border-[#DAD6CA] py-3.5 transition-all duration-300 last:border-b-0 md:grid-cols-[0.13fr_0.87fr] md:py-[1.125rem] ${
                        isActive ? "opacity-100" : "opacity-35"
                      }`}
                    >
                      <div className="flex items-start gap-4">
                        <span
                          className={`font-mono text-[3rem] leading-none tracking-[0] transition-colors md:text-[4.45rem] ${
                            isActive ? "text-[#0B5CFF]" : "text-[#101318]/25"
                          }`}
                        >
                          {pain.number}
                        </span>
                      </div>
                      <div className="max-w-3xl">
                        <h3 className="max-w-3xl text-[1.35rem] font-semibold leading-[1.04] tracking-[0] text-[#101318] md:text-[2.38rem]">
                          {pain.title}
                        </h3>
                        <p className="mt-2.5 max-w-2xl text-sm leading-6 text-[#58606B] md:text-base md:leading-6">
                          {pain.body}
                        </p>
                      </div>
                    </article>
                  );
                })}
              </div>
            </div>
          </div>
        </section>

        <section ref={pathsRef} id="paths" className="relative px-5 py-20 md:min-h-[180svh] md:px-8 md:pb-12 md:pt-28">
          <div className="absolute inset-0 bg-[#F8F7F1]" />
          <div className="absolute inset-0 bg-[linear-gradient(90deg,rgba(10,13,18,0.045)_1px,transparent_1px)] bg-[size:52px_52px]" />
          <div className="relative mx-auto grid max-w-7xl overflow-hidden border border-[#DAD6CA]/80 bg-[#FBFAF5]/88 backdrop-blur-[2px] md:sticky md:top-24 lg:grid-cols-[0.44fr_0.56fr]">
            <div className="flex min-h-[520px] flex-col justify-center border-b border-[#DAD6CA] px-6 py-12 md:px-10 lg:border-b-0 lg:border-r lg:px-14">
              <p className="mb-8 max-w-sm text-xs font-semibold uppercase text-[#0B5CFF]">
                Why current tests are not enough
              </p>
              <h2 className="max-w-[680px] text-[2.25rem] font-semibold leading-[0.96] tracking-[0] text-[#090A0C] sm:text-[3.05rem] md:text-[3.45rem]">
                <span className="block">Clean mocks prove</span>
                <span className="block">the call path.</span>
                <span className="block">HyTri proves the</span>
                <span className="block">side-effect path.</span>
              </h2>
              <p className="mt-9 max-w-md text-base leading-7 text-[#58606B]">
                Most teams can prove that an agent ran. That still does not prove
                it stayed safe when service state repeated, rejected, drifted, or
                committed ambiguously.
              </p>
              <p className="mt-6 max-w-md text-base leading-7 text-[#58606B]">
                HyTri lets the agent mutate a stateful twin, injects the edge
                case, then returns evidence before production systems are touched.
              </p>
              <div className="mt-10 max-w-md">
                <div className="h-1 overflow-hidden bg-[#DAD6CA]">
                  <div
                    className="paths-progress h-full origin-left bg-[#0B5CFF] transition-transform duration-150"
                    style={{ transform: `scaleX(${comparisonProgress})` }}
                  />
                </div>
                <p className="mt-3 text-sm font-semibold text-[#0B5CFF]">
                  Reading contrast {activeComparison + 1} / {comparisonRows.length}
                </p>
              </div>
            </div>

            <div className="grid grid-cols-2 bg-white text-center">
              <div className="border-b border-r border-[#DAD6CA] bg-[#090A0C] px-4 py-5 font-mono text-lg text-white md:text-2xl">
                Current testing
              </div>
              <div className="border-b border-[#DAD6CA] bg-[#0B5CFF] px-4 py-5 font-mono text-lg text-white md:text-2xl">
                Safety sandbox
              </div>
              {comparisonRows.map((row, index) => {
                const isActive = activeComparison === index;
                const hasPassed = activeComparison > index;

                return (
                  <React.Fragment key={row.current}>
                    <div
                      className={`flex min-h-32 items-center justify-center border-b border-r border-[#E6E0D3] px-5 py-7 text-sm leading-6 transition-all duration-500 md:px-8 md:text-base ${
                        isActive
                          ? "bg-[#FBFAF5] text-[#101318] opacity-100"
                          : hasPassed
                            ? "bg-white text-[#58606B] opacity-65"
                            : "bg-white text-[#26313F] opacity-45"
                      }`}
                    >
                      {row.current}
                    </div>
                    <div
                      className={`relative flex min-h-32 items-center justify-center border-b border-[#E6E0D3] px-5 py-7 text-sm leading-6 transition-all duration-500 md:px-8 md:text-base ${
                        isActive
                          ? "bg-[#EAF2FF] text-[#0A0D12] opacity-100 shadow-[inset_4px_0_0_#0B5CFF]"
                          : hasPassed
                            ? "bg-white text-[#26313F] opacity-80"
                            : "bg-white text-[#101318] opacity-55"
                      }`}
                    >
                      {isActive ? (
                        <span className="absolute left-4 top-4 h-2 w-2 rounded-full bg-[#0B5CFF]" aria-hidden="true" />
                      ) : null}
                      {row.safety}
                    </div>
                  </React.Fragment>
                );
              })}
            </div>
          </div>
        </section>

        <section id="demo" className="relative overflow-hidden bg-[#F8F7F1] px-5 py-20 text-[#0A0D12] md:px-8 md:py-24">
          <div className="absolute inset-0 bg-[linear-gradient(90deg,rgba(10,13,18,0.055)_1px,transparent_1px)] bg-[size:52px_52px]" />
          <div className="relative mx-auto max-w-7xl">
            <p className="text-center text-xs font-semibold uppercase tracking-[0] text-[#0B5CFF]">
              Four-step validation run
            </p>
            <h2 className="mx-auto mt-6 max-w-5xl text-center font-mono text-[2.5rem] font-normal leading-[1.08] tracking-[0] text-[#090A0C] sm:text-[3.35rem] md:text-[4.15rem]">
              Run the incident before production can.
            </h2>
            <p className="mx-auto mt-6 max-w-2xl text-center text-base leading-7 text-[#58606B] md:text-lg">
              Seed service state, inject one edge case, let the agent act, then
              return the evidence packet.
            </p>

            <div className="mt-16 grid border border-[#DAD6CA]/80 bg-[#FBFAF5]/88 backdrop-blur-[2px] lg:grid-cols-2">
              {crashTestFeatures.map((feature) => (
                <article
                  key={feature.title}
                  className="min-h-[430px] border-b border-[#DAD6CA]/80 p-6 last:border-b-0 lg:border-r lg:[&:nth-child(2n)]:border-r-0 lg:[&:nth-last-child(-n+2)]:border-b-0 md:p-9"
                >
                  <h3 className="font-mono text-3xl font-normal leading-tight tracking-[0] text-[#090A0C] md:text-4xl">
                    {feature.title}
                  </h3>
                  <p className="mt-5 max-w-lg text-base leading-7 text-[#58606B]">
                    {feature.body}
                  </p>
                  <div className="mt-10 flex items-center justify-center">
                    <FeatureVisual visual={feature.visual} />
                  </div>
                </article>
              ))}
            </div>
          </div>
        </section>

        <section id="report" className="px-5 py-20 md:px-8 md:py-28">
          <SectionHeader
            eyebrow="What comes back"
            title="The result is a decision packet, not a log dump."
            body="Every failed run explains what changed, why it is unsafe, what guardrail should stop it, and how to rerun the same scenario as a regression."
          />
          <div className="mx-auto mt-14 max-w-6xl border border-[#DAD6CA] bg-white">
            {incidentCards.map((card, index) => (
              <div key={card.policy} className="grid border-b border-[#E6E0D3] last:border-b-0 lg:grid-cols-[0.38fr_0.62fr]">
                <div className="border-b border-[#E6E0D3] p-6 lg:border-b-0 lg:border-r">
                  <div className="flex items-center gap-3 text-[#0B5CFF]">
                    <TriangleAlert className="h-5 w-5" />
                    <span className="text-xs font-semibold uppercase">
                      Incident {String(index + 1).padStart(2, "0")}
                    </span>
                  </div>
                  <h3 className="mt-4 break-words font-mono text-lg font-semibold text-[#101318]">
                    {card.policy}
                  </h3>
                </div>
                <div className="grid gap-0 sm:grid-cols-3">
                  <div className="border-b border-[#E6E0D3] p-6 sm:border-b-0 sm:border-r">
                    <p className="text-xs font-semibold uppercase text-[#667085]">
                      What happened
                    </p>
                    <p className="mt-3 text-sm leading-6 text-[#26313F]">{card.happened}</p>
                  </div>
                  <div className="border-b border-[#E6E0D3] p-6 sm:border-b-0 sm:border-r">
                    <p className="text-xs font-semibold uppercase text-[#667085]">
                      Why it matters
                    </p>
                    <p className="mt-3 text-sm leading-6 text-[#26313F]">{card.matters}</p>
                  </div>
                  <div className="p-6">
                    <p className="text-xs font-semibold uppercase text-[#667085]">
                      Guardrail
                    </p>
                    <p className="mt-3 text-sm leading-6 text-[#26313F]">{card.guardrail}</p>
                  </div>
                </div>
              </div>
            ))}
          </div>
          <div className="mx-auto mt-8 grid max-w-6xl border border-[#DAD6CA] bg-[#101318] text-white lg:grid-cols-[0.38fr_0.62fr]">
            <div className="border-b border-white/14 p-6 lg:border-b-0 lg:border-r">
              <p className="text-xs font-semibold uppercase tracking-[0] text-[#8CB3FF]">
                Demo packet
              </p>
              <h3 className="mt-4 text-3xl font-semibold leading-tight">
                Open the evidence behind the claim.
              </h3>
              <p className="mt-5 text-sm leading-6 text-white/62">
                SAAS-003 is packaged like a review artifact: summary,
                policy report, state diff, patch hints, and trace evidence.
              </p>
            </div>
            <div className="px-6 py-3">
              <ArtifactLinkList artifacts={homeArtifactLinks} dark />
            </div>
          </div>
        </section>

        <WorkflowSection />

        <PocHandoffSection />

        <section id="start" className="bg-[#0B5CFF] px-5 py-16 text-white md:px-8">
          <div className="mx-auto grid max-w-7xl items-center gap-8 md:grid-cols-[1fr_auto]">
            <div>
              <p className="text-xs font-semibold uppercase text-white/65">
                Next step
              </p>
              <h2 className="mt-3 max-w-3xl text-3xl font-semibold md:text-5xl">
                Start with SAAS-003, then map one focused workflow.
              </h2>
            </div>
            <div className="flex flex-col gap-3 sm:flex-row md:flex-col">
              <a
                href="/demo/saas-003"
                className="inline-flex items-center justify-center gap-2 bg-white px-5 py-3 font-semibold text-[#0B5CFF] transition-transform hover:-translate-y-0.5"
              >
                Start SAAS-003 demo
                <Play className="h-4 w-4" />
              </a>
              <a
                href="/demo/connect#design-partner"
                className="inline-flex items-center justify-center gap-2 border border-white/30 px-5 py-3 font-semibold text-white transition-colors hover:bg-white/10"
              >
                Plan POC input
                <ClipboardCheck className="h-4 w-4" />
              </a>
            </div>
          </div>
        </section>
      </main>
    </div>
  );
}
