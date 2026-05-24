---
title: PRESSURE_MODE_SPEC
type: design
status: draft-f5-pressure-mode-spec
owner: 后端架构 / AI 架构 / 产品设计
source_task: AIFI-BE-004
permalink: ai-for-interviewer/docs/02-design/pressure-mode-spec
---

# PRESSURE_MODE_SPEC

## 1. Purpose and governance boundary

本文承接 `AIFI-BE-004`，冻结 Pressure Mode 的 mode-level spec。它把 `P-PRESSURE-001` 至 `P-PRESSURE-009` 的 Prompt Contract 连接到 session lifecycle、turn model、API、data、persistence、runtime graph、UI state 和测试计划。

本文只做文档设计，不修改 `apps/**`、`tests/**`、依赖、migration 或 CI。本文不替代 `API_SPEC.md`、`DATA_MODEL.md`、`PERSISTENCE_MODEL.md`、`PROMPT_SPEC.md`、`SECURITY_PRIVACY.md`、`UX_SPEC.md` 或 `UI_DESIGN_SYSTEM.md`；当这些 active docs 已有字段或边界时，本文只给 Pressure mode 的组合规则和实现前置条件。

## 2. Current implementation state

| Area | Current implementation | Conclusion |
|---|---|---|
| pressure use case placeholder | `PressureUseCases.bootstrap()` 只返回 `ApplicationResult(value="pressure_skeleton")` | 不能承载 session lifecycle、turn loop、answer assessment 或 report handoff |
| pressure router placeholder | `apps/api/app/api/v1/pressure.py` 只有 `APIRouter(prefix="/pressure-sessions", tags=["pressure"])`，没有 endpoint handler | `API_SPEC.md` 已有 contract，但代码未实现 |
| pressure schema placeholder | `PressureSessionResponse` 只有 `session_id` / `status` | 不能表达 turn、pace、score、report input、low confidence 或 candidate refs |
| pressure repository placeholder | `PressureRepository` Protocol 只有 `get_ref(session_id)`，未见具体 repository | 不能支持 owner-scoped session read、turn persistence、pause/resume 或 report handoff |
| pressure command/query placeholder | `CreatePressureQuestionTaskCommand` / `GetPressureSessionQuery` 只有 `session_id` | 不能表达 create/start/answer/follow-up/end 所需输入 |
| prompt contracts exist but no runtime implementation | `PRESSURE_CONTRACTS.md` 已有 `P-PRESSURE-001..009` Draft；`PROMPT_ASSET_SPEC.md` 登记 target pressure prompt assets | Prompt Contract 不等于 runtime graph、prompt builder、validator、API 或 persistence |

## 3. Non-goals

- 不实现 Pressure API、use case、repository、schema、graph、prompt builder、validator 或测试。
- 不新增 endpoint handler、ORM、DDL、migration、依赖、CI 或真实 provider 调用。
- 不把 Pressure graph 放入 PR2。
- 不把 checkpoint 当业务事实源。
- 不保存 raw prompt、raw completion、provider payload、system prompt、hidden scoring rules 或未脱敏日志正文。
- 不把 AI 输出静默升级为正式 `Weakness`、正式 `Asset`、正式 `TrainingRecommendation` 或 `TrainingTask`。
- 不提供精确通过概率、录取概率、offer 概率、必过 / 必挂预测。
- 不让 Pressure 继承 Polish 的同题无限打磨动作语义。

## 4. Pressure vs Polish boundary

| Boundary | Polish Mode | Pressure Mode |
|---|---|---|
| Primary goal | 围绕主题 / 次主题做同题多轮打磨、诊断、参考回答和考点扩展 | 模拟真实面试节奏，推进连续问答、追问、节奏控制、结束判断和报告输入 |
| Turn shape | 同一道题可以多轮回答和改进 | 一轮包含 question -> answer -> assessment -> follow-up / continue / end |
| Default action | 可继续打磨当前题、重新回答、看参考答案 | 不默认提供同题无限改写；主动作是回答、追问、下一题、暂停、结束并生成报告 |
| AI output | feedback、score、loss point、reference answer、asset / weakness candidate | opening、first question、answer quality、follow-up strategy/question、pace、end condition、session score、report input package |
| Formal write | candidate / suggestion 需确认后才能 formalize | 同样只允许 candidate / suggestion refs，正式写入必须走确认链路 |

## 5. Session lifecycle

| Step | Trigger | Required input | Output | Persistence / status | User visible state |
|---|---|---|---|---|---|
| create | `POST /api/v1/pressure-sessions` | owner-scoped resume/job/binding/source refs | `InterviewSession` + `PressureSessionDetail` | `created` / `active` 初始状态；initial `SessionSummary` | 会话已创建，可开始 |
| start | 用户进入工作台或确认开始 | session ref、source availability、opening strategy readiness | start marker / current pace state | session `active`，记录 audit / trace | 当前问题准备中 |
| ask first question | `P-PRESSURE-001/002` | opening strategy、job/resume versions、forbidden refs | first question candidate | `Question` candidate、turn initialized | 首题生成中 / 首题可回答 |
| answer | `POST /api/v1/pressure-sessions/{session_id}/answers` | question ref、answer text、idempotency key | `Answer` | 同步保存；不调用 LLM | 回答已保存 |
| assess answer | `P-PRESSURE-003` via feedback task | answer ref、question ref、session summary | answer quality result | `Feedback` / quality result refs、low confidence refs | 评估中 / 评估可见 |
| follow-up strategy | `P-PRESSURE-004` | quality refs、recent turns、pace state | strategy result | strategy ref、session summary update | 系统决定追问 / 切换 / 继续 |
| follow-up question | `P-PRESSURE-005` | strategy、anti-repeat refs、target gaps | follow-up question | next `Question` candidate / new turn init | 追问生成中 / 追问可回答 |
| continue | user or graph route | pace / coverage / end check | next turn route | turn refs update | 下一题或继续追问 |
| pause | user action or system failure | stable snapshot refs | paused state | `paused` + `source_session_snapshot_ref` | 已暂停，可恢复 |
| resume | user action | pause snapshot、covered turns、owner check | resumed route | `active` or `resume_failed` | 恢复成功 / 恢复失败 |
| end | user action or end condition | end condition result、turn refs | end state | `completed` / `failed` / `cancelled` | 已结束，可生成报告 |
| report handoff | user requests report or graph route | `P-PRESSURE-008/009` refs | report input package ref | report input package / score refs | 报告生成中 |
| review handoff | report/review entry | report/session/turn refs | review source refs | mock review task input refs | 可发起模拟面试复盘 |

## 6. Pressure turn model

`PressureTurn` 是 mode-level 逻辑模型，不要求立即新增 ORM。实现可用 `Question`、`Answer`、`Feedback`、`SessionSummary`、`TraceRef`、`typed_reference_links` 或等价结构承载。

| Field group | Required semantics |
|---|---|
| identity | `pressure_turn_ref`、`pressure_session_ref`、`turn_index`、`owner_ref` |
| question | `question_ref`、`question_type=pressure_first/pressure_follow_up`、source refs、anti-repeat refs |
| answer | `answer_ref`、answer status、submitted_at、base question version ref |
| assessment | `answer_quality_ref`、quality level、missing points、risk signals、low confidence flags |
| strategy | follow-up strategy ref、target gap refs、pause / end hints |
| pace | pace state、pressure intensity hint、follow-up depth hint、fatigue / low confidence impact |
| end | end condition ref、continue / pause / end route、report readiness |
| trace | validation result refs、evidence refs、trace refs、audit refs |

## 7. Opening strategy

Opening Strategy 由 `P-PRESSURE-001` 生成。它必须基于当前 owner 的岗位、简历、可用 Job Match / Polish 上游、session goal 和 forbidden repeat refs。输出只作为会话内策略，不生成整场题库，不写正式 Weakness / Asset / TrainingRecommendation。

## 8. First question

First Question 由 `P-PRESSURE-002` 生成。它必须创建 `question_type=pressure_first` 或等价题目候选，绑定 opening strategy、job/resume versions、expected answer signals、anti-repeat refs 和 evidence refs。首题可以直接进入答题流程，但不能泄露参考答案，不能复用 Polish same-question 打磨题。

## 9. Answer save

Pressure answer save 是同步 Core action，不调用 LLM。它必须校验 session / question owner、question belongs to pressure session、answer length、idempotency key 和 stale question version；成功后只写 `Answer`、api trace 和 audit event。后续 answer quality assessment 另走 async feedback / graph task。

## 10. Answer quality assessment

Answer Quality Assessment 由 `P-PRESSURE-003` 生成。它只评估当前问题和当前回答的充分性、相关性、深度、技术准确性、结构、沟通、risk signals、missing points 和 follow-up input。它不能虚构用户未表达经历，不能把岗位不匹配直接包装成稳定能力缺陷，不能静默创建正式 Weakness。

## 11. Follow-up strategy

Follow-up Strategy 由 `P-PRESSURE-004` 生成。它只选择追问策略、澄清策略、换方向、暂停或结束提示，不生成具体追问题目。策略必须绑定 current question、answer quality result、opening strategy、session summary、forbidden repeat refs 和 evidence refs。

## 12. Follow-up question

Follow-up Question 由 `P-PRESSURE-005` 生成。它必须消费 `P-PRESSURE-004` 的 strategy，不得直接复用 strategy 文案，不得重复已问问题或 Polish same-question 打磨题。生成后初始化下一轮 `PressureTurn`。

## 13. Pressure intensity and pace

Pressure intensity 是 mode state / hint，不是隐藏评分、不是真实心理画像，也不是单次 LLM 自由变量。`P-PRESSURE-006` 可生成 pace state、recommended pace action、pressure intensity adjustment、follow-up depth adjustment、pause / resume recommendation 和 low confidence impact。用户暂停、退出或切换模式的选择必须优先。

## 14. End condition

`P-PRESSURE-007` 只生成结束建议，不自动结束会话、不生成报告正文、不生成正式回流对象。结束判断必须基于 coverage、asked / answered question refs、answer quality trend、pace state、user requested end signal 和 low confidence state。`ready_for_session_score` 和 `ready_for_report_input_assembly` 只是准备状态。

## 15. Session score

`P-PRESSURE-008` 生成 pressure session scoring candidate / formal handoff。正式 `ScoreResult` 只能使用 `score_type=pressure_session`、`score_scale=0_100_product_scale`、`ScoreRuleVersion`、`score_version`、`rubric_version`、dimension scores、evidence refs、trace refs、confidence 和 validation status。它不得复用 Job Match 或 Polish score 作为整场压力面分，不得输出精确通过概率、必过或必挂。

## 16. Report handoff

`P-PRESSURE-009` 只组装 report input package，不生成报告正文、报告结论或通过倾向文案。Report handoff 必须包含 session summary、question / answer refs、answer quality refs、follow-up chain refs、pace refs、end condition ref、session score ref、evidence bundle refs、low confidence bundle、risk signal refs、candidate refs 和 excluded sources。

## 17. Review handoff

Pressure output 可作为 `mock_review_generation_graph` / Review contracts 的输入。Review handoff 只传 session/report/turn/score/evidence refs 和安全摘要，不传 raw prompt、raw completion、provider payload、checkpoint payload 或不可展示原文。Review 产生的 Weakness / Asset / Training 只能是 candidate / suggestion refs。

## 18. Weakness / asset / training candidate handoff

Pressure 可以通过 feedback、session score、report input 或 review handoff 产生 `weakness_candidate_refs`、`asset_candidate_refs` 或 `training_suggestion_refs`。这些 refs 必须 owner scoped、evidence-bound、low-confidence-aware，并进入用户确认链路；用户确认前不得创建正式 Weakness、Asset、AssetVersion、TrainingRecommendation 或 TrainingTask。

## 19. API design

### 19.1 Current API contract mapping

| Required capability | Current API_SPEC reference | Mode-level rule |
|---|---|---|
| create pressure session | `API-PRESSURE-001` | 创建 `InterviewSession` + `PressureSessionDetail`，不调用 LLM |
| get pressure session | `API-PRESSURE-002` | 返回当前 session status、current question、progress、low confidence |
| create question task | `API-PRESSURE-003` | 可触发 opening/first question 或 follow-up question task；必须返回 async task status |
| create answer | `API-PRESSURE-004` | 同步保存回答，不调用 LLM |
| create feedback task | `API-PRESSURE-005` | 触发 assessment、pace、end condition、session score、report input package 中的授权子集 |
| progress tree | `API-PROGRESS-001` | 展示压力面进展树、current position 和恢复状态 |
| report generation | `API-REPORT-001` and related report read / copy APIs | 只能消费 `P-PRESSURE-009` report input package，不允许 Pressure graph 生成报告正文 |
| mock review generation | review APIs | 只消费已授权 Pressure report/session refs，不自动 formalize candidates |

### 19.2 Endpoints required before graph implementation

在 `pressure_interview_graph` 实现前，API 层必须能表达以下动作；可通过现有 endpoint 明确扩展 request schema，也可由 `API_SPEC.md` 另行登记 dedicated endpoint，但不得由代码自行发明未登记 route：

| Action | Required before graph | Minimum API contract requirement |
|---|---|---|
| `start_pressure_session` | yes | create 后进入 active / running 的显式状态转换或 create response 中可测试的 start state |
| `pause_pressure_session` | yes | 保存最小恢复快照，返回 paused / pause failed |
| `resume_pressure_session` | yes | 校验 snapshot、covered turns、owner 和 source availability，返回 active / resume failed |
| `end_pressure_session` | yes | 记录 completed / cancelled / failed，保留用户选择路径 |
| `generate_pressure_report` | yes | 通过 report endpoint 消费 report input package ref，不由 Pressure endpoint 返回报告正文 |
| `generate_mock_review_from_pressure` | yes for PR8 review handoff | 通过 review endpoint 消费 pressure session/report refs |

## 20. Data model

| Logical object | Required Pressure fields / refs | Target active doc |
|---|---|---|
| `InterviewSession` | owner, actor, mode=`pressure`, status, resume/job/binding refs, current question, progress position | `DATA_MODEL.md` |
| `PressureSessionDetail` | session ref, current question ref, turn refs, follow-up chain refs, pace state, interruption state, end condition state, report generation state | `DATA_MODEL.md` |
| `PressureTurn` | logical turn ref, question ref, answer ref, quality ref, strategy ref, pace ref, end check ref, trace/evidence refs | this spec + `DATA_MODEL.md` handoff |
| `Question` | `pressure_first` / `pressure_follow_up`, generation state, source refs, anti-repeat refs | `DATA_MODEL.md` / `API_SPEC.md` |
| `Answer` | question ref, answer text, answer round, submitted state, version ref | `DATA_MODEL.md` |
| `Feedback` / quality result | answer quality, next action, low confidence, score input refs | `DATA_MODEL.md` |
| `ScoreResult` | `score_type=pressure_session`, score rule version, dimension scores, evidence, validation | `SCORING_SPEC.md` / `DATA_MODEL.md` |
| `SessionSummary` | covered turn refs, asked question refs, forbidden repeat refs, open / closed threads, candidate refs, low confidence | `DATA_MODEL.md` |
| `PressureReportInputPackage` | report input refs, score refs, risk refs, candidate refs, source availability | this spec + `PERSISTENCE_MODEL.md` handoff |

## 21. Persistence model

| Persistence concern | Required rule |
|---|---|
| physical tables | Existing `interview_sessions`, `pressure_session_details`, `questions`, `answers`, `feedback`, `score_results`, `ai_tasks`, `ai_task_results`, `evidence_refs`, `trace_refs` and `typed_reference_links` or equivalent are enough for planning; no DDL in this task |
| turn refs | If no dedicated `pressure_turns` table is added, turn identity must be reconstructable from question / answer / feedback / typed refs and `SessionSummary.covered_turn_refs` |
| pace/end/report refs | Pace, end condition and report input package may be persisted as typed refs / task results / summary snapshots until a later authorized schema adds concrete tables |
| checkpoint | Checkpoint may hold resume/replay state only; business reads must use persisted refs and summaries, not checkpoint payload |
| rollback | in-flight pressure tasks must be cancellable / fail-closed; late writes cannot create formal objects |
| raw-off | Raw prompt, completion and provider payload are not persisted in normal tables, checkpoint, trace-visible body, API response or copy content |

## 22. Prompt design

Pressure runtime prompt assets are target assets in `PROMPT_ASSET_SPEC.md`; this spec closes mode-level sequencing but does not implement builders or validators.

| Contract | Runtime prompt bundle | Required prompt asset before graph implementation |
|---|---|---|
| `P-PRESSURE-001` | `pressure_opening_strategy` | `prompt_asset.pressure.opening.001` |
| `P-PRESSURE-002` | `pressure_first_question_generation` | `prompt_asset.pressure.first_question.001` |
| `P-PRESSURE-003` | `pressure_answer_quality_assessment` | `prompt_asset.pressure.answer_quality.001` |
| `P-PRESSURE-004` | `pressure_follow_up_strategy` | pressure follow-up strategy asset |
| `P-PRESSURE-005` | `pressure_follow_up_question_generation` | pressure follow-up question asset |
| `P-PRESSURE-006` | `pressure_pace_control` | pressure pace asset |
| `P-PRESSURE-007` | `pressure_end_condition_check` | pressure end condition asset |
| `P-PRESSURE-008` | `pressure_session_score` | pressure session score asset |
| `P-PRESSURE-009` | `pressure_report_input_assembly` | pressure report input asset |

All assets need schema id, prompt version, redaction boundary, golden / regression / negative fixtures, no-same-question-loop fixture, source unavailable fixture, candidate-only fixture, no exact probability fixture and raw-off fixture before runtime graph implementation.

## 23. Graph design

### 23.1 Required graph decision

| Decision | Verdict |
|---|---|
| Whether `pressure_interview_graph` may be implemented before this spec is accepted | No. This spec must be accepted first. |
| Whether Pressure belongs in PR8 or needs a separate PR | Default target is PR8 Report / Review / Pressure / candidate closure. A separate Pressure PR is allowed only if main Agent explicitly creates a scoped AIFI task / PR scope after AIFI-BE-005 or accepted risk. |
| Whether Pressure enters PR2 | No. PR2 remains AI Runtime data / repository foundation only after re-authorization; no business graph and no Pressure graph. |
| Which endpoints are required before graph implementation | See §19.2. Start/pause/resume/end/report/review handoff must be expressible in active API contract before graph code. |
| Which pressure prompt assets are required before graph implementation | See §22. All `P-PRESSURE-001..009` runtime bundles / assets and validators must be mapped before graph code. |

### 23.2 Graph state and nodes

| Graph node | Input | Output | Side effect | Failure route |
|---|---|---|---|---|
| `load_pressure_context` | owner/session/job/resume refs | compact context refs | read-only | `source_unavailable` |
| `generate_opening` | context | opening strategy ref | LLM via runtime transport | `generation_failed` / deterministic safe opening |
| `generate_first_question` | opening + anti-repeat refs | question candidate | write question / task result after validation | low confidence question |
| `wait_for_answer_interrupt` | question ref | interrupt / waiting state | write interrupt ref | timed out / cancelled |
| `save_answer_handoff` | answer ref from API | answer state patch | no LLM | validation failed |
| `analyze_answer_quality` | answer/question refs | quality refs | write feedback / validation refs | low confidence |
| `select_follow_up_strategy` | quality + pace | strategy ref | none or task result | partial |
| `generate_follow_up_question` | strategy | follow-up question | write question candidate | generation failed |
| `control_pace` | turn refs | pace state | update session summary / refs | partial |
| `check_end_condition` | turn refs + pace | continue / pause / end route | update end condition refs | partial |
| `generate_session_score` | end condition + turns | score ref | validated `ScoreResult` only after gate | low confidence / validation failed |
| `assemble_report_input_package` | session/turn/score refs | report input package ref | persist package refs | partial / source unavailable |

## 24. Frontend UI states

Pressure UI uses the four-zone workbench from `UX_SPEC.md`: current interview status bar, progress tree, chat window and input area. It must not inherit Polish actions.

| UI state | Required display / action |
|---|---|
| default | current question, pace / intensity hint, progress, input area |
| question generating | skeleton / running state; no duplicate send |
| answer saving | send disabled; answer save status visible |
| assessment running | quality / follow-up generation status visible |
| follow-up available | follow-up question shown as system message |
| low confidence | low confidence reason and next actions visible |
| paused | resume / end actions visible |
| resume failed | retry / end / return actions visible |
| end recommended | continue / pause / end and generate report options visible |
| report generating | report task status visible |
| source unavailable | choose available source / return / manual review |
| candidate handoff | candidate refs visible as pending confirmation, not formal objects |

## 25. Test plan

| Test area | Required assertions |
|---|---|
| API contract | owner scope, idempotency, source unavailable, async task status, low confidence visible, pause/resume/end state |
| answer save | answer save does not call LLM; saves owner-scoped answer and audit |
| no same-question loop | first / follow-up generation rejects repeated Polish or Pressure question refs |
| prompt validation | each `P-PRESSURE-*` output has contract id, validation result, evidence refs, trace refs and low confidence fields |
| pace/end | pace does not ignore pause/exit; end condition does not auto-end without user path |
| score | no exact probability; score uses `pressure_session`, `ScoreRuleVersion`, evidence and validation |
| report handoff | `P-PRESSURE-009` package is not report body |
| candidate-only | Weakness / Asset / Training outputs remain candidate / suggestion until confirmation |
| raw-off | no raw prompt, completion, provider payload, system prompt or hidden scoring rule in API/log/trace/checkpoint/copy content |
| UI | Pressure does not show Polish default actions: continue polishing current question, rewrite current answer, start polish as default action |

## 26. Validation plan

Docs-only validation for AIFI-BE-004 must run:

```bash
git status --short --untracked-files=all
git diff --stat
git diff --check
.venv/bin/python -m tools.doc_governor.cli doc-quality-gate --repo-root .
```

Implementation PR validation must additionally add pytest / frontend checks under an explicitly authorized PR scope; this task does not create those tests.

## 27. Migration / rollout

- Pressure runtime stays default-off until a later authorized PR maps API, repository, prompt assets, validators, graph nodes and tests.
- PR2 remains blocked from business graph work and cannot create `pressure_interview_graph`.
- PR8 is the default home for Pressure graph + Report / Review / candidate closure unless a separate Pressure PR is explicitly authorized.
- Rollout must preserve legacy placeholder compatibility until real endpoints and schemas replace placeholders.
- Rollback must cancel or fail-close in-flight pressure tasks and must not late-write formal objects.

## 28. Definition of Done

| Requirement | Done evidence |
|---|---|
| Purpose and governance boundary | §1 defines scope and active doc relationship |
| Current implementation state | §2 lists use case, router, schema, repository, command/query and prompt/runtime gap |
| Non-goals | §3 |
| Pressure vs Polish boundary | §4 |
| Session lifecycle | §5 covers create/start/first question/answer/assessment/follow-up/continue/pause/resume/end/report/review |
| Pressure turn model | §6 |
| Opening / first question / answer / assessment / follow-up / pace / end / score / handoff | §7-§18 |
| API / data / persistence / prompt / graph / UI / tests / validation / rollout | §19-§27 |
| Required tables | §19.1, §20, §22, §23.2, §24, §25 plus capability/state/contract tables below |
| Required graph decision | §23.1 |
| AIFI-BE-004 closure | `BACKLOG.md` status can be set to `ACCEPTED` after validation passes |
| PR2 blocked statement | `BACKLOG.md` / PR sequence must still state PR2 is blocked by remaining non-AIFI-BE-004 gates |

### Capability matrix

| Capability | Current Code | Required Spec | Required Runtime | Target Document | Target PR |
|---|---|---|---|---|---|
| Pressure session lifecycle | placeholder use case/router | §5 | session use cases + API + repository | this spec / `API_SPEC.md` | PR8 or separate Pressure PR |
| Pressure turn loop | not implemented | §6 | turn refs, task orchestration, anti-repeat | this spec / `DATA_MODEL.md` | PR8 |
| Opening / first question | prompt contracts only | §7-§8 | prompt assets, validators, question persistence | `PRESSURE_CONTRACTS.md` / `PROMPT_ASSET_SPEC.md` | PR8 |
| Answer save | not implemented | §9 | sync answer use case, no LLM | `API_SPEC.md` / this spec | PR8 |
| Answer quality / follow-up | prompt contracts only | §10-§12 | feedback task / graph nodes | this spec | PR8 |
| Pace / end | prompt contracts only | §13-§14 | pace/end state + UI | this spec / `UX_SPEC.md` | PR8 |
| Session score | prompt contract only | §15 | `ScoreResult` gate | `SCORING_SPEC.md` | PR8 |
| Report / review handoff | graph plan only | §16-§17 | report input package + review refs | this spec / `08_BACKEND_GRAPH_PLANS_REPORT_REVIEW.md` | PR8 |
| Candidate handoff | active data/API rules | §18 | confirmation chain | `DATA_MODEL.md` / `API_SPEC.md` | PR8 |

### Pressure state table

| Pressure State | Trigger | Input | Output | Persistence | User Visible State | Tests |
|---|---|---|---|---|---|---|
| `created` | create session | resume/job refs | session refs | `InterviewSession`, `PressureSessionDetail` | created | create success/idempotency |
| `opening_generating` | start | session refs | opening ref | task result / trace | opening running | provider failure/low confidence |
| `question_available` | first/follow-up generated | opening/strategy | question ref | `Question` | answer enabled | no repeat |
| `answer_submitted` | user send | answer text | answer ref | `Answer`, audit | saved | answer save no LLM |
| `assessment_running` | feedback task | answer ref | quality ref | `Feedback` / validation | assessing | quality low confidence |
| `follow_up_available` | strategy + question | quality ref | follow-up question | `Question` + turn refs | follow-up visible | no same-question loop |
| `paused` | user pause | stable refs | pause snapshot | session status + snapshot | paused | pause snapshot |
| `resume_failed` | resume invalid | snapshot refs | failure | audit / low confidence | retry/end | source unavailable |
| `end_recommended` | end check | coverage/pace | end recommendation | end condition ref | continue/pause/end | no auto end |
| `completed` | user end | end route | completed session | session status | report CTA | end/report handoff |
| `report_input_ready` | score + assembly | session score | package ref | report input package refs | report generating | package not report body |

### Pressure contract table

| Pressure Contract | Runtime Node | Prompt Asset | Validator | Persistence Target | Test |
|---|---|---|---|---|---|
| `P-PRESSURE-001` | `generate_opening` | `prompt_asset.pressure.opening.001` | opening schema + evidence validator | opening strategy ref / trace | opening low confidence |
| `P-PRESSURE-002` | `generate_first_question` | `prompt_asset.pressure.first_question.001` | question schema + anti-repeat validator | `Question` candidate | no repeat / no answer leak |
| `P-PRESSURE-003` | `analyze_answer_quality` | `prompt_asset.pressure.answer_quality.001` | quality schema + fact boundary validator | quality / feedback refs | no fabricated experience |
| `P-PRESSURE-004` | `select_follow_up_strategy` | pressure strategy asset | strategy schema validator | strategy ref | strategy no concrete question |
| `P-PRESSURE-005` | `generate_follow_up_question` | pressure follow-up asset | question + anti-repeat validator | follow-up question ref | no same-question loop |
| `P-PRESSURE-006` | `control_pace` | pressure pace asset | pace schema + safety validator | pace state ref | pause/exit honored |
| `P-PRESSURE-007` | `check_end_condition` | pressure end asset | end schema validator | end condition ref | no auto-end |
| `P-PRESSURE-008` | `generate_session_score` | pressure score asset | scoring + no probability validator | `ScoreResult` refs | score version/evidence/no probability |
| `P-PRESSURE-009` | `assemble_report_input_package` | pressure report input asset | package schema validator | report input package ref | package not report body |

## 29. Change log

| Date | Change | Impact |
|---|---|---|
| 2026-05-24 | 初始化 AIFI-BE-004 Pressure Mode mode-level spec | 冻结 Pressure session、turn、API/data/persistence/prompt/graph/UI/test 承接；Pressure graph 不进入 PR2；PR8 或独立授权 Pressure PR 才能实现 |
