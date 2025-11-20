"""
Tesseract OCR engine implementation.
"""

import io
import logging
from dataclasses import dataclass
from typing import List, Dict, Any, Optional, Tuple, TYPE_CHECKING

import pytesseract
from pytesseract import TesseractNotFoundError, Output
from PIL import Image

from .base import OCREngine, OCRResult, OCRWord, OCRLine, OCRBoundingBox

if TYPE_CHECKING:
    from .base import OCRFilterMetrics

logger = logging.getLogger(__name__)


@dataclass
class WordProcessingResult:
    """Result of processing a single word from OCR data."""
    confidence: float
    word_text: str
    ocr_word: OCRWord
    is_filtered: bool
    line_key: Optional[Tuple[int, int, int]]  # (block_num, par_num, line_num)


@dataclass
class WordsProcessingResult:
    """Result of processing all words from OCR data."""
    ocr_words: List[OCRWord]
    words_by_line: Dict[Tuple[int, int, int], List[OCRWord]]
    filtered_words: List[OCRWord]
    total_words_detected: int
    words_structural: int
    words_empty: int
    accepted_confidences: List[float]
    filtered_confidences: List[float]


class TesseractEngine(OCREngine):
    """Tesseract OCR engine implementation."""

    def __init__(self, languages: List[str] | str = 'spa', confidence_threshold: float = 70):
        """
        Initialize Tesseract OCR engine.
        
        Args:
            languages: List of language codes (e.g., ['eng', 'spa'])
            confidence_threshold: Minimum confidence threshold (0-100) for word acceptance.
                                 If None, uses default from config.
        """
        super().__init__(languages)
        self.confidence_threshold = confidence_threshold
        
        # Convert languages list to string format (e.g., "eng+spa") once
        if isinstance(self.languages, list):
            self.lang_string = "+".join(self.languages)
        else:
            self.lang_string = self.languages
        
        logger.debug(
            f"TesseractEngine initialized with confidence threshold: {self.confidence_threshold}, "
            f"languages: {self.lang_string}"
        )

    def initialize(self) -> None:
        """Initialize Tesseract OCR engine."""
        logger.info("Initializing Tesseract OCR engine...")

        # Set up Tesseract configuration using pre-computed lang_string
        self._tesseract_config = f"-l {self.lang_string}"

        # Test Tesseract availability
        try:
            pytesseract.get_tesseract_version()
            logger.info(
                f"Tesseract OCR initialized successfully with languages: {self.lang_string}"
            )
        except TesseractNotFoundError as e:
            logger.error(f"Tesseract OCR is not available: {e}")
            raise
        except Exception as e:
            logger.error(f"Failed to initialize Tesseract: {e}")
            raise

    def extract_text(self, image_path: str) -> OCRResult:
        """Extract text with detailed information including bounding boxes and confidence scores."""
        self._ensure_initialized()

        try:
            logger.debug(f"Extracting text with data from {image_path} using Tesseract")
            with Image.open(image_path) as img:
                data = pytesseract.image_to_data(img, lang=self.lang_string, output_type=Output.DICT)
            
            # Process the data to create OCRResult
            ocr_result = self._process_ocr_data(data)
            logger.debug(f"Successfully extracted {ocr_result.total_words} words with location data")
            return ocr_result
        except TesseractNotFoundError as e:
            logger.error(f"Tesseract OCR is not available: {e}")
            raise
        except Exception as e:
            logger.error(f"Tesseract OCR data extraction failed: {e}")
            raise

    def extract_text_from_bytes(
        self, image_bytes: bytes, image_format: str = "png"
    ) -> OCRResult:
        """Extract text with detailed information from image bytes using Tesseract."""
        self._ensure_initialized()

        try:
            # Create PIL Image from bytes (no disk I/O needed)
            img = Image.open(io.BytesIO(image_bytes))
            
            # Extract text directly from PIL Image in memory
            data = pytesseract.image_to_data(img, lang=self.lang_string, output_type=Output.DICT)
            
            # Process the data to create OCRResult
            ocr_result = self._process_ocr_data(data)
            logger.debug(f"Successfully extracted {ocr_result.total_words} words with location data from bytes")
            return ocr_result
        except TesseractNotFoundError as e:
            logger.error(f"Tesseract OCR is not available: {e}")
            raise
        except Exception as e:
            logger.error(f"Tesseract OCR data extraction from bytes failed: {e}")
            raise

    def extract_text_boxes(self, image_path: str) -> List[Dict[str, Any]]:
        """Extract text with simple bounding boxes for each character."""
        self._ensure_initialized()

        try:
            logger.debug(f"Extracting text boxes from {image_path} using Tesseract")
            with Image.open(image_path) as img:
                boxes = pytesseract.image_to_boxes(img, config=self._tesseract_config)
            
            # Parse the boxes data
            processed_boxes = self._process_boxes_data(boxes)
            logger.debug(f"Successfully extracted {len(processed_boxes)} character boxes")
            return processed_boxes
        except TesseractNotFoundError as e:
            logger.error(f"Tesseract OCR is not available: {e}")
            raise
        except Exception as e:
            logger.error(f"Tesseract OCR boxes extraction failed: {e}")
            raise

    def _process_ocr_data(self, data: Dict[str, List]) -> OCRResult:
        """Process raw OCR data into OCRResult structure."""
        from .base import OCRFilterMetrics
        
        # Process all words
        processing_result = self._process_words(data)
        
        # Create lines from grouped words
        ocr_lines = self._create_ocr_lines(processing_result.words_by_line)
        
        # Combine text from lines
        combined_text = '\n'.join([line.text for line in ocr_lines])
        
        # Calculate filter metrics
        filter_metrics = self._calculate_filter_metrics(
            processing_result,
            len(processing_result.ocr_words)
        )
        
        # Log metrics
        logger.debug(
            f"OCR Filter Metrics: {len(processing_result.ocr_words)}/{processing_result.total_words_detected} words accepted "
            f"(filtered: {len(processing_result.filtered_words)}, "
            f"structural: {processing_result.words_structural}, "
            f"empty: {processing_result.words_empty}). "
            f"Avg confidence: accepted={filter_metrics.avg_confidence_accepted:.1f}, "
            f"filtered={filter_metrics.avg_confidence_filtered:.1f}"
        )

        return OCRResult(
            text=combined_text,
            words=processing_result.ocr_words,
            lines=ocr_lines,
            total_words=len(processing_result.ocr_words),
            total_lines=len(ocr_lines),
            filter_metrics=filter_metrics
        )

    def _process_words(
        self, data: Dict[str, List]
    ) -> WordsProcessingResult:
        """
        Process all words from OCR data.
        
        Returns:
            WordsProcessingResult with all processing data
        """
        ocr_words: List[OCRWord] = []
        words_by_line: Dict[tuple, List[OCRWord]] = {}
        
        # Metrics tracking
        total_words_detected = 0
        words_structural = 0
        words_empty = 0
        filtered_words: List[OCRWord] = []
        accepted_confidences: List[float] = []
        filtered_confidences: List[float] = []

        for i in range(len(data['text'])):
            word_result = self._process_word(data, i)
            total_words_detected += 1
            
            if word_result is None:
                continue
            
            # Track special confidence values
            if word_result.confidence == -1:
                words_structural += 1
                continue
            elif word_result.confidence == 0:
                words_empty += 1
                continue
            
            # Handle filtered words
            if word_result.is_filtered:
                filtered_words.append(word_result.ocr_word)
                filtered_confidences.append(word_result.confidence)
                continue
            
            # Accepted word - add to collections
            accepted_confidences.append(word_result.confidence)
            ocr_words.append(word_result.ocr_word)
            
            # Initialize line key if needed
            if word_result.line_key not in words_by_line:
                words_by_line[word_result.line_key] = []
            words_by_line[word_result.line_key].append(word_result.ocr_word)

        return WordsProcessingResult(
            ocr_words=ocr_words,
            words_by_line=words_by_line,
            filtered_words=filtered_words,
            total_words_detected=total_words_detected,
            words_structural=words_structural,
            words_empty=words_empty,
            accepted_confidences=accepted_confidences,
            filtered_confidences=filtered_confidences,
        )

    def _process_word(
        self, data: Dict[str, List], index: int
    ) -> Optional[WordProcessingResult]:
        """
        Process a single word entry from OCR data.
        
        Args:
            data: Raw OCR data dictionary
            index: Index of the word to process
            
        Returns:
            WordProcessingResult with word processing data, or None if word should be skipped
        """
        confidence = float(data['conf'][index])
        word_text = data['text'][index].strip()
        
        # Skip empty words early
        if not word_text:
            return None
        
        # Create basic OCR word (for filtered words tracking)
        ocr_word_basic = OCRWord(
            text=word_text,
            confidence=confidence,
            bbox=OCRBoundingBox(
                left=int(data['left'][index]),
                top=int(data['top'][index]),
                width=int(data['width'][index]),
                height=int(data['height'][index])
            )
        )
        
        # Check if word is filtered by confidence threshold
        is_filtered = confidence < self.confidence_threshold
        
        # If filtered, return basic word info
        if is_filtered:
            return WordProcessingResult(
                confidence=confidence,
                word_text=word_text,
                ocr_word=ocr_word_basic,
                is_filtered=True,
                line_key=None,
            )
        
        # Create full OCR word with line metadata for accepted words
        block_num = int(data['block_num'][index])
        par_num = int(data['par_num'][index])
        line_num = int(data['line_num'][index])
        line_key = (block_num, par_num, line_num)
        
        ocr_word = self._create_ocr_word(data, index, line_key)
        
        return WordProcessingResult(
            confidence=confidence,
            word_text=word_text,
            ocr_word=ocr_word,
            is_filtered=False,
            line_key=line_key,
        )

    def _create_ocr_word(
        self, data: Dict[str, List], index: int, line_key: tuple, word_num: Optional[int] = None
    ) -> OCRWord:
        """
        Create an OCRWord object with full metadata.
        
        Args:
            data: Raw OCR data dictionary
            index: Index of the word
            line_key: Tuple of (block_num, par_num, line_num)
            word_num: Optional word number within line (calculated if not provided)
            
        Returns:
            OCRWord object with full metadata
        """
        block_num, par_num, line_num = line_key
        
        return OCRWord(
            text=data['text'][index].strip(),
            confidence=float(data['conf'][index]),
            bbox=OCRBoundingBox(
                left=int(data['left'][index]),
                top=int(data['top'][index]),
                width=int(data['width'][index]),
                height=int(data['height'][index])
            ),
            block_num=block_num,
            par_num=par_num,
            line_num=line_num,
            word_num=word_num or 0  # Will be set by caller if needed
        )

    def _create_ocr_lines(
        self, words_by_line: Dict[tuple, List[OCRWord]]
    ) -> List[OCRLine]:
        """
        Create OCRLine objects from grouped words.
        
        Args:
            words_by_line: Dictionary mapping line keys to lists of OCRWord objects
            
        Returns:
            List of OCRLine objects
        """
        ocr_lines: List[OCRLine] = []
        
        for line_key, line_words in words_by_line.items():
            if not line_words:
                continue
            
            block_num, par_num, line_num = line_key
            
            # Set word_num for each word in the line
            for word_num, word in enumerate(line_words):
                word.word_num = word_num
            
            # Calculate line properties
            line_bbox = self._calculate_bbox_from_words(line_words)
            line_text = ' '.join([word.text for word in line_words])
            line_confidence = sum([word.confidence for word in line_words]) / len(line_words)
            
            ocr_line = OCRLine(
                text=line_text,
                confidence=line_confidence,
                bbox=line_bbox,
                words=line_words,
                block_num=block_num,
                par_num=par_num,
                line_num=line_num
            )
            ocr_lines.append(ocr_line)
        
        return ocr_lines

    def _calculate_filter_metrics(
        self, processing_result: WordsProcessingResult, words_accepted: int
    ) -> "OCRFilterMetrics":
        """
        Calculate and create OCRFilterMetrics from processing results.
        
        Args:
            processing_result: WordsProcessingResult from _process_words
            words_accepted: Number of accepted words
            
        Returns:
            OCRFilterMetrics object
        """
        from .base import OCRFilterMetrics
        
        accepted_confidences = processing_result.accepted_confidences
        filtered_confidences = processing_result.filtered_confidences
        filtered_words = processing_result.filtered_words
        
        # Calculate confidence statistics
        avg_confidence_accepted = (
            sum(accepted_confidences) / len(accepted_confidences)
            if accepted_confidences else 0.0
        )
        avg_confidence_filtered = (
            sum(filtered_confidences) / len(filtered_confidences)
            if filtered_confidences else 0.0
        )
        min_confidence_accepted = (
            min(accepted_confidences) if accepted_confidences else 0.0
        )
        max_confidence_filtered = (
            max(filtered_confidences) if filtered_confidences else 0.0
        )
        
        # Get sample of filtered words (first 10 for logging/debugging)
        filtered_words_sample = [word.text for word in filtered_words[:10]]
        
        return OCRFilterMetrics(
            total_words_detected=processing_result.total_words_detected,
            words_accepted=words_accepted,
            words_filtered=len(filtered_words),
            words_structural=processing_result.words_structural,
            words_empty=processing_result.words_empty,
            confidence_threshold=self.confidence_threshold,
            avg_confidence_accepted=avg_confidence_accepted,
            avg_confidence_filtered=avg_confidence_filtered,
            min_confidence_accepted=min_confidence_accepted,
            max_confidence_filtered=max_confidence_filtered,
            filtered_words_sample=filtered_words_sample
        )

    def _process_boxes_data(self, boxes: str) -> List[Dict[str, Any]]:
        """Process raw boxes data into a more usable format."""
        processed_boxes = []
        
        for line in boxes.split('\n'):
            if line.strip():
                parts = line.split()
                if len(parts) >= 6:
                    char_data = {
                        'character': parts[0],
                        'left': int(parts[1]),
                        'top': int(parts[2]),
                        'right': int(parts[3]),
                        'bottom': int(parts[4]),
                        'page_num': int(parts[5]) if len(parts) > 5 else 0
                    }
                    processed_boxes.append(char_data)
        
        return processed_boxes

    def _calculate_bbox_from_words(self, words: List[OCRWord]) -> OCRBoundingBox:
        """Calculate bounding box that encompasses all given words."""
        if not words:
            return OCRBoundingBox(left=0, top=0, width=0, height=0)
        
        left = min(word.bbox.left for word in words)
        top = min(word.bbox.top for word in words)
        right = max(word.bbox.left + word.bbox.width for word in words)
        bottom = max(word.bbox.top + word.bbox.height for word in words)
        
        return OCRBoundingBox(
            left=left,
            top=top,
            width=right - left,
            height=bottom - top
        )

    def get_supported_languages(self) -> List[str]:
        """Get list of supported language codes for Tesseract."""
        try:
            # Get available languages from Tesseract
            available_langs = pytesseract.get_languages()
            logger.debug(f"Tesseract available languages: {available_langs}")
            return available_langs
        except TesseractNotFoundError as e:
            logger.warning(f"Tesseract OCR is not available: {e}")
            raise
        except Exception as e:
            logger.warning(f"Could not get Tesseract languages: {e}")
            raise
