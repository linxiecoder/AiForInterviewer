---
title: 00_GOAL_L5_MASTER
type: note
permalink: ai-for-interviewer/docs/goals/2026-06-07/00-goal-l5-master
---

# GOAL-L5-MASTER

## Goal ID

`GOAL-L5-MASTER`

## Goal name

AiForInterviewer L5 Controlled Multi-Agent System Completion

## Objective

把 AiForInterviewer 从 Question / Feedback L2 planned guarded workflows 和 Agent Platform C foundation，推进到 L5 controlled multi-agent system。

This is an umbrella goal. It must govern multiple scoped windows; it is not a single oversized implementation window.

## User-confirmed execution strategy

用户已确认采用选项 C：

```text
One L5 Master Goal
  -> L5-READINESS-RECON-W1
  -> Based on GitHub main + tests/evals,裁剪后续窗口
```

## Source of truth

1. `USER_CONFIRMED`: 用户明确确认。
2. `GITHUB_CODE`: GitHub main 当前代码。
3. `TEST_RESULT`: 当前测试 / Eval 结果。
4. `PROJECT_SOURCE`: Project source 文档。
5. `GOAL_SOURCE`: GOAL0531 历史目标和阶段意图。
6. `HISTORICAL_CHAT`: 历史聊天，仅作线索。
7. `SUBWINDOW_OUTPUT`: 子窗口输出，必须经总控审计。

If sources conflict:

- GitHub describes current implementation.
- Tests/evals describe behavior evidence.
- Project source describes target architecture and governance.
- GOAL0531 describes historical intent.
- Difference must be recorded as gap.

## L5 definition

L5 accepted only when all required evidence exists:

- Supervisor / Orchestrator Agent exists and is registered.
- At least three business agents collaborate through typed candidate handoff.
- Cross-agent plan / state / handoff / trace / replay exists.
- Shared CanonicalEvidencePack / InterviewContext / SourceSupportSummary is used.
- Controlled tool loop has `max_steps`, `max_retries`, `timeout`, and `stop_conditions`.
- HITL protects asset conflict, formal write, low confidence, and ownership ambiguity.
- Agent outputs remain candidate / suggestion only.
- Formal write remains `Application Service -> Domain Policy -> Handoff -> Repository / Transaction`.
- Provider request remains compact and fail-closed.
- Fake is limited to tests / evals / replay.
- Multi-agent eval / replay / regression CI gate passes.
- Human release decision is recorded.

## Non-goals

- Do not call Question / Feedback L2 planned workflows L5.
- Do not call Phase 8 / C4 runtime L5 release.
- Do not introduce unbounded autonomous loops.
- Do not allow Agent direct DB / repository write.
- Do not allow Tool direct repository exposure.
- Do not allow Prompt Builder to own business policy.
- Do not claim AI quality with unit tests only.
- Do not claim L5 with fake-only eval.
- Do not persist raw prompt / raw provider payload / raw completion.

## First executable window

`L5-READINESS-RECON-W1`

Purpose:

Use GitHub main + current tests/evals to determine whether the repository can enter Phase 11 directly, or whether Phase 1-10 foundation gaps must be closed first.

## Expected branch after recon

- `GREEN`: Phase 1-10 foundation sufficiently closed -> enter Phase 11 with L5-specific windows.
- `AMBER`: small number of foundation blockers -> run blocker windows first, then Phase 11.
- `RED`: major foundation gaps remain -> resume Phase 1-10 closure before L5 implementation.

## Release rule

L5 cannot be marked done until L5-002 through L5-006 are validated or explicitly deferred with user-confirmed release risk.