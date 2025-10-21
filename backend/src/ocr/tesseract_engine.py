"""
Tesseract OCR engine implementation.
"""

import logging
import os
import tempfile
from typing import List, Dict, Any, Optional, Tuple

import pytesseract
from pytesseract import TesseractNotFoundError, Output
from PIL import Image

from .base import OCREngine

logger = logging.getLogger(__name__)


class TesseractEngine(OCREngine):
    """Tesseract OCR engine implementation."""

    def __init__(self, languages: List[str] = None):
        super().__init__(languages)
        self._tesseract_config = None

    def initialize(self) -> None:
        """Initialize Tesseract OCR engine."""
        logger.info("Initializing Tesseract OCR engine...")

        # Set up Tesseract configuration
        lang_string = "+".join(self.languages)
        self._tesseract_config = f"--oem 3 --psm 6 -l {lang_string}"

        # Test Tesseract availability
        try:
            pytesseract.get_tesseract_version()
            logger.info(
                f"Tesseract OCR initialized successfully with languages: {lang_string}"
            )
        except TesseractNotFoundError as e:
            logger.error(f"Tesseract OCR is not available: {e}")
            raise
        except Exception as e:
            logger.error(f"Failed to initialize Tesseract: {e}")
            raise

    def extract_text(self, image_path: str) -> Dict[str, Any]:
        """Extract text with detailed information including bounding boxes and confidence scores."""
        self._ensure_initialized()

        try:
            logger.debug(f"Extracting text with data from {image_path} using Tesseract")
            with Image.open(image_path) as img:
                data = pytesseract.image_to_data(img, config=self._tesseract_config, output_type=Output.DICT)
            
            # Process the data to create a more usable format
            processed_data = self._process_ocr_data(data)
            logger.debug(f"Successfully extracted {len(processed_data['words'])} words with location data")
            return processed_data
        except TesseractNotFoundError as e:
            logger.error(f"Tesseract OCR is not available: {e}")
            raise
        except Exception as e:
            logger.error(f"Tesseract OCR data extraction failed: {e}")
            raise

    def extract_text_from_bytes(
        self, image_bytes: bytes, image_format: str = "png"
    ) -> Dict[str, Any]:
        """Extract text with detailed information from image bytes using Tesseract."""
        self._ensure_initialized()

        try:
            # Create temporary file for Tesseract
            with tempfile.NamedTemporaryFile(
                suffix=f".{image_format}", delete=False
            ) as temp_file:
                temp_file.write(image_bytes)
                temp_path = temp_file.name

            # Extract text with data
            data = self.extract_text(temp_path)

            # Clean up temp file
            os.unlink(temp_path)

            return data
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

    def _process_ocr_data(self, data: Dict[str, List]) -> Dict[str, Any]:
        """Process raw OCR data into a more usable format."""
        words = []
        lines = []
        paragraphs = []
        blocks = []

        # Group data by hierarchy
        current_line = None
        current_paragraph = None
        current_block = None

        for i in range(len(data['text'])):
            if int(data['conf'][i]) > 0:  # Only process words with confidence > 0
                word_data = {
                    'text': data['text'][i].strip(),
                    'confidence': int(data['conf'][i]),
                    'bbox': {
                        'left': int(data['left'][i]),
                        'top': int(data['top'][i]),
                        'width': int(data['width'][i]),
                        'height': int(data['height'][i])
                    },
                    'block_num': int(data['block_num'][i]),
                    'par_num': int(data['par_num'][i]),
                    'line_num': int(data['line_num'][i]),
                    'word_num': int(data['word_num'][i])
                }
                
                if word_data['text']:  # Only add non-empty words
                    words.append(word_data)

        # Group words into lines, paragraphs, and blocks
        words_by_line = {}
        for word in words:
            line_key = (word['block_num'], word['par_num'], word['line_num'])
            if line_key not in words_by_line:
                words_by_line[line_key] = []
            words_by_line[line_key].append(word)

        # Create line data
        for line_key, line_words in words_by_line.items():
            if line_words:
                line_bbox = self._calculate_bbox([word['bbox'] for word in line_words])
                line_text = ' '.join([word['text'] for word in line_words])
                line_confidence = sum([word['confidence'] for word in line_words]) / len(line_words)
                
                line_data = {
                    'text': line_text,
                    'confidence': line_confidence,
                    'bbox': line_bbox,
                    'words': line_words,
                    'block_num': line_words[0]['block_num'],
                    'par_num': line_words[0]['par_num'],
                    'line_num': line_words[0]['line_num']
                }
                lines.append(line_data)

        return {
            'words': words,
            'lines': lines,
            'text': ' '.join([word['text'] for word in words]),
            'total_words': len(words),
            'total_lines': len(lines)
        }

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

    def _calculate_bbox(self, bboxes: List[Dict[str, int]]) -> Dict[str, int]:
        """Calculate bounding box that encompasses all given bboxes."""
        if not bboxes:
            return {'left': 0, 'top': 0, 'width': 0, 'height': 0}
        
        left = min(bbox['left'] for bbox in bboxes)
        top = min(bbox['top'] for bbox in bboxes)
        right = max(bbox['left'] + bbox['width'] for bbox in bboxes)
        bottom = max(bbox['top'] + bbox['height'] for bbox in bboxes)
        
        return {
            'left': left,
            'top': top,
            'width': right - left,
            'height': bottom - top
        }

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
