---
title: SUBTASK_DESIGN
type: note
permalink: ai-for-interviewer/docs/modules/m10-admin-governance-and-observability/sub-modules/st10-01-admin-member-and-role-ops/subtask-design
---

# ST10_01 成员治理与角色操作 - 子任务设计

## 1. 文档定位

- 本文档承接模块设计，并把“成员治理与角色操作”拆成可持续细化的子任务设计单元。
- 当前成熟度：仅有骨架。

## 2. 父模块

- M10 管理台、治理与可观测性；父级索引：[MODULE_TASK_INDEX.md](../../MODULE_TASK_INDEX.md)。

## 3. 子任务目标

- 明确管理台中的成员治理、角色分配和团队管理员入口。

## 4. 输入文档

- ../../MODULE_REQUIREMENTS.md。
- ../../MODULE_DESIGN.md。
- ../../MODULE_API_DESIGN.md。
- ../../MODULE_SCHEMA_DESIGN.md。
- ../../MODULE_LOGIC_DESIGN.md。

## 5. 范围内
- 管理台成员治理设计
- 角色操作边界
- 权限依赖清单

## 6. 不在范围内

- 不直接进入代码实现。
- 不替代父模块的全局边界定义。
- 不解决未进入本子任务范围的跨模块问题。

## 7. 当前已知目标区域
- apps/api/app/api/routes/admin.py
- apps/web/src/app/(dashboard)/admin/members/**

## 8. 当前设计缺口

- 仍需明确输入输出契约。
- 仍需明确验证方式和 DoD。
- 仍需进一步缩小到可实施的文件/页面/接口边界。

## 9. 设计完成判定

- 输入、输出、范围、依赖稳定。
- 目标对象、页面或接口边界明确。
- 验证目标可描述。
- 没有阻塞级待确认问题。

## 10. 旧待确认内容处理

- 当前无子任务内 open 问题。
- OQ-004 已由当前需求 / 设计输入中的 `FC-02` confirmed 覆盖：一期采用 session cookie。
- OQ-005 已由当前需求 / 设计输入中的 `FC-02` confirmed 覆盖：一期角色为普通用户 / 管理员两级，管理员可额外按团队筛选。
- 该确认不激活本 ST，也不改变“当前成熟度：仅有骨架”的状态。

## 11. 下一轮建议补充

- 补充精确输入输出。
- 补充接口/字段/状态相关设计。
- 补充验证目标与下游引用方式。