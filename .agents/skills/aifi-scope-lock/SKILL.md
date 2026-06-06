---
name: aifi-scope-lock
description: Establish an AiForInterviewer Scope Lock before controlled read or write work and stop on file, task, operation, or done-condition mismatch.
---

# aifi-scope-lock

## Purpose

在 AiForInterviewer 仓库中建立本轮工作的 Scope Lock，明确范围、允许文件、禁止文件、必要检查和升级条件。只负责边界锁定，不负责业务实现。

## Default mode

- 默认只读核查。
- 只有用户明确给出写入授权时，才允许进入对应的受控写入模式。
- 不执行提交、推送、发布或归档自动化。
- 如果任务需要跨模块理解、影响面分析、调用链分析或大量文件读取，先调用 `aifi-context-index-gate`，用 Understand-Anything / CodeGraph 获取压缩上下文，而不是直接 `Read` / `Grep` 多文件。
- 如果任务需要跨文档 / 代码证据交叉验证，或需要读取多个 project-source / goal / runtime 文件，先调用 `aifi-context-index-gate`，再启动 subagent 或多文件 `Read` / `Grep`。

## Required output

```text
scope: [本轮任务和完成条件]
allowed files: [允许读取或修改的文件/目录]
forbidden files: [禁止读取或修改的文件/目录]
required checks: [修改前后必须执行的检查]
escalation condition: [何时停止并请求确认]
```

## Execution steps

1. 对照用户请求建立 Scope Lock。
2. 核对待读取、待编辑文件和操作是否在授权范围内。
3. 涉及阶段、任务、需求、归档或治理入口时，按 `AGENTS.md` 读取对应 active 入口；否则不强制读取大量治理文档。
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
- 不用多文件 `Read` / `Grep` 替代必要的 `aifi-context-index-gate` 前置查询。
- 不创建临时计划、并行任务体系或旧路线图入口。
- 不执行提交、推送、发布或归档自动化。
