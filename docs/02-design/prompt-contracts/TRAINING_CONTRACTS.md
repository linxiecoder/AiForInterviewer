---
title: TRAINING_CONTRACTS
type: design
status: draft-f4-prompt-contracts
owner: AI / Prompt 架构
source_task: AIFI-PROMPT-001
parent: docs/02-design/PROMPT_SPEC.md
permalink: ai-for-interviewer/docs/02-design/prompt-contracts/training-contracts
---

# TRAINING_CONTRACTS

## 1. 文件声明

- 本文件是 `docs/02-design/PROMPT_SPEC.md` 的子文档。
- 主 `PROMPT_SPEC.md` 的 Contract Catalog 是 canonical registry。
- 本文件不得自行新增未登记 ID。
- 本文件不得改变 contract ID、名称、目标或状态。
- 本文件不定义 API endpoint、数据库 schema、provider、模型参数、向量库或 embedding。
- 本文件不关闭 `F4_TECH_DESIGN` UNKNOWN。
- 本文件不把 `AIFI-PROMPT-001` 标记为 DONE。

## 2. 当前状态

Training contracts 当前均为 Stub。本文只同步主 catalog 的轻量摘要，后续授权前不得填充详细正文、输出 schema、校验规则、失败处理或持久化交接细则。

## 3. Catalog 摘要

| Contract ID | 名称 | 目标 | 状态 |
|---|---|---|---|
| `P-TRAINING-001` | Training Recommendation | 生成训练建议 | Stub |
| `P-TRAINING-002` | Training Priority Ranking | 训练建议排序 | Stub |
| `P-TRAINING-003` | Training Result Review | 训练结果复盘 | Stub |

## 4. 后续填充边界

- 后续填充必须先更新或确认主 `PROMPT_SPEC.md` 的 canonical registry。
- 未获得后续授权前，本文件不得把 Stub contract 扩写为 Draft 正文。
- 本文件不得替代 `API_SPEC.md`、`DATA_MODEL.md` 或 `SECURITY_PRIVACY.md`。
