class Validator:

    @staticmethod
    def check(goal, result):
        if not result:
            return "FAIL"
        return "PASS"

    @staticmethod
    def audit_all(state):
        return {
            "total": len(state.get("history", [])),
            "status": "ok"
        }