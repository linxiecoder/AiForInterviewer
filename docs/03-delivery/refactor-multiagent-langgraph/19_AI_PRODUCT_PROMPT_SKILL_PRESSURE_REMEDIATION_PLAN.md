---
title: AI 产品设计、Prompt / Skill / Pressure / 架构边界深度审计与修复计划
type: delivery-planning
status: draft-pr1
owner: 项目交付
permalink: ai-for-interviewer/docs/03-delivery/refactor-multiagent-langgraph/ai-product-prompt-skill-pressure-remediation-plan
---

# AI 产品设计、Prompt / Skill / Pressure / 架构边界深度审计与修复计划

## 1. 文档目的

本文执行 PR1.6 docs-only remediation，用于识别并规划修复 PR1 / PR1.5 后仍未满足 implementation-ready 的 AI 产品设计、Prompt、Skill、Pressure 和 AI/Core 目录边界问题。

本轮结论是：**PR2 code implementation 不可启动**。AIFI-ARCH-007 已由 `docs/02-design/SKILL_MODEL_SPEC.md` 接受并关闭 Skill Model blocker；PR2 在 `AIFI-BE-004`、`AIFI-PROMPT-002`、`AIFI-BE-005` 及 `BACKLOG.md` 仍登记的其他 blocker 关闭，或主 Agent 显式接受风险并重新授权前，只能执行 repo-state preflight、只读 recon 和受权文档回写；不得修改 `apps/**`、`tests/**`、依赖、migration、CI、后端代码、前端代码或业务代码。

本文不替代 `docs/02-design/*`、`docs/02-design/prompt-contracts/*.md`、`docs/03-delivery/BACKLOG.md`、`docs/03-delivery/DELIVERY_PLAN.md`、`docs/00-governance/DOCS_INDEX.md` 或 ADR。长期事实必须回写 active docs、进入 `BACKLOG.md` AIFI 任务或进入 ADR 后，才可作为实现依据。

`docs/tmp` 只作本轮输入证据，不作为事实源。
它不是 canonical registry 或 canonical source。

checkpoint 只用于 resume / replay / debug / runtime recovery，不是业务事实源。
它不是 business truth source。

raw prompt、raw completion、provider payload 不得进入普通日志、checkpoint、API response 或普通 trace 可见正文。

## 2. 审计输入

| 输入类别 | 已读文件 / 符号 | 本轮用途 | 边界 |
|---|---|---|---|
| 治理入口 | `AGENTS.md`; `docs/00-governance/DOCS_INDEX.md`; `docs/tmp/GOAL_PR1_6_AI_PRODUCT_PROMPT_SKILL_PRESSURE.md` | 确认 PR1.6 scope、禁止修改范围、required reading、required validation | `docs/tmp` 不是事实源 |
| 专题文档 | `docs/03-delivery/refactor-multiagent-langgraph/README.md`; `17_PR_BREAKDOWN_AND_IMPLEMENTATION_SEQUENCE.md`; `18_LANGGRAPH_DEPENDENCY_AND_SPIKE_PLAN.md`; `03_TARGET_DIRECTORY_STRUCTURE.md`; `04_BACKEND_AGENT_RUNTIME_PLAN.md`; `10_DATA_MODEL_AND_MIGRATION_PLAN.md`; `13_TEST_PLAN_BACKEND.md`; `15_VALIDATION_PLAN.md`; `16_DESIGN_DOCS_REFACTOR_PLAN.md` | 确认 PR1.6 blocker freeze、PR2 blocked、Option C、runtime / repository / validation / backfill planning | 仅作为 F5 专题 planning package |
| ADR | `docs/04-decisions/ADR-0005-langgraph-agentic-workflow-runtime.md` | 确认 Option C、Core 不依赖 LangGraph、checkpoint 非业务事实源、raw-off、candidate/formal 边界、AIFI-ARCH-008 directory closure | ADR 状态为 Proposed，不代表 active docs 全部回写 |
| active design docs | `APPLICATION_FLOW_SPEC.md`; `PERSISTENCE_MODEL.md`; `DATA_MODEL.md`; `PROMPT_SPEC.md`; `SCORING_SPEC.md`; `SECURITY_PRIVACY.md`; `API_SPEC.md`; `UX_SPEC.md`; `UI_DESIGN_SYSTEM.md`; `SKILL_MODEL_SPEC.md` | 核对 API / data / prompt / score / skill / security / UX / UI 对 Pressure、Prompt、Skill、candidate/formal 和 raw-off 的当前事实 | AIFI-ARCH-007 只新增 Skill Model active doc，并对 DATA / PROMPT / SCORING 做最小交叉引用 |
| prompt contracts | `docs/02-design/prompt-contracts/*.md` | 核对 `P-PRESSURE-*`、`P-POLISH-*`、`P-REPORT-*`、`P-REVIEW-*`、`P-WEAKNESS-*`、`P-ASSET-*`、`P-TRAINING-*` 为 Draft contract，不是生产 Prompt Asset | 不新增 contract ID |
| Pressure code | `PressureUseCases.bootstrap`; `apps/api/app/api/v1/pressure.py`; `apps/api/app/schemas/pressure.py`; `CreatePressureQuestionTaskCommand`; `GetPressureSessionQuery` | 证明 Pressure 代码仍是 placeholder / skeleton | 只读，不修改代码 |
| Polish / LLM code | `PolishUseCases`; `PolishQuestionLlmService`; `PolishFeedbackLlmService`; `build_polish_question_generation_prompt_bundle`; `build_polish_feedback_prompt_bundle`; `PolishProgressTreeV2Pipeline`; `LlmJobMatchAnalyzer` | 证明 runtime compact prompt builders 已存在，但缺 Production Prompt Asset / Evaluation 设计 | 只读，不调用 provider |
| Skill 相关模型 | `ScoreDimension`; `Weakness`; `WeaknessCandidate`; `Asset`; `AssetVersion`; `TrainingRecommendation`; `TrainingTask`; `InterviewReport`; `InterviewReview`; `PolishProgressTree*` | 证明能力语义分散，尚无统一 Skill / Capability Model | 只读，不新增模型 |
| SubAgent 尝试 | `multi_agent_v1.spawn_agent` 已返回多个 agent id；`wait_agent` 对首批 id 返回 `not_found`，快速复核 agent 超时未返回 | Goal mode 工具支持 spawn，但本轮未获得可引用的 SubAgent 最终报告 | 最终结论以主 Agent 本地证据为准 |

## 3. 人工审计问题确认

| 问题 | 结论 | 证据 |
|---|---|---|
| AI/Core 目录不一致与 AI 嵌套过深 | 已由 AIFI-ARCH-008 关闭。最终目录形态冻结为 `application/ai_runtime/**` + `infrastructure/ai_runtime/langgraph/**`；`application/ai/**`、`application/agents/**`、`infrastructure/agent_runtime/**` 和 `langgraph_adapters/**` 不再作为 PR2-PR8 创建目标 | `03_TARGET_DIRECTORY_STRUCTURE.md` §5；`04_BACKEND_AGENT_RUNTIME_PLAN.md` §4-§5；ADR-0005 §Decision / §Consequences |
| Pressure mode 缺 mode-level spec 与代码未实现 | 确认。active docs 和 prompt contracts 有 Pressure Draft 语义，但代码只有 router prefix、DTO placeholder、`PressureUseCases.bootstrap()` 返回 `pressure_skeleton` | `PROMPT_SPEC.md` §9.4；`PRESSURE_CONTRACTS.md` §13；`apps/api/app/application/pressure/use_cases.py` `PressureUseCases.bootstrap`; `apps/api/app/api/v1/pressure.py`; `apps/api/app/schemas/pressure.py` |
| Polish prompt design 不足 | 确认。Polish question / feedback / progress tree 已有 runtime builders 和 LLM service，但 `PROMPT_SPEC.md` 只冻结 contract registry，不承载 Production Prompt Asset registry、golden fixtures 或 model comparison policy | `question_prompts.py` `build_polish_question_generation_prompt_bundle`; `feedback_prompts.py` `build_polish_feedback_prompt_bundle`; `question_llm.py` `PolishQuestionLlmService`; `feedback_llm.py` `PolishFeedbackLlmService`; `PROMPT_SPEC.md` §9 |
| Skill model 缺失 | 已由 AIFI-ARCH-007 关闭。`SKILL_MODEL_SPEC.md` 已登记 active design doc，冻结统一 Skill taxonomy，并明确 `ScoreDimension`、`ProgressTree`、`Weakness`、`Asset`、`TrainingRecommendation` 等对象不能替代 Skill Model | `SKILL_MODEL_SPEC.md`; `DATA_MODEL.md` §11.2; `SCORING_SPEC.md` §8-§9; `PROMPT_SPEC.md` §12-§13; `progress_tree_v2.py`; `models/scoring.py`; `models/weakness.py`; `models/asset.py`; `models/training.py` |
| 其他 implementation readiness 问题 | 确认。AIFI-ARCH-007 只关闭 Skill Model blocker；PR2 仍受 source-of-truth backfill、runtime flag、repository contract、bootstrap / rollback、test list、raw-off security、Prompt Asset、Pressure hold 和 PR2 preflight readiness 阻断 | `README.md` §3.3 / §8.1；`17_PR_BREAKDOWN_AND_IMPLEMENTATION_SEQUENCE.md` §6；`BACKLOG.md` AIFI-BE-004 / AIFI-PROMPT-002 / AIFI-BE-005 |

## 4. 补充问题清单

### 4.1 Blocker

| ID | Severity | Area | Evidence | Impact | Required Fix | Target Document | Target PR |
|---|---|---|---|---|---|---|---|
| PR16-BLOCKER-001 | Blocker | PR2 启动门槛 | `README.md` §3.3 / §8.1；`17_PR_BREAKDOWN_AND_IMPLEMENTATION_SEQUENCE.md` §6；`BACKLOG.md` AIFI-BE-004 / AIFI-PROMPT-002 / AIFI-BE-005；`SKILL_MODEL_SPEC.md` 已关闭 AIFI-ARCH-007 | PR2 如果启动代码实现，会绕过仍未关闭的 PR1.6 blocker | 维持 PR2 blocked；先关闭剩余 blocker 任务或登记人工 accepted risk | `BACKLOG.md`; `README.md`; `17_PR_BREAKDOWN_AND_IMPLEMENTATION_SEQUENCE.md`; 本文 §10-§12 | PR1.6; PR2 blocked |
| PR16-BLOCKER-002 | Blocker | Source-of-truth backfill | `DOCS_INDEX.md` §1 / §2 说明专题包不替代 active docs；`16_DESIGN_DOCS_REFACTOR_PLAN.md` §4 映射 active docs 回写 | 代码实现可能直接引用 planning package，而非 active API / DATA / PROMPT / SECURITY 事实源 | 冻结 active docs 回写清单；回写完成或显式登记不阻断理由后再授权实现 | `APPLICATION_FLOW_SPEC.md`; `PERSISTENCE_MODEL.md`; `DATA_MODEL.md`; `API_SPEC.md`; `PROMPT_SPEC.md`; `SECURITY_PRIVACY.md`; `BACKLOG.md` | PR1.6 decision; authorized active-docs-sync PR |
| PR16-BLOCKER-003 | Blocker | Runtime enablement / feature flag | `17_PR_BREAKDOWN_AND_IMPLEMENTATION_SEQUENCE.md` §6 G6；`04_BACKEND_AGENT_RUNTIME_PLAN.md` §6.7 / §10 | 未冻结 default-off、per-graph flag、real-provider gate、rollback，PR2 无法证明 runtime 不会误触发 provider 或业务 graph | 冻结 runtime enablement flag、per-graph flag、real-provider gate、default-off、disable / rollback 行为 | `04_BACKEND_AGENT_RUNTIME_PLAN.md`; `15_VALIDATION_PLAN.md`; `SECURITY_PRIVACY.md`; `17_PR_BREAKDOWN_AND_IMPLEMENTATION_SEQUENCE.md` | PR1.6 remediation; PR2 blocked |
| PR16-BLOCKER-004 | Blocker | Pressure mode-level spec | `apps/api/app/application/pressure/use_cases.py` `PressureUseCases.bootstrap`; `apps/api/app/api/v1/pressure.py`; `PRESSURE_CONTRACTS.md` §13 | Pressure contracts 已 Draft，但 runtime、API、data、UI、graph、tests 没有 mode-level spec，Pressure graph 不能进入实现 | 新增或回写 Pressure mode-level spec，覆盖 session / turn / pace / end / report handoff / review handoff / candidates / API / data / prompt / graph / UI / tests | `APPLICATION_FLOW_SPEC.md`; `DATA_MODEL.md`; `API_SPEC.md`; `UX_SPEC.md`; `UI_DESIGN_SYSTEM.md`; `PROMPT_SPEC.md`; `PRESSURE_CONTRACTS.md` | AIFI-BE-004; PR2 blocked; Pressure graph held |
| PR16-BLOCKER-005 | Blocker | Repository / bootstrap / rollback / tests | `10_DATA_MODEL_AND_MIGRATION_PLAN.md` repository planning；`13_TEST_PLAN_BACKEND.md` test planning；`15_VALIDATION_PLAN.md` validation planning；当前仓库无 Alembic | PR2 若直接写 runtime tables / repositories，会把方法级 contract、SQLAlchemy bootstrap、rollback 和 test method 缺口转移到代码评审 | 逐项冻结 repository methods、owner scope、idempotency replay、timeline read、LLM summary read、retention cleanup、SQLAlchemy bootstrap / rollback、test names | `10_DATA_MODEL_AND_MIGRATION_PLAN.md`; `13_TEST_PLAN_BACKEND.md`; `15_VALIDATION_PLAN.md`; `PERSISTENCE_MODEL.md`; `DATA_MODEL.md` | AIFI-BE-005; PR2 blocked |
| PR16-BLOCKER-006 | Blocker | Security / privacy raw-off | `ADR-0005` §3 / §8；`SECURITY_PRIVACY.md` LLM / trace / log 边界；`API_SPEC.md` AiTask status 不返回 provider payload | raw prompt、raw completion、provider payload、checkpoint payload 一旦进入日志 / checkpoint / API，会破坏隐私与可回滚边界 | 补 negative tests 和可见性矩阵，证明 raw payload 不进入 checkpoint、timeline、API response、copy content、普通 trace | `SECURITY_PRIVACY.md`; `API_SPEC.md`; `15_VALIDATION_PLAN.md`; `13_TEST_PLAN_BACKEND.md` | AIFI-BE-005; PR2 blocked |

### 4.2 Major

| ID | Severity | Area | Evidence | Impact | Required Fix | Target Document | Target PR |
|---|---|---|---|---|---|---|---|
| PR16-MAJOR-001 | Major | AI/Core directory boundary | `03_TARGET_DIRECTORY_STRUCTURE.md` §5、`04_BACKEND_AGENT_RUNTIME_PLAN.md` §4-§5 和 ADR-0005 已冻结最终目录形态 | AIFI-ARCH-008 关闭后，PR3 / PR4 import scan 规则可稳定落到唯一路径 | **Closed by AIFI-ARCH-008**：采用 Option 2，收敛为 `application/ai_runtime/**` + `infrastructure/ai_runtime/langgraph/**`；禁止 `application/ai/**`、`application/agents/**`、`infrastructure/agent_runtime/**` 和 `langgraph_adapters/**` | `03_TARGET_DIRECTORY_STRUCTURE.md`; `04_BACKEND_AGENT_RUNTIME_PLAN.md`; `17_PR_BREAKDOWN_AND_IMPLEMENTATION_SEQUENCE.md`; ADR-0005 | AIFI-ARCH-008 |
| PR16-MAJOR-002 | Major | Prompt Asset / Evaluation | `PROMPT_SPEC.md` §9 为 contract registry；`question_prompts.py` / `feedback_prompts.py` 已有 runtime bundle builders | 生产 Prompt 资产、版本、golden fixtures、model comparison 和 rollback 无统一设计 | 定义 Prompt Asset registry、Evaluation Fixture、model comparison policy、redaction / rollback policy | `PROMPT_SPEC.md`; `prompt-contracts/*.md`; proposed Prompt Asset registry; `13_TEST_PLAN_BACKEND.md` | AIFI-PROMPT-002 |
| PR16-MAJOR-003 | Major | Skill / Capability Model | 已新增 `docs/02-design/SKILL_MODEL_SPEC.md` 并登记 `DOCS_INDEX.md`；`DATA_MODEL.md`、`SCORING_SPEC.md`、`PROMPT_SPEC.md` 已补最小交叉引用 | 多模式能力语义已具备 active doc；后续实现若绕过该 doc 仍会产生不可追踪映射 | **Closed by AIFI-ARCH-007**：后续 graph 只能引用已冻结 Skill taxonomy 与现有对象映射 | `docs/02-design/SKILL_MODEL_SPEC.md`; `DATA_MODEL.md`; `SCORING_SPEC.md`; `PROMPT_SPEC.md` | AIFI-ARCH-007 |
| PR16-MAJOR-004 | Major | Legacy direct LLM migration | `LlmJobMatchAnalyzer.analyze`; `PolishQuestionLlmService.generate_with_llm_or_fallback`; `PolishFeedbackLlmService.generate_with_llm_or_fallback` 仍直接经 `LlmTransport` | graph 迁移若缺 parity policy，可能破坏现有 API、fallback、validation 和 candidate-only 行为 | 每个 graph 迁移前冻结 legacy fallback、parity tests、response compatibility、deprecation / rollback policy | `06_BACKEND_GRAPH_PLANS_RESUME_JOBMATCH.md`; `07_BACKEND_GRAPH_PLANS_POLISH.md`; `13_TEST_PLAN_BACKEND.md`; `15_VALIDATION_PLAN.md` | PR5 / PR6 / PR8 |
| PR16-MAJOR-005 | Major | Pressure / Report / Review handoff | `APPLICATION_FLOW_SPEC.md` flows 8-10；`PROMPT_SPEC.md` §9.4-§9.6；`PRESSURE_CONTRACTS.md` §13 | Pressure score、report input、review candidates 容易混成一次 graph output，绕过 report/review/candidate 边界 | 拆清 Pressure graph、Report graph、Review graph、Weakness / Asset / Training candidate handoff | `APPLICATION_FLOW_SPEC.md`; `PROMPT_SPEC.md`; `REPORT_CONTRACTS.md`; `REVIEW_CONTRACTS.md`; `PRESSURE_CONTRACTS.md`; `DATA_MODEL.md` | AIFI-BE-004; PR8 |

### 4.3 Minor

| ID | Severity | Area | Evidence | Impact | Required Fix | Target Document | Target PR |
|---|---|---|---|---|---|---|---|
| PR16-MINOR-001 | Minor | Fake transport / fixtures | `apps/api/app/infrastructure/llm/job_match.py` 与 Polish builders 已形成多类 deterministic 逻辑；Prompt Asset / golden fixtures 未统一 | fake 输出可能承载业务真相，掩盖 Prompt contract drift | fake transport 只做 deterministic transport；业务期望迁移到 per-contract golden fixtures | `PROMPT_SPEC.md`; proposed Prompt Asset registry; `13_TEST_PLAN_BACKEND.md` | AIFI-PROMPT-002; PR4-PR8 |
| PR16-MINOR-002 | Minor | Frontmatter / status wording | 多个专题文档仍为 `status: draft-pr1`，正文同时出现 PR1.5 / PR1.6 / PR2 blocked | 读者可能混淆 PR1.5 implementation-ready 与 PR1.6 blocked 的关系 | 在专题索引中保持 PR1.6 blocked 声明；状态命名清理必须另行授权 | `README.md`; `DOCS_INDEX.md`; `17_PR_BREAKDOWN_AND_IMPLEMENTATION_SEQUENCE.md` | Optional docs cleanup PR |

### 4.4 Follow-up

| ID | Severity | Area | Evidence | Impact | Required Fix | Target Document | Target PR |
|---|---|---|---|---|---|---|---|
| PR16-FOLLOW-001 | Follow-up | Prompt quality metrics | `PROMPT_SPEC.md` 当前冻结 contract schema / validation，但没有跨模型质量指标表 | PR5-PR8 无统一 Prompt acceptance 口径 | 定义 schema validity、semantic constraints、evidence precision、redaction, cost / latency summary、fallback rate | proposed Prompt Asset registry; `PROMPT_SPEC.md`; `15_VALIDATION_PLAN.md` | AIFI-PROMPT-002 |
| PR16-FOLLOW-002 | Follow-up | Skill migration fixtures | `SKILL_MODEL_SPEC.md` 已定义 Skill fixture 名称和断言 | 后续 Skill graph 或 training graph 仍需在实现测试中落地 low confidence / conflicting evidence 行为 | 在后续 PR 的 backend / frontend test plan 中引用并实现这些 fixtures | `SKILL_MODEL_SPEC.md`; `13_TEST_PLAN_BACKEND.md`; `14_TEST_PLAN_FRONTEND.md` | PR5-PR8 / F7 |
| PR16-FOLLOW-003 | Follow-up | Pressure UI states | `UX_SPEC.md` / `UI_DESIGN_SYSTEM.md` 有 pressure 页面与状态，但缺 mode-level spec 后的 turn loop / pace / interrupt 映射 | PR7 / PR8 前端可能照搬 Polish 行为 | 回写 Pressure UI state machine 和组件状态映射 | `UX_SPEC.md`; `UI_DESIGN_SYSTEM.md`; `API_SPEC.md` | AIFI-BE-004; PR7 / PR8 |

## 5. AI/Core 目录方案重审

| Option | Directory Shape | Pros | Cons | Migration Cost | Long-term Maintainability | Recommendation |
|---|---|---|---|---|---|---|
| 1. 保持 PR1.5 方案但加强规则 | `apps/api/app/application/agents/**`; `apps/api/app/application/ai/**`; `apps/api/app/infrastructure/agent_runtime/langgraph/**` | 改动最小；贴近 `03_TARGET_DIRECTORY_STRUCTURE.md` 与 `04_BACKEND_AGENT_RUNTIME_PLAN.md` 当前表格 | 命名与 ADR-0005 的 open issue 冲突；`agents` 与 `ai` 语义分裂；后续 `application/ai_runtime` 再出现会扩大迁移 | Low now, High later | 中等偏低，依赖持续人工解释 | 不推荐作为长期形态；只能作为历史输入 |
| 2. 聚合 AI runtime 目录，减少深嵌 | `apps/api/app/application/ai_runtime/{facade,contracts,registry,trace_bridge,side_effect_guard,handoff,interrupts,runtime_flags}.py`; `apps/api/app/infrastructure/ai_runtime/langgraph/**`; `apps/api/app/infrastructure/db/repositories/ai_runtime/**` | AI Runtime 与 Core Business 边界清晰；命名与 ADR open issue 可一次收敛；import scan 更稳定；PR2 可只落 repository / persistence，不创建业务 graph | 已由 AIFI-ARCH-008 更新 `03`、`04`、`17` 和 ADR-0005；PR3 只需按最终路径实现 | Medium | 高，目录职责可被测试和 review 稳定执行 | **最终采用**。AIFI-ARCH-008 已回写目录与 ADR caveat |
| 3. 按业务 graph domain 组织 AI runtime | `apps/api/app/application/ai_runtime/graphs/{job_match,polish,pressure,report,review}/**`; shared runtime contracts 分散到各 graph 下 | 每个业务 graph 就近维护 descriptor、node contract、prompt mapping | PR2 / PR3 过早暴露业务 graph；Pressure / Skill / Prompt blockers 未关闭时容易把 planning gap 写进代码；共享 guard / trace / handoff 易重复 | High | 中等，graph 多后共享语义易漂移 | 不推荐作为 PR2/PR3 形态；可在 PR5-PR8 逐 graph 引入 |

最终决策：**Option 2，聚合 AI runtime 目录**。AIFI-ARCH-008 已把 ADR-0005 的 directory open issue 更新为 accepted directory shape，并同步 `03_TARGET_DIRECTORY_STRUCTURE.md`、`04_BACKEND_AGENT_RUNTIME_PLAN.md`、`17_PR_BREAKDOWN_AND_IMPLEMENTATION_SEQUENCE.md`。PR2 仍不得创建业务 graph 目录，也不得扩大 LangGraph import 边界；PR2 code implementation 仍需其他 PR1.6 blocker 关闭或 accepted risk 后重新授权。

## 6. Pressure Mode Remediation Plan

当前成熟度判定：**Pressure code = placeholder；Pressure active docs / prompt contracts = Draft planning；Pressure graph = blocked until mode-level spec closes**。

| 检查项 | 当前状态 | 证据 | PR2 / PR8 影响 |
|---|---|---|---|
| 代码成熟度 | placeholder | `PressureUseCases.bootstrap()` 返回 `pressure_skeleton`; `pressure.py` 只有 `APIRouter`; `PressureSessionResponse` 只有 `session_id` / `status` | PR2 不可实现 Pressure runtime；PR8 或单独 Pressure PR 才能进入 |
| active docs | 有 API / application flow / data / UX 片段，但没有统一 mode-level spec | `APPLICATION_FLOW_SPEC.md` flows 8-10；`API_SPEC.md` API-PRESSURE-*；`DATA_MODEL.md` PressureSessionDetail | 需回写或新建 spec 后再做 graph |
| prompt contracts | `P-PRESSURE-001` 至 `P-PRESSURE-009` 为 Draft | `PROMPT_SPEC.md` §9.4；`PRESSURE_CONTRACTS.md` §13 | 只能指导 contract，不等于 runtime prompt asset ready |
| graph plan | Pressure 与 Report / Review 在后段 graph planning 中相关 | `08_BACKEND_GRAPH_PLANS_REPORT_REVIEW.md`; `17` PR8 行 | Pressure graph 推迟到 mode-level spec 后 |

Pressure mode-level spec 必须补齐：

| Required Topic | Required Content | Target Document | Target PR |
|---|---|---|---|
| session lifecycle | create / active / paused / completed / failed / cancelled；source unavailable 处理；owner scope | `APPLICATION_FLOW_SPEC.md`; `DATA_MODEL.md`; `API_SPEC.md` | AIFI-BE-004 |
| opening strategy | `P-PRESSURE-001` 与会话目标、岗位/简历摘要、禁重复 refs、低置信边界 | `PROMPT_SPEC.md`; `PRESSURE_CONTRACTS.md`; Prompt Asset registry | AIFI-BE-004; AIFI-PROMPT-002 |
| first question | 首题生成、题目类型、source refs、question persistence、repeat guard | `APPLICATION_FLOW_SPEC.md`; `API_SPEC.md`; `DATA_MODEL.md` | AIFI-BE-004 |
| answer save | 保存回答不调用 LLM；owner、version、idempotency、长度校验 | `APPLICATION_FLOW_SPEC.md`; `API_SPEC.md`; `13_TEST_PLAN_BACKEND.md` | AIFI-BE-004 |
| answer quality assessment | `P-PRESSURE-003` 输出质量判断，不直接写 score formal object | `PRESSURE_CONTRACTS.md`; `SCORING_SPEC.md`; `DATA_MODEL.md` | AIFI-BE-004 |
| follow-up strategy | `P-PRESSURE-004` 选择追问策略，绑定 previous turn、coverage、forbidden refs | `PRESSURE_CONTRACTS.md`; `APPLICATION_FLOW_SPEC.md` | AIFI-BE-004 |
| follow-up question | `P-PRESSURE-005` 生成追问，不重复同题，不绕过 answer quality | `PRESSURE_CONTRACTS.md`; `API_SPEC.md` | AIFI-BE-004 |
| pressure intensity | 强度是模式状态 / hint，不是隐藏评分或单次 LLM 自由变量 | `UX_SPEC.md`; `UI_DESIGN_SYSTEM.md`; `PRESSURE_CONTRACTS.md` | AIFI-BE-004 |
| pace | `P-PRESSURE-006` 控制节奏；暂停、继续、超时、低置信可见 | `APPLICATION_FLOW_SPEC.md`; `UX_SPEC.md`; `API_SPEC.md` | AIFI-BE-004 |
| turn loop | opening -> first question -> answer save -> assessment -> follow-up / continue / end | `APPLICATION_FLOW_SPEC.md`; `08_BACKEND_GRAPH_PLANS_REPORT_REVIEW.md` | AIFI-BE-004; PR8 |
| end condition | `P-PRESSURE-007` 只判断是否结束，不生成正式报告 | `PRESSURE_CONTRACTS.md`; `APPLICATION_FLOW_SPEC.md` | AIFI-BE-004 |
| session score | `P-PRESSURE-008` 引用 `ScoreRuleVersion`，不得输出精确通过概率 | `SCORING_SPEC.md`; `PROMPT_SPEC.md`; `DATA_MODEL.md` | AIFI-BE-004 |
| report handoff | `P-PRESSURE-009` 组装 report input package，不生成 report body | `APPLICATION_FLOW_SPEC.md`; `REPORT_CONTRACTS.md`; `DATA_MODEL.md` | AIFI-BE-004; PR8 |
| review handoff | Pressure outputs 作为 Review 输入；Review candidate refs 不自动 formalize | `REVIEW_CONTRACTS.md`; `APPLICATION_FLOW_SPEC.md`; `DATA_MODEL.md` | AIFI-BE-004; PR8 |
| weakness / asset / training candidate handoff | 只产生 candidate / suggestion refs；正式对象必须用户确认 | `DATA_MODEL.md`; `API_SPEC.md`; `WEAKNESS_CONTRACTS.md`; `ASSET_CONTRACTS.md`; `TRAINING_CONTRACTS.md` | AIFI-BE-004; PR8 |
| API | endpoints、request / response、async status、error mapping、idempotency、owner scope | `API_SPEC.md` | AIFI-BE-004 |
| data model | `PressureSessionDetail`、turn refs、pace state、score refs、report input refs | `DATA_MODEL.md`; `PERSISTENCE_MODEL.md` | AIFI-BE-004 |
| prompt design | Pressure Prompt Asset、version、golden fixtures、redaction、model comparison | `PROMPT_SPEC.md`; Prompt Asset registry | AIFI-PROMPT-002 |
| graph design | graph state / node / edge / handoff / side-effect guard / replay policy | `08_BACKEND_GRAPH_PLANS_REPORT_REVIEW.md`; `04_BACKEND_AGENT_RUNTIME_PLAN.md` | PR8 after blockers |
| frontend UI | session state、turn chain、pace, intensity, low confidence, end CTA, report entry | `UX_SPEC.md`; `UI_DESIGN_SYSTEM.md` | PR7 / PR8 |
| tests | no same-question loop、answer save no LLM、candidate-only、no exact probability、raw-off | `13_TEST_PLAN_BACKEND.md`; `14_TEST_PLAN_FRONTEND.md`; `15_VALIDATION_PLAN.md` | AIFI-BE-004; PR8 |

是否应在 PR2 前完成：**是**，至少需要完成 mode-level spec 与 PR2 hold 决策；Pressure graph 本身不进入 PR2。Pressure graph 应推迟到 mode-level spec、Prompt Asset / Evaluation 和必要目录边界关闭后。Skill Model 已由 `SKILL_MODEL_SPEC.md` 接受，Pressure graph 只能引用该 active doc 的 skill refs。应新建或回写的文档包括：`APPLICATION_FLOW_SPEC.md`、`DATA_MODEL.md`、`API_SPEC.md`、`UX_SPEC.md`、`UI_DESIGN_SYSTEM.md`、`PROMPT_SPEC.md`、`PRESSURE_CONTRACTS.md`、`08_BACKEND_GRAPH_PLANS_REPORT_REVIEW.md`，必要时新增经 `BACKLOG.md` / `DOCS_INDEX.md` 登记的 Pressure mode-level spec。

## 7. Prompt Design Remediation Plan

| Concept | Definition | Required Owner / Evidence | 禁止事项 |
|---|---|---|---|
| Prompt Contract | `PROMPT_SPEC.md` 和 `prompt-contracts/*.md` 中登记的 `P-*` contract id、goal、inputs、outputs、validation、trace / evidence、failure policy | `PROMPT_SPEC.md` canonical registry + 子文档 Draft | 不等同于完整生产 Prompt 文案，不定义 provider / model 参数 |
| Runtime Prompt Bundle | 运行时代码构造并传给 `LlmTransportRequest` 的结构化 prompt 输入包，例如 contract ids、input refs、schema id、prompt version、evidence bundle | `question_prompts.py`; `feedback_prompts.py`; progress prompt builders; future graph node builders | 不保存 raw prompt、raw completion、provider payload 到普通日志、checkpoint、API response |
| Production Prompt Asset | 可版本化、可评审、可灰度、可回滚的生产 Prompt 模板 / 文案资产 | Prompt Asset registry；owner、asset_id、contract ids、version、model policy、fixtures、rollback policy | 不隐藏在 Python builder 或 fake transport 中 |
| Evaluation Fixture | golden inputs、expected structure、validator expectations、redaction cases、model comparison baseline | `13_TEST_PLAN_BACKEND.md`; Prompt Asset registry; deterministic fake / schema validator | 不把 provider 200 当作 Prompt 成功 |

Polish prompt design 文件应包含：

- `P-POLISH-*` contract 到 `polish_question_generation`、`polish_answer_feedback`、progress tree prompt assets 的映射。
- `asset_id`、`prompt_version`、`schema_id`、`contract_ids`、runtime task type、input ref policy、redaction policy。
- golden fixtures：success、schema invalid、semantic invalid、evidence refs invalid、low confidence、source unavailable、fallback、candidate-only。
- question quality metrics：重复题检测、required elements coverage、business constraint coverage、evidence precision、answer leak prevention。
- feedback quality metrics：score dimension consistency、loss point evidence、retry delta validity、candidate redaction、legacy compatibility。

Pressure prompt design 文件应包含：

- `P-PRESSURE-001` 至 `P-PRESSURE-009` 的 Prompt Asset 与 runtime bundle 版本。
- opening、first question、answer quality、follow-up strategy、follow-up question、pace、end condition、session score、report input assembly 的分步 fixture。
- no same-question loop、pace / intensity visibility、source unavailable、report input is not report body、candidate-only handoff。

Report / Review prompt design 文件应包含：

- `P-REPORT-*` 与 `P-REVIEW-*` 的 report section / review item / candidate refs / copy boundary 映射。
- no exact probability、hidden scoring rules redaction、copy content not export、review source trust flags、third-party privacy flags。
- report / review score consistency fixture 与 candidate-only fixture。

| Remediation Topic | Required Rule | Target Document | Target PR |
|---|---|---|---|
| Prompt versioning | 每个 Production Prompt Asset 必须有 `prompt_version`、`schema_id`、compatible contract ids、rollback target | Prompt Asset registry; `PROMPT_SPEC.md` | AIFI-PROMPT-002 |
| Prompt regression tests | 每个 asset 至少覆盖 success、validation_failed、low_confidence、source_unavailable、fallback、redaction | `13_TEST_PLAN_BACKEND.md`; Prompt Asset registry | AIFI-PROMPT-002 |
| Golden fixtures | fixture 不保存真实简历全文 / 岗位全文 / provider payload；使用 refs、safe summaries、expected schema | Prompt Asset registry; `15_VALIDATION_PLAN.md` | AIFI-PROMPT-002 |
| Prompt quality metrics | schema validity、semantic constraints、evidence precision、redaction pass、consistency、cost / latency summary | `PROMPT_SPEC.md`; Prompt Asset registry | AIFI-PROMPT-002 |
| Model comparison policy | 只比较结构化质量、边界、成本、延迟、fallback rate；真实 provider smoke 必须显式 gate | Prompt Asset registry; `SECURITY_PRIVACY.md` | AIFI-PROMPT-002 |
| Redaction and forbidden output policy | raw prompt、raw completion、provider payload、system prompt、hidden scoring rules 禁止进入日志、checkpoint、API、copy content | `SECURITY_PRIVACY.md`; `API_SPEC.md`; `15_VALIDATION_PLAN.md` | AIFI-PROMPT-002; AIFI-BE-005 |

Contract -> Runtime prompt -> Code builder -> Validator -> Tests 映射表：

| Contract | Runtime prompt | Code builder | Validator | Tests |
|---|---|---|---|---|
| `P-POLISH-002` | `polish_question_generation` bundle | `build_polish_question_generation_prompt_bundle` | `validate_llm_question_output`; `adapt_llm_output_to_question_draft` | question schema, semantic, evidence refs, repeated question, redaction, fallback |
| `P-POLISH-003/004/005/009` | `polish_answer_feedback` bundle | `build_polish_feedback_prompt_bundle` | `validate_feedback_llm_output`; `adapt_llm_output_to_structured_payload`; feedback consistency validation | feedback schema, dimension consistency, retry delta, candidate-only, raw payload leak |
| Progress tree prompt assets | `polish_progress_tree_*` bundles | `PolishProgressTreeV2Pipeline`; progress prompt builders | progress tree normalization / quality gates | progress tree grounding, source excerpts, low confidence, no fabricated display terms |
| `P-JOBMATCH-001/002/003/004` | `job_match_analysis` bundle | `LlmJobMatchAnalyzer.analyze` | `_normalize_job_match_payload`; scoring / evidence normalization | job match score, weakness candidate, no exact probability, fallback parity |
| `P-PRESSURE-001..009` | Pressure runtime bundles | Not implementation-ready; target pressure prompt builders | Target Pressure validators | no same-question loop, pace/end, report input not report body, candidate-only |
| `P-REPORT-*` | Report runtime bundles | Target report prompt builders | Target report validators | report score refs, copy boundary, no exact probability, source unavailable |
| `P-REVIEW-*` | Review runtime bundles | Target review prompt builders | Target review validators | candidate-only, third-party privacy, trust flags, no formal write |

## 8. Skill / Capability Model Remediation Plan

结论：AIFI-ARCH-007 已将统一 Skill Model 回写为 active design doc：`docs/02-design/SKILL_MODEL_SPEC.md`。`ScoreDimension`、`ProgressTree`、`Weakness`、`Asset`、`TrainingRecommendation` / `TrainingTask` 都不能单独承担 Skill Model；后续 graph 只能引用已冻结 taxonomy 和 mapping，不得发明临时 skill key。

| Existing Concept | 当前职责 | 不能承担 Skill Model 的原因 |
|---|---|---|
| `ScoreDimension` | 评分规则版本下的维度、权重、分值解释 | 是评分解释结构，不表达长期能力分类、能力等级、证据累积、训练路径 |
| `ProgressTree` | 会话内面试主题、节点、状态、当前位置 | 是 runtime / session planning，不是跨模式能力 taxonomy |
| `Weakness` / `WeaknessCandidate` | 已确认或待确认的薄弱项 | 表达问题 / 风险，不覆盖正向能力、熟练度、成长轨迹 |
| `Asset` / `AssetVersion` | 可复用表达素材、版本和来源 | 是内容资产，不是能力本体 |
| `TrainingRecommendation` / `TrainingTask` | 训练建议和用户显式训练动作 | 是行动计划 / 执行记录，不是能力分类体系 |

推荐 Skill taxonomy：

| Type | Required Fields / Semantics | Connects To |
|---|---|---|
| `SkillTaxonomyVersion` | version、scope、effective date、migration policy、owner | 所有 Skill mapping |
| `SkillArea` | top-level capability area，例如技术深度、项目表达、系统设计、业务理解、风险控制 | Skill 分组、报告维度 |
| `Skill` | stable skill id、area id、name、observable behaviors、related job signals | question pattern、score dimension、weakness、asset、training |
| `SkillLevel` | level id、behavior rubric、evidence threshold、confidence requirement | SkillAssessment、SkillProgress |
| `SkillEvidence` | evidence_ref、source_type、source_version、summary、confidence、owner_ref | answer、feedback、report、review、training result |
| `SkillAssessment` | skill id、score / level、confidence、evidence_refs、validation status、generated_by_task_id | ScoreResult、Review、Report |
| `SkillGap` | target skill、current level、target level、gap reason、evidence refs、candidate boundary | WeaknessCandidate、TrainingRecommendation candidate |
| `SkillProgress` | skill id、time series、confirmed evidence refs、training result refs、trend | TrainingTask、Review |
| `SkillToQuestionPattern` | skill id、question pattern ids、difficulty、mode applicability | polish question、pressure question |
| `SkillToScoreDimension` | skill id、score dimension id、weight policy、non-equivalence note | ScoreDimension |
| `SkillToTrainingAction` | skill id、training recommendation shape、asset refs、entry mode | TrainingRecommendation、TrainingTask |

它如何连接：

| Product Area | Skill Model Role | Boundary |
|---|---|---|
| resume analysis | 从简历证据生成初始 SkillEvidence / possible skill signals | 不自动定级为高置信 SkillAssessment |
| job match | 将岗位要求映射到 target Skill / SkillGap | 不输出精确通过概率 |
| progress tree | 使用 SkillToQuestionPattern 辅助选题 | ProgressTree 节点不是 Skill |
| polish question | 基于 SkillGap / topic 生成题目 | 仍走 question validation 与 no repeat |
| pressure question | 基于 SkillGap / pressure focus 生成压力追问 | 需 mode-level spec 后启用 |
| feedback score | 反馈可产生 SkillEvidence / SkillAssessment candidate | 不自动写 formal Weakness |
| report | 聚合 confirmed evidence 和 score refs | 不暴露 hidden scoring rules |
| review | 形成 SkillGap / weakness / asset / training candidate refs | 仍需用户确认 |
| weakness | Weakness 可映射 SkillGap，但不等于 Skill | 候选到正式需确认 |
| asset | Asset 可支撑 SkillEvidence 或训练材料 | Asset 不是 Skill |
| training | TrainingRecommendation / TrainingTask 作用于 SkillGap | AI suggestion 不自动创建 TrainingTask |

`SKILL_MODEL_SPEC.md` 状态：**已新增并登记为 active design doc**。AIFI-ARCH-007 已关闭 Skill Model 设计 blocker；PR2 code implementation 仍需等待 Pressure、Prompt Asset / Evaluation、PR2 preflight readiness 等剩余 blocker 关闭，或主 Agent 显式接受风险。

迁移顺序：

1. `AIFI-ARCH-007` 已冻结 Skill taxonomy、mapping、confirmation boundary、fixture。
2. `DOCS_INDEX.md` 已登记 `SKILL_MODEL_SPEC.md`。
3. `DATA_MODEL.md`、`SCORING_SPEC.md`、`PROMPT_SPEC.md` 已补最小映射交叉引用；`APPLICATION_FLOW_SPEC.md` 暂不改写，后续实现 PR 只能引用 `SKILL_MODEL_SPEC.md`。
4. PR5 / PR6 / PR8 graph migration 只引用已冻结 Skill mapping，不发明临时 Skill。
5. F7 fixtures 覆盖 low confidence、conflicting evidence、manual correction、training result update。

## 9. Existing Code Migration Matrix

| Existing File | Existing Symbol | Current Role | Target Role | Action | Target File / Symbol | PR | Tests |
|---|---|---|---|---|---|---|---|
| `apps/api/app/application/polish/use_cases.py` | `PolishUseCases` | Core Polish session、question、answer、feedback、progress tree workflow | Core answer save 保留；AI generation 经 `AiOrchestrationFacade` / AI Runtime port | split / wrap | `application/polish/**` Core use case + `application/ai_runtime/facade.py` | PR6 after blockers | answer save no LLM; legacy API compatibility; candidate-only |
| `apps/api/app/application/polish/question_llm.py` | `PolishQuestionLlmService` | question generation LLM / fallback / validation service | Graph node callable through project-owned port; legacy fallback retained | wrap then parity migrate | `application/ai_runtime/graphs/polish/question_node.py` or equivalent descriptor | PR6 | question schema; semantic constraints; repeated question; fallback parity |
| `apps/api/app/application/polish/feedback_llm.py` | `PolishFeedbackLlmService` | feedback LLM / deterministic fallback / consistency validation | Graph node callable through project-owned port; candidate-only preserved | wrap then parity migrate | `application/ai_runtime/graphs/polish/feedback_node.py` or equivalent descriptor | PR6 / PR8 | feedback consistency; raw payload leak negative; candidate formal boundary |
| `apps/api/app/infrastructure/llm/job_match.py` | `LlmJobMatchAnalyzer` | direct LLM job match analyzer via `LlmTransport` | Job Match graph node with legacy analyzer fallback and parity policy | wrap then deprecate | `application/ai_runtime/graphs/job_match/**`; `infrastructure/llm/job_match.py` fallback | PR5 | API parity; score refs; weakness candidate; no exact probability |
| `apps/api/app/application/pressure/use_cases.py` | `PressureUseCases` | placeholder bootstrap returning `pressure_skeleton` | Pressure mode Core use case / AI Runtime graph entry after mode spec | hold | Target only after AIFI-BE-004: `application/pressure/**` + `application/ai_runtime/graphs/pressure/**` | PR8 or authorized Pressure PR | session lifecycle; turn loop; answer save no LLM; no same-question loop |
| `apps/api/app/api/v1/pressure.py` | `router` | route prefix placeholder | Pressure API endpoints after mode-level API contract | hold | `apps/api/app/api/v1/pressure.py` | PR8 or authorized Pressure PR | owner scoped endpoints; async status; source unavailable; no export |
| `apps/api/app/schemas/pressure.py` | `PressureSessionResponse` | minimal DTO placeholder | Pressure session / question / answer / feedback / score DTOs after active contract | hold | `apps/api/app/schemas/pressure.py` | PR8 or authorized Pressure PR | schema contract; low confidence visible; candidate refs |
| `apps/api/app/application/polish/question_prompts.py` | `build_polish_question_generation_prompt_bundle` | runtime compact prompt bundle builder | registered Runtime Prompt Bundle tied to Production Prompt Asset | keep + register | Prompt Asset registry; builder metadata | AIFI-PROMPT-002 then PR6 | golden fixtures; redaction; evidence refs invalid |
| `apps/api/app/application/polish/feedback_prompts.py` | `build_polish_feedback_prompt_bundle` | runtime feedback prompt bundle builder | registered Runtime Prompt Bundle tied to feedback Prompt Asset | keep + register | Prompt Asset registry; builder metadata | AIFI-PROMPT-002 then PR6 | feedback golden fixtures; score dimension consistency |
| `apps/api/app/application/polish/progress_tree_v2.py` | `PolishProgressTreeV2Pipeline` | progress tree LLM pipeline / planner / normalization | Polish graph progress node; Skill mapping consumer, not Skill source | split boundary | `application/ai_runtime/graphs/polish/progress_tree_node.py`; Skill Model mapping | PR6 + AIFI-ARCH-007 | grounding; low confidence; Skill mapping non-equivalence |
| `apps/api/app/infrastructure/db/models/report.py` | `InterviewReport`; `ReportSection` | report persistence skeleton | Core report formal object; graph writes through Core command / repository | keep Core; handoff via facade | `application/reports/**`; `application/ai_runtime/graphs/report/**` | PR8 | report score refs; copy boundary; no exact probability |
| `apps/api/app/infrastructure/db/models/review.py` | `InterviewReview` | review persistence skeleton | Core review formal object; graph outputs candidate refs through Core command | keep Core; handoff via facade | `application/reviews/**`; `application/ai_runtime/graphs/review/**` | PR8 | candidate-only; privacy flags; review source trust |
| `apps/api/app/infrastructure/db/models/scoring.py` | `ScoreDimension` | scoring dimension / rule element | Mapping target for `SkillToScoreDimension`; not Skill source | map only | `SKILL_MODEL_SPEC.md` mapping table | AIFI-ARCH-007 | mapping fixture; no exact probability |
| `apps/api/app/infrastructure/db/models/weakness.py` | `Weakness`; `WeaknessCandidate` | formal / candidate weakness objects | SkillGap consumer / mapping target; confirmation boundary preserved | map only | `SKILL_MODEL_SPEC.md`; `DATA_MODEL.md` | AIFI-ARCH-007; PR8 | no silent formal write; candidate confirmation |
| `apps/api/app/infrastructure/db/models/asset.py` | `Asset`; `AssetVersion` | formal reusable asset and version | SkillEvidence / training material source; not Skill | map only | `SKILL_MODEL_SPEC.md`; `DATA_MODEL.md` | AIFI-ARCH-007; PR8 | asset candidate confirmation; source refs |
| `apps/api/app/infrastructure/db/models/training.py` | `TrainingRecommendation`; `TrainingTask` | training suggestion / explicit task | SkillToTrainingAction consumer; AI suggestion cannot auto-create task | map only | `SKILL_MODEL_SPEC.md`; `DATA_MODEL.md`; `TRAINING_CONTRACTS.md` | AIFI-ARCH-007; PR8 | confirm before task; no auto TrainingTask |

## 10. PR Sequence 修正建议

| 问题 | 回答 |
|---|---|
| PR2 是否可以启动 | **不可以启动 code implementation**。只能做 repo-state preflight、只读 recon 和受权文档回写。 |
| 如果不能，阻塞项是什么 | `AIFI-BE-004` Pressure mode-level spec；`AIFI-PROMPT-002` Prompt Asset / Evaluation；`AIFI-BE-005` PR2 runtime data model preflight readiness gate；以及本文 §4 仍未关闭的 blocker。`AIFI-ARCH-007` Skill / Capability Model 已由 `SKILL_MODEL_SPEC.md` 接受并关闭；AIFI-ARCH-008 AI/Core directory boundary 已关闭，不再作为 PR2 blocker。 |
| 是否新增 PR1.6 | **是，PR1.6 必需**。当前仓库已登记 PR1.6 文档和 blocker note，本轮只更新本文档。 |
| PR1.6 应做哪些文档修复 | 创建 / 完善本文；冻结 PR2 blocked；登记 Pressure / Prompt Asset / Skill / Directory / PR2 readiness findings；明确 active docs 回写目标和验证命令。 |
| PR2 / PR3 / PR4 / PR5 / PR6 / PR8 是否需要重排 | 需要局部重排：PR2 保持 blocked；PR3/PR4 不创建业务 graph；PR5/PR6/PR8 必须在 Prompt Asset 和 Pressure spec 等剩余 blocker 关闭后按 graph 分批进入，并统一引用 `SKILL_MODEL_SPEC.md`。directory boundary 已由 AIFI-ARCH-008 关闭。 |
| Pressure / Skill / Prompt 应该插入哪个 PR | Pressure spec 插入 AIFI-BE-004，在 PR8 或单独 Pressure PR 之前；Skill 已由 AIFI-ARCH-007 / `SKILL_MODEL_SPEC.md` 关闭，后续任何 skill-based graph 只能引用该 active doc；Prompt Asset / Evaluation 插入 AIFI-PROMPT-002，在 PR5-PR8 prompt migration 前。 |
| 是否要新增 AIFI 任务 | 当前 `BACKLOG.md` 已存在 AIFI-BE-004、AIFI-PROMPT-002、AIFI-ARCH-007、AIFI-ARCH-008、AIFI-BE-005；本轮不新增任务。`SKILL_MODEL_SPEC.md` 已由 AIFI-ARCH-007 落为 active doc；若后续拆出 Prompt Asset registry，需另行授权更新 `BACKLOG.md`。 |
| 是否要更新 DOCS_INDEX / BACKLOG / ADR-0005 | AIFI-ARCH-008 本轮只更新 ADR-0005 和授权专题文档；不更新 `DOCS_INDEX.md` 或 `BACKLOG.md`。当前 `DOCS_INDEX.md` 已登记 19 号文档，`BACKLOG.md` 已登记 PR1.6 blocker tasks；BACKLOG 状态需另行授权维护。 |

修正后的 PR sequence：

| PR | Corrected Scope | Gate |
|---|---|---|
| PR1.6 | docs-only blocker identification / remediation planning | 本文验证通过；PR2 remains blocked |
| AIFI-BE-004 | Pressure mode-level spec | Pressure graph held until accepted |
| AIFI-PROMPT-002 | Prompt Asset / Evaluation design | PR5-PR8 prompt migration held until registry / fixtures accepted |
| AIFI-ARCH-007 | Skill / Capability Model | **Accepted**：`SKILL_MODEL_SPEC.md` 已登记；skill-based graph / training mapping 只能按该 active doc 实现 |
| AIFI-ARCH-008 | AI/Core directory boundary + ADR caveat | **Closed in this revision**：PR3/PR4 directory / import boundary frozen |
| AIFI-BE-005 | PR2 Runtime Data Model preflight readiness gate | PR2 code implementation can be re-authorized only after pass or accepted risk |
| PR2 | AI Runtime data / repository foundation only after re-authorization | no business graph, no LangGraph dependency, no real provider |
| PR3 | `application/ai_runtime` facade / contracts / registry / guard | Core no LangGraph import |
| PR4-LG-DEP / PR4 | LangGraph dependency spike + infrastructure adapter / fake graph | only infrastructure adapter imports LangGraph; raw-off |
| PR5 | Job Match graph parity migration | legacy compatibility and score/candidate tests |
| PR6 | Polish graph migration | prompt assets and answer-save-no-LLM tests |
| PR7 | Frontend AI runtime UI | sanitized status / timeline / interrupt UI only |
| PR8 | Report / Review / Pressure / candidate closure | Pressure spec, Prompt assets, Skill mapping, candidate confirmation |

## 11. Implementation-Ready Criteria

| Criteria | Required Standard | Validation Command / Evidence |
|---|---|---|
| 方法级 contract | 每个 facade、runner、repository、graph node、prompt builder、validator 必须列明 inputs / outputs / side effects / errors / tests | target design doc + method test names |
| 数据模型级 contract | owner、status、record_version、trace refs、evidence refs、candidate/formal、retention、rollback 均冻结 | `DATA_MODEL.md`; `PERSISTENCE_MODEL.md`; repository tests |
| graph state / node / edge contract | graph state 只保存 refs / safe summaries / validation flags；node 不直接写 formal object；edge failure 可见 | graph plan + boundary tests |
| prompt asset contract | Prompt Contract、Runtime Prompt Bundle、Production Prompt Asset、Evaluation Fixture 映射完整 | Prompt Asset registry + golden fixtures |
| skill model contract | Skill taxonomy、Skill mapping、confirmation boundary、low confidence / conflicting evidence fixture 完整 | `SKILL_MODEL_SPEC.md` |
| API / schema contract | endpoint、request / response、status、error、idempotency、owner scope、source unavailable、candidate refs 已冻结 | `API_SPEC.md`; contract tests |
| frontend state machine | loading、queued、running、partial、low_confidence、validation_failed、source_unavailable、generation_failed、cancelled、retry、candidate confirmation 状态完整 | `UX_SPEC.md`; `UI_DESIGN_SYSTEM.md`; frontend tests |
| test method contract | test file、test method、arrange / act / assert、fixtures、redaction negative cases 与 target behavior 对齐 | `13_TEST_PLAN_BACKEND.md`; `14_TEST_PLAN_FRONTEND.md`; `15_VALIDATION_PLAN.md` |
| validation command | repo-state、diff、doc governor、forbidden wording scan、raw-off scan、import boundary scan 在授权 scope 内通过 | 本文 §12 命令；实现 PR 的 pytest / npm gates |

PR2 code implementation 的 P0 gates：

| Gate | 必须满足 | 未满足时结论 |
|---|---|---|
| P0-1 Source-of-truth backfill | PR1.6 决定 active docs 回写范围；必要回写完成或 accepted risk 登记 | PR2 blocked |
| P0-2 Runtime feature flags | runtime enablement、per-graph flag、real-provider gate、default-off、rollback 冻结 | PR2 blocked |
| P0-3 Directory boundary | `application/ai_runtime/**` / `infrastructure/ai_runtime/langgraph/**` 唯一冻结；`application/ai/**`、`application/agents/**`、`infrastructure/agent_runtime/**` 和 `langgraph_adapters/**` 禁止创建 | Satisfied by AIFI-ARCH-008；若后续 PR 改变目录形态则重新阻断 |
| P0-4 Repository contract | runtime repository methods、owner scope、timeline read、LLM summary read、idempotency replay、retention cleanup 冻结 | PR2 blocked |
| P0-5 Bootstrap / rollback | SQLAlchemy bootstrap、rollback order、in-flight run handling、pending writes fail-closed 规则明确 | PR2 blocked |
| P0-6 Test list consistency | PR2 tests 文件名、method、fixtures、redaction markers、owner cases 与 repository contract 对齐 | PR2 blocked |
| P0-7 Prompt asset boundary | PR2 不依赖 production prompt asset；PR5-PR8 前 Prompt Asset registry / fixtures 冻结 | PR2 blocked for prompt migration |
| P0-8 Pressure hold | Pressure mode-level spec 未完成前不创建 Pressure business graph | Pressure graph blocked |
| P0-9 Skill model accepted | `SKILL_MODEL_SPEC.md` 已登记；任何 graph 不得生成未授权 `Skill*` formal object，且不得把 Weakness / ScoreDimension / ProgressTree / Asset / Training 对象当 Skill | Skill-based graph allowed only after remaining PR scope authorization |
| P0-10 Security/privacy | raw prompt、raw completion、provider payload、checkpoint payload、system prompt、hidden scoring rules 禁止边界和 negative tests 明确 | PR2 blocked |

## 12. Recommended Next Action

推荐下一步：

1. 完成本 PR1.6 文档验证，确保只存在本文档 diff。
2. 不启动 PR2 code implementation；PR2 仅可做 repo-state preflight、只读 recon 和受权文档回写。
3. 由主 Agent 另行授权后，继续按 `AIFI-BE-004`、`AIFI-PROMPT-002`、`AIFI-BE-005` 关闭剩余 blocker；AIFI-ARCH-007 已由 `SKILL_MODEL_SPEC.md` 接受。
4. 若需要修改 `BACKLOG.md`、`DOCS_INDEX.md` 或 ADR-0005，必须先停止当前 PR1.6 docs-only scope 并获得新授权。
5. 只有 §11 P0 gates 全部关闭，或 accepted risk 被明确登记后，才允许给出 PR2 runtime foundation 代码实现 prompt。

是否先提交当前 PR1.5：可以先提交 PR1.5 或当前 PR1.6 文档 diff，但提交 / push 不在本轮授权范围内。是否启动 PR1.6：**是，本轮正在执行 PR1.6**。是否禁止 PR2：**禁止 PR2 code implementation**。如果未来允许 PR2，前置条件是 blocker 关闭或 accepted risk 登记，并重新锁定 PR2 allowed files / tests / validation。

本轮验证必须覆盖 repo-state、diff stat、whitespace check、doc governor、禁用模糊措辞扫描、临时输入 / checkpoint 事实源边界扫描，以及 raw payload / 表头人工确认扫描；实际命令以 `docs/tmp/GOAL_PR1_6_AI_PRODUCT_PROMPT_SKILL_PRESSURE.md` 的 Validation 段为准。
