from pathlib import Path

from tools.testing.temp_artifacts import (
    create_managed_temp_root_guard,
    create_repo_temp_dir_guard,
    find_repo_temp_dir_residuals,
    managed_temp_root_guard_enabled,
    repo_temp_dir_guard_enabled,
)


def pytest_sessionstart(session) -> None:
    repo_root = Path(__file__).resolve().parents[1]
    guards = []
    if repo_temp_dir_guard_enabled():
        guards.append(create_repo_temp_dir_guard(repo_root))
        session.config._repo_temp_like_preexisting = find_repo_temp_dir_residuals(repo_root)
    else:
        session.config._repo_temp_like_preexisting = []
    if managed_temp_root_guard_enabled():
        guards.append(create_managed_temp_root_guard())
    session.config._test_temp_dir_guards = guards


def pytest_sessionfinish(session, exitstatus: int) -> None:
    repo_root = Path(__file__).resolve().parents[1]
    guards = getattr(session.config, "_test_temp_dir_guards", [])

    leaks: list[str] = []
    for guard in guards:
        leaks.extend(guard.find_unexpected_directories())
    if repo_temp_dir_guard_enabled():
        leaks.extend(find_repo_temp_dir_residuals(repo_root))
        preexisting = getattr(session.config, "_repo_temp_like_preexisting", [])
        if preexisting:
            leaks.extend(
                [f"preexisting temp-like directory: {item}" for item in preexisting]
            )
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
