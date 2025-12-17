import json
import re
from pathlib import Path
import os
import random
from sqlalchemy import select
from sqlalchemy.orm import selectinload
import ner_shared as ner_lib
from lib.constants import ML_MODELS_DIR

import spacy
from spacy.training.example import Example
from spacy.util import minibatch, compounding

# Add the backend directory to the Python path
backend_dir = Path(__file__).parent.parent.parent / "backend"
os.sys.path.insert(0, str(backend_dir))

from src.db.connection import get_session
from src.models.database import Document

# -------------------------------
# 1️⃣ Load fine-tuned SpaCy model
# -------------------------------
model_id = "bradenacurtis/es_core_news_sm_finetuned"
model_path = ML_MODELS_DIR / model_id.replace("/", "-")
model_path.mkdir(parents=True, exist_ok=True)

# -------------------------------
# 1️⃣ Connect to DB and get OCR data
# -------------------------------
db = next(get_session())

documents = db.exec(
    select(Document)
    .options(selectinload(Document.ocr_data))
    .order_by(Document.created_at)
).scalars().all()

n_docs = 10
documents = random.sample(documents, min(len(documents), n_docs))

# -------------------------------
# 2️⃣ Extract and clean lines from OCRData
# -------------------------------

lines_for_annotation = []
for doc in documents:
    for ocr in doc.ocr_data:
        lines_json = json.loads(ocr.lines_data)
        for line in lines_json:
            cleaned = ner_lib.clean_line(line["text"])
            if cleaned:
                lines_for_annotation.append(cleaned)

print(f"Collected {len(lines_for_annotation)} lines for annotation.")

# -------------------------------
# 5️⃣ Generate SpaCy TRAIN_DATA
# -------------------------------
TRAIN_DATA = []

for line in lines_for_annotation:
    ents = ner_lib.label_entities(line)
    ents = ner_lib.remove_overlaps(ents)
    if ents:
        TRAIN_DATA.append((line, {"entities": ents}))

print(f"Generated {len(TRAIN_DATA)} labeled training examples.")

# Save TRAIN_DATA for inspection
with open("ocr_ner_train_data.json", "w", encoding="utf-8") as f:
    json.dump(TRAIN_DATA, f, ensure_ascii=False, indent=2)

# -------------------------------
# 6️⃣ Fine-tune SpaCy model with better parameters
# -------------------------------
nlp = spacy.load("es_core_news_sm")

# Disable other pipes during training for efficiency
other_pipes = [pipe for pipe in nlp.pipe_names if pipe != "ner"]
with nlp.disable_pipes(*other_pipes):
    ner = nlp.get_pipe("ner")
    
    # Add labels
    for label in ["PER", "DATE", "GPE", "ORG"]:
        ner.add_label(label)
    
    optimizer = nlp.resume_training()
    
    print("Starting fine-tuning with improved parameters...")
    
    # More epochs and better batch sizing
    for epoch in range(30):
        losses = {}
        random.shuffle(TRAIN_DATA)
        
        batches = minibatch(TRAIN_DATA, size=compounding(4.0, 32.0, 1.001))
        
        for batch in batches:
            examples = []
            for text, annotations in batch:
                doc = nlp.make_doc(text)
                example = Example.from_dict(doc, annotations)
                examples.append(example)
            
            # Lower dropout for better learning
            nlp.update(examples, drop=0.2, sgd=optimizer, losses=losses)
        
        if epoch % 5 == 0:
            print(f"Epoch {epoch+1}/30 - Losses: {losses}")

# -------------------------------
# 7️⃣ Save fine-tuned model
# -------------------------------
nlp.to_disk(model_path)
print(f"\nFine-tuned model saved to {model_path}")

# -------------------------------
# 8️⃣ Test the model with problematic examples
# -------------------------------
test_texts = [
    "ABRAHAM SOFER BALID, panameño, nació el 15 de abril de 1980 en la Ciudad de Panamá",
    "La Junta Directiva aprobó el Pacto Social",
    "BORIS BARRIOS GONZÁLEZ, Notario Público Primero",
    "en la República de Panamá, el Total Derechos es 60.00",
    "El Agente Residente actuará conforme al Registro Público"
]

print("\n" + "="*60)
print("TEST PREDICTIONS:")
print("="*60)

for test_text in test_texts:
    doc = nlp(test_text)
    print(f"\nText: {test_text}")
    if doc.ents:
        for ent in doc.ents:
            print(f"  → {ent.text:30s} ({ent.label_})")
    else:
        print("  → No entities detected")