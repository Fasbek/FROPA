"""
Script principal para ejecutar el análisis de Judd-Ofelt.
Este script importa los módulos de E/S y de física para orquestar el flujo de trabajo.
"""
import pandas as pd
from .data_io import (load_oscillator_data, load_abs_matrix_elements, 
                     load_emission_matrix_elements, load_sellmeier_coeffs,
                     load_emission_spectrum)
from .physics_core import (calculate_refractive_index, calculate_S_ed_exp, 
                          perform_jo_fit, calculate_radiative_properties,
                          calculate_emission_cross_section)
from .utils import EMISSION_BANDS_TO_ANALYZE, PRETTY_NAMES

# --- 0. Definición de Rutas de Archivos ---
# (Relativas a la carpeta raíz 'JuddOfelt_Analyzer')
PATH_OSC = 'data_original/Oscillator_Er.txt'
PATH_ABS_MATRIX = 'data_original/AbsMatrixElements_Er_C1968.txt'
PATH_EM_MATRIX = 'data_original/EmMatrixElements_Er.txt'
PATH_SELLMEIER = 'data_original/Sellmeier.txt'
PATH_EMISSION_PREFIX = 'data_original/emision_'


def main():
    print("Iniciando análisis de Judd-Ofelt...")

    # --- 1. CARGA DE DATOS COMUNES ---
    print("Cargando archivos de datos base...")
    wavelengths_nm, f_exp_all_samples, sample_names = load_oscillator_data(PATH_OSC)
    abs_matrix_elements = load_abs_matrix_elements(PATH_ABS_MATRIX)
    em_matrix_df = load_emission_matrix_elements(PATH_EM_MATRIX)
    sellmeier_all_samples = load_sellmeier_coeffs(PATH_SELLMEIER)

    if wavelengths_nm is None or abs_matrix_elements is None or em_matrix_df is None or sellmeier_all_samples is None:
        print("Error fatal: No se pudieron cargar los archivos base. Terminando.")
        return

    print(f"Muestras detectadas: {sample_names}")

    # Listas para almacenar resultados de todas las muestras
    judd_ofelt_results = []
    all_rad_summaries = {}
    cross_section_results = []

    # --- 2. BUCLE PRINCIPAL DE ANÁLISIS POR MUESTRA ---
    for i, sample_name in enumerate(sample_names):
        print(f"\n--- Procesando muestra: {sample_name} ---")
        
        if sample_name not in sellmeier_all_samples:
            print(f"  AVISO: No se encontraron coeficientes de Sellmeier para '{sample_name}'. Saltando esta muestra.")
            continue
        
        coeffs = sellmeier_all_samples[sample_name]

        # --- a) Ajuste de Parámetros de Judd-Ofelt ---
        n_values_abs = calculate_refractive_index(wavelengths_nm, coeffs)
        S_ed_exp = calculate_S_ed_exp(wavelengths_nm, f_exp_all_samples[:, i], n_values_abs)
        
        omega_params, S_ed_calc, rms_dev = perform_jo_fit(S_ed_exp, abs_matrix_elements)

        judd_ofelt_results.append({
            "Sample": sample_name, 
            "Ω2 (x10⁻²⁰)": omega_params[0] * 1e20, 
            "Ω4 (x10⁻²⁰)": omega_params[1] * 1e20,
            "Ω6 (x10⁻²⁰)": omega_params[2] * 1e20, 
            "Ω4/Ω6": omega_params[1] / omega_params[2], 
            "δ_rms (x10⁻²⁰)": rms_dev * 1e20
        })

        # --- b) Cálculo de Propiedades Radiativas ---
        rad_props_detailed = calculate_radiative_properties(omega_params, coeffs, em_matrix_df)
        
        if rad_props_detailed.empty:
            print("  AVISO: No se pudieron calcular las propiedades radiativas.")
            continue
            
        all_rad_summaries[sample_name] = rad_props_detailed
        output_filename = f'propiedades_radiativas_resumen_{sample_name}.csv'
        rad_props_detailed.to_csv(output_filename, index=False, float_format='%.4e')
        print(f"  > Propiedades radiativas guardadas en: {output_filename}")

        # --- c) Análisis de Sección Eficaz de Emisión ---
        emission_file = f'{PATH_EMISSION_PREFIX}{sample_name}.txt'
        full_emission_df = load_emission_spectrum(emission_file)
        
        if full_emission_df is None:
            print("  Saltando análisis de sección eficaz para esta muestra.")
            continue

        print("  Calculando secciones eficaces de emisión...")
        for trans_info in EMISSION_BANDS_TO_ANALYZE:
            # Buscar la tasa radiativa (A_rad) calculada para esta transición
            trans_data = rad_props_detailed[
                (rad_props_detailed['SLJ'] == trans_info['SLJ']) & 
                (rad_props_detailed["S'L'J'"] == trans_info["S'L'J'"])
            ]
            
            if not trans_data.empty:
                A_rad = trans_data['A'].iloc[0]
                analysis_results = calculate_emission_cross_section(full_emission_df, trans_info, A_rad, coeffs)
                
                if analysis_results:
                    analysis_results['Glass'] = sample_name
                    analysis_results['λ_ex (nm)'] = 980 # Esto podría ser un parámetro de entrada
                    cross_section_results.append(analysis_results)
            else:
                print(f"  AVISO: No se encontró A_rad para la transición {trans_info['Level']}. No se puede calcular sigma_e.")

    # --- 3. REPORTE FINAL ---
    print_final_reports(judd_ofelt_results, all_rad_summaries, cross_section_results)


def print_final_reports(jo_results, rad_summaries, cs_results):
    """Imprime y guarda los DataFrames finales con los resultados."""
    
    # Reporte 1: Parámetros de Judd-Ofelt
    print("\n\n" + "="*80)
    print("--- PARÁMETROS DE JUDD-OFELT CALCULADOS ---")
    print("="*80)
    df_jo = pd.DataFrame(jo_results)
    print(df_jo.to_string(index=False, float_format="%.4f"))
    df_jo.to_csv('judd_ofelt_parametros_resumen.csv', index=False, float_format='%.4e')
    print("\n> Reporte de parámetros J-O guardado en 'judd_ofelt_parametros_resumen.csv'")

    # Reporte 2: Propiedades Radiativas (una tabla por muestra)
    for sample_name, final_df in rad_summaries.items():
        print("\n\n" + "="*80)
        print(f"--- PROPIEDADES RADIATIVAS (Muestra: {sample_name}) ---")
        print("="*80)
        # Reemplazar slugs por nombres bonitos para el reporte
        final_df_pretty = final_df.copy()
        final_df_pretty['SLJ'] = final_df_pretty['SLJ'].map(PRETTY_NAMES).fillna(final_df_pretty['SLJ'])
        final_df_pretty["S'L'J'"] = final_df_pretty["S'L'J'"].map(PRETTY_NAMES).fillna(final_df_pretty["S'L'J'"])
        print(final_df_pretty.to_string(index=False, float_format="%.2f"))

    # Reporte 3: Resumen de Sección Eficaz
    if cs_results:
        print("\n\n" + "="*80)
        print("--- TABLA RESUMEN DE SECCIÓN EFICAZ DE EMISIÓN ESTIMULADA ---")
        print("="*80)
        
        final_df_cs = pd.DataFrame(cs_results)
        # Reordenar columnas
        cols = ['λ_ex (nm)', 'Glass', 'Level', 'E_exp (cm⁻¹)', 'Δλ_eff (nm)', 'σₑ (x10⁻²¹ cm²)', 'ΔG (x10⁻²⁸ cm³)']
        final_df_cs = final_df_cs[cols]
        
        print(final_df_cs.to_string(index=False, float_format="%.4f"))
        
        final_output_filename = 'tabla_resumen_seccion_eficaz.csv'
        final_df_cs.to_csv(final_output_filename, index=False, float_format='%.4e')
        print(f"\n> Tabla de resumen de sección eficaz guardada en: {final_output_filename}")


if __name__ == "__main__":
    # Esta línea permite que el script sea ejecutado directamente
    main()
