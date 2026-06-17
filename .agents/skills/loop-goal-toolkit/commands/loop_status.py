from core.state_store import StateStore

def main():
    state = StateStore.load()
    return {
        "current": state.get("current_goal"),
        "history_size": len(state.get("history", []))
    }

if __name__ == "__main__":
    print(main())