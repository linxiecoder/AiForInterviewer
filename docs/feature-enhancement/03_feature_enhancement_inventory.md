---
title: Feature Enhancement Refactor Inventory
type: inventory
status: draft
owner: architecture-review
permalink: ai-for-interviewer/feature-enhancement/feature-enhancement-inventory
---

# Feature Enhancement Refactor Inventory

## 1. Purpose and Inputs

本文是 Phase 3 的正式功能强化重构清单。它把 Phase 2.5 的 RDP、REUSE、ADB 和 FE-SEED 收敛为 FE-* inventory，用于后续人工审查、Spec Kit specification、Codex Goal 拆分和实施排序。

本阶段只生成 inventory，不进入实现，不生成 Spec Kit 文档，不生成 Codex Goal，不修改业务代码、测试、配置、依赖、lockfile、CI 或 generated files。

输入优先级如下：

| 优先级 | 输入 | 用途 |
| --- | --- | --- |
| Primary | `docs/feature-enhancement/02b_reuse_synthesis.md` | 唯一候选生成来源；FE-* 只能从其中的 RDP / REUSE / ADB / FE-SEED 收敛而来 |
| Supporting | `docs/feature-enhancement/01_project_architecture_assessment.md` | 解释项目现有模块、项目证据和 non-claim 边界 |
| Supporting | `docs/feature-enhancement/02_reference_skill_capability_study.md` | 解释参考 Skill 的 design-only、schema_like_design、release_note_claim 和 absence_verified |
| Supporting | `AGENTS.md` | 约束写入边界、active docs、archive 和禁止事项 |
| Supporting | `docs/00-governance/DOCS_INDEX.md` | 约束当前有效文档体系和后续 handoff 入口 |

## 2. Inventory Generation Policy

Phase 3 不机械复制 FE-SEED。每个 FE 项都必须完成一次筛选：先确认项目问题，再确认参考灵感，再确认项目证据是否足够，最后决定 status、spec_readiness 和 phase3_decision。

生成规则：

| 规则 | Phase 3 执行方式 |
| --- | --- |
| RDP 是设计原语 | 只能作为 reusable primitive，不是任务编号，也不是实现承诺 |
| REUSE 是采用门槛 | `adopt` / `adapt` 且项目证据足够时才可能 proposed；`research` / `reject` 不得直接实现 |
| ADB 是采用 brief | 只支持 strong / medium 的候选，不能为 weak / blocked 项补造实施依据 |
| FE-SEED 是候选种子 | 可拆分、合并或降级，但必须保留 trace |
| NEW_FROM_REFERENCE gate | 必须说明 Phase 1 为什么没体现、当前项目证据是否足够、缺项目证据时不得 proposed |
| project_evidence_missing gate | 只能进入 `research`、`deferred` 或 `rejected`，spec_readiness 只能是 `not_ready` 或 `partial` |
| reference evidence gate | Markdown workflow、examples、release notes、schema_like_design 不能写成 executable implementation |
| non-claim gate | fake、replay、deterministic、default-off 不能写成 live-provider quality |

## 3. Source Traceability

| FE | Source Trace | Source Flag | Absorption Mode | Phase 3 Decision |
| --- | --- | --- | --- | --- |
| FE-001 | RDP-006, RDP-017; REUSE-001, REUSE-010; ADB-001, ADB-010; FE-SEED-001, FE-SEED-007 | PROJECT_REINFORCED + NEW_FROM_REFERENCE | adopt | proposed |
| FE-002 | RDP-005; REUSE-002; ADB-002; FE-SEED-002 | PROJECT_REINFORCED | adopt | proposed |
| FE-003 | RDP-003, RDP-010; REUSE-005; ADB-005; FE-SEED-003 | NEW_FROM_REFERENCE | adapt | proposed |
| FE-004 | RDP-005, RDP-010; REUSE-006, REUSE-018; ADB-006, ADB-012; FE-SEED-004, FE-SEED-006 | NEW_FROM_REFERENCE | adapt | proposed |
| FE-005 | RDP-011; REUSE-007; ADB-007; FE-SEED-005 | NEW_FROM_REFERENCE | adapt | proposed |
| FE-006 | RDP-013; REUSE-008; ADB-008; FE-SEED-010 | NEW_FROM_REFERENCE | adapt | needs_confirmation |
| FE-007 | RDP-016; REUSE-003; ADB-003; FE-SEED-008 | NEW_FROM_REFERENCE | adopt | proposed |
| FE-008 | RDP-002, RDP-004, RDP-018; REUSE-004, REUSE-017; ADB-004, ADB-011; FE-SEED-009 | NEW_FROM_REFERENCE + PROJECT_REINFORCED | adapt | proposed |
| FE-009 | RDP-015, RDP-018; REUSE-009; ADB-009; FE-SEED-009 | NEW_FROM_REFERENCE | adapt | proposed |
| FE-010 | RDP-007, RDP-010, RDP-013; REUSE-011; FE-SEED-011 | NEW_FROM_REFERENCE | research | research |
| FE-011 | RDP-009; REUSE-013; FE-SEED-012 | NEW_FROM_REFERENCE | research | deferred |
| FE-012 | RDP-008; REUSE-012; FE-SEED-013 | NEW_FROM_REFERENCE | research | research |
| FE-013 | RDP-012; REUSE-014; FE-SEED-014 | NEW_FROM_REFERENCE | research | research |
| FE-014 | RDP-001; REUSE-016; FE-SEED-015 | NEW_FROM_REFERENCE | research | research |
| FE-015 | RDP-014; REUSE-015; FE-SEED-016 | NEW_FROM_REFERENCE | reject | rejected |

## 4. Candidate Screening Rules

| Screening Rule | Proposed Allowed | Research / Deferred / Rejected Required |
| --- | --- | --- |
| 项目已有 executable_evidence 或 partial executable_evidence | 是，但必须写清 validation strategy 和 non-claim boundary | 不适用 |
| 参考 Skill 只有 `design-only` Markdown workflow | 只有当项目已有承接面时可 adapt | 无项目承接面时 research |
| 参考 Skill 是 `schema_like_design` | 不得当作 Pydantic schema、DB schema、migration 或 validator | 先做 project-native schema research |
| 参考 Skill 是 examples | 只能作为 behavior-contract seed | 不得当作测试或 fixture 已存在 |
| 参考 Skill 是 release notes | 只能作为 compatibility checklist 灵感 | 不得当作 migration automation |
| `project_evidence_missing=yes` | 不允许 | 必须 research、deferred 或 rejected |
| 涉及 transcript、storybank、outcome、coaching state、challenge protocol | 当前不允许 proposed | 缺输入、隐私、存储、安全或 UX 边界时保持 research/deferred/rejected |

## 5. FE Inventory Summary

| Category | FE Items | Summary |
| --- | --- | --- |
| product_feature | FE-003, FE-004, FE-005, FE-006 | Workbench / Polish 的用户可见增强；FE-006 因 scope 仍需人工确认 |
| engineering_guardrail | FE-001, FE-002, FE-007 | non-claim、contract drift、examples seed 的工程保护 |
| agent_workflow | FE-008 | lazy reference loading 和 doc-governor command matrix |
| docs_governance | FE-009 | active docs handoff、compatibility checklist 和后续登记规则 |
| research | FE-010, FE-012, FE-013, FE-014, FE-015 | role/JD routing、transcript、outcome、coaching state、challenge policy |
| deferred | FE-011 | storybank 到 Assets 的生命周期需要 discovery |

| Decision | FE Items |
| --- | --- |
| proposed | FE-001, FE-002, FE-003, FE-004, FE-005, FE-007, FE-008, FE-009 |
| needs_confirmation | FE-006 |
| research | FE-010, FE-012, FE-013, FE-014 |
| deferred | FE-011 |
| rejected | FE-015 |

## 6. Proposed FE Items

### FE-001 Capability Status and Non-Claim Guard

| Field | Content |
| --- | --- |
| category | engineering_guardrail |
| status | proposed |
| spec_readiness | ready |
| project evidence | `CAPABILITY_PRESERVATION_MATRIX.md`、`tests/api/test_skeleton_guard.py`、eval non_claims、runtime `default-off` flags |
| reference inspiration | RDP-006/RDP-017 的 non-claim discipline 和 claim boundary UI wording；参考侧仍是 `design-only` |
| target state | 所有 FE、后续 Spec 和 UI copy 都显式区分 implemented、partial、skeleton、design-only、fake、replay、deterministic、default-off |
| validation strategy | static rg guard、capability wording guard、future focused tests；不证明 live-provider quality |
| risk | 过度保守导致真实进展难表达 |
| acceptance criteria | FE 文档和 YAML 均包含 evidence status；后续 Spec 不把 reference design-only 写成实现；fake/replay/deterministic/default-off 不写成 live-provider quality |

### FE-002 Backend / Frontend API Contract Drift Guard

| Field | Content |
| --- | --- |
| category | engineering_guardrail |
| status | proposed |
| spec_readiness | ready |
| project evidence | `apps/api/app/schemas/envelope.py`、`apps/web/src/shared/api/envelope.ts`、route snapshot 和 scoring/confidence schema |
| reference inspiration | RDP-005 的 evidence/confidence sourcing |
| target state | `source_availability`、`confidence_level`、`evidence_refs`、low confidence 语义在 backend/frontend contract 中有 parity guard |
| validation strategy | schema parity、route snapshot、TypeScript/static guard；不运行真实 provider |
| risk | 过早泛化 API 字段 |
| acceptance criteria | Spec 只覆盖现有 envelope 优先；不得新增宽泛框架；validation 明确证明字段同步，不证明 AI 质量 |

### FE-003 Workbench State-Aware Action Routing

| Field | Content |
| --- | --- |
| category | product_feature |
| status | proposed |
| spec_readiness | partial |
| project evidence | `InterviewPage.tsx`、`InterviewPage.test.ts`、`tests/web/test_interview_actions.py` 的 Workbench action/state partial evidence |
| reference inspiration | RDP-003/RDP-010 的 mode routing 和 recommended next action；参考 command router 是 `design-only` |
| target state | Workbench 以可审计 view model 区分 send answer、regenerate current node、new question、feedback next action、complete |
| validation strategy | frontend helper tests、static action guard、UI disabled/label state checks |
| risk | 误复制 reference command router |
| acceptance criteria | `regenerate_current_node` 与 `new_question` 语义分离；推荐动作可由状态推导；无 reference command engine 引入 |

### FE-004 Polish Progress Tree and Input Readiness Gate

| Field | Content |
| --- | --- |
| category | product_feature |
| status | proposed |
| spec_readiness | partial |
| project evidence | Polish feedback validation、warnings、source support policy、Workbench/Polish progress tree partial evidence |
| reference inspiration | RDP-005/RDP-010 的 input readiness、gated progression 和 evidence-aware next action |
| target state | 输入不足时降低置信、建议补资料或允许用户继续但显示边界；progress tree 体现 gate、redo 和 next action |
| validation strategy | API warning tests、UI notice tests、contract tests；不证明 transcript ingestion |
| risk | 偷渡 transcript feature 或新建 Training 主流程 |
| acceptance criteria | 不因输入不足生成完整质量声明；不引入 transcript parser；不把 Polish gate 扩成 Training 产品流 |

### FE-005 Feedback Correction Capture Loop

| Field | Content |
| --- | --- |
| category | product_feature |
| status | proposed |
| spec_readiness | partial |
| project evidence | feedback validation、low confidence warnings、provider redaction guard、Polish feedback service tests |
| reference inspiration | RDP-011 的 human correction loop |
| target state | 用户可以捕获 correction note、source refs 和 review state；系统只记录和待审，不宣称自动学习 |
| validation strategy | future API schema tests、UI state tests、redaction checks、non-claim wording guard |
| risk | 被误写成 automatic calibration |
| acceptance criteria | correction capture 不改变评分质量 claim；敏感信息有 redaction 边界；后续推荐只可使用已验证 correction |

### FE-007 Examples as Behavior-Contract Seeds

| Field | Content |
| --- | --- |
| category | engineering_guardrail |
| status | proposed |
| spec_readiness | ready |
| project evidence | 项目已有 pytest/TypeScript 测试入口，可在后续实现中承接 examples |
| reference inspiration | RDP-016；reference examples 是 `design-only` |
| target state | examples 只进入 acceptance wording、golden case intent 和人工审查样例，不作为已有测试 |
| validation strategy | 文档标记 guard、future real tests；不证明 runtime behavior |
| risk | examples 带入不适合本产品的假设 |
| acceptance criteria | 所有 examples 均标为 design-only；后续实现必须新增项目测试后才能升级为 executable_evidence |

### FE-008 Lazy Reference Loading and Doc-Governor Command Matrix

| Field | Content |
| --- | --- |
| category | agent_workflow |
| status | proposed |
| spec_readiness | ready |
| project evidence | `tools/doc_governor/cli.py`、`package.json`、`DOCS_INDEX.md`、AGENTS workflow |
| reference inspiration | RDP-002/RDP-004/RDP-018 的 command registry、lazy reference loading 和 active docs handoff |
| target state | 按任务类型声明允许读取、禁止读取、允许命令和禁止命令；reference clone 只在验证具体 RDP 时打开 |
| validation strategy | doc governor/static checks、manual scope review；本阶段不运行 build/test/install |
| risk | command matrix 漂移 |
| acceptance criteria | 不新增并行 roadmap；不把 Markdown workflow 当 enforcement；命令矩阵必须回到 active docs 或 doc governor |

### FE-009 Active Docs Handoff and Compatibility Checklist

| Field | Content |
| --- | --- |
| category | docs_governance |
| status | proposed |
| spec_readiness | ready |
| project evidence | `AGENTS.md`、`DOCS_INDEX.md`、`BACKLOG.md` / `DELIVERY_PLAN.md` 边界、capability preservation 证据 |
| reference inspiration | RDP-015/RDP-018 的 versioned workflow evolution；reference release notes 是 `release_note_claim` |
| target state | 后续 FE 进入 active docs、BACKLOG、DELIVERY_PLAN 或 ADR；compatibility checklist 只记录兼容风险，不声称 migration automation |
| validation strategy | diff check、active docs registry review、route/capability snapshot review |
| risk | checklist 被误当测试 |
| acceptance criteria | 不新增 parallel plan；release notes 不写成 migration；所有后续 Spec Kit entry 都有 active docs handoff |

## 7. Research Items

### FE-010 Role / JD-Specific Practice Routing Discovery

| Field | Content |
| --- | --- |
| category | research |
| status | research |
| spec_readiness | not_ready |
| project evidence | feedback score/confidence 和 JD binding partial evidence；role drill map `project_evidence_missing` |
| reference inspiration | RDP-007/RDP-010/RDP-013 的 rubric calibration、role drill 和 cross-surface consistency |
| target state | 先研究 JD category、target role、question category 与 practice path 的最小映射 |
| validation strategy | design brief、golden examples、manual rubric review |
| risk | 被误写成自动 calibration 或 outcome correlation |
| acceptance criteria | 不进入实现；不声明 role drill engine；先明确 human labels、golden cases 和边界 |

### FE-012 Transcript and Input Quality Gate Discovery

| Field | Content |
| --- | --- |
| category | research |
| status | research |
| spec_readiness | not_ready |
| project evidence | transcript ingestion、storage、privacy、fixture、parser tests 均为 `project_evidence_missing` |
| reference inspiration | RDP-008 的 transcript quality gate；参考为 `design-only` |
| target state | 研究 transcript input model、privacy、fixture、quality gate 和 parser ownership |
| validation strategy | discovery brief、fixture plan、privacy review |
| risk | 偷渡 transcript ingestion |
| acceptance criteria | 不创建 transcript API 或 parser；只定义研究问题和证据计划 |

### FE-013 Outcome Drift and Calibration Boundary Discovery

| Field | Content |
| --- | --- |
| category | research |
| status | research |
| spec_readiness | not_ready |
| project evidence | outcome log、用户授权、correlation method 均为 `project_evidence_missing` |
| reference inspiration | RDP-012 的 outcome drift boundary；参考 calibration docs 是 `design-only` |
| target state | 定义 outcome 数据分类、consent/privacy、non-claim wording 和不足数据状态 |
| validation strategy | privacy/design review、manual policy review |
| risk | 误写成录用预测或 live-provider quality |
| acceptance criteria | 不实现 outcome prediction；不宣称评分与真实结果相关；先有 consent 和 privacy 边界 |

### FE-014 Project-Native Coaching State Lifecycle Research

| Field | Content |
| --- | --- |
| category | research |
| status | research |
| spec_readiness | not_ready |
| project evidence | 统一 coaching state schema、migration、archive rules 为 `project_evidence_missing` |
| reference inspiration | RDP-001；`coaching_state.md` 和 schema migration 是 `schema_like_design` |
| target state | 盘点 project-native state owner、update trigger、retention/archive 和迁移需求 |
| validation strategy | state inventory、schema brief、governance review |
| risk | 复制 `coaching_state.md` 绕过现有 DB/API/privacy 边界 |
| acceptance criteria | 不复制参考 schema；不生成 migration；只输出 project-native research brief |

### FE-015 Bounded Challenge Protocol Policy

| Field | Content |
| --- | --- |
| category | research |
| status | research |
| spec_readiness | not_ready |
| project evidence | product UX opt-in、stop condition、safety copy、resolution 均不足 |
| reference inspiration | RDP-014 的 bounded challenge protocol；参考为 `design-only` |
| target state | 当前拒绝无边界 challenge protocol；若未来重启，必须先有 opt-in、安全文案和停止规则 |
| validation strategy | policy review、UX safety review |
| risk | 无边界强压用户 |
| acceptance criteria | phase3_decision 为 rejected；不进入 Spec Kit；不进入实现 |

## 8. Deferred Items

### FE-011 Storybank to Assets Lifecycle Discovery

| Field | Content |
| --- | --- |
| category | deferred |
| status | deferred |
| spec_readiness | not_ready |
| project evidence | Assets 有类比面，但 storybank lifecycle、story schema、retirement tests 为 `project_evidence_missing` |
| reference inspiration | RDP-009 的 storybank lifecycle；参考 storybank 是 `design-only` / `schema_like_design` |
| target state | 判断是否扩展 Assets 或新增 Story/Experience model |
| validation strategy | asset mapping brief、privacy review、schema proposal |
| risk | 误称 Assets 已实现 storybank |
| acceptance criteria | 不进入当前 Spec；不声称 storybank 已存在；先完成 Assets mapping decision |

## 9. Rejected Items

| FE | Rejected Scope | Reason |
| --- | --- | --- |
| FE-015 | 直接复制参考 Skill 的 challenge protocol 到产品反馈或练习流 | 缺少用户 opt-in、stop condition、安全文案和 resolution；当前只能保留 bounded policy research，占位不实现 |

## 10. Execution Phases

| Phase | FE Items | Gate |
| --- | --- | --- |
| Phase 4A Guardrail Spec | FE-001, FE-002, FE-007, FE-009 | 先保护 non-claim、contract drift、examples seed 和 active docs handoff |
| Phase 4B Workbench / Polish Product Spec | FE-003, FE-004, FE-005 | 只在项目已有 partial evidence 上细化用户路径 |
| Phase 4C Workflow Governance Spec | FE-008 | command matrix 与 lazy reading packet 需回到治理入口 |
| Phase 4D Confirmation or Research | FE-006, FE-010, FE-011, FE-012, FE-013, FE-014, FE-015 | 人工确认、研究或拒绝，不进入实现 |

## 11. Documentation Refresh Rules

1. 本 inventory 不是 active requirement、delivery plan、BACKLOG 或 ADR。
2. proposed FE 进入后续 Spec Kit 前，必须回读 `BACKLOG.md`、`DELIVERY_PLAN.md` 和相关 active docs。
3. research / deferred / rejected 项不得写入 implementation task。
4. reference Skill 的 Markdown workflow、schema_like_design、examples 和 release notes 必须保持 reference inspiration，不得升级为 project executable evidence。
5. 后续若要把 FE 变成 active 任务，必须通过 `docs/03-delivery/BACKLOG.md`；若涉及阶段，必须通过 `docs/03-delivery/DELIVERY_PLAN.md`。

## 12. Commit Policy

本阶段不执行 `git add`、`git commit` 或 `git push`。后续若提交，commit 只应包含：

- `docs/feature-enhancement/03_feature_enhancement_inventory.md`
- `.codex/feature-enhancement/feature_enhancement_inventory.yaml`

若 `git status --short --untracked-files=all` 出现其他文件状态，必须停止并报告。

## 13. Spec Kit Entry Rules

| Rule | Content |
| --- | --- |
| 可进入 Spec Kit | `phase3_decision=proposed` 且 `spec_readiness=ready` 或明确可收敛的 `partial` |
| 需要人工确认 | `phase3_decision=needs_confirmation` |
| 不可进入 Spec Kit | `research`、`deferred`、`rejected` |
| 最小首批建议 | FE-001 + FE-002 |
| 禁止 | 不得把 FE inventory 当 Spec；不得把 examples 当 tests；不得把 release notes 当 migration |

## 14. Codex Goal Conversion Rules

1. Codex Goal 只能从已人工审查通过的 proposed FE 转换。
2. 每个 Goal 必须只覆盖一个 FE 或一个明确子集。
3. Goal 必须列出 allowlist、forbidden files、验证命令和 non-claim boundary。
4. `project_evidence_missing` 的 FE 不得转换为 implementation Goal。
5. fake、replay、deterministic、default-off 只能作为 regression evidence，不能作为 live-provider quality。

## 15. Human Review Checklist

- [ ] 每个 FE 是否包含 project evidence、reference inspiration、target state、validation strategy、category、status、spec_readiness、risk、acceptance criteria。
- [ ] NEW_FROM_REFERENCE 且缺项目证据的项是否都不是 proposed。
- [ ] design-only、schema_like_design、examples、release_note_claim 是否均未被写成 executable implementation。
- [ ] fake / replay / deterministic / default-off 是否均未被写成 live-provider quality。
- [ ] proposed FE 是否可以先从 FE-001/FE-002 开始。
- [ ] FE-006 是否需要人工确认现有 surfaces 范围。
- [ ] FE-010 到 FE-015 是否仍保持 research/deferred/rejected。

## 16. Open Questions

1. FE-006 的 existing-surface consistency 是否只覆盖 Resume/Job/Assets/Polish，还是需要排除 Assets 中尚未完成的 story-like 用法。
2. FE-003 和 FE-004 是否同一 Spec Kit specification，还是拆成 Workbench UI 与 Polish backend/input readiness 两个 spec。
3. FE-005 correction capture 的最小用户动作是标记不准、补充事实、提交 correction note，还是三者分阶段。
4. FE-008 command matrix 是进入 doc governor，还是先进入 active docs governance 文档。
5. FE-010 role/JD-specific routing 是否有可用 human label 或 golden case 来源。
6. FE-011 storybank 是否未来映射到 Assets，还是需要独立 Story/Experience model。
7. FE-012 transcript 是否属于当前产品边界。
8. FE-013 outcome tracking 是否有合法稳定的数据来源和用户授权模型。

## 17. Next Step Recommendation

最建议先进入 Spec Kit 的是 FE-001 和 FE-002，理由是它们保护所有后续候选的 claim boundary 和 API/frontend contract boundary，且项目证据最充分。第二批再进入 FE-003、FE-004 和 FE-005；FE-006 先做人工确认；FE-010 到 FE-015 不进入实现。
