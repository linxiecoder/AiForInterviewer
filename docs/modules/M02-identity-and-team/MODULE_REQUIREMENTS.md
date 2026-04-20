# M02 鉴权、团队与成员 - 模块需求

## 1. 文档定位

- 本文档用于把原始需求和原始实施计划中与“鉴权、团队与成员”相关的内容提炼成模块级需求。
- 当前状态：初稿。
- 下游输入目标：MODULE_DESIGN.md、MODULE_API_DESIGN.md、MODULE_SCHEMA_DESIGN.md、MODULE_LOGIC_DESIGN.md。

## 2. 来源文档

### 2.1 原始需求引用
- docs/superpowers/specs/2026-04-20-ai-interview-p1-design.md：3.1 用户与团队模型
- docs/superpowers/specs/2026-04-20-ai-interview-p1-design.md：7.1 团队与用户
- docs/superpowers/specs/2026-04-20-ai-interview-p1-design.md：12 权限与治理

### 2.2 原始实施计划引用
- docs/superpowers/plans/2026-04-20-ai-interview-p1-implementation.md：314-320 身份与团队域
- docs/superpowers/plans/2026-04-20-ai-interview-p1-implementation.md：373-384 鉴权与成员 API
- docs/superpowers/plans/2026-04-20-ai-interview-p1-implementation.md：635-666 权限矩阵与鉴权验证基线
- docs/superpowers/plans/2026-04-20-ai-interview-p1-implementation.md：1645-1936 任务 3

## 3. 模块目标

- 定义 P1 的身份模型、团队隔离规则、成员目录和权限矩阵。

## 4. 模块范围内
- 鉴权机制边界
- 团队、用户、成员对象
- 成员目录与登录流程
- 管理员/成员权限矩阵

## 5. 不在本模块范围内
- 外部用户系统集成
- 生产级 SSO
- 复杂租户计费

## 6. 关键角色与对象
- teams
- users
- memberships / team-user 关系
- auth token / session

## 7. 关键流程
- 登录返回当前用户上下文
- 跨团队访问限制
- 管理员与成员的读写边界

## 8. 对下游文档的输出要求

- MODULE_DESIGN.md 需要基于本文件明确组件拆分与职责边界。
- MODULE_API_DESIGN.md 需要基于本文件明确接口、鉴权与错误语义。
- MODULE_SCHEMA_DESIGN.md 需要基于本文件明确数据对象、关系、状态和约束。
- MODULE_LOGIC_DESIGN.md 需要基于本文件明确流程、规则、状态机与异常路径。

## 9. 当前缺口

- 仍需把原始文档中的细节进一步提纯到稳定边界。
- 仍需把跨模块耦合点从“描述性要求”转为“可引用的文档输入”。

## 10. 待确认问题
- OQ-004 P1 鉴权机制采用固定 Bearer token、JWT 还是 session cookie
- OQ-005 团队管理员与普通成员的权限矩阵是否先只覆盖 P1 页面

## 11. 关联文档

- MODULE_DESIGN.md。
- MODULE_API_DESIGN.md。
- MODULE_SCHEMA_DESIGN.md。
- MODULE_LOGIC_DESIGN.md。
- MODULE_TASK_INDEX.md。
- MODULE_DEPENDENCIES.md。
- MODULE_OPEN_QUESTIONS.md。
