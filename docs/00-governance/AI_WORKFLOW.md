---
title: AI_WORKFLOW
type: governance
status: active-f0
owner: 文档治理
permalink: ai-for-interviewer/docs/00-governance/ai-workflow
---

# AI_WORKFLOW

本文档约束 Codex / AI 在 AiForInterviewer 仓库中的读取、修改、落库和收口流程。

## 1. 默认读取顺序

1. `AGENTS.md`
2. `docs/00-governance/DOCS_INDEX.md`
3. 与当前任务对应的唯一入口：
   - 阶段：`docs/03-delivery/DELIVERY_PLAN.md`
   - 任务：`docs/03-delivery/BACKLOG.md`
   - 需求追踪：`docs/01-product/REQUIREMENT_TRACEABILITY.md`
   - 归档：`archive/MANIFEST.md`

## 2. 修改前检查

修改前必须确认：

- 本轮是否有明确目标、允许路径和禁止路径。
- 是否会新增文档入口、阶段体系或任务体系。
- 是否引用了 archive 内容作为执行依据。
- 是否触碰仍可能被 state/source_doc 绑定的旧文件。
- 是否需要先登记到 `BACKLOG.md` 或 `MANIFEST.md`。

## 3. 写入规则

| 内容 | 写入位置 |
| --- | --- |
| 新任务 | `docs/03-delivery/BACKLOG.md` |
| 新阶段或里程碑 | `docs/03-delivery/DELIVERY_PLAN.md` |
| 历史需求追踪 | `docs/01-product/REQUIREMENT_TRACEABILITY.md` |
| 归档动作 | `archive/MANIFEST.md` |
| 治理规则变更 | `docs/00-governance/DOCS_GOVERNANCE.md` |

Codex 不得把临时分析文件升级为 active 文档，也不得绕过上述入口创建新的长期真值。

## 4. archive 使用规则

- 可以读取 archive 作为历史证据。
- 不得把 archive 作为当前执行依据。
- 需要复用 archive 内容时，先迁入 active 文档并建立追踪。
- 归档审计报告只提供证据，不替代 `DOCS_INDEX.md`、`DELIVERY_PLAN.md`、`BACKLOG.md` 或 `REQUIREMENT_TRACEABILITY.md`。

## 5. 完成输出

每次完成文档治理落库或迁移后，输出：

1. `git status --short`
2. `git diff --stat`
3. 新增文件清单
4. 修改文件清单
5. 移动到 archive 的文件清单
6. 仍需人工确认的问题
7. 旧阶段或旧任务体系是否仍存在于 active docs
