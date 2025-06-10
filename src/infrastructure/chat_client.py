from typing import List
import uuid

from src.services.workflow import create_workflow
from src.models.domain_models import ActiveFilter



class ChatService:
    def __init__(self):
        self.workflow = create_workflow()

    def process_chat_request(self, user_query: str, active_filters: List[ActiveFilter], session_id: str = None):
        session_id = session_id or str(uuid.uuid4())

        initial_state = {
            "query": user_query,
            "active_filters": active_filters,
            "clarification_request": [],
            "concepts": [],
            "matched_filters": [],
            "pii_mappings": {},
            "session_id": session_id,
            "message": ""
        }

        result = self.workflow.invoke(initial_state)

        return {
            "active_filters": result.get("active_filters", []),
            "clarification_request": result.get("clarification_request", []),
            "message": result.get("message", ""),
            "session_id": session_id
        }