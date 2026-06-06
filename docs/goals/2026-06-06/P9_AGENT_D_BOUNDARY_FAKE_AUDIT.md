---
title: P9_AGENT_D_BOUNDARY_FAKE_AUDIT
type: goal-evidence
status: recon_only
permalink: ai-for-interviewer/docs/goals/2026-06-06/p9-agent-d-boundary-fake-audit
---

# P9 Agent D — Boundary / Fake / Provider / Security Audit

## Scope Lock

- Role: read-only provider/fake/security audit.
- Agent id: `019e9c37-1ddb-7220-930c-44bef4f35e59`.
- Output source: sub-agent final response, controller audited before single-writer patch.
- Forbidden: provider/runtime/prompt/API/DB/domain/frontend behavior change.

## Findings

| Boundary | Current evidence | P9 requirement |
|---|---|---|
| Provider boundary | P7 provider fail-closed and forbidden-key tests exist | Add eval-only regression fixtures and report scanners |
| Runtime fake | Runtime `LLM_PROVIDER=fake` rejection exists | Keep fake visible only as tests/evals/replay evidence |
| Fake import boundary | Production fake import scan exists | P9 eval code must not import production runtime fake wiring |
| Runtime metadata | Existing adapter guards fake-provider/fail-open/formal refs | P9 may only regression-test existing metadata semantics |
| Replay side effects | Existing replay side-effect counters fail closed | P9 must not claim real-provider quality from replay |
| Report safety | Runtime sanitizers exist | P9 reports need independent JSON + Markdown scanner |

## Required Scanner Delta

P9 scanner must cover normalized recursive key variants and secret-like values for:

- `raw_prompt`
- `system_prompt`
- `developer_prompt`
- `raw_completion`
- `provider_payload`
- `raw_provider_payload`
- `full_resume`
- `full_jd`
- `full_answer`
- `full_asset_body`
- `token`
- `secret`
- `cookie`
- `api_key`

## Agent D Conclusion

P9 can add eval-only provider/fake/report regression gates. It must not reopen or modify production provider/runtime behavior. Reports must expose replay/fake non-claims and fail on forbidden report data.
