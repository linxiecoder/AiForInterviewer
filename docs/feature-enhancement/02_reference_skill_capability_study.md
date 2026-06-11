---
title: Reference Skill Capability Study
type: assessment
status: draft
owner: architecture-review
permalink: ai-for-interviewer/feature-enhancement/reference-skill-capability-study
---

# Reference Skill Capability Study

## 1. Scope, Source Pin, Method

本文只评估 `/tmp/interview-coach-skill-phase2-20260611` 这份 reference skill 在 Phase 2 中可作为能力研究输入的内容。reference HEAD 已核对为 `634a8dd8689e0420c21e5f0c8ae3cfa9e1a7ab7e`。

本轮只生成本文件，不运行 Spec Kit，不修改业务代码、测试、配置、依赖、CI、Phase 1 文档或 Phase 3 文档。Reference 侧 `CAP-*`、`RP-*`、`TP-*`、`TPR-*`、`ART-*`、`VAL-*`、`GR-*`、`REF-OPP-*` 的 source evidence 只来自 `/tmp/interview-coach-skill-phase2-20260611` 下的实际文件；CodeGraph、`.understand-anything` 或任何索引产物不得作为 reference 文件级证据。

方法顺序：

1. 先完成 reference repo coverage audit。
2. 再逐文件读取 root docs、release docs、`references/*.md`、`references/commands/*.md`。
3. 对实际发现文件做文件级分类。
4. 从 reference 原生能力、实践、任务模式、artifact、validation signal、guardrail 中连续编号抽取。
5. 仅在第 13 节及之后把 Phase 1 候选项作为弱背景映射。

## 2. Full Coverage Inventory

| 指标 | 数量 | 说明 |
| --- | ---: | --- |
| total files discovered | 80 | 含 `.git/**` inventory material |
| non_git_files_discovered | 51 | 不含 `.git/**` |
| markdown_files_discovered | 48 | 全部已读取并分类 |
| markdown_files_classified | 48 | 无未分类 Markdown |
| references_files_classified | 18 | `references/*.md` |
| references_commands_files_classified | 25 | `references/commands/*.md` |

| 预期类别 | 分类 | 证据 | Phase 2 结论 |
| --- | --- | --- | --- |
| `tests/` | absent_expected_category | full inventory | reference repo 未提供测试目录，不能推断可执行验证 |
| `scripts/` | absent_expected_category | full inventory | reference repo 未提供脚本目录，不能推断自动化流程 |
| `schemas/` | absent_expected_category | full inventory | 只有 Markdown schema-like docs，不是机器可执行 schema |
| `contracts/` | absent_expected_category | full inventory | 无独立 contract artifact |
| `workflows/` | absent_expected_category | full inventory | workflow 存在于 Markdown command docs 中 |
| `prompts/` | absent_expected_category | full inventory | 无独立 prompt 文件目录 |
| `evals/` | absent_expected_category | full inventory | 无 eval suite |
| `validation/` | absent_expected_category | full inventory | 无 validation harness |
| `templates/` | absent_expected_category | full inventory | 输出模板嵌在 Markdown 内 |
| `reports/` | absent_expected_category | full inventory | 无生成报告目录 |

`absent_expected_category` 只用于上述预期但不存在的目录/类别；实际发现的文件只使用 `primary_evidence`、`supporting_evidence`、`low_relevance`、`unreadable`、`skipped_binary_or_irrelevant`。

## 3. File Classification Matrix

| 路径/范围 | 文件数 | 分类 | 用途 |
| --- | ---: | --- | --- |
| `SKILL.md` | 1 | primary_evidence | skill 入口、状态文件、命令注册、guardrail、schema-like state |
| `README.md` | 1 | primary_evidence | command surface、版本叙述、使用模型、能力总览 |
| `VERSIONS.md` | 1 | primary_evidence | release capability claims 与迁移叙述 |
| `releases/*.md` | 2 | primary_evidence | v2/v3 release-note capability claims |
| `references/*.md` | 18 | primary_evidence | shared coaching modules、rubrics、schemas、migration、transcript/story engines |
| `references/commands/*.md` | 25 | primary_evidence | command-level workflows、priority checks、output schemas、state integration |
| `.claude/settings.json` | 1 | supporting_evidence | local skill/tool settings context, not capability evidence |
| `.gitignore` | 1 | supporting_evidence | repo hygiene context, not capability evidence |
| `LICENSE` | 1 | supporting_evidence | license context, not capability evidence |
| `.git/**` | 29 | skipped_binary_or_irrelevant | inventory material only, not file-level capability evidence |
| unreadable files | 0 | unreadable | no unreadable file found |
| low relevance files | 0 | low_relevance | no discovered non-git file needed this classification |

Markdown coverage status: all 48 Markdown files are classified. No discovered Markdown file is missing from the classification matrix.

## 4. Evidence Model and Claim Rules

Phase 2 evidence levels:

| Evidence level | Definition | Allowed claim shape |
| --- | --- | --- |
| direct_reference_text | A claim is directly stated in a specific reference file. | The reference describes this behavior or artifact. |
| cross_reference_consistent | Multiple reference files align on the same behavior, artifact, or rule. | The reference design is internally consistent across files. |
| release_note_claim | README/VERSIONS/release docs claim a capability or change. | Release claim only; needs artifact verification before maturity upgrade. |
| schema_like_design | Markdown defines state shape, output schema, table, migration, or artifact structure. | Design-only schema signal unless executable schema is found. |
| absence_verified | Full inventory confirms expected category/file is absent. | Negative evidence; do not infer implementation. |
| executable_evidence | Executable code, test, script, schema validator, CI, or eval artifact exists. | No such reference evidence found in this audit. |
| unsupported_or_unknown | Requested claim lacks source support. | Do not state as a reference finding. |

Evidence-level crosswalk:

| Phase 2 level | Phase 1 / Phase 3 generic relationship | Boundary |
| --- | --- | --- |
| direct_reference_text | maps to `design-only` unless paired with executable artifact evidence | direct text is not maturity |
| cross_reference_consistent | maps to stronger `design-only` / internally consistent reference signal | consistency is not runtime validation |
| release_note_claim | maps to claim-only supporting signal | release notes do not prove executable behavior |
| schema_like_design | maps to design-only schema / artifact model | Markdown schema is not a validator |
| absence_verified | maps to negative evidence / known gap | absence can bound claims |
| executable_evidence | would map to implementation or validation evidence | no entries found in this reference audit |
| unsupported_or_unknown | maps to unknown / unsupported | claim must be removed or marked unknown |

Claim rules:

1. evidence level is not maturity.
2. `direct_reference_text` or `cross_reference_consistent` may still describe only design-only capability.
3. Markdown workflows and schema-like docs remain design-only unless executable evidence is found.
4. Release notes can support “the reference claims X”, not “X is operationally validated”.
5. No reference-native claim may be sourced from CodeGraph, `.understand-anything`, or inferred index output.

## 5. Capability Catalog CAP-*

| ID | Capability | Evidence level | Source evidence | Phase 2 assessment |
| --- | --- | --- | --- | --- |
| CAP-001 | Session state and continuity through `coaching_state.md`, session log, score history, interview loops, storybank, archival rules, and schema migration. | cross_reference_consistent | `SKILL.md`, `references/coaching-state-schema.md`, `references/schema-migration.md`, `references/archival-rules.md`, `references/state-update-triggers.md`, `references/commands/progress.md` | Strong design signal; design-only because no executable state manager exists. |
| CAP-002 | Command registry and intent routing across interview coaching commands. | direct_reference_text | `SKILL.md`, `README.md`, `references/commands/help.md` | Clear command surface; Markdown-only command definitions. |
| CAP-003 | Evidence-based coaching with confidence labels, source tiers, and no unsupported company/salary claims. | cross_reference_consistent | `references/evidence-sourcing.md`, `references/commands/research.md`, `references/commands/prep.md`, `references/commands/salary.md`, `references/commands/negotiate.md` | High-value guardrail model; not executable enforcement. |
| CAP-004 | Five-dimension scoring model for Substance, Structure, Relevance, Credibility, and Differentiation, with seniority calibration and root-cause review. | cross_reference_consistent | `references/rubrics-detailed.md`, `references/calibration-engine.md`, `references/cross-cutting.md`, `references/commands/analyze.md`, `references/commands/progress.md` | Consistent rubric design; no scoring implementation found. |
| CAP-005 | Format-aware transcript analysis across interview types and transcript sources. | cross_reference_consistent | `references/transcript-formats.md`, `references/transcript-processing.md`, `references/commands/analyze.md`, `references/commands/debrief.md` | Detailed parsing and quality-gate design; no parser artifact found. |
| CAP-006 | Storybank, story strength, earned secrets, narrative identity, and portfolio-optimized story mapping. | cross_reference_consistent | `references/storybank-guide.md`, `references/story-mapping-engine.md`, `references/differentiation.md`, `references/commands/stories.md`, `references/commands/prep.md` | Rich artifact model; design-only table/schema. |
| CAP-007 | Practice and mock progression through gated drills, warmups, self-assessment delta, interviewer read, and role-specific pressure. | cross_reference_consistent | `references/commands/practice.md`, `references/commands/mock.md`, `references/role-drills.md`, `references/challenge-protocol.md` | Detailed workflow design; no runtime drill engine found. |
| CAP-008 | Company/JD research, role-fit assessment, interviewer intelligence, and claim verification tiers. | cross_reference_consistent | `references/commands/research.md`, `references/commands/prep.md`, `references/commands/decode.md`, `references/cross-cutting.md` | Useful source discipline; browsing/search execution is not packaged as code. |
| CAP-009 | Application-material optimization for resume, LinkedIn, pitch, outreach, apply answers, and thank-you notes with cross-surface consistency. | cross_reference_consistent | `references/commands/resume.md`, `references/commands/linkedin.md`, `references/commands/pitch.md`, `references/commands/outreach.md`, `references/commands/apply.md`, `references/commands/thankyou.md` | Broad workflow coverage; templates are embedded in docs. |
| CAP-010 | Progress intelligence, outcome correlation, calibration drift detection, graduation criteria, and retrospective closure. | cross_reference_consistent | `references/commands/progress.md`, `references/calibration-engine.md`, `references/commands/reflect.md` | Strong analytical model; no persisted analytics implementation found. |
| CAP-011 | Presentation, compensation, negotiation, and technical-format coaching boundaries. | cross_reference_consistent | `references/commands/present.md`, `references/commands/salary.md`, `references/commands/negotiate.md`, `references/commands/prep.md` | Boundary-aware workflows; design-only. |
| CAP-012 | Directness-level modulation and Level 5 challenge protocol. | cross_reference_consistent | `references/challenge-protocol.md`, `references/coaching-voice.md`, `references/commands/practice.md`, `references/commands/mock.md`, `references/commands/stories.md` | Reusable guardrail/practice pattern; no policy engine found. |

## 6. Reference Practices RP-*

| ID | Practice | Evidence level | Source evidence | Notes |
| --- | --- | --- | --- | --- |
| RP-001 | Load reference docs on demand based on command scope. | direct_reference_text | `SKILL.md`, `references/commands/*.md` | Command files repeatedly name companion references. |
| RP-002 | Ask one question at a time in guided workflows. | cross_reference_consistent | `SKILL.md`, `references/commands/kickoff.md`, `references/commands/pitch.md`, `references/commands/stories.md` | Interaction discipline, not UI requirement. |
| RP-003 | Start with priority checks and soft gates before deep work. | cross_reference_consistent | `references/commands/prep.md`, `references/commands/resume.md`, `references/commands/outreach.md`, `references/commands/salary.md` | Useful for command readiness design. |
| RP-004 | Use strengths, gaps, scorecards, and next-step recommendations as output shape. | cross_reference_consistent | `references/commands/analyze.md`, `references/commands/practice.md`, `references/commands/mock.md`, `references/commands/progress.md` | Common feedback envelope. |
| RP-005 | Preserve state history through migration, archival, and versioning instead of overwriting context blindly. | cross_reference_consistent | `references/schema-migration.md`, `references/archival-rules.md`, `references/commands/stories.md`, `references/commands/reflect.md` | State hygiene practice. |
| RP-006 | Label confidence and source tier for external/company claims. | cross_reference_consistent | `references/evidence-sourcing.md`, `references/commands/research.md`, `references/commands/prep.md` | Candidate-provided and public-source boundaries are explicit. |
| RP-007 | Reuse artifacts across commands for cross-surface consistency. | cross_reference_consistent | `references/commands/pitch.md`, `references/commands/resume.md`, `references/commands/linkedin.md`, `references/commands/outreach.md` | Positioning and storybank are shared inputs. |
| RP-008 | Isolate hard critique to directness Level 5 or explicit challenge paths. | cross_reference_consistent | `references/challenge-protocol.md`, `references/coaching-voice.md`, `references/commands/progress.md` | Avoids accidental over-aggressive coaching. |

## 7. Task Patterns TP-* and Turn/Prompt Patterns TPR-*

| ID | Pattern | Evidence level | Source evidence | Extraction |
| --- | --- | --- | --- | --- |
| TP-001 | Command registry as task surface. | direct_reference_text | `SKILL.md`, `README.md`, `references/commands/help.md` | Commands are the primary workflow entry points. |
| TP-002 | Priority check before action. | cross_reference_consistent | `references/commands/pitch.md`, `references/commands/resume.md`, `references/commands/present.md`, `references/commands/salary.md` | Checks missing kickoff, urgent interview, existing state. |
| TP-003 | Depth-level variants. | cross_reference_consistent | `references/commands/research.md`, `references/commands/resume.md`, `references/commands/outreach.md`, `references/commands/present.md` | Quick / Standard / Deep variants recur. |
| TP-004 | Parse, classify, act, save. | cross_reference_consistent | `references/commands/analyze.md`, `references/commands/decode.md`, `references/commands/prep.md`, `references/state-update-triggers.md` | Input analysis leads to artifact update. |
| TP-005 | Recommended next action at output close. | cross_reference_consistent | `references/commands/*.md` | Most command schemas end with recommended next and alternatives. |
| TP-006 | Soft gate, proceed with caveat, or redirect. | cross_reference_consistent | `references/commands/practice.md`, `references/commands/research.md`, `references/commands/salary.md` | Avoids blocking while naming risk. |
| TPR-001 | Ask for self-assessment after forming independent coach score. | direct_reference_text | `references/commands/practice.md`, `references/commands/progress.md` | Reduces anchoring. |
| TPR-002 | Use decision-tree triage after scoring. | cross_reference_consistent | `references/cross-cutting.md`, `references/rubrics-detailed.md`, `references/calibration-engine.md` | Turns scores into root causes. |
| TPR-003 | Rotate challenge lenses at Level 5. | direct_reference_text | `references/challenge-protocol.md`, `references/commands/practice.md` | Assumption, blind spot, pre-mortem, devil's advocate, strengthening path. |
| TPR-004 | Replay interviewer read / inner monologue from candidate evidence. | cross_reference_consistent | `references/commands/analyze.md`, `references/commands/mock.md`, `references/commands/practice.md` | Converts transcript/answer into external perspective. |
| TPR-005 | Use exact Markdown output schemas per command. | schema_like_design | `references/commands/*.md`, `references/coaching-state-schema.md` | Schema-like design only. |

## 8. Artifact Register ART-*

| ID | Artifact | Evidence level | Source evidence | Maturity boundary |
| --- | --- | --- | --- | --- |
| ART-001 | `coaching_state.md` with Profile, Session Log, Score History, Storybank, Interview Loops, Active Coaching Strategy, and related sections. | schema_like_design | `SKILL.md`, `references/coaching-state-schema.md` | Markdown state model, not executable persistence. |
| ART-002 | Interview Intelligence tables: Question Bank, Effective/Ineffective Patterns, Company Patterns, Recruiter/Interviewer Feedback. | schema_like_design | `SKILL.md`, `references/commands/analyze.md`, `references/commands/debrief.md`, `references/commands/progress.md` | Designed tables only. |
| ART-003 | Storybank index and Story Details with STAR text, earned secret, version history, and deploy use-case. | schema_like_design | `references/storybank-guide.md`, `references/commands/stories.md` | Markdown artifact model. |
| ART-004 | Score History, Outcome Log, Calibration State, and Cross-Dimension Root Causes. | schema_like_design | `references/calibration-engine.md`, `references/commands/progress.md` | Analytics schema-like docs. |
| ART-005 | JD Analysis / Role-Fit Assessment entries. | schema_like_design | `references/commands/decode.md`, `references/commands/prep.md`, `references/cross-cutting.md` | Design artifact for prep/research. |
| ART-006 | Application answer files under `job-search/[company]_application.md`. | schema_like_design | `references/commands/apply.md`, `SKILL.md` | File convention described, not implemented here. |
| ART-007 | Resume, LinkedIn, Positioning, Outreach, Presentation, Comp, and Negotiation strategy sections. | schema_like_design | `references/commands/resume.md`, `references/commands/linkedin.md`, `references/commands/pitch.md`, `references/commands/outreach.md`, `references/commands/present.md`, `references/commands/salary.md`, `references/commands/negotiate.md` | Embedded output/state schema. |
| ART-008 | Release/version notes. | release_note_claim | `VERSIONS.md`, `releases/v2.md`, `releases/v3.md`, `README.md` | Claims of capability evolution, not validation artifact. |

## 9. Validation Signals VAL-*

| ID | Validation signal | Evidence level | Source evidence | Assessment |
| --- | --- | --- | --- | --- |
| VAL-001 | Command output schemas constrain expected response shape. | schema_like_design | `references/commands/*.md` | Useful design validation target; not executable. |
| VAL-002 | State schema and schema migration define compatibility checks. | schema_like_design | `references/coaching-state-schema.md`, `references/schema-migration.md` | Migration design, no migration script. |
| VAL-003 | Quality gates for transcript quality, storybank health, JD/currentness, and format discovery. | cross_reference_consistent | `references/transcript-processing.md`, `references/commands/prep.md`, `references/commands/stories.md`, `references/commands/practice.md` | Human/agent workflow gates. |
| VAL-004 | Rubrics and graduation criteria provide expected scoring thresholds. | cross_reference_consistent | `references/rubrics-detailed.md`, `references/commands/progress.md`, `references/commands/practice.md` | Scoring criteria exist; no scorer validation. |
| VAL-005 | Claim verification tiers guard company, salary, and external assertions. | cross_reference_consistent | `references/evidence-sourcing.md`, `references/commands/research.md`, `references/commands/salary.md`, `references/commands/prep.md` | Strong guardrail design. |
| VAL-006 | Absence of tests/scripts/evals/CI means no executable validation is available in the reference. | absence_verified | full inventory | Do not infer runtime guarantee. |

No `executable_evidence` entries were found.

## 10. Guardrails GR-*

| ID | Guardrail | Evidence level | Source evidence | Boundary |
| --- | --- | --- | --- | --- |
| GR-001 | Do not make unsupported claims; label confidence and source tier. | cross_reference_consistent | `references/evidence-sourcing.md`, `references/commands/research.md`, `references/commands/prep.md` | Applies especially to company/interviewer facts. |
| GR-002 | Ask one question at a time in discovery workflows. | cross_reference_consistent | `SKILL.md`, `references/commands/kickoff.md`, `references/commands/stories.md` | Interaction guardrail. |
| GR-003 | Do not fabricate candidate experience, company facts, salary data, or technical correctness. | cross_reference_consistent | `references/commands/resume.md`, `references/commands/salary.md`, `references/commands/prep.md`, `references/commands/present.md` | Candidate safety boundary. |
| GR-004 | Technical-format coaching is communication coaching, not domain correctness evaluation. | direct_reference_text | `references/commands/prep.md`, `references/commands/present.md` | High-stakes boundary. |
| GR-005 | Level 5 challenge protocol is explicit and scoped. | cross_reference_consistent | `references/challenge-protocol.md`, `references/coaching-voice.md` | Prevents unrequested harsh critique. |
| GR-006 | Archive or summarize old state when thresholds are exceeded. | cross_reference_consistent | `SKILL.md`, `references/archival-rules.md`, `references/commands/progress.md` | State-size guardrail. |
| GR-007 | Detect stale company/research/interview intelligence. | cross_reference_consistent | `references/commands/research.md`, `references/commands/progress.md`, `references/commands/prep.md` | Temporal freshness guardrail. |
| GR-008 | Respect candidate agency when redirecting, gating, or recommending retargeting. | cross_reference_consistent | `references/commands/practice.md`, `references/commands/progress.md`, `references/commands/research.md` | Coaching recommendation, not forced decision. |

## 11. Reference-Derived Opportunities REF-OPP-*

| ID | Opportunity | Reference basis | Evidence level | Suggested handling |
| --- | --- | --- | --- | --- |
| REF-OPP-001 | Build a command registry / developer command matrix for product and docs operations. | `SKILL.md`, `README.md`, `references/commands/help.md` | cross_reference_consistent | Adapt as metadata/inventory, not copied command set. |
| REF-OPP-002 | Add evidence vocabulary and non-claim guardrails to capability docs. | `references/evidence-sourcing.md`, `references/commands/research.md`, `references/commands/prep.md` | cross_reference_consistent | Adopt as docs governance language. |
| REF-OPP-003 | Use state schema and migration concepts as inspiration for long-lived coaching/session records. | `references/coaching-state-schema.md`, `references/schema-migration.md`, `references/archival-rules.md` | schema_like_design | Research before implementation because reference lacks executable schema. |
| REF-OPP-004 | Introduce transcript format taxonomy and quality gates for interview analysis workflows. | `references/transcript-formats.md`, `references/transcript-processing.md`, `references/commands/analyze.md` | cross_reference_consistent | Adapt to existing product/contracts only after Phase 3 inventory. |
| REF-OPP-005 | Model a storybank / reusable evidence asset concept for candidate answers and feedback continuity. | `references/storybank-guide.md`, `references/story-mapping-engine.md`, `references/commands/stories.md` | cross_reference_consistent | Adapt cautiously; product semantics may differ. |
| REF-OPP-006 | Convert output schemas into validation checklists or acceptance criteria. | `references/commands/*.md` | schema_like_design | Use as design checklist, not generated schema. |
| REF-OPP-007 | Use practice progression and warmup / self-assessment delta as workbench UX inspiration. | `references/commands/practice.md`, `references/role-drills.md` | cross_reference_consistent | Research UX fit before implementation. |
| REF-OPP-008 | Add recommended-next affordances after feedback or prep workflows. | `references/commands/*.md` | cross_reference_consistent | Adapt to product flow, avoid command-name copying. |
| REF-OPP-009 | Strengthen redaction/source boundaries for provider and external-data claims. | `references/evidence-sourcing.md`, `references/commands/salary.md`, `references/commands/prep.md` | cross_reference_consistent | Pair with executable tests in later phases. |
| REF-OPP-010 | Separate design-only, release-note, and executable evidence in all future enhancement inventories. | full audit | absence_verified | Adopt immediately as assessment practice. |

## 12. Reference Claim Boundary

The reference repo is a Markdown skill package. It contains command workflows, output schemas, state schemas, rubrics, examples, release notes, and guardrail text. It does not contain executable tests, scripts, validators, CI workflows, runtime services, database schema, API contracts, or application code.

Therefore:

- Reference-native capabilities may be described as reference design capabilities.
- A capability supported by `direct_reference_text` or `cross_reference_consistent` is still design-only unless executable evidence exists.
- Markdown schema-like docs may inspire artifact design but cannot be treated as machine-validated schema.
- Release docs may support “the reference claims this changed”, not “this behavior is operationally validated”.
- Any future implementation claim must come from AiForInterviewer code, tests, contracts, or validated runtime artifacts, not from this reference study alone.

## 13. Phase 1 CAND-* Mapping

Phase 1 candidates are weak background only. They do not participate in sections 1-12 reference-native extraction.

| Phase 1 candidate | Related reference opportunities | Use in Phase 2 |
| --- | --- | --- |
| CAND-001 Interview Workbench maintainability and real interaction validation | REF-OPP-004, REF-OPP-007, REF-OPP-008 | Transcript quality gates, staged practice, and recommended-next patterns are relevant design inputs. |
| CAND-002 API / Frontend contract drift guard | REF-OPP-006, REF-OPP-010 | Output schema discipline can inform contract checklist design, but reference has no executable contract tests. |
| CAND-003 Capability status / non-claim guard | REF-OPP-002, REF-OPP-010 | Directly aligned with evidence vocabulary and claim-boundary rules. |
| CAND-004 CI baseline expansion | REF-OPP-006, REF-OPP-010 | Reference supplies validation ideas but no CI implementation evidence. |
| CAND-005 Polish backend aggregate seam | REF-OPP-005, REF-OPP-008 | Storybank and continuity patterns may inform aggregate concepts only after code inventory. |
| CAND-006 App composition / config diagnostics | REF-OPP-001, REF-OPP-006 | Command registry and readiness checks can inspire diagnostics, not dictate architecture. |
| CAND-007 AI Runtime evidence taxonomy | REF-OPP-002, REF-OPP-009, REF-OPP-010 | Strong conceptual match for evidence levels, source tiers, and non-claim wording. |
| CAND-008 Provider boundary / redaction golden samples | REF-OPP-002, REF-OPP-009 | External-claim and no-fabrication guardrails are relevant; later work needs executable redaction samples. |
| CAND-009 Doc Governor CLI command registry | REF-OPP-001 | Reference command registry is the clearest inspiration, but command names should not be copied mechanically. |
| CAND-010 Developer command matrix | REF-OPP-001, REF-OPP-006 | Matrix pattern is promising for docs/dev workflow inventory. |

## 14. Secondary Audit Gaps

| Gap | Evidence level | Impact |
| --- | --- | --- |
| No executable tests, evals, CI, or validation harness. | absence_verified | No runtime or regression assurance can be inferred. |
| No machine-readable schemas. | absence_verified | Schema-like Markdown requires translation and validation design. |
| No standalone prompt directory or prompt tests. | absence_verified | Prompt behavior is embedded in docs, not testable as-is. |
| No API, frontend, backend, or database contracts. | absence_verified | Any product mapping requires AiForInterviewer-side inventory. |
| No generated reports/templates directory. | absence_verified | Outputs are reference templates inside command docs. |
| License was read only as supporting evidence. | supporting_evidence | Any reuse beyond conceptual adaptation needs separate license review. |
| This draft is not an active registry entry until governance follow-up. | direct_reference_text | `docs/00-governance/DOCS_INDEX.md` remains the active docs registry. |

## 15. Adopt / Adapt / Reject / Research

| Decision | Items | Rationale |
| --- | --- | --- |
| Adopt | Evidence vocabulary; non-claim rules; confidence/source-tier language; clear design-only boundary. | Low implementation risk and directly improves assessment rigor. |
| Adopt | Coverage audit counts and file classification discipline. | Prevents sampling bias and category misuse. |
| Adapt | Command registry, recommended-next, priority checks, and depth levels. | Useful interaction patterns, but must fit AiForInterviewer product architecture. |
| Adapt | State schema, storybank, transcript quality gates, and calibration concepts. | Valuable models; require Phase 3 inventory before implementation. |
| Reject | Mechanical copying of command names, persona wording, or `coaching_state.md` as product truth. | Reference is a skill package, not AiForInterviewer architecture. |
| Reject | Treating Markdown workflows as implementation, runtime guarantee, or CI validation. | No executable evidence exists. |
| Research | Which opportunities map to current contracts, frontend flows, backend aggregates, and provider boundaries. | Needs Phase 3 source inventory. |
| Research | What validation artifacts would be required to upgrade any design-only reference idea. | Later phases need tests/contracts/evals. |

## 16. Mechanical Copying Risks

1. Copying the reference command set would import a Claude-skill interface rather than AiForInterviewer product flows.
2. Copying `coaching_state.md` directly would bypass existing persistence, API, and privacy boundaries.
3. Copying salary/company research text could create stale or jurisdiction-sensitive claims.
4. Copying output schemas as product contracts would skip ownership, validation, and compatibility review.
5. Copying challenge protocol wording without UX context could make feedback tone inconsistent with product expectations.
6. Copying Markdown examples into runtime prompts would blur design examples with production behavior.
7. Copying release-note claims as implementation facts would violate the evidence model.

## 17. Phase 3 Inputs

Phase 3 should receive these inputs as reference-derived, design-only candidates:

| Input | Source IDs | Needed Phase 3 check |
| --- | --- | --- |
| Evidence taxonomy and claim-boundary rules | CAP-003, GR-001, REF-OPP-002, REF-OPP-010 | Find current AiForInterviewer evidence/status vocabulary and false-claim risks. |
| Command / workflow registry concept | CAP-002, RP-001, TP-001, REF-OPP-001 | Inventory existing CLI/docs/dev commands and ownership. |
| Output schema checklist concept | TPR-005, VAL-001, ART-007, REF-OPP-006 | Compare with existing API/frontend/test contracts. |
| Transcript quality and format taxonomy | CAP-005, VAL-003, REF-OPP-004 | Inspect current transcript ingestion, feedback, and workbench paths. |
| Storybank / reusable candidate evidence concept | CAP-006, ART-003, REF-OPP-005 | Determine whether current domain model has equivalent aggregates. |
| Practice progression / warmup / self-assessment delta | CAP-007, TPR-001, REF-OPP-007 | Compare with current interview workbench UX and backend semantics. |
| External claim/source guardrails | CAP-003, GR-003, GR-004, REF-OPP-009 | Map to provider boundary, redaction, and external-data policies. |
| Calibration/progress analytics | CAP-010, ART-004, VAL-004 | Identify available score/outcome data and privacy constraints. |

## 18. Phase 3 Readiness and Open Questions

Readiness:

- Phase 2 reference coverage is sufficient for Phase 3 inventory inputs.
- Extracted opportunities are bounded as reference-derived and design-only.
- Phase 1 mapping is isolated to section 13 and later.
- No executable maturity claim is made from reference Markdown alone.

Open questions for Phase 3:

1. Which existing AiForInterviewer modules already implement equivalent evidence/status vocabulary?
2. Which existing tests or contracts can validate non-claim guardrails?
3. Does the product have a first-class concept equivalent to storybank, or should this remain a future research idea?
4. Where should recommended-next logic live if adapted: frontend view model, backend policy, or docs-only checklist?
5. What source paths own transcript parsing, feedback generation, provider redaction, and workbench interaction state?
6. Which opportunities are docs-only improvements versus implementation candidates?

## 19. Evidence Index

| Evidence source | Classification | Used for |
| --- | --- | --- |
| `/tmp/interview-coach-skill-phase2-20260611/SKILL.md` | primary_evidence | CAP-001, CAP-002, RP-001, ART-001, GR-002 |
| `/tmp/interview-coach-skill-phase2-20260611/README.md` | primary_evidence | CAP-002, TP-001, ART-008 |
| `/tmp/interview-coach-skill-phase2-20260611/VERSIONS.md` | primary_evidence | ART-008, release_note_claim |
| `/tmp/interview-coach-skill-phase2-20260611/releases/v2.md` | primary_evidence | ART-008, release_note_claim |
| `/tmp/interview-coach-skill-phase2-20260611/releases/v3.md` | primary_evidence | ART-008, release_note_claim |
| `/tmp/interview-coach-skill-phase2-20260611/references/archival-rules.md` | primary_evidence | CAP-001, RP-005, GR-006 |
| `/tmp/interview-coach-skill-phase2-20260611/references/calibration-engine.md` | primary_evidence | CAP-004, CAP-010, ART-004, VAL-004 |
| `/tmp/interview-coach-skill-phase2-20260611/references/challenge-protocol.md` | primary_evidence | CAP-012, TPR-003, GR-005 |
| `/tmp/interview-coach-skill-phase2-20260611/references/coaching-state-schema.md` | primary_evidence | CAP-001, ART-001, VAL-002 |
| `/tmp/interview-coach-skill-phase2-20260611/references/coaching-voice.md` | primary_evidence | CAP-012, RP-008, GR-005 |
| `/tmp/interview-coach-skill-phase2-20260611/references/cross-cutting.md` | primary_evidence | CAP-004, CAP-008, TPR-002 |
| `/tmp/interview-coach-skill-phase2-20260611/references/differentiation.md` | primary_evidence | CAP-006, CAP-009 |
| `/tmp/interview-coach-skill-phase2-20260611/references/evidence-sourcing.md` | primary_evidence | CAP-003, RP-006, GR-001 |
| `/tmp/interview-coach-skill-phase2-20260611/references/examples.md` | primary_evidence | CAP-004, VAL-004 |
| `/tmp/interview-coach-skill-phase2-20260611/references/mode-detection.md` | primary_evidence | TP-004 |
| `/tmp/interview-coach-skill-phase2-20260611/references/role-drills.md` | primary_evidence | CAP-007, REF-OPP-007 |
| `/tmp/interview-coach-skill-phase2-20260611/references/rubrics-detailed.md` | primary_evidence | CAP-004, VAL-004 |
| `/tmp/interview-coach-skill-phase2-20260611/references/schema-migration.md` | primary_evidence | CAP-001, RP-005, VAL-002 |
| `/tmp/interview-coach-skill-phase2-20260611/references/state-update-triggers.md` | primary_evidence | CAP-001, TP-004 |
| `/tmp/interview-coach-skill-phase2-20260611/references/story-mapping-engine.md` | primary_evidence | CAP-006, REF-OPP-005 |
| `/tmp/interview-coach-skill-phase2-20260611/references/storybank-guide.md` | primary_evidence | CAP-006, ART-003 |
| `/tmp/interview-coach-skill-phase2-20260611/references/transcript-formats.md` | primary_evidence | CAP-005, REF-OPP-004 |
| `/tmp/interview-coach-skill-phase2-20260611/references/transcript-processing.md` | primary_evidence | CAP-005, VAL-003 |
| `/tmp/interview-coach-skill-phase2-20260611/references/commands/*.md` | primary_evidence | CAP-002 through CAP-012, RP-001 through RP-008, TP/TPR, ART, VAL, GR |
| `/tmp/interview-coach-skill-phase2-20260611/.claude/settings.json` | supporting_evidence | settings context only |
| `/tmp/interview-coach-skill-phase2-20260611/.gitignore` | supporting_evidence | repo hygiene context only |
| `/tmp/interview-coach-skill-phase2-20260611/LICENSE` | supporting_evidence | license context only |
| `/tmp/interview-coach-skill-phase2-20260611/.git/**` | skipped_binary_or_irrelevant | inventory only |
