"""
Dataset Generation Package

This package provides a language-agnostic interface for generating training datasets
with OCR error simulation. It supports multiple languages and is easily extensible.

Usage:
    from dataset_gen import DatasetGeneratorFactory
    
    # Create English implementation
    en_data_gen, en_dataset_gen = DatasetGeneratorFactory.create('en')
    
    # Generate dataset
    en_dataset_gen.generate_dataset(templates, 1000, 0.05, 'output.csv')
"""

from .factory import DatasetGeneratorFactory, LanguageManager
from .interfaces import LanguageDataGenerator, DatasetGeneratorInterface, LanguageConfig

# Convenience imports
from .factory import create_implementation, get_supported_languages, is_language_supported

__all__ = [
    'DatasetGeneratorFactory',
    'LanguageManager', 
    'LanguageDataGenerator',
    'DatasetGeneratorInterface',
    'LanguageConfig',
    'create_implementation',
    'get_supported_languages',
    'is_language_supported'
]

__version__ = "1.0.0"
