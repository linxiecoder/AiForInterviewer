---
title: P9_MASTER_GOAL
type: note
permalink: ai-for-interviewer/docs/goals/2026-06-06/p9-master-goal
---

# P9 Master Goal — Eval / CI / Regression Gate

You are in the AiForInterviewer repository executing a controlled Phase 9 window.

## Window ID

P9-W0-W4-EVAL-CI-REGRESSION-GATE

## Phase

Phase 9 — Eval / CI / Regression gate

## Capability IDs

Primary:

- EVAL-001 AI Eval gate
- FAKE-001 Fake cleanup verification in tests/evals/replay only
- PRO-002 Provider boundary regression verification
- QAG-004 Question Agent planner / planned workflow eval coverage
- QAG-006 Question Skills eval coverage
- QAG-007 Question Tools eval coverage
- FAG-006 Feedback Agent Definition eval coverage
- FAG-007 Feedback Skills eval coverage
- FAG-008 Feedback Tools eval coverage
- AGT-006 Handoff contract eval coverage
- AGT-007 Agent Trace contract eval coverage
- WIN-001 Execution window protocol evidence

Secondary / coverage-only:

- CTX-001 / CTX-002 / CTX-003 for canonical evidence and source support behavior cases
- PRO-001 only as regression evidence; do not refactor provider behavior in this phase
- L5-001 only as non-claim / gap-lock evidence; do not implement L5 Phase 11/12

## Source of Truth

Use this priority order:

1. User-confirmed instructions.
2. GitHub main current code as implementation fact.
3. Current tests / eval results as behavior evidence.
4. Project sources as target architecture and governance rules.
5. GOAL0531 as historical intent only.
6. Historical chats as clues only.
7. Sub-agent output only after controller audit.

If GitHub code conflicts with Project sources or GOAL, describe current code from GitHub, target from Project sources, and record a gap. Do not treat GOAL as current implementation fact.

## Phase 9 Goal

Build a real regression eval foundation:

- AI eval datasets.
- Deterministic graders.
- Eval runners.
- JSON and Markdown reports.
- Regression gate that returns non-zero on blocking failures.
- CI integration.
- Project source backfill.

Phase 9 must prove that eval failures can block done status. It must not claim AI quality through unit tests only. It must not claim real-provider quality from fake-only or replay-only evals.

## Explicit Non-Goals

Do not implement or fix Phase 8 runtime gaps.
Do not implement Supervisor / Orchestrator Agent.
Do not implement Phase 11 or Phase 12 L5 product workflow.
Do not alter production prompt text.
Do not alter runtime provider behavior.
Do not change DB schema.
Do not change API contract.
Do not let eval runner require live provider credentials in default CI.
Do not store raw prompt, raw completion, provider payload, full resume, full JD, full answer, full asset body, secrets, tokens, cookies, or API keys in eval reports.
Do not mark L5 done.

## Multi-Agent Execution Protocol

Run these agents in parallel first. They are read-only unless explicitly told otherwise.

- Agent A: Eval baseline recon.
- Agent B: Dataset and grader design.
- Agent C: Runner, report, and CI recon.
- Agent D: Boundary, fake, provider, and security audit.
- Agent E: Phase 8 gap guard and L5 non-claim audit.

Each sub-agent must output a file under `docs/goals/2026-06-06/`:

- `P9_AGENT_A_EVAL_BASELINE_RECON.md`
- `P9_AGENT_B_DATASET_GRADER_DESIGN.md`
- `P9_AGENT_C_RUNNER_CI_RECON.md`
- `P9_AGENT_D_BOUNDARY_FAKE_AUDIT.md`
- `P9_AGENT_E_PHASE8_GAP_GUARD.md`

After all sub-agents complete, the controller must merge their findings into:

- `docs/goals/2026-06-06/P9_CONTROLLER_RECON_MERGE.md`

Then and only then, exactly one writer may patch code/docs. The writer must follow `20_SINGLE_WRITER_IMPLEMENTATION_GOAL.md`.

## Must Recon First

Read current code and docs before patching. At minimum inspect files/directories if they exist:

Project sources:

- `docs/project-sources/00_PROJECT_BRIEF.md`
- `docs/project-sources/01_SOURCE_OF_TRUTH_POLICY.md`
- `docs/project-sources/03_AGENT_PLATFORM_ARCHITECTURE.md`
- `docs/project-sources/04_AGENT_DEFINITION_STANDARD.md`
- `docs/project-sources/07_CANONICAL_EVIDENCE_CONTRACT.md`
- `docs/project-sources/09_REFACTOR_TRACEABILITY_MATRIX.md`
- `docs/project-sources/10_EXECUTION_WINDOW_PROTOCOL.md`
- `docs/project-sources/12_ACCEPTANCE_GATES.md`
- `docs/project-sources/13_DECISION_LOG.md`
- `docs/project-sources/14_RISK_REGISTER.md`
- `docs/project-sources/17_PHASE_ROADMAP_LOCK.md`
- `docs/project-sources/18_AGENT_PLATFORM_C_TARGET.md`

Current eval/test/runners/CI:

- `tests/evals/`
- `evals/`
- `scripts/evals/`
- `scripts/qa/`
- `tests/architecture/`
- `tests/api/test_fake_llm_boundary.py`
- `tests/api/test_llm_runtime.py`
- `pyproject.toml`
- `pytest.ini`
- `.github/workflows/`
- `package.json`
- `Makefile`

Question / Feedback / Provider implementation references, read-only unless explicitly allowed below:

- `apps/api/app/application/polish/agents/question/`
- `apps/api/app/application/polish/agents/feedback/`
- `apps/api/app/application/agents/`
- `apps/api/app/application/ai_provider/`
- `apps/api/app/infrastructure/llm/`
- `apps/api/app/infrastructure/ai_runtime/`

## Candidate Allowed Files

The writer may modify only files needed for eval and CI gate:

```text
docs/goals/2026-06-06/P9_*.md
docs/goals/README.md
docs/project-sources/09_REFACTOR_TRACEABILITY_MATRIX.md
docs/project-sources/12_ACCEPTANCE_GATES.md
docs/project-sources/13_DECISION_LOG.md
docs/project-sources/14_RISK_REGISTER.md
docs/project-sources/17_PHASE_ROADMAP_LOCK.md
tests/evals/**
evals/**
scripts/evals/**
scripts/qa/**
apps/api/app/application/agents/eval/**
.github/workflows/**
pyproject.toml
pytest.ini
Makefile
package.json
```

Rules for allowed files:

- `apps/api/app/application/agents/eval/**` may contain eval contracts, pure runners, report models, and no production runtime behavior.
- `.github/workflows/**`, `Makefile`, `package.json`, `pyproject.toml`, and `pytest.ini` may be changed only to register or run eval gates.
- Project source edits must be evidence/backfill only; do not rewrite roadmap semantics beyond Phase 9 evidence.

## Forbidden Files

Do not modify:

```text
apps/api/app/api/v1/**
apps/api/app/domain/**
apps/api/app/application/polish/question_generation_prompts.py
apps/api/app/application/polish/feedback_prompt_assets.py
apps/api/app/application/polish/question_grounding.py
apps/api/app/application/polish/feedback_rules.py
apps/api/app/application/polish/agents/question/** except eval-only references if already under tests/evals
apps/api/app/application/polish/agents/feedback/** except eval-only references if already under tests/evals
apps/api/app/application/ai_provider/** except read-only recon
apps/api/app/infrastructure/llm/**
apps/api/app/infrastructure/db/**
apps/api/app/infrastructure/ai_runtime/** except read-only recon
database migrations
prompt assets
provider request builders
runtime provider wiring
LangGraph runtime implementation
```

If an eval requires touching forbidden files, stop and report the gap. Do not patch.

## Behavior Change Allowed

No production behavior change.

CI behavior may change by adding an eval regression gate. Eval runner behavior may be added.

## Prompt / Schema / Provider Change Allowed

No production prompt, provider payload, runtime schema, or API schema change.

Eval dataset schema and report schema may be added under eval-only directories.

## DB Schema Change Allowed

No.

## Implementation Requirements

1. Establish eval suite registry or manifest for Phase 9. It must bind suite IDs to capability IDs, dataset refs, grader refs, minimum pass criteria, and CI gate behavior.
2. Add regression datasets covering at least:
   - Canonical evidence/source support: direct project evidence, adjacent project evidence, job gap only, insufficient context.
   - Question Agent: job_gap_only must not claim candidate did the work; adjacent evidence must be hypothetical; grounding-blocked case; follow-up anti-repetition; deterministic fallback not generated success.
   - Feedback Agent: asset conflict blocks `generate_next_question`; asset candidate requires user confirmation; answer coverage; same-question change; feedback card ordering for asset consistency; provider unavailable / validation failed not success.
   - Provider boundary: forbidden keys rejected or absent from provider-facing/report payloads; no full prompt asset fallback; fail-closed evidence.
   - Fake gate: fake can be used only in tests/evals/replay and must be trace/report visible; runtime fake provider remains rejected.
   - Agent handoff / trace: question_candidate, feedback_candidate, asset_update_candidate must carry trace/validation refs and must not be formal writes.
   - Phase 8 runtime foundation: only evaluate what exists. Record missing runtime gap as deferred. Do not implement runtime features.
3. Add deterministic graders. Prefer structured assertions, schema checks, forbidden-phrase/key scanners, and reason-code coverage. Avoid brittle exact-text graders unless the fixture is deterministic.
4. Add an eval runner with modes:
   - `replay` or `fixture` for default CI and deterministic regression.
   - optional `real_provider` or `advisory` mode only if already supported; it must be skipped by default unless explicit env vars exist.
5. Add report generation:
   - JSON report for machines.
   - Markdown report for docs/goals.
   - Include commit SHA if available, dataset digest, suite ID, grader version, mode, pass/fail/skip counts, blocking failures, deferred cases, and non-claims.
6. Add regression gate:
   - Non-zero exit on blocking eval failure.
   - Skips must be explicit and categorized as `deferred`, `unsupported`, or `requires_real_provider`.
   - A negative-control fixture must prove the gate fails when a blocking case fails.
7. Add CI integration:
   - Default CI must not require live provider credentials.
   - CI must run the replay/fixture eval gate.
   - If GitHub Actions exists, add or extend a job. If not, add a documented script target and record the gap.
8. Backfill Project sources:
   - Matrix: update EVAL-001, FAKE-001, PRO-002, QAG/FAG/AGT eval evidence statuses as appropriate.
   - Acceptance Gates: add or update Eval Gate if missing.
   - Risk Register: update RISK-007 mitigation evidence; add P9-specific risk if needed.
   - Decision Log: record Phase 9 CI gate decision if new.
   - Phase Roadmap: record Phase 9 evidence without claiming Phase 10 or L5 release.
9. Do not close capabilities lacking eval evidence. Use `deferred_with_reason` or equivalent wording.

## Validation Commands

Run what exists and record exact results. Minimum target set:

```bash
git diff --check
pytest tests/evals -q
python scripts/evals/run_eval_gate.py --suite phase9 --mode replay --report-dir docs/goals/2026-06-06
```

If these exist, run as applicable:

```bash
pytest tests/architecture -q
pytest tests/api/test_fake_llm_boundary.py tests/api/test_llm_runtime.py -q
python scripts/evals/run_eval_gate.py --suite phase9 --mode replay --expect-fail-fixture
npm run web:test
```

If full backend validation is practical, run:

```bash
pytest -q
```

If a command cannot run, explain why, classify the risk, and do not mark done without evidence.

## Rollback

Revert only Phase 9 files:

- `tests/evals/**`
- `evals/**`
- `scripts/evals/**`
- `scripts/qa/**`
- `apps/api/app/application/agents/eval/**`
- `.github/workflows/**`
- eval-related changes in `pyproject.toml`, `pytest.ini`, `Makefile`, `package.json`
- `docs/goals/2026-06-06/P9_*.md`
- evidence/backfill edits in `docs/project-sources/**`

No DB rollback is required.

## Done Criteria

Phase 9 can be marked done only if:

- Every Phase 9 capability ID has at least one regression eval case or an explicit deferred record with reason and owner phase.
- Eval runner exists and can produce JSON + Markdown reports.
- Eval regression gate returns non-zero on blocking failures.
- CI gate is documented and integrated, or CI integration gap is explicitly documented and Phase 9 is not marked fully done.
- Fake-only/replay-only runs are not represented as real-provider quality evidence.
- Provider forbidden data is scanned or gated in eval/report artifacts.
- No prompt/provider/DB/API/runtime behavior diff occurred.
- Phase 8 runtime gaps remain explicit and are not silently fixed by Phase 9.
- Phase 9 is recorded as L5 Foundation only, not L5 release.
- Project sources are backfilled.
- Final audit passes.

## Final Output Required

1. Root Cause
2. Multi-Agent Recon Summary
3. What Changed
4. Files Changed
5. Behavior Before / After
6. Eval Coverage Matrix
7. Validation Commands and Results
8. CI Gate Evidence
9. Remaining Risks / Deferred Gaps
10. Source Backfill Summary
11. Follow-up Goal for Phase 10

## Stop Conditions

Stop and report to controller if:

- A required eval needs forbidden production behavior changes.
- A runtime gap from Phase 8 is necessary to make the eval pass.
- CI requires live provider secrets by default.
- Eval data would store raw prompt, raw provider payload, full resume/JD/answer/asset body, or secrets.
- The work requires DB schema or API contract changes.
- A sub-agent recommends marking Phase 9 as L5 release.
- Current GitHub code materially contradicts Project source and cannot be reconciled without user decision.