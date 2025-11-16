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

from scanpro_lib.ocr import OCREngine
import joblib
import pandas as pd
from tqdm import tqdm
from scanpro_lib.utils.pdf_helper import PDFHelper
from scanpro_lib.ocr.factory import get_default_ocr_engine
from scanpro_lib.models.classifier import Page, TrainingData
from scanpro_lib.utils.text_preprocessing import DocumentMetrics


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
    Lightweight PDF processor for extracting raw OCR text.
    Used for training data preparation without text cleaning or metrics tracking.
    """
    def __init__(self, ocr_engine: OCREngine):
        self.ocr_engine = ocr_engine
    
    def extract_text_with_tesseract(
        self, 
        pdf_path: str, 
        max_pages: Optional[int] = None
    ) -> List[Page]:
        """
        Extract text using OCR engine (raw, unfiltered).
        
        Args:
            pdf_path: Path to PDF file
            max_pages: Maximum number of pages to process (None = all pages)
        
        Returns:
            List of Page objects with raw OCR text
        """
        pages = []
        
        # Extract pages using PDFHelper (can accept path directly)
        for page_data in PDFHelper.extract_pages_as_bytes(pdf_path):
            if max_pages is not None and page_data.page_number >= max_pages:
                break

            # Use OCR engine to extract text from page bytes (already in PNG format)
            ocr_result = self.ocr_engine.extract_text_from_bytes(
                page_data.image_bytes, 
                image_format='png'
            )
            
            # Create Page with raw OCR text (unfiltered)
            page = Page(
                page_number=page_data.page_number,
                text=ocr_result.text
            )
            pages.append(page)
        
        return pages
    
    def extract_text_native(
        self, 
        pdf_path: str, 
        max_pages: Optional[int] = None
    ) -> List[Page]:
        """
        Extract text using native PDF text extraction (raw, unfiltered).
        
        Args:
            pdf_path: Path to PDF file
            max_pages: Maximum number of pages to process (None = all pages)
        
        Returns:
            List of Page objects with raw native text
        """
        pages = []
        
        # Extract native text using PDFHelper (can accept path directly)
        # extract_pages_as_bytes now automatically extracts text from each page
        for page_data in PDFHelper.extract_pages_as_bytes(pdf_path):
            if max_pages is not None and page_data.page_number >= max_pages:
                break
            
            # Create Page with raw native text (unfiltered)
            page = Page(
                page_number=page_data.page_number,
                text=page_data.text
            )
            pages.append(page)
        
        return pages

def load_training_data(input_path: Path, max_pages: int = None) -> TrainingData:
    """
    Load TrainingData from disk using Pydantic model_validate.
    
    Args:
        input_path: Path to the JSON file containing TrainingData
    
    Returns:
        TrainingData object or None if file doesn't exist
    """
    import json
    
    if not input_path.exists():
        raise FileNotFoundError(f"Training data file not found: {input_path}")
    
    # Load JSON and validate using Pydantic model_validate
    with open(input_path, 'r', encoding='utf-8') as f:
        data_dict = json.load(f)
    
    # Use Pydantic model_validate to create and validate the TrainingData object
    training_data = TrainingData.model_validate(data_dict).trim_pages(max_pages)
    
    return training_data

def save_training_data(training_data: TrainingData, output_path: Path):
    """
    Save TrainingData to disk as JSON.
    
    Args:
        training_data: TrainingData object to save
        labels: List of integer labels (for backward compatibility)
        output_path: Path to save the JSON file
    """
    import json
    
    output_path.parent.mkdir(parents=True, exist_ok=True)
    
    # Convert TrainingData to dict and save as JSON
    training_data_dict = training_data.model_dump()
    
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(training_data_dict, f, indent=2, ensure_ascii=False)

def generate_training_data(
    data_dir: Path, 
    pdf_processor: PDFProcessor,
    use_tesseract: bool = True,
    max_pages: Optional[int] = None
) -> TrainingData:
    """
    Generate TrainingData from a directory of PDFs organized by category.
    
    Expected directory structure:
    data_dir/
        category1/
            file1.pdf
            file2.pdf
        category2/
            file1.pdf
            ...
    
    Args:
        data_dir: Path to the directory containing category subdirectories with PDFs
        pdf_processor: PDFProcessor instance for extracting raw text from PDFs
        use_tesseract: Whether to use Tesseract OCR (True) or native extraction (False)
        max_pages: Maximum number of pages to process per document (None = all pages)
    
    Returns:
        TrainingData object with all processed documents organized by category
        (contains raw, unfiltered OCR text)
    """
    from scanpro_lib.models.classifier import DocumentData
    from datetime import datetime, timezone
    
    category_data: Dict[str, List[DocumentData]] = {}
    class_names = sorted([
        d for d in os.listdir(data_dir) 
        if os.path.isdir(os.path.join(data_dir, d))
    ])
    
    # Initialize category_data for all categories
    for cls in class_names:
        category_data[cls] = []
    
    print(f"\n📚 Processing dataset from {data_dir}")
    print(f"📁 Found {len(class_names)} categories: {class_names}\n")
    
    total_documents = 0
    
    for cls in tqdm(class_names, desc="Processing categories"):
        folder = os.path.join(data_dir, cls)
        pdf_files = [f for f in os.listdir(folder) if f.endswith(".pdf")]
        
        for filename in tqdm(pdf_files, desc=f"  {cls}", leave=False):
            pdf_path = os.path.join(folder, filename)
            
            try:
                # Extract raw pages using the PDF processor (no cleaning)
                if use_tesseract:
                    pages = pdf_processor.extract_text_with_tesseract(
                        pdf_path, max_pages=max_pages
                    )
                else:
                    pages = pdf_processor.extract_text_native(
                        pdf_path, max_pages=max_pages
                    )
                
                # Create DocumentData with raw OCR pages
                doc_data = DocumentData(
                    num_pages=len(pages),
                    file_name=filename,
                    pages=pages
                )
                
                category_data[cls].append(doc_data)
                total_documents += 1
                
            except Exception as e:
                print(f"⚠️  Error processing {filename}: {e}")
                continue
    
    print(f"\n✅ Processed {total_documents} documents")
    
    # Create TrainingData object
    training_data = TrainingData(
        categories=class_names,
        category_data=category_data,
        num_documents=total_documents,
        timestamp=datetime.now(timezone.utc).isoformat()
    )
    
    return training_data