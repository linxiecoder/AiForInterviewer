---
name: aifi-control-plane-audit
description: Use when AiForInterviewer work asks about control authority, decision writers/executors, runtime drift, or fail-closed hardening.
---

# aifi-control-plane-audit

## Purpose

用代码证据回答“控制能力在哪里”。本 Skill 适用于 control-flow、next action、runtime enforcement、state update、frontend gating、fail-closed loop、decision leak map 和 minimal cut 审计。

默认只读。除非用户明确授权实现，否则不得 patch。

## When to use

- 用户要求 yes/no verdict：是否存在 single control authority / single control plane。
- 用户问 control architecture、runtime drift、decision leak、authority consolidation、minimal cut。
- 需要审计哪些 API、service、domain policy、storage、frontend、scoring 路径能写入或执行同一类决策。
- 需要判断 policy 是否只是存在，还是已经成为 enforced execution authority。
- 用户要求“如果只能改 3 个地方 / 10 个函数 / 20% 改动”的安全顺序。

不要用于普通模块清单、DDD 术语整理或无运行时决策含义的代码 review。

## Inputs

1. 被审计的 decision object：例如 `next_action`、`feedback_intent`、`progress_tree_state`。
2. 候选 authority：例如某个 policy、service、facade、schema 或 token。
3. 用户要求的输出结构和允许读取范围。
4. 是否只读。默认只读。

## Required Context

1. 读取 `AGENTS.md` 与 `docs/00-governance/DOCS_INDEX.md`，确认 active truth source 和 archive 边界。
2. 若任务跨模块，先用 `aifi-context-index-gate` 或 CodeGraph/semantic tools 缩小路径。
3. 最终结论必须回到当前代码、tests、API/schema/frontend 行为证据；不能只引用历史 docs 或 memory。

## Audit Layers

按层枚举 writer、reader、executor 和 fallback：

1. API layer：endpoint、pending/fallback payload、response assembly、validation。
2. Application/service layer：use case、application service、orchestration facade、task creation。
3. Domain/policy layer：policy decision、rule adapter、reason code、scoring metadata。
4. Storage layer：repository write、post-processing、history payload。
5. Frontend layer：button/menu handler、context action、derived action、passive/active renderer。
6. Runtime/provider/eval layer：graph/runtime descriptor、fake/replay/default-off path。

每层都标出：

- can write?
- can execute?
- can bypass authority?
- validates authority token?
- failure mode: open / closed / unknown

## Procedure

1. 定义 decision object 和 expected authority。
2. 找所有生成、修改、持久化、展示、执行该 decision 的路径。
3. 区分 `authority candidate exists` 与 `authority enforced`。
4. 检查是否有 signed decision / decision_ref / required_refs / reason_codes / policy_signature 这类不可伪造闭环；没有则不能声称 fail-closed。
5. 检查 frontend 是否只是 passive renderer，还是能自行推断或触发执行。
6. 检查 storage 或 fallback 是否会在 policy/validation 之后追加、改写或降级 decision。
7. 输出 yes/no verdict、decision leak map、minimal cut、safe execution order、residual risk。

## Minimal Cut Rules

安全顺序通常是：

1. 先生成 authoritative decision。
2. 再让消费者读取并验证 authority。
3. 再收紧 API/frontend/storage fallback。
4. 最后删除 legacy execution entry。

不要先删 frontend fallback、先强制 API token、或先做 storage hard guard，除非已证明所有消费者能读懂新 authority。

## Output Format

```markdown
## 结论

YES / NO / PARTIAL / UNKNOWN: <是否存在 enforceable single control authority>

## Decision Object

- object:
- expected authority:
- current authority candidate:

## Decision Leak Map

| Layer | Path / Symbol | Can write | Can execute | Bypass | Evidence |
|---|---|---:|---:|---:|---|

## Enforcement Gap

- policy exists:
- signature/token validation:
- frontend passive mode:
- storage post-processing:
- fallback behavior:

## Minimal Cut

| Step | Change surface | Why first | Breakage risk |
|---|---|---|---|

## Residual Risk

- ...
```

## Common Mistakes

- 看到 policy 函数就断言 control plane 已经收敛。
- 把 schema validation 当成 execution authority。
- 忽略 frontend handler 或 context menu 对状态流的副作用。
- 忽略 repository/history payload 在 validation 后追加字段。
- 把 scoring metadata 与 runtime action owner 混成同一个 authority。
- 在只读窗口把 minimal fix 写成已实现。
