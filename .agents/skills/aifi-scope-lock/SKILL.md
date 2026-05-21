---
name: aifi-scope-lock
description: Establish an AiForInterviewer Scope Lock before controlled read or write work and stop on file, task, operation, or done-condition mismatch.
---

# aifi-scope-lock

## Purpose

在 AiForInterviewer 仓库中建立本轮工作的 Scope Lock，明确 task_id、文件范围、允许操作、禁止操作、最终交付物和完成条件。

## Default mode

- 默认只读核查。
- 只有用户明确给出写入授权时，才允许进入对应的受控写入模式。
- 不执行提交、推送、发布或归档自动化。

## Required Scope Lock

```text
task_id: [如适用，必须是 AIFI-*]
files: [允许读取或修改的文件清单]
figma_nodes: [如适用，精确 node_id 清单]
allowed_ops: [READ_ONLY / EDIT_ONE_FILE / EDIT_LISTED_FILES / COMMIT_ONLY]
forbidden_ops: [禁止动作]
final_artifact: [最终交付物]
done_condition: [完成条件]
```

## Execution steps

1. 读取 `AGENTS.md`、`docs/00-governance/DOCS_INDEX.md` 和当前任务相关 active 入口。
2. 对照用户请求建立 Scope Lock。
3. 核对 task_id、文件路径、figma_nodes、allowed_ops、forbidden_ops 和 done_condition。
4. 若实际请求、待编辑文件或操作与 Scope Lock 不一致，立即停止并报告 mismatch。
5. 若证据不足，输出 `UNKNOWN` 或 `待核查`，不得推断通过。

## Mismatch report

```markdown
## 结论

UNKNOWN：Scope Lock mismatch，已停止。

## Scope checked

- task_id: ...
- files: ...
- figma_nodes: ...
- allowed_ops: ...

## 证据

| 检查项 | 证据来源 | 读取范围 | 结论 | 说明 |
|---|---|---|---|---|

## 风险

- ...

## 下一步动作

- 请确认新的 Scope Lock 或授权范围。
```

## Forbidden actions

- 不扩大读取或修改范围。
- 不修改未列入 Scope Lock 的文件。
- 不创建临时计划、并行任务体系或旧路线图入口。
- 不执行提交、推送、发布或归档自动化。
