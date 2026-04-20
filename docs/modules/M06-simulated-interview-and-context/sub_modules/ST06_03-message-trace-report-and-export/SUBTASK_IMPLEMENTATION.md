# ST06_03 消息流、trace、报告与导出 - 子任务实施

## 1. 文档定位

- 本文档用于承接子任务级实施准备。
- 当前成熟度：仅有骨架。
- 当前状态：尚不可直接实施。

## 2. 实施目标

- 在子任务设计成熟后，把“消息流、trace、报告与导出”转成可交给 Codex 的实施单元。

## 3. 前置条件

- SUBTASK_DESIGN.md 达到“可作为下游输入”。
- 父模块相关设计文档达到至少“可评审”。
- 关联开放问题中不存在阻塞项。

## 4. 计划中的目标区域
- apps/api/app/services/interview_engine.py
- apps/api/app/services/interview_export_service.py
- apps/web/src/components/interview/**

## 5. 计划中的实施产出
- 消息与 trace 设计
- 报告对象草图
- 导出实施边界

## 6. 当前缺失项

- 精确文件范围未定稿。
- 实施步骤未细化。
- 验证命令/验证方法未定稿。
- DoD 与回滚方案未定稿。

## 7. 进入可直接用于实施前必须补充

- 目标
- 修改范围
- 实施步骤
- 验证方法
- 完成定义（DoD）
- 回滚方案

## 8. 当前阻塞项
- OQ-012 上下文包中的 source priority 与引用摘要规则如何固定

## 9. 实施后必须回写的文档

- TASK_INDEX.md。
- EXECUTION_LOG.md。
- ../../MODULE_TASK_INDEX.md。
- ../../MODULE_EXECUTION_LOG.md。
- DOCUMENT_MATURITY.md。
- DOCUMENT_PROGRESS.md。
