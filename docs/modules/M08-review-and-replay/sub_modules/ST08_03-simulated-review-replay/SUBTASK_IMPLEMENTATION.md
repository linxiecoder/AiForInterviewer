# ST08_03 模拟面试复盘回放与导出 - 子任务实施

## 1. 文档定位

- 本文档用于承接子任务级实施准备。
- 当前成熟度：仅有骨架。
- 当前状态：尚不可直接实施。

## 2. 实施目标

- 在子任务设计成熟后，把“模拟面试复盘回放与导出”转成可交给 Codex 的实施单元。

## 3. 前置条件

- SUBTASK_DESIGN.md 达到“可作为下游输入”。
- 父模块相关设计文档达到至少“可评审”。
- 关联开放问题中不存在阻塞项。

## 4. 计划中的目标区域
- apps/api/app/services/review_engine.py
- apps/api/app/api/routes/reviews.py
- apps/web/src/components/review/**

## 5. 计划中的实施产出
- 映射逻辑设计
- 回放摘要结构
- 导出策略

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
- OQ-010 归档粒度是整份资产、片段还是题目级
- OQ-014 模拟面试、打磨模式和复盘是否共用同一评估口径

## 9. 实施后必须回写的文档

- TASK_INDEX.md。
- EXECUTION_LOG.md。
- ../../MODULE_TASK_INDEX.md。
- ../../MODULE_EXECUTION_LOG.md。
- DOCUMENT_MATURITY.md。
- DOCUMENT_PROGRESS.md。
