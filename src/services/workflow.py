from src.services.graph import NLP2FiltersGraph
from src.services.nodes import GraphNodes
from src.infrastructure.llm_client import llm_service
from src.infrastructure.embedding_client import embedding_service
from src.infrastructure.redis_client import redis_store
from src.infrastructure.pii_client import pii_service

def create_workflow():
    """Create and return the workflow instance"""
    nodes = GraphNodes(
        llm_service=llm_service,
        embedding_service=embedding_service,
        vector_store=redis_store,
        pii_service=pii_service
    )
    workflow = NLP2FiltersGraph(nodes)
    return workflow