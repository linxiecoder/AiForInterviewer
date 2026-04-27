# M04 匹配分析与训练证据 - 模块设计

## 0. Workbench MVP 当前需求与设计输入

- 当前需求输入：`docs/requirements/workbench-mvp/`。
- 当前设计输入：`docs/design/workbench-mvp/`。
- 重点引用：`scope.md`、`object-model-rag-multiround-backend.md`、`scoring-review-export-dod.md`。
- 模块承接摘要：岗位-简历绑定、匹配分析、评分证据、规则版本和训练信号输入。
- 后续补齐项：补齐评分证据、规则版本、WeaknessItem 输入和异常路径。
- 边界：本节只记录模块摘要、入口关系和后续补齐项；不复制正式设计正文，不提升模块成熟度，不放行 formal window、implementation packet 或代码实现。

## 1. 文档定位

- 本文档用于把模块需求转为模块级结构设计。
- 当前状态：仅有骨架。

## 2. 模块职责边界

- 模块职责：定义岗位-简历绑定、匹配分析、评分依据和训练证据输出。
- 上游依赖：M03
- 下游承接：ST04_01、ST04_02、ST04_03

## 3. 计划中的组件拆分
- ST04_01 岗位-简历绑定与输入契约：明确绑定关系、输入对象和多简历绑定边界。
- ST04_02 匹配分析、评分与证据：沉淀分析对象、评分口径、证据结构和版本字段。
- ST04_03 分析展示与训练入口：连接岗位详情中的分析区块、弱项摘要和训练入口。

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
