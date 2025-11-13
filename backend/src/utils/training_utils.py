"""
Training utilities for document classification.
Provides metrics tracking, dataset loading, and PDF processing for training pipelines.
"""

import io
import json
import os
import time
from collections import defaultdict
from dataclasses import asdict
from datetime import datetime
from functools import wraps
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

from src.ocr.base import OCREngine
import fitz  # PyMuPDF
import joblib
import pandas as pd
from tqdm import tqdm
from src.utils.pdf_helper import PDFHelper

from src.ocr.factory import get_default_ocr_engine

from .text_preprocessing import DocumentMetrics, TextCleaner


class MetricsTracker:
    """
    Observer Pattern: Tracks and aggregates metrics across the training pipeline.
    Acts as a central repository for all training metrics.
    """
    def __init__(self, output_dir: Path):
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)
        
        # Per-document metrics
        self.document_metrics: List[DocumentMetrics] = []
        
        # Aggregated metrics
        self.aggregated_stats: Dict[str, Any] = defaultdict(dict)
        
        # Pipeline timing
        self.pipeline_timings: Dict[str, float] = {}
        
        # Model performance
        self.model_metrics: Dict[str, Any] = {}
        
        # Feature extraction stats
        self.feature_stats: Dict[str, Any] = {}
        
    def record_document(self, metrics: DocumentMetrics):
        """Record metrics for a single document"""
        self.document_metrics.append(metrics)
    
    def record_timing(self, stage: str, duration: float):
        """Record time taken for a pipeline stage"""
        self.pipeline_timings[stage] = duration
    
    def record_model_metrics(self, metrics: Dict[str, Any]):
        """Record model performance metrics"""
        self.model_metrics.update(metrics)
    
    def record_feature_stats(self, stats: Dict[str, Any]):
        """Record feature extraction statistics"""
        self.feature_stats.update(stats)
    
    def aggregate_document_stats(self):
        """Aggregate statistics across all documents"""
        if not self.document_metrics:
            return
        
        df = pd.DataFrame([m.to_dict() for m in self.document_metrics])
        
        # Overall statistics
        self.aggregated_stats['overall'] = {
            'total_documents': len(df),
            'avg_original_words': df['original_words'].mean(),
            'avg_final_words': df['after_stopwords_words'].mean(),
            'avg_reduction_pct': ((df['original_words'] - df['after_stopwords_words']) / df['original_words'] * 100).mean(),
            'total_processing_time': df['processing_time'].sum(),
            'avg_processing_time': df['processing_time'].mean(),
        }
        
        # Per-category statistics
        for category in df['category'].unique():
            cat_df = df[df['category'] == category]
            self.aggregated_stats[f'category_{category}'] = {
                'count': len(cat_df),
                'avg_original_words': cat_df['original_words'].mean(),
                'avg_final_words': cat_df['after_stopwords_words'].mean(),
                'avg_reduction_pct': ((cat_df['original_words'] - cat_df['after_stopwords_words']) / cat_df['original_words'] * 100).mean(),
            }
        
        # Cleaning effectiveness
        self.aggregated_stats['cleaning_effectiveness'] = {
            'avg_ocr_fixes_per_doc': df['after_ocr_fix_words'].mean() - df['original_words'].mean(),
            'avg_artifacts_removed': df['after_ocr_artifacts_words'].mean() - df['after_ocr_fix_words'].mean(),
            'avg_stopwords_removed': df['removed_stopwords_count'].mean(),
            'stopword_removal_pct': (df['removed_stopwords_count'] / df['after_nonalpha_words'] * 100).mean(),
        }
    
    def export_metrics(self, filename: str = None):
        """Export all metrics to JSON and CSV files"""
        if filename is None:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"training_metrics_{timestamp}"
        
        # Aggregate stats
        self.aggregate_document_stats()
        
        # Export document-level metrics to CSV
        csv_path = None
        if self.document_metrics:
            df = pd.DataFrame([m.to_dict() for m in self.document_metrics])
            csv_path = self.output_dir / f"{filename}_documents.csv"
            df.to_csv(csv_path, index=False)
            print(f"📊 Document metrics exported to: {csv_path}")
        
        # Export aggregated metrics to JSON
        export_data = {
            'timestamp': datetime.now().isoformat(),
            'aggregated_stats': dict(self.aggregated_stats),
            'pipeline_timings': self.pipeline_timings,
            'model_metrics': self.model_metrics,
            'feature_stats': self.feature_stats,
        }
        
        json_path = self.output_dir / f"{filename}_summary.json"
        with open(json_path, 'w', encoding='utf-8') as f:
            json.dump(export_data, f, indent=2, ensure_ascii=False)
        print(f"📊 Summary metrics exported to: {json_path}")
        
        return json_path, csv_path
    
    def print_summary(self):
        """Print a human-readable summary of metrics"""
        self.aggregate_document_stats()
        
        print("\n" + "="*60)
        print("📊 TRAINING METRICS SUMMARY")
        print("="*60)
        
        if 'overall' in self.aggregated_stats:
            overall = self.aggregated_stats['overall']
            print(f"\n📄 Overall Statistics:")
            print(f"   Total Documents: {overall['total_documents']}")
            print(f"   Avg Original Words: {overall['avg_original_words']:.1f}")
            print(f"   Avg Final Words: {overall['avg_final_words']:.1f}")
            print(f"   Avg Reduction: {overall['avg_reduction_pct']:.1f}%")
            print(f"   Total Processing Time: {overall['total_processing_time']:.2f}s")
            print(f"   Avg Processing Time: {overall['avg_processing_time']:.3f}s/doc")
        
        if 'cleaning_effectiveness' in self.aggregated_stats:
            cleaning = self.aggregated_stats['cleaning_effectiveness']
            print(f"\n🧹 Cleaning Effectiveness:")
            print(f"   Avg Stopwords Removed: {cleaning['avg_stopwords_removed']:.1f}")
            print(f"   Stopword Removal Rate: {cleaning['stopword_removal_pct']:.1f}%")
        
        if self.pipeline_timings:
            print(f"\n⏱️  Pipeline Timings:")
            for stage, duration in self.pipeline_timings.items():
                print(f"   {stage}: {duration:.2f}s")
        
        if self.model_metrics:
            print(f"\n🎯 Model Performance:")
            for metric, value in self.model_metrics.items():
                print(f"   {metric}: {value}")
        
        print("="*60 + "\n")


def track_timing(func):
    """
    Decorator Pattern: Automatically tracks execution time of functions.
    Looks for metrics_tracker in the calling context.
    """
    @wraps(func)
    def wrapper(*args, **kwargs):
        start_time = time.time()
        result = func(*args, **kwargs)
        duration = time.time() - start_time
        
        # Try to find metrics_tracker from various sources
        tracker = None
        if kwargs.get('metrics_tracker'):
            tracker = kwargs['metrics_tracker']
        elif args and hasattr(args[0], 'metrics_tracker'):
            tracker = args[0].metrics_tracker
        
        if tracker and isinstance(tracker, MetricsTracker):
            func_name = func.__name__
            tracker.record_timing(func_name, duration)
        
        return result
    return wrapper


class PDFProcessor:
    """
    Builder Pattern: Builds the document processing pipeline with metrics tracking.
    Used for training data preparation.
    """
    def __init__(self, ocr_engine: OCREngine, text_cleaner: TextCleaner, metrics_tracker: Optional[MetricsTracker] = None):
        self.ocr_engine = ocr_engine
        self.text_cleaner = text_cleaner
        self.metrics_tracker = metrics_tracker
    
    def extract_text_with_tesseract(
        self, 
        pdf_path: str, 
        filename: str, 
        category: str, 
        max_pages: int = 5
    ) -> Tuple[str, str, DocumentMetrics]:
        """
        Extract text using OCR engine and clean it.
        
        Returns:
            Tuple of (original_text, cleaned_text, metrics)
        """
        raw_text = ""
        
        # Extract pages using PDFHelper (can accept path directly)
        for page_data in PDFHelper.extract_pages_as_bytes(pdf_path):
            if page_data.page_number >= max_pages:
                break
            # Use OCR engine to extract text from page bytes (already in PNG format)
            ocr_result = self.ocr_engine.extract_text_from_bytes(
                page_data.image_bytes, 
                image_format='png'
            )
            raw_text += ocr_result.text + "\n"
        
        # Clean text and get metrics
        cleaned_text, metrics = self.text_cleaner.clean_text(
            raw_text, filename, category, return_metrics=True
        )
        
        # Record metrics if tracker is available
        if self.metrics_tracker:
            self.metrics_tracker.record_document(metrics)
        
        return raw_text, cleaned_text, metrics
    
    def extract_text_native(
        self, 
        pdf_path: str, 
        filename: str, 
        category: str, 
        max_pages: int = 5
    ) -> Tuple[str, str, DocumentMetrics]:
        """
        Extract text using native PDF text extraction.
        
        Returns:
            Tuple of (original_text, cleaned_text, metrics)
        """
        raw_text = ""
        
        # Extract native text using PDFHelper (can accept path directly)
        # extract_pages_as_bytes now automatically extracts text from each page
        for page_data in PDFHelper.extract_pages_as_bytes(pdf_path):
            if page_data.page_number >= max_pages:
                break
            raw_text += page_data.text + "\n"
        
        # Clean text and get metrics
        cleaned_text, metrics = self.text_cleaner.clean_text(
            raw_text, filename, category, return_metrics=True
        )
        
        if self.metrics_tracker:
            self.metrics_tracker.record_document(metrics)
        
        return raw_text, cleaned_text, metrics


def save_processed_data(
    texts: List[str], 
    labels: List[int], 
    class_names: List[str], 
    output_path: Path, 
    original_texts: Optional[List[str]] = None
):
    """
    Save processed training data to disk for later reuse.
    This avoids reprocessing PDFs on subsequent training runs.
    """
    output_path.parent.mkdir(parents=True, exist_ok=True)
    
    data = {
        'texts': texts,  # Cleaned texts
        'labels': labels,
        'class_names': class_names,
        'timestamp': datetime.now().isoformat(),
        'num_documents': len(texts),
        'num_categories': len(class_names),
    }
    
    # Add original texts if provided
    if original_texts is not None:
        data['original_texts'] = original_texts
        print(f"💾 Saving both original and cleaned texts")
    
    joblib.dump(data, output_path)
    print(f"💾 Processed training data saved to: {output_path}")
    print(f"   Documents: {len(texts)}, Categories: {len(class_names)}")


def load_processed_data(
    input_path: Path
) -> Optional[Tuple[List[str], List[int], List[str], Optional[List[str]]]]:
    """
    Load previously processed training data from disk.
    Returns None if file doesn't exist or is invalid.
    
    Returns:
        Tuple of (texts, labels, class_names, original_texts) where original_texts may be None
    """
    if not input_path.exists():
        return None
    
    try:
        data = joblib.load(input_path)
        print(f"📂 Loading cached training data from: {input_path}")
        print(f"   Documents: {data['num_documents']}, Categories: {data['num_categories']}")
        if 'timestamp' in data:
            print(f"   Cached on: {data['timestamp']}")
        original_texts = data.get('original_texts', None)
        if original_texts:
            print(f"   Includes original raw texts: Yes")
        return data['texts'], data['labels'], data['class_names'], original_texts
    except Exception as e:
        print(f"⚠️  Error loading cached data: {e}")
        return None

