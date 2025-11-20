"""
Training script for TF-IDF + Naive Bayes document classifier.
Uses shared utilities from backend for consistent preprocessing.
"""

import os
import sys
import time
from pathlib import Path
from typing import List, Dict, Optional, Tuple
import json

import lib.constants as c

from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics import accuracy_score, classification_report
from sklearn.naive_bayes import MultinomialNB
from sklearn.model_selection import train_test_split
from sklearn.linear_model import LogisticRegression
from tqdm import tqdm
import joblib

# Import shared utilities from backend
from lib.utils.text_preprocessing import TextCleaner, DocumentMetrics
from lib.utils.training_utils import (
    MetricsTracker,
    PDFProcessor,
    load_training_data,
    save_training_data,
)
from lib.ocr.factory import get_default_ocr_engine

from lib.utils.file_hasher import calculate_file_hash
from lib.models.classifier import (
    Page, 
    DocumentData, 
    TrainingData, 
    TFIDFClassifierModel,
    TrainingMetadata
)

# ========== CONFIG ==========
DATA_DIR = c.DOCUMENT_RAW_DIR
PROCESSED_DATA_DIR = c.DOCUMENT_DATASET_DIR

CLASSIFIER_MODEL_ID = "bradenacurtis/classifier-tfidf"
CLASSIFIER_MODEL_DIR = c.ML_MODELS_DIR / CLASSIFIER_MODEL_ID.replace("/", "-")

MAX_PAGE = 5
    
def main():
    """Main training pipeline with comprehensive metrics tracking"""
    
    # Initialize metrics tracker
    CLASSIFIER_MODEL_DIR.mkdir(parents=True, exist_ok=True)
    metrics_tracker = MetricsTracker(CLASSIFIER_MODEL_DIR)
    
    # Initialize OCR engine
    ocr_engine = get_default_ocr_engine()
    ocr_engine.initialize()
    
    # Initialize text cleaner for cleaning text during training
    text_cleaner = TextCleaner(track_metrics=True)
    
    print("="*60)
    print("🚀 Starting Training Pipeline with Metrics Tracking")
    print("="*60)
    
    training_data = load_training_data(c.TRAINING_DATA_PATH, max_pages=MAX_PAGE)
    
    # Extract texts and labels from TrainingData
    raw_texts = training_data.extract_texts()
    labels = training_data.extract_labels()
    class_names = training_data.categories
    
    # Clean texts for training (lightweight function when needed)
    print("\n🧹 Cleaning texts for training...")
    texts = []
    for raw_text in tqdm(raw_texts, desc="Cleaning texts"):
        cleaned_text, metrics = text_cleaner.clean_text(raw_text, return_metrics=True)
        texts.append(cleaned_text)
    
    # Extract file hashes (in same order as texts)
    file_hashes = training_data.extract_file_hashes()
    
    # ========== TRAIN/TEST SPLIT ==========
    start_time = time.time()
    # Split texts, labels, and hashes together
    X_train, X_test, y_train, y_test, train_hashes, test_hashes = train_test_split(
        texts, labels, file_hashes, test_size=0.2, stratify=labels, random_state=42
    )
    split_time = time.time() - start_time
    metrics_tracker.record_timing("train_test_split", split_time)
    
    # Store training data hashes
    train_data_hashes = train_hashes
    
    print(f"\n📊 Dataset split: {len(X_train)} train, {len(X_test)} test")
    
    # ========== FEATURE EXTRACTION ==========
    start_time = time.time()
    # Improved TF-IDF parameters for better confidence
    vectorizer = TfidfVectorizer(
        max_features=10000,  # Increased from 5000 for more discriminative features
        ngram_range=(1, 3),  # Added trigrams for better context
        min_df=2,  # Ignore terms that appear in fewer than 2 documents
        max_df=0.95,  # Ignore terms that appear in more than 95% of documents
        sublinear_tf=True,  # Apply sublinear tf scaling (1 + log(tf))
        norm='l2',  # L2 normalization
        smooth_idf=True  # Smooth idf weights
    )
    X_train_vec = vectorizer.fit_transform(X_train)
    X_test_vec = vectorizer.transform(X_test)
    feature_time = time.time() - start_time
    metrics_tracker.record_timing("feature_extraction", feature_time)
    
    # Record feature statistics
    metrics_tracker.record_feature_stats({
        'vocabulary_size': len(vectorizer.vocabulary_),
        'max_features': 10000,
        'ngram_range': '(1,3)',
        'min_df': 2,
        'max_df': 0.95,
        'sublinear_tf': True,
        'train_samples': X_train_vec.shape[0],
        'test_samples': X_test_vec.shape[0],
        'feature_dim': X_train_vec.shape[1],
    })
    
    print(f"📈 Feature extraction complete: {X_train_vec.shape[1]} features")
    
    # ========== TRAIN MODEL ==========
    start_time = time.time()
    # Try both MultinomialNB and LogisticRegression, pick the best
    print("\n🔍 Training models to find best configuration...")
    
    # MultinomialNB with optimized alpha
    nb_clf = MultinomialNB(alpha=0.1)  # Lower alpha = less smoothing, more confident
    nb_clf.fit(X_train_vec, y_train)
    nb_train_proba = nb_clf.predict_proba(X_train_vec)
    nb_train_conf = [max(p) for p in nb_train_proba]
    nb_train_mean_conf = sum(nb_train_conf) / len(nb_train_conf)
    
    # LogisticRegression (often gives higher confidence)
    lr_clf = LogisticRegression(
        max_iter=1000,
        C=1.0,  # Regularization strength
        multi_class='multinomial',
        solver='lbfgs',
        class_weight='balanced'  # Handle class imbalance
    )
    lr_clf.fit(X_train_vec, y_train)
    lr_train_proba = lr_clf.predict_proba(X_train_vec)
    lr_train_conf = [max(p) for p in lr_train_proba]
    lr_train_mean_conf = sum(lr_train_conf) / len(lr_train_conf)
    
    # Choose model with higher average confidence
    if lr_train_mean_conf > nb_train_mean_conf:
        clf = lr_clf
        model_type = "LogisticRegression"
        print(f"   Selected LogisticRegression (mean confidence: {lr_train_mean_conf:.3f})")
    else:
        clf = nb_clf
        model_type = "MultinomialNB"
        print(f"   Selected MultinomialNB (mean confidence: {nb_train_mean_conf:.3f})")
    
    train_time = time.time() - start_time
    metrics_tracker.record_timing("model_training", train_time)
    metrics_tracker.record_model_metrics({'model_type': model_type})
    
    print(f"✅ Model training complete in {train_time:.2f}s")
    
    # ========== EVALUATE ==========
    start_time = time.time()
    y_pred = clf.predict(X_test_vec)
    y_pred_proba = clf.predict_proba(X_test_vec)
    eval_time = time.time() - start_time
    metrics_tracker.record_timing("model_evaluation", eval_time)
    
    acc = accuracy_score(y_test, y_pred)
    
    # Calculate confidence scores (max probability for each prediction)
    test_confidences = [max(proba) for proba in y_pred_proba]
    
    # Also evaluate on training data to see training confidence
    y_train_pred = clf.predict(X_train_vec)
    y_train_proba = clf.predict_proba(X_train_vec)
    train_confidences = [max(proba) for proba in y_train_proba]
    train_acc = accuracy_score(y_train, y_train_pred)
    
    # Record model metrics
    metrics_tracker.record_model_metrics({
        'validation_accuracy': float(acc),
        'train_accuracy': float(train_acc),
        'test_samples': len(y_test),
        'train_samples': len(y_train),
        'test_confidence_mean': float(sum(test_confidences) / len(test_confidences)),
        'test_confidence_min': float(min(test_confidences)),
        'test_confidence_max': float(max(test_confidences)),
        'train_confidence_mean': float(sum(train_confidences) / len(train_confidences)),
        'train_confidence_min': float(min(train_confidences)),
        'train_confidence_max': float(max(train_confidences)),
    })
    
    print(f"\n🎯 Test Set Accuracy: {acc*100:.2f}%")
    print(f"🎯 Train Set Accuracy: {train_acc*100:.2f}%")
    
    # Confidence statistics
    print(f"\n📊 Confidence Statistics:")
    print(f"   Test Set:")
    print(f"      Mean: {sum(test_confidences)/len(test_confidences):.3f}")
    print(f"      Min:  {min(test_confidences):.3f}")
    print(f"      Max:  {max(test_confidences):.3f}")
    print(f"      < 0.6: {sum(1 for c in test_confidences if c < 0.6)} ({sum(1 for c in test_confidences if c < 0.6)/len(test_confidences)*100:.1f}%)")
    print(f"      < 0.5: {sum(1 for c in test_confidences if c < 0.5)} ({sum(1 for c in test_confidences if c < 0.5)/len(test_confidences)*100:.1f}%)")
    print(f"   Train Set:")
    print(f"      Mean: {sum(train_confidences)/len(train_confidences):.3f}")
    print(f"      Min:  {min(train_confidences):.3f}")
    print(f"      Max:  {max(train_confidences):.3f}")
    print(f"      < 0.6: {sum(1 for c in train_confidences if c < 0.6)} ({sum(1 for c in train_confidences if c < 0.6)/len(train_confidences)*100:.1f}%)")
    print(f"      < 0.5: {sum(1 for c in train_confidences if c < 0.5)} ({sum(1 for c in train_confidences if c < 0.5)/len(train_confidences)*100:.1f}%)")
    
    # Show some examples of low confidence predictions
    print(f"\n⚠️  Low Confidence Examples (Test Set, confidence < 0.6):")
    low_conf_examples = [(i, y_test[i], y_pred[i], test_confidences[i], y_pred_proba[i]) 
                         for i in range(len(y_test)) if test_confidences[i] < 0.6]
    if low_conf_examples:
        for idx, (i, true_label, pred_label, conf, proba) in enumerate(low_conf_examples[:5]):  # Show first 5
            true_cat = class_names[true_label]
            pred_cat = class_names[pred_label]
            proba_dict = {class_names[j]: proba[j] for j in range(len(class_names))}
            correct = "✓" if true_label == pred_label else "✗"
            print(f"   {correct} True: {true_cat:12} | Pred: {pred_cat:12} | Conf: {conf:.3f} | Probs: {proba_dict}")
    else:
        print("   (None found)")
    
    # Show low confidence examples from TRAINING set (these are the ambiguous documents)
    print(f"\n⚠️  Low Confidence Examples (Train Set, confidence < 0.6):")
    low_conf_train_examples = [(i, y_train[i], y_train_pred[i], train_confidences[i], y_train_proba[i]) 
                               for i in range(len(y_train)) if train_confidences[i] < 0.6]
    if low_conf_train_examples:
        for idx, (i, true_label, pred_label, conf, proba) in enumerate(low_conf_train_examples[:10]):  # Show first 10
            true_cat = class_names[true_label]
            pred_cat = class_names[pred_label]
            proba_dict = {class_names[j]: proba[j] for j in range(len(class_names))}
            correct = "✓" if true_label == pred_label else "✗"
            # Show text length for context
            text_len = len(X_train[i])
            print(f"   {correct} True: {true_cat:12} | Pred: {pred_cat:12} | Conf: {conf:.3f} | Len: {text_len:5} | Probs: {proba_dict}")
    else:
        print("   (None found)")
    
    print("\n📋 Classification Report (Test Set):")
    print(classification_report(y_test, y_pred, target_names=class_names))
    
    # ========== SAVE MODEL ==========
    # Prepare parameters for TrainingMetadata (using keyword arguments for clarity)
    training_params = {
        "model_id": CLASSIFIER_MODEL_ID,
        "model_type": model_type,
        "vectorizer": vectorizer,
        "classifier": clf,
        "class_names": class_names,
        "X_train": X_train,
        "X_test": X_test,
        "y_train": y_train,
        "y_test": y_test,
        "train_acc": train_acc,
        "test_acc": acc,
        "train_confidences": train_confidences,
        "test_confidences": test_confidences,
        "test_split_percentage": 20.0,
        "train_data_hashes": train_data_hashes,
    }
    
    # Create TFIDFClassifierModel instance and save all files
    classifier_model = TFIDFClassifierModel(
        model_dir=CLASSIFIER_MODEL_DIR,
        classifier_file=CLASSIFIER_MODEL_DIR / "document_classifier_nb.joblib",
        vectorizer_file=CLASSIFIER_MODEL_DIR / "tfidf_vectorizer.joblib",
        class_names_file=CLASSIFIER_MODEL_DIR / "class_names.json",
        training_metadata_file=CLASSIFIER_MODEL_DIR / "training_metadata.json",
        classifier=clf,
        vectorizer=vectorizer,
        training_params=training_params
    )
    classifier_model.save()
    
    print(f"\n✅ Model saved to: {classifier_model.classifier_file}")
    print(f"✅ Vectorizer saved to: {classifier_model.vectorizer_file}")
    print(f"✅ Class names saved to: {classifier_model.class_names_file}")
    print(f"✅ Training metadata saved to: {classifier_model.training_metadata_file}")
    print(f"📁 Model folder: {CLASSIFIER_MODEL_DIR}")
    
    # ========== EXPORT METRICS ==========
    metrics_tracker.print_summary()
    # json_path, csv_path = metrics_tracker.export_metrics()

if __name__ == "__main__":
    main()
