# Workbench MVP Design Canon

## 1. 定位

`docs/design/workbench-mvp/` 是 AI 模拟面试一期工作台 MVP 的当前正式设计事实源。后续范围判断、模块承接、任务治理和实现准备均应优先引用本目录。

本目录只承载产品与设计事实，不代表：

- `DOC_STATE.yaml` 已放行新的 formal window。
- 已生成 implementation packet。
- 已允许创建或修改业务代码目录。
- 已完成 M01-M10 的模块级详细设计。

## 2. 文档索引

| 文档 | 职责 | 当前事实源 |
| --- | --- | --- |
| [scope.md](scope.md) | 一期 MVP 范围、角色边界、in-scope / out-of-scope、后续 backlog 边界 | 是 |
| [information-architecture.md](information-architecture.md) | 页面与信息架构、用户路径、对象可见性、状态流转、模块承接关系 | 是 |
| [object-model-rag-multiround-backend.md](object-model-rag-multiround-backend.md) | 核心对象模型、RAG、多轮、后端服务边界和状态字段 | 是 |
| [scoring-review-export-dod.md](scoring-review-export-dod.md) | 评分、复盘、导出、Definition of Done、质量门禁和验收标准 | 是 |

## 3. 事实优先级

当不同文档表述冲突时，按以下顺序处理：

1. 本目录中的当前正式设计事实源。
2. `DESIGN_DECISIONS.md` 与 `OPEN_QUESTIONS.md` 中已 confirmed 的决策和问题归并。
3. `PLAN_LATEST.md`、`TASK_INDEX.md`、`MODULE_INDEX.md` 的当前推进和治理索引。
4. 历史 W13 plans、旧 P1 设计稿、旧实现计划和 archive 文档。

历史 W13 plans 只保留为迁移来源和桥接入口，不再作为 current design fact source。若其正文与本目录冲突，以本目录为准。

## 4. 与其他文档的关系

| 文档族 | 关系 |
| --- | --- |
| 旧 W13 plans | 已降级为短桥接文档，仅记录迁移来源和跳转关系。 |
| `docs/modules/M01-M10/**` | 只能承接模块摘要、入口关系和后续补齐项，不复制本目录正文。 |
| `TASK_INDEX.md` / ST13 双文档 | 作为任务治理和开窗准备材料，可引用本目录事实，但不因引用本目录而自动获得实施资格。 |
| backlog / roadmap | 记录后续待办、归档候选和路线图，不覆盖本目录的当前事实。 |
| archive 文档 | 仅保留历史追溯价值，不作为 current fact source。 |

## 5. 已确认的总体事实

- 一期目标是 AI 模拟面试工作台级 MVP，不是 W10 `apps/web` mock 原型的直接续作。
- 一期包含真实 LLM、完整登录 / 权限、服务端保存、历史模拟记录、评分复盘、RAG / 知识库、多轮高阶面试、Markdown 下载 / 复制、薄弱项体系、训练抽屉和资产归档。
- 默认入口是历史模拟记录列表，也可从岗位详情发起模拟面试。
- 面试台是执行页，完成后回写历史记录与复盘。
- 多轮不等于固定 3 轮。固定 3 轮只能作为压力面题组策略候选，不能作为所有模式的总规则。
- `ST13_01~ST13_25` 是当前任务治理入口，但仍不能进入实现、formal window 或 packet。

## 6. 未完成事项

- M01-M10 仍需后续模块窗口补齐模块级详细设计。
- formal window open 仍需单独确认。
- implementation packet 仍需单独生成和验证。
- 具体数据库 schema、API route、prompt 模板、provider 配置、权限矩阵和 UI 组件实现仍属于后续实施设计或实现阶段。
