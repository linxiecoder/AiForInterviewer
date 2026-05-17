"""AI task value objects."""

from dataclasses import dataclass


@dataclass(frozen=True)
class ContractId:
    value: str

