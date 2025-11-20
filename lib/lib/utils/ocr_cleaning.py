"""
OCR text cleaning utilities for legal documents.
This module provides functions to clean OCR output from Spanish legal documents,
fixing common character misrecognitions and noise patterns.
"""

import re
from typing import Any, Dict, Optional, Tuple


def clean_legal_ocr(
    text: str, 
    return_stats: bool = False,
    stats_dict: Optional[Dict[str, int]] = None
) -> str | Tuple[str, Dict[str, int]]:
    """
    Clean OCR text from legal documents.
    
    This function specifically handles common OCR errors found in Spanish legal documents,
    including character misrecognitions, isolated special characters, and common word errors.
    
    Args:
        text: Raw OCR text with errors
        return_stats: If True, return a tuple (cleaned_text, statistics_dict)
        stats_dict: Optional dictionary to update with statistics (mutated in place)
        
    Returns:
        Cleaned text with improved quality, or tuple (text, stats) if return_stats=True
    """
    if not text or not text.strip():
        if return_stats:
            return text, {}
        return text
    
    # Initialize statistics tracking
    fix_stats = stats_dict if stats_dict is not None else {}
    
    # Remove isolated special characters and noise patterns
    # Remove sequences of pipes, tildes, dollar signs (common OCR noise)
    text = re.sub(r'[|~$]{1,}', ' ', text)
    
    # Remove isolated single characters that are likely OCR errors (like 'o', 'g', 'S' alone)
    text = re.sub(r'\s+[oOgS]\s+', ' ', text)
    
    # Remove lines that are mostly special characters or very short noise
    lines = text.split('\n')
    cleaned_lines = []
    for line in lines:
        # Skip lines that are mostly special characters or very short isolated characters
        if len(line.strip()) <= 2 and re.match(r'^[^\w\s]{0,2}$', line.strip()):
            continue
        cleaned_lines.append(line)
    text = '\n'.join(cleaned_lines)
    
    # Fix common Spanish legal terms and OCR errors
    # Store pattern names for statistics tracking
    legal_fixes = {
        # Common OCR character misrecognitions
        ('Noto', r'\bNoto\b'): 'Notario',
        ('Curto', r'\bCurto\b'): 'Cuarto',
        ('PASAS', r'\bPASAS\b'): 'PANAMA',
        ('Panam', r'\bPanam\b(?!á)'): 'Panama',  # Fix "Panam" but not "Panamá"
        ('dela', r'\bdela\b'): 'de la',
        ('tos', r'\btos\b'): 'los',
        ('Cbocea', r'\bCbocea\b'): 'Cabecera',
        ('SEDO', r'\bSEDO\b'): 'SEDE',
        ('potecoliza', r'\bpotecoliza\b'): 'protocoliza',
        ('protcolza', r'\bprotcolza\b'): 'protocoliza',
        ('protcolizo', r'\bprotcolizo\b'): 'protocolizo',
        ('República', r'\bRepública\b(?!\s)'): 'República ',
        # Common word errors
        ('pasas', r'\bpasas\b'): 'Panama',
        ('Not!', r'\bNot!\b'): 'Notario',
        ('deta', r'\bdeta\b'): 'identidad',
        ('peroo', r'\bperoo\b'): 'persona',
        ('mámero', r'\bmámero\b'): 'número',
        ('compare', r'\bcompare\b(?!cer)'): 'comparecer',
        ('var,', r'\bvar,\b'): 'varón,',
        ('pasto', r'\bpasto\b'): 'panameño',
        ('ada', r'\bada\b'): 'edad',
        ('eat', r'\beat\b'): 'esta',
        ('cut', r'\bcut\b'): 'esta',
        ('Meade', r'\bMeade\b'): 'identidad',
        ('tes', r'\btes\b(?!\s+mi)'): 'tres',
        # Additional common OCR errors from legal documents
        ('choa', r'\bchoa\b'): 'número',
        ('sty', r'\bsty\b'): 'seiscientos',
        ('tro', r'\btro\b'): 'tres',
        ('recents', r'\brecents\b'): 'ciento',
        ('moves', r'\bmoves\b'): 'setecientos',
        ('Pemonsimenis', r'\bPemonsimenis\b'): 'personas',
        ('vat,', r'\bvat,\b'): 'varón,',
        ('có', r'\bcó\b'): 'cédula',
        ('idemidad', r'\bidemidad\b'): 'identidad',
        ('personas |', r'\bpersonas\s+\|\s*\b'): 'personas ',
        ('ine', r'\bine\b(?!\s+con)'): 'una',
        ('ctl', r'\bctl\b'): 'cédula',
        ('dead', r'\bdead\b'): 'identidad',
        ('pone!', r'\bpone!\b'): 'número',
        ('cuerociónos', r'\bcuerociónos\b'): 'cuatrocientos',
        ('acest', r'\bacest\b'): 'seiscientos',
        ('sit', r'\bsit\b'): 'setecientos',
        ('uiniene', r'\buiniene\b'): 'quinientos',
        ('decisis', r'\bdecisis\b'): 'dieciséis',
        ('peat', r'\bpeat\b'): 'presente',
        # Note: 'is', 'eo', 'ah' fixes removed as they're too aggressive
        # These can be valid words in context
        ('gen', r'\bgen\b'): 'efecto',
        ('eSrepoo', r'\beSrepoo\b'): 'presente',
        ('yal', r'\byal\b'): 'y al',
        ('Que ala', r'\bQue\s+ala\b'): 'Que a la',
        # Note: Removing 'cc' and 'cece' fixes as they might be legitimate abbreviations
        ('Soria', r'\bSoria\b'): 'Señoría',
        ('slice', r'\bslice\b'): 'solicita',
        ('imterendon', r'\bimterendon\b'): 'interesados',
        ('Adver', r'\bAdver\b'): 'Advertir',
        ('excita', r'\bexcita\b'): 'escritura',
        ('Ida', r'\bIda\b'): 'la',
        ('coco', r'\bcoco\b'): 'copia',
        ('fu', r'\bfu\b'): 'fue',
        ('dels', r'\bdels\b'): 'de los',
        ('tios', r'\btios\b'): 'testigos',
        ('instrumentals', r'\binstrumentals\b'): 'instrumentales',
        ('SOU', r'\bSOU\b'): 'SOLIS',
        ('Yeina', r'\bYeina\b'): 'vecina',
        ('Seasorees', r'\bSeasorees\b'): 'Señores',
        ('chata', r'\bchata\b'): 'cuarenta',
        ('ques', r'\bques\b'): 'que es',
        ('on', r'\bon\b(?!\s+het)'): 'y',
        ('het', r'\bhet\b'): 'la',
        ('leap', r'\bleap\b'): 'leer',
        ('nt', r'\bnt\b'): 'no',
        ('dination', r'\bdination\b'): 'determinación',
        ('ici', r'\bici\b'): 'la',
        # Note: 'pc' removal skipped as it might be a legitimate abbreviation
        ('Jos', r'\bJos\b'): 'Los',
        ('ates', r'\bates\b'): 'actos',
        ('dy', r'\bdy\b'): 'doy',
        ('Evert', r'\bEvert\b'): 'Efectuado',
        ('eva', r'\beva\b'): 'el',
        ('meo', r'\bmeo\b'): 'me',
        ('sesion', r'\bsesion\b'): 'seiscientos',
        ('Ries', r'\bRies\b'): 'Firmas',
        ('ABEL', r'\bABEL\b'): 'AVILA',
        ('PEL', r'\bPEL\b'): 'DEL',
        ('PANA —', r'\bPANA\s*—\s*\b'): 'PANAMA',
        # Fix common patterns in legal documents
        ('ID_format', r'\b(\d+)\s*-\s*(\d+)\s*-\s*(\d+)\b'): r'\1-\2-\3',  # Normalize ID number formatting
    }
    
    for (fix_name, pattern), replacement in legal_fixes.items():
        # Check if pattern matches before replacement
        matches = re.findall(pattern, text, flags=re.IGNORECASE)
        if matches:
            match_count = len(matches) if isinstance(matches, list) else 1
            fix_stats[fix_name] = fix_stats.get(fix_name, 0) + match_count
            text = re.sub(pattern, replacement, text, flags=re.IGNORECASE)
    
    # Remove excessive whitespace (but preserve newlines for document structure)
    # First normalize line breaks
    text = re.sub(r'\r\n', '\n', text)
    text = re.sub(r'\r', '\n', text)
    
    # Remove excessive spaces but keep single spaces
    text = re.sub(r'[ \t]+', ' ', text)
    
    # Remove empty lines (more than 2 consecutive)
    text = re.sub(r'\n{3,}', '\n\n', text)
    
    # Clean up trailing whitespace on lines
    lines = text.split('\n')
    lines = [line.rstrip() for line in lines]
    text = '\n'.join(lines)
    
    # Final normalization
    text = text.strip()
    
    if return_stats:
        return text, fix_stats
    return text


def extract_document_features(
    text: str,
    return_stats: bool = False,
    stats_dict: Optional[Dict[str, int]] = None
) -> Dict[str, Any] | Tuple[Dict[str, Any], Dict[str, int]]:
    """
    Extract document-level features that are reliable even with poor OCR.
    
    These features can be used for ensemble approaches or as additional
    inputs to the classifier.
    
    Args:
        text: Document text
        return_stats: If True, return a tuple (features_dict, phrase_stats_dict)
        stats_dict: Optional dictionary to update with phrase match statistics
        
    Returns:
        Dictionary of extracted features, or tuple (features, phrase_stats) if return_stats=True
    """
    features = {}
    phrase_stats = stats_dict if stats_dict is not None else {}
    
    # Count occurrences of important legal phrases (even if slightly corrupted)
    important_phrases = {
        'REPUBLICA': r'(?i)rep[úu]blica|republica',
        'PANAMA': r'(?i)panam[áa]|panama',
        'NOTARIA': r'(?i)notar[íi]a|notaria',
        'ESCRITURA': r'(?i)escritura',
        'CERTIFICADO': r'(?i)certificado',
        'SOCIEDAD': r'(?i)sociedad',
        'ANONIMA': r'(?i)an[óo]nima|anomina',
    }
    
    for phrase_name, pattern in important_phrases.items():
        matches = re.findall(pattern, text)
        match_count = len(matches) if isinstance(matches, list) else 1
        features[f'phrase_{phrase_name.lower()}_count'] = match_count
        if match_count > 0:
            phrase_stats[f'phrase_{phrase_name}'] = phrase_stats.get(f'phrase_{phrase_name}', 0) + match_count
    
    # Extract document numbers and dates (common patterns)
    doc_numbers = re.findall(r'(?i)(?:escritura|escritura|notaria).*?no\.?\s*[:\-]?\s*(\d+)', text)
    dates = re.findall(r'\d{1,2}\s+de\s+\w+\s+de\s+\d{4}', text)
    
    features['has_document_number'] = len(doc_numbers) > 0
    features['has_date'] = len(dates) > 0
    features['document_number_count'] = len(doc_numbers)
    features['date_count'] = len(dates)
    
    # Count all-caps sections (headers, titles)
    all_caps_lines = [line for line in text.split('\n') 
                      if line.strip() and line.strip().isupper() and len(line.strip()) > 5]
    features['all_caps_sections'] = len(all_caps_lines)
    
    # Document length features
    features['total_length'] = len(text)
    features['line_count'] = len(text.split('\n'))
    features['word_count'] = len(text.split())
    
    if return_stats:
        return features, phrase_stats
    return features

