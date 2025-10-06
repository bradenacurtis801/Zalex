import easyocr
from typing import List, Tuple, Union
import os

_reader = None

def get_ocr_reader(languages: List[str], gpu: bool) -> easyocr.Reader:
    global _reader
    if _reader is None:
        _reader = easyocr.Reader(languages, gpu=gpu)
    return _reader

class OCRProcessor:
    
    def __init__(self, languages: List[str] = ['en'], gpu: bool = False) -> None:

        self.reader = get_ocr_reader(languages, gpu)
        self.languages = languages
        self.gpu = gpu

    def extract_text(self, image_path: str, detail: int = 1) -> List[Tuple]:

        if not os.path.exists(image_path):
            raise FileNotFoundError(f"Image file not found: {image_path}")
            
        results = self.reader.readtext(image_path, detail=detail)
        return results

    def extract_text_only(self, image_path: str) -> str:

        results = self.extract_text(image_path, detail=0)
        return " ".join(results)

    def batch_process(self, image_paths: List[str], detail: int = 1) -> List[List[Tuple]]:

        results = []
        for image_path in image_paths:
            if os.path.exists(image_path):
                result = self.extract_text(image_path, detail)
                results.append(result)
            else:
                print(f"Warning: Image file not found: {image_path}")
                results.append([])
        return results

    def save_text_to_file(self, image_path: str, output_path: str) -> str:
        
        # Ensure output directory exists
        os.makedirs(os.path.dirname(output_path), exist_ok=True)
        
        # Extract text
        text_content = self.extract_text_only(image_path)
        
        # Save to file
        with open(output_path, 'w+', encoding='utf-8') as f:
            f.write(text_content)
        
        return output_path
