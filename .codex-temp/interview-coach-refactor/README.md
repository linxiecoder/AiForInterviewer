---
title: interview-coach-refactor 临时工作区
type: temporary-workspace
status: draft
---

# interview-coach 吸收重构临时工作区

本目录只用于 `feature/interview-coach-refactor` feature branch 生命周期内的 interview-coach 吸收重构临时材料。这里的内容只服务于临时发现、收敛和后续授权窗口，不是 active docs、roadmap、delivery plan、ADR、backlog 或长期事实源。

最终合入 `main` 前，需要把仍需保留的结论压缩迁移到 `docs/active/interview-coach-refactor.md`。最终 `main` 不应保留 `.codex-temp/interview-coach-refactor/`。

本目录中的临时规则不得写入 `AGENTS.md`；仓库长期协作规则仍以 `AGENTS.md` 和 `docs/00-governance/DOCS_INDEX.md` 登记的 active docs 为准。

## 目录结构

| 路径 | 用途 |
| --- | --- |
| `01-discovery/` | 发现材料、现状读取和证据摘录 |
| `02-scope/` | 范围边界、非目标和风险边界 |
| `03-requirements/` | 临时需求整理和吸收映射草案 |
| `04-design/` | 临时设计草案和方案比较 |
| `05-goals/` | 受控目标切片和退出条件草案 |
| `06-implementation/` | 实施记录和变更批次草案 |
| `07-validation/` | 验证计划、命令和结果摘录 |
| `08-migration/` | 迁移、合并和清理记录 |

## 分支与合并策略

- 工作流使用一个 feature branch 承载临时工作区和后续授权变更。
- 最终只执行一次合并进入 `main`。
- 合并前必须确认临时材料中需要转正的内容已迁入仓库 active docs 或代码事实源。
- 合并前必须确认 `.codex-temp/interview-coach-refactor/` 不作为 `main` 上的长期目录保留。
