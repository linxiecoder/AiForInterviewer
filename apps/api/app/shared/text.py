"""Text helpers without domain rules."""


def normalize_whitespace(value: str) -> str:
    return " ".join(value.split())

