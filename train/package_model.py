#!/usr/bin/env python3
"""
Model packaging script for distribution.
This script creates a distributable model package that can be uploaded to
GitHub, HuggingFace, or other model repositories.
"""

import json
import shutil
import zipfile
from datetime import datetime
from pathlib import Path


def create_model_package(model_dir: str, output_dir: str = "dist") -> str:
    """
    Create a distributable model package.

    Args:
        model_dir: Path to the trained model directory
        output_dir: Directory to create the package in

    Returns:
        str: Path to the created package
    """
    model_path = Path(model_dir)
    output_path = Path(output_dir)
    output_path.mkdir(exist_ok=True)

    # Create package directory
    package_name = f"scanpro-model-{datetime.now().strftime('%Y%m%d-%H%M%S')}"
    package_dir = output_path / package_name
    package_dir.mkdir(exist_ok=True)

    print(f"📦 Creating model package: {package_name}")

    # Copy model files
    model_files = ["model_metadata.json", "category_embeddings.json"]

    for file_name in model_files:
        src_file = model_path / file_name
        if src_file.exists():
            dst_file = package_dir / file_name
            shutil.copy2(src_file, dst_file)
            print(f"  ✅ Copied {file_name}")
        else:
            print(f"  ❌ Missing {file_name}")

    # Create model info file
    model_info = {
        "name": "scanpro-document-classifier",
        "version": "1.0.0",
        "description": "Document classification model for ScanPro",
        "created_at": datetime.now().isoformat(),
        "files": model_files,
        "requirements": {
            "sentence_transformers": ">=2.0.0",
            "numpy": ">=1.20.0",
            "scikit-learn": ">=1.0.0",
        },
        "usage": {
            "backend_path": "SCANPRO_MODEL_PATH environment variable",
            "example": "export SCANPRO_MODEL_PATH=/path/to/model",
        },
    }

    info_file = package_dir / "model_info.json"
    with open(info_file, "w") as f:
        json.dump(model_info, f, indent=2)

    print(f"  ✅ Created model_info.json")

    # Create README
    readme_content = f"""# ScanPro Document Classification Model

## Model Information
- **Name**: {model_info['name']}
- **Version**: {model_info['version']}
- **Created**: {model_info['created_at']}

## Files
- `model_metadata.json` - Model metadata and configuration
- `category_embeddings.json` - Category embeddings for classification
- `model_info.json` - Package information

## Usage

### Backend Integration
Set the model path via environment variable:
```bash
export SCANPRO_MODEL_PATH=/path/to/model
```

### Direct Usage
```python
from src.ml.classification.model_loader import load_pretrained_classifier

classifier = load_pretrained_classifier("/path/to/model")
if classifier.is_available():
    result = classifier.classify("document text here")
    print(f"Category: {{result.category}}, Confidence: {{result.confidence}}")
```

## Requirements
- sentence-transformers >= 2.0.0
- numpy >= 1.20.0
- scikit-learn >= 1.0.0

## Categories
The model supports the following document categories:
{json.dumps(model_info.get('categories', []), indent=2)}
"""

    readme_file = package_dir / "README.md"
    with open(readme_file, "w") as f:
        f.write(readme_content)

    print(f"  ✅ Created README.md")

    # Create zip package
    zip_file = output_path / f"{package_name}.zip"
    with zipfile.ZipFile(zip_file, "w", zipfile.ZIP_DEFLATED) as zipf:
        for file_path in package_dir.rglob("*"):
            if file_path.is_file():
                arcname = file_path.relative_to(package_dir)
                zipf.write(file_path, arcname)

    print(f"📦 Package created: {zip_file}")
    print(f"📁 Package directory: {package_dir}")

    return str(zip_file)


def main():
    """Main function."""
    model_dir = "/Users/bradencurtis/MYWORKSPACE/ScanPro/train/models"
    output_dir = "/Users/bradencurtis/MYWORKSPACE/ScanPro/dist"

    package_path = create_model_package(model_dir, output_dir)
    print(f"✅ Model package ready for distribution: {package_path}")


if __name__ == "__main__":
    main()
