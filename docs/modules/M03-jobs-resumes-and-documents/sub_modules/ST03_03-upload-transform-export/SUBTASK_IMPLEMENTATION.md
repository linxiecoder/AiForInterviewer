# ST03_03 上传、转换与导出链路 - 子任务实施

## 1. 文档定位

- 本文档用于承接子任务级实施准备。
- 当前成熟度：仅有骨架。
- 当前状态：尚不可直接实施。

## 2. 实施目标

- 在子任务设计成熟后，把“上传、转换与导出链路”转成可交给 Codex 的实施单元。

## 3. 前置条件

- SUBTASK_DESIGN.md 达到“可作为下游输入”。
- 父模块相关设计文档达到至少“可评审”。
- 关联开放问题中不存在阻塞项。

## 4. 计划中的目标区域
- apps/api/app/services/storage_service.py
- apps/api/app/services/pdf_to_markdown_service.py
- apps/api/app/tasks/**

## 5. 计划中的实施产出
- 上传与转换流程设计
- 导出策略
- 对象存储约束

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
- OQ-006 Markdown 预览与导出是否必须共用同一渲染链
- OQ-007 上传、转换、导出在 P1 中哪些必须异步

## 9. 实施后必须回写的文档

- TASK_INDEX.md。
- EXECUTION_LOG.md。
- ../../MODULE_TASK_INDEX.md。
- ../../MODULE_EXECUTION_LOG.md。
- DOCUMENT_MATURITY.md。
- DOCUMENT_PROGRESS.md。
