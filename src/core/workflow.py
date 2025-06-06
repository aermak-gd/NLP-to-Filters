from typing import Dict, Any, List
from langgraph.graph import StateGraph, END
from jinja2 import Environment, FileSystemLoader
import json

from src.core.models import (
    FilterState, ExtractedConcept, ActiveFilter, FilterMatch
)
from src.services.pii_service import pii_service
from src.services.llm_service import llm_service
from src.services.embedding_service import embedding_service
from src.services.redis_service import redis_store

template_env = Environment(loader=FileSystemLoader('prompts'))


def mask_pii_node(state: FilterState) -> FilterState:
    """Mask PII in user query"""
    query = state.query or ""

    masked_query, pii_mappings = pii_service.mask_text(query)

    return FilterState(
        query=masked_query,
        pii_mappings=pii_mappings,
        concepts=state.concepts,
        matched_filters=state.matched_filters,
        clarification_request=state.clarification_request,
        active_filters=state.active_filters,
        message=state.message,
        session_id=state.session_id
    )


def extract_concepts_node(state: FilterState) -> FilterState:
    """Extract filter concepts from query using LLM"""
    query = state.query or ""
    active_filters = state.active_filters or []

    template = template_env.get_template('concept_extraction.jinja2')

    system_prompt = template.render(current_filters=active_filters)

    response = llm_service.generate_completion(
        system_prompt=system_prompt,
        user_prompt=query,
        temperature=0.1,
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
        pii_mappings=state.pii_mappings,
        concepts=concepts,
        matched_filters=state.matched_filters,
        clarification_request=state.clarification_request,
        active_filters=state.active_filters,
        message=state.message,
        session_id=state.session_id
    )


def match_filters_node(state: FilterState) -> FilterState:
    """Match extracted concepts to available filters using batch processing"""

    if not state.concepts:
        return state

    matched_filters = state.matched_filters.copy() if state.matched_filters else []

    concept_texts = [', '.join([concept.text] + concept.generated_keywords) for concept in state.concepts]

    embeddings = embedding_service.embed_batch(concept_texts)

    batch_results = redis_store.search_filters_batch(
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
                operators=match.get("operators", ""),
                options=match.get("options", []),
                confidence=match["confidence"],
                matched_concept=concept.text
            )
            matched_filters.append(filter_match)

    return FilterState(
        query=state.query,
        pii_mappings=state.pii_mappings,
        concepts=state.concepts,
        matched_filters=matched_filters,  # Updated
        clarification_request=state.clarification_request,
        active_filters=state.active_filters,
        message=state.message,
        session_id=state.session_id
    )


def fill_values_node(state: FilterState) -> FilterState:
    """Fill in filters using LLM to select operators and values"""
    if not state.matched_filters:
        return state

    template = template_env.get_template('value_filling.jinja2')
    system_prompt = template.render(matched_filters=state.matched_filters)

    try:
        response = llm_service.generate_completion(
            system_prompt=system_prompt,
            user_prompt="",
            temperature=0.1,
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

                active_filter = {
                    'filter_id': match.filter_id,
                    'filter_name': match.filter_name,
                    'operator': llm_result.get('operator', 'EQUAL'),
                    'value': llm_result.get('value', '')
                }
                new_active_filters = [f for f in new_active_filters if f.get('filter_name') != match.filter_name]
                new_active_filters.append(active_filter)

    except Exception as e:
        print(f"Error processing LLM response: {e}")
        return state

    return FilterState(
        query=state.query,
        pii_mappings=state.pii_mappings,
        concepts=state.concepts,
        matched_filters=state.matched_filters,
        clarification_request=new_clarification_requests,
        active_filters=new_active_filters,
        message=state.message,
        session_id=state.session_id
    )


def handle_drops_node(state: FilterState) -> FilterState:
    """Handle filter removal requests"""
    concepts = state.concepts or []
    active_filters = state.active_filters.copy() if state.active_filters else []

    drop_concepts = [c for c in concepts if c.action == "drop"]

    if not drop_concepts:
        return state

    for concept in drop_concepts:
        concept_lower = concept.text.lower()
        active_filters = [
            f for f in active_filters
            if f.filter_name.lower() not in concept_lower
        ]

    return FilterState(
        query=state.query,
        pii_mappings=state.pii_mappings,
        concepts=state.concepts,
        matched_filters=state.matched_filters,
        clarification_request=state.clarification_request,
        active_filters=active_filters,  # Updated
        message=state.message,
        session_id=state.session_id
    )


def prepare_response_node(state: FilterState) -> FilterState:
    """Prepare final response with unmasked values"""
    active_filters = state.active_filters.copy() if state.active_filters else []
    clarification_request = state.clarification_request or []
    pii_mappings = state.pii_mappings or {}

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
        pii_mappings=state.pii_mappings,
        concepts=state.concepts,
        matched_filters=state.matched_filters,
        clarification_request=state.clarification_request,
        active_filters=active_filters,
        message=message,  # Updated
        session_id = state.session_id
    )


def create_workflow() -> StateGraph:
    """Create the LangGraph workflow"""

    workflow = StateGraph(FilterState)

    # workflow.add_node("mask_pii", mask_pii_node)
    workflow.add_node("extract_concepts", extract_concepts_node)
    workflow.add_node("match_filters", match_filters_node)
    workflow.add_node("fill_values", fill_values_node)
    # workflow.add_node("handle_drops", handle_drops_node)
    workflow.add_node("prepare_response", prepare_response_node)

    # workflow.add_edge("mask_pii", "extract_concepts")
    workflow.add_edge("extract_concepts", "match_filters")
    workflow.add_edge("match_filters", "fill_values")
    workflow.add_edge("fill_values", "prepare_response")
    # workflow.add_edge("handle_drops", "prepare_response")
    workflow.add_edge("prepare_response", END)

    workflow.set_entry_point("extract_concepts")

    return workflow.compile()