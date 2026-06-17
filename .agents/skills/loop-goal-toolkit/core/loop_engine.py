def build_prompt(goal):
    return f"""
GOAL:
{goal}

INSTRUCTION:
Execute this goal using Codex CLI.

OUTPUT REQUIREMENTS:
- changes
- explanation
- status
"""