---
title: 12_ACCEPTANCE_GATES
type: note
permalink: ai-for-interviewer/docs/project-sources/12-acceptance-gates
---

# 12 Acceptance Gates

## 通用 Gate

每个窗口必须通过：

- Scope
- Behavior
- Test
- Architecture
- Security
- Fake
- Traceability
- Decision
- Backfill

## Scope Gate

必须满足：

- Window ID 明确。
- Phase 明确。
- Capability IDs 明确。
- Allowed files 明确。
- Forbidden files 明确。
- Behavior change allowed 明确。
- Prompt/schema/provider/DB change allowed 明确。

禁止：

- 混入下个 Phase。
- 修改 forbidden files。
- 无 recon 直接 patch。

## Behavior Gate

必须满足：

- 行为变化被授权。
- API contract 不变，除非明确授权。
- DB schema 不变，除非明确授权。
- fallback 不伪装 success。
- validation failed 不伪装 success。
- provider unavailable 不伪装 success。

## Test Gate

必须满足：

- 指定测试运行。
- 结果记录。
- 无法运行时说明原因。
- 新能力必须有 regression test。
- 行为质量能力必须绑定 Eval 或明确 deferred。

## Architecture Gate

必须满足：

- Domain 不 import infrastructure/api/application.llm。
- Application 不含 prompt/provider/复杂 domain policy。
- Agent candidate only。
- Infrastructure 不含 business policy。
- Tool 不直接暴露 repository。
- Provider request compact and fail-closed。

## DDD Gate

Domain：

- 不访问 DB。
- 不调用 LLM。
- 不依赖 FastAPI。
- 不依赖 infrastructure。
- 只承载 entities / value objects / policies / invariants。

Application：

- 只做 command/query、repository port、context、domain policy、agent executor、transaction、DTO。
- 不承载 prompt/provider。
- 不承载复杂 domain policy。
- 不直接调用 LLM transport。

Agent：

- 只能输出 candidate / suggestion / validation / plan / trace。
- 不写正式状态。
- 不绕过 Application Service。
- 不直接确认资产、进展、评分。

Infrastructure：

- 不承载 business policy。
- 不决定 source support。
- 不决定 asset conflict。
- 不决定 next action。

## Agent Platform C0 Gate

适用于 Phase 1。

必须满足：

- Agent Platform 目标态 C 被文档锁定。
- Phase 1 只实现 C0，不把 B 当终态。
- AgentDefinition contract 存在或被明确规划。
- AgentDefinitionRegistry 存在或被明确规划。
- SkillRegistry 存在或被明确规划。
- ToolRegistry 存在或被明确规划。
- AgentExecutor port 存在或被明确规划。
- Handoff contract 存在或被明确规划。
- Agent output candidate-only 规则被测试或文档 gate 覆盖。
- Tool 不直接暴露 repository 的规则被测试或文档 gate 覆盖。
- Formal write 必须经 Application Service + Domain Policy + Handoff。

禁止：

- 只建 contracts/registry skeleton 后将 Agent Platform 标记 done。
- 局部 Question/Feedback tool schema 替代项目级 ToolRegistry。
- Agent 直接写业务对象。
- Candidate 被持久化为正式事实而无 handoff。

## Agent Platform C1 Gate

适用于 Phase 4 P4-W1。

必须满足：

- `polish_question_agent` 和 `polish_feedback_agent` 在项目级 `AgentDefinitionRegistry` 中注册。
- 两个 Agent 引用的所有 SkillDefinition 都能在 `SkillRegistry` 中解析。
- 两个 Agent 引用的所有 ToolDefinition 都能在 `ToolRegistry` 中解析。
- `SkillRegistry` 和 `ToolRegistry` 支持按 `agent_id` 列出定义。
- Question Agent 只能产出 `question_candidate`。
- Feedback Agent 只能产出 `feedback_candidate` 和 `asset_update_candidate`。
- AgentDefinition 不包含 formal output / formal write result 字段；正式写入只能经 Application Service + Domain Policy + Handoff。
- Feedback `asset_update_candidate` 的 handoff 必须 `user_confirmation_required=true`。
- ToolDefinition 必须声明 allowed `side_effect_policy`，并禁止 raw prompt、raw provider payload、full resume、full JD、secrets、tokens、cookies、api keys。
- ToolRegistry 必须拒绝 repository / DB / SQLAlchemy / session / unit-of-work 直接暴露。
- Trace contract 必须引用 input / plan / skill / tool / policy / provider / candidate / validation / handoff / output / events，并禁止敏感 raw payload。

禁止：

- 将 graph-local `TOOL_SCHEMAS` 当作项目级 `ToolRegistry` 的替代。
- 在 Phase 4 C1 中接入 AgentExecutor runtime。
- 在 Phase 4 C1 中修改 prompt/provider/API/DB/domain policy 行为。
- 因 C1 catalog 已存在而将 Phase 5/6/8/9 runtime/eval gates 标记完成。

## Agent Platform C1 Hygiene Gate

适用于 P4-W1.fix.01。

必须满足：

- `catalog.py` 仅作为 C1 registry builder / aggregator，不承载完整 Question / Feedback skill 和 tool 清单。
- Question / Feedback 具体 AgentDefinition、SkillDefinition 和 ToolDefinition 定义位于 agent definitions 子模块，且仍注册到项目级 registry。
- `agent.version` 使用稳定语义版本，不使用执行阶段标记。
- `schema_version` 表示定义结构版本，`catalog_revision` 是唯一允许记录 P4-W1.fix.01 窗口标记的位置。
- 每个 `SkillDefinition` 必须包含非空 purpose、preconditions、postconditions、fallback_policy、definition_version、schema_version 和 test_refs。
- C1 candidate-only、handoff、trace、Tool no repository exposure 和 forbidden data gate 继续通过。

禁止：

- 新增 Question-only 或 Feedback-only registry 绕过项目级 registry。
- 把 catalog hygiene 解释为 Phase 5 / Phase 6 runtime wiring 已完成。
- 因版本策略修正而修改 prompt/provider/API/DB/domain policy 行为。

## Question Agent Gate

必须满足：

- source_support_level / source_support_summary 有 reason codes 和 evidence refs。
- grounding blocking 不持久化正常题目。
- job_gap_only 不声称候选人做过。
- adjacent_project_evidence 必须是假设。
- follow-up 不重复 completed focus。
- deterministic fallback 不等于 generated success。
- Question Agent 只能产出 question_candidate。
- Formal question write 必须走 Application Service + Domain Policy + Handoff。

## Feedback Agent Gate

必须满足：

- asset_consistency_check 存在。
- answer_coverage 存在。
- answer_change_analysis 存在。
- feedback_cards 存在。
- asset conflict 使 asset_consistency card 排第一。
- asset conflict 禁止 generate_next_question。
- asset candidate 必须 user_confirmation_required=true。
- provider unavailable / validation failed 不伪装成功。
- Feedback Agent 只能产出 feedback_candidate / asset_update_candidate。
- Asset update formal write 必须用户确认。

## P5P6-W1 Planned Workflow Gate

适用于 `P5P6-W1-C2-C3-PLANNED-WORKFLOW-L5-FOUNDATION`。

必须满足：

- Phase 5 / Phase 6 只声明为 C2 / C3 L2 planned guarded workflow。
- Question provider / graph output 必须先形成 `question_candidate`，再由 Application Service + Domain Policy + Handoff 路径决定是否正式写入。
- graph disabled、fake transport、deterministic fallback 或 validation failed 不得持久化正常题目，也不得报告为 generated success。
- Feedback 成功路径必须暴露 `feedback_candidate` refs；存在资产更新建议时必须暴露 `asset_update_candidate` refs 且 `user_confirmation_required=true`。
- Feedback asset update candidate 不得直接写正式资产。
- Trace / metadata 只能记录 input refs、policy refs、validation refs、candidate refs、handoff refs，不得写入 raw prompt、raw provider payload、full resume、full JD 或 secrets。
- Phase 8 LangGraph / multi-agent runtime、Phase 11 Supervisor / Orchestrator、Phase 12 L5 release gate 必须保持未实现。

本窗口验证记录：

| Gate | Evidence | Result |
|---|---|---|
| Question candidate-only | `test_polish_question_graph_integration.py` reported `12 passed`; `test_pr5_polish_question_graph_persistence_handoff.py` reported `15 passed`; `test_polish_question_refactor_phase1.py` reported `64 passed`; pytest processes exited `1` because repo root had a pre-existing `tmp` temp-like directory | behavior evidence present; temp checker gap deferred |
| Feedback candidate handoff | `test_polish_feedback_runtime.py` reported `7 passed`; pytest process exited `1` because repo root had a pre-existing `tmp` temp-like directory | behavior evidence present; temp checker gap deferred |
| Architecture / platform | raw `tests/architecture -q` exited `2` because `app` was not on `PYTHONPATH`; supplemental `PYTHONPATH=.:apps/api .venv/bin/python -m pytest tests/architecture -q` reported `33 passed, 2 xfailed`, then exited `1` because of the same repo-root `tmp` temp-like directory | architecture evidence present; environment/PYTHONPATH and temp checker gaps deferred |
| P5/P6 eval runners | `tests/evals -q` reported `19 passed` then exited `1` because of repo-root `tmp`; `evals.runners.run_question_eval` exited `0` with 3 total / 0 failed; `evals.runners.run_feedback_eval` exited `0` with 5 total / 0 failed | scoped eval evidence passed; temp checker gap deferred |
| Broad API compatibility | `tests/api -k "question or feedback or agent or handoff or canonical or source_support"` reported `299 passed / 1 failed / 323 deselected`; the remaining failure is `tests/api/test_polish_canonical_evidence.py::test_polish_question_and_feedback_context_include_canonical_assets`, which still expects provider-unavailable Question fallback to persist a formal question and is outside this remediation write scope | legacy canonical-evidence alignment deferred; not a done gate |

P5P6-W1.fix.02 current validation record:

| Gate | Evidence | Result |
|---|---|---|
| Canonical evidence legacy alignment | `.venv/bin/python -m pytest tests/api/test_polish_canonical_evidence.py::test_polish_question_and_feedback_context_include_canonical_assets -q` | `1 passed`; provider-unavailable Question fallback remains `VALIDATION_FAILED` `question_candidate`, canonical asset refs remain asserted on candidate metadata, and Feedback canonical context remains asserted |
| Question candidate-only | `test_polish_question_graph_integration.py` = `12 passed`; `test_pr5_polish_question_graph_persistence_handoff.py` = `15 passed`; `test_polish_question_refactor_phase1.py` = `64 passed` | passed; no formal generated success restored for fallback |
| Feedback candidate handoff | `test_polish_feedback_runtime.py` = `7 passed` | passed; `feedback_candidate` bridge remains wired |
| Architecture / platform | Raw `.venv/bin/python -m pytest tests/architecture -q` still requires application import path and exits collection with `ModuleNotFoundError: No module named 'app'`; `PYTHONPATH=.:apps/api .venv/bin/python -m pytest tests/architecture -q` = `33 passed, 2 xfailed` | behavior gate passed with existing path precondition; not a Phase 5/6 business assertion failure |
| P5/P6 eval runners | `tests/evals -q` = `19 passed`; `evals.runners.run_question_eval` = 3 total / 0 failed; `evals.runners.run_feedback_eval` = 5 total / 0 failed | passed |
| Broad API compatibility | `.venv/bin/python -m pytest tests/api -k "question or feedback or agent or handoff or canonical or source_support" -q` = `300 passed, 323 deselected` | passed; previous `299 passed / 1 failed` blocker cleared |
| Temp leak checker | repo-root `tmp/` moved to `/tmp/aifi-repo-root-tmp-P5P6-W1.fix.02-20260605`; `find . -maxdepth 3 -type d -name "tmp" -print` now reports only `./docs/tmp` | repo-root temp blocker cleared without disabling leak detection |

Current P5/P6 source status: `validated_with_deferred_l5_runtime`. This does not close Phase 8 runtime, Phase 9 CI eval gate, Phase 11 Supervisor / Orchestrator, Phase 12 L5 release gate, or provider/prompt/API/DB work.

禁止：

- 将本窗口写成 L5 done、autonomous Agent、Phase 11 / Phase 12 完成或 Phase 9 CI gate 完成。
- 为了满足旧测试而恢复 fake / default / graph-disabled fallback formal write。
- 修改 prompt/provider/API/DB 行为来扩大本窗口。

## Provider Gate

必须满足：

- CompactProviderRequestBuilder required。
- No full prompt asset fallback。
- Forbidden keys rejected。
- Provider request schema-bound。
- Provider request redacted。
- Provider request traceable。
- Provider unavailable fail-closed。
- Validation failed fail-closed。

Forbidden keys：

- raw_prompt
- system_prompt
- developer_prompt
- raw_completion
- provider_payload
- raw_provider_payload
- full_resume
- full_jd
- full_answer
- full_asset_body
- token
- secret
- cookie
- api_key

## Canonical Evidence Gate

必须满足：

- CanonicalEvidencePack 是 Question / Feedback / Progress / Scoring / Training loop 的共享事实契约。
- source_support_summary 包含 level / refs / reason_codes / confidence。
- asset_confirmed 是 canonical asset 正常事实来源。
- asset_archived 不作为默认事实源。
- 当前回答新事实不能直接成为正式资产。
- asset conflict 必须 HITL。
- context_digest 稳定。

## Fake Gate

必须满足：

- Fake 只能用于 tests / evals / replay。
- Runtime env 不允许 fake provider。
- Fake path 不得伪装真实 provider success。
- Fake output 必须 trace visible。
- Fake imports 不得污染 production runtime wiring。

## Traceability Gate

必须满足：

- Capability ID 更新。
- Matrix 状态更新。
- Decision Log 更新。
- Risk Register 更新。
- Acceptance Gate 更新。
- Project source backfill。
- Gap closed 或 deferred。

## Done Gate

Capability 标记 done 必须同时满足：

- 设计更新。
- 代码迁移。
- 旧位置不再承载职责。
- 单测通过。
- 必要 eval 通过。
- 验证运行。
- 无 forbidden scope 修改。
- Project source 回填。
- 用户确认需要确认的关键决策。
