# 项目协作规则

本文档是当前项目的高优先级协作入口，用于沉淀全局规则并索引核心文档。

## MVP 三迭代交付总控规则

当前项目按「AI 模拟面试工作台级 MVP」推进。MVP 交付必须拆成 R0 / R1 / R2 三个迭代，不允许一次性铺开所有能力。

### R0：可运行主链路

R0 目标是交付最小但真实可运行的模拟面试闭环。

R0 必须优先覆盖：

- 最小登录或用户身份边界
- 岗位录入 / 读取
- 简历录入 / 读取
- 启动一次模拟面试
- 真实 LLM 生成问题
- 用户提交回答
- 服务端保存面试记录
- 最小历史记录回看
- 最小评分或反馈
- 最小复盘结果
- Markdown 复制或下载
- 主链路测试或最小集成验证

R0 明确不做：

- 复杂 RAG 质量评估
- 完整知识库治理
- 多模式高阶面试
- 完整训练中心
- 完整资产归档
- 企业级权限
- 多租户
- 复杂管理后台
- 大规模 UI 打磨
- 无关重构

### R1：可信工作台闭环

R1 只能在 R0 accepted / done 或用户明确授权后推进。

R1 目标是在 R0 基础上增强数据、评分、RAG 和复盘可信度。

R1 优先覆盖：

- API contract 收敛
- 数据模型和数据库 migration 稳定
- 岗位 / 简历 / 面试 / 问答 / 评分 / 复盘关系可追踪
- RAG 最小可用：文档切块、索引、检索、引用
- 0-100 多维评分
- 复盘中展示评分理由、证据、建议
- 历史记录可恢复和回看
- LLM / RAG / 解析失败时有明确降级提示
- 主链路和关键边界测试

R1 明确不做：

- 高级检索质量平台
- 复杂团队共享知识库
- 完整训练闭环
- 批量导出
- 高级运维监控
- 大规模重构

### R2：训练闭环与资产沉淀

R2 只能在 R1 accepted / done 或用户明确授权后推进。

R2 目标是形成从面试到复盘、弱点识别、训练建议和资产归档的闭环。

R2 优先覆盖：

- 薄弱项识别
- 弱点证据关联
- 训练建议或训练抽屉
- 训练任务入列或待打磨清单
- 模拟面试复盘增强
- 真实面试复盘入口或最小闭环
- 资产归档
- Markdown 导出增强
- 最终 MVP DoD 收口

R2 明确不做：

- 企业级商业化
- 多端客户端
- 实时语音 / 视频
- ATS 集成
- 复杂组织管理
- 完整运营后台

### 每日自检规则

当用户说“每日自检”“今天怎么推进”“继续项目”“检查当前计划”“开启下一步”或“下一步做什么”时，必须执行 Daily Check，而不是直接进入实现。

Daily Check 必须读取和复用现有文档体系：

- `docs/governance/DOC_STATE.yaml`
- `docs/governance/DOC_AUTOMATION.md`
- `docs/DOC_GOVERNANCE.md`
- `TASK_INDEX.md`
- `PLAN_LATEST.md`
- `EXECUTION_LOG.md`
- `OPEN_QUESTIONS.md`
- `docs/planning/workbench-mvp/2026-04-25-workbench-mvp-backlog-roadmap.md`
- `docs/tasks/workbench-mvp/2026-04-25-workbench-mvp-task-remap.md`
- `docs/tasks/workbench-mvp/st13-task-packages/**`
- `docs/requirements/workbench-mvp/**`
- `docs/design/workbench-mvp/**`

Daily Check 必须输出：

1. Repo 状态：branch、commit、`git status --short`、未解释改动、是否允许继续。
2. R0 / R1 / R2 交付切片映射表。
3. 当前主推进迭代。
4. 计划偏离检查。
5. 今日唯一主目标。
6. 下一步窗口卡。
7. 是否需要用户确认。

### R0/R1/R2 与现有文档体系的关系

R0 / R1 / R2 只是交付切片视角，不是新的状态真值系统。

不得默认新增：

- `ITERATION_STATE.md`
- `R0_PLAN.md`
- `R1_PLAN.md`
- `R2_PLAN.md`
- 任何新的长期状态入口

如需固化 R0 / R1 / R2 映射，优先回写到现有文档：

1. `docs/planning/workbench-mvp/2026-04-25-workbench-mvp-backlog-roadmap.md`
2. `PLAN_LATEST.md`
3. `TASK_INDEX.md`
4. 对应 `docs/tasks/workbench-mvp/st13-task-packages/**`
5. `EXECUTION_LOG.md`

新增文档前必须说明：

- 为什么现有文档不能承接
- 后续 Daily Check 是否会读取
- 谁维护
- 写入路径
- 用户是否已确认

### Gate 与实现边界

任务是否可实现，以 `DOC_STATE.yaml`、`DOC_AUTOMATION.md` 和 doc-governor gate 为准。

禁止：

- formal window 未打开就直接写业务代码
- implementation packet 未生成就直接实现
- 没有 allowed paths / forbidden paths 就修改文件
- 没有 DoD 或验证命令就开窗
- 把 Markdown 正文中的 ready / candidate / implementation-ready 描述当作正式状态
- 把 preview / dry-run / facts-only candidate 当作 official state
- R0 未 accepted 就主动实现 R1 / R2 能力
- 新增后续不会维护和读取的文档

### 下一步窗口卡格式

每次建议开启下一步前，必须输出窗口卡：

| 字段 | 内容 |
| --- | --- |
| Window ID | 例如 `R0-W01` |
| Iteration | R0 / R1 / R2 |
| Task Mode | analysis / implementation / review / documentation / testing / governance |
| Goal | 本窗口唯一目标 |
| Existing Source | 对应现有任务、backlog item、OQ 或状态字段 |
| Allowed Paths | 允许修改路径 |
| Forbidden Paths | 禁止修改路径 |
| Input Docs | 必须读取的现有文档 |
| DoD | 完成标准 |
| Validation | 验证命令 |
| Change Budget | 最大修改文件数 / 是否允许新增文件 |
| Stop Conditions | 停止条件 |
| Writeback Target | 如需更新文档，写入哪个现有文档；不需要则写 `none` |

没有窗口卡，不得进入实现。

### 目标偏离识别

如果出现以下任一情况，必须明确提醒“目标偏离”：

- R0 未完成，却开始实现 R1 / R2 能力
- formal window 未打开，却建议直接写业务代码
- implementation packet 未生成，却建议直接进入实现
- 没有 allowed paths / forbidden paths，却建议修改文件
- 没有 DoD 或验证命令，却建议开窗
- 又开始整理大而全的文档体系
- 新增了后续不会读取和维护的文档
- 当前任务不解除任何阻断
- 当前任务不能推进当前主迭代
- 修改范围超过窗口目标
- 多个 Codex session 可能同时修改同一文件

输出格式：

`目标偏离：是。原因：[原因]。建议回到：[具体任务或阻断项]。`

如果没有偏离：

`目标偏离：否。当前动作服务于 [R0/R1/R2] 的 [具体目标]。`

### 推进缓慢识别

如果出现以下任一情况，必须提醒“推进缓慢风险”：

- 连续两次只做文档整理，没有解除 gate 或推进实现前置条件
- 同一问题反复生成计划，没有进入验证或状态确认
- 每日目标不是唯一目标
- 每个窗口都跨多个主题
- 任务没有完成标准
- 任务没有验证命令
- 输出建议没有指向现有任务 ID、backlog ID 或 gate 阻断项
- 文档更新后没有指定后续谁读取、何时读取、在哪里读取
- R0 主链路还没跑通，却投入大量精力做 UI polish、复杂 RAG 或训练体系

输出格式：

`推进缓慢风险：是。原因：[原因]。最短推进动作：[一个动作]。`


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

本仓库的项目治理总则定义在 [`DOC_GOVERNANCE.md`](docs/DOC_GOVERNANCE.md)。

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

需要特别说明：
- [`DOC_GOVERNANCE.md`](docs/DOC_GOVERNANCE.md) 当前定位为人工协作总则、项目治理总则，不再充当完整 `doc-governor` 工具实现真值。
- 当任务涉及 `doc-governor` 的命令行为、状态 schema、gate 规则、confirmed state 写回、document round、history、open-window 等结构化状态自动化行为时，必须同时阅读：
  - [`docs/governance/DOC_AUTOMATION.md`](docs/governance/DOC_AUTOMATION.md)
  - `tools/doc_governor/cli.py`
  - `tools/doc_governor/schema.py`
  - `tools/doc_governor/validate.py`
  - `tools/doc_governor/evaluate.py`
  - `tools/doc_governor/confirm.py`

如果 `AGENTS.md`、[`DOC_GOVERNANCE.md`](docs/DOC_GOVERNANCE.md)、[`docs/governance/DOC_AUTOMATION.md`](docs/governance/DOC_AUTOMATION.md) 或当前代码实现看似冲突：
- 目录结构、角色边界、全局总则以 `AGENTS.md` 为准
- 人工协作流程、文档职责、项目治理口径以 [`DOC_GOVERNANCE.md`](docs/DOC_GOVERNANCE.md) 为准
- 自动化边界、状态文件规则、命令契约以 [`docs/governance/DOC_AUTOMATION.md`](docs/governance/DOC_AUTOMATION.md) 为准
- 实际命令参数、对象模型、gate 判定与写回行为以 `tools/doc_governor/*.py` 当前实现为准

### 1.3.1 结构化状态自动化规则

文档治理自动化的本地机制定义在 [`docs/governance/DOC_AUTOMATION.md`](docs/governance/DOC_AUTOMATION.md)。

当前自动化边界固定为：
- `docs/governance/DOC_STATE.bootstrap.yaml` 只是 bootstrap 输出，不是正式真值。
- `docs/governance/DOC_STATE.yaml` 是正式真值，只允许通过 `confirm-transition`、round lifecycle 写回与显式 seed 更新维护。
- bootstrap 只允许导入白名单来源：文件系统、`OPEN_QUESTIONS.md` 结构化表、`TASK_INDEX.md` 结构化表。
- Markdown 正文中的 `maturity` / `readiness` / `candidate` / `review` 自我宣称不得直接导入状态层。
- `documents` 一级治理对象只存在于 `DOC_STATE.yaml`，当前优先支持 `design/spec` 与 `plan/implementation`。
- Windows 本地 Codex CLI 集成统一使用 `codex.cmd exec`，不使用 `codex.ps1`。
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
- 根目录 `*.md`: 全局总控、索引、标准、决策、成熟度、进展与开放问题
- `docs/requirements/`: 当前需求事实源
- `docs/design/`: 当前设计事实源
- `docs/planning/`: 当前规划文档
- `docs/tasks/`: 当前任务文档
- `docs/governance/`: 文档治理规则、运行手册、状态文件与报告输出
- `docs/modules/`: `M01-M10` 模块需求、模块设计、模块任务和模块问题
- `EXECUTION_LOG.md`: 当前过程记录入口
- `archive/`: 历史材料，不作为当前事实源
- `tools/doc_governor/`: 文档治理 CLI、状态流转、扫描、校验与报告渲染
- `tests/doc_governor/`: `doc_governor` 对应测试、fixtures 与 smoke / integration 验证
- `requirements.txt`: 当前 Python 依赖入口

#### Guardrails
- 不要直接改 `node_modules/`、`.serena/`、`.worktrees/`、`__pycache__/`、`pytest-cache-files-*` 等本地缓存或工作目录
- `docs/governance/DOC_STATE.yaml` 是正式真值；`DOC_STATE.bootstrap.yaml` 只是 bootstrap 输出
- 修改 `tools/doc_governor/` 时，必须同步检查 `tests/doc_governor/` 的影响

#### Verification
- 文档治理 / 工具改动后运行: `python -m pytest tests/doc_governor -q`
- CLI 入口检查: `python -m tools.doc_governor.cli --help`
- 涉及状态评估链路时运行: `python -m tools.doc_governor.cli evaluate-state --input docs/governance/DOC_STATE.yaml`

#### Preferred workflow
- 先定位入口 symbol
- 再看调用链和引用
- 再改最小闭环

### 1.6 上下文使用规则

遇到需求讨论、方案讨论、模块设计、任务拆分、实施计划时：
- 优先读取本仓库 AGENTS.md
- 优先使用可用的记忆/检索工具查找历史讨论、设计决策、开放问题、约束
- 若历史上下文与当前用户新要求冲突，以当前用户明确指令为准，同时指出冲突点
- 讨论结束时，必须产出可复用的压缩总结，便于后续继续讨论

### 1.7 禁止偏移

以下情况必须明确提醒用户并纠偏：
- 需求尚未澄清就直接进入代码实现
- 模块边界未明确就开始拆分细节任务
- 历史决策已存在却重复讨论且未说明变更原因
- 当前讨论已偏离“模拟面试工具”主目标

### 1.8 Basic Memory 目录路由规则

写入 Basic Memory 时，必须显式指定 directory，不允许省略。

目录映射如下：

- 项目总目标、全局约束、项目说明 -> 00-project
- 正式需求、需求边界、验收标准 -> 10-requirements
- 已确认决策 -> 20-decisions
- 尚未关闭的开放问题 -> 30-open-questions
- 模块职责、模块边界、模块设计 -> 40-module-design
- 实施计划、阶段计划、任务拆分 -> 50-plans
- 风险、限制、依赖、假设 -> 60-risks-constraints
- 每轮讨论总结 -> 90-session-summaries

写入规则:

- 新主题使用 write_note
- 已存在同主题笔记时优先 edit_note，不重复创建近似笔记
- 写入前先 search_notes，避免重复
- 每轮有效讨论结束后，至少写入一条会话总结或更新一条已有笔记

### 1.8.1 Basic Memory 自动读写补充规则

当任务属于需求开发、文档治理、模块推进、设计讨论、任务拆分或任务总结时：

- 开始前先读取 `AGENTS.md` 与必要的正式规则文档，再检索 `AiForInterviewer` 的 Basic Memory 上下文，不要直接凭当前聊天继续。
- 若 `search_notes` 的 default / hybrid / vector 检索失败，必须降级到 `text -> title -> permalink -> recent_activity -> list_directory -> read_note/build_context`，不得把向量失败误判成“没有历史记忆”。
- 写入时只允许使用白名单目录：`00-project`、`10-requirements`、`20-decisions`、`30-open-questions`、`40-module-design`、`50-plans`、`60-risks-constraints`、`90-session-summaries`。
- 禁止写入根目录、空目录或 `notes/`。
- 写入或更新后必须回读验证；若 Basic Memory 写入失败，必须输出可复制的待写入内容，不能让结论只停留在聊天上下文。

### 1.8.2 Basic Memory 程序级包装器规则

当需要以程序方式读写 Basic Memory，而不是只依赖 Skill 约束时：

- 优先使用 `python -m tools.basic_memory_guard.cli`。
- 程序级包装器当前只覆盖 `00-project`、`20-decisions`、`30-open-questions`、`60-risks-constraints`、`90-session-summaries` 五类长期上下文写入。
- `safe-write` 必须先检索、后写入、再回读验证；若命中同标题笔记则默认更新，若存在歧义则拒绝写入并输出 fallback 包。
- `20-decisions` 仅允许写入 `confirmed` / `accepted` / `approved` 的内容，包装器不得替代正式拍板。
- Basic Memory 只是长期上下文层，不能反推 `doc_governor` / `DOC_STATE.yaml` 的正式结构化真值。
- `vector search` 只是增强路径，不是唯一检索路径；向量失败不得阻断上下文读取。

### 1.9 测试规则

- 默认测试入口使用 `python -m tools.test_runner.run_tests`，避免散装 pytest 在仓库目录留下临时目录。
- 禁止测试直接在仓库根目录创建 `tmp-*`、`tmp_*`、`temp-*`、`temp_*`、`M01-test`、`fake-repo`、`sample-project` 等目录。
- 根目录与 `tests/` 下若存在匹配 `^(?:_?tmp|temp)(?:[-_].*)?$` 的目录残留，测试必须失败。
- 详细约束与验证命令见 [`docs/governance/TEST_POLICY.md`](docs/governance/TEST_POLICY.md)。

## 2. 当前文档索引

### 2.1 规范

- [项目语言规范](docs/project-language-rules.md)
- [文档治理自动化规则](docs/governance/DOC_AUTOMATION.md)
- [测试执行与临时产物治理规则](docs/governance/TEST_POLICY.md)
- [Basic Memory Guard 运行说明](docs/governance/BASIC_MEMORY_GUARD.md)
- [讨论轮次工作流](docs/governance/DISCUSSION_WORKFLOW.md)
- [Doc Governor 运行手册](docs/governance/DOC_GOVERNOR_RUNBOOK.md)
- [Doc Governor 工具债追踪](docs/governance/DOC_GOVERNOR_TOOL_DEBT.md)

### 2.2 需求

- [AI 模拟面试一期工作台 MVP 需求入口](docs/requirements/workbench-mvp/README.md)
- [AI 模拟面试一期工作台 MVP 范围与验收需求](docs/requirements/workbench-mvp/scope-and-acceptance.md)

### 2.3 设计

- [AI 模拟面试一期工作台 MVP 设计入口](docs/design/workbench-mvp/README.md)
- [AI 模拟面试一期工作台 MVP 范围设计](docs/design/workbench-mvp/scope.md)
- [AI 模拟面试一期工作台 MVP 信息架构设计](docs/design/workbench-mvp/information-architecture.md)
- [AI 模拟面试一期工作台 MVP 对象模型、RAG、多轮与后端边界设计](docs/design/workbench-mvp/object-model-rag-multiround-backend.md)
- [AI 模拟面试一期工作台 MVP 评分、复盘、导出与 DoD 设计](docs/design/workbench-mvp/scoring-review-export-dod.md)

### 2.4 计划

- [AI 模拟面试系统当前仓库执行计划](docs/planning/2026-04-25-current-repo-execution-plan.md)
- [AI 模拟面试一期工作台 MVP 待办与路线图清单](docs/planning/workbench-mvp/2026-04-25-workbench-mvp-backlog-roadmap.md)

### 2.5 任务文档

- [AI 模拟面试一期工作台 MVP 任务重映射草案](docs/tasks/workbench-mvp/2026-04-25-workbench-mvp-task-remap.md)
- [AI 模拟面试一期工作台 MVP ST13_21 API / 后端服务边界双文档](docs/tasks/workbench-mvp/st13-task-packages/ST13_21/ST13_21_DESIGN.md) / [实施说明](docs/tasks/workbench-mvp/st13-task-packages/ST13_21/ST13_21_IMPLEMENTATION.md)
- [AI 模拟面试一期工作台 MVP ST13_20 服务端保存 / 数据库双文档](docs/tasks/workbench-mvp/st13-task-packages/ST13_20/ST13_20_DESIGN.md) / [实施说明](docs/tasks/workbench-mvp/st13-task-packages/ST13_20/ST13_20_IMPLEMENTATION.md)
- [AI 模拟面试一期工作台 MVP ST13_24 测试 / 验收 / DoD 双文档](docs/tasks/workbench-mvp/st13-task-packages/ST13_24/ST13_24_DESIGN.md) / [实施说明](docs/tasks/workbench-mvp/st13-task-packages/ST13_24/ST13_24_IMPLEMENTATION.md)
- [AI 模拟面试一期工作台 MVP ST13_25 文档治理 / 收口 / Basic Memory 双文档](docs/tasks/workbench-mvp/st13-task-packages/ST13_25/ST13_25_DESIGN.md) / [实施说明](docs/tasks/workbench-mvp/st13-task-packages/ST13_25/ST13_25_IMPLEMENTATION.md)

### 2.6 全局文档体系

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

### 2.7 模块目录

- [AI 模拟面试 P1 模块文档目录](docs/modules)

## 3. 执行说明

- 若后续规则与普通说明文档冲突，以本文档和用户最新要求为准。
- 若新增文档会影响实现、协作或交付方式，应先更新本文档索引，再继续扩展实现。

## 3.1 评估命令约束

- `evaluate-state` 是只读评估命令。
- 命令只输出结构化 JSON，不写任何状态文件。
- 它不会修改 `DOC_STATE.bootstrap.yaml` 或 `DOC_STATE.yaml`。
- 读取 `DOC_STATE*.yaml` 依赖 `PyYAML`。

## 3.2 报告渲染约束

- `render-report --evaluate-json <PATH>` 是主渲染入口。
- `render-report --state <PATH>` 只是共享 evaluate 路径的 wrapper，不得重写 evaluate 规则。
- 默认输出必须是 `docs/governance/DOC_GOVERNOR_REPORT.md`。
- `--report-path` 只允许写到 `docs/governance/` 下，且不得指向 `DOC_STATE.yaml` 或 `DOC_STATE.bootstrap.yaml`。
- 报告输出只是解释性只读结果，不是 confirmed state，不得直接驱动 `confirm-transition` 或状态写回。

## 3.3 状态确认约束

- `confirm-transition` 默认输入为 `docs/governance/DOC_STATE.yaml`；若该文件不存在则直接失败。
- `confirm-transition` 仅允许写入/更新 `DOC_STATE.yaml`，禁止写入/覆盖 `DOC_STATE.bootstrap.yaml`。
- `proposed_changes` 不允许提交 `last_transition_id`、`last_confirmed_at`、`last_confirmed_by`，这三项必须由系统在 approve 成功时补齐。
- `candidate_status` 提升（none/observe -> candidate）需至少一条 `--evidence-ref`。
- Bootstrap 默认补齐 OQ policy（`gate_policy_source=bootstrap_default`）只能作为审核输入，不得单独支撑批准路径。
