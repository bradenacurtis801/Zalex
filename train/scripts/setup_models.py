#!/usr/bin/env python3
"""
Model setup script for ScanPro.
This script handles model downloads and setup for different environments.
"""

import os
import sys
from pathlib import Path
import logging

# Add the backend directory to the Python path
sys.path.append(str(Path(__file__).parent.parent))

from config import ML_MODELS_DIR, CLASSIFICATION_MODEL_DIR, NER_MODEL_DIR

logger = logging.getLogger(__name__)

class ModelSetup:
    """Handles model setup and configuration."""
    
    def __init__(self):
        self.model_configs = {
            "spanish_classifier": {
                "description": "Spanish document classifier model",
                "files": [
                    "config.json",
                    "model.safetensors",
                    "tokenizer_config.json", 
                    "vocab.json",
                    "merges.txt",
                    "special_tokens_map.json",
                    "training_args.bin"
                ],
                "source": "local",  # or "huggingface", "s3", etc.
                "path": "backend/test_data/es/spanish_doc_classifier_model/"
            },
            "checkpoint_model": {
                "description": "Fine-tuned checkpoint model",
                "files": [
                    "config.json",
                    "model.safetensors",
                    "optimizer.pt",
                    "rng_state.pth",
                    "scheduler.pt", 
                    "trainer_state.json",
                    "training_args.bin"
                ],
                "source": "local",
                "path": "results/checkpoint-9/"
            }
        }
    
    def setup_models(self):
        """Set up all required models."""
        logger.info("Setting up ML models...")
        
        for model_name, config in self.model_configs.items():
            self._setup_model(model_name, config)
    
    def _setup_model(self, model_name: str, config: dict):
        """Set up a specific model."""
        logger.info(f"Setting up {model_name}: {config['description']}")
        
        if config["source"] == "local":
            self._copy_local_model(model_name, config)
        else:
            logger.warning(f"Model source '{config['source']}' not implemented yet")
    
    def _copy_local_model(self, model_name: str, config: dict):
        """Copy model from local source to target directory."""
        source_path = Path(config["path"])
        target_dir = ML_MODELS_DIR / model_name
        
        if not source_path.exists():
            logger.warning(f"Source path {source_path} does not exist")
            return
        
        target_dir.mkdir(parents=True, exist_ok=True)
        
        copied_files = 0
        for filename in config["files"]:
            source_file = source_path / filename
            target_file = target_dir / filename
            
            if source_file.exists():
                import shutil
                shutil.copy2(source_file, target_file)
                copied_files += 1
                logger.info(f"Copied {filename}")
            else:
                logger.warning(f"File {filename} not found in source")
        
        logger.info(f"Copied {copied_files}/{len(config['files'])} files for {model_name}")

def main():
    """Main function."""
    logging.basicConfig(level=logging.INFO)
    
    setup = ModelSetup()
    setup.setup_models()

if __name__ == "__main__":
    main()
