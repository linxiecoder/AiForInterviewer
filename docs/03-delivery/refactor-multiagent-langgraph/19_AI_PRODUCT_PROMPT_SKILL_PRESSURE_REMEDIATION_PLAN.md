---
title: AI 产品设计、Prompt / Skill / Pressure / 架构边界深度审计与修复计划
type: delivery-planning
status: draft-pr1
owner: 项目交付
permalink: ai-for-interviewer/docs/03-delivery/refactor-multiagent-langgraph/ai-product-prompt-skill-pressure-remediation-plan
---

# AI 产品设计、Prompt / Skill / Pressure / 架构边界深度审计与修复计划

## 1. 文档目的

本文是 PR1.6 docs-only remediation 计划，用于把 AI 产品设计、Prompt Design、Skill Model、Pressure Mode 和 LangGraph 架构边界审计发现统一收口到一个受控修复入口。

本轮结论采用 Readiness QA 的更严格门禁：**PR2 代码实现不可启动，必须先执行 PR1.6 remediation**。在所有阻塞项关闭前，PR2 只允许执行 repo-state preflight、只读 recon、本文档验证，以及经主 Agent 另行授权的 active docs 回写决策；不得修改 `apps/**`、`tests/**`、依赖、migration 或 CI。

本文不替代 `docs/02-design/*`、`docs/02-design/prompt-contracts/*.md`、`docs/03-delivery/BACKLOG.md`、`docs/03-delivery/DELIVERY_PLAN.md`、`docs/00-governance/DOCS_INDEX.md` 或 ADR。长期事实必须按治理规则回写 active docs、登记 AIFI 任务或进入 ADR 后才可作为实现依据。

## 2. 审计输入

| 输入类别 | 本轮使用方式 | 边界 |
|---|---|---|
| `AGENTS.md`、`DOCS_INDEX.md`、`DOCS_GOVERNANCE.md` | 确认 active docs、archive 边界、写入边界和禁止新建并行路线图 | 作为治理事实源 |
| `BACKLOG.md`、`DELIVERY_PLAN.md` | 确认 AIFI-BE-002 / AIFI-BE-003 状态和 F5 readiness | 不在本轮修改 |
| `PRD.md`、`REQUIREMENT_TRACEABILITY.md` | 确认产品需求与历史需求入口 | 不新增产品需求 |
| `PROMPT_SPEC.md`、`prompt-contracts/*.md` | 确认 Prompt contract registry、Pressure / Report / Review / Weakness / Asset / Training Draft 状态 | 不写生产 Prompt 文案 |
| `refactor-multiagent-langgraph/README.md`、`03`、`04`、`10`、`13`、`15`、`16`、`17`、`18` | 确认 PR1 / PR1.5 目录、runtime、data、test、validation、回写和 PR sequence 设计 | 只能作为专题 planning evidence |
| 当前代码只读符号 | 核对 `PolishUseCases`、`PolishQuestionLlmService`、`PolishFeedbackLlmService`、`LlmJobMatchAnalyzer`、pressure placeholder、prompt builders、progress tree pipeline、report/review/weakness/asset/training skeleton | 不改代码 |
| A-E SubAgent 只读审计结论 | 汇总 Architecture Boundary、Pressure Mode、Prompt Design、Skill / Capability、Readiness QA 发现 | Readiness QA 的 blocker 覆盖较宽松的“有条件启动 PR2”结论 |

### 2.1 SubAgent 结论汇总

| SubAgent | 审计主题 | 结论 |
|---|---|---|
| A Architecture Boundary | AI/Core 目录和 LangGraph import 边界 | 推荐 Option C 分阶段落地；当前 AI runtime 目录规划存在 `application/ai`、`application/agents`、`application/ai_runtime` 和 `infrastructure/agent_runtime` / `infrastructure/ai_runtime` 命名分裂风险 |
| B Pressure Mode | Pressure mode readiness | Prompt contracts 已 Draft，但代码仍是 route / use case placeholder；必须先补 mode-level spec |
| C Prompt Design | Prompt asset 与评估闭环 | `PROMPT_SPEC.md` 是 contract registry，不是 production prompt asset；缺 Prompt Asset registry、golden fixtures 和 model comparison policy |
| D Skill / Capability | 统一能力模型 | 当前 `ScoreDimension`、`ProgressTree`、`Weakness`、`Asset`、`TrainingRecommendation` / `TrainingTask` 都不能承担统一 Skill Model |
| E Readiness QA | PR2 可启动性 | PR2 code implementation 判定为 FAIL；source-of-truth 回写、feature flag、repository contract、bootstrap/rollback、测试清单一致性未闭合 |

## 3. 人工问题确认

本轮按用户确认的执行边界写入以下结论：

- PR1.6 只创建本文档，不修改 `BACKLOG.md`、`DOCS_INDEX.md`、active design docs、`apps/**`、`tests/**`、依赖、migration 或 CI。
- PR1.5 不得被当作 PR2 代码实现放行证据。
- Architecture Agent 的“PR2 可有条件启动基础层”结论被 Readiness QA 的 blocker 覆盖。
- PR2 在 blocker 关闭前只能执行 preflight、PR1.6 文档修复和 active docs 回写决策。
- Pressure graph 不进入 PR2；Pressure runtime spec 完成前也不得进入业务 graph PR。
- Skill Model 只能在新增 AIFI 任务并登记 `DOCS_INDEX.md` 后成为 active design doc。

### 3.1 Findings

| ID | Severity | Area | Evidence | Impact | Required Fix | Target Document | Target PR |
|---|---|---|---|---|---|---|---|
| PR16-BLOCKER-001 | Blocker | Source-of-truth backfill | `DOCS_INDEX.md` 明确 `refactor-multiagent-langgraph/` 不替代 active design docs；`16_DESIGN_DOCS_REFACTOR_PLAN.md` 仅给出回写矩阵 | PR2 可能基于 planning evidence 写代码，绕过 active API / DATA / PROMPT / SECURITY 事实源 | 先冻结 PR1.6 回写决策，明确哪些事实进入 active docs、哪些只留在专题包 | `16_DESIGN_DOCS_REFACTOR_PLAN.md`; `BACKLOG.md`; `DOCS_INDEX.md`; `APPLICATION_FLOW_SPEC.md`; `DATA_MODEL.md`; `PERSISTENCE_MODEL.md`; `API_SPEC.md`; `SECURITY_PRIVACY.md`; `PROMPT_SPEC.md` | PR1.6 docs-only; active-docs-sync PR after authorization |
| PR16-BLOCKER-002 | Blocker | Runtime enablement feature flag | `17_PR_BREAKDOWN_AND_IMPLEMENTATION_SEQUENCE.md` 要求 G6 feature flag frozen，但当前未冻结最终 runtime enablement flag 名称、default-off 语义和 real-provider gate | PR2 runtime 表或 repository 可能先落地，但无法证明默认关闭、可回滚、不可误触发真实 provider | 冻结 runtime feature flag、per-graph enablement flag、real-provider gate 和 default-off 行为 | `04_BACKEND_AGENT_RUNTIME_PLAN.md`; `15_VALIDATION_PLAN.md`; `17_PR_BREAKDOWN_AND_IMPLEMENTATION_SEQUENCE.md`; `SECURITY_PRIVACY.md` | PR1.6 remediation; PR2 blocked |
| PR16-BLOCKER-003 | Blocker | Pressure / Report / Review runtime prompt | `PROMPT_SPEC.md` 已登记 `P-PRESSURE-*`、`P-REPORT-*`、`P-REVIEW-*` Draft；代码 `apps/api/app/application/pressure/use_cases.py` 与 `apps/api/app/api/v1/pressure.py` 仍为 placeholder | Prompt contract Draft 容易被误读为 runtime prompt asset ready，Pressure / Report / Review graph 可能无 mode-level spec 即进入实现 | 补 Pressure mode-level spec、Report / Review runtime prompt bundle 边界、graph execution mapping 和 test fixture | `APPLICATION_FLOW_SPEC.md`; `PROMPT_SPEC.md`; `prompt-contracts/PRESSURE_CONTRACTS.md`; `prompt-contracts/REPORT_CONTRACTS.md`; `prompt-contracts/REVIEW_CONTRACTS.md`; `API_SPEC.md`; `DATA_MODEL.md`; `UX_SPEC.md` | PR1.6 spec decision; PR8 or separately authorized Pressure PR |
| PR16-BLOCKER-004 | Blocker | PR2 repository / rollback / tests | `10_DATA_MODEL_AND_MIGRATION_PLAN.md` 规划 repository methods；`13_TEST_PLAN_BACKEND.md` 规划 tests；`17` 仍要求 G2-G7 同时关闭 | 如果方法级 contract、bootstrap/rollback、test method 与 active docs 未一致，PR2 会把设计缺口转移到代码评审 | 将 repository 方法、owner scope、idempotency replay、rollback、SQLAlchemy bootstrap 和 tests 逐项对齐 active docs | `10_DATA_MODEL_AND_MIGRATION_PLAN.md`; `13_TEST_PLAN_BACKEND.md`; `15_VALIDATION_PLAN.md`; `PERSISTENCE_MODEL.md`; `DATA_MODEL.md` | PR1.6 remediation; PR2 blocked |
| PR16-MAJOR-001 | Major | AI/Core directory boundary | `03_TARGET_DIRECTORY_STRUCTURE.md` 规划 `application/ai`、`application/agents`、`infrastructure/agent_runtime/langgraph/**`；用户目标要求长期收敛到 `application/ai_runtime/**` 与 `infrastructure/ai_runtime/langgraph/**` | 目录分裂会让 Core / AI Runtime / LangGraph adapter 边界难以测试，后续 import scan 规则不稳定 | 采用 Option C 分阶段落地，冻结最终命名并更新回写矩阵；PR2 不创建业务 graph 目录 | `03_TARGET_DIRECTORY_STRUCTURE.md`; `04_BACKEND_AGENT_RUNTIME_PLAN.md`; `17_PR_BREAKDOWN_AND_IMPLEMENTATION_SEQUENCE.md`; ADR-0005 | PR1.6 remediation; PR3/PR4 after authorization |
| PR16-MAJOR-002 | Major | Polish runtime prompt ahead of design | 代码已有 `PolishQuestionLlmService`、`PolishFeedbackLlmService`、`build_polish_question_generation_prompt_bundle`、`build_polish_feedback_prompt_bundle` 和 progress tree prompt builders | 现有 runtime prompt bundle 实现领先于 Prompt Asset registry / evaluation fixture 设计，容易造成生产 prompt 与 contract registry 脱节 | 明确 Prompt Contract、Runtime Prompt Bundle、Production Prompt Asset、Evaluation Fixture 的职责和 registry 字段 | `PROMPT_SPEC.md`; `prompt-contracts/POLISH_CONTRACTS.md`; new Prompt Asset registry after authorization | PR1.6 remediation; PR6 before Polish graph migration |
| PR16-MAJOR-003 | Major | Skill model missing | `rg` 未发现 `SkillTaxonomyVersion`、`SkillArea`、`SkillLevel`、`SkillAssessment` 等统一模型；现有能力语义分散在 `ScoreDimension`、`ProgressTree`、`Weakness`、`Asset`、`TrainingRecommendation` | 薄弱项、训练建议、资产、评分和进展树无法稳定映射到同一能力成长模型 | 新增 `SKILL_MODEL_SPEC.md` 的 AIFI 任务和 `DOCS_INDEX.md` 登记，再定义 Skill mapping model | `BACKLOG.md`; `DOCS_INDEX.md`; proposed `docs/02-design/SKILL_MODEL_SPEC.md`; `DATA_MODEL.md`; `PROMPT_SPEC.md`; `SCORING_SPEC.md` | PR1.6 decision; separate docs PR after authorization |
| PR16-MAJOR-004 | Major | Capability semantics fragmentation | `ScoreDimension` 表达评分维度，`ProgressTree` 表达模拟面试状态，`Weakness` / `Asset` / `Training` 表达不同生命周期对象 | 如果直接把任一对象提升为 Skill，会污染对象生命周期和用户确认边界 | 定义 Skill 与 Score / Progress / Weakness / Asset / Training 的映射关系，不改变现有对象职责 | proposed `SKILL_MODEL_SPEC.md`; `DATA_MODEL.md`; `SEMANTICS_GLOSSARY.md`; `APPLICATION_FLOW_SPEC.md` | PR1.6 decision; separate docs PR after authorization |
| PR16-MAJOR-005 | Major | Legacy direct LLM deprecation | `LlmJobMatchAnalyzer`、`PolishQuestionLlmService`、`PolishFeedbackLlmService` 仍直接经 `LlmTransport` 执行；`17` 仅定义 graph PR 顺序 | 没有 per-graph parity policy 时，迁移可能破坏 legacy compatibility 或双写业务结果 | 每个 graph 迁移前冻结 legacy fallback、parity tests、response compatibility 和 rollback policy | `07_BACKEND_GRAPH_PLANS_POLISH.md`; `08_BACKEND_GRAPH_PLANS_REPORT_REVIEW.md`; `13_TEST_PLAN_BACKEND.md`; `15_VALIDATION_PLAN.md` | PR1.6 remediation; PR5-PR8 before each graph |
| PR16-MINOR-001 | Minor | Fake LLM transport scope | `infrastructure/llm/fake_transport.py` 同时承担 Job Match、Polish progress、question、feedback 等多类业务 fake 行为 | fake transport 过大时，业务 contract drift 可能被 fake 输出掩盖 | 拆出 per-contract fixture / golden fixture policy，fake transport 只做 deterministic transport，不承载未登记业务真相 | `PROMPT_SPEC.md`; `13_TEST_PLAN_BACKEND.md`; proposed Prompt Asset registry | PR1.6 remediation; PR4-PR8 |
| PR16-MINOR-002 | Minor | Frontmatter / status wording | `refactor-multiagent-langgraph/*.md` 多数仍是 `status: draft-pr1`，但正文出现 PR1.5 DONE / implementation-ready 语义 | 读者可能把 draft-pr1、PR1.5 DONE 和 PR2 ready 混读 | 在 PR1.6 中明确 PR1.5 只是 planning evidence；如需状态修正，另行授权统一 frontmatter 语义 | `README.md`; `17_PR_BREAKDOWN_AND_IMPLEMENTATION_SEQUENCE.md`; `DOCS_INDEX.md` | PR1.6 remediation; optional docs cleanup PR |

## 4. 补充问题清单

| QID | 需裁决问题 | 决策原因 | 目标记录位置 | 未关闭时的门禁 |
|---|---|---|---|---|
| PR16-Q001 | 哪些 PR1.6 结论必须回写 active docs，哪些只保留在专题包 | 防止专题包成为并行事实源 | `16_DESIGN_DOCS_REFACTOR_PLAN.md`、`BACKLOG.md`、`DOCS_INDEX.md`、目标 active docs | PR2 code implementation FAIL |
| PR16-Q002 | AI Runtime 最终目录命名是否统一为 `application/ai_runtime/**` 和 `infrastructure/ai_runtime/langgraph/**` | 当前专题包命名与目标命名不一致 | `03_TARGET_DIRECTORY_STRUCTURE.md`、ADR-0005 | PR3 / PR4 import boundary 不可冻结 |
| PR16-Q003 | runtime enablement feature flag、per-graph flag、real-provider gate 的最终名称 | PR2 / PR3 / PR4 需要 default-off、rollback 和 no-provider 证明 | `04_BACKEND_AGENT_RUNTIME_PLAN.md`、`15_VALIDATION_PLAN.md`、`SECURITY_PRIVACY.md` | PR2 blocked |
| PR16-Q004 | Pressure mode-level spec 是否新增独立 active design doc 或回写现有 docs | Pressure runtime 不只是 Prompt contract；还需要 API、data、graph、UI、test | `APPLICATION_FLOW_SPEC.md`、`API_SPEC.md`、`DATA_MODEL.md`、`UX_SPEC.md`、`PROMPT_SPEC.md` | Pressure graph blocked |
| PR16-Q005 | Prompt Asset registry 的目标路径和 owner | `PROMPT_SPEC.md` 不是生产 Prompt 文案库 | `PROMPT_SPEC.md` 或新登记 Prompt Asset registry | PR6 / PR8 runtime prompt migration blocked |
| PR16-Q006 | Skill Model 是否作为新 active design doc 登记 | 统一能力模型缺失，不能由 `Weakness` 或 `ScoreDimension` 临时承担 | `BACKLOG.md`、`DOCS_INDEX.md`、proposed `SKILL_MODEL_SPEC.md` | Skill-based product / graph work blocked |
| PR16-Q007 | 每个 legacy direct LLM path 的 deprecation / parity policy | 防止 graph 迁移破坏现有 API 与 deterministic fallback | `13_TEST_PLAN_BACKEND.md`、对应 graph plan | PR5-PR8 graph migration blocked |
| PR16-Q008 | fake transport 与 golden fixtures 的职责分离 | fake transport 当前承载业务输出，需避免测试误放行 | `PROMPT_SPEC.md`、Prompt Asset registry、`13_TEST_PLAN_BACKEND.md` | model comparison / regression evidence incomplete |

## 5. AI/Core 目录方案

PR1.6 采用 **Option C 分阶段落地**，但需要先修正命名收敛规则。长期目标如下：

| 层级 | 长期目录 | 职责 | 允许依赖 | 禁止依赖 | 启动 PR |
|---|---|---|---|---|---|
| Core Business | `apps/api/app/domain/**`、`apps/api/app/application/{jobs,resumes,bindings,polish,pressure,reports,reviews,weaknesses,assets,training,scoring}/**` | 业务事实、owner、validation、formal object、candidate confirmation | project-owned ports / DTO、`AiOrchestrationFacade` contract | LangGraph、checkpoint schema、AgentState、provider SDK | existing + PR3 facade wiring |
| AI Runtime application | `apps/api/app/application/ai_runtime/**` | `AiOrchestrationFacade`、runner port、registry、side-effect guard、trace bridge、interrupt service、handoff contract | project-owned DTO、LLM port、Core command ports | LangGraph concrete API、SQLAlchemy concrete session、provider raw SDK | PR3 after active docs sync |
| Business graph descriptors | `apps/api/app/application/ai_runtime/graphs/{polish,pressure,report,review,job_match}/**` | graph descriptors、node contracts、project-owned state schemas | AI Runtime contracts、Prompt contract ids | LangGraph compile / invoke、checkpoint implementation、formal write bypass | PR5-PR8 only |
| LangGraph infrastructure | `apps/api/app/infrastructure/ai_runtime/langgraph/**` | LangGraph adapter、checkpointer factory、serializer、fake graph runtime adapter | `langgraph` / approved dependency pins、AI Runtime ports | Core Business use case internals、business repository direct writes | PR4-LG-DEP / PR4 |
| Runtime persistence | `apps/api/app/infrastructure/db/repositories/ai_runtime/**` or equivalent repository names frozen by PR2 | `agent_runs`、node runs、interrupts、checkpoint refs、LLM call summaries | SQLAlchemy models、sanitized DTO | LangGraph objects、checkpoint payload as business result | PR2 only after gates closed |

### 5.1 分阶段原则

1. PR2 不创建 `graphs/{polish,pressure,report,review,job_match}` 业务 graph 目录，不引入 LangGraph dependency，不接业务 runtime。
2. PR2 只有在 PR1.6 blockers 关闭后，才可实现 runtime table / repository / sanitized LLM persistence 的最小基础层。
3. PR3 创建 `application/ai_runtime/**` facade / port / contract 时，必须证明 Core 只依赖 project-owned DTO。
4. PR4-LG-DEP / PR4 只能在 `infrastructure/ai_runtime/langgraph/**` 引入 concrete LangGraph API。
5. PR5-PR8 每个业务 graph 必须先完成对应 active docs 回写和 parity policy，不能把 graph plan 当唯一实现依据。

## 6. Pressure

Pressure 当前结论：contracts 已 Draft，但代码仍是 placeholder；PR1.6 必须先补 mode-level spec，Pressure graph 推迟到 spec 完成后的 PR8 或另行授权 PR。

### 6.1 当前证据

| 证据 | 结论 |
|---|---|
| `PROMPT_SPEC.md` §9.4 登记 `P-PRESSURE-001` 至 `P-PRESSURE-009` 为 Draft | Prompt contract 已有输入 / 输出 / trace / validation 基础 |
| `apps/api/app/api/v1/pressure.py` 仅注册 router | API route 尚未形成业务 endpoint |
| `apps/api/app/application/pressure/use_cases.py` 返回 `pressure_skeleton` | application use case 仍是 placeholder |
| `08_BACKEND_GRAPH_PLANS_REPORT_REVIEW.md` 同时规划 `pressure_interview_graph`、report、review | Pressure 被放在 PR8 相关 graph planning 中，不能作为 PR2 基础层内容 |

### 6.2 Pressure mode-level spec 必须冻结的内容

| 主题 | 必须冻结内容 | Target Document | Target PR |
|---|---|---|---|
| Mode semantics | 压力面不是 Polish 变体；它有独立 session、turn、pace、end condition 和 report input package | `APPLICATION_FLOW_SPEC.md`; `UX_SPEC.md`; `DATA_MODEL.md` | PR1.6 active-docs-sync decision |
| API / data contract | `PressureSessionDetail`、turn refs、question / answer refs、pace state、pause / resume、end、report input package | `API_SPEC.md`; `DATA_MODEL.md`; `PERSISTENCE_MODEL.md` | PR1.6 active-docs-sync decision |
| Runtime prompt bundle | Opening、first question、answer quality、follow-up、pace、end check、session score、report input assembly 的 runtime bundle 边界 | `PROMPT_SPEC.md`; `prompt-contracts/PRESSURE_CONTRACTS.md`; Prompt Asset registry | PR1.6 / PR8 |
| Graph boundary | Pressure graph 不写 report body，不写 formal Weakness / Asset / Training；只产生 question、score、report input、candidate refs | `08_BACKEND_GRAPH_PLANS_REPORT_REVIEW.md`; `SECURITY_PRIVACY.md` | PR8 or authorized Pressure PR |
| UI state | 当前题、追问链、节奏提示、中断、低置信、source unavailable、结束后报告入口 | `UX_SPEC.md`; `UI_DESIGN_SYSTEM.md` | PR7 / PR8 after active sync |
| Test contract | follow-up no same question loop、pace / end condition、pause / resume、report input is not report body、no exact probability | `13_TEST_PLAN_BACKEND.md`; `14_TEST_PLAN_FRONTEND.md`; `15_VALIDATION_PLAN.md` | PR1.6 / PR8 |

## 7. Prompt Design

PR1.6 冻结以下边界，避免把 Prompt contract、生产 Prompt 和评估 fixture 混用。

| 概念 | 定义 | 可作为实现依据的条件 | 禁止事项 |
|---|---|---|---|
| Prompt Contract | `PROMPT_SPEC.md` 和 `prompt-contracts/*.md` 中的 contract id、goal、input/output schema、validation、trace/evidence、failure policy | 已登记到 canonical registry，且与 active API / DATA / SECURITY 对齐 | 不等同于完整生产 Prompt 文案 |
| Runtime Prompt Bundle | 运行时传给 `LlmTransportRequest.evidence_bundle` 的结构化输入包，包括 contract ids、input refs、evidence bundle、schema id、prompt version | 必须由 prompt builder 或 registry 生成，可被 golden fixture 验证 | 不保存 raw prompt、raw completion、provider payload 到普通日志、checkpoint 或 API response |
| Production Prompt Asset | 可版本化、可评审、可灰度、可回滚的生产 Prompt 文案或模板资产 | 必须进入 Prompt Asset registry，包含 owner、version、schema、model policy、fixture coverage、rollback policy | 不得只隐藏在 Python builder 或 fake transport 中 |
| Evaluation Fixture | golden input / expected structure / validation errors / model comparison baseline | 必须可离线跑 deterministic fake 或 schema validator；真实 provider smoke 需显式 gate | 不把 provider 200 当成 Prompt 成功 |

### 7.1 Prompt Asset registry 建议字段

| Field | Rule |
|---|---|
| `asset_id` | 稳定 id，例如 `prompt_asset_polish_question_v1` |
| `contract_ids` | 只能引用已登记 `P-*` contract |
| `runtime_task_type` | 与 `LlmTransportRequest.task_type` 对齐 |
| `schema_id` / `prompt_version` | 用于 trace、rollback、fixture 对账 |
| `input_ref_policy` | 只允许 refs / summaries / evidence chunks，不允许默认塞入完整简历、完整岗位、完整历史会话 |
| `redaction_policy` | 明确禁止 raw prompt、raw completion、provider payload、system prompt、hidden scoring rules 外泄 |
| `golden_fixture_ids` | 覆盖 success、validation_failed、low_confidence、source_unavailable、fallback |
| `model_comparison_policy` | 只比较 schema validity、semantic constraints、consistency、redaction、cost / latency summary；不以单次文本主观质量放行 |
| `rollback_policy` | 可回退到上一 prompt version 或 deterministic fallback |

### 7.2 当前 Prompt remediation 切入点

| Area | 当前证据 | Required Fix | Target PR |
|---|---|---|---|
| Polish question | `PolishQuestionLlmService` 与 `build_polish_question_generation_prompt_bundle` 已存在 | 将 runtime bundle 与 Prompt Asset registry 对齐，补 golden fixtures | PR6 before graph migration |
| Polish feedback | `PolishFeedbackLlmService` 与 `build_polish_feedback_prompt_bundle` 已存在 | 冻结 feedback asset version、consistency fixture、candidate-only redaction fixture | PR6 / PR8 |
| Progress tree | `progress_prompts.py`、`progress_v2_prompts.py`、`PolishProgressTreeV2Pipeline` 已存在 | 区分 progress tree prompt asset 与 Skill Model，不把 tree 节点当 Skill taxonomy | PR6 plus Skill docs |
| Job Match | `LlmJobMatchAnalyzer` 直接调用 `LlmTransport` | 建立 graph parity policy 和 prompt asset fixture，保留 legacy fallback | PR5 |
| Pressure / Report / Review | contracts Draft，runtime builder 未形成生产资产 | 在 mode-level spec 后再定义 runtime assets | PR8 or authorized PR |

## 8. Skill Model

当前没有统一能力模型。以下对象均不能单独承担 Skill Model：

| 现有对象 | 当前职责 | 不能承担统一 Skill Model 的原因 |
|---|---|---|
| `ScoreDimension` | 某类评分的维度和分值 | 它是评分解释维度，不表达能力层级、学习路径、证据累积和跨模式成长 |
| `ProgressTree` / progress tree plan/state | 模拟面试过程中的主题、节点和优先级 | 它是会话运行状态，不是长期能力 taxonomy |
| `Weakness` / `WeaknessCandidate` | 用户确认或候选薄弱项 | 它表达问题或风险，不覆盖正向能力、熟练度和成长轨迹 |
| `Asset` / `AssetVersion` | 可复用表达素材或知识资产 | 它是内容资产，不是能力本体 |
| `TrainingRecommendation` / `TrainingTask` | 训练建议和显式训练任务 | 它是行动计划，不是能力分类体系 |

### 8.1 建议新增模型

只有在新增 AIFI 任务并登记 `DOCS_INDEX.md` 后，才建议创建 `docs/02-design/SKILL_MODEL_SPEC.md`。建议模型如下：

| Type | 目的 | 与现有对象关系 |
|---|---|---|
| `SkillTaxonomyVersion` | 冻结能力分类版本、适用产品范围、迁移规则 | 被 Score / Progress / Weakness / Training 引用 |
| `SkillArea` | 顶层能力域，例如技术深度、项目表达、系统设计、业务理解、风险控制 | 不等同于导航或页面模块 |
| `Skill` | 可训练、可评估的能力项 | 可被 Weakness、Asset、Training、ScoreDimension 映射 |
| `SkillLevel` | 能力等级和可观测行为 | 不由 LLM 单次输出临时发明 |
| `SkillEvidence` | 证据引用，来自回答、反馈、报告、复盘、训练结果 | 只保存 refs / summaries / evidence ids |
| `SkillAssessment` | 某次 assessment 的 skill score / confidence / evidence | 可由 ScoreResult 或 Review 生成，但保留低置信边界 |
| `SkillGap` | skill 与目标岗位 / 面试要求的差距 | 可映射为 WeaknessCandidate，但不自动 formalize |
| `SkillProgress` | 跨会话能力变化 | 由 confirmed evidence 和训练结果驱动，不由 graph replay 推断 |

### 8.2 Skill Model 门禁

| Gate | 通过标准 | 未通过时禁止 |
|---|---|---|
| AIFI task | `BACKLOG.md` 有明确 AIFI 任务承接 Skill Model 设计 | 禁止创建 active `SKILL_MODEL_SPEC.md` |
| DOCS_INDEX 登记 | 新文档登记为 active design draft 或明确目录边界 | 禁止作为实现依据 |
| Mapping matrix | `ScoreDimension`、`ProgressTree`、`Weakness`、`Asset`、`Training` 的映射和非替代关系写清楚 | 禁止 PR5-PR8 以任一对象临时充当 Skill |
| Confirmation boundary | `SkillGap` 到 `Weakness` / `TrainingRecommendation` 的用户确认边界明确 | 禁止自动写 formal object |
| Fixture | 至少覆盖 one-skill multi-evidence、low confidence、conflicting evidence、training result update | 禁止发布 skill-based graph |

## 9. 旧模块迁移矩阵

| Existing Module / Symbol | 当前证据 | 迁移决策 | Target Package / Boundary | Required Contract Before Code | Target PR |
|---|---|---|---|---|---|
| `PolishUseCases` | `apps/api/app/application/polish/use_cases.py` 已承载 question、answer、feedback、progress tree 业务流程 | split：Core answer save 保留；question / feedback / progress tree 通过 facade 启动 graph | Core stays in `application/polish`; AI entry moves to `application/ai_runtime/**` after sync | answer save no LLM、feedback independent task、legacy API compatibility | PR6 |
| `PolishQuestionLlmService` | 已有 feature flag、real-provider gate、fallback、repair、validation | wrap：作为 `generate_question_candidate` 或 runtime prompt tool | AI Runtime graph node calls existing service through project port | Prompt Asset registry、golden fixtures、question quality parity | PR6 |
| `PolishFeedbackLlmService` | 已有 deterministic fallback、real-provider gate、schema / consistency validation | wrap：作为 `generate_feedback_candidate` | AI Runtime graph node calls service; candidates remain candidate-only | feedback asset version、consistency fixture、candidate formal boundary | PR6 / PR8 |
| `LlmJobMatchAnalyzer` | `infrastructure/llm/job_match.py` 直接调用 `LlmTransport` | wrap then deprecate after graph parity | `job_match_graph` behind facade; legacy analyzer as fallback | API parity、score / candidate boundary、no exact probability fixture | PR5 |
| Pressure placeholders | route 和 use case 当前只形成 placeholder | hold：不得迁移，先写 mode-level spec | `pressure_interview_graph` only after Pressure active docs sync | Pressure session lifecycle、turn / pace、API/data/UI/test contract | PR8 or authorized Pressure PR |
| Prompt builders | Polish question / feedback / progress builders 已存在 | keep + register：把 builder 输出纳入 Runtime Prompt Bundle / Prompt Asset registry | Prompt asset layer, not Core Business | registry fields、version、schema id、redaction、fixtures | PR6 / PR8 |
| Progress tree pipeline | `PolishProgressTreeLlmService`、`PolishProgressTreeQualityFirstPlanner`、`PolishProgressTreeV2Pipeline` 已存在 | split：session state pipeline 保留；Skill taxonomy 不从 progress tree 反推 | `polish_progress_tree_graph`; Skill model doc separate | progress tree prompt asset、Skill mapping matrix、node ref stability | PR6 plus Skill docs |
| Report / Review models and use cases | `InterviewReport`、`ReportSection`、`InterviewReview` models 存在；use cases 多为 skeleton | wrap when created：graph persistence must call Core command/repository | `report_generation_graph`、`mock_review_generation_graph`、`real_review_generation_graph` | report score consistency、copy boundary、review privacy、candidate-only | PR8 |
| `ScoreDimension` / scoring schema | `ScoreDimension` 和 `SCORING_SPEC.md` 已定义评分维度 | keep：评分维度不是 Skill Model；只能映射到 Skill | Scoring stays in Core; Skill mapping via spec | `SkillAssessment` / `SkillGap` mapping | Skill docs before skill-based graph |
| `Weakness` / `Asset` / `TrainingRecommendation` / `TrainingTask` | formal models and candidate repositories exist | keep formal boundary：graph 只写 candidate / suggestion；formal write needs user confirmation | Core confirmation command / candidate confirmation interrupt | confirmation schema、audit、rollback、no auto TrainingTask | PR8 |
| `fake_transport.py` | fake transport 承载多类业务 fake 输出 | narrow：transport deterministic；business expected outputs move to golden fixtures | LLM infrastructure fake + Prompt fixtures | per-contract fixtures、model comparison policy | PR4-PR8 |

## 10. PR sequence

| Step | 允许动作 | 禁止动作 | Exit Gate |
|---|---|---|---|
| PR1.6 docs-only remediation | 创建本文档；验证文档、禁词、doc governor | 修改 `apps/**`、`tests/**`、依赖、migration、`BACKLOG.md`、`DOCS_INDEX.md`；commit / push | 本文验证通过；PR2 remains blocked |
| PR1.6 active-docs-sync decision | 经主 Agent 另行授权后，决定 active docs / BACKLOG / DOCS_INDEX 回写清单 | 未授权写 active docs；把专题包当 active source | 回写范围、AIFI task、owner、验证命令明确 |
| PR2 preflight only | `git status`、branch/HEAD/divergence、model style scan、current docs read | 写 runtime code | PR1.6 blockers 全部关闭 |
| PR2 AI Runtime foundation | 仅在 gate 关闭后实现 runtime tables / repositories / sanitized LLM persistence | business graph、LangGraph dependency、frontend、real provider | owner、raw-off、retention、checkpoint ref、idempotency tests pass |
| PR3 facade / contract | 创建 `application/ai_runtime/**` facade、runner port、registry、guard、handoff、interrupt contract | concrete LangGraph import、business graph migration | Core no LangGraph import；fake vertical slice no formal write |
| PR4-LG-DEP / PR4 | dependency spike、LangGraph adapter、fake graph runtime | business graph、provider direct call、raw payload persistence | exact pins、official API check、serializer gate、fake graph redaction |
| PR5 Job Match graph | 单 graph parity migration | Polish / Pressure / Report / Review 混入 | legacy API compatible；score/candidate boundary pass |
| PR6 Polish graph | Question / feedback / progress tree graph migration | answer save LLM、candidate formal write | answer save no LLM；feedback independent task；prompt fixtures pass |
| PR7 Frontend AI Runtime UI | status、timeline、interrupt、candidate confirmation UI | backend graph logic、raw AgentState display | web tests/build pass；sanitized UI only |
| PR8 Report / Review / Pressure / Candidate closure | Report / Review / Pressure graph and candidate confirmation closure | export/download、exact probability、formal write without confirmation | copy boundary、privacy, candidate, redaction tests pass |

## 11. Implementation-ready criteria

PR2 code implementation 只有在以下 P0 gate 全部关闭后才可启动：

| Gate | 必须满足 | 验证证据 |
|---|---|---|
| P0-1 Source-of-truth backfill | PR1.6 已决定 active docs 回写范围；必要回写已完成或明确不阻断 PR2 的理由已登记 | active docs diff / accepted decision |
| P0-2 Runtime feature flags | runtime enablement flag、per-graph flag、real-provider gate、default-off、rollback behavior 冻结 | `04` / `15` / `17` / `SECURITY_PRIVACY.md` |
| P0-3 Directory boundary | `application/ai_runtime/**` 与 `infrastructure/ai_runtime/langgraph/**` 或等价命名被唯一冻结；import scan 规则同步 | directory plan + boundary test plan |
| P0-4 Repository contract | runtime repository methods、owner scope、timeline read、LLM summary read、idempotency replay、retention cleanup 冻结 | `10_DATA_MODEL_AND_MIGRATION_PLAN.md` + active docs |
| P0-5 Bootstrap / rollback | 当前无 Alembic 的 SQLAlchemy bootstrap、rollback order、in-flight run handling、pending writes fail-closed 规则明确 | `10` + validation plan |
| P0-6 Test list consistency | PR2 tests 的文件名、method、arrange / act / assert、redaction markers、owner cases 与 repository contract 对齐 | `13_TEST_PLAN_BACKEND.md` + `15_VALIDATION_PLAN.md` |
| P0-7 Prompt asset boundary | PR2 不依赖 production prompt asset；PR5-PR8 前必须有 Prompt Asset registry / fixtures 决策 | `PROMPT_SPEC.md` or authorized registry plan |
| P0-8 Pressure hold | Pressure mode-level spec 未完成前，PR2 和 PR3 / PR4 不创建 Pressure business graph | Pressure spec decision |
| P0-9 Skill model hold | Skill Model 未登记 active doc 前，任何 graph 不生成 `Skill*` formal object 或把 Weakness / ScoreDimension 当 Skill | Skill model decision |
| P0-10 Security/privacy | raw prompt、raw completion、provider payload、checkpoint payload、system prompt、hidden scoring rules 的禁止边界和 negative tests 明确 | `SECURITY_PRIVACY.md` + redaction tests |

若任一 P0 gate 未关闭，PR2 结论保持 `FAIL: code implementation blocked`。

## 12. Recommended next action

推荐下一步按以下顺序执行：

1. 先完成本文档验证，确认 PR1.6 docs-only diff 干净。
2. 由主 Agent 决定是否授权 active docs 回写；未授权时，不修改 `BACKLOG.md`、`DOCS_INDEX.md` 或 `docs/02-design/**`。
3. 若授权回写，先新增或更新 AIFI 任务，再回写 source-of-truth、runtime flag、directory boundary、Prompt Asset registry、Pressure mode-level spec 和 Skill Model 决策。
4. PR2 仍只执行 preflight；只有 §11 全部 P0 gate 关闭后，才允许进入 runtime foundation 代码实现。

PR1.6 文档验证命令：

```bash
git status --short --untracked-files=all
git diff --stat
git diff --check
.venv/bin/python -m tools.doc_governor.cli doc-quality-gate --repo-root .
rg -n "<forbidden-vague-wording-regex>" docs/03-delivery/refactor-multiagent-langgraph/19_AI_PRODUCT_PROMPT_SKILL_PRESSURE_REMEDIATION_PLAN.md
rg -n "<forbidden-temporary-source-and-checkpoint-truth-regex>" docs/03-delivery/refactor-multiagent-langgraph/19_AI_PRODUCT_PROMPT_SKILL_PRESSURE_REMEDIATION_PLAN.md
rg -n "raw prompt|raw completion|provider payload|Target Document|Target PR" docs/03-delivery/refactor-multiagent-langgraph/19_AI_PRODUCT_PROMPT_SKILL_PRESSURE_REMEDIATION_PLAN.md
```
