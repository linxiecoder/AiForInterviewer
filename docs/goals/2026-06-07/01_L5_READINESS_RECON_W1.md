---
title: 01_L5_READINESS_RECON_W1
type: note
permalink: ai-for-interviewer/docs/goals/2026-06-07/01-l5-readiness-recon-w1
---

# L5-READINESS-RECON-W1

你现在在 AiForInterviewer 仓库中执行一个受控重构审计窗口。

## Window ID

`L5-READINESS-RECON-W1`

## Phase

Pre-Phase-11 / L5 Readiness Recon

## Capability IDs

- L5-001
- L5-002
- L5-003
- L5-004
- L5-005
- L5-006
- AGT-001
- AGT-002
- AGT-003
- AGT-004
- AGT-005
- AGT-006
- AGT-007
- CTX-001
- CTX-002
- CTX-003
- QAG-004
- QAG-005
- QAG-006
- QAG-007
- FAG-006
- FAG-007
- FAG-008
- PRO-001
- PRO-002
- EVAL-001
- FAKE-001
- WIN-001

## Goal

只做 L5 readiness recon，不改业务代码。

基于 GitHub main 当前代码、当前测试 / Eval、runtime 配置、CI 配置，判断仓库是否具备进入 Phase 11 L5 Controlled Multi-Agent Orchestration 的条件。

## Primary question

当前仓库是否已经具备进入 Phase 11 的最低前置条件？

If not, list blocking gaps, corresponding Phase, Capability IDs, and recommended window sequence.

## Source of truth

1. `USER_CONFIRMED`: 用户已确认采用选项 C：一个 L5 Master Goal + L5 readiness recon，再裁剪后续窗口。
2. `GITHUB_CODE`: GitHub main 当前代码是当前实现事实源。
3. `TEST_RESULT`: 当前测试 / Eval 结果是行为证据源。
4. `PROJECT_SOURCE`: Project source 是目标架构、窗口协议、验收规则源。
5. `GOAL0531`: 历史目标和阶段意图源，不得当成当前代码事实源。
6. 子窗口输出必须经总控审计，不得直接作为 done evidence。

## Must recon first

读取并审计以下路径；若路径不存在，记录为 `ABSENT`，不得臆测实现存在。

### Project source / docs

- Project sources / docs 中所有与以下主题相关的文件：
  - Source of Truth Policy
  - Execution Window Protocol
  - Agent Platform Architecture
  - Agent Definition Standard
  - DDD Target Architecture
  - Canonical Evidence Contract
  - Refactor Traceability Matrix
  - Acceptance Gates
  - Risk Register
  - Decision Log
  - Phase Roadmap Lock
  - Agent Platform C Target

### Application / Agent platform

```text
apps/api/app/application/agents/
apps/api/app/application/agents/contracts/
apps/api/app/application/agents/definitions/
apps/api/app/application/agents/registry/
apps/api/app/application/agents/runtime/
apps/api/app/application/agents/handoff/
apps/api/app/application/agents/eval/
apps/api/app/application/ai_runtime/
apps/api/app/application/ai_runtime/contracts.py
apps/api/app/application/ai_runtime/registry.py
apps/api/app/application/ai_runtime/facade.py
apps/api/app/application/ai_runtime/handoff.py
```

### Polish application

```text
apps/api/app/application/polish/
apps/api/app/application/polish/use_cases.py
apps/api/app/application/polish/*_application_service.py
apps/api/app/application/polish/services/
apps/api/app/application/polish/context/
apps/api/app/application/polish/agents/question/
apps/api/app/application/polish/agents/feedback/
```

### Domain policies

```text
apps/api/app/domain/
apps/api/app/domain/polish/
apps/api/app/domain/polish/policies/
```

### Provider / LLM boundary

```text
apps/api/app/application/ai_provider/
apps/api/app/infrastructure/llm/
apps/api/app/infrastructure/ai_runtime/
```

### Tests / eval / CI

```text
tests/architecture/
tests/evals/
tests/fakes/
tests/api/
.github/workflows/
pyproject.toml
pytest.ini
Makefile
scripts/
```

## Recon commands

Run read-only discovery commands first:

```bash
pwd
git status --short
git rev-parse --abbrev-ref HEAD
git rev-parse HEAD

find apps/api/app/application -maxdepth 4 -type f | sort
find apps/api/app/domain -maxdepth 5 -type f | sort || true
find apps/api/app/infrastructure -maxdepth 4 -type f | sort || true
find tests -maxdepth 4 -type f | sort || true
find .github -maxdepth 4 -type f | sort || true
```

Then inspect imports and symbols:

```bash
grep -R "class .*Agent" -n apps/api/app/application apps/api/app/domain apps/api/app/infrastructure || true
grep -R "AgentDefinition" -n apps/api/app tests || true
grep -R "SkillRegistry\|ToolRegistry\|AgentExecutor\|Handoff" -n apps/api/app tests || true
grep -R "CanonicalEvidencePack\|SourceSupportSummary\|source_support" -n apps/api/app tests || true
grep -R "fake" -n apps/api/app tests | head -200 || true
grep -R "raw_prompt\|system_prompt\|developer_prompt\|raw_completion\|provider_payload\|full_resume\|full_jd\|full_asset_body" -n apps/api/app tests || true
grep -R "LangGraph\|StateGraph\|checkpoint\|replay\|resume\|interrupt" -n apps/api/app tests || true
grep -R "pytest\|eval\|grader\|dataset\|regression" -n tests scripts .github pyproject.toml pytest.ini Makefile || true
```

## Validation commands

Run existing tests only. Do not create or modify tests in this window.

Minimum:

```bash
pytest tests/architecture
pytest tests/evals
pytest tests/api/test_fake_llm_boundary.py
pytest tests/api/test_llm_runtime.py
```

If some paths do not exist, record as `ABSENT` and continue with available tests:

```bash
pytest
```

## Behavior change allowed

No.

## Prompt/schema/provider change allowed

No.

## DB schema change allowed

No.

## Allowed files

No implementation files.

If the repository has a dedicated docs/audit or project_sources area, you may create one audit report file only:

```text
docs/audit/L5_READINESS_RECON_W1.md
```

or

```text
project_sources/L5_READINESS_RECON_W1.md
```

If neither path exists, do not create files. Put the full report in final output.

## Forbidden files

```text
apps/api/app/application/polish/question_generation_prompts.py
apps/api/app/application/polish/feedback_prompt_assets.py
any prompt asset files
apps/api/app/infrastructure/llm/**
apps/api/app/infrastructure/db/**
database migrations
API route contract files
production provider implementation files
production DB implementation files
any file requiring behavior change
any file requiring schema change
```

## Implementation requirements

- Do not patch implementation.
- Do not rename files.
- Do not move files.
- Do not change imports.
- Do not format unrelated files.
- Do not add runtime behavior.
- Do not introduce Supervisor / Orchestrator yet.
- Do not implement Phase 11 or Phase 12 in this window.

## Classification scope

Classify current repository state against:

### Foundation readiness

- DDD rails
- PolishUseCases facade convergence
- focused application services ownership
- CanonicalEvidencePack shape
- SourceSupportSummary shape
- InterviewContext
- Domain policies
- Question Agent definition / skills / tools / planner / handoff
- Feedback Agent definition / skills / tools / planner / handoff
- Provider compact fail-closed boundary
- Fake isolation
- Eval / CI / regression foundation
- Runtime / replay / trace / interrupt foundation

### L5 readiness

- L5-002 Supervisor / Orchestrator Agent
- L5-003 Cross-agent handoff / state / trace
- L5-004 Three-or-more-agent product workflow
- L5-005 Controlled tool loop hardening
- L5-006 Multi-agent eval / replay / release gate

For each capability, produce:

- Capability ID
- Current code evidence
- Test / Eval evidence
- Status: `not_started`, `recon_done`, `design_done`, `implementation_planned`, `implemented`, `validated`, `blocked`, `deferred`, `done`
- Confidence: `high`, `medium`, `low`
- Gap
- Recommended next window
- Whether it blocks Phase 11 entry

## Readiness decision

Return exactly one of:

### GREEN

Phase 1-10 foundation is sufficiently closed. Enter Phase 11.

### AMBER

Phase 11 is close, but specific foundation blockers must be closed first. Provide 2-6 blocker windows, then Phase 11 window sequence.

### RED

Do not enter Phase 11. Major Phase 1-10 foundation capabilities are missing or unvalidated. Provide full closure roadmap.

## Acceptance criteria

- Every claimed implemented / validated / done capability has code evidence and test/eval evidence.
- Missing files are recorded as `ABSENT`.
- GOAL / Project source claims are not treated as code facts.
- L5 readiness decision is explicitly `GREEN` / `AMBER` / `RED`.
- Follow-up windows are named and ordered.
- No code behavior changed.
- No prompt/provider/DB/API behavior changed.
- Test commands and results are recorded.
- Any inability to run tests is recorded with reason and risk.

## Stop conditions

Stop and report to 总控 if:

- Repository cannot be read.
- `git status --short` shows unexpected large dirty changes before this window starts.
- Running tests would require destructive setup.
- Any required conclusion would require modifying forbidden files.
- You find Agent direct formal write, Tool direct repository exposure, provider fail-open, or fake runtime usage in production path.
- You find Project source and GitHub code materially contradict each other in a way that changes phase ordering.

## Final output format

1. Executive Readiness Decision
   - GREEN / AMBER / RED
   - One-paragraph rationale
2. Repository Evidence
   - Branch
   - Commit SHA
   - Dirty status
   - Relevant directory presence / absence
3. Capability Matrix
   - Capability ID
   - Capability
   - Code Evidence
   - Test / Eval Evidence
   - Status
   - Confidence
   - Gap
   - Blocks Phase 11?
   - Recommended Next Window
4. L5-Specific Findings
   - L5-002 Supervisor / Orchestrator
   - L5-003 Cross-agent handoff / state / trace
   - L5-004 Multi-agent product workflow
   - L5-005 Controlled tool loop hardening
   - L5-006 Eval / replay / release gate
5. Foundation Blockers Before Phase 11
   - Ordered blocker list
   - Each blocker mapped to Phase and Capability IDs
6. Recommended Window Plan
   - GREEN plan: P11-W1 to P12-W4
   - AMBER plan: blocker windows first, then P11-W1 to P12-W4
   - RED plan: Phase 1-10 closure windows first
7. Validation Commands and Results
   - Command
   - Result
   - Failure reason if any
8. Risks
   - Candidate/formal boundary
   - Provider fail-open
   - Fake runtime contamination
   - Eval insufficiency
   - Cross-agent trace/replay gap
   - Scope drift risk
9. Source Backfill Recommendations
   - Matrix updates needed
   - Decision Log updates needed
   - Risk Register updates needed
   - Acceptance Gate updates needed
   - Phase Roadmap updates needed
10. Follow-up Goal
   - Provide the exact next recommended Window ID and one-paragraph goal.