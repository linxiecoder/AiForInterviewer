# 项目协作规则

本文档是当前项目的高优先级协作入口，用于沉淀全局规则并索引核心文档。

## 1. 全局规则

### 1.1 文档语言规则

默认情况下，当前项目中的文档主体必须使用中文，代码与技术标识按常规技术规范保持英文。详细规则见：

- [项目语言规范](docs/project-language-rules.md)

### 1.2 文档索引规则

后续新增的正式项目文档，应先补充到本文档的索引中，再继续扩展内容，避免规则、设计和计划分散失管。

建议纳入索引的文档类型包括：

- 全局规范
- 产品设计稿
- 实现计划
- 开发约定
- 操作手册

### 1.3 文档治理规则

本仓库的文档治理细则定义在 [`DOC_GOVERNANCE.md`](docs/DOC_GOVERNANCE.md)。

当任务涉及以下任一事项时，必须先阅读并遵守 [`DOC_GOVERNANCE.md`](docs/DOC_GOVERNANCE.md)：
- 文档成熟度评估
- 文档进展更新
- 多 Codex 并行分工
- 模块文档完善
- 子任务文档完善
- 需求变更回写
- 共享契约冲突处理
- 子任务是否具备可实施条件的判断

如果 `AGENTS.md` 与 [`DOC_GOVERNANCE.md`](docs/DOC_GOVERNANCE.md) 看似冲突：
- 目录结构、角色边界、全局总则以 `AGENTS.md` 为准
- 文档治理细节、成熟度规则、进展规则、回写规则以 [`DOC_GOVERNANCE.md`](docs/DOC_GOVERNANCE.md) 为准

### 1.4 Markdown 安全读写规则

- 涉及 `.md` 文件的读取、编辑、重写或乱码修复时，优先使用全局 skill `markdown-safe-read-write`。
- 在 Windows 环境下处理 Markdown 时，必须显式使用 UTF-8 读写，并在写后从磁盘回读验证，避免把错误解码后的内容再次保存。
- 发现 `�`、异常 `?` 或 `妯 / 鍏 / 鏂 / 鐩 / 锛 / 闂 / 鎴` 等典型乱码片段时，应先诊断根因，不要直接覆盖原文件。

## 2. 当前文档索引

### 2.1 规范

- [项目语言规范](docs/project-language-rules.md)

### 2.2 设计

- [AI 模拟面试 P1 文本版闭环设计稿](docs/superpowers/specs/2026-04-20-ai-interview-p1-design.md)

### 2.3 计划

- [AI 模拟面试 P1 MVP 实现计划](docs/superpowers/plans/2026-04-20-ai-interview-p1-implementation.md)

### 2.4 全局文档体系

- [AI 模拟面试 P1 最新文档总控](PLAN_LATEST.md)
- [AI 模拟面试 P1 任务索引](TASK_INDEX.md)
- [AI 模拟面试 P1 执行日志](EXECUTION_LOG.md)
- [AI 模拟面试 P1 技术标准](TECHNICAL_STANDARDS.md)
- [AI 模拟面试 P1 设计决策](DESIGN_DECISIONS.md)
- [AI 模拟面试 P1 模块索引](MODULE_INDEX.md)
- [AI 模拟面试 P1 待确认问题](OPEN_QUESTIONS.md)
- [AI 模拟面试 P1 文档成熟度](DOCUMENT_MATURITY.md)
- [AI 模拟面试 P1 文档进展](DOCUMENT_PROGRESS.md)

### 2.5 模块目录

- [AI 模拟面试 P1 模块文档目录](docs/modules)

## 3. 执行说明

- 若后续规则与普通说明文档冲突，以本文档和用户最新要求为准。
- 若新增文档会影响实现、协作或交付方式，应先更新本文档索引，再继续扩展实现。
