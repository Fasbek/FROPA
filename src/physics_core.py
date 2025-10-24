import numpy as np
import pandas as pd
import os

def _calculate_A_rad_specific(initial_slug, final_slug, omegas, coeffs, em_df, sm):
    """
    Función interna para calcular A(J->J') para UNA SOLA transición específica bajo demanda.
    """
    from .constants import H, E, PI
    
    # Encuentra todas las contribuciones J-J' para la transición de nivel a nivel
    trans_group = em_df[(em_df['Initial_Name_Slug'] == initial_slug) & (em_df['Final_Name_Slug'] == final_slug)]
    if trans_group.empty:
        return 0

    A_ed_total, A_md_total = 0, 0
    J_init = trans_group['J_initial'].iloc[0]

    for _, row in trans_group.iterrows():
        nu, U_sq = row['wavenumber_cm_1'], row[['U2', 'U4', 'U6']].to_numpy()
        n = calculate_refractive_index(1e7 / nu, coeffs, sm)
        t_const = (64 * PI**4 * nu**3) / (3 * H * (2 * J_init + 1))
        
        S_ed = E**2 * np.sum(omegas * U_sq)
        A_ed_total += (t_const * ((n * (n**2 + 2)**2) / 9)) * S_ed
        
        # S_md = SMD(row['J_initial'], row['L_initial'], row['S_initial'],
        #            row['J_final'], row['L_final'], row['S_final'], nu)
        S_md = SMD(row['J_initial'], row['L_initial'], row['S_initial'],
                   row['J_final'], row['L_final'], row['S_final'])
        A_md_total += t_const * (n**3) * S_md
        
    return A_ed_total + A_md_total

def calculate_refractive_index(wavelength_nm, coeffs_list, model_type):
    from .utils import SELLMEIER_MODEL_1
    is_scalar, wl_arr = np.isscalar(wavelength_nm), np.atleast_1d(wavelength_nm)
    sum_term = 0.0
    if model_type == SELLMEIER_MODEL_1:
        base, loop_coeffs = 1.0, coeffs_list
    else:
        base, loop_coeffs = coeffs_list[0], coeffs_list[1:]
    for i in range(0, len(loop_coeffs), 2):
        B, C = loop_coeffs[i], loop_coeffs[i + 1]
        sum_term += B / (1 - C / wl_arr**2)
    result = np.sqrt(base + sum_term)
    return result[0] if is_scalar else result

def calculate_S_ed_exp(wavelengths, f_exp, n_values):
    from .constants import H, C, M, PI
    J_ground = 15/2; wl_cm = np.array(wavelengths) * 1e-7
    num = 3*H*wl_cm*(2*J_ground+1)*9*np.array(n_values)*np.array(f_exp)
    den = 8*PI**2*M*C*(np.array(n_values)**2+2)**2
    with np.errstate(divide='ignore', invalid='ignore'): S_ed = num/den
    return np.nan_to_num(S_ed)

def perform_jo_fit(S_ed_exp, abs_matrix_elements):
    omegas, _, _, _ = np.linalg.lstsq(abs_matrix_elements, S_ed_exp, rcond=None)
    rms = np.sqrt(np.sum((S_ed_exp - np.dot(abs_matrix_elements, omegas))**2) / (len(S_ed_exp) - 3))
    return omegas, rms

# def SMD(J1, L1, S1, J2, L2, S2, ν):
#     from .constants import H, C, E, PI
#     if J1==J2 and S1==S2 and L1==L2:
#         t1=(J1*(J1+1)+S1*(S1+1)-L1*(L1+1))/(2*J1*(J1+1)); t2=(J1*(J1+1)*(2*J1+1))**2/(4*PI*E*H*C)
#         return t1*t2
#     elif J2==J1-1 and S1==S2 and L1==L2:
#         t1=((S1+L1+J1-L1-S1)*(L1+J1-S1+L1))/(4*J1*(J1+1))
#         return t1*np.exp(-ν)
#     return 0

def SMD(J1, L1, S1, J2, L2, S2):
    """
    Calcula la fuerza de línea teórica de dipolo magnético (S_md).
    Implementa las reglas de selección ΔL=0, ΔS=0, ΔJ=0,±1.
    """
    from .constants import H, C, M, E, PI

    # --- CORRECCIÓN: Lógica de SMD reescrita ---
    # Reglas de selección principales
    if S1 != S2 or L1 != L2 or (J1 == 0 and J2 == 0):
        return 0

    # Constante pre-factor de Bohr Magneton al cuadrado en unidades cgs
    # μ_B² = (eħ / 2mc)² = (e * (h/2π) / 2mc)²
    mu_B_sq = ((E * H) / (4 * PI * M * C))**2

    # Matriz de elemento al cuadrado |<L,S,J || L+2S || L,S,J'>|²
    if J2 == J1: # ΔJ = 0
        if J1 == 0: return 0 # J=0 a J=0 prohibido
        g = 1 + (J1*(J1+1) + S1*(S1+1) - L1*(L1+1)) / (2*J1*(J1+1))
        matrix_element_sq = g**2 * J1 * (J1+1) * (2*J1+1)
    elif J2 == J1 - 1: # ΔJ = -1
        matrix_element_sq = ((S1+L1+1)**2 - J1**2) * (J1**2 - (L1-S1)**2) / (4*J1)
    elif J2 == J1 + 1: # ΔJ = +1 (CASO FALTANTE)
        matrix_element_sq = ((S1+L1+1)**2 - (J1+1)**2) * ((J1+1)**2 - (L1-S1)**2) / (4*(J1+1))
    else: # ΔJ > 1
        return 0

    return mu_B_sq * matrix_element_sq

def calculate_radiative_properties(omegas, coeffs, em_df, sm, sel_levels):
    from .constants import H, E, PI
    results = []
    for level_name in sel_levels:
        trans = em_df[em_df['Initial_Name_Slug'] == level_name]
        if trans.empty: continue
        groups = trans.groupby('Final_Name_Slug')
        A_total, temp_calcs = 0, []
        for f_name, group in groups:
            A_ed, A_md = 0, 0
            J_init = group['J_initial'].iloc[0]
            for _, row in group.iterrows():
                nu, U_sq = row['wavenumber_cm_1'], row[['U2', 'U4', 'U6']].to_numpy()
                n = calculate_refractive_index(1e7/nu, coeffs, sm)
                t_const = (64*PI**4*nu**3)/(3*H*(2*J_init+1))
                S_ed = E**2 * np.sum(omegas * U_sq)
                A_ed += (t_const*((n*(n**2+2)**2)/9))*S_ed
                # S_md = SMD(row['J_initial'],row['L_initial'],row['S_initial'],row['J_final'],row['L_final'],row['S_final'],nu)
                S_md_val = SMD(row['J_initial'],row['L_initial'],row['S_initial'],row['J_final'],row['L_final'],row['S_final'])
                A_md += t_const*(n**3)*S_md_val
            A_trans = A_ed + A_md
            temp_calcs.append({'SLJ': level_name, "S'L'J'": f_name, 'A_ed': A_ed, 'A_md': A_md, 'A': A_trans})
            A_total += A_trans
        if A_total > 0:
            for calc in temp_calcs:
                results.append({**calc, 'β_R (%)':(calc['A']/A_total)*100, 'A_T (s⁻¹)':A_total, 'τ_R (ms)':(1/A_total)*1000})
    if results:
        df = pd.DataFrame(results)
        cols = ['SLJ', "S'L'J'", 'A_ed', 'A_md', 'A', 'β_R (%)', 'A_T (s⁻¹)', 'τ_R (ms)']
        return df.reindex(columns=[col for col in cols if col in df.columns])
    return pd.DataFrame()

def calculate_emission_cross_section(em_spectrum_df, band_info, A_rad, coeffs, sm):
    from .constants import C, PI
    band = em_spectrum_df[(em_spectrum_df['wavelength_nm']>=band_info['range_min'])&(em_spectrum_df['wavelength_nm']<=band_info['range_max'])].copy()
    if band.empty or len(band)<2: return None
    band['n'] = calculate_refractive_index(band['wavelength_nm'], coeffs, sm)
    band['lambda_cm'] = band['wavelength_nm']*1e-7
    den_int = np.trapz(band['lambda_cm']*band['intensity']*(band['n']**2), x=band['lambda_cm'])
    if den_int==0: return None
    max_idx = band['intensity'].idxmax()
    max_I, max_lam_cm = band.loc[max_idx, 'intensity'], band.loc[max_idx, 'lambda_cm']
    num = A_rad*(max_lam_cm**5)*max_I; den = 8*PI*C*den_int
    sigma = num/den
    if not np.isfinite(sigma): return None
    E_exp, int_I_nm = 1/max_lam_cm, np.trapz(band['intensity'], x=band['wavelength_nm'])
    d_lam = int_I_nm/max_I if max_I>0 else 0; d_G = sigma*(d_lam*1e-7)
    return {'Level': f"{band_info['initial']} → {band_info['final']}", 'E_exp (cm⁻¹)':E_exp, 'Δλ_eff (nm)':d_lam, 'σₑ (x10⁻²¹ cm²)':sigma*1e21, 'ΔG (x10⁻²⁸ cm³)':d_G*1e28}

def run_full_analysis(p_osc, p_abs, p_sell, p_em_dir, sm,
                      do_rad_calc, p_em, sel_trans_rad,
                      do_cs_calc, user_bands):
    from . import data_io
    wl, f_exp, s_names = data_io.load_oscillator_data(p_osc)
    abs_mx = data_io.load_abs_matrix_elements(p_abs)
    sell_co = data_io.load_sellmeier_coeffs(p_sell, sm)
    if wl is None or abs_mx is None or sell_co is None: raise ValueError("Error cargando archivos principales.")
    jo_res, rad_sum, cs_res = [], {}, []
    em_mx = data_io.load_emission_matrix_elements(p_em) if (do_rad_calc or do_cs_calc) and p_em and os.path.exists(p_em) else None

    for i, s_name in enumerate(s_names):
        coeffs = sell_co.get(s_name.replace('TZGE','TZGNE'), sell_co.get(s_name))
        if coeffs is None: continue
        n_vals = calculate_refractive_index(wl, coeffs, sm)
        omegas, rms = perform_jo_fit(calculate_S_ed_exp(wl, f_exp[:, i], n_vals), abs_mx)
        jo_res.append({"Sample":s_name, "Ω2 (x10⁻²⁰)":omegas[0]*1e20, "Ω4 (x10⁻²⁰)":omegas[1]*1e20, "Ω6 (x10⁻²⁰)":omegas[2]*1e20, "Ω4/Ω6":omegas[1]/omegas[2], "δ_rms (x10⁻²⁰)":rms*1e20})

        if do_rad_calc and em_mx is not None:
            rad_sum[s_name] = calculate_radiative_properties(omegas, coeffs, em_mx, sm, sel_trans_rad)
        else:
            rad_sum[s_name] = pd.DataFrame()

        if do_cs_calc and em_mx is not None and user_bands:
            em_f = os.path.join(p_em_dir, f'emision_{s_name.replace("TZGE","TZGNE",1)}.txt')
            if not os.path.exists(em_f): em_f = os.path.join(p_em_dir, f'emision_{s_name}.txt')
            if not os.path.exists(em_f): continue
            em_spectrum_df = data_io.load_emission_spectrum(em_f)
            if em_spectrum_df is None: continue

            for band in user_bands:
                A_rad_specific = 0
                rad_props_df = rad_sum.get(s_name, pd.DataFrame())
                if not rad_props_df.empty:
                    trans_data = rad_props_df[(rad_props_df['SLJ'] == band['initial_slug']) & (rad_props_df["S'L'J'"] == band['final_slug'])]
                    if not trans_data.empty:
                        A_rad_specific = trans_data['A'].iloc[0]
                
                if A_rad_specific == 0:
                    A_rad_specific = _calculate_A_rad_specific(band['initial_slug'], band['final_slug'], omegas, coeffs, em_mx, sm)

                if A_rad_specific > 0:
                    analysis = calculate_emission_cross_section(em_spectrum_df, band, A_rad_specific, coeffs, sm)
                    if analysis:
                        analysis.update({'Glass':s_name, 'λ_ex (nm)':980}); cs_res.append(analysis)
    return jo_res, rad_sum, cs_res