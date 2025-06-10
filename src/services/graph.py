from langgraph.graph import StateGraph, END

from src.models.domain_models import FilterState
from nodes import GraphNodes

class NLP2FiltersGraph:
    def __init__(self, nodes: GraphNodes):
        self.nodes = nodes
        self.graph = self._build_graph()

    def _build_graph(self) -> StateGraph:
        """Build the LangGraph workflow"""
        workflow = StateGraph(FilterState)

        # workflow.add_node("mask_pii", mask_pii_node)
        workflow.add_node("extract_concepts", self.nodes.extract_concepts_node)
        workflow.add_node("handle_drops", self.nodes.handle_drops_node)
        workflow.add_node("match_filters", self.nodes.match_filters_node)
        workflow.add_node("fill_values", self.nodes.fill_values_node)
        workflow.add_node("prepare_response", self.nodes.prepare_response_node)

        # workflow.add_edge("mask_pii", "extract_concepts")
        workflow.add_edge("extract_concepts", "handle_drops")
        workflow.add_edge("handle_drops", "match_filters")
        workflow.add_edge("match_filters", "fill_values")
        workflow.add_edge("fill_values", "prepare_response")
        workflow.add_edge("prepare_response", END)

        workflow.set_entry_point("extract_concepts")

        return workflow.compile()

    def invoke(self, state: FilterState) -> FilterState:
        """Execute graph"""
        return self.graph.invoke(state)