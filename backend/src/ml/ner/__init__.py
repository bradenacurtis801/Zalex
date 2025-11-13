"""
NER (Named Entity Recognition) module.
Provides interfaces and implementations for entity extraction.
"""

from .base_ner import NERModel, NERResult, Entity
from .spacy_ner import SpacyNERModel

__all__ = [
    "NERModel",
    "NERResult",
    "Entity",
    "SpacyNERModel",
]

