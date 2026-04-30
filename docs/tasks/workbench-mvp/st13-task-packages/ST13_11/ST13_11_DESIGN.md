---
title: ST13_11_DESIGN
type: note
permalink: ai-for-interviewer/docs/tasks/workbench-mvp/st13-task-packages/st13-11/st13-11-design
---

# 子任务设计文档

## 1. 文档定位

- 本文档定义 `ST13_11` 真实 LLM provider / adapter 的 R0 provider 边界。
- 本文档只冻结 provider 设计输入，不授权业务代码实现。
- 本文档不替代 `docs/governance/DOC_STATE.yaml`、implementation packet 或后续 implementation window。

## 2. 基本信息与关联

- 子任务 ID：`ST13_11`
- 子任务名称：真实 LLM provider / adapter
- 所属 requirement：`RQ01`
- 所属模块：`M04`
- 上游需求事实源：`docs/requirements/workbench-mvp/**`
- 上游设计事实源：`docs/design/workbench-mvp/**`
- 对应官方状态条目：`docs/governance/DOC_STATE.yaml -> subtasks.ST13_11`

## 3. 子任务目标

- 为真实 R0 提供可插拔 LLM provider boundary。
- 支持真实 provider 配置，但测试不得依赖真实 API key 或外部网络。
- 支持 deterministic provider 仅用于 test / dev。
- 明确禁止把 deterministic provider 的成功冒充为真实 LLM 成功。
- 为后续 start interview、generate question、submit answer、next turn、review、score 和 Markdown export 提供统一生成入口。

## 4. 范围边界

### 4.1 本任务覆盖

- provider interface。
- request / result model。
- provider config。
- real provider adapter boundary。
- deterministic test provider。
- provider error mapping。
- provider tests。

### 4.2 本任务不覆盖

- interview main flow routes / services。
- scoring / review / Markdown export business。
- full RAG。
- prompt platform。
- full DB migration / ORM / repository。
- frontend。

## 5. 技术方案

### 5.1 Provider 抽象

- 定义最小 `LLMProvider.generate(request)` 抽象。
- request 至少表达 purpose、job、resume、history、last_answer 和 metadata。
- result 至少表达 provider、model、content、finish_reason、usage 和 metadata。
- metadata 至少承载 request_id、session_id、turn_index 和 prompt_version。

### 5.2 真实 provider 边界

- 真实 provider 通过环境配置选择。
- R0 provider 实现必须允许在测试中 mock transport / client，不直接调用外部网络。
- 缺少真实 provider 配置时返回稳定错误，不允许静默 fallback 到 deterministic provider。

### 5.3 Deterministic provider 边界

- deterministic provider 仅用于 test / dev 显式配置。
- deterministic provider 输出必须稳定、可断言。
- deterministic provider 的 response metadata 必须明确标记 provider=deterministic。

### 5.4 错误映射

- provider 缺配置、非法 provider 名称、超时、client failure 和 provider unavailable 必须映射到稳定错误码。
- 错误 envelope 必须能被 API 边界复用，并包含 request_id。

## 6. 对上下游的影响

- 上游复用 `ST13_21` 的最小 API service boundary 与 error envelope 基础。
- 下游 `R0-Final-03` 只能在 provider gate 和 packet 就绪后接入 interview main flow。
- 本任务不改变 `ST13_20` 的 persistence contract。
- 本任务不代表 R0 主链路完成。

## 7. 设计约束

- provider 层必须可独立测试。
- 测试中不得读取真实 secret。
- 测试中不得访问真实外部网络。
- provider fallback 不得掩盖配置错误或真实 provider failure。
- 任何 main flow、scoring、review、export、RAG 或 DB 扩展都必须留给后续窗口。