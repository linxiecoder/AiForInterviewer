---
title: LangGraph 依赖与 Spike 验证计划
type: delivery-planning
status: draft-pr1
owner: 项目交付
permalink: ai-for-interviewer/docs/03-delivery/refactor-multiagent-langgraph/langgraph-dependency-and-spike-plan
---

# LangGraph 依赖与 Spike 验证计划

## 1. 文档目的

本文冻结 LangGraph MultiAgent 重构的依赖引入、版本锁定、官方 API 二次核验、checkpointer / serializer、minimal fake graph spike、CI 验证和降级策略。PR1.5 不安装依赖、不修改依赖文件、不调用 provider；本文是 PR4 dependency spike 的执行规格。

PR4 在依赖引入前必须先完成本文清单。PR4 未通过本文验证时，不得迁移任何真实业务 graph。

## 2. 输入来源

- `03_TARGET_DIRECTORY_STRUCTURE.md`
- `04_BACKEND_AGENT_RUNTIME_PLAN.md`
- `SECURITY_PRIVACY.md` 的 raw prompt / completion / provider payload 禁止边界
- `API_SPEC.md` 的 async task / owner / status / error envelope / no raw payload 边界
- 当前代码：`application/llm` port、`infrastructure/llm` fake / OpenAI-compatible transport、`tests/api/test_architecture_boundaries.py`

## 3. 依赖引入 PR 编号

| PR | 是否允许改依赖 | 允许文件 | 禁止动作 | 验收 |
|---|---|---|---|---|
| PR1.5 | 否 | 本文档 | 安装依赖、改 requirements / pyproject、调用 provider | 文档冻结 |
| PR2 | 否 | AI Runtime DB / repository 相关代码和测试 | 引入 LangGraph / LangChain 包 | runtime refs / raw-off 通过 |
| PR3 | 否 | facade / port / contracts / boundary tests | application 层 import LangGraph | AST boundary 通过 |
| **PR4-LG-DEP** | **是** | 后端依赖文件、`infrastructure/agent_runtime/langgraph/**`、PR4 tests | 迁移真实业务 graph、调用真实 provider、放宽 raw payload | 本文全部验证命令通过 |

PR4-LG-DEP 是唯一依赖引入 PR。若主 Agent 调整 PR 编号，必须同步更新 `17_PR_BREAKDOWN_AND_IMPLEMENTATION_SEQUENCE.md` 和本文 §3；未同步时以本文 `PR4-LG-DEP` 为依赖引入 gate。

## 4. 依赖选择

| Package | PR4 默认结论 | 用途 | Import allowlist | 禁止用途 |
|---|---|---|---|---|
| `langgraph` | 引入 | graph definition / compile / invoke / interrupt / resume spike | 仅 `apps/api/app/infrastructure/agent_runtime/langgraph/**` | application / domain / repository / DB model 直接 import |
| `langgraph-checkpoint-postgres` | 引入，前提是官方 API 二次核验确认支持当前 Python / Postgres / serializer 组合 | production checkpointer candidate | 仅 `infrastructure/agent_runtime/langgraph/checkpointer_factory.py` | Core Business table 查询、API response、business truth source |
| `langchain-core` | 仅在 LangGraph 官方 API 要求时作为 transitive / direct core abstraction 引入 | message / runnable / serializer 相关 core type bridge | PR1.5 默认不允许 application 直接 import；PR4 若必须暴露 type，需在 boundary test 中添加具体 symbol allowlist | 替代 project-owned DTO、污染 facade / Core UseCase signature |
| `langchain-openai` | PR4 不引入 | 无 | 无 | 绕过现有 `application/llm/ports.py` 和 `infrastructure/llm/openai_compatible.py` |

`langchain-openai` 暂不引入的原因：当前代码已经有 `LlmTransport` port、OpenAI-compatible transport、fake transport 和 raw-off logging 约束。PR4 fake graph spike 只验证 LangGraph runtime，不验证 provider SDK。真实 provider 接入继续走现有 `LlmTransport` / `PersistedLlmTransport`，避免 graph node 直接持有 provider client。

## 5. 版本锁定策略

PR4-LG-DEP 必须使用 exact pin，不允许只写 `>=`、`~=` 或未锁上限的范围。锁定结果必须进入后端依赖文件和 lock / constraints 文件；若仓库当时没有 lock 机制，PR4-LG-DEP 必须新增或更新项目已采用的等价 constraints 文件，并在 PR 描述中列出解析来源。

| Package | 锁定规则 | 变更条件 |
|---|---|---|
| `langgraph` | exact pin，例如 `langgraph==x.y.z`；`x.y.z` 由 PR4 官方核验和本地 spike 确认 | 只有 PR4-LG-DEP 可首次引入；后续升级必须单独 dependency PR |
| `langgraph-checkpoint-postgres` | exact pin，与 `langgraph` 官方兼容矩阵一致 | 若官方矩阵不兼容当前 Python/Postgres，PR4 必须启用 §12 降级策略 |
| `langchain-core` | exact pin；版本必须来自 `langgraph` 依赖树或官方兼容声明 | 禁止为了 convenience import 升级 |
| `langchain-openai` | 不写入依赖 | 需要引入时必须创建独立 provider adapter PR，并证明不绕过 `LlmTransport` |

PR4-LG-DEP 版本解析命令：

```bash
python -m pip index versions langgraph
python -m pip index versions langgraph-checkpoint-postgres
python -m pip index versions langchain-core
python -m pip install --dry-run --report /tmp/aifi-langgraph-deps.json \
  "langgraph==<resolved>" \
  "langgraph-checkpoint-postgres==<resolved>" \
  "langchain-core==<resolved>"
```

`<resolved>` 不能进入 PR；PR4 必须把命令输出中的具体版本写入依赖文件。若 `pip index versions` 在 CI 或本地不可用，PR4 使用项目包管理器等价命令，但仍必须生成可审计 dependency resolution output。

## 6. Python / 平台兼容

PR4-LG-DEP 必须读取当前仓库 Python 版本约束，并执行以下兼容检查：

```bash
python --version
python -c "import sys; print(sys.version_info)"
python -m pip install --dry-run --report /tmp/aifi-langgraph-python-compat.json \
  "langgraph==<resolved>" \
  "langgraph-checkpoint-postgres==<resolved>" \
  "langchain-core==<resolved>"
```

兼容规则：

- 依赖 metadata 的 `Requires-Python` 必须覆盖当前后端运行版本。
- 若 package 要求高于当前 Python，PR4-LG-DEP 不能升级 Python；必须触发 §12 降级策略。
- CI matrix 若只有一个 Python 版本，PR4-LG-DEP 只验证该版本；若 CI matrix 有多个版本，所有后端测试版本都必须通过 dry-run 和 fake graph tests。

## 7. 官方 API 二次核验清单

PR4-LG-DEP 修改依赖文件前必须二次核验官方 API，并在 PR 描述记录核验日期、链接、版本和结论。

| 主题 | 必须核验的 API / 文档点 | PR4 落点 | 验收 |
|---|---|---|---|
| graph compile / invoke | graph builder、compile、invoke / stream 调用签名 | `runner.py` | fake graph start 通过 |
| interrupt / resume | human-in-the-loop interrupt、resume command / state update API | `runner.py`、`interrupts.py` | fake interrupt/resume 通过 |
| checkpoint thread / namespace | thread id、checkpoint namespace、checkpoint id 获取方式 | `checkpointer_factory.py`、trace bridge event | `agent_checkpoint_refs` 只存 ref |
| memory checkpointer | test-only memory checkpointer API | PR4 tests | 不需要 Postgres 即可跑 fake graph |
| Postgres checkpointer | setup / connection / lifecycle / async-sync API | `checkpointer_factory.py` | production config test 通过或触发 §12 |
| encrypted serializer | encrypted serializer class / constructor / key requirements | `serializer.py` | 缺 key fail closed |
| event streaming | node event / state event / metadata redaction path | `runner.py` | timeline event sanitized |
| error model | compile / invoke / checkpoint exceptions | `map_langgraph_error` | project error mapping tests |

二次核验不得引用博客或旧 issue 作为唯一依据；必须优先使用官方 docs、package docs、源码 docstring 或安装后 introspection。若官方 docs 与安装包行为不一致，以安装包 introspection + spike test 为 merge gate。

## 8. 测试环境 checkpointer

PR4 tests 默认使用 memory checkpointer：

| 环境 | Backend | Serializer | Key | 规则 |
|---|---|---|---|---|
| unit / contract tests | memory checkpointer | test serializer or encrypted serializer with deterministic fake key | fake key from test fixture | 不连接 Postgres；不调用 provider；不保存 raw payload |
| integration tests with DB | memory checkpointer + runtime DB repositories | encrypted serializer if LangGraph API supports it | fake key from env fixture | `agent_checkpoint_refs` 写 DB，但 checkpoint payload 不进入 API / Core tables |

测试环境禁止从真实 `.env` 读取 provider key。fake graph 使用 `FakeLlmTransport` 或 pure deterministic node，不发网络请求。

## 9. 生产环境 checkpointer

PR4 默认生产策略：

| 项 | 冻结规则 |
|---|---|
| backend | `langgraph-checkpoint-postgres`，仅当 §7 二次核验和 §11 spike 通过 |
| ownership | checkpoint tables 不承载 owner truth；owner 存在 `agent_runs` / `agent_checkpoint_refs` |
| source of truth | checkpoint 不是 business read model，不作为 formal object 来源 |
| ref table | `agent_checkpoint_refs` 保存 namespace、thread id、checkpoint id、sequence、status、run id、owner id |
| retention | retention policy 由 `SECURITY_PRIVACY.md` 回写；PR4 只实现最小可删除 / 可过期 metadata |
| raw payload | checkpoint state 不保存 raw prompt、raw completion、provider payload；state 只存 refs / summaries / flags |

若 PG checkpointer 官方 API 与当前项目不兼容，PR4 不能用自制业务表模拟 LangGraph checkpoint；必须启用 §12 降级策略。

## 10. Encrypted Serializer 与密钥策略

PR4-LG-DEP 必须实现 encrypted serializer gate。密钥名默认冻结为 `LANGGRAPH_AES_KEY`；如果官方 API 使用不同名称或需要 key object，项目仍以 `LANGGRAPH_AES_KEY` 作为外部环境变量入口，在 `serializer.py` 内转换。

| 环境 | `LANGGRAPH_AES_KEY` 规则 | 失败处理 |
|---|---|---|
| local test | 可由 pytest fixture 提供 deterministic fake key | 未提供时使用 test-only memory serializer；不能进入 production path |
| local dev | 必须显式设置或使用 documented dev fake value | 缺失时 LangGraph runtime disabled |
| CI | 使用 CI secret / masked env；PR4 fake graph tests 可用 fixture fake key | 不打印 key；缺失则跳过 production-checkpointer test 并保留 memory-checkpointer test，PR 不能标记 production-ready |
| production | 必须来自 secret manager / runtime env | 缺失或格式不合法时 API 启动禁用 LangGraph runtime，返回 `GraphDisabledError` / `generation_failed`，不降级为 plaintext checkpoint |

密钥日志规则：

- 不打印 `LANGGRAPH_AES_KEY` 值、长度外的可逆信息、派生 key、serializer internal payload。
- `.env.example` 只能出现 fake / placeholder 值，不得出现真实 key。
- key rotation 策略由主 Agent 回写 `SECURITY_PRIVACY.md` / release runbook；PR4 只实现 fail-closed 与 no-log。

## 11. Minimal Fake Graph Spike

PR4-LG-DEP 必须先落 minimal fake graph，再允许接业务 graph。

### 11.1 Fake graph scope

| 项 | 冻结值 |
|---|---|
| graph name | `fake_runtime_smoke_graph` |
| nodes | `load_refs` -> `call_fake_llm` -> `validate_result` -> optional `interrupt_for_confirmation` -> `handoff_candidate_only` |
| LLM | `FakeLlmTransport` or deterministic node; no provider |
| state | `AgentGraphState` refs / summaries / flags only |
| checkpoint | memory checkpointer in unit tests; PG checkpointer only in explicit integration test |
| output | `AgentRunResult` with task/run refs, candidate refs, validation summary |
| formal write | forbidden |

### 11.2 Fake graph required tests

| Test | Assertion |
|---|---|
| `test_fake_graph_start_records_run_node_and_checkpoint_ref` | run/node/checkpoint ref written; no checkpoint payload exposed |
| `test_fake_graph_interrupt_resume_records_audit_and_timeline` | interrupt has owner/schema/action; resume validates payload |
| `test_fake_graph_replay_is_read_only` | replay never calls `AgentPersistenceHandoff` formal write |
| `test_fake_graph_uses_fake_llm_transport_only` | no provider env required; no network |
| `test_fake_graph_timeline_sanitizes_payload` | no raw prompt / completion / provider payload / AgentState |
| `test_only_langgraph_infrastructure_imports_langgraph` | import boundary enforced |

### 11.3 Spike success criteria

- `AgentGraphRunner` port tests pass without importing LangGraph in application layer.
- `LangGraphAgentRunner` fake graph tests pass.
- memory checkpointer path works in test env.
- PG checkpointer path either passes integration config test or triggers §12 documented downgrade before merge.
- encrypted serializer gate fails closed when production config lacks key.
- no test calls real provider.

## 12. 官方 API 不匹配降级策略

| Mismatch | 降级动作 | 允许合并条件 | 禁止 |
|---|---|---|---|
| `langgraph-checkpoint-postgres` incompatible with current Python / DB / sync style | PR4 keeps memory checkpointer for tests and marks production LangGraph runtime disabled by feature flag | dependency PR includes explicit `GraphDisabledError` path, no business graph migration | 自制 checkpoint table 冒充 LangGraph checkpoint |
| encrypted serializer API unavailable or incompatible | PR4 cannot enable production checkpoint; fake graph uses memory checkpointer only | serializer gate test proves production fails closed | plaintext production checkpoint |
| interrupt / resume API differs from docs | PR4 maps actual API through adapter and updates method-level tests | fake interrupt/resume passes with installed package | leaking LangGraph command/state into application signatures |
| event streaming unavailable | PR4 uses invoke + explicit trace bridge events for fake graph | timeline sanitized tests pass | exposing raw state to frontend |
| `langchain-core` version conflict | PR4 removes direct app-level dependency and keeps project-owned DTO | dry-run dependency resolution passes | changing Core DTO to LangChain DTO |
| `langgraph` import shape changes | PR4 updates `infrastructure/agent_runtime/langgraph/**` only | AST boundary still passes | importing LangGraph in application/Core to work around |

降级后 PR4 仍不得迁移真实业务 graph。业务 graph PR5-PR8 的前置条件是 production runtime path 已通过 PG checkpointer 或主 Agent 明确回写 active docs 接受 no-production-checkpoint boundary。

## 13. CI 兼容

PR4-LG-DEP 必须保持现有后端测试命令可运行，并新增 dependency/fake graph tests。CI 不需要真实 provider key。

| Gate | Command | Expected |
|---|---|---|
| dependency resolution | `python -m pip install --dry-run --report /tmp/aifi-langgraph-deps.json ...` | resolve succeeds with exact pins |
| architecture boundary | `.venv/bin/python -m pytest tests/api/test_architecture_boundaries.py -q` | only infrastructure LangGraph path imports LangGraph |
| fake graph runtime | `.venv/bin/python -m pytest tests/api/test_agent_runtime_fake_graph.py tests/api/test_langgraph_checkpointer_factory.py -q` | no provider call; memory checkpointer works |
| redaction | `.venv/bin/python -m pytest tests/api/test_agent_runtime_redaction.py -q` | no raw prompt/completion/provider payload |
| existing LLM fake | `.venv/bin/python -m pytest tests/api/test_polish_question_llm.py tests/api/test_polish_api.py -q` | existing fake / legacy compatibility preserved |

If CI lacks Postgres service for PR4, PG checkpointer integration test must be isolated behind an explicit marker such as `pytest -m langgraph_postgres`. The default CI gate still must prove memory checkpointer, serializer fail-closed and import boundaries.

## 14. 验证命令

PR1.5 文档验证命令：

```bash
git status --short --untracked-files=all
git diff --stat
git diff --check
rg -n "<forbidden-vague-planning-phrases>" docs/03-delivery/refactor-multiagent-langgraph/03_TARGET_DIRECTORY_STRUCTURE.md docs/03-delivery/refactor-multiagent-langgraph/04_BACKEND_AGENT_RUNTIME_PLAN.md docs/03-delivery/refactor-multiagent-langgraph/18_LANGGRAPH_DEPENDENCY_AND_SPIKE_PLAN.md
rg -n "import LangGraph|直接 import LangGraph|langchain-openai" docs/03-delivery/refactor-multiagent-langgraph/03_TARGET_DIRECTORY_STRUCTURE.md docs/03-delivery/refactor-multiagent-langgraph/04_BACKEND_AGENT_RUNTIME_PLAN.md docs/03-delivery/refactor-multiagent-langgraph/18_LANGGRAPH_DEPENDENCY_AND_SPIKE_PLAN.md
```

PR4-LG-DEP 依赖验证命令：

```bash
python --version
python -m pip index versions langgraph
python -m pip index versions langgraph-checkpoint-postgres
python -m pip index versions langchain-core
python -m pip install --dry-run --report /tmp/aifi-langgraph-deps.json \
  "langgraph==<resolved>" \
  "langgraph-checkpoint-postgres==<resolved>" \
  "langchain-core==<resolved>"
.venv/bin/python -m pytest tests/api/test_architecture_boundaries.py -q
.venv/bin/python -m pytest tests/api/test_agent_runtime_fake_graph.py tests/api/test_langgraph_checkpointer_factory.py -q
.venv/bin/python -m pytest tests/api/test_agent_runtime_redaction.py -q
```

## 15. Definition of Done

- 依赖引入 PR 已冻结为 `PR4-LG-DEP`。
- `langgraph`、`langgraph-checkpoint-postgres`、`langchain-core`、`langchain-openai` 的选择结论已明确。
- 版本锁定策略要求 exact pin 和 dependency resolution report。
- 官方 API 二次核验清单覆盖 graph、interrupt/resume、checkpoint、memory checkpointer、PG checkpointer、encrypted serializer、streaming、error mapping。
- 测试环境 memory checkpointer、生产环境 PG checkpointer、encrypted serializer 和 `LANGGRAPH_AES_KEY` 策略已冻结。
- Minimal fake graph spike 的 scope、tests、success criteria 已冻结。
- CI 兼容和官方 API 不匹配降级策略已冻结。
