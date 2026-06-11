---
title: Reuse Synthesis from Reference Skill
type: assessment
status: draft
owner: architecture-review
permalink: ai-for-interviewer/feature-enhancement/reuse-synthesis
---

# Reuse Synthesis from Reference Skill

## 1. Purpose and Inputs

本文是 Phase 2.5 的复用综合设计文档，用于把 Phase 1 的项目架构评估和 Phase 2 的参考 Skill 能力研究，转成 Phase 3 可以人工审计、可以拆分候选增强项、也可以拒绝误用的输入。本文不登记新任务，不替代 `docs/03-delivery/BACKLOG.md`，不替代 `docs/03-delivery/DELIVERY_PLAN.md`，也不把参考仓库的 Markdown workflow、schema_like_design、examples 或 release notes 写成当前项目的可执行能力。

本文的工作方式是：先把参考 Skill 拆成可复用设计原语，再与 AiForInterviewer 的现有证据逐项交叉，最后输出 adoption design brief 和 Phase 3 candidate seed。对没有项目证据的项，本文只给 `research` 或 `deferred`，不直接进入 `FE_candidate`。

| 输入 | 本文用途 | 证据边界 |
| --- | --- | --- |
| `docs/feature-enhancement/01_project_architecture_assessment.md` | 提供 AiForInterviewer 当前架构、问题、候选增强方向和 non-claim 事实 | project_assessment |
| `docs/feature-enhancement/02_reference_skill_capability_study.md` | 提供参考 Skill inventory、能力分层、证据分类和缺失项 | reference_capability_study |
| `AGENTS.md`, `docs/00-governance/DOCS_INDEX.md` | 提供当前 active docs 入口、写入边界、archive 边界和文档治理约束 | governance_evidence |
| `/tmp/interview-coach-skill-phase2-20260611` at `634a8dd8689e0420c21e5f0c8ae3cfa9e1a7ab7e` | 提供参考 Skill 原文证据 | direct_reference_text，但多数为 `design-only` |
| 项目源码、测试、CI 和现有文档 | 验证哪些参考设计已经有项目承接面，哪些仍是缺口 | `executable_evidence` 或 `project_evidence_missing` |

本文使用的证据词如下，后续章节保持同一含义：

| 词 | 含义 | Phase 3 含义 |
| --- | --- | --- |
| `executable_evidence` | 当前项目已有代码、测试、脚本、CI 或可执行 guard 证据 | 可进入 `FE_candidate` 或 `support_task`，仍需按 scope 验证 |
| `design-only` | 参考 Skill 只有 Markdown workflow、说明或规则 | 只能抽取设计，不可宣称实现 |
| `schema_like_design` | Markdown 看起来像 schema，但不是可执行 schema、migration 或 validator | 只能作为 schema 设计素材 |
| `release_note_claim` | 版本说明或发布说明中的能力描述 | 只能说明演进意图，不能证明实现 |
| `project_evidence_missing` | 当前项目未找到相应代码、测试或产品面 | 不得直接进入 `FE_candidate` |
| `unsupported_or_unknown` | 证据不足，无法支撑采用或拒绝以外的结论 | 默认 `research`、`deferred` 或 `reject` |

本文也明确把以下类别分开处理：

| 类别 | 说明 | 典型落点 |
| --- | --- | --- |
| 产品能力强化 | 面向用户可见能力或工作台体验的增强 | Workbench、Polish、Assets、Resume/Job binding |
| 工程 guardrail | 防止 contract drift、false claim、provider 泄漏、default-off 误写的工程约束 | schema/test/static guard/CI |
| agent workflow | 约束 AI/开发者读取、路由、文档消费方式 | command matrix、lazy reading packet |
| 文档治理 | 保证 Phase 3 候选进入 active docs，而不是并行计划体系 | `BACKLOG.md`、`DELIVERY_PLAN.md`、`DOCS_INDEX.md` |
| research / deferred | 产品或数据边界未定，需要先做发现或验证 | transcript、storybank、outcome drift |

## 2. Why Phase 1 and Phase 2 Are Not Sufficient Yet

Phase 1 和 Phase 2 都有价值，但它们不是 Phase 3 的直接设计输入。Phase 1 主要回答“当前项目有什么、缺什么、哪些 claim 不能升级”；Phase 2 主要回答“参考 Skill 写了什么、哪些只是 Markdown、哪些能力可以作为灵感”。二者之间还缺少复用设计层。

| 不足 | Phase 1 / Phase 2 的现状 | 为什么会阻断 Phase 3 |
| --- | --- | --- |
| 缺少设计方向 | Phase 1 给出 CAND-001 到 CAND-010，Phase 2 给出 CAP/REF-OPP，但没有说明先做产品能力、guardrail 还是 research | Phase 3 容易把候选增强混成大包，无法决定落地顺序 |
| 缺少可复用设计原语提炼 | Phase 2 仍按参考 Skill 文件和命令分类 | Phase 3 需要的是可迁移机制，例如 state lifecycle、lazy loading、quality gate，而不是复制 command 文档 |
| 缺少 Project × Reference 交叉分析 | Phase 1 项目侧、Phase 2 参考侧分离 | 无法判断哪些能 adopt、哪些必须 adapt、哪些只能 reject 或 research |
| 缺少 adoption design brief | 两份文档没有为强/中候选写清背景、落地方式、验证面和风险 | Phase 3 容易直接生成实现任务，但缺少可审计设计 |
| 缺少验证策略 | Phase 1 有测试/CI事实，Phase 2 有 absence_verified，但没有合并成候选级 gate | 可能把 `design-only`、`schema_like_design`、`release_note_claim` 错写成 `executable_evidence` |
| 缺少 reject/not-copy 原因 | Phase 2 标记了不能误用，但没有形成明确 Do-Not-Copy 清单 | Phase 3 可能复制 coaching state、rubric、examples 或 release notes，造成 false implementation claim |

因此，Phase 3 readiness 只能保持 `partial`：有些 guardrail 和局部产品增强已经有项目证据，可以进入候选；但 transcript、storybank、outcome drift、完整 coaching state 等能力仍是 `project_evidence_missing`，只能 research 或 deferred。

## 3. Reuse-Oriented Reference Reading

本文按“可迁移机制”读取参考 Skill，而不是按命令名逐项搬运。参考 Skill 的价值主要在于设计结构：它把状态、证据、推荐动作、纠错、进度和结果反馈放进一个 coaching workflow；但它的文件形态是 Markdown Skill package，没有发现 `tests/`、`scripts/`、`schemas/`、`contracts/`、`evals/` 或 `validation/` 这类可执行实现证据。

| 参考区域 | 可复用机制 | 不能误写成什么 |
| --- | --- | --- |
| `SKILL.md`, `README.md` | command registry、mode routing、lazy reference loading、session rule、recommended next action | 不能写成运行时 router 或产品 command engine |
| `references/coaching-state-schema.md`, `references/state-update-triggers.md`, `references/schema-migration.md` | state lifecycle、update trigger、compatibility idea | 不能写成数据库 schema、Pydantic schema、migration 或 validator |
| `references/evidence-sourcing.md` | evidence/confidence/source tier 和 unknown handling | 不能写成已接入项目 provider 的 evidence pipeline |
| `references/rubrics-detailed.md`, `references/calibration-engine.md` | rubric calibration、root cause、outcome drift 设计 | 不能写成 live scoring quality 或录用结果相关性 |
| `references/transcript-formats.md`, `references/transcript-processing.md` | transcript input readiness、quality gate、format normalization | 当前项目 `project_evidence_missing`，不能直接进 FE_candidate |
| `references/storybank-guide.md`, `references/story-mapping-engine.md` | storybank lifecycle、story reuse、story fit mapping | 当前项目只有 Assets 类比面，不等于 storybank |
| `references/commands/practice.md`, `mock.md`, `progress.md` | gated progression、state-aware recommended next action、redo gate | 只能 adapt 到现有 Workbench / Polish progress tree |
| `references/commands/feedback.md`, `reflect.md` | human correction capture、post-session reflection、archive | 只能先做 capture 和 review，不做 automatic calibration claim |
| `references/examples.md` | behavior-contract seed 和示例语料 | examples 不是 tests |
| `VERSIONS.md`, `releases/*.md` | versioned workflow evolution | release notes 只是 `release_note_claim` |

这个读取方式带来的核心结论是：参考 Skill 很适合提供产品和 workflow 的设计原语，但几乎不能直接提供可执行实现。Phase 3 若采用参考内容，必须在 AiForInterviewer 项目证据上重新落地。

## 4. Reusable Design Primitives

本章把参考 Skill 拆成 RDP-*。每个 RDP 都说明背景、问题、可复用设计、本项目落地方式和边界。RDP 不是任务编号，也不是实现承诺。

| ID | 背景和问题 | 可复用设计 | AiForInterviewer 落地方式 | 分类 | 证据边界 |
| --- | --- | --- | --- | --- | --- |
| RDP-001 | 面试辅导会跨 session 积累履历、JD、回答、反馈、结果和纠错。如果没有生命周期，状态会变成不可审计文本。 | state lifecycle：schema、update trigger、archive/retention、migration note 分开。 | 先研究 project-native interview state，不复制 `coaching_state.md`。可参考现有 DB models、report metadata、capability matrix 的状态词。 | research / deferred | 参考为 `schema_like_design`，项目统一 coaching state `project_evidence_missing`。 |
| RDP-002 | 用户动作和开发者命令容易散落在 UI、CLI 和文档里，后续难以验证。 | command registry 与 file routing 分离：命令入口只声明意图，具体 reference 按需加载。 | 可映射到 `tools/doc_governor/cli.py`、`package.json` command matrix，也可为 Workbench action view model 提供分层思路。 | agent workflow / 工程 guardrail | 项目 CLI 有 `executable_evidence`，参考 command docs 为 `design-only`。 |
| RDP-003 | “换一道题”“继续追问”“提交回答”“看反馈”这类动作表面相似，但状态含义不同。 | mode routing：按优先级、多步意图和当前状态路由 recommended next action。 | Workbench 应把 `regenerate_current_node`、`new_question`、answer submit、feedback next action 分开建模。 | 产品能力强化 | 项目 Workbench 有 partial `executable_evidence`，参考 router 为 `design-only`。 |
| RDP-004 | 大量参考文件会放大上下文噪声，AI 或开发者容易读错范围。 | lazy reference loading：只在命令或设计问题触发时读取对应 reference。 | 可进入 active docs governance handoff 和 doc governor packet 规则，作为 Phase 3 文档消费 guard。 | agent workflow / 文档治理 | 项目有 `DOCS_INDEX.md` 和 doc governor 证据；不做 runtime dependency loader。 |
| RDP-005 | 面试建议若没有来源、置信度和未知边界，会变成不可验证建议。 | evidence/confidence sourcing：source availability、evidence refs、low confidence flags、unknown language。 | 直接承接 `apps/api/app/schemas/envelope.py` 与 `apps/web/src/shared/api/envelope.ts`，补强 API/frontend drift guard。 | 工程 guardrail / 产品能力强化 | 项目已有 `executable_evidence`。 |
| RDP-006 | 项目已有 partial、skeleton、default-off、fake/replay/deterministic 等边界，最容易在文档或 UI 中被升级成“已实现”。 | non-claim discipline：固定词表、负证据、capability status、claim boundary UI wording rules。 | 继续使用 capability matrix、skeleton guard、eval non-claims，并要求 UI copy 不把 replay/default-off 写成 live quality。 | 工程 guardrail / 文档治理 | 项目已有 `executable_evidence`；参考 absence 进一步强化。 |
| RDP-007 | 评分不是只有分数，还要解释维度、证据、角色级别和不确定性。 | rubric calibration：five dimensions、root cause、seniority、score drift。 | 仅可先用于 score explanation 和 confidence guard；不能宣称自动评分质量或 outcome correlation。 | 产品能力强化 / research | 项目有 feedback score/confidence partial evidence，outcome calibration `project_evidence_missing`。 |
| RDP-008 | 参考 Skill 强调 transcript 质量先于分析，否则分析会基于破碎输入。 | transcript quality gate：format detection、speaker mapping、partial transcript warning、input readiness。 | 当前项目没有 transcript ingestion 证据；只能研究输入模型、隐私和 fixture。 | research / deferred | `project_evidence_missing`，不得进入 FE_candidate。 |
| RDP-009 | storybank 不是回答样例，而是可复用面试素材资产，需维护来源、状态、覆盖面和退役规则。 | storybank lifecycle：story inventory、STAR text、evidence tags、reuse mapping、retirement/enhancement。 | 可研究是否映射到现有 Assets / 可复用面试素材，但不能直接假设已有 storybank。 | 产品能力强化 / research | Assets 只是类比面；storybank `project_evidence_missing`。 |
| RDP-010 | 练习如果没有阶段和 gate，用户不知道下一步该复练、推进还是补资料。 | gated progression：stage、gate、redo protocol、state-aware recommended next action。 | 可 adapt 到 Polish progress tree、Workbench next action 和 input readiness。 | 产品能力强化 | 项目有 partial Workbench/Polish 证据。 |
| RDP-011 | 用户纠正 AI 判断时，如果不记录，后续推荐会重复错。 | human correction loop：capture first、analyze later、calibration candidate、audit trail。 | Polish feedback 可先增加 correction capture 和 warning review，不做自动学习声明。 | 产品能力强化 / 工程 guardrail | 项目 feedback validation 有 partial `executable_evidence`。 |
| RDP-012 | 评分与真实结果之间会漂移，但漂移只能由真实 outcome 反馈驱动。 | outcome drift boundary：outcome log、trend、calibration confidence、insufficient data state。 | 当前只能定义 outcome tracking boundary，不做录用结果预测或质量 claim。 | research / deferred | outcome log `project_evidence_missing`。 |
| RDP-013 | Resume、JD、Assets、Polish 的内容如果各写各的，会导致定位和故事不一致。 | cross-surface consistency：共享 positioning/story source，跨 surface 使用同一证据边界。 | 只在现有 Resume/Job/Assets/Polish surface 做 consistency guard，不复制 LinkedIn/outreach/salary 全面 workflow。 | 产品能力强化 | 项目已有 partial surface 证据。 |
| RDP-014 | 参考 Skill 的 challenge protocol 可以提高质量，但若无边界会压过用户意图。 | bounded challenge protocol：opt-in、level、stop condition、resolution。 | 无产品边界前拒绝复制；最多 research bounded challenge policy。 | research / reject | 参考为 `design-only`，项目 UX 边界 `unsupported_or_unknown`。 |
| RDP-015 | workflow 会演进，旧状态和旧输出需要兼容解释。 | versioned workflow evolution：version note、migration checklist、compatibility guard。 | 可转成 capability preservation、route snapshot、schema drift checklist。 | 工程 guardrail / 文档治理 | 项目有 preservation matrix 和 route/eval guard；参考 release 为 `release_note_claim`。 |
| RDP-016 | 示例能帮助定义行为，但不能证明系统行为。 | examples as behavior-contract seed：examples 只用于 acceptance wording 和 golden case seed。 | Phase 3 可把 reference examples 转为待实现测试的设计素材，但必须由项目测试承接。 | 工程 guardrail | 参考 examples 为 `design-only`，项目测试才是 `executable_evidence`。 |
| RDP-017 | 产品界面上“低置信度”“未验证”“默认关闭”若写法不统一，会制造误导。 | claim boundary UI wording rules：UI 文案必须反映 source/evidence/default-off/replay 边界。 | Workbench、Polish feedback、eval report UI/文档都应使用统一 claim boundary copy。 | 产品能力强化 / 工程 guardrail | 项目有 envelope/eval/capability evidence，可 adapt。 |
| RDP-018 | 参考复用结束后必须交接到 active docs，而不是生成新的临时计划体系。 | active docs governance handoff：候选进 `BACKLOG.md`，阶段进 `DELIVERY_PLAN.md`，证据索引进 active docs。 | Phase 3 输入必须从本 02b 到正式治理入口，不绕过 `DOCS_INDEX.md`。 | 文档治理 | `AGENTS.md` 和 `DOCS_INDEX.md` 是 governance evidence。 |

这些 RDP 中，RDP-005、RDP-006、RDP-016、RDP-017 属于“证据和 claim 边界”主线；RDP-003、RDP-010、RDP-011、RDP-013 属于“产品能力强化”主线；RDP-001、RDP-008、RDP-009、RDP-012、RDP-014 属于“需要先研究”的主线。Phase 3 不应把这三类混成一个实现任务。

## 5. Project Problems Reopened by Reference Study

参考 Skill 重新打开的问题，不是因为 Phase 1 错了，而是 Phase 1 主要从当前仓库出发，没有足够的参考机制来命名产品能力缺口。

| 问题 ID | 背景 | Phase 1 已有事实 | 参考 Skill 重新打开的角度 | 本项目落地方式 |
| --- | --- | --- | --- | --- |
| PP-001 | capability status 和文档 claim 仍需防腐 | Phase 1 已标记 partial/skeleton/default-off/fake/replay/deterministic 不能升级 | RDP-006/RDP-017 把 non-claim 扩展到 UI wording 和 Phase 3 seed gate | 作为所有 FE-SEED 的前置 guardrail |
| PP-002 | Workbench action/mode routing 难以人工审计 | Phase 1 指出 `InterviewPage.tsx` 体量大、action/state 多 | RDP-003/RDP-010 提供 state-aware recommended next action 和 gated progression | 抽出 action view model，区分 send/regenerate/next/complete |
| PP-003 | API/frontend envelope 字段可能 drift | Phase 1 指出 Pydantic 与 TS 手写同步风险 | RDP-005 要求 source/confidence/evidence 成为一等字段 | 做 schema/contract drift guard，优先覆盖 envelope |
| PP-004 | input readiness / quality gate 不够产品化 | Phase 1 主要关注 validation 和 runtime evidence | RDP-008/RDP-010 把“输入是否足够”放在分析前 | 对 Polish/Workbench 先做 input readiness，不直接做 transcript feature |
| PP-005 | human correction capture 缺少闭环 | Phase 1 有 feedback validation 和 warnings 证据，但不是 correction lifecycle | RDP-011 把用户纠错视为后续推荐的输入 | 先捕获 correction note、source refs、review state，不做自动学习 |
| PP-006 | storybank → Assets 的产品能力边界未定义 | Phase 1 识别 Assets，但没有 storybank lifecycle | RDP-009 指出 storybank 是可复用面试素材资产 | 进入 research，验证是否扩展 Assets 还是新模型 |
| PP-007 | Polish progress tree 可以更像阶段化练习 | Phase 1 有 Polish partial 和 progress tree 证据 | RDP-010 提供 gate、redo、next action 机制 | adapt 到现有 Polish，不新建 Training 主流程 |
| PP-008 | examples 的价值没有被转成行为契约 | Phase 1 关注测试证据，Phase 2 发现 reference examples | RDP-016 要求 examples 只作为 behavior-contract seed | 作为 acceptance/golden case 素材，不能替代 tests |
| PP-009 | role/JD-specific practice routing 未成体系 | 项目已有 Resume/Job/Polish 绑定，但没有参考式 role drill map | RDP-007/RDP-010/RDP-013 提供角色/JD差异化练习路由 | 只能在已有 JD/Polish surfaces adapt，缺证据处 research |
| PP-010 | outcome tracking boundary 缺失 | Phase 1 已避免 live quality claim | RDP-012 把真实 outcome 与评分 drift 分开 | 先定义 boundary 和 privacy，不做 outcome prediction |
| PP-011 | active docs handoff 需要防止新计划体系 | AGENTS/DOCS_INDEX 禁止并行 roadmap | RDP-018 要求候选进 active docs | Phase 3 只能把 seed 转入正式 BACKLOG/DELIVERY_PLAN |

## 6. Project × Reference Reuse Matrix

本矩阵是 Phase 3 入口的核心。`source_flag=NEW_FROM_REFERENCE` 的行必须解释：为什么 Phase 1 没体现、当前项目证据是否足够、如果 `project_evidence_missing` 则不得直接进入 `FE_candidate`。

| ID | source_flag | RDP | decision | strength | project problem | Phase 1 为什么没体现 | 项目证据是否足够 | project_evidence_missing | Phase 3 handling | 说明 |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| REUSE-001 | PROJECT_REINFORCED | RDP-006, RDP-017 | adopt | strong | PP-001 | Phase 1 已体现，但偏文档/测试 non-claim，未展开 UI wording | 足够：capability matrix、skeleton guard、eval non-claims | no | support_task | 直接继承 non-claim discipline，作为 Phase 3 所有候选的 guard。 |
| REUSE-002 | PROJECT_REINFORCED | RDP-005 | adopt | strong | PP-003 | Phase 1 已识别 contract drift，但未把 reference evidence/confidence 设计合入 | 足够：`envelope.py`、`envelope.ts`、score schema | no | FE_candidate | source/confidence/evidence 字段可进入 schema drift guard。 |
| REUSE-003 | NEW_FROM_REFERENCE | RDP-016 | adopt | strong | PP-008 | Phase 1 关注现有测试，没有分析 reference examples 的设计用途 | 足够：项目有 pytest/TS tests，可把 examples 降级为 seed | no | support_task | examples as behavior-contract seed，不能作为 tests。 |
| REUSE-004 | NEW_FROM_REFERENCE | RDP-004, RDP-018 | adopt | strong | PP-011 | Phase 1 没有把 lazy reference loading 提炼成 active docs handoff | 足够：`DOCS_INDEX.md`、doc governor、AGENTS 工作流 | no | support_task | 进入文档治理和 agent workflow，不触碰业务代码。 |
| REUSE-005 | NEW_FROM_REFERENCE | RDP-003 | adapt | medium | PP-002 | Phase 1 指出 Workbench 大，但未用 mode routing 命名问题 | 足够：Workbench action/tests 有 partial 证据 | no | FE_candidate | 把 recommended next action 作为 view model，而不是复制 command router。 |
| REUSE-006 | NEW_FROM_REFERENCE | RDP-010 | adapt | medium | PP-007 | Phase 1 有 Polish partial，但没有 gated progression 设计语言 | 足够：Polish progress tree/Workbench 证据 partial | no | FE_candidate | 适合改造为 progress tree gate 和 next action。 |
| REUSE-007 | NEW_FROM_REFERENCE | RDP-011 | adapt | medium | PP-005 | Phase 1 有 feedback validation，但没把 human correction 作为生命周期输入 | 足够：warnings/low confidence/validation 可承接 capture | no | FE_candidate | 先做 correction capture，禁止 automatic calibration claim。 |
| REUSE-008 | NEW_FROM_REFERENCE | RDP-013 | adapt | medium | PP-006, PP-009 | Phase 1 分析现有 surfaces，没有参考式 cross-surface consistency | 部分足够：Resume/Job/Assets/Polish 有证据，LinkedIn/outreach 无 | no | FE_candidate_limited | 仅覆盖已有 surfaces，明确不扩展缺失 surfaces。 |
| REUSE-009 | NEW_FROM_REFERENCE | RDP-015 | adapt | medium | PP-011 | Phase 1 有 preservation matrix，但未借鉴 versioned workflow evolution | 足够：capability preservation、route/eval guard | no | support_task | 变成 compatibility checklist，不写成 migration automation。 |
| REUSE-010 | NEW_FROM_REFERENCE | RDP-017 | adapt | medium | PP-001, PP-010 | Phase 1 主要是工程 claim，未强调 UI claim boundary copy | 足够：envelope/eval/capability evidence 可支撑 copy guard | no | FE_candidate | UI/报告文案要显示 partial、low confidence、default-off/replay 边界。 |
| REUSE-011 | NEW_FROM_REFERENCE | RDP-007 | research | weak | PP-009 | Phase 1 没有参考式 rubric calibration 和 role drill map | 不足：只有 feedback score/confidence，缺 human labels/outcome | yes | research | 不能直接进入 FE_candidate，只能研究 rubric version/golden cases。 |
| REUSE-012 | NEW_FROM_REFERENCE | RDP-008 | research | weak | PP-004 | Phase 1 没有 transcript 产品输入，因为项目未见 transcript surface | 不足：transcript input/storage/privacy/fixture 缺失 | yes | research | transcript quality gate 只能先研究。 |
| REUSE-013 | NEW_FROM_REFERENCE | RDP-009 | research | weak | PP-006 | Phase 1 识别 Assets，但没把 storybank 当可复用面试素材生命周期 | 不足：Assets 不等于 storybank，缺 story schema/lifecycle tests | yes | deferred | storybank → Assets 需 discovery，不能直接 FE_candidate。 |
| REUSE-014 | NEW_FROM_REFERENCE | RDP-012 | research | weak | PP-010 | Phase 1 避免 live quality claim，因此没有 outcome drift 产品设计 | 不足：outcome log、privacy、correlation method 缺失 | yes | research | outcome tracking boundary 先研究，禁止 outcome prediction。 |
| REUSE-015 | NEW_FROM_REFERENCE | RDP-014 | reject | blocked | PP-001, PP-010 | Phase 1 不涉及 reference challenge protocol | 不足：产品 opt-in、safety、resolution 缺失 | yes | reject | 拒绝无边界 challenge protocol，可另开 bounded policy research。 |
| REUSE-016 | NEW_FROM_REFERENCE | RDP-001 | research | weak | PP-004, PP-006 | Phase 1 没有统一 coaching state lifecycle，因为当前项目 surface 分散 | 不足：project-native schema/migration/archive rules 缺失 | yes | research | 不复制 `coaching_state.md`，先做状态生命周期发现。 |
| REUSE-017 | PROJECT_REINFORCED | RDP-002 | adapt | medium | PP-002, PP-011 | Phase 1 有 command surfaces，但没拆 command registry/file routing | 足够：doc governor CLI、package scripts、Workbench actions | no | support_task | 适合做 developer command matrix 和 action registry 支撑。 |
| REUSE-018 | NEW_FROM_REFERENCE | RDP-010, RDP-005 | adapt | medium | PP-004, PP-007 | Phase 1 关注 validation，但没把 input readiness 作为用户可见 gate | 部分足够：Polish validation/Workbench state 可承接 | no | FE_candidate | 输入不足时推荐补资料或降置信，不生成假完整反馈。 |

## 7. Adoption Design Briefs

本章只为 `strong` 和 `medium` 的 REUSE 项写 ADB-*。`weak` 或 `blocked` 项不写 adoption brief，只保留 research/reject 说明。

### ADB-001 Evidence and Non-Claim Guard

| 字段 | 内容 |
| --- | --- |
| source | REUSE-001, RDP-006, RDP-017 |
| 背景 | AiForInterviewer 已经存在 partial/skeleton/default-off/fake/replay/deterministic 等状态词，但 Phase 3 会引入参考 Skill 的大量设计文本，false claim 风险上升。 |
| 问题 | 如果不统一 claim boundary，Phase 3 可能把 reference design-only 或 replay eval 写成 live-provider quality。 |
| 可复用设计 | 固定 capability status、non_claims、low confidence、source availability、UI wording rules。 |
| 本项目落地方式 | 保持 capability matrix、`tests/api/test_skeleton_guard.py`、eval reports 和 UI copy 同步；新增候选必须声明 evidence type。 |
| 验证方式 | rg/static guard 查禁 claim 升级；focused tests 验证 skeleton/default-off/non_claims 文案不漂移。 |
| 风险 | 过度保守可能让真实进展也难以表达；需允许 `implemented and locally validated` 等受控状态，但必须有证据。 |
| Phase 3 建议 | `support_task`，作为所有 FE_candidate 的前置 gate。 |

### ADB-002 API / Frontend Evidence Contract Guard

| 字段 | 内容 |
| --- | --- |
| source | REUSE-002, RDP-005 |
| 背景 | 后端 Pydantic envelope 与前端 TS envelope 已有 source/confidence/evidence 字段，但手写同步会 drift。 |
| 问题 | 用户界面若拿不到 `source_availability`、`evidence_refs`、`low_confidence_flags`，就无法呈现 claim boundary。 |
| 可复用设计 | evidence/confidence sourcing 成为 contract 一等字段。 |
| 本项目落地方式 | 以 `apps/api/app/schemas/envelope.py` 和 `apps/web/src/shared/api/envelope.ts` 为主，增加 schema drift guard 或 contract snapshot。 |
| 验证方式 | schema field parity、route snapshot、TS compile/static guard；不需要 reference executable evidence。 |
| 风险 | 字段过早泛化会扩大 API surface；应优先覆盖已有 envelope，不新建通用框架。 |
| Phase 3 建议 | `FE_candidate`，readiness `partial` but actionable。 |

### ADB-003 Examples as Behavior-Contract Seed

| 字段 | 内容 |
| --- | --- |
| source | REUSE-003, RDP-016 |
| 背景 | 参考 Skill 的 examples 对行为期望有价值，但没有执行性。 |
| 问题 | 直接把 examples 当 tests 会制造虚假验证。 |
| 可复用设计 | examples 只作为 acceptance wording、golden case seed、manual review sample。 |
| 本项目落地方式 | Phase 3 可以从 examples 提炼测试名称或 fixture intent，但最终必须由项目 pytest/TS tests 承接。 |
| 验证方式 | 文档中所有 examples 标记为 `design-only`；实现窗口必须新增真实测试才算 `executable_evidence`。 |
| 风险 | examples 可能带有参考 Skill 的产品假设；必须删去不适合 AiForInterviewer 的表述。 |
| Phase 3 建议 | `support_task`。 |

### ADB-004 Lazy Reference Loading and Active Docs Handoff

| 字段 | 内容 |
| --- | --- |
| source | REUSE-004, RDP-004, RDP-018 |
| 背景 | Phase 3 会同时面对 Phase 1、Phase 2、02b、active docs 和 reference clone，读取噪声高。 |
| 问题 | 若没有读取顺序和交接边界，容易绕过 `BACKLOG.md`、`DELIVERY_PLAN.md`，生成平行计划。 |
| 可复用设计 | command-triggered lazy loading + active docs governance handoff。 |
| 本项目落地方式 | 让 Phase 3 只从本文件读取 FE-SEED，再回到 active docs 登记；reference clone 只在验证特定 RDP 时打开。 |
| 验证方式 | Phase 3 输出必须引用 `DOCS_INDEX.md`、`BACKLOG.md`、`DELIVERY_PLAN.md` 的边界；不得新增 roadmap。 |
| 风险 | 过度流程化会慢；但这是防止 false planning 的必要 guard。 |
| Phase 3 建议 | `support_task`。 |

### ADB-005 Workbench State-Aware Recommended Next Action

| 字段 | 内容 |
| --- | --- |
| source | REUSE-005, RDP-003 |
| 背景 | Workbench 中发送回答、换题、查看反馈、进入下一步是用户最核心流程。 |
| 问题 | 如果 action/mode 只堆在组件条件分支里，人工很难审计哪一步被允许。 |
| 可复用设计 | state-aware recommended next action：根据当前 node、answer、feedback、quality state 给出下一动作。 |
| 本项目落地方式 | 抽出可测试 view model 或 action registry，保留 `regenerate_current_node` 与 `new_question` 的语义差异。 |
| 验证方式 | `InterviewPage.test.ts` 或静态 guard 验证 action label、disabled state、recommended action 与状态一致。 |
| 风险 | 不能把参考 command router 直接搬进产品；应贴合现有 Workbench 状态。 |
| Phase 3 建议 | `FE_candidate`。 |

### ADB-006 Polish Progress Tree Gated Progression

| 字段 | 内容 |
| --- | --- |
| source | REUSE-006, RDP-010 |
| 背景 | Polish 已有 progress tree 和问答反馈链路，但用户下一步动作可以更清晰。 |
| 问题 | 没有 gate 时，用户可能在输入不足时继续生成，或在反馈未消化时推进。 |
| 可复用设计 | gated progression：input readiness、redo gate、next action、completion boundary。 |
| 本项目落地方式 | 只 adapt 到现有 Polish progress tree，不新建 Training 主流程。 |
| 验证方式 | UI 状态测试 + API warning/low confidence fields；输入不足时显示补资料或低置信，不输出完整 claim。 |
| 风险 | gate 过严会阻断探索；应允许用户继续，但必须显示 evidence boundary。 |
| Phase 3 建议 | `FE_candidate`。 |

### ADB-007 Human Correction Capture

| 字段 | 内容 |
| --- | --- |
| source | REUSE-007, RDP-011 |
| 背景 | 用户可能指出 AI 反馈不准、缺少事实或误解 JD。 |
| 问题 | 如果 correction 不被捕获，后续推荐会重复错误；如果直接自动学习，又会越过证据边界。 |
| 可复用设计 | capture first, analyze later：记录 correction、source refs、review state 和 low confidence reason。 |
| 本项目落地方式 | 在 Polish feedback 或 Workbench feedback 面增加 correction capture，不宣称自动校准。 |
| 验证方式 | API payload/schema test、UI state test、non-claim wording test。 |
| 风险 | correction 可能包含敏感信息；需要 redaction 和 data boundary。 |
| Phase 3 建议 | `FE_candidate`，readiness `partial`。 |

### ADB-008 Existing-Surface Consistency Guard

| 字段 | 内容 |
| --- | --- |
| source | REUSE-008, RDP-013 |
| 背景 | 当前项目已有 Resume、Job、Assets、Polish，但没有 LinkedIn/outreach/salary surfaces。 |
| 问题 | 跨 surface consistency 有产品价值，但完整复制参考 Skill 会超出当前产品边界。 |
| 可复用设计 | shared source and evidence boundary across existing surfaces。 |
| 本项目落地方式 | 只校验 Resume/Job/Assets/Polish 中使用的事实、JD 约束和 asset refs。 |
| 验证方式 | contract/static tests 验证 source refs、job binding 和 asset usage 不漂移。 |
| 风险 | 如果把缺失 surface 也纳入，会误建新产品线。 |
| Phase 3 建议 | `FE_candidate_limited`。 |

### ADB-009 Versioned Workflow Compatibility Checklist

| 字段 | 内容 |
| --- | --- |
| source | REUSE-009, RDP-015 |
| 背景 | 参考 Skill 有 versioned workflow 和 schema migration 文档，但没有执行器。 |
| 问题 | Phase 3 若改 envelope、progress tree 或 docs status，需要兼容说明，不能写成自动 migration。 |
| 可复用设计 | compatibility checklist、route snapshot、capability preservation。 |
| 本项目落地方式 | 接入 preservation matrix、route/eval snapshot、doc governor preview。 |
| 验证方式 | `git diff --check`、route/static snapshot、capability wording guard。 |
| 风险 | checklist 不是测试；必须与可执行 guard 配套。 |
| Phase 3 建议 | `support_task`。 |

### ADB-010 Claim Boundary UI Wording

| 字段 | 内容 |
| --- | --- |
| source | REUSE-010, RDP-017 |
| 背景 | 用户看到低置信、缺证据、默认关闭、replay-only 报告时，需要知道它们不是质量保证。 |
| 问题 | 工程 non-claim 若不进入 UI wording，产品仍可能误导用户。 |
| 可复用设计 | UI copy mirrors evidence status：partial、low confidence、source unavailable、default-off、replay-only。 |
| 本项目落地方式 | Workbench、Polish feedback、eval/report 文案统一使用 source/confidence 字段驱动。 |
| 验证方式 | UI text tests/static rg guard；检查不得出现 live-provider quality claim。 |
| 风险 | 文案过硬会影响体验；应短句清晰，不使用内部术语堆砌。 |
| Phase 3 建议 | `FE_candidate`。 |

### ADB-011 Developer Command Matrix

| 字段 | 内容 |
| --- | --- |
| source | REUSE-017, RDP-002, RDP-004 |
| 背景 | 项目已有 doc governor CLI、package scripts、eval scripts，但入口分散。 |
| 问题 | 开发者和 AI 容易运行错误命令，或把 build/test 禁止窗口误触发。 |
| 可复用设计 | command registry、scope-aware routing、lazy command packet。 |
| 本项目落地方式 | 在 active docs 或 doc governor 中维护命令矩阵，按任务类型声明允许/禁止命令。 |
| 验证方式 | doc governor preview 或 static rg；本窗口不运行 build/test/install。 |
| 风险 | 命令矩阵会随项目漂移，需要治理入口维护。 |
| Phase 3 建议 | `support_task`。 |

### ADB-012 Input Readiness and Quality Gate

| 字段 | 内容 |
| --- | --- |
| source | REUSE-018, RDP-005, RDP-010 |
| 背景 | 参考 Skill 把输入质量放在分析前；当前项目的 Polish/Workbench 已有部分 validation 和 warnings。 |
| 问题 | 输入不足时继续生成完整反馈，会扩大 hallucination 和 false confidence。 |
| 可复用设计 | input readiness：enough evidence、missing source、low confidence、recommended next action。 |
| 本项目落地方式 | 在 Polish/Workbench 中把 warnings 与 recommended next action 绑定，例如补充 JD、补充回答、继续但显示 low confidence。 |
| 验证方式 | API warning tests、frontend disabled/notice state tests、claim wording guard。 |
| 风险 | 不应把 transcript quality gate 偷渡进当前产品；transcript 仍是 research。 |
| Phase 3 建议 | `FE_candidate`。 |

## 8. What to Adopt Directly

可以直接采用的是规则和审查方式，不是参考 Skill 的文件结构。

| adopt 项 | 采用内容 | 为什么值得吸收 | AiForInterviewer 落地 |
| --- | --- | --- | --- |
| ADOPT-001 | evidence/confidence/non-claim 必须成为 Phase 3 候选字段 | 项目已有 envelope、eval non_claims 和 skeleton guard，吸收成本低、收益高 | 所有 FE-SEED 必须声明 evidence status 和 claim boundary |
| ADOPT-002 | examples 只能作为 behavior-contract seed | 参考 examples 有表达价值，但没有可执行性 | Phase 3 可把 examples 转成测试设计，不把 examples 当测试 |
| ADOPT-003 | lazy reference loading | 能减少 Phase 3 读取噪声和越界复用 | 只在验证具体 RDP/REUSE 时打开 reference clone 文件 |
| ADOPT-004 | active docs governance handoff | 防止 02b 变成新入口或平行计划 | Phase 3 seed 若采用，必须进入 `BACKLOG.md`/`DELIVERY_PLAN.md` |
| ADOPT-005 | release notes 降级为 `release_note_claim` | 避免把版本说明写成 migration/executable proof | 版本演进只进入 compatibility checklist |
| ADOPT-006 | `project_evidence_missing` 阻断 FE_candidate | 保护 transcript、storybank、outcome 等未证实产品能力 | 缺项目证据的 NEW_FROM_REFERENCE 项只给 research/deferred |

## 9. What to Adapt

需要 adapt 的内容有明确产品价值，但不能按参考 Skill 原样复制。

| adapt 项 | 参考设计 | 改造为 AiForInterviewer 的方式 | 不直接采用原因 |
| --- | --- | --- | --- |
| ADAPT-001 | command/mode routing | Workbench action view model、doc governor command matrix | 参考是 Markdown command list，不是 runtime router |
| ADAPT-002 | state-aware recommended next action | 根据当前 node、answer、feedback、readiness 生成下一步 | 当前项目已有 Workbench 状态，不需要参考 Skill 的全命令体系 |
| ADAPT-003 | input readiness / quality gate | Polish/Workbench 显示 missing evidence、low confidence、补资料建议 | transcript quality gate 缺产品输入，不能直接上 transcript |
| ADAPT-004 | human correction capture | 记录 correction note、source refs、review state | 自动 calibration 没有证据，必须先人审 |
| ADAPT-005 | Polish progress tree gated progression | 在现有 progress tree 上加入 gate、redo、completion copy | 不新建 Training 产品流 |
| ADAPT-006 | storybank → Assets / 可复用面试素材 | 先研究 Assets 是否可承接 story lifecycle | storybank model、retirement rules、tests 均缺失 |
| ADAPT-007 | role/JD-specific practice routing | 只在已有 JD/Polish surfaces 做 practice variation | 缺少 reference 的 role drill engine 和 outcome data |
| ADAPT-008 | cross-surface consistency | 限定 Resume/Job/Assets/Polish | LinkedIn/outreach/salary surfaces 当前不在产品证据内 |
| ADAPT-009 | claim boundary UI wording rules | UI copy 使用 source/confidence/default-off/replay 边界 | 不能暴露过多内部术语，也不能隐去风险 |
| ADAPT-010 | versioned workflow evolution | compatibility checklist、route snapshot、capability preservation | reference schema migration 是 `schema_like_design` |

## 10. What to Reject

拒绝项不是说参考 Skill 没价值，而是当前项目证据或产品边界不足，直接复制会制造风险。

| reject 项 | 拒绝内容 | rationale | safer alternative |
| --- | --- | --- | --- |
| REJECT-001 | 直接复制 `coaching_state.md` | 它是 `schema_like_design`，不是项目 DB/API schema | 先做 RDP-001 project-native state lifecycle research |
| REJECT-002 | 把 Markdown command workflow 当 runtime routing | 参考只有 `design-only`，没有 router code/tests | 用 Workbench view model 或 doc governor command registry 承接 |
| REJECT-003 | 把 rubric 文档写成自动评分质量 | 缺 human labels、golden cases、outcome data | 先做 score explanation 和 confidence guard |
| REJECT-004 | 把 calibration notes 写成真实 outcome correlation | outcome log `project_evidence_missing` | 先定义 outcome tracking boundary 和 privacy |
| REJECT-005 | 把 examples 当 tests | examples 没有执行性 | 转成 behavior-contract seed，再由项目测试实现 |
| REJECT-006 | 把 release notes 当 migration automation | `release_note_claim` 不是 migration proof | 写 compatibility checklist 和真实 migration test |
| REJECT-007 | 无 evidence capture 就展示 confidence label | 会制造虚假可信度 | 将 confidence 绑定 `source_availability`、`evidence_refs`、`low_confidence_flags` |
| REJECT-008 | 复制无边界 Level 5 challenge protocol | 缺 opt-in、stop condition、safety 和 resolution | 只保留 bounded challenge research |
| REJECT-009 | 一次性复制 LinkedIn/outreach/salary 全 surface | 当前项目没有这些 surface 的产品证据 | 限定现有 Resume/Job/Assets/Polish |
| REJECT-010 | 把 agent workflow guardrail 当代码 enforcement | Markdown 不能替代测试或 runtime validation | 配套 executable guard 或明确仅为 workflow |
| REJECT-011 | 把 fake/replay/deterministic/default-off 写成 live-provider quality | 当前证据只能证明 replay/local/contract，不证明 live quality | UI/report 使用 non_claims 和 provider_evidence_type |
| REJECT-012 | 新建 Training 主流程 | 当前 active docs 和 Phase 1 不支持 Training 作为 MVP 产品事实 | 在 Workbench/Polish 内做 bounded progression |

## 11. What Needs More Research

以下项有潜在产品价值，但现在不满足 FE_candidate 条件。它们若进入 Phase 3，只能以 `research` 或 `deferred` 形式进入，且必须明确最小证据。

| 研究项 | source | 当前缺口 | 最小研究产物 | Phase 3 状态 |
| --- | --- | --- | --- | --- |
| Transcript input readiness / quality gate | REUSE-012, RDP-008 | transcript input、storage、privacy、fixture、parser tests 均缺 | 输入模型、隐私边界、样例 fixture、quality gate 规则 | research |
| Storybank → Assets / 可复用面试素材 | REUSE-013, RDP-009 | Assets 是否能承接 STAR story、source refs、retirement 未定 | story asset schema 草案、生命周期规则、与 Assets 的映射决策 | deferred |
| Outcome tracking boundary | REUSE-014, RDP-012 | outcome log、用户授权、correlation 方法缺失 | outcome 数据分类、consent/privacy、non-claim wording | research |
| Rubric calibration / role drill map | REUSE-011, RDP-007 | 缺 human labels、golden cases、role-level mapping | rubric versioning、role/JD drill taxonomy、人工审查样例 | research |
| Project-native coaching state lifecycle | REUSE-016, RDP-001 | 统一 state schema、migration、archive 规则缺失 | state inventory、owner、retention/archive 决策 | research |
| Bounded challenge policy | REUSE-015, RDP-014 | UX opt-in、stop condition、safety copy 缺失 | opt-in copy、stop rules、review gate | research 或 reject |

## 12. Do-Not-Copy Risks

| 风险 | rationale | safer alternative |
| --- | --- | --- |
| 不要复制 `coaching_state.md` 作为项目 schema | 参考文件是 `schema_like_design`，没有 validator、migration、DB model | 从现有 DB/API/Assets/Polish 反推 project-native schema |
| 不要把 reference command docs 当产品命令引擎 | 它们是 `design-only` Markdown workflow | 只抽取 action registry 思路，并用项目测试验证 |
| 不要把 storybank 写成现有 Assets 已实现 | 当前只有 Assets 类比面，storybank lifecycle `project_evidence_missing` | 做 Assets mapping research |
| 不要把 transcript processing 写成已有输入能力 | 项目未见 transcript ingestion、privacy、fixture | 先建 transcript discovery brief |
| 不要把 rubric calibration 写成 live scoring quality | 缺 human labels、outcome data 和 calibration eval | 只做 score explanation / confidence boundary |
| 不要把 outcome drift 写成录用预测或结果相关性 | outcome log 和合法数据来源缺失 | 先定义 outcome tracking boundary |
| 不要把 examples 写成测试通过 | examples 不是 pytest/TS/static guard | 转成 behavior-contract seed，后续补真实 tests |
| 不要把 release notes 写成 migration 已实现 | release notes 是 `release_note_claim` | 用 compatibility checklist 和 executable migration evidence |
| 不要把 fake/replay/deterministic/default-off 写成 live-provider quality | 当前 eval/run flags 只证明本地回归或 contract | 在 UI/report 中显示 provider_evidence_type 和 non_claims |
| 不要把 human correction capture 写成自动学习 | correction capture 只是输入记录，不能证明模型改进 | 先存 review state 和 audit trail |
| 不要把 cross-surface consistency 扩到不存在的 surface | LinkedIn/outreach/salary 无项目产品证据 | 限定 Resume/Job/Assets/Polish |
| 不要绕过 active docs 创建 Phase 3 平行计划 | `AGENTS.md` 和 `DOCS_INDEX.md` 禁止新 roadmap/plan 入口 | 采用项进入 `BACKLOG.md` 和 `DELIVERY_PLAN.md` |

## 13. Phase 3 Candidate Seeds

FE-SEED-* 是候选种子，不是任务。Phase 3 需要把被接受的 seed 转成正式 BACKLOG 任务；`research`、`deferred` 和 `reject` 不能直接实现。

| ID | title | source RDP/REUSE/ADB | problem | target | evidence | readiness | scope | validation_surface | risk | Phase 3 建议状态 |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| FE-SEED-001 | Evidence / non-claim guard consolidation | RDP-006, RDP-017; REUSE-001; ADB-001 | Phase 3 容易把 partial、design-only、replay 写成 done/live quality | 统一候选 evidence status、non_claims、UI wording rule | capability matrix、skeleton guard、eval reports `executable_evidence` | strong | 工程 guardrail / 文档治理 | static rg、focused tests、diff check | 过度保守导致真实进展难表达 | support_task |
| FE-SEED-002 | API/frontend envelope contract drift guard | RDP-005; REUSE-002; ADB-002 | source/confidence/evidence 字段后端和前端可能漂移 | 校验 `envelope.py` 与 `envelope.ts` 字段一致 | API/web envelope `executable_evidence` | strong | 工程 guardrail | schema parity、route snapshot、TS/static guard | 字段泛化过大 | FE_candidate |
| FE-SEED-003 | Workbench state-aware recommended next action | RDP-003, RDP-010; REUSE-005; ADB-005 | Workbench action 复杂，用户下一步不总是清晰 | 提供 send/regenerate/feedback/next 的可审计 view model | `InterviewPage.tsx`, `InterviewPage.test.ts`, `tests/web/test_interview_actions.py` | medium | 产品能力强化 | frontend unit/static tests | 误复制 reference command router | FE_candidate |
| FE-SEED-004 | Polish input readiness / quality gate | RDP-005, RDP-010; REUSE-018; ADB-012 | 输入不足时可能生成过度完整反馈 | 缺证据时降置信、推荐补资料或显式继续 | feedback validation/warnings partial `executable_evidence` | medium | 产品能力强化 / 工程 guardrail | API warning tests、UI notice tests | 偷渡 transcript feature | FE_candidate |
| FE-SEED-005 | Human correction capture for Polish feedback | RDP-011; REUSE-007; ADB-007 | 用户纠错未形成审计输入 | 捕获 correction note、source refs、review state | feedback validation/service/tests partial evidence | medium | 产品能力强化 | API schema tests、UI state tests、redaction checks | 被误写成 automatic calibration | FE_candidate |
| FE-SEED-006 | Polish progress tree gated progression | RDP-010; REUSE-006; ADB-006 | 进度树缺少 gate/redo/next action 的统一说明 | 把 gated progression adapt 到现有 Polish progress tree | Workbench/Polish partial evidence | medium | 产品能力强化 | UI state tests、contract tests | 新建 Training 主流程 | FE_candidate |
| FE-SEED-007 | Claim boundary UI wording rules | RDP-006, RDP-017; REUSE-010; ADB-010 | UI 文案可能隐藏 low confidence/default-off/replay 边界 | 文案跟随 source/confidence/provider_evidence_type | envelope/eval/capability evidence | medium | 产品能力强化 / 工程 guardrail | UI text/static rg guard | 文案过硬影响体验 | FE_candidate |
| FE-SEED-008 | Examples as behavior-contract seed | RDP-016; REUSE-003; ADB-003 | reference examples 有价值但不能验证 | 把 examples 转成 acceptance/golden case seed | reference examples `design-only` + project tests `executable_evidence` | strong | 工程 guardrail | 文档标记、后续真实测试 | examples 带入不适用假设 | support_task |
| FE-SEED-009 | Developer command matrix and lazy reading packet | RDP-002, RDP-004, RDP-018; REUSE-004, REUSE-017; ADB-004, ADB-011 | 命令和文档读取容易越界 | 建立 task-type command matrix 与 lazy reading packet | doc governor CLI、package scripts、DOCS_INDEX | medium | agent workflow / 文档治理 | doc governor/static check | 矩阵漂移 | support_task |
| FE-SEED-010 | Existing-surface consistency guard | RDP-013; REUSE-008; ADB-008 | Resume/Job/Assets/Polish 可能事实不一致 | 只在现有 surfaces 做 source refs 和 JD binding consistency | Resume/Job/Assets/Polish partial evidence | medium | 产品能力强化 | contract/static tests | 扩张到不存在 surfaces | FE_candidate_limited |
| FE-SEED-011 | Role/JD-specific practice routing discovery | RDP-007, RDP-010, RDP-013; REUSE-011 | 当前没有明确 role drill map | 研究如何基于 JD/role 调整 practice path | feedback/JD binding partial，role drill map `project_evidence_missing` | weak | 产品能力强化 / research | design brief、golden examples | 被误写成自动 calibration | research |
| FE-SEED-012 | Storybank to Assets lifecycle discovery | RDP-009; REUSE-013 | storybank 是可复用面试素材，但项目证据不足 | 判断是否扩展 Assets 或新建 story asset model | storybank `project_evidence_missing` | weak | research / deferred | schema proposal、asset mapping、privacy review | 误称 Assets 已实现 storybank | deferred |
| FE-SEED-013 | Transcript quality gate discovery | RDP-008; REUSE-012 | transcript analysis 缺输入质量边界 | 研究 transcript input model、privacy、fixture、quality gate | transcript `project_evidence_missing` | weak | research | discovery brief、fixture plan | 偷渡 transcript ingestion | research |
| FE-SEED-014 | Outcome tracking boundary discovery | RDP-012; REUSE-014 | outcome drift 需要真实结果数据，但当前无证据 | 定义 outcome log、consent、non-claim wording | outcome log `project_evidence_missing` | weak | research | privacy/design review | 误写成录用预测 | research |
| FE-SEED-015 | Project-native coaching state lifecycle research | RDP-001; REUSE-016 | 参考 state schema 不可复制，项目 surface 分散 | 盘点 state owner、update trigger、archive/retention | reference `schema_like_design`; project unified state missing | weak | research | state inventory、schema brief | 复制 `coaching_state.md` | research |
| FE-SEED-016 | Bounded challenge protocol policy | RDP-014; REUSE-015 | challenge protocol 可能有质量价值，但产品安全边界不足 | 定义 opt-in、stop condition、resolution 或保持拒绝 | product UX `unsupported_or_unknown` | blocked | research / reject | policy review | 无边界强压用户 | reject |

Phase 3 readiness remains `partial`。可以直接处理的主要是 FE-SEED-001 到 FE-SEED-010；FE-SEED-011 到 FE-SEED-016 需要 research/deferred/reject，不应作为直接实现项。

## 14. Validation and Acceptance Strategy

Phase 3 的验证应先证据、后功能；先边界、后体验。本文不运行 install/build/test/migration/Docker，也不运行 Spec Kit。后续实现窗口需要按具体 seed 选择 focused 验证。

| 验证层 | 接受标准 | 适用 seed |
| --- | --- | --- |
| Scope gate | 修改文件和任务入口必须符合 `AGENTS.md`、`DOCS_INDEX.md`、`BACKLOG.md`、`DELIVERY_PLAN.md` | 所有 seed |
| Evidence gate | 每个候选必须声明 `executable_evidence`、`design-only`、`schema_like_design`、`project_evidence_missing` 或 `unsupported_or_unknown` | 所有 seed |
| NEW_FROM_REFERENCE gate | `NEW_FROM_REFERENCE` 必须说明 Phase 1 为什么没体现、项目证据是否足够、缺证据时不能 FE_candidate | REUSE-003 到 REUSE-018 |
| Non-claim gate | fake/replay/deterministic/default-off 不得写成 live-provider quality | FE-SEED-001, FE-SEED-007 |
| Contract gate | API/frontend source/confidence/evidence 字段不得 drift | FE-SEED-002 |
| Product UX gate | recommended next action、input readiness、correction capture 必须有 UI/contract 验证面 | FE-SEED-003 到 FE-SEED-007 |
| Research gate | transcript/storybank/outcome/state lifecycle 必须先有 design brief 和最小证据计划 | FE-SEED-011 到 FE-SEED-015 |
| Reject gate | bounded challenge protocol 不得在缺 opt-in/safety/resolution 时进入实现 | FE-SEED-016 |

本文自身的 post-write 验收应包含：

```bash
git status --short --untracked-files=all
test -f docs/feature-enhancement/02b_reuse_synthesis.md
git diff --stat
git diff --check -- docs/feature-enhancement/02b_reuse_synthesis.md
rg -n "RDP-[0-9]{3}|REUSE-[0-9]{3}|ADB-[0-9]{3}|FE-SEED-[0-9]{3}" docs/feature-enhancement/02b_reuse_synthesis.md
rg -n "NEW_FROM_REFERENCE|adopt|adapt|reject|research" docs/feature-enhancement/02b_reuse_synthesis.md
rg -n "project_evidence_missing|design-only|schema_like_design|unsupported_or_unknown|executable_evidence" docs/feature-enhancement/02b_reuse_synthesis.md
```

最终 `git status --short --untracked-files=all` 只应出现：

```text
 M docs/feature-enhancement/02b_reuse_synthesis.md
```

## 15. Recommended Phase 3 Inputs

Phase 3 推荐按以下顺序消费输入：

1. 先读本文件 `docs/feature-enhancement/02b_reuse_synthesis.md`，只从 FE-SEED-* 选择候选，不直接从参考 Skill 生成任务。
2. 读取 `AGENTS.md` 和 `docs/00-governance/DOCS_INDEX.md`，确认 active docs、写入边界和 archive 规则。
3. 若候选进入正式计划，再读取 `docs/03-delivery/BACKLOG.md` 和 `docs/03-delivery/DELIVERY_PLAN.md`，按现有任务体系登记。
4. 需要项目事实时，回读 Phase 1；需要参考原文时，回读 Phase 2 和固定 commit 的 reference clone。
5. 对产品能力强化，优先看 Workbench、Polish、Assets、Resume/Job binding 的 current executable evidence。
6. 对工程 guardrail，优先看 envelope schema、capability matrix、skeleton guard、eval scripts、runtime flags、provider boundary。
7. 对 agent workflow 和文档治理，优先看 doc governor CLI、package scripts、`DOCS_INDEX.md`。
8. 对 `project_evidence_missing` 项，只允许生成 research/deferred brief，不允许生成实现任务。

推荐 Phase 3 第一批可审计输入：

| 优先级 | Seed | 原因 |
| --- | --- | --- |
| MUST | FE-SEED-001 | 防止后续所有候选 false claim。 |
| MUST | FE-SEED-002 | API/frontend envelope 是多个产品体验的共同 contract。 |
| SHOULD | FE-SEED-003, FE-SEED-004, FE-SEED-005, FE-SEED-006, FE-SEED-007 | 它们直接强化 Workbench/Polish 产品体验，且有 partial 项目证据。 |
| SHOULD | FE-SEED-008, FE-SEED-009 | 它们提升验证和工作流质量，不需要扩产品 surface。 |
| COULD | FE-SEED-010 | 有产品价值，但必须限定现有 surfaces。 |
| LATER | FE-SEED-011 到 FE-SEED-015 | 缺项目证据，需要 research/deferred。 |
| reject | FE-SEED-016 | 目前不满足产品安全边界。 |

## 16. Open Questions

1. Phase 3 第一批是先做 FE-SEED-001/002 的 guardrail，还是并行推进 FE-SEED-003 的 Workbench recommended next action？
2. `source_availability`、`confidence_level`、`evidence_refs` 是否应由 Pydantic schema 生成 TS type，还是先用 parity guard 控制手写同步？
3. Polish correction capture 的最小用户动作是什么：标记反馈不准、补充事实、提交 correction note，还是三者都要？
4. input readiness 是只显示 warning，还是阻止生成完整反馈？是否需要“继续但低置信”的用户选择？
5. storybank 是否应映射到现有 Assets，还是另建 Story/Experience model？当前证据只能支持 research。
6. role/JD-specific practice routing 的最小可验证输入是什么：JD category、target role、question category，还是用户目标？
7. transcript quality gate 是否属于当前产品边界？如果是，隐私、存储、fixture 和 parser ownership 谁负责？
8. outcome tracking 是否有合法、稳定且用户可控的数据来源？没有时 UI 应如何说明不能做 outcome correlation？
9. claim boundary UI wording 应放在 shared copy helper、envelope rendering helper，还是每个 surface 独立处理？
10. bounded challenge protocol 是否有用户明确 opt-in 场景？如果没有，是否永久 reject？

## 17. Evidence Index

本索引区分 reference evidence 和 project evidence。reference evidence 主要是 `design-only`、`schema_like_design` 或 `release_note_claim`；project evidence 才可能是 `executable_evidence`。

### Reference Evidence

| 证据 | 分类 | 本文使用方式 |
| --- | --- | --- |
| `/tmp/interview-coach-skill-phase2-20260611/SKILL.md` | `design-only` | command registry、mode routing、lazy reference loading、session state 设计原语 |
| `/tmp/interview-coach-skill-phase2-20260611/README.md` | `design-only` | command map、storybank、practice/mock/progress overview |
| `/tmp/interview-coach-skill-phase2-20260611/VERSIONS.md` | `release_note_claim` | versioned workflow evolution，不作为实现证据 |
| `/tmp/interview-coach-skill-phase2-20260611/releases/v2.md`, `releases/v3.md` | `release_note_claim` | 能力扩展声明，不作为 migration 或 executable proof |
| `/tmp/interview-coach-skill-phase2-20260611/references/coaching-state-schema.md` | `schema_like_design` | state lifecycle 设计，不复制为项目 schema |
| `/tmp/interview-coach-skill-phase2-20260611/references/schema-migration.md` | `schema_like_design` | migration idea，不作为 migration automation |
| `/tmp/interview-coach-skill-phase2-20260611/references/state-update-triggers.md` | `design-only` | update trigger 设计，不作为 event processor |
| `/tmp/interview-coach-skill-phase2-20260611/references/archival-rules.md` | `design-only` | archive/retention 设计 |
| `/tmp/interview-coach-skill-phase2-20260611/references/evidence-sourcing.md` | `design-only` | source/confidence/unknown handling |
| `/tmp/interview-coach-skill-phase2-20260611/references/mode-detection.md` | `design-only` | intent priority 和 routing 设计 |
| `/tmp/interview-coach-skill-phase2-20260611/references/rubrics-detailed.md` | `design-only` | rubric dimensions 和 scoring explanation seed |
| `/tmp/interview-coach-skill-phase2-20260611/references/calibration-engine.md` | `design-only` | calibration/outcome drift idea，只能 research |
| `/tmp/interview-coach-skill-phase2-20260611/references/transcript-formats.md`, `transcript-processing.md` | `design-only` | transcript quality gate research seed |
| `/tmp/interview-coach-skill-phase2-20260611/references/storybank-guide.md`, `story-mapping-engine.md` | `design-only` | storybank lifecycle 和 story fit research seed |
| `/tmp/interview-coach-skill-phase2-20260611/references/commands/*.md` | `design-only` | command-specific workflow patterns，不是 runtime commands |
| `/tmp/interview-coach-skill-phase2-20260611/references/examples.md` | `design-only` | behavior-contract seed，不是 tests |
| `/tmp/interview-coach-skill-phase2-20260611/tests/`, `scripts/`, `schemas/`, `contracts/`, `evals/`, `validation/` | `unsupported_or_unknown` / absence | Phase 2 未发现这些可执行目录；不能推断 reference executable implementation |

### Project Evidence

| 证据 | 分类 | 本文使用方式 |
| --- | --- | --- |
| `docs/feature-enhancement/01_project_architecture_assessment.md` | project_assessment | 当前项目事实、候选增强、non-claim 边界 |
| `docs/feature-enhancement/02_reference_skill_capability_study.md` | reference_capability_study | 参考 inventory、absence_verified、CAP/REF-OPP |
| `AGENTS.md`, `docs/00-governance/DOCS_INDEX.md` | governance_evidence | active docs、写入边界、禁止并行计划 |
| `docs/03-delivery/refactor/CAPABILITY_PRESERVATION_MATRIX.md` | `executable_evidence` supporting | status vocabulary、partial/skeleton/default-off non-claim |
| `tests/api/test_skeleton_guard.py` | `executable_evidence` | skeleton/partial/non-claim guard |
| `apps/api/app/schemas/envelope.py` | `executable_evidence` | API source/confidence/evidence envelope |
| `apps/web/src/shared/api/envelope.ts` | `executable_evidence` | frontend envelope mirror |
| `apps/api/app/schemas/scoring.py` | `executable_evidence` | score/confidence/allowed formal score boundary |
| `apps/api/app/schemas/job_match.py` | `executable_evidence` | confidence/evidence consistency validation |
| `apps/api/app/application/polish/feedback_validation.py` | `executable_evidence` | feedback schema、warnings、unsafe marker guard |
| `tests/api/test_polish_feedback_validation.py`, `tests/api/test_polish_feedback_generation_service.py` | `executable_evidence` | feedback validation 和 fake-provider non-success checks |
| `apps/api/app/domain/polish/policies/source_support_policy.py` | `executable_evidence` | source support levels and insufficient context boundary |
| `apps/api/app/application/polish/canonical_evidence.py` | `executable_evidence` | canonical evidence pack、refs、warnings、blocking issues |
| `apps/api/app/application/ai_runtime/runtime_flags.py` | `executable_evidence` | default-off runtime flags，不证明 live quality |
| `scripts/evals/run_eval_gate.py`, `scripts/evals/run_l5_eval_suite.py` | `executable_evidence` | deterministic/replay eval reports and non_claims |
| `.github/workflows/eval-gate.yml` | `executable_evidence` | replay/deterministic CI gate command |
| `apps/api/app/application/llm/provider_boundary.py` | `executable_evidence` | provider boundary and redaction guard |
| `apps/web/src/pages/interview/InterviewPage.tsx`, `apps/web/src/pages/interview/InterviewPage.test.ts` | `executable_evidence` | Workbench action/state/progress tree partial evidence |
| `tests/web/test_interview_actions.py` | `executable_evidence` | Workbench action static guard |
| `tools/doc_governor/cli.py` | `executable_evidence` | doc governor command registry and preview/check commands |
| `package.json`, `apps/web/package.json` | `executable_evidence` | developer command matrix and frontend typecheck entry |
| transcript ingestion, storybank lifecycle, outcome log, full coaching state migration | `project_evidence_missing` | 只能进入 research/deferred，不能进入 FE_candidate |
