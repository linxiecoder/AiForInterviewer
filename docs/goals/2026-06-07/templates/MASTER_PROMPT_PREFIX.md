---
title: MASTER_PROMPT_PREFIX
type: note
permalink: ai-for-interviewer/docs/goals/2026-06-07/templates/master-prompt-prefix
---

# Master Prompt Prefix

Use this prefix before any window prompt when sending work to Codex.

```md
你现在在 AiForInterviewer 仓库中执行受控重构窗口。

必须遵守：

1. 用户确认是最高优先级。
2. GitHub main 当前代码是当前实现事实源。
3. 当前测试 / Eval 结果是行为证据源。
4. Project source 是目标架构和窗口治理规则源。
5. GOAL0531 是历史目标和阶段意图源，不是当前代码事实源。
6. 子窗口输出必须经总控审计，不得直接作为 done evidence。

如果 GOAL / Project source / GitHub 冲突：

- GitHub 描述当前实现。
- Project source 描述目标架构和规则。
- GOAL 描述历史意图。
- 差异记录为 gap。

执行规则：

- 必须先 recon，再 classify，再 scope lock，再 patch，再 validate，再 report/backfill。
- 不得未 recon 直接 patch。
- 不得修改 forbidden files。
- 不得把 fallback 当 generated success。
- 不得把 candidate 当 formal business fact。
- Agent 不得直接写正式业务事实。
- Tool 不得直接暴露 repository。
- Provider request 必须 compact and fail-closed。
- Fake 只能用于 tests / evals / replay。
- 若触发 stop condition，停止并返回总控。
```