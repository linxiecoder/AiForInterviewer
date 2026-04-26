# AI 模拟面试项目模块索引

## 1. 文档定位

本文档只作为模块导航和模块状态摘要，不承载完整模块设计正文、需求正文、任务正文或过程日志。

## 2. 模块文档规则

| 文档 | 职责 |
| --- | --- |
| `MODULE_REQUIREMENTS.md` | 模块需求 |
| `MODULE_DESIGN.md` | 模块设计 |
| `MODULE_API_DESIGN.md` | API 设计 |
| `MODULE_SCHEMA_DESIGN.md` | schema 设计 |
| `MODULE_LOGIC_DESIGN.md` | 逻辑设计 |
| `MODULE_TASK_INDEX.md` | 模块任务索引 |
| `MODULE_OPEN_QUESTIONS.md` | 模块问题 |
| `MODULE_EXECUTION_LOG.md` | 模块过程记录 |

## 3. 模块入口

| module | path | primary responsibility | current status |
| --- | --- | --- | --- |
| M01 | `docs/modules/M01-M10/M01/` | 基础用户、权限与共享适配边界 | not implementation-ready |
| M02 | `docs/modules/M01-M10/M02/` | 成员 / 账号 / 基础访问边界 | not implementation-ready |
| M03 | `docs/modules/M01-M10/M03/` | 岗位 / 简历 / 资料管理边界 | not implementation-ready |
| M04 | `docs/modules/M01-M10/M04/` | 面试记录与会话边界 | not implementation-ready |
| M05 | `docs/modules/M01-M10/M05/` | 面试工作台交互边界 | not implementation-ready |
| M06 | `docs/modules/M01-M10/M06/` | LLM / RAG / 多轮上下文边界 | not implementation-ready |
| M07 | `docs/modules/M01-M10/M07/` | 评分、反馈与复盘边界 | not implementation-ready |
| M08 | `docs/modules/M01-M10/M08/` | 导出与结果交付边界 | not implementation-ready |
| M09 | `docs/modules/M01-M10/M09/` | 弱点训练材料边界 | not implementation-ready |
| M10 | `docs/modules/M01-M10/M10/` | 文档治理、测试与收口边界 | not implementation-ready |

## 4. 上游输入

| input | use |
| --- | --- |
| `docs/requirements/workbench-mvp/**` | Workbench MVP 需求范围与验收输入 |
| `docs/design/workbench-mvp/**` | Workbench MVP 设计输入 |
| `TASK_INDEX.md` | 跨模块任务索引 |
| `docs/governance/DOC_STATE.yaml` | 正式状态与 gate |

## 5. 当前约束

- 模块文档不得引用历史材料作为当前 source。
- 模块文档不得提升 maturity 或 implementation readiness。
- 模块文档不得打开子任务窗口。
- 被状态层引用的任务文档需要另开状态迁移窗口处理路径问题。
