from typing import List, Dict, Tuple
import spacy
from spacy.tokens import DocBin, Doc
from spacy.matcher import PhraseMatcher
from spacy.language import Language
from spacy.pipeline import EntityRuler
import re
import json
from pathlib import Path

def make_docbin(nlp, examples: List[Tuple[str, dict]]):
    db = DocBin()
    for text, ann in examples:
        doc = nlp.make_doc(text)
        ents = []
        for (start, end, label) in ann.get("entities", []):
            span = doc.char_span(start, end, label=label, alignment_mode="contract")
            if span is None:
                span = doc.char_span(start, end, label=label, alignment_mode="expand")
            if span is None:
                print("Warning: couldn't create span:", text[start:end], start, end)
                continue
            ents.append(span)
        doc.ents = ents
        doc.user_data["meta"] = ann.get("meta", {})
        db.add(doc)
    return db

def generate_example_data():
	# This is just a placeholder until I can get the NER to work with the OCR and practice on the example documents we have
    examples = []
    txt1 = "Marriage Certificate: John A. Doe and Mary Peterson were married on 05/12/2018. Certificate No: M-12345."
    entities1 = []
    entities1.append((19, 31, "SPOUSE_1"))
    entities1.append((36, 47, "SPOUSE_2"))
    entities1.append((62, 70, "DATE_MARRIAGE"))
    entities1.append((86, 93, "CERT_NO"))
    examples.append((txt1, {"entities": entities1, "meta": {"doc_type": "marriage"}}))
    return examples

def save_data(nlp, out_path: str):
    examples = generate_demo_data()
    db = make_docbin(nlp, examples)
    db.to_disk(out_path)


if __name__ == "__main__":
	# This should hypothetically work with Spanish too, but I'll need to test it more
    nlp = spacy.blank("xx")
    nlp.add_pipe("tok2vec")
    nlp.add_pipe("ner")
    save_data(nlp, "train.spacy")
    print("Done writing train.spacy")
