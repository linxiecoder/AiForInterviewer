from core.validator import Validator
from core.state_store import StateStore

def main():
    state = StateStore.load()
    return Validator.audit_all(state)

if __name__ == "__main__":
    print(main())