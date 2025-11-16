"""
EasyOCR engine implementation.
"""

import logging
import os
import tempfile
from typing import List

import easyocr
from PIL import Image

# Compatibility fix for Pillow 10.0.0+ where Image.ANTIALIAS was removed
# EasyOCR internally uses Image.ANTIALIAS, so we need to provide it
if not hasattr(Image, 'ANTIALIAS'):
    # Map ANTIALIAS to LANCZOS (the equivalent resampling filter)
    if hasattr(Image, 'Resampling'):
        # Pillow 10.0.0+
        Image.ANTIALIAS = Image.Resampling.LANCZOS
    else:
        # Older Pillow versions
        Image.ANTIALIAS = Image.LANCZOS

from .base import OCREngine, OCRResult, OCRWord, OCRLine, OCRBoundingBox

logger = logging.getLogger(__name__)


class EasyOCREngine(OCREngine):
    """EasyOCR engine implementation."""

    def __init__(self, languages: List[str] = None):
        super().__init__(languages)
        self._reader = None

    def initialize(self) -> None:
        """Initialize EasyOCR engine."""
        logger.info("Initializing EasyOCR engine...")

        try:
            # Convert language codes to EasyOCR format
            easyocr_langs = []
            for lang in self.languages:
                if lang == "eng":
                    easyocr_langs.append("en")
                elif lang == "spa":
                    easyocr_langs.append("es")
                else:
                    # Map other languages as needed
                    easyocr_langs.append(lang)

            logger.debug(f"Creating EasyOCR reader with languages: {easyocr_langs}")
            self._reader = easyocr.Reader(easyocr_langs)
            logger.info("EasyOCR engine initialized successfully")
        except Exception as e:
            logger.error(f"Failed to initialize EasyOCR: {e}")
            raise

    def extract_text(self, image_path: str) -> OCRResult:
        """Extract text from an image file using EasyOCR."""
        self._ensure_initialized()

        try:
            logger.debug(f"Extracting text from {image_path} using EasyOCR")
            # Use detail=1 to get bounding boxes and confidence scores
            results = self._reader.readtext(image_path, detail=1, paragraph=False)
            
            # Process EasyOCR results into OCRResult structure
            ocr_result = self._process_easyocr_results(results)
            logger.debug(f"Successfully extracted {ocr_result.total_words} words with location data")
            return ocr_result
        except Exception as e:
            logger.error(f"EasyOCR extraction failed: {e}")
            return OCRResult(text="", words=[], lines=[], total_words=0, total_lines=0)

    def extract_text_from_bytes(
        self, image_bytes: bytes, image_format: str = "png"
    ) -> OCRResult:
        """Extract text from image bytes using EasyOCR."""
        self._ensure_initialized()

        try:
            # Create temporary file for EasyOCR
            with tempfile.NamedTemporaryFile(
                suffix=f".{image_format}", delete=False
            ) as temp_file:
                temp_file.write(image_bytes)
                temp_path = temp_file.name

            # Extract text
            ocr_result = self.extract_text(temp_path)

            # Clean up temp file
            os.unlink(temp_path)

            return ocr_result
        except Exception as e:
            logger.error(f"EasyOCR extraction from bytes failed: {e}")
            return OCRResult(text="", words=[], lines=[], total_words=0, total_lines=0)

    def _process_easyocr_results(self, results: List) -> OCRResult:
        """
        Process EasyOCR results into OCRResult structure.
        
        EasyOCR returns: List of tuples [(bbox, text, confidence), ...]
        where bbox is [[x1, y1], [x2, y2], [x3, y3], [x4, y4]]
        """
        ocr_words: List[OCRWord] = []
        ocr_lines: List[OCRLine] = []
        
        # EasyOCR doesn't provide block/par/line numbers, so we'll treat each detection as a line
        # and assign sequential numbers
        line_num = 0
        
        for result in results:
            if len(result) >= 3:
                bbox_coords, text, confidence = result[0], result[1], result[2]
                
                if not text or not text.strip():
                    continue
                
                # Convert EasyOCR bbox format to our format
                # EasyOCR: [[x1, y1], [x2, y2], [x3, y3], [x4, y4]]
                # We need: left, top, width, height
                if len(bbox_coords) >= 4:
                    x_coords = [point[0] for point in bbox_coords]
                    y_coords = [point[1] for point in bbox_coords]
                    
                    left = int(min(x_coords))
                    top = int(min(y_coords))
                    right = int(max(x_coords))
                    bottom = int(max(y_coords))
                    
                    bbox = OCRBoundingBox(
                        left=left,
                        top=top,
                        width=right - left,
                        height=bottom - top
                    )
                    
                    # Convert confidence from 0-1 to 0-100 scale (matching Tesseract)
                    confidence_100 = float(confidence) * 100.0 if confidence <= 1.0 else float(confidence)
                    
                    # Split text into words (simple whitespace split)
                    words_in_text = text.strip().split()
                    line_words: List[OCRWord] = []
                    
                    for word_num, word_text in enumerate(words_in_text):
                        ocr_word = OCRWord(
                            text=word_text,
                            confidence=confidence_100,
                            bbox=bbox,  # Same bbox for all words in this detection
                            block_num=0,  # EasyOCR doesn't provide block info
                            par_num=0,    # EasyOCR doesn't provide paragraph info
                            line_num=line_num,
                            word_num=word_num
                        )
                        ocr_words.append(ocr_word)
                        line_words.append(ocr_word)
                    
                    # Create line from this detection
                    ocr_line = OCRLine(
                        text=text.strip(),
                        confidence=confidence_100,
                        bbox=bbox,
                        words=line_words,
                        block_num=0,  # EasyOCR doesn't provide block info
                        par_num=0,    # EasyOCR doesn't provide paragraph info
                        line_num=line_num
                    )
                    ocr_lines.append(ocr_line)
                    line_num += 1
        
        # Combine all text
        combined_text = ' '.join([word.text for word in ocr_words])
        
        return OCRResult(
            text=combined_text,
            words=ocr_words,
            lines=ocr_lines,
            total_words=len(ocr_words),
            total_lines=len(ocr_lines)
        )

    def get_supported_languages(self) -> List[str]:
        """Get list of supported language codes for EasyOCR."""
        # EasyOCR supports many languages, return common ones
        return [
            "eng",
            "spa",
            "fra",
            "deu",
            "ita",
            "por",
            "rus",
            "jpn",
            "kor",
            "chi_sim",
            "chi_tra",
        ]
