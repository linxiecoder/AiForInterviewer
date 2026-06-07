"""Runtime theme strategies for polish interview sessions."""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum


class PolishTheme(str, Enum):
    TECHNICAL = "technical"
    COMMUNICATION = "communication"
    MIXED = "mixed"


@dataclass(frozen=True)
class PolishThemeStrategy:
    theme: str
    label: str
    explicit_weight: int
    implicit_weight: int
    question_intent: str
    question_types: tuple[str, ...]
    feedback_sections: tuple[str, ...]
    weakness_update_policy: str


_POLISH_THEME_STRATEGIES: dict[str, PolishThemeStrategy] = {
    PolishTheme.TECHNICAL.value: PolishThemeStrategy(
        theme=PolishTheme.TECHNICAL.value,
        label="技术打磨",
        explicit_weight=80,
        implicit_weight=20,
        question_intent="围绕工程链路、异常收敛、指标验证和技术取舍进行深挖。",
        question_types=("状态机", "幂等", "失败路径", "对账补偿", "性能指标", "成本控制", "可观测性"),
        feedback_sections=("technical_gaps", "p7_reference_answer", "next_training_suggestions"),
        weakness_update_policy="优先更新显性技术短板，表达问题只记录为辅助提示。",
    ),
    PolishTheme.COMMUNICATION.value: PolishThemeStrategy(
        theme=PolishTheme.COMMUNICATION.value,
        label="表达能力",
        explicit_weight=25,
        implicit_weight=75,
        question_intent="围绕 STAR 结构、背景压缩、职责边界、逻辑顺序和复盘表达进行打磨。",
        question_types=("STAR", "背景压缩", "个人职责边界", "逻辑顺序", "取舍表达", "复盘总结", "面试口语化"),
        feedback_sections=("communication_gaps", "oral_script", "next_training_suggestions"),
        weakness_update_policy="优先更新隐性表达短板，技术问题只作为表达素材补充。",
    ),
    PolishTheme.MIXED.value: PolishThemeStrategy(
        theme=PolishTheme.MIXED.value,
        label="混合",
        explicit_weight=60,
        implicit_weight=40,
        question_intent="同时观察技术深度、owner 视角和结构化表达。",
        question_types=("技术深度", "表达结构", "owner 视角", "显性技术权重", "隐性表达权重"),
        feedback_sections=(
            "weight_explanation",
            "technical_gaps",
            "communication_gaps",
        ),
        weakness_update_policy="同时更新显性技术和隐性表达短板，按权重决定下一轮训练优先级。",
    ),
}


def resolve_polish_theme_strategy(theme: str | None) -> PolishThemeStrategy:
    normalized = (theme or PolishTheme.MIXED.value).strip().lower()
    normalized = normalized or PolishTheme.MIXED.value
    strategy = _POLISH_THEME_STRATEGIES.get(normalized)
    if strategy is None:
        valid_values = ", ".join(sorted(_POLISH_THEME_STRATEGIES))
        raise ValueError(f"Invalid polish_theme: {theme!r}. Expected one of: {valid_values}")
    return strategy
