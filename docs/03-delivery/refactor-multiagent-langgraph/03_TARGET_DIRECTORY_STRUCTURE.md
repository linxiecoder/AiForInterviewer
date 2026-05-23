---
title: 目标目录结构与模块边界
type: delivery-planning
status: draft-pr1
owner: 项目交付
permalink: ai-for-interviewer/docs/03-delivery/refactor-multiagent-langgraph/target-directory-structure
---

# 目标目录结构与模块边界

## 1. 文档目的

本文冻结 LangGraph MultiAgent 重构的目标目录结构、模块职责、import 规则、architecture boundary test 规则和前后端双域边界。它只规划目录和边界，不创建代码目录、不修改业务代码、不安装依赖。

PR1.5 的 implementation-ready 判定标准是：后续 PR2-PR8 可以直接按本文创建文件、写测试和做 import scan，不需要再讨论 LangGraph 应放在哪一层。

## 2. 输入来源

- `docs/tmp/CODEX_LANGGRAPH_AI_NON_AI_BOUNDARY.md`
- `02_RECOMMENDED_ARCHITECTURE.md`
- `04_BACKEND_AGENT_RUNTIME_PLAN.md`
- active docs：`APPLICATION_FLOW_SPEC.md`、`PERSISTENCE_MODEL.md`、`DATA_MODEL.md`、`API_SPEC.md`、`SECURITY_PRIVACY.md`
- 当前代码映射：`apps/api/app/application/llm/types.py`、`ports.py`、`apps/api/app/infrastructure/llm/runtime.py`、`openai_compatible.py`、`fake_transport.py`、`job_match.py`
- 当前 boundary test：`tests/api/test_architecture_boundaries.py`

## 3. 当前状态

当前后端已有 application / infrastructure 分层、`application/llm` port、`infrastructure/llm` fake / OpenAI-compatible transport 和 AST import boundary test。当前代码没有 LangGraph 依赖。PR1.5 只冻结未来 LangGraph 依赖进入位置：**唯一允许直接 import LangGraph / LangChain graph runtime API 的目录是 `apps/api/app/infrastructure/agent_runtime/langgraph/**`**。

当前前端已有 `entities`、`features`、`widgets`、`pages`、`shared` 分层。PR1.5 只冻结 Core UI 与 AI Runtime UI 的目录边界，不新增前端代码。

## 4. Scope Lock

| 项 | 冻结值 |
|---|---|
| task_id | `AIFI-BE-002` 的 PR1 planning package refinement |
| allowed write files | `03_TARGET_DIRECTORY_STRUCTURE.md`、`04_BACKEND_AGENT_RUNTIME_PLAN.md`、`18_LANGGRAPH_DEPENDENCY_AND_SPIKE_PLAN.md` |
| forbidden writes | `apps/**`、`tests/**`、依赖文件、migration、CI、其他 docs |
| implementation target | PR2-PR8 |
| non-goal | 不实现 LangGraph graph，不安装依赖，不调用 provider，不 commit / push |

## 5. 后端目标目录骨架

### 5.1 唯一 LangGraph import 目录

| 目录 / 文件 | 职责 | 允许依赖 | 禁止依赖 | 域 | 测试位置 | PR |
|---|---|---|---|---|---|---|
| `apps/api/app/infrastructure/agent_runtime/langgraph/**` | LangGraph concrete adapter、graph compile / invoke / stream、checkpointer factory、serializer factory、interrupt / resume adapter、checkpoint ref extraction | `langgraph`、`langgraph-checkpoint-postgres`、LangChain core abstractions、`application/agents` contracts、runtime repositories | Core Business service、Core formal write command bypass、API response schema direct write | AI Runtime infrastructure adapter | `tests/api/test_langgraph_checkpointer_factory.py`、`tests/api/test_agent_runtime_fake_graph.py`、`tests/api/test_architecture_boundaries.py` | PR4 |
| `apps/api/app/infrastructure/agent_runtime/langgraph/runner.py` | `LangGraphAgentRunner` concrete implementation | LangGraph compiled graph API、`AgentGraphRunner` port DTO、trace bridge contract、checkpointer factory | Business use case internals、frontend schema、raw provider payload persistence | AI Runtime infrastructure adapter | fake graph start/resume/replay/timeline tests | PR4 |
| `apps/api/app/infrastructure/agent_runtime/langgraph/checkpointer_factory.py` | production / test checkpointer construction and namespace policy | LangGraph checkpoint APIs、Postgres checkpointer when PR4 chooses PG backend、encrypted serializer factory | Core Business tables as checkpoint truth source | AI Runtime infrastructure adapter | checkpointer factory and encrypted serializer tests | PR4 |
| `apps/api/app/infrastructure/agent_runtime/langgraph/serializer.py` | checkpoint serializer selection and `LANGGRAPH_AES_KEY` validation | LangGraph serializer API、secret provider abstraction | logging key material、saving plaintext raw prompt/completion | AI Runtime infrastructure adapter | serializer key validation tests | PR4 |

**Import freeze:** no other backend path may directly import modules whose top-level package starts with `langgraph`, `langchain`, `langchain_core` or `langchain_openai`, except `langchain_core` DTO / message abstractions if PR4 explicitly freezes a narrower allowlist in `18_LANGGRAPH_DEPENDENCY_AND_SPIKE_PLAN.md` and adds AST tests for that allowlist. PR1.5 default is stricter: application layer defines project-owned DTOs and ports, not LangChain DTOs.

### 5.2 Application AI Runtime boundary

| 目录 / 文件 | 职责 | 允许依赖 | 禁止依赖 | 域 | 测试位置 | PR |
|---|---|---|---|---|---|---|
| `apps/api/app/application/ai/orchestration_facade.py` | Core UseCase 与 AI Runtime 的唯一交界面；创建 / 复用 `AiTask` 与 `AgentRunContext`；调用 `AgentGraphRunner` port | Core command DTO、owner-checked refs、`application/agents` contracts、AI task repository port | LangGraph concrete adapter、checkpointer API、provider raw payload、formal object direct write | AI Runtime application boundary | `tests/api/test_ai_orchestration_facade.py` | PR3 |
| `apps/api/app/application/agents/contracts.py` | `AgentGraphRunner` port、runtime DTO、error types、status enums | project-owned DTO、`application/llm` port types by reference | LangGraph / LangChain imports、SQLAlchemy、FastAPI | AI Runtime application contract | `tests/api/test_agent_contracts.py` | PR3 |
| `apps/api/app/application/agents/state.py` | project-owned serializable graph state schema；只保存 refs / summaries / flags / validation status | project-owned refs、safe summary DTO | full resume / answer body by default、raw prompt、raw completion、provider payload、checkpoint table schema | AI Runtime application DTO | serialization / redaction tests | PR3 |
| `apps/api/app/application/agents/registry.py` | `AgentGraphRegistry`：task type -> graph key / contract ids / prompt schema / feature flag / PR owner 映射 | project-owned graph descriptor DTO | LangGraph compiled graph object、infrastructure adapter instance | AI Runtime application service | registry tests | PR3 |
| `apps/api/app/application/agents/trace_bridge.py` | `AgentTraceBridge` application contract；定义 run / node / LLM / validation / interrupt / checkpoint ref 事件写入接口 | runtime DTO、trace repository port interface | SQLAlchemy concrete session、LangGraph checkpoint object、raw payload | AI Runtime application contract | trace bridge contract tests | PR3 |
| `apps/api/app/application/agents/side_effect_guard.py` | `AgentSideEffectGuard`：节点副作用白名单、raw-off、formal-write 阻断 | graph descriptor、node intent DTO、policy config | direct DB writes、provider client | AI Runtime application policy | side effect policy tests | PR3 |
| `apps/api/app/application/agents/persistence_handoff.py` | `AgentPersistenceHandoff`：AI result -> Core command handoff contract | validated result DTO、candidate refs、Core command ports | formal object write without confirmation、checkpoint payload | AI Runtime / Core handoff contract | handoff contract tests | PR3-PR4 |
| `apps/api/app/application/agents/interrupts.py` | `AgentInterruptService` application contract：interrupt create/read/resume validation | owner-checked run refs、resume schema DTO、audit port | LangGraph interrupt object leak、raw AgentState display | AI Runtime application service | interrupt contract tests | PR3-PR4 |
| `apps/api/app/application/agents/langgraph_adapters/**` | **保留但只允许放 application 层 factory contract / DTO / adapter descriptor**；用于描述“需要一个 LangGraph adapter”，不承载 concrete LangGraph code | `AgentGraphRunner` port、registry descriptor、project DTO | `import langgraph`、`import langchain*`、compiled graph object、checkpointer factory implementation | AI Runtime application boundary | adapter descriptor import tests | PR3 |

`application/agents/langgraph_adapters/**` 的保留结论：**保留为 contract / DTO 目录，不直接 import LangGraph**。若 PR3 发现该目录只会增加噪声，则 PR3 可删除该目录规划并把 descriptor 合并进 `application/agents/contracts.py`；该调整必须只发生在 PR3，且同步更新 `tests/api/test_architecture_boundaries.py::test_only_infrastructure_langgraph_adapter_imports_langgraph`。

### 5.3 Core Business 与 DB 边界

| 目录 / 文件 | 职责 | 允许依赖 | 禁止依赖 | 域 | 测试位置 | PR |
|---|---|---|---|---|---|---|
| `apps/api/app/domain/**` | 纯领域对象、业务状态、值对象 | standard library、project domain shared | LangGraph、LangChain、AgentGraphState、infrastructure、FastAPI、SQLAlchemy | Core Business | existing boundary tests | PR2-PR8 |
| `apps/api/app/application/{auth,resumes,jobs,bindings,interviews,reports,reviews,assets,weaknesses,training,scoring,polish}/**` | Core use cases；只处理 owner / command / formal object / candidate confirmation | Core repositories ports、`AiOrchestrationFacade` contract where generation is needed | LangGraph、LangChain、graph node、checkpointer、AgentGraphState、provider client | Core Business application | boundary + use case tests | PR3-PR8 |
| `apps/api/app/infrastructure/db/models/**` | ORM / DB model | SQLAlchemy、domain enums | LangGraph、LangChain、AgentGraphState、checkpoint payload object | shared DB infrastructure | AST boundary tests | PR2 |
| `apps/api/app/infrastructure/db/repositories/agent_run.py` | write / read `agent_runs`、`agent_node_runs`、`agent_interrupts`、`agent_checkpoint_refs` | SQLAlchemy、runtime models、project DTO | LangGraph object, Core formal write bypass | AI Runtime repository | repository tests | PR2-PR4 |
| `apps/api/app/infrastructure/db/repositories/llm_call.py` | write / read sanitized LLM call summary and payload policy refs | SQLAlchemy、LLM runtime models、redaction policy | raw prompt / raw completion default-on、API response DTO | AI Runtime repository | redaction repository tests | PR2-PR4 |
| `apps/api/app/infrastructure/db/repositories/*business*.py` | Core Business persistence | SQLAlchemy、business models | LangGraph、AgentGraphState、checkpoint schema | Core Business repository | AST boundary tests | PR2-PR8 |

Core Business、Repository 和 DB Model 禁止依赖 LangGraph 的可执行规则：

```text
Forbidden import prefixes outside apps/api/app/infrastructure/agent_runtime/langgraph/**:
- langgraph
- langchain
- langchain_core
- langchain_openai

Forbidden project imports for Core Business paths:
- app.application.agents.state.AgentGraphState
- app.application.agents.nodes
- app.application.agents.graphs
- app.infrastructure.agent_runtime.langgraph
```

### 5.4 LLM runtime 与 Agent runtime 边界

| 目录 / 文件 | 职责 | 允许依赖 | 禁止依赖 | 域 | 测试位置 | PR |
|---|---|---|---|---|---|---|
| `apps/api/app/application/llm/types.py` | LLM transport request/result DTO，当前已存在 | project enums、safe refs / evidence bundle | LangGraph state、provider response body | application LLM contract | existing / new LLM tests | PR2-PR4 |
| `apps/api/app/application/llm/ports.py` | `LlmTransport` protocol，当前已存在 | project DTO | provider concrete SDK、LangGraph | application LLM contract | existing / new LLM tests | PR2-PR4 |
| `apps/api/app/infrastructure/llm/persisted_transport.py` | wrapper：调用 existing transport，写 sanitized trace / usage / validation | lower `LlmTransport`、sanitizer、trace repository | raw prompt / completion default-on、formal write | shared infrastructure | `tests/api/test_persisted_llm_transport.py` | PR2-PR4 |
| `apps/api/app/infrastructure/llm/openai_compatible.py` | provider adapter，当前已存在；继续禁止日志记录 prompt / completion / provider payload | `httpx`、provider config、project DTO | LangGraph concrete runtime | provider infrastructure | existing LLM tests | PR2-PR8 |
| `apps/api/app/infrastructure/llm/fake_transport.py` | deterministic fake，当前已存在；PR4 fake graph 使用它验证 no-provider path | project DTO、fixtures | provider network call | testable infrastructure | fake transport tests | PR4 |

LangGraph graph node 不直接调用 provider SDK；只能调用 `LlmTransport` 或 `PersistedLlmTransport`，并携带 `LlmTraceContext` / equivalent project DTO。PR4 若需要 LangChain model abstraction，只能在 `infrastructure/agent_runtime/langgraph/**` 内做 adapter，不能替代现有 `application/llm/ports.py`。

## 6. 前端目标目录骨架

### 6.1 AI Runtime UI 目录

| 目录 | 职责 | 允许依赖 | 禁止依赖 | 域 | 测试位置 | PR |
|---|---|---|---|---|---|---|
| `apps/web/src/entities/ai-task/**` | AI task types、API client、status helpers | `shared/api`、sanitized `AiTaskStatusResponse` | LangGraph checkpoint、raw provider fields、raw prompt/completion | AI Runtime UI entity | `entities/ai-task/**/*.test.ts` | PR7 |
| `apps/web/src/entities/agent-run/**` | agent run summary、timeline event、interrupt types | `shared/api`、runtime DTO | AgentState、checkpoint payload、node raw state | AI Runtime UI entity | `entities/agent-run/**/*.test.ts` | PR7 |
| `apps/web/src/features/ai-task-status/**` | polling、retry、cancel、status badge | ai-task entity、shared UI | business object direct mutation | AI Runtime feature | feature tests | PR7 |
| `apps/web/src/features/agent-interrupt-resume/**` | interrupt approve / edit / reject / resume | agent-run entity、shared forms | raw AgentState display | AI Runtime feature | feature tests | PR7 |
| `apps/web/src/features/candidate-confirmation/**` | candidate confirmation drawer and actions | candidate DTO、agent-run interrupt API、Core confirmation API | silent formal write | AI Runtime / Core handoff UI | feature tests | PR7-PR8 |
| `apps/web/src/widgets/task-status-panel/**` | reusable task status panel | ai-task feature | provider debug payload | AI Runtime widget | widget tests | PR7 |
| `apps/web/src/widgets/agent-run-timeline/**` | sanitized timeline display | agent-run entity | checkpoint payload、raw node state、raw prompt、raw completion、provider payload | AI Runtime widget | widget tests | PR7 |

### 6.2 Core UI 与 AI Runtime UI 边界

Core UI 包括 resume / job / binding / polish / report / review / weakness / asset / training 的普通业务页面、表单、列表和详情。Core UI 可读取 `ai_task_id`、`agent_run_id`、status summary、timeline summary 和 candidate refs，但不得导入 Agent 内部状态、checkpoint payload、node raw state 或 provider payload。

AI Runtime UI 只展示：

- task status：queued / running / succeeded / partial / low_confidence / validation_failed / source_unavailable / generation_failed / timed_out / cancelled。
- sanitized timeline event：node key、display status、started/finished time、validation summary、low confidence flags、checkpoint ref id。
- interrupt summary：action schema、candidate refs、required user action、resume status。
- LLM summary：model family、duration、validation status、usage summary；不展示 raw prompt / completion / provider payload。

Candidate confirmation drawer 属于业务确认 UI，不是 LangGraph debug UI。它只能通过 Core confirmation API 或 `AgentInterruptService` resume API 触发正式写入。

## 7. Import 规则和 AST / rg 验证

### 7.1 AST boundary tests

PR3 必须在 `tests/api/test_architecture_boundaries.py` 增加以下测试：

```python
def test_only_langgraph_infrastructure_imports_langgraph() -> None:
    violations = _find_forbidden_imports_outside_allowed_roots(
        APP_ROOT,
        forbidden_prefixes=("langgraph", "langchain", "langchain_core", "langchain_openai"),
        allowed_roots=(APP_ROOT / "infrastructure" / "agent_runtime" / "langgraph",),
    )
    assert violations == []
```

PR3 必须增加 Core Business 禁止依赖 Agent internals 的测试：

```python
def test_core_business_does_not_import_agent_internals() -> None:
    core_roots = [
        APP_ROOT / "domain",
        APP_ROOT / "application" / "auth",
        APP_ROOT / "application" / "resumes",
        APP_ROOT / "application" / "jobs",
        APP_ROOT / "application" / "bindings",
        APP_ROOT / "application" / "interviews",
        APP_ROOT / "application" / "reports",
        APP_ROOT / "application" / "reviews",
        APP_ROOT / "application" / "assets",
        APP_ROOT / "application" / "weaknesses",
        APP_ROOT / "application" / "training",
        APP_ROOT / "application" / "scoring",
    ]
    violations = []
    for root in core_roots:
        violations.extend(
            _find_forbidden_imports(
                root,
                forbidden_prefixes=(
                    "app.application.agents.state",
                    "app.application.agents.nodes",
                    "app.application.agents.graphs",
                    "app.infrastructure.agent_runtime.langgraph",
                ),
            )
        )
    assert violations == []
```

PR4 必须补充 repository / DB model scan：

```python
def test_db_models_and_repositories_do_not_import_langgraph() -> None:
    violations = _find_forbidden_imports(
        APP_ROOT / "infrastructure" / "db",
        forbidden_prefixes=("langgraph", "langchain", "langchain_core", "langchain_openai"),
    )
    assert violations == []
```

### 7.2 rg scan 命令

PR3 / PR4 的验证命令必须包含：

```bash
rg -n "from langgraph|import langgraph|from langchain|import langchain|from langchain_core|import langchain_core|from langchain_openai|import langchain_openai" apps/api/app \
  -g "*.py" \
  -g "!apps/api/app/infrastructure/agent_runtime/langgraph/**"

rg -n "AgentGraphState|agent_runtime.langgraph|application.agents.nodes|application.agents.graphs" \
  apps/api/app/domain apps/api/app/application apps/api/app/infrastructure/db \
  -g "*.py"
```

预期：第一条命令无输出；第二条命令只允许命中 `apps/api/app/application/ai/**` 或 `apps/api/app/application/agents/**` 的 contract / DTO 文件，不允许命中 Core Business、DB model 或 repository。

## 8. 与 active docs 的关系

本文仅规划目标目录。实际目录创建、代码迁移和测试补齐必须按 `BACKLOG.md` 后续 AIFI 任务执行；长期目录边界如需成为 canonical 架构规范，必须由主 Agent 汇总回写 `TECH_DESIGN.md`、`APPLICATION_FLOW_SPEC.md`、`PERSISTENCE_MODEL.md`、`SECURITY_PRIVACY.md` 或 ADR。

## 9. 非目标

- 不创建代码目录。
- 不移动现有文件。
- 不修改 import。
- 不新增测试文件。
- 不调整 frontend route。
- 不选择具体 package 版本；依赖与 spike 见 `18_LANGGRAPH_DEPENDENCY_AND_SPIKE_PLAN.md`。

## 10. 后续 PR 使用方式

| PR | 使用本文方式 | 禁止越界 |
|---|---|---|
| PR2 | 创建 AI Runtime tables / repositories / sanitized LLM persistence | 不引入 LangGraph dependency |
| PR3 | 创建 facade、runner port、registry、contracts、policy、handoff、interrupt contract 和 boundary tests | 不 import LangGraph concrete API |
| PR4 | 在 `infrastructure/agent_runtime/langgraph/**` 引入 LangGraph adapter、checkpointer、serializer、fake graph runtime | 不迁移业务 graph，不让 Core 直接 import LangGraph |
| PR5-PR8 | 按业务 graph / UI 切片逐步填充 | 不绕过 facade / handoff / confirmation |

## 11. Definition of Done

- 唯一直接 import LangGraph 的目录已冻结为 `apps/api/app/infrastructure/agent_runtime/langgraph/**`。
- `application/agents/langgraph_adapters/**` 的保留范围已冻结为 contract / DTO，不直接 import LangGraph。
- `checkpointer_factory.py` 和 `LangGraphAgentRunner` 已归属 infrastructure；`AgentTraceBridge` 已归属 application contract；DB write adapter / repository 已归属 `infrastructure/db/repositories`。
- Core Business、Repository、DB Model 禁止依赖 LangGraph 的 import rules 和 AST / rg scan 规则已给出。
- Frontend Core UI 与 AI Runtime UI 边界已冻结。
