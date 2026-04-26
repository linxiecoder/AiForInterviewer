# ST13_25 IMPLEMENTATION：文档治理 / 收口 / Basic Memory

## 1. 文档状态

- 状态：`draft`
- 文档性质：`implementation plan only`
- 实施状态：`not implementation-ready`
- formal window：`formal window closed`
- implementation packet：`implementation packet forbidden`
- contract 状态：`contract_refined`
- 本文件只描述未来治理收口窗口如何执行；当前不写 Basic Memory。
- W13-E8.5 已将本文件登记到 `DOC_STATE.yaml` 既有 `facts.implementation_doc` slot，`exists=true`，`template_like=false`；该登记不改变 `implementation_doc_state=missing`、`readiness=blocked` 或 formal window 状态。

## 2. 关联 ST13 / WT13

- ST13：`ST13_25`
- WT13 alias：`WT13-25`
- 设计文档：`docs/superpowers/plans/st13-task-packages/ST13_25/ST13_25_DESIGN.md`

## 3. 进入实现前置条件

- `ST13_25_DESIGN.md` 完成评审。
- `ST13_21`、`ST13_20`、`ST13_24` 的治理输入已稳定。
- 用户明确授权后续 Basic Memory / Superpowers 写回。
- required doc slot State Update 已由 W13-E8.5 单独完成；后续仍需 readiness 复核和 formal window 用户确认。

## 4. formal window 前置条件

- 用户另窗确认可以打开 `ST13_25` formal window。
- `DOC_STATE.yaml` required doc slot 已由 W13-E8.5 State Update 窗口写入并通过 validate/evaluate；后续仍需单独状态窗口处理 formal window。
- 本文档不得自行声明 formal window open。

## 5. implementation packet 前置条件

- formal window 已打开。
- 治理写回 checklist、验证命令、fallback 包和交接格式已明确。
- allowed modify paths、forbidden paths、required tests、acceptance criteria 均已填实。
- 当前窗口不生成 implementation packet。

## 6. 允许修改范围

未来治理收口窗口才可能允许：

- Basic Memory 写回，且必须先检索、写入、回读验证。
- Superpowers 计划更新，且必须引用当前事实源。
- 父索引、OQ/DD、执行日志、进展、成熟度的治理收口更新。

当前 W13-E9 不写 Basic Memory。

## 7. 禁止修改范围

- 当前不写 Basic Memory。
- 当前不调用 Basic Memory。
- 不修改 `DOC_STATE.yaml`。
- 不生成 implementation packet。
- 不打开 formal window。
- 不创建 `apps/**`、`infra/**`、`tools/**`、`tests/**`。
- 不执行 Git 提交或推送。

## 8. 预期实现步骤

1. 检查父索引和双文档引用。
2. 检查 OQ / DD / backlog-roadmap 是否闭环。
3. 运行 validate/evaluate 和关键词扫描。
4. 如获授权，执行 Basic Memory 检索、写入、回读验证。
5. 输出收口报告和 fallback 包。

以上步骤中的 Basic Memory 写回当前不执行。

## 9. 验证命令

未来治理收口窗口至少需要：

```bash
python -m tools.doc_governor.cli validate-state --input docs/governance/DOC_STATE.yaml
python -m tools.doc_governor.cli evaluate-state --input docs/governance/DOC_STATE.yaml
```

如涉及测试，还应使用：

```bash
python -m tools.test_runner.run_tests
```

## 10. 测试要求

- validate-state / evaluate-state 不退化。
- 关键词扫描覆盖 task id、双文档路径、状态词、OQ。
- 禁止范围检查确认未修改 `docs/governance/**`、`apps/**`、`infra/**`、`tools/**`、`tests/**`。
- Basic Memory 写回如发生，必须有 readback 验证。
- contract_refined 不得写成治理已收口或实现完成。

## 11. 回退策略

- 文档回退：回退本双文档和父索引引用。
- Basic Memory 回退：若写入失败，不强行覆盖；输出 fallback 包。
- 状态回退：必须另开 State Update 或治理窗口；本文档不得直接修改 `DOC_STATE.yaml`。

## 12. 日志 / 观测要求

治理收口应记录：

- 执行窗口。
- 修改文件清单。
- 验证命令和结果。
- 写回对象。
- 未完成项。
- 后续窗口建议。

## 13. 安全 / 隐私检查

- Basic Memory 和 Superpowers 写回不得包含真实简历、provider key、私有知识库内容。
- 收口报告不得把 archive 历史文档误写成当前事实源。
- 不得将 proposed-default 写成 confirmed，除非用户已确认。

## 14. 交接输出格式

未来治理收口窗口必须输出：

- confirmed 结论。
- 风险和限制。
- 验证结果。
- 后续 State Update / Basic Memory / formal window 建议。
- fallback 包，如写回失败。

## 15. Basic Memory / Superpowers 写回要求

未来写回必须：

- 先检索，避免重复。
- 写入 confirmed、风险、下一步、验证结果。
- 回读验证。
- 显式使用白名单目录。

当前 W13-E9 不写 Basic Memory，不调用 Basic Memory，不更新 Superpowers 外部状态。

## 16. 当前未放行实现说明

`ST13_25_IMPLEMENTATION.md` 的存在和 contract_refined 状态都不等于 implementation-ready。当前不写 Basic Memory，不调用 Basic Memory，不生成 implementation packet，不打开 formal window，不修改 `DOC_STATE.yaml`。
