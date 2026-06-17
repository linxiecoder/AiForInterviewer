import subprocess

class CodexExecutor:

    @staticmethod
    def run(prompt):
        return subprocess.run(
            ["codex", "exec", prompt],
            capture_output=True,
            text=True
        ).stdout