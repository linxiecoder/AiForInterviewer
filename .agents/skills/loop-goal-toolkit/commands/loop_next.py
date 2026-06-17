from core.goal_engine import GoalEngine
from core.state_store import StateStore

def main():
    state = StateStore.load()
    return GoalEngine.select_next(state)

if __name__ == "__main__":
    print(main())