"""
Final refinements test for NER
"""

import ner_shared as ner_lib

# ============================================================================
# ALL TEST CASES IN A SINGLE LIST (text, should_be_PER)
# ============================================================================

test_cases = [
    # Problematic lines
    ("NOTARIA UNDECIMA DEL CIRCUITO DE PANAMA", False),
    ("ESCRITURA PUBLICA NUMERO MIL DOSCIENTOS", False),
    ("Los directores podrán ser removidos", True),
    ("as well as the following", False),
    ("may make themselves present", False),
    ("Shareholders Board convened special", False),
    ("Néw Orteans, LA 70112", False),
    ("New Orleans, LA 70112", False),
    ("CARLOS CEDEÑO, varón, panameño", True),
    ("RAUL ALBERTO ADAMES FRANCESCHI, Notario", True),

    # Final refinement cases
    ("CARLOS STRAH CASTRELLON, Notario Público", True),
    ("AMADO EVERARDO ARJONA DUQUE, varón", True),
    ("JORGE LUIS ESPINOSA compareció", True),
    ("Licenciado Amado Everardo Arjona actuó", True),
    ("MIGUEL ANGEL CEDEÑO firmó", True),
    ("FUNDACION LUCKY STAR es una entidad", False),
    ("MINISTERIO DE ECONOMÍA aprobó", False),
    ("CÓDIGO FISCAL, artículo", False),
    ("ESCRITURA PÚBLICA número", False),
    ("REPRESENTANTE LEGAL de la sociedad", False),
    ("OBLIGACIONES ANTE TERCEROS quedan", False),
    ("SEÑOR CONTRIBUYENTE debe", False),
    ("Samuel Lewis, calle conocida", False),
    ("MIEMBROS INICIALES del consejo", False),
    ("NOTARIA UNDECIMA del circuito", False),
    ("PANBRIDGE INVESTMENT CORP.", False),
    ("ACCIONES COMUNES sin valor", False),
]

# ============================================================================
# RUN TEST
# ============================================================================

correct = 0
total = len(test_cases)

print("="*80)
print("TESTING ALL CASES WITH EXPECTED PER FLAG")
print("="*80)

for text, should_be_per in test_cases:
    entities = ner_lib.label_entities(text)
    entities = ner_lib.remove_overlaps(entities)
    
    has_per = any(e[2] == "PER" for e in entities)
    is_correct = has_per == should_be_per
    
    if is_correct:
        correct += 1
        status = "✓"
    else:
        status = "✗"
    
    print(f"\n{status} '{text[:50]}'")
    print(f"   Expected PER={should_be_per}, Got={has_per}")
    if entities:
        for start, end, label in entities:
            print(f"   → {text[start:end]:30s} ({label})")

print(f"\n{'='*80}")
print(f"ACCURACY: {correct}/{total} ({100*correct/total:.1f}%)")
print(f"{'='*80}")
