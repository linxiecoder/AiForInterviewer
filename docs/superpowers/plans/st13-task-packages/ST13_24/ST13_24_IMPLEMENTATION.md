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

- `ST13_24_DESIGN.md` 完成评审。
- `ST13_21` API contract 和 `ST13_20` 数据 contract 至少形成可引用版本。
- 每个目标 ST13 的 acceptance criteria 和 required tests 非空。
- 测试临时产物规则、浏览器真实验证要求、失败回退要求和自动化 / 手工分层已明确。

## 4. formal window 前置条件

- 用户另窗确认可以打开 `ST13_24` formal window。
- `DOC_STATE.yaml` required doc slot 已由 W13-E8.5 State Update 窗口写入并通过 validate/evaluate；后续仍需单独状态窗口处理 formal window。
- 本文档不得自行声明 formal window open。

## 5. implementation packet 前置条件

- formal window open 前置确认已完成。
- required tests 可执行或明确可补齐。
- allowed modify paths、forbidden paths、acceptance criteria 均已填实。
- 当前窗口不生成 implementation packet。

## 6. 允许修改范围

未来测试实现窗口才可能允许：

- `tests/**` 中被 formal window 明确授权的测试文件。
- 与测试说明直接相关的文档。
- 必要的 fixture 或 helper，但必须遵守临时产物治理规则。

当前 W13-E9 不允许创建测试代码。

## 7. 禁止修改范围

- 当前不创建 `tests/**`。
- 不修改 `tools/**`、test runner、pytest fixture、CI 配置。
- 不创建 `apps/**` 或 `infra/**`。
- 不修改 `DOC_STATE.yaml`。
- 不生成 implementation packet。

## 8. 预期实现步骤

1. 复核 API / 数据 contract。
2. 建立 required tests matrix。
3. 按 ST13 分配 P0/P1/P2/P3 验收。
4. 编写被授权的测试代码。
5. 运行统一测试入口并清理临时产物。

以上步骤当前均不执行。

## 9. 验证命令

未来实现窗口默认使用：

```bash
python -m tools.test_runner.run_tests
python -m tools.doc_governor.cli validate-state --input docs/governance/DOC_STATE.yaml
python -m tools.doc_governor.cli evaluate-state --input docs/governance/DOC_STATE.yaml
```

新增窄范围测试后必须补充对应命令。

## 10. 测试要求

- 遵守 `docs/governance/TEST_POLICY.md`。
- 不得在仓库根目录或 `tests/` 下遗留 `tmp/temp`。
- 失败时停止并输出失败原因。
- 不得用散装 pytest 绕过统一入口，除非是窄范围调试且明确说明。
- 浏览器真实验证、API contract 测试和数据测试只能在后续授权窗口执行。

## 11. 回退策略

- 文档回退：回退本双文档和父索引引用。
- 测试回退：仅限未来授权的测试文件。
- 状态回退：必须另开 State Update 或治理窗口；本文档不得直接修改 `DOC_STATE.yaml`。

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

当前 W13-E9 不写 Basic Memory。

## 16. 当前未放行实现说明

`ST13_24_IMPLEMENTATION.md` 的存在和 contract_refined 状态都不等于 implementation-ready。当前不创建 `tests/**`，不写测试代码，不生成 implementation packet，不打开 formal window。

## 17. W13-E13.5 candidate 表达策略同步

`ST13_24` 在 W13-E13.5 后继续只保留文档层 `formal_window_candidate_recommended`。正式状态层暂不写 `candidate_status=candidate`，不直接写 `readiness=downstream_ready`。

该策略不新增测试实现任务，不改变本文件的 implementation plan only 定位。下一轮如继续，只能先验证 facts-only Candidate Preview；当前仍不创建 `tests/**`，不生成 implementation packet，不打开 formal window。

## 18. W13-E13.8 facts-only 正式 State Update 同步

W13-E13.8 已在 docs/governance 直下 Preview 严格全绿后，将 `ST13_24.facts` 的 facts-only candidate 推荐字段写入正式 `DOC_STATE.yaml`：

- `formal_window_candidate_recommended=true`
- `formal_window_candidate_source=W13-E11 candidate evaluation`
- `formal_window_candidate_review_status=pending_confirmation`
- `formal_window_candidate_state=document_layer_recommended`
- `formal_window_candidate_notes=formal window closed; implementation-ready false; implementation packet forbidden`

该写入不改变本文件的实施边界：formal window 仍关闭，implementation-ready 仍为 false，implementation packet 仍禁止，`tests/**` 仍不得创建。
