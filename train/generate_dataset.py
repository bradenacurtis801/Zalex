"""
Script to generate training data from PDFs and save to TRAINING_DATA_PATH.

This script processes PDFs organized by category and generates a TrainingData object
that can be used for model training.
"""

import lib.constants as c
from lib.utils.training_utils import (
    PDFProcessor,
    generate_training_data,
    save_training_data,
)
from lib.ocr.factory import get_default_ocr_engine


def main():
    """Generate training data from PDFs and save to disk."""
    
    print("="*60)
    print("🚀 Starting Training Data Generation")
    print("="*60)
    
    # Initialize components
    print("\n📦 Initializing components...")
    
    # Initialize OCR engine
    ocr_engine = get_default_ocr_engine()
    ocr_engine.initialize()
    print("   ✅ OCR engine initialized")
    
    # Initialize PDF processor (lightweight, no cleaning or metrics)
    pdf_processor = PDFProcessor(ocr_engine)
    print("   ✅ PDF processor initialized")
    
    # Generate training data
    print(f"\n📚 Generating training data from: {c.DOCUMENT_RAW_DIR}")
    training_data = generate_training_data(
        data_dir=c.DOCUMENT_RAW_DIR,
        pdf_processor=pdf_processor,
        use_tesseract=True,
        max_pages=None  # Process all pages
    )
    
    # Save training data
    print(f"\n💾 Saving training data to: {c.TRAINING_DATA_PATH}")
    save_training_data(training_data, c.TRAINING_DATA_PATH)
    
    # Print summary
    print("\n" + "="*60)
    print("✅ Training Data Generation Complete!")
    print("="*60)
    print(f"\n📊 Summary:")
    print(f"   Total documents: {training_data.num_documents}")
    print(f"   Categories: {len(training_data.categories)}")
    print(f"   Categories: {', '.join(training_data.categories)}")
    print(f"   Saved to: {c.TRAINING_DATA_PATH}")
    print(f"   Timestamp: {training_data.timestamp}")
    
    print("="*60 + "\n")


if __name__ == "__main__":
    main()

