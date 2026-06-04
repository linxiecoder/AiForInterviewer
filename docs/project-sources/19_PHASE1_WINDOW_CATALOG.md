---
title: 19_PHASE1_WINDOW_CATALOG
type: note
permalink: ai-for-interviewer/docs/project-sources/19-phase1-window-catalog
---

# 19 Phase 1 Window Catalog

## Phase 1 Name

DDD Rails + Agent Platform C0 + Polish Facade Convergence

## Phase 1 Definition

Phase 1 是项目级 DDD 起点，但不是一次性全项目 DDD 迁移。

Phase 1 必须同时服务两个目标：

1. 建立项目级 DDD rails。
2. 以 Polish 为第一条纵切面收敛 PolishUseCases facade。

Phase 1 同时必须确保 Agent Platform 不偏离 C target。

## Phase 1 Global Allowed

- Project-level DDD rails。
- Agent Platform C0 skeleton。
- PolishUseCases facade 收敛。
- Focused application services ownership extraction。
- Architecture boundary tests。
- Provider boundary tests / gates only。
- Matrix / Risk / Decision source backfill。

## Phase 1 Global Forbidden

- Prompt rewrite。
- Provider behavior refactor。
- DB schema change。
- API contract change。
- Question / Feedback Domain Policy migration。
- Full AgentExecutor runtime migration。
- LangGraph behavior change。
- Eval gate finalization。
- Asset formal write behavior change。
- Score / progress formal behavior change。

## P1-W1

### Window ID

P1-W1-DDD-RAILS-AGENT-C0-POLISH-FACADE

### Goal

建立 DDD rails + Agent Platform C0 skeleton + PolishUseCases facade 收敛的最小安全窗口。

### Capability IDs

- DDD-001
- DDD-002
- DDD-003
- AGT-001
- AGT-002
- AGT-003
- AGT-004
- AGT-005
- WIN-001

### Current Evidence Required

Must recon first:

- apps/api/app/application/polish/use_cases.py
- apps/api/app/application/polish/question_application_service.py
- apps/api/app/application/polish/feedback_application_service.py
- apps/api/app/application/polish/session_application_service.py
- apps/api/app/application/polish/answer_application_service.py
- apps/api/app/application/polish/progress_application_service.py
- apps/api/app/application/polish/report_application_service.py
- apps/api/app/application/ai_runtime/contracts.py
- apps/api/app/application/ai_runtime/registry.py
- apps/api/app/application/ai_runtime/facade.py
- apps/api/app/application/ai_runtime/handoff.py
- tests/api/test_polish_application_service_split.py
- tests/api/test_polish_question_refactor_phase1.py

### Allowed Files

Candidate allowed files:

```text
apps/api/app/application/agents/contracts/
apps/api/app/application/agents/definitions/
apps/api/app/application/agents/registry/
apps/api/app/application/agents/runtime/
apps/api/app/application/agents/handoff/
apps/api/app/application/polish/use_cases.py
apps/api/app/application/polish/*_application_service.py
tests/architecture/
tests/api/test_polish_application_service_split.py
tests/api/test_polish_question_refactor_phase1.py
```

### Forbidden Files

```text
apps/api/app/application/polish/question_generation_prompts.py
apps/api/app/application/polish/feedback_prompt_assets.py
apps/api/app/application/polish/question_grounding.py
apps/api/app/application/polish/feedback_rules.py
apps/api/app/infrastructure/llm/
apps/api/app/infrastructure/db/
apps/api/app/api/v1/
database migrations
```

### Behavior Change Allowed

No.

### Prompt/schema/provider Change Allowed

No.

Provider boundary tests only if scoped.

### DB Schema Change Allowed

No.

### Requirements

- Do not change API behavior.
- Do not change prompt content.
- Do not change provider request behavior.
- Do not change DB schema.
- Do not migrate domain policies.
- Add C0 contracts / registry / executor port without wiring full runtime.
- PolishUseCases should move toward facade-only.
- Focused services should start owning selected orchestration, not merely delegate.
- Keep backward-compatible imports.

### Validation Commands

Minimum:

```bash
pytest tests/api/test_polish_application_service_split.py
pytest tests/api/test_polish_question_refactor_phase1.py
```

If architecture tests added:

```bash
pytest tests/architecture
```

### Done Criteria

- Agent Platform C0 skeleton exists or is explicitly implemented.
- PolishUseCases remains backward-compatible.
- Selected focused services no longer merely delegate.
- No prompt/provider/DB/API behavior diff.
- Tests pass or inability explained.
- Matrix updated.
- Risk Register updated.
- Decision Log updated.

### Rollback

Revert changed files in allowed scope.
No DB rollback required.

## P1-W2

### Window ID

P1-W2-POLISH-SERVICE-OWNERSHIP

### Goal

继续将 Polish application orchestration 从 use_cases.py 迁入 focused services。

### Capability IDs

- DDD-001
- DDD-002

### Allowed Files

```text
apps/api/app/application/polish/use_cases.py
apps/api/app/application/polish/*_application_service.py
apps/api/app/application/polish/services/
tests/api/test_polish_application_service_split.py
tests/api/test_polish_api.py
```

### Forbidden Files

```text
prompt builders
provider boundary
DB migrations
domain policies
ai runtime behavior
```

### Behavior Change Allowed

No.

### Done Criteria

- More orchestration owned by focused services.
- use_cases.py shrinks or delegates facade-only.
- Existing tests pass.
- No behavior diff.

## P1-W3

### Window ID

P1-W3-ARCHITECTURE-BOUNDARY-TESTS

### Goal

增加 DDD / Agent / Provider boundary tests，防止后续偏移。

### Capability IDs

- DDD-003
- AGT-002
- AGT-003
- AGT-004
- PRO-002
- FAKE-001

### Allowed Files

```text
tests/architecture/
tests/api/test_fake_llm_boundary.py
tests/api/test_llm_runtime.py
```

### Forbidden Files

```text
business implementation files unless required for testability
prompt builders
provider behavior implementation
DB migrations
```

### Behavior Change Allowed

No.

### Prompt/schema/provider Change Allowed

No behavior change.
Tests only.

### Done Criteria

Tests assert:

- Domain does not import infrastructure/api/application.llm.
- Application services do not import infrastructure LLM transport directly.
- Agent candidate-only boundary exists.
- ToolRegistry does not expose repository directly.
- Provider request forbids full prompt asset fallback.
- Fake runtime provider is rejected.
- Forbidden keys are scanned or test-gated.

## P1 Stop Conditions

Stop and return to 总控 if:

- Need to change prompt.
- Need to change provider behavior.
- Need DB migration.
- Need API contract change.
- Need to migrate domain policies.
- Need to directly wire Question / Feedback to full AgentExecutor runtime.
- Current GitHub code contradicts Project source materially.
- Tests require behavior changes outside Phase 1 scope.

## Phase 1 Completion Criteria

Phase 1 can close only when:

- P1-W1 done.
- P1-W2 done or explicitly deferred with reason.
- P1-W3 done.
- Matrix updated.
- Decision Log updated.
- Risk Register updated.
- Acceptance Gates updated.
- No B-as-target drift.
- Phase 2 entry criteria documented.

## Phase 2 Entry Criteria

Before Phase 2:

- Phase 1 C0 skeleton stable.
- Polish facade direction stable.
- SourceSupportSummary target contract locked.
- No unreviewed prompt/provider/DB changes from Phase 1.