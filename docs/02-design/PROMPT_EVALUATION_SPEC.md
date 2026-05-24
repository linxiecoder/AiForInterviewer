---
title: PROMPT_EVALUATION_SPEC
type: design
status: draft-f5-prompt-evaluation
owner: AI / Prompt 架构
source_task: AIFI-PROMPT-002
permalink: ai-for-interviewer/docs/02-design/prompt-evaluation-spec
---

# PROMPT_EVALUATION_SPEC

## 1. 文档目的与边界

本文承接 `AIFI-PROMPT-002`，定义 Prompt Evaluation Fixture、Prompt Regression Suite、质量指标、模型比较、人工评审、CI gate、release / rollback 规则。

本文只做文档设计，不新增或修改 `apps/**`、`tests/**`、依赖、migration 或 CI。本文中的 fixture path 和 test name 是后续实现输入；本轮不创建测试文件，不调用真实外部 LLM。

## 2. Fixture 类型

| 类型 | 目的 | 必须包含 | 禁止包含 |
|---|---|---|---|
| Golden Fixture | 证明 asset 在代表性成功输入下能生成 schema-valid、semantic-valid、evidence-valid 输出 | safe input summary、input refs、expected schema、expected validation status、accepted output shape | 真实完整简历 / JD、raw prompt、raw completion、provider payload |
| Regression Fixture | 锁定历史修复过的边界，避免 prompt / builder / validator 回退 | 历史 failure marker、expected fallback / repair / accept 结果、trace expectation | 模糊“文本更好”的主观断言 |
| Negative Fixture | 证明错误输出被拒绝、fallback、low confidence 或 manual review | counterexample input、invalid output、expected validation error、fallback reason | 把无证据输出修成成功 |
| Redaction Fixture | 证明敏感字段、provider payload、hidden rubric 和 system prompt 不外泄 | forbidden markers、scan target、expected no-match | 真实密钥或真实 provider payload |
| Model Comparison Fixture | 比较模型时的固定输入与评分 rubric | fixed input refs、metrics、cost / latency summary、provider gate | 以 provider 200 作为成功 |

## 3. Golden Fixtures

Golden fixtures 以 Prompt Asset 为单位管理，命名建议为 `golden.<asset_id>.<scenario>.vN`。每个 golden fixture 必须满足：

1. 输入只使用 safe summary、refs、脱敏片段和 compact evidence。
2. expected output 只断言结构、关键字段、evidence refs、confidence、candidate/formal boundary 和 forbidden output。
3. golden fixture 更新必须说明原因：contract 变更、schema 变更、validator 变更或人工接受的 prompt 改进。
4. golden fixture 不允许绕过 validator，也不允许用人工主观文本质量替代 schema / semantic / evidence 断言。

| Fixture Set | Golden Cases |
|---|---|
| `eval.polish.question.v1` | valid question, low confidence accepted, source unavailable visible, no answer leak |
| `eval.polish.feedback.v1` | valid first feedback, valid retry feedback, score repair accepted, low confidence accepted |
| `eval.polish.progress.v1` | quality-first menu, grounded tree, bad title rewritten / low confidence |
| `eval.pressure.*.v1` | per-stage valid output with pace / end / report handoff boundaries |
| `eval.report.*.v1` | report body, section score explanation, risk wording, copyable content |
| `eval.review.*.v1` | mock review, real input structuring, real review, review item extraction |
| `eval.jobmatch.*.v1` | match analysis, score, points, weakness candidate |

## 4. Regression Fixtures

Regression fixtures 必须覆盖已经出现过或高风险的 drift：

| Area | Required Regression |
|---|---|
| Polish question | `evidence_refs_invalid`、source ref 误作 evidence ref、object ref、empty refs、required elements missing、business constraint missing、重复题 |
| Polish feedback | schema invalid、metadata full evidence leak、score dimension mismatch、invalid retry improved point、retry without previous loss point、provider error redaction |
| Polish progress | selected evidence 原句误作 display title、unsupported 技术栈编造、low confidence 被覆盖 |
| Pressure | same-question loop、unsupported pressure tone、report input 被写成 report body、pace / pause signal ignored |
| Report | exact probability、hidden scoring rule、copy content redaction miss、source unavailable 被写成高置信 |
| Review | third-party privacy leak、unconfirmed real input、candidate formal write、review source trust flags missing |
| Job Match | score out of range、exact pass probability、weakness candidate formalized、missing evidence refs |

## 5. Negative Fixtures And Counterexamples

每个 Prompt Asset 至少要有一个 counterexample。Counterexample 的 expected result 只能是 validation failed、low confidence、fallback、manual review 或 rejected，不允许用 repair 把不可信输出改成成功。

| Counterexample Type | Expected Result |
|---|---|
| raw prompt / raw completion / provider payload appears | redaction failure and fallback / reject |
| evidence ref not in allowed refs | `evidence_refs_invalid` or equivalent semantic invalid |
| score without score rule version | validation failed or low confidence |
| exact pass probability | reject / rewrite to allowed risk tendency wording |
| formal object write request | reject; candidate-only boundary preserved |
| hidden rubric or calibration detail | reject / redact |
| source unavailable but high confidence | low confidence or validation failed |

## 6. Prompt Quality Metrics

| Metric | Definition | Passing Interpretation |
|---|---|---|
| `schema_valid_rate` | schema-valid outputs / total evaluated outputs | 结构化输出稳定；不能证明语义正确 |
| `semantic_valid_rate` | semantic-valid outputs / total evaluated outputs | required elements、business constraints、candidate/formal、score policy 等通过 |
| `evidence_ref_valid_rate` | evidence-valid outputs / outputs requiring evidence | 输出 evidence refs 是 allowed refs 的 exact subset |
| `repeat_question_rate` | duplicated / near-duplicated questions / generated questions | 越低越好；重复题必须触发 fallback 或 repair |
| `hallucination_rate` | unsupported facts / evaluated outputs | 必须接近 0；出现具体编造事实时 release blocked |
| `score_consistency_rate` | score fields consistent with dimension / rubric / rule version | 评分输出可解释且不越界 |
| `low_confidence_accuracy` | low-confidence labels matching expected weak evidence cases / weak evidence cases | 不允许资料不足时伪装高置信 |
| `fallback_rate` | fallback / total evaluated outputs | 过高说明 prompt 不稳定；过低可能说明 validator 太松 |

辅助指标可以记录 cost、latency、repair rate、manual review rate、redaction pass rate，但不得替代上表核心指标。

## 7. Model Comparison Policy

模型比较只能在显式授权和 provider gate 下执行。比较目标是结构化质量、边界遵守、成本和延迟，不是主观文案偏好。

| Rule | Requirement |
|---|---|
| Gate | 默认不调用真实 provider；必须显式启用 real-provider gate |
| Dataset | 使用同一 fixture set、同一 input refs、同一 redaction policy |
| Metrics | 至少记录 `schema_valid_rate`、`semantic_valid_rate`、`evidence_ref_valid_rate`、`hallucination_rate`、`fallback_rate`、cost 和 latency |
| Provider 200 | 只能证明 transport 成功，不能证明 prompt 成功 |
| Winner | 必须通过 validator、redaction、candidate/formal 和 evidence gates；不能只按文本流畅度选择 |
| Rollback | 新模型表现低于 baseline 或触发 forbidden output 时回滚到上一 `prompt_version` / model policy |

## 8. Fake Provider Vs Real Provider Gated Evaluation

| Evaluation Mode | Purpose | Allowed By Default | Required Evidence |
|---|---|---|---|
| deterministic fake provider | 验证 builder、schema、validator、fallback、redaction 和 regression fixtures | 是 | local tests / fixture runner |
| static fake output | 验证指定输出被 accept / reject / repair | 是 | exact validation status and fallback reason |
| real-provider smoke | 验证 provider integration and prompt behavior under gate | 否 | explicit env gate、raw-off scan、redaction scan、no external secret leak、manual approval |
| model comparison | 比较多个模型质量、成本、延迟和边界遵守 | 否 | fixed fixture set、metric report、rollback decision |

真实 provider 评估不得读取 `.env`、不得外泄 prompt / user data、不得把 provider payload 写入普通日志、checkpoint、API response 或 copy content。

## 9. Human Review Rubric

人工评审只补充自动指标，不能代替 validator。

| Dimension | Review Question |
|---|---|
| task fit | 输出是否只完成当前 `task_type`，没有扩展成完整业务流程 |
| evidence grounding | 关键结论是否能回到 allowed evidence refs |
| user value | 用户可见文本是否具体、可执行、不过度承诺 |
| safety | 是否避免 exact pass probability、hidden scoring rules、provider payload、敏感信息 |
| candidate boundary | 是否只输出 candidate / suggestion / draft，正式对象仍需确认 |
| low confidence | 资料不足、证据冲突、source unavailable 是否清楚降级 |
| legacy compatibility | 对已有 API / DTO / fallback 语义是否兼容 |

人工评审结果必须记录 reviewer、fixture set、asset_id、prompt_version、结论和 blocking comments。

## 10. CI Gates

本轮不修改 CI；以下是后续实现 gate 设计。未授权实现前，这些 gate 只作为 docs acceptance 输入。

| Gate | Scope | Failure Meaning |
|---|---|---|
| prompt fixture runner | asset fixture set | prompt asset not releasable |
| redaction scan | fixture output, API response, trace summary | release blocked |
| schema / semantic validation | all prompt outputs | prompt or validator drift |
| evidence ref exact subset | evidence-bearing outputs | hallucination / invalid citation risk |
| no formal write | candidate outputs | candidate/formal boundary broken |
| model comparison report | real-provider gated runs | cannot promote new model / prompt |
| `git diff --check` and doc governor | docs changes | documentation gate failed |

## 11. Prompt Release / Rollback Policy

| Step | Requirement |
|---|---|
| release candidate | new `prompt_version` registered in `PROMPT_ASSET_SPEC.md` or implementation manifest |
| fixture update | golden / regression / negative fixtures reviewed and versioned |
| validation | all local fake-provider gates pass; real provider only if explicitly gated |
| approval | human review accepts blocking rubric dimensions |
| rollout | runtime flag / per-asset version can select old or new version |
| rollback | failing asset reverts to `rollback_target_prompt_version`; trace records reason |
| deprecation | old version remains readable until all trace retention and replay needs expire |

Rollback must be fail-closed: if asset registry, schema, validator or evaluation fixture is missing, runtime must use deterministic fallback or previous accepted version rather than silently promoting an unregistered prompt.

## 12. Per-Asset Evaluation Matrix

| Asset Set | Required Metrics | Required Negative Fixtures | Release Readiness |
|---|---|---|---|
| `eval.polish.question.v1` | schema, semantic, evidence refs, repeat question, hallucination, fallback | fabricated entity, answer leak, invalid evidence refs, missing required elements | ready as design input; runtime tests already cover key cases |
| `eval.polish.feedback.v1` | schema, score consistency, evidence, low confidence, fallback | raw payload leak, invalid retry, score mismatch, provider error | ready as design input; runtime tests already cover key cases |
| `eval.polish.progress.v1` | schema, hallucination, grounding, low confidence | copied evidence title, unsupported topic, source unavailable | needs implementation fixture expansion before PR6 |
| `eval.pressure.*.v1` | schema, semantic, repeat question, pace, score consistency, fallback | same-question loop, unsupported pressure tone, report body leak | blocked by AIFI-BE-004 mode-level spec |
| `eval.report.*.v1` | schema, evidence, score consistency, low confidence, redaction | exact probability, hidden rubric, copy content leak | target PR8 |
| `eval.review.*.v1` | schema, evidence, privacy, candidate boundary, low confidence | third-party privacy leak, unconfirmed input, formal write | target PR8 |
| `eval.jobmatch.*.v1` | schema, score consistency, evidence, hallucination, fallback | exact probability, missing evidence, formal weakness write | PR6 conditional wrapper / descriptor parity |

## 13. AIFI-PROMPT-002 Readiness Verdict

`AIFI-PROMPT-002` 的 Prompt Evaluation 设计在本文和 `PROMPT_ASSET_SPEC.md` 同时登记后达到 implementation-ready 的文档标准。后续实现可以按 asset registry、fixture set、metrics、fake / real provider gate、human review rubric、CI gate 和 rollback policy 落测试与 runtime manifest。

该结论不授权 PR2 code implementation。PR2 仍需等待 `BACKLOG.md` 中其他 blocker 和 PR2 preflight gate 关闭，或主 Agent 显式接受风险并重新授权。

## 14. 变更记录

| 日期 | 变更 | 影响 |
|---|---|---|
| 2026-05-24 | 新增 Prompt Evaluation fixture / metric / release 设计 | 关闭 AIFI-PROMPT-002 的 evaluation 设计缺口；PR2 仍保持 blocked |
