# M10 管理台、治理与可观测性 - 模块需求

## 1. 文档定位

- 本文档用于把原始需求和原始实施计划中与“管理台、治理与可观测性”相关的内容提炼成模块级需求。
- 当前状态：初稿。
- 下游输入目标：MODULE_DESIGN.md、MODULE_API_DESIGN.md、MODULE_SCHEMA_DESIGN.md、MODULE_LOGIC_DESIGN.md。

## 2. 来源文档

> W13-StateArchive 说明：本节中的旧 P1 设计稿和旧实现计划引用仅用于历史追溯；当前一期工作台 MVP 事实以 `PLAN_LATEST.md`、四份 W13 唯一事实源、`DESIGN_DECISIONS.md` 与 `OPEN_QUESTIONS.md` 为准。

### 2.1 原始需求引用
- docs/superpowers/specs/2026-04-20-ai-interview-p1-design.md：5.4 日志与可观测性组件
- docs/superpowers/specs/2026-04-20-ai-interview-p1-design.md：12 权限与治理
- docs/superpowers/specs/2026-04-20-ai-interview-p1-design.md：13 管理台能力
- docs/superpowers/specs/2026-04-20-ai-interview-p1-design.md：15.8 管理台

### 2.2 原始实施计划引用
- docs/superpowers/plans/2026-04-20-ai-interview-p1-implementation.md：365-370 治理域
- docs/superpowers/plans/2026-04-20-ai-interview-p1-implementation.md：464-478 管理台 API
- docs/superpowers/plans/2026-04-20-ai-interview-p1-implementation.md：779-801 日志基线
- docs/superpowers/plans/2026-04-20-ai-interview-p1-implementation.md：981-1002 里程碑 11
- docs/superpowers/plans/2026-04-20-ai-interview-p1-implementation.md：4047-4296 任务 11

## 3. 模块目标

- 定义管理台成员治理、模型目录、评分规则、系统设置、日志、CI/E2E 和 search snapshot 运维接口。

## 4. 模块范围内
- 管理台成员管理
- 模型目录与推荐来源
- 评分规则与系统设置
- 日志、CI/E2E、运维接口

## 5. 不在本模块范围内
- 生产级监控平台
- 自动化在线模型同步

## 6. 关键角色与对象
- model_registry_entries
- scoring_rules
- system_settings
- admin audit / ops records

## 7. 关键流程
- 管理员治理操作
- 模型推荐来源与配置
- 日志与测试基线
- search snapshot 导入/运维边界

## 8. 对下游文档的输出要求

- MODULE_DESIGN.md 需要基于本文件明确组件拆分与职责边界。
- MODULE_API_DESIGN.md 需要基于本文件明确接口、鉴权与错误语义。
- MODULE_SCHEMA_DESIGN.md 需要基于本文件明确数据对象、关系、状态和约束。
- MODULE_LOGIC_DESIGN.md 需要基于本文件明确流程、规则、状态机与异常路径。

## 9. 当前缺口

- 仍需把原始文档中的细节进一步提纯到稳定边界。
- 仍需把跨模块耦合点从“描述性要求”转为“可引用的文档输入”。

## 10. 旧待确认问题处理

- 当前无模块内 open 问题。
- OQ-002 已由 W13 `FC-19` 标记为 historical：仅保留为 W10 旧口径来源追踪，不再作为当前一期 MVP 事实源。
- OQ-004 已由 W13 `FC-02` confirmed 覆盖：一期采用 session cookie。
- OQ-005 已由 W13 `FC-02` confirmed 覆盖：一期角色为普通用户 / 管理员两级，管理员可额外按团队筛选。
- OQ-007 已由 W13 `FC-12` confirmed 覆盖：上传同步入库，转换和导出异步。
- OQ-017 已由 W13 `FC-18` confirmed 覆盖：模型采用本地 catalog / seed。
- OQ-018 已由 W13 `FC-18` confirmed 覆盖：snapshot 只导入不抓取，管理台负责导入与运维入口。
- 以上事实源以 `OPEN_QUESTIONS.md`、`DESIGN_DECISIONS.md` 和 W13 唯一事实源文档为准，不再作为当前阻塞。

## 11. 关联文档

- MODULE_DESIGN.md。
- MODULE_API_DESIGN.md。
- MODULE_SCHEMA_DESIGN.md。
- MODULE_LOGIC_DESIGN.md。
- MODULE_TASK_INDEX.md。
- MODULE_DEPENDENCIES.md。
- MODULE_OPEN_QUESTIONS.md。
