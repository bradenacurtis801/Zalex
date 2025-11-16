"""
spaCy-based NER implementation.
Uses spaCy models for named entity recognition.
"""

import logging
from typing import List, Optional

import spacy
from spacy import Language

from .base_ner import NERModel, NERResult, Entity

logger = logging.getLogger(__name__)

"""
To install the spaCy model, run the following command:
pip install https://github.com/explosion/spacy-models/releases/download/es_core_news_sm-3.7.0/es_core_news_sm-3.7.0-py3-none-any.whl 
"""

class SpacyNERModel(NERModel):
    """
    spaCy-based NER model for entity extraction.
    Supports multiple languages and can be configured per document type.
    """

    def __init__(
        self,
        model_name_or_path: str = "es_core_news_sm",  # Default to Spanish small model
        cache_folder: Optional[str] = None,
        token: Optional[str] = None,
    ):
        """
        Initialize the spaCy NER model.

        Args:
            model_name_or_path: spaCy model name (e.g., "es_core_news_sm", "en_core_web_sm")
            cache_folder: Optional cache folder (not used for spaCy, but kept for interface consistency)
            token: Optional token (not used for spaCy, but kept for interface consistency)
        """
        super().__init__(model_name_or_path, cache_folder, token)
        self.nlp: Optional[Language] = None
        self._supported_entity_types: List[str] = []

    def initialize(self) -> bool:
        """
        Initialize the spaCy model.

        Returns:
            bool: True if initialization successful, False otherwise
        """

        logger.info(f"Loading spaCy model: {self.model_name_or_path}")
        
        # Try to load the model
        self.nlp = spacy.load(self.model_name_or_path)

        # Get supported entity types from the model
        if self.nlp and "ner" in self.nlp.pipe_names:
            # Get all entity labels the model can predict
            ner_labels = self.nlp.get_pipe("ner").labels
            self._supported_entity_types = list(ner_labels)
            logger.info(
                f"spaCy model loaded successfully. "
                f"Supported entity types: {self._supported_entity_types}"
            )
        else:
            logger.warning("spaCy model does not have NER component")
            self._supported_entity_types = []

        self.is_initialized = True
        return True

    def extract_entities(
        self, text: str, doc_type: Optional[str] = None
    ) -> NERResult:
        """
        Extract named entities from text using spaCy.

        Args:
            text: The text to extract entities from
            doc_type: Optional document type/category (can be used to adjust behavior)

        Returns:
            NERResult: Result containing extracted entities
        """
        if not self.is_initialized or self.nlp is None:
            logger.error("NER model not initialized")
            return NERResult(
                entities=[],
                method="spacy",
                details={"error": "Model not initialized"},
            )

        if not text or not text.strip():
            return NERResult(entities=[], method="spacy", details={})

        try:
            # Process text with spaCy
            doc = self.nlp(text)

            # Extract entities
            entities = []
            for ent in doc.ents:
                # Convert spaCy entity to our Entity format
                entity = Entity(
                    text=ent.text,
                    label=ent.label_,  # spaCy label (e.g., "PERSON", "ORG", "LOC")
                    start=ent.start_char,
                    end=ent.end_char,
                    confidence=None,  # spaCy doesn't provide confidence scores by default
                )
                entities.append(entity)

            logger.debug(
                f"Extracted {len(entities)} entities from text "
                f"(length: {len(text)} characters, doc_type: {doc_type})"
            )

            return NERResult(
                entities=entities,
                method="spacy",
                details={
                    "model": self.model_name_or_path,
                    "doc_type": doc_type,
                    "text_length": len(text),
                },
            )

        except Exception as e:
            logger.error(f"Error extracting entities with spaCy: {e}", exc_info=True)
            return NERResult(
                entities=[],
                method="spacy",
                details={"error": str(e)},
            )

    def get_supported_entity_types(self) -> List[str]:
        """
        Get list of entity types this model can extract.

        Returns:
            List[str]: List of supported entity type labels
        """
        return self._supported_entity_types.copy()

    def get_model_info(self) -> dict:
        """Get information about the loaded model."""
        base_info = super().get_model_info()
        base_info.update({
            "spacy_version": spacy.__version__ if spacy else None,
            "has_ner_component": "ner" in self.nlp.pipe_names if self.nlp else False,
        })
        return base_info

