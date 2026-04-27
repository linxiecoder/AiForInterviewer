# ST13_25 IMPLEMENTATION：文档治理 / 收口 / Basic Memory

## 1. 文档状态

- 状态：`draft`
- 文档性质：ST13 任务实施说明；只定义后续执行条件，不是 implementation packet
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

- formal window open 前置确认需在后续状态窗口完成。
- 治理写回 checklist、验证命令、fallback 包和交接格式已明确。
- allowed modify paths、forbidden paths、required tests、acceptance criteria 均已填实。
- 当前窗口不生成 implementation packet。
- 文档治理任务通常不生成业务 implementation packet；若未来确需治理 packet，必须由用户单独确认 packet 类型、目标、允许路径、禁止路径、required tests、acceptance criteria、回退策略和是否涉及 Basic Memory 写回。

## 6. 允许修改范围

未来治理收口窗口才可能允许：

- Basic Memory 写回，且必须先检索、写入、回读验证。
- Superpowers 计划更新，且必须引用当前输入。
- 父索引、OQ/DD、执行日志、进展、成熟度的治理收口更新。

当前 W13-E9 不写 Basic Memory。

## 7. 禁止修改范围

- 当前不写 Basic Memory。
- 当前不调用 Basic Memory。
- 当前不调用外部记忆写回流程。
- 不修改 `DOC_STATE.yaml`。
- 不生成 implementation packet。
- 不打开 formal window。
- 不创建 `apps/**`、`infra/**`、`tools/**`、`tests/**`。
- 不执行 Git 提交或推送。

### 7.1 W13-E14-B 当前窗口硬约束

当前 W13-E14-B 只补齐 formal window 前置材料，不进入实现：

- 当前不写 Basic Memory，不执行 Basic Memory 写入、更新或回读。
- 当前不调用外部记忆写回流程，不把聊天内容视为已写记忆。
- 当前不修改 `docs/governance/DOC_STATE.yaml` 或 `docs/governance/**`。
- 当前不生成 implementation packet，不调用 open-window，不标记 implementation-ready。
- 当前 formal window 保持 closed；facts-only candidate 推荐不等于 formal window open。
- 当前只允许修改 `ST13_25_DESIGN.md` 与 `ST13_25_IMPLEMENTATION.md`。
- 当前发现父索引、State Update、Basic Memory、Superpowers 或 archive 需要同步时，只交接给 W13-E14-Merge 或后续授权窗口。

## 8. 预期实现步骤

1. 检查父索引和双文档引用。
2. 检查 OQ / DD / backlog-roadmap 是否闭环。
3. 运行 validate/evaluate 和关键词扫描。
4. 如获授权，执行 Basic Memory 检索、写入、回读验证。
5. 输出收口报告和 fallback 包。

以上步骤中的 Basic Memory 写回当前不执行。

### 8.1 未来写回执行顺序

未来如用户另窗授权 Basic Memory / Superpowers 写回，执行顺序必须固定为：

1. 先确认授权范围：是否允许写 Basic Memory、是否允许更新 Superpowers、是否允许修改父索引、是否允许触碰 archive。
2. 先检索：查找同主题笔记、近似会话总结、已确认决策和风险约束，避免重复写入。
3. 再写入：只写 confirmed 结论、风险、下一步和验证结果，不写 proposed-default 为 confirmed，不写未授权实现事实。
4. 再回读验证：确认写入路径、标题、正文摘要和关键结论可读。
5. 写回失败时输出 fallback 包：包含主题、目录建议、摘要、confirmed 结论、遗留风险、验证结果、下一步建议和后续补写正文。
6. 最终提交和整体收口由未来 merge 总控窗口负责，本文件不替代总控提交、状态写回或 Basic Memory 授权。

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
- 收口报告不得把 archive 历史文档误写成当前输入。
- 不得将 proposed-default 写成 confirmed，除非用户已确认。

## 14. 交接输出格式

未来治理收口窗口必须输出：

- 收口类型：完整收口、部分收口、失败收口或回退收口。
- confirmed 结论。
- 修改范围。
- 风险和限制。
- 验证结果。
- 剩余风险。
- 后续 State Update / Basic Memory / formal window 建议。
- fallback 包，如写回失败。

## 15. Basic Memory / Superpowers 写回要求

未来写回必须：

- 先检索，避免重复。
- 写入 confirmed、风险、下一步、验证结果。
- 回读验证。
- 显式使用白名单目录。
- 只更新当前输入或对应计划，不更新 archive 历史文档作为当前事实。
- 不把 proposed-default、near-ready 或 facts-only candidate 推荐写成 confirmed。

当前 W13-E14-B 不写 Basic Memory，不调用 Basic Memory，不调用外部记忆写回流程，不更新 Superpowers 外部状态。

## 16. 当前未放行实现说明

`ST13_25_IMPLEMENTATION.md` 的存在和 contract_refined 状态都不等于 implementation-ready。当前不写 Basic Memory，不调用 Basic Memory，不生成 implementation packet，不打开 formal window，不修改 `DOC_STATE.yaml`。

## 17. W13-E13.5 candidate 表达策略同步

`ST13_25` 在 W13-E13.5 后继续只保留文档层 `formal_window_candidate_recommended`。正式状态层暂不写 `candidate_status=candidate`，不直接写 `readiness=downstream_ready`。

该策略不新增治理实现任务，不改变本文件的 implementation plan only 定位。下一轮如继续，只能先验证 facts-only Candidate Preview；当前仍不写 Basic Memory，不调用 Basic Memory，不生成 implementation packet，不打开 formal window。

## 18. W13-E13.8 facts-only 正式 State Update 同步

W13-E13.8 已在 docs/governance/previews 路径 Preview 严格全绿后，将 `ST13_25.facts` 的 facts-only candidate 推荐字段写入正式 `DOC_STATE.yaml`：

- `formal_window_candidate_recommended=true`
- `formal_window_candidate_source=W13-E11 candidate evaluation`
- `formal_window_candidate_review_status=pending_confirmation`
- `formal_window_candidate_state=document_layer_recommended`
- `formal_window_candidate_notes=formal window closed; implementation-ready false; implementation packet forbidden`

该写入不改变本文件的实施边界：formal window 仍关闭，implementation-ready 仍为 false，implementation packet 仍禁止，Basic Memory 仍不得在本窗口写入。
