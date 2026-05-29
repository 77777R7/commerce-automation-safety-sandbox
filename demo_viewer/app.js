const data = window.DEMO_VIEWER_DATA;

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
    .replace(/\b\w/g, (match) => match.toUpperCase());
}

function metricHtml(value, label) {
  return `<div class="metric"><strong>${value}</strong><span>${label}</span></div>`;
}

function renderHero() {
  el("heroMetrics").innerHTML = [
    metricHtml(data.summary.scenarioCount, "P0 accident classes"),
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
  el("caseId").textContent = `${scenario.id} / ${activeRunner === "bad" ? "Failure path" : "Safe path"}`;
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
