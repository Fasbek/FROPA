import tkinter as tk
from tkinter import ttk, filedialog, messagebox, font
import os
import numpy as np
import pandas as pd
import sys
import traceback

# --- Setup de Path y Recursos ---
project_root = os.path.dirname(os.path.abspath(__file__))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

def resource_path(relative_path):
    try:
        base_path = sys._MEIPASS
    except Exception:
        base_path = os.path.abspath(".")
    return os.path.join(base_path, relative_path)

try:
    from src.utils import PRETTY_NAMES, SELLMEIER_MODEL_1, SELLMEIER_MODEL_2
    from src.data_io import get_available_transitions, load_emission_matrix_elements
except ImportError as e:
    messagebox.showerror("Error de Importación", f"No se pudo importar 'src'.\nDetalles:\n{e}")
    sys.exit()

class ResultsWindow(tk.Toplevel):
    def __init__(self, parent, jo, rad, cs, conf):
        super().__init__(parent)
        self.title("FROPA - Reporte de Resultados")
        self.geometry("1100x700")
       
        # --- Guardar referencias a los datos para exportación ---
        self.jo_raw_data = jo
        self.rad_raw_data = rad
        self.cs_raw_data = cs
        self.conf = conf
        # --------------------------------------------------------------
        
        try:
            # Usamos la función resource_path que ya tienes definida
            self.iconbitmap(resource_path("icon.ico"))
        except Exception:
            # Si falla (ej. en Linux o si no encuentra el archivo), que no detenga el programa
            pass
        
        # --- CONTENEDOR SUPERIOR PARA EL BOTÓN ---
        header_frame = ttk.Frame(self)
        header_frame.pack(fill=tk.X, padx=10, pady=(5, 0))

        # Botón de exportar en la esquina superior derecha
        ttk.Button(header_frame, text="📥 Exportar Tablas Individuales (.txt)", 
                   command=self.export_individual_tables).pack(side=tk.RIGHT)
        
        nb = ttk.Notebook(self)
        nb.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

        # Siempre mostrar Judd-Ofelt y Fuerzas (son la base)
        t1 = ttk.Frame(nb); nb.add(t1, text="Parámetros Ωλ")
        df_jo = pd.DataFrame(jo)[["Sample", "Ω2", "Ω4", "Ω6", "rms_S"]]
        df_jo.columns = ["Muestra", "Ω2", "Ω4", "Ω6", "δ_rms (S)"]
        self.create_table(t1, df_jo)

        t2 = ttk.Frame(nb); nb.add(t2, text="Fuerzas de Oscilador")
        canvas = tk.Canvas(t2)
        scrollbar_t2 = ttk.Scrollbar(t2, orient="vertical", command=canvas.yview)
        container_f = ttk.Frame(canvas)
        
        container_f.bind("<Configure>", lambda e: canvas.configure(scrollregion=canvas.bbox("all")))
        canvas.create_window((0, 0), window=container_f, anchor="nw")
        canvas.configure(yscrollcommand=scrollbar_t2.set)
        
        canvas.pack(side="left", fill="both", expand=True)
        scrollbar_t2.pack(side="right", fill="y")
        
        for res in jo:
            # Restauramos la etiqueta con los errores del ajuste
            info_txt = f"Muestra: {res['Sample']} | δ_rms: {res['rms_f']:.4f} | Δ_RMS: {res['rms_perc']:.2f}%"
            lbl = ttk.Label(container_f, text=info_txt, font=('Arial', 10, 'bold'))
            lbl.pack(pady=(10,0), anchor="w", padx=10)
            self.create_table(container_f, res['f_table'], height=11)

        # CONDICIONAL: Solo mostrar si se seleccionó "Propiedades Radiativas"
        if conf.get("do_rad") and rad:
            t3 = ttk.Frame(nb); nb.add(t3, text="Prop. Radiativas")
            
            # --- IMPLEMENTACIÓN DE SCROLL GLOBAL ---
            canvas_t3 = tk.Canvas(t3)
            scrollbar_t3 = ttk.Scrollbar(t3, orient="vertical", command=canvas_t3.yview)
            container_rad = ttk.Frame(canvas_t3)
            
            container_rad.bind("<Configure>", lambda e: canvas_t3.configure(scrollregion=canvas_t3.bbox("all")))
            canvas_t3.create_window((0, 0), window=container_rad, anchor="nw")
            canvas_t3.configure(yscrollcommand=scrollbar_t3.set)
            
            canvas_t3.pack(side="left", fill="both", expand=True)
            scrollbar_t3.pack(side="right", fill="y")
            # ---------------------------------------
            
            for s_name, df in rad.items():
                if not df.empty:
                    # Añadimos el Label y la Tabla al 'container_rad' para que se muevan con el scroll
                    ttk.Label(container_rad, text=f"Muestra: {s_name}", font=('Arial', 10, 'bold')).pack(pady=(10, 0), padx=10, anchor="w")
                    
                    # Preparar nombres bonitos (Pretty Names)
                    df_pretty = df.copy()
                    from src.utils import PRETTY_NAMES
                    df_pretty['SLJ'] = df_pretty['SLJ'].map(PRETTY_NAMES).fillna(df_pretty['SLJ'])
                    df_pretty["S'L'J'"] = df_pretty["S'L'J'"].map(PRETTY_NAMES).fillna(df_pretty["S'L'J'"])
                    
                    # Insertar la tabla en el contenedor con scroll
                    self.create_table(container_rad, df_pretty)

        # CONDICIONAL: Solo mostrar si se seleccionó "Sección Eficaz"
        if conf.get("do_cs") and cs:
            t4 = ttk.Frame(nb); nb.add(t4, text="Sección Eficaz")
            df_cs = pd.DataFrame(cs)
            cols = ['λ_ex (nm)', 'Glass', 'Level', 'E_exp (cm⁻¹)', 'Δλ_eff (nm)', 'σₑ (x10⁻²¹ cm²)', 'ΔG (x10⁻²⁸ cm³)']
            self.create_table(t4, df_cs[cols])
            
        # # --- Panel de Botones Inferior ---
        # btn_frame = ttk.Frame(self, padding=10)
        # btn_frame.pack(fill=tk.X, side=tk.BOTTOM)

        # ttk.Button(btn_frame, text="Exportar Tablas Individuales (.txt)", 
        #            command=self.export_individual_tables).pack(side=tk.RIGHT, padx=5)

    # MODIFICACIÓN: Agregamos height=None como argumento opcional
    def create_table(self, parent, df, height=None):
        if df.empty: 
            ttk.Label(parent, text="Sin datos disponibles").pack(); return
        
        frame = ttk.Frame(parent)
        frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=5)
        
        # Si se pasa height, se aplica al Treeview
        if height:
            tree = ttk.Treeview(frame, columns=list(df.columns), show='headings', height=height)
        else:
            tree = ttk.Treeview(frame, columns=list(df.columns), show='headings')
            
        vsb = ttk.Scrollbar(frame, orient="vertical", command=tree.yview)
        hsb = ttk.Scrollbar(frame, orient="horizontal", command=tree.xview)
        tree.configure(yscrollcommand=vsb.set, xscrollcommand=hsb.set)

        for col in df.columns:
            tree.heading(col, text=col)
            tree.column(col, width=120, anchor="center")
        
        for _, row in df.iterrows():
            values = [f"{v:.4f}" if isinstance(v, (float, np.float64)) else v for v in row]
            tree.insert("", tk.END, values=values)

        tree.grid(row=0, column=0, sticky='nsew')
        vsb.grid(row=0, column=1, sticky='ns')
        hsb.grid(row=1, column=0, sticky='ew')
        frame.grid_columnconfigure(0, weight=1)
        frame.grid_rowconfigure(0, weight=1)
    
    def export_individual_tables(self):
        target_dir = filedialog.askdirectory(title="Seleccionar carpeta para exportar resultados")
        if not target_dir:
            return

        try:
            from src.utils import PRETTY_NAMES

            # 1. Exportar Parámetros Ωλ (Solo con rms_S)
            df_jo = pd.DataFrame(self.jo_raw_data)[["Sample", "Ω2", "Ω4", "Ω6", "rms_S"]]
            df_jo.columns = ["Muestra", "Omega2_x10-20", "Omega4_x10-20", "Omega6_x10-20", "rms_S_LineStrength"]
            df_jo.to_csv(os.path.join(target_dir, "JO_Parameters.txt"), 
                         sep='\t', index=False, float_format="%.4f")

            # 2. Exportar Fuerzas de Oscilador (Incluyendo sus propios RMS al final)
            for res in self.jo_raw_data:
                safe_name = "".join(x for x in res['Sample'] if x.isalnum() or x in "._-")
                f_path = os.path.join(target_dir, f"Oscillator_Strengths_{safe_name}.txt")
                
                with open(f_path, 'w', encoding='utf-8') as f:
                    # Escribimos la tabla principal
                    res['f_table'].to_csv(f, sep='\t', index=False, float_format="%.4f")
                    # Añadimos los errores específicos de esta muestra al final
                    f.write(f"\n# Indicadores de Calidad para {res['Sample']}:\n")
                    f.write(f"rms_f_Oscillator_Strength (x10-6):\t{res['rms_f']:.4f}\n")
                    f.write(f"RMS_Error_Total (%):\t{res['rms_perc']:.2f}\n")

            # 3. Exportar Propiedades Radiativas (Ajustando espaciado manual)
            if self.rad_raw_data:
                for s_name, df in self.rad_raw_data.items():
                    if not df.empty:
                        safe_name = "".join(x for x in s_name if x.isalnum() or x in "._-")
                        rad_path = os.path.join(target_dir, f"Radiative_Props_{safe_name}.txt")
                        
                        df_exp = df.copy()
                        df_exp['SLJ'] = df_exp['SLJ'].map(PRETTY_NAMES).fillna(df_exp['SLJ'])
                        df_exp["S'L'J'"] = df_exp["S'L'J'"].map(PRETTY_NAMES).fillna(df_exp["S'L'J'"])
                        
                        # Usamos to_string para que Pandas calcule el espaciado exacto por columnas
                        # y luego lo guardamos como texto para que se vea alineado en cualquier editor
                        content = df_exp.to_string(index=False, justify='left', float_format=lambda x: f"{x:.4f}")
                        with open(rad_path, 'w', encoding='utf-8') as f:
                            f.write(content)

            # 4. Exportar Sección Eficaz (Alineación consistente)
            if self.cs_raw_data:
                df_cs = pd.DataFrame(self.cs_raw_data)
                cols = ['λ_ex (nm)', 'Glass', 'Level', 'E_exp (cm⁻¹)', 'Δλ_eff (nm)', 'σₑ (x10⁻²¹ cm²)', 'ΔG (x10⁻²⁸ cm³)']
                content_cs = df_cs[cols].to_string(index=False, justify='left', float_format=lambda x: f"{x:.4f}")
                with open(os.path.join(target_dir, "Cross_Sections.txt"), 'w', encoding='utf-8') as f:
                    f.write(content_cs)

            messagebox.showinfo("Éxito", "Tablas exportadas con alineación corregida y asignación de errores correcta.")
        
        except Exception as e:
            messagebox.showerror("Error", f"No se pudo exportar la data: {e}")
        
# --- CLASE PRINCIPAL ---
class JuddOfeltApp:
    def __init__(self, root):
        self.valid_samples = []      # Etiquetas extraídas del archivo de osciladores
        self.emission_files = {}     # Diccionario { 'Etiqueta': 'Ruta/archivo.txt' }
        self.cs_checkbox = None
        self.root = root
        self.root.title("FROPA – Fluorescence Radiative and Optical Parameter Analyzer v1.2.1")
        self.root.geometry("800x850")
        self.lambda_ex_var = tk.DoubleVar(value=980.0) # Valor por defecto
        try:
            self.root.iconbitmap(resource_path("icon.ico"))
        except Exception: pass
        self.path_vars = {n: tk.StringVar() for n in ["osc","abs","sell","em_dir","em_user"]}
        self.calc_vars = {"rad":tk.BooleanVar(value=False), "cs":tk.BooleanVar(value=False)}
        self.em_source_var, self.sellmeier_model = tk.StringVar(value="internal"), tk.StringVar(value=SELLMEIER_MODEL_1)
        self.trans_vars, self.user_bands, self.results_win = {}, [], None
        self.calc_vars["rad"].trace("w", self.toggle_options)
        self.calc_vars["cs"].trace("w", self.toggle_options)
        self.em_source_var.trace("w", self.on_em_source_change)
        mf = ttk.Frame(self.root, padding="10")
        mf.pack(fill=tk.BOTH, expand=True)
        self.setup_ui(mf)
        self.toggle_options()
        self.log("Configure su análisis y presione 'Ejecutar'.")

    def load_oscillator_file(self):
        path = filedialog.askopenfilename(filetypes=[("Archivos de Texto", "*.txt")])
        if path:
            try:
                # Leemos solo la cabecera para extraer etiquetas
                df = pd.read_csv(path, sep=r'\s+', nrows=0)
                # La primera columna es 'Band', las demás son etiquetas de muestras
                self.valid_samples = df.columns[1:].tolist()
                
                if not self.valid_samples:
                    raise ValueError("No se detectaron columnas de muestras en el archivo.")
                
                self.path_vars["osc"].set(path)
                self.log(f"Archivo de Osciladores cargado.\nMuestras identificadas: {', '.join(self.valid_samples)}")
            except Exception as e:
                messagebox.showerror("Error de Formato", f"El archivo de osciladores no es válido:\n{e}")
                
    def load_emission_files(self):
        if not self.valid_samples:
            messagebox.showwarning("Faltan Datos", "Primero cargue el archivo de Fuerzas de Oscilador para identificar las muestras.")
            return

        paths = filedialog.askopenfilenames(filetypes=[("Archivos de Texto", "*.txt")])
        if not paths:
            return

        for p in paths:
            fname = os.path.basename(p)
            # Buscamos si la etiqueta está contenida en el nombre del archivo
            match = next((s for s in self.valid_samples if s in fname), None)
            
            if match:
                self.emission_files[match] = p
                self.log(f"Espectro vinculado: {fname} -> Muestra {match}")
            else:
                messagebox.showerror("Muestra No Identificada", 
                    f"El archivo '{fname}' no coincide con ninguna muestra del archivo de osciladores.\n"
                    f"Muestras esperadas: {', '.join(self.valid_samples)}")
        
        # Actualizar indicadores en la interfaz
        count = len(self.emission_files)
        self.lbl_spectra_count.config(text=f"Espectros vinculados: {count}")
        # Mostrar solo los nombres de archivos vinculados
        self.update_spectra_status()
        nombres = [os.path.basename(f) for f in self.emission_files.values()]
        if hasattr(self, 'spectra_list_lbl'):
            self.spectra_list_lbl.config(text="Archivos: " + ", ".join(nombres))    
    
    def setup_ui(self, p):

        # Contenedor superior de 3 columnas
        top_container = ttk.Frame(p)
        top_container.pack(fill=tk.X, pady=5)
        
        # Columna 1: Nombres originales restaurados
        self.f1_container = ttk.Frame(top_container)
        self.f1_container.grid(row=0, column=0, sticky="nsew", padx=2)
        f1 = ttk.LabelFrame(self.f1_container, text="1. Archivos Principales", padding=10)
        f1.pack(fill=tk.BOTH, expand=True)
        self.create_file_input_row(f1, "Fuerza de Oscilador (.txt):", self.path_vars["osc"], 0)
        self.create_file_input_row(f1, "Matriz Absorción (.txt):", self.path_vars["abs"], 1)
        self.create_file_input_row(f1, "Coef. Sellmeier (.txt):", self.path_vars["sell"], 2)
        
        # Columna 2: Fuente de Emisión
        self.f2_container = ttk.LabelFrame(top_container, text="2. Fuente de Datos de Emisión", padding=5)
        self.f2_container.grid(row=0, column=1, sticky="nsew", padx=2)
        ttk.Radiobutton(self.f2_container, text="Usar datos internos (Kaminskii)", 
                        variable=self.em_source_var, value="internal").pack(anchor="w", pady=2)
        ttk.Radiobutton(self.f2_container, text="Cargar archivo propio:", 
                        variable=self.em_source_var, value="user").pack(anchor="w", pady=2)
        self.user_em_button = ttk.Button(self.f2_container, text="Cargar...", 
                                         command=self.load_user_em_matrix, width=10)
        self.user_em_button.pack(anchor="w", padx=20)

        # Columna 3: Botón Play Circular
        f3_container = ttk.Frame(top_container)
        f3_container.grid(row=0, column=2, sticky="nsew", padx=10)
        self.btn_play = tk.Button(f3_container, text="▶", font=("Arial", 28), 
                                  bg="#27ae60", fg="white", command=self.run_analysis,
                                  width=2, height=1, relief="raised", cursor="hand2", bd=4)
        self.btn_play.pack(expand=True)

        top_container.columnconfigure(0, weight=5)
        top_container.columnconfigure(1, weight=3)
        top_container.columnconfigure(2, weight=1)

        # Secciones inferiores
        self.setup_calc_config(p)
        self.setup_rad_options(p)
        self.setup_cs_options(p)
        # RESTAURACIÓN DEL LOG (Anclado abajo)
        self.setup_log_display(p)


    def log(self, msg):
        self.log_text.config(state=tk.NORMAL)
        self.log_text.delete(1.0, tk.END)
        self.log_text.insert(tk.END, msg)
        self.log_text.config(state=tk.DISABLED)
        self.root.update_idletasks()

    def setup_file_inputs(self, p):
        f = ttk.LabelFrame(p, text="1. Archivos Principales", padding=10)
        f.pack(fill=tk.BOTH, expand=True)
        # Usamos nombres cortos para ganar espacio horizontal
        self.create_file_input_row(f, "Oscilador:", self.path_vars["osc"], 0)
        self.create_file_input_row(f, "Absorción:", self.path_vars["abs"], 1)
        self.create_file_input_row(f, "Sellmeier:", self.path_vars["sell"], 2)

    def setup_em_source(self, p):
        f = ttk.LabelFrame(p, text="2. Fuente de Datos de Emisión", padding=10)
        f.pack(fill=tk.X, expand=False, pady=5)
        self.rad_internal = ttk.Radiobutton(f, text="Usar datos internos (Kaminskii)", variable=self.em_source_var, value="internal")
        self.rad_internal.grid(row=0, column=0, sticky="w", padx=5)
        user_em_f = ttk.Frame(f)
        user_em_f.grid(row=0, column=1, sticky="ew", padx=20)
        self.rad_user = ttk.Radiobutton(user_em_f, text="Cargar archivo propio:", variable=self.em_source_var, value="user")
        self.rad_user.pack(side=tk.LEFT)
        self.user_em_button = ttk.Button(user_em_f, text="Cargar...", command=self.load_user_em_matrix)
        self.user_em_button.pack(side=tk.LEFT, padx=5)
        f.columnconfigure(1, weight=1)

    def setup_calc_config(self, p):
        f = ttk.LabelFrame(p, text="3. Configuración General", padding=10)
        f.pack(fill=tk.X, expand=False, pady=5)
        
        f_left = ttk.Frame(f)
        f_left.grid(row=0, column=0, sticky="nsew", padx=5, pady=5)
        ttk.Label(f_left, text="Modelo de Sellmeier:").pack(anchor="w")
        ttk.Combobox(f_left, textvariable=self.sellmeier_model, 
                     values=[SELLMEIER_MODEL_1, SELLMEIER_MODEL_2], 
                     state="readonly", width=30).pack(anchor="w", fill=tk.X)
        
        f_right = ttk.Frame(f)
        f_right.grid(row=0, column=1, sticky="nsew", padx=5, pady=5)
        
        # Checkbox de Propiedades Radiativas
        ttk.Checkbutton(f_right, text="Calcular Propiedades Radiativas (A, β, τ)", 
                        variable=self.calc_vars["rad"]).pack(anchor="w")
        
        # ASIGNACIÓN CORRECTA: Primero el widget, luego pack
        self.cs_checkbox = ttk.Checkbutton(f_right, text="Calcular Sección Eficaz de Emisión (σₑ)", 
                                           variable=self.calc_vars["cs"])
        self.cs_checkbox.pack(anchor="w")
        
        f.columnconfigure(0, weight=1)
        f.columnconfigure(1, weight=1)

    def setup_rad_options(self, p):
        self.rad_f = ttk.LabelFrame(p, text="4. Opciones de Propiedades Radiativas", padding=10)
        self.rad_f.pack(fill=tk.X, expand=False, pady=5)
        self.trans_lbl = ttk.Label(self.rad_f, text="Seleccionar transiciones a calcular:")
        self.trans_lbl.pack(anchor="w")
        self.trans_f = ttk.Frame(self.rad_f)
        self.trans_f.pack(anchor="w", fill=tk.X, pady=(5,0))

    def setup_cs_options(self, p):
        self.cs_f = ttk.LabelFrame(p, text="5. Configuración de Sección Eficaz (σₑ)", padding=10)
        
        # Contenedor principal de dos columnas
        cols_container = ttk.Frame(self.cs_f)
        cols_container.pack(fill=tk.BOTH, expand=True)

        # --- COLUMNA IZQUIERDA (Bandas y Rangos) - Más ancha ---
        left_col = ttk.Frame(cols_container)
        left_col.grid(row=0, column=0, sticky="nsew", padx=(0, 10))
        
        ttk.Label(left_col, text="Definición de Bandas:", font=('Arial', 9, 'bold')).pack(anchor="w")
        
        add_f = ttk.Frame(left_col)
        add_f.pack(fill=tk.X, pady=5)
        
        self.cs_init_lvl, self.cs_final_lvl = tk.StringVar(), tk.StringVar()
        
        # Primera fila de selección
        row1 = ttk.Frame(add_f)
        row1.pack(fill=tk.X)
        ttk.Label(row1, text="Desde:").pack(side=tk.LEFT)
        self.cs_init_combo = ttk.Combobox(row1, textvariable=self.cs_init_lvl, state="readonly", width=10)
        self.cs_init_combo.pack(side=tk.LEFT, padx=5)
        self.cs_init_combo.bind("<<ComboboxSelected>>", self.update_final_levels_combo)
        
        ttk.Label(row1, text="Hasta:").pack(side=tk.LEFT)
        self.cs_final_combo = ttk.Combobox(row1, textvariable=self.cs_final_lvl, state="readonly", width=10)
        self.cs_final_combo.pack(side=tk.LEFT, padx=5)
        
        # Segunda fila de rango
        row2 = ttk.Frame(add_f)
        row2.pack(fill=tk.X, pady=5)
        ttk.Label(row2, text="Rango (nm):").pack(side=tk.LEFT)
        self.cs_min_entry = ttk.Entry(row2, width=7)
        self.cs_min_entry.pack(side=tk.LEFT, padx=2)
        ttk.Label(row2, text="-").pack(side=tk.LEFT)
        self.cs_max_entry = ttk.Entry(row2, width=7)
        self.cs_max_entry.pack(side=tk.LEFT, padx=2)
        
        ttk.Button(row2, text="Añadir", command=self.add_band).pack(side=tk.RIGHT)

        # Listbox de bandas
        list_f = ttk.Frame(left_col)
        list_f.pack(fill=tk.BOTH, expand=True)
        self.bands_lb = tk.Listbox(list_f, height=4, font=('Arial', 9))
        scrl = ttk.Scrollbar(list_f, orient=tk.VERTICAL, command=self.bands_lb.yview)
        self.bands_lb.config(yscrollcommand=scrl.set)
        self.bands_lb.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrl.pack(side=tk.RIGHT, fill=tk.Y)
        ttk.Button(left_col, text="Eliminar", command=self.remove_band).pack(anchor="e")

        # --- COLUMNA DERECHA (Archivos de Espectros) ---
        right_col = ttk.Frame(cols_container)
        right_col.grid(row=0, column=1, sticky="nsew")
        
        ttk.Label(right_col, text="Archivos de Espectro:", font=('Arial', 9, 'bold')).pack(anchor="w")
        ttk.Button(right_col, text="Cargar Espectros", command=self.load_emission_files).pack(fill=tk.X, pady=5)
        
        # Longitud de onda de excitación
        ex_f = ttk.Frame(right_col) # O en left_col, donde prefieras
        ex_f.pack(fill=tk.X, pady=5)
        ttk.Label(ex_f, text="λ_ex (nm):").pack(side=tk.LEFT)
        ttk.Entry(ex_f, textvariable=self.lambda_ex_var, width=8).pack(side=tk.LEFT, padx=5)
        
        self.lbl_spectra_count = ttk.Label(right_col, text="Cargados: 0", foreground="green")
        self.lbl_spectra_count.pack(anchor="w")
        
        # Un pequeño cuadro de texto para listar qué muestras ya tienen archivo
        self.spectra_status_text = tk.Text(right_col, height=6, width=25, font=('Arial', 8), state=tk.DISABLED, bg="#f0f0f0")
        self.spectra_status_text.pack(fill=tk.BOTH, expand=True, pady=5)

        cols_container.columnconfigure(0, weight=3) # Columna de bandas más ancha
        cols_container.columnconfigure(1, weight=1)

    def update_spectra_status(self):
        
        # Aseguramos que el widget existe antes de escribir
        if not hasattr(self, 'spectra_status_text'): return
        
        self.spectra_status_text.config(state=tk.NORMAL)
        self.spectra_status_text.delete(1.0, tk.END)
        for sample in self.valid_samples:
            status = "[OK]" if sample in self.emission_files else "[Falta]"
            self.spectra_status_text.insert(tk.END, f"{status} {sample}\n")
        self.spectra_status_text.config(state=tk.DISABLED)
        self.lbl_spectra_count.config(text=f"Cargados: {len(self.emission_files)}")

    def setup_log_display(self, p):
        # Quitamos side=BOTTOM para que siga el flujo natural
        self.log_frame = ttk.LabelFrame(p, text="Log de Estado", padding="5")
        self.log_frame.pack(fill=tk.X, pady=10) 
        
        self.log_text = tk.Text(self.log_frame, height=4, state=tk.DISABLED, 
                                wrap=tk.WORD, font=("Arial", 8), bg="#f8f9fa")
        self.log_text.pack(fill=tk.X)

    # --- MÉTODOS HELPER RESTAURADOS ---
    def create_file_input_row(self, p, l, v, r):
        ttk.Label(p, text=l).grid(row=r, column=0, sticky="w", padx=2)
        
        # Mostramos el nombre del archivo en un Label azul para que no ocupe tanto
        name_var = tk.StringVar(value="---")
        lbl_name = ttk.Label(p, textvariable=name_var, foreground="blue", width=15)
        lbl_name.grid(row=r, column=1, padx=5)
        
        def pick_file():
            path = filedialog.askopenfilename(filetypes=[("Archivos de Texto", "*.txt")])
            if path:
                v.set(path)
                name_var.set(os.path.basename(path))
                if v == self.path_vars["osc"]:
                    self.extract_valid_samples(path)

        ttk.Button(p, text="...", command=pick_file, width=3).grid(row=r, column=2, padx=2)
        p.columnconfigure(1, weight=1)
        
    def extract_valid_samples(self, path):
        try:
            # Leemos solo la cabecera (fila 0)
            df = pd.read_csv(path, sep=r'\s+', nrows=0)
            # Filtramos para obtener solo las etiquetas de las muestras
            self.valid_samples = df.columns[2:].tolist()
            
            if self.valid_samples:
                self.log(f"Muestras identificadas: {', '.join(self.valid_samples)}")
                # Si la sección 5 ya estaba abierta, actualizamos los [Falta]
                if self.calc_vars["cs"].get():
                    self.update_spectra_status()
            else:
                messagebox.showwarning("Archivo Vacío", "No se encontraron etiquetas de muestras en el archivo de osciladores.")
        except Exception as e:
            messagebox.showerror("Error de Lectura", f"No se pudo procesar el archivo de osciladores:\n{e}")

    def create_dir_input_row(self, p, l, v, r):
        ttk.Label(p, text=l).grid(row=r, column=0, sticky="w", padx=5, pady=3)
        ttk.Entry(p, textvariable=v, width=60).grid(row=r, column=1, sticky="ew", padx=5)
        ttk.Button(p, text="Examinar...", command=lambda var=v: self.load_directory(var), width=10).grid(row=r, column=2, sticky="e", padx=5)
        p.columnconfigure(1, weight=1)

    def load_file(self, var):
        path = filedialog.askopenfilename(filetypes=[("Archivos de Texto", "*.txt")])
        if path: var.set(path)

    def load_directory(self, var):
        path = filedialog.askdirectory()
        if path: var.set(path)
    # --- FIN DE MÉTODOS HELPER ---

    def set_widget_state_recursive(self, p, state):
        try: p.configure(state=state)
        except tk.TclError: pass
        for child in p.winfo_children(): self.set_widget_state_recursive(child, state)

    def toggle_options(self, *args):
        if self.cs_checkbox is None: return

        is_rad_active = self.calc_vars["rad"].get()

        if not is_rad_active:
            # Forzamos la deselección y el bloqueo
            self.calc_vars["cs"].set(False) 
            self.cs_checkbox.configure(state=tk.DISABLED)
            # Ocultamos la sección 5 inmediatamente
            self.cs_f.pack_forget()
        else:
            self.cs_checkbox.configure(state=tk.NORMAL)

        # Visibilidad Sección 4
        self.set_widget_state_recursive(self.rad_f, tk.NORMAL if is_rad_active else tk.DISABLED)
        if is_rad_active:
            self.on_em_source_change()
        else:
            for w in self.trans_f.winfo_children(): w.destroy()
            ttk.Label(self.trans_f, text="Seleccione fuente...").pack()

        # Visibilidad Sección 5
        if self.calc_vars["cs"].get() and is_rad_active:
            self.cs_f.pack(fill=tk.X, expand=False, pady=5, after=self.rad_f)
            self.update_cs_combos()
        else:
            self.cs_f.pack_forget()

    def on_em_source_change(self, *args):
        em_path = self.get_current_em_matrix_path()
        btn_state = tk.NORMAL if self.em_source_var.get() == "user" else tk.DISABLED
        self.user_em_button.configure(state=btn_state)
        if self.calc_vars["rad"].get(): self.populate_transitions(em_path)
        if self.calc_vars["cs"].get(): self.update_cs_combos()

    def get_current_em_matrix_path(self):
        return resource_path(os.path.join('data_original','EmMatrixElements_Er.txt')) if self.em_source_var.get()=="internal" else self.path_vars["em_user"].get()

    def load_user_em_matrix(self): self.load_file(self.path_vars["em_user"]); self.on_em_source_change()

    def populate_transitions(self, fp):
        for w in self.trans_f.winfo_children(): w.destroy()
        self.trans_vars = {}
        if not self.calc_vars["rad"].get() or not fp or not os.path.exists(fp): return ttk.Label(self.trans_f, text="Seleccione fuente...").pack()
        try:
            em_df = load_emission_matrix_elements(fp); available = get_available_transitions(em_df)
            if not available: raise ValueError("No se encontraron transiciones.")
            for i, (slug, name) in enumerate(available.items()):
                var = tk.BooleanVar(value=True)
                ttk.Checkbutton(self.trans_f, text=name, variable=var).grid(row=i//4, column=i%4, sticky="w", padx=5)
                self.trans_vars[slug] = var
        except Exception as e: ttk.Label(self.trans_f, text=f"Error: {e}").pack()

    # def update_cs_combos(self, *args):
    #     em_path = self.get_current_em_matrix_path()
    #     if not em_path or not os.path.exists(em_path): self.cs_init_combo['values'] = []; self.cs_final_combo['values'] = []; return
    #     try:
    #         self.current_em_df_for_cs = load_emission_matrix_elements(em_path)
    #         initial_levels = get_available_transitions(self.current_em_df_for_cs)
    #         self.cs_init_combo['values'] = list(initial_levels.values())
    #         if self.cs_init_lvl.get() not in self.cs_init_combo['values']: self.cs_init_lvl.set(''); self.cs_final_lvl.set(''); self.cs_final_combo['values'] = []
    #         else: self.update_final_levels_combo()
    #     except Exception: self.cs_init_combo['values'] = []; self.cs_final_combo['values'] = []
        
    def update_cs_combos(self, *args):
        em_path = self.get_current_em_matrix_path()
        if not em_path or not os.path.exists(em_path): 
            self.cs_init_combo['values'] = []
            self.cs_final_combo['values'] = []
            return
        try:
            self.current_em_df_for_cs = load_emission_matrix_elements(em_path)
            initial_levels = get_available_transitions(self.current_em_df_for_cs)
            self.cs_init_combo['values'] = list(initial_levels.values())
            
            if self.cs_init_lvl.get() not in self.cs_init_combo['values']:
                self.cs_init_lvl.set('')
                self.cs_final_lvl.set('')
                self.cs_final_combo['values'] = []
            else:
                self.update_final_levels_combo()
        except Exception as e:
            self.log(f"Error cargando niveles: {e}")

    def update_final_levels_combo(self, *args):
        initial_pretty = self.cs_init_combo.get()
        if not initial_pretty or not hasattr(self, 'current_em_df_for_cs'): self.cs_final_combo['values'] = []; self.cs_final_lvl.set(''); return
        slug = next((k for k,v in PRETTY_NAMES.items() if v==initial_pretty), None)
        if not slug: self.cs_final_combo['values'] = []; self.cs_final_lvl.set(''); return
        possible_finals = self.current_em_df_for_cs[self.current_em_df_for_cs['Initial_Name_Slug']==slug]
        self.cs_final_combo['values'] = [PRETTY_NAMES.get(s, s) for s in possible_finals['Final_Name_Slug'].unique()]
        if self.cs_final_lvl.get() not in self.cs_final_combo['values']: self.cs_final_lvl.set('')

    def add_band(self):
        initial, final = self.cs_init_combo.get(), self.cs_final_combo.get()
        r_min_str, r_max_str = self.cs_min_entry.get(), self.cs_max_entry.get()
        if not (initial and final and r_min_str and r_max_str): return messagebox.showwarning("Faltan Datos", "Seleccione niveles y complete el rango.")
        try:
            r_min, r_max = float(r_min_str), float(r_max_str)
            if r_min >= r_max: raise ValueError("Rango mínimo debe ser menor al máximo.")
        except ValueError as e: return messagebox.showerror("Error de Formato", f"Rango inválido: {e}")
        i_slug,f_slug = next((k for k,v in PRETTY_NAMES.items() if v==initial),None), next((k for k,v in PRETTY_NAMES.items() if v==final),None)
        if not i_slug or not f_slug: return messagebox.showerror("Error Interno", "No se encontraron slugs.")
        band_info = {"initial":initial, "final":final, "initial_slug":i_slug, "final_slug":f_slug, "range_min":r_min, "range_max":r_max}
        self.user_bands.append(band_info); self.bands_lb.insert(tk.END, f"{initial} → {final} ({r_min}-{r_max} nm)")
        self.cs_init_lvl.set(''); self.cs_final_lvl.set(''); self.cs_min_entry.delete(0, tk.END); self.cs_max_entry.delete(0, tk.END)
        self.log(f"Banda añadida. Nota: Asegúrese que sus archivos .txt cubran el rango {r_min}-{r_max} nm.")
        
    def remove_band(self):
        sel = self.bands_lb.curselection()
        if not sel: return
        for i in sorted(sel, reverse=True): self.bands_lb.delete(i); self.user_bands.pop(i)
            
    def run_analysis(self):
        paths = {k: v.get() for k,v in self.path_vars.items()}
        if not all(p for k,p in paths.items() if k in ["osc","abs","sell"]): 
            return messagebox.showerror("Error", "Cargue los archivos de la Sección 1.")
        
        do_rad, do_cs = self.calc_vars["rad"].get(), self.calc_vars["cs"].get()
        em_path = self.get_current_em_matrix_path()
        sel_trans = [s for s,v in self.trans_vars.items() if v.get()]
        
        if do_rad and (not os.path.exists(em_path) or not sel_trans): 
            return messagebox.showerror("Error", "Para Prop. Radiativas, elija fuente y seleccione transiciones.")
        
        if do_cs:
            if not self.user_bands: 
                return messagebox.showerror("Error", "Para Sección Eficaz, añada al menos una banda.")
            if not self.emission_files: 
                return messagebox.showerror("Error", "Cargue los archivos de espectro en la Sección 5.")

        self.log("Iniciando Análisis...")
        self.root.config(cursor="watch")
        try:
            from src.physics_core import run_full_analysis
            # Se envía self.emission_files en lugar de la carpeta
            jo, rad, cs = run_full_analysis(
                paths['osc'], paths['abs'], paths['sell'], 
                self.emission_files, 
                self.sellmeier_model.get(), do_rad, em_path, sel_trans, do_cs, self.user_bands,
                self.lambda_ex_var.get()
            )
            
            self.log("¡Análisis completado!")
            if self.results_win: self.results_win.destroy()
            self.results_win = ResultsWindow(self.root, jo, rad, cs, {"do_rad":do_rad, "do_cs":do_cs})
        except Exception as e:
            self.log(f"ERROR: {e}")
            traceback.print_exc()
            messagebox.showerror("Error en Cálculo", f"Ocurrió un error:\n{e}")
        finally:
            self.root.config(cursor="")

if __name__ == "__main__":
    app_root = tk.Tk()
    JuddOfeltApp(app_root)
    app_root.mainloop()