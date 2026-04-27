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
| M01 | `docs/modules/M01-foundation-and-platform/` | 基础设施、平台边界与共享能力 | not implementation-ready |
| M02 | `docs/modules/M02-identity-and-team/` | 身份、团队、成员与权限边界 | not implementation-ready |
| M03 | `docs/modules/M03-jobs-resumes-and-documents/` | 岗位、简历与文档资料边界 | not implementation-ready |
| M04 | `docs/modules/M04-match-analysis-and-evidence/` | 匹配分析、评分证据与规则版本边界 | not implementation-ready |
| M05 | `docs/modules/M05-assets-and-retrieval/` | 资产、知识库、检索与归档边界 | not implementation-ready |
| M06 | `docs/modules/M06-simulated-interview-and-context/` | 模拟面试、上下文包、LLM / RAG 与多轮边界 | not implementation-ready |
| M07 | `docs/modules/M07-polish-assessment-and-progress/` | 打磨、评估与进度边界 | not implementation-ready |
| M08 | `docs/modules/M08-review-and-replay/` | 复盘、回放、真实面试输入与导出边界 | not implementation-ready |
| M09 | `docs/modules/M09-training-and-weakness-lifecycle/` | 训练、薄弱项与生命周期边界 | not implementation-ready |
| M10 | `docs/modules/M10-admin-governance-and-observability/` | 管理台、治理、可观测性与收口边界 | not implementation-ready |

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
- 当前跨模块任务文档入口为 `docs/tasks/workbench-mvp/**`，任务是否可实施仍以状态层 gate 为准。
