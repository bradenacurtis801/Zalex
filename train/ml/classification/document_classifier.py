import pandas as pd
import numpy as np
import torch
import evaluate
from datasets import Dataset, DatasetDict
from transformers import (
    AutoTokenizer,
    AutoModelForSequenceClassification,
    TrainingArguments,
    Trainer,
    DataCollatorWithPadding
)


def create_dataset(df, label_map):
    """Converts a pandas DataFrame into a Hugging Face Dataset object."""
    # Map string labels to integer IDs
    df['label'] = df['doc_type'].map(label_map)
    # Create the Dataset object
    return Dataset.from_pandas(df)


def tokenize_function(examples):
    """Tokenizes the text data."""
    # The tokenizer will pad and truncate the text to the model's max input length.[1]
    return tokenizer(examples["text"], truncation=True, padding="max_length")


def compute_metrics(eval_pred):
    """Computes accuracy metric for evaluation."""
    predictions, labels = eval_pred
    # Get the prediction with the highest probability
    predictions = np.argmax(predictions, axis=1)
    return accuracy.compute(predictions=predictions, references=labels)


def predict(text, model, tokenizer):
    """Makes a prediction on a single piece of text."""
    # Tokenize the input text
    inputs = tokenizer(text, return_tensors="pt", truncation=True, padding=True)

    # Move inputs to the same device as the model
    inputs = {k: v.to(model.device) for k, v in inputs.items()}

    # Get model output (logits)
    with torch.no_grad():
        outputs = model(**inputs)

    # Get the predicted class ID by finding the max logit
    predicted_class_id = torch.argmax(outputs.logits, dim=-1).item()

    # Map the class ID back to the string label
    return model.config.id2label[predicted_class_id]


if __name__ == '__main__':
    # --- 1. Data Preparation ---
    # In a real application, this DataFrame would be created from your OCR output.
    data = {
        'text': [
            'This is a birth certificate for John Doe',
            'Marriage license for Jane and John Smith',
            'Property deed for 123 Main Street',
            'Birth certificate for Alice Johnson',
            'Marriage license for Bob and Carol Wilson',
            'Property deed for 456 Oak Avenue',
            'Birth certificate for David Brown',
            'Marriage license for Eve and Frank Davis',
            'Property deed for 789 Pine Street'
        ],
        'doc_type': [
            'birth_certificate', 'marriage_license', 'property_deed',
            'birth_certificate', 'marriage_license', 'property_deed',
            'birth_certificate', 'marriage_license', 'property_deed'
        ]
    }
    df = pd.DataFrame(data)

    # --- 2. Label Mapping ---
    # Create mappings from class names to integer IDs and back.[1]
    labels = df['doc_type'].unique().tolist()
    label2id = {label: i for i, label in enumerate(labels)}
    id2label = {i: label for i, label in enumerate(labels)}
    num_labels = len(labels)

    print(f"Label to ID Mapping: {label2id}")
    print(f"ID to Label Mapping: {id2label}\n")

    # --- 3. Create and Tokenize Dataset ---
    # Convert pandas DataFrame to Hugging Face Dataset
    full_dataset = create_dataset(df, label2id)

    # Split the dataset into training and testing sets
    train_test_split = full_dataset.train_test_split(test_size=0.3)
    dataset_dict = DatasetDict({
        'train': train_test_split['train'],
        'test': train_test_split['test']
    })

    # Load the tokenizer for DistilBERT
    model_checkpoint = "distilbert-base-uncased"
    tokenizer = AutoTokenizer.from_pretrained(model_checkpoint)

    # Apply the tokenization function to the entire dataset
    tokenized_datasets = dataset_dict.map(tokenize_function, batched=True)
    print("Tokenized Datasets:")
    print(tokenized_datasets)

    # --- 4. Model Training ---
    # Load the pre-trained DistilBERT model, configured for our multi-class problem.[1, 2]
    model = AutoModelForSequenceClassification.from_pretrained(
        model_checkpoint,
        num_labels=num_labels,
        id2label=id2label,
        label2id=label2id
    )

    # Import config paths
    from config import TRAINING_RESULTS_DIR, TRAINING_LOGS_DIR
    
    # Define training arguments
    training_args = TrainingArguments(
        output_dir=str(TRAINING_RESULTS_DIR),
        evaluation_strategy="epoch",
        learning_rate=2e-5,
        per_device_train_batch_size=4,
        per_device_eval_batch_size=4,
        num_train_epochs=3,
        weight_decay=0.01,
        logging_dir=str(TRAINING_LOGS_DIR),
        logging_steps=1,
    )

    # Load the evaluation metric
    accuracy = evaluate.load("accuracy")

    # The Trainer class handles the entire training and evaluation loop.[1, 3]
    trainer = Trainer(
        model=model,
        args=training_args,
        train_dataset=tokenized_datasets["train"],
        eval_dataset=tokenized_datasets["test"],
        tokenizer=tokenizer,
        compute_metrics=compute_metrics,
    )

    print("\n--- Starting Model Training ---")
    trainer.train()
    print("--- Training Finished ---\n")

    # --- 5. Evaluation and Prediction ---
    print("\n--- Evaluating Model on Test Set ---")
    eval_results = trainer.evaluate()
    print(f"Evaluation Accuracy: {eval_results['eval_accuracy']:.4f}\n")

    # Example of making a prediction on new text
    print("--- Making a Prediction on New Text ---")
    new_document_text = "This is a legal document detailing the sale of a house from the seller to the buyer."
    predicted_label = predict(new_document_text, model, tokenizer)

    print(f"Input Text: '{new_document_text}'")
    print(f"Predicted Document Type: '{predicted_label}'")
