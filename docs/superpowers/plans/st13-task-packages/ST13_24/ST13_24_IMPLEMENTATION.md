# ST13_24 IMPLEMENTATION：测试 / 验收 / DoD

## 1. 文档状态

- 状态：`draft`
- 文档性质：`implementation plan only`
- 实施状态：`not implementation-ready`
- formal window：`formal window closed`
- implementation packet：`implementation packet forbidden`
- contract 状态：`contract_refined`
- 本文件只描述未来测试 / 验收窗口如何执行；当前不创建测试代码。
- W13-E8.5 已将本文件登记到 `DOC_STATE.yaml` 既有 `facts.implementation_doc` slot，`exists=true`，`template_like=false`；该登记不改变 `implementation_doc_state=missing`、`readiness=blocked` 或 formal window 状态。

## 2. 关联 ST13 / WT13

- ST13：`ST13_24`
- WT13 alias：`WT13-24`
- 设计文档：`docs/superpowers/plans/st13-task-packages/ST13_24/ST13_24_DESIGN.md`

## 3. 进入实现前置条件

当前未放行实现。未来如要进入 ST13_24 实现窗口，必须先满足以下条件：

1. 总控已另窗打开 `ST13_24 / WT13-24` formal window，且正式状态层允许后续 implementation packet 流程。
2. `ST13_24_DESIGN.md` 中的 acceptance criteria、required tests、implementation scope、allowed paths、forbidden paths、formal window 前置条件、implementation packet 前置条件和回退策略已完成复核。
3. `ST13_21` API contract 与 `ST13_20` 数据 contract 已稳定到可支撑测试矩阵拆分；若仍有影响测试的 blocker，必须记录并阻断实现。
4. 是否创建 `tests/**`、是否创建测试代码、是否补充 fixture / helper、是否执行 browser verification，均已有用户确认。
5. 临时产物规则、失败停止条件、验证命令、收口输出和回退说明已写入 implementation packet 或等价授权材料。
6. 未来实现窗口不得绕过 `preflight-open-window`、`validate-state`、`evaluate-state` 或当前工具 gate。

任一前置条件缺失时，只能继续文档治理或输出确认卡，不得进入实现。

## 4. formal window 前置条件

formal window open 必须由总控或状态治理窗口处理，本文档不得自行声明 formal window open。打开前必须满足：

- 用户另窗明确确认可以打开 `ST13_24` formal window。
- 正式 `DOC_STATE.yaml` 已在授权状态窗口中处理 formal window 相关字段；本窗口不修改 `DOC_STATE.yaml`。
- 基于正式 `DOC_STATE.yaml` 的 `validate-state` / `evaluate-state` 重新执行且为 `ok=true,error=0,warning=0`，`documents_blocked_count=0`。
- allowed paths / forbidden paths 已冻结，且如涉及 `tests/**`，已有单独授权。
- `implementation_doc_state`、candidate 推荐事实、required doc slot 和 blocker 状态不被人工正文误读；facts-only candidate 推荐不等于 formal window open。

当前 formal window 仍为 `formal window closed`。

## 5. implementation packet 前置条件

implementation packet 只能在 formal window open 后、且 gate 全部通过后生成。生成前必须满足：

- `implementation_packet_inputs.goal` 非空，且只覆盖测试 / 验收 / DoD，不扩展为应用实现。
- `allowed_modify_paths` 和 `forbidden_paths` 非空，并与用户授权一致。
- `required_tests` 非空，覆盖 governance tests、contract tests、unit tests、integration tests、browser verification、manual acceptance。
- `acceptance_criteria` 非空，覆盖产品 DoD、数据 DoD、UI DoD、工程 DoD、收口 DoD，以及 API、数据库、RAG、LLM、多轮、打磨、压力面、评分复盘、Markdown 导出、权限、安全、错误态、空状态。
- packet 生成前重新执行 `preflight-open-window` 或等价 gate，并重新跑 `validate-state` / `evaluate-state`。
- 若任一 gate、测试前置或禁止范围检查失败，必须停止生成 packet 并输出失败回退说明。

当前不生成 implementation packet。

## 6. implementation scope / allowed paths

### 6.1 当前窗口允许修改范围

当前 W13-E14-A 只允许修改：

- `docs/superpowers/plans/st13-task-packages/ST13_24/ST13_24_DESIGN.md`
- `docs/superpowers/plans/st13-task-packages/ST13_24/ST13_24_IMPLEMENTATION.md`

当前不创建 `tests/**`，不写测试代码，不同步父索引，不写 Basic Memory，不修改状态层。

### 6.2 未来实现窗口可能允许的范围

未来只有在 formal window 和 implementation packet 均已通过后，才可能允许：

- `tests/**` 中被明确授权的测试文件。
- 与 required tests 直接相关的测试 fixture / helper。
- 被 implementation packet 点名的窄范围文档补充。
- 被总控批准的 browser verification 命令、截图 / trace 输出位置和失败证据格式。

上述范围不是当前授权。

## 7. forbidden paths / 禁止修改范围

当前窗口和 formal window 打开前均禁止：

- `tests/**`
- `apps/**`
- `infra/**`
- `tools/**`
- `docs/governance/**`
- `docs/governance/DOC_STATE.yaml`
- `PLAN_LATEST.md`
- `EXECUTION_LOG.md`
- `DOCUMENT_PROGRESS.md`
- `DOCUMENT_MATURITY.md`
- `TASK_INDEX.md`
- `MODULE_INDEX.md`
- `OPEN_QUESTIONS.md`
- `DESIGN_DECISIONS.md`
- `AGENTS.md`
- `docs/superpowers/plans/st13-task-packages/ST13_20/**`
- `docs/superpowers/plans/st13-task-packages/ST13_21/**`
- `docs/superpowers/plans/st13-task-packages/ST13_25/**`
- `docs/modules/**`
- 历史材料目录
- `package.json`
- `package-lock.json`
- `pnpm-lock.yaml`
- Basic Memory 写入或外部记忆写回
- test runner、pytest fixture、CI 配置、dev server 配置

## 8. 预期实现步骤

以下步骤仅供未来授权窗口使用，当前均不执行：

1. 通过 `preflight-open-window` 或等价 gate 复核 formal window 状态。
2. 复核 `ST13_21` API contract、`ST13_20` 数据 contract 和 ST13_24 acceptance criteria。
3. 建立 required tests matrix，并标记 governance / contract / unit / integration / browser / manual 层级。
4. 按 P0/P1/P2/P3 分配验收和失败停止条件。
5. 在被授权的路径内编写测试代码或测试辅助材料。
6. 运行统一测试入口、窄范围验证命令和 browser verification。
7. 执行临时产物残留检查，并输出失败回退说明。

## 9. 验证命令

当前窗口只执行状态验证和关键词 / 禁止范围检查。未来实现窗口默认使用：

```bash
python -m tools.test_runner.run_tests
python -m tools.doc_governor.cli validate-state --input docs/governance/DOC_STATE.yaml
python -m tools.doc_governor.cli evaluate-state --input docs/governance/DOC_STATE.yaml
```

新增窄范围测试后必须补充对应命令；browser verification、API contract 测试和数据测试只能在后续授权窗口执行。

## 10. required tests / 测试要求

- governance tests：`validate-state`、`evaluate-state`、关键词检查、禁止范围检查、UTF-8 回读。
- contract tests：API schema、权限矩阵、错误 taxonomy、数据对象关系、RAG evidence、LLM 失败语义、评分 / 复盘、Markdown 导出权限过滤。
- unit tests：状态转换、校验、导出内容组装、权限判断、格式化等纯逻辑。
- integration tests：API + 数据库 + RAG + LLM provider mock / stub + 评分复盘 + 导出链路。
- browser verification：桌面 / 移动视口、面试台交互、复盘详情、错误态 / 空状态、导出入口。
- manual acceptance：主链体验、复杂 UI、文案可读性、复盘解释性、训练建议质量和管理员运营边界。

所有测试必须遵守 `docs/governance/TEST_POLICY.md`。不得在仓库根目录或 `tests/` 下遗留 `tmp-*`、`tmp_*`、`temp-*`、`temp_*`、debug 目录或等价临时产物。失败时停止并输出失败命令、失败原因、受影响文件、临时产物路径、是否需要状态回退和是否需要用户确认。

## 11. 回退策略

- 文档回退：当前仅可回退 ST13_24 双文档中的本次补齐内容；父索引或状态层回退交给 `W13-E14-Merge` 或状态治理窗口。
- 测试回退：仅限未来授权的测试文件；当前不创建测试文件。
- 临时产物回退：清理测试策略允许位置中的临时目录，若根目录或 `tests/` 出现残留必须停止并报告路径。
- 状态回退：必须另开 State Update 或治理窗口；本文档不得直接修改 `DOC_STATE.yaml`。
- browser verification 回退：保留截图 / trace / 复现路径，停止声称 UI DoD 通过；未授权时不得顺手修 UI 或测试。
- 范围冲突回退：输出确认卡，不自行改变 ST13_24 任务范围。

## 12. 日志 / 观测要求

未来测试输出应保留：

- 命令。
- 通过 / 失败结果。
- 失败摘要。
- 临时产物路径和清理结果。
- 与 ST13 / WT13 的映射。

## 13. 安全 / 隐私检查

- 测试 fixture 不得包含真实简历、真实 provider key、私有知识库内容。
- LLM / RAG / export 测试必须使用脱敏样例。
- 权限测试必须覆盖越权读取和管理员筛选边界。

## 14. 交接输出格式

未来实现窗口收口时必须输出：

- 修改文件清单。
- tests matrix 摘要。
- 验证命令和结果。
- 临时产物检查结果。
- 未完成项和 blocker。

## 15. Basic Memory / Superpowers 写回要求

未来收口窗口如获授权，必须先检索、后写入、再回读验证。写回内容至少包含 confirmed 测试策略、风险、下一步和验证结果。

当前 W13-E14-A 不写 Basic Memory。

## 16. 当前未放行实现说明

`ST13_24_IMPLEMENTATION.md` 的存在和 contract_refined 状态都不等于 implementation-ready。当前不创建 `tests/**`，不写测试代码，不生成 implementation packet，不打开 formal window。

## 17. W13-E13.5 candidate 表达策略同步

`ST13_24` 在 W13-E13.5 后继续只保留文档层 `formal_window_candidate_recommended`。正式状态层暂不写 `candidate_status=candidate`，不直接写 `readiness=downstream_ready`。

该策略不新增测试实现任务，不改变本文件的 implementation plan only 定位。下一轮如继续，只能先验证 facts-only Candidate Preview；当前仍不创建 `tests/**`，不生成 implementation packet，不打开 formal window。

## 18. W13-E13.8 facts-only 正式 State Update 同步

W13-E13.8 已在 docs/governance/previews 路径 Preview 严格全绿后，将 `ST13_24.facts` 的 facts-only candidate 推荐字段写入正式 `DOC_STATE.yaml`：

- `formal_window_candidate_recommended=true`
- `formal_window_candidate_source=W13-E11 candidate evaluation`
- `formal_window_candidate_review_status=pending_confirmation`
- `formal_window_candidate_state=document_layer_recommended`
- `formal_window_candidate_notes=formal window closed; implementation-ready false; implementation packet forbidden`

该写入不改变本文件的实施边界：formal window 仍关闭，implementation-ready 仍为 false，implementation packet 仍禁止，`tests/**` 仍不得创建。
