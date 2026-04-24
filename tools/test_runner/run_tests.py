from __future__ import annotations

import argparse
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="统一测试入口：使用专用 basetemp 执行 pytest，并在结束后清理临时目录。"
    )
    parser.add_argument(
        "--pytest-args",
        nargs=argparse.REMAINDER,
        help="透传给 pytest 的附加参数。例如：--pytest-args -k temp_policy -q",
    )
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    repo_root = Path(__file__).resolve().parents[2]
    base_temp = Path(tempfile.mkdtemp(prefix="ai-for-interviewer-pytest-"))

    cmd = [sys.executable, "-m", "pytest", "--basetemp", str(base_temp)]
    if args.pytest_args:
        cmd.extend(args.pytest_args)
    else:
        cmd.append("tests")

    try:
        completed = subprocess.run(cmd, cwd=repo_root)
        return completed.returncode
    finally:
        shutil.rmtree(base_temp, ignore_errors=True)


if __name__ == "__main__":
    raise SystemExit(main())

