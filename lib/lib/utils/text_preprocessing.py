"""
Text preprocessing utilities for document classification.
Provides consistent text cleaning for both training and inference.
"""

import re
import time
from dataclasses import dataclass, field, asdict
from typing import Dict, List, Optional, Tuple

from nltk.corpus import stopwords

try:
    spanish_stopwords = set(stopwords.words('spanish'))
except LookupError:
    import nltk
    nltk.download('stopwords', quiet=True)
    spanish_stopwords = set(stopwords.words('spanish'))

# Domain-specific stopwords for legal documents
DOMAIN_STOPWORDS = {
    "notaria", "republica", "provincia", "copia", "escritura",
    "folio", "registro", "publico", "telefono", "certificado",
    "licenciado", "compareciente", "otorgante", "inmueble",
    "finca", "parte", "comprador", "vendedor", "tom", "reforma",
    "agraria", "minicipal", "municipal"
}

# Combined stopwords
CUSTOM_STOPWORDS = spanish_stopwords.union(DOMAIN_STOPWORDS)


@dataclass
class DocumentMetrics:
    """Data class for per-document cleaning metrics (Repository Pattern)"""
    filename: str
    category: str
    original_length: int = 0
    original_words: int = 0
    after_ocr_fix_words: int = 0
    after_ocr_artifacts_words: int = 0
    after_nonalpha_words: int = 0
    after_stopwords_words: int = 0
    removed_stopwords_count: int = 0
    processing_time: float = 0.0
    ocr_errors_fixed: List[str] = field(default_factory=list)
    artifacts_removed: List[str] = field(default_factory=list)
    final_text_length: int = 0
    
    def to_dict(self) -> Dict:
        return asdict(self)


class TextCleaner:
    """
    Strategy Pattern: Encapsulates cleaning strategies with optional metrics tracking.
    This class provides consistent text cleaning for both training and inference.
    """
    def __init__(self, track_metrics: bool = False):
        """
        Initialize TextCleaner.
        
        Args:
            track_metrics: If True, returns metrics along with cleaned text
        """
        self.track_metrics = track_metrics
    
    def fix_common_ocr_errors(self, text: str) -> Tuple[str, List[str]]:
        """Fix common OCR errors and return list of fixes applied"""
        fixes_applied = []
        
        # Common OCR error patterns found in legal documents
        patterns = [
            # Basic normalization
            (r'\bFundac[ií]n\b', 'fundacion'),
            (r'\bRep[ií]blica\b', 'republica'),
            (r'\bPanam[eé]\b', 'panama'),
            (r'\bC[eé]nsado\b', 'censado'),
            
            # Common character misrecognitions
            (r'\beprotcealin\b', 'se protocoliza'),
            (r'\bprotcolza\b', 'protocoliza'),
            (r'\bprotcolizo\b', 'protocolizo'),
            (r'\bpotecoliza\b', 'protocoliza'),
            (r'\bcom\s+domiclo\b', 'con domicilio'),
            (r'\benn\s+cad\b', 'en la ciudad'),
            (r'\bncionalda[óo]\b', 'nacionalidad'),
            (r'\betadouniense\b', 'estadounidense'),
            (r'\baconaldadextaounidense\b', 'estadounidense'),
            (r'\bidentdad\b', 'identidad'),
            (r'\bidendad\b', 'identidad'),
            (r'\bpenonal\b', 'personal'),
            (r'\bpaspone\b', 'pasaporte'),
            (r'\bpliore\b', 'pasaporte'),
            (r'\bvecan\b', 'vecino'),
            (r'\bmanifetaton\b', 'manifiestan'),
            (r'\bInepret\b', 'intérprete'),
            (r'\beotender\b', 'entender'),
            (r'\bpatil\b', 'español'),
            (r'\bpers\b', 'para'),
            (r'\bqueres\b', 'querer'),
            (r'\bconosco\b', 'conozco'),
            (r'\bauoczado\b', 'autorizado'),
            (r'\bfoal\b', 'final'),
            (r'\bccl\b', 'acto'),
            (r'\bme\s+preven\b', 'me previene'),
            (r'\bpoecllzc[óo]n\b', 'protocolización'),
            (r'\bprococi[óo]n\b', 'protocolización'),
            (r'\boliida\b', 'solicitada'),
            (r'\bepedira\b', 'solicitada'),
            (r'\bCoeds\b', 'Conforme'),
            (r'\bbec\b', 'se'),
            (r'\bLicencido\b', 'Licenciado'),
            (r'\bPbco\b', 'Público'),
            (r'\bpnaor\b', 'Notario'),
            (r'\bcompaeceon\b', 'comparecer'),
            (r'\bpennalment\b', 'personalmente'),
            (r'\bmámerocuato\b', 'número'),
            (r'\brecess\b', 'novecientos'),
            (r'\bvain\b', 'varón'),
            (r'\bmayo\b', 'mayor'),
            (r'\bcards\b', 'casada'),
            (r'\bProvinci\b', 'Provincia'),
            (r'\bChris\b', 'Chiriquí'),
            (r'\bRepl\b', 'República'),
            (r'\bDies\b', 'Dieciséis'),
            (r'\bBaguta\b', 'Barqueta'),
            (r'\bmeena\b', 'necesita'),
            (r'\bton\b', 'con'),
            (r'\bprocoln\b', 'protocolizan'),
            (r'\bFUNDAGION\b', 'FUNDACIÓN'),
            (r'\bfundagion\b', 'fundación'),
            
            # Fix spacing issues
            (r'\bde\s+la\b', 'dela'),  # Normalize spacing
            (r'\bdel\s+', 'del '),  # Normalize spacing
        ]
        
        for pattern, replacement in patterns:
            if re.search(pattern, text, re.IGNORECASE):
                text = re.sub(pattern, replacement, text, flags=re.IGNORECASE)
                fixes_applied.append(f"{pattern} -> {replacement}")
        
        # Remove repeated letters (but keep double letters that might be valid)
        text = re.sub(r'(.)\1{3,}', r'\1', text)  # Only remove 4+ repeats
        
        return text, fixes_applied
    
    def remove_ocr_artifacts(self, text: str) -> Tuple[str, List[str]]:
        """Remove OCR artifacts and return list of artifacts found"""
        artifacts = []
        
        # Find artifacts before removal
        artifacts.extend(re.findall(r'\(\d+(-\d+)*\)', text))
        artifacts.extend(re.findall(r'[\|\@\¢\~\—\_]', text))
        
        text = re.sub(r'\(\d+(-\d+)*\)', ' ', text)
        text = re.sub(r'[\|\@\¢\~\—\_]', ' ', text)
        text = re.sub(r'\s+', ' ', text)
        
        return text.strip(), artifacts
    
    def clean_text(
        self, 
        text: str, 
        filename: str = "", 
        category: str = "",
        return_metrics: Optional[bool] = None
    ) -> str | Tuple[str, DocumentMetrics]:
        """
        Clean text using the same pipeline as training.
        This ensures consistency between training and inference.
        
        Args:
            text: Raw text to clean
            filename: Optional filename for metrics tracking
            category: Optional category for metrics tracking
            return_metrics: Override self.track_metrics if provided
        
        Returns:
            Cleaned text, or tuple (cleaned_text, metrics) if tracking metrics
        """
        should_track = return_metrics if return_metrics is not None else self.track_metrics
        start_time = time.time() if should_track else None
        
        # Initialize metrics if tracking
        metrics = None
        if should_track:
            metrics = DocumentMetrics(
                filename=filename,
                category=category,
                original_length=len(text),
                original_words=len(text.split())
            )
        
        # Step 1: Lowercase
        text_lower = text.lower()
        
        # Step 2: Fix OCR errors
        text_fixed, ocr_fixes = self.fix_common_ocr_errors(text_lower)
        if metrics:
            metrics.after_ocr_fix_words = len(text_fixed.split())
            metrics.ocr_errors_fixed = ocr_fixes
        
        # Step 3: Remove artifacts
        text_cleaned, artifacts = self.remove_ocr_artifacts(text_fixed)
        if metrics:
            metrics.after_ocr_artifacts_words = len(text_cleaned.split())
            metrics.artifacts_removed = artifacts[:10]  # Limit to first 10 for storage
        
        # Step 4: Remove non-alphanumeric (keep Spanish characters)
        text_cleaned = re.sub(r'[^a-záéíóúñü0-9\s]', ' ', text_cleaned)
        tokens = text_cleaned.split()
        if metrics:
            metrics.after_nonalpha_words = len(tokens)
        
        # Step 5: Remove stopwords
        tokens_no_stop = [t for t in tokens if t not in CUSTOM_STOPWORDS]
        if metrics:
            metrics.after_stopwords_words = len(tokens_no_stop)
            metrics.removed_stopwords_count = len(tokens) - len(tokens_no_stop)
        
        # Final text
        final_text = " ".join(tokens_no_stop)
        if metrics:
            metrics.final_text_length = len(final_text)
            metrics.processing_time = time.time() - start_time
        
        if should_track:
            return final_text, metrics
        return final_text, None

