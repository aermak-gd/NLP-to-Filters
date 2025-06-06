from typing import List, Dict, Any, Optional, Union
from dataclasses import dataclass
from datetime import datetime

@dataclass
class ExtractedConcept:
    """What the LLM extracts from user query"""
    text: str  # "age > 59"
    generated_keywords: List[str]
    action: str = "add"  # add, drop, modify
    category: Optional[str] = None  # optional hint from LLM

@dataclass
class FilterMatch:
    """Result of RAG matching concept to filter"""
    filter_id: str
    filter_name: str
    operators: List[str]
    options: List[str]
    confidence: float  # From RAG similarity
    matched_concept: str  # Which concept matched this

@dataclass
class ActiveFilter:
    """A filter ready to be applied"""
    filter_id: str
    filter_name: str
    operator: str  # From filter metadata, not enum
    value: Any

@dataclass
class FilterSuggestion:
    """When multiple filters match a concept"""
    concept_text: str
    options: List[ActiveFilter]  # Possible filters with metadata

@dataclass
class FilterState:
    """Minimal state for filter management"""
    query: str
    active_filters: List[ActiveFilter]
    # clarification_response: List[Dict[str, Any]] # Append to active_filters on Front
    pii_mappings: Dict[str, str]
    concepts: List[ExtractedConcept]
    matched_filters: List[FilterMatch]
    clarification_request: List[FilterSuggestion]
    session_id: str
    # timestamp: datetime
    message: str = ""

@dataclass
class Message:
    query: str
    active_filters: List[ActiveFilter]
    clarification_request: List[ActiveFilter]
    session_id: str
    timestamp: datetime