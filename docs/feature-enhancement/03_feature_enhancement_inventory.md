---
title: 功能强化重构清单
type: inventory
status: draft
owner: architecture-review
permalink: ai-for-interviewer/feature-enhancement/feature-enhancement-inventory
---

# 功能强化重构清单

## 1. 目的与范围

本文档是 Phase 3 功能强化重构清单，用于把参考 Skill 复用综合结论整理成普通工程师可以人工审计的设计清单和重构候选清单。

本文只定义清单，不执行代码修改，不生成 Spec Kit 文档，不生成 Codex Goal，不修改业务代码、测试代码、配置、依赖、lockfile、CI 或 generated files。

本文的主要输入是 `docs/feature-enhancement/02b_reuse_synthesis.md`。`docs/feature-enhancement/01_project_architecture_assessment.md` 和 `docs/feature-enhancement/02_reference_skill_capability_study.md` 只作为辅助证据：它们帮助解释项目现状和参考 Skill 的证据边界，但不直接生成 FE 清单。

`.codex/feature-enhancement/feature_enhancement_inventory.yaml` 当前属于本地忽略路径，不作为本轮提交内容。本轮只修订 Markdown 人工审计文档；若后续确实需要机器可读清单入库，应在单独授权窗口把清单转写到 `docs/feature-enhancement/03_feature_enhancement_inventory.yaml`。

## 2. 输入材料与优先级

| 优先级 | 输入材料 | 本文使用方式 | 边界 |
| --- | --- | --- | --- |
| 主要输入 | `docs/feature-enhancement/02b_reuse_synthesis.md` | 提供 RDP、REUSE、ADB 和 FE-SEED，并作为 FE 清单的唯一生成来源 | 可以生成清单，但不代表可以直接实现 |
| 辅助证据 | `docs/feature-enhancement/01_project_architecture_assessment.md` | 解释项目已有模块、已有证据、partial / skeleton / default-off / fake / replay / deterministic 等 non-claim 边界 | 不能单独生成新 FE |
| 辅助证据 | `docs/feature-enhancement/02_reference_skill_capability_study.md` | 解释 Interview-coach 参考 Skill 的能力分层和证据类型 | 不能把参考 Skill 当作项目实现 |
| 治理约束 | `AGENTS.md` | 约束 active docs、写入边界、archive 边界和禁止事项 | 不允许新建并行计划体系 |
| 治理约束 | `docs/00-governance/DOCS_INDEX.md` | 确认当前有效文档体系和后续 handoff 入口 | 不替代 `BACKLOG.md` 或 `DELIVERY_PLAN.md` |

优先级规则如下：

1. FE 项必须能追溯到 `02b_reuse_synthesis.md` 中的 RDP / REUSE / ADB / FE-SEED。
2. `01_project_architecture_assessment.md` 只用于解释项目证据是否存在。
3. `02_reference_skill_capability_study.md` 只用于解释参考 Skill 可以借鉴什么、不能照搬什么。
4. 所有后续实施入口仍必须回到 active docs、`BACKLOG.md`、`DELIVERY_PLAN.md` 或 ADR；本文不是任务入口。

## 3. 清单生成规则

本文把 `02b_reuse_synthesis.md` 的候选种子整理为 FE-* 项。生成规则是先判断项目问题，再判断参考实践，再判断项目证据，最后给出 `proposed`、`research`、`deferred` 或 `rejected`。

| 规则 | 人工审查含义 |
| --- | --- |
| RDP 是可复用设计原语 | RDP 解释“可借鉴的机制”，不是任务编号，也不是实现承诺 |
| REUSE 是采用判断 | `adopt` / `adapt` / `reject` / `research` 只说明复用方式，不自动变成代码任务 |
| ADB 是采用说明 | ADB 只为 strong / medium 候选解释为什么值得进入后续规格阶段 |
| FE-SEED 是候选种子 | FE-SEED 可以合并、拆分、降级或拒绝，但必须保留来源追踪 |
| NEW_FROM_REFERENCE 需要特别审查 | NEW_FROM_REFERENCE 代表该方向主要来自参考 Skill，不代表马上可实现 |
| project_evidence_missing 阻断实现 | 标记 `project_evidence_missing` 的项不能直接进入实现，只能是 `research` 或 `deferred`，极端情况下可 `rejected` |
| reference evidence 降级使用 | `design-only`、`schema_like_design`、`release_note_claim`、examples 都不能写成 `executable_evidence` |
| non-claim 优先 | fake / replay / deterministic / default-off 只能说明本地回归、回放或默认关闭边界，不能写成 live-provider quality |

证据词解释：

| 词 | 中文解释 | 本文处理方式 |
| --- | --- | --- |
| `executable_evidence` | 项目中已有代码、测试、脚本、CI、schema 或可执行 guard 证据 | 可以支持 `proposed`，但仍需明确验证范围 |
| `design-only` | 参考 Skill 只有 Markdown workflow、说明或人工流程 | 只能作为设计素材，不是实现证据 |
| `schema_like_design` | 参考 Markdown 看起来像 schema，但不是项目 schema、migration 或 validator | 只能触发项目原生 schema 研究 |
| `release_note_claim` | release notes 或版本说明中的能力描述 | 只能作为演进意图，不是 migration 或实现证明 |
| `project_evidence_missing` | 当前项目缺少对应代码、测试、产品面、数据或隐私边界 | 不得直接进入实现 |
| `unsupported_or_unknown` | 证据不足或无法确认 | 默认研究、延后或拒绝 |

## 4. 分类标准

分类解释：

| 分类 | 中文解释 | 典型判断 |
| --- | --- | --- |
| `product_feature` | 面向用户可见体验或产品流程的能力强化 | Workbench、Polish、Assets、Resume/Job binding 等已有 surface 的体验增强 |
| `engineering_guardrail` | 防止 contract drift、false claim、provider 泄漏、默认关闭误写的工程护栏 | schema parity、static guard、non-claim wording、contract snapshot |
| `agent_workflow` | 约束开发者或 AI 如何读取材料、选择命令和执行受控窗口 | lazy reference loading、doc-governor command matrix、scope-aware packet |
| `docs_governance` | 保证候选进入 active docs，而不是新建平行计划体系 | BACKLOG / DELIVERY_PLAN / DOCS_INDEX handoff |
| `research` | 有潜在价值，但缺少项目证据、数据边界、隐私边界或 UX 决策 | transcript、outcome、role/JD routing、project-native state |
| `deferred` | 当前不适合进入后续规格阶段，但可保留为未来发现项 | storybank 到 Assets 生命周期 |

状态解释：

| 状态 | 中文解释 | 可做什么 | 不能做什么 |
| --- | --- | --- | --- |
| `proposed` | 有项目承接面，适合进入后续人工审查和规格阶段 | 可进入后续 Spec Kit 规格准备或受控 Goal 拆分 | 不能跳过 active docs 和验证方案直接实现 |
| `research` | 方向有价值，但关键项目证据不足 | 只能产出发现报告、边界说明、样例计划或人工评审材料 | 不能创建实现任务 |
| `deferred` | 方向可能有价值，但当前阶段证据和产品边界都不够 | 保留为后续候选或 discovery backlog | 不能进入当前规格或实现 |
| `rejected` | 当前直接采用会制造误导、安全风险或 false implementation claim | 可保留拒绝原因和更安全替代方案 | 不能以变体绕过拒绝原因进入实现 |

## 5. 清单总览

| FE | 中文名称 | 分类 | 状态 | 来源 | 审计结论 |
| --- | --- | --- | --- | --- | --- |
| FE-001 | 能力状态与 non-claim 护栏 | `engineering_guardrail` | `proposed` | RDP-006, RDP-017; REUSE-001, REUSE-010; ADB-001, ADB-010; FE-SEED-001, FE-SEED-007 | 先保护 capability status、UI wording 和 false-claim 边界 |
| FE-002 | 后端/前端 API 契约漂移护栏 | `engineering_guardrail` | `proposed` | RDP-005; REUSE-002; ADB-002; FE-SEED-002 | 后端和前端 evidence / confidence 字段需要 parity guard |
| FE-003 | Workbench 状态感知动作路由与 recommended next | `product_feature` | `proposed` | RDP-003, RDP-010; REUSE-005; ADB-005; FE-SEED-003 | 可在已有 Workbench action/state 证据上细化 |
| FE-004 | Polish 进度树与 next-action 证据门禁 | `product_feature` | `proposed` | RDP-005, RDP-010; REUSE-006, REUSE-018; ADB-006, ADB-012; FE-SEED-004, FE-SEED-006 | 可把 input readiness、gate、redo、next action 显式化 |
| FE-005 | 反馈纠错捕获闭环 | `product_feature` | `proposed` | RDP-011; REUSE-007; ADB-007; FE-SEED-005 | 可先记录 correction，不宣称自动学习 |
| FE-006 | 现有 surface 一致性护栏 | `product_feature` | `proposed` | RDP-013; REUSE-008; ADB-008; FE-SEED-010 | 仅限 Resume/Job/Assets/Polish 等已有 surface |
| FE-007 | examples 行为契约种子 | `engineering_guardrail` | `proposed` | RDP-016; REUSE-003; ADB-003; FE-SEED-008 | examples 只能转成验收语义和后续测试种子 |
| FE-008 | lazy reference loading 与 doc-governor 命令矩阵 | `agent_workflow` | `proposed` | RDP-002, RDP-004, RDP-018; REUSE-004, REUSE-017; ADB-004, ADB-011; FE-SEED-009 | 是工作流和命令矩阵，不是代码 enforcement |
| FE-009 | active docs 交接与兼容清单 | `docs_governance` | `proposed` | RDP-015, RDP-018; REUSE-009; ADB-009; FE-SEED-009 | 后续候选必须回到 active docs 和正式任务入口 |
| FE-010 | role/JD-specific 练习路由研究 | `research` | `research` | RDP-007, RDP-010, RDP-013; REUSE-011; FE-SEED-011 | 缺 human labels、golden cases 和 role drill map |
| FE-011 | storybank 到 Assets / reusable interview evidence 生命周期 | `deferred` | `deferred` | RDP-009; REUSE-013; FE-SEED-012 | Assets 只是类比面，storybank 生命周期缺项目证据 |
| FE-012 | transcript / 输入质量门禁研究 | `research` | `research` | RDP-008; REUSE-012; FE-SEED-013 | transcript ingestion、隐私、fixture、parser ownership 缺失 |
| FE-013 | outcome drift / calibration loop 边界 | `research` | `research` | RDP-012; REUSE-014; FE-SEED-014 | 缺 outcome log、授权和 correlation 方法 |
| FE-014 | 项目原生 coaching state 生命周期 | `research` | `research` | RDP-001; REUSE-016; FE-SEED-015 | 不能复制参考 `coaching_state.md`，需先盘点项目状态所有权 |
| FE-015 | bounded challenge protocol 政策 | `research` | `rejected` | RDP-014; REUSE-015; FE-SEED-016 | 缺 opt-in、stop condition、安全文案和 resolution，当前拒绝直接采用 |

## 6. 建议进入后续规格阶段的事项

第一批建议只进入 `proposed` 项，且先做护栏再做体验：

| 优先级 | FE | 建议 | 原因 |
| --- | --- | --- | --- |
| MUST | FE-001 | 先进入后续规格阶段 | 它保护所有后续 FE 不把 partial、design-only、fake、replay、deterministic、default-off 写成 live quality |
| MUST | FE-002 | 先进入后续规格阶段 | API/frontend contract drift 会直接影响 UI 的 source/confidence/evidence 表达 |
| SHOULD | FE-007, FE-009 | 与 FE-001 同批或紧随其后 | examples seed 和 active docs handoff 是防止 false implementation claim 的文档/验证基础 |
| SHOULD | FE-003, FE-004, FE-005 | 第二批产品体验规格 | Workbench / Polish 已有 partial 项目证据，但需要明确状态机、输入质量和 correction 边界 |
| SHOULD | FE-008 | 与文档治理或 doc-governor 规格合并 | lazy reference loading 和 command matrix 是人工审计友好化的工作流支撑 |
| COULD | FE-006 | 有条件进入 | 必须限定到 Resume/Job/Assets/Polish，不扩展 LinkedIn/outreach/salary 等不存在 surface |

这些项进入规格阶段前仍需人工审查：确认 scope、allowlist、验证命令、non-claim wording 和 active docs handoff。

## 7. 研究项

以下 FE 只能研究，不能直接实现：

| FE | 研究问题 | 缺少的项目证据 | 最小研究产物 |
| --- | --- | --- | --- |
| FE-010 | role/JD-specific practice routing 是否能基于现有 JD、target role、question category 做最小路由 | human labels、golden cases、role drill map、outcome data | role/JD drill taxonomy、人工 rubric 样例、不可宣称 calibration 的边界 |
| FE-012 | transcript / input quality gate 是否属于当前产品边界 | transcript input、storage、privacy、fixture、parser tests | 输入模型、隐私边界、fixture 计划、quality gate 规则 |
| FE-013 | outcome drift / calibration loop 是否有合法稳定数据来源 | outcome log、用户授权、correlation method、低样本处理 | outcome 数据分类、consent/privacy、non-claim wording |
| FE-014 | project-native coaching state lifecycle 的 owner、trigger、archive 和 migration 边界是什么 | 统一 coaching state schema、migration、retention/archive rules | state inventory、owner map、schema brief、治理审查 |

研究项的共同规则：缺 `project_evidence_missing` 的关键证据前，不得转换为 implementation Goal。

## 8. 延后项

| FE | 延后原因 | 后续重启条件 |
| --- | --- | --- |
| FE-011 | storybank → Assets / reusable interview evidence lifecycle 有产品价值，但当前只有 Assets 类比面；缺 story schema、STAR evidence、source refs、retirement/enhancement lifecycle 和 tests | 先完成 Assets mapping decision、隐私边界、story asset schema 草案，再判断扩展 Assets 还是新建 Story/Experience model |

FE-011 延后并不代表拒绝 storybank。它代表当前证据不足，不能把 storybank 写成现有 Assets 已实现，也不能绕过产品和数据边界直接进入规格。

## 9. 拒绝项

| FE | 拒绝内容 | 拒绝原因 | 更安全的替代方案 |
| --- | --- | --- | --- |
| FE-015 | 直接复制 Interview-coach 的 bounded challenge protocol 或 Level 5 challenge 进入产品反馈/练习流 | 当前缺少用户 opt-in、stop condition、安全文案、resolution 机制和 UX 审查；直接采用会压过用户意图并制造安全风险 | 保留 policy research 问题；未来若重启，先定义 opt-in、停止规则、用户可见文案和人工 review gate |

## 10. FE 项详细说明

### FE-001 能力状态与 non-claim 护栏

| 审查项 | 说明 |
| --- | --- |
| 要解决什么问题 | Phase 3 会引入大量参考设计，如果不先锁 claim 边界，容易把 partial、skeleton、design-only、fake、replay、deterministic、default-off 写成已实现或 live-provider quality。 |
| 为什么值得做 | 它是后续所有 FE 的前置安全带，能保护文档、UI copy、eval report 和实现任务不出现 false claim。 |
| 来自项目的证据 | capability preservation 证据、skeleton guard、eval non_claims、runtime default-off flags 和既有状态词。 |
| 借鉴了 Interview-coach 的什么实践 | RDP-006 / RDP-017 的 non-claim discipline 和 claim boundary UI wording。 |
| 哪些做法可以吸收 | 固定 capability status、evidence status、non_claims、low confidence、source availability、UI wording rules。 |
| 哪些做法不能照搬 | 不能把参考 Skill 的 Markdown 规则写成项目已有代码 enforcement。 |
| 本轮范围包括什么 | 定义 FE 清单中的 evidence/status/claim boundary 字段和后续人工审查要求。 |
| 本轮范围不包括什么 | 不新增测试、不改 UI、不改 runtime、不证明 live-provider quality。 |
| 后续如何验证 | static rg guard、capability wording guard、focused tests、UI wording review。 |
| 风险是什么 | 过度保守会让真实进展难表达；后续需允许有证据支撑的 implemented 状态。 |
| 为什么是 proposed | 项目已有 `executable_evidence` 和明确复用价值，适合进入后续规格阶段。 |

### FE-002 后端/前端 API 契约漂移护栏

| 审查项 | 说明 |
| --- | --- |
| 要解决什么问题 | 后端 Pydantic schema 与前端 TypeScript type 手写同步，source/confidence/evidence 字段容易 drift。 |
| 为什么值得做 | Workbench、Polish 和 claim boundary UI 都依赖这些字段；字段漂移会让前端无法正确表达证据边界。 |
| 来自项目的证据 | `apps/api/app/schemas/envelope.py`、`apps/web/src/shared/api/envelope.ts`、scoring/confidence schema 和 route snapshot。 |
| 借鉴了 Interview-coach 的什么实践 | RDP-005 的 evidence/confidence sourcing，把 source availability、evidence refs 和 low confidence 当作一等字段。 |
| 哪些做法可以吸收 | contract parity、schema field mapping、source/confidence/evidence 的统一语义。 |
| 哪些做法不能照搬 | 不能因为参考文档有 evidence-sourcing 就新建宽泛证据框架或真实 provider quality claim。 |
| 本轮范围包括什么 | 在清单中定义 contract drift guard 的问题、证据、范围和验收方向。 |
| 本轮范围不包括什么 | 不生成 schema、不改 API、不跑 TypeScript、不接入 provider。 |
| 后续如何验证 | schema parity、route snapshot、TS/static guard、字段渲染测试。 |
| 风险是什么 | 字段过早泛化会扩大 API surface；应优先覆盖现有 envelope。 |
| 为什么是 proposed | 项目有明确承接面，且参考实践可直接转成 guardrail 设计。 |

### FE-003 Workbench 状态感知动作路由与 recommended next

| 审查项 | 说明 |
| --- | --- |
| 要解决什么问题 | Workbench 中发送回答、换一道题、继续追问、查看反馈、完成练习等动作状态复杂，人工审计不容易看清哪一步被允许。 |
| 为什么值得做 | recommended next action 能降低用户困惑，也能让前端状态和测试更可审计。 |
| 来自项目的证据 | `InterviewPage.tsx`、`InterviewPage.test.ts`、`tests/web/test_interview_actions.py` 的 action/state partial evidence。 |
| 借鉴了 Interview-coach 的什么实践 | RDP-003 / RDP-010 的 mode routing、gated progression 和 recommended next action。 |
| 哪些做法可以吸收 | 把 `regenerate_current_node`、`new_question`、answer submit、feedback next action、complete 分开建模。 |
| 哪些做法不能照搬 | 不能复制参考 Skill 的 Markdown command router，也不能把 agent command 当产品 runtime router。 |
| 本轮范围包括什么 | 定义 Workbench action view model 的清单项和后续验证方向。 |
| 本轮范围不包括什么 | 不改 `InterviewPage.tsx`，不调整 UI 文案，不改后端接口。 |
| 后续如何验证 | frontend helper tests、static action guard、UI label/disabled state checks。 |
| 风险是什么 | 抽象过度会拉大改动面；后续应先做可测试 view model，不做大重构。 |
| 为什么是 proposed | Workbench 已有 partial 项目证据，可在既有 surface 上收敛。 |

### FE-004 Polish 进度树与 next-action 证据门禁

| 审查项 | 说明 |
| --- | --- |
| 要解决什么问题 | Polish 输入不足、反馈未消化或证据缺失时，系统可能仍给出过度完整的下一步或反馈。 |
| 为什么值得做 | progress tree、input readiness、redo gate 和 next action 能让用户知道该补资料、复练还是继续。 |
| 来自项目的证据 | Polish feedback validation、warnings、source support policy、Workbench/Polish progress tree partial evidence。 |
| 借鉴了 Interview-coach 的什么实践 | RDP-005 / RDP-010 的 input readiness、gated progression 和 evidence-aware next action。 |
| 哪些做法可以吸收 | 输入不足时显示 missing evidence、low confidence、补充 JD/回答的 recommended next；允许继续但显示边界。 |
| 哪些做法不能照搬 | 不能偷渡 transcript feature，也不能把 Polish gate 扩成 Training 主流程。 |
| 本轮范围包括什么 | 定义 Polish progress tree 和 next-action evidence gating 的设计清单。 |
| 本轮范围不包括什么 | 不实现 transcript parser，不新建 Training，不改变评分算法。 |
| 后续如何验证 | API warning tests、UI notice tests、contract tests、claim wording guard。 |
| 风险是什么 | gate 过严会阻断用户探索；需要保留“继续但低置信”的产品路径。 |
| 为什么是 proposed | 项目已有 validation/warning 承接面，适合后续规格化。 |

### FE-005 反馈纠错捕获闭环

| 审查项 | 说明 |
| --- | --- |
| 要解决什么问题 | 用户指出 AI 反馈不准、缺少事实或误解 JD 时，当前 correction 还没有清晰的捕获和审计闭环。 |
| 为什么值得做 | correction capture 能减少重复误判，并为后续人工审查和低置信策略提供输入。 |
| 来自项目的证据 | feedback validation、low confidence warnings、provider redaction guard、Polish feedback service tests。 |
| 借鉴了 Interview-coach 的什么实践 | RDP-011 的 human correction loop：capture first, analyze later。 |
| 哪些做法可以吸收 | 记录 correction note、source refs、review state、low confidence reason 和 audit trail。 |
| 哪些做法不能照搬 | 不能宣称自动学习、自动校准或模型质量提升。 |
| 本轮范围包括什么 | 定义 correction capture 的清单边界和后续验证方向。 |
| 本轮范围不包括什么 | 不改模型、不做 automatic calibration、不引入新的训练闭环。 |
| 后续如何验证 | API schema tests、UI state tests、redaction checks、non-claim wording guard。 |
| 风险是什么 | correction 可能包含敏感信息，必须有 redaction 和 data boundary。 |
| 为什么是 proposed | 项目已有 feedback validation 和 warnings，可先做捕获而不做自动学习。 |

### FE-006 现有 surface 一致性护栏

| 审查项 | 说明 |
| --- | --- |
| 要解决什么问题 | Resume、Job、Assets、Polish 等已有 surface 可能使用不同事实、JD 约束或 asset refs，导致面试证据不一致。 |
| 为什么值得做 | 限定在已有 surface 内做 consistency guard，可以提升产品可信度且不扩展新产品线。 |
| 来自项目的证据 | Resume/Job/Assets/Polish partial evidence 和已有 JD binding。 |
| 借鉴了 Interview-coach 的什么实践 | RDP-013 的 cross-surface consistency 和 shared source boundary。 |
| 哪些做法可以吸收 | 共享 source refs、JD binding、asset usage 和 evidence boundary。 |
| 哪些做法不能照搬 | 不能复制 LinkedIn/outreach/salary 等当前项目不存在的 surface。 |
| 本轮范围包括什么 | 把 FE-006 定义为仅限 existing surfaces 的 proposed 项。 |
| 本轮范围不包括什么 | 不新增 storybank，不新增外部职业平台 surface，不改 Assets 模型。 |
| 后续如何验证 | contract/static tests、source refs review、JD binding review。 |
| 风险是什么 | 容易把 storybank 或不存在 surface 偷渡进来；后续必须明确 allowlist。 |
| 为什么是 proposed | 现有 surface 有部分证据；在限定范围内可以进入规格阶段。 |

### FE-007 examples 行为契约种子

| 审查项 | 说明 |
| --- | --- |
| 要解决什么问题 | 参考 Skill 的 examples 有行为表达价值，但没有执行性，容易被误写成测试。 |
| 为什么值得做 | 把 examples 降级为 behavior-contract seeds，可以帮助定义验收语义，而不制造虚假测试通过。 |
| 来自项目的证据 | 项目已有 pytest / TypeScript 测试入口，可在后续实现窗口承接。 |
| 借鉴了 Interview-coach 的什么实践 | RDP-016 的 examples as behavior-contract seeds。 |
| 哪些做法可以吸收 | acceptance wording、golden case intent、人工审查样例。 |
| 哪些做法不能照搬 | 不能把 examples 当 fixtures、tests 或 runtime behavior 已存在。 |
| 本轮范围包括什么 | 定义 examples 只能作为设计种子和验收语义。 |
| 本轮范围不包括什么 | 不新增 tests，不复制参考 examples 到项目测试目录。 |
| 后续如何验证 | 文档标记 guard；后续实现必须新增真实测试后才能升级为 `executable_evidence`。 |
| 风险是什么 | reference examples 可能带入不适合 AiForInterviewer 的产品假设。 |
| 为什么是 proposed | 该项是低风险工程 guardrail，有明确人工审计价值。 |

### FE-008 lazy reference loading 与 doc-governor 命令矩阵

| 审查项 | 说明 |
| --- | --- |
| 要解决什么问题 | Phase 3 材料多，开发者或 AI 容易过度读取 reference clone、误跑禁止命令，或把 Markdown workflow 当实现。 |
| 为什么值得做 | lazy reference loading 和 command matrix 能让人工审计知道什么时候读什么、哪些命令允许、哪些命令禁止。 |
| 来自项目的证据 | `tools/doc_governor/cli.py`、`package.json`、`DOCS_INDEX.md`、AGENTS workflow。 |
| 借鉴了 Interview-coach 的什么实践 | RDP-002 / RDP-004 / RDP-018 的 command registry、lazy reference loading 和 active docs handoff。 |
| 哪些做法可以吸收 | task-type command matrix、lazy reading packet、scope-aware command selection。 |
| 哪些做法不能照搬 | agent guardrail 不能写成 code enforcement；Markdown workflow 不能替代 runtime validation 或 tests。 |
| 本轮范围包括什么 | 定义 command matrix 和 lazy reading 的清单项。 |
| 本轮范围不包括什么 | 不改 doc governor，不改 package scripts，不执行 build/test/install。 |
| 后续如何验证 | doc governor preview、static rg、manual scope review。 |
| 风险是什么 | 命令矩阵容易随项目漂移，需要放入 active docs 或 doc governor 维护。 |
| 为什么是 proposed | 项目已有治理和 CLI 承接面，可进入后续规格。 |

### FE-009 active docs 交接与兼容清单

| 审查项 | 说明 |
| --- | --- |
| 要解决什么问题 | Phase 3 清单若不回到 active docs，容易变成新的平行计划入口。 |
| 为什么值得做 | active docs handoff 能保证后续任务仍由 `BACKLOG.md`、`DELIVERY_PLAN.md`、ADR 和相关 active docs 承接。 |
| 来自项目的证据 | `AGENTS.md`、`DOCS_INDEX.md`、`BACKLOG.md` / `DELIVERY_PLAN.md` 边界和 capability preservation 证据。 |
| 借鉴了 Interview-coach 的什么实践 | RDP-015 / RDP-018 的 versioned workflow evolution 和 governance handoff；reference release notes 只是 `release_note_claim`。 |
| 哪些做法可以吸收 | compatibility checklist、route snapshot、capability preservation、active docs registry review。 |
| 哪些做法不能照搬 | 不能把 release notes 写成 migration automation，不能新建 parallel plan。 |
| 本轮范围包括什么 | 定义后续 FE 如何进入 active docs 和正式任务体系。 |
| 本轮范围不包括什么 | 不修改 `BACKLOG.md`、`DELIVERY_PLAN.md` 或 `DOCS_INDEX.md`。 |
| 后续如何验证 | diff check、active docs registry review、route/capability snapshot review。 |
| 风险是什么 | checklist 被误当测试；后续需要可执行 guard 配套。 |
| 为什么是 proposed | 这是清单进入后续阶段的必要治理项。 |

### FE-010 role/JD-specific 练习路由研究

| 审查项 | 说明 |
| --- | --- |
| 要解决什么问题 | 当前 role/JD-specific practice routing 还没有清晰 taxonomy，无法证明不同岗位/JD 下推荐练习路径可靠。 |
| 为什么值得研究 | 角色和 JD 差异化练习有产品价值，但必须先有人工样例和边界。 |
| 来自项目的证据 | feedback score/confidence 和 JD binding partial evidence；role drill map 为 `project_evidence_missing`。 |
| 借鉴了 Interview-coach 的什么实践 | RDP-007 / RDP-010 / RDP-013 的 rubric calibration、role drill 和 cross-surface consistency。 |
| 哪些做法可以吸收 | 研究 JD category、target role、question category 与 practice path 的最小映射。 |
| 哪些做法不能照搬 | 不能宣称 automatic calibration、seniority scoring 或 outcome correlation。 |
| 本轮范围包括什么 | 把该项列为研究项，明确缺口和最小产物。 |
| 本轮范围不包括什么 | 不生成实现任务，不改推荐算法。 |
| 后续如何验证 | design brief、golden examples、manual rubric review。 |
| 风险是什么 | 过早实现会制造“按岗位精准训练”的虚假能力声明。 |
| 为什么是 research | 缺 human labels、golden cases、role-level mapping 和 outcome data。 |

### FE-011 storybank 到 Assets / reusable interview evidence 生命周期

| 审查项 | 说明 |
| --- | --- |
| 要解决什么问题 | storybank 是可复用面试素材生命周期，但当前项目只有 Assets 类比面，不能证明已有 storybank。 |
| 为什么值得保留 | 可复用面试证据、STAR story、source refs 和 retirement/enhancement 未来可能提升 Assets 价值。 |
| 来自项目的证据 | Assets 有类比面；storybank lifecycle、story schema、retirement tests 为 `project_evidence_missing`。 |
| 借鉴了 Interview-coach 的什么实践 | RDP-009 的 storybank lifecycle 和 story fit mapping。 |
| 哪些做法可以吸收 | 研究 story asset schema、来源、状态、复用范围、退役和增强规则。 |
| 哪些做法不能照搬 | 不能把 storybank 写成现有 Assets 已实现，也不能直接复制参考 storybank Markdown。 |
| 本轮范围包括什么 | 延后并记录重启条件。 |
| 本轮范围不包括什么 | 不新增 Story/Experience model，不改 Assets，不进入当前规格。 |
| 后续如何验证 | asset mapping brief、privacy review、schema proposal。 |
| 风险是什么 | 把 Assets 和 storybank 混同会造成数据模型和产品边界混乱。 |
| 为什么是 deferred | 有价值但当前证据不足，且需要产品/数据边界先行。 |

### FE-012 transcript / 输入质量门禁研究

| 审查项 | 说明 |
| --- | --- |
| 要解决什么问题 | transcript 分析若输入破碎、speaker mapping 不明或隐私边界不清，后续反馈会建立在错误输入上。 |
| 为什么值得研究 | input quality gate 的思想可借鉴，但 transcript 是否属于当前产品边界尚未确认。 |
| 来自项目的证据 | transcript ingestion、storage、privacy、fixture、parser tests 均为 `project_evidence_missing`。 |
| 借鉴了 Interview-coach 的什么实践 | RDP-008 的 transcript quality gate、format detection 和 speaker mapping。 |
| 哪些做法可以吸收 | 研究输入模型、隐私边界、fixture 计划和 quality gate 规则。 |
| 哪些做法不能照搬 | 不能偷渡 transcript parser、transcript API 或 storage 方案。 |
| 本轮范围包括什么 | 把 transcript quality gate 作为 research 项记录。 |
| 本轮范围不包括什么 | 不进入实现，不生成 parser，不改隐私模型。 |
| 后续如何验证 | discovery brief、fixture plan、privacy review。 |
| 风险是什么 | 过早实现会引入敏感数据和错误分析风险。 |
| 为什么是 research | 缺输入、存储、隐私、fixture 和 parser ownership 证据。 |

### FE-013 outcome drift / calibration loop 边界

| 审查项 | 说明 |
| --- | --- |
| 要解决什么问题 | outcome drift 需要真实结果反馈；没有合法稳定数据来源时，不能声称评分和真实面试结果相关。 |
| 为什么值得研究 | 如果未来有用户授权 outcome 数据，可用于校准边界和低样本提示。 |
| 来自项目的证据 | outcome log、用户授权、correlation method 均为 `project_evidence_missing`。 |
| 借鉴了 Interview-coach 的什么实践 | RDP-012 的 outcome drift boundary 和 insufficient data state。 |
| 哪些做法可以吸收 | outcome 数据分类、consent/privacy、non-claim wording、insufficient data 文案。 |
| 哪些做法不能照搬 | 不能写成录用预测、评分质量证明或 live-provider quality。 |
| 本轮范围包括什么 | 定义研究问题和拒绝 false outcome claim 的边界。 |
| 本轮范围不包括什么 | 不收集 outcome，不做 correlation，不调整评分。 |
| 后续如何验证 | privacy/design review、manual policy review。 |
| 风险是什么 | 结果数据敏感且易被误解为招聘预测。 |
| 为什么是 research | 缺 outcome log、consent 和 correlation 方法。 |

### FE-014 项目原生 coaching state 生命周期

| 审查项 | 说明 |
| --- | --- |
| 要解决什么问题 | 面试辅导状态跨 Resume、Job、Assets、Polish、Workbench，但当前没有统一 project-native coaching state 生命周期。 |
| 为什么值得研究 | 状态 owner、update trigger、archive/retention 和 migration 边界清楚后，后续才可能安全扩展。 |
| 来自项目的证据 | 统一 coaching state schema、migration、archive rules 为 `project_evidence_missing`。 |
| 借鉴了 Interview-coach 的什么实践 | RDP-001 的 state lifecycle、update trigger 和 migration note；参考 `coaching_state.md` 是 `schema_like_design`。 |
| 哪些做法可以吸收 | 研究 state owner、update trigger、retention/archive 和兼容性 checklist。 |
| 哪些做法不能照搬 | 不能复制 `coaching_state.md`，不能生成 migration，不能绕过现有 DB/API/privacy 边界。 |
| 本轮范围包括什么 | 把 project-native lifecycle 作为 research 项。 |
| 本轮范围不包括什么 | 不新建 schema，不写 migration，不改数据模型。 |
| 后续如何验证 | state inventory、schema brief、governance review。 |
| 风险是什么 | 复制参考 schema 会制造与项目现有模型冲突的伪事实源。 |
| 为什么是 research | 缺 project-native state owner 和可执行 schema 证据。 |

### FE-015 bounded challenge protocol 政策

| 审查项 | 说明 |
| --- | --- |
| 要解决什么问题 | bounded challenge protocol 可能提升反馈强度，但无边界挑战会压过用户意图。 |
| 为什么值得记录 | 记录拒绝原因可防止后续把参考 Skill 的 challenge protocol 偷渡进产品流。 |
| 来自项目的证据 | product UX opt-in、stop condition、safety copy、resolution 均不足。 |
| 借鉴了 Interview-coach 的什么实践 | RDP-014 的 bounded challenge protocol；参考为 `design-only`。 |
| 哪些做法可以吸收 | 仅保留 policy research 问题：opt-in、stop rule、resolution、review gate。 |
| 哪些做法不能照搬 | 不能直接复制 Level 5 challenge、强压式反馈或无退出机制的挑战流程。 |
| 本轮范围包括什么 | 明确当前拒绝直接采用。 |
| 本轮范围不包括什么 | 不进入 Spec Kit，不进入 Codex Goal，不进入实现。 |
| 后续如何验证 | policy review、UX safety review。 |
| 风险是什么 | 无边界挑战会损害用户控制感和安全边界。 |
| 为什么是 rejected | 缺 opt-in、stop condition、安全文案和 resolution，直接采用风险大于收益。 |

## 11. 后续执行阶段建议

| 后续阶段 | 建议纳入 | 进入条件 |
| --- | --- | --- |
| Phase 4A Guardrail Spec | FE-001, FE-002, FE-007, FE-009 | 先锁 non-claim、contract drift、examples seed 和 active docs handoff |
| Phase 4B Workbench / Polish Product Spec | FE-003, FE-004, FE-005 | 只在既有 Workbench / Polish partial evidence 上细化用户路径 |
| Phase 4C Workflow Governance Spec | FE-008 | command matrix 与 lazy reading packet 需要回到 active docs 或 doc governor |
| Phase 4D Existing Surface Confirmation | FE-006 | 人工确认 existing surfaces allowlist 和 Assets 边界 |
| Phase 4E Research / Deferred / Reject Review | FE-010, FE-011, FE-012, FE-013, FE-014, FE-015 | 只做研究、延后或拒绝复核，不进入实现 |

执行阶段必须保持“小批量、可验证、可回退”。如果某个 FE 后续预计修改超过 5 个文件，应先给影响范围、风险点和验证方案，再开始改动。

## 12. 文档刷新规则

1. 本文不是 active requirement、delivery plan、BACKLOG 或 ADR。
2. 本文刷新时，必须优先回读 `docs/feature-enhancement/02b_reuse_synthesis.md`。
3. 若 `01_project_architecture_assessment.md` 或 `02_reference_skill_capability_study.md` 后续发生变化，只能作为辅助证据刷新本文，不能直接生成新 FE。
4. 后续若要把 FE 变成 active 任务，必须进入 `docs/03-delivery/BACKLOG.md`；若涉及阶段，必须进入 `docs/03-delivery/DELIVERY_PLAN.md`。
5. reference Skill 的 Markdown workflow、`schema_like_design`、examples 和 release notes 必须保持 reference inspiration，不得升级为 project `executable_evidence`。
6. fake / replay / deterministic / default-off 必须继续写成受限证据，不得写成 live-provider quality。
7. 研究、延后、拒绝项不得被后续文档改写成“已实现”。

## 13. 提交策略

本轮只准备一个后续修订提交的内容，不修改历史，不 amend，不 force push。

本轮不执行 `git add`、`git commit` 或 `git push`。若后续人工决定提交，提交内容应只包含：

- `docs/feature-enhancement/03_feature_enhancement_inventory.md`
- 可选：`docs/feature-enhancement/03_feature_enhancement_inventory.yaml`，仅当需要把机器可读清单入库时创建

如果 `git status --short --untracked-files=all` 出现上述范围外的文件状态，应停止并先处理 scope mismatch。

## 14. Spec Kit 进入规则

本文不执行 Spec Kit。后续只有满足以下条件的项才能进入 Spec Kit 规格阶段：

| 条件 | 说明 |
| --- | --- |
| 状态必须是 `proposed` | `research`、`deferred`、`rejected` 不可进入 |
| 必须有项目承接证据 | 至少有 partial `executable_evidence` 或明确的 existing surface |
| 必须有 non-claim boundary | 说明 fake / replay / deterministic / default-off / design-only 的处理方式 |
| 必须有验证面 | 明确后续 tests、static guard、schema parity、manual review 或 doc governor check |
| 必须回到 active docs | 不得把本文当 Spec，也不得绕过 `BACKLOG.md` / `DELIVERY_PLAN.md` |

最小首批建议是 FE-001 和 FE-002。它们保护所有后续候选的 claim boundary 和 backend/frontend contract boundary。

## 15. Codex Goal 转换规则

1. Codex Goal 只能从人工审查通过的 `proposed` FE 转换。
2. 每个 Goal 必须只覆盖一个 FE，或覆盖一个明确且可验证的 FE 子集。
3. Goal 必须列出 allowlist、forbidden files、验证命令、non-claim boundary 和 done condition。
4. `project_evidence_missing` 的 FE 不得转换为 implementation Goal。
5. `research`、`deferred`、`rejected` 不得转换为 implementation Goal。
6. fake、replay、deterministic、default-off 只能作为 regression / contract / local evidence，不能作为 live-provider quality。
7. agent workflow guardrail 只能约束工作流；若要变成代码 enforcement，必须另有可执行测试或 runtime validation 设计。

## 16. 人工审查清单

- [ ] 文档是否明确说明本文是 Phase 3 功能强化重构清单。
- [ ] 文档是否明确说明主要输入是 `docs/feature-enhancement/02b_reuse_synthesis.md`。
- [ ] 文档是否明确说明 01 和 02 只是辅助证据，不直接生成清单。
- [ ] 文档是否明确说明本文只定义清单，不执行代码修改。
- [ ] 每个 FE 是否说明要解决什么问题、为什么值得做、项目证据、参考实践、可吸收做法、不可照搬做法、本轮范围、非本轮范围、后续验证、风险和状态理由。
- [ ] `product_feature`、`engineering_guardrail`、`agent_workflow`、`docs_governance`、`research`、`deferred` 是否已有中文解释。
- [ ] `proposed`、`research`、`deferred`、`rejected` 是否已有中文解释。
- [ ] NEW_FROM_REFERENCE 是否明确不代表马上可实现。
- [ ] `project_evidence_missing` 是否明确不能直接进入实现。
- [ ] reference Skill 的 Markdown workflow、`schema_like_design`、examples、release notes 是否均未写成 executable implementation。
- [ ] fake / replay / deterministic / default-off 是否均未写成 live-provider quality。
- [ ] agent guardrail 是否没有被写成 code enforcement。
- [ ] FE-001 到 FE-009 是否只作为后续规格候选，不作为本轮实现。
- [ ] FE-010、FE-012、FE-013、FE-014 是否保持 research。
- [ ] FE-011 是否保持 deferred。
- [ ] FE-015 是否保持 rejected。
- [ ] 是否没有新增 roadmap、plan-v2、latest-plan、codex-plan 或平行任务体系。

## 17. 开放问题与下一步

1. FE-001 和 FE-002 是否作为第一批后续规格输入，先于所有产品体验增强。
2. FE-003 和 FE-004 是否拆成 Workbench action view model 与 Polish input readiness 两个规格，还是作为 Workbench / Polish next-action 统一规格。
3. FE-005 correction capture 的最小用户动作是“标记不准”“补充事实”“提交 correction note”，还是分阶段支持。
4. FE-006 的 existing surfaces 是否只包含 Resume/Job/Assets/Polish，Assets 中 story-like 用法是否需要额外排除。
5. FE-008 command matrix 是进入 doc governor，还是先进入 active docs governance 文档。
6. FE-010 role/JD-specific practice routing 是否有可用 human labels、golden cases 或人工 rubric 来源。
7. FE-011 storybank 未来是映射到 Assets，还是新建 Story/Experience model。
8. FE-012 transcript 是否属于当前产品边界；若属于，谁负责隐私、存储、fixture 和 parser ownership。
9. FE-013 outcome tracking 是否有合法稳定的数据来源和用户授权模型；没有时 UI 应如何说明不能做 outcome correlation。
10. FE-015 bounded challenge protocol 是否存在明确 opt-in 场景；没有时应继续保持 rejected。

下一步建议：先人工审查 FE-001 和 FE-002 的 scope、验证面和 active docs handoff，再决定是否进入后续规格阶段。研究、延后和拒绝项不应进入实现队列。
