# 项目协作规则

本文档是当前项目的高优先级协作入口，用于沉淀全局规则并索引核心文档。

## 1. 全局规则

### 1.1 文档语言规则

默认情况下，当前项目中的文档主体必须使用中文，代码与技术标识按常规技术规范保持英文。详细规则见：

- [项目语言规范](docs/project-language-rules.md)

### 1.2 文档索引规则

后续新增的正式项目文档，应先补充到本文档的索引中，再继续扩展内容，避免规则、设计和计划分散失管。

建议纳入索引的文档类型包括：

- 全局规范
- 产品设计稿
- 实现计划
- 开发约定
- 操作手册

### 1.3 文档治理规则

本仓库的文档治理细则定义在 [`DOC_GOVERNANCE.md`](docs/DOC_GOVERNANCE.md)。

当任务涉及以下任一事项时，必须先阅读并遵守 [`DOC_GOVERNANCE.md`](docs/DOC_GOVERNANCE.md)：
- 文档成熟度评估
- 文档进展更新
- 多 Codex 并行分工
- 模块文档完善
- 子任务文档完善
- 需求变更回写
- 共享契约冲突处理
- 子任务是否具备可实施条件的判断
- 具体文档模板定义不在本文件重复维护；若模板已有独立文件或独立索引，应以模板文件为准。

如果 `AGENTS.md` 与 [`DOC_GOVERNANCE.md`](docs/DOC_GOVERNANCE.md) 看似冲突：
- 目录结构、角色边界、全局总则以 `AGENTS.md` 为准
- 文档治理细节、成熟度规则、进展规则、回写规则以 [`DOC_GOVERNANCE.md`](docs/DOC_GOVERNANCE.md) 为准

### 1.3.1 结构化状态自动化规则

文档治理自动化的本地机制定义在 [`docs/governance/DOC_AUTOMATION.md`](docs/governance/DOC_AUTOMATION.md)。

当前 Phase 1A 的自动化边界固定为：
- `docs/governance/DOC_STATE.bootstrap.yaml` 只是 bootstrap 输出，不是正式真值。
- `docs/governance/DOC_STATE.yaml` 不得由当前阶段自动生成、覆盖或回写。
- bootstrap 只允许导入白名单来源：文件系统、`OPEN_QUESTIONS.md` 结构化表、`TASK_INDEX.md` 结构化表。
- Markdown 正文中的 `maturity` / `readiness` / `candidate` / `review` 自我宣称不得直接导入状态层。
- 当前 `doc-governor` 依赖本地 Python 环境可导入 `yaml`（PyYAML）；若缺失，应显式失败，不允许静默 fallback。

### 1.3.2 子任务模板规则

子任务双文档模板统一定义在 [`docs/SUBTASK_DOC_TEMPLATES.md`](docs/SUBTASK_DOC_TEMPLATES.md)。

当任务涉及以下任一事项时，除阅读 [`DOC_GOVERNANCE.md`](docs/DOC_GOVERNANCE.md) 外，还应同时阅读 [`docs/SUBTASK_DOC_TEMPLATES.md`](docs/SUBTASK_DOC_TEMPLATES.md)：
- 新建或完善 `SUBTASK_DESIGN.md`
- 新建或完善 `SUBTASK_IMPLEMENTATION.md`
- 判断子任务双文档字段是否完整
- 检查设计文档与实施文档是否职责分离
### 1.4 Markdown 安全读写规则

- 涉及 `.md` 文件的读取、编辑、重写或乱码修复时，优先使用全局 skill `markdown-safe-read-write`。
- 在 Windows 环境下处理 Markdown 时，必须显式使用 UTF-8 读写，并在写后从磁盘回读验证，避免把错误解码后的内容再次保存。
- 发现 `�`、异常 `?` 或 `妯 / 鍏 / 鏂 / 鐩 / 锛 / 闂 / 鎴` 等典型乱码片段时，应先诊断根因，不要直接覆盖原文件。

### 1.5 仓库指导

#### Repo map
- apps/web: 前端
- apps/api: 后端接口
- packages/shared: 跨端共享类型与工具
- scripts/: 构建与发布脚本

#### Guardrails
- 不要直接改 generated/ 下文件
- 涉及数据库 schema 的改动必须附带 migration
- 涉及 shared 类型改动时，必须检查 web/api 两端影响

#### Verification
- 前端修改后运行: pnpm -C apps/web test
- 后端修改后运行: pnpm -C apps/api test
- 跨包改动后运行: pnpm test

#### Preferred workflow
- 先定位入口 symbol
- 再看调用链和引用
- 再改最小闭环

## 2. 当前文档索引

### 2.1 规范

- [项目语言规范](docs/project-language-rules.md)
- [文档治理自动化规则](docs/governance/DOC_AUTOMATION.md)
- [讨论轮次工作流](docs/governance/DISCUSSION_WORKFLOW.md)

### 2.2 设计

- [AI 模拟面试 P1 文本版闭环设计稿](docs/superpowers/specs/2026-04-20-ai-interview-p1-design.md)

### 2.3 计划

- [AI 模拟面试 P1 MVP 实现计划](docs/superpowers/plans/2026-04-20-ai-interview-p1-implementation.md)

### 2.4 全局文档体系

- [AI 模拟面试 P1 最新文档总控](PLAN_LATEST.md)
- [AI 模拟面试 P1 任务索引](TASK_INDEX.md)
- [AI 模拟面试 P1 执行日志](EXECUTION_LOG.md)
- [AI 模拟面试 P1 技术标准](TECHNICAL_STANDARDS.md)
- [AI 模拟面试 P1 设计决策](DESIGN_DECISIONS.md)
- [AI 模拟面试 P1 模块索引](MODULE_INDEX.md)
- [AI 模拟面试 P1 待确认问题](OPEN_QUESTIONS.md)
- [AI 模拟面试 P1 文档成熟度](DOCUMENT_MATURITY.md)
- [AI 模拟面试 P1 文档进展](DOCUMENT_PROGRESS.md)
- [AI 模拟面试 P1 文档治理规则](docs/DOC_GOVERNANCE.md)
- [AI 模拟面试 P1 子任务双文档模板](docs/SUBTASK_DOC_TEMPLATES.md)

### 2.5 模块目录

- [AI 模拟面试 P1 模块文档目录](docs/modules)

## 3. 执行说明

- 若后续规则与普通说明文档冲突，以本文档和用户最新要求为准。
- 若新增文档会影响实现、协作或交付方式，应先更新本文档索引，再继续扩展实现。

## Evaluate Command Contract
Phase 2A evaluate-state is read-only report output.
- Command outputs structured JSON only and does not write any state files.
- It does not change DOC_STATE.bootstrap.yaml or DOC_STATE.yaml.
- PyYAML is required for reading DOC_STATE*.yaml inputs.

## 2.6 Phase 2B Render Command

- `render-report --evaluate-json <PATH>` is the primary report render entry.
- `render-report --state <DOC_STATE.bootstrap.yaml>` is only an optional wrapper and must call `evaluate_state_file` only; it must not re-implement evaluate rules.
- Default output must be `docs/governance/DOC_GOVERNOR_REPORT.md`.
- `--report-path` is only allowed under `docs/governance/` and must never target `DOC_STATE.yaml` or `DOC_STATE.bootstrap.yaml`.
- Report output is read-only interpretation only; it is not confirmed state and must not drive confirm-transition or state write-back.

## Confirm Transition (Phase 3A)
- `confirm-transition` 默认输入为 `docs/governance/DOC_STATE.yaml`；若该文件不存在则直接失败。
- `confirm-transition` 仅允许写入/更新 `DOC_STATE.yaml`，禁止写入/覆盖 `DOC_STATE.bootstrap.yaml`。
- `proposed_changes` 不允许提交 `last_transition_id`、`last_confirmed_at`、`last_confirmed_by`，这三项必须由系统在 approve 成功时补齐。
- `candidate_status` 提升（none/observe -> candidate）需至少一条 evidence。`
- Bootstrap 默认补齐 OQ policy（`gate_policy_source=bootstrap_default`）只能作为审核输入，不得单独支撑批准路径。
