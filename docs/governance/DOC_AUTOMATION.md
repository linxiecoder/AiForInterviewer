# 文档治理自动化规则

## 1. 目标与当前范围

- 本文档定义本地 `doc-governor` 的自动化边界。
- 当前仅覆盖 Phase 1A：结构化底座、白名单扫描、bootstrap 输出、模板/占位符识别。
- 当前不覆盖：`validate-state`、`evaluate`、`render`、`confirm-transition`、自动开窗。

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
