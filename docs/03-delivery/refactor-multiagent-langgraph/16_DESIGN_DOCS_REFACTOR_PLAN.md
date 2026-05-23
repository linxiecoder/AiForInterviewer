---
title: 设计文档输出与重构计划
type: delivery-planning
status: draft-pr1
owner: 项目交付
permalink: ai-for-interviewer/docs/03-delivery/refactor-multiagent-langgraph/design-docs-refactor-plan
---

# 设计文档输出与重构计划

## 1. 文档目的

本文说明 LangGraph MultiAgent 重构后如何回写 active docs，避免专题设计包变成并行事实源。

## 2. 输入来源

- `AGENTS.md`
- `docs/00-governance/DOCS_INDEX.md`
- `docs/00-governance/DOCS_GOVERNANCE.md`
- active design docs：`APPLICATION_FLOW_SPEC.md`、`PERSISTENCE_MODEL.md`、`DATA_MODEL.md`、`PROMPT_SPEC.md`、`SCORING_SPEC.md`、`SECURITY_PRIVACY.md`、`API_SPEC.md`、`UX_SPEC.md`、`UI_DESIGN_SYSTEM.md`
- `prompt-contracts/*.md`
- 本专题 PR1 规划包

## 3. 当前状态

`docs/tmp` 是临时输入；本目录是 PR1 planning package；active facts 仍在 `docs/02-design/*`、`docs/03-delivery/*` 和已登记 ADR 中。

## 4. 目标输出

输出：

- 精确到 active doc 章节和 PR 的回写矩阵。
- source of truth 决策规则。
- 哪些内容留在专题设计包。
- 哪些内容必须回写 active docs。
- 冲突优先级和 PR2 可执行文档边界。
- archive 规则。
- 文档验收标准。

## 5. 必须覆盖范围

### 5.1 Active docs 回写矩阵

| Active doc | 目标章节 / 位置 | 必须回写内容 | 保留在专题包的内容 | 回写 PR | 阻断关系 |
|---|---|---|---|---|---|
| `docs/02-design/APPLICATION_FLOW_SPEC.md` | §2 全局原则、§3 Prompt 输入结构、§4 Flow matrix、§5 Validation / persistence handoff | `AiOrchestrationFacade`、`AgentRun`、runtime event flow、interrupt/resume、timeline、business handoff、Core command 写入边界 | Option 比较、SubAgent recon、目录草案 | PR3/PR4 | PR3 前必须回写 facade / runner / handoff；PR4 前必须回写 interrupt/resume |
| `docs/02-design/PERSISTENCE_MODEL.md` | §2 交接边界、§3 表族总览、§7 migration / rollback handoff | Core Business Tables / AI Runtime Tables / LangGraph Checkpoint Tables 三分；`agent_checkpoint_refs` 只保存 ref；in-flight task rollback；checkpoint 非事实源 | 字段命名草案、checkpointer 选型备忘 | PR2 | PR2 阻断 |
| `docs/02-design/DATA_MODEL.md` | §4.4 API handoff、§5.10 LLM trace、§6 audit chain、§7 状态域 | `AgentRun`、`AgentNodeRun`、`AgentInterrupt`、`LlmCall`、`AgentCheckpointRef` 逻辑对象；candidate/formal、trace/evidence、owner/status 字段语义 | 早期表格草案、PR 分拆说明 | PR2 | PR2 阻断 |
| `docs/02-design/API_SPEC.md` | §3 response envelope、§5 async task protocol、§6 endpoint matrix、§8 schema、§11 F7 assertions | `/api/v1/agent-runs`、timeline、interrupt resume、sanitized LLM summary；`AiTaskStatusResponse` 与 `AgentRunStatusResponse` 的边界；raw-off response 字段 | endpoint 草案比较、API 扩展备忘 | PR3/PR4 | PR3/PR4 阻断 |
| `docs/02-design/PROMPT_SPEC.md` | §7 validation、§8 trace/evidence、§9 contract catalog、各 domain 后续小节 | contract -> graph/node execution mapping；每个 graph 的 contract_ids、validation、low confidence、trace context、persistence target | graph skeleton、Option 比较 | PR5-PR8 | 每个业务 graph 迁移前阻断 |
| `docs/02-design/prompt-contracts/*.md` | 已登记 contract 的详细正文 / stub 摘要后追加 execution mapping | 只补已登记 `P-*` contract 的 graph execution mapping；不得新增未登记 contract ID | 未确认 graph 选项、未来 contract 候选 | PR5-PR8 | 对应 graph PR 阻断 |
| `docs/02-design/SCORING_SPEC.md` | score generation / handoff / F7 fixture 相关章节 | graph 评分节点必须引用 `ScoreRuleVersion`；scoring candidate 通过 validation 后才可写正式 `ScoreResult`；禁止精确通过概率 | graph 评分节点草案 | PR5/PR6/PR8 | 涉及评分 graph 前阻断 |
| `docs/02-design/SECURITY_PRIVACY.md` | §9 LLM 输入、§11 trace/retention/redaction、§12 日志、§21.3 handoff、§22 release checks | raw-off payload、checkpoint payload 禁止、timeline/debug/admin 可见矩阵、redaction、retention、audit、provider payload 禁止 | 风险草案、debug UI 草图 | PR2/PR4/PR8 | PR2 raw-off / PR4 timeline 阻断 |
| `docs/02-design/UX_SPEC.md` | 打磨 / 压力面工作台、内容沉淀确认、低置信校对、状态和异常章节 | AI task status、sanitized timeline、interrupt drawer、candidate confirmation、low confidence、validation failed、source unavailable 可见状态 | PR7 UI planning、组件草案 | PR7 | PR7 阻断 |
| `docs/02-design/UI_DESIGN_SYSTEM.md` | status badge、timeline、drawer、banner、panel、error state 组件章节 | runtime status badge、timeline event row、interrupt drawer、confirmation actions、low confidence banner、validation failed panel | 组件草案和测试备忘 | PR7 | PR7 阻断 |
| `docs/03-delivery/DELIVERY_PLAN.md` | F5 / M5 描述 | 仅当 PR2-PR8 阶段、里程碑或退出条件调整时更新 | PR breakdown 证据 | 主 Agent 受权 PR | 非本 SubAgent 范围 |
| `docs/03-delivery/BACKLOG.md` | AIFI-BE-002 行及后续任务行 | 消除 `AIFI-BE-002 DONE` 歧义；如需要新增 PR2-PR8 AIFI 任务，由主 Agent 汇总 | 规划细节 | 主 Agent 受权 PR | 非本 SubAgent 范围 |
| `docs/00-governance/DOCS_INDEX.md` | §1 当前有效入口、§2 目录边界、ADR 列表 | 登记 ADR-0005；必要时说明 PR1.5 spec 与 active docs 关系 | 无 | 主 Agent 受权 PR | 非本 SubAgent 范围 |
| `docs/04-decisions/ADR-0005-langgraph-agentic-workflow-runtime.md` | 全文 | Option C proposed 决策、边界、回滚和 active docs backfill | 方案比较细节留在 01 | PR1.5 | PR2 启动前需要 |

### 5.2 Source of truth 决策

| 事实类型 | Source of truth | 本专题包角色 |
|---|---|---|
| 产品需求 | `PRD.md` | 不改写 |
| API 字段 | `API_SPEC.md` | 草案输入 |
| 数据模型 | `DATA_MODEL.md` / `PERSISTENCE_MODEL.md` | 草案输入 |
| Prompt contract | `PROMPT_SPEC.md` / `prompt-contracts/*.md` | execution mapping 草案 |
| 安全隐私 | `SECURITY_PRIVACY.md` | 风险和验证补充 |
| 交付任务 | `BACKLOG.md` | PR1 已登记 |
| 长期架构决策 | `docs/04-decisions/ADR-0005-langgraph-agentic-workflow-runtime.md` proposed；Accepted 前仍需主 Agent / 架构评审确认 | 提供 Option 比较、边界、回滚输入 |

### 5.3 冲突优先级

| 冲突类型 | 优先级 | 处理规则 |
|---|---:|---|
| 本专题与 `AGENTS.md` / `DOCS_INDEX.md` / `BACKLOG.md` / `DELIVERY_PLAN.md` 冲突 | 1 | 以上位治理和交付入口为准；本专题回写修正 |
| 本专题与 `docs/02-design/*` active docs 冲突 | 2 | active docs 为准；若本专题结论需要生效，先按矩阵回写 active docs |
| 本专题与 ADR 冲突 | 2 | Accepted ADR 高于 proposed ADR；ADR-0005 proposed 高于普通 planning evidence |
| 本专题内部文档冲突 | 3 | README 和 16 的治理边界优先于各实施计划；02 的架构边界优先于 04-15 的细节 |
| `docs/tmp` 与任何 active / topic doc 冲突 | 5 | `docs/tmp` 只作输入，不参与执行裁决 |

任何冲突不得通过实现代码“先做了再补文档”解决；必须先由主 Agent 汇总到 active docs、BACKLOG 或 ADR。

### 5.4 PR1.5 后文档可用性

| 文档 / 内容 | PR1.5 后状态 | 可指导的 PR | 限制 |
|---|---|---|---|
| `README.md` PR1/PR1.5、PR2 checklist、active docs 关系 | implementation-ready governance input | PR2 | 不替代 BACKLOG / DOCS_INDEX |
| `01_ARCHITECTURE_OPTIONS.md` 硬条件、fallback、权重矩阵 | implementation-ready architecture input | PR2 | Option B fallback 必须显式登记 |
| `02_RECOMMENDED_ARCHITECTURE.md` runtime event、handoff、raw-off、checkpoint policy | implementation-ready architecture input | PR2 | API endpoint 细节仍需 PR3/PR4 回写 `API_SPEC.md` |
| `16_DESIGN_DOCS_REFACTOR_PLAN.md` PR2 行 | implementation-ready doc governance input | PR2 | 只能指导 PR2 active docs backfill，不授权改其它 docs |
| ADR-0005 proposed | proposed decision input | PR2 | 不是 Accepted；主 Agent 仍需登记 DOCS_INDEX |
| `04`、`05`、`10` 中 runtime data / trace 部分 | PR2 planning input | PR2 | 需在 PR2 代码/测试中验证 |
| `06`、`07`、`08`、`09` business graph plans | planning evidence | PR5-PR8 | 对应 graph 前必须回写 PROMPT / API / DATA / SECURITY |
| `11` Agent Runtime API plan | planning evidence | PR3/PR4 | endpoint 前必须回写 `API_SPEC.md` |
| `12`、`14` frontend plans | planning evidence | PR7 | UI 前必须回写 UX / UI design system |
| `13`、`15` test/validation plans | planning evidence | PR2-PR8 | 命令和文件名需以实现 PR 当前 repo 为准 |
| `17` PR breakdown | planning evidence | 主 Agent 汇总 | 不替代 BACKLOG |

### 5.5 AIFI-BE-002 DONE 语义收敛

`AIFI-BE-002 DONE` 只表示 PR1 已完成专题规划包骨架、BACKLOG / DOCS_INDEX 登记和 Option C 方向冻结。它不表示：

- LangGraph dependency、adapter、checkpointer 或 fake graph 已实现。
- AI Runtime tables、migration、rollback 或 repositories 已实现。
- `AiOrchestrationFacade`、Agent Runtime API、timeline、interrupt/resume 已实现。
- Job Match / Polish / Report / Review / Weakness / Asset / Training graph 已迁移。
- security/privacy、runtime、provider、redaction、raw-off 和 owner boundary 已通过发布级验收。

主 Agent 应在后续受权 PR 中把该说明同步到 `BACKLOG.md` 或后续 AIFI 任务，避免 DONE 被误读为 implementation complete。

### 5.6 Archive 规则

本专题包不移动 archive 文件。若后续任何文件下线，必须登记 `archive/MANIFEST.md`，并说明原路径、归档路径、原因、替代路径、状态和阻断条件。

## 6. 与 active docs 的关系

专题包只能作为 staging evidence。active docs 回写后才是执行依据；不得引用 `docs/tmp` 或本目录绕过 active docs。

## 7. 非目标

- 不把 `docs/tmp` 迁为 canonical。
- 不创建 roadmap-v2。
- 不把 archive/review docs 当当前事实。
- 不在 PR1 修改 `docs/02-design/**`。

## 8. 后续 PR 使用方式

PR2-PR8 在实现证据稳定后最小回写 active docs。每次回写必须说明：来源、目标 active doc、变更事实、验证命令、是否需要 ADR。

## 9. Definition of Done

- 回写矩阵覆盖用户指定 active docs。
- 明确哪些留在专题包、哪些回写 active docs。
- archive 规则明确。
- 专题包不成为并行事实源。
