---
name: aifi-commit-readiness-gate
description: Use when AiForInterviewer work needs SAFE TO COMMIT/NOT READY, PR readiness, push, index audit, remote sync, or commit hygiene.
---

# aifi-commit-readiness-gate

## Purpose

判断本轮 AiForInterviewer 变更是否真的可以提交、合并、打包 PR 或推送。核心原则是把代码/测试稳定、git index ready、branch/range clean、remote/PR 可见性分开判断。

本 Skill 不负责实现功能，也不自动 stage、commit、push、merge 或关闭 issue。

## When to use

- 用户要求 `SAFE TO COMMIT` / `NOT READY` 结论。
- pre-commit cleanup、commit-readiness、merge readiness、PR readiness、release closeout gate。
- 测试已通过但 staged / unstaged / untracked 是否匹配提交边界仍不清楚。
- push 被 hook 阻断后，需要只读确认远端状态。
- 需要区分本轮相关改动、既有噪音、无关提交、docs freshness blocker。

不要用于普通实现前的设计判断；那时先用 `aifi-scope-lock` 或对应实现 Skill。

## Required Inputs

1. 目标动作：commit、amend、PR note、push confirmation、merge readiness 或 read-only audit。
2. 目标 base：例如 `main`、`origin/main` 或 upstream。
3. 用户给出的 allowlist、forbidden files、必须运行的验证命令。
4. 是否允许写入 git index 或执行 commit/push。默认不允许。

## Baseline Commands

先运行或读取：

```bash
git branch --show-current
git rev-parse HEAD
git status --short --branch --untracked-files=all
git diff --stat
git diff --cached --stat
git diff --name-status
git diff --cached --name-status
```

如涉及 remote / PR / merge，再运行或读取：

```bash
git rev-list --left-right --count @{u}...HEAD
git rev-list --left-right --count origin/main...HEAD
git log --oneline --decorate origin/main..HEAD
git diff --name-status origin/main...HEAD
git diff --stat origin/main...HEAD
```

如 push 被 hook 阻断，只做只读确认：

```bash
git fetch origin
git ls-remote origin refs/heads/main
git rev-list --left-right --count origin/main...HEAD
```

## Classification

把所有变更分成四类：

1. `in-scope staged`：已 staged 且属于本轮目标。
2. `in-scope unstaged/untracked`：属于本轮目标但还没进入 index。
3. `pre-existing or unrelated`：不属于本轮目标的历史噪音、无关文件或无关 commit。
4. `blocker`：会让 commit/merge/PR/push 结论不成立的项。

不要只用 `git diff --stat` 判断范围。untracked 文件必须用 `git status --short --untracked-files=all` 或 `git ls-files --others --exclude-standard` 核对。

## Verdict Rules

只能输出以下结论之一：

- `SAFE TO COMMIT`：staged index 精确包含本轮应提交文件；没有相关 unstaged/untracked 遗漏；无无关 staged 文件；必需验证通过；branch/range 没有阻断项。
- `NOT READY`：代码或测试可稳定，但 index、untracked、allowlist、branch range、docs freshness、验证证据或 remote 状态不满足。
- `BLOCKED`：发现需要用户决策的范围外改动、无关 commit、hook 阻断、base 不明确、测试真实失败或权限问题。
- `UNKNOWN`：证据不足，不能判断。

测试通过不等于 `SAFE TO COMMIT`。代码稳定和 git index readiness 必须分开写。

## Procedure

1. 读取 `AGENTS.md` 和当前用户 scope。
2. 跑 baseline commands。
3. 对 staged、unstaged、untracked、branch range 做分类。
4. 运行用户要求的验证命令；如果 focused pytest 因 repo-root `tmp/` leak guard 失败，先用 `AI_FOR_INTERVIEWER_ALLOW_TEST_DIR_LEAKS=1` 区分环境噪音和业务失败。
5. 如涉及 PR/merge，检查 `origin/main...HEAD` 或指定 base range 中是否有无关 commit/file。
6. 如涉及 push，被 hook 阻断后不变体重试；改用只读 remote confirmation。
7. 输出 verdict、证据、阻断项和下一步最小动作。

## Output Format

```markdown
## 结论

SAFE TO COMMIT / NOT READY / BLOCKED / UNKNOWN: <一句话理由>

## 代码与测试状态

- commands:
- result:
- unresolved test gaps:

## Git Index Readiness

| 分类 | 文件/提交 | 结论 |
|---|---|---|

## Branch / Remote

- current branch:
- HEAD:
- base/upstream:
- range result:

## Blockers

- ...

## 下一步

- ...
```

## Common Mistakes

- 把 `1356 passed`、`npm run web:test` 通过直接写成 merge-ready。
- 只看 `git diff --stat`，漏掉 untracked docs/tests。
- 只检查 working tree，不检查 staged index 与 intended commit 是否一致。
- push 被 hook 阻断后尝试绕过；应停止并报告，再用只读命令确认远端状态。
- 有无关 commit 时继续跑完整验证；应先做 range triage。
