---
title: SubAgent Recon 汇总报告
type: delivery-planning
status: draft-pr1
owner: 项目交付
permalink: ai-for-interviewer/docs/03-delivery/refactor-multiagent-langgraph/subagent-recon-report
---

# SubAgent Recon 汇总报告

## 1. 文档目的

本文件记录 PR1 SubAgent-assisted 只读 recon 的职责分工、代码 symbol 级发现、旧模块迁移矩阵入口、当前实现成熟度、未解决问题和 PR1.5 修复闭环。它用于给后续 PR2-PR8 提供上下文，但不替代 active docs，也不把 SubAgent 草稿直接提升为事实源。

## 2. 输入来源

- SubAgent A：Docs Governance Agent 只读输出。
- SubAgent B：Architecture Skeleton Agent 只读输出。
- SubAgent C：Backend Runtime Skeleton Agent 只读输出。
- SubAgent D：Graph Plans Skeleton Agent 本轮代码 symbol 级 recon 与 06-09 implementation-ready graph spec。
- SubAgent E：Frontend / Testing / Validation Skeleton Agent 只读输出。
- active docs：`AGENTS.md`、`DOCS_INDEX.md`、`BACKLOG.md`、`APPLICATION_FLOW_SPEC.md`、`PERSISTENCE_MODEL.md`、`DATA_MODEL.md`、`PROMPT_SPEC.md`、`SCORING_SPEC.md`、`SECURITY_PRIVACY.md`、`API_SPEC.md`、`UX_SPEC.md`、`UI_DESIGN_SYSTEM.md`、`prompt-contracts/*.md`。
- 临时输入：`docs/tmp/CODEX_LANGGRAPH_MULTIAGENT_README.md`、`docs/tmp/CODEX_LANGGRAPH_AI_NON_AI_BOUNDARY.md`。`docs/tmp` 只作为 PR1 输入，不作为长期事实源。

## 3. 当前状态

本轮只修改 PR1 专题设计包内 SubAgent D 拥有的 `00/06/07/08/09` 文档，不执行 PR2-PR8 的实现、测试编写、migration、provider 调用、commit 或 push。

Plan mode 核心结论已纳入本文件：

- 采用 LangGraph-first / Option C。
- 单微服务双域：Core Business 与 AI Runtime 在同一后端内分层隔离。
- Core Business 不依赖 LangGraph。
- Core UseCase 只通过 `AiOrchestrationFacade` 触达 AI Runtime。
- LangGraph checkpoint 不是业务事实源。
- AI Runtime 需要 agent run、node run、interrupt、LLM trace、checkpoint ref 和 sanitized timeline。
- candidate / suggestion 不得静默升级为 formal object。
- raw prompt、raw completion、provider payload 不进入日志、checkpoint 或 API response。
- LLM node 不直接写 formal object；formal write 只能由 Core Business command/API 在用户确认或显式动作后执行。

## 4. 目标输出

- SubAgent A-E 职责回顾。
- SubAgent D 代码 symbol 级 recon 摘要。
- 旧模块迁移矩阵入口。
- 当前实现成熟度矩阵。
- 未解决问题清单。
- PR1.5 修复闭环。
- SubAgent 冲突与主 Agent 决策。

## 5. SubAgent A-E 职责回顾

| SubAgent | 职责 | 输出摘要 |
|---|---|---|
| A Docs Governance | 查找 docs index / backlog，分析登记风格和治理风险 | 确认 `DOCS_INDEX.md` 与 `BACKLOG.md` 路径，建议新增 AIFI 任务并登记专题包 |
| B Architecture | 起草 README、Option、推荐架构、目录结构 | 建议 Option C、双域架构、facade、checkpoint 非事实源 |
| C Backend Runtime | 起草 runtime、LLM trace、data、API 骨架 | 建议 `AiOrchestrationFacade`、`AgentGraphRunner`、`PersistedLlmTransport`、runtime 表 |
| D Graph Plans | 起草并补强 06-09 graph plans | 覆盖 resume/job match/polish/report/review/weakness/asset/training/confirmation graph，并补齐 node contract 与旧 symbol 迁移策略 |
| E Frontend / Testing | 起草 12-17 frontend/test/validation/PR breakdown | 覆盖 AI task UI、timeline、interrupt、candidate confirmation、PR1-PR8 验证 |

## 6. SubAgent 已发现事实

| 来源 | 已发现事实 | 主 Agent 处理 |
|---|---|---|
| A | `docs/tmp` 只能作为输入，不是事实源 | 在 README、DOCS_INDEX 和各文档关系章节重复声明 |
| A | 专题包不能替代 active canonical docs | 在 `DOCS_INDEX.md` 登记为专题设计包 |
| A | 建议新增 `AIFI-BE-002` | 采用，范围限定为 PR1 文档登记与设计包骨架 |
| B | Option C 最能支撑 graph/runtime/trace/interrupt 长期演进 | 采用为推荐架构 |
| B | ADR 可能需要后续创建 | PR1 不创建 ADR；若 Option C 长期固化，由主 Agent 另行授权 ADR |
| C | runtime 需要 facade、runner port、LangGraph adapter、trace bridge | 纳入 04、05、10、11 |
| C | API_SPEC 需由主 Agent 补读 | 主 Agent 已补读，11 仍标记后续 contract 需正式回写 |
| D | Graph 草案中的部分节点名与用户指定清单不同 | 正式文档按用户指定节点名冻结，额外节点只作为补充 |
| D | 旧 Job Match / Polish 代码已具备可包装的 LLM service、validator、repository 与测试门 | 在本文件 §8 与 06/07 建立 symbol 到 graph node 映射 |
| E | 当前前端测试以类型/契约为主，PR7 若引入 runner 需单独授权 | 纳入 14、17 风险与 PR7 scope |

## 7. 代码 symbol 级 recon 摘要

| 领域 | 文件 / symbol | 当前事实 | Graph spec 处理 |
|---|---|---|---|
| LLM transport | `apps/api/app/application/llm/types.py::LlmTransportRequest` | dataclass 只包含 `contract_ids`、`task_type`、`input_refs`、`evidence_bundle`，用于最小输入包 | Graph LLM node 必须继续使用 sanitized refs + evidence bundle；不得把 raw prompt/completion/provider payload 写入 state |
| LLM port | `apps/api/app/application/llm/ports.py::LlmTransport.generate` | 抽象 provider 边界 | PR2-PR4 wrap 为 persisted transport / trace bridge；Core Business 不 import LangGraph |
| Job Match LLM | `apps/api/app/infrastructure/llm/job_match.py::LlmJobMatchAnalyzer.analyze` | 调用 `LlmTransportRequest(contract_ids=JOB_MATCH_CONTRACT_IDS, task_type="job_match_analysis", input_refs, evidence_bundle)`，normalize provider payload 后返回 `JobMatchAnalyzerOutput` | 06 将其包装为 `run_job_match_analyzer` node；normalize 与 score gate 分离 |
| Job Match validator | `_normalize_job_match_payload` 与相关 normalize helper | 负责 loose provider payload shape、dimension score、gap coverage、source refs 标准化 | 06 将其收敛到 `normalize_job_match_payload` node 和 `job_match_score_gate` node |
| Polish question use case | `PolishUseCases.create_question_task` | 校验 session/progress tree，调用 `PolishQuestionLlmService.generate_with_llm_or_fallback`，再 `SqlAlchemyPolishRepository.add_question` 和 `add_task` | 07 拆为 request validation、context、LLM/fallback、quality、persist question、complete task |
| Polish answer save | `PolishUseCases.create_answer` | 保存 answer，校验 idempotency，不调用 LLM | 07 保留为 Core Business；不得纳入 feedback LLM graph |
| Progress tree | `PolishUseCases.refresh_progress_tree_state`、`PolishProgressTreeLlmService.generate_initial/refresh_state`、`build_deterministic_progress_node_question` | 支持 tree 初始化/刷新、deterministic question build、progress state update | 07 将 progress tree refresh 和 question generation graph 显式拆分 |
| Question quality | `validate_question_quality` | 阻断 legacy template、theme mismatch、answer leak、重复、unsupported entity 等；允许低置信 warning | 07 作为 `question_quality_gate` validator |
| Feedback use case | `PolishUseCases.create_feedback_task` | 构建 deterministic payload，调用 feedback LLM/fallback，`validate_feedback_consistency`，extract candidates，candidate LLM enhancement，persist feedback/task | 07 拆为 feedback candidate、schema/consistency gate、candidate extraction/enhancement、persist feedback/score/candidates |
| Feedback quality | `validate_feedback_consistency`、`compute_score_result_from_dimensions` | 校验 point refs、score consistency、critical loss coverage、retry delta、no leak；blocking 时生成 safe fallback | 07 作为 `feedback_consistency_gate` 与 `persist_score` 前置 validator |
| Candidate extraction | `extract_feedback_candidates`、`safe_candidate_dict`、`PolishCandidateLlmService.enhance_with_llm_or_fallback` | 生成 weakness/asset/training/oral/polished candidates，并保持 candidate-only | 09 作为 candidate graph 旧实现入口；formal write 仍由 confirmation command 承接 |
| Polish repository | `SqlAlchemyPolishRepository.add_question/add_feedback/update_progress_tree/add_task` | 现有同步 DB write path | Graph node 只调用 repository/tool；checkpoint 不替代 repository business truth |
| Polish API | `apps/api/app/api/v1/polish.py` | 响应 sanitizer 过滤 feedback raw payload，路由保持旧 API 兼容 | PR6 graph facade 必须保持 API contract 和 response sanitizer |
| Current tests | `tests/api/test_job_match_api.py`、`test_polish_api.py`、`test_polish_question_llm.py`、`test_polish_feedback_llm.py`、`test_polish_candidates.py` | 覆盖 owner、validation failed 不保存、fallback、raw payload redaction、candidate confirmation、rollback、training task explicit action | 06-09 将这些测试作为迁移后必须保留或迁移的 regression gates |

## 8. 旧代码迁移矩阵入口

各 graph 文件包含 graph 专属迁移矩阵；本表是总入口，不替代 06-09 的细化表。

| Existing Symbol | Target Node / Tool / Validator | Strategy | PR | Tests |
|---|---|---|---|---|
| `LlmTransportRequest` | all LLM nodes input package | keep | PR2-PR8 | transport raw-off scan、contract id fixture |
| `LlmTransport.generate` | `PersistedLlmTransport` / graph LLM tool | wrap | PR2-PR4 | provider failure、no raw payload、trace summary |
| `LlmJobMatchAnalyzer.analyze` | `job_match_graph.run_job_match_analyzer` | wrap | PR5 | `test_llm_analyzer_*`、provider unavailable |
| `_normalize_job_match_payload` helpers | `normalize_job_match_payload` / `job_match_score_gate` | split | PR5 | invalid payload、gap coverage、0/100 score |
| `PolishUseCases.create_question_task` | `polish_question_graph` facade entry | split | PR6 | question API compatibility、progress node、fallback |
| `PolishQuestionLlmService.generate_with_llm_or_fallback` | `generate_question_candidate` LLM/fallback tool | wrap | PR6 | question LLM fake/fallback/raw-off |
| `build_deterministic_progress_node_question` | deterministic fallback tool | keep | PR6 | deterministic question fixture |
| `validate_question_quality` | `question_quality_gate` | keep | PR6 | semantic validation、answer leak、duplicate |
| `PolishUseCases.create_answer` | Core Business answer save | keep | PR6 | answer idempotency、answer save no LLM |
| `PolishUseCases.create_feedback_task` | `polish_feedback_graph` facade entry | split | PR6 | feedback API compatibility、legacy payload |
| `validate_feedback_consistency` | `feedback_consistency_gate` | keep | PR6 | consistency invalid、score repair、raw leak |
| `extract_feedback_candidates` | candidate extraction node/tool | wrap | PR6/PR8 | no formal write、candidate refs |
| `PolishCandidateLlmService.enhance_with_llm_or_fallback` | candidate enhancement node/tool | wrap | PR8 | fake provider accepted、forbidden payload fallback |
| `SqlAlchemyPolishRepository.add_question/add_feedback/update_progress_tree/add_task` | persistence tools | keep | PR6 | repository write path and API readback |
| Candidate repository `confirm/dismiss/merge/archive` | Core formal write command behind interrupt | wrap | PR8 | confirm creates formal refs、dismiss/merge no formal、rollback |
| Legacy direct LLM call from Core UseCase | `AiOrchestrationFacade` call | deprecate after graph parity | PR6-PR8 | architecture boundary no LangGraph import |
| Raw provider payload surfaced through API/log/checkpoint | none | delete/forbid | PR2-PR8 | raw prompt/completion/provider payload scans |

## 9. 当前实现成熟度矩阵

| Area | Current implementation maturity | Graph readiness | Blocking boundary |
|---|---|---|---|
| Runtime facade / runner | Skeleton-only in planning docs | L1 planning | PR2 must define facade, runner, registry and trace bridge before graph implementation |
| LLM transport | Existing transport request/port and domain services available | L3 wrap-ready | Raw payload policy and persisted trace adapter must precede provider graph use |
| Job Match | Existing LLM analyzer, payload normalization and tests available | L4 implementation-ready for PR5 | `ScoreResult(job_match)` persistence target must be confirmed in PR5 data/API handoff |
| Resume Analysis | No dedicated active `P-RESUME-*` contract | L2 deterministic source-bundle ready | PR5 must freeze deterministic contract/file/symbol boundary before standalone graph |
| Polish Question | Existing use case, LLM/fallback, deterministic builder, quality validator, repository, tests available | L4 implementation-ready for PR6 | Graph facade must preserve API response and legacy metadata |
| Polish Feedback | Existing deterministic payload, LLM/fallback, consistency validator, candidate extraction/enhancement, repository, tests available | L4 implementation-ready for PR6 | `persist_score` may require ScoreResult repository extension outside SubAgent D files |
| Report | Active Prompt/API/Data contracts exist; no current implementation located in requested symbol list | L3 spec-ready | PR8 must implement worker state, reducer, partial policy and persistence tools |
| Review | Active Prompt/API/Data contracts exist; no current implementation located in requested symbol list | L3 spec-ready | Real review needs third-party redaction and user confirmation gates before LLM |
| Weakness/Asset/Training candidate | Existing Polish candidate extraction and formal confirmation tests available | L3/L4 hybrid | PR8 must centralize confirmation interrupt schema and formal write handoff |
| Frontend confirmation/timeline | Planning docs only | L2 UI handoff ready | PR7 must implement UI with no raw payload and candidate correction states |

## 10. 当前测试覆盖矩阵

| 测试类别 | 当前线索 | 迁移后必须保留的断言 |
|---|---|---|
| Backend architecture boundary | `test_architecture_boundaries.py` | Core Business 不 import LangGraph；facade 是唯一 runtime 入口 |
| Job Match API / analyzer | `test_job_match_api.py` | persisted completed result、source digest、provider unavailable、payload normalization、owner scoped、invalid result not saved |
| Polish API | `test_polish_api.py` | session/question/answer/feedback compatibility、answer save no LLM、progress tree state |
| Polish Question LLM | `test_polish_question_llm.py` | compact signals、feature flag、real-provider gate、valid fake accepted、schema/semantic fallback、no raw payload |
| Polish Feedback LLM | `test_polish_feedback_llm.py` | compact previous feedback、feature flag、real-provider gate、retry delta、score repair、low confidence、redacted provider details |
| Polish Candidates | `test_polish_candidates.py` | sanitizer、duplicate merge key owner scope、confirm formal refs、dismiss/merge/archive no formal write、rollback、training task explicit action |
| Docs governance | `tests/doc_governor -q` | 专题包仍不替代 active docs，不新增并行 roadmap/task 入口 |

## 11. 未解决问题清单

| Issue | Current decision | Frozen boundary | Owner PR | File / symbol to inspect |
|---|---|---|---|---|
| `ScoreResult(job_match)` and `ScoreResult(polish_answer)` physical write path | Graph spec requires `persist_score_result`; current requested symbol list only confirms payload score and task score_type | Graph may not invent ORM writes; PR owning data/API must add or bind repository | PR5/PR6 | `apps/api/app/infrastructure/db/repositories/*`, `PERSISTENCE_MODEL.md`, `API_SPEC.md` |
| Dedicated `resume_analysis_graph` contract | No active `P-RESUME-*` contract | Treat as deterministic source-bundle graph until PR5 freezes exact contract | PR5 | `APPLICATION_FLOW_SPEC.md`, `JOB_MATCH_CONTRACTS.md` |
| Report/review concrete repository symbols | Requested code list has no report/review implementation files | 08 freezes persistence targets and node contracts only; implementation PR must locate or create authorized repository tools | PR8 | `PERSISTENCE_MODEL.md`, `API_SPEC.md`, future report/review repositories |
| Candidate confirmation interrupt storage | Existing candidate repository has confirm/dismiss/merge/archive behavior; LangGraph interrupt table/tool not yet implemented | Checkpoint is runtime resume aid only; `UserConfirmationRef`/audit/business table are truth | PR8 | candidate repository, runtime interrupt plan, `API_SPEC.md` |
| Runtime audit event mapping | Active docs require audit; runtime table/schema not implemented in this scope | Graph nodes emit sanitized audit events through runtime/audit port, not raw payload | PR2-PR4/PR8 | `SECURITY_PRIVACY.md`, `PERSISTENCE_MODEL.md`, runtime plan |
| Report `Send` / parallel worker API version | LangGraph implementation details not confirmed in code | 08 uses conceptual `Send` fanout; implementation PR must pin package/API in dependency PR only if authorized | PR8 | dependency plan outside SubAgent D scope |

## 12. PR1.5 修复闭环

| PR1.5 Fix | Applied in this package | Evidence |
|---|---|---|
| Replace broad skeleton with implementation-ready graph specs | Yes | 06-09 now include per-node Graph/Node/Mapping/Input/Output/State/Side effect/Idempotency/Checkpoint/Retry/Fallback/Failure/Tests tables |
| Add code symbol recon summary | Yes | §7 |
| Add legacy migration matrix | Yes | §8 and graph-specific migration matrices |
| Remove ambiguous planning language | Yes | Explicit PR/file/symbol/frozen boundary provided for unresolved issues |
| Keep AI/non-AI boundary | Yes | §3, §8, §11 plus 06-09 node contracts |
| Preserve no raw payload policy | Yes | Required in all graph specs and tests |
| Preserve checkpoint non-truth policy | Yes | Checkpoint columns say runtime resume only, repository/business refs are truth |

## 13. SubAgent 冲突与主 Agent 决策

| 冲突 / 差异 | 主 Agent 决策 |
|---|---|
| 用户文字写“18 个文档”，清单实际包含 19 个文件 | 按完整清单创建 19 个文件，避免遗漏 `00_SUBAGENT_RECON_REPORT.md` |
| SubAgent A 建议 `AIFI-BE-002` 优先级可用 SHOULD | 采用 SHOULD；PR1 是专题规划，不直接声明 MVP 发布阻断 |
| SubAgent B 提到 ADR | PR1 不写 ADR，后续如 Option C 长期固化再走受权 ADR |
| SubAgent C 标题与用户指定标题不完全一致 | 正式文档使用用户指定标题 |
| SubAgent D 部分 graph 节点名不同 | 正式文档使用用户指定节点名，并保留额外节点为补充 |
| SubAgent E 指出前端无真实 runner | PR7 需单独决策是否引入 Vitest/RTL/MSW/Playwright |

## 14. 与 active docs 的关系

本 recon 报告仅记录本轮只读发现和规划判断。任何长期事实必须回写到 active docs；任何历史材料只能通过 `REQUIREMENT_TRACEABILITY.md` 或 `archive/MANIFEST.md` 追踪，不能从本文件反向绕过 active docs。

## 15. 非目标

- 不完整重做全仓 recon。
- 不修改业务代码、测试、依赖或 migration。
- 不把 SubAgent 草稿原文作为正式规范。
- 不把 `docs/tmp` 提升为 canonical。
- 不确认真实 LangGraph / provider 选型细节。
- 不让 LLM node 直接写 formal object。
- 不让 checkpoint 成为 business truth source。

## 16. 后续 PR 使用方式

- PR2/PR3 必须补齐 backend runtime 精确 recon：现有 `AiTask`、LLM service、repository、API router 的迁移点。
- PR4 必须补齐 LangGraph checkpointer、fake graph 和 trace bridge 的实现证据。
- PR5/PR6/PR8 必须按业务 graph 做逐链路 recon，不得只引用本 PR1 skeleton。
- PR7 必须补齐前端测试 runner 与 API contract 是否稳定的决策。
- PR8 必须将 candidate confirmation interrupt 与 Core formal write command 分层实现，禁止 late graph result 绕过 confirmation。

## 17. Definition of Done

- SubAgent A-E 输出已被归并。
- 冲突已由主 Agent 决策。
- AI / 非 AI 双域边界已明确。
- 代码 symbol 级 recon、迁移矩阵、成熟度矩阵、未解决问题和 PR1.5 闭环已落入本文件。
- 06-09 graph spec 达到 implementation-ready：每个 graph 均有统一 node contract 表。
- 本报告明确自身不是 active canonical docs。
