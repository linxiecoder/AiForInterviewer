# 模块待确认问题

## 1. 文档定位

- 本文档用于记录当前模块内部仍未收敛、会影响模块设计或子任务推进的问题。
- 本文档是模块级问题清单，不代替根目录 `OPEN_QUESTIONS.md` 的全局问题总表。
- 当前模块主责 Codex 在推进模块文档时，若发现新的模块级问题，应优先记录在这里。
- 若问题已明显影响多个模块、多个子任务或共享契约，应进一步上升到根目录 `OPEN_QUESTIONS.md`。

## 2. 状态定义

- `open`：问题已识别，但尚无明确默认方案
- `confirmed`：问题已确认，后续文档应按确认结果回写
- `historical`：历史问题，当前事实已回收到 Workbench MVP 正式设计事实源或全局确认层
- `superseded`：问题已失效或已被其他新口径替代

## 3. 问题表

| MQ ID | 问题 | 状态 | 影响范围 | 当前建议 | 是否需上升到全局 | 需回写文档 |
| --- | --- | --- | --- | --- | --- | --- |
| MQ-001 | 模板占位：本模块是否负责 XXX | superseded | 无当前影响 | 这是旧模板示例，不作为当前模块问题 | 否 | 无 |
| MQ-002 | 模板占位：异常路径是否需要回滚 | superseded | 无当前影响 | 这是旧模板示例，不作为当前模块问题 | 否 | 无 |
| OQ-009 | Embedding 与向量化来源如何确定 | historical | `MODULE_REQUIREMENTS.md`、`MODULE_TASK_INDEX.md`、`ST06_02` | 已由 Workbench MVP 正式设计事实源和 `FC-05` / `DD-021` 覆盖：RAG / 知识库进入一期，支持混合检索，失败时降级继续并标注证据缺口 | 否 | 已在本模块文档改为历史引用 |
| OQ-011 | Search snapshot 的来源只做导入还是需要抓取 | historical | `MODULE_REQUIREMENTS.md`、`MODULE_TASK_INDEX.md`、`ST06_02` | 已由 Workbench MVP 正式设计事实源和 `FC-18` / `DD-008` 覆盖：Search snapshot 只导入不抓取 | 否 | 已在本模块文档改为历史引用 |
| OQ-012 | 上下文包中的 source priority 与引用摘要规则如何固定 | historical | `MODULE_REQUIREMENTS.md`、`MODULE_TASK_INDEX.md`、`ST06_02`、`ST06_03` | 已由 Workbench MVP 正式设计事实源和 `FC-05` / `DD-021` 覆盖：RAG 引用、检索结果与证据缺口进入面试、评分和复盘证据链 | 否 | 已在本模块文档改为历史引用 |
| OQ-018 | 管理台是否负责 search snapshot 导入与运维 | historical | `MODULE_REQUIREMENTS.md`、`MODULE_TASK_INDEX.md`、`ST06_02` | 已由 Workbench MVP 正式设计事实源和 `FC-18` 覆盖：管理台负责导入与运维入口，完整运维能力低干扰占位 | 否 | 已在本模块文档改为历史引用 |

## 4. 当前高优问题

| 优先级 | MQ ID | 当前阻塞文档 | 原因 | 本轮处理要求 |
| --- | --- | --- | --- | --- |
| - | - | - | 当前无模块级 open 问题 | 旧 MQ/OQ 只保留 historical / superseded 记录，不阻断模块文档继续补齐 |

## 5. 需要升级到全局的问题

> 只有当问题影响多个模块、共享契约或全局技术口径时，才列在这里，等待总控 Codex 同步到根目录 `OPEN_QUESTIONS.md`。

- 暂无

## 6. 使用说明

- 模块 Codex 每轮推进模块文档时，都应检查是否新增了模块级问题。
- 若问题只影响当前模块，优先记录在本文件。
- 若问题已影响多个模块、共享契约或全局技术口径，应在本文件记录后，同时上报总控 Codex，并推动更新根目录 `OPEN_QUESTIONS.md`。
- 当问题状态从 `open` 变为 `confirmed`、`historical` 或 `superseded` 时，应同步回写受影响模块文档。
