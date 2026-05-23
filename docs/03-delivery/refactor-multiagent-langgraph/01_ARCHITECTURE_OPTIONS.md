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

### 5.1 Option A：局部最小接入

| 项 | 内容 |
|---|---|
| 方案定位 | 在现有 LLM service 或 use case 中嵌入 LangGraph，尽量少改目录 |
| 架构图占位 | `Core UseCase -> Existing LLM Service -> LangGraph subflow` |
| 后端模块图占位 | 现有 `application/*` 与 LangGraph import 混合 |
| 前端模块图占位 | 维持现有页面状态，最多增加 task status |
| 数据流图占位 | 业务 API 直接触发 service，service 内部保存业务结果 |
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

### 5.2 Option B：半分层 Agent Runtime

| 项 | 内容 |
|---|---|
| 方案定位 | 抽出部分 runtime service，但业务 use case 仍可能感知 graph 名称和 state |
| 架构图占位 | `Core UseCase -> Agent Runtime Service -> LangGraph Adapter` |
| 后端模块图占位 | 新增 `application/agents`，但旧 LLM service 与 graph 仍交织 |
| 前端模块图占位 | 增加 timeline / interrupt，但 API 字段可能跟 graph 绑定 |
| 数据流图占位 | runtime 与业务表共享写入路径 |
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

### 5.3 Option C：LangGraph-first Agentic Workflow Runtime

| 项 | 内容 |
|---|---|
| 方案定位 | 在单微服务内建立 Core Business / AI Runtime 双域，所有 graph 经 facade/runner 进入 |
| 架构图占位 | `Core UseCase -> AiOrchestrationFacade -> AgentGraphRunner -> LangGraphAgentRunner` |
| 后端模块图占位 | `application/ai`、`application/agents`、`infrastructure/agent_runtime` 分层 |
| 前端模块图占位 | Core UI 与 AI Runtime UI 分离：task status、timeline、interrupt、candidate confirmation |
| 数据流图占位 | Core API 创建 task/ref，AI Runtime 写 runtime trace，通过 handoff 写业务结果 |
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

### 5.4 决策矩阵

| 维度 | Option A | Option B | Option C |
|---|---:|---:|---:|
| 架构清晰度 | 1 | 3 | 5 |
| 长期演进能力 | 1 | 3 | 5 |
| 代码腐化风险 | 高 | 中 | 低 |
| 对当前代码冲击 | 低 | 中 | 中高 |
| 测试复杂度 | 初期低、后期高 | 中 | 初期高、后期可控 |
| 数据迁移复杂度 | 低但边界弱 | 中 | 中高但边界清晰 |
| 可观测性 | 低 | 中 | 高 |
| replay / resume 能力 | 弱 | 中 | 强 |
| human-in-the-loop 能力 | 弱 | 中 | 强 |
| 前端改造成本 | 低 | 中 | 中高 |
| 交付风险 | 后期高 | 中 | 可拆分控制 |

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

- Option A / B / C 均已覆盖定位、图占位、边界、优缺点、成本、风险和推荐度。
- 决策矩阵覆盖用户指定维度。
- 推荐 Option C 且说明不推荐条件。
- 明确本文不是 active canonical docs。

