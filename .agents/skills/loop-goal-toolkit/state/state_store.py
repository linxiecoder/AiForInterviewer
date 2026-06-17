import json
from pathlib import Path

STATE_PATH = Path(__file__).parent.parent / "state/state.json"

class StateStore:

    @staticmethod
    def load():
        if not STATE_PATH.exists():
            return {"current_goal": None, "history": []}
        return json.loads(STATE_PATH.read_text())

    @staticmethod
    def save(state):
        STATE_PATH.write_text(json.dumps(state, indent=2))

    @staticmethod
    def update(goal, result, validation):
        state = StateStore.load()
        state["history"].append({
            "goal": goal,
            "result": str(result),
            "validation": validation
        })
        StateStore.save(state)