# POC Success Criteria

The POC is successful when both teams can answer the same question:

```txt
Does this staging agent or workflow make unsafe commerce decisions under realistic failure conditions?
```

## Technical Success

Required:

- The design partner can connect a staging agent or workflow through MCP or HTTP.
- The same integration can run at least one unsafe path and one safe path.
- All five P0 scenarios can run or be mapped to the partner's workflow domain.
- Unsafe behavior produces structured policy findings.
- Safe behavior passes with zero findings.
- Artifacts are generated and downloadable.
- The partner can inspect trace, policy report, state diff, report, and patch hints.

## Business Success

Required:

- At least one finding maps to a risk the partner recognizes from real commerce operations.
- The operator-facing report is understandable without reading code.
- The engineering team can identify a concrete guardrail or code/workflow change.
- The partner can explain why the safety check should run before production changes.

## Security And Data Success

Required:

- No production store token is used.
- No real payment, fulfillment, warehouse, or customer-message credentials are used.
- No real customer PII is required.
- Workspace and artifact access are scoped to the design partner.
- Token revoke and workspace suspend are available as kill-switch actions.

## Commercial Success

Strong signals:

- The partner wants to save a failed run as a regression scenario.
- The partner wants to test another workflow.
- The partner asks to run the check before release or customer deployment.
- The partner asks for team access, hosted run history, or CI/MCP integration.
- The partner is willing to pay for a follow-up pilot.

## POC Exit Options

After the first POC, choose one:

1. No fit: archive findings and stop.
2. Manual pilot: run more scenarios with our help.
3. Integration pilot: connect one staging workflow to MCP/HTTP.
4. Paid POC: define scenario pack, reporting cadence, and success metrics.

## Recommended First Paid POC Shape

Scope:

- One staging agent or workflow.
- Five P0 scenarios.
- One custom scenario or action-log replay if available.
- One review session.
- One remediation summary.

Target price:

```txt
$500-$2,000
```

Expected deliverables:

- Run artifacts.
- Executive summary.
- Engineering findings.
- Recommended guardrails.
- Regression scenario candidates.
