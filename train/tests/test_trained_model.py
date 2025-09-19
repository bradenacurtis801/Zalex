#!/usr/bin/env python3
"""
Test script for the trained Spanish document classifier.
"""

import sys
from pathlib import Path

# Add the train directory to Python path
sys.path.insert(0, str(Path(__file__).parent.parent))

from ml.classification.finetune_and_predict import DocumentClassifier
from config import DOCUMENT_DATASET_DIR, SPANISH_CLASSIFIER_MODEL

def test_trained_model():
    """Test the trained model with sample documents."""
    print("=== Testing Trained Spanish Document Classifier ===")
    print("=" * 60)
    
    # Path to your trained model
    model_path = str(SPANISH_CLASSIFIER_MODEL)
    
    try:
        # Load the trained model
        print("Loading trained model...")
        classifier = DocumentClassifier(model_path)
        print("✅ Model loaded successfully!")
        
        # Test with sample documents using config constants
        test_documents = [
            str(DOCUMENT_DATASET_DIR.parent / "sample_document_to_classify.txt"),
            str(DOCUMENT_DATASET_DIR / "birth_certificate" / "acta-de-nacimiento.txt"),
            str(DOCUMENT_DATASET_DIR / "marriage_certificate" / "Bestaetigte-Uebersetzung-Heiratsurkunde-Mexiko.txt"),
            str(DOCUMENT_DATASET_DIR / "property_deeds" / "page1_image1.txt")
        ]
        
        print("\n" + "=" * 60)
        print("Testing with sample documents:")
        print("=" * 60)
        
        for doc_path in test_documents:
            if Path(doc_path).exists():
                print(f"\n📄 Testing: {doc_path}")
                print("-" * 40)
                
                try:
                    predicted_class, confidence = classifier.classify(doc_path)
                    print(f"🎯 Predicted class: {predicted_class}")
                    print(f"📊 Confidence: {confidence:.2%}")
                    
                    # Add confidence interpretation
                    if confidence > 0.8:
                        print("✅ High confidence prediction")
                    elif confidence > 0.6:
                        print("⚠️  Medium confidence prediction")
                    else:
                        print("❌ Low confidence prediction")
                        
                except Exception as e:
                    print(f"❌ Error processing {doc_path}: {e}")
            else:
                print(f"⚠️  File not found: {doc_path}")
        
        print("\n" + "=" * 60)
        print("✅ Model testing complete!")
        
    except Exception as e:
        print(f"❌ Failed to load model: {e}")
        return False
    
    return True

def test_with_custom_text():
    """Test the model with custom text input."""
    print("\n" + "=" * 60)
    print("Testing with custom text:")
    print("=" * 60)
    
    # Create a temporary test file with more diverse text
    test_texts = [
        ("Birth Certificate", "ACTA DE NACIMIENTO\n\nNombre: Juan Carlos Pérez\nFecha de nacimiento: 15 de marzo de 1990\nLugar: Hospital San Carlos, Madrid\nPadre: Carlos Pérez\nMadre: María González"),
        ("Marriage Certificate", "CERTIFICADO DE MATRIMONIO\n\nContrayentes: María García López y Carlos Rodríguez\nFecha: 20 de junio de 2020\nLugar: Registro Civil de Madrid\nTestigos: Ana Martín y Pedro Sánchez"),
        ("Property Deed", "ESCRITURA DE COMPRAVENTA\n\nVendedor: Inmobiliaria Madrid S.L.\nComprador: Juan Pérez García\nPropiedad: Calle Mayor 123, Madrid\nPrecio: 250.000 euros\nFecha: 15 de enero de 2021")
    ]
    
    model_path = str(SPANISH_CLASSIFIER_MODEL)
    
    try:
        classifier = DocumentClassifier(model_path)
        
        for doc_type, text in test_texts:
            # Create temporary file
            temp_file = Path("temp_test.txt")
            temp_file.write_text(text, encoding='utf-8')
            
            try:
                predicted_class, confidence = classifier.classify(str(temp_file))
                print(f"\n📝 Text: {text[:50]}...")
                print(f"🎯 Predicted: {predicted_class}")
                print(f"📊 Confidence: {confidence:.2%}")
                print(f"✅ Expected: {doc_type}")
                
            finally:
                # Clean up temp file
                if temp_file.exists():
                    temp_file.unlink()
                    
    except Exception as e:
        print(f"❌ Error in custom text testing: {e}")

if __name__ == "__main__":
    print("🧪 Testing Trained Spanish Document Classifier")
    print("=" * 60)
    
    # Test with existing documents
    success = test_trained_model()
    
    if success:
        # Test with custom text
        test_with_custom_text()
    
    print("\n🎉 Testing complete!")
