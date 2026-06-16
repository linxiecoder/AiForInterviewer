# 自定义输出目录说明

推荐把过程材料放到：

```text
tmp/goal_for_refactor/<run_id>_loop/
```

例如：

```text
tmp/goal_for_refactor/260617_loop/
```

目录结构：

```text
tmp/goal_for_refactor/260617_loop/
  docs/
    00_LOOP_PROTOCOL.md
    01_GOAL_QUEUE.md
    02_PASS_CRITERIA.md
    03_SCOPE_BOUNDARY.md
  goals/
    goal-001.md
    goal-002.md
  prompts/
    04_AUTOMATION_PROMPT.md
  runs/
    .gitkeep
  scripts/
    goal_gate.py
    validate_goal.py
    goal_status.py
  state.json
  BOOTSTRAP_REPORT.md
```

稳定 Skill 可保留在：

```text
.agents/skills/goal-loop-engineer/SKILL.md
```

原因：Codex App / Codex CLI 通过 `.agents/skills` 扫描 Skill；如果执行器 Skill 也放进 tmp，`Use $goal-loop-engineer` 可能无法被发现。
