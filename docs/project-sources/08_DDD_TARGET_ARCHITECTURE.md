---
title: 08_DDD_TARGET_ARCHITECTURE
type: note
permalink: ai-for-interviewer/docs/project-sources/08-ddd-target-architecture
---

# 08 DDD Target Architecture

## 目标

建立项目级 DDD 分层架构，并以 Polish 作为第一条纵切面进行 facade 收敛。

Phase 1 是 DDD 起点，但不是一次性全项目 DDD 代码迁移。

## 核心决策

### DEC-DDD-001 Phase 1 Definition

Status: confirmed

Phase 1 定义为：

DDD Rails + Agent Platform C0 + Polish Facade Convergence

含义：

- 项目级 DDD rails 必须确立。
- Agent Platform C0 skeleton 必须确立。
- PolishUseCases facade 必须开始收敛。
- 不做全仓库一次性 DDD 大迁移。
- 不改 prompt / provider / DB / API 行为。
- 不迁 Question / Feedback domain policy。

## Layers

### API Adapter

职责：

- HTTP request / response
- auth
- status code
- response filtering
- route-level DTO mapping

禁止：

- 复杂业务规则
- prompt/provider 逻辑
- DB 细节
- Domain Policy 实现
- Agent planning

### Application Services

职责：

- command/query
- repository port
- context service
- domain policy 调用
- agent executor 调用
- transaction
- DTO orchestration
- handoff coordination

禁止：

- prompt/provider 细节
- 复杂 domain policy
- LLM transport 直接调用
- DB implementation 细节
- business invariant 内联膨胀

### Domain

职责：

- entities
- value objects
- policies
- state rules
- business invariants

禁止：

- DB
- LLM
- FastAPI
- infrastructure
- provider SDK
- prompt rendering

### Agent Layer

职责：

- contracts
- definitions
- skills
- tools
- planners
- executors
- candidate outputs
- trace
- handoff contracts

禁止：

- formal business write
- repository direct access
- provider SDK direct coupling without boundary
- hidden side effects

### Provider Boundary

职责：

- prompt builder
- compact request
- parser
- redaction
- fail-closed
- schema validation

禁止：

- 业务不变量决策
- 正式事实写入
- full prompt asset fallback
- raw model IO persistence

### Infrastructure

职责：

- DB
- LLM transport
- LangGraph runtime
- embedding
- RAG
- replay
- observability

禁止：

- business policy
- candidate/formal decision
- domain invariant

### Eval

职责：

- datasets
- graders
- runners
- reports
- regression gates
- CI gate

禁止：

- runtime fake 污染生产路径
- 只验证 fake 行为后宣称 AI 质量已通过

## Target Directory

目标目录：

```text
apps/api/app/domain/polish/policies/
apps/api/app/application/agents/contracts/
apps/api/app/application/agents/definitions/
apps/api/app/application/agents/registry/
apps/api/app/application/agents/runtime/
apps/api/app/application/agents/handoff/
apps/api/app/application/agents/eval/
apps/api/app/application/polish/services/
apps/api/app/application/polish/context/
apps/api/app/application/polish/agents/question/
apps/api/app/application/polish/agents/feedback/
apps/api/app/application/ai_provider/
apps/api/app/infrastructure/llm/
apps/api/app/infrastructure/ai_runtime/
apps/api/app/infrastructure/db/
tests/architecture/
tests/evals/
tests/fakes/
```

## Boundary Rules

### Domain Boundary

Domain 不依赖：

- infrastructure
- api
- FastAPI
- DB
- LLM
- provider
- application.llm
- prompt builder

### Application Boundary

Application Service 可依赖：

- domain policies
- repository ports
- context services
- agent executor ports
- DTOs

Application Service 不得包含：

- prompt/provider 细节
- 复杂 domain policy
- direct LLM transport
- DB implementation

### Agent Boundary

Agent 可产出：

- candidate
- suggestion
- validation result
- plan
- trace

Agent 不得：

- 写正式状态
- 直接更新资产
- 直接确认 progress
- 直接确认 score
- 绕过 Application Service

### Provider Boundary

Provider request 必须：

- compact
- schema-bound
- redacted
- fail-closed
- traceable

Provider request 禁止：

- raw prompt fallback
- full prompt asset fallback
- full resume
- full JD
- full asset body
- provider payload echo
- secrets

### Infrastructure Boundary

Infrastructure 不承载 business policy。

允许：

- transport
- persistence
- runtime implementation
- logging
- replay storage
- checkpointer

不允许：

- source support decision
- asset conflict decision
- next action decision
- score range policy
- formal write decision

## Phase 1 Scope Lock

Phase 1 第一窗口必须限制为：

- Project-level DDD rails
- Agent Platform C0 skeleton
- PolishUseCases facade convergence
- boundary tests
- no behavior change unless explicitly approved

Phase 1 不是：

- 全仓库 DDD 一次性迁移
- Question / Feedback policy migration
- provider request refactor
- prompt rewrite
- DB schema migration
- LangGraph full runtime migration

## Done Criteria for DDD Capability

DDD capability 只有同时满足以下条件，才能标记 done：

- 设计更新
- 代码迁移
- 旧位置不再承载职责
- 单测
- 必要 eval
- 验证运行
- 无 forbidden scope 修改
- Project source 回填

文件移动但职责未迁移，不得标记 done。