# M08 复盘与回放 - 模块设计

## 0. Workbench MVP Design Canon 承接

- 当前正式设计事实源：`docs/design/workbench-mvp/`。
- 重点引用：`information-architecture.md`、`object-model-rag-multiround-backend.md`、`scoring-review-export-dod.md`。
- 模块承接摘要：模拟复盘、真实面试复盘、逐题拆解、导出和归档入口。
- 后续补齐项：按真实 / 模拟复盘、低置信度校对、Markdown 导出和证据展示补齐模块设计。
- 边界：本节只记录模块摘要、入口关系和后续补齐项；不复制正式设计正文，不提升模块成熟度，不放行 formal window、implementation packet 或代码实现。

## 1. 文档定位

- 本文档用于把模块需求转为模块级结构设计。
- 当前状态：仅有骨架。

## 2. 模块职责边界

- 模块职责：定义复盘总对象、真实面试导入、逐题分析、从模拟面试生成复盘以及导出。
- 上游依赖：M06、M07
- 下游承接：ST08_01、ST08_02、ST08_03

## 3. 计划中的组件拆分
- ST08_01 复盘总对象与列表/详情：定义 review 对象、列表页和详情页的首轮结构。
- ST08_02 真实面试导入与逐题分析：明确真实面试输入格式、拆题分析和结果结构。
- ST08_03 模拟面试复盘回放与导出：明确从 interview 到 review 的映射规则和导出边界。

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
