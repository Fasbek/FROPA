"""
Utilidades, constantes y mapeos de nombres para el proyecto.
"""

# Mapeo de "slugs" internos a nombres "bonitos" para reportes
PRETTY_NAMES = {
    '2H11/2': '²H₁₁/₂',
    '4S3/2': '⁴S₃/₂',
    '4F9/2': '⁴F₉/₂',
    '4F7/2': '⁴F₇/₂',
    '4F5/2': '⁴F₅/₂',
    '4I9/2': '⁴I₉/₂',
    '4I11/2': '⁴I₁₁/₂',
    '4I13/2': '⁴I₁₃/₂',
    '4I15/2': '⁴I₁₅/₂'
}

# Lista blanca de transiciones de EMISIÓN permitidas para el análisis
ALLOWED_EMISSION_TRANSITIONS = {
    '2H11/2': ['4S3/2', '4F9/2', '4I9/2', '4I11/2', '4I13/2', '4I15/2'],
    '4S3/2': ['4F9/2', '4I9/2', '4I11/2', '4I13/2', '4I15/2'],
    '4F9/2': ['4I9/2', '4I11/2', '4I13/2', '4I15/2']
}

# Bandas de emisión a analizar para la sección eficaz
# EMISSION_BANDS_TO_ANALYZE = [
#     {'Level': '²H₁₁/₂ → ⁴I₁₅/₂', 'SLJ': '2H11/2', "S'L'J'": '4I15/2', 'range': (511, 533)},
#     {'Level': '⁴S₃/₂ → ⁴I₁₅/₂',  'SLJ': '4S3/2', "S'L'J'": '4I15/2', 'range': (533, 564)},
#     {'Level': '⁴F₉/₂ → ⁴I₁₅/₂',  'SLJ': '4F9/2', "S'L'J'": '4I15/2', 'range': (640, 680)},
#     {'Level': '⁴I₁₃/₂ → ⁴I₁₅/₂',  'SLJ': '4I13/2', "S'L'J'": '4I15/2', 'range': (1450, 1650)}
# ]

def get_level_name_slug(J, L, S):
    """
    Genera un 'slug' de texto simple (ej. '4I15/2') para un nivel de energía,
    usando los mapeos especiales definidos.
    """
    multiplicity = int(round(2 * S + 1))
    L_char_map = ['S', 'P', 'D', 'F', 'G', 'H', 'I']
    L_int = int(round(L))
    L_char = L_char_map[L_int] if L_int < len(L_char_map) else '?'
    J_num_str = str(int(2 * J))
    
    # Casos especiales (basados en tu script original)
    if J == 5.5 and S == 0.5 and L_int == 5: return '2H11/2'
    if J == 1.5 and S == 1.5 and L_int == 0: return '4S3/2'
    if J == 4.5 and S == 1.5 and L_int == 3: return '4F9/2'
    if J == 3.5 and S == 1.5 and L_int == 3: return '4F7/2'
    if J == 2.5 and S == 1.5 and L_int == 3: return '4F5/2'
    if J == 4.5 and S == 1.5 and L_int == 6: return '4I9/2'
    if J == 5.5 and S == 1.5 and L_int == 6: return '4I11/2'
    if J == 6.5 and S == 1.5 and L_int == 6: return '4I13/2'
    if J == 7.5 and S == 1.5 and L_int == 6: return '4I15/2'
    
    return f'{multiplicity}{L_char}{J_num_str}/2'

# --- NUEVO: Constantes para Modelos de Sellmeier ---
# Modelo con un número PAR de coeficientes
SELLMEIER_MODEL_1 = "n² = 1 + Σ [Bᵢ / (1 - Cᵢ/λ²)]"
# Modelo con un número IMPAR de coeficientes
SELLMEIER_MODEL_2 = "n² = A + Σ [Bᵢ / (1 - Cᵢ/λ²)]"