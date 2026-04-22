# 文档治理自动化规则

## 1. 目标与当前范围

- 本文档定义本地 `doc-governor` 的自动化边界。
- 当前已落地并冻结 Phase 1A：结构化底座、白名单扫描、bootstrap 输出、模板/占位符识别。
- 当前同时定义 Phase 2A / Phase 2B / Phase 3A 的 contract，用于后续实现、验证与回归测试对齐。

## 2. 真值优先级

当前结构化真值优先级固定为：
1. `docs/governance/DOC_STATE.yaml`（正式真值，当前阶段保留）
2. `doc-governor` 的结构化 diagnostics / bootstrap 结果
3. Markdown 正文叙述

注意：
- `docs/governance/DOC_STATE.bootstrap.yaml` 只是 bootstrap 输出，不是正式真值。
- bootstrap 文件不得被直接当成 readiness / candidate / maturity 的最终结论。

## 3. 白名单扫描来源

Phase 1A 的 `repo_scan` 只允许读取以下来源：
- 文件系统中的 `docs/modules/**`
- 根目录 `OPEN_QUESTIONS.md` 结构化表
- 根目录 `TASK_INDEX.md` 结构化表

Phase 1A 明确禁止：
- 从正文 prose 推断 maturity / readiness / candidate / review
- 从正文 prose 推断 `active_working_doc`
- 从非白名单 Markdown 段落导入共享契约真值

## 4. Bootstrap 输出与失败策略

默认输出固定为：
- `docs/governance/DOC_STATE.bootstrap.yaml`
- `docs/governance/BOOTSTRAP_REPORT.md`

固定约束：
- 若输出文件已存在且未显式传 `--overwrite`，bootstrap 必须失败。
- bootstrap 无论如何不得写入或覆盖 `docs/governance/DOC_STATE.yaml`。
- 只要任意子任务命中 `implementation_doc.exists=true 且 template_like=false`，bootstrap 就必须整体失败，并且不得写出半可信的 `DOC_STATE.bootstrap.yaml`。

## 5. 空模板与假信号

Phase 1A 当前必须识别并拦截以下假信号：
- 空 `SUBTASK_IMPLEMENTATION.md` 模板
- PowerShell / 变量占位符残留
- 明显统一模板骨架残留

这些信号只可用于“阻止假成熟度导入”，不能正向提升 readiness。

## 6. 环境假设

- 当前 `doc-governor` 依赖本地 Python 环境可导入 `yaml`（PyYAML）。
- 当前不提供 YAML 解析/写入的自研 fallback。
- 若依赖缺失，CLI 必须 fail-fast，并输出 `BOOTSTRAP_PYYAML_UNAVAILABLE`。

检查命令：

```powershell
python -X utf8 -c "import yaml"
```

## Evaluate Command Contract
Phase 2A `evaluate-state` is read-only governance evaluation output.
- Command outputs structured JSON only and does not write any state files.
- It does not change DOC_STATE.bootstrap.yaml or DOC_STATE.yaml.
- PyYAML is required for reading DOC_STATE*.yaml inputs.
- `evaluate-state` 必须同时评估阶段 gate 输入与资产治理输入；后者至少覆盖 requirement / module / task / governance 文档资产、命名规则、目录规则、模板规则、索引关系和生命周期分类。
- `delta_summary`（含 blocker 增减、review_required 变化、readiness 变化，以及后续补充的 asset / compliance 变化）仅用于本轮讨论优先级，不可替代人工确认与 `confirm-transition` 审核。

## Phase 2 扩展：资产治理与协同治理

### 1. `doc_governance` 职责扩展

Phase 2 的 `doc_governance` 不得只被定义为 stage gate 引擎。对当前 `doc_governance` + Codex 协同流程而言，gate 判断本身依赖一套被治理的文档资产集合、固定命名/目录/模板约束、父子索引关系与明确生命周期边界；如果这些内容不受治理，`module_decomposition_ready`、`task_design_ready`、`implementation_ready` 会出现“语义上看起来通过、资产上其实不可交付”的假阳性。

因此，Phase 2 必须把 `doc_governance` 扩展为两类职责并列的机制：

- `artifact governance`：管理 requirement / module / task / governance 相关文档资产本身，确保文档存在、归位、被索引、受模板约束，并且没有孤立、过时、越权或未纳管资产。
- `policy governance`：管理这套协同机制依赖的命名规则、目录规则、模板规则、索引关系、生命周期分类以及哪些资产可以参与 gate、哪些资产只能作为参考或运行时产物。

在这一定义下，`doc-governor` 不是只对“文档内容成熟度”打分，而是对“Codex 协同机制产出的文档体系是否可治理、可审计、可持续放行”做统一判断。

### 2. 文档资产模型

Phase 2 应把以下产物都纳入统一资产模型，并为每类资产定义 `object_id`、`asset_class`、`canonical_path`、`owner_scope`、`parent_refs`、`template_ref`、`index_refs`、`lifecycle_class`、`gate_relevance`。

| 产物类型 | 作用 | 最小受管资产 | gate 角色 |
| --- | --- | --- | --- |
| requirement 文档 | 表达需求目标、范围、需求到 module/task 的分解关系 | 当前兼容模式下至少包括 `PLAN_LATEST.md`、`MODULE_INDEX.md`、`TASK_INDEX.md`；未来可收敛到 `docs/requirements/<RQxx>-<slug>/` | `module_decomposition_ready` 的上游输入 |
| module 文档 | 表达模块需求、设计、接口、数据、逻辑、任务拆解、依赖、日志、开放问题 | `MODULE_REQUIREMENTS.md`、`MODULE_DESIGN.md`、`MODULE_API_DESIGN.md`、`MODULE_SCHEMA_DESIGN.md`、`MODULE_LOGIC_DESIGN.md`、`MODULE_TASK_INDEX.md`、`MODULE_DEPENDENCIES.md`、`MODULE_OPEN_QUESTIONS.md`、`MODULE_EXECUTION_LOG.md` | `module_decomposition_ready`、`task_design_ready` 的主体输入 |
| task 文档 | 表达单个任务/子任务的设计与实施 | `SUBTASK_DESIGN.md`、`SUBTASK_IMPLEMENTATION.md`；当前 schema 可继续沿用 `subtasks` 作为 task 对象容器 | `task_design_ready`、`implementation_ready` 的主体输入 |
| governance 文档 | 表达治理规则、流程、索引、审批边界 | `AGENTS.md`、`docs/DOC_GOVERNANCE.md`、`docs/governance/DOC_AUTOMATION.md`、`docs/governance/DISCUSSION_WORKFLOW.md`、`docs/SUBTASK_DOC_TEMPLATES.md`、`DOCUMENT_MATURITY.md`、`DOCUMENT_PROGRESS.md`、`OPEN_QUESTIONS.md` | 为 gate、模板、审批和索引检查提供规则来源 |
| curated examples | 作为示例、样例、最佳实践或训练数据，帮助 Codex 对齐写法，但不充当正式真值 | 建议放在 `docs/governance/examples/curated/` 或测试 fixtures 中，并显式标注 `example_kind` | 默认不直接参与放行，只能作参考 |
| runtime artifacts | 运行时生成、评估中间结果、round 记录、报告和历史 | `DOC_STATE.bootstrap.yaml`、`DOC_GOVERNOR_REPORT.md`、`docs/governance/rounds/*.md`、`transition_history.jsonl`、evaluate JSON 输出 | 可提供 diagnostics / evidence，但不能冒充 official state |

三类生命周期必须显式区分：

- `official state`：正式真值或正式受管文档，能参与审批、索引和 gate。
- `runtime artifacts`：运行中间件、报告、历史、round 计划、bootstrap 输出；默认只读、不可直接替代正式状态。
- `curated examples`：人为整理的示例或样板；用于参考、训练和对齐，不直接作为放行证据。

### 3. 命名与目录规则

Phase 2 应为对象、文件和目录分别定义规范，并把这些规范从“人工约定”升级为“可检查规则”。

对象 ID 建议如下：

- requirement：`RQxx`，例如 `RQ01`。
- module：`Mxx`，例如 `M01`。
- task：优先使用 `MTxx_yy`；现有 `STxx_yy` 仅作为历史容器或兼容别名时保留，并必须在状态层显式标记 `legacy_aliases` / `historical_container=true`。
- open question：继续沿用 `OQ-xxx`。
- governance round：继续沿用 `R-YYYY-MM-DD` 或现有 round id 规范。

目录规则建议如下：

- requirement 官方资产：
  当前最小兼容实现可继续使用根目录 requirement 索引簇（如 `PLAN_LATEST.md`、`MODULE_INDEX.md`、`TASK_INDEX.md`）。
  后续若需要多 requirement 并存，再收敛到 `docs/requirements/<requirement_id>-<slug>/`。
- module 官方资产：固定在 `docs/modules/<module_id>-<slug>/`。
- task 官方资产：当前兼容实现继续使用 `docs/modules/<module_id>-<slug>/sub_modules/<task_id>-<slug>/`。
- governance 官方资产：固定在仓库根治理文档与 `docs/governance/`。
- curated examples：固定在 `docs/governance/examples/curated/` 或测试专用 fixtures 根，不得与 official docs 混放。
- runtime artifacts：固定在 `docs/governance/` 的受控输出路径下，例如 `DOC_STATE.bootstrap.yaml`、`DOC_GOVERNOR_REPORT.md`、`rounds/`、`transition_history.jsonl`，以及未来可选的 `evaluate/` 子目录。

文件名规则建议如下：

- 官方 slot 文件名必须固定且可枚举，不允许同义改名。
- 文件名中的 ID、父目录 ID、对象元数据中的 ID 必须可双向校验。
- runtime artifact 不得占用 official state 文件名，不得写入官方 slot 目录冒充正式文档。
- curated examples 必须通过目录位置或元数据显式表明“示例身份”，不能与正式模板同名同位。

#### 文档语言规则（强制）

对 `doc_governance` 与 Codex 协同机制产出的 requirement、module、task、plan、spec、runbook、governance 等正式项目文档，标题与正文默认必须使用中文。

允许保留英文的内容仅限必要技术标识，包括但不限于：

- 代码
- 命令
- 文件路径
- 配置键
- API / 类 / 函数 / 字段名
- 协议名、标准名、库名、框架名
- 难以自然翻译且翻译会降低准确性的专业术语

不允许出现以下情况：

- 使用英文作为文档主标题或章节标题
- 使用英文自然语言撰写大段正文
- 用英文描述本应中文表达的需求、技术方案、实施方案、结论

若需保留英文术语，优先采用“中文说明 + 英文原词”的写法。

该规则属于 `artifact governance` / `policy governance` 的正式资产治理规则之一，不是可选写作建议。

### 4. 资产检查规则

Phase 2 至少应新增以下五类检查，并将结果统一输出为结构化 diagnostics。

#### 存在性检查

- 检查每个受管对象在当前阶段所要求的官方 slot 是否存在。
- 缺少 requirement / module / task 的必需文档时，必须产生 blocker 级 diagnostic。
- runtime artifacts 和 curated examples 不可被计入官方存在性通过。

#### 模板完整性检查

- 检查文档是否匹配其 slot 对应模板的最小必填结构。
- 检查是否存在空模板、占位符残留、关键章节缺失、只复制模板骨架未填充等情况。
- 模板完整性检查必须区分“存在但不完整”和“存在且可作为下游输入”。

#### 父子索引检查

- requirement 必须能索引到其 module 集合。
- module 必须同时被 requirement 索引和全局 / 模块内任务索引引用。
- task 必须能从 `TASK_INDEX.md` 与所属 `MODULE_TASK_INDEX.md` 找到，且路径、父对象、依赖关系一致。
- governance 文档必须维持规则索引关系，避免模板、流程和状态规则失联。

#### 命名合规检查

- 检查对象 ID、目录名、文件名、索引引用名是否符合约定模式。
- 检查 module/task 目录中的 ID 与索引中的 ID 是否一致。
- 检查历史容器是否被错误地当成正式 task 使用。
- 检查 runtime artifact / curated example 是否误用正式命名。

#### 过时 / 孤立 / 未纳管文档检查

- 检查 governed roots 下是否存在未被任何对象注册或索引引用的文档。
- 检查索引里是否仍引用已经失效、迁移或历史冻结的路径。
- 检查是否存在“有文件、无对象归属”、“有对象、无索引关系”、“有目录、无生命周期标注”的资产。
- 检查历史容器文档是否已正确标记为 `historical` / `legacy_locked`，而不是继续被系统当作可放行资产。

#### 语言合规检查

- 对正式项目文档检查主标题、章节标题与正文自然语言是否默认使用中文。
- 对必要技术标识允许保留英文，但不得扩展成英文主标题、英文章节标题或英文大段正文。
- 语言不合规必须标记为 `artifact policy violation`，并记录到相应对象的 `compliance` / diagnostics。

建议把检查结果至少分为：

- `fatal`：直接阻断 gate。
- `warning`：不自动放行，需 review。
- `info`：记录治理债务，但不阻断当前轮次。

### 5. 与阶段 gate 的结合方式

Phase 2 起，gate 不再只由内容成熟度和 OQ 阻塞决定，还必须同时吸收资产检查结果。

`module_decomposition_ready` 必须同时满足：

- requirement 级官方索引簇存在且可解析。
- module 官方目录与必需 slot 存在。
- module 与 requirement / `MODULE_INDEX.md` / `TASK_INDEX.md` 的索引关系成立。
- 不存在 `fatal` 级命名违规、孤儿官方文档、未纳管 module 资产。
- 不存在未处理的正式文档语言违规。

`task_design_ready` 必须同时满足：

- 上游 `module_decomposition_ready` 已成立。
- task 官方目录与 `SUBTASK_DESIGN.md` 存在并通过模板完整性检查。
- task 能在全局 `TASK_INDEX.md` 与所属 `MODULE_TASK_INDEX.md` 双向定位。
- task 不依赖 runtime artifact 或 curated example 冒充正式设计输入。
- task 设计输入与 task 正式文档不存在未处理的语言违规。

`implementation_ready` 必须同时满足：

- 上游 `task_design_ready` 已成立。
- `SUBTASK_IMPLEMENTATION.md` 存在并通过模板完整性检查。
- 与该 task 相关的 official docs 没有 `fatal` 级资产问题。
- 任何 `runtime artifacts` 或 `curated examples` 都不能替代官方 implementation doc 或官方 state。
- 与该 task 相关的正式 requirement / module / task / plan / spec / runbook / governance 文档不存在未处理的语言违规。

建议采用统一组合逻辑：

- `gate_result = semantic_checks_pass AND required_asset_checks_pass`
- `review_required = semantic_review_required OR asset_warning_present`
- `blocker_refs` 允许引入 `asset:*` / `policy:*` 前缀，使 gate 报告能显式解释“为什么因为资产治理而不能放行”。
- 对语言不合规，建议统一生成 `policy:language_non_compliant` 或更细粒度的 `policy:language_non_compliant:<slot>` blocker/ref，用于阶段放行与收口判断。

### 6. 状态层如何表达

状态层需要同时表达对象状态、资产状态和规则合规状态，但三者职责不同。

- 对象状态：继续放在 `state.confirmed`，表达该对象当前被正式确认的 `maturity`、`candidate_status`、`review_status`、`readiness`、`blocker_refs`。
- 资产状态：放在 `facts.asset_slots` / `facts.asset_summary`，表达各官方 slot 的存在性、模板完整性、父子索引和生命周期分类。
- 规则合规状态：放在 `facts.compliance` / `facts.rule_checks`，表达命名、目录、索引、未纳管资产、历史容器映射等合规结果。

建议的最小结构如下：

```yaml
global_policy:
  paths:
    modules_root: docs/modules
    open_questions_doc: OPEN_QUESTIONS.md
    task_index_doc: TASK_INDEX.md
  asset_policy:
    requirement_roots:
      - .
    governance_roots:
      - docs/governance
    curated_example_roots:
      - docs/governance/examples/curated
    runtime_artifact_roots:
      - docs/governance
    id_patterns:
      requirement: ^RQ\\d{2}$
      module: ^M\\d{2}$
      task: ^(MT\\d{2}_\\d{2}|ST\\d{2}_\\d{2})$
requirements:
  RQ01:
    meta:
      canonical_scope: root_requirement_cluster
    facts:
      asset_slots: {}
      asset_summary: {}
      compliance: {}
    state:
      confirmed: {}
modules:
  M01:
    meta: {}
    facts:
      asset_slots: {}
      asset_summary: {}
      compliance: {}
    state:
      confirmed: {}
subtasks:
  MT01_01:
    meta:
      module_id: M01
    facts:
      asset_slots: {}
      asset_summary: {}
      compliance: {}
    state:
      confirmed: {}
governance_assets: {}
curated_examples: {}
runtime_artifacts: {}
```

其中有两条边界必须保持不变：

- `official state` 仍以 `DOC_STATE.yaml` 为正式真值。
- `evaluate-state` 仍只读，只能根据 `facts` 和规则计算 gate / diagnostics，不能把评估结果自动写回 `state.confirmed`。

### 7. 最小落地方案

最小可落地方案不应先做“全文档体系大迁移”，而应优先在当前仓库结构上补齐可治理能力，覆盖一个 requirement、2~3 个 module、每个 module 若干 task。

建议按以下范围落地：

1. 新增一个逻辑 requirement 对象，例如 `RQ01`，但先复用当前根目录 requirement 索引簇，不强制立即搬迁到 `docs/requirements/`。
2. 直接复用现有 `docs/modules/Mxx-*/` 目录和现有 module slot 规则。
3. task 对象先继续复用当前 `sub_modules/<task_id>-<slug>/` 目录和 `SUBTASK_*` 双文档，不在最小方案里强推目录重构。
4. 在状态 schema 中新增 requirement / governance / curated examples / runtime artifacts 的受管注册区，以及 `asset_policy`、`asset_slots`、`asset_summary`、`compliance` 结构。
5. 在 `repo_scan` / `validate` / `evaluate-state` 中先实现五类基础检查：
   - 存在性检查
   - 模板完整性检查
   - 父子索引检查
   - 命名合规检查
   - 过时 / 孤立 / 未纳管文档检查
6. 在 `evaluate-state` 输出中新增 requirement / asset / compliance 摘要，并把 `fatal` 资产问题并入 `blocker_refs` 与 gate 结论。
7. 在 `render-report` 中显式区分 `official state`、`runtime artifacts`、`curated examples` 三类结果来源，避免报告把中间产物写成正式结论。

这样做的收益是：

- 先支撑当前 `doc_governance` + Codex 协同机制，而不是停留在单纯 document round MVP。
- 先把“哪些文档应存在、应叫什么、应放哪、应如何互相索引、哪些只是运行时产物”治理清楚，再谈更大规模自动开窗或自动审批。
- 即使当前只覆盖 1 个 requirement、2~3 个 module 和若干 task，也能建立一套可扩展的资产治理骨架，后续再按对象类型扩展即可。

## OQ Bootstrap Defaults and Evaluate Boundary

- `bootstrap-state` must persist for every OQ entry: `gate_level`, `resolution_policy`, `status`, `affects`.
- Source priority is fixed:
  - explicit values from structured `OPEN_QUESTIONS.md` columns first;
  - fallback defaults only for missing OQ policy fields:
    - `gate_level = observe_only`
    - `resolution_policy = proposed_default_ok`
- Missing policy fields must emit only one aggregated warning `BOOTSTRAP_OQ_POLICY_DEFAULT_APPLIED` (not per-OQ warnings).
- `evaluate-state` is report-only and must not apply OQ policy defaults internally; missing policy fields should fail validation before evaluation.

## Render Command Contract

- `render-report --evaluate-json <PATH>` is the only primary render input.
- `render-report --state <DOC_STATE.bootstrap.yaml>` is an optional wrapper and must share the same evaluate path internally.
- `render-report` output is Markdown only and must summarize the current gate result plus asset-governance result; current Phase 2 minimum scope is `summary/modules/subtasks/oqs/diagnostics`, and once requirement / asset / compliance summaries land it must include those sections as well.
- `render-report` 的 `## Next Round Agenda` 仅输出建议性议程，不可直接替代 `confirm-transition` 的审批与状态写回流程。
- Default output path is `docs/governance/DOC_GOVERNOR_REPORT.md`.
- `--report-path` may only target files under `docs/governance/` and must not target official state files.
- The report must include fixed boundary notes stating it is report-only and not ready or ready-to-open status.
- 报告中必须显式区分 `official state`、`runtime artifacts`、`curated examples` 三类来源，避免把运行中间产物或示例误写成正式放行依据。

## init-official-state (Phase 3A.1) Contract

- Primary command: `python tools/doc_governor/cli.py init-official-state`.
- Default input file is `docs/governance/DOC_STATE.bootstrap.yaml`.
- Default output file is fixed to `docs/governance/DOC_STATE.yaml`; no alternate output paths are supported.
- `--force-overwrite` is disabled by default and required to replace an existing official state file.
- The official state copy includes:
  - `schema_version`
  - `global_policy`
  - `oqs` (with `gate_policy_source` preserved)
  - `modules[*].meta` / `modules[*].facts`
  - `subtasks[*].meta` / `subtasks[*].facts`
- `modules[*].state.confirmed` and `subtasks[*].state.confirmed` are initialized from factory defaults only (no auto-confirmed results import).
- `subtask.state.confirmed.implementation_doc_state` defaults to `missing`.
- `last_transition_id` / `last_confirmed_at` / `last_confirmed_by` are not imported from bootstrap.
- `init-official-state` does not write `transition_history.jsonl`.

## confirm-transition (Phase 3A) Contract
- 默认输入文件为 `docs/governance/DOC_STATE.yaml`，若不存在直接失败。
- `confirm-transition` 只允许写入 `docs/governance/DOC_STATE.yaml`，禁止写入/覆盖 `docs/governance/DOC_STATE.bootstrap.yaml`。
- `--proposed-changes` 仅允许 `maturity`、`candidate_status`、`review_status`、`readiness`、`blocker_refs`、`implementation_doc_state`。
- `last_transition_id`、`last_confirmed_at`、`last_confirmed_by` 仅由系统在 approve 时写入，不允许在 proposed_changes 输入中携带。
- `candidate_status` 提升到更高态（例如 none/observe -> candidate）必须提供至少一条 `--evidence-ref`。
- 当 OQ `gate_policy_source=bootstrap_default` 时，不能作为自动通过 `candidate/readiness` 推进的充分依据；仅作为 review 依据之一。
