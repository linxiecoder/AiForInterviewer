---
title: ADR-0002-unified-delivery-system
type: decision
status: accepted
owner: 文档治理
date: 2026-05-02
permalink: ai-for-interviewer/docs/04-decisions/adr-0002-unified-delivery-system
---

# ADR-0002 统一交付体系

## 状态

Accepted

## 背景

F0 审计确认旧阶段、旧计划和旧任务编号散落在历史文档、模块文档和任务包中。继续使用这些体系会造成执行窗口、Backlog 和交付计划并行。

## 决策

1. 废弃旧 R 系推进语言作为活跃阶段体系。
2. 废弃旧 P 系编号作为活跃阶段体系。
3. 当前阶段只使用 `F0` 到 `F8`。
4. 当前里程碑只使用 `M0` 到 `M8`。
5. 当前任务只使用 `AIFI-*`。
6. 当前优先级只使用 `MUST`、`SHOULD`、`COULD`、`LATER`。
7. 所有阶段进入 `docs/03-delivery/DELIVERY_PLAN.md`。
8. 所有任务进入 `docs/03-delivery/BACKLOG.md`。

## 影响

- 旧编号只能作为历史来源出现在 `docs/01-product/REQUIREMENT_TRACEABILITY.md` 或 `archive/MANIFEST.md`。
- 新任务不得直接写入旧任务包、旧模块任务索引或临时计划文档。
- 后续实现窗口必须从 `BACKLOG.md` 选取 `AIFI-*` 任务。

## 替代方案

- 保留旧编号并新增映射层：拒绝，会继续扩大文档体系复杂度。
- 同时维护旧 Backlog 和新 Backlog：拒绝，会造成执行入口分裂。
