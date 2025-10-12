"""
Factory classes for creating language-specific dataset generators.
"""

from typing import Dict, Tuple, Any
from .interfaces import LanguageDataGenerator, DatasetGeneratorInterface
from . import impl


class DatasetGeneratorFactory:
    """Main factory class for creating language-specific implementations"""
    
    _implementations: Dict[str, callable] = {
        'en': impl.en.DatasetGenerator(),
        'english': impl.en.DatasetGenerator(),
        'es': impl.es.DatasetGenerator(),
        'spanish': impl.es.DatasetGenerator(),
    }
    
    @classmethod
    def get_supported_languages(cls) -> list:
        """Get list of supported languages"""
        return list(cls._implementations.keys())
    
    @classmethod
    def create(cls, language: str) -> DatasetGeneratorInterface:
        """
        Create language-specific implementation components
        
        Args:
            language: Language code or name (e.g., 'en', 'english', 'es', 'spanish')
            
        Returns:
            DatasetGenerator instance with access to language_generator
            
        Raises:
            ValueError: If language is not supported
        """
        language = language.lower()
        
        if language not in cls._implementations:
            supported = ', '.join(cls.get_supported_languages())
            raise ValueError(f"Language '{language}' not supported. Supported languages: {supported}")
        
        return cls._implementations[language]
    
    @classmethod
    def register_language(cls, language: str, language_code: str):
        """
        Register a new language implementation
        
        Args:
            language: Language name (e.g., 'french')
            language_code: Language code (e.g., 'fr')
        """
        impl_module = getattr(impl, language_code)
        cls._implementations[language.lower()] = impl_module.DatasetGenerator()
    
    @classmethod
    def is_supported(cls, language: str) -> bool:
        """Check if a language is supported"""
        return language.lower() in cls._implementations
    
    @classmethod
    def create_data_generator(cls, language: str) -> LanguageDataGenerator:
        """Create only the data generator for a language"""
        return cls.create(language).language_generator
    
    @classmethod
    def create_dataset_generator(cls, language: str) -> DatasetGeneratorInterface:
        """Create only the dataset generator for a language"""
        return cls.create(language)


class LanguageManager:
    """Manager class for handling multiple language implementations with caching"""
    
    def __init__(self):
        self._implementations: Dict[str, DatasetGeneratorInterface] = {}
    
    def get_implementation(self, language: str) -> DatasetGeneratorInterface:
        """
        Get or create implementation for a language (cached)
        
        Args:
            language: Language code or name
            
        Returns:
            DatasetGenerator instance with access to language_generator
        """
        language = language.lower()
        
        if language not in self._implementations:
            self._implementations[language] = DatasetGeneratorFactory.create(language)
        
        return self._implementations[language]
    
    def get_data_generator(self, language: str) -> LanguageDataGenerator:
        """Get data generator for a language (cached)"""
        return self.get_implementation(language).language_generator
    
    def get_dataset_generator(self, language: str) -> DatasetGeneratorInterface:
        """Get dataset generator for a language (cached)"""
        return self.get_implementation(language)
    
    def clear_cache(self):
        """Clear cached implementations"""
        self._implementations.clear()
    
    def get_loaded_languages(self) -> list:
        """Get list of currently loaded languages"""
        return list(self._implementations.keys())
    
    def preload_language(self, language: str):
        """Preload a language implementation into cache"""
        self.get_implementation(language)
    
    def preload_all_languages(self):
        """Preload all supported languages into cache"""
        for lang in DatasetGeneratorFactory.get_supported_languages():
            self.preload_language(lang)


# Convenience functions
def create_implementation(language: str) -> Tuple[LanguageDataGenerator, DatasetGeneratorInterface]:
    """Convenience function to create language implementation"""
    return DatasetGeneratorFactory.create(language)


def get_supported_languages() -> list:
    """Convenience function to get supported languages"""
    return DatasetGeneratorFactory.get_supported_languages()


def is_language_supported(language: str) -> bool:
    """Convenience function to check if language is supported"""
    return DatasetGeneratorFactory.is_supported(language)


def create_data_generator(language: str) -> LanguageDataGenerator:
    """Convenience function to create only data generator"""
    return DatasetGeneratorFactory.create_data_generator(language)


def create_dataset_generator(language: str) -> DatasetGeneratorInterface:
    """Convenience function to create only dataset generator"""
    return DatasetGeneratorFactory.create_dataset_generator(language)
