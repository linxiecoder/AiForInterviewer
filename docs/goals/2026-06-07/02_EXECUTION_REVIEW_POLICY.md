---
title: 02_EXECUTION_REVIEW_POLICY
type: note
permalink: ai-for-interviewer/docs/goals/2026-06-07/02-execution-review-policy
---

# Execution Review Policy

## Direct answer

你不能只“连续执行所有窗口”而完全不把结果回给总控。

推荐执行方式：

1. `L5-READINESS-RECON-W1` 必须回给总控审计。
2. Recon 之后的窗口可以按预批准序列执行，但每个窗口结果至少要归档为 digest。
3. 遇到 stop condition、scope drift、测试失败、架构决策、AMBER/RED blocker、forbidden file 需求时，必须停止并回总控。
4. 不需要每个完全正常的小窗口都长篇回传给总控后再等新规划；但不能跳过窗口结果记录、测试结果、Matrix/Decision/Risk 回填。

## Why

子窗口输出不是最高事实源。它只是审计材料。真正的实现事实来自 GitHub main 当前代码，行为证据来自当前测试 / Eval。

Capability 不能只因为 Codex 报告“完成”就标记 done。Done 必须同时有设计、代码迁移、旧职责迁出、测试/Eval、验证命令、无 forbidden scope 修改、source backfill、gap 关闭或 deferred、必要用户确认。

## Mandatory return-to-总控 cases

The window executor must stop and return to 总控 when any of the following occurs:

### Source / repository uncertainty

- Repository cannot be read.
- Current branch is not expected.
- Dirty status contains unexpected changes.
- Project source, GOAL, and GitHub code materially contradict each other.
- Required files are absent and this changes phase ordering.

### Scope breach

- Needs forbidden files.
- Needs prompt/schema/provider/DB/API change not authorized by the current window.
- Needs migration outside current Phase.
- Needs to implement Phase 11/12 during Phase 5/6 or earlier.
- Needs behavior change when behavior change is not allowed.

### Architecture / safety breach

- Agent would directly write formal business facts.
- Tool would directly expose repository.
- Infrastructure would decide business policy.
- Prompt builder would decide source support, asset conflict, next action, or score policy.
- Provider boundary would fail open or fallback to full prompt/full resume/full JD/full asset body.
- Fake provider contaminates production runtime.

### Test / eval breach

- Required tests fail.
- Required tests cannot run and risk is non-trivial.
- Eval gap blocks capability done.
- Fake-only eval is used as product quality evidence.
- Replay / trace evidence is missing for L5 claim.

### Product / decision breach

- Human confirmation is needed.
- HITL behavior needs definition.
- A new Agent, Skill, Tool, State, Handoff, Eval, or migration order decision has multiple viable options.
- A capability would be marked done with deferred gaps.

## When continuous execution is acceptable

Continuous execution is acceptable only when all conditions are true:

- The previous window output is GREEN or has user-approved AMBER blockers.
- Next window is already named in the approved sequence.
- Scope, allowed files, forbidden files, behavior permissions, validation commands, rollback, and done criteria are already explicit.
- No stop condition is triggered.
- Tests pass or failures are explicitly allowed as non-blocking by the window.
- The executor writes a digest using `templates/WINDOW_RESULT_DIGEST.md`.

## Recommended operating mode

Use a checkpoint rhythm:

```text
Mandatory checkpoint:
  after L5-READINESS-RECON-W1

Recommended checkpoint:
  after each Phase boundary
  after P11-W3 multi-agent workflow
  after P12-W1 eval suite
  before final L5 release decision

Optional batch execution:
  P11-W1 + P11-W2 if recon is GREEN and both are contract-only
  P12-W2 + P12-W3 if P12-W1 passed and no schema/persistence change is required
```

## Minimum archive per window

Every window must produce at least:

- Window ID
- Commit SHA before / after
- Files changed
- Commands run
- Test/eval result
- Matrix status changes proposed
- Decision/Risk/Acceptance backfill required
- Remaining risks
- Next recommended window

Use `templates/WINDOW_RESULT_DIGEST.md`.