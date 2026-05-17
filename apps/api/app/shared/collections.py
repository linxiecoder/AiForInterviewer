"""Collection helpers without domain rules."""

from collections.abc import Iterable
from typing import TypeVar

T = TypeVar("T")


def unique_preserve_order(values: Iterable[T]) -> list[T]:
    seen: set[T] = set()
    result: list[T] = []
    for value in values:
        if value in seen:
            continue
        seen.add(value)
        result.append(value)
    return result

