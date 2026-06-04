---
title: 10_EXECUTION_WINDOW_PROTOCOL
type: note
permalink: ai-for-interviewer/docs/project-sources/10-execution-window-protocol
---

# 10 Execution Window Protocol

## 目的

每个实施窗口必须受控执行，防止 scope 漂移、目标偏移、文档与代码事实混淆、子窗口越权修改。

## 每个窗口必须包含

- Window ID
- Phase
- Capability IDs
- Goal
- Current evidence
- Allowed files
- Forbidden files
- Behavior change allowed
- Prompt/schema/provider change allowed
- DB schema change allowed
- Tests
- Eval
- Rollback
- Done criteria
- Final report format

## Source of Truth

每个窗口必须遵守：

1. 用户明确确认。
2. GitHub main 当前代码。
3. 当前测试 / Eval 结果。
4. Project source 文档。
5. GOAL0531 历史目标和阶段意图。
6. 历史聊天。
7. 子窗口输出，必须经总控审计。

如果冲突：

- GitHub 描述当前实现。
- Project source 描述目标架构和规则。
- GOAL 描述历史意图。
- 差异记录为 gap。

## 标准流程

### 1. Recon

必须先读取：

- 目标文件
- 调用方
- 被调用方
- 相关测试
- runtime 配置
- Project sources

禁止未 recon 直接 patch。

### 2. Classify

识别：

- Capability IDs
- Phase
- Layer
- 是否触及 forbidden scope
- 是否需要用户确认

### 3. Scope Lock

冻结：

- allowed files
- forbidden files
- behavior change
- prompt/schema/provider change
- DB schema change
- tests
- rollback

### 4. Patch

规则：

- 最小 diff
- 不大范围格式化
- 不越权
- 不混入下个 Phase
- 不把 fallback 当成功
- 不把 candidate 当 formal fact

### 5. Validate

必须运行指定测试。
不能运行则说明原因和风险。

### 6. Report

最终报告必须包含：

1. Root Cause
2. What Changed
3. Files Changed
4. Behavior Before / After
5. Validation Commands and Results
6. Remaining Risks
7. Follow-up Goal

### 7. Backfill

必须更新：

- Traceability Matrix
- Decision Log
- Risk Register
- Acceptance Gates when needed
- Phase Roadmap when needed

## Phase 1 Special Rule

Phase 1 定义：

DDD Rails + Agent Platform C0 + Polish Facade Convergence

Phase 1 允许：

- 项目级 DDD rails
- Agent contracts / registry / executor port skeleton
- PolishUseCases facade 收敛
- focused application services ownership extraction
- architecture / boundary tests
- provider boundary tests only

Phase 1 禁止：

- prompt rewrite
- provider behavior refactor
- DB schema change
- API contract change
- Question / Feedback domain policy migration
- LangGraph full runtime migration
- full AgentExecutor runtime migration
- Eval gate finalization
- asset formal write behavior change

Phase 1 不得把 B 当完成态。
B，即 contracts + registry skeleton，只能作为 C0 的一部分。
目标态是 C：AgentExecutor + SkillRegistry + ToolRegistry 并最终接入 Question / Feedback。

## Stop Conditions

必须停止并回总控确认：

- 需要修改 forbidden files。
- 需要改变未授权 prompt/schema/provider/DB。
- 无法读取关键文件。
- 发现 GOAL / Project source / GitHub 重大冲突。
- 需要把 candidate 写成 formal fact。
- 需要 Agent 直接写业务对象。
- 需要 Tool 直接暴露 repository。
- 需要 provider request 携带 full prompt asset fallback。
- 发现测试要求与目标架构冲突。

## Window Template

```md
Window ID:
<WINDOW_ID>

Phase:
<PHASE_NAME>

Capability IDs:
<CAPABILITY_IDS>

Goal:
<GOAL>

Current Evidence:
<GITHUB_CODE / TEST_RESULT / PROJECT_SOURCE / GOAL_SOURCE>

Allowed Files:
<ALLOWED_FILES>

Forbidden Files:
<FORBIDDEN_FILES>

Behavior Change Allowed:
yes/no

Prompt/schema/provider Change Allowed:
yes/no

DB Schema Change Allowed:
yes/no

Implementation Requirements:
<REQUIREMENTS>

Validation Commands:
<COMMANDS>

Rollback:
<ROLLBACK>

Done Criteria:
<DONE_CRITERIA>

Final Output:
1. Root Cause
2. What Changed
3. Files Changed
4. Behavior Before / After
5. Validation Commands and Results
6. Remaining Risks
7. Follow-up Goal

Stop Conditions:
<STOP_CONDITIONS>
```