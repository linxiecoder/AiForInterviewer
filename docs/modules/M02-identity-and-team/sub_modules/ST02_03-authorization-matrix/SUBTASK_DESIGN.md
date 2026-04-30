---
title: SUBTASK_DESIGN
type: note
permalink: ai-for-interviewer/docs/modules/m02-identity-and-team/sub-modules/st02-03-authorization-matrix/subtask-design
---

# ST02_03 授权矩阵与管理员/成员边界 - 子任务设计

## 1. 文档定位

- 本文档承接模块设计，并把“授权矩阵与管理员/成员边界”拆成可持续细化的子任务设计单元。
- 当前成熟度：仅有骨架。

## 2. 父模块

- M02 鉴权、团队与成员。

## 3. 子任务目标

- 明确权限矩阵、401/403 语义、跨团队访问规则和管理员/成员边界。

## 4. 输入文档

- ../../MODULE_REQUIREMENTS.md
- ../../MODULE_DESIGN.md
- ../../MODULE_API_DESIGN.md
- ../../MODULE_SCHEMA_DESIGN.md
- ../../MODULE_LOGIC_DESIGN.md

## 5. 范围内

- 权限矩阵文档
- 管理员与成员的能力边界
- 401 / 403 / 跨团队访问规则
- 权限测试基线

## 6. 不在范围内

- 不直接进入代码实现。
- 不替代鉴权机制本身的技术选型。
- 不覆盖团队、用户与成员目录的数据建模细节。

## 7. 当前已知目标区域

- `apps/api/app/api/routes/**`
- `apps/api/app/services/authorization/**`
- `apps/web/src/lib/permissions/**`
- `apps/web/src/app/(dashboard)/**`

## 8. 当前设计缺口

- 仍需明确输入输出契约。
- 仍需明确页面级和接口级权限边界。
- 仍需明确验证方式和 DoD。
- 仍需把目标区域收敛到可实施的文件级边界。

## 9. 设计完成判定

- 输入、输出、范围和依赖稳定。
- 管理员与成员的可见性、可操作性边界明确。
- 401 / 403 / 跨团队访问规则可验证。
- 没有阻塞级待确认问题。

## 10. 当前待确认内容

- OQ-004 P1 鉴权机制采用固定 Bearer token、JWT 还是 session cookie。
- OQ-005 团队管理员与普通成员的权限矩阵是否先只覆盖 P1 页面。

## 11. 下一轮建议补充

- 补充精确输入输出。
- 补充接口/字段/状态相关设计。
- 补充验证目标与下游引用方式。