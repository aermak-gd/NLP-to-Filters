import json
from pathlib import Path
from jinja2 import Environment, FileSystemLoader

from src.models.domain_models import FilterState, ExtractedConcept, FilterMatch, ActiveFilter
from src.infrastructure.llm_client import LLMService
from src.infrastructure.embedding_client import EmbeddingService
from src.infrastructure.redis_client import RedisFilterStore
from src.infrastructure.pii_client import PIIService

current_file_dir = Path(__file__).parent
prompts_dir = current_file_dir / '../../config/prompts'
template_env = Environment(loader=FileSystemLoader(prompts_dir))

class GraphNodes:
    def __init__(self,
                 llm_service: LLMService,
                 embedding_service: EmbeddingService,
                 vector_store: RedisFilterStore,
                 pii_service: PIIService):
        self.llm_service = llm_service
        self.embedding_service = embedding_service
        self.vector_store = vector_store
        self.pii_service = pii_service

    def mask_pii_node(self, state: FilterState) -> FilterState:
        """Mask PII in user query"""
        query = state.query or ""

        masked_query, pii_mappings = self.pii_service.mask_text(query)

        return FilterState(
            query=masked_query,
            pii_mappings=pii_mappings,  # Updated
            concepts=state.concepts,
            matched_filters=state.matched_filters,
            clarification_request=state.clarification_request,
            active_filters=state.active_filters,
            message=state.message,
            session_id=state.session_id
        )

    def extract_concepts_node(self, state: FilterState) -> FilterState:
        """Extract filter concepts from query using LLM"""
        query = state.query or ""
        active_filters = state.active_filters or []

        template = template_env.get_template('concept_extraction.jinja2')

        system_prompt = template.render(current_filters=active_filters)

        response = self.llm_service.generate_completion(
            system_prompt=system_prompt,
            user_prompt=query,
            json_mode=True
        )

        try:
            concepts_data = json.loads(response)
            concepts = [ExtractedConcept(**c) for c in concepts_data]
        except Exception as e:
            print(f"Error parsing concepts: {e}")
            concepts = []

        return FilterState(
            query=state.query,
            # pii_mappings=state.pii_mappings,
            concepts=concepts,
            matched_filters=state.matched_filters,
            clarification_request=state.clarification_request,
            active_filters=state.active_filters,
            message=state.message,
            session_id=state.session_id
        )

    def handle_drops_node(self, state: FilterState) -> FilterState:
        """Handle filter removal requests"""
        concepts = state.concepts.copy() if state.concepts else []
        active_filters = state.active_filters.copy() if state.active_filters else []

        drop_concepts = [c for c in concepts if c.action == "drop"]
        concepts = [c for c in concepts if c.action != "drop"]

        if not drop_concepts:
            return state

        for concept in drop_concepts:
            concept_lower = concept.filter_name.lower()
            active_filters = [
                f for f in active_filters
                if f.filter_name.lower() not in concept_lower
            ]

        return FilterState(
            query=state.query,
            # pii_mappings=state.pii_mappings,
            concepts=concepts,  # Updated
            matched_filters=state.matched_filters,
            clarification_request=state.clarification_request,
            active_filters=active_filters,  # Updated
            message=state.message,
            session_id=state.session_id
        )

    def match_filters_node(self, state: FilterState) -> FilterState:
        """Match extracted concepts to available filters using batch processing"""

        if not state.concepts:
            return state

        matched_filters = state.matched_filters.copy() if state.matched_filters else []

        concept_texts = [', '.join([concept.text] + concept.generated_keywords) for concept in state.concepts]

        embeddings = self.embedding_service.embed_batch(concept_texts)

        batch_results = self.redis_store.search_filters_batch(
            embeddings,
            top_k=2,
            score_threshold=0.3
        )

        HIGH_CONFIDENCE_THRESHOLD = 0.5
        CLOSE_CONFIDENCE_GAP = 0.3

        for i, concept in enumerate(state.concepts):
            matching_filters = batch_results[i] if i < len(batch_results) else []

            if not matching_filters:
                continue

            best_match = matching_filters[0]
            best_confidence = best_match["confidence"]

            close_matches = [
                match for match in matching_filters
                if (match["confidence"] >= HIGH_CONFIDENCE_THRESHOLD and
                    abs(match["confidence"] - best_confidence) <= CLOSE_CONFIDENCE_GAP)
            ]

            matches_to_process = close_matches if len(close_matches) > 1 else [best_match]

            for match in matches_to_process:
                filter_match = FilterMatch(
                    filter_id=match["filter_id"],
                    filter_name=match["display_name"],
                    description=match["description"],
                    operators=match.get("operators", ""),
                    options=match.get("options", []),
                    confidence=match["confidence"],
                    matched_concept=concept.text
                )
                matched_filters.append(filter_match)

        return FilterState(
            query=state.query,
            # pii_mappings=state.pii_mappings,
            concepts=state.concepts,
            matched_filters=matched_filters,  # Updated
            clarification_request=state.clarification_request,
            active_filters=state.active_filters,
            message=state.message,
            session_id=state.session_id
        )

    def fill_values_node(self, state: FilterState) -> FilterState:
        """Fill in filters using LLM to select operators and values"""
        if not state.matched_filters:
            return state

        template = template_env.get_template('value_filling.jinja2')
        system_prompt = template.render(matched_filters=state.matched_filters)

        try:
            response = self.llm_service.generate_completion(
                system_prompt=system_prompt,
                user_prompt="",
                json_mode=True
            )

            filter_results = json.loads(response)

            # Group filters by matched_concept to identify duplicates
            concept_groups = {}
            for match in state.matched_filters:
                concept = match.matched_concept
                if concept not in concept_groups:
                    concept_groups[concept] = []
                concept_groups[concept].append(match)

            new_active_filters = state.active_filters.copy() if state.active_filters else []
            new_clarification_requests = state.clarification_request.copy() if state.clarification_request else []

            llm_results_by_name = {result['filter_display_name']: result for result in filter_results}

            for concept, matches in concept_groups.items():
                if len(matches) > 1:
                    options = []
                    for match in matches:
                        llm_result = llm_results_by_name.get(match.filter_name, {})
                        options.append({
                            'filter_id': match.filter_id,
                            'filter_name': match.filter_name,
                            'operator': llm_result.get('operator', 'EQUAL'),
                            'value': llm_result.get('value', '')
                        })

                    clarification = {
                        'concept_text': concept,
                        'options': options
                    }
                    new_clarification_requests.append(clarification)
                else:
                    match = matches[0]
                    llm_result = llm_results_by_name.get(match.filter_name, {})

                    active_filter = ActiveFilter(
                        filter_id=match.filter_id,
                        filter_name=match.filter_name,
                        description=match.description,
                        operator=llm_result.get('operator', 'EQUAL'),
                        value=llm_result.get('value', ''),
                    )
                    new_active_filters = [f for f in new_active_filters if f.filter_name != match.filter_name]
                    new_active_filters.append(active_filter)

        except Exception as e:
            print(f"Error processing LLM response: {e}")
            return state

        return FilterState(
            query=state.query,
            # pii_mappings=state.pii_mappings,
            concepts=state.concepts,
            matched_filters=state.matched_filters,
            clarification_request=new_clarification_requests,
            active_filters=new_active_filters,
            message=state.message,
            session_id=state.session_id
        )

    def prepare_response_node(self, state: FilterState) -> FilterState:
        """Prepare final response with unmasked values"""
        active_filters = state.active_filters.copy() if state.active_filters else []
        clarification_request = state.clarification_request or []
        # pii_mappings = state.pii_mappings or {}

        messages = []

        if active_filters:
            messages.append(f"Applied {len(active_filters)} filter(s)")

        if clarification_request:
            messages.append(f"I need clarification on {len(clarification_request)} filter(s)")

        message = ". ".join(messages) if messages else "No filters to apply"

        # Unmask any PII in filter values if needed
        # for filter_item in active_filters:
        #     if isinstance(filter_item.value, str):
        #         filter_item.value = pii_service.unmask_text(filter_item.value, pii_mappings)

        return FilterState(
            query=state.query,
            # pii_mappings=state.pii_mappings,
            concepts=state.concepts,
            matched_filters=state.matched_filters,
            clarification_request=state.clarification_request,
            active_filters=active_filters,
            message=message,  # Updated
            session_id=state.session_id
        )