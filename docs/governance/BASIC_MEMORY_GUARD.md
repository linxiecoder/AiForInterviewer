---
title: BASIC_MEMORY_GUARD
type: note
permalink: ai-for-interviewer/docs/governance/basic-memory-guard
Owner: 文档治理
Last Updated: 2026-05-02
Scope: Basic Memory 写入路由、包装器和只读/写回边界
Depends On: AGENTS.md, docs/governance/DOC_AUTOMATION.md
Supersedes: none
---

# Basic Memory Guard 运行说明

## 1. 定位与范围

`tools/basic_memory_guard/` 是当前仓库对 Basic Memory 的最小程序级包装器。

它的目标不是替代 Skill，也不是替代 Basic Memory 本体，而是把以下高风险约束硬化到代码层：

- 禁止写错目录
- 禁止直接写根目录或 `notes/`
- 写前必须检索，尽量避免重复创建同主题记忆
- `20-decisions` 必须经过明确确认状态
- 写入后必须回读验证
- Basic Memory 命令失败时必须输出可复制待写入包

边界说明：

- Skill 负责行为编排，例如什么时候应该读上下文、什么时候应该沉淀总结。
- wrapper 负责写入硬约束与最小检索降级。
- Basic Memory 负责长期上下文沉淀。
- `doc_governor` / `docs/governance/DOC_STATE.yaml` 仍然是正式结构化真值来源。
- Basic Memory 中的内容不能反推正式状态，也不能替代 `confirm-transition` 等正式治理链路。

## 2. CLI 入口

统一入口：

```powershell
python -m tools.basic_memory_guard.cli --help
```

当前提供 4 个动作：

- `preflight-read`
- `safe-write`
- `verify-readback`
- `emit-fallback`

## 3. 命令说明

### 3.1 preflight-read

用于任务开始前读取上下文。

示例：

```powershell
python -m tools.basic_memory_guard.cli preflight-read `
  --project AiForInterviewer `
  --query "AiForInterviewer 项目主目标" `
  --query "文档治理" `
  --page-size 5
```

行为：

- 优先执行 `hybrid -> default search-notes`
- `vector` 可用时作为增强，不可用时只记 warning，不中断任务
- 失败后继续降级到 `title -> permalink -> recent activity -> directory listing -> read_note`

### 3.2 safe-write

用于安全写入或更新上下文。

示例：

```powershell
python -m tools.basic_memory_guard.cli safe-write `
  --project AiForInterviewer `
  --directory "30-open-questions" `
  --title "问题：是否需要把 Basic Memory wrapper 接入统一工具链" `
  --content "# 问题：是否需要把 Basic Memory wrapper 接入统一工具链`n`n- 当前先落最小 CLI。"
```

### 3.3 verify-readback

用于对指定笔记做回读验证。

示例：

```powershell
python -m tools.basic_memory_guard.cli verify-readback `
  --project AiForInterviewer `
  --directory "00-project" `
  --title "AiForInterviewer 项目主目标" `
  --expected-fragment "模拟面试项目"
```

### 3.4 emit-fallback

用于在 Basic Memory 命令失败时输出可复制待写入包。

示例：

```powershell
python -m tools.basic_memory_guard.cli emit-fallback `
  --project AiForInterviewer `
  --directory "90-session-summaries" `
  --title "会话总结：Basic Memory wrapper 第一版" `
  --reason "bm tool write-note failed" `
  --content "# 会话总结：Basic Memory wrapper 第一版`n`n- 已完成程序级硬约束封装。"
```

## 4. 已硬化的规则

### 4.1 目录与写入边界

`safe-write` 当前只允许写入以下目录：

- `00-project`
- `20-decisions`
- `30-open-questions`
- `60-risks-constraints`
- `90-session-summaries`

禁止：

- 根目录
- 空目录
- `notes/`
- 白名单之外的任意目录

### 4.2 决策写入边界

当目录为 `20-decisions` 时，必须显式传入以下确认状态之一：

- `confirmed`
- `accepted`
- `approved`

否则程序直接拒绝写入。

### 4.3 写前检索与去重

`safe-write` 在写入前必须执行检索。

当前策略：

- 若命中目标目录中的同标题笔记，则默认更新，不默认新建
- 若命中多个同标题笔记，或命中近似主题但无法安全判定，应拒绝写入并输出 fallback 包
- 若已存在完全相同的内容片段，则跳过重复追加

### 4.4 写后回读验证

`safe-write` 每次成功调用 `write-note` / `edit-note` 后，都会立即执行 `verify-readback`。

验证项包括：

- 回读命中目录是否正确
- 目标内容片段是否真正存在于回读内容中

任一项失败，都视为本轮写入不可信，必须输出 fallback 包。

### 4.5 检索降级

检索顺序固定为：

1. `hybrid`
2. 普通 `search-notes`
3. `vector` 增强检索
4. `title`
5. `permalink`
6. `recent activity`
7. 本地目录 listing
8. `read_note`

说明：

- `vector search` 只是增强，不是唯一检索路径。
- 向量检索失败不能等同于“没有历史记忆”。
- 第一版 wrapper 通过 `bm` CLI 调用 Basic Memory，不直接接 Basic Memory Python API。
- 所有 `bm` 命令集中封装在 `tools/basic_memory_guard/bm_cli.py`，避免散落到多个脚本。

## 5. 与 Skill / Basic Memory / doc_governor 的协作关系

推荐分层如下：

- `requirements-context` Skill：在任务开始前决定需要读取哪些上下文
- `requirements-memory` Skill：在任务结束时决定应该沉淀哪些内容
- `tools/basic_memory_guard/`：把写入目录、去重、回读验证、fallback 做成程序级硬约束
- Basic Memory：保存长期上下文
- `doc_governor` / `DOC_STATE.yaml`：维护正式状态真值

这意味着：

- Skill 可以决定“要不要写”
- wrapper 决定“能不能安全写”
- `doc_governor` 决定“正式状态是什么”

## 6. 当前已知边界

第一版 wrapper 仍保留以下人工确认边界：

- “是否属于正式决策”仍需要调用方显式传入确认状态，wrapper 只做拒绝与放行，不替代拍板
- 命中近似主题但无法判定是否同一笔记时，wrapper 会保守拒绝，而不是自动 merge
- `bm tool write-note` 当前 CLI 参数能力有限，wrapper 第一版只依赖标题、目录、内容与标签，不承担更复杂的元数据写入
- 为避免污染真实 Basic Memory，本仓库测试只做 fake client 单元测试与只读 CLI 验证，不自动创建真实校验笔记

## 7. 验证与临时产物约束

建议验证命令：

```powershell
python -m unittest tests.basic_memory_guard.test_guard -v
python -m unittest tests.test_temp_artifact_policy -v
python -m tools.basic_memory_guard.cli --help
```

本仓库中与 wrapper 相关的测试统一使用 `tools.testing.temp_artifacts.ManagedTempArtifacts`。

因此：

- 测试临时目录会进入固定受管根目录
- 测试结束自动清理
- 不应在仓库根目录留下 `_tmp`、`tmp`、`temp` 等测试目录
