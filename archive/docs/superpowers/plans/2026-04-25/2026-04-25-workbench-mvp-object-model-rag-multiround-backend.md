---
title: 2026-04-25-workbench-mvp-object-model-rag-multiround-backend
type: note
permalink: ai-for-interviewer/archive/docs/superpowers/plans/2026-04-25/2026-04-25-workbench-mvp-object-model-rag-multiround-backend
---

# AI 模拟面试一期工作台 MVP 对象模型、RAG、多轮与后端边界草案

## 1. 迁移状态

本文件已完成 Workbench MVP Design Canon 迁移，当前事实源已迁入：

- `docs/design/workbench-mvp/object-model-rag-multiround-backend.md`

当前事实不得再引用本文件作为依据。若本文件与 `docs/design/workbench-mvp/` 内容冲突，以 `docs/design/workbench-mvp/` 为准。

## 2. 历史摘要

本文件曾承载 W13-C / W13-FC 后的一期工作台 MVP 对象模型、RAG、多轮和后端边界结论。

已迁入正式事实源的核心内容包括：

- 账号与权限、岗位与简历、知识库与检索、模拟面试、打磨模式、压力面模式、评分复盘、薄弱项训练、资产导出、LLM 与审计对象族。
- 用户私有知识库、管理员公共知识库、检索引用、证据缺口和失败降级。
- 打磨模式由 `ProgressTree` 驱动，压力面由 `InterviewQuestionSet` 驱动。
- 后端需覆盖服务端保存、权限、RAG、LLM、多轮状态机、评分复盘和导出快照，但本文不定义具体实现。

## 3. 迁移来源说明

本文件是 `docs/design/workbench-mvp/object-model-rag-multiround-backend.md` 的迁移来源之一，仅保留历史追溯和桥接入口价值。

后续对象模型、RAG、多轮和后端边界判断必须引用 `docs/design/workbench-mvp/`。