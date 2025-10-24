import pandas as pd
from .utils import SELLMEIER_MODEL_1 # Importamos la constante

def load_oscillator_data(filepath):
    try:
        osc_data = pd.read_csv(filepath, sep=r'\s+')
        wavelengths_nm = osc_data.iloc[:, 0].values
        sample_names = osc_data.columns[1:].tolist()
        f_exp_all_samples = osc_data.iloc[:, 1:].values
        if f_exp_all_samples.ndim == 1:
            f_exp_all_samples = f_exp_all_samples.reshape(-1, 1)
        return wavelengths_nm, f_exp_all_samples, sample_names
    except Exception as e:
        raise ValueError(f"Error cargando archivo de oscilador: {e}")

def load_abs_matrix_elements(filepath):
    try:
        return pd.read_csv(filepath, delim_whitespace=True, header=None).to_numpy()
    except Exception as e:
        raise ValueError(f"Error cargando matriz de absorción: {e}")

def load_emission_matrix_elements(filepath):
    from .utils import get_level_name_slug
    try:
        df = pd.read_csv(filepath, delim_whitespace=True, header=None)
        df.columns = ['J_initial', 'L_initial', 'S_initial','J_final', 'L_final', 'S_final',
                      'wavenumber_cm_1', 'U2', 'U4', 'U6']
        df['Initial_Name_Slug'] = df.apply(lambda r: get_level_name_slug(r['J_initial'], r['L_initial'], r['S_initial']), axis=1)
        df['Final_Name_Slug'] = df.apply(lambda r: get_level_name_slug(r['J_final'], r['L_final'], r['S_final']), axis=1)
        return df
    except Exception as e:
        raise ValueError(f"Error cargando matriz de emisión: {e}")

def get_available_transitions(em_matrix_df):
    from .utils import PRETTY_NAMES
    if em_matrix_df is None: return {}
    unique_slugs = em_matrix_df['Initial_Name_Slug'].unique()
    transitions = {slug: PRETTY_NAMES.get(slug, slug) for slug in unique_slugs}
    return dict(sorted(transitions.items(), key=lambda item: item[1]))

def load_sellmeier_coeffs(filepath, model_type):
    """
    Carga y VALIDA los coeficientes de Sellmeier según el modelo seleccionado,
    infiriendo el número de coeficientes del propio archivo.
    """
    try:
        df = pd.read_csv(filepath, delim_whitespace=True)
        
        # --- LÓGICA DE VALIDACIÓN ACTUALIZADA ---
        num_coeff_cols = len(df.columns) - 1 # Resta la columna 'Sample'
        
        is_model1 = (model_type == SELLMEIER_MODEL_1)
        is_even = (num_coeff_cols % 2 == 0)

        # Validación de Paridad:
        # Modelo 1 (n²=1+...) espera un número PAR de coeficientes (B1,C1, B2,C2...)
        # Modelo 2 (n²=A+...) espera un número IMPAR de coeficientes (A, B1,C1, B2,C2...)
        if is_model1 and not is_even:
            raise ValueError(
                f"Para el modelo '{model_type}', se esperaba un número PAR de coeficientes, "
                f"pero el archivo tiene {num_coeff_cols}."
            )
        if not is_model1 and is_even:
            raise ValueError(
                f"Para el modelo '{model_type}', se esperaba un número IMPAR de coeficientes, "
                f"pero el archivo tiene {num_coeff_cols}."
            )
        
        if num_coeff_cols < 1:
            raise ValueError("El archivo de Sellmeier no contiene columnas de coeficientes.")
        
        # --- FIN DE LÓGICA DE VALIDACIÓN ---
        
        df = df.set_index(df.columns[0])
        return {index: row.tolist() for index, row in df.iterrows()}
        
    except Exception as e:
        raise ValueError(f"Error procesando coeficientes de Sellmeier: {e}")

def load_emission_spectrum(filepath):
    try:
        df = pd.read_csv(filepath, sep=r'\s+', names=['wavelength_nm', 'intensity'], comment='#').apply(pd.to_numeric, errors='coerce').dropna()
        if df.empty: return None
        return df
    except Exception:
        return None