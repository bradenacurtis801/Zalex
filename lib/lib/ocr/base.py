"""
Base OCR engine interface and types.
"""

from abc import ABC, abstractmethod
from dataclasses import dataclass, field, asdict
from enum import Enum
from typing import List, Optional, Dict, Any


class OCREngineType(Enum):
    """Available OCR engine types."""

    TESSERACT = "tesseract"
    EASYOCR = "easyocr"


@dataclass
class OCRBoundingBox:
    """Bounding box coordinates for OCR text elements."""
    left: int
    top: int
    width: int
    height: int


@dataclass
class OCRWord:
    """Represents a single word from OCR."""
    text: str
    confidence: float  # 0-100 scale
    bbox: OCRBoundingBox
    block_num: int = 0
    par_num: int = 0
    line_num: int = 0
    word_num: int = 0

    def to_dict(self) -> Dict[str, Any]:
        """Convert OCRWord to dictionary format."""
        return {
            'text': self.text,
            'confidence': int(self.confidence),  # Convert to int as expected by schema
            'bbox': {
                'left': self.bbox.left,
                'top': self.bbox.top,
                'width': self.bbox.width,
                'height': self.bbox.height
            },
            'block_num': self.block_num,
            'par_num': self.par_num,
            'line_num': self.line_num,
            'word_num': self.word_num
        }


@dataclass
class OCRLine:
    """Represents a line of text from OCR."""
    text: str
    confidence: float  # Average confidence of words in line
    bbox: OCRBoundingBox
    words: List[OCRWord]
    block_num: int = 0
    par_num: int = 0
    line_num: int = 0

    def to_dict(self) -> Dict[str, Any]:
        """Convert OCRLine to dictionary format."""
        return {
            'text': self.text,
            'confidence': float(self.confidence),
            'bbox': {
                'left': self.bbox.left,
                'top': self.bbox.top,
                'width': self.bbox.width,
                'height': self.bbox.height
            },
            'words': [word.to_dict() for word in self.words],
            'block_num': self.block_num,
            'par_num': self.par_num,
            'line_num': self.line_num
        }


@dataclass
class OCRFilterMetrics:
    """Metrics about filtered OCR data."""
    total_words_detected: int = 0  # Total words detected by Tesseract
    words_accepted: int = 0  # Words that passed confidence threshold
    words_filtered: int = 0  # Words filtered out (below threshold)
    words_structural: int = 0  # Words with -1 confidence (structural elements)
    words_empty: int = 0  # Words with 0 confidence (empty text)
    confidence_threshold: float = 0.0  # Threshold used for filtering
    avg_confidence_accepted: float = 0.0  # Average confidence of accepted words
    avg_confidence_filtered: float = 0.0  # Average confidence of filtered words
    min_confidence_accepted: float = 0.0  # Minimum confidence of accepted words
    max_confidence_filtered: float = 0.0  # Maximum confidence of filtered words
    filtered_words_sample: List[str] = field(default_factory=list)  # Sample of filtered words (first 10)
    
    def to_dict(self) -> Dict:
        """Convert metrics to dictionary."""
        return asdict(self)


@dataclass
class OCRResult:
    """Structured OCR result with text, words, lines, and metadata."""
    text: str  # Combined text from all words
    words: List[OCRWord]
    lines: List[OCRLine]
    total_words: int
    total_lines: int
    filter_metrics: Optional[OCRFilterMetrics] = None  # Optional filtering metrics

    def to_dict(self) -> Dict[str, Any]:
        """Convert OCRResult to dictionary format for JSON storage."""
        result = {
            'words': [word.to_dict() for word in self.words],
            'lines': [line.to_dict() for line in self.lines]
        }
        if self.filter_metrics:
            result['filter_metrics'] = self.filter_metrics.to_dict()
        return result
    
    def words_to_dict(self) -> List[Dict[str, Any]]:
        """Convert words list to dictionary format."""
        return [word.to_dict() for word in self.words]
    
    def lines_to_dict(self) -> List[Dict[str, Any]]:
        """Convert lines list to dictionary format."""
        return [line.to_dict() for line in self.lines]


class OCREngine(ABC):
    """Abstract base class for OCR engines."""

    def __init__(self, languages: List[str] = None):
        """
        Initialize the OCR engine.

        Args:
            languages: List of language codes (e.g., ['eng', 'spa'])
        """
        self.languages = languages or ["eng"]
        self._initialized = False

    @abstractmethod
    def initialize(self) -> None:
        """Initialize the OCR engine. Called once before first use."""
        pass

    @abstractmethod
    def extract_text(self, image_path: str) -> OCRResult:
        """
        Extract text from an image file.

        Args:
            image_path: Path to the image file

        Returns:
            OCRResult with structured text data
        """
        pass

    @abstractmethod
    def extract_text_from_bytes(
        self, image_bytes: bytes, image_format: str = "png"
    ) -> OCRResult:
        """
        Extract text from image bytes.

        Args:
            image_bytes: Raw image data
            image_format: Image format (png, jpg, etc.)

        Returns:
            OCRResult with structured text data
        """
        pass

    @abstractmethod
    def get_supported_languages(self) -> List[str]:
        """
        Get list of supported language codes.

        Returns:
            List of supported language codes
        """
        pass

    @property
    def is_initialized(self) -> bool:
        """Check if the engine is initialized."""
        return self._initialized

    def _ensure_initialized(self) -> None:
        """Ensure the engine is initialized before use."""
        if not self._initialized:
            self.initialize()
            self._initialized = True
