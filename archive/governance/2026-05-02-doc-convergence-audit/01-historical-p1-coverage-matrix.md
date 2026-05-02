---
title: 2026-05-02-historical-p1-coverage-matrix
type: note
permalink: ai-for-interviewer/archive/governance/2026-05-02-historical-p1-coverage-matrix-1
---

# Historical P1 Design Coverage Matrix

## Purpose

本文档用于审计历史设计稿 `archive/docs/superpowers/specs/2026-04-20-ai-interview-p1-design.md` 中的主要产品、设计、技术和治理内容，在当前 AiForInterviewer 文档体系中的承接状态。

本矩阵只作为归档审计证据，不恢复历史 P1 设计稿的当前事实源地位。当前需求事实源仍是 `docs/requirements/workbench-mvp/**`，当前设计事实源仍是 `docs/design/workbench-mvp/**`，当前计划入口仍是 `PLAN_LATEST.md` 与 `docs/planning/workbench-mvp/MASTER_IMPLEMENTATION_PLAN.md`，当前任务入口仍是 `TASK_INDEX.md`。

## Source documents

- `archive/docs/superpowers/specs/2026-04-20-ai-interview-p1-design.md`
- `docs/requirements/workbench-mvp/README.md`
- `docs/requirements/workbench-mvp/scope-and-acceptance.md`
- `docs/design/workbench-mvp/README.md`
- `docs/design/workbench-mvp/scope.md`
- `docs/design/workbench-mvp/information-architecture.md`
- `docs/design/workbench-mvp/object-model-rag-multiround-backend.md`
- `docs/design/workbench-mvp/scoring-review-export-dod.md`
- `docs/design/workbench-mvp/r1-penpot-lowfi-spec.md`
- `docs/planning/workbench-mvp/MASTER_IMPLEMENTATION_PLAN.md`
- `PLAN_LATEST.md`
- `TASK_INDEX.md`
- `docs/governance/ACTIVE_DOC_CANON.md`

## Classification legend

| status | meaning |
| --- | --- |
| 已吸收 | 历史主题已被当前需求、设计、计划或任务体系承接，可继续从当前事实源读取。 |
| 已替换 | 历史主题已被新的阶段、技术、范围或治理决策替代，不能按历史口径继续推进。 |
| R1/R2 延后 | 历史主题仍有价值，但当前不属于 R0 主链路，需在 R1 或 R2 另窗推进。 |
| 明确不做 | 历史主题已被当前 MVP 范围排除，或不属于当前项目验收目标。 |
| 需要补入当前设计 | 历史主题仍应进入当前体系，但当前设计文档覆盖不足，需要后续窗口补齐。 |

## Coverage matrix

| historical topic | historical source | status | current source / replacement | decision rationale | target phase | follow-up |
| ---------------- | ----------------- | ------ | ---------------------------- | ------------------ | ------------ | --------- |
| 历史 P1 文档目标 | `1. 文档目标` | 已替换 | `docs/governance/ACTIVE_DOC_CANON.md`; `docs/requirements/workbench-mvp/README.md`; `docs/design/workbench-mvp/README.md` | 历史稿不再是当前事实源，当前体系已把需求、设计、计划、任务和治理入口拆开。 | historical-only | none |
| P1/P2/P3 历史分期 | `2. 项目分期` | 已替换 | `docs/planning/workbench-mvp/2026-05-01-r-stage-mapping.md`; `MASTER_IMPLEMENTATION_PLAN.md` | 当前唯一交付阶段为 R0/R1/R2，历史 P* 只保留映射和追溯用途。 | historical-only | 在后续 canon/index 修补中清理活跃标题里的 P1 口径。 |
| P2 多模态面试 | `2. 项目分期 / P2：多模态面试` | 明确不做 | `docs/requirements/workbench-mvp/scope-and-acceptance.md` | 当前 MVP 聚焦 Web 文本工作台，实时语音、视频和多端体验被排除。 | out-of-scope | none |
| P3 高级治理与增强 | `2. 项目分期 / P3：高级治理与增强` | R1/R2 延后 | `MASTER_IMPLEMENTATION_PLAN.md`; `docs/design/workbench-mvp/scoring-review-export-dod.md` | 治理、观测、资产沉淀和训练闭环只在 R1/R2 逐步增强，不进入 R0 主链路。 | R2 | R0 完成后重新评估治理增强窗口。 |
| 单团队用户与团队模型 | `3.1 用户与团队模型` | 已替换 | `scope-and-acceptance.md`; `object-model-rag-multiround-backend.md` | 当前只要求最小身份与权限边界，企业级组织、多团队和复杂多租户不作为一期前提。 | R0 | 在 R0 身份边界窗口中只保留最小可见性设计。 |
| 全量 AI 驱动能力边界 | `3.2 智能能力边界` | 已吸收 | `scope-and-acceptance.md`; `object-model-rag-multiround-backend.md`; `scoring-review-export-dod.md` | 当前已承接 LLM 出题、追问、反馈、复盘、评分解释和训练建议，但按 R0/R1/R2 切片推进。 | R0 | none |
| PDF / MD 简历导入与 PDF 导出细节 | `3.3 简历处理边界`; `9.1 简历导入与编辑` | 需要补入当前设计 | `scope-and-acceptance.md`; `information-architecture.md` | 当前只写岗位与简历材料录入、保存、读取，未完整定义 PDF 原件保留、PDF 转 MD、版本快照和 PDF 导出策略。 | R1 | 建议在 `docs/design/workbench-mvp/object-model-rag-multiround-backend.md` 或后续 M03 设计中补齐导入/转换/版本/导出边界。 |
| 打磨模式 | `3.4 面试模式边界 / 打磨模式`; `9.4 打磨模式` | R1/R2 延后 | `object-model-rag-multiround-backend.md`; `scoring-review-export-dod.md`; `MASTER_IMPLEMENTATION_PLAN.md` | 当前对象模型保留打磨模式和训练抽屉，但 R0 只优先跑通模拟面试主链路。 | R2 | R2 训练闭环窗口再细化打磨模式。 |
| 模拟模式 | `3.4 面试模式边界 / 模拟模式`; `9.5 模拟模式` | 已吸收 | `scope-and-acceptance.md`; `information-architecture.md`; `MASTER_IMPLEMENTATION_PLAN.md` | 当前 R0 主链路就是从岗位、简历、上下文进入文本模拟面试并生成评分复盘。 | R0 | none |
| Next.js + FastAPI + PostgreSQL 历史技术栈 | `4. 推荐技术方案` | 已替换 | `TECHNICAL_STANDARDS.md`; `docs/development/local-startup.md`; `docs/development/database.md`; `apps/web/**`; `apps/api/**` | 当前仓库事实为 `apps/web` Vite/React 和 `apps/api` FastAPI，数据层已支持 PostgreSQL runtime 与 SQLite fallback；Next.js 不再是当前实现事实。 | historical-only | 在 R0-W03 中统一技术栈事实语言。 |
| pgvector、Redis、对象存储 | `4.3 数据层`; `4.4 缓存与异步任务`; `4.5 对象存储` | R1/R2 延后 | `object-model-rag-multiround-backend.md`; `MASTER_IMPLEMENTATION_PLAN.md`; `docs/development/database.md` | 当前只保留 RAG、索引、引用、资产和导出的对象边界，不把 Redis、pgvector 或对象存储作为 R0 必需实现。 | R1 | 后续 R1/R2 数据和 RAG 窗口决定是否引入具体基础设施。 |
| UI 组件层、日志与可观测性、模型注册组件 | `4.6 基础设施补充`; `5.4 日志与可观测性组件` | R1/R2 延后 | `MASTER_IMPLEMENTATION_PLAN.md`; `docs/development/r1-trusted-trace-ui-compliance.md` | 当前已有基础运行和 traceability 文档，但完整组件层、模型注册与观测平台不属于 R0 主链路。 | R1 | R1 可信工作台和工程治理窗口再展开。 |
| 前端 Web 层和 UI 组件架构 | `5.1 前端 Web 层`; `5.2 前端 UI 组件层` | 已替换 | `information-architecture.md`; `r1-penpot-lowfi-spec.md`; `apps/web/**` | 历史稿以 Next.js 管理台为假设，当前前端事实为 Vite/React 工作台页面和 R1 low-fi 页面规格。 | R1 | R0-W03 统一技术栈事实，R1 UX 窗口继续低保真/高保真衔接。 |
| 业务后端编排层 | `5.3 业务后端` | 已吸收 | `object-model-rag-multiround-backend.md`; `apps/api/app/**`; `MASTER_IMPLEMENTATION_PLAN.md` | 当前设计已定义账号、岗位、简历、知识库、模拟记录、复盘、导出、资产和 LLM 审计边界。 | R0 | none |
| 问题生成与参考材料包原则 | `6. 问题生成与参考材料原则` | 已吸收 | `scope-and-acceptance.md`; `object-model-rag-multiround-backend.md` | 当前已把岗位、简历、材料、历史回答作为上下文和引用证据，RAG 不直接决定分数。 | R0 | none |
| 考点规划、问题生成和 trace 记录 | `6. 问题生成与参考材料原则` | 已吸收 | `object-model-rag-multiround-backend.md`; `apps/api/app/traceability.py` | 当前设计保留 `ReferencePack`、引用、证据缺口和生成审计，仓库已有 traceability 切片。 | R1 | R1 traceability 窗口继续验证字段闭环。 |
| Team / User 数据模型 | `7.1 团队与用户` | 已替换 | `scope-and-acceptance.md`; `object-model-rag-multiround-backend.md` | 当前不承诺完整团队管理，保留最小账号、角色、权限和资源可见性。 | R0 | R0 身份边界只做最小实现。 |
| Job / Resume / ResumeDocument 模型 | `7.2 岗位与简历` | 已吸收 | `scope-and-acceptance.md`; `object-model-rag-multiround-backend.md`; `information-architecture.md` | 当前已把岗位、简历、文档作为发起模拟和复盘的业务输入。 | R0 | PDF/MD 转换细节另见 gap 行。 |
| 岗位-简历匹配分析 | `7.3 岗位-简历分析`; `9.2 岗位创建与简历绑定` | R1/R2 延后 | `information-architecture.md`; `object-model-rag-multiround-backend.md`; `r1-penpot-lowfi-spec.md` | 当前 IA 保留 `MatchSignal` 和岗位详情入口，但 R0 主链路只需要基础岗位/简历上下文。 | R1 | R1 可信工作台补齐匹配分析字段和页面消费。 |
| 资产库模型与归档记录 | `7.4 资产库`; `9.7 归档到资产库` | R1/R2 延后 | `object-model-rag-multiround-backend.md`; `scoring-review-export-dod.md`; `MASTER_IMPLEMENTATION_PLAN.md` | 当前设计保留 Asset、ArchiveRequest、ExportSnapshot，但完整资产库与归档增强属于 R2。 | R2 | R2 资产沉淀窗口细化 asset schema 与归档策略。 |
| 模拟面试与消息模型 | `7.5 模拟面试与消息` | 已吸收 | `object-model-rag-multiround-backend.md`; `information-architecture.md`; `apps/api/app/interview_flow/**` | 当前已定义 `InterviewSession`、`InterviewRound`、`InterviewTurn`、`Question`、`Answer` 和追问关系。 | R0 | none |
| 能力树、节点评分与进展快照 | `7.6 评估与进展`; `8.2 节点级评分` | R1/R2 延后 | `object-model-rag-multiround-backend.md`; `scoring-review-export-dod.md`; `MASTER_IMPLEMENTATION_PLAN.md` | 当前保留能力树和训练状态对象，但 R0 不要求完整能力树进展系统。 | R2 | R2 训练闭环窗口再定义能力树最小可用版本。 |
| 复盘对象模型 | `7.7 复盘`; `9.6 复盘` | 已吸收 | `scoring-review-export-dod.md`; `information-architecture.md`; `apps/api/app/review/**` | 当前已区分模拟面试复盘、真实面试复盘和题级反馈。 | R1 | none |
| 薄弱项与打磨主题模型 | `7.8 薄弱项与打磨主题`; `10. 薄弱项体系` | 已吸收 | `object-model-rag-multiround-backend.md`; `scoring-review-export-dod.md` | 当前保留 `WeaknessItem`、证据关联、状态消减和训练入口。 | R2 | none |
| 实时搜索快照 | `7.9 搜索快照`; `6. 问题生成与参考材料原则` | 明确不做 | `scope-and-acceptance.md`; `object-model-rag-multiround-backend.md` | 当前 RAG 聚焦用户私有文档和公共知识库低干扰入口，不把实时互联网搜索作为 MVP 必需能力。 | out-of-scope | 如未来需要联网搜索，应另立需求。 |
| 题目级、节点级、场次级评分 | `8.1` 到 `8.3` | 已吸收 | `scoring-review-export-dod.md`; `apps/api/app/scoring/**` | 当前设计要求 0-100 多维评分、维度分、题级反馈和证据关联。 | R1 | none |
| 岗位匹配度、薄弱点、通过概率 | `8.4 结果级判断`; `9.5 模拟模式` | 需要补入当前设计 | `scoring-review-export-dod.md` | 当前设计提到岗位匹配和通过概率，但未完整固化“通过概率必须规则计算”的来源和展示边界。 | R1 | 建议补入 `docs/design/workbench-mvp/scoring-review-export-dod.md`。 |
| 简历导入与编辑流程 | `9.1 简历导入与编辑`; `15.3 简历模块` | 需要补入当前设计 | `information-architecture.md`; `r1-penpot-lowfi-spec.md` | 当前 IA 有简历管理页，R1 low-fi 有简历列表/详情，但转换日志、版本历史和导出记录仍未在当前正式设计中完整落点。 | R1 | 建议补入简历/文档输入设计。 |
| 岗位创建与简历绑定流程 | `9.2 岗位创建与简历绑定`; `15.2 岗位模块` | 已吸收 | `scope-and-acceptance.md`; `information-architecture.md`; `r1-penpot-lowfi-spec.md` | 当前已保留岗位、简历、岗位详情、发起模拟和岗位/简历上下文关系。 | R0 | none |
| 模拟面试启动流程 | `9.3 模拟面试启动`; `15.4 模拟面试模块` | 已吸收 | `scope-and-acceptance.md`; `information-architecture.md`; `MASTER_IMPLEMENTATION_PLAN.md` | 当前 R0 明确要求从岗位、简历、上下文材料启动一次文本模拟面试。 | R0 | none |
| 真实面试复盘入口 | `9.6 复盘 / 真实面试复盘`; `15.5 复盘模块` | R1/R2 延后 | `information-architecture.md`; `scoring-review-export-dod.md`; `MASTER_IMPLEMENTATION_PLAN.md` | 当前设计保留真实面试复盘，但 R0 主链路优先模拟面试复盘，真实面试入口进入 R2 增强闭环。 | R2 | R2 复盘增强窗口细化逐字稿校对和低置信度处理。 |
| Markdown 导出与 PDF 导出 | `9.1 简历导出 PDF`; `15.4 模拟面试导出`; `15.5 复盘导出` | 已替换 | `scoring-review-export-dod.md`; `MASTER_IMPLEMENTATION_PLAN.md` | 当前一期只要求 Markdown 下载/复制，完整 PDF 和复杂模板不是必须能力。 | R0 | PDF 如恢复需进入 R1/R2 变更。 |
| 薄弱项生命周期与停练规则 | `10.3` 到 `10.6` | 已吸收 | `scoring-review-export-dod.md`; `object-model-rag-multiround-backend.md` | 当前设计保留 active、low_priority、dismissed、resolved 类状态和消减/停练语义。 | R2 | none |
| 待打磨清单 | `11.1 待打磨清单` | R1/R2 延后 | `scoring-review-export-dod.md`; `MASTER_IMPLEMENTATION_PLAN.md` | 当前已抽象为训练建议、训练任务和训练抽屉，完整待打磨清单属于训练闭环。 | R2 | R2 训练窗口再决定是否保留独立清单。 |
| 训练抽屉 | `11.2 训练抽屉`; `15.7 训练中心 / 薄弱项页` | 已吸收 | `information-architecture.md`; `scoring-review-export-dod.md`; `r1-penpot-lowfi-spec.md` | 当前 IA 与评分设计均保留训练抽屉作为弱项到训练的统一入口。 | R2 | none |
| 团队管理员和成员权限 | `12. 权限与治理` | 已替换 | `scope-and-acceptance.md`; `object-model-rag-multiround-backend.md` | 当前只要求基础身份、访问控制和资源可见性，不交付完整团队管理员治理。 | R0 | R0 只做最小身份边界，完整角色治理另窗评估。 |
| 管理台能力 | `13. 管理台能力`; `15.8 管理台` | 明确不做 | `scope-and-acceptance.md`; `design/workbench-mvp/scope.md` | 大规模运营后台和复杂管理台不属于当前 MVP 验收前提。 | out-of-scope | none |
| 模型配置与最新模型推荐 | `13.1 模型配置`; `13.2 最新模型推荐` | R1/R2 延后 | `object-model-rag-multiround-backend.md`; `MASTER_IMPLEMENTATION_PLAN.md` | 当前只保留 LLM provider、配置、版本和审计对象，模型推荐策略不进入 R0。 | R1 | 后续 LLM provider/fallback 窗口再定义。 |
| 页面信息架构 | `14. 页面信息架构`; `17. 页面流转总图` | 已吸收 | `information-architecture.md`; `r1-penpot-lowfi-spec.md` | 当前 IA 已重建一级导航、核心页面、用户路径、状态流转和模块承接关系。 | R0 | none |
| 工作台页面 | `15.1 工作台`; `19.19.1 工作台` | 已吸收 | `information-architecture.md`; `r1-penpot-lowfi-spec.md` | 当前保留工作台首页、近期模拟、待处理复盘和训练建议入口。 | R1 | none |
| 岗位页面 | `15.2 岗位模块`; `19.19.2 岗位详情` | 已吸收 | `information-architecture.md`; `r1-penpot-lowfi-spec.md` | 当前保留岗位列表、岗位详情、绑定简历和发起模拟入口。 | R0 | none |
| 简历页面 | `15.3 简历模块`; `19.19.5 简历编辑` | 需要补入当前设计 | `information-architecture.md`; `r1-penpot-lowfi-spec.md` | 当前已有简历管理页低保真，但正式设计未完整写清 MD 编辑、预览、版本、转换日志和导出记录。 | R1 | 建议在当前设计目录补一份简历/文档输入细化设计。 |
| 模拟面试页面 | `15.4 模拟面试模块`; `19.19.3 模拟面试` | 已吸收 | `information-architecture.md`; `r1-penpot-lowfi-spec.md`; `MASTER_IMPLEMENTATION_PLAN.md` | 当前已保留模拟记录列表、发起页、面试台、详情和历史回看。 | R0 | none |
| 复盘页面 | `15.5 复盘模块`; `19.19.4 复盘详情` | 已吸收 | `information-architecture.md`; `scoring-review-export-dod.md`; `r1-penpot-lowfi-spec.md` | 当前已保留复盘列表、可信复盘详情、题级反馈、证据、训练建议和导出入口。 | R1 | none |
| 资产库页面 | `15.6 资产库模块` | R1/R2 延后 | `information-architecture.md`; `object-model-rag-multiround-backend.md`; `MASTER_IMPLEMENTATION_PLAN.md` | 当前 IA 保留知识库和资产对象，完整资产库页面属于 R2 资产沉淀。 | R2 | R2 资产归档窗口补齐页面和对象细节。 |
| 训练中心 / 薄弱项页 | `15.7 训练中心 / 薄弱项页`; `19.19.6 训练中心` | R1/R2 延后 | `information-architecture.md`; `r1-penpot-lowfi-spec.md`; `MASTER_IMPLEMENTATION_PLAN.md` | 当前保留训练抽屉和 R2 roadmap 低保真，完整训练中心不进入 R0。 | R2 | R2 训练闭环窗口细化。 |
| 列表、状态、AI 结果和面试页交互规范 | `16. 全局交互规范` | 已吸收 | `r1-penpot-lowfi-spec.md`; `scoring-review-export-dod.md` | 当前 low-fi 文档已定义页面共同结构、状态表达、安全展示和实现约束。 | R1 | none |
| 视觉定位和品牌关键词 | `19.1 视觉定位`; `19.15 最终视觉风格定稿摘要` | 需要补入当前设计 | `r1-penpot-lowfi-spec.md` | 当前有 R1 低保真页面规格，但历史稿的大量高保真视觉语言、品牌关键词和设计 token 未成为当前正式设计系统。 | R1 | 建议新增或补齐高保真设计系统文档。 |
| 配色、字体、材质、布局与组件规则 | `19.2` 到 `19.4`; `19.20 核心组件定稿` | 需要补入当前设计 | `r1-penpot-lowfi-spec.md` | 当前 low-fi 只覆盖页面结构和原则，不足以替代历史稿的可执行高保真视觉规范与组件定稿。 | R1 | 建议 R1 UX 窗口生成 design system rules 与关键页面高保真规范。 |
| 页面家族、高保真结构和 UI Brief | `19.18 页面家族深化`; `19.19 关键页面高保真结构深化`; `19.21 执行级 UI Brief` | 需要补入当前设计 | `r1-penpot-lowfi-spec.md`; `MASTER_IMPLEMENTATION_PLAN.md` | 当前 Penpot low-fi 是输入，但尚未形成高保真设计系统、关键页面视觉验收和前端实现对照。 | R1 | 在 R1 UX 后续窗口补齐高保真设计系统和关键页面验收。 |
| 安全、隐私和权限展示边界 | `12. 权限与治理`; `16.3 AI 结果规范`; `19.10 状态系统与标签体系` | 已吸收 | `object-model-rag-multiround-backend.md`; `r1-penpot-lowfi-spec.md`; `scoring-review-export-dod.md` | 当前设计要求资源可见性、审计、低置信度、错误态和安全展示边界。 | R1 | none |
| 测试、验收和 DoD | `18. 设计结论`; `19.21 执行级 UI Brief` | 已吸收 | `scope-and-acceptance.md`; `scoring-review-export-dod.md`; `MASTER_IMPLEMENTATION_PLAN.md`; `TASK_INDEX.md` | 当前需求、评分/复盘设计和主计划都定义了验收、DoD、治理 gate 和阶段门禁。 | R0 | none |

## Gaps requiring current-design updates

| topic | recommended target doc | reason |
| --- | --- | --- |
| PDF / MD 简历导入、PDF 原件保留、PDF 转 MD、版本快照和 PDF 导出策略 | `docs/design/workbench-mvp/object-model-rag-multiround-backend.md` 或后续 M03 设计文档 | 当前只覆盖岗位与简历材料录入、保存和读取，缺少转换与版本策略。 |
| 通过概率必须来自规则计算 | `docs/design/workbench-mvp/scoring-review-export-dod.md` | 当前有通过概率展示口径，但未明确规则来源、低置信度影响和禁止黑盒独立数值。 |
| 简历编辑页的 MD 编辑、预览、版本历史、转换日志和导出记录 | `docs/design/workbench-mvp/information-architecture.md` 或新增当前设计细化文档 | 当前 IA 和 low-fi 有页面入口，但正式设计细节不足。 |
| 高保真视觉定位、品牌关键词和设计 token | `docs/design/workbench-mvp/r1-penpot-lowfi-spec.md` 的后续高保真设计系统文档 | 当前只有低保真结构，不足以替代历史视觉规范。 |
| 配色、字体、材质、布局与组件定稿 | 后续 R1 design system / UI specification 文档 | 当前缺少可执行高保真视觉规范和组件验收。 |
| 页面家族、高保真关键页面结构和 UI Brief | 后续 R1 UX / Penpot 高保真窗口 | 当前 Penpot low-fi 只提供结构输入，未形成前端实现可消费的高保真规范。 |

## Historical-only / replaced decisions

| topic | status | replacement / reason |
| --- | --- | --- |
| 历史 P1 设计稿作为事实源 | 已替换 | 当前事实源由 `ACTIVE_DOC_CANON.md`、requirements、design、planning 和 task index 分层承接。 |
| P1/P2/P3 阶段体系 | 已替换 | 统一为 R0/R1/R2，历史 P* 只做映射和追溯。 |
| 多模态面试作为 P2 默认路线 | 明确不做 | 当前 MVP 排除实时语音、视频和多端客户端。 |
| 完整团队/多团队管理 | 已替换 | 当前只保留最小身份、权限和资源可见性。 |
| Next.js 作为当前前端技术栈 | 已替换 | 当前仓库事实为 Vite/React。 |
| 实时互联网搜索快照 | 明确不做 | 当前 RAG 聚焦岗位、简历、材料、历史回答和知识库，不把联网搜索作为 MVP 必需项。 |
| PDF 作为一期导出必需能力 | 已替换 | 当前一期导出优先 Markdown 下载/复制。 |
| 完整管理台 | 明确不做 | 大规模运营后台和复杂管理台超出当前 MVP。 |

## Follow-up windows

| window | unique goal | write scope |
| --- | --- | --- |
| `R0-W02-CANON-AND-INDEX-REPAIR` | 修补 `ACTIVE_DOC_CANON.md`、root entry docs 和索引语言，确保有效文档白名单唯一且历史稿只作证据。 | 待窗口卡授权。 |
| `R0-W03-FACT-CONFLICT-REPAIR` | 修复当前文档中 Next.js、PostgreSQL/SQLite、apps/api、apps/web、Vite/React 等事实冲突。 | 待窗口卡授权。 |
| `R0-W04-ARCHIVE-LEDGER-UPDATE` | 将本矩阵纳入归档台账，并为后续归档候选建立原路径、替代文档和历史证据说明。 | 待窗口卡授权。 |
| `R0-W05-GATE-REVALIDATION` | 在文档收敛修补完成后重新跑只读 state validation，并评估是否可以重新进入 doc-quality gate。 | 待窗口卡授权。 |

## Validation notes

- 本矩阵未恢复历史 P1 设计稿的 active fact source 地位。
- 本矩阵不修改 `DOC_STATE.yaml`，不打开 formal window，不生成 implementation packet。
- 本矩阵不授权业务代码、测试代码、工具代码或 Basic Memory 写入。
- 本矩阵只新增归档审计文件，后续如需同步索引、台账或 canon，必须另开窗口。