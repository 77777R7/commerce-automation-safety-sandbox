import React, { useEffect, useRef, useState } from "react";
import ArrowRight from "lucide-react/dist/esm/icons/arrow-right.js";
import Box from "lucide-react/dist/esm/icons/box.js";
import CheckCircle2 from "lucide-react/dist/esm/icons/check-circle-2.js";
import ChevronRight from "lucide-react/dist/esm/icons/chevron-right.js";
import ClipboardCheck from "lucide-react/dist/esm/icons/clipboard-check.js";
import Code2 from "lucide-react/dist/esm/icons/code-2.js";
import CreditCard from "lucide-react/dist/esm/icons/credit-card.js";
import ExternalLink from "lucide-react/dist/esm/icons/external-link.js";
import FileText from "lucide-react/dist/esm/icons/file-text.js";
import GitPullRequest from "lucide-react/dist/esm/icons/git-pull-request.js";
import Github from "lucide-react/dist/esm/icons/github.js";
import History from "lucide-react/dist/esm/icons/history.js";
import Layers3 from "lucide-react/dist/esm/icons/layers-3.js";
import ListChecks from "lucide-react/dist/esm/icons/list-checks.js";
import MessageCircle from "lucide-react/dist/esm/icons/message-circle.js";
import Play from "lucide-react/dist/esm/icons/play.js";
import Settings from "lucide-react/dist/esm/icons/settings.js";
import Slack from "lucide-react/dist/esm/icons/slack.js";
import TriangleAlert from "lucide-react/dist/esm/icons/triangle-alert.js";
import LiveDashboardHomePage from "./Dashboard";

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

const productName = "HyTri Labs";
const investorOneLiner = "Catch unsafe agent side effects before production does.";

const plainEnglishIncident = {
  setup: "One duplicate service event reached the agent twice.",
  observed: "It created two human alerts and two recovery checks.",
  fix: "Store the event ID before any downstream action.",
};

const outcomeRail = [
  {
    label: "Expected",
    value: "1 alert + 1 recovery check",
    body: "One incident should create one human notification and one engineering path.",
  },
  {
    label: "Observed",
    value: "2 alerts + 2 recovery checks",
    body: "The unsafe agent treated the duplicate event as new work.",
  },
  {
    label: "Fix",
    value: "Persist event ID first",
    body: "Deduplicate before alerts, tickets, checks, refunds, or workflow writes.",
  },
];

const homeArtifactLinks = [
  {
    title: "Review summary",
    body: "The plain-English pass/fail result a reviewer can understand first.",
    href: "/artifacts/saas-003/failed/github_check_summary.md",
  },
  {
    title: "Policy decision",
    body: "The structured safety finding, severity, and recommendation.",
    href: "/artifacts/saas-003/failed/policy_report.json",
  },
  {
    title: "State diff",
    body: "The before/after side effects that prove what actually changed.",
    href: "/artifacts/saas-003/failed/state_diff.json",
  },
  {
    title: "Fix hints",
    body: "The smallest repair rule the agent builder can act on.",
    href: "/artifacts/saas-003/failed/patch_hints.md",
  },
];

const buildReviewArtifacts = (run: "failed" | "passed") => [
  {
    title: "Review summary",
    href: `/artifacts/saas-003/${run}/github_check_summary.md`,
    body: "Reviewer-friendly result, conclusion, and annotations.",
  },
  {
    title: "Policy decision",
    href: `/artifacts/saas-003/${run}/policy_report.json`,
    body: "Structured findings for automation and audit.",
  },
  {
    title: "State diff",
    href: `/artifacts/saas-003/${run}/state_diff.json`,
    body: "Before and after state across the twin.",
  },
  {
    title: "Fix hints",
    href: `/artifacts/saas-003/${run}/patch_hints.md`,
    body: "The smallest guardrail needed before production.",
  },
  {
    title: "Agent action ledger",
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
    label: "Investor",
    fit: "Use this for the 30-second product story: unsafe agent side effects caught before production.",
    scope:
      "Open SAAS-003 and show the plain-English incident: expected one recovery path, observed two, fixed by event ID persistence.",
    status: "Open demo dashboard",
    href: "/dashboard",
  },
  {
    label: "Design Partner",
    fit: "Use this when a team wants to map one risky workflow into a repeatable validation scenario.",
    scope:
      "Bring one workflow, name the side effects that must happen exactly once, and leave with a decision packet.",
    status: "Plan POC workflow",
    href: "/demo/connect#design-partner",
  },
  {
    label: "Agent Builder",
    fit: "Use this when a builder wants to run an external agent through MCP or HTTP instead of reading static artifacts.",
    scope:
      "Give the agent the scenario prompt, let it act through the sandbox surface, then inspect trace, state diff, and fix hints.",
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

const incidentReviewFacts = [
  {
    label: "Expected",
    value: "1 alert + 1 recovery check",
    body: "One upstream incident should create one human notification and one engineering recovery path.",
  },
  {
    label: "Observed",
    value: "2 alerts + 2 recovery checks",
    body: "The unsafe run repeated both downstream side effects when the same event arrived again.",
  },
  {
    label: "Required control",
    value: "Persist event ID before side effects",
    body: "Use the upstream event ID as the idempotency key before alerts, checks, tickets, or workflow writes.",
  },
];

const reviewerChecklist = [
  "Stateful twin replayed the duplicate delivery.",
  "Agent actions were allowed inside the sandbox.",
  "Policy pack read the event ledger and state diff.",
  "Decision packet returned review summary, policy decision, state diff, and fix hints.",
];

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
      "Use this path when the goal is comprehension in 30 seconds: one duplicate event, one blocked run, one repair rule.",
    steps: [
      "Open the demo dashboard",
      "Show Expected / Observed / Fix",
      "Open the review summary",
    ],
    cta: "Open demo dashboard",
    href: "/dashboard",
  },
  {
    id: "design-partner",
    title: "Design partner POC",
    body:
      "Use this path when a team wants to bring one real workflow and see whether it can become a repeatable validation scenario.",
    steps: [
      "Bring one workflow",
      "Name the external writes",
      "Receive one decision packet",
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
      "Read trace, state diff, and fix hints",
    ],
    cta: "Open agent prompt",
    href: "/artifacts/saas-003/external_agent_prompt.md",
  },
];

const pocSteps = [
  {
    label: "Input",
    title: "One workflow with external writes",
    body:
      "Use a staging agent, synthetic event, or redacted action log. Production credentials are not needed.",
  },
  {
    label: "Run",
    title: "One scenario pack",
    body:
      "Start with SAAS-003, then map the closest retry, duplicate, timeout, rejection, or stale-state edge case.",
  },
  {
    label: "Output",
    title: "Decision packet",
    body:
      "Return trace highlights, state changes, policy findings, fix hints, and a scenario that can become a regression check.",
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

function HyTriMark({ className = "" }: { className?: string }) {
  return (
    <div className={`flex flex-col gap-[3px] ${className}`} aria-hidden="true">
      <div className="flex gap-[3px]">
        <div className="h-5 w-4 skew-x-[-12deg] rounded-[1px] bg-black" />
        <div className="h-5 w-7 skew-x-[-12deg] rounded-[1px] bg-black" />
      </div>
      <div className="-ml-[2px] flex gap-[3px]">
        <div className="h-5 w-3 skew-x-[-12deg] rounded-[1px] bg-black" />
        <div className="h-5 w-8 skew-x-[-12deg] rounded-[1px] bg-black" />
      </div>
    </div>
  );
}

function HyTriLogo() {
  return (
    <div className="flex items-center gap-3" aria-hidden="true">
      <HyTriMark />
      <span className="font-logo flex items-baseline gap-[0.18em] text-[1.72rem] font-semibold leading-none tracking-[0] text-black">
        <span>HyTri</span>
        <span>Labs</span>
      </span>
    </div>
  );
}

const featureVisuals: Record<string, { alt: string; src: string }> = {
  state: {
    alt: "Abstract service twin, seeded state, and event ledger diagram",
    src: "/feature-seed-twins-serious.png",
  },
  faults: {
    alt: "Abstract duplicate event and edge-case injection diagram",
    src: "/feature-inject-edge-case-serious.png",
  },
  agent: {
    alt: "Abstract agent action lane and sandbox tool execution diagram",
    src: "/feature-let-agents-act-serious.png",
  },
  evidence: {
    alt: "Abstract evidence packet, trace, state diff, and policy finding diagram",
    src: "/feature-return-evidence-serious.png",
  },
};

function FeatureVisual({ visual }: { visual: string }) {
  const asset = featureVisuals[visual] ?? featureVisuals.state;

  return (
    <img
      src={asset.src}
      alt={asset.alt}
      className="w-full max-w-xl border border-[#DAD6CA] bg-[#F7F5EF] object-cover"
      loading="lazy"
    />
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
  const reviewStatus = hasFinding ? "Blocked before production" : "Safe to continue";
  const reviewStatusBody = hasFinding
    ? "One duplicate event produced duplicate alerts and recovery checks inside the sandbox."
    : "The duplicate event replayed, but the agent created exactly one alert and one recovery check.";
  const checkSummary = hasFinding
    ? "1 high-severity policy failed"
    : "0 policy findings";
  const checkAction = hasFinding
    ? "Persist the upstream event ID before any downstream side effect."
    : "Keep SAAS-003 as a regression check for future agent changes.";
  const primaryArtifacts = reviewArtifacts.slice(0, 3);
  const secondaryArtifacts = reviewArtifacts.slice(3);

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
        <section className="px-5 pb-10 pt-10 md:px-8 md:pb-14 md:pt-14">
          <div className="mx-auto max-w-7xl">
            <div className="grid gap-8 lg:grid-cols-[0.56fr_0.44fr] lg:items-center">
              <div>
                <p className="text-xs font-semibold uppercase tracking-[0] text-[#0B5CFF]">
                  Incident review / PR check result
                </p>
                <h1 className="mt-4 max-w-3xl text-[2.25rem] font-semibold leading-[1.04] tracking-[0] text-[#090A0C] md:text-[3.85rem]">
                  Duplicate webhook recovery work.
                </h1>
                <p className="mt-6 max-w-2xl text-lg leading-8 text-[#58606B]">
                  SAAS-003 shows whether an action-taking agent turns one duplicate
                  event into repeated downstream work.
                </p>
              </div>
              <div className="border border-[#DAD6CA] bg-white p-5">
                <div className="flex items-start justify-between gap-4">
                  <div className="flex items-start gap-3">
                    <div
                      className={`mt-0.5 flex h-8 w-8 shrink-0 items-center justify-center rounded-full ${
                        hasFinding ? "bg-[#D94A17] text-white" : "bg-[#11845B] text-white"
                      }`}
                    >
                      {hasFinding ? <TriangleAlert className="h-4 w-4" /> : <CheckCircle2 className="h-4 w-4" />}
                    </div>
                    <div>
                      <p className="text-xs font-semibold uppercase tracking-[0] text-[#667085]">
                        Check run
                      </p>
                      <p className="mt-1 text-2xl font-semibold leading-tight text-[#101318]">
                        {reviewStatus}
                      </p>
                    </div>
                  </div>
                  <div
                    className={`shrink-0 border px-2.5 py-1 text-xs font-semibold uppercase tracking-[0] ${
                      hasFinding
                        ? "border-[#F3B99F] bg-[#FFF7F1] text-[#C2410C]"
                        : "border-[#9BE6C2] bg-[#F0FFF7] text-[#047857]"
                    }`}
                  >
                    {run.status}
                  </div>
                </div>
                <p className="mt-4 text-sm leading-6 text-[#26313F]">{reviewStatusBody}</p>
                <div className="mt-5 grid gap-3 sm:grid-cols-3">
                  <div>
                    <p className="text-xs font-semibold uppercase tracking-[0] text-[#667085]">Finding</p>
                    <p className={hasFinding ? "mt-1 text-sm font-semibold text-[#C2410C]" : "mt-1 text-sm font-semibold text-[#047857]"}>
                      {checkSummary}
                    </p>
                  </div>
                  <div>
                    <p className="text-xs font-semibold uppercase tracking-[0] text-[#667085]">Writes</p>
                    <p className="mt-1 text-sm font-semibold text-[#101318]">0 production writes</p>
                  </div>
                  <div>
                    <p className="text-xs font-semibold uppercase tracking-[0] text-[#667085]">Fix</p>
                    <p className="mt-1 text-sm font-semibold text-[#101318]">Persist event ID</p>
                  </div>
                </div>
              </div>
            </div>

            <div className="mt-8 border border-[#DAD6CA] bg-white">
              <div className="grid md:grid-cols-3">
                {incidentReviewFacts.map((fact) => (
                  <div
                    key={fact.label}
                    className="border-b border-[#E6E0D3] p-4 last:border-b-0 md:border-b-0 md:border-r md:last:border-r-0"
                  >
                    <p className="text-xs font-semibold uppercase tracking-[0] text-[#667085]">
                      {fact.label}
                    </p>
                    <p
                      className={`mt-2 font-mono text-2xl leading-tight ${
                        fact.label === "Observed" ? "text-[#C2410C]" : "text-[#0B5CFF]"
                      }`}
                    >
                      {fact.value}
                    </p>
                    <p className="mt-2 text-sm leading-5 text-[#58606B]">{fact.body}</p>
                  </div>
                ))}
              </div>
            </div>
          </div>
        </section>

        <section className="px-5 pb-20 md:px-8 md:pb-28">
          <div className="mx-auto max-w-7xl">
            <div className="border border-[#DAD6CA] bg-white">
              <div className="grid border-b border-[#DAD6CA] lg:grid-cols-[1fr_auto]">
                <div className="p-6 md:p-8">
                  <p className="text-xs font-semibold uppercase tracking-[0] text-[#667085]">
                    PR check replay
                  </p>
                  <h2 className="mt-3 text-3xl font-semibold tracking-[0] text-[#101318] md:text-4xl">
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
                    Failed run
                  </button>
                  <button
                    type="button"
                    onClick={() => setMode("good")}
                    className={`h-12 min-w-32 rounded-full px-5 text-sm font-semibold transition-colors ${
                      !isBad ? "bg-[#0B5CFF] text-white" : "bg-[#F0EEE5] text-[#58606B] hover:bg-[#E7E2D5]"
                    }`}
                  >
                    Passed run
                  </button>
                </div>
              </div>

              <div className="grid lg:grid-cols-[0.55fr_0.45fr]">
                <div className="border-b border-[#DAD6CA] p-6 lg:border-b-0 lg:border-r md:p-8">
                  <p className="text-xs font-semibold uppercase tracking-[0] text-[#0B5CFF]">
                    Run timeline
                  </p>
                  <div className="mt-5 divide-y divide-[#E6E0D3]">
                    {run.timeline.map((item, index) => (
                      <div key={item} className="grid grid-cols-[2rem_1fr] gap-4 py-4 first:pt-0 last:pb-0">
                        <div className="flex h-8 w-8 items-center justify-center rounded-full bg-[#0B5CFF] font-mono text-xs text-white">
                          {index + 1}
                        </div>
                        <p className="pt-1 text-sm leading-6 text-[#26313F]">{item}</p>
                      </div>
                    ))}
                  </div>
                </div>

                <aside className="p-6 md:p-8">
                  <div className="flex items-center gap-3">
                    {isBad ? (
                      <TriangleAlert className="h-5 w-5 text-[#C2410C]" />
                    ) : (
                      <CheckCircle2 className="h-5 w-5 text-[#0B5CFF]" />
                    )}
                    <p className="text-xs font-semibold uppercase tracking-[0] text-[#667085]">
                      Policy decision
                    </p>
                  </div>
                  <h3 className="mt-4 text-2xl font-semibold leading-tight tracking-[0] text-[#101318]">
                    {run.finding.title}
                  </h3>
                  <p className="mt-4 text-sm leading-6 text-[#58606B]">{run.finding.summary}</p>

                  <div className="mt-6 border-y border-[#E6E0D3] py-5">
                    <p className="text-xs font-semibold uppercase tracking-[0] text-[#667085]">
                      Required control
                    </p>
                    <p className="mt-2 text-sm font-semibold leading-6 text-[#0B5CFF]">{run.finding.recommendation}</p>
                  </div>

                  <details className="mt-5 border border-[#E6E0D3] bg-[#FBFAF5]">
                    <summary className="cursor-pointer p-4 text-sm font-semibold text-[#101318]">
                      Show repair hints
                    </summary>
                    <div className="border-t border-[#E6E0D3] p-4 pt-1">
                      {run.patchHints.map((hint) => (
                        <div key={hint} className="mt-3 flex gap-3 text-sm leading-6 text-[#26313F]">
                          <CheckCircle2 className="mt-0.5 h-4 w-4 shrink-0 text-[#0B5CFF]" />
                          <span>{hint}</span>
                        </div>
                      ))}
                    </div>
                  </details>
                </aside>
              </div>
            </div>

            <div className="mt-6 border border-[#DAD6CA] bg-white p-6 md:p-8">
              <div className="flex flex-col gap-4 md:flex-row md:items-end md:justify-between">
                <div>
                  <p className="text-xs font-semibold uppercase tracking-[0] text-[#667085]">
                    Evidence packet
                  </p>
                  <h3 className="mt-3 text-2xl font-semibold tracking-[0] text-[#101318]">
                    Three files tell the story.
                  </h3>
                </div>
                <p className="max-w-md text-sm leading-6 text-[#667085]">
                  Start with the review summary, policy decision, and state diff.
                  The remaining files stay available for deeper audit.
                </p>
              </div>

              <div className="mt-6 grid gap-3 md:grid-cols-3">
                {primaryArtifacts.map((artifact, index) => (
                  <a
                    key={artifact.href}
                    href={artifact.href}
                    target="_blank"
                    rel="noreferrer"
                    className="group border border-[#E6E0D3] bg-[#FBFAF5] p-4 transition-colors hover:border-[#0B5CFF] hover:bg-white"
                  >
                    <div className="flex items-start justify-between gap-3">
                      <span className="flex h-8 w-8 shrink-0 items-center justify-center border border-[#DAD6CA] bg-white font-mono text-xs text-[#0B5CFF]">
                        {String(index + 1).padStart(2, "0")}
                      </span>
                      <ExternalLink className="h-4 w-4 shrink-0 text-[#98A2B3] transition-transform group-hover:translate-x-0.5 group-hover:text-[#0B5CFF]" />
                    </div>
                    <p className="mt-4 text-sm font-semibold text-[#101318]">{artifact.title}</p>
                    <p className="mt-2 text-sm leading-5 text-[#667085]">{artifact.body}</p>
                    <p className="mt-4 border-t border-[#E6E0D3] pt-3 font-mono text-xs leading-5 text-[#667085]">
                      {artifact.href.split("/").pop()}
                    </p>
                  </a>
                ))}
              </div>

              <details className="mt-4 border border-[#E6E0D3] bg-[#FBFAF5]">
                <summary className="cursor-pointer p-4 text-sm font-semibold text-[#101318]">
                  Show all 6 artifacts
                </summary>
                <div className="grid gap-3 border-t border-[#E6E0D3] p-4 md:grid-cols-3">
                  {secondaryArtifacts.map((artifact, index) => (
                    <a
                      key={artifact.href}
                      href={artifact.href}
                      target="_blank"
                      rel="noreferrer"
                      className="group border border-[#E6E0D3] bg-white p-4 transition-colors hover:border-[#0B5CFF]"
                    >
                      <div className="flex items-start justify-between gap-3">
                        <span className="font-mono text-xs text-[#0B5CFF]">
                          {String(index + primaryArtifacts.length + 1).padStart(2, "0")}
                        </span>
                        <ExternalLink className="h-4 w-4 shrink-0 text-[#98A2B3] transition-transform group-hover:translate-x-0.5 group-hover:text-[#0B5CFF]" />
                      </div>
                      <p className="mt-3 text-sm font-semibold text-[#101318]">{artifact.title}</p>
                      <p className="mt-2 font-mono text-xs leading-5 text-[#667085]">{artifact.href.split("/").pop()}</p>
                    </a>
                  ))}
                </div>
              </details>
            </div>

            <div className="mt-6 grid gap-4 lg:grid-cols-2">
              <details className="border border-[#DAD6CA] bg-white">
                <summary className="cursor-pointer p-5 text-sm font-semibold uppercase tracking-[0] text-[#0B5CFF]">
                  Why this is not a mock
                </summary>
                <div className="grid gap-3 border-t border-[#E6E0D3] p-5 md:grid-cols-2">
                  {reviewerChecklist.map((item) => (
                    <div key={item} className="flex gap-3 border border-[#E6E0D3] bg-[#FBFAF5] p-4">
                      <ClipboardCheck className="mt-0.5 h-4 w-4 shrink-0 text-[#0B5CFF]" />
                      <p className="text-sm leading-6 text-[#26313F]">{item}</p>
                    </div>
                  ))}
                </div>
              </details>

              <details className="border border-[#DAD6CA] bg-white">
                <summary className="cursor-pointer p-5 text-sm font-semibold uppercase tracking-[0] text-[#0B5CFF]">
                  State changes
                </summary>
                <div className="overflow-x-auto border-t border-[#E6E0D3]">
                  <div className="min-w-[42rem]">
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
              </details>
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
        eyebrow="Where to go next"
        title="Three paths from the same proof."
        body="Investors need the incident in plain English. Design partners need a POC shape. Agent builders need the tool path and artifacts."
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
            Bring one risky workflow. Leave with evidence a buyer can review.
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

type DashboardView = "pr" | "twins" | "scenarios" | "tests";
type DashboardRunStatus = "failed" | "passed" | "running";
type DashboardIcon = React.ComponentType<{ className?: string }>;

const dashboardNav: Array<{
  id: DashboardView;
  label: string;
  section: "Environments" | "Tests";
  icon: DashboardIcon;
}> = [
  { id: "pr", label: "PR Test Runs", section: "Environments", icon: GitPullRequest },
  { id: "twins", label: "Twin Runs", section: "Environments", icon: Layers3 },
  { id: "scenarios", label: "Scenarios", section: "Environments", icon: ListChecks },
  { id: "tests", label: "Test Runs", section: "Tests", icon: History },
];

const utilityNav: Array<{ label: string; icon: DashboardIcon }> = [
  { label: "Ask", icon: MessageCircle },
  { label: "MCP", icon: Code2 },
  { label: "Settings", icon: Settings },
];

const dashboardRuns = [
  {
    id: "saas003-failed",
    scenario: "SAAS-003",
    title: "Duplicate webhook recovery work",
    repo: "77777R7/commerce-automation-safety-sandbox",
    pr: "#42",
    sha: "abc123",
    mode: "Unsafe agent",
    status: "failed" as DashboardRunStatus,
    conclusion: "failure",
    time: "2 min ago",
    summary:
      "One Stripe event produced duplicate Slack alerts and duplicate GitHub recovery checks.",
    policy: "stripe_duplicate_webhook_side_effects_must_be_deduped",
    expected: "1 Slack alert, 1 GitHub check",
    observed: "2 Slack alerts, 2 GitHub checks",
    repair: "Persist Stripe event ID before side effects",
    artifactRoot: "/artifacts/saas-003/failed",
    signals: [
      { label: "Stripe deliveries", value: "2", tone: "blue" },
      { label: "Slack alerts", value: "2", tone: "red" },
      { label: "GitHub checks", value: "2", tone: "red" },
      { label: "Findings", value: "1 high", tone: "red" },
    ],
  },
  {
    id: "saas003-passed",
    scenario: "SAAS-003",
    title: "Duplicate webhook deduped",
    repo: "77777R7/commerce-automation-safety-sandbox",
    pr: "#42",
    sha: "def456",
    mode: "Safe repair",
    status: "passed" as DashboardRunStatus,
    conclusion: "success",
    time: "5 min ago",
    summary:
      "The duplicate Stripe delivery replayed, but the agent created exactly one alert and one check.",
    policy: "no_policy_findings",
    expected: "1 Slack alert, 1 GitHub check",
    observed: "1 Slack alert, 1 GitHub check",
    repair: "Keep idempotency guardrail as regression",
    artifactRoot: "/artifacts/saas-003/passed",
    signals: [
      { label: "Stripe deliveries", value: "2", tone: "blue" },
      { label: "Slack alerts", value: "1", tone: "green" },
      { label: "GitHub checks", value: "1", tone: "green" },
      { label: "Findings", value: "0", tone: "green" },
    ],
  },
  {
    id: "saas001-failed",
    scenario: "SAAS-001",
    title: "Failed payment published success state",
    repo: "demo/billing-agent",
    pr: "#17",
    sha: "91b7c0",
    mode: "Unsafe agent",
    status: "failed" as DashboardRunStatus,
    conclusion: "failure",
    time: "18 min ago",
    summary:
      "A failed billing event still posted a success signal, which would mislead reviewers.",
    policy: "github_check_must_match_policy_status",
    expected: "action_required",
    observed: "success",
    repair: "Gate GitHub check conclusion on policy status",
    artifactRoot: "/artifacts/saas-003/failed",
    signals: [
      { label: "Stripe state", value: "failed", tone: "red" },
      { label: "Slack alert", value: "missing", tone: "red" },
      { label: "GitHub check", value: "success", tone: "red" },
      { label: "Findings", value: "4", tone: "red" },
    ],
  },
];

const scenarioTemplates = [
  {
    id: "SAAS-003",
    name: "Duplicate Webhook Side Effects",
    tag: "Template",
    body:
      "Duplicate Stripe webhook delivery should not create duplicate Slack alerts or GitHub recovery checks.",
    services: ["Stripe", "Slack", "GitHub"],
    counts: "Stripe 2 · Slack 2 · GitHub 2",
    labels: ["billing", "webhook", "idempotency", "functional"],
    status: "Recommended demo",
  },
  {
    id: "SAAS-001",
    name: "Failed Payment Success Notification",
    tag: "Template",
    body:
      "Failed Stripe payment must not produce Slack or GitHub success state before recovery is complete.",
    services: ["Stripe", "Slack", "GitHub"],
    counts: "Stripe 12 · Slack 9 · GitHub 4",
    labels: ["billing", "checks", "recovery", "functional"],
    status: "Policy pack ready",
  },
  {
    id: "SAAS-002",
    name: "Private Channel Alert Fallback",
    tag: "Template",
    body:
      "Billing alerts must remain visible even when a Slack bot cannot post into the private channel.",
    services: ["Stripe", "Slack"],
    counts: "Stripe 5 · Slack 11",
    labels: ["permissions", "fallback", "alerts", "functional"],
    status: "Regression ready",
  },
  {
    id: "PR-GH-01",
    name: "DevOps CI/CD Pipeline",
    tag: "Mock",
    body:
      "One GitHub repo fails validation, Slack posts deployment state, and the PR check remains action-required.",
    services: ["GitHub", "Slack"],
    counts: "GitHub 10 · Slack 13",
    labels: ["devops", "ci-cd", "checks", "functional"],
    status: "Demo mock",
  },
  {
    id: "AUTH-01",
    name: "Access Control Boundaries",
    tag: "Mock",
    body:
      "Outside contributor PRs, branch protections, mixed repo access, and private alert routing.",
    services: ["GitHub", "Slack"],
    counts: "GitHub 7 · Slack 10",
    labels: ["security", "auth", "access", "edge-case"],
    status: "Demo mock",
  },
  {
    id: "PAY-EDGE",
    name: "Payment Fraud & Edge Cases",
    tag: "Mock",
    body:
      "Declined cards, disputes, partial refunds, duplicate events, and automated fraud alerting.",
    services: ["Stripe", "Slack"],
    counts: "Stripe 9 · Slack 13",
    labels: ["payments", "fraud", "edge-case", "risk"],
    status: "Demo mock",
  },
];

const serviceGroups = [
  { label: "Billing", services: ["Stripe", "GitHub", "Slack"] },
  { label: "Workflow", services: ["MCP", "HTTP", "Action Log", "Policy Pack"] },
  { label: "Artifacts", services: ["Trace", "State Diff", "Patch Hints", "Run Manifest"] },
];

function dashboardToneClass(tone: string) {
  if (tone === "red") return "border-[#F3B99F] bg-[#FFF7F1] text-[#C2410C]";
  if (tone === "green") return "border-[#A8E6C3] bg-[#F0FFF7] text-[#047857]";
  return "border-[#BFD4FF] bg-[#F4F8FF] text-[#0B5CFF]";
}

function DashboardStatusPill({ status }: { status: DashboardRunStatus }) {
  const className =
    status === "failed"
      ? "border-[#F3B99F] bg-[#FFF7F1] text-[#C2410C]"
      : status === "passed"
        ? "border-[#A8E6C3] bg-[#F0FFF7] text-[#047857]"
        : "border-[#BFD4FF] bg-[#F4F8FF] text-[#0B5CFF]";

  return (
    <span className={`inline-flex items-center rounded-full border px-2.5 py-1 text-xs font-medium ${className}`}>
      {status}
    </span>
  );
}

function DashboardShellLogo() {
  return (
    <div className="flex items-center gap-2 rounded-full bg-white px-3 py-2 text-stone-950 shadow-[0_1px_0_rgba(28,25,23,0.04)]">
      <HyTriMark className="scale-[0.7] origin-left" />
      <span className="font-logo whitespace-nowrap text-[1.24rem] font-semibold leading-none tracking-[0] text-black">
        HyTri Labs
      </span>
    </div>
  );
}

function DashboardSidebar({
  activeView,
  setActiveView,
}: {
  activeView: DashboardView;
  setActiveView: (view: DashboardView) => void;
}) {
  const sections: Array<"Environments" | "Tests"> = ["Environments", "Tests"];

  return (
    <aside className="flex border-b border-[#E3E0DA] bg-[#F1EFEA] lg:min-h-screen lg:flex-col lg:border-b-0 lg:border-r">
      <div className="flex h-16 items-center justify-between px-4">
        <DashboardShellLogo />
        <button
          type="button"
          className="flex h-8 w-8 items-center justify-center rounded-full text-stone-400 transition-colors hover:bg-white hover:text-stone-900"
          aria-label="Collapse sidebar"
        >
          <ChevronRight className="h-4 w-4 rotate-180" />
        </button>
      </div>

      <nav className="min-w-64 px-2 py-2">
        {sections.map((section) => (
          <div key={section} className="mb-8">
            <p className="px-3 pb-2 text-[10px] font-medium uppercase tracking-[0.18em] text-stone-400">
              {section}
            </p>
            <div className="space-y-0.5">
              {dashboardNav
                .filter((item) => item.section === section)
                .map((item) => {
                  const Icon = item.icon;
                  const isActive = activeView === item.id;

                  return (
                    <button
                      key={item.id}
                      type="button"
                      onClick={() => setActiveView(item.id)}
                      className={`flex h-10 w-full items-center gap-3 rounded-lg px-3 text-left text-sm font-medium transition-colors ${
                        isActive
                          ? "bg-[#DDD9D5] text-black"
                          : "text-stone-600 hover:bg-white/70 hover:text-black"
                      }`}
                    >
                      <Icon className="h-4 w-4 shrink-0" />
                      <span>{item.label}</span>
                    </button>
                  );
                })}
            </div>
          </div>
        ))}

        <div className="space-y-0.5">
          {utilityNav.map((item) => {
            const Icon = item.icon;
            return (
              <button
                key={item.label}
                type="button"
                className="flex h-10 w-full items-center gap-3 rounded-lg px-3 text-left text-sm font-medium text-stone-600 transition-colors hover:bg-white/70 hover:text-black"
              >
                <Icon className="h-4 w-4 shrink-0" />
                <span>{item.label}</span>
              </button>
            );
          })}
        </div>
      </nav>

      <div className="mt-auto hidden border-t border-[#E3E0DA] p-3 lg:block">
        <div className="flex items-center justify-between gap-3">
          <p className="truncate text-sm font-semibold text-stone-900">@77777R7</p>
          <button type="button" className="text-xs text-stone-500 transition-colors hover:text-black">
            Demo mode
          </button>
        </div>
        <div className="mt-4">
          <div className="flex items-center justify-between text-[10px] text-stone-500">
            <span>Free sessions remaining</span>
            <span className="font-semibold text-stone-700">10/10</span>
          </div>
          <div className="mt-2 h-1 overflow-hidden rounded-full bg-stone-200">
            <div className="h-full w-full bg-[#16C784]" />
          </div>
        </div>
      </div>
    </aside>
  );
}

function RecentRunsRail({
  activeView,
  selectedRunId,
  setSelectedRunId,
}: {
  activeView: DashboardView;
  selectedRunId: string;
  setSelectedRunId: (id: string) => void;
}) {
  const railLabel =
    activeView === "pr"
      ? "Previous PR check runs"
      : activeView === "twins"
        ? "Previous twin runs"
        : activeView === "scenarios"
          ? "Recent scenario runs"
          : "Saved test runs";

  return (
    <aside className="hidden min-h-screen flex-col border-l border-[#E3E0DA] bg-[#F1EFEA] xl:flex">
      <div className="flex h-16 items-center justify-between border-b border-[#E3E0DA] px-4">
        <div>
          <p className="text-[10px] font-medium uppercase tracking-[0.18em] text-stone-400">
            {railLabel}
          </p>
          <p className="mt-1 text-xs text-stone-600">Saved runs for this workflow</p>
        </div>
        <button
          type="button"
          className="flex h-9 w-9 items-center justify-center rounded-full border border-stone-200 bg-white text-stone-500 shadow-sm transition-colors hover:text-black"
          aria-label="Collapse recent runs rail"
        >
          <ChevronRight className="h-4 w-4" />
        </button>
      </div>
      <div className="min-h-0 flex-1 space-y-3 overflow-y-auto px-3 py-4">
        {dashboardRuns.map((run) => {
          const isActive = selectedRunId === run.id;
          return (
            <button
              key={run.id}
              type="button"
              onClick={() => setSelectedRunId(run.id)}
              className={`w-full rounded-xl border p-3 text-left transition-all ${
                isActive
                  ? "border-stone-400 bg-white shadow-[0_8px_22px_rgba(28,25,23,0.06)]"
                  : "border-dashed border-stone-200 bg-white/50 hover:border-stone-300 hover:bg-white"
              }`}
            >
              <div className="flex items-start justify-between gap-3">
                <div>
                  <p className="text-xs font-semibold text-stone-950">{run.scenario}</p>
                  <p className="mt-1 line-clamp-2 text-xs leading-5 text-stone-600">{run.title}</p>
                </div>
                <DashboardStatusPill status={run.status} />
              </div>
              <div className="mt-3 flex items-center justify-between text-[11px] text-stone-500">
                <span>{run.pr}</span>
                <span>{run.time}</span>
              </div>
            </button>
          );
        })}
      </div>
    </aside>
  );
}

function ServiceBadge({ service }: { service: string }) {
  const palette =
    service === "Stripe"
      ? "border-[#F2C86B] bg-[#FFF8E7] text-[#A15C00]"
      : service === "Slack"
        ? "border-[#FDBA9E] bg-[#FFF3EC] text-[#C2410C]"
        : service === "GitHub"
          ? "border-stone-300 bg-white text-stone-700"
          : "border-[#BFD4FF] bg-[#F4F8FF] text-[#0B5CFF]";

  return <span className={`rounded-full border px-2.5 py-1 text-xs font-medium ${palette}`}>{service}</span>;
}

function PrChecksView({ activeRun }: { activeRun: (typeof dashboardRuns)[number] }) {
  const isFailed = activeRun.status === "failed";
  const artifacts = [
    ["Review summary", `${activeRun.artifactRoot}/github_check_summary.md`],
    ["Policy report", `${activeRun.artifactRoot}/policy_report.json`],
    ["State diff", `${activeRun.artifactRoot}/state_diff.json`],
    ["Patch hints", `${activeRun.artifactRoot}/patch_hints.md`],
  ];

  return (
    <div className="mx-auto flex min-h-[calc(100dvh-3rem)] w-full max-w-5xl flex-col justify-center px-6 py-8">
      <div className="text-center">
        <h1 className="font-serif text-5xl font-normal leading-none text-stone-950 md:text-6xl">
          PR Checks
        </h1>
        <p className="mx-auto mt-4 max-w-3xl text-base leading-7 text-stone-500">
          Run agent validation against stateful Stripe, Slack, and GitHub twins, then publish a PR-check-style result back to reviewers.
        </p>
      </div>

      <div className="mt-10 rounded-2xl border border-stone-200 bg-white p-6">
        <div className="flex flex-col gap-5 lg:flex-row lg:items-start lg:justify-between">
          <div>
            <div className="flex flex-wrap items-center gap-2">
              <span className="rounded-full bg-stone-100 px-2.5 py-1 text-xs text-stone-700">Team</span>
              <DashboardStatusPill status={activeRun.status} />
              <span className="rounded-full border border-stone-200 px-2.5 py-1 text-xs text-stone-500">
                conclusion: {activeRun.conclusion}
              </span>
            </div>
            <h2 className="mt-5 text-3xl font-semibold leading-tight tracking-[0] text-stone-950">
              {activeRun.title}
            </h2>
            <p className="mt-3 max-w-2xl text-sm leading-6 text-stone-600">{activeRun.summary}</p>
          </div>
          <div className="rounded-xl border border-stone-200 bg-[#F7F5F2] p-4 lg:w-64">
            <p className="text-[10px] font-medium uppercase tracking-[0.18em] text-stone-400">
              GitHub target
            </p>
            <p className="mt-2 break-words text-sm font-semibold leading-5 text-stone-900">{activeRun.repo}</p>
            <div className="mt-3 flex items-center gap-2 text-xs text-stone-500">
              <GitPullRequest className="h-4 w-4" />
              <span>{activeRun.pr}</span>
              <span>·</span>
              <span>{activeRun.sha}</span>
            </div>
          </div>
        </div>

        <div className="mt-6 grid gap-3 md:grid-cols-4">
          {activeRun.signals.map((signal) => (
            <div key={signal.label} className={`rounded-xl border p-4 ${dashboardToneClass(signal.tone)}`}>
              <p className="text-xs font-medium opacity-70">{signal.label}</p>
              <p className="mt-2 font-mono text-2xl leading-none">{signal.value}</p>
            </div>
          ))}
        </div>

        <div className="mt-6 grid gap-4 lg:grid-cols-[1fr_1fr_1fr]">
          <div className="rounded-xl border border-stone-200 bg-[#F7F5F2] p-4">
            <p className="text-xs font-medium uppercase tracking-[0.14em] text-stone-400">Expected</p>
            <p className="mt-2 text-sm font-semibold leading-6 text-stone-900">{activeRun.expected}</p>
          </div>
          <div className="rounded-xl border border-stone-200 bg-[#F7F5F2] p-4">
            <p className="text-xs font-medium uppercase tracking-[0.14em] text-stone-400">Observed</p>
            <p className={`mt-2 text-sm font-semibold leading-6 ${isFailed ? "text-[#C2410C]" : "text-[#047857]"}`}>
              {activeRun.observed}
            </p>
          </div>
          <div className="rounded-xl border border-stone-200 bg-[#F7F5F2] p-4">
            <p className="text-xs font-medium uppercase tracking-[0.14em] text-stone-400">Repair</p>
            <p className="mt-2 text-sm font-semibold leading-6 text-[#0B5CFF]">{activeRun.repair}</p>
          </div>
        </div>

        <div className="mt-6 rounded-xl border border-stone-200 bg-white p-4">
          <div className="flex flex-col gap-4 md:flex-row md:items-center md:justify-between">
            <div>
              <p className="text-[10px] font-medium uppercase tracking-[0.18em] text-stone-400">
                Policy annotation
              </p>
              <p className="mt-2 font-mono text-sm leading-6 text-stone-800">{activeRun.policy}</p>
            </div>
            <a
              href="/demo/saas-003"
              className="inline-flex items-center justify-center gap-2 rounded-lg bg-black px-4 py-2.5 text-sm font-normal text-white transition-colors hover:bg-stone-800"
            >
              Open full replay
              <ArrowRight className="h-4 w-4" />
            </a>
          </div>
        </div>

        <div className="mt-6 grid gap-3 md:grid-cols-4">
          {artifacts.map(([label, href]) => (
            <a
              key={href}
              href={href}
              target="_blank"
              rel="noreferrer"
              className="group rounded-xl border border-stone-200 bg-[#F7F5F2] p-4 transition-colors hover:border-stone-400 hover:bg-white"
            >
              <div className="flex items-center justify-between">
                <FileText className="h-4 w-4 text-stone-500" />
                <ExternalLink className="h-4 w-4 text-stone-400 transition-transform group-hover:translate-x-0.5" />
              </div>
              <p className="mt-4 text-sm font-semibold text-stone-950">{label}</p>
            </a>
          ))}
        </div>
      </div>
    </div>
  );
}

function TwinRunsView({
  selectedServices,
  setSelectedServices,
}: {
  selectedServices: string[];
  setSelectedServices: React.Dispatch<React.SetStateAction<string[]>>;
}) {
  const toggleService = (service: string) => {
    setSelectedServices((current) =>
      current.includes(service)
        ? current.filter((item) => item !== service)
        : [...current, service],
    );
  };

  return (
    <div className="mx-auto w-full max-w-5xl px-6 py-10">
      <div className="text-center">
        <h1 className="font-serif text-5xl font-normal leading-none text-stone-950 md:text-6xl">
          Twins
        </h1>
        <p className="mx-auto mt-4 max-w-3xl text-base leading-7 text-stone-500">
          Spin up short-lived Stripe, Slack, and GitHub service twins without deploying app code.
        </p>
      </div>

      <div className="mt-8 rounded-2xl border border-stone-200 bg-white p-6">
        <label className="mb-3 block text-sm font-normal text-stone-700">Service twins</label>
        {serviceGroups.map((group) => (
          <div key={group.label} className="mb-5 last:mb-0">
            <p className="mb-2 text-xs font-medium uppercase tracking-wide text-stone-400">{group.label}</p>
            <div className="flex flex-wrap gap-2">
              {group.services.map((service) => {
                const selected = selectedServices.includes(service);
                return (
                  <button
                    key={service}
                    type="button"
                    onClick={() => toggleService(service)}
                    className={`rounded-full border px-3 py-1.5 text-sm transition-colors ${
                      selected
                        ? "border-black bg-black text-white"
                        : "border-stone-200 bg-white text-stone-700 hover:border-stone-300"
                    }`}
                  >
                    {service}
                  </button>
                );
              })}
            </div>
          </div>
        ))}

        <p className="mt-6 text-sm text-stone-500">
          Choose the services available, then pick how long this twin environment should live.
        </p>

        <div className="mt-6 grid gap-6 xl:grid-cols-[0.45fr_0.55fr]">
          <div>
            <label className="mb-1 block text-sm font-normal text-stone-700">Session type</label>
            <div className="inline-flex rounded-lg border border-stone-200 bg-white p-0.5">
              <button type="button" className="whitespace-nowrap rounded-md bg-black px-4 py-2 text-sm text-white">
                Short-lived session
              </button>
              <button type="button" className="whitespace-nowrap rounded-md px-4 py-2 text-sm text-stone-600">
                Permanent
              </button>
            </div>
            <p className="mt-2 text-xs text-stone-500">Expires automatically after the TTL below.</p>

            <label className="mb-1 mt-6 block text-sm font-normal text-stone-700">Session TTL</label>
            <div className="flex items-center gap-3">
              <input
                value="10"
                readOnly
                className="h-11 w-28 rounded-lg border border-stone-200 bg-white px-3 text-sm text-black outline-none"
              />
              <span className="text-sm text-stone-500">minutes</span>
            </div>
            <p className="mt-2 text-xs text-stone-500">Free plan max: 10 minutes.</p>
          </div>

          <div className="min-w-0 rounded-xl border border-stone-200 bg-stone-50 p-4">
            <label className="mb-2 block text-sm font-normal text-stone-700">
              Describe the twin state <span className="text-stone-400">(optional)</span>
            </label>
            <textarea
              className="min-h-28 w-full resize-y rounded-lg border border-stone-200 bg-white px-3 py-2.5 text-sm text-black placeholder:text-stone-400 focus:border-black focus:outline-none focus:ring-2 focus:ring-black/10"
              placeholder="Example: replay duplicate Stripe invoice.payment_failed, one Slack billing alert, and one GitHub action-required check."
            />
            <div className="mt-4 flex flex-col gap-3">
              <select className="h-11 w-full min-w-0 rounded-lg border border-stone-200 bg-white px-3 text-sm text-black">
                <option>Template: Duplicate Webhook Side Effects</option>
                <option>Template: Failed Payment Success Notification</option>
                <option>Template: Private Channel Alert Fallback</option>
              </select>
              <button
                type="button"
                className="inline-flex w-fit min-w-36 items-center justify-center gap-2 rounded-lg bg-black px-5 py-2.5 text-sm font-normal text-white transition-colors hover:bg-stone-800"
              >
                Provision twins
                <Box className="h-4 w-4" />
              </button>
            </div>
          </div>
        </div>

        <div className="mt-6 grid gap-3 md:grid-cols-3">
          {[
            { icon: CreditCard, title: "StripeTwin", body: "Events, invoices, payment intents, retries." },
            { icon: Slack, title: "SlackTwin", body: "Channels, messages, delivery failures, alerts." },
            { icon: Github, title: "GitHubTwin", body: "Check runs, issues, PR comments, recovery state." },
          ].map((item) => {
            const Icon = item.icon;
            return (
              <div key={item.title} className="rounded-xl border border-stone-200 bg-[#F7F5F2] p-4">
                <Icon className="h-5 w-5 text-stone-700" />
                <p className="mt-4 text-sm font-semibold text-stone-950">{item.title}</p>
                <p className="mt-2 text-sm leading-5 text-stone-500">{item.body}</p>
              </div>
            );
          })}
        </div>
      </div>
    </div>
  );
}

function ScenariosView({ setActiveView }: { setActiveView: (view: DashboardView) => void }) {
  return (
    <div className="mx-auto w-full max-w-6xl px-6 py-10">
      <h1 className="font-serif text-4xl font-normal leading-none text-stone-950">
        Scenarios
      </h1>
      <p className="mt-3 max-w-3xl text-base leading-7 text-stone-500">
        Saved twin configurations. Use them in short-lived twin runs or start permanent validation URLs.
      </p>

      <section className="mt-8">
        <h2 className="text-base font-semibold text-stone-950">Your Scenarios</h2>
        <button
          type="button"
          className="mt-4 flex h-36 w-full max-w-md flex-col items-center justify-center rounded-2xl border border-dashed border-stone-300 bg-white/45 text-stone-600 transition-colors hover:border-stone-500 hover:bg-white"
        >
          <span className="text-4xl leading-none">+</span>
          <span className="mt-4 text-sm">Create Scenario</span>
        </button>
      </section>

      <section className="mt-10">
        <h2 className="text-base font-semibold text-stone-950">Templates</h2>
        <p className="mt-1 text-sm text-stone-500">Common scenarios to get started</p>
        <div className="mt-5 grid gap-4 lg:grid-cols-3">
          {scenarioTemplates.map((scenario) => (
            <article
              key={scenario.id}
              className="flex min-h-72 flex-col rounded-2xl border border-stone-200 bg-stone-50 p-5 transition-all hover:border-stone-400 hover:shadow-[0_8px_24px_rgba(28,25,23,0.06)]"
            >
              <div className="flex items-start justify-between gap-3">
                <h3 className="text-base font-semibold leading-6 text-stone-950">{scenario.name}</h3>
                <span className="rounded-full bg-stone-200 px-2.5 py-1 text-xs text-stone-600">{scenario.tag}</span>
              </div>
              <p className="mt-3 line-clamp-3 text-sm leading-6 text-stone-500">{scenario.body}</p>
              <div className="mt-4 flex flex-wrap gap-2">
                {scenario.services.map((service) => (
                  <ServiceBadge key={service} service={service} />
                ))}
              </div>
              <p className="mt-3 text-sm text-stone-500">{scenario.counts}</p>
              <div className="mt-3 flex flex-wrap gap-2">
                {scenario.labels.map((label) => (
                  <span key={label} className="rounded-full bg-white px-2.5 py-1 text-xs text-stone-500">
                    {label}
                  </span>
                ))}
              </div>
              <div className="mt-auto flex flex-wrap gap-2 pt-5">
                <button
                  type="button"
                  onClick={() => setActiveView("pr")}
                  className="rounded-lg bg-black px-4 py-2 text-sm font-normal text-white transition-colors hover:bg-stone-800"
                >
                  Use in Run
                </button>
                <button
                  type="button"
                  className="rounded-lg border border-stone-200 bg-white px-4 py-2 text-sm font-normal text-stone-700 transition-colors hover:bg-stone-50"
                >
                  Clone
                </button>
              </div>
            </article>
          ))}
        </div>
      </section>
    </div>
  );
}

function TestRunsView({
  setSelectedRunId,
  setActiveView,
}: {
  setSelectedRunId: (id: string) => void;
  setActiveView: (view: DashboardView) => void;
}) {
  return (
    <div className="mx-auto w-full max-w-6xl px-6 py-10">
      <h1 className="font-serif text-4xl font-normal leading-none text-stone-950">
        Test Runs
      </h1>
      <p className="mt-3 max-w-3xl text-base leading-7 text-stone-500">
        Review pass/fail history, artifact contracts, and repair hints for the demo workflow.
      </p>

      <div className="mt-8 overflow-hidden rounded-2xl border border-stone-200 bg-white">
        <div className="grid grid-cols-[0.9fr_0.9fr_0.7fr_0.6fr_0.6fr] border-b border-stone-200 bg-stone-50 px-4 py-3 text-xs font-medium uppercase tracking-[0.14em] text-stone-400">
          <span>Scenario</span>
          <span>Result</span>
          <span>GitHub</span>
          <span>Mode</span>
          <span>Action</span>
        </div>
        {dashboardRuns.map((run) => (
          <div
            key={run.id}
            className="grid grid-cols-[0.9fr_0.9fr_0.7fr_0.6fr_0.6fr] items-center border-b border-stone-100 px-4 py-4 text-sm last:border-b-0"
          >
            <div>
              <p className="font-semibold text-stone-950">{run.scenario}</p>
              <p className="mt-1 text-xs text-stone-500">{run.title}</p>
            </div>
            <div>
              <DashboardStatusPill status={run.status} />
              <p className="mt-1 text-xs text-stone-500">{run.summary}</p>
            </div>
            <div className="text-stone-600">
              <p>{run.pr}</p>
              <p className="text-xs text-stone-400">{run.sha}</p>
            </div>
            <p className="text-stone-600">{run.mode}</p>
            <button
              type="button"
              onClick={() => {
                setSelectedRunId(run.id);
                setActiveView("pr");
              }}
              className="inline-flex w-fit items-center gap-2 rounded-lg border border-stone-200 px-3 py-2 text-sm text-stone-700 transition-colors hover:border-stone-400 hover:bg-stone-50"
            >
              Select
              <ChevronRight className="h-4 w-4" />
            </button>
          </div>
        ))}
      </div>
    </div>
  );
}

function DashboardHomePage() {
  const [activeView, setActiveView] = useState<DashboardView>("pr");
  const [selectedRunId, setSelectedRunId] = useState(dashboardRuns[0].id);
  const [selectedServices, setSelectedServices] = useState(["Stripe", "Slack", "GitHub"]);
  const activeRun = dashboardRuns.find((run) => run.id === selectedRunId) ?? dashboardRuns[0];

  return (
    <div className="min-h-screen bg-[#F7F5F2] text-stone-950 antialiased">
      <div className="grid min-h-screen lg:grid-cols-[256px_minmax(0,1fr)] xl:grid-cols-[256px_minmax(0,1fr)_280px]">
        <DashboardSidebar activeView={activeView} setActiveView={setActiveView} />
        <main className="min-w-0">
          {activeView === "pr" ? <PrChecksView activeRun={activeRun} /> : null}
          {activeView === "twins" ? (
            <TwinRunsView selectedServices={selectedServices} setSelectedServices={setSelectedServices} />
          ) : null}
          {activeView === "scenarios" ? <ScenariosView setActiveView={setActiveView} /> : null}
          {activeView === "tests" ? (
            <TestRunsView setSelectedRunId={setSelectedRunId} setActiveView={setActiveView} />
          ) : null}
        </main>
        <RecentRunsRail
          activeView={activeView}
          selectedRunId={selectedRunId}
          setSelectedRunId={setSelectedRunId}
        />
      </div>
    </div>
  );
}

export default function App() {
  const pathname = typeof window === "undefined" ? "/" : window.location.pathname;

  if (pathname === "/dashboard" || pathname === "/dashboard/" || pathname === "/app" || pathname === "/app/") {
    return <LiveDashboardHomePage />;
  }

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
            href="/dashboard"
            className="pointer-events-auto inline-flex items-center gap-2 rounded-full border border-white/26 bg-[#0B5CFF]/94 px-5 py-3 text-sm font-semibold text-white shadow-[0_12px_36px_rgba(11,92,255,0.22)] backdrop-blur-xl transition-transform hover:-translate-y-0.5"
          >
            Open demo dashboard
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
            src="/hero-commerce-ai.png"
            alt=""
            aria-hidden="true"
            className="absolute inset-0 h-full w-full object-cover object-center"
          />
          <div className="absolute inset-0 bg-gradient-to-r from-[#F8F7F3]/18 via-[#F8F7F3]/6 to-transparent" />

          <div className="relative mx-auto flex min-h-[100svh] max-w-7xl items-start px-5 pb-12 pt-[8.75rem] md:px-8 md:pb-14 md:pt-[10.25rem] lg:pt-[10.75rem] xl:pt-[11.25rem]">
            <div className="max-w-[640px] overflow-visible">
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
                  href="/dashboard"
                  className="inline-flex items-center justify-center gap-2 rounded-full bg-[#0B5CFF] px-5 py-3.5 text-sm font-semibold text-white transition-transform hover:-translate-y-0.5"
                >
                  Open demo dashboard
                  <Play className="h-4 w-4" />
                </a>
                <a
                  href="#report"
                  className="inline-flex items-center justify-center gap-2 rounded-full border border-[#0A0D12]/20 bg-white/12 px-5 py-3.5 text-sm font-semibold text-[#0A0D12] backdrop-blur-md transition-colors hover:bg-white/32"
                >
                  Open evidence packet
                  <FileText className="h-4 w-4" />
                </a>
              </div>
              <div className="hero-actions mt-6 grid max-w-[640px] border border-white/28 bg-white/24 text-[#101318] shadow-[0_14px_40px_rgba(10,13,18,0.08)] backdrop-blur-xl sm:grid-cols-3">
                {outcomeRail.map((item, index) => (
                  <div
                    key={item.label}
                    className="border-b border-white/32 p-4 last:border-b-0 sm:border-b-0 sm:border-r sm:last:border-r-0"
                  >
                    <p className="text-[0.68rem] font-semibold uppercase tracking-[0] text-[#667085]">
                      {item.label}
                    </p>
                    <p
                      className={`mt-1 font-mono text-sm leading-tight ${
                        index === 1 ? "text-[#C2410C]" : "text-[#0B5CFF]"
                      }`}
                    >
                      {item.label === "Expected"
                        ? "1 alert + 1 check"
                        : item.label === "Fix"
                          ? "Persist event ID"
                          : item.value}
                    </p>
                  </div>
                ))}
              </div>
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
          <img
            src="/paths-sky-bg.png"
            alt=""
            aria-hidden="true"
            className="absolute inset-0 h-full w-full object-cover object-center"
          />
          <div className="absolute inset-0 bg-[#F8F7F1]/38" />
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
              SAAS-003 product proof
            </p>
            <h2 className="mx-auto mt-6 max-w-5xl text-center font-mono text-[2.5rem] font-normal leading-[1.08] tracking-[0] text-[#090A0C] sm:text-[3.35rem] md:text-[4.15rem]">
              A duplicate event becomes a blocked validation run.
            </h2>
            <p className="mx-auto mt-6 max-w-2xl text-center text-base leading-7 text-[#58606B] md:text-lg">
              The sandbox lets the agent act inside stateful twins, then returns
              the trace, state diff, policy decision, and fix hints before real
              systems are touched.
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
                href="/dashboard"
                className="inline-flex items-center justify-center gap-2 bg-white px-5 py-3 font-semibold text-[#0B5CFF] transition-transform hover:-translate-y-0.5"
              >
                Open demo dashboard
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
