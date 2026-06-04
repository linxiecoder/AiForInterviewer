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