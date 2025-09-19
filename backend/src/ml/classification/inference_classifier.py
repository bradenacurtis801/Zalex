"""
Inference-only document classifier for the FastAPI server.
This module provides a lightweight interface to use pre-trained models
without the training dependencies.
"""

import os
import torch
from transformers import AutoTokenizer, AutoModelForSequenceClassification
from typing import Tuple, Optional
import logging

logger = logging.getLogger(__name__)

class DocumentClassifier:
    """
    Lightweight document classifier for inference only.
    Loads pre-trained models and provides classification functionality.
    """
    
    def __init__(self, model_path: str):
        """
        Initialize the classifier with a pre-trained model.
        
        Args:
            model_path: Path to the trained model directory
        """
        self.model_path = model_path
        self.device = "cuda" if torch.cuda.is_available() else "cpu"
        self.model = None
        self.tokenizer = None
        self._load_model()
    
    def _load_model(self):
        """Load the pre-trained model and tokenizer."""
        try:
            if not os.path.exists(self.model_path):
                logger.warning(f"Model path {self.model_path} does not exist")
                return
                
            logger.info(f"Loading model from {self.model_path}")
            self.tokenizer = AutoTokenizer.from_pretrained(self.model_path)
            self.model = AutoModelForSequenceClassification.from_pretrained(self.model_path).to(self.device)
            self.model.eval()
            logger.info(f"Model loaded successfully on {self.device}")
            
        except Exception as e:
            logger.error(f"Failed to load model: {e}")
            self.model = None
            self.tokenizer = None
    
    def is_available(self) -> bool:
        """Check if the model is loaded and available for inference."""
        return self.model is not None and self.tokenizer is not None
    
    def classify(self, text: str) -> Tuple[Optional[str], float]:
        """
        Classify a document based on its text content.
        
        Args:
            text: The text content of the document to classify
            
        Returns:
            Tuple of (predicted_class, confidence_score) or (None, 0.0) if unavailable
        """
        if not self.is_available():
            logger.warning("Model not available for classification")
            return None, 0.0
        
        try:
            # Tokenize the input text
            inputs = self.tokenizer(
                text, 
                return_tensors="pt", 
                truncation=True, 
                padding=True, 
                max_length=512
            )
            inputs = {k: v.to(self.device) for k, v in inputs.items()}
            
            # Get model prediction
            with torch.no_grad():
                outputs = self.model(**inputs)
            
            # Get probabilities using softmax
            logits = outputs.logits
            probabilities = torch.nn.functional.softmax(logits, dim=-1)[0]
            
            # Get the highest probability prediction
            predicted_class_id = torch.argmax(probabilities).item()
            predicted_class_name = self.model.config.id2label[predicted_class_id]
            confidence = probabilities[predicted_class_id].item()
            
            return predicted_class_name, confidence
            
        except Exception as e:
            logger.error(f"Classification failed: {e}")
            return None, 0.0
    
    def classify_file(self, file_path: str) -> Tuple[Optional[str], float]:
        """
        Classify a document from a file path.
        
        Args:
            file_path: Path to the text file to classify
            
        Returns:
            Tuple of (predicted_class, confidence_score) or (None, 0.0) if unavailable
        """
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                text = f.read()
            return self.classify(text)
        except FileNotFoundError:
            logger.error(f"File not found: {file_path}")
            return None, 0.0
        except Exception as e:
            logger.error(f"Error reading file {file_path}: {e}")
            return None, 0.0
