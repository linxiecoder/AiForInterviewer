# M01 基础平台与工作台壳层 - 模块需求

## 1. 文档定位

- 本文档用于把原始需求和原始实施计划中与“基础平台与工作台壳层”相关的内容提炼成模块级需求。
- 当前状态：初稿。
- 下游输入目标：MODULE_DESIGN.md、MODULE_API_DESIGN.md、MODULE_SCHEMA_DESIGN.md、MODULE_LOGIC_DESIGN.md。

## 2. 来源文档

### 2.1 原始需求引用
- docs/superpowers/specs/2026-04-20-ai-interview-p1-design.md：4 推荐技术方案
- docs/superpowers/specs/2026-04-20-ai-interview-p1-design.md：5.1 前端 Web 层
- docs/superpowers/specs/2026-04-20-ai-interview-p1-design.md：5.2 前端 UI 组件层
- docs/superpowers/specs/2026-04-20-ai-interview-p1-design.md：14 页面信息架构
- docs/superpowers/specs/2026-04-20-ai-interview-p1-design.md：16 全局交互规范
- docs/superpowers/specs/2026-04-20-ai-interview-p1-design.md：19 视觉风格规范

### 2.2 原始实施计划引用
- docs/superpowers/plans/2026-04-20-ai-interview-p1-implementation.md：22-282 目标仓库结构与完整仓库目录规划
- docs/superpowers/plans/2026-04-20-ai-interview-p1-implementation.md：282-303 环境基线
- docs/superpowers/plans/2026-04-20-ai-interview-p1-implementation.md：303-310 跨任务约束
- docs/superpowers/plans/2026-04-20-ai-interview-p1-implementation.md：1003-1391 任务 1
- docs/superpowers/plans/2026-04-20-ai-interview-p1-implementation.md：1392-1644 任务 2

## 3. 模块目标

- 建立全新项目的仓库结构、运行时基线、工作台壳层、i18n 入口、列表原语、测试与文档治理规则。

## 4. 模块范围内
- 仓库目录、环境模板、基础设施占位
- FastAPI 健康检查与日志初始化
- Next.js 最小入口、App Shell、列表原语
- i18n 消息入口与文档治理约束

## 5. 不在本模块范围内
- 业务领域对象
- 正式鉴权与权限矩阵
- AI 推理与检索能力

## 6. 关键角色与对象
- 环境变量清单
- 健康检查响应
- 页面壳层配置
- i18n 消息资源

## 7. 关键流程
- 本地开发环境启动顺序
- 工作台壳层与列表原语复用规则
- 文档更新与索引同步规则

## 8. 对下游文档的输出要求

- MODULE_DESIGN.md 需要基于本文件明确组件拆分与职责边界。
- MODULE_API_DESIGN.md 需要基于本文件明确接口、鉴权与错误语义。
- MODULE_SCHEMA_DESIGN.md 需要基于本文件明确数据对象、关系、状态和约束。
- MODULE_LOGIC_DESIGN.md 需要基于本文件明确流程、规则、状态机与异常路径。

## 9. 当前缺口

- 仍需把原始文档中的细节进一步提纯到稳定边界。
- 仍需把跨模块耦合点从“描述性要求”转为“可引用的文档输入”。

## 10. 待确认问题
- OQ-001 仓库结构是否固定为 monorepo (`apps/web` + `apps/api` + `infra`)
- OQ-002 首轮是否只建立最小运行时、测试和 CI 基线
- OQ-003 视觉规范首轮需要沉淀到什么粒度

## 11. 关联文档

- MODULE_DESIGN.md。
- MODULE_API_DESIGN.md。
- MODULE_SCHEMA_DESIGN.md。
- MODULE_LOGIC_DESIGN.md。
- MODULE_TASK_INDEX.md。
- MODULE_DEPENDENCIES.md。
- MODULE_OPEN_QUESTIONS.md。
