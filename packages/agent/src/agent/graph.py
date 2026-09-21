"""Builds the TableTalk graph.

    Start -> elicit (parallel Send per member) -> aggregate & retrieve
          -> consensus reached? --no--> back to elicit (targeted follow-up)
                                --yes-> present shortlist -> log selection -> End

Solo mode is this exact graph with `members` of length 1: the consensus
check resolves on the first pass since there's only one member's
constraints to satisfy, so no extra branching is needed for solo vs group.
"""

from __future__ import annotations

from langgraph.graph import END, StateGraph
from langgraph.types import Send

from agent.nodes import aggregate_and_retrieve, elicit_member, present_shortlist
from agent.state import TableTalkState


def _fan_out_to_members(state: TableTalkState) -> list[Send]:
    """Parallel Send: one elicit_member branch per member, independent of the others."""
    return [Send("elicit", member) for member in state["members"]]


def _consensus_reached(state: TableTalkState) -> str:
    """Conditional edge: route back for another round, or move to present.

    Routes based on whichever member's constraints are currently blocking
    consensus, not a fixed script. `round_count` caps the loop so a group
    that never converges still terminates (see Evaluation plan: consensus-
    loop bound).
    """
    score = state.get("consensus_score") or 0.0
    if score >= state["consensus_threshold"]:
        return "present"
    if state["round_count"] >= state["max_rounds"]:
        return "present"  # bail out with best-effort shortlist rather than loop forever
    state["round_count"] += 1
    return "elicit"


def build_graph():
    graph = StateGraph(TableTalkState)

    graph.add_node("elicit", elicit_member)
    graph.add_node("aggregate", aggregate_and_retrieve)
    graph.add_node("present", present_shortlist)

    graph.set_conditional_entry_point(_fan_out_to_members, {"elicit": "elicit"})
    graph.add_edge("elicit", "aggregate")
    graph.add_conditional_edges(
        "aggregate", _consensus_reached, {"elicit": "elicit", "present": "present"}
    )
    graph.add_edge("present", END)

    return graph.compile()
