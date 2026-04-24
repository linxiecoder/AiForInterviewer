from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Iterable

from .bm_cli import BmCliClient, BmCommandError
from .policy import DEFAULT_MEMORY_ROOT, DEFAULT_PROJECT, validate_request


@dataclass
class SearchAttempt:
    mode: str
    query: str
    ok: bool
    hit_count: int = 0
    error: str | None = None


@dataclass
class ReadbackResult:
    ok: bool
    action: str
    title: str
    directory: str
    identifier: str | None = None
    file_path: str | None = None
    reason: str | None = None
    note: dict[str, Any] | None = None
    fallback_package: dict[str, Any] | None = None


@dataclass
class PreflightReadResult:
    ok: bool
    attempts: list[SearchAttempt] = field(default_factory=list)
    hits: list[dict[str, Any]] = field(default_factory=list)
    readbacks: list[dict[str, Any]] = field(default_factory=list)
    recent_activity: list[dict[str, Any]] = field(default_factory=list)
    directory_listing: list[dict[str, str]] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)


@dataclass
class SafeWriteRequest:
    directory: str
    title: str
    content: str
    project: str = DEFAULT_PROJECT
    topic: str | None = None
    queries: list[str] = field(default_factory=list)
    decision_status: str | None = None
    tags: list[str] = field(default_factory=list)


@dataclass
class SafeWriteResult:
    ok: bool
    action: str
    title: str
    directory: str
    identifier: str | None = None
    reason: str | None = None
    verification: ReadbackResult | None = None
    fallback_package: dict[str, Any] | None = None
    attempts: list[SearchAttempt] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)
    matched_note: dict[str, Any] | None = None
    related_hits: list[dict[str, Any]] | None = None
    stale_hit: dict[str, Any] | None = None


class MemoryGuardService:
    SEARCH_MODES = ("hybrid", "default", "vector", "title", "permalink")
    READBACK_LIMIT = 3

    def __init__(
        self,
        *,
        bm_client: BmCliClient | Any | None = None,
        memory_root: str | Path = DEFAULT_MEMORY_ROOT,
    ) -> None:
        self.bm_client = bm_client or BmCliClient()
        self.memory_root = Path(memory_root)

    def preflight_read(
        self,
        *,
        queries: list[str],
        project: str = DEFAULT_PROJECT,
        page_size: int = 5,
        timeframe: str = "7d",
    ) -> PreflightReadResult:
        attempts: list[SearchAttempt] = []
        hits, search_warnings = self._run_search_cascade(
            queries=queries,
            project=project,
            page_size=page_size,
            attempts=attempts,
        )
        recent_activity = self._safe_recent_activity(
            project=project,
            timeframe=timeframe,
            page_size=page_size,
            warnings=search_warnings,
        )
        directory_listing = self._list_directory_entries(limit=page_size)
        readbacks = self._read_top_hits(hits=hits, project=project, warnings=search_warnings)
        ok = bool(hits or recent_activity or directory_listing or readbacks)
        return PreflightReadResult(
            ok=ok,
            attempts=attempts,
            hits=hits,
            readbacks=readbacks,
            recent_activity=recent_activity,
            directory_listing=directory_listing,
            warnings=search_warnings,
        )

    def safe_write(self, request: SafeWriteRequest) -> SafeWriteResult:
        request_content = request.content or ""
        request_title = request.title.strip()
        try:
            normalized = validate_request(request.directory, request.decision_status)
        except ValueError as exc:
            fallback = self.emit_fallback(
                project=request.project,
                directory=(request.directory or "").strip() or "/",
                title=request_title,
                content=request_content,
                reason=str(exc),
                queries=self._build_queries(request),
                decision_status=request.decision_status,
                tags=request.tags,
            )
            return SafeWriteResult(
                ok=False,
                action="rejected",
                title=request_title,
                directory=(request.directory or "").strip(),
                reason=str(exc),
                fallback_package=fallback,
                related_hits=[],
            )

        attempts: list[SearchAttempt] = []
        warnings: list[str] = []
        queries = self._build_queries(request)
        hits, search_warnings = self._run_search_cascade(
            queries=queries,
            project=request.project,
            page_size=10,
            attempts=attempts,
        )
        warnings.extend(search_warnings)

        match, conflict_reason, related_hits = self._select_existing_note(
            title=request_title,
            directory=normalized.directory,
            hits=hits,
            warnings=warnings,
        )

        if conflict_reason:
            fallback = self.emit_fallback(
                project=request.project,
                directory=normalized.directory,
                title=request_title,
                content=request_content,
                reason=conflict_reason,
                queries=queries,
                decision_status=normalized.decision_status,
                tags=request.tags,
            )
            return SafeWriteResult(
                ok=False,
                action="rejected",
                title=request_title,
                directory=normalized.directory,
                reason=conflict_reason,
                fallback_package=fallback,
                attempts=attempts,
                warnings=warnings,
                matched_note=match,
                related_hits=related_hits,
            )

        try:
            if match is not None:
                identifier = (
                    match.get("title")
                    or match.get("permalink")
                    or request_title
                )
                try:
                    current = self.bm_client.read_note(
                        identifier,
                        project=request.project,
                        include_frontmatter=True,
                    )
                except BmCommandError as exc:
                    stale_reason = f"read_note_failed: {exc}"
                    warnings.append("stale_search_hit_found")
                    stale_hit = self._build_stale_hit_payload(
                        match=match,
                        stale_reason=stale_reason,
                        search_attempt=self._find_search_attempt_for_hit(
                            match=match,
                            attempts=attempts,
                        ),
                    )
                    fallback = self.emit_fallback(
                        project=request.project,
                        directory=normalized.directory,
                        title=request_title,
                        content=request_content,
                        reason="stale_or_unreadable_existing_note",
                        queries=queries,
                        decision_status=normalized.decision_status,
                        tags=request.tags,
                    )
                    fallback["stale_hit"] = stale_hit
                    return SafeWriteResult(
                        ok=False,
                        action="rejected",
                        title=request_title,
                        directory=normalized.directory,
                        reason="stale_or_unreadable_existing_note",
                        fallback_package=fallback,
                        attempts=attempts,
                        warnings=warnings,
                        matched_note=match,
                        related_hits=related_hits,
                        stale_hit=stale_hit,
                    )
                stale_reason = self._assess_existing_note_readability(
                    current=current,
                    request=request,
                    match=match,
                )
                if stale_reason:
                    warnings.append("stale_search_hit_found")
                    stale_hit = self._build_stale_hit_payload(
                        match=match,
                        stale_reason=stale_reason,
                        search_attempt=self._find_search_attempt_for_hit(
                            match=match,
                            attempts=attempts,
                        ),
                    )
                    fallback = self.emit_fallback(
                        project=request.project,
                        directory=normalized.directory,
                        title=request_title,
                        content=request_content,
                        reason="stale_or_unreadable_existing_note",
                        queries=queries,
                        decision_status=normalized.decision_status,
                        tags=request.tags,
                    )
                    fallback["stale_hit"] = stale_hit
                    return SafeWriteResult(
                        ok=False,
                        action="rejected",
                        title=request_title,
                        directory=normalized.directory,
                        reason="stale_or_unreadable_existing_note",
                        fallback_package=fallback,
                        attempts=attempts,
                        warnings=warnings,
                        matched_note=match,
                        related_hits=related_hits,
                        stale_hit=stale_hit,
                    )
                current_content = current.get("content") or ""
                if request_content and request_content in current_content:
                    verification = self.verify_readback(
                        title=request_title,
                        directory=normalized.directory,
                        expected_fragments=self._build_verification_fragments(
                            request_content=request_content,
                            mode="updated",
                        ),
                        project=request.project,
                        require_title=True,
                    )
                    return SafeWriteResult(
                        ok=verification.ok,
                        action="skipped-duplicate" if verification.ok else "failed",
                        title=request_title,
                        directory=normalized.directory,
                        identifier=current.get("permalink") or current.get("title"),
                        reason=verification.reason,
                        verification=verification,
                        fallback_package=verification.fallback_package
                        if not verification.ok
                        else None,
                        attempts=attempts,
                        warnings=warnings,
                        matched_note=match,
                        related_hits=related_hits,
                    )
                self.bm_client.edit_note(
                    identifier,
                    operation="append",
                    content=request_content,
                    project=request.project,
                )
                action = "updated"
                operation = "append"
            else:
                self.bm_client.write_note(
                    title=request_title,
                    folder=normalized.directory,
                    content=request_content,
                    project=request.project,
                    tags=request.tags,
                )
                action = "created"
                operation = "create"
                if related_hits:
                    warnings.append("related_hits_found")
        except BmCommandError as exc:
            fallback = self.emit_fallback(
                project=request.project,
                directory=normalized.directory,
                title=request_title,
                content=request_content,
                reason=str(exc),
                queries=queries,
                decision_status=normalized.decision_status,
                tags=request.tags,
            )
            return SafeWriteResult(
                ok=False,
                action="failed",
                title=request_title,
                directory=normalized.directory,
                reason=str(exc),
                fallback_package=fallback,
                attempts=attempts,
                warnings=warnings,
                matched_note=match,
                related_hits=related_hits,
            )

        verification = self.verify_readback(
            title=request_title,
            directory=normalized.directory,
            expected_fragments=self._build_verification_fragments(
                request_content=request_content,
                mode=operation,
            ),
            project=request.project,
            require_title=True,
        )
        fallback = None
        ok = verification.ok
        if not ok:
            fallback = (
                verification.fallback_package
                if verification.fallback_package
                else self.emit_fallback(
                    project=request.project,
                    directory=normalized.directory,
                    title=request.title,
                    content=request_content,
                    reason=verification.reason or "write succeeded but readback verification failed",
                    queries=queries,
                    decision_status=normalized.decision_status,
                    tags=request.tags,
                )
            )
        return SafeWriteResult(
            ok=ok,
            action=action if ok else "failed",
            title=request_title,
            directory=normalized.directory,
            identifier=verification.identifier,
            reason=verification.reason,
            verification=verification,
            fallback_package=fallback,
            attempts=attempts,
            warnings=warnings,
            matched_note=match,
            related_hits=related_hits,
        )

    def verify_readback(
        self,
        *,
        title: str,
        directory: str,
        expected_fragments: list[str],
        project: str = DEFAULT_PROJECT,
        require_title: bool = False,
    ) -> ReadbackResult:
        try:
            normalized = validate_request(directory, None)
        except ValueError as exc:
            return ReadbackResult(
                ok=False,
                action="verify_failed",
                title=title,
                directory=directory,
                reason=str(exc),
            )

        try:
            note = self.bm_client.read_note(
                title,
                project=project,
                include_frontmatter=True,
            )
        except BmCommandError as exc:
            raw_msg = str(exc)
            reason = "note_not_found" if "missing" in raw_msg.lower() else raw_msg
            fallback = self._build_readback_fallback(
                project=project,
                directory=normalized.directory,
                title=title,
                expected_fragments=expected_fragments,
                reason=reason,
                note=None,
            )
            return ReadbackResult(
                ok=False,
                action="verify_failed",
                title=title,
                directory=normalized.directory,
                reason=reason,
                fallback_package=fallback,
                note=None,
            )

        if not isinstance(note, dict):
            fallback = self._build_readback_fallback(
                project=project,
                directory=normalized.directory,
                title=title,
                expected_fragments=expected_fragments,
                reason="note_not_found",
                note=None,
            )
            return ReadbackResult(
                ok=False,
                action="verify_failed",
                title=title,
                directory=normalized.directory,
                reason="note_not_found",
                fallback_package=fallback,
            )

        file_path = note.get("file_path")
        note_title = note.get("title")
        if require_title:
            if not isinstance(note_title, str) or not note_title.strip():
                fallback = self._build_readback_fallback(
                    project=project,
                    directory=normalized.directory,
                    title=title,
                    expected_fragments=expected_fragments,
                    reason="note_title_missing",
                    note=note,
                )
                return ReadbackResult(
                    ok=False,
                    action="verify_failed",
                    title=title,
                    directory=normalized.directory,
                    identifier=note.get("permalink") or note.get("title"),
                    file_path=file_path if isinstance(file_path, str) else None,
                    reason="note_title_missing",
                    note=note,
                    fallback_package=fallback,
                )
            if note_title.strip() != title.strip():
                fallback = self._build_readback_fallback(
                    project=project,
                    directory=normalized.directory,
                    title=title,
                    expected_fragments=expected_fragments,
                    reason="title_mismatch",
                    note=note,
                )
                return ReadbackResult(
                    ok=False,
                    action="verify_failed",
                    title=title,
                    directory=normalized.directory,
                    identifier=note.get("permalink") or note.get("title"),
                    file_path=file_path if isinstance(file_path, str) else None,
                    reason="title_mismatch",
                    note=note,
                    fallback_package=fallback,
                )

        if not isinstance(file_path, str) or not file_path:
            fallback = self._build_readback_fallback(
                project=project,
                directory=normalized.directory,
                title=title,
                expected_fragments=expected_fragments,
                reason="note_not_found",
                note=note,
            )
            return ReadbackResult(
                ok=False,
                action="verify_failed",
                title=title,
                directory=normalized.directory,
                identifier=note.get("permalink") or note.get("title"),
                file_path=file_path if isinstance(file_path, str) else None,
                reason="note_not_found",
                note=note,
                fallback_package=fallback,
            )

        if not file_path.startswith(f"{normalized.directory}/"):
            reason = f"expected note under `{normalized.directory}`, got: {file_path}"
            fallback = self._build_readback_fallback(
                project=project,
                directory=normalized.directory,
                title=title,
                expected_fragments=expected_fragments,
                reason=reason,
                note=note,
            )
            return ReadbackResult(
                ok=False,
                action="verify_failed",
                title=title,
                directory=normalized.directory,
                identifier=note.get("permalink") or note.get("title"),
                file_path=file_path,
                reason=reason,
                note=note,
                fallback_package=fallback,
            )

        content = note.get("content")
        if content is None:
            content = ""
        if not isinstance(content, str):
            content = ""
        normalized_content = content.replace("\r\n", "\n").replace("\r", "\n")
        for fragment in expected_fragments:
            normalized_fragment = fragment.replace("\r\n", "\n").replace("\r", "\n")
            if normalized_fragment and normalized_fragment not in normalized_content:
                reason = f"expected fragment missing: {fragment}"
                fallback = self._build_readback_fallback(
                    project=project,
                    directory=normalized.directory,
                    title=title,
                    expected_fragments=expected_fragments,
                    reason=reason,
                    note=note,
                )
                return ReadbackResult(
                    ok=False,
                    action="verify_failed",
                    title=title,
                    directory=normalized.directory,
                    identifier=note.get("permalink") or note.get("title"),
                    file_path=file_path,
                    reason=reason,
                    note=note,
                    fallback_package=fallback,
                )

        return ReadbackResult(
            ok=True,
            action="verified",
            title=title,
            directory=normalized.directory,
            identifier=note.get("permalink") or note.get("title"),
            file_path=file_path,
            note=note,
        )

    def emit_fallback(
        self,
        *,
        project: str,
        directory: str,
        title: str,
        content: str,
        reason: str,
        queries: list[str] | None = None,
        decision_status: str | None = None,
        tags: list[str] | None = None,
    ) -> dict[str, Any]:
        package = {
            "project": project,
            "directory": directory,
            "title": title,
            "decision_status": decision_status,
            "queries": list(queries or []),
            "tags": list(tags or []),
            "reason": reason,
            "content": content,
            "copyable_markdown": "\n".join(
                [
                    f"# {title}",
                    "",
                    f"- project: {project}",
                    f"- directory: {directory}",
                    f"- reason: {reason}",
                    *( [f"- decision_status: {decision_status}"] if decision_status else [] ),
                    "",
                    content,
                ]
            ),
        }
        return package

    def _build_readback_fallback(
        self,
        *,
        project: str,
        directory: str,
        title: str,
        expected_fragments: list[str],
        reason: str,
        note: dict[str, Any] | None,
    ) -> dict[str, Any]:
        expected_fragment = expected_fragments[0] if expected_fragments else None
        fallback = self.emit_fallback(
            project=project,
            directory=directory,
            title=title,
            content="",
            reason=reason,
            queries=[f"title:{title}"],
        )
        fallback["expected_fragment"] = expected_fragment
        fallback["expected_fragments"] = list(expected_fragments)
        fallback["manual_recommended_action"] = (
            "请手动确认该笔记是否存在；内容缺失时可直接创建或重新执行 safe-write。"
        )
        fallback["read_note_preview"] = note
        return fallback

    def _build_queries(self, request: SafeWriteRequest) -> list[str]:
        ordered = [request.title, request.topic, *request.queries]
        seen: set[str] = set()
        queries: list[str] = []
        for item in ordered:
            value = (item or "").strip()
            if not value:
                continue
            lowered = value.lower()
            if lowered in seen:
                continue
            queries.append(value)
            seen.add(lowered)
        return queries or [request.title]

    def _run_search_cascade(
        self,
        *,
        queries: Iterable[str],
        project: str,
        page_size: int,
        attempts: list[SearchAttempt],
    ) -> tuple[list[dict[str, Any]], list[str]]:
        unique_hits: dict[tuple[str, str], dict[str, Any]] = {}
        warnings: list[str] = []
        for query in queries:
            for mode in self.SEARCH_MODES:
                try:
                    response = self.bm_client.search_notes(
                        query,
                        mode=mode,
                        project=project,
                        page_size=page_size,
                    )
                except BmCommandError as exc:
                    attempts.append(
                        SearchAttempt(
                            mode=mode,
                            query=query,
                            ok=False,
                            error=str(exc),
                        )
                    )
                    warnings.append(str(exc))
                    continue

                results = list(response.get("results", []))
                attempts.append(
                    SearchAttempt(
                        mode=mode,
                        query=query,
                        ok=True,
                        hit_count=len(results),
                    )
                )
                for item in results:
                    key = (
                        item.get("file_path", ""),
                        item.get("title", ""),
                    )
                    unique_hits[key] = item
                if results:
                    break
        return list(unique_hits.values()), warnings

    def _select_existing_note(
        self,
        *,
        title: str,
        directory: str,
        hits: list[dict[str, Any]],
        warnings: list[str],
    ) -> tuple[dict[str, Any] | None, str | None, list[dict[str, Any]]]:
        exact_matches: list[dict[str, Any]] = []
        related_hits: list[dict[str, Any]] = []
        target = title.strip().lower()
        normalized_directory = directory.strip().lower()

        for item in hits:
            hit_title = item.get("title")
            if not isinstance(hit_title, str) or not hit_title.strip():
                warnings.append("incomplete_search_hit_ignored")
                continue

            if hit_title.strip().lower() == target:
                exact_matches.append(item)
                if not isinstance(item.get("file_path"), str) or not item.get("file_path"):
                    warnings.append("incomplete_search_hit_ignored")
                if not isinstance(item.get("permalink"), str) or not item.get("permalink"):
                    warnings.append("incomplete_search_hit_ignored")
                continue

            related_hits.append(item)
            if not isinstance(item.get("permalink"), str) or not item.get("permalink"):
                warnings.append("related_hit_incomplete")
                continue

        if not exact_matches:
            return None, None, related_hits

        in_directory = [
            item
            for item in exact_matches
            if (
                isinstance(item.get("file_path"), str)
                and item.get("file_path").startswith(f"{directory}/")
            )
        ]
        if len(in_directory) == 1:
            return in_directory[0], None, related_hits
        if len(in_directory) > 1:
            return None, f"目录 `{normalized_directory}` 下存在同名标题重复记录: {title}", related_hits
        if any(
            isinstance(item.get("file_path"), str)
            and item.get("file_path")
            and not item.get("file_path").startswith(f"{directory}/")
            for item in exact_matches
        ):
            return None, "title_conflict_different_directory", related_hits
        return exact_matches[0], None, related_hits

    def _build_verification_fragments(
        self,
        *,
        request_content: str,
        mode: str,
    ) -> list[str]:
        normalized = (request_content or "").strip()
        if not normalized:
            return []
        if mode == "create":
            return [normalized[:120]]
        return [normalized]

    def _assess_existing_note_readability(
        self,
        *,
        current: dict[str, Any] | None,
        request: SafeWriteRequest,
        match: dict[str, Any],
    ) -> str | None:
        if current is None:
            return "read_note_result_is_none"
        if not isinstance(current, dict):
            return "read_note_not_dict"

        title = current.get("title")
        if not isinstance(title, str) or not title.strip():
            return "read_note_title_missing"

        permalink = current.get("permalink")
        if not isinstance(permalink, str) or not permalink.strip():
            return "read_note_permalink_missing"

        file_path = current.get("file_path")
        if not isinstance(file_path, str) or not file_path.strip():
            return "read_note_file_path_missing"

        if current.get("content") is None and not (self.memory_root / file_path).exists():
            return "read_note_content_missing_and_file_not_found"

        return None

    def _find_search_attempt_for_hit(
        self,
        *,
        match: dict[str, Any],
        attempts: list[SearchAttempt],
    ) -> dict[str, Any] | None:
        target_title = (match.get("title") or "").strip().lower()
        if target_title:
            for attempt in attempts:
                if target_title in (attempt.query or "").lower() and attempt.ok:
                    return {
                        "mode": attempt.mode,
                        "query": attempt.query,
                        "ok": attempt.ok,
                        "hit_count": attempt.hit_count,
                    }
        if attempts:
            last = attempts[-1]
            return {
                "mode": last.mode,
                "query": last.query,
                "ok": last.ok,
                "hit_count": last.hit_count,
            }
        return None

    def _build_stale_hit_payload(
        self,
        *,
        match: dict[str, Any],
        stale_reason: str,
        search_attempt: dict[str, Any] | None,
    ) -> dict[str, Any]:
        return {
            "title": match.get("title"),
            "permalink": match.get("permalink"),
            "file_path": match.get("file_path"),
            "entity_permalink": match.get("entity") or match.get("permalink"),
            "stale_reason": stale_reason,
            "search_attempt": search_attempt,
            "manual_recommended_action": (
                "建议手动清理 Basic Memory 索引或换唯一标题重测。"
            ),
        }

    def _safe_recent_activity(
        self,
        *,
        project: str,
        timeframe: str,
        page_size: int,
        warnings: list[str],
    ) -> list[dict[str, Any]]:
        try:
            return self.bm_client.recent_activity(
                project=project,
                timeframe=timeframe,
                page_size=page_size,
            )
        except BmCommandError as exc:
            warnings.append(str(exc))
            return []

    def _read_top_hits(
        self,
        *,
        hits: list[dict[str, Any]],
        project: str,
        warnings: list[str],
    ) -> list[dict[str, Any]]:
        readbacks: list[dict[str, Any]] = []
        for item in hits[: self.READBACK_LIMIT]:
            identifier = item.get("title") or item.get("permalink")
            if not identifier:
                continue
            try:
                readbacks.append(
                    self.bm_client.read_note(
                        identifier,
                        project=project,
                        include_frontmatter=True,
                    )
                )
            except BmCommandError as exc:
                warnings.append(str(exc))
        return readbacks

    def _list_directory_entries(self, *, limit: int) -> list[dict[str, str]]:
        entries: list[dict[str, str]] = []
        if not self.memory_root.exists():
            return entries
        for directory in sorted(path for path in self.memory_root.iterdir() if path.is_dir()):
            for note_path in sorted(directory.glob("*.md")):
                entries.append(
                    {
                        "directory": directory.name,
                        "file_path": note_path.relative_to(self.memory_root).as_posix(),
                    }
                )
                if len(entries) >= limit:
                    return entries
        return entries
