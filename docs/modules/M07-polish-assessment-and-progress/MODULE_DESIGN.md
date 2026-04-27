# M07 打磨模式、评估与进度 - 模块设计

## 0. Workbench MVP 当前需求与设计输入

- 当前需求输入：`docs/requirements/workbench-mvp/`。
- 当前设计输入：`docs/design/workbench-mvp/`。
- 重点引用：`scope.md`、`object-model-rag-multiround-backend.md`、`scoring-review-export-dod.md`。
- 模块承接摘要：打磨模式、ProgressTree、题级反馈、能力树、训练入口和部分导出。
- 后续补齐项：明确打磨模式不固定轮次，并与压力面评分和训练闭环分离。
- 边界：本节只记录模块摘要、入口关系和后续补齐项；不复制正式设计正文，不提升模块成熟度，不放行 formal window、implementation packet 或代码实现。

## 1. 文档定位

- 本文档用于把模块需求转为模块级结构设计。
- 当前状态：仅有骨架。

## 2. 模块职责边界

- 模块职责：定义打磨主题推荐、能力树、逐题评估和进度快照。
- 上游依赖：M06
- 下游承接：ST07_01、ST07_02、ST07_03

## 3. 计划中的组件拆分
- ST07_01 打磨主题推荐与启动：定义主题推荐来源、主题对象和打磨启动页。
- ST07_02 能力树蓝图与节点状态：定义能力蓝图、节点层级、状态和 UI 承载方式。
- ST07_03 逐题评估与进度快照：定义 answer assessment、技术原理卡和进度快照。

## 4. 跨模块协作点

- 需要从上游模块接收输入，再向本模块子任务输出约束。
- 依赖详情见 MODULE_DEPENDENCIES.md。

## 5. 当前设计缺口

- 组件边界仍需进一步量化到 API / schema / logic 三类设计文档。
- 异常路径、失败回滚和数据一致性策略尚未细化。

## 6. 进入可评审前需要补充的内容

- 模块内部组件关系图或文字版职责图。
- 关键交互顺序。
- 错误与回退处理原则。
- 与其他模块的耦合边界。

## 7. 关联文档

- MODULE_REQUIREMENTS.md。
- MODULE_API_DESIGN.md。
- MODULE_SCHEMA_DESIGN.md。
- MODULE_LOGIC_DESIGN.md。
