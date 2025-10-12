# Dataset Generation Package

A language-agnostic interface for generating training datasets with OCR error simulation.

> **Note**: This is a prototype that could replace `createDatasets.py` and be extended to handle specific document types like birth certificates, marriage certificates, and other official documents.

## Quick Start

```python
from dataset_gen import DatasetGeneratorFactory

# Create English implementation
en_data_gen, en_dataset_gen = DatasetGeneratorFactory.create('en')

# Generate sample data
print(en_data_gen.generate_name())
print(en_data_gen.generate_sentence())

# Generate dataset
templates = {'Document A': 'path/to/template.txt'}
en_dataset_gen.generate_dataset(templates, 1000, 0.05, 'output.csv')
```

## Features

- **Multi-language Support**: English and Spanish implementations included
- **OCR Error Simulation**: Realistic character confusion patterns
- **Template-based Generation**: Use placeholder tokens for dynamic content
- **Factory Pattern**: Easy creation and management of implementations
- **Caching**: Efficient memory usage with LanguageManager
- **Extensible**: Easy to add new languages
- **Namespace-based**: Simple `DataGenerator` and `DatasetGenerator` classes per language

## Supported Languages

- **English** (`en`, `english`)
- **Spanish** (`es`, `spanish`)

## Architecture

```
dataset_gen/
├── __init__.py              # Package exports
├── factory.py               # Main factory classes
├── interfaces.py            # Abstract base classes
├── implementations/
│   ├── __init__.py
│   ├── en.py                # English implementation
│   └── es.py                # Spanish implementation
└── README.md               # This file
```

## Usage Examples

### Basic Usage

```python
from dataset_gen import DatasetGeneratorFactory

# Create implementation
data_gen, dataset_gen = DatasetGeneratorFactory.create('en')

# Generate data
name = data_gen.generate_name()
sentence = data_gen.generate_sentence()
word = data_gen.generate_word()
```

### Dataset Generation

```python
# Define templates
templates = {
    'Document Type A': 'path/to/template1.txt',
    'Document Type B': 'path/to/template2.txt',
}

# Generate dataset
dataset_gen.generate_dataset(
    templates=templates,
    num_samples=1000,
    ocr_error_rate=0.05,
    output_file='training_data.csv'
)
```

### Using LanguageManager (Caching)

```python
from dataset_gen import LanguageManager

manager = LanguageManager()

# Get generators (cached after first use)
en_gen = manager.get_data_generator('en')
es_gen = manager.get_data_generator('es')

# Generate data
english_text = en_gen.generate_paragraph()
spanish_text = es_gen.generate_paragraph()
```

### Convenience Functions

```python
from dataset_gen import create_data_generator, create_dataset_generator

# Create only data generator
data_gen = create_data_generator('en')

# Create only dataset generator
dataset_gen = create_dataset_generator('es')
```

## Template Format

Templates use placeholder tokens:

- `{ID}` - Random ID number
- `{Name}` - Generated name
- `{Sentence}` - Generated sentence
- `{Paragraph}` - Generated paragraph
- `{Word}` - Generated word
- `{Phone}` - Generated phone number
- `{Address}` - Generated address
- `{Date}` - Generated date

Example template:
```
Document ID: {ID}
Name: {Name}
Description: {Paragraph}
Contact: {Phone}
Address: {Address}
Date: {Date}
```

## Adding New Languages

1. Create implementation file: `implementations/[language_code].py` (e.g., `fr.py`)
2. Implement `DataGenerator` and `DatasetGenerator` classes
3. Register using `DatasetGeneratorFactory.register_language()`

Example:
```python
# In implementations/fr.py
class DataGenerator(LanguageDataGenerator):
    # Implement all abstract methods

class DatasetGenerator(DatasetGeneratorInterface):
    # Implement all abstract methods

# Register the language
DatasetGeneratorFactory.register_language('french', 'fr')
```

## Dependencies

- `faker` - For generating realistic fake data
- `wonderwords` - For English word/sentence generation
- `random` - For randomization
- `csv` - For dataset output
- `os` - For file operations

## Error Handling

The factory includes proper error handling for:
- Unsupported languages
- Missing template files
- File I/O errors
- Invalid parameters

## Performance

- LanguageManager caches implementations for efficiency
- OCR error simulation is optimized for speed
- Memory usage is kept minimal through streaming
- Batch processing is supported for large datasets

## Future Expansion

This prototype could be extended to handle specific document types with specialized generators:

### Document Type Specialization
- **Birth Certificates**: Specialized templates and field generators for birth records
- **Marriage Certificates**: Custom data generation for marriage documentation
- **Driver's Licenses**: State-specific formatting and data patterns
- **Passports**: Country-specific document structures
- **Medical Records**: Healthcare-specific terminology and formatting

### Implementation Approach
```python
# Example: Birth certificate generator
class BirthCertificateGenerator(DatasetGeneratorInterface):
    def generate_birth_certificate_data(self, country: str, num_samples: int):
        # Country-specific birth certificate generation
        pass

# Example: Marriage certificate generator  
class MarriageCertificateGenerator(DatasetGeneratorInterface):
    def generate_marriage_certificate_data(self, country: str, num_samples: int):
        # Country-specific marriage certificate generation
        pass
```

### Benefits of Extension
- **Domain-specific OCR errors**: Different document types have different character confusion patterns
- **Realistic data patterns**: Each document type has its own data structure and validation rules
- **Specialized templates**: Document-specific placeholder tokens and formatting
- **Multi-language support**: Each document type can be localized for different countries/languages

This would allow the system to generate highly realistic training datasets for specific document types while maintaining the flexible language and OCR error simulation framework.
