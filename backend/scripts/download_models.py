#!/usr/bin/env python3
"""
Model download and management script for ScanPro.
Downloads required ML models to the appropriate directories.
"""

import os
import sys
import requests
import zipfile
import shutil
from pathlib import Path
from typing import Dict, List, Optional
import logging

# Add the backend directory to the Python path
sys.path.append(str(Path(__file__).parent.parent))

from config import ML_MODELS_DIR, CLASSIFICATION_MODEL_DIR, NER_MODEL_DIR

logger = logging.getLogger(__name__)

class ModelManager:
    """Manages downloading and organizing ML models."""
    
    def __init__(self):
        self.models_config = {
            "spanish_classifier": {
                "url": "https://huggingface.co/your-username/spanish-doc-classifier/resolve/main/",
                "files": [
                    "config.json",
                    "model.safetensors", 
                    "tokenizer_config.json",
                    "vocab.json",
                    "merges.txt",
                    "special_tokens_map.json",
                    "training_args.bin"
                ],
                "target_dir": ML_MODELS_DIR / "spanish_doc_classifier_model"
            },
            "checkpoint_model": {
                "url": "https://your-model-storage.com/checkpoint-9/",
                "files": [
                    "config.json",
                    "model.safetensors",
                    "optimizer.pt",
                    "rng_state.pth", 
                    "scheduler.pt",
                    "trainer_state.json",
                    "training_args.bin"
                ],
                "target_dir": ML_MODELS_DIR / "checkpoint-9"
            }
        }
    
    def download_file(self, url: str, target_path: Path) -> bool:
        """Download a single file from URL to target path."""
        try:
            logger.info(f"Downloading {url} to {target_path}")
            response = requests.get(url, stream=True)
            response.raise_for_status()
            
            target_path.parent.mkdir(parents=True, exist_ok=True)
            
            with open(target_path, 'wb') as f:
                for chunk in response.iter_content(chunk_size=8192):
                    f.write(chunk)
            
            logger.info(f"Successfully downloaded {target_path.name}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to download {url}: {e}")
            return False
    
    def download_model(self, model_name: str) -> bool:
        """Download all files for a specific model."""
        if model_name not in self.models_config:
            logger.error(f"Unknown model: {model_name}")
            return False
        
        config = self.models_config[model_name]
        target_dir = config["target_dir"]
        base_url = config["url"]
        
        logger.info(f"Downloading model: {model_name}")
        logger.info(f"Target directory: {target_dir}")
        
        success_count = 0
        total_files = len(config["files"])
        
        for filename in config["files"]:
            url = f"{base_url}{filename}"
            target_path = target_dir / filename
            
            if self.download_file(url, target_path):
                success_count += 1
        
        if success_count == total_files:
            logger.info(f"Successfully downloaded all files for {model_name}")
            return True
        else:
            logger.warning(f"Downloaded {success_count}/{total_files} files for {model_name}")
            return False
    
    def download_all_models(self) -> bool:
        """Download all configured models."""
        logger.info("Starting download of all models...")
        
        all_success = True
        for model_name in self.models_config.keys():
            if not self.download_model(model_name):
                all_success = False
        
        if all_success:
            logger.info("All models downloaded successfully!")
        else:
            logger.warning("Some models failed to download. Check logs for details.")
        
        return all_success
    
    def list_available_models(self) -> List[str]:
        """List all available model names."""
        return list(self.models_config.keys())
    
    def check_model_exists(self, model_name: str) -> bool:
        """Check if a model is already downloaded."""
        if model_name not in self.models_config:
            return False
        
        config = self.models_config[model_name]
        target_dir = config["target_dir"]
        
        # Check if all required files exist
        for filename in config["files"]:
            if not (target_dir / filename).exists():
                return False
        
        return True

def main():
    """Main function for command-line usage."""
    import argparse
    
    parser = argparse.ArgumentParser(description="Download ML models for ScanPro")
    parser.add_argument("--model", "-m", help="Specific model to download")
    parser.add_argument("--all", "-a", action="store_true", help="Download all models")
    parser.add_argument("--list", "-l", action="store_true", help="List available models")
    parser.add_argument("--check", "-c", help="Check if model exists")
    
    args = parser.parse_args()
    
    # Set up logging
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    manager = ModelManager()
    
    if args.list:
        models = manager.list_available_models()
        print("Available models:")
        for model in models:
            status = "✓" if manager.check_model_exists(model) else "✗"
            print(f"  {status} {model}")
    
    elif args.check:
        exists = manager.check_model_exists(args.check)
        print(f"Model '{args.check}': {'✓ Exists' if exists else '✗ Missing'}")
    
    elif args.model:
        success = manager.download_model(args.model)
        sys.exit(0 if success else 1)
    
    elif args.all:
        success = manager.download_all_models()
        sys.exit(0 if success else 1)
    
    else:
        parser.print_help()

if __name__ == "__main__":
    main()
