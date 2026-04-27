# M06 模拟面试、上下文与导出 - 模块设计

## 0. Workbench MVP 当前需求与设计输入

- 当前需求输入：`docs/requirements/workbench-mvp/`。
- 当前设计输入：`docs/design/workbench-mvp/`。
- 重点引用：`scope.md`、`information-architecture.md`、`object-model-rag-multiround-backend.md`。
- 模块承接摘要：模拟记录列表、发起模拟、面试台、上下文包、多轮状态机和模拟复盘输入。
- 后续补齐项：按记录列表默认入口、打磨模式和压力面模式重切会话链路。
- 边界：本节只记录模块摘要、入口关系和后续补齐项；不复制正式设计正文，不提升模块成熟度，不放行 formal window、implementation packet 或代码实现。

## 1. 文档定位

- 本文档用于把模块需求转为模块级结构设计。
- 当前状态：仅有骨架。

## 2. 模块职责边界

- 模块职责：定义模拟面试会话、上下文包、问题来源、消息流、报告与导出。
- 上游依赖：M03、M04、M05
- 下游承接：ST06_01、ST06_02、ST06_03

## 3. 计划中的组件拆分
- ST06_01 面试会话创建与列表：定义模拟面试列表、新建页和会话对象的首轮边界。
- ST06_02 上下文包与问题来源规则：明确 source priority、search snapshot 消费边界和问题生成引用规则。
- ST06_03 消息流、trace、报告与导出：定义答题接口、trace、会话完成、轻量报告和导出链路。

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
