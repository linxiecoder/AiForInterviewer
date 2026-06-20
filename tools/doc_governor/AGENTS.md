# tools/doc_governor 局部规则

本文件只补充根目录 `AGENTS.md`。冲突时以根规则、`docs/00-governance/*`、`docs/03-implementation/*` 和当前工具测试为准。

## 角色

- `tools/doc_governor` 是文档治理和任务状态同步工具，不是新的产品 roadmap、计划入口或长期事实源。
- 工具输出必须回写到已授权的 active docs、BACKLOG、DELIVERY_PLAN、ADR 或 archive 台账边界内。
- 不得让工具生成 `plan-v2`、`latest-plan`、`codex-plan`、新阶段体系或并行任务编号。

## 主要入口

- `cli.py` 是命令行入口。
- `schema.py`、`rules.py`、`validate.py` 承载结构和规则校验。
- `document_scan.py`、`repo_scan.py`、`template_detection.py` 承载扫描和识别。
- `task_*`、`requirement_*`、`*_state_sync.py` 文件承载任务/需求/状态同步能力。
- `codex_packet.py`、`task_packet.py`、`round_template.py` 承载受控窗口材料生成。

## 修改规则

- 修改工具前先读目标能力对应的 `tests/doc_governor` 测试。
- 结构化文档、frontmatter、表格和链接必须用现有解析/渲染能力处理，不要用脆弱字符串替换。
- 涉及归档、任务状态、需求追踪、窗口计划时，必须保持 active/archive 边界和 `AIFI-*` 编号规则。
- 工具不得把 `docs/goals/` evidence-only 内容升级为 active requirement、active design、delivery plan 或 ADR。

## 验证

- 聚焦运行 `python -m pytest tests/doc_governor/<target>.py -q`。
- 临时文件必须遵守 `docs/00-governance/TEST_POLICY.md`。
- 修改 CLI 输出时要同时检查调用方测试、快照式文本断言和错误语义。

## 输出边界

- 报告类输出要区分 `PASS`、`WARN`、`UNKNOWN`，不要把证据缺失写成通过。
- 涉及归档动作时必须包含原路径、归档路径、原因、替代路径、状态和阻断条件。
- 涉及需求继承时只能通过 `docs/01-product/REQUIREMENT_TRACEABILITY.md` 建立追踪。
- 涉及任务状态时只能通过 `docs/03-implementation/BACKLOG.md` 和既有同步规则落库。
