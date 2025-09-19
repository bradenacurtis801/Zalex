import os
import pandas as pd
import torch
from sklearn.model_selection import train_test_split
from datasets import Dataset, DatasetDict, Features, ClassLabel, Value
from transformers import (
    AutoTokenizer,
    AutoModelForSequenceClassification,
    TrainingArguments,
    Trainer,
    RobertaTokenizer,
    RobertaModel
)
import numpy as np
from sklearn.metrics import accuracy_score, f1_score

# --- Configuration ---
import sys
from pathlib import Path
sys.path.append(str(Path(__file__).parent.parent.parent))
from config import DOCUMENT_DATASET_DIR, SPANISH_CLASSIFIER_MODEL, TRAINING_RESULTS_DIR, TRAINING_LOGS_DIR

# The foundational Spanish model we will fine-tune.
# This is a powerful model from the Barcelona Supercomputing Center.
# Updated to use the current available model from PlanTL-GOB-ES
BASE_MODEL_NAME = "UMUTeam/roberta-spanish-sentiment-analysis"  # Pre-fine-tuned Spanish model
# Directory where your labeled .txt files are
DATA_DIRECTORY = str(DOCUMENT_DATASET_DIR)
# Directory to save the final, fine-tuned model
FINE_TUNED_MODEL_PATH = str(SPANISH_CLASSIFIER_MODEL)


# --- 1. Data Preparation ---

def load_and_prepare_data(data_path):
    """Loads text files, creates labels, and prepares a pandas DataFrame."""
    texts, labels = [], []
    for category in os.listdir(data_path):
        category_path = os.path.join(data_path, category)
        if os.path.isdir(category_path):
            for filename in os.listdir(category_path):
                file_path = os.path.join(category_path, filename)
                try:
                    with open(file_path, 'r', encoding='utf-8') as f:
                        texts.append(f.read())
                        labels.append(category)
                except Exception as e:
                    print(f"Error reading {file_path}: {e}")

    df = pd.DataFrame({'text': texts, 'category': labels})

    # Create numerical labels required by the model
    df['label'] = pd.Categorical(df['category']).codes

    # Create mappings between numerical IDs and category names
    id2label = dict(enumerate(df['category'].astype('category').cat.categories))
    label2id = {v: k for k, v in id2label.items()}

    print(f"Loaded {len(df)} documents.")
    print(f"Categories found: {label2id}")

    return df, id2label, label2id


# --- 2. Fine-Tuning The Model ---

def fine_tune_model(df, id2label, label2id):
    """Fine-tunes the transformer model on the provided dataframe."""

    num_labels = len(id2label)

    # Load tokenizer and model
    print(f"\nLoading base model: {BASE_MODEL_NAME}")
    # Using use_fast=False for better compatibility in some environments
    tokenizer = AutoTokenizer.from_pretrained(BASE_MODEL_NAME, use_fast=False)
    model = AutoModelForSequenceClassification.from_pretrained(
        BASE_MODEL_NAME,
        num_labels=num_labels,
        id2label=id2label,
        label2id=label2id
    )

    # *** FIX: Define the features to cast the 'label' column correctly ***
    # Get the list of unique category names for the ClassLabel
    class_names = list(label2id.keys())
    features = Features({
        'text': Value('string'),
        'category': Value('string'),
        'label': ClassLabel(names=class_names)
    })

    # Convert pandas DataFrame to Hugging Face Dataset, applying the features
    dataset = Dataset.from_pandas(df, features=features)

    # Split into training and testing sets. This will now work correctly.
    train_test_split_dataset = dataset.train_test_split(test_size=0.2, seed=42, stratify_by_column="label")

    # Create a DatasetDict
    dataset_dict = DatasetDict({
        'train': train_test_split_dataset['train'],
        'test': train_test_split_dataset['test']
    })
    print("\nDataset structure:")
    print(dataset_dict)

    # Tokenization function
    def tokenize(batch):
        return tokenizer(batch['text'], padding='max_length', truncation=True)

    # Apply tokenization to the datasets
    print("\nTokenizing datasets...")
    tokenized_datasets = dataset_dict.map(tokenize, batched=True)

    # --- FIX: Using arguments compatible with very old transformers versions ---
    # NOTE: This removes evaluation during training. The model saved will be from the
    # final epoch, not necessarily the one with the best performance.
    # The recommended solution is to upgrade your library: pip install --upgrade transformers
    training_args = TrainingArguments(
        output_dir=str(TRAINING_RESULTS_DIR),
        num_train_epochs=10,  # Increased from 3 to 10
        per_device_train_batch_size=4,  # Reduced for better learning
        per_device_eval_batch_size=4,
        warmup_steps=100,  # Reduced warmup
        weight_decay=0.01,
        learning_rate=2e-5,  # Added explicit learning rate
        logging_dir=str(TRAINING_LOGS_DIR),
        logging_steps=10,
        save_strategy="epoch",  # Save after each epoch
        eval_strategy="epoch",  # Evaluate after each epoch
    )

    # Define metrics computation function
    def compute_metrics(eval_pred):
        predictions, labels = eval_pred
        predictions = np.argmax(predictions, axis=1)
        f1 = f1_score(labels, predictions, average='weighted')
        acc = accuracy_score(labels, predictions)
        return {'accuracy': acc, 'f1': f1}

    # Instantiate the Trainer
    trainer = Trainer(
        model=model,
        args=training_args,
        train_dataset=tokenized_datasets['train'],
        eval_dataset=tokenized_datasets['test'],
        compute_metrics=compute_metrics,
    )

    # Start fine-tuning
    print("\nStarting fine-tuning... (This may take a while. A GPU is recommended.)")
    trainer.train()
    print("Fine-tuning complete.")

    # Save the fine-tuned model
    print(f"\nSaving the fine-tuned model to '{FINE_TUNED_MODEL_PATH}'")
    trainer.save_model(FINE_TUNED_MODEL_PATH)
    tokenizer.save_pretrained(FINE_TUNED_MODEL_PATH)


# --- 3. Prediction (Inference) ---

class DocumentClassifier:
    def __init__(self, model_path):
        """Loads the fine-tuned model and tokenizer from a specified path."""
        print(f"Loading model from {model_path}...")
        self.device = "cuda" if torch.cuda.is_available() else "cpu"
        print(f"Using device: {self.device}")

        self.tokenizer = AutoTokenizer.from_pretrained(model_path)
        self.model = AutoModelForSequenceClassification.from_pretrained(model_path).to(self.device)
        self.model.eval()  # Set model to evaluation mode

    def classify(self, file_path):
        """Classifies a single document given its file path."""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                text = f.read()
        except FileNotFoundError:
            return "Error: File not found.", 0.0

        # Tokenize the input text
        inputs = self.tokenizer(text, return_tensors="pt", truncation=True, padding=True, max_length=512)
        inputs = {k: v.to(self.device) for k, v in inputs.items()}

        # Get model prediction
        with torch.no_grad():
            outputs = self.model(**inputs)

        # Get probabilities using softmax
        logits = outputs.logits
        probabilities = torch.nn.functional.softmax(logits, dim=-1)[0]

        # Get the highest probability prediction
        predicted_class_id = torch.argmax(probabilities).item()
        predicted_class_name = self.model.config.id2label[predicted_class_id]
        confidence = probabilities[predicted_class_id].item()

        return predicted_class_name, confidence


# --- Main Execution ---
if __name__ == "__main__":
    # Check if a model is already trained. If not, train it.
    if not os.path.exists(FINE_TUNED_MODEL_PATH):
        print("Fine-tuned model not found. Starting the data preparation and training process.")

        # Ensure data directory exists
        if not os.path.exists(DATA_DIRECTORY) or not os.listdir(DATA_DIRECTORY):
            print(f"\nERROR: The directory '{DATA_DIRECTORY}' is empty or does not exist.")
            print("Please create it and add your labeled document folders and .txt files.")
        else:
            # 1. Prepare Data
            main_df, id2label_map, label2id_map = load_and_prepare_data(DATA_DIRECTORY)

            # 2. Fine-tune the model
            fine_tune_model(main_df, id2label_map, label2id_map)

    # 3. Use the model for prediction
    print("\n--- Document Classification Inference ---")
    if os.path.exists(FINE_TUNED_MODEL_PATH):
        # Initialize the classifier with our fine-tuned model
        classifier = DocumentClassifier(model_path=FINE_TUNED_MODEL_PATH)

        # --- PREDICT A NEW DOCUMENT ---
        # Replace this with the actual path to a new document you want to classify
        # For this example, we'll create a dummy file.
        test_file_path = "sample_document_to_classify.txt"

        print(f"\nClassifying document: '{test_file_path}'")
        predicted_type, confidence_score = classifier.classify(test_file_path)

        print(f"\nPredicted Document Type: '{predicted_type}'")
        print(f"Confidence: {confidence_score:.2%}")

    else:
        print("\nCould not perform prediction because the model has not been trained yet.")
