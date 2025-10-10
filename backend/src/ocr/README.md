# OCR Engine System

This module provides a flexible OCR (Optical Character Recognition) system that allows you to easily swap between different OCR backends.

## Available Engines

### Tesseract (Default)
- **Pros**: Stable, lightweight, fast startup, good Docker support
- **Cons**: Lower accuracy for some languages
- **Best for**: Production environments, Docker containers

### EasyOCR
- **Pros**: Higher accuracy, better language support, modern deep learning
- **Cons**: Heavy, slow startup, memory intensive, can cause segfaults
- **Best for**: High accuracy requirements, development

## Usage

### Basic Usage
```python
from src.ocr import create_ocr_engine, OCREngineType

# Use default engine (Tesseract)
engine = create_ocr_engine()

# Use specific engine
engine = create_ocr_engine(OCREngineType.EASYOCR)

# Use with specific languages
engine = create_ocr_engine(
    OCREngineType.TESSERACT, 
    languages=['eng', 'spa']
)

# Extract text
text = engine.extract_text('/path/to/image.png')
```

### Configuration
The system uses Tesseract by default for stability and performance. To use EasyOCR, modify the code directly:

```python
# Use Tesseract (default)
engine = create_ocr_engine(OCREngineType.TESSERACT)

# Use EasyOCR (for development/testing)
engine = create_ocr_engine(OCREngineType.EASYOCR)
```

### Legacy Interface
The old interface still works for backward compatibility:
```python
from src.ocr.ocr_reader import extract_text_from_image

text = extract_text_from_image('/path/to/image.png', 'eng+spa')
```

## Engine Comparison

| Feature | Tesseract | EasyOCR |
|---------|-----------|---------|
| Startup Time | Fast | Slow (downloads models) |
| Memory Usage | Low | High |
| Accuracy | Good | Excellent |
| Docker Support | Excellent | Good |
| Language Support | Many | Many |
| Stability | High | Medium |

## Recommendations

- **Production**: Use Tesseract for stability and performance
- **Development**: Use EasyOCR for higher accuracy
- **Docker**: Use Tesseract to avoid memory issues
- **High Accuracy**: Use EasyOCR with sufficient resources
