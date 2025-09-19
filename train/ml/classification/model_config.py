"""
Configuration file for Spanish document classification models.
Contains different model options and their specifications.
"""

# Available Spanish models for document classification
SPANISH_MODELS = {
    "roberta-base-bne": {
        "name": "PlanTL-GOB-ES/roberta-base-bne",
        "description": "RoBERTa base model trained on Spanish National Library corpus",
        "size": "base",
        "recommended_for": "General Spanish text classification",
        "memory_usage": "~500MB",
        "speed": "fast"
    },
    "roberta-large-bne": {
        "name": "PlanTL-GOB-ES/roberta-large-bne", 
        "description": "RoBERTa large model trained on Spanish National Library corpus",
        "size": "large",
        "recommended_for": "High accuracy Spanish text classification",
        "memory_usage": "~1.5GB",
        "speed": "slower"
    },
    "roberta-ner": {
        "name": "BSC-LT/roberta-base-bne-capitel-ner",
        "description": "RoBERTa base model fine-tuned for Spanish NER",
        "size": "base",
        "recommended_for": "Document classification with entity recognition",
        "memory_usage": "~500MB", 
        "speed": "fast"
    },
    "roberta-biomedical": {
        "name": "BSC-LT/roberta-base-biomedical-es",
        "description": "RoBERTa base model trained on Spanish biomedical texts",
        "size": "base",
        "recommended_for": "Medical/legal document classification",
        "memory_usage": "~500MB",
        "speed": "fast"
    }
}

# Default model selection
DEFAULT_MODEL = "roberta-base-bne"

def get_model_config(model_key: str = None):
    """
    Get model configuration by key.
    
    Args:
        model_key: Key from SPANISH_MODELS dict, or None for default
        
    Returns:
        dict: Model configuration
    """
    if model_key is None:
        model_key = DEFAULT_MODEL
    
    if model_key not in SPANISH_MODELS:
        raise ValueError(f"Unknown model key: {model_key}. Available: {list(SPANISH_MODELS.keys())}")
    
    return SPANISH_MODELS[model_key]

def list_available_models():
    """List all available models with their descriptions."""
    print("Available Spanish Models for Document Classification:")
    print("=" * 60)
    
    for key, config in SPANISH_MODELS.items():
        print(f"\n{key}:")
        print(f"  Model: {config['name']}")
        print(f"  Description: {config['description']}")
        print(f"  Size: {config['size']}")
        print(f"  Recommended for: {config['recommended_for']}")
        print(f"  Memory usage: {config['memory_usage']}")
        print(f"  Speed: {config['speed']}")

if __name__ == "__main__":
    list_available_models()
