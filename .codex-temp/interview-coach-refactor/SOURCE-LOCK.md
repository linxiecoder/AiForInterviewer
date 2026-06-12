---
title: interview-coach-refactor 来源锁定
type: temporary-source-lock
status: locked
---

# SOURCE-LOCK

## AIForInterviewer 来源

- 当前分支: `feature/interview-coach-refactor`
- 当前 commit: `cc94db2d79365b021e33096a4988c4864fd743d8`
- 分支守卫结果: 通过。
- 工作区守卫结果: 仅存在 `.codex-temp/interview-coach-refactor/` 下的未跟踪文件。
- `AGENTS.md` 守卫结果: 无 status entry，且无 diff。

## interview-coach-skill 来源

- Repository URL: `https://github.com/noamseg/interview-coach-skill.git`
- 本地临时路径: `/tmp/interview-coach-skill`
- clone 后观察到的远端默认分支: `origin/main`
- 本地检出分支: `main`
- analyzed commit hash: `634a8dd8689e0420c21e5f0c8ae3cfa9e1a7ab7e`
- commit date: `2026-05-29`
- 来源可用性: 已可用，并已为 Round 1 discovery 锁定。
- 来源放置规则: interview-coach-skill source 保持在 AIForInterviewer 仓库之外。

## 证据规则

- 每一条 interview-coach finding 必须引用 `/tmp/interview-coach-skill` 中的真实文件路径。
- 后续任何 Adopt / Adapt 决策都必须同时具备 interview-coach evidence 和明确的 AIForInterviewer landing point。
- 任何没有 AIForInterviewer landing point 的能力，后续只能按 Defer / Reject / Research-only 处理。
- Round 1 只做 discovery：不预设任何 AIForInterviewer implementation landing point。
- 不得把 interview-coach 的 command system、directory structure、prompt wording、workflow wording 或 output wording 直接复制进 AIForInterviewer。
- `.codex-temp/interview-coach-refactor/` 下的临时材料不是 active docs、ADR、backlog、delivery plan 或 implementation facts。
