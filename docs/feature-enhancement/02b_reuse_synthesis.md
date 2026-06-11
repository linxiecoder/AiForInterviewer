---
title: Reuse Synthesis from Reference Skill
type: assessment
status: draft
owner: architecture-review
permalink: ai-for-interviewer/feature-enhancement/reuse-synthesis
---

# Reuse Synthesis from Reference Skill

## 1. Purpose and Inputs

本文用于把 Phase 1 的项目架构评估和 Phase 2 的参考技能能力研究转换成 Phase 3 可消费的复用桥接输入。它不登记新任务，不替代 `docs/03-delivery/BACKLOG.md`，也不把参考仓库的 Markdown 工作流升级为当前项目实现事实。

输入范围：

| 输入 | 用途 | 证据等级 |
| --- | --- | --- |
| `docs/feature-enhancement/01_project_architecture_assessment.md` | 项目现状、痛点、候选增强方向 | project_assessment |
| `docs/feature-enhancement/02_reference_skill_capability_study.md` | 参考技能能力清单、证据分类和初步机会 | reference_capability_study |
| `/tmp/interview-coach-skill-phase2-20260611` at `634a8dd8689e0420c21e5f0c8ae3cfa9e1a7ab7e` | 参考技能原始 Markdown 证据 | direct_reference_text |
| `apps/api/app/schemas/envelope.py`, `apps/web/src/shared/api/envelope.ts` | 当前 API/frontend envelope 字段 | executable_evidence |
| `apps/api/app/application/polish/feedback_validation.py`, `tests/api/test_polish_feedback_validation.py`, `tests/api/test_polish_feedback_generation_service.py` | Polish feedback schema、warning、unsafe marker guard | executable_evidence |
| `apps/api/app/application/ai_runtime/runtime_flags.py`, `scripts/evals/run_eval_gate.py`, `scripts/evals/run_l5_eval_suite.py` | default-off runtime、deterministic/replay eval non-claim | executable_evidence |
| `docs/03-delivery/refactor/CAPABILITY_PRESERVATION_MATRIX.md`, `tests/api/test_skeleton_guard.py` | capability status/non-claim guard | executable_evidence |
| `apps/web/src/pages/interview/InterviewPage.tsx`, `apps/web/src/pages/interview/InterviewPage.test.ts`, `tests/web/test_interview_actions.py` | workbench action/state/front-end contract evidence | executable_evidence |
| `tools/doc_governor/cli.py`, `package.json`, `.github/workflows/eval-gate.yml` | project command/quality gate surfaces | executable_evidence |

参考技能证据分类：

| 类别 | 文件 | 本文处理 |
| --- | --- | --- |
| root workflow | `SKILL.md`, `README.md`, `VERSIONS.md` | design-only；可抽取机制，不可视为运行时实现 |
| release notes | `releases/v2.md`, `releases/v3.md` | release_note_claim；仅说明版本演进意图 |
| shared references | `references/*.md` | design-only 或 schema_like_design；`coaching-state-schema.md`、`schema-migration.md` 不是可执行 schema |
| commands | `references/commands/*.md` | design-only；可抽取 command/mode/routing pattern |
| examples | `references/examples.md` | example_calibration；不能当测试 |
| executable artifacts | `tests/`, `scripts/`, `schemas/`, `contracts/`, `evals/`, `validation/` | 未发现可执行证据；本文标记为 `unsupported_or_unknown` 或 `project_evidence_missing` 时不生成 FE_candidate |

本文使用的状态词：

| 词 | 含义 |
| --- | --- |
| `executable_evidence` | 当前项目存在代码或测试证据 |
| `design-only` | 参考技能仅有 Markdown 工作流或说明 |
| `schema_like_design` | 看似 schema 的 Markdown 模板，但不是可执行 schema |
| `project_evidence_missing` | 当前项目未找到同等实现证据 |
| `unsupported_or_unknown` | 证据不足，不能推断为可复用实现 |

## 2. Why Phase 1 and Phase 2 Are Not Sufficient Yet

Phase 1 的价值是建立项目侧事实：当前仓库已有 Resume/Job/Binding/Assets 等基础能力、Polish 处于 partial 状态、AI Runtime/eval 只能证明 deterministic/replay/local regression contract，不能证明 live-provider quality。它也提出了 CAND-001 到 CAND-010 等候选方向。但 Phase 1 没有深读参考技能，也没有把参考技能拆成可复用设计原语。

Phase 2 的价值是建立参考侧事实：参考技能覆盖 coaching state、23 个 command、rubric、storybank、transcript processing、outcome calibration、cross-surface rewrite 等能力；同时 Phase 2 已确认这些能力基本来自 Markdown 说明，没有 tests/scripts/contracts/evals 之类可执行证据。Phase 2 的不足是它仍然按参考技能自身分类，尚未把能力转成当前项目可采用、需改造、需拒绝、需研究的工程决策。

因此，Phase 1 不能直接生成 Phase 3，因为它缺少参考复用拆解；Phase 2 也不能直接生成 Phase 3，因为它缺少项目证据映射和 adoption/reject 边界。

Phase 3 should not consume 01 and 02 directly. It should consume this 02b synthesis as the bridge input.

## 3. Reuse-Oriented Reference Reading

本文按“机制”而不是“命令名”读取参考技能：

| 机制 | 参考来源 | 可复用核心 | 证据边界 |
| --- | --- | --- | --- |
| state lifecycle | `SKILL.md`, `references/coaching-state-schema.md`, `references/state-update-triggers.md`, `references/archival-rules.md` | session state、storybank、score history、outcome log、archive thresholds | schema_like_design；不是数据库模型或 migration |
| command/mode routing | `SKILL.md`, `references/mode-detection.md`, `references/commands/*.md` | command registry、file routing、multi-step intent detection | design-only；不能当 runtime router |
| lazy reference loading | `SKILL.md` command table and file routing | 只有命令触发时加载对应 reference | design-only；可转成项目文档/CLI strategy |
| evidence/confidence sourcing | `references/evidence-sourcing.md`, `references/commands/decode.md`, `references/commands/prep.md` | source tier、confidence label、unknown handling | design-only；项目已有 envelope 字段可承接 |
| rubric calibration | `references/rubrics-detailed.md`, `references/calibration-engine.md` | five-dimensional scoring、seniority、root cause、outcome drift | design-only；不能宣称自动 scoring quality |
| transcript quality gate | `references/transcript-formats.md`, `references/transcript-processing.md`, `references/commands/analyze.md` | format detection、quality signal、partial transcript handling | project_evidence_missing；仅 research |
| storybank lifecycle | `references/storybank-guide.md`, `references/story-mapping-engine.md`, `references/commands/stories.md` | story inventory、reuse mapping、retirement/enhancement | project_evidence_missing 或 partial asset analogy；仅 research/deferred |
| gated progression | `references/commands/practice.md`, `references/commands/mock.md`, `references/commands/progress.md` | stage gate、self-assessment delta、redo protocol | 可映射到 Polish progress tree，但需 adapt |
| human correction loop | `references/commands/feedback.md`, `references/calibration-engine.md` | feedback capture、coach correction、calibration update | 可映射到 Polish validation warnings/HITL，但需 adapt |
| cross-surface consistency | `references/commands/resume.md`, `linkedin.md`, `pitch.md`, `outreach.md`, `apply.md` | story and positioning consistency across surfaces | 项目仅有 Resume/Job/Assets/Polish；需 adapt/research |
| versioned workflow evolution | `VERSIONS.md`, `releases/*.md`, `references/schema-migration.md` | phased workflow evolution and compatibility notes | release_note_claim/schema_like_design；不可当 migration automation |

## 4. Reusable Design Primitives

| ID | 设计原语 | 参考证据 | 项目证据状态 | 复用约束 |
| --- | --- | --- | --- | --- |
| RDP-001 | 状态生命周期必须有 schema、update trigger、archive/retention 规则 | `coaching_state.md` 模板、state update triggers、archival rules | partial；项目有 DB models、reports/evals metadata，但没有统一 interview coaching state | 只能作为目标模型设计，不可复制 `coaching_state.md` |
| RDP-002 | command registry 与 file routing 分离 | `SKILL.md` command table、`references/commands/*.md` | executable_evidence；`tools/doc_governor/cli.py` 有 subparser command registry | adapt 到项目 CLI/docs governor 或前端 action registry |
| RDP-003 | mode detection 应按优先级和多步意图路由 | `references/mode-detection.md` | partial；`InterviewPage.tsx` 有 action/view-model 和 `regenerate_current_node`/`new_question` 区分 | adapt；不能把 Markdown priority list 当 runtime router |
| RDP-004 | lazy reference loading 降低上下文噪声 | `SKILL.md` file routing | executable_evidence supporting；项目已有 docs index/governance 和 command packet pattern | adopt 为工作流/文档读取规则，非产品代码默认实现 |
| RDP-005 | evidence/confidence/source availability 是一等字段 | `evidence-sourcing.md`, `decode.md`, `prep.md` | executable_evidence；API envelope 和 web envelope 有 `source_availability`, `evidence_refs`, `low_confidence_flags`, `confidence_level` | adopt/adapt，作为 Phase 3 contract drift guard 输入 |
| RDP-006 | non-claim discipline 需要固定词表和负证据 | Phase 2 absence evidence、reference design-only boundary | executable_evidence；capability matrix、skeleton guard、eval non-claims | adopt；不能把 reference release notes 写成实现 |
| RDP-007 | rubric calibration 要区分 scoring rubric 与 outcome correlation | `rubrics-detailed.md`, `calibration-engine.md` | partial；Polish feedback 有 score/confidence，但没有真实 outcome correlation | research 或 adapt 为 score explanation guard |
| RDP-008 | transcript format detection 与 quality gate 应先于分析 | `transcript-formats.md`, `transcript-processing.md`, `analyze.md` | project_evidence_missing | research；不得生成 FE_candidate |
| RDP-009 | storybank 是生命周期资产，不只是回答样例库 | `storybank-guide.md`, `story-mapping-engine.md` | project_evidence_missing；项目 Assets 可类比但不是 storybank | research/deferred |
| RDP-010 | gated progression 需要 stage、gate、redo、next action | `practice.md`, `mock.md`, `progress.md` | partial；Polish progress tree、question/answer/feedback loop 存在 | adapt 到 workbench/progress tree |
| RDP-011 | human correction loop 应把用户纠错写入后续判断 | `feedback.md`, `calibration-engine.md` | partial；Polish feedback validation 有 warnings/HITL-like low confidence flags | adapt，先做 correction capture，不做自动校准声明 |
| RDP-012 | outcome drift 应由真实结果反馈驱动 | `calibration-engine.md`, `progress.md`, `feedback.md` | project_evidence_missing | research；不得宣称评分与录用结果相关 |
| RDP-013 | cross-surface consistency 需要共用 positioning/story source | `resume.md`, `linkedin.md`, `pitch.md`, `outreach.md`, `apply.md` | partial；项目有 Resume/Job/Assets/Polish，但无 LinkedIn/outreach surfaces | adapt 局部，不做一键全域 rewrite |
| RDP-014 | challenge protocol 必须有边界、分级和 resolution | `challenge-protocol.md` | partial；Phase 12 L5 eval 有 bounded loop/non-claim guard | reject unbounded copy；可 research bounded challenge |
| RDP-015 | versioned workflow evolution 需要兼容矩阵和 migration proof | `VERSIONS.md`, `releases/*.md`, `schema-migration.md` | executable_evidence supporting；项目有 capability preservation matrix、route snapshot | adapt 为 docs/contract migration checklist，不当自动 migration |
| RDP-016 | examples 可作为 calibration prompts，但不能替代测试 | `references/examples.md` | executable_evidence；项目已有 Python/TS static tests | adopt 该边界；examples 只能辅助 acceptance text |

## 5. Project Problems Reopened by Reference Study

| 问题 | Phase 1 事实 | 参考技能带来的重新打开点 | Phase 3 含义 |
| --- | --- | --- | --- |
| P-001 capability status 仍容易被升级误写 | matrix/skeleton guard 已存在 | 参考技能大量 design-only 文本更容易被误读为能力实现 | Phase 3 必须先继承 non-claim gate |
| P-002 workbench action/mode routing 复杂度升高 | `InterviewPage.tsx` 已承担 session tree、question、answer、feedback、regenerate | 参考技能有 command/mode/routing 体系 | 需要把 action registry/view model 抽成可审计边界 |
| P-003 API/frontend contract drift | Pydantic envelope 与 TS envelope 手写同步 | 参考技能强调 source/confidence/next action | Phase 3 可优先做 envelope/contract drift guard |
| P-004 Polish feedback 需要 evidence/correction 可见性 | feedback validation 有 schema、warnings、unsafe marker | 参考技能把 feedback 作为 calibration input | 先做 human correction capture，不做 automatic outcome calibration |
| P-005 provider/eval evidence taxonomy | runtime default-off，eval replay/deterministic non-claim | 参考技能没有 executable evidence | Phase 3 必须禁止 reference-only quality claim |
| P-006 transcript/storybank/outcome 能力缺失 | 当前项目没有 transcript ingestion/storybank/outcome log 证据 | 参考技能覆盖完整 coaching lifecycle | 只能作为 research/deferred 输入 |
| P-007 doc/command governance 可借鉴 lazy loading | doc governor 有大量 subcommands | 参考技能 command registry 更聚焦用户 intent | 可 adapt 成 developer command matrix/packet reading |
| P-008 cross-surface consistency 局部存在但不完整 | Resume/Job/Assets/Polish 存在，LinkedIn/outreach 不存在 | 参考技能跨 surface 完整 | Phase 3 只能局部复用到已有 surfaces |

## 6. Project × Reference Reuse Matrix

| ID | RDP | decision | 项目证据 | candidate_strength | Phase 3 treatment | 说明 |
| --- | --- | --- | --- | --- | --- | --- |
| REUSE-001 | RDP-006 | adopt | `tests/api/test_skeleton_guard.py`, capability matrix, eval scripts | strong | support_task | 直接继承 status/non-claim vocabulary，防止把 design-only 写成 done |
| REUSE-002 | RDP-005 | adopt | API/web envelope 已有 source/confidence/evidence fields | strong | FE_candidate | 用于 contract drift guard 和 workbench 可见状态 |
| REUSE-003 | RDP-016 | adopt | 项目已有 pytest/TS tests；参考 examples 无执行性 | strong | support_task | examples 只能进入 acceptance examples，不作为 tests |
| REUSE-004 | RDP-002 | adapt | `tools/doc_governor/cli.py`, `package.json` scripts | medium | support_task | 借鉴 command registry/lazy routing，服务开发者命令矩阵 |
| REUSE-005 | RDP-003 | adapt | `InterviewPage.tsx`, `InterviewPage.test.ts` 区分 question/action/mode | medium | FE_candidate | 转成 workbench action state machine 或 view model，不复制 Markdown routing |
| REUSE-006 | RDP-010 | adapt | Polish progress tree routes and tests exist, aggregate remains partial | medium | FE_candidate | 把 gated progression 收敛到当前 progress tree，不引入新 Training 产品流 |
| REUSE-007 | RDP-011 | adapt | feedback validation warnings、low_confidence_flags、candidate refs | medium | FE_candidate | 先做 human correction capture and review loop |
| REUSE-008 | RDP-013 | adapt | Resume/Job/Assets/Polish exists; no LinkedIn/outreach | medium | FE_candidate | 只做已有 surfaces 的 consistency guard |
| REUSE-009 | RDP-015 | adapt | capability matrix、route snapshot、doc governor state tooling | medium | support_task | 版本演进可转为 compatibility checklist，不能当 migration automation |
| REUSE-010 | RDP-007 | research | Polish feedback 有 score/confidence，但无 outcome correlation | weak | research | rubric calibration 要先定义可验证数据来源 |
| REUSE-011 | RDP-008 | research | project_evidence_missing | weak | research | transcript quality gate 需要先确认输入、存储、隐私、fixture |
| REUSE-012 | RDP-009 | research | project_evidence_missing | weak | deferred | storybank lifecycle 需要资产模型研究；不能直接进 FE_candidate |
| REUSE-013 | RDP-012 | research | project_evidence_missing | weak | research | outcome drift 依赖真实 outcome log，目前不能做 product claim |
| REUSE-014 | RDP-014 | reject | Phase 12 eval only supports bounded deterministic/replay guard | blocked | reject | 拒绝无边界 Level 5 challenge protocol 和无 resolution 的强压流程 |
| REUSE-015 | RDP-001 | research | partial state evidence only | weak | research | 不复制 `coaching_state.md`，先研究 project-native state lifecycle |
| REUSE-016 | RDP-004 | adopt | docs index + command packets 支持按需读取 | strong | support_task | 作为 AI 工作流和 doc governor 的读取策略 |

## 7. Adoption Design Briefs

| ID | 目标 | 复用来源 | 项目落点 | 边界 |
| --- | --- | --- | --- | --- |
| ADB-001 | Evidence and non-claim guard | RDP-005, RDP-006, RDP-016 | capability matrix、eval scripts、API/web envelope | adopt；不产生新业务能力 |
| ADB-002 | Workbench action and mode routing | RDP-002, RDP-003, RDP-010 | `InterviewPage.tsx` action view models and tests | adapt；保持 current Polish scope |
| ADB-003 | API/frontend source/confidence contract guard | RDP-005 | Pydantic envelope + TS envelope | adopt/adapt；优先防 drift |
| ADB-004 | Polish feedback correction loop | RDP-011 | feedback validation/service/tests | adapt；human correction 先于 automatic calibration |
| ADB-005 | Provider and eval quality lane separation | RDP-006 | provider boundary、runtime flags、eval gates | adopt；real provider quality 仍是 separate lane |
| ADB-006 | Transcript quality gate research | RDP-008 | 未定输入/存储/隐私边界 | research；project_evidence_missing |
| ADB-007 | Storybank and asset lifecycle research | RDP-009, RDP-013 | Assets/Resume/Polish 可能承接 | research/deferred；project_evidence_missing |
| ADB-008 | Gated progression for Polish progress tree | RDP-010 | progress-tree routes、current question composer | adapt；不新建 Training flow |
| ADB-009 | Developer command matrix | RDP-002, RDP-004 | `tools/doc_governor/cli.py`, `package.json` | support_task；不影响 runtime |
| ADB-010 | Outcome drift and rubric calibration research | RDP-007, RDP-012 | 需要 outcome log and privacy policy | research；不得宣称 correlation |
| ADB-011 | Cross-surface consistency within existing surfaces | RDP-013 | Resume/Job/Assets/Polish | adapt；拒绝一口气复制 LinkedIn/outreach/salary 全 surface |

## 8. What to Adopt Directly

可以直接采用的是边界和判定方法，而不是参考技能的具体文件结构。

| 项 | 采用内容 | 原因 |
| --- | --- | --- |
| NEW_FROM_REFERENCE adopt-001 | 把 source/confidence/evidence/non-claim 当作 Phase 3 的必填审查维度 | 项目已有 envelope/eval/capability guard，可直接承接 |
| NEW_FROM_REFERENCE adopt-002 | 把 examples 与 tests 严格分离 | 参考仓库 examples 无执行性，项目已有测试入口 |
| NEW_FROM_REFERENCE adopt-003 | 按需读取 reference/command 文档 | 降低上下文噪声，符合现有 docs index/doc governor 思路 |
| NEW_FROM_REFERENCE adopt-004 | 对 release notes 使用 release_note_claim 分类 | 防止把版本说明当 migration evidence |
| NEW_FROM_REFERENCE adopt-005 | 使用 `project_evidence_missing` 阻断 FE_candidate | 防止 transcript/storybank/outcome 直接混入 implementation backlog |

## 9. What to Adapt

| 项 | 改造内容 | 改造方式 |
| --- | --- | --- |
| adapt-001 | command/mode routing | 从 Markdown priority list 改造成 workbench/doc-governor 可测试 action registry |
| adapt-002 | gated progression | 映射到 Polish progress tree/current question composer，而不是创建 Training 主流程 |
| adapt-003 | feedback correction loop | 先捕获人工纠错、validation warnings、low confidence flags，再考虑 calibration |
| adapt-004 | cross-surface consistency | 仅覆盖 Resume/Job/Assets/Polish，不复制 LinkedIn/outreach/salary |
| adapt-005 | rubric calibration | 先做 score explanation and confidence guard，不宣称 outcome quality |
| adapt-006 | versioned evolution | 转成 compatibility checklist、route snapshot、schema drift guard |
| adapt-007 | lazy reference loading | 转成 AI workflow/doc governor packet 规则，而不是 runtime dependency loader |

## 10. What to Reject

| 项 | 拒绝内容 | 原因 |
| --- | --- | --- |
| reject-001 | 直接复制 `coaching_state.md` | 它是 schema_like_design，不是项目 DB/API model |
| reject-002 | 把 Markdown command workflow 当 runtime routing | 缺少 executable evidence |
| reject-003 | 把 rubric 当自动 scoring quality | 缺少真实评分校验和 outcome correlation |
| reject-004 | 把 calibration notes 当真实 outcome correlation | project_evidence_missing |
| reject-005 | 把 examples 当 tests | examples 只能说明用例，不验证行为 |
| reject-006 | 把 release notes 当 migration automation | release_note_claim 不是 migration proof |
| reject-007 | 没有 evidence capture 就暴露 confidence labels | 会制造虚假可信度 |
| reject-008 | unbounded Level 5 challenge protocol | 容易突破用户意图和产品安全边界 |
| reject-009 | one-shot cross-surface rewrite | 当前项目没有全部 surfaces 和回滚机制 |
| reject-010 | treating agent guardrail as code enforcement | Markdown guardrail 不能替代代码/测试 gate |
| reject-011 | 把 fake/replay/deterministic eval 写成 live-provider quality | 当前项目已有 non-claim guard 明确禁止 |
| reject-012 | 新建 Training 产品主流程 | 当前治理中 Training 独立产品模式不属于 MVP 实现事实 |

## 11. What Needs More Research

| 研究项 | 原因 | 需要的最小证据 |
| --- | --- | --- |
| transcript quality gate | project_evidence_missing | transcript input model、privacy rule、fixture、parser tests |
| storybank lifecycle | project_evidence_missing | story asset schema、source refs、retirement/enhancement rules |
| outcome drift calibration | project_evidence_missing | outcome log、consent/privacy、correlation methodology |
| rubric seniority calibration | 当前只有 feedback score/confidence 局部证据 | rubric versioning、golden cases、human review labels |
| multi-surface consistency | 当前 surfaces 不完整 | explicit surface inventory、shared positioning source |
| bounded challenge protocol | 参考 Level 5 无项目产品边界 | opt-in policy、stop condition、safety review、HITL trigger |
| state lifecycle migration | 参考 schema 是 Markdown | project-native schema、migration tests、archive rules |

## 12. Do-Not-Copy Risks

1. 不要 copying `coaching_state.md` directly；它是 `schema_like_design`，不是当前项目 schema。
2. 不要 treating Markdown command workflow as runtime routing；必须有代码、测试和可观察 routing contract。
3. 不要 treating rubric as automatic scoring quality；rubric 文档不能证明评分可靠。
4. 不要 treating calibration notes as real outcome correlation；没有真实 outcome log 就只能 research。
5. 不要 treating examples as tests；examples 不能替代 pytest/tsc/static contract。
6. 不要 treating release notes as migration automation；release notes 不是 migration runner。
7. 不要 adding confidence labels without evidence capture；`confidence_level` 必须绑定 source/evidence/low_confidence_flags。
8. 不要 copying unbounded Level 5 challenge protocol；必须有 opt-in、stop condition、resolution。
9. 不要 one-shot cross-surface rewrite；当前项目 surface 不完整且缺少回滚。
10. 不要 treating agent guardrail as code enforcement；Markdown guardrail 只能是工作流约束。
11. 不要把 fake/replay/deterministic eval 当 real provider quality。
12. 不要把 `route prefix only`、`repository pass`、`disabled nav`、`default-off graph` 写成 implemented。

## 13. Phase 3 Candidate Seeds

| ID | 候选方向 | 来源 | candidate_strength | Phase 3 treatment | 项目证据 | 说明 |
| --- | --- | --- | --- | --- | --- | --- |
| FE-SEED-001 | Evidence/non-claim guard consolidation | REUSE-001, REUSE-002 | strong | support_task | capability matrix、skeleton guard、eval non-claims | Phase 3 的第一道门禁 |
| FE-SEED-002 | API/frontend envelope contract drift guard | REUSE-002 | strong | FE_candidate | `envelope.py`, `envelope.ts`, route snapshot | 校验 source/confidence/evidence/next_actions 字段同步 |
| FE-SEED-003 | Workbench action state model extraction | REUSE-005, REUSE-006 | strong | FE_candidate | `InterviewPage.tsx`, `InterviewPage.test.ts` | 把 send/regenerate/complete/next action 收敛为可测试 view model |
| FE-SEED-004 | Polish feedback evidence and correction loop | REUSE-007 | medium | FE_candidate | feedback validation/service/tests | 捕获 correction/warnings，不做 automatic calibration claim |
| FE-SEED-005 | Provider redaction and evidence lane golden checks | REUSE-001, REUSE-002 | strong | FE_candidate | provider boundary、feedback validation、eval scripts | 增强 raw prompt/provider payload 禁止泄漏证据 |
| FE-SEED-006 | Eval report non-claim rendering guard | REUSE-001 | strong | support_task | `run_eval_gate.py`, `run_l5_eval_suite.py` | 确保 deterministic/replay 报告持续渲染 non_claims |
| FE-SEED-007 | Developer command matrix and lazy reading packet | REUSE-004, REUSE-016 | medium | support_task | doc governor CLI、package scripts | 把命令入口做成可审计矩阵 |
| FE-SEED-008 | Transcript quality gate discovery | REUSE-011 | weak | research | project_evidence_missing | 先研究输入、隐私、fixture；不得 FE_candidate |
| FE-SEED-009 | Storybank/asset lifecycle discovery | REUSE-012 | weak | deferred | project_evidence_missing | 先决定是否映射到 Assets 或新 model |
| FE-SEED-010 | Outcome drift calibration discovery | REUSE-013 | weak | research | project_evidence_missing | 需要真实 outcome log 和人审标签 |
| FE-SEED-011 | Existing-surface consistency guard | REUSE-008 | medium | FE_candidate | Resume/Job/Assets/Polish partial evidence | 只覆盖已有 surfaces |
| FE-SEED-012 | Bounded challenge protocol policy | REUSE-014 | blocked | reject | unsupported_or_unknown for product UX | 拒绝无边界复制；可另行研究 opt-in policy |

## 14. Validation and Acceptance Strategy

Phase 3 接受策略必须先验证证据等级，再验证功能价值。

| 层 | 策略 | 必须通过 |
| --- | --- | --- |
| scope gate | 候选项只能来自本 02b 的 REUSE/ADB/FE-SEED | Phase 3 不直接消费 01/02 |
| evidence gate | 每个候选必须声明 `executable_evidence`、`design-only`、`schema_like_design`、`project_evidence_missing` 或 `unsupported_or_unknown` | `project_evidence_missing` 不能进入 FE_candidate |
| contract gate | API/frontend 字段需有 Pydantic + TS 对照或生成式校验 | source/confidence/evidence fields 不漂移 |
| non-claim gate | fake/replay/deterministic/default-off 只能证明 regression/contract | 不得输出 live-provider quality claim |
| UX gate | workbench action changes 必须有 TS/static tests | 不把 routing 改成不可测 UI 条件堆叠 |
| provider safety gate | provider payload/raw prompt/raw completion/API key 禁止泄漏 | redaction tests 或 static checks |
| docs gate | 若新增任务，必须进 `docs/03-delivery/BACKLOG.md` | 不新增 parallel roadmap |

本文没有运行 install/build/tests/migrations/Docker，后续 Phase 3 若进入实现窗口，应按具体 FE-SEED 选择 focused pytest、web typecheck、`git diff --check` 和静态 rg gate。

## 15. Recommended Phase 3 Inputs

Phase 3 推荐输入顺序：

1. 本文件 `docs/feature-enhancement/02b_reuse_synthesis.md`。
2. `docs/00-governance/DOCS_INDEX.md` and `AGENTS.md`，确认文档治理和写入边界。
3. `docs/03-delivery/BACKLOG.md` and `docs/03-delivery/DELIVERY_PLAN.md`，确认候选是否能进入正式任务。
4. Phase 1/Phase 2 仅作为 supporting evidence，不直接生成任务。
5. 参考 clone 固定 HEAD `634a8dd8689e0420c21e5f0c8ae3cfa9e1a7ab7e`，只按 design-only/schema_like_design 读取。
6. 项目侧最小证据包：API/web envelope、feedback validation、capability matrix、skeleton guard、eval scripts、runtime flag resolver、provider boundary、InterviewPage/tests、doc governor CLI。

Phase 3 可以以 `partial` 状态启动：可以从 FE-SEED-001 到 FE-SEED-007/011 选择强或中等强度候选，但 transcript/storybank/outcome/challenge 相关项必须保持 research/deferred/reject。

## 16. Open Questions

1. Phase 3 是先做 contract/non-claim guard，还是先做 workbench action state model？
2. `source_availability`、`confidence_level`、`evidence_refs` 是否需要由 Pydantic schema 生成 TS type，而不是手写同步？
3. Polish feedback correction loop 的最小用户动作是什么：标记反馈不准、补充事实、还是提交人工 correction note？
4. Storybank 是否应映射到现有 Assets，还是另建 Story/Experience model？当前 `project_evidence_missing`。
5. Transcript ingestion 是否属于当前产品边界？如果是，隐私、存储、质量 gate 谁负责？
6. Outcome drift 是否有合法且稳定的 outcome 数据来源？没有时只能 research。
7. Bounded challenge protocol 是否需要产品 opt-in 和安全 copy？没有时保持 reject。
8. Developer command matrix 是进入 doc governor，还是进入独立 docs governance artifact？

## 17. Evidence Index

| 证据 | 分类 | 支持内容 |
| --- | --- | --- |
| `/tmp/interview-coach-skill-phase2-20260611/SKILL.md` | design-only | command registry、session state、lazy file routing、rubric entry |
| `/tmp/interview-coach-skill-phase2-20260611/README.md` | design-only | command lifecycle、storybank、progression、outcome calibration summary |
| `/tmp/interview-coach-skill-phase2-20260611/VERSIONS.md` | release_note_claim | v1-v3 evolution and planned v4/v5 |
| `/tmp/interview-coach-skill-phase2-20260611/releases/v2.md`, `releases/v3.md` | release_note_claim | capability expansion claims only |
| `/tmp/interview-coach-skill-phase2-20260611/references/coaching-state-schema.md` | schema_like_design | `coaching_state.md` shape |
| `/tmp/interview-coach-skill-phase2-20260611/references/state-update-triggers.md` | design-only | command-to-state update rules |
| `/tmp/interview-coach-skill-phase2-20260611/references/archival-rules.md` | design-only | archive thresholds |
| `/tmp/interview-coach-skill-phase2-20260611/references/evidence-sourcing.md` | design-only | source grounding and confidence language |
| `/tmp/interview-coach-skill-phase2-20260611/references/mode-detection.md` | design-only | intent priority and routing |
| `/tmp/interview-coach-skill-phase2-20260611/references/rubrics-detailed.md` | design-only | five-dimensional scoring model |
| `/tmp/interview-coach-skill-phase2-20260611/references/calibration-engine.md` | design-only | outcome drift and correction loop idea |
| `/tmp/interview-coach-skill-phase2-20260611/references/transcript-formats.md`, `transcript-processing.md` | design-only | transcript quality gate candidate |
| `/tmp/interview-coach-skill-phase2-20260611/references/storybank-guide.md`, `story-mapping-engine.md` | design-only | story lifecycle and mapping |
| `/tmp/interview-coach-skill-phase2-20260611/references/commands/*.md` | design-only | command-specific workflow patterns |
| `/tmp/interview-coach-skill-phase2-20260611/references/examples.md` | example_calibration | examples, not tests |
| `docs/feature-enhancement/01_project_architecture_assessment.md` | project_assessment | current project facts and candidate directions |
| `docs/feature-enhancement/02_reference_skill_capability_study.md` | reference_capability_study | reference inventory and absence of executable evidence |
| `docs/03-delivery/refactor/CAPABILITY_PRESERVATION_MATRIX.md` | executable_evidence | status vocabulary and partial/skeleton/default-off non-claims |
| `tests/api/test_skeleton_guard.py` | executable_evidence | guardrails for skeleton/partial/non-claim text |
| `apps/api/app/schemas/envelope.py` | executable_evidence | source/confidence/evidence envelope fields |
| `apps/web/src/shared/api/envelope.ts` | executable_evidence | frontend envelope mirrors |
| `apps/api/app/application/polish/feedback_validation.py` | executable_evidence | feedback schema, warnings, unsafe marker rejection |
| `tests/api/test_polish_feedback_validation.py`, `tests/api/test_polish_feedback_generation_service.py` | executable_evidence | feedback validation and fake-provider non-success tests |
| `apps/api/app/application/llm/provider_boundary.py` | executable_evidence | provider request validation and sensitive value redaction |
| `apps/api/app/application/ai_runtime/runtime_flags.py` | executable_evidence | default-off runtime flag resolver |
| `scripts/evals/run_eval_gate.py`, `scripts/evals/run_l5_eval_suite.py` | executable_evidence | deterministic/replay reports with non_claims and provider_evidence_type |
| `.github/workflows/eval-gate.yml` | executable_evidence | replay/deterministic CI gate commands |
| `apps/web/src/pages/interview/InterviewPage.tsx`, `apps/web/src/pages/interview/InterviewPage.test.ts` | executable_evidence | workbench question/answer/feedback/action/progress tree contracts |
| `tests/web/test_interview_actions.py` | executable_evidence | workbench action static guard |
| `tools/doc_governor/cli.py` | executable_evidence | doc governor command registry and packet commands |
| `package.json`, `apps/web/package.json` | executable_evidence | developer command matrix and web typecheck behavior |
