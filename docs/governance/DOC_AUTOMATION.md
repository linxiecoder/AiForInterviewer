# 文档治理自动化规则

## 1. 目标与当前范围

- 本文档定义本地 `doc-governor` 的自动化边界。
- 当前已落地并冻结 Phase 1A：结构化底座、白名单扫描、bootstrap 输出、模板/占位符识别。
- 当前同时定义 Phase 2A / Phase 2B / Phase 3A 的 contract，用于后续实现、验证与回归测试对齐。
- 当前最小闭环覆盖三条链路：
  - `bootstrap-state` 的白名单结构化扫描
  - `DOC_STATE.yaml` 的 validate / evaluate / render / confirm
  - 面向 `design/spec` 与 `plan/implementation` 文档的 round + Codex packet 工作流
- 当前不做：
  - 自动调用 Codex CLI 并自动应用变更
  - 自动批准文档状态
  - 从 Markdown 正文直接导入 confirmed state

### 1.1 当前能力分层

为避免把规划写成现状，本文档中的能力边界固定分为三类：

- 已接入主链：
  - `bootstrap-state`、`validate-state`、`evaluate-state`、`render-report`、`confirm-transition`
  - `init-official-state`
  - `show-history`、`summarize-history`
  - `preflight-open-window`、`open-window`、`plan-open-window`
  - document round 相关的 `plan-round`、`generate-round-template`、`apply-round`、`update-round-status`、`generate-codex-packet`
- 已实现但仍属独立检查器 / 待接线能力：
  - `tools/doc_governor/asset_checks.py`
  - `tools/doc_governor/language_check.py`
  - 一部分 requirement / asset / compliance 扩展结构
- 规划中的对象模型或输出契约：
  - 更完整的 requirement / governance / curated examples / runtime artifacts 注册区
  - 更完整的 asset/compliance 摘要与 render 展示
  - `MTxx_yy` 命名迁移及历史别名体系

后文若描述 requirement / asset / compliance / language governance / render 扩展，必须明确标注属于哪一类，不能默认视为“主链当前已自动生效”。

## 2. 真值优先级

当前结构化真值优先级固定为：
1. `docs/governance/DOC_STATE.yaml`
2. `doc-governor` 的 diagnostics / evaluate / round / packet 结果
3. Markdown 正文叙述

注意：
- `docs/governance/DOC_STATE.bootstrap.yaml` 只是 bootstrap 输出，不是正式真值。
- bootstrap 文件不得被直接当成 readiness / candidate / maturity / document status 的最终结论。
- `confirm-transition` 负责 confirmed business state 的正式审批写回；round lifecycle 还会维护 document tracking 字段，例如 `active_round_id`、`last_round_id`。

## 3. 白名单扫描来源

Phase 1A 的 `repo_scan` 仍只允许读取以下来源：
- 文件系统中的 `docs/modules/**`
- 根目录 `OPEN_QUESTIONS.md` 结构化表
- 根目录 `TASK_INDEX.md` 结构化表

Phase 1A 明确禁止：
- 从正文 prose 推断 maturity / readiness / candidate / review
- 从正文 prose 推断 `active_working_doc`
- 从非白名单 Markdown 段落导入共享契约真值

## 4. Official State 与 Document Entity 边界

- `documents` 一级治理对象只存在于 `docs/governance/DOC_STATE.yaml`。
- 当前只支持两类 document entity：
  - `design`
  - `plan`
- document entity 必须显式登记：
  - `meta.doc_type`
  - `meta.path`
  - `meta.required_sections`
  - `meta.relations`
- 允许从正文提取的事实仅包括：
  - heading 树
  - 必备章节命中情况
  - 显式 `OQ-*` / `Mxx` / 文档路径引用
  - `TODO/TBD/待确认/待补充` 等占位标记
- 不允许从正文直接导入：
  - `ready / blocked / approved / implementation-ready`
  - `candidate`
  - `maturity`
  - `active_round_id`
  - 任意 confirmed state

## 5. Bootstrap 输出与失败策略

默认输出固定为：
- `docs/governance/DOC_STATE.bootstrap.yaml`
- `docs/governance/BOOTSTRAP_REPORT.md`

固定约束：
- 若输出文件已存在且未显式传 `--overwrite`，bootstrap 必须失败。
- bootstrap 无论如何不得写入或覆盖 `docs/governance/DOC_STATE.yaml`。
- 只要任意子任务命中 `implementation_doc.exists=true 且 template_like=false`，bootstrap 就必须整体失败，并且不得写出半可信的 `DOC_STATE.bootstrap.yaml`。

## 6. Evaluate Command Contract

Phase 2A `evaluate-state` 是只读命令：
- Command 只输出结构化 JSON，不写任何状态文件。
- 它不会修改 `DOC_STATE.bootstrap.yaml` 或 `DOC_STATE.yaml`。
- PyYAML 是读取 `DOC_STATE*.yaml` 的必需依赖。
- `delta_summary`（含 blocker 增减、review_required 变化、readiness 变化）仅用于本轮讨论优先级，不可替代人工确认与 `confirm-transition` 审核。
- `documents`、`governance_rounds`、`rounds_summary` 都属于 evaluate 输出的一部分，但仍然只是解释层，不是 confirmed state。

推荐主入口：

```powershell
python -m tools.doc_governor.cli evaluate-state --input docs/governance/DOC_STATE.yaml
```

## 7. Render Command Contract

- `render-report --evaluate-json <PATH>` 是主入口。
- `render-report --state <PATH>` 是 evaluate 的 wrapper，不得重写 evaluate 规则。
- 默认输出路径是 `docs/governance/DOC_GOVERNOR_REPORT.md`。
- `--report-path` 只允许写到 `docs/governance/` 下，且不得指向 `DOC_STATE.yaml` 或 `DOC_STATE.bootstrap.yaml`。
- `render-report` 只输出解释性 Markdown，不能直接驱动 `confirm-transition`。
- `## Next Round Agenda` 只输出建议性议程，不可直接替代审批与状态写回流程。
- 当前 render 主链输出范围以 `summary / modules / subtasks / documents / oqs / open rounds / round delta / next round agenda / diagnostics notes` 为准；requirement / asset / compliance 摘要与来源分类展示尚未成为当前主链固定输出。

## 8. Round Lifecycle Contract

当前 round 生命周期固定为：

1. `plan-round`
2. `generate-round-template`
3. `generate-codex-packet`
4. 人工执行 Codex CLI
5. `update-round-status --status review`
6. `confirm-transition`
7. `update-round-status --status closed`

固定 round 状态：
- `open`
- `in_progress`
- `review`
- `closed`

固定 round 结构最少包括：
- `round_id`
- `workflow`
- `topic`
- `scope`
- `status`
- `opened_at`
- `opened_by`
- `decision_refs`
- `target_documents`
- `required_evidence_refs`
- `exit_criteria`
- `writeback_items`

## 9. Codex Packet Contract

Windows 本地统一使用：

```powershell
C:\Users\Administrator\AppData\Roaming\npm\codex.cmd exec
```

当前不支持 `codex.ps1`。

`generate-codex-packet` 固定生成三类产物：
- `docs/governance/packets/<round_id>.packet.json`
- `docs/governance/packets/<round_id>.prompt.md`
- `docs/governance/packets/<round_id>.exec.txt`

packet 必须至少包含：
- 本轮目标
- 目标文档
- 允许修改范围
- 禁止修改范围
- 治理约束
- 必须引用的 evidence / decision
- exit criteria
- 回写建议

## 10. confirm-transition Contract

- 默认输入文件是 `docs/governance/DOC_STATE.yaml`，若不存在直接失败。
- `confirm-transition` 只允许写入 `docs/governance/DOC_STATE.yaml`，禁止写入或覆盖 `DOC_STATE.bootstrap.yaml`。
- `module/subtask` 仍沿用原字段边界。
- `document` 当前只允许在 `--proposed-changes` 中提交：
  - `maturity`
  - `status`
  - `review_status`
  - `blocker_refs`
  - `active_round_id`
- `last_transition_id`、`last_confirmed_at`、`last_confirmed_by` 仅由系统在 approve 时写入，不允许在 proposed_changes 输入中携带。
- 当传入 `--round-id` 时，`--reason` 必须包含 `Decision:` 锚点。
- OQ `gate_policy_source=bootstrap_default` 不能作为自动通过 `candidate/readiness` 推进的充分依据；仅作为 review 依据之一。

## 11. 环境假设

- 当前 `doc-governor` 依赖本地 Python 环境可导入 `yaml`（PyYAML）。
- 当前不提供 YAML 解析/写入的自研 fallback。
- 若依赖缺失，CLI 必须 fail-fast。

检查命令：

```powershell
python -X utf8 -c "import yaml"
python -m tools.doc_governor.cli --help
```

## 12. 资产治理、语言治理与扩展规划边界

以下补充约束用于覆盖 requirement / 资产治理 / 合规检查与 official state 初始化边界。为避免把规划误写成现状，本节明确区分“当前已接入主链”“已实现但仍属独立检查器 / 待接线能力”“规划中的对象模型或输出契约”。

### 12.1 当前已接入主链的能力

当前主链已稳定接入的能力包括：

- `bootstrap-state` 的白名单结构化扫描与 bootstrap 输出
- `validate-state`、`evaluate-state`、`render-report`、`confirm-transition`
- `init-official-state`
- `show-history`、`summarize-history`
- `preflight-open-window`、`open-window`、`plan-open-window`
- document round 相关的 `plan-round`、`generate-round-template`、`apply-round`、`update-round-status`、`generate-codex-packet`

其中与 requirement / asset / compliance 直接相关、且当前已进入主链的边界仅包括：

- `requirement_scan` 会在当前仓库结构下生成最小 requirement 根对象，并复用根目录 requirement 索引簇
- `DOC_STATE.yaml` 中若已经存在 requirement 级 `asset_slots` / `compliance` 等事实，`evaluate-state` 可以消费这些事实参与 gate
- `evaluate-state` 仍然是只读评估命令，不写回任何 state 文件
- `render-report` 只渲染当前 evaluate payload 中已经存在且主链支持的摘要，不额外推断 requirement / asset / compliance 结论

当前主链下，task 对象的正式容器仍是 `subtasks`，命名规则仍以 `STxx_yy` 为准；`implementation_ready` 还受 `implementation_doc_state`、`formal_window_open`、`blocker_refs` 等正式状态约束，不能仅靠文档等级或人工描述推出。

### 12.2 已实现但仍属独立检查器 / 待接线能力

当前仓库内已经存在以下实现，但它们不应被描述成“默认已由主链自动执行”：

- `tools/doc_governor/asset_checks.py`
- `tools/doc_governor/language_check.py`
- 一部分更细粒度的 requirement / asset / compliance 数据结构与测试

因此，下列能力目前只能视为独立检查器能力、待接线能力，或局部已实现但尚未成为 `scan_repo -> bootstrap -> evaluate-state -> render-report` 主链默认行为：

- orphan / stale / ungoverned 文档检查
- 更完整的父子索引检查
- 更完整的命名合规检查
- 对正式文档的语言合规扫描
- module / task 级资产治理摘要的自动汇总
- 将 `asset:*` / `policy:*` blocker 全量并入当前主链 gate

这些能力可以作为后续接线目标或独立诊断来源，但当前不得在报告或治理文档中写成“已经自动阻断主链放行”。

### 12.3 规划中的对象模型与输出契约

以下内容目前属于规划方向，不得作为当前 schema、validate、evaluate、render 的既成事实：

- requirement / governance / curated examples / runtime artifacts 的完整受管注册区
- `asset_policy`、`asset_summary`、`compliance` 的全对象统一 schema
- `render-report` 中 requirement / asset / compliance 摘要的固定区块
- `render-report` 中对 `official state`、`runtime artifacts`、`curated examples` 的显式来源分区
- `MTxx_yy` 命名迁移、`legacy_aliases`、`historical_container=true` 等历史兼容体系

当前代码真值仍是：

- requirement：当前最小主链按现有 requirement 索引簇工作
- module：`Mxx`
- task / subtask：`STxx_yy`
- task 对象容器：`subtasks`
- typed blocker refs：继续按当前 schema 校验

若后续要推进 `MTxx_yy`、完整资产注册区或更强 render 契约，应先同步修改 `schema.py`、`validate.py`、`evaluate.py`、`render.py` 以及对应测试，再回写本文件。

### 12.4 当前 render、asset、compliance 的真实边界

当前 `render-report` 的真实边界如下：

- `render-report --evaluate-json <PATH>` 是主入口
- `render-report --state <PATH>` 只是共享 evaluate 路径的 wrapper
- 报告当前主链输出范围以 `summary / modules / subtasks / documents / oqs / open rounds / round delta / next round agenda / diagnostics notes` 为准
- 报告当前不会自动新增 requirement / asset / compliance 摘要区块
- 报告当前不会按三类来源固定分栏显示 `official state`、`runtime artifacts`、`curated examples`

因此，任何关于“asset governance 已完整纳入 render 报告”“language compliance 已在 render 中固定展示”“报告已显式分离三类来源”的描述，都只能作为规划项，不能作为当前行为描述。

### 12.5 文档语言规则（强制）

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

该规则属于正式项目协作约束，不是可选写作建议。

### 12.6 OQ bootstrap 默认值与 evaluate 边界

- `bootstrap-state` 必须为每个 OQ 保留 `gate_level`、`resolution_policy`、`status`、`affects`。
- 来源优先级固定为：
  - 优先读取 `OPEN_QUESTIONS.md` 结构化列中的显式值
  - 仅在 OQ policy 字段缺失时补默认值：
    - `gate_level = observe_only`
    - `resolution_policy = proposed_default_ok`
- 缺失 policy 字段时，只应产出一个聚合 warning：`BOOTSTRAP_OQ_POLICY_DEFAULT_APPLIED`，不应按 OQ 逐条刷告警。
- `evaluate-state` 仍是只读报告命令，不得在评估阶段内部补写 OQ 默认值；若缺字段，应在 validate 阶段先报错或告警。

### 12.7 `init-official-state` 补充约束

- 推荐命令入口：`python -m tools.doc_governor.cli init-official-state`
- 默认输入文件为 `docs/governance/DOC_STATE.bootstrap.yaml`
- 输出文件固定为 `docs/governance/DOC_STATE.yaml`，不提供替代输出路径
- 默认不覆盖已存在的 official state；如需替换，必须显式传 `--force-overwrite`
- official state 初始化时会复制 bootstrap 中允许继承的结构化事实，并为 confirmed state 填充工厂默认值；不会自动导入 evaluate 结论
- `last_transition_id`、`last_confirmed_at`、`last_confirmed_by` 不从 bootstrap 导入
- `init-official-state` 不写入 `transition_history.jsonl`

### 12.8 `confirm-transition` 补充约束

- 默认输入文件为 `docs/governance/DOC_STATE.yaml`，若不存在直接失败
- `confirm-transition` 只允许写入 `docs/governance/DOC_STATE.yaml`，禁止写入或覆盖 `docs/governance/DOC_STATE.bootstrap.yaml`
- `--proposed-changes` 仅允许提交当前 confirm 代码支持的 confirmed 字段
- `last_transition_id`、`last_confirmed_at`、`last_confirmed_by` 仅由系统在 approve 时写入，不允许在 `proposed_changes` 输入中携带
- `candidate_status` 提升到更高态时必须提供至少一条 `--evidence-ref`
- 当 OQ `gate_policy_source=bootstrap_default` 时，不能单独支撑 `candidate` 或 `readiness` 的批准路径，只能作为 review 输入之一
