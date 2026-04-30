---
title: 2026-04-27-document-system-refactor-plan
type: note
permalink: ai-for-interviewer/archive/docs/superpowers/plans/2026-04-27-document-system-refactor-plan
---

# AI 模拟面试项目全量文档体系重构计划

> 本文是步骤 1 / 计划冻结产物，只为步骤 2 提供可执行输入。本文不执行移动、归档、删除、引用修改、状态写回、formal window open、implementation packet、业务代码实现、`git add`、`commit` 或 `push`。

## 1. 总体结论

当前文档体系已经完成 Workbench MVP Design Canon 迁移，但仍存在四类结构问题：

1. `docs/superpowers/plans/**` 同时承载 planning、task、process、bridge、历史跳转，目录职责混杂。
2. 根目录入口文档同时承担索引、当前事实源摘要、过程状态和推进建议，存在职责混合风险。
3. 模块需求文档仍引用旧 P1 跳转路径作为历史来源，虽然已标注历史语义，但活动文档仍包含过时路径。
4. ST13 任务文档与 `2026-04-25-workbench-mvp-task-remap.md` 被 `DOC_STATE.yaml` 正式引用，不能在不改状态层的步骤 2 中移动。

当前 Workbench MVP 设计事实源应继续统一为：

- `docs/design/workbench-mvp/README.md`
- `docs/design/workbench-mvp/scope.md`
- `docs/design/workbench-mvp/information-architecture.md`
- `docs/design/workbench-mvp/object-model-rag-multiround-backend.md`
- `docs/design/workbench-mvp/scoring-review-export-dod.md`

但若要严格区分需求与设计，步骤 2 还应从 `docs/design/workbench-mvp/scope.md` 和根目录 OQ/DD 中抽出产品范围、需求边界、验收口径，建立 `docs/requirements/workbench-mvp/` 作为需求事实源；设计目录只保留设计事实与设计约束。

## 2. 前置检查记录

| 命令 | 结果 |
| --- | --- |
| `git status --short` | 无输出，工作区干净 |
| `git rev-parse --abbrev-ref HEAD` | `main` |
| `git rev-list --left-right --count origin/main...HEAD` | `0 0` |
| `python -m tools.doc_governor.cli validate-state --input docs/governance/DOC_STATE.yaml` | `ok=true,error=0,warning=0` |
| `python -m tools.doc_governor.cli evaluate-state --input docs/governance/DOC_STATE.yaml` | `ok=true,error=0,warning=0`；`rounds_open_count=0`；`documents_blocked_count=0`；`formal_window_open=false` 仍阻断 implementation-ready |
| `git diff --check` | 无输出 |

本轮未执行 `git add`、未提交、未推送。

## 3. 文档盘点范围

扫描范围：

- 根目录 `*.md`
- `docs/**/*.md`
- `archive/**/*.md`

排除范围：

- `.git/**`
- `node_modules/**`
- `__pycache__/**`
- `.pytest_cache/**`
- `tests/**`
- 其他本地缓存目录

盘点计数：

| 分组 | Markdown 数量 |
| --- | ---: |
| 根目录 | 11 |
| `docs/design/**` | 5 |
| `docs/governance/**` | 8 |
| `docs/modules/**` 模块级 | 90 |
| `docs/modules/**/sub_modules/**` 子任务级 | 60 |
| `docs/superpowers/plans/*.md` | 23 |
| `docs/superpowers/plans/st13-task-packages/**` | 8 |
| `docs/superpowers/specs/**` | 1 |
| `docs/*.md` | 3 |
| `archive/**` | 2 |
| 合计 | 211 |

## 4. 文档类型总览表

| type | active docs count | archive candidates count | main entry | problem summary |
| --- | ---: | ---: | --- | --- |
| requirement | 约 21 | 0 | `OPEN_QUESTIONS.md`；目标新增 `docs/requirements/workbench-mvp/` | 产品范围和验收口径仍散落在设计 canon、OQ/DD 和根文档摘要中，需要抽出为需求事实源 |
| design | 约 79 | 4 | `docs/design/workbench-mvp/README.md`；`docs/modules/**/MODULE_*_DESIGN.md` | Workbench MVP 设计事实源已归位；旧 W13 bridge docs 应归档，避免再被误用 |
| planning | 约 8 | 12+ | `PLAN_LATEST.md`；`docs/superpowers/plans/2026-04-25-current-repo-execution-plan.md` | `docs/superpowers/plans/**` 混有过程记录、桥接文档、任务双文档 |
| task | 约 49 | 0 | `TASK_INDEX.md`；`MODULE_TASK_INDEX.md`；ST13 双文档 | ST13 双文档位于 plans 目录但被 `DOC_STATE.yaml` 引用，步骤 2 不可移动 |
| process | 约 14 | 12+ | `EXECUTION_LOG.md`；`MODULE_EXECUTION_LOG.md`；治理报告 | 历史迁移、state-write、readiness audit、candidate evaluation 仍在 plans 目录 |
| governance | 约 12 | 0 | `AGENTS.md`；`docs/DOC_GOVERNANCE.md`；`docs/governance/DOC_AUTOMATION.md` | 规则文档职责基本清晰；生成报告不得当作状态真值 |
| index | 约 7 | 0 | `README.md`；`AGENTS.md`；`MODULE_INDEX.md`；`TASK_INDEX.md` | 索引文档仍含较多事实摘要，应压缩为导航和 canonical source 清单 |
| archive | 2 | N/A | `archive/**` | archive 当前只含旧 P1 正文；还缺旧 W13 bridge、旧计划、完成过程文档归档 |

## 5. 重要文档分类表

| path | inferred current type | expected type | active? | should archive? | should move? | should split? | current fact source? | stale? | mixed responsibility? | canonical replacement | reason | notes |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| `README.md` | index + fact summary | index | yes | no | no | yes | no | no | yes | canonical source list only | 当前包含事实源说明和历史归档提示 | 步骤 2 压缩正文事实 |
| `AGENTS.md` | governance + index | governance + index | yes | no | no | yes | partly | no | yes | keep rules; index only as navigation | 同时含规则和长索引 | archive 文档应放归档分组，不放活动设计/计划分组 |
| `PLAN_LATEST.md` | planning + current summary | planning | yes | no | no | yes | no | no | yes | `docs/requirements/**` + `docs/design/**` | 当前推进入口可保留事实源清单，不承载事实正文 | 被用户作为当前入口，保留 |
| `TASK_INDEX.md` | task + index | task | yes | no | no | yes | task source only | no | yes | `DOC_STATE.yaml` + ST13 docs | 可保留任务 ID、依赖、required docs、readiness | 不写设计正文 |
| `MODULE_INDEX.md` | index + planning summary | index | yes | no | no | yes | no | no | yes | module docs | 保留模块导航、状态摘要、下轮建议 | 不写模块设计正文 |
| `OPEN_QUESTIONS.md` | requirement + decision state | requirement | yes | no | no | yes | requirement/OQ source | no | yes | `docs/requirements/workbench-mvp/` for normalized requirements | OQ 归并和 confirmed/rejected/superseded 可保留 | 不再承载长产品正文 |
| `DESIGN_DECISIONS.md` | design decision + index | requirement/design decision | yes | no | no | yes | decision source | no | yes | design docs + requirement docs | 决策可保留，设计正文应在 design docs | 保留 DD 表 |
| `DOCUMENT_PROGRESS.md` | process + index | process/index | yes | no | no | yes | no | no | yes | `EXECUTION_LOG.md` for detail | 保留当前进展摘要，不承载设计事实 | archive 引用只可标历史 |
| `DOCUMENT_MATURITY.md` | governance metric + index | governance/index | yes | no | no | yes | no | no | yes | `DOC_STATE.yaml` + maturity table | 保留成熟度，不承载事实正文 | archive 文档不能作为当前事实 |
| `EXECUTION_LOG.md` | process | process | yes | no | no | no | no | partly | no | none | 可保留历史路径作为过程记录 | allowed exception: 历史执行记录可引用旧路径但必须标历史 |
| `TECHNICAL_STANDARDS.md` | governance/design constraints | governance | yes | no | no | maybe | partly | no | maybe | `docs/design/**` for product-specific design | 技术标准保留约束，不写产品设计正文 | 步骤 2 只做引用复核 |
| `docs/design/workbench-mvp/README.md` | design index | design index | yes | no | no | no | design index | no | no | self | 当前 Design Canon 入口 | 保留 |
| `docs/design/workbench-mvp/scope.md` | requirement + design boundary | design + requirement source | yes | no | no | yes | yes today | no | yes | split to `docs/requirements/workbench-mvp/scope.md` plus retained design boundary | 产品范围、边界、DoD 口径更像 requirement | 用户需确认是否步骤 2 创建 requirements 目录 |
| `docs/design/workbench-mvp/information-architecture.md` | design | design | yes | no | no | no | yes | no | no | self | IA / 用户旅程正式设计事实 | 保留 |
| `docs/design/workbench-mvp/object-model-rag-multiround-backend.md` | design | design | yes | no | no | no | yes | no | no | self | 对象模型/RAG/多轮/后端边界 | 保留 |
| `docs/design/workbench-mvp/scoring-review-export-dod.md` | design + acceptance constraints | design | yes | no | no | maybe | yes | no | partial | `docs/requirements/workbench-mvp/acceptance.md` for acceptance summary | DoD/验收口径需与需求层分离 | 设计约束保留，验收口径抽摘要 |
| `docs/superpowers/plans/2026-04-25-workbench-mvp-scope.md` | bridge | archive | yes | yes | yes | no | no | yes | no | `docs/design/workbench-mvp/scope.md`; target requirement doc | 已是迁移来源，不应继续在 active plans | 移入 archive |
| `docs/superpowers/plans/2026-04-25-workbench-mvp-ia-user-journey.md` | bridge | archive | yes | yes | yes | no | no | yes | no | `docs/design/workbench-mvp/information-architecture.md` | 已是迁移来源 | 移入 archive |
| `docs/superpowers/plans/2026-04-25-workbench-mvp-object-model-rag-multiround-backend.md` | bridge | archive | yes | yes | yes | no | no | yes | no | `docs/design/workbench-mvp/object-model-rag-multiround-backend.md` | 已是迁移来源 | 移入 archive |
| `docs/superpowers/plans/2026-04-25-workbench-mvp-scoring-review-export-dod.md` | bridge | archive | yes | yes | yes | no | no | yes | no | `docs/design/workbench-mvp/scoring-review-export-dod.md` | 已是迁移来源 | 移入 archive |
| `docs/superpowers/specs/2026-04-20-ai-interview-p1-design.md` | jump stub | archive/delete-if-empty | yes | yes | yes | no | no | yes | no | `archive/docs/superpowers/specs/2026-04-20-ai-interview-p1-design.md`; `docs/design/workbench-mvp/` | 旧 P1 正文已在 archive | 清引用后删除空壳或归档 stub |
| `docs/superpowers/plans/2026-04-20-ai-interview-p1-implementation.md` | jump stub | archive/delete-if-empty | yes | yes | yes | no | no | yes | no | `archive/docs/superpowers/plans/2026-04-20-ai-interview-p1-implementation.md`; current plan | 旧实现计划正文已在 archive | 清引用后删除空壳或归档 stub |
| `archive/docs/superpowers/specs/2026-04-20-ai-interview-p1-design.md` | archive | archive | no | already | no | no | no | yes | no | `docs/design/workbench-mvp/` | 历史材料 | 不作为当前事实源 |
| `archive/docs/superpowers/plans/2026-04-20-ai-interview-p1-implementation.md` | archive | archive | no | already | no | no | no | yes | no | current plan/task docs | 历史材料 | 不作为当前事实源 |
| `docs/superpowers/plans/2026-04-25-workbench-mvp-design-canon-plan.md` | completed planning/process | archive | yes | yes | yes | no | no | yes | yes | current design canon + this refactor plan | 计划已被执行，当前内容仍写“步骤 2 未执行”等旧事实 | 归档并从 active index 移除 |
| `docs/superpowers/plans/2026-04-25-current-repo-execution-plan.md` | planning + process + fact summary | planning | yes | no | blocked | yes | plan source only | partial | yes | `DOC_STATE.yaml` path locked; requirements/design docs for facts | `DOC_STATE.yaml` document entity 引用此路径 | 只可原地瘦身，不移动 |
| `docs/superpowers/plans/2026-04-25-workbench-mvp-backlog-roadmap.md` | planning | planning | yes | no | no | no | no | no | no | self | backlog/roadmap 可保留 | 清理 archive 后续事项引用 |
| `docs/superpowers/plans/2026-04-25-workbench-mvp-task-remap.md` | task plan + state process | task/planning | yes | no | blocked | yes | task source in state | partial | yes | `TASK_INDEX.md` + `DOC_STATE.yaml` + ST13 docs | `DOC_STATE.yaml` 大量引用此路径/source_doc | 步骤 2 只更新 stale wording，不移动 |
| `docs/superpowers/plans/2026-04-25-workbench-mvp-state-write-*.md` | state write process | archive/process | yes | yes | yes | no | no | yes | no | `EXECUTION_LOG.md` summary + archive | 已完成阶段性 state write 记录 | 归档为过程材料 |
| `docs/superpowers/plans/2026-04-25-workbench-mvp-st13-*.md` | readiness/process/planning | archive/process or task | yes | mostly yes | mostly yes | no | no | partial | partial | `TASK_INDEX.md` + ST13 double docs | 多数是完成的审计/评估/准备方案 | 不移动 state-referenced ST13 double docs |
| `docs/superpowers/plans/st13-task-packages/ST13_20/**` | task docs | task | yes | no | blocked | no | task doc source | no | no | self | `DOC_STATE.yaml` 引用 design/implementation doc paths | 不能移动 |
| `docs/superpowers/plans/st13-task-packages/ST13_21/**` | task docs | task | yes | no | blocked | no | task doc source | no | no | self | `DOC_STATE.yaml` 引用 design/implementation doc paths | 不能移动 |
| `docs/superpowers/plans/st13-task-packages/ST13_24/**` | task docs | task | yes | no | blocked | no | task doc source | no | no | self | `DOC_STATE.yaml` 引用 design/implementation doc paths | 不能移动 |
| `docs/superpowers/plans/st13-task-packages/ST13_25/**` | task docs | task | yes | no | blocked | no | task doc source | no | no | self | `DOC_STATE.yaml` 引用 design/implementation doc paths | 不能移动 |
| `docs/modules/M01-M10/MODULE_REQUIREMENTS.md` | requirement + historical refs | requirement | yes | no | blocked directory | yes | module requirement source | partial | yes | `docs/requirements/workbench-mvp/` + archive paths | 10 份仍引用旧 P1 active jump path | 改历史引用到 archive 或新需求源 |
| `docs/modules/M01-M10/MODULE_DESIGN.md` | design | design | yes | no | blocked directory | no | module design source | no | no | self | 10 份模块设计 | 不移动 |
| `docs/modules/M01-M10/MODULE_API_DESIGN.md` | design | design | yes | no | blocked directory | no | module API design source | no | no | self | 10 份 API 设计 | 不移动 |
| `docs/modules/M01-M10/MODULE_SCHEMA_DESIGN.md` | design | design | yes | no | blocked directory | no | module schema design source | no | no | self | 10 份 schema 设计 | 不移动 |
| `docs/modules/M01-M10/MODULE_LOGIC_DESIGN.md` | design | design | yes | no | blocked directory | no | module logic design source | no | no | self | 10 份 logic 设计 | 不移动 |
| `docs/modules/M01-M10/MODULE_TASK_INDEX.md` | task index | task | yes | no | blocked directory | maybe | module task source | partial | yes | `TASK_INDEX.md` + module docs | 旧 STxx/MTxx 只可历史化，不可激活 | 不移动 |
| `docs/modules/M01-M10/MODULE_OPEN_QUESTIONS.md` | requirement/process | requirement | yes | no | blocked directory | maybe | module OQ source | partial | yes | `OPEN_QUESTIONS.md` + module docs | 历史 MQ/OQ 应保持 historical/superseded | 不移动 |
| `docs/modules/M01-M10/MODULE_EXECUTION_LOG.md` | process | process | yes | no | blocked directory | no | no | partial | no | none | 模块过程日志可保留历史路径 | 不移动 |
| `docs/modules/M01-M10/sub_modules/**/SUBTASK_DESIGN.md` | subtask design | task/design | yes | no | no | no | no formal source | partial | maybe | module docs + `TASK_INDEX.md` | 30 份旧子任务设计多为历史/骨架 | 不移动；当前不放行 |
| `docs/modules/M01-M10/sub_modules/**/SUBTASK_IMPLEMENTATION.md` | subtask implementation plan | task/process | yes | no | no | maybe | no | partial | maybe | formal packet only after gate | 30 份实施文档不能代表 implementation-ready | 不移动；当前不放行 |
| `docs/DOC_GOVERNANCE.md` | governance | governance | yes | no | no | no | governance source | no | no | self | 人工治理总则 | 保留 |
| `docs/SUBTASK_DOC_TEMPLATES.md` | governance/template | governance | yes | no | no | no | template source | no | no | self | 子任务模板真值 | 保留 |
| `docs/project-language-rules.md` | governance | governance | yes | no | no | no | language source | no | no | self | 语言规则 | 保留 |
| `docs/governance/DOC_AUTOMATION.md` | governance | governance | yes | no | no | no | automation source | no | no | self | 自动化边界 | 保留 |
| `docs/governance/DOC_STATE.yaml` | state truth | governance state | yes | no | no | no | official state source | no | no | self | 本轮和步骤 2 均不得修改 | 非 Markdown，但为阻断依据 |
| `docs/governance/BOOTSTRAP_REPORT.md` | generated process | process/governance output | yes | no | no | no | no | no | no | `DOC_STATE.yaml` for truth | 解释性报告，不是真值 | 不手改生成报告 |
| `docs/governance/DOC_GOVERNOR_REPORT.md` | generated process | process/governance output | yes | no | no | no | no | no | no | `DOC_STATE.yaml` for truth | 解释性报告，不是真值 | 不手改生成报告 |
| `docs/governance/DOC_GOVERNOR_TOOL_DEBT.md` | governance/tool backlog | governance/planning | yes | no | no | no | no | no | partial | self | 只记录工具债 | 不反向改产品事实 |

## 6. 文档重构动作表

| path | current type | target type | action in step 2 | target path | canonical replacement | reason | risk | notes |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| `docs/requirements/workbench-mvp/README.md` | none | requirement index | create | same | self | 建立需求层入口 | 新增目录需用户确认 | 不复制设计正文 |
| `docs/requirements/workbench-mvp/scope-and-acceptance.md` | none | requirement | create | same | self | 抽出产品范围、需求边界、验收口径 | 可能与现有 `scope.md` 形成重复 | 需要同步引用规则 |
| `docs/design/workbench-mvp/scope.md` | design + requirement | design | rewrite | same | requirement doc + self | 保留设计边界，抽离需求正文 | 抽离过度可能丢上下文 | 只做职责分离，不改 confirmed 事实 |
| 四份旧 W13 bridge docs | bridge | archive | archive | `archive/docs/superpowers/plans/2026-04-25/` | `docs/design/workbench-mvp/**` | 不再作为 current design fact source | 过程追溯路径变化 | 先更新活动引用 |
| 旧 P1 specs / implementation jump stubs | jump | archive/delete-if-empty | delete-if-empty or archive stub | `archive/docs/superpowers/...` | archive 正文 + current canon | active 目录不应保留过时跳转 | 删除可能影响断链保护 | 必须先 `rg` 清零非历史引用 |
| `2026-04-25-workbench-mvp-design-canon-plan.md` | completed plan | archive | archive | `archive/docs/superpowers/plans/2026-04-25/` | current design canon + this plan | 已完成且含旧步骤状态 | 若仍被索引引用需同步 | 只作为历史计划 |
| `2026-04-25-current-repo-execution-plan.md` | planning + fact | planning | rewrite | same | requirement/design canon | 被 `DOC_STATE.yaml` 引用不能移动 | 误改 required sections | 保留 required sections |
| `2026-04-25-workbench-mvp-task-remap.md` | task + state process | task/planning | rewrite / blocked move | same | `TASK_INDEX.md` + `DOC_STATE.yaml` | 被 `DOC_STATE.yaml` 引用 source_doc | 移动会破坏状态层 | 清理“四份 W13 唯一事实源”旧措辞 |
| `docs/superpowers/plans/st13-task-packages/**` | task docs | task | keep / blocked move | same | self | 被 `DOC_STATE.yaml` 引用 doc paths | 移动需状态写回 | 只改 stale wording |
| completed state-write / readiness / candidate docs | process/planning | archive | archive | `archive/docs/superpowers/plans/2026-04-25/` | `EXECUTION_LOG.md` summary + state truth | 已完成过程文档不应占 active plans | 可能仍有活动索引 | 先更新 AGENTS/PLAN/TASK refs |
| root index docs | mixed | index/planning/requirement/process | rewrite | same | canonical tables | 压缩事实正文 | 大范围 markdown churn | 不改事实，只改职责 |
| module requirement docs | requirement + historical refs | requirement | rewrite | same | new requirement doc + archive refs | 旧 P1 active jump path需清理 | 模块引用多 | 保持历史语义 |
| module task / subtask docs | task/history | task | rewrite minimal | same | `TASK_INDEX.md` + design canon | 不激活旧任务 | 误读为 ready | 保持 not ready |

## 7. canonical 当前事实源计划表

| domain | current source today | target canonical source | action required | notes |
| --- | --- | --- | --- | --- |
| 正式结构化状态 | `docs/governance/DOC_STATE.yaml` | same | keep | 步骤 2 不修改 |
| Workbench MVP 产品需求 / 范围 / 验收 | `docs/design/workbench-mvp/scope.md`、`OPEN_QUESTIONS.md`、`DESIGN_DECISIONS.md` | `docs/requirements/workbench-mvp/scope-and-acceptance.md` + OQ/DD decision index | create + split | 需用户确认是否创建 requirement 目录 |
| Workbench MVP 设计事实 | `docs/design/workbench-mvp/**` | same | keep + minor references | 五份 Design Canon 保留 |
| 当前执行计划 | `PLAN_LATEST.md`、`docs/superpowers/plans/2026-04-25-current-repo-execution-plan.md` | same paths, planning-only | rewrite | current-repo path 被 DOC_STATE 锁定 |
| 正式任务入口 | `TASK_INDEX.md`、`DOC_STATE.yaml`、ST13 双文档 | same | keep | ST13 docs 暂不迁移目录 |
| 模块事实 | `docs/modules/M01-M10/**` | same directories | keep + stale ref cleanup | 模块目录被 DOC_STATE 引用 |
| 过程记录 | `EXECUTION_LOG.md`、`MODULE_EXECUTION_LOG.md`、generated reports | same + archive completed process docs | archive old process docs | 过程记录不得作为当前事实源 |
| 治理规则 | `AGENTS.md`、`docs/DOC_GOVERNANCE.md`、`docs/governance/**` | same | keep | 生成报告不是真值 |
| 文档索引 | `README.md`、`AGENTS.md`、`MODULE_INDEX.md`、`TASK_INDEX.md` | same | rewrite | 只保留导航与 canonical source |
| 历史材料 | `archive/**` | `archive/**` | expand | archive 不参与当前事实源 |

## 8. 归档计划表

| old path | archive target path | reason | replaced by | active references to remove | blocked by DOC_STATE? | step 2 action |
| --- | --- | --- | --- | --- | --- | --- |
| `docs/superpowers/plans/2026-04-25-workbench-mvp-scope.md` | `archive/docs/superpowers/plans/2026-04-25/2026-04-25-workbench-mvp-scope.md` | 旧 W13 bridge | requirement scope + `docs/design/workbench-mvp/scope.md` | design-canon-plan refs; process exceptions allowed | no | archive |
| `docs/superpowers/plans/2026-04-25-workbench-mvp-ia-user-journey.md` | `archive/docs/superpowers/plans/2026-04-25/2026-04-25-workbench-mvp-ia-user-journey.md` | 旧 W13 bridge | `docs/design/workbench-mvp/information-architecture.md` | design-canon-plan refs; process exceptions allowed | no | archive |
| `docs/superpowers/plans/2026-04-25-workbench-mvp-object-model-rag-multiround-backend.md` | `archive/docs/superpowers/plans/2026-04-25/2026-04-25-workbench-mvp-object-model-rag-multiround-backend.md` | 旧 W13 bridge | `docs/design/workbench-mvp/object-model-rag-multiround-backend.md` | design-canon-plan refs; process exceptions allowed | no | archive |
| `docs/superpowers/plans/2026-04-25-workbench-mvp-scoring-review-export-dod.md` | `archive/docs/superpowers/plans/2026-04-25/2026-04-25-workbench-mvp-scoring-review-export-dod.md` | 旧 W13 bridge | `docs/design/workbench-mvp/scoring-review-export-dod.md` | design-canon-plan refs; process exceptions allowed | no | archive |
| `docs/superpowers/plans/2026-04-25-workbench-mvp-design-canon-plan.md` | `archive/docs/superpowers/plans/2026-04-25/2026-04-25-workbench-mvp-design-canon-plan.md` | 完成计划且含旧状态 | this plan + Design Canon | AGENTS / plans index refs | no | archive |
| `docs/superpowers/specs/2026-04-20-ai-interview-p1-design.md` | already `archive/docs/superpowers/specs/2026-04-20-ai-interview-p1-design.md`; optional stub archive | 旧跳转空壳 | archive + current requirement/design | root/module refs | no | delete-if-empty or archive stub |
| `docs/superpowers/plans/2026-04-20-ai-interview-p1-implementation.md` | already `archive/docs/superpowers/plans/2026-04-20-ai-interview-p1-implementation.md`; optional stub archive | 旧跳转空壳 | archive + current plan/task | root/module refs | no | delete-if-empty or archive stub |
| `docs/superpowers/plans/2026-04-25-workbench-mvp-state-write-plan.md` | `archive/docs/superpowers/plans/2026-04-25/` | 完成 state-write 计划 | `EXECUTION_LOG.md` + `DOC_STATE.yaml` | AGENTS/PLAN refs | no | archive |
| `docs/superpowers/plans/2026-04-25-workbench-mvp-state-write-stage*.md` | `archive/docs/superpowers/plans/2026-04-25/` | 完成过程记录 | `EXECUTION_LOG.md` + `DOC_STATE.yaml` | AGENTS/PLAN refs | no | archive |
| ST13 readiness/review/candidate/precheck plans | `archive/docs/superpowers/plans/2026-04-25/` | 完成评估/准备过程 | `TASK_INDEX.md` + state truth | AGENTS/PLAN/TASK refs | no | archive unless actively required |
| `docs/superpowers/plans/2026-04-25-workbench-mvp-task-remap.md` | N/A | 状态层引用 | `DOC_STATE.yaml` source_doc | none | yes | blocked; keep path |
| `docs/superpowers/plans/st13-task-packages/**` | N/A | 状态层引用 task docs | self | none | yes | blocked; keep path |
| `docs/superpowers/plans/2026-04-25-current-repo-execution-plan.md` | N/A | 状态层 document entity 引用 | self | none | yes | blocked; keep path |

## 9. 引用替换计划表

| old reference | new reference | files to update | reason | allowed exceptions | step 2 action |
| --- | --- | --- | --- | --- | --- |
| `docs/superpowers/plans/2026-04-25-workbench-mvp-scope.md` | `docs/requirements/workbench-mvp/scope-and-acceptance.md` for requirement facts; `docs/design/workbench-mvp/scope.md` for design facts | root docs, active plans, module docs | 旧 bridge 不作事实源 | `EXECUTION_LOG.md` historical trace | replace active refs |
| `docs/superpowers/plans/2026-04-25-workbench-mvp-ia-user-journey.md` | `docs/design/workbench-mvp/information-architecture.md` | active docs | 旧 bridge 不作事实源 | process logs | replace active refs |
| `docs/superpowers/plans/2026-04-25-workbench-mvp-object-model-rag-multiround-backend.md` | `docs/design/workbench-mvp/object-model-rag-multiround-backend.md` | active docs | 旧 bridge 不作事实源 | process logs | replace active refs |
| `docs/superpowers/plans/2026-04-25-workbench-mvp-scoring-review-export-dod.md` | `docs/design/workbench-mvp/scoring-review-export-dod.md` and requirement acceptance doc | active docs | 旧 bridge 不作事实源 | process logs | replace active refs |
| `docs/superpowers/specs/2026-04-20-ai-interview-p1-design.md` | archive path for historical citation; `docs/design/workbench-mvp/` for current design | module requirements, root docs, plans | old active jump path stale | none unless explicitly redirect stub remains | replace |
| `docs/superpowers/plans/2026-04-20-ai-interview-p1-implementation.md` | archive path for historical citation; current plan/task docs for current work | module requirements, root docs, plans | old active jump path stale | none unless explicitly redirect stub remains | replace |
| `archive/**` in active design/planning sections | move to archive/history section or remove from active index | `AGENTS.md`, `README.md`, maturity/progress docs | archive 不应作为当前入口 | archive section is allowed | rewrite index grouping |
| `四份 W13` / `W13 唯一事实源` | `Workbench MVP 正式设计事实源` or `历史 W13 bridge` | active docs | 避免误读旧 W13 plans | process logs may preserve historical wording | replace when current-facing |
| `current fact source` pointing to plans | requirement/design canonical paths | active docs | 消除重复事实源 | process logs | replace |

## 10. 引用命中分类摘要

| pattern | representative hits | classification | step 2 disposition |
| --- | --- | --- | --- |
| `archive/` | `README.md`、`AGENTS.md`、`PLAN_LATEST.md`、`DOCUMENT_*`、governance docs | current-valid when explicitly historical; archive-misused when listed under active design/planning | 移入归档分组或压缩 |
| old W13 bridge paths | `EXECUTION_LOG.md`、`2026-04-25-workbench-mvp-design-canon-plan.md` | process/history or obsolete-active-doc | archive design-canon plan; process log保留历史 |
| old P1 active paths | module `MODULE_REQUIREMENTS.md` 10 份等 | stale-reference | 改 archive path or current canonical |
| `当前事实源` / `唯一事实源` | root docs、design canon、task-remap、module docs | current-valid or stale wording | 当前-facing 统一指向 canonical |
| `W13 唯一事实源` in module execution logs/subtasks | module process/subtask docs | process-in-design-doc or historical wording | 保留历史时标注 historical；否则改正式设计事实源 |

## 11. 混合职责清理计划

| file | mixed responsibilities | target primary type | content to keep | content to move / remove | target destination | step 2 action |
| --- | --- | --- | --- | --- | --- | --- |
| `README.md` | index + fact summary + archive notes | index | repo入口、canonical source 清单 | 大段事实说明 | requirement/design docs | rewrite |
| `AGENTS.md` | rules + active index + archive index | governance/index | rules、必要索引 | archive 文档从 active 设计/计划区移出 | archive section | rewrite |
| `PLAN_LATEST.md` | plan + current facts + process | planning | 当前阶段、下一步、阻断 | 设计/需求正文、历史细节 | requirement/design/process docs | rewrite |
| `TASK_INDEX.md` | task index + historical explanation | task | task id、依赖、required docs、readiness、blockers | 设计正文、历史蓝图解释 | design/requirements/archive | rewrite minimal |
| `OPEN_QUESTIONS.md` | OQ + requirement facts | requirement/OQ | open/proposed/confirmed/rejected/superseded 问题状态 | 产品范围长正文 | requirements doc | split |
| `DESIGN_DECISIONS.md` | decision index + design facts | decision index | confirmed DD、影响范围、source ref | 大段设计事实 | design docs | rewrite minimal |
| `DOCUMENT_PROGRESS.md` | process + fact summary | process/index | 当前阶段、完成项、阻断 | current design fact body | design/requirements | rewrite |
| `DOCUMENT_MATURITY.md` | maturity + current source | governance/index | maturity table | archive/current facts expansion | canonical source table | rewrite |
| `docs/design/workbench-mvp/scope.md` | requirement + design | design | 设计边界、设计约束、与设计 canon 关系 | 产品范围/验收口径的规范化正文 | `docs/requirements/workbench-mvp/scope-and-acceptance.md` | split |
| `docs/superpowers/plans/2026-04-25-current-repo-execution-plan.md` | planning + process + current facts | planning | current repo execution plan、验证命令、下一步 | design事实正文、旧蓝图说明 | requirements/design/archive | rewrite in place |
| `docs/superpowers/plans/2026-04-25-workbench-mvp-task-remap.md` | task plan + state dry-run + old W13 wording | task/planning | task remap、state-blocked relation | 过程结论长文、旧 facts-source wording | process archive / canonical refs | rewrite in place; no move |
| module `MODULE_REQUIREMENTS.md` | requirement + historical source citations | requirement | module requirements and historical trace | old active jump paths | archive paths or requirement canon | rewrite |
| `SUBTASK_IMPLEMENTATION.md` files | implementation plan + readiness impression | task/process | acceptance criteria, required tests, blockers when present | design facts and readiness claims | subtask design / DOC_STATE gate | rewrite only if in allowed set |

## 12. 步骤 2 禁止范围

步骤 2 也不得触碰：

- `docs/governance/DOC_STATE.yaml`，除非用户另开 state-blocked 专项窗口；本次不改。
- `docs/governance/DOC_STATE.bootstrap.yaml`
- `tools/**`
- `tests/**`
- `apps/**`
- `infra/**`
- business implementation
- formal window
- implementation packet
- `git add`
- `git commit`
- `git push`

## 13. 步骤 2 执行输入包

### 13.1 created files

建议创建：

- `docs/requirements/workbench-mvp/README.md`
- `docs/requirements/workbench-mvp/scope-and-acceptance.md`

不创建新的 `docs/design/**` 正式设计文档；现有五份 Design Canon 保留。

### 13.2 moved / archived files

建议移动到 `archive/docs/superpowers/plans/2026-04-25/`：

- 四份旧 W13 bridge docs
- `2026-04-25-workbench-mvp-design-canon-plan.md`
- completed state-write stage docs
- completed ST13 readiness/review/candidate/precheck docs

建议处理旧跳转空壳：

- `docs/superpowers/specs/2026-04-20-ai-interview-p1-design.md`
- `docs/superpowers/plans/2026-04-20-ai-interview-p1-implementation.md`

处理方式由用户确认：`delete-if-empty` 或移动 stub 到 archive。

明确不移动：

- `docs/superpowers/plans/2026-04-25-current-repo-execution-plan.md`
- `docs/superpowers/plans/2026-04-25-workbench-mvp-task-remap.md`
- `docs/superpowers/plans/st13-task-packages/**`
- `docs/modules/M01-M10/**`

### 13.3 rewritten files

允许步骤 2 重写的活动文档：

- `README.md`
- `AGENTS.md`
- `PLAN_LATEST.md`
- `TASK_INDEX.md`
- `MODULE_INDEX.md`
- `OPEN_QUESTIONS.md`
- `DESIGN_DECISIONS.md`
- `DOCUMENT_PROGRESS.md`
- `DOCUMENT_MATURITY.md`
- `TECHNICAL_STANDARDS.md` only if stale refs are found
- `docs/design/workbench-mvp/scope.md`
- `docs/design/workbench-mvp/scoring-review-export-dod.md` only for acceptance/source wording
- `docs/superpowers/plans/2026-04-25-current-repo-execution-plan.md`
- `docs/superpowers/plans/2026-04-25-workbench-mvp-task-remap.md`
- `docs/superpowers/plans/2026-04-25-workbench-mvp-backlog-roadmap.md`
- module `MODULE_REQUIREMENTS.md` and `MODULE_TASK_INDEX.md` only for stale refs and historical wording
- state-referenced ST13 double docs only for stale source wording, not path moves

### 13.4 reference replacements

1. current requirement references -> `docs/requirements/workbench-mvp/scope-and-acceptance.md`
2. current design references -> `docs/design/workbench-mvp/**`
3. old W13 bridge references -> archive path only when historical
4. old P1 references -> archive path only when historical; otherwise current canonical
5. `archive/**` references in active indexes -> archive section only
6. `W13 唯一事实源` -> `Workbench MVP 正式设计事实源` unless historical/process

### 13.5 validation commands

步骤 2 开始前：

```powershell
git status --short
git rev-parse --abbrev-ref HEAD
git rev-list --left-right --count origin/main...HEAD
python -m tools.doc_governor.cli validate-state --input docs/governance/DOC_STATE.yaml
python -m tools.doc_governor.cli evaluate-state --input docs/governance/DOC_STATE.yaml
git diff --check
```

步骤 2 完成后：

```powershell
git status --short
git diff --check
python -m tools.doc_governor.cli validate-state --input docs/governance/DOC_STATE.yaml
python -m tools.doc_governor.cli evaluate-state --input docs/governance/DOC_STATE.yaml
```

引用审计：

```powershell
rg -n "archive/" README.md AGENTS.md PLAN_LATEST.md TASK_INDEX.md MODULE_INDEX.md OPEN_QUESTIONS.md DESIGN_DECISIONS.md DOCUMENT_PROGRESS.md DOCUMENT_MATURITY.md docs --glob "!archive/**"
rg -n "docs/superpowers/plans/2026-04-25-workbench-mvp-(scope|ia-user-journey|object-model-rag-multiround-backend|scoring-review-export-dod)\\.md" . --glob "!archive/**"
rg -n "docs/superpowers/specs/2026-04-20-ai-interview-p1-design\\.md|docs/superpowers/plans/2026-04-20-ai-interview-p1-implementation\\.md" . --glob "!archive/**"
rg -n "四份 W13|W13 唯一事实源|旧 W13|旧 P1|历史蓝图归档|已迁移|已废弃|迁移至|跳转" README.md AGENTS.md PLAN_LATEST.md TASK_INDEX.md MODULE_INDEX.md OPEN_QUESTIONS.md DESIGN_DECISIONS.md DOCUMENT_PROGRESS.md DOCUMENT_MATURITY.md docs --glob "!archive/**"
rg -n "current fact source|当前事实源|唯一事实源|事实源|source of truth|Design Canon|DesignCanon|canonical" README.md AGENTS.md PLAN_LATEST.md TASK_INDEX.md MODULE_INDEX.md OPEN_QUESTIONS.md DESIGN_DECISIONS.md DOCUMENT_PROGRESS.md DOCUMENT_MATURITY.md docs --glob "!archive/**"
```

禁止范围检查：

```powershell
git diff --name-only -- docs/governance/DOC_STATE.yaml docs/governance/DOC_STATE.bootstrap.yaml tools tests apps infra
rg -n "formal_window_open: true|implementation_ready: true|candidate_status: candidate|implementation packet|已生成 implementation packet|已打开 formal window|可直接进入实现" README.md AGENTS.md PLAN_LATEST.md TASK_INDEX.md MODULE_INDEX.md OPEN_QUESTIONS.md DESIGN_DECISIONS.md DOCUMENT_PROGRESS.md DOCUMENT_MATURITY.md docs --glob "!archive/**"
```

### 13.6 forbidden scope checks

步骤 2 发现以下任一情况必须停止：

- `DOC_STATE.yaml` 出现 diff
- `DOC_STATE.bootstrap.yaml` 出现 diff
- `tools/**`、`tests/**`、`apps/**`、`infra/**` 出现 diff
- 任何文本宣称 formal window 已打开
- 任何文本宣称已生成 implementation packet
- 任何文本宣称已可直接进入业务实现
- `validate-state` 或 `evaluate-state` 不为 `ok=true,error=0,warning=0`

### 13.7 rollback plan

未提交前回退：

```powershell
git status --short
git restore -- README.md AGENTS.md PLAN_LATEST.md TASK_INDEX.md MODULE_INDEX.md OPEN_QUESTIONS.md DESIGN_DECISIONS.md DOCUMENT_PROGRESS.md DOCUMENT_MATURITY.md TECHNICAL_STANDARDS.md
git restore -- docs/design/workbench-mvp docs/superpowers/plans docs/modules
```

若创建了新 requirements 目录且需要回退，先确认路径再删除：

```powershell
Resolve-Path docs/requirements/workbench-mvp
Remove-Item -Recurse -Force docs/requirements/workbench-mvp
```

若移动到 archive 后需回退，优先用 `git restore -- <paths>` 恢复被移动文件；不得用 `git reset --hard`。

### 13.8 completion criteria

步骤 2 完成标准：

1. 需求、设计、规划、任务、过程、治理、索引、归档职责已在活动文档中分离。
2. Workbench MVP 需求事实源和设计事实源不重复承载同一正文。
3. 旧 W13 bridge docs 已归档或不再位于 active plans。
4. 旧 P1 active jump refs 已清理。
5. 活动索引不再把 archive 文档作为当前入口。
6. `DOC_STATE.yaml` 未修改。
7. state-blocked docs 未移动。
8. 未打开 formal window。
9. 未生成 implementation packet。
10. 未进入业务代码实现。
11. `validate-state` / `evaluate-state` 均 `ok=true,error=0,warning=0`。
12. `git diff --check` 无输出。
13. 未 `git add`、未 `commit`、未 `push`，除非用户另行明确授权。

## 14. 用户确认项

进入步骤 2 前必须确认：

1. 是否接受创建 `docs/requirements/workbench-mvp/`，把产品范围、需求边界和验收口径从设计/根文档中抽出。
2. 是否接受四份旧 W13 bridge docs 归档到 `archive/docs/superpowers/plans/2026-04-25/`。
3. 是否接受 `2026-04-25-workbench-mvp-design-canon-plan.md` 归档。
4. 是否接受 completed state-write / readiness / candidate / precheck docs 归档。
5. 旧 P1 active jump stubs 是 `delete-if-empty`，还是作为 redirect stub 移入 archive。
6. 是否允许步骤 2 改写根入口文档以压缩事实正文。
7. 是否允许步骤 2 最小改写模块 `MODULE_REQUIREMENTS.md` / `MODULE_TASK_INDEX.md` 的旧路径引用。
8. 是否存在暂不归档的例外文档。

## 15. 不确定项

| item | uncertainty | recommended default |
| --- | --- | --- |
| `docs/requirements/workbench-mvp/` 是否创建 | 当前仓库没有独立需求目录，但严格职责分离需要 | 创建 |
| 旧跳转 stub 是否删除 | 删除可减少过时活动路径，保留可防断链 | 若引用清零，`delete-if-empty`；否则移动到 archive redirect |
| generated reports 是否改写 | 报告由工具生成，不适合手改 | 不改，只在索引中标明非真值 |
| ST13 task docs 是否迁出 plans | 理想上应迁到 task 目录，但被 state 引用 | 本次不迁，另开 state migration |
| current-repo execution plan 是否移动 | 被 `DOC_STATE.yaml` document entity 引用 | 本次不迁，只原地瘦身 |

## 16. 步骤 1 完成声明

本步骤已完成计划冻结，且满足：

1. 未执行归档。
2. 未移动文件。
3. 未改引用。
4. 未修改设计正文。
5. 已输出文档分类表。
6. 已输出归档计划表。
7. 已输出引用替换计划表。
8. 已输出步骤 2 执行输入包。
9. 已列出不确定项。
10. 已明确需要用户确认后才能进入步骤 2。
11. 未 `git add`。
12. 未 `commit`。
13. 未 `push`。