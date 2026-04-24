from __future__ import annotations

import json
import subprocess
from dataclasses import dataclass
from typing import Any, Sequence

from .policy import DEFAULT_PROJECT


@dataclass
class BmCommandError(RuntimeError):
    command: list[str]
    returncode: int
    stdout: str
    stderr: str

    def __post_init__(self) -> None:
        command_text = " ".join(self.command)
        message = self.stderr.strip() or self.stdout.strip() or "bm command failed"
        RuntimeError.__init__(self, f"{command_text} failed: {message}")


class BmCliClient:
    def __init__(self, executable: str = "bm") -> None:
        self.executable = executable

    def search_notes(
        self,
        query: str,
        *,
        mode: str,
        project: str = DEFAULT_PROJECT,
        page_size: int = 10,
    ) -> dict[str, Any]:
        args = ["tool", "search-notes", query, "--project", project, "--page-size", str(page_size)]
        if mode == "hybrid":
            args.append("--hybrid")
        elif mode == "vector":
            args.append("--vector")
        elif mode == "title":
            args.append("--title")
        elif mode == "permalink":
            args.append("--permalink")
        elif mode != "default":
            raise ValueError(f"unsupported search mode: {mode}")
        return self._run_json(args)

    def read_note(
        self,
        identifier: str,
        *,
        project: str = DEFAULT_PROJECT,
        include_frontmatter: bool = True,
    ) -> dict[str, Any]:
        args = ["tool", "read-note", identifier, "--project", project]
        if include_frontmatter:
            args.append("--include-frontmatter")
        return self._run_json(args)

    def recent_activity(
        self,
        *,
        project: str = DEFAULT_PROJECT,
        timeframe: str = "7d",
        page_size: int = 10,
    ) -> list[dict[str, Any]]:
        return self._run_json(
            [
                "tool",
                "recent-activity",
                "--project",
                project,
                "--timeframe",
                timeframe,
                "--page-size",
                str(page_size),
            ]
        )

    def write_note(
        self,
        *,
        title: str,
        folder: str,
        content: str,
        project: str = DEFAULT_PROJECT,
        tags: Sequence[str] | None = None,
    ) -> str:
        args = [
            "tool",
            "write-note",
            "--title",
            title,
            "--folder",
            folder,
            "--content",
            content,
            "--project",
            project,
        ]
        for tag in tags or ():
            args.extend(["--tags", tag])
        return self._run_text(args)

    def edit_note(
        self,
        identifier: str,
        *,
        operation: str,
        content: str,
        project: str = DEFAULT_PROJECT,
    ) -> str:
        args = [
            "tool",
            "edit-note",
            identifier,
            "--operation",
            operation,
            "--content",
            content,
            "--project",
            project,
        ]
        return self._run_text(args)

    def _run_json(self, args: list[str]) -> Any:
        output = self._run_text(args)
        try:
            return json.loads(output)
        except json.JSONDecodeError as exc:
            raise BmCommandError(
                [self.executable, *args],
                0,
                output,
                f"invalid JSON from bm: {exc}",
            ) from exc

    def _run_text(self, args: list[str]) -> str:
        command = [self.executable, *args]
        try:
            completed = subprocess.run(
                command,
                capture_output=True,
                text=True,
                encoding="utf-8",
                errors="replace",
                check=False,
            )
        except FileNotFoundError as exc:
            raise BmCommandError(command, 127, "", str(exc)) from exc
        if completed.returncode != 0:
            raise BmCommandError(
                command,
                completed.returncode,
                completed.stdout,
                completed.stderr,
            )
        return completed.stdout
