---
title: P5-W1.fix.01 Question Planned Workflow Remediation Closeout
type: execution-evidence
status: implemented_with_validation_blockers
permalink: goals/2026-06-05/p5-w1-fix01-question-planned-workflow-remediation/closeout
---

# P5-W1.fix.01 Question Planned Workflow Remediation Closeout

## Scope

- Window: `P5-W1.fix.01-QUESTION-PLANNED-WORKFLOW-REMEDIATION`
- Phase: Phase 5 Question Agent Planned Workflow
- Status: `implemented_with_validation_blockers`
- Scope lock: Phase 5 C2 / L2 only. Phase 8 runtime、Phase 11 Supervisor / Orchestrator、Phase 12 L5 release gate 未实现。

## Root Cause

之前的 `QAG-004` 状态表述过强：Question 路径已有 candidate metadata、fallback guard 和 `polish_question_graph.py`，但没有独立的生产组件 `apps/api/app/application/polish/agents/question/planned_workflow.py`。因此 “Question C2 / L2 planned guarded workflow implemented” 在审计前缺少 dedicated production component 证据。

## Remediation Evidence

- 新增 Question planned workflow component：`apps/api/app/application/polish/agents/question/planned_workflow.py`。
- normal question path 已接入 workflow：
  - graph/provider accepted candidate path 先进入 `run_question_planned_workflow(...)`，再由 Application Service / Domain Policy / Handoff 决定正式写入。
  - direct service path 先进入 `run_question_planned_workflow(...)`，再由同一 handoff path 决定正式写入。
- workflow metadata 覆盖 `source_support_summary`、grounding policy result、follow-up / anti-repetition metadata、`question_candidate`、`validation_refs`、`trace_refs`、policy refs、skill refs、tool refs 和 formal write boundary。
- fake、graph-disabled、provider unavailable、deterministic degraded generation、validation failed 不再写正式 question success，而是返回 `question_candidate` validation task。
- Feedback planned workflow bridge 未做本 remediation 的实现改动；本轮只保留并验证 `feedback_candidate` / `asset_update_candidate` candidate-first 语义。

## Validation

| Command | Result |
|---|---|
| `python3 -m py_compile apps/api/app/application/polish/use_cases.py` | exit 0 |
| `python3 -m py_compile apps/api/app/application/polish/agents/question/planned_workflow.py` | exit 0 |
| `python3 -m py_compile apps/api/app/application/polish/agents/feedback/planned_workflow.py` | exit 0 |
| `.venv/bin/python -m pytest tests/api/test_polish_question_graph_integration.py -q` | `12 passed`; exit 1 only because repo-root `tmp` temp checker reported pre-existing temp-like directory |
| `.venv/bin/python -m pytest tests/api/test_pr5_polish_question_graph_persistence_handoff.py -q` | `15 passed`; exit 1 only because repo-root `tmp` temp checker reported pre-existing temp-like directory |
| `.venv/bin/python -m pytest tests/api/test_polish_question_refactor_phase1.py -q` | `64 passed`; exit 1 only because repo-root `tmp` temp checker reported pre-existing temp-like directory |
| `.venv/bin/python -m pytest tests/api/test_polish_feedback_runtime.py -q` | `7 passed`; exit 1 only because repo-root `tmp` temp checker reported pre-existing temp-like directory |
| `.venv/bin/python -m pytest tests/evals -q` | `19 passed`; exit 1 only because repo-root `tmp` temp checker reported pre-existing temp-like directory |
| `.venv/bin/python -m evals.runners.run_question_eval` | exit 0; 3 total / 0 failed |
| `.venv/bin/python -m evals.runners.run_feedback_eval` | exit 0; 5 total / 0 failed |
| `.venv/bin/python -m pytest tests/api -k "question or feedback or agent or handoff or canonical or source_support" -q` | `299 passed / 1 failed / 323 deselected`; remaining failure is `tests/api/test_polish_canonical_evidence.py::test_polish_question_and_feedback_context_include_canonical_assets`, which expects provider-unavailable fallback to persist a formal question and is outside this window write scope |
| `git diff --check` | exit 0 |

## Deferred Gaps

- Repo root pre-existing `tmp` directory still causes pytest temp leak checker to exit non-zero after otherwise passing focused business assertions.
- Raw `tests/architecture -q` still requires `PYTHONPATH`; supplemental `PYTHONPATH=.:apps/api .venv/bin/python -m pytest tests/architecture -q` reported `33 passed, 2 xfailed` and then hit the same temp checker.
- `tests/api/test_polish_canonical_evidence.py::test_polish_question_and_feedback_context_include_canonical_assets` remains a legacy expectation alignment gap outside this remediation write scope.
- `QAG-004` must remain `implemented_with_validation_blockers`, not `done`, until temp checker and remaining legacy alignment gap are resolved in an authorized window.
