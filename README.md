# AI 模拟面试系统仓库说明

## 1. 项目是什么

- 本项目的主目标是持续推进“AI 模拟面试系统”的设计、治理、拆分、验证与后续开发协作。
- 当前仓库保存的是该项目的设计文档、治理状态、`doc_governor` / `doc_governance` 工具链，以及对应测试与验证工具。

## 2. 当前仓库是什么

当前仓库当前承载的核心内容包括：

- 根目录全局文档：项目计划、执行日志、设计决策、开放问题、成熟度与进展等治理入口。
- `docs/governance/`：文档治理规则、自动化规则、运行手册、测试政策等正式治理文档。
- `docs/superpowers/`：AI 模拟面试系统的上游产品设计稿与上游实现蓝图。
- `tools/doc_governor/`：辅助 Codex 做文档治理、任务拆分、状态评估、交接和验证收口的 CLI 工具链。
- `tests/`：`doc_governor` 及测试守卫相关验证。

## 3. 当前仓库不是什么

- 当前仓库不是已经完整落地的 `apps/web`、`apps/api`、`infra` monorepo 业务实现仓库。
- 当前仓库也不应被表述为“已经具备完整 Web/API/infra 运行结构”的代码仓。
- `docs/superpowers/plans/2026-04-20-ai-interview-p1-implementation.md` 中出现的大量 `apps/web`、`apps/api`、`infra`、`.github/workflows` 等路径，当前应视为未来 monorepo 蓝图，而不是当前仓库现实。

## 4. 四层叙事边界

### 4.1 当前仓库真相

- 当前仓库真实承载的是模拟面试系统的设计文档、治理状态、`doc_governor` 工具、测试与验证机制。
- 当前可直接核验的仓库主入口是根目录治理文档、`docs/`、`tools/doc_governor/`、`tests/` 与 `requirements.txt`。

### 4.2 上游产品蓝图

- `docs/superpowers/specs/2026-04-20-ai-interview-p1-design.md` 和 `docs/superpowers/plans/2026-04-20-ai-interview-p1-implementation.md` 仍服务“AI 模拟面试系统”主目标。
- 其中设计稿仍可作为产品目标和体验方向输入。
- 其中实现计划当前必须视为“上游产品蓝图 / 未来 monorepo 目标”，不能直接当作当前仓库的落地实施计划。
- 根据 W3 已证实结果，`DOC-PLAN-P1` 当前命中 `document_repo_truth_mismatch`，因此不能继续被主入口表述为“当前仓库可直接执行计划”。

### 4.3 阶段 3 白名单治理历史

- 阶段 3、白名单、formal window、`M01-M03` 等叙事属于本仓库此前的治理历史与阶段记录。
- 这些内容仍有保留价值，但当前不应继续压过“模拟面试系统”作为主项目目标的主入口叙事。
- 当前入口应先说明仓库真相、上游蓝图与工具链位置，再把阶段性治理历史作为背景信息看待。

### 4.4 当前 `doc_governor` 宽 CLI 工具链

- `doc_governor` 是一个辅助 Codex 推进软件项目设计开发的治理工具链。
- 它主要服务于：文档治理、任务拆分、状态评估、执行交接、验证收口。
- 当前 CLI 命令面已由 W2 对齐到治理文档；使用时应区分主链命令、扩展命令、生成类命令，以及 preview/apply/sync/seed 类命令的不同角色。

## 5. 当前推荐工作流

推荐按以下顺序进入当前仓库：

1. 先读 `README.md`、`AGENTS.md`，确认仓库定位、规则和范围。
2. 再读 `PLAN_LATEST.md`，确认当前推进计划、已完成项、阻断项与下一步。
3. 运行 `validate-state`，确认正式状态文件通过校验。
4. 运行 `evaluate-state`，读取当前治理评估结果与 blocker。
5. 需要解释性报告时，再运行 `render-report`。
6. 需要规划一轮文档推进时，再根据治理文档决定是否使用 `plan-round`、`generate-codex-packet` 等命令。
7. 多窗口执行后，由 W5 或总控窗口统一做只读验证与收口判断。

当前推荐命令示例：

```powershell
python -m tools.doc_governor.cli validate-state --input docs/governance/DOC_STATE.yaml
python -m tools.doc_governor.cli evaluate-state --input docs/governance/DOC_STATE.yaml
python -m tools.doc_governor.cli render-report --state docs/governance/DOC_STATE.yaml
```

使用边界：

- 可以把 `validate-state`、`evaluate-state`、`render-report` 视为当前主入口常用命令。
- 可以说明扩展命令和生成类命令的存在。
- 不得把 preview/apply/sync/seed 类命令写成默认主链 SOP。
- 不得把 `generate-implementation-packet`、`apply-round` 写成默认闭环。
- `render-report` 和生成出的治理报告只是解释性产物，不是 `DOC_STATE.yaml` 或 `confirm-transition` 的 confirmed state 真值。

## 6. 测试与临时产物规则

当前测试与临时产物规则采用 W4 已统一的口径：

- 默认测试入口使用 `python -m tools.test_runner.run_tests`。
- 常规临时目录机制固定为 `ManagedTempArtifacts` / `ManagedTempArtifactsTestCase`。
- `python -m tools.test_runner.run_tests` 负责提供并清理 `--basetemp`。
- 仓库测试禁止把 `tmp_path` / `tmp_path_factory` 作为常规临时目录机制。
- 仓库根目录与 `tests/` 下的残留扫描由 `tests/conftest.py` 的 pytest 会话级守卫统一执行。
- `raw tempfile.*`、`pytester/runpytest`、手写 `shutil.rmtree(...)`、repo-local `tmp/temp` literal 都属于禁止路径。
- 受控例外仅限 `tests/test_temp_artifact_policy.py` 与 `tests/doc_governor/test_temp_artifacts.py`。
- 调试保留使用 `AI_FOR_INTERVIEWER_KEEP_TEST_ARTIFACTS=1`，可选 `AI_FOR_INTERVIEWER_TEST_TEMP_ROOT`。
- `AI_FOR_INTERVIEWER_ALLOW_TEST_DIR_LEAKS=1` 仅限一次性诊断，不应作为日常跑测或 CI 默认。

## 7. 当前风险与待后续处理事项

- `DOC-PLAN-P1` 当前命中 `document_repo_truth_mismatch`，旧 P1 implementation plan 暂不能作为当前仓库直接执行计划。
- `render.py` / `bootstrap.py` 的生成标题与说明性正文中文化仍需后续窗口处理；W1 本轮只记录，不改工具代码。
- 基线已有 4 个未跟踪项：`.tmp_dbg_impl_state/`、`artifacts/`、`tmp_readiness_case.yaml`、`tmp_test_state2.yaml`。它们不在 W1 本轮清理范围。

## 8. 相关入口

- 协作规则入口：`AGENTS.md`
- 当前推进计划：`PLAN_LATEST.md`
- 全局执行日志：`EXECUTION_LOG.md`
- 人工治理总则：`docs/DOC_GOVERNANCE.md`
- 自动化规则：`docs/governance/DOC_AUTOMATION.md`
- 运行手册：`docs/governance/DOC_GOVERNOR_RUNBOOK.md`
- 测试政策：`docs/governance/TEST_POLICY.md`
