---
title: DOCS02_MANUAL_AUDIT_REMEDIATION
type: review-remediation
status: fixed-pending-verification
owner: 技术架构 / 文档治理
source_task: AIFI-ARCH-006
permalink: ai-for-interviewer/docs/02-design/reviews/docs02-manual-audit-remediation
---

# docs/02-design 人工审计问题核验与整改记录

## 1. 记录边界

- 本文件记录人工审计四类问题的核验、证据、修复动作和复核清单。
- 本文件是 review / remediation evidence，不替代 active design docs。
- 修复后的事实已回写到 active design docs：`SCORING_SPEC.md`、`SEMANTICS_GLOSSARY.md`、`PERSISTENCE_MODEL.md`、`APPLICATION_FLOW_SPEC.md`、`TECH_DESIGN.md`、`DATA_MODEL.md`、`API_SPEC.md`、`PROMPT_SPEC.md` 和必要 prompt-contract 子文档。

## 2. Audit verdict summary

| 审计问题 | 判定 | 证据文件 | 现有设计已覆盖 | 仍缺什么 | 是否阻断 F5 | 是否阻断 F6 | 是否阻断 F7 | 修复到 active doc |
|---|---|---|---|---|---|---|---|---|
| 1. 评分机制缺少统一规则、算法、维度、权重、输入输出、落库和 API / Prompt 对应 | `partially_true` | `TECH_DESIGN.md` §14.2、`DATA_MODEL.md` §10、`API_SPEC.md` §4.4 / §7 / §8、`PROMPT_SPEC.md` §7.2、`JOB_MATCH_CONTRACTS.md`、`POLISH_CONTRACTS.md`、`PRESSURE_CONTRACTS.md`、`REPORT_CONTRACTS.md`、`F4_FULL_DESIGN_ACCEPTANCE.md` | 已覆盖 0-100 product scale、禁止精确通过概率、`ScoreResult`、`ScoreRuleVersion`、evidence、confidence、validation、low confidence 降级、部分评分 contract | 缺独立 canonical scoring spec；缺所有 score type 的默认维度、权重总和、公式、缺失维度处理、API / Prompt / persistence / F7 fixture 一张表 | 是，F5 无法稳定实现统一 scoring service | 部分，F6 可展示字段但无法判断不同分数含义 | 是，F7 缺权重、公式、缺失维度和每类 score fixture | 新增 `SCORING_SPEC.md`，并更新 TECH / API / PROMPT / scoring contracts |
| 2. “低置信度”等术语是否真实存在、是否定义清楚、是否存在系统虚假生成或语义漂移 | `partially_true` | `SHARED_CONTRACTS.md` §10.3 / §10.4、`PROMPT_SPEC.md` §6 / §7、`API_SPEC.md` §4.3、`DATA_MODEL.md` §10、`DOCS02_DEEP_SEMANTIC_RISK_REGISTER.md` | 低置信度真实存在，并已覆盖触发条件、failure signal、API 状态、不得写正式对象、source unavailable 和 validation failed | 缺跨文档 glossary；`available / partial / unavailable / mixed` 与 `source_*` canonical enum 的层级关系不够清晰；`validation_status` 值存在 `passed / failed` 与 canonical 值不一致 | 部分，状态语义不统一会造成后端分支漂移 | 是，F6 容易把 low confidence 当成功或错误态吞掉 | 是，F7 enum / state fixture 无统一断言 | 新增 `SEMANTICS_GLOSSARY.md`，并更新 TECH / API / PROMPT / SHARED |
| 3. 数据模型是否只有逻辑模型，是否缺少字段、API 映射、物理关系、1:N / M:N / join table 和去重设计 | `true` | `DATA_MODEL.md` §1 / §3 / §11 明确“不定义物理 schema”；`F4_TO_F8_READINESS_RISK_REGISTER.md` / `DOCS02_DEEP_SEMANTIC_REMEDIATION_MATRIX.md` 记录 persistence handoff 缺口 | 已覆盖逻辑对象、引用模型、状态、版本、candidate / confirmation、AI task、trace、evidence 和 logical schema 草案 | 缺 F5 persistence handoff：建议物理模型、PK、owner / actor、version、status、FK、unique、1:N / M:N、join / reference table、read model 与 API schema 映射 | 是，F5 会从逻辑对象自行推导物理关系 | 部分，F6 依赖 read model / API schema 稳定性 | 是，F7 无法验证 join table、历史引用、candidate 不转 formal | 新增 `PERSISTENCE_MODEL.md`，并更新 DATA / TECH / API |
| 4. API 是否只有字段设计，是否缺少实现编排、跨模型查询、打磨模式每次回答后的数据组装、LLM 调用时机、调用次数、Prompt 结构和持久化流程 | `partially_true` | `API_SPEC.md` §6-§8 已有 route / field contract；`TECH_DESIGN.md` §14.1 有 AI 编排总览；`POLISH_CONTRACTS.md` 有各 P-* 触发和输入；review docs 记录 API / orchestration 风险 | endpoint、字段、error、async task、F7 assertion 已较完整；Prompt contracts 覆盖输入、输出、validation、trace 和低置信度 | 缺 use-case orchestration spec，把 endpoint、模型读取 / 写入、AiTask、P-*、LLM call plan、Prompt 输入结构、持久化和响应串成流程；尤其打磨 answer save 与 feedback task 拆分不够集中 | 是，F5 会把 API 字段表误当业务流程 | 部分，F6 能调用 endpoint 但不知道每步任务状态与结果边界 | 是，F7 缺 end-to-end flow fixture | 新增 `APPLICATION_FLOW_SPEC.md`，并更新 TECH / API / PROMPT |

## 3. 同类问题审计分类

| 分类 | 命中情况 | 处置 |
|---|---|---|
| 1. canonical spec 缺失 | 评分、低置信度 glossary、persistence handoff、application flow 都缺独立 canonical 文档 | 已新增四份 active design docs |
| 2. 术语存在但生命周期不闭合 | Low Confidence、source availability、validation status、candidate / suggestion 存在但跨文档聚合值和 canonical 值关系不够清晰 | `SEMANTICS_GLOSSARY.md` 统一语义和映射 |
| 3. API endpoint 存在但 application flow 缺失 | `API_SPEC.md` endpoint 字段完整度较高，但缺每个 use case 的读取、写入、AiTask 和 LLM call plan | `APPLICATION_FLOW_SPEC.md` 补齐 14 个流程 |
| 4. Prompt contract 存在但没有映射到 API task / LLM call plan | P-* contract 详细，但“哪些合并一次调用、哪些 on-demand”分散 | `APPLICATION_FLOW_SPEC.md` 定义合并 / 独立 task 规则，PROMPT / child docs 加引用 |
| 5. DATA logical object 存在但缺 physical / persistence handoff | `DATA_MODEL.md` 明确不定义物理 schema | `PERSISTENCE_MODEL.md` 补 F5 handoff |
| 6. 状态枚举跨文档不一致 | `passed / failed`、`available / partial / unavailable / mixed` 与 canonical enum 混用 | `SEMANTICS_GLOSSARY.md` 给映射；API 保留兼容但 canonical 化 |
| 7. candidate / suggestion / formal object 边界不清 | 大体已清楚，但 persistence / flow 未集中描述 | `PERSISTENCE_MODEL.md` / `APPLICATION_FLOW_SPEC.md` 明确 confirmation 前不得 formal write |
| 8. 低置信度、source unavailable、validation failed 被普通 success 吞掉 | active docs 已多处禁止，但缺统一 F7 状态断言 | `SEMANTICS_GLOSSARY.md` 和新 F7 fixture 要求补齐 |
| 9. deferred_non_blocking 被误用为阻断性实现缺口 | 存在复杂算法、校准、provider、RAG 实现等合理 deferred；但评分公式、持久化关系、flow 不应继续 deferred | 本轮将阻断性 handoff 回写 active docs，保留复杂算法类 deferred |

## 4. 修复动作与修改文件

| 文件 | 修复动作 |
|---|---|
| `docs/02-design/SCORING_SPEC.md` | 新增评分 canonical spec，覆盖 score type、维度、权重、公式、正式落库、API / Prompt 映射和 F7 fixture |
| `docs/02-design/SEMANTICS_GLOSSARY.md` | 新增跨文档语义词汇表，统一 Low Confidence、validation、source availability 和 candidate / formal 边界 |
| `docs/02-design/PERSISTENCE_MODEL.md` | 新增 F5 persistence handoff，覆盖建议物理模型、关系、join / reference table、API schema 映射和去重边界 |
| `docs/02-design/APPLICATION_FLOW_SPEC.md` | 新增 application flow spec，覆盖 14 个流程、LLM call plan、Prompt 结构、低置信度、持久化和 F7 fixture |
| `docs/00-governance/DOCS_INDEX.md` | 登记新增 active design docs |
| `docs/02-design/TECH_DESIGN.md` | 增加 scoring / semantics / persistence / application flow 交接引用 |
| `docs/02-design/DATA_MODEL.md` | 明确逻辑模型到 `PERSISTENCE_MODEL.md` 的交接，避免 F5 自行推导物理模型 |
| `docs/02-design/API_SPEC.md` | 明确 endpoint contract 到 `APPLICATION_FLOW_SPEC.md` 的交接；更新 scoring canonical enum 和 `ScoreResultResponse` 字段 |
| `docs/02-design/PROMPT_SPEC.md` | 明确 P-* contract 到 application flow 的运行编排关系；评分细则以 `SCORING_SPEC.md` 为 canonical |
| `prompt-contracts/JOB_MATCH_CONTRACTS.md`、`POLISH_CONTRACTS.md`、`PRESSURE_CONTRACTS.md`、`REPORT_CONTRACTS.md`、`SHARED_CONTRACTS.md` | 增加 canonical scoring / semantics 引用，不重写 contract 正文 |

## 5. 仍保留的 deferred_non_blocking 项

- 真实招聘结果校准、复杂调参、复杂阈值和模型质量评估算法。
- provider、模型参数、embedding、向量库、RAG 索引和 token budget 具体数值。
- 资产质量算法、资产合并 / 替代 / 归档算法、复杂语义去重。
- 薄弱项合并、严重度、状态自动消减和训练优先级复杂算法。
- F8 release / ops / runbook / rollback / observability 输入仍按既有 `AR-F4-F8-003` 跟踪，不在本轮修复范围内。

## 6. F5 / F6 / F7 readiness 影响

| 阶段 | 整改后影响 |
|---|---|
| F5 后端实现 | 评分 service、persistence schema、AiTask 编排和 use-case flow 有 active handoff；仍需 F5 选择实际 DB / queue / worker 实现 |
| F6 前端接入 | API status、low confidence、candidate / confirmation、copy boundary 和 scoring fields 有更稳定解释；前端仍以 `API_SPEC.md` endpoint 为调用事实源 |
| F7 contract tests | 新增 scoring、semantics、persistence、application flow fixture 依据；可验证 no exact probability、answer save no LLM、feedback merged call、join table、source unavailable 和 candidate-only |

## 7. 后续复核清单

- `rg -n "pass_probability|offer_probability|admission_probability|pass_rate_percent|73%|必过|必挂" docs/02-design`
- `rg -n "SCORING_SPEC|SEMANTICS_GLOSSARY|PERSISTENCE_MODEL|APPLICATION_FLOW_SPEC" docs/00-governance/DOCS_INDEX.md docs/02-design`
- `rg -n "polish_round" docs/02-design/API_SPEC.md docs/02-design/SCORING_SPEC.md`
- `rg -n "source_available|source_archived|source_deleted|source_disabled|source_unavailable" docs/02-design/SEMANTICS_GLOSSARY.md docs/02-design/API_SPEC.md docs/02-design/PROMPT_SPEC.md`
- `rg -n "POST /api/v1/polish-sessions/\\{session_id\\}/answers|POST /api/v1/polish-sessions/\\{session_id\\}/feedback|P-POLISH-003|P-POLISH-004|P-POLISH-005|P-POLISH-009" docs/02-design/APPLICATION_FLOW_SPEC.md`
- `git diff --check`

## 8. 当前状态

Status: `Fixed / Pending verification`。

本记录不标记整体 F4 accepted，不创建 final acceptance approval，不关闭 `AR-F4-F8-003`，不进入 implementation。
