"""
Models for classifier training data.
"""

from pathlib import Path
from typing import List, Dict, Optional, Any, TYPE_CHECKING
from pydantic import BaseModel, Field, field_validator, model_validator, ConfigDict
import json

if TYPE_CHECKING:
    from sklearn.feature_extraction.text import TfidfVectorizer
    from scanpro_lib.utils.training_utils import MetricsTracker


class Page(BaseModel):
    """Represents a single page of a document."""
    page_number: int
    text: str


class DocumentData(BaseModel):
    """Represents a document with its pages."""
    num_pages: int
    file_name: str
    file_hash: str
    pages: List[Page]


class TrainingData(BaseModel):
    """Represents training data organized by categories."""
    categories: List[str]
    category_data: Dict[str, List[DocumentData]]
    num_documents: int
    timestamp: str

    def trim_pages(self, max_pages: int | None = None) -> 'TrainingData':
        """
        Trim the pages of the training data to the specified maximum number of pages.
        
        Args:
            max_pages: Maximum number of pages to keep per document
        
        Returns:
            Self (modified in place)
        """
        if not max_pages:
            return self
            
        for category in self.categories:
            for doc_data in self.category_data[category]:
                # Trim pages and update num_pages
                doc_data.pages = doc_data.pages[:max_pages]
                doc_data.num_pages = len(doc_data.pages)
        return self
    
    def extract_texts(self, max_pages: int | None = None) -> List[str]:
        """
        Extract text strings from TrainingData for model training.
        Combines page texts for each document, optionally limiting to first n pages.
        
        Args:
            max_pages: Maximum number of pages to extract per document. If None, extracts all pages.
        
        Returns:
            List of text strings (one per document) - will be cleaned at runtime
        """
        texts = []
        for category in self.categories:
            for doc_data in self.category_data[category]:
                # Get pages to process (first n pages if max_pages is specified, otherwise all)
                pages_to_process = doc_data.pages[:max_pages] if max_pages is not None else doc_data.pages
                
                # Combine page texts
                combined_text = "\n".join(page.text for page in pages_to_process)
                texts.append(combined_text)
        return texts
    
    def extract_labels(self) -> List[int]:
        """
        Extract labels from TrainingData for model training.
        
        Returns:
            List of integer labels
        """
        labels = []
        class_to_idx = {cls: i for i, cls in enumerate(self.categories)}
        for category in self.categories:
            for _ in self.category_data[category]:
                labels.append(class_to_idx[category])
        return labels
    
    def extract_file_hashes(self) -> List[str]:
        """
        Extract file hashes from TrainingData.
        
        Returns:
            List of file hashes (one per document, in same order as extract_texts)
        """
        hashes = []
        for category in self.categories:
            for doc_data in self.category_data[category]:
                hashes.append(doc_data.file_hash)
        return hashes


class ClassNamesData(BaseModel):
    """Class names mapping data."""
    class_names: List[str]
    id2label: Dict[int, str]
    label2id: Dict[str, int]
    
    @field_validator('class_names', mode='before')
    @classmethod
    def validate_class_names(cls, v):
        """Convert integers to strings if needed (for backward compatibility)."""
        if isinstance(v, list):
            return [str(item) if not isinstance(item, str) else item for item in v]
        return v


class TrainingDataMetadata(BaseModel):
    """Metadata about the training data used."""
    total_documents: int
    total_categories: int
    train_samples: int
    test_samples: int
    test_split_percentage: float
    distribution: Dict[str, Dict[str, int | float]]


class FeatureExtractionMetadata(BaseModel):
    """Metadata about feature extraction parameters."""
    vectorizer_type: str
    max_features: int
    ngram_range: List[int]
    min_df: int
    max_df: float
    sublinear_tf: bool
    vocabulary_size: int
    feature_dim: int


class ModelParametersMetadata(BaseModel):
    """Metadata about model parameters."""
    model_type: str
    alpha: Optional[float] = None
    C: Optional[float] = None
    solver: Optional[str] = None
    class_weight: Optional[str] = None


class ConfidenceMetrics(BaseModel):
    """Confidence score metrics."""
    mean: float
    min: float
    max: float
    low_confidence_count: int
    low_confidence_percentage: float


class PerformanceMetricsMetadata(BaseModel):
    """Metadata about model performance."""
    train_accuracy: float
    test_accuracy: float
    train_confidence: ConfidenceMetrics
    test_confidence: ConfidenceMetrics


class TrainingMetadata(BaseModel):
    """Complete training metadata for TFIDF classifier."""
    model_id: str
    training_timestamp: str
    model_type: str
    training_data: TrainingDataMetadata
    feature_extraction: FeatureExtractionMetadata
    model_parameters: ModelParametersMetadata
    performance_metrics: PerformanceMetricsMetadata
    train_data_hashes: Optional[List[str]] = Field(None, description="File hashes of documents used for training")
    
    @classmethod
    def from_training_objects(
        cls,
        model_id: str,
        model_type: str,
        vectorizer: Any,  # TfidfVectorizer
        classifier: Any,  # sklearn classifier
        class_names: List[str],
        X_train: List[str],
        X_test: List[str],
        y_train: List[int],
        y_test: List[int],
        train_acc: float,
        test_acc: float,
        train_confidences: List[float],
        test_confidences: List[float],
        test_split_percentage: float = 20.0,
        train_data_hashes: Optional[List[str]] = None
    ) -> 'TrainingMetadata':
        """
        Create TrainingMetadata from training objects.
        
        Args:
            model_id: Unique identifier for the model
            model_type: Type of classifier ("MultinomialNB" or "LogisticRegression")
            vectorizer: Fitted TfidfVectorizer instance
            classifier: Trained sklearn classifier
            class_names: List of category names
            X_train: Training texts
            X_test: Test texts
            y_train: Training labels
            y_test: Test labels
            train_acc: Training accuracy
            test_acc: Test accuracy
            train_confidences: Training confidence scores
            test_confidences: Test confidence scores
            test_split_percentage: Percentage of data used for testing
        
        Returns:
            TrainingMetadata instance
        """
        from datetime import datetime, timezone
        from collections import Counter
        
        # Calculate training data distribution
        # Combine train and test labels to get total distribution
        all_labels = list(y_train) + list(y_test)
        label_counts = Counter(all_labels)
        train_label_counts = Counter(y_train)
        test_label_counts = Counter(y_test)
        
        training_distribution = {}
        for idx, class_name in enumerate(class_names):
            total_count = label_counts.get(idx, 0)
            train_count = train_label_counts.get(idx, 0)
            test_count = test_label_counts.get(idx, 0)
            training_distribution[class_name] = {
                "total": total_count,
                "train": train_count,
                "test": test_count,
                "train_percentage": round((train_count / total_count * 100) if total_count > 0 else 0, 2),
                "test_percentage": round((test_count / total_count * 100) if total_count > 0 else 0, 2)
            }
        
        # Extract feature extraction metadata from vectorizer
        feature_extraction = FeatureExtractionMetadata(
            vectorizer_type=type(vectorizer).__name__,
            max_features=vectorizer.max_features if hasattr(vectorizer, 'max_features') else None,
            ngram_range=list(vectorizer.ngram_range) if hasattr(vectorizer, 'ngram_range') else [1, 1],
            min_df=vectorizer.min_df if hasattr(vectorizer, 'min_df') else None,
            max_df=vectorizer.max_df if hasattr(vectorizer, 'max_df') else None,
            sublinear_tf=vectorizer.sublinear_tf if hasattr(vectorizer, 'sublinear_tf') else False,
            vocabulary_size=len(vectorizer.vocabulary_) if hasattr(vectorizer, 'vocabulary_') else 0,
            feature_dim=len(vectorizer.vocabulary_) if hasattr(vectorizer, 'vocabulary_') else 0
        )
        
        # Extract model parameters from classifier
        model_parameters = ModelParametersMetadata(
            model_type=model_type,
            alpha=getattr(classifier, 'alpha', None) if model_type == "MultinomialNB" else None,
            C=getattr(classifier, 'C', None) if model_type == "LogisticRegression" else None,
            solver=getattr(classifier, 'solver', None) if model_type == "LogisticRegression" else None,
            class_weight=str(getattr(classifier, 'class_weight', None)) if model_type == "LogisticRegression" else None
        )
        
        # Create confidence metrics
        train_confidence = ConfidenceMetrics(
            mean=float(sum(train_confidences) / len(train_confidences)) if train_confidences else 0.0,
            min=float(min(train_confidences)) if train_confidences else 0.0,
            max=float(max(train_confidences)) if train_confidences else 0.0,
            low_confidence_count=sum(1 for c in train_confidences if c < 0.6) if train_confidences else 0,
            low_confidence_percentage=round(sum(1 for c in train_confidences if c < 0.6) / len(train_confidences) * 100, 2) if train_confidences else 0.0
        )
        
        test_confidence = ConfidenceMetrics(
            mean=float(sum(test_confidences) / len(test_confidences)) if test_confidences else 0.0,
            min=float(min(test_confidences)) if test_confidences else 0.0,
            max=float(max(test_confidences)) if test_confidences else 0.0,
            low_confidence_count=sum(1 for c in test_confidences if c < 0.6) if test_confidences else 0,
            low_confidence_percentage=round(sum(1 for c in test_confidences if c < 0.6) / len(test_confidences) * 100, 2) if test_confidences else 0.0
        )
        
        # Create performance metrics
        performance_metrics = PerformanceMetricsMetadata(
            train_accuracy=float(train_acc),
            test_accuracy=float(test_acc),
            train_confidence=train_confidence,
            test_confidence=test_confidence
        )
        
        # Create training data metadata
        training_data_meta = TrainingDataMetadata(
            total_documents=len(X_train) + len(X_test),
            total_categories=len(class_names),
            train_samples=len(X_train),
            test_samples=len(X_test),
            test_split_percentage=test_split_percentage,
            distribution=training_distribution
        )
        
        return cls(
            model_id=model_id,
            training_timestamp=datetime.now(timezone.utc).isoformat(),
            model_type=model_type,
            training_data=training_data_meta,
            feature_extraction=feature_extraction,
            model_parameters=model_parameters,
            performance_metrics=performance_metrics,
            train_data_hashes=train_data_hashes
        )


class TFIDFClassifierModel(BaseModel):
    """
    Model for validating TFIDF classifier folder structure and files.
    
    Expected folder structure:
    - document_classifier_nb.joblib (required)
    - tfidf_vectorizer.joblib (required)
    - class_names.json (required)
    - training_metadata.json (optional but recommended)
    """
    model_config = ConfigDict(extra='forbid')  # Prevent extra fields not in schema
    
    model_dir: Path = Field(..., description="Path to the classifier model directory", exclude=True)
    classifier_file: Path = Field(..., description="Path to document_classifier_nb.joblib", exclude=True)
    vectorizer_file: Path = Field(..., description="Path to tfidf_vectorizer.joblib", exclude=True)
    class_names_file: Path = Field(..., description="Path to class_names.json", exclude=True)
    training_metadata_file: Optional[Path] = Field(None, description="Path to training_metadata.json", exclude=True)
    
    class_names_data: Optional[ClassNamesData] = Field(None, description="Loaded class names data")
    training_metadata: Optional[TrainingMetadata] = Field(None, description="Loaded training metadata")
    
    # Training objects stored for saving (excluded from serialization)
    classifier: Optional[Any] = Field(None, description="Trained sklearn classifier", exclude=True)
    vectorizer: Optional[Any] = Field(None, description="Fitted TfidfVectorizer", exclude=True)
    training_params: Optional[Dict[str, Any]] = Field(None, description="Keyword parameters for TrainingMetadata.from_training_objects", exclude=True)
    
    @field_validator('model_dir', mode='before')
    @classmethod
    def validate_model_dir(cls, v):
        """Convert string to Path if needed."""
        if isinstance(v, str):
            return Path(v)
        return v
    
    @field_validator('classifier_file', 'vectorizer_file', 'class_names_file', 'training_metadata_file', mode='before')
    @classmethod
    def validate_paths(cls, v):
        """Convert string to Path if needed."""
        if v is None:
            return None
        if isinstance(v, str):
            return Path(v)
        return v
    
    @model_validator(mode='after')
    def validate_files_exist(self):
        """
        Validate that all required files exist.
        Only validates if files are expected to exist (not when creating new model for saving).
        """
        # Skip validation if classifier/vectorizer/training_params are set (creating new model)
        if self.classifier is not None or self.vectorizer is not None or self.training_params is not None:
            return self
        
        # Only validate if loading existing model
        errors = []
        
        # Check required files
        if not self.classifier_file.exists():
            errors.append(f"Classifier file not found: {self.classifier_file}")
        
        if not self.vectorizer_file.exists():
            errors.append(f"Vectorizer file not found: {self.vectorizer_file}")
        
        if not self.class_names_file.exists():
            errors.append(f"Class names file not found: {self.class_names_file}")
        
        # Check optional file
        if self.training_metadata_file and not self.training_metadata_file.exists():
            errors.append(f"Training metadata file not found: {self.training_metadata_file}")
        
        if errors:
            raise ValueError(f"Model validation failed:\n" + "\n".join(f"  - {e}" for e in errors))
        
        return self
    
    @classmethod
    def from_directory(cls, model_dir: Path | str) -> 'TFIDFClassifierModel':
        """
        Create a TFIDFClassifierModel instance from a model directory.
        
        Args:
            model_dir: Path to the classifier model directory
        
        Returns:
            TFIDFClassifierModel instance with validated structure
        
        Raises:
            ValueError: If required files are missing
        """
        model_dir = Path(model_dir) if isinstance(model_dir, str) else model_dir
        
        if not model_dir.exists():
            raise ValueError(f"Model directory does not exist: {model_dir}")
        
        if not model_dir.is_dir():
            raise ValueError(f"Path is not a directory: {model_dir}")
        
        # Define expected file paths
        classifier_file = model_dir / "document_classifier_nb.joblib"
        vectorizer_file = model_dir / "tfidf_vectorizer.joblib"
        class_names_file = model_dir / "class_names.json"
        training_metadata_file = model_dir / "training_metadata.json"
        
        # Create instance (validation will check file existence)
        instance = cls(
            model_dir=model_dir,
            classifier_file=classifier_file,
            vectorizer_file=vectorizer_file,
            class_names_file=class_names_file,
            training_metadata_file=training_metadata_file if training_metadata_file.exists() else None
        )
        
        # Load class names data
        instance.load_class_names()
        
        # Load training metadata if available
        if instance.training_metadata_file:
            instance.load_training_metadata()
        
        return instance
    
    def load_class_names(self) -> ClassNamesData:
        """
        Load and validate class names data from JSON file.
        
        Returns:
            ClassNamesData instance
        
        Raises:
            ValueError: If file is invalid or missing required fields
        """
        try:
            with open(self.class_names_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            self.class_names_data = ClassNamesData.model_validate(data)
            return self.class_names_data
        except json.JSONDecodeError as e:
            raise ValueError(f"Invalid JSON in class_names.json: {e}")
        except Exception as e:
            raise ValueError(f"Error loading class names: {e}")
    
    def get_class_names(self) -> List[str]:
        """
        Get list of class names.
        
        Returns:
            List of class name strings
        """
        if self.class_names_data is None:
            self.load_class_names()
        return self.class_names_data.class_names
    
    def get_id2label(self) -> Dict[int, str]:
        """
        Get id to label mapping.
        
        Returns:
            Dictionary mapping integer IDs to class names
        """
        if self.class_names_data is None:
            self.load_class_names()
        return self.class_names_data.id2label
    
    def get_label2id(self) -> Dict[str, int]:
        """
        Get label to id mapping.
        
        Returns:
            Dictionary mapping class names to integer IDs
        """
        if self.class_names_data is None:
            self.load_class_names()
        return self.class_names_data.label2id
    
    def load_training_metadata(self) -> TrainingMetadata:
        """
        Load and validate training metadata from JSON file.
        
        Returns:
            TrainingMetadata instance
        
        Raises:
            ValueError: If file is invalid or missing required fields
        """
        if not self.training_metadata_file or not self.training_metadata_file.exists():
            raise ValueError(f"Training metadata file not found: {self.training_metadata_file}")
        
        try:
            with open(self.training_metadata_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            self.training_metadata = TrainingMetadata.model_validate(data)
            return self.training_metadata
        except json.JSONDecodeError as e:
            raise ValueError(f"Invalid JSON in training_metadata.json: {e}")
        except Exception as e:
            raise ValueError(f"Error loading training metadata: {e}")
    
    def get_training_metadata(self) -> Optional[TrainingMetadata]:
        """
        Get training metadata.
        
        Returns:
            TrainingMetadata instance or None if not available
        """
        if self.training_metadata is None and self.training_metadata_file and self.training_metadata_file.exists():
            self.load_training_metadata()
        return self.training_metadata
    
    def save(self) -> None:
        """
        Save all model files to the model directory.
        
        Saves:
        - Classifier model (joblib)
        - Vectorizer (joblib)
        - Class names (JSON)
        - Training metadata (JSON, includes train_data_hashes if provided)
        
        Requires classifier, vectorizer, and training_params to be set in constructor.
        """
        import joblib
        
        if self.classifier is None or self.vectorizer is None or self.training_params is None:
            raise ValueError("classifier, vectorizer, and training_params must be set before calling save()")
        
        # Create TrainingMetadata from keyword params
        training_metadata = TrainingMetadata.from_training_objects(**self.training_params)
        
        # Extract class_names from params
        class_names = self.training_params.get("class_names", [])
        
        # Ensure directory exists
        self.model_dir.mkdir(parents=True, exist_ok=True)
        
        # Save classifier
        joblib.dump(self.classifier, self.classifier_file)
        
        # Save vectorizer
        joblib.dump(self.vectorizer, self.vectorizer_file)
        
        # Save class names
        class_names_data = ClassNamesData(
            class_names=class_names,
            id2label={i: name for i, name in enumerate(class_names)},
            label2id={name: i for i, name in enumerate(class_names)}
        )
        with open(self.class_names_file, 'w', encoding='utf-8') as f:
            json.dump(class_names_data.model_dump(), f, indent=2, ensure_ascii=False)
        
        # Save training metadata
        if not self.training_metadata_file:
            # Set default path if not already set
            self.training_metadata_file = self.model_dir / "training_metadata.json"
        
        with open(self.training_metadata_file, 'w', encoding='utf-8') as f:
            json.dump(training_metadata.model_dump(exclude_none=True), f, indent=2, ensure_ascii=False)
        
        # Update instance data
        self.class_names_data = class_names_data
        self.training_metadata = training_metadata
    
    def validate_structure(self) -> Dict[str, bool]:
        """
        Validate the model folder structure and return status for each file.
        
        Returns:
            Dictionary with file paths as keys and existence status as values
        """
        return {
            "model_dir": self.model_dir.exists() and self.model_dir.is_dir(),
            "classifier_file": self.classifier_file.exists(),
            "vectorizer_file": self.vectorizer_file.exists(),
            "class_names_file": self.class_names_file.exists(),
            "training_metadata_file": self.training_metadata_file.exists() if self.training_metadata_file else False,
        }
