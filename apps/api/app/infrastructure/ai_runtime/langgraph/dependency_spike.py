from __future__ import annotations

from typing import TypedDict

from langgraph.graph import END, START, StateGraph


class FakeSpikeState(TypedDict):
    topic: str
    steps: list[str]
    provider_calls: int
    db_writes: int
    formal_business_writes: int


def run_dependency_spike() -> dict[str, object]:
    graph = StateGraph(FakeSpikeState)
    graph.add_node("fake_node", _fake_node)
    graph.add_edge(START, "fake_node")
    graph.add_edge("fake_node", END)

    compiled = graph.compile()
    result = compiled.invoke(
        {
            "topic": "dependency-spike",
            "steps": ["compiled"],
            "provider_calls": 0,
            "db_writes": 0,
            "formal_business_writes": 0,
        }
    )

    return {
        "graph_name": "pr4_lg_dep_fake_graph",
        "topic": result["topic"],
        "steps": result["steps"],
        "provider_calls": result["provider_calls"],
        "db_writes": result["db_writes"],
        "formal_business_writes": result["formal_business_writes"],
    }


def _fake_node(state: FakeSpikeState) -> FakeSpikeState:
    return {
        "topic": state["topic"],
        "steps": [*state["steps"], "invoked"],
        "provider_calls": state["provider_calls"],
        "db_writes": state["db_writes"],
        "formal_business_writes": state["formal_business_writes"],
    }
