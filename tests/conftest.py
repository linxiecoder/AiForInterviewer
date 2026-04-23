from pathlib import Path

from tools.testing.temp_artifacts import (
    create_repo_temp_dir_guard,
    repo_temp_dir_guard_enabled,
)


def pytest_sessionstart(session) -> None:
    if not repo_temp_dir_guard_enabled():
        session.config._repo_temp_dir_guard = None
        return

    repo_root = Path(__file__).resolve().parents[1]
    session.config._repo_temp_dir_guard = create_repo_temp_dir_guard(repo_root)


def pytest_sessionfinish(session, exitstatus: int) -> None:
    guard = getattr(session.config, "_repo_temp_dir_guard", None)
    if guard is None:
        session.config._repo_temp_dir_leaks = []
        return

    leaks = guard.find_unexpected_directories()
    session.config._repo_temp_dir_leaks = leaks
    if leaks and exitstatus == 0:
        session.exitstatus = 1


def pytest_terminal_summary(terminalreporter, exitstatus: int, config) -> None:
    leaks = getattr(config, "_repo_temp_dir_leaks", [])
    if not leaks:
        return

    terminalreporter.section("repo temp directory leaks")
    terminalreporter.write_line(
        "unexpected directories remained in the repository after the test run:"
    )
    for leak in leaks:
        terminalreporter.write_line(f"- {leak}")
