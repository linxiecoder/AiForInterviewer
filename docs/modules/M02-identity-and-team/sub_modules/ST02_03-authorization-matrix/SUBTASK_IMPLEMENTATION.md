# ST02_03 授权矩阵与管理员/成员边界 - 子任务实施

## 1. 文档定位

- 本文档用于承接子任务级实施准备。
- 当前成熟度：仅有骨架。
- 当前状态：尚不可直接实施。

## 2. 实施目标

- 在子任务设计成熟后，把“授权矩阵与管理员/成员边界”转成可交给 Codex 的实施单元。

## 3. 前置条件

- `SUBTASK_DESIGN.md` 达到“可作为下游输入”。
- 父模块相关设计文档达到至少“可评审”。
- OQ-004 与 OQ-005 不再构成阻塞。

## 4. 计划中的目标区域

- `apps/api/app/api/routes/**`
- `apps/api/app/services/authorization/**`
- `apps/web/src/lib/permissions/**`
- `apps/web/src/app/(dashboard)/**`

## 5. 计划中的实施产出

- 权限判断策略
- 管理员/成员边界约束
- 401 / 403 / 跨团队访问处理
- 基础权限测试

## 6. 当前缺失项

- 精确文件范围未定稿。
- 实施步骤未细化。
- 验证命令与验证方法未定稿。
- DoD 与回滚方案未定稿。

## 7. 进入可直接用于实施前必须补充

- 目标
- 修改范围
- 实施步骤
- 验证方法
- 完成定义（DoD）
- 回滚方案

## 8. 当前阻塞项

- OQ-004 P1 鉴权机制采用固定 Bearer token、JWT 还是 session cookie。
- OQ-005 团队管理员与普通成员的权限矩阵是否先只覆盖 P1 页面。

## 9. 实施后必须回写的文档

- TASK_INDEX.md
- EXECUTION_LOG.md
- ../../MODULE_TASK_INDEX.md
- ../../MODULE_EXECUTION_LOG.md
- DOCUMENT_MATURITY.md
- DOCUMENT_PROGRESS.md
