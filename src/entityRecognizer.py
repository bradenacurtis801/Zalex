import spacy
from typing import List

class NamedEntityRecognizer:
	def __init__(self):
		self.nlp = spacy.load("en_core_web_sm")

	def nameEntities(self, document_text) -> List:
		doc = self.nlp(document_text)
		entities = []
		for ent in doc.ents:
			entities.append(ent.label_, ent.text)
		return entities
