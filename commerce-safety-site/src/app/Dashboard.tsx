import React, { useCallback, useEffect, useMemo, useState } from "react";
import ArrowRight from "lucide-react/dist/esm/icons/arrow-right.js";
import Box from "lucide-react/dist/esm/icons/box.js";
import CheckCircle2 from "lucide-react/dist/esm/icons/check-circle-2.js";
import ChevronRight from "lucide-react/dist/esm/icons/chevron-right.js";
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
import Settings from "lucide-react/dist/esm/icons/settings.js";
import Slack from "lucide-react/dist/esm/icons/slack.js";
import TriangleAlert from "lucide-react/dist/esm/icons/triangle-alert.js";

type DashboardView = "pr" | "twins" | "scenarios" | "tests";
type DashboardRunStatus = "failed" | "passed" | "running";
type DashboardTone = "blue" | "red" | "green" | "neutral";
type DashboardIcon = React.ComponentType<{ className?: string }>;
type RunMode = "unsafe" | "safe";

type DashboardSignal = {
  label: string;
  value: string;
  tone: DashboardTone;
};

type DashboardArtifact = {
  key: string;
  label: string;
  href: string;
};

type DashboardRun = {
  id: string;
  sessionId: string;
  scenario: string;
  title: string;
  repo: string;
  pr: string;
  sha: string;
  mode: string;
  status: DashboardRunStatus;
  conclusion: string;
  time: string;
  summary: string;
  policy: string;
  expected: string;
  observed: string;
  repair: string;
  sourceKind: "live" | "seed";
  artifacts: DashboardArtifact[];
  signals: DashboardSignal[];
};

type DashboardScenario = {
  id: string;
  name: string;
  tag: string;
  body: string;
  services: string[];
  counts: string;
  labels: string[];
  status: string;
};

type DashboardPayload = {
  runs: DashboardRun[];
  scenarios: DashboardScenario[];
};

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

const serviceGroups = [
  { label: "Billing", services: ["Stripe", "GitHub", "Slack"] },
  { label: "Workflow", services: ["MCP", "HTTP", "Action Log", "Policy Pack"] },
  { label: "Artifacts", services: ["Trace", "State Diff", "Patch Hints", "Run Manifest"] },
];

async function requestJson<T>(path: string, options?: RequestInit): Promise<T> {
  const response = await fetch(path, {
    ...options,
    headers: {
      "Content-Type": "application/json",
      ...(options?.headers ?? {}),
    },
  });
  const payload = await response.json();
  if (!response.ok || payload.ok === false) {
    throw new Error(payload.message || payload.error || `Request failed: ${path}`);
  }
  return payload as T;
}

async function loadDashboard(): Promise<DashboardPayload> {
  const [runsPayload, scenariosPayload] = await Promise.all([
    requestJson<{ runs: DashboardRun[] }>("/api/dashboard/runs"),
    requestJson<{ scenarios: DashboardScenario[] }>("/api/dashboard/scenarios"),
  ]);
  return {
    runs: runsPayload.runs,
    scenarios: scenariosPayload.scenarios,
  };
}

function dashboardToneClass(tone: DashboardTone) {
  if (tone === "red") return "border-[#FF9D72]/72 bg-[#FFF2EA]/82 text-[#C2410C]";
  if (tone === "green") return "border-[#7DE5B1]/70 bg-[#EEFFF7]/80 text-[#047857]";
  if (tone === "neutral") return "border-white/45 bg-white/44 text-[#344054]";
  return "border-[#9EC4FF]/76 bg-[#EEF6FF]/82 text-[#0B5CFF]";
}

function DashboardStatusPill({ status }: { status: DashboardRunStatus }) {
  const className =
    status === "failed"
      ? "border-[#FF9D72]/80 bg-[#FFF2EA]/90 text-[#C2410C]"
      : status === "passed"
        ? "border-[#7DE5B1]/80 bg-[#EEFFF7]/90 text-[#047857]"
        : "border-[#9EC4FF]/80 bg-[#EEF6FF]/90 text-[#0B5CFF]";

  return (
    <span className={`inline-flex items-center rounded-full border px-2.5 py-1 text-xs font-semibold ${className}`}>
      {status}
    </span>
  );
}

function HyTriMark({ className = "" }: { className?: string }) {
  return (
    <span aria-hidden="true" className={`grid h-9 w-11 grid-cols-2 gap-1 ${className}`}>
      <span className="rounded-[2px] bg-black [transform:skew(-9deg)]" />
      <span className="rounded-[2px] bg-black [transform:skew(-9deg)]" />
      <span className="rounded-[2px] bg-black [transform:skew(-9deg)]" />
      <span className="rounded-[2px] bg-black [transform:skew(-9deg)]" />
    </span>
  );
}

function DashboardShellLogo() {
  return (
    <a
      href="/"
      className="flex items-center gap-2 rounded-full border border-white/42 bg-white/54 px-3 py-2 text-[#0A0D12] shadow-[0_16px_48px_rgba(11,92,255,0.12)] backdrop-blur-2xl transition-transform hover:-translate-y-0.5"
      aria-label="HyTri Labs home"
    >
      <HyTriMark className="scale-[0.68] origin-left" />
      <span className="font-logo whitespace-nowrap text-[1.24rem] font-semibold leading-none tracking-[0] text-black">
        HyTri Labs
      </span>
    </a>
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
    <aside className="flex flex-col border-b border-white/40 bg-white/26 backdrop-blur-2xl lg:min-h-screen lg:border-b-0 lg:border-r">
      <div className="flex h-20 items-center justify-between px-4">
        <DashboardShellLogo />
        <button
          type="button"
          className="flex h-8 w-8 items-center justify-center rounded-full border border-white/44 bg-white/32 text-[#667085] transition-colors hover:bg-white/70 hover:text-[#0A0D12]"
          aria-label="Collapse sidebar"
        >
          <ChevronRight className="h-4 w-4 rotate-180" />
        </button>
      </div>

      <nav className="w-full min-w-0 px-2 py-2">
        {sections.map((section) => (
          <div key={section} className="mb-8">
            <p className="px-3 pb-2 text-[10px] font-semibold uppercase tracking-[0.18em] text-[#667085]">
              {section}
            </p>
            <div className="space-y-1">
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
                      className={`flex h-11 w-full items-center gap-3 rounded-2xl px-3 text-left text-sm font-semibold transition-all ${
                        isActive
                          ? "border border-white/54 bg-white/64 text-[#0A0D12] shadow-[0_14px_32px_rgba(11,92,255,0.12)]"
                          : "text-[#475467] hover:bg-white/44 hover:text-[#0A0D12]"
                      }`}
                    >
                      <Icon className={`h-4 w-4 shrink-0 ${isActive ? "text-[#0B5CFF]" : ""}`} />
                      <span>{item.label}</span>
                    </button>
                  );
                })}
            </div>
          </div>
        ))}

        <div className="space-y-1">
          {utilityNav.map((item) => {
            const Icon = item.icon;
            return (
              <button
                key={item.label}
                type="button"
                className="flex h-11 w-full items-center gap-3 rounded-2xl px-3 text-left text-sm font-semibold text-[#475467] transition-colors hover:bg-white/44 hover:text-[#0A0D12]"
              >
                <Icon className="h-4 w-4 shrink-0" />
                <span>{item.label}</span>
              </button>
            );
          })}
        </div>
      </nav>

      <div className="mt-auto hidden border-t border-white/38 p-4 lg:block">
        <div className="rounded-3xl border border-white/44 bg-white/38 p-4 backdrop-blur-xl">
          <div className="flex items-center justify-between gap-3">
            <p className="truncate text-sm font-semibold text-[#0A0D12]">@77777R7</p>
            <span className="text-xs font-semibold text-[#0B5CFF]">Local demo</span>
          </div>
          <div className="mt-4">
            <div className="flex items-center justify-between text-[10px] text-[#667085]">
              <span>Sandbox sessions</span>
              <span className="font-semibold text-[#344054]">local only</span>
            </div>
            <div className="mt-2 h-1 overflow-hidden rounded-full bg-white/64">
              <div className="h-full w-3/4 rounded-full bg-[#0B5CFF]" />
            </div>
          </div>
        </div>
      </div>
    </aside>
  );
}

function RecentRunsRail({
  activeView,
  runs,
  selectedRunId,
  setSelectedRunId,
}: {
  activeView: DashboardView;
  runs: DashboardRun[];
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
    <aside className="hidden min-h-screen flex-col border-l border-white/40 bg-white/24 backdrop-blur-2xl xl:flex">
      <div className="flex h-20 items-center justify-between border-b border-white/38 px-4">
        <div>
          <p className="text-[10px] font-semibold uppercase tracking-[0.18em] text-[#667085]">
            {railLabel}
          </p>
          <p className="mt-1 text-xs text-[#475467]">Live and seed runs for this workflow</p>
        </div>
        <button
          type="button"
          className="flex h-9 w-9 items-center justify-center rounded-full border border-white/48 bg-white/50 text-[#667085] shadow-sm transition-colors hover:bg-white hover:text-[#0A0D12]"
          aria-label="Collapse recent runs rail"
        >
          <ChevronRight className="h-4 w-4" />
        </button>
      </div>
      <div className="min-h-0 flex-1 space-y-3 overflow-y-auto px-3 py-4">
        {runs.length === 0 ? (
          <div className="rounded-3xl border border-dashed border-white/58 bg-white/32 p-4 text-sm leading-6 text-[#667085]">
            Runs will appear here after the dashboard API loads.
          </div>
        ) : null}
        {runs.map((run) => {
          const isActive = selectedRunId === run.id;
          return (
            <button
              key={run.id}
              type="button"
              onClick={() => setSelectedRunId(run.id)}
              className={`w-full rounded-3xl border p-3 text-left transition-all ${
                isActive
                  ? "border-white/80 bg-white/72 shadow-[0_18px_46px_rgba(11,92,255,0.14)]"
                  : "border-white/40 bg-white/34 hover:border-white/70 hover:bg-white/56"
              }`}
            >
              <div className="flex items-start justify-between gap-3">
                <div>
                  <p className="text-xs font-semibold text-[#0A0D12]">{run.scenario}</p>
                  <p className="mt-1 line-clamp-2 text-xs leading-5 text-[#475467]">{run.title}</p>
                </div>
                <DashboardStatusPill status={run.status} />
              </div>
              <div className="mt-3 flex items-center justify-between text-[11px] text-[#667085]">
                <span>{run.sourceKind === "live" ? "live" : "seed"}</span>
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
      ? "border-[#F2C86B]/80 bg-[#FFF8E7]/82 text-[#A15C00]"
      : service === "Slack"
        ? "border-[#FDBA9E]/80 bg-[#FFF3EC]/82 text-[#C2410C]"
        : service === "GitHub"
          ? "border-white/70 bg-white/68 text-[#344054]"
          : "border-[#9EC4FF]/76 bg-[#EEF6FF]/82 text-[#0B5CFF]";

  return <span className={`rounded-full border px-2.5 py-1 text-xs font-semibold ${palette}`}>{service}</span>;
}

function RunActionButton({
  mode,
  runningMode,
  onRun,
}: {
  mode: RunMode;
  runningMode: RunMode | null;
  onRun: (mode: RunMode) => void;
}) {
  const isRunning = runningMode === mode;
  const disabled = runningMode !== null;
  const label = mode === "unsafe" ? "Run failing PR check" : "Run deduped PR check";

  return (
    <button
      type="button"
      disabled={disabled}
      onClick={() => onRun(mode)}
      className={`inline-flex min-h-11 w-full items-center justify-center gap-2 rounded-full px-5 py-3 text-center text-sm font-semibold transition-all disabled:cursor-wait disabled:opacity-65 sm:w-auto ${
        mode === "unsafe"
          ? "bg-[#0A0D12] text-white hover:-translate-y-0.5 hover:bg-black"
          : "border border-white/56 bg-white/54 text-[#0A0D12] backdrop-blur-xl hover:-translate-y-0.5 hover:bg-white/84"
      }`}
    >
      {isRunning ? "Running..." : label}
      {mode === "unsafe" ? <TriangleAlert className="h-4 w-4" /> : <CheckCircle2 className="h-4 w-4" />}
    </button>
  );
}

function EmptyRunState({ reload }: { reload: () => void }) {
  return (
    <div className="mx-auto flex min-h-[calc(100dvh-3rem)] w-full max-w-4xl flex-col justify-center px-6 py-10">
      <div className="rounded-[2rem] border border-white/52 bg-white/46 p-8 text-center shadow-[0_26px_80px_rgba(11,92,255,0.12)] backdrop-blur-2xl">
        <p className="text-xs font-semibold uppercase tracking-[0.18em] text-[#0B5CFF]">Dashboard API</p>
        <h1 className="mt-4 text-4xl font-semibold tracking-[0] text-[#0A0D12]">Waiting for run data</h1>
        <p className="mx-auto mt-4 max-w-xl text-sm leading-6 text-[#475467]">
          Start `npm run dev:dashboard` so the React app can talk to the local dashboard API and Python live sandbox.
        </p>
        <button
          type="button"
          onClick={reload}
          className="mt-6 inline-flex items-center justify-center rounded-full bg-[#0B5CFF] px-5 py-3 text-sm font-semibold text-white"
        >
          Retry connection
        </button>
      </div>
    </div>
  );
}

function PrChecksView({
  activeRun,
  runningMode,
  runError,
  onRun,
}: {
  activeRun: DashboardRun;
  runningMode: RunMode | null;
  runError: string;
  onRun: (mode: RunMode) => void;
}) {
  const isFailed = activeRun.status === "failed";

  return (
    <div className="mx-auto flex min-h-[calc(100dvh-3rem)] w-full max-w-6xl flex-col justify-center px-5 py-8 md:px-8">
      <div className="grid gap-6 lg:grid-cols-[0.92fr_1.08fr] lg:items-end">
        <div>
          <p className="text-xs font-semibold uppercase tracking-[0.18em] text-[#0B5CFF]">
            Live PR safety check
          </p>
          <h1 className="mt-3 text-5xl font-semibold leading-[0.94] tracking-[0] text-[#0A0D12] md:text-6xl">
            PR Checks
          </h1>
          <p className="mt-4 max-w-2xl text-base leading-7 text-[#475467]">
            Run a stateful Stripe, Slack, and GitHub twin session, then return the
            same evidence packet a reviewer would need before approving agent code.
          </p>
        </div>
        <div className="flex flex-col gap-3 rounded-[2rem] border border-white/48 bg-white/34 p-4 shadow-[0_18px_60px_rgba(11,92,255,0.1)] backdrop-blur-2xl sm:flex-row sm:justify-end">
          <RunActionButton mode="unsafe" runningMode={runningMode} onRun={onRun} />
          <RunActionButton mode="safe" runningMode={runningMode} onRun={onRun} />
        </div>
      </div>

      {runError ? (
        <div className="mt-4 rounded-3xl border border-[#FF9D72]/60 bg-[#FFF2EA]/80 px-4 py-3 text-sm font-semibold text-[#C2410C] backdrop-blur-xl">
          {runError}
        </div>
      ) : null}

      <div className="mt-7 rounded-[2rem] border border-white/50 bg-white/48 p-5 shadow-[0_28px_90px_rgba(11,92,255,0.12)] backdrop-blur-2xl md:p-6">
        <div className="flex flex-col gap-5 lg:flex-row lg:items-start lg:justify-between">
          <div>
            <div className="flex flex-wrap items-center gap-2">
              <span className="rounded-full bg-white/64 px-2.5 py-1 text-xs font-semibold text-[#344054]">
                {activeRun.sourceKind === "live" ? "live run" : "seed run"}
              </span>
              <DashboardStatusPill status={activeRun.status} />
              <span className="rounded-full border border-white/58 bg-white/36 px-2.5 py-1 text-xs font-semibold text-[#667085]">
                conclusion: {activeRun.conclusion}
              </span>
            </div>
            <h2 className="mt-5 text-3xl font-semibold leading-tight tracking-[0] text-[#0A0D12]">
              {activeRun.title}
            </h2>
            <p className="mt-3 max-w-2xl text-sm leading-6 text-[#475467]">{activeRun.summary}</p>
          </div>
          <div className="rounded-[1.5rem] border border-white/52 bg-white/42 p-4 shadow-[0_14px_42px_rgba(16,24,40,0.08)] backdrop-blur-xl lg:w-72">
            <p className="text-[10px] font-semibold uppercase tracking-[0.18em] text-[#667085]">
              GitHub target
            </p>
            <p className="mt-2 break-words text-sm font-semibold leading-5 text-[#0A0D12]">{activeRun.repo}</p>
            <div className="mt-3 flex items-center gap-2 text-xs text-[#667085]">
              <GitPullRequest className="h-4 w-4 text-[#0B5CFF]" />
              <span>{activeRun.pr}</span>
              <span>·</span>
              <span>{activeRun.sha}</span>
            </div>
          </div>
        </div>

        <div className="mt-6 grid gap-3 md:grid-cols-4">
          {activeRun.signals.map((signal) => (
            <div key={signal.label} className={`rounded-[1.35rem] border p-4 backdrop-blur-xl ${dashboardToneClass(signal.tone)}`}>
              <p className="text-xs font-semibold opacity-70">{signal.label}</p>
              <p className="mt-2 font-mono text-2xl leading-none">{signal.value}</p>
            </div>
          ))}
        </div>

        <div className="mt-6 grid gap-4 lg:grid-cols-[1fr_1fr_1fr]">
          <div className="rounded-[1.5rem] border border-white/52 bg-white/42 p-4 backdrop-blur-xl">
            <p className="text-xs font-semibold uppercase tracking-[0.14em] text-[#667085]">Expected</p>
            <p className="mt-2 text-sm font-semibold leading-6 text-[#0A0D12]">{activeRun.expected}</p>
          </div>
          <div className="rounded-[1.5rem] border border-white/52 bg-white/42 p-4 backdrop-blur-xl">
            <p className="text-xs font-semibold uppercase tracking-[0.14em] text-[#667085]">Observed</p>
            <p className={`mt-2 text-sm font-semibold leading-6 ${isFailed ? "text-[#C2410C]" : "text-[#047857]"}`}>
              {activeRun.observed}
            </p>
          </div>
          <div className="rounded-[1.5rem] border border-white/52 bg-white/42 p-4 backdrop-blur-xl">
            <p className="text-xs font-semibold uppercase tracking-[0.14em] text-[#667085]">Repair</p>
            <p className="mt-2 break-words text-sm font-semibold leading-6 text-[#0B5CFF]">{activeRun.repair}</p>
          </div>
        </div>

        <div className="mt-6 rounded-[1.5rem] border border-white/52 bg-white/44 p-4 backdrop-blur-xl">
          <div className="flex flex-col gap-4 md:flex-row md:items-center md:justify-between">
            <div>
              <p className="text-[10px] font-semibold uppercase tracking-[0.18em] text-[#667085]">
                Policy annotation
              </p>
              <p className="mt-2 font-mono text-sm leading-6 text-[#344054]">{activeRun.policy}</p>
            </div>
            <a
              href="/demo/saas-003"
              className="inline-flex items-center justify-center gap-2 rounded-full bg-[#0A0D12] px-4 py-2.5 text-sm font-semibold text-white transition-colors hover:bg-black"
            >
              Open full replay
              <ArrowRight className="h-4 w-4" />
            </a>
          </div>
        </div>

        <div className="mt-6 grid gap-3 md:grid-cols-5">
          {activeRun.artifacts.map((artifact) => (
            <a
              key={artifact.key}
              href={artifact.href}
              target="_blank"
              rel="noreferrer"
              className="group rounded-[1.35rem] border border-white/52 bg-white/40 p-4 backdrop-blur-xl transition-colors hover:border-white/86 hover:bg-white/70"
            >
              <div className="flex items-center justify-between">
                <FileText className="h-4 w-4 text-[#0B5CFF]" />
                <ExternalLink className="h-4 w-4 text-[#98A2B3] transition-transform group-hover:translate-x-0.5 group-hover:text-[#0B5CFF]" />
              </div>
              <p className="mt-4 text-sm font-semibold text-[#0A0D12]">{artifact.label}</p>
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
    <div className="mx-auto w-full max-w-6xl px-5 py-10 md:px-8">
      <div>
        <p className="text-xs font-semibold uppercase tracking-[0.18em] text-[#0B5CFF]">Service twins</p>
        <h1 className="mt-3 text-5xl font-semibold leading-none tracking-[0] text-[#0A0D12]">
          Twins
        </h1>
        <p className="mt-4 max-w-3xl text-base leading-7 text-[#475467]">
          Spin up short-lived Stripe, Slack, and GitHub twins without deploying app code.
        </p>
      </div>

      <div className="mt-8 rounded-[2rem] border border-white/50 bg-white/48 p-6 shadow-[0_28px_90px_rgba(11,92,255,0.12)] backdrop-blur-2xl">
        {serviceGroups.map((group) => (
          <div key={group.label} className="mb-5 last:mb-0">
            <p className="mb-2 text-xs font-semibold uppercase tracking-wide text-[#667085]">{group.label}</p>
            <div className="flex flex-wrap gap-2">
              {group.services.map((service) => {
                const selected = selectedServices.includes(service);
                return (
                  <button
                    key={service}
                    type="button"
                    onClick={() => toggleService(service)}
                    className={`rounded-full border px-3 py-1.5 text-sm font-semibold transition-colors ${
                      selected
                        ? "border-[#0B5CFF] bg-[#0B5CFF] text-white"
                        : "border-white/56 bg-white/42 text-[#344054] hover:bg-white/76"
                    }`}
                  >
                    {service}
                  </button>
                );
              })}
            </div>
          </div>
        ))}

        <div className="mt-7 grid gap-5 xl:grid-cols-[0.45fr_0.55fr]">
          <div className="rounded-[1.5rem] border border-white/52 bg-white/40 p-4 backdrop-blur-xl">
            <label className="mb-1 block text-sm font-semibold text-[#344054]">Session type</label>
            <div className="inline-flex rounded-full border border-white/56 bg-white/40 p-1">
              <button type="button" className="whitespace-nowrap rounded-full bg-[#0A0D12] px-4 py-2 text-sm font-semibold text-white">
                Short-lived session
              </button>
              <button type="button" className="whitespace-nowrap rounded-full px-4 py-2 text-sm font-semibold text-[#667085]">
                Permanent
              </button>
            </div>
            <p className="mt-2 text-xs text-[#667085]">Expires automatically after the TTL below.</p>

            <label className="mb-1 mt-6 block text-sm font-semibold text-[#344054]">Session TTL</label>
            <div className="flex items-center gap-3">
              <input
                value="10"
                readOnly
                className="h-11 w-28 rounded-2xl border border-white/58 bg-white/58 px-3 text-sm text-[#0A0D12] outline-none"
              />
              <span className="text-sm text-[#667085]">minutes</span>
            </div>
          </div>

          <div className="min-w-0 rounded-[1.5rem] border border-white/52 bg-white/40 p-4 backdrop-blur-xl">
            <label className="mb-2 block text-sm font-semibold text-[#344054]">
              Describe the twin state <span className="text-[#98A2B3]">(optional)</span>
            </label>
            <textarea
              className="min-h-28 w-full resize-y rounded-2xl border border-white/58 bg-white/58 px-3 py-2.5 text-sm text-[#0A0D12] placeholder:text-[#98A2B3] focus:border-[#0B5CFF] focus:outline-none focus:ring-2 focus:ring-[#0B5CFF]/10"
              placeholder="Example: replay duplicate Stripe invoice.payment_failed, one Slack billing alert, and one GitHub action-required check."
            />
            <div className="mt-4 flex flex-col gap-3">
              <select className="h-11 w-full min-w-0 rounded-2xl border border-white/58 bg-white/58 px-3 text-sm text-[#0A0D12]">
                <option>Template: Duplicate Webhook Side Effects</option>
                <option>Template: Failed Payment Success Notification</option>
                <option>Template: Private Channel Alert Fallback</option>
              </select>
              <button
                type="button"
                className="inline-flex w-fit min-w-36 items-center justify-center gap-2 rounded-full bg-[#0A0D12] px-5 py-2.5 text-sm font-semibold text-white transition-colors hover:bg-black"
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
              <div key={item.title} className="rounded-[1.5rem] border border-white/52 bg-white/38 p-4 backdrop-blur-xl">
                <Icon className="h-5 w-5 text-[#0B5CFF]" />
                <p className="mt-4 text-sm font-semibold text-[#0A0D12]">{item.title}</p>
                <p className="mt-2 text-sm leading-5 text-[#667085]">{item.body}</p>
              </div>
            );
          })}
        </div>
      </div>
    </div>
  );
}

function ScenariosView({
  scenarios,
  setActiveView,
}: {
  scenarios: DashboardScenario[];
  setActiveView: (view: DashboardView) => void;
}) {
  return (
    <div className="mx-auto w-full max-w-6xl px-5 py-10 md:px-8">
      <p className="text-xs font-semibold uppercase tracking-[0.18em] text-[#0B5CFF]">Scenario catalog</p>
      <h1 className="mt-3 text-5xl font-semibold leading-none tracking-[0] text-[#0A0D12]">
        Scenarios
      </h1>
      <p className="mt-4 max-w-3xl text-base leading-7 text-[#475467]">
        Saved twin configurations. Use them in short-lived twin runs or start permanent validation URLs.
      </p>

      <section className="mt-8">
        <h2 className="text-base font-semibold text-[#0A0D12]">Your Scenarios</h2>
        <button
          type="button"
          className="mt-4 flex h-36 w-full max-w-md flex-col items-center justify-center rounded-[2rem] border border-dashed border-white/70 bg-white/36 text-[#475467] backdrop-blur-xl transition-colors hover:bg-white/60"
        >
          <span className="text-4xl leading-none">+</span>
          <span className="mt-4 text-sm font-semibold">Create Scenario</span>
        </button>
      </section>

      <section className="mt-10">
        <h2 className="text-base font-semibold text-[#0A0D12]">Templates</h2>
        <p className="mt-1 text-sm text-[#667085]">Common scenarios to get started</p>
        <div className="mt-5 grid gap-4 lg:grid-cols-3">
          {scenarios.map((scenario) => (
            <article
              key={scenario.id}
              className="flex min-h-72 flex-col rounded-[2rem] border border-white/50 bg-white/46 p-5 shadow-[0_22px_70px_rgba(11,92,255,0.1)] backdrop-blur-2xl transition-all hover:border-white/86 hover:bg-white/64"
            >
              <div className="flex items-start justify-between gap-3">
                <h3 className="text-base font-semibold leading-6 text-[#0A0D12]">{scenario.name}</h3>
                <span className="rounded-full bg-white/64 px-2.5 py-1 text-xs font-semibold text-[#667085]">{scenario.tag}</span>
              </div>
              <p className="mt-3 line-clamp-3 text-sm leading-6 text-[#667085]">{scenario.body}</p>
              <div className="mt-4 flex flex-wrap gap-2">
                {scenario.services.map((service) => (
                  <ServiceBadge key={service} service={service} />
                ))}
              </div>
              <p className="mt-3 text-sm text-[#667085]">{scenario.counts}</p>
              <div className="mt-3 flex flex-wrap gap-2">
                {scenario.labels.map((label) => (
                  <span key={label} className="rounded-full bg-white/50 px-2.5 py-1 text-xs text-[#667085]">
                    {label}
                  </span>
                ))}
              </div>
              <div className="mt-auto flex flex-wrap gap-2 pt-5">
                <button
                  type="button"
                  onClick={() => setActiveView("pr")}
                  className="rounded-full bg-[#0A0D12] px-4 py-2 text-sm font-semibold text-white transition-colors hover:bg-black"
                >
                  Use in Run
                </button>
                <button
                  type="button"
                  className="rounded-full border border-white/58 bg-white/42 px-4 py-2 text-sm font-semibold text-[#344054] transition-colors hover:bg-white/76"
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
  runs,
  setSelectedRunId,
  setActiveView,
}: {
  runs: DashboardRun[];
  setSelectedRunId: (id: string) => void;
  setActiveView: (view: DashboardView) => void;
}) {
  return (
    <div className="mx-auto w-full max-w-6xl px-5 py-10 md:px-8">
      <p className="text-xs font-semibold uppercase tracking-[0.18em] text-[#0B5CFF]">Run history</p>
      <h1 className="mt-3 text-5xl font-semibold leading-none tracking-[0] text-[#0A0D12]">
        Test Runs
      </h1>
      <p className="mt-4 max-w-3xl text-base leading-7 text-[#475467]">
        Review pass/fail history, artifact contracts, and repair hints for the demo workflow.
      </p>

      <div className="mt-8 overflow-hidden rounded-[2rem] border border-white/50 bg-white/48 shadow-[0_28px_90px_rgba(11,92,255,0.12)] backdrop-blur-2xl">
        <div className="hidden grid-cols-[0.9fr_0.9fr_0.7fr_0.6fr_0.6fr] border-b border-white/48 bg-white/36 px-4 py-3 text-xs font-semibold uppercase tracking-[0.14em] text-[#667085] md:grid">
          <span>Scenario</span>
          <span>Result</span>
          <span>GitHub</span>
          <span>Mode</span>
          <span>Action</span>
        </div>
        {runs.map((run) => (
          <div
            key={run.id}
            className="grid gap-4 border-b border-white/44 px-4 py-4 text-sm last:border-b-0 md:grid-cols-[0.9fr_0.9fr_0.7fr_0.6fr_0.6fr] md:items-center"
          >
            <div>
              <p className="font-semibold text-[#0A0D12]">{run.scenario}</p>
              <p className="mt-1 text-xs text-[#667085]">{run.title}</p>
            </div>
            <div>
              <DashboardStatusPill status={run.status} />
              <p className="mt-1 text-xs text-[#667085]">{run.summary}</p>
            </div>
            <div className="text-[#475467]">
              <p>{run.pr}</p>
              <p className="text-xs text-[#98A2B3]">{run.sha}</p>
            </div>
            <p className="text-[#475467]">{run.mode}</p>
            <button
              type="button"
              onClick={() => {
                setSelectedRunId(run.id);
                setActiveView("pr");
              }}
              className="inline-flex w-fit items-center gap-2 rounded-full border border-white/58 bg-white/42 px-3 py-2 text-sm font-semibold text-[#344054] transition-colors hover:bg-white/76"
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

export default function DashboardHomePage() {
  const [activeView, setActiveView] = useState<DashboardView>("pr");
  const [runs, setRuns] = useState<DashboardRun[]>([]);
  const [scenarios, setScenarios] = useState<DashboardScenario[]>([]);
  const [selectedRunId, setSelectedRunId] = useState("");
  const [selectedServices, setSelectedServices] = useState(["Stripe", "Slack", "GitHub"]);
  const [isLoading, setIsLoading] = useState(true);
  const [loadError, setLoadError] = useState("");
  const [runError, setRunError] = useState("");
  const [runningMode, setRunningMode] = useState<RunMode | null>(null);

  const reload = useCallback(async () => {
    setIsLoading(true);
    setLoadError("");
    try {
      const next = await loadDashboard();
      setRuns(next.runs);
      setScenarios(next.scenarios);
      setSelectedRunId((current) => current || next.runs[0]?.id || "");
    } catch (error) {
      setLoadError(error instanceof Error ? error.message : "Dashboard API unavailable.");
    } finally {
      setIsLoading(false);
    }
  }, []);

  useEffect(() => {
    void reload();
  }, [reload]);

  const activeRun = useMemo(
    () => runs.find((run) => run.id === selectedRunId) ?? runs[0],
    [runs, selectedRunId],
  );

  const runPrCheck = useCallback(async (mode: RunMode) => {
    setRunError("");
    setRunningMode(mode);
    try {
      const payload = await requestJson<{ run: DashboardRun }>("/api/dashboard/pr-checks/run", {
        method: "POST",
        body: JSON.stringify({ scenarioId: "SAAS-003", mode }),
      });
      setRuns((current) => [payload.run, ...current.filter((run) => run.id !== payload.run.id)]);
      setSelectedRunId(payload.run.id);
      setActiveView("pr");
    } catch (error) {
      setRunError(error instanceof Error ? error.message : "Could not run the PR check.");
    } finally {
      setRunningMode(null);
    }
  }, []);

  return (
    <div className="relative min-h-screen overflow-hidden bg-[#EAF6FF] text-[#0A0D12] antialiased">
      <img
        src="/paths-sky-bg.png"
        alt=""
        aria-hidden="true"
        className="absolute inset-0 h-full w-full object-cover object-center opacity-95"
      />
      <div className="absolute inset-0 bg-gradient-to-br from-white/58 via-[#EAF6FF]/42 to-[#0B5CFF]/10" />
      <div className="absolute inset-x-0 top-0 h-52 bg-white/28 blur-3xl" />

      <div className="relative grid min-h-screen lg:grid-cols-[272px_minmax(0,1fr)] xl:grid-cols-[272px_minmax(0,1fr)_300px]">
        <DashboardSidebar activeView={activeView} setActiveView={setActiveView} />
        <main className="min-w-0">
          {isLoading ? (
            <div className="mx-auto flex min-h-[calc(100dvh-3rem)] w-full max-w-4xl flex-col justify-center px-6 py-10">
              <div className="rounded-[2rem] border border-white/52 bg-white/46 p-8 text-center shadow-[0_26px_80px_rgba(11,92,255,0.12)] backdrop-blur-2xl">
                <p className="text-xs font-semibold uppercase tracking-[0.18em] text-[#0B5CFF]">Loading</p>
                <h1 className="mt-4 text-4xl font-semibold tracking-[0] text-[#0A0D12]">Connecting to sandbox backend</h1>
              </div>
            </div>
          ) : activeRun ? (
            <>
              {activeView === "pr" ? (
                <PrChecksView
                  activeRun={activeRun}
                  runningMode={runningMode}
                  runError={runError || loadError}
                  onRun={runPrCheck}
                />
              ) : null}
              {activeView === "twins" ? (
                <TwinRunsView selectedServices={selectedServices} setSelectedServices={setSelectedServices} />
              ) : null}
              {activeView === "scenarios" ? (
                <ScenariosView scenarios={scenarios} setActiveView={setActiveView} />
              ) : null}
              {activeView === "tests" ? (
                <TestRunsView runs={runs} setSelectedRunId={setSelectedRunId} setActiveView={setActiveView} />
              ) : null}
            </>
          ) : (
            <EmptyRunState reload={reload} />
          )}
        </main>
        <RecentRunsRail
          activeView={activeView}
          runs={runs}
          selectedRunId={selectedRunId}
          setSelectedRunId={setSelectedRunId}
        />
      </div>
    </div>
  );
}
