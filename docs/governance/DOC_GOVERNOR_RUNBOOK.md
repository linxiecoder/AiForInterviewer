# Doc Governor Runbook

## 1. 适用范围

本手册用于在 Windows 本地配合 Codex CLI 执行 `doc_governor` 的 document round 工作流，当前优先支持：

- 设计文档（`design/spec`）
- 实施计划（`plan/implementation`）

## 2. 入口约定

统一 CLI 入口：

```powershell
python -m tools.doc_governor.cli --help
```

统一 Codex CLI 入口：

```powershell
C:\Users\Administrator\AppData\Roaming\npm\codex.cmd exec
```

## 3. 最小闭环命令链

### 3.1 评估官方状态

```powershell
python -m tools.doc_governor.cli evaluate-state --input docs/governance/DOC_STATE.yaml > tmp_eval.json
python -m tools.doc_governor.cli render-report --evaluate-json tmp_eval.json
```

### 3.2 为 document 生成 round plan

单文档：

```powershell
python -m tools.doc_governor.cli plan-round --state docs/governance/DOC_STATE.yaml --entity-type document --entity-id DOC-SPEC-P1 --round-id R-SPEC-01
```

双文档联动：

```powershell
python -m tools.doc_governor.cli plan-round --state docs/governance/DOC_STATE.yaml --entity-type document --round-id R-SPECPLAN-01
```

### 3.3 生成 round 模板并登记 open

```powershell
python -m tools.doc_governor.cli generate-round-template --round-id R-SPECPLAN-01 --state docs/governance/DOC_STATE.yaml --entity-type document
```

### 3.4 生成 Codex packet

```powershell
python -m tools.doc_governor.cli generate-codex-packet --round-id R-SPECPLAN-01 --state docs/governance/DOC_STATE.yaml
```

### 3.5 执行本地 Codex CLI

直接执行 packet 产物中的命令：

```powershell
Get-Content -LiteralPath docs\governance\packets\R-SPECPLAN-01.exec.txt -Encoding UTF8
```

### 3.6 进入 review / close

```powershell
python -m tools.doc_governor.cli update-round-status --round-id R-SPECPLAN-01 --state docs/governance/DOC_STATE.yaml --status review --actor alice
python -m tools.doc_governor.cli confirm-transition --input docs/governance/DOC_STATE.yaml --entity-type document --entity-id DOC-SPEC-P1 --proposed-changes "{\"status\":\"active\",\"review_status\":\"approved\",\"blocker_refs\":[],\"active_round_id\":\"R-SPECPLAN-01\"}" --mode approve --actor alice --reason "Decision: spec refined" --round-id R-SPECPLAN-01
python -m tools.doc_governor.cli update-round-status --round-id R-SPECPLAN-01 --state docs/governance/DOC_STATE.yaml --status closed --actor alice --close-reason completed --decision-ref decision:DR-SPECPLAN-01 --result-summary "spec/plan refined"
```

## 4. 关键文件

- 官方状态：`docs/governance/DOC_STATE.yaml`
- 报告：`docs/governance/DOC_GOVERNOR_REPORT.md`
- rounds：`docs/governance/rounds/*.md`
- packets：`docs/governance/packets/*`
- 历史：`docs/governance/transition_history.jsonl`

## 5. 常见故障

### 5.1 `codex.ps1` 被执行策略拦截

不要切到 `codex.ps1`，统一使用 `codex.cmd`。

### 5.2 `confirm-transition` 提示缺少 `Decision:`

如果传入了 `--round-id`，则 `--reason` 必须包含 `Decision:` 锚点。

### 5.3 packet 生成后 round 没进入 `in_progress`

检查：
- `generate-codex-packet` 是否对的是官方状态文件
- round 是否已在 `governance_rounds` 中登记

### 5.4 设计稿或计划文档没有被 evaluate 到

检查：
- `DOC_STATE.yaml` 中是否已登记 `documents`
- `meta.path` 是否为仓库相对路径
- heading 是否与 `required_sections.heading` 精确一致
