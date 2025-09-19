import spacy
from spacy.tokens import DocBin
from spacy.util import filter_spans
import os
import random

# --- 1. Data Preparation ---
# spaCy's NER training format consists of a list of tuples. Each tuple
# contains the text and a dictionary with an "entities" key. The value is a
# list of character spans, each with a start index, end index, and entity label.
# [1]
TRAIN_DATA = [
    ("Birth certificate issued to Mary Johnson, case ID BC-98765.", {
        "entities": [(0, 16, "PERSON"), (40, 48, "ID")]
    }),
    ("Property deed transfer for parcel 123-45-678 recorded.", {
        "entities": [(32, 44, "PARCEL")]
    }),
    ("Marriage certificate M-12345 is now on file for Emily White.", {
        "entities": [(0, 20, "DOCUMENT"), (21, 28, "ID"), (50, 61, "PERSON")]
    }),
    ("Official birth record for David Miller, dated 01/01/1990.", {
        "entities": [(0, 20, "DOCUMENT"), (25, 37, "PERSON"), (45, 55, "DATE")]
    }),
    ("Land parcel 987-65-432 was sold to Robert Brown.", {
        "entities": [(11, 23, "PARCEL"), (35, 47, "PERSON")]
    }),
    ("The court docket number is CV-2023-001 for the case of Susan Davis.", {
        "entities": [(25, 35, "CASE_ID"), (50, 62, "PERSON")]
    }),
    ("A new birth certificate was created for Michael Clark on 11/22/2022.", {
        "entities": [(0, 20, "DOCUMENT"), (45, 58, "PERSON"), (62, 72, "DATE")]
    })
]

def create_spacy_file(data, output_file):
    """
    Converts annotated data into spaCy's binary.spacy format for training.

    This function uses the DocBin object for efficient serialization of the
    annotated Doc objects. It also handles potential overlapping entities
    by using filter_spans, which is a best practice for creating clean
    training data.[1, 2]
    """
    nlp = spacy.blank("en")  # Create a blank English model [1]
    db = DocBin()  # Create a DocBin object [3, 1]

    for text, annot in data:
        doc = nlp.make_doc(text)
        ents = []
        for start, end, label in annot["entities"]:
            span = doc.char_span(start, end, label=label, alignment_mode="contract")
            if span is None:
                # This can happen if character spans don't align with token boundaries
                print(f"Skipping entity: span for '{text[start:end]}' in '{text}' is not valid.")
            else:
                ents.append(span)

        # filter_spans removes overlapping entities, keeping the longest one
        filtered_ents = filter_spans(ents)
        doc.ents = filtered_ents
        db.add(doc)

    db.to_disk(output_file)  # Save the DocBin to a file [1]
    print(f"Successfully created {output_file}")


# --- 2. Configuration and Training (Instructions for Terminal) ---
# The following steps should be run in your terminal after running this script.

# Step 2a: Generate the base configuration file
# This command creates a 'config.cfg' file with default settings for an
# English NER pipeline, optimized for efficiency (faster, smaller model).
# [3, 1]
#
# COMMAND:
# python -m spacy init fill-config base_config.cfg config.cfg

# Step 2b: Train the model
# This command starts the training process. It uses the generated config file,
# specifies the output directory for the trained model, and provides the paths
# to the training and development.spacy files we created.
# [3, 1]
#
# COMMAND:
# python -m spacy train config.cfg --output./ner_model --paths.train./train.spacy --paths.dev./dev.spacy


# --- 3. Inference with the Custom Model ---
def predict_entities(model_path, text):
    """
    Loads a trained spaCy model and uses it to predict entities in a given text.
    """
    print(f"\n--- Loading model from {model_path} ---")
    try:
        nlp_ner = spacy.load(model_path)
    except IOError:
        print(f"Error: Model not found at '{model_path}'.")
        print("Please make sure you have trained the model using the terminal commands above.")
        return

    doc = nlp_ner(text)
    print(f"--- Predicting entities for text: '{text}' ---")
    if not doc.ents:
        print("No entities found.")
    else:
        for ent in doc.ents:
            print(f"  -> Entity: '{ent.text}', Label: '{ent.label_}'")


if __name__ == '__main__':
    # Create training and development datasets
    random.shuffle(TRAIN_DATA)
    split_point = int(len(TRAIN_DATA) * 0.8)
    train_set = TRAIN_DATA[:split_point]
    dev_set = TRAIN_DATA[split_point:]

    create_spacy_file(train_set, "train.spacy")
    create_spacy_file(dev_set, "dev.spacy")

    print("\n" + "=" * 50)
    print("Data preparation complete. Now, follow these steps in your terminal:")
    print("1. Create the config file:")
    print("   python -m spacy init fill-config base_config.cfg config.cfg")
    print(f"\n2. Start training:")
    print(f"   python -m spacy train config.cfg --output {NER_MODEL_DIR} --paths.train ./train.spacy --paths.dev ./dev.spacy")
    print("=" * 50 + "\n")

    # Import config paths
    from backend.config import NER_MODEL_DIR
    
    # --- Example of how to use the model after training is complete ---
    # The model will be saved in the NER model directory
    MODEL_PATH = str(NER_MODEL_DIR / "model-best")

    # You can uncomment the lines below to test the prediction function
    # once your model has been trained and saved.
    # test_document_1 = "A property deed for parcel 456-78-901 was filed for Sarah Connor."
    # test_document_2 = "Marriage license ML-67890 was approved on 08/15/2024."

    # predict_entities(MODEL_PATH, test_document_1)
    # predict_entities(MODEL_PATH, test_document_2)
