class GoalEngine:

    @staticmethod
    def select_next(state):
        # MVP：简单取下一个未完成 goal
        goals = state.get("goals", ["g-1", "g-2", "g-3"])

        done = {h["goal"] for h in state.get("history", [])}

        for g in goals:
            if g not in done:
                return g

        return None

    @staticmethod
    def peek_next(state):
        return GoalEngine.select_next(state)