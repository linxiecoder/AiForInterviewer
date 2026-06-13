---
title: TECH_DESIGN
type: design
status: draft-f4-entry
owner: 技术架构
source_task: AIFI-ARCH-001
permalink: ai-for-interviewer/docs/02-design/tech-design
---

# TECH_DESIGN

## 1. 文档状态

- 本文件是 F4 技术设计主架构锚点，用于承接 `AIFI-ARCH-001` 的后续分段设计。
- 本文件不是完整 M4 交付，不替代 `DATA_MODEL.md`、`API_SPEC.md`、`PROMPT_SPEC.md` 或 `SECURITY_PRIVACY.md`。
- 本文件冻结 MVP 主架构、模块边界、分层原则、运行链路和子文档输入边界，并在本轮记录 `AR-F4-FULL-001` 的 F4 UNKNOWN 收敛结论。
- 本文件不标记 F4 / M4 / `AIFI-ARCH-001` 完成；最终退出仍以 `F4_FULL_DESIGN_ACCEPTANCE.md` 的 Pending / verification 状态为准。

## 2. F4 目标

- 基于 PRD、UX_SPEC、UI_DESIGN_SYSTEM 和交付计划，拆分 MVP 技术设计产物。
- 先在 `TECH_DESIGN.md` 中建立跨子文档一致的主架构锚点，避免数据、API、Prompt 和安全隐私分段各自发明架构。
- 在后续分段中明确数据模型、API、Prompt、LLM 边界、安全隐私、评分与状态策略。
- 为 F5 实现、F7 验收和发布前风险复核提供可追踪技术依据。

## 3. 输入来源

- `docs/01-product/PRD.md`：MVP 业务对象、核心数据流、非目标、评分/复制/通过倾向口径和 UNKNOWN 台账。
- `docs/02-design/UX_SPEC.md`：F2 低保真信息架构、核心页面场景、状态与异常路径。
- `docs/02-design/UI_DESIGN_SYSTEM.md`：F3 设计系统草案、交互状态约束和前端实现交接边界。
- `docs/03-implementation/DELIVERY_PLAN.md`：F4 / M4 目标、产物和阶段边界。
- `docs/03-implementation/BACKLOG.md`：AIFI-ARCH、AIFI-DATA、AIFI-API、AIFI-PROMPT、AIFI-SEC 后续任务入口。
- 仓库技术配置：根目录 `package.json`、`requirements.txt`、`apps/web/package.json`、`apps/web/vite.config.ts`、`apps/web/tsconfig.json` 和 API 启动入口；这些配置只证明前后端技术入口仍保留，具体页面、接口、持久化和测试实现以 F5/F6 后续落地为准。

## 4. 非目标

- 不在本文件中展开数据表、字段、API endpoint、Prompt 模板、安全策略或测试用例。
- `DATA_MODEL.md`、`API_SPEC.md`、`PROMPT_SPEC.md` 与 `SECURITY_PRIVACY.md` 均已作为 F4 active draft 文档存在；本文件不替代这些子文档，也不表示实现状态完成。
- 不创建或关闭 ADR。
- 不更新 DELIVERY_PLAN 或任何无关任务状态；BACKLOG 与 DOCS_INDEX 仅允许围绕已初始化的 F4 子文档做最小状态同步。
- 不在本文中重开 PRD §10 已由 F4 子文档承接的待决策项。
- MVP 不支持 PDF、Markdown、Word 或批量文件导出；报告复制是页面交互，不是文件导出。
- MVP 不支持解析外部材料并自动生成岗位 / JD。
- MVP 简历输入只接收 Markdown 文本提交 / 编辑；不设计 PDF parser、OCR、文件上传存储、MIME 校验或对象存储作为 MVP 必需链路。
- MVP 不承诺精确通过概率或准确预测面试结果。

## 5. 架构目标与设计原则

- 以 MVP 可交付为优先，采用当前仓库已保留的 Web + API 技术入口和分层目标，不引入无证据的新框架、服务拆分或部署形态。
- 前端负责交互、状态呈现和用户动作收集；后端负责业务编排、持久化边界、LLM 调用和安全控制。
- 所有 LLM Prompt、模型调用参数、密钥和原始模型响应必须留在后端边界内，前端只接收可展示结果、状态和可追踪错误。
- 业务状态必须可追踪、可恢复、可解释；分数、通过倾向和低信心输出不得伪装成确定预测。
- 数据对象、API 契约、Prompt 规范和安全隐私约束必须从同一组模块边界出发。
- 项目经历属于 Markdown 简历正文片段或派生 outline 节点，不升级为独立顶层业务对象、顶层数据对象或 API module CRUD 资源。
- 资产库不是简历的别名，承担跨会话沉淀、复用和反馈回流职责。
- 报告复制是页面交互能力，不是文件导出能力。

## 6. MVP 系统上下文与架构总览

- 用户通过浏览器访问 Web 前端，完成简历、岗位 / JD、模拟面试、报告、复盘和训练建议相关交互。
- 前端通过 HTTP API 与 API 后端交互；API 负责接收请求、校验边界输入、执行业务编排并返回状态或结果。
- 后端内部按应用编排、领域能力、LLM 边界、持久化边界和安全审计边界分层。
- LLM Provider 是外部依赖；后端通过隔离层调用，不允许 UI 直接访问模型或密钥。
- 持久化方案、数据库 schema、数据保留和部署拓扑待 `DATA_MODEL.md` 与 `SECURITY_PRIVACY.md` 明确。
- 队列、对象存储、独立 LLM 服务、服务网格和多租户部署当前没有仓库配置证据，不作为 MVP 默认架构。

## 7. 当前仓库技术栈事实

- 根目录 `package.json` 声明 Node `>=20`，workspace 为 `apps/web`。
- 根目录脚本提供 `web:dev`、`web:build`、`web:test`、`dev:api` 和 `api:dev`。
- `apps/web/package.json` 声明前端使用 React、React DOM、Ant Design、Vite、TypeScript 和 `@vitejs/plugin-react`。
- `apps/web/vite.config.ts` 使用 Vite React plugin。
- `apps/web/tsconfig.json` 启用 TypeScript strict、`react-jsx` 和 Bundler module resolution。
- `apps/web/package.json` 保留 `test` 脚本作为当前前端入口类型检查；旧单元测试和 E2E 用例不作为本文件的当前实现基线。
- legacy E2E 用例删除后，`apps/web/playwright.config.ts` 不作为当前 active 测试入口；后续 F7 如需 E2E，应按当前 MVP 实现重新建立测试配置。
- 根目录 `requirements.txt` 声明 FastAPI、httpx、SQLAlchemy、psycopg、uvicorn、pytest 和 PyYAML。
- 根目录 API 脚本使用 `python3 -m uvicorn app.main:app --app-dir apps/api` 启动 FastAPI 应用。
- 当前未读取到根目录 `pyproject.toml`、根目录 `vite.config.ts` 或根目录 `tsconfig.json` 作为架构依据；未保留在当前工作区中的页面、API route、schema 和测试文件不得作为当前实现依据。

## 8. 技术栈选型与方案对比

- 方案 A：沿用当前仓库技术栈，采用 Vite + React + TypeScript + Ant Design 前端，以及 FastAPI + SQLAlchemy + psycopg 后端。
  - 推荐作为 MVP 默认方案。
  - 优点是已有配置、脚本和依赖证据，能减少 F4 到 F5 的迁移成本。
  - 风险是部分持久化、部署、鉴权和异步任务策略仍需后续子文档补齐。
- 方案 B：切换到 Next.js、SSR 或其他前端框架。
  - 不推荐作为当前 MVP 默认方案。
  - 当前仓库没有相关配置证据，且会引入路由、构建、部署和数据获取策略重写。
- 方案 C：拆出独立 LLM 服务、队列 worker 或多服务架构。
  - 不推荐作为当前 MVP 默认方案。
  - 除非后续 API、性能或安全设计证明同步 API 编排无法满足 MVP，否则应先保持单 API 后端内的 LLM 隔离层。
- 若后续决定替换主技术栈、引入独立服务或变更 LLM Provider 抽象边界，应先评估是否需要 ADR。

## 9. 系统分层

- Web UI 层：页面、表单、报告展示、复制交互、会话状态展示和错误提示。
- Web 状态适配层：把 API 状态转换为页面 view model，不承载业务真相和 LLM 判断。
- API 边界层：请求校验、鉴权入口、错误语义、任务状态查询和响应 schema。
- 应用编排层：串联简历、岗位、会话、报告、复盘、资产沉淀、训练建议和反馈回流。
- 领域能力层：封装匹配分析、问题生成、回答打磨、压力追问、评分、弱项归因和建议生成。
- LLM / Prompt 边界层：构造模型输入、调用模型、校验结构化输出、记录 trace、处理低信心和失败结果。
- 持久化边界层：封装数据读写、状态版本、会话快照、报告结果、资产版本和审计所需记录。
- 安全与观测边界层：约束密钥、隐私字段、日志脱敏、错误追踪和发布前风险复核。

## 10. 功能模块划分

- 简历模块：保存 Markdown 简历主体；项目经历、能力标签等只作为正文片段或派生 outline 被定位和引用，不提供独立模块 CRUD。
- 岗位 / JD 模块：保存岗位目标、JD 文本、岗位约束和岗位绑定关系。
- 岗位匹配分析模块：基于简历与岗位生成匹配结果、差距解释和后续训练输入。
- 打磨模式会话模块：围绕用户回答进行追问、优化建议和可复用表达沉淀。
- 压力面模式会话模块：围绕高压追问、追问链路和压力反馈生成训练结果。
- 进展树模块：展示能力、任务、会话和训练建议之间的进展关系。
- 面试报告模块：汇总模拟面试过程、评分、解释、建议和页面复制内容。
- 面试复盘模块：承接模拟面试复盘和真实面试复盘，形成反馈与改进项。
- 薄弱项模块：沉淀、合并、更新和关闭弱项，但具体生命周期由 `DATA_MODEL.md` 明确。
- 资产库模块：沉淀可复用回答、项目表达、岗位材料和反馈结果，不等同于简历模块。
- 训练建议模块：基于匹配分析、会话、报告、复盘和薄弱项生成下一步训练建议。
- 反馈回流模块：把用户确认、复制、复盘和真实面试反馈回写到资产与训练上下文。

## 11. 模块依赖与数据流关系

- 前端只依赖 API 契约，不直接读取数据库、不直接调用 LLM、不保存业务真相。
- API 边界层调用应用编排层；应用编排层协调领域能力、LLM 边界和持久化边界。
- 简历 Markdown 版本和岗位 / JD 版本是匹配分析、会话生成、报告生成和训练建议的主要输入；F6 不得绕过 API 从展示概念反推模块级 CRUD。
- 打磨模式和压力面模式会话产生回答、追问、评分、弱项和资产候选。
- 面试报告和面试复盘消费会话过程、评分结果、弱项和用户反馈。
- 资产库消费简历、会话、报告和复盘输出，并向后续匹配分析、会话和训练建议提供上下文。
- 训练建议消费匹配分析、弱项、进展树、资产库和复盘结果，不直接改写源会话记录。
- 反馈回流通过应用编排层进入资产库、弱项和训练建议，不绕过状态与版本边界。

## 12. 核心运行链路总览

- 简历与岗位链路：用户提交 Markdown 简历文本和岗位 / JD，后端保存或更新输入，形成后续分析和训练上下文。
- 匹配分析链路：后端读取简历与岗位上下文，调用领域能力和必要的 LLM 边界，返回匹配解释、差距和建议入口。
- 打磨模式链路：用户提交回答或素材，后端生成追问、打磨建议、表达优化和资产候选。
- 压力面模式链路：用户进入压力训练，后端生成追问链、压力反馈、弱项和训练建议。
- 模拟面试复盘链路：会话结束后，后端汇总过程、评分、解释、报告内容和下一步训练建议。
- 真实面试复盘链路：用户录入真实面试反馈，后端形成复盘、弱项更新、资产沉淀和训练建议。
- 报告复制链路：前端根据 API 返回的报告内容执行页面复制；后端不生成 PDF、Markdown、Word 或批量文件。
- 反馈回流链路：用户确认、修正或复盘反馈经 API 写入，影响资产、弱项和后续训练上下文。

## 13. 状态机与状态流总览

- 输入类状态：简历、岗位 / JD 和真实面试反馈应区分草稿、可用、需补充和废弃，具体枚举由 `DATA_MODEL.md` 明确。
- 任务类状态：匹配分析、报告生成、复盘生成和训练建议生成应区分待处理、处理中、成功、失败和低信心完成。
- 会话类状态：打磨模式、压力面模式和模拟面试应区分未开始、进行中、暂停、完成和异常结束。
- 报告类状态：面试报告应区分生成中、可查看、可复制、生成失败和内容需风险提示。
- 弱项类状态：薄弱项应支持新增、合并建议、验证中、改善中和关闭候选；正式状态变化必须经过用户确认或显式业务动作，最小状态域由 `DATA_MODEL.md` §7 / §9 承接。
- 资产类状态：资产应支持候选、已确认、已归档、被替代和禁用；版本创建、替代和合并必须保留 `AssetCandidate` / `AssetVersionSuggestion` / `UserConfirmationRef` 边界，复杂算法按 §16 的 deferred_non_blocking 处理。
- LLM 输出状态：结构化输出应区分通过校验、校验失败、低信心、部分可用和不可用。
- 状态流必须能支撑 API 查询、前端展示、重试提示、审计追踪和 F7 验收。

## 14. AI / LLM 总览

- LLM 能力属于后端受控依赖，不是前端能力，也不是独立产品事实源。
- Prompt 组装、上下文裁剪、模型选择、调用参数、输出校验、重试策略和降级策略由 `PROMPT_SPEC.md` 细化。
- LLM 输入应由应用编排层按最小必要原则组装，避免把无关简历、岗位、反馈或隐私字段送入模型。
- LLM 输出必须经过结构化校验和业务语义校验后才能进入报告、复盘、弱项或资产候选。
- 低信心、冲突、不完整和模型失败结果必须以状态和风险提示进入 API 语义，不得伪装为正常高置信结果。
- 评分、通过倾向和训练建议应表达为辅助判断，不承诺精确通过概率或真实面试结果预测。
- 测试中的 LLM 行为应通过可替换 transport 或确定性替身验证，避免依赖真实模型稳定性。

### 14.1 AI 编排总览

本节冻结 F4 的 AI 编排设计锚点，供后续 `PROMPT_SPEC.md`、`API_SPEC.md`、`DATA_MODEL.md`、`SECURITY_PRIVACY.md` 和 F5 后端实现承接。

- LLM 是后端受控依赖，不是完整业务能力；Prompt 是模型调用 contract 的一部分，不是打磨模式、压力面模式、报告、复盘、薄弱项或训练建议的完整实现边界。
- 打磨模式、压力面模式、报告、复盘、薄弱项和训练建议必须由应用编排层串联领域能力、retrieval / RAG、context assembly、session memory、LLM 调用、输出校验、持久化、trace / evidence 引用和失败恢复。
- 每个 AI 子任务都应有明确输入来源、上下文预算、检索依赖、输出 schema、校验规则、失败状态和可追踪引用；不得把一个大 Prompt 或单次 LLM 调用作为单一业务流程。

打磨模式编排至少包含以下链路：输入选择、上下文装配、题目生成或题目选择、用户回答、回答诊断、0-100 评分、失分点归因、参考回答生成、考点解析、技术原理扩展、下一轮改进建议、弱项候选、资产候选、用户确认回流和会话状态更新。该链路可以拆分为多个 AI 子任务和领域规则步骤，不应退化成单次 LLM 调用直接返回全量结果。

压力面模式编排至少包含以下链路：开场策略、首题生成、用户回答、回答质量判断、追问策略选择、追问生成、连续问答状态推进、节奏控制、结束条件判断、整场评分、面试报告生成、复盘入口、薄弱项和训练建议提炼。压力面侧重连续追问、真实节奏和整场评估，不应按同题无限打磨处理。

Retrieval / RAG / 资产检索应区分不同来源和用途：

- 知识库检索：用于岗位、题目、考点、评分解释、报告和训练建议的外部或内部知识证据。
- 资产库检索：用于复用用户已确认的项目表达、回答素材、岗位材料和反馈沉淀。
- 薄弱项检索：用于选择当前训练重点、避免重复训练和追踪改善状态。
- 历史报告 / 复盘检索：用于引用生成时的会话、评分、报告、复盘和用户确认记录。
- 必要时的互联网检索：仅作为后续产品、安全和来源治理明确后的显式补充来源，不作为 MVP 默认强依赖。

检索结果进入模型上下文前，必须完成 owner / scope 校验、来源版本确认、证据摘要、去重、排序、裁剪，以及 `EvidenceRef` / `TraceRef` 等引用绑定。本文不选择具体向量数据库、embedding 模型、搜索服务或索引实现。

Context Assembly 不得把一场模拟面试内容整体塞进一个 Prompt；后端应按任务和轮次组装最小必要上下文。上下文层次至少包含固定系统规则、模式规则、当前岗位版本摘要、当前简历版本摘要、当前轮题目和回答、最近若干轮问答、session summary、资产库命中、薄弱项命中、RAG evidence、禁止重复追问列表、输出 schema / validation 要求。一次组装过程应能通过 `RAGContextAssembly`、`LlmRequestTrace` 或同等 trace 边界回溯输入来源、裁剪原因和低置信度状态。

LLM 输出进入业务对象前必须经过结构化校验、业务语义校验、低置信度标记、evidence / trace 绑定、失败状态表达，以及可重试或人工校对路径。模型失败、检索为空、上下文超长、输出不完整、证据冲突或来源不可用时，不得伪装为正常高置信结果；API 和持久化对象应表达失败、部分可用、低置信度或需人工校对状态。

AI Task Contract 输出进入业务系统时，应先形成 `AiTaskResultRef`，再按结果语义进入 `CandidateRef` 或 `SuggestionRef`，需要用户动作时再绑定 `UserConfirmationRef`，最后才允许在确认、编辑、合并或显式业务动作后进入 formal object。candidate / suggestion 不等于正式对象；`confirm`、`edit`、`skip`、`merge`、`reject`、`manual_review` 是应用编排语义，不是单次 LLM 调用。`API_SPEC.md` 与 `DATA_MODEL.md` 已承接该前置边界；`APPLICATION_FLOW_SPEC.md` 是 API 到 application service / P-* contract / LLM call plan / persistence handoff 的 canonical 编排交接；`API_SPEC.md` 已将 endpoint、异步任务、重试、幂等、rate limit 和 F7 contract assertion 作为 F5/F6/F7 handoff。

后续子文档交接边界如下：

- `PROMPT_SPEC.md` 应定义 AI 子任务 contract、输入输出 schema、上下文预算、检索依赖、校验和失败处理，不应只是提示词文案集合。
- `API_SPEC.md` 应表达多步任务、状态查询、重试、暂停恢复、报告生成和回流确认的接口语义。
- `DATA_MODEL.md` 应承接 RAG、trace、evidence、session summary、context assembly 的逻辑对象和引用关系。
- `SECURITY_PRIVACY.md` 应承接 owner 校验、隐私裁剪、日志脱敏、trace 保存和 LLM 输入最小化约束。
- `SCORING_SPEC.md` 应作为评分公式、score type、rubric dimensions、默认权重、低置信度降级、`ScoreResult` 和 F7 scoring fixture 的 canonical 文档。
- `SEMANTICS_GLOSSARY.md` 应作为 Low Confidence、`confidence_level`、`validation_status`、`source_availability` 和 candidate / suggestion / formal object 语义的 canonical 文档。
- `PERSISTENCE_MODEL.md` 应作为 F5 persistence handoff，避免后端从 `DATA_MODEL.md` 的逻辑对象自行推导物理关系、join table 或引用表。

### 14.2 评分、通过倾向、风险提示与校准口径

本节冻结 `AR-F4-FULL-003` 的最小实现口径，处理评分、通过倾向、风险提示和校准边界；评分机制的 canonical 细则以 `SCORING_SPEC.md` 为准，低置信度和状态语义以 `SEMANTICS_GLOSSARY.md` 为准。这些结论同时作为本轮 `AR-F4-FULL-001` 中评分类 F4 阻断项的已关闭证据，不进入 F5 implementation。

- 0-100 分数是产品评分刻度，用于表达当前输入、rubric 和 evidence 下的相对表现，不是精确通过概率、录取概率、offer 概率或通过率百分比。
- MVP 正式评分只保留 `score_value` / `display_score` 这一类用户可见展示分；不把 `raw_score`、`normalized_score` 和 `display_score` 三套分数同时作为正式报告字段。若模型或内部步骤生成候选原始分，只能停留在 validation / trace，不得作为正式报告评分展示。
- 正式 `ScoreResult` 必须绑定 `score_version`、`ScoreRuleVersion` / `rubric_version`、`score_scale=0_100_product_scale`、`score_type`、`generated_at`、`generated_by_task_id`、`TraceRef`、`EvidenceRef`、`ScoreEvidenceLink`、`confidence_level` 和 `validation_status`。
- 评分来源是 rubric / rule version，不是不可追踪的单次 LLM 主观判断。LLM 可以生成 scoring candidate / draft，但正式报告评分必须经过结构化 schema 校验、业务语义校验、证据绑定、低置信度分类和版本记录。
- MVP rubric 维度按 score type 固定到 rule version 元数据：岗位匹配默认覆盖 `requirement_alignment`、`experience_evidence`、`skill_coverage`、`gap_risk`、`readiness_actions`；面试会话 / 报告默认覆盖 `answer_relevance`、`technical_depth`、`communication_structure`、`evidence_specificity`、`risk_control`。
- 权重策略由 `ScoreRuleVersion` 记录为整数权重，单个 rule version 内权重总和为 100；权重可因 `score_type` 不同而不同，但不得由 LLM 在单次输出中临时发明。MVP 初始规则版本可使用上述维度的固定权重，后续变更必须发布新 rule version。
- 版本变更后，历史报告继续引用生成时的 `score_version`、`rubric_version` 和 `ScoreRuleVersion`；不同版本分数不可直接强比较，除非后续引入明确校准映射。重新评分必须产生新的 `ScoreResult` 或新版本结果，不改写历史分数。
- MVP 不要求真实招聘结果校准。最小校准策略是：固定 rule version、维护人工验收样例集、使用回归测试 fixture 覆盖边界分数 / 低置信度 / source unavailable / validation failed / 风险提示，并在版本变更时执行样例回归。真实结果校准为 `LATER` / `SHOULD`，不得阻断 MVP；校准样例不得包含未脱敏第三方隐私。
- 用户可见通过倾向只允许分档表达：`偏低`、`中等`、`偏高`、`需谨慎`。禁止展示精确通过概率、录取概率、offer 概率、通过率百分比或“你有 73% 概率通过”等等价措辞。
- 低置信度、证据不足、source unavailable、validation failed、评分规则版本缺失或 evidence binding failed 时，不得给出确定性通过倾向；用户可见文案必须降级为“证据不足，无法判断倾向”或等价安全措辞。
- 通过倾向和风险提示只作为训练辅助说明，不作为自动决策依据，不触发自动拒绝、自动通过、自动训练任务或正式弱项写入。
- 风险等级固定为 `low`、`medium`、`high`、`unknown`；每条风险必须包含 `risk_reason`、`risk_level`、`confidence_level`、`evidence_refs`、`score_version`、`rubric_version`、`rule_version_ref`、`validation_status` 和 `low_confidence_flags`。风险提示必须和改进建议区分：风险提示解释当前风险来源，改进建议只给后续行动入口。
- 风险提示禁止恐吓式、确定性、歧视性或不可解释表达；不得把岗位匹配缺口直接包装成稳定能力缺陷，也不得引用未脱敏第三方公司、面试官或无权限来源作为用户可见风险依据。
- 用户可见评分、通过倾向和风险提示必须包含可信度说明和非决策性免责声明，说明结果基于当前材料、规则版本和证据生成，仅用于面试准备辅助，不代表真实招聘决定。
- F7 至少形成断言：0-100 score 可正常生成；不出现精确通过概率；low confidence 时不输出确定倾向；source unavailable 时报告降级；validation failed 时不落正式报告评分；不暴露隐藏评分规则；`risk_level` 与 `evidence_refs` 同步存在；`score_version` / `rubric_version` 存在；copy content 不包含内部评分规则。

### 14.3 Interview Coach G-003 / G-004 / Composition Layer 架构边界

本节迁入原 standalone G-003 / G-004 / Composition 规格中已确认的架构含义；原规格文件不再作为 standalone system spec。这里仅记录 G-003、G-004 与 Composition Layer 的职责边界，不新增能力定义。

| 层 | 架构职责 | 已确认实现路径 | 禁止外推 |
|---|---|---|---|
| G-003 Evaluation Layer | 产出 evaluation / feedback / UI-safe status labeling；反馈前可消费 bounded `structured_answer` | `apps/api/app/application/polish/transcript_signal_parser.py`、`feedback_generation_service.py`、`feedback_prompt_assets.py` | 不输出 transcript structure、behavioral signal extraction、candidate reasoning trace、understanding model、taxonomy 或 coaching plan |
| G-004 Understanding Layer | 产出 `transcript_analysis_v1`、transcript structure 和 behavioral signals | `apps/api/app/application/transcript_analysis/models.py`、`parser.py`、`analyzer.py`、`service.py` | 不生成 feedback、score、rubric verdict、evaluation、coaching plan 或正式能力判断 |
| Composition Layer | 按 mode 调用 G-003 / G-004，并做 response envelope 层级 routing / packaging | `apps/api/app/application/composition/service.py` | 不做跨层解释、重写、评分、语义升级、降级或状态覆盖 |

G-003、G-004 与 Composition Layer 不是顺序 pipeline。G-003 不依赖 G-004 的内部语义，G-004 不依赖 G-003 的输出，Composition Layer 也不得把其中任一层转换成另一层的输入语义。组合只表示 routing 与 packaging，不表示跨层推理或语义转换。

运行模式边界：

- `interview` mode：G-004 always runs；G-003 conditionally runs；响应只在 envelope 层并列呈现可用输出。
- `training` mode：G-004 runs；G-003 runs；返回 balanced output，但不得把训练建议写成正式 TrainingTask。
- `analysis` mode：G-004 only；不得隐式触发 G-003，也不得从 G-004 输出推导 feedback。

## 15. 子文档输入边界

- `DATA_MODEL.md` 以本文件的模块划分、状态域和数据流为输入，定义业务对象、数据对象、状态枚举、版本策略和持久化边界。
- `API_SPEC.md` 以本文件的系统分层、核心链路和状态流为输入，定义 API 契约、错误语义、任务追踪和前后端协作边界。
- `PROMPT_SPEC.md` 以本文件的 LLM 边界、AI 子任务 contract、上下文装配、检索依赖和低信心要求为输入，定义输入输出 schema、上下文预算、模型调用、输出校验和失败处理约束，不作为提示词文案集合。
- `SECURITY_PRIVACY.md` 以本文件的数据流、LLM 输入、资产沉淀和日志边界为输入，定义隐私字段、保留策略、密钥、权限和发布风险。
- `SCORING_SPEC.md` 以本文件的评分 / 风险口径为输入，冻结 score type、默认维度、权重、公式、落库、API / Prompt 映射和 F7 scoring fixture。
- `SEMANTICS_GLOSSARY.md` 以本文件的状态流和低信心要求为输入，统一 low confidence、validation、source availability 和失败状态语义。
- `PERSISTENCE_MODEL.md` 以 `DATA_MODEL.md` 的逻辑对象为输入，给出 F5 建议物理模型、关系、join / reference table 和 API schema 映射。
- `APPLICATION_FLOW_SPEC.md` 以 `API_SPEC.md` endpoint、`PROMPT_SPEC.md` P-* contract 和 `DATA_MODEL.md` / `PERSISTENCE_MODEL.md` 对象为输入，定义 use-case orchestration、LLM 调用时机、调用次数和持久化交接。
- `RELEASE_HANDOFF_SPEC.md` 以 TECH / API / DATA / PERSISTENCE / SECURITY / PROMPT / SCORING / SEMANTICS / FLOW 和 delivery docs 为输入，定义 F8 release / ops / retrospective handoff；它不是正式发布清单、运行手册、监控平台实现或部署脚本。
- 子文档可以细化本文件锚点，但不得绕过本文档重新定义顶层模块、前后端职责或 LLM 所属边界。

### 15.1 F4 到 F6 交接（handoff）规则

本节补充 `AR-F4-F8-002` 的 F4→F6 handoff 规则；页面级接入矩阵的 canonical 位置为 `API_SPEC.md` §6.1-§6.6。

- F6 前端只依赖 `API_SPEC.md` 中的 endpoint、response schema、状态映射、error envelope、candidate / confirmation flow、copy boundary 和 F7 assertions，不得从 `UX_SPEC.md`、`UI_DESIGN_SYSTEM.md` 或实现代码反向发明 API 字段、状态或错误码。
- `UX_SPEC.md` / `UI_DESIGN_SYSTEM.md` 只约束页面、组件、布局、用户任务和交互状态；当 F2/F3 页面需要的数据不在 `API_SPEC.md` 中时，必须登记为 待补缺口（remaining gap），不得在 F6 mock adapter 中伪造业务事实。
- `API_SPEC.md` §6.1 覆盖 F6 page / surface 的 API、schema、loading / empty / error / permission / candidate / copy / F7 assertion 接入规则；§6.2 覆盖必须显式处理的状态；§6.3-§6.4 覆盖前端字段族和确认流。
- 本轮按人工审计决策执行：Resume API Markdown-only。F6 简历页面只使用 `ResumeDetail.markdown_text` / `current_version_ref` / `status`，不得调用或假设 project-experience module CRUD；项目经历定位只能来自 Markdown 内容或 derived outline。
- F6 岗位 list/detail 必须直接消费 `JobBindingSummary` 与 `JobMatchSummary`，不得通过额外详情二次查询拼接基础摘要；`latest_match_summary` 不返回精确通过概率。
- F6 打磨模式必须先读取 `GET /api/v1/polish-topics`，并在创建会话时传递 `resume_job_binding_id`、`topic_id`、`subtopic_id` 或经过安全输入处理的 `custom_topic_text`。
- F6 岗位详情和岗位绑定页面的解绑动作必须接入 `DELETE /api/v1/resume-job-bindings/{binding_id}`；请求带 `base_version_ref`、可选 `reason` 和 `Idempotency-Key`，响应展示 `binding_status`、历史结果保留引用和默认入口影响摘要；解绑不得删除历史报告、复盘或匹配分析。
- F6 复盘列表必须接入 `GET /api/v1/reviews`，直接消费 `ReviewSummary[]` 的类型、来源摘要、状态、置信度、`source_availability`、关联报告 / 会话引用和下一步动作；不得靠多次详情查询拼接列表核心摘要。
- F6 复盘复制必须通过 review copy content / copy event 边界，用户可见内容不得包含 system prompt、provider payload、隐藏评分规则或未脱敏第三方 / 公司 / 面试官 / 他人隐私；复制审计只记录 actor、target、范围摘要和结果，不记录正文。
- F6 低置信校对保存必须通过 candidate correction 边界，用户修正先形成 `CandidateCorrection` / `UserCorrectionRef` 并经过 validation；不得直接覆盖原候选、正式对象或 Prompt source。
- F6 内容沉淀目标必须通过 `DepositTarget` / confirmation 边界，目标可为 `asset`、`weakness`、`training_suggestion`、`polish_input`、`pressure_input`、`next_interview_input`、`review_note`、`none` 或 `skip`；Prompt 只能建议目标，正式写入必须来自用户确认或显式业务动作。
- F6 不得提供文件导出、PDF / Markdown / Word / docx 下载、文件上传解析、外部材料解析岗位、精确通过概率、system prompt、provider payload 或隐藏评分规则展示。
- 如果 F6 发现需要新增 dashboard aggregate、report history list、candidate inbox 或 persisted account preferences API，必须回到 `API_SPEC.md` / `BACKLOG.md` 的后续 refinement；不得把这些能力作为本轮 AR-F4-F8-002 的隐含实现。

### 15.2 F4 到 F8 发布交接（release handoff）规则

本节补充 `AR-F4-F8-003` 的 F4->F8 handoff 规则；F8 release / ops / retrospective handoff 的 canonical 位置为 `RELEASE_HANDOFF_SPEC.md`。

- F4 只提供 F8 发布产物输入，不生成最终 `RELEASE_CHECKLIST.md`、`CHANGELOG.md`、runbook、rollback strategy、known limitations 或 release retrospective。
- F8 release checklist 输入必须覆盖 route inventory、no export、no PDF / docx / Word / Markdown file download、no file upload parsing、no external material parsing for jobs、no exact probability、copy boundary、owner boundary、candidate / suggestion 不自动转 formal object、low confidence、source unavailable、validation failed、score version / rubric version / evidence refs。
- F8 known limitations 必须从 `RELEASE_HANDOFF_SPEC.md` §4 生成，并区分 product non-goal、implementation limitation、operational limitation、accepted risk 和 next-iteration item；不得把限制写成已实现能力。
- F8 runbook 输入必须覆盖 provider unavailable、provider timeout、provider rate limit、AI task timeout、generation failed、validation failed、low confidence spike、source unavailable、RAG retrieval empty、owner mismatch spike、idempotency conflict、stale version conflict、copy boundary violation、export not supported attempt、audit / trace write failure、database migration failure 和 backup restore required。
- F8 rollback / migration 输入必须以 `PERSISTENCE_MODEL.md` 的 owner、version、trace、audit、ScoreRuleVersion、AiTask 和 historical reference 语义为准；rollback 不得静默改写历史报告、复盘、评分或资产版本引用。
- Observability handoff 只冻结 signals 和检查项，不选择监控平台、日志平台、SIEM、云服务或部署拓扑；完整平台化能力由 `BACKLOG.md` 的 F8 / LATER 任务承接。
- Deferred->Backlog 映射必须以 `RELEASE_HANDOFF_SPEC.md` §10 和 `BACKLOG.md` 为准；复杂算法、provider tuning、vector database、enterprise SSO / ACL、internet search、advanced backup restore automation 和 release automation 不阻断 MVP，但不得悬空。
- F5 / F6 / F7 可以根据该 handoff 预留日志、trace、audit、rate limit、retry、source availability、copy boundary 和 migration / rollback 测试输入；这不代表 F8 运维能力在 F4 已实现。
- `F4_TO_F8_READINESS_ACCEPTANCE.md` 即使记录 `AR-F4-F8-003` Verified，也不得自动写 Accepted；整体 readiness 仍需人工 approval。

## 16. F4 UNKNOWN 收敛与后置边界

本节用于关闭 `AR-F4-FULL-001` 指向的 F4 阻断口径：active design docs 不再把评分、接口、数据结构、Prompt、模型结果状态、安全边界、候选 / 正式对象、资产回流、真实面试复盘、进展树、暂停恢复、题目推荐、复盘切分或薄弱项生命周期表达为未处置的 M4 阻断项。下表是 F4 退出前的处置状态，verification 仍由 `F4_FULL_DESIGN_ACCEPTANCE.md` 记录。

| 主题 | 分类 | F4 设计结论 | 证据路径 / 承接 |
|---|---|---|---|
| 评分公式、权重、阈值、评分解释、校准方法 | already_closed_by_recent_remediation | 0-100 是产品刻度；正式 `ScoreResult` 绑定 `score_version`、`rubric_version`、`ScoreRuleVersion`、证据、置信度、validation 和 trace；MVP 使用固定 rule version、人工样例和 F7 fixture 校准。真实招聘结果校准、复杂调参和隐藏规则实现细节为 `SHOULD` / `LATER`，不阻断 M4。 | 本文件 §14.2；`SCORING_SPEC.md`；`DATA_MODEL.md` §10；`PROMPT_SPEC.md` §7.2；`API_SPEC.md` §4.4 / §8；`SECURITY_PRIVACY.md` §17.1 |
| 通过倾向、风险提示、可信度说明和免责声明 | already_closed_by_recent_remediation | 通过倾向只允许分档；低置信度、证据不足、`source_unavailable` 或 `validation_failed` 时降级为证据不足；风险提示必须绑定 evidence、版本、confidence、validation 和免责声明；不得展示精确通过概率。 | 本文件 §14.2；`REPORT_CONTRACTS.md` §3.3；`API_SPEC.md` §4.4；`SECURITY_PRIVACY.md` §17 |
| API endpoint、error semantics、retry、idempotency、rate limit、async task | already_closed_by_recent_remediation | `/api/v1`、response / error envelope、核心 endpoint matrix、async task protocol、retry、cancel、timeout、idempotency、rate limit、owner enforcement 和 F7 assertions 已冻结为 F5/F6/F7 handoff；F5 不得重新发明 endpoint。 | `API_SPEC.md` §3-§10；本文件 §15 |
| 数据结构、状态枚举、版本策略、trace / evidence 字段 | must_close_in_F4 | 逻辑对象、统一引用模型、candidate / suggestion / confirmation、状态域、版本 / 快照引用、trace / evidence / audit 字段已冻结；F5 物理 handoff、join / reference table 和 API schema 映射由 `PERSISTENCE_MODEL.md` 承接；物理 DDL、索引和 ORM 为实现细节。 | `DATA_MODEL.md` §4-§12；`PERSISTENCE_MODEL.md` |
| Prompt contract、模型调用结果状态、低置信度、source unavailable、validation failed | must_close_in_F4 | 48 个 `P-*` contract 均为 Draft；`status`、failure signals、low confidence、validation、evidence、trace、candidate / suggestion / persistence handoff 已冻结；完整 Prompt 文案、provider、模型参数和向量库选型为 provider-independent 实现细节，不阻断 M4。 | `PROMPT_SPEC.md` §4-§13；`prompt-contracts/*.md` |
| 安全边界、LLM 输入最小化、provider payload、system prompt、隐藏评分规则 | must_close_in_F4 | 前端不得访问模型、密钥、Prompt、provider payload 或隐藏评分规则；后端按最小必要上下文组装；日志、trace、copy content 和 API response 均不得泄露敏感正文或 provider payload。 | `SECURITY_PRIVACY.md` §9 / §11 / §17 / §21；`API_SPEC.md` §8 |
| 资产合并、候选态到正式态、用户确认边界 | must_close_in_F4 | AI 输出只能先进入 candidate / suggestion；正式 `Asset`、`AssetVersion`、`Weakness`、`TrainingRecommendation` 和 `TrainingTask` 必须经过用户确认、编辑、合并或显式业务动作。资产质量、合并排序和复杂去重算法为 deferred_non_blocking。 | `DATA_MODEL.md` §4.3 / §5.9 / §9；`API_SPEC.md` §7；`ASSET_CONTRACTS.md` |
| 真实面试复盘、第三方隐私、公司信息脱敏 | must_close_in_F4 | 真实面试复盘只来源于用户手动录入；必须记录可信度、完整度和来源；第三方 / 公司 / 个人敏感信息只可使用脱敏摘要，不得进入日志、copy content 或高置信风险依据。 | `DATA_MODEL.md` §5.8；`SECURITY_PRIVACY.md` §15 / §17.1；`REVIEW_CONTRACTS.md` |
| 进展树、暂停恢复、题目推荐、复盘切分、薄弱项生命周期 | deferred_non_blocking | M4 冻结最小对象、状态、API task / retry / cancel / timeout、candidate / suggestion / confirmation 和 F7 断言边界；完整状态机 fixture、排序算法、结束阈值、跨复盘聚合和自动消减规则继续由 `AR-F4-FULL-005` 或后续 `SHOULD` / `LATER` 承接，不作为 `AR-F4-FULL-001` 的 M4 阻断。 | `DATA_MODEL.md` §7 / §8 / §9 / §12；`API_SPEC.md` §5 / §9 / §11；`PROMPT_SPEC.md` §13 |
| 文件导出、PDF / Markdown / Word / docx 下载、文件上传解析、外部材料解析岗位 | deferred_non_blocking | 明确为 MVP non-goal 或 Deferred；MVP 只支持 Markdown 文本输入和页面复制，不支持文件导出、文件解析或外部材料自动生成岗位。 | 本文件 §4；`API_SPEC.md` §8；`SECURITY_PRIVACY.md` §8 / §14 / §23；`RELEASE_HANDOFF_SPEC.md` §4 |
| 多租户、企业治理、商业化、复杂部署拓扑、对象存储、独立 worker | deferred_non_blocking | 当前证据不足且非 MVP 必需；默认不进入 MVP 主架构。若后续引入，需另行 ADR / 安全文档 / 实现设计。 | 本文件 §4 / §8；`SECURITY_PRIVACY.md` §23；`RELEASE_HANDOFF_SPEC.md` §10 |

## 17. 后续分段执行顺序

1. 对 `AR-F4-FULL-001` 做 verification，确认 active docs 的阻断项均已关闭、已后置为 non-blocking 或被识别为 false positive。
2. 基于 `API_SPEC.md` 当前 API handoff，F5 只实现已冻结 contract，不得重新回退为 endpoint 占位或自行发明错误语义。
3. 基于 `APPLICATION_FLOW_SPEC.md` 当前 use-case orchestration，F5 只实现已冻结的读取 / 写入 / AiTask / P-* contract / LLM call plan / persistence handoff，不得把 API 字段表当成完整业务流程。
4. 基于 `PERSISTENCE_MODEL.md` 当前 persistence handoff，F5 只实现已冻结的 owner、version、status、join / reference table 和历史引用语义，不得从逻辑对象自行推导冲突物理关系。
5. 维护 `PROMPT_SPEC.md` 与 `prompt-contracts/*.md` 的 canonical registry / child-doc 一致性；新增 `P-*` 必须先登记主 catalog。
6. 在 F5 / F7 中按 `SECURITY_PRIVACY.md` 验证 owner / scope、trace、evidence、audit、source unavailable、复制和 LLM payload 风险。
7. `AR-F4-FULL-005`、F3 / F6 交接和 prompt-contract 过期 Stub 文案属于后续单 finding 或 Medium / Low 范围，本轮不更改其 review 状态。

## 18. 本轮状态

- `DATA_MODEL.md`、`SECURITY_PRIVACY.md`、`PROMPT_SPEC.md`、`API_SPEC.md` 均已作为 F4 active draft 文档存在。
- `SCORING_SPEC.md`、`SEMANTICS_GLOSSARY.md`、`PERSISTENCE_MODEL.md`、`APPLICATION_FLOW_SPEC.md` 已作为 F4 active handoff draft 登记，分别承接评分、语义、持久化和应用编排整改。
- `RELEASE_HANDOFF_SPEC.md` 已作为 F4->F8 release / ops / retrospective handoff draft 登记，承接 release checklist、known limitations、runbook、rollback / migration、observability、Deferred->Backlog 和 F8 输出映射；不创建 F8 最终发布产物。
- `PROMPT_SPEC.md` 已拆分 `prompt-contracts/*.md` 子文档，并完成全量 Prompt Contract Draft 覆盖。
- `API_SPEC.md` 已作为 F4 API contract handoff 存在，当前覆盖 base path、response / error envelope、endpoint matrix、async task、retry、idempotency、rate limit、copy boundary 和 F7 test assertions。
- `DATA_MODEL.md` 已同步候选态、建议态、用户确认流、AI output handoff、Asset / Training 逻辑对象。
- 本轮按 `AR-DOCS02-SEM-001` 补齐 UX 可见任务到 API / DATA / TECH / PROMPT / SECURITY 的五条链路：岗位解绑、复盘列表、复盘复制、低置信校对保存和内容沉淀目标；等待独立 verification，不处理 `AR-DOCS02-SEM-002/003`。
- `AR-F4-FULL-003` 的评分、通过倾向、风险提示和校准口径已回写并完成 verification；不代表 F4 全量验收 Accepted。
- 本轮 `AR-F4-FULL-001` 将 F4 active design docs 中的阻断式 UNKNOWN 口径改为已冻结、已处置或 deferred_non_blocking；等待独立 verification。
- 本轮不进入 implementation，不修改业务代码，不把 `F4_FULL_DESIGN_ACCEPTANCE.md` 标记为 Accepted。
- 未修改代码、archive 或实现方案。
