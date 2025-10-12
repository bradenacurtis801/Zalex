from abc import ABC, abstractmethod
from typing import List, Tuple, Dict, Any
import os
import csv
from dataclasses import dataclass


class LanguageDataGenerator(ABC):
    """Abstract base class for language-specific data generation"""
    
    def __init__(self, language: str, locale: str = None):
        self.language = language
        self.locale = locale or language
    
    @abstractmethod
    def generate_name(self) -> str:
        """Generate a name in the target language"""
        pass
    
    @abstractmethod
    def generate_sentence(self) -> str:
        """Generate a sentence in the target language"""
        pass
    
    @abstractmethod
    def generate_paragraph(self) -> str:
        """Generate a paragraph in the target language"""
        pass
    
    @abstractmethod
    def generate_word(self) -> str:
        """Generate a word in the target language"""
        pass
    
    @abstractmethod
    def generate_phone(self) -> str:
        """Generate a phone number in the target language format"""
        pass
    
    @abstractmethod
    def generate_address(self) -> str:
        """Generate an address in the target language format"""
        pass
    
    @abstractmethod
    def generate_date(self) -> str:
        """Generate a date in the target language format"""
        pass
    
    @abstractmethod
    def get_ocr_confusion_chars(self) -> Dict[str, List[str]]:
        """Get character confusion sets for OCR error simulation"""
        pass


class DatasetGeneratorInterface(ABC):
    """Abstract base class for dataset generation"""
    
    def __init__(self, language_generator: LanguageDataGenerator):
        self.language_generator = language_generator
    
    @abstractmethod
    def generate_dataset(self, templates: Dict[str, str], num_samples: int, 
                        ocr_error_rate: float, output_file: str) -> None:
        """Generate training dataset with OCR errors"""
        pass
    
    @abstractmethod
    def get_sentence_fragment(self, template: str, min_length: int = 5, 
                            max_length: int = 20) -> str:
        """Extract a random sentence fragment from template"""
        pass
    
    @abstractmethod
    def generate_template_data(self, template_path: str, doc_type: str, 
                             num_samples: int, ocr_error_rate: float, 
                             all_templates: List[str]) -> List[List[str]]:
        """Generate data for a specific template"""
        pass


class LanguageConfig:
    """Configuration class for language-specific settings"""
    
    def __init__(self, language: str, locale: str, templates_dir: str, 
                 faker_locale: str = None):
        self.language = language
        self.locale = locale
        self.templates_dir = templates_dir
        self.faker_locale = faker_locale or locale
    
    def get_template_path(self, template_name: str) -> str:
        """Get full path to template file"""
        return os.path.join(self.templates_dir, f"{template_name}.txt")
    
    def get_processed_path(self, filename: str) -> str:
        """Get path for processed text"""
        return os.path.join("..", "data", "OCRProcessed", f"{filename}.txt")
