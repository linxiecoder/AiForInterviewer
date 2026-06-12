---
title: interview-coach-skill 发现结论
type: temporary-discovery
status: complete
---

# interview-coach-skill 发现结论

## 1. 来源位置

- canonical repository: `https://github.com/noamseg/interview-coach-skill.git`
- 本地临时 checkout: `/tmp/interview-coach-skill`
- clone 后观察到的远端默认分支: `origin/main`
- 本地检出分支: `main`
- analyzed commit hash: `634a8dd8689e0420c21e5f0c8ae3cfa9e1a7ab7e`
- commit date: `2026-05-29`

## 2. 已检查文件

- `README.md`
- `LICENSE`
- `VERSIONS.md`
- `SKILL.md`
- `references/coaching-state-schema.md`
- `references/schema-migration.md`
- `references/state-update-triggers.md`
- `references/archival-rules.md`
- `references/rubrics-detailed.md`
- `references/evidence-sourcing.md`
- `references/calibration-engine.md`
- `references/storybank-guide.md`
- `references/story-mapping-engine.md`
- `references/transcript-formats.md`
- `references/transcript-processing.md`
- `references/cross-cutting.md`
- `references/mode-detection.md`
- `references/commands/analyze.md`
- `references/commands/feedback.md`
- `references/commands/practice.md`
- `references/commands/prep.md`
- `references/commands/progress.md`
- `references/commands/research.md`
- `references/commands/stories.md`

## 3. 事实发现

1. `SKILL.md` 是顶层运行入口。它定义了优先级层级：session state、triage、evidence enforcement、question sequencing、coaching voice 和 schema compliance 共同约束执行。它还通过 command registry 和 file-routing table，把显式命令路由到对应的 per-command reference files。

2. `references/mode-detection.md` 定义了 intent router。它先优先处理显式命令，其次处理 transcript input，再把用户意图类型映射到 feedback capture、debrief、company prep、story work、practice、progress、offer negotiation 和 written application support 等 workflow。它还定义了 multi-step intent sequences，不要求用户手动选择每一个 command。

3. `references/coaching-state-schema.md` 把 long-running session state 建模为结构化 Markdown 文件。该 schema 包含 profile data、resume analysis、storybank index and story details、score history、outcome log、interview intelligence、drill progression、active interview loops、active coaching strategy、calibration state、cross-surface artifacts、meta-check log、session log 和 coaching notes。

4. `references/schema-migration.md` 定义了 backward-compatible state migration rules。读取旧版 `coaching_state.md` 时，会静默补齐缺失 section 和较新字段，包括 newer storybank columns、calibration state、career-transition fields、interview intelligence 和 renamed score-history columns。

5. `references/state-update-triggers.md` 把 workflow outputs 映射到具体 state updates。例如 score-producing workflows 更新 Score History，transcript analysis 更新 Active Coaching Strategy 和 Interview Intelligence，debrief 更新 story usage 和 outcomes，feedback 路由 external comments 和 outcomes，progress 更新 calibration 和 archival summaries。

6. `references/rubrics-detailed.md` 将 five-dimension scoring rubric 扩展为 1-5 anchors、root-cause taxonomy、seniority calibration bands、aggregate interview-level assessment 和 trend interpretation。该 rubric 将观察到的弱分数连接到可能 root causes 和 targeted fixes，而不是把分数当作孤立标签。

7. `references/transcript-formats.md` 定义了分析前的 transcript format detection 和 normalization。它覆盖多种 transcript sources，标准化 speaker turns，保留 useful markers，检测 multi-speaker cases，并输出 speaker-label coverage、normalization confidence、artifact detection 等 quality signals。

8. `references/transcript-processing.md` 定义了分阶段 transcript pipeline：normalization、cleaning、quality gate、format-aware parsing、anti-pattern scan、multi-lens scoring、format-specific score extensions、合成为 interview delta，以及 state update。它区分 behavioral Q&A、panel exchanges、system-design or case phases、technical/behavioral mixes、case-study stages 和 presentation sections。

9. `references/commands/analyze.md` 将 transcript pipeline 作为 workflow 使用。它会请求 self-assessment，但要求先完成 independent scoring 再比较；它还单独检测 compensation-call transcripts，使用 priority stack 分诊 bottlenecks，更新 active coaching strategy，并写入 questions、scores、company patterns 等 interview intelligence。

10. `references/evidence-sourcing.md` 定义了 recommendations 的 grounding rules。它要求每条有意义的 recommendation 基于真实来源，要求 coach 直接说明 uncertainty，并在缺少必要数据时停止 unsupported guidance。

11. `references/commands/prep.md` 包含 company 和 interviewer grounding rules。它要求在应用 company-specific guidance 前先做 current company research，区分 verified sources、general public knowledge 和 unknowns，并要求 company-culture 或 interviewer claims 带 source attribution。

12. `references/storybank-guide.md` 将 storybank 定义为 index 和 full story-details store 的组合。它追踪 story ID、skill tags、impact、domain、stakes、earned secret、strength、usage count、last-used date 和 notes；同时包含 health checks、retirement criteria、enhancement prompts 和 rapid-retrieval drills。

13. `references/story-mapping-engine.md` 定义了 story-to-question mapping protocol。它使用 fit levels、conflict resolution、variety constraints、prior-round freshness checks、overuse checks、earned-secret-aware selection 和 secondary-skill utilization。prep、stories 和 progress workflows 会引用它。

14. `references/commands/stories.md` 将 storybank work 操作化。它区分 add、improve、gap analysis、retirement、retrieval drill 和 narrative-identity flows；要求持久化 full story details，而不是只保存 index row；并基于 target roles 和 active prep context 排序 gaps。

15. `references/commands/practice.md` 定义了 gated drill progression。它按 prerequisite difficulty 排序 drills，要求 warmup round，使用带 independent coach scoring 和 candidate self-assessment delta 的 per-round protocol，将 role-drill axes 映射回 core dimensions，并更新 drill progression 和 revisit queues。

16. `references/commands/progress.md` 定义了 progress review thresholds。它根据 available data 调整输出，以叙述方式解释 trends 而不是只展示表格，将 self-assessment 与 coach scores 比较，在 outcomes 足够时检查 real-outcome correlation，审查 calibration drift，并更新 active coaching strategy。

17. `references/calibration-engine.md` 集中处理 calibration。它定义 calibration metadata、scoring-drift detection、cross-dimension root-cause lifecycle、intelligence data 的 temporal decay、role-drill score mapping、learning from successes，以及当 scores 不能预测 outcomes 时对 unmeasured factors 的调查。

18. `references/commands/feedback.md` 将 between-session input 视为先 capture、不是先 analysis。它分类 recruiter/interviewer feedback、outcomes、coaching corrections、post-session memory 和 meta-feedback；与 coach scoring 矛盾的 external feedback 会成为 drift signal，而不是被直接忽略。

19. `references/archival-rules.md` 定义了 long-running coaching 的 state-size controls。它将较旧的 score history、session log、interview intelligence 和 JD analyses 压缩为 summaries，同时保留 recent rows 的细节。

20. `references/cross-cutting.md` 定义了跨 command 使用的 shared modules，包括 differentiation、gap handling、signal reading、psychological readiness、cultural/linguistic awareness、role-fit assessment、challenge protocol 和 cross-command dependencies。

21. `VERSIONS.md` 记录了该仓库自身的 version thesis。它表明 transcript support、multi-format analysis、story mapping、outcome calibration、company intelligence、full-lifecycle commands 和 schema hardening 是跨版本有意加入的，而不是偶然的 file sprawl。

22. `LICENSE` 是 MIT。这不覆盖当前 Round 1 约束：审计只记录 facts 和 patterns，不把 interview-coach source 复制进 AIForInterviewer。

## 4. 候选可复用能力模式

以下只是 capability patterns，不是 AIForInterviewer landing-point assumptions，也不是 implementation decisions。

1. source-backed command routing pattern：顶层入口把详细 workflows 委托给 command-specific references 和 shared cross-cutting modules。Evidence: `SKILL.md`, `references/mode-detection.md`, `references/commands/analyze.md`.

2. persistent coaching state pattern：一个 structured state model、migration rules、update triggers、archival thresholds 和 session-start/session-end behavior 共同保持 long-running coaching 连贯。Evidence: `references/coaching-state-schema.md`, `references/schema-migration.md`, `references/state-update-triggers.md`, `references/archival-rules.md`.

3. capture-versus-analysis separation pattern：轻量 feedback capture 先保留数据，避免过早重新分析；更深层 workflows 后续再消费这些数据。Evidence: `references/commands/feedback.md`, `references/commands/progress.md`, `references/calibration-engine.md`.

4. transcript ingestion pipeline pattern：检测 source format、normalize、assess quality、按 interview format parse、score、triage，并 persist intelligence。Evidence: `references/transcript-formats.md`, `references/transcript-processing.md`, `references/commands/analyze.md`.

5. evidence and confidence pattern：recommendations 与 company/interviewer claims 带 source grounding、uncertainty labels，或在缺少数据时明确停止。Evidence: `references/evidence-sourcing.md`, `references/commands/prep.md`, `references/commands/research.md`.

6. rubric-plus-root-cause pattern：scores 绑定 anchors、seniority calibration、root-cause taxonomy 和 targeted fixes。Evidence: `references/rubrics-detailed.md`, `references/commands/analyze.md`, `references/calibration-engine.md`.

7. storybank as reusable memory pattern：紧凑可搜索的 story index 连接 full story details、usage history、strength scoring、freshness 和 gap analysis。Evidence: `references/storybank-guide.md`, `references/story-mapping-engine.md`, `references/commands/stories.md`.

8. progress calibration pattern：score history 与 self-assessment、external feedback、real outcomes、drift signals 和 success patterns 比较。Evidence: `references/commands/progress.md`, `references/calibration-engine.md`, `references/commands/feedback.md`.

9. state-aware next-step pattern：workflow 结束时根据 current state 和 bottleneck data 选择单一 next action，而不是展示静态菜单。Evidence: `SKILL.md`, `references/commands/analyze.md`, `references/commands/progress.md`.

10. long-context hygiene pattern：通过 summarization thresholds 和 recent-detail retention 管理 state 增长。Evidence: `references/archival-rules.md`, `references/commands/progress.md`, `references/coaching-state-schema.md`.

## 5. 非复制建议

1. 不要把 interview-coach command list 或 command names 复制为 AIForInterviewer product workflow。Evidence: `SKILL.md`, `README.md`, `references/commands/analyze.md`, `references/commands/practice.md`, `references/commands/progress.md`, `references/commands/stories.md`.

2. 不要复制将 `SKILL.md` 重命名为 agent entry files 的 activation instructions。它们是 repository-specific installation instructions，不是 reusable product architecture。Evidence: `README.md`.

3. 不要把 source repository 的 directory layout 复制进 AIForInterviewer。该 layout 是为 agent prompt routing 优化的 skill-reference bundle，不是 AIForInterviewer module boundary 的证据。Evidence: `SKILL.md`, `references/commands/analyze.md`, `references/cross-cutting.md`.

4. 不要复制 prompt、workflow、output-schema、menu、greeting、recommendation 或 coaching voice wording。Round 1 只记录 structural patterns 和 facts。Evidence: `SKILL.md`, `references/commands/practice.md`, `references/commands/progress.md`, `references/commands/stories.md`.

5. 不要原样复制 flat-file `coaching_state.md` model。source 展示的是 continuity pattern，但 persistence shape 和 state ownership 需要单独的 AIForInterviewer landing-point audit。Evidence: `references/coaching-state-schema.md`, `references/state-update-triggers.md`, `references/schema-migration.md`.

6. 不要在未与 AIForInterviewer scoring semantics 后续比较的情况下，把 exact scoring dimension names、anchors 或 hire-signal labels 复制进 AIForInterviewer。Evidence: `references/rubrics-detailed.md`, `references/commands/analyze.md`, `references/commands/progress.md`.

7. 不要复制 company-research 或 interviewer-intelligence claims 或 examples。任何 AIForInterviewer grounding model 都必须来自它自己的 data contracts 和 product safety requirements。Evidence: `references/evidence-sourcing.md`, `references/commands/prep.md`, `references/commands/research.md`.

8. 不要复制 story prompts、example stories 或 coaching prose。只有 indexed experiences、usage metadata 和 gap analysis 的抽象模型适合后续评估。Evidence: `references/storybank-guide.md`, `references/commands/stories.md`, `references/story-mapping-engine.md`.

## 6. 未知项和开放问题

- Round 2 只读审计中，哪些 AIForInterviewer code 和 active docs 是正确的 landing-point candidates？
- 哪些 AIForInterviewer state、scoring、transcript、evidence 和 progress semantics 已经存在，哪些只存在于 design docs？
- 哪些 interview-coach capabilities 与 AIForInterviewer product requirements 重叠，哪些只是 agent-only behavior？
- 如果映射到 AIForInterviewer，哪些 source patterns 会造成 safety、privacy、UX、persistence 或 governance conflicts？
- 如果任何 idea 在 discovery 之外进入 actual implementation 或 documentation，后续轮次应如何处理 MIT license attribution？
- 哪些 findings 需要更深入检查本 Round 1 slice 未读取的 command files，例如 `mock`、`debrief`、`research`、`decode`、`resume`、`linkedin`、`pitch`、`outreach`、`salary` 或 `negotiate`？
