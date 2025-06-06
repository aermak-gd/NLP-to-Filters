import re
from typing import Dict, List, Tuple
from dataclasses import dataclass


@dataclass
class PIIEntity:
    text: str
    type: str
    start: int
    end: int


class PIIService:
    """Simple regex-based PII detection and masking"""

    def __init__(self):
        # Regex patterns for common PII
        self.patterns = {
            'email': r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b',
            'phone': r'\b(?:\+?1[-.\s]?)?\(?[0-9]{3}\)?[-.\s]?[0-9]{3}[-.\s]?[0-9]{4}\b',
            'ssn': r'\b\d{3}-\d{2}-\d{4}\b',
            'credit_card': r'\b\d{4}[\s-]?\d{4}[\s-]?\d{4}[\s-]?\d{4}\b',
            'date_of_birth': r'\b(?:0[1-9]|1[0-2])[\/\-](?:0[1-9]|[12]\d|3[01])[\/\-](?:19|20)\d{2}\b',
        }

        self.name_keywords = ['mr.', 'mrs.', 'ms.', 'dr.', 'prof.']

    def detect_pii(self, text: str) -> List[PIIEntity]:
        """Detect PII entities in text"""
        entities = []

        for pii_type, pattern in self.patterns.items():
            for match in re.finditer(pattern, text, re.IGNORECASE):
                entities.append(PIIEntity(
                    text=match.group(),
                    type=pii_type,
                    start=match.start(),
                    end=match.end()
                ))

        return sorted(entities, key=lambda x: x.start)

    def mask_text(self, text: str) -> Tuple[str, Dict[str, str]]:
        """Mask PII in text and return mappings"""
        entities = self.detect_pii(text)

        if not entities:
            return text, {}

        masked_text = text
        mappings = {}
        offset = 0

        for entity in entities:
            mask_token = f"<{entity.type.upper()}_{len(mappings) + 1}>"

            start = entity.start + offset
            end = entity.end + offset

            masked_text = masked_text[:start] + mask_token + masked_text[end:]

            offset += len(mask_token) - (entity.end - entity.start)

            mappings[mask_token] = entity.text

        return masked_text, mappings

    def unmask_text(self, text: str, mappings: Dict[str, str]) -> str:
        """Restore PII in text using mappings"""
        unmasked_text = text

        for mask_token, original_value in mappings.items():
            unmasked_text = unmasked_text.replace(mask_token, original_value)

        return unmasked_text

pii_service = PIIService()