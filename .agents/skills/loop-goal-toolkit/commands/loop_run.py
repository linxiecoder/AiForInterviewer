from core.goal_engine import GoalEngine
from core.loop_engine import build_prompt
from core.executor_codex import CodexExecutor
from core.validator import Validator
from core.state_store import StateStore

def main():
    state = StateStore.load()

    goal = GoalEngine.select_next(state)
    if not goal:
        return {"status": "NO_GOAL"}

    prompt = build_prompt(goal)

    result = CodexExecutor.run(prompt)

    validation = Validator.check(goal, result)

    StateStore.update(goal, result, validation)

    return {
        "goal": goal,
        "status": validation,
        "output": result
    }

if __name__ == "__main__":
    print(main())