# M09 训练中心与薄弱项生命周期 - 模块设计

## 0. Workbench MVP 当前需求与设计输入

- 当前需求输入：`docs/requirements/workbench-mvp/`。
- 当前设计输入：`docs/design/workbench-mvp/`。
- 重点引用：`scope.md`、`object-model-rag-multiround-backend.md`、`scoring-review-export-dod.md`。
- 模块承接摘要：WeaknessItem、训练抽屉、证据聚合、消减、停练和训练生命周期。
- 后续补齐项：区分薄弱项中心与待打磨执行层，补齐训练状态和回写边界。
- 边界：本节只记录模块摘要、入口关系和后续补齐项；不复制正式设计正文，不提升模块成熟度，不放行 formal window、implementation packet 或代码实现。

## 1. 文档定位

- 本文档用于把模块需求转为模块级结构设计。
- 当前状态：仅有骨架。

## 2. 模块职责边界

- 模块职责：定义薄弱项聚合、训练抽屉、待打磨入列和生命周期状态流转。
- 上游依赖：M04、M07、M08
- 下游承接：ST09_01、ST09_02、ST09_03

## 3. 计划中的组件拆分
- ST09_01 薄弱项聚合与训练中心：定义 weakness item、聚合维度、排序方式和训练中心页。
- ST09_02 训练抽屉与待打磨入列：定义训练抽屉动作、待打磨清单和跨模块入列方式。
- ST09_03 生命周期、消减与停练规则：定义弱项的状态机、消减和停练规则。

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
