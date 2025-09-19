import easyocr
import logging

logger = logging.getLogger(__name__)

_reader = None

def get_ocr_reader():
    global _reader
    if _reader is None:
        logger.info("Initializing EasyOCR reader...")
        logger.debug("Creating EasyOCR reader with English language support...")
 #       reader = easyocr.Reader(['es', 'en'])  # Spanish and English
        _reader = easyocr.Reader(['en'])  # Spanish and English
        logger.debug("EasyOCR reader created successfully")
        logger.info("EasyOCR reader initialized.")
    else:
        logger.debug("Using existing EasyOCR reader instance")
    return _reader