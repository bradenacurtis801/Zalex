import json
import re
import spacy
from pathlib import Path
import os
from sqlalchemy import func
from sqlalchemy.orm import selectinload
from sqlmodel import select
from lib.constants import ML_MODELS_DIR


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

nlp = spacy.load(str(model_path))

# -------------------------------
# 2️⃣ Connect to DB
# -------------------------------
db = next(get_session())  # get a real SQLAlchemy session

# -------------------------------
# 3️⃣ Fetch n random documents with their OCR data
# -------------------------------
n_documents = 5  # adjust as needed

documents = db.exec(
    select(Document)
    .options(selectinload(Document.ocr_data))
    .order_by(func.random())
    .limit(n_documents)
).all()

if not documents:
    print("No documents found.")
    exit()

# -------------------------------
# 4️⃣ Extract lines from OCRData
# -------------------------------
lines_for_ner = []
for doc in documents:
    for ocr in doc.ocr_data:
        try:
            lines_json = json.loads(ocr.lines_data)
            for line in lines_json:
                clean_line = re.sub(r"\s+", " ", line["text"]).strip()
                if clean_line:
                    lines_for_ner.append(clean_line)
        except json.JSONDecodeError:
            continue  # skip invalid JSON

if not lines_for_ner:
    print("No OCR lines found in selected documents.")
    exit()

# -------------------------------
# 5️⃣ Run NER on each line
# -------------------------------
print("Entities extracted from OCR documents:")

all_entities = []

for i, line in enumerate(lines_for_ner):
    doc = nlp(line)
    if doc.ents:
        print(f"\nLine {i}: {line}")
        for ent in doc.ents:
            print(f"  - {ent.text} ({ent.label_})")
            all_entities.append({"text": ent.text, "label": ent.label_})

# -------------------------------
# 6️⃣ Optional: print all entities together
# -------------------------------
print("\nAll entities found in documents:")
print(all_entities)
