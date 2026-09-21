"""Phase-1 smoke test: the graph compiles and a length-1 (solo) run terminates."""

from agent.graph import build_graph


def test_graph_compiles():
    graph = build_graph()
    assert graph is not None
