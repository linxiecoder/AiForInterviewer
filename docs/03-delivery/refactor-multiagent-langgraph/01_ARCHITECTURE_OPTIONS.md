---
title: LangGraph MultiAgent 架构方案比较
type: delivery-planning
status: draft-pr1
owner: 项目交付
permalink: ai-for-interviewer/docs/03-delivery/refactor-multiagent-langgraph/architecture-options
---

# LangGraph MultiAgent 架构方案比较

## 1. 文档目的

本文比较 LangGraph MultiAgent 重构的 Option A / B / C，明确为什么 PR1 推荐 Option C，并给后续 PR2-PR8 提供可追踪的架构决策输入。

## 2. 输入来源

- `docs/tmp/CODEX_LANGGRAPH_MULTIAGENT_README.md`
- `docs/tmp/CODEX_LANGGRAPH_AI_NON_AI_BOUNDARY.md`
- active design docs：`APPLICATION_FLOW_SPEC.md`、`PERSISTENCE_MODEL.md`、`DATA_MODEL.md`、`PROMPT_SPEC.md`、`SCORING_SPEC.md`、`SECURITY_PRIVACY.md`、`API_SPEC.md`
- `docs/03-delivery/BACKLOG.md`
- `docs/03-delivery/DELIVERY_PLAN.md`

## 3. 当前状态

当前系统已有 Core Business、AI task、Prompt contract、trace/evidence、candidate/formal object、security/privacy 和 frontend UX 的 active 设计基础，但还没有独立的 LangGraph Agent Runtime 层、checkpoint ref 表、agent timeline API 或统一 interrupt/resume 模型。

## 4. 目标输出

输出三种方案比较：

- Option A：在现有 LLM service 内局部接入 LangGraph。
- Option B：抽出部分 agent runtime，但保留业务 service 与 graph 交织。
- Option C：LangGraph-first Agentic Workflow Runtime，单微服务双域架构。

## 5. 必须覆盖范围

### 5.0 架构选择硬条件

以下条件不是评分偏好，而是进入 PR2-PR8 主干前必须满足的硬门槛：

| 硬条件 | 要求 | 违反后处理 |
|---|---|---|
| 单微服务双域 | 保持一个后端服务，但 Core Business Domain 与 AI Agentic Workflow Domain 必须分层 | 停止对应实现，回到架构文档和 ADR 修正 |
| Core 不依赖 LangGraph | Core UseCase、domain、repository、DB model 不得 import LangGraph、AgentState、graph node 或 checkpoint schema | 不能进入主干；必须先拆 facade / port |
| Facade 唯一入口 | Core UseCase 只能通过 `AiOrchestrationFacade` 或等价 application port 触达 AI Runtime | 禁止直接调用 graph runner、node、checkpointer |
| Checkpoint 非事实源 | LangGraph checkpoint 只用于 resume / replay / debug，不作为 business read model 或 formal object source | 删除 business read path，改用 Core tables / AI Runtime refs |
| Raw-off payload | raw prompt、raw completion、provider request / response payload 默认不保存、不入日志、不入 checkpoint、不入 API response | 阻断 PR；先补 redaction / schema / tests |
| Candidate/formal 边界 | AI node 只能产出 candidate / suggestion / validation / trace；formal object 由 Core command、用户确认或显式业务动作写入 | 禁止自动 formal write；补 confirmation/audit |
| Active docs 优先 | 本专题和 `docs/tmp` 不替代 `docs/02-design/*`、`BACKLOG.md`、`DOCS_INDEX.md` 或 ADR | 冲突时以 active docs / ADR 为准，并回写专题包 |

### 5.1 Option A：局部最小接入

| 项 | 内容 |
|---|---|
| 方案定位 | 在现有 LLM service 或 use case 中嵌入 LangGraph，尽量少改目录 |
| 架构路径 | `Core UseCase -> Existing LLM Service -> LangGraph subflow` |
| 后端模块边界 | 现有 `application/*` 与 LangGraph import 混合 |
| 前端模块边界 | 维持现有页面状态，最多增加 task status |
| 数据流路径 | 业务 API 直接触发 service，service 内部保存业务结果 |
| Graph runtime 与业务 service 边界 | 边界弱，容易让业务 service 依赖 graph state |
| LLM transport 与 LangGraph 边界 | transport 可能被 graph node 直接调用 |
| 持久化边界 | checkpoint、trace、business write 易混杂 |
| 测试边界 | 单测容易依赖 graph internals |
| 优点 | 初期 diff 小 |
| 缺点 | 长期腐化风险高，candidate/formal 和 raw payload 边界难守 |
| 迁移成本 | 初期低，后期高 |
| 可维护性 | 低 |
| 可观测性 | 弱 |
| 风险 | checkpoint 被误当业务事实源；Core import LangGraph |
| 推荐度 | 不推荐 |
| 不推荐条件 | 有多 graph、interrupt/resume、trace、candidate closure 和 frontend timeline 需求时不适合 |

Option A 禁止进入主干的条件：

1. 任何 Core UseCase、repository、domain model 或 API schema 需要 import LangGraph、AgentState、checkpoint schema 或 graph node。
2. 任何业务读取路径需要从 checkpoint payload、raw completion 或 provider payload 组装用户可见结果。
3. 任何 LLM node、旧 LLM service 或 runtime helper 可以直接写 `Weakness`、`Asset`、`AssetVersion`、`TrainingRecommendation`、`TrainingTask` 或正式 `ScoreResult`，且缺少 `UserConfirmationRef` / explicit Core command。
4. 任何日志、trace、checkpoint、API response 或 frontend state 出现 raw prompt、raw completion、provider request / response payload。
5. PR2-PR4 需要同时引入 runtime 表、checkpoint、timeline、interrupt/resume，而 Option A 不能提供可测试边界。

### 5.2 Option B：半分层 Agent Runtime

| 项 | 内容 |
|---|---|
| 方案定位 | 抽出部分 runtime service，但业务 use case 仍可能感知 graph 名称和 state |
| 架构路径 | `Core UseCase -> Agent Runtime Service -> LangGraph Adapter` |
| 后端模块边界 | 新增 `application/agents`，但旧 LLM service 与 graph 仍交织 |
| 前端模块边界 | 增加 timeline / interrupt，但 API 字段可能跟 graph 绑定 |
| 数据流路径 | runtime 与业务表共享写入路径 |
| Graph runtime 与业务 service 边界 | 中等，需靠约束防止泄漏 |
| LLM transport 与 LangGraph 边界 | 可统一 transport，但 node 仍可能绕过 policy |
| 持久化边界 | 可规划 runtime 表，但 checkpoint ref 和 business write 仍需强审查 |
| 测试边界 | 可做 runtime tests，但业务 graph tests 仍耦合 |
| 优点 | 比 Option A 清晰，迁移成本低于 C |
| 缺点 | 容易形成双重入口和历史 service 尾巴 |
| 迁移成本 | 中 |
| 可维护性 | 中 |
| 可观测性 | 中 |
| 风险 | facade 不唯一，旧 service 与 graph 并行 |
| 推荐度 | 条件推荐，但不作为本轮目标 |
| 不推荐条件 | 需要长期维护多 graph、replay/resume 和跨端 runtime UI 时不够彻底 |

Option B fallback 条件：

| 条件 | 允许 fallback 到 Option B 的范围 | 禁止事项 |
|---|---|---|
| PR2 发现现有 schema / bootstrap 无法一次性承载完整 AI Runtime tables | 可先落 `AiTask`、`agent_runs`、`agent_node_runs`、`llm_calls`、`agent_checkpoint_refs` 的最小子集 | 不得让 Core 直接依赖 LangGraph 或 checkpoint payload |
| PR3 Facade 改造受旧 UseCase 阻塞 | 可保留 legacy LLM service 作为 facade 后的 adapter wrapper | 不得出现 Core -> graph/node/checkpointer 直连 |
| PR4 LangGraph adapter 或 checkpointer 选型风险未关闭 | 可用 fake graph / in-memory adapter 验证 runner contract | 不得把 fake adapter 的 state 当业务事实源 |
| PR5-PR8 单个业务 graph 暂不迁移 | 可让该业务链路继续走 legacy provider path | 不得放宽 raw-off、candidate/formal、owner 和 trace redaction 规则 |

Option B 只能作为阶段性降级实现，不得成为隐式长期架构。若 fallback 超过一个 PR，必须由主 Agent 更新 BACKLOG / active docs，并在 ADR-0005 或后续 ADR 中登记降级范围、截止 PR 和退出条件。

### 5.3 Option C：LangGraph-first Agentic Workflow Runtime

| 项 | 内容 |
|---|---|
| 方案定位 | 在单微服务内建立 Core Business / AI Runtime 双域，所有 graph 经 facade/runner 进入 |
| 架构路径 | `Core UseCase -> AiOrchestrationFacade -> AgentGraphRunner -> LangGraphAgentRunner` |
| 后端模块边界 | `application/ai`、`application/agents`、`infrastructure/agent_runtime` 分层 |
| 前端模块边界 | Core UI 与 AI Runtime UI 分离：task status、timeline、interrupt、candidate confirmation |
| 数据流路径 | Core API 创建 task/ref，AI Runtime 写 runtime trace，通过 handoff 写业务结果 |
| Graph runtime 与业务 service 边界 | 强，Core 不 import LangGraph |
| LLM transport 与 LangGraph 边界 | 统一 `PersistedLlmTransport` 与 `LlmTraceContext` |
| 持久化边界 | Core Business Tables / AI Runtime Tables / LangGraph Checkpoint Tables 三分 |
| 测试边界 | 可做 facade contract、fake graph、redaction、checkpoint ref、business handoff tests |
| 优点 | 架构清晰、可演进、可观测、可 replay/resume |
| 缺点 | PR2-PR4 初始规划和测试成本更高 |
| 迁移成本 | 中高，但可拆 PR1-PR8 |
| 可维护性 | 高 |
| 可观测性 | 高 |
| 风险 | 过度一次性迁移会扩大 diff；需严格 PR 顺序 |
| 推荐度 | 推荐 |
| 不推荐条件 | 如果只有单次简单 LLM call 且无 trace/resume/candidate closure，Option C 可能过重 |

Option C 前置条件：

1. PR2 先落 runtime data / trace / checkpoint ref / rollback 基础，不迁移业务 graph。
2. PR3 再落 `AiOrchestrationFacade`、`AgentGraphRunner` port 和 command/result contract，保持 Core -> facade -> port 的依赖方向。
3. PR4 才允许引入 concrete `LangGraphAgentRunner`、fake graph、checkpointer、interrupt/resume 和 timeline API。
4. PR5-PR8 逐 graph 迁移，每个 graph 必须先有 contract mapping、source bundle、validation、candidate/formal handoff 和 raw-off tests。
5. `SECURITY_PRIVACY.md`、`API_SPEC.md`、`DATA_MODEL.md`、`PERSISTENCE_MODEL.md` 中涉及 raw-off、checkpoint、timeline、retention、debug/admin visibility 的事实必须按 `16_DESIGN_DOCS_REFACTOR_PLAN.md` 回写。
6. ADR-0005 至少保持 `proposed` 且未被主 Agent 标记为 rejected；若 ADR 被拒绝，PR2 不得以 Option C 名义落 runtime 主干。

### 5.4 权重和得分决策矩阵

评分使用 1-5 分，5 表示最符合当前 AIFI-BE-002 后续 PR 目标；权重合计 100。

| 维度 | 权重 | Option A | Option B | Option C | 评分理由 |
|---|---:|---:|---:|---:|---|
| 架构清晰度 | 15 | 1 | 3 | 5 | Option C 明确 Core / AI Runtime / infrastructure 分层 |
| Core 不依赖 LangGraph 可验证性 | 12 | 1 | 3 | 5 | Option A 依赖泄漏风险最高；Option C 可用 import boundary tests |
| Checkpoint 非事实源边界 | 10 | 1 | 3 | 5 | Option C 把 checkpoint refs 与 Core tables 分离 |
| Raw-off payload 安全性 | 10 | 2 | 3 | 5 | Option C 可集中到 transport / trace bridge / API schema 验证 |
| Candidate/formal handoff | 10 | 2 | 3 | 5 | Option C 强制 handoff 到 Core command 和 confirmation |
| replay / resume / interrupt 能力 | 10 | 1 | 3 | 5 | Option C 原生支持 runtime event 与 checkpoint ref |
| 可观测性和 timeline | 8 | 1 | 3 | 5 | Option C 可形成 agent run / node run / sanitized timeline |
| PR 拆分可控性 | 8 | 2 | 3 | 4 | Option C 初始成本高，但 PR2-PR8 可拆 |
| 迁移成本 | 7 | 5 | 3 | 2 | Option A 初期成本最低；Option C 成本最高 |
| 前端/API 稳定性 | 5 | 2 | 3 | 4 | Option C 可隔离 Core API 和 Runtime API |
| 长期演进能力 | 5 | 1 | 3 | 5 | 多 graph / report / review / training 场景需要长期 runtime |
| 加权总分 | 100 | 181 | 300 | 468 | Option C 胜出 |

得分计算：`权重 * 分值` 后求和；满分 500。Option C 虽有 PR2-PR4 初始成本，但在 boundary、security、runtime observability、candidate/formal 和 replay/resume 上满足硬条件，因此作为 PR1.5 推荐主线。

### 5.5 决策结论

PR1.5 推荐 Option C 作为后续 PR 主线，并允许 Option B 作为显式登记的阶段性 fallback。Option A 不允许进入主干；它只能作为反例或 legacy path 清理对象。Option C 的长期架构状态由 ADR-0005 以 `proposed` 形式记录，后续若主 Agent 或架构评审接受，应再同步 `DOCS_INDEX.md` 并回写 active docs。

## 6. 与 active docs 的关系

本文只比较方案，不替代 active technical design。Option C 若后续被长期采纳，必须通过 `16_DESIGN_DOCS_REFACTOR_PLAN.md` 回写 active docs；若需要 ADR，必须另行受权创建。

## 7. 非目标

- 不选择具体 LangGraph checkpointer 存储实现。
- 不写目录、代码、migration 或测试。
- 不改变 active API / DATA / PROMPT / SECURITY 文档。
- 不证明真实 provider 输出质量。

## 8. 后续 PR 使用方式

- PR2-PR4 按 Option C 建立 runtime 骨架。
- PR5-PR8 按 Option C 逐 graph 接入，禁止回退到 Option A 的 direct import 模式。
- 若后续发现 Option C 某部分过重，只能在 active docs 中登记降级决策，不能隐式实现 Option A。

## 9. Definition of Done

- Option A / B / C 均已覆盖定位、架构路径、模块边界、数据流路径、边界、优缺点、成本、风险和推荐度。
- 决策矩阵覆盖用户指定维度。
- 推荐 Option C 且说明不推荐条件。
- 明确本文不是 active canonical docs。
