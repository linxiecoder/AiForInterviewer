# ST13_13 评分体系设计说明

## 1. 文档定位

本文档定义 `ST13_13` 在 `R0-Final-04` 中的最小评分边界。它只用于推进评分体系的 gate、formal window 与 implementation packet，不直接实现业务代码。

`ST13_13` 只覆盖 R0 最小 `0-100` 评分。复盘摘要由 `ST13_15` 承接，Markdown 导出由 `ST13_19` 承接，测试 / 验收输入引用 `ST13_24`，持久化复用 `ST13_20`。

## 2. 子任务目标

- 为 R0 提供基于 `ST13_12` interview session 的最小 `0-100` score。
- 支持 deterministic scoring rule 或经 `ST13_11` provider boundary 的 provider-assisted scoring。
- 将 score、生成状态、版本和 trace metadata 写入 `ST13_20` minimal persistence 的 session payload。
- 保持 validation、missing session 404、provider failure 与 stable error envelope 兼容。
- 为 `ST13_15` review summary 和 `ST13_19` Markdown export 提供可消费的评分输入。

## 3. 范围

### 3.1 进入 R0-Final-04

- 对已完成或进行中的 interview session 生成最小 `0-100` score。
- 输出 score number / integer，并保证边界在 `0-100`。
- 输出最小 scoring metadata：`content_version`、`scoring_strategy`、`generated_at` 或等价字段。
- 允许 deterministic scoring rule，或通过 `ST13_11` provider boundary 生成评分摘要后归一化为 `0-100`。
- provider failure、validation error、missing session 404 均映射到稳定 error envelope。
- score payload 可保存到 `ST13_20` session payload，不新增 full DB、ORM、migration。

### 3.2 不进入 R0-Final-04

- full scoring platform。
- 多维评分平台、评分运营后台或复杂校准系统。
- full RAG evidence quality platform。
- training center 或弱点训练闭环。
- asset archive、PDF export、frontend。
- full DB、ORM、migration 或 repository layer。

## 4. 技术方案

- 新增最小 scoring service，输入为 `InterviewSession`、turns、answers 和必要 metadata。
- scoring service 可以使用 deterministic rule；若使用 provider，必须调用 `ST13_11` provider boundary，不得直接访问真实 provider SDK / HTTP client。
- API route 只暴露 R0 最小评分触发 / 读取能力，并沿用 `ST13_21` error envelope。
- 持久化只复用 `ST13_20` minimal store 的 session payload，不引入正式数据库 schema。
- score 输出供 `ST13_15` 和 `ST13_19` 读取，不把 review 或 export 逻辑塞入评分服务。

## 5. 依赖与输入

- `ST13_11`：provider boundary、deterministic provider、provider failure mapping。
- `ST13_12`：interview session、turns、answers、history。
- `ST13_20`：minimal persistence 与 session payload。
- `ST13_21`：API boundary 与 stable error envelope。
- `ST13_24`：评分 / 复盘 / Markdown 导出的 required tests 与 DoD 输入。

## 6. 边界约束

- 本设计只授权 R0 最小评分，不授权完整评分平台。
- 不要求真实外部网络或真实 API key 才能测试。
- RAG evidence 可以作为后续设计输入，但 R0-Final-04 不实现 full RAG，也不让 RAG 直接决定分数。
- 若实现需要修改 forbidden paths，应停止并回到 governance 窗口。

