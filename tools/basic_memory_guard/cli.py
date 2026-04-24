from __future__ import annotations

import argparse
import json
from dataclasses import asdict, is_dataclass
from typing import Any

from .guard import MemoryGuardService, SafeWriteRequest
from .policy import DEFAULT_MEMORY_ROOT, DEFAULT_PROJECT


def build_parser() -> argparse.ArgumentParser:
    shared_parser = argparse.ArgumentParser(add_help=False)
    shared_parser.add_argument(
        "--project",
        default=DEFAULT_PROJECT,
        help="Basic Memory 项目名。",
    )
    shared_parser.add_argument(
        "--memory-root",
        default=DEFAULT_MEMORY_ROOT,
        help="Basic Memory 本地项目根目录。",
    )

    parser = argparse.ArgumentParser(
        prog="python -m tools.basic_memory_guard.cli",
        description="Basic Memory 程序级读写包装器。",
        parents=[shared_parser],
    )
    subparsers = parser.add_subparsers(dest="command")

    preflight = subparsers.add_parser(
        "preflight-read",
        help="任务开始前读取上下文。",
        parents=[shared_parser],
    )
    preflight.add_argument("--query", action="append", required=True, help="检索词，可重复。")
    preflight.add_argument("--page-size", type=int, default=5, help="每轮最大返回数。")
    preflight.add_argument("--timeframe", default="7d", help="recent activity 时间窗口。")

    safe_write = subparsers.add_parser(
        "safe-write",
        help="安全写入或更新上下文。",
        parents=[shared_parser],
    )
    safe_write.add_argument("--directory", required=True, help="目标目录。")
    safe_write.add_argument("--title", required=True, help="笔记标题。")
    safe_write.add_argument("--content", required=True, help="写入内容。")
    safe_write.add_argument("--topic", help="主题，用于补充检索。")
    safe_write.add_argument("--query", action="append", default=[], help="额外检索词，可重复。")
    safe_write.add_argument(
        "--decision-status",
        help="决策状态，仅允许 confirmed/accepted/approved 写入 20-decisions。",
    )
    safe_write.add_argument("--tag", action="append", default=[], help="标签，可重复。")

    verify = subparsers.add_parser(
        "verify-readback",
        help="写后回读验证。",
        parents=[shared_parser],
    )
    verify.add_argument("--directory", required=True, help="目标目录。")
    verify.add_argument("--title", required=True, help="笔记标题。")
    verify.add_argument(
        "--expected-fragment",
        action="append",
        default=[],
        help="回读时必须存在的片段，可重复。",
    )

    fallback = subparsers.add_parser(
        "emit-fallback",
        help="输出可复制待写入包。",
        parents=[shared_parser],
    )
    fallback.add_argument("--directory", required=True, help="目标目录。")
    fallback.add_argument("--title", required=True, help="笔记标题。")
    fallback.add_argument("--content", required=True, help="待写入内容。")
    fallback.add_argument("--reason", required=True, help="失败原因。")
    fallback.add_argument("--query", action="append", default=[], help="检索词，可重复。")
    fallback.add_argument("--decision-status", help="决策状态。")
    fallback.add_argument("--tag", action="append", default=[], help="标签，可重复。")

    return parser


def _to_json(value: Any) -> str:
    if is_dataclass(value):
        value = asdict(value)
    return json.dumps(value, ensure_ascii=False, indent=2)


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    try:
        args = parser.parse_args(argv)
    except SystemExit as exc:
        return int(exc.code or 0)

    if not args.command:
        parser.print_help()
        return 1

    service = MemoryGuardService(memory_root=args.memory_root)

    if args.command == "preflight-read":
        result = service.preflight_read(
            queries=args.query,
            project=args.project,
            page_size=args.page_size,
            timeframe=args.timeframe,
        )
        print(_to_json(result))
        return 0 if result.ok else 1

    if args.command == "safe-write":
        result = service.safe_write(
            SafeWriteRequest(
                project=args.project,
                directory=args.directory,
                title=args.title,
                content=args.content,
                topic=args.topic,
                queries=list(args.query or []),
                decision_status=args.decision_status,
                tags=list(args.tag or []),
            )
        )
        print(_to_json(result))
        return 0 if result.ok else 1

    if args.command == "verify-readback":
        result = service.verify_readback(
            title=args.title,
            directory=args.directory,
            expected_fragments=list(args.expected_fragment or []),
            project=args.project,
        )
        print(_to_json(result))
        return 0 if result.ok else 1

    if args.command == "emit-fallback":
        result = service.emit_fallback(
            project=args.project,
            directory=args.directory,
            title=args.title,
            content=args.content,
            reason=args.reason,
            queries=list(args.query or []),
            decision_status=args.decision_status,
            tags=list(args.tag or []),
        )
        print(_to_json(result))
        return 0

    parser.print_help()
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
