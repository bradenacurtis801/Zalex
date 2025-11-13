"""
Training script for TF-IDF + Naive Bayes document classifier.
Uses shared utilities from backend for consistent preprocessing.
"""

import os
import sys
import time
from pathlib import Path
from typing import List

from config import DOCUMENT_RAW_DIR, TRAINING_RESULTS_DIR, DOCUMENT_DATASET_DIR

# Add backend to path so we can import shared utilities
backend_path = Path(__file__).parent.parent / "backend"
sys.path.insert(0, str(backend_path))

from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics import accuracy_score, classification_report
from sklearn.naive_bayes import MultinomialNB
from sklearn.model_selection import train_test_split, GridSearchCV
from sklearn.linear_model import LogisticRegression
from tqdm import tqdm
import joblib

# Import shared utilities from backend
from src.utils.text_preprocessing import TextCleaner, DocumentMetrics
from src.utils.training_utils import (
    MetricsTracker,
    PDFProcessor,
    save_processed_data,
    load_processed_data,
)

# Import config
from config import ML_MODELS_DIR

# ========== CONFIG ==========
DATA_DIR = DOCUMENT_RAW_DIR
PROCESSED_DATA_DIR = DOCUMENT_DATASET_DIR
PROCESSED_DATA_FILE = PROCESSED_DATA_DIR / "processed_training_data.joblib"
CLASSIFIER_MODEL_ID = "bradenacurtis/scanpro-classifier-tfidf"
CLASSIFIER_MODEL_DIR = ML_MODELS_DIR / CLASSIFIER_MODEL_ID.replace("/", "-")

def load_dataset(data_dir: Path, pdf_processor: PDFProcessor, use_tesseract: bool = True, 
                 use_cache: bool = True, force_reprocess: bool = False):
    """
    Load dataset with comprehensive metrics tracking and caching support.
    
    Args:
        data_dir: Directory containing category subdirectories
        pdf_processor: PDFProcessor instance with metrics tracking
        use_tesseract: Whether to use Tesseract OCR or native extraction
        use_cache: Whether to use cached processed data if available
        force_reprocess: Force reprocessing even if cached data exists
    
    Returns:
        Tuple of (texts, labels, class_names)
    """
    # Try to load from cache first
    if use_cache and not force_reprocess:
        cached_data = load_processed_data(PROCESSED_DATA_FILE)
        if cached_data is not None:
            texts, labels, class_names, _ = cached_data
            return texts, labels, class_names
    
    # Process from raw PDFs
    texts, labels = [], []
    original_texts = []  # Store original raw texts
    class_names = sorted([d for d in os.listdir(data_dir) if os.path.isdir(os.path.join(data_dir, d))])
    class_to_idx = {c: i for i, c in enumerate(class_names)}

    print(f"\n📚 Processing dataset from {data_dir}")
    print(f"📁 Found {len(class_names)} categories: {class_names}\n")

    for cls in tqdm(class_names, desc="Processing categories"):
        folder = os.path.join(data_dir, cls)
        pdf_files = [f for f in os.listdir(folder) if f.endswith(".pdf")]
        
        for filename in tqdm(pdf_files, desc=f"  {cls}", leave=False):
            pdf_path = os.path.join(folder, filename)
            
            try:
                if use_tesseract:
                    original_text, cleaned_text, metrics = pdf_processor.extract_text_with_tesseract(
                        pdf_path, filename, cls
                    )
                else:
                    original_text, cleaned_text, metrics = pdf_processor.extract_text_native(
                        pdf_path, filename, cls
                    )
                
                texts.append(cleaned_text)
                original_texts.append(original_text)
                labels.append(class_to_idx[cls])
                
            except Exception as e:
                print(f"⚠️  Error processing {filename}: {e}")
                continue
    
    print(f"\n✅ Processed {len(texts)} documents")
    
    # Save processed data for future use (including original texts)
    if use_cache:
        save_processed_data(texts, labels, class_names, PROCESSED_DATA_FILE, original_texts)
    
    return texts, labels, class_names

# ========== MAIN TRAINING PIPELINE ==========

def main():
    """Main training pipeline with comprehensive metrics tracking"""
    
    # Initialize metrics tracker
    CLASSIFIER_MODEL_DIR.mkdir(parents=True, exist_ok=True)
    metrics_tracker = MetricsTracker(CLASSIFIER_MODEL_DIR)
    
    # Initialize components with metrics tracking
    # TextCleaner will track metrics when return_metrics=True is passed
    text_cleaner = TextCleaner(track_metrics=True)
    pdf_processor = PDFProcessor(text_cleaner, metrics_tracker=metrics_tracker)
    
    print("="*60)
    print("🚀 Starting Training Pipeline with Metrics Tracking")
    print("="*60)
    
    # ========== LOAD DATA ==========
    # Check if we should use cached data or reprocess
    use_cache = True  # Set to False to always reprocess
    force_reprocess = False  # Set to True to force reprocessing even if cache exists
    
    start_time = time.time()
    texts, labels, class_names = load_dataset(
        DATA_DIR, 
        pdf_processor, 
        use_tesseract=True,
        use_cache=use_cache,
        force_reprocess=force_reprocess
    )
    load_time = time.time() - start_time
    metrics_tracker.record_timing("dataset_loading", load_time)
    
    # ========== TRAIN/TEST SPLIT ==========
    start_time = time.time()
    X_train, X_test, y_train, y_test = train_test_split(
        texts, labels, test_size=0.2, stratify=labels, random_state=42
    )
    split_time = time.time() - start_time
    metrics_tracker.record_timing("train_test_split", split_time)
    
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
    # Save to a dedicated folder for this classifier
    CLASSIFIER_MODEL_DIR.mkdir(parents=True, exist_ok=True)
    
    model_path = CLASSIFIER_MODEL_DIR / "document_classifier_nb.joblib"
    vectorizer_path = CLASSIFIER_MODEL_DIR / "tfidf_vectorizer.joblib"
    class_names_path = CLASSIFIER_MODEL_DIR / "class_names.json"
    
    joblib.dump(clf, model_path)
    joblib.dump(vectorizer, vectorizer_path)
    
    # Save class names mapping (important for proper category names)
    import json
    class_names_data = {
        "class_names": class_names,
        "id2label": {i: name for i, name in enumerate(class_names)},
        "label2id": {name: i for i, name in enumerate(class_names)}
    }
    with open(class_names_path, 'w', encoding='utf-8') as f:
        json.dump(class_names_data, f, indent=2, ensure_ascii=False)
    
    print(f"\n✅ Model saved to: {model_path}")
    print(f"✅ Vectorizer saved to: {vectorizer_path}")
    print(f"✅ Class names saved to: {class_names_path}")
    print(f"📁 Model folder: {CLASSIFIER_MODEL_DIR}")
    
    # ========== EXPORT METRICS ==========
    metrics_tracker.print_summary()
    json_path, csv_path = metrics_tracker.export_metrics()
    
    print("\n" + "="*60)
    print("✅ Training Pipeline Complete!")
    print("="*60)
    print(f"\n📊 Metrics exported:")
    print(f"   Summary: {json_path}")
    if csv_path:
        print(f"   Documents: {csv_path}")
    print("\n💡 Use these metrics to analyze:")
    print("   - Cleaning effectiveness per category")
    print("   - Processing time bottlenecks")
    print("   - Text reduction patterns")
    print("   - OCR error frequency")
    print("="*60 + "\n")


if __name__ == "__main__":
    main()
