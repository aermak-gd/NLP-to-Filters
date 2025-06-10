from src.services.graph import NLP2FiltersGraph
from src.services.nodes import GraphNodes

def create_workflow():
    """Create and return the workflow instance"""
    nodes = GraphNodes()
    workflow = NLP2FiltersGraph(nodes)
    return workflow