---
title: ADR-0001-document-governance
type: decision
status: accepted
owner: 文档治理
date: 2026-05-02
permalink: ai-for-interviewer/docs/04-decisions/adr-0001-document-governance
---

# ADR-0001 文档治理唯一体系

## 状态

Accepted

## 背景

F0 审计确认仓库中曾同时存在多套文档入口、旧计划、旧任务索引、模块文档和归档报告。并行入口会让后续 Codex 或人工协作者误把历史材料恢复为当前执行依据。

## 决策

1. 当前有效文档索引只由 `docs/00-governance/DOCS_INDEX.md` 承载。
2. 文档生命周期、命名、归档、迁移和防腐规则只由 `docs/00-governance/DOCS_GOVERNANCE.md` 承载。
3. AI / Codex 工作流只由 `docs/00-governance/AI_WORKFLOW.md` 承载。
4. `archive/` 只保存历史来源、证据、废弃文档和审计报告，不作为当前执行依据。
5. 所有归档动作必须登记到 `archive/MANIFEST.md`。
6. 历史内容如仍有效，必须先迁入 active docs，再参与后续交付。

## 影响

- 旧文档可以保留历史价值，但不得绕过 active docs。
- 新增正式文档必须先登记到 `DOCS_INDEX.md` 或对应 active 入口。
- 迁移或废弃文档时，不允许删除历史文件，只能移动到 archive 并登记。

## 替代方案

- 保留旧 active canon 和旧 planning/task 入口：拒绝，容易恢复并行事实源。
- 直接删除旧文档：拒绝，破坏历史可追溯性。
