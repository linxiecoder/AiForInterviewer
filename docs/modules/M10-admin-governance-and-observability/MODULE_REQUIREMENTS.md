# M10 管理台、治理与可观测性 - 模块需求

## 1. 文档定位

- 本文档用于把原始需求和原始实施计划中与“管理台、治理与可观测性”相关的内容提炼成模块级需求。
- 当前状态：初稿。
- 下游输入目标：MODULE_DESIGN.md、MODULE_API_DESIGN.md、MODULE_SCHEMA_DESIGN.md、MODULE_LOGIC_DESIGN.md。

## 2. 来源文档

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

## 10. 待确认问题
- OQ-002 首轮是否只建立最小运行时、测试和 CI 基线
- OQ-004 P1 鉴权机制采用固定 Bearer token、JWT 还是 session cookie
- OQ-005 团队管理员与普通成员的权限矩阵是否先只覆盖 P1 页面
- OQ-007 上传、转换、导出在 P1 中哪些必须异步
- OQ-017 管理台的模型推荐来源是本地 catalog 还是在线同步
- OQ-018 管理台是否负责 search snapshot 导入与运维

## 11. 关联文档

- MODULE_DESIGN.md。
- MODULE_API_DESIGN.md。
- MODULE_SCHEMA_DESIGN.md。
- MODULE_LOGIC_DESIGN.md。
- MODULE_TASK_INDEX.md。
- MODULE_DEPENDENCIES.md。
- MODULE_OPEN_QUESTIONS.md。
