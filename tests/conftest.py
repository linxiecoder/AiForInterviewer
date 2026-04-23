from pathlib import Path

from tools.testing.temp_artifacts import (
    create_managed_temp_root_guard,
    create_repo_temp_dir_guard,
    managed_temp_root_guard_enabled,
    repo_temp_dir_guard_enabled,
)


def pytest_sessionstart(session) -> None:
    repo_root = Path(__file__).resolve().parents[1]
    guards = []
    if repo_temp_dir_guard_enabled():
        guards.append(create_repo_temp_dir_guard(repo_root))
    if managed_temp_root_guard_enabled():
        guards.append(create_managed_temp_root_guard())
    session.config._test_temp_dir_guards = guards


def pytest_sessionfinish(session, exitstatus: int) -> None:
    guards = getattr(session.config, "_test_temp_dir_guards", [])
    if not guards:
        session.config._repo_temp_dir_leaks = []
        return

    leaks: list[str] = []
    for guard in guards:
        leaks.extend(guard.find_unexpected_directories())
    leaks = sorted(set(leaks))
    session.config._repo_temp_dir_leaks = leaks
    if leaks and exitstatus == 0:
        session.exitstatus = 1


def pytest_terminal_summary(terminalreporter, exitstatus: int, config) -> None:
    leaks = getattr(config, "_repo_temp_dir_leaks", [])
    if not leaks:
        return

    terminalreporter.section("test temp directory leaks")
    terminalreporter.write_line(
        "unexpected directories remained after the test run:"
    )
    for leak in leaks:
        terminalreporter.write_line(f"- {leak}")
