---
title: MODULE_REQUIREMENTS
type: note
permalink: ai-for-interviewer/docs/modules/m05-assets-and-retrieval/module-requirements
---

# M05 资产库、归档与检索 - 模块需求

## 0. Workbench MVP 当前需求与设计输入

- 当前需求输入：`docs/requirements/workbench-mvp/`。
- 当前设计输入：`docs/design/workbench-mvp/`。
- 重点引用：`scope.md`、`information-architecture.md`、`object-model-rag-multiround-backend.md`、`scoring-review-export-dod.md`。
- 模块承接摘要：知识库、RAG、检索引用、资产归档和动态 schema 子集。
- 后续补齐项：补齐知识库索引、检索失败降级、资产归档和引用证据边界。
- 边界：本节只记录模块摘要、入口关系和后续补齐项；不复制正式设计正文，不提升模块成熟度，不放行 formal window、implementation packet 或代码实现。

## 1. 文档定位

- 本文档用于把原始需求和原始实施计划中与“资产库、归档与检索”相关的内容提炼成模块级需求。
- 当前状态：初稿。
- 下游输入目标：MODULE_DESIGN.md、MODULE_API_DESIGN.md、MODULE_SCHEMA_DESIGN.md、MODULE_LOGIC_DESIGN.md。

## 2. 来源文档

> historical context：历史 P1 设计稿和历史实现计划只用于追溯，不作为当前依据。当前需求事实源为 `docs/requirements/workbench-mvp/**`，当前设计事实源为 `docs/design/workbench-mvp/**`；规划入口为 `PLAN_LATEST.md`，任务入口为 `TASK_INDEX.md`、`docs/governance/DOC_STATE.yaml` 和当前任务文档。

### 2.1 原始需求引用
- 历史 P1 设计材料：6 问题生成与参考材料原则
- 历史 P1 设计材料：7.4 资产库
- 历史 P1 设计材料：7.9 搜索快照
- 历史 P1 设计材料：9.7 归档到资产库
- 历史 P1 设计材料：15.6 资产库模块

### 2.2 原始实施计划引用
- 历史 P1 实现计划材料：340-345 资产库域
- 历史 P1 实现计划材料：412-424 资产库 API
- 历史 P1 实现计划材料：682-692 资产库与向量数据库
- 历史 P1 实现计划材料：887-902 里程碑 6
- 历史 P1 实现计划材料：2582-2884 任务 6

## 3. 模块目标

- 定义资产类型、资产对象、归档来源和检索入库机制。

## 4. 模块范围内
- 资产类型 schema
- 资产对象与详情
- 归档记录与来源追踪
- 检索分块入库

## 5. 不在本模块范围内
- 在线向量检索前台搜索页
- 复杂 RAG 编排平台

## 6. 关键角色与对象
- asset_types
- assets
- archive_records
- retrieval_chunks

## 7. 关键流程
- 资产录入与结构化字段约束
- 归档来源追踪
- 检索分块与索引任务

## 8. 对下游文档的输出要求

- MODULE_DESIGN.md 需要基于本文件明确组件拆分与职责边界。
- MODULE_API_DESIGN.md 需要基于本文件明确接口、鉴权与错误语义。
- MODULE_SCHEMA_DESIGN.md 需要基于本文件明确数据对象、关系、状态和约束。
- MODULE_LOGIC_DESIGN.md 需要基于本文件明确流程、规则、状态机与异常路径。

## 9. 当前缺口

- 仍需把原始文档中的细节进一步提纯到稳定边界。
- 仍需把跨模块耦合点从“描述性要求”转为“可引用的文档输入”。

## 10. 待确认问题
- 当前无模块级 open 问题。
- historical：旧 `OQ-009` 已由 Workbench MVP 当前设计输入和 `FC-05` / `DD-021` 覆盖；当前口径为 RAG / 知识库进入一期，支持混合检索，失败时降级继续并标注证据缺口。
- historical：旧 `OQ-010` 已由 Workbench MVP 当前设计输入和 `FC-14` / `DD-027` 覆盖；当前口径为一期支持整份和单题归档到资产库，归档时选择资产类型，类型带 schema 时动态渲染字段表单。

## 11. 关联文档

- MODULE_DESIGN.md。
- MODULE_API_DESIGN.md。
- MODULE_SCHEMA_DESIGN.md。
- MODULE_LOGIC_DESIGN.md。
- MODULE_TASK_INDEX.md。
- MODULE_DEPENDENCIES.md。
- MODULE_OPEN_QUESTIONS.md。