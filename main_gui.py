import tkinter as tk
from tkinter import ttk, filedialog, messagebox, font
import os
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

# --- Ventana de Resultados ---
class ResultsWindow(tk.Toplevel):
    def __init__(self, parent, jo, rad, cs, conf):
        super().__init__(parent)
        self.title("Resultados del Análisis")
        self.geometry("800x600")
        try:
            self.iconbitmap(resource_path("icon.ico"))
        except Exception: pass
        self.results_font = font.Font(family="Courier", size=10)
        mf = ttk.Frame(self, padding="10")
        mf.pack(fill=tk.BOTH, expand=True)
        sy, sx = ttk.Scrollbar(mf, orient=tk.VERTICAL), ttk.Scrollbar(mf, orient=tk.HORIZONTAL)
        self.rt = tk.Text(mf, wrap=tk.NONE, yscrollcommand=sy.set, xscrollcommand=sx.set, font=self.results_font)
        sy.config(command=self.rt.yview)
        sx.config(command=self.rt.xview)
        sy.pack(side=tk.RIGHT, fill=tk.Y)
        sx.pack(side=tk.BOTTOM, fill=tk.X)
        self.rt.pack(fill=tk.BOTH, expand=True)
        ttk.Button(mf, text="Guardar Resultados en .txt", command=self.save).pack(pady=(10, 0), anchor="e")
        self.display(jo, rad, cs, conf)
        self.raw_text = self.rt.get(1.0, tk.END)
        self.transient(parent)
        self.grab_set()

    def log(self, msg): self.rt.insert(tk.END, msg + "\n")

    def display(self, jo, rad, cs, conf):
        self.log("="*80 + "\n--- PARÁMETROS DE JUDD-OFELT ---\n" + "="*80)
        self.log(pd.DataFrame(jo).to_string(index=False, float_format="%.4f"))
        if conf["do_rad"]:
            self.log("\n\n" + "="*80 + "\n--- PROPIEDADES RADIATIVAS ---\n" + "="*80)
            for s, df in rad.items():
                self.log(f"\n--- Muestra: {s} ---")
                if df.empty: self.log("No se calcularon propiedades."); continue
                df_p=df.copy(); df_p['SLJ']=df_p['SLJ'].map(PRETTY_NAMES).fillna(df_p['SLJ']); df_p["S'L'J'"]=df_p["S'L'J'"].map(PRETTY_NAMES).fillna(df_p["S'L'J'"])
                self.log(df_p.to_string(index=False, float_format="%.4f"))
        if conf["do_cs"] and cs:
            self.log("\n\n"+"="*80+"\n--- SECCIÓN EFICAZ DE EMISIÓN ---\n"+"="*80)
            df_cs = pd.DataFrame(cs).reindex(columns=['λ_ex (nm)','Glass','Level','E_exp (cm⁻¹)','Δλ_eff (nm)','σₑ (x10⁻²¹ cm²)','ΔG (x10⁻²⁸ cm³)'])
            self.log(df_cs.to_string(index=False, float_format="%.4f"))

    def save(self):
        fp = filedialog.asksaveasfilename(title="Guardar como...", defaultextension=".txt", filetypes=[("Archivos de Texto", "*.txt")])
        if not fp: return
        try:
            with open(fp, 'w', encoding='utf-8') as f: f.write("Resultados del Análisis Judd-Ofelt\FJORA v1.1\n"+"="*40+"\n\n"+self.raw_text)
        except Exception as e: messagebox.showerror("Error al Guardar", f"No se pudo guardar: {e}")

# --- CLASE PRINCIPAL ---
class JuddOfeltApp:
    def __init__(self, root):
        self.root = root
        self.root.title("FROPA – Fluorescence Radiative and Optical Parameter Analyzer v1.1")
        self.root.geometry("800x850")
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

    def setup_ui(self, p):
        self.setup_file_inputs(p)
        self.setup_em_source(p)
        self.setup_calc_config(p)
        self.setup_rad_options(p)
        self.setup_cs_options(p)
        ttk.Button(p, text="Ejecutar Análisis", command=self.run_analysis).pack(pady=15, ipady=5)
        self.setup_log_display(p)

    def log(self, msg):
        self.log_text.config(state=tk.NORMAL)
        self.log_text.delete(1.0, tk.END)
        self.log_text.insert(tk.END, msg)
        self.log_text.config(state=tk.DISABLED)
        self.root.update_idletasks()

    def setup_file_inputs(self, p):
        f = ttk.LabelFrame(p,text="1. Archivos Principales",padding=10)
        f.pack(fill=tk.X,expand=False,pady=5)
        self.create_file_input_row(f,"Fuerza de Oscilador (.txt):",self.path_vars["osc"],0)
        self.create_file_input_row(f,"Matriz Absorción (.txt):",self.path_vars["abs"],1)
        self.create_file_input_row(f,"Coef. Sellmeier (.txt):",self.path_vars["sell"],2)
        self.create_dir_input_row(f,"Carpeta Espectros Emisión:",self.path_vars["em_dir"],3)

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
        ttk.Combobox(f_left, textvariable=self.sellmeier_model, values=[SELLMEIER_MODEL_1, SELLMEIER_MODEL_2], state="readonly", width=30).pack(anchor="w", fill=tk.X)
        f_right = ttk.Frame(f)
        f_right.grid(row=0, column=1, sticky="nsew", padx=5, pady=5)
        ttk.Checkbutton(f_right, text="Calcular Propiedades Radiativas (A, β, τ)", variable=self.calc_vars["rad"]).pack(anchor="w")
        ttk.Checkbutton(f_right, text="Calcular Sección Eficaz de Emisión (σₑ)", variable=self.calc_vars["cs"]).pack(anchor="w")
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
        self.cs_f = ttk.LabelFrame(p, text="5. Definición de Bandas para Sección Eficaz (σₑ)", padding=10)
        self.cs_f.pack(fill=tk.X, expand=False, pady=5)
        add_f = ttk.Frame(self.cs_f); add_f.pack(fill=tk.X, pady=5)
        self.cs_init_lvl, self.cs_final_lvl = tk.StringVar(), tk.StringVar()
        self.cs_min_entry, self.cs_max_entry = ttk.Entry(add_f, width=7), ttk.Entry(add_f, width=7)
        ttk.Label(add_f, text="Desde:").grid(row=0, column=0, padx=2)
        self.cs_init_combo = ttk.Combobox(add_f, textvariable=self.cs_init_lvl, state="readonly", width=10)
        self.cs_init_combo.grid(row=0, column=1, padx=2); self.cs_init_combo.bind("<<ComboboxSelected>>", self.update_final_levels_combo)
        ttk.Label(add_f, text="Hasta:").grid(row=0, column=2, padx=2)
        self.cs_final_combo = ttk.Combobox(add_f, textvariable=self.cs_final_lvl, state="readonly", width=10)
        self.cs_final_combo.grid(row=0, column=3, padx=2)
        ttk.Label(add_f, text="Rango (nm):").grid(row=0, column=4, padx=(10,2)); self.cs_min_entry.grid(row=0, column=5)
        ttk.Label(add_f, text="-").grid(row=0, column=6); self.cs_max_entry.grid(row=0, column=7)
        ttk.Button(add_f, text="Añadir Banda", command=self.add_band).grid(row=0, column=8, padx=(10,2))
        list_f = ttk.Frame(self.cs_f); list_f.pack(fill=tk.X, pady=5)
        bands_scrl = ttk.Scrollbar(list_f, orient=tk.VERTICAL)
        self.bands_lb = tk.Listbox(list_f, height=5, yscrollcommand=bands_scrl.set)
        bands_scrl.config(command=self.bands_lb.yview); bands_scrl.pack(side=tk.RIGHT, fill=tk.Y)
        self.bands_lb.pack(side=tk.LEFT, fill=tk.X, expand=True)
        ttk.Button(list_f, text="Eliminar", command=self.remove_band, width=8).pack(side=tk.LEFT, padx=10, anchor="center")

    def setup_log_display(self, p):
        f = ttk.LabelFrame(p, text="Log de Estado", padding="5"); f.pack(fill=tk.BOTH, expand=True, pady=5)
        self.log_text = tk.Text(f, height=5, state=tk.DISABLED, wrap=tk.WORD)
        self.log_text.pack(fill=tk.BOTH, expand=True)

    # --- MÉTODOS HELPER RESTAURADOS ---
    def create_file_input_row(self, p, l, v, r):
        ttk.Label(p, text=l).grid(row=r, column=0, sticky="w", padx=5, pady=3)
        ttk.Entry(p, textvariable=v, width=60).grid(row=r, column=1, sticky="ew", padx=5)
        ttk.Button(p, text="Examinar...", command=lambda var=v: self.load_file(var), width=10).grid(row=r, column=2, sticky="e", padx=5)
        p.columnconfigure(1, weight=1)

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
        self.set_widget_state_recursive(self.rad_f, tk.NORMAL if self.calc_vars["rad"].get() else tk.DISABLED)
        if self.calc_vars["rad"].get(): self.on_em_source_change()
        else: self.populate_transitions(None)
        self.set_widget_state_recursive(self.cs_f, tk.NORMAL if self.calc_vars["cs"].get() else tk.DISABLED)
        if self.calc_vars["cs"].get(): self.update_cs_combos()

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

    def update_cs_combos(self, *args):
        em_path = self.get_current_em_matrix_path()
        if not em_path or not os.path.exists(em_path): self.cs_init_combo['values'] = []; self.cs_final_combo['values'] = []; return
        try:
            self.current_em_df_for_cs = load_emission_matrix_elements(em_path)
            initial_levels = get_available_transitions(self.current_em_df_for_cs)
            self.cs_init_combo['values'] = list(initial_levels.values())
            if self.cs_init_lvl.get() not in self.cs_init_combo['values']: self.cs_init_lvl.set(''); self.cs_final_lvl.set(''); self.cs_final_combo['values'] = []
            else: self.update_final_levels_combo()
        except Exception: self.cs_init_combo['values'] = []; self.cs_final_combo['values'] = []

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

    def remove_band(self):
        sel = self.bands_lb.curselection()
        if not sel: return
        for i in sorted(sel, reverse=True): self.bands_lb.delete(i); self.user_bands.pop(i)
            
    def run_analysis(self):
        paths = {k: v.get() for k,v in self.path_vars.items()}
        if not all(p for k,p in paths.items() if k in ["osc","abs","sell"]): return messagebox.showerror("Error", "Cargue los archivos de la Sección 1.")
        do_rad, do_cs = self.calc_vars["rad"].get(), self.calc_vars["cs"].get()
        em_path = self.get_current_em_matrix_path()
        sel_trans = [s for s,v in self.trans_vars.items() if v.get()]
        if do_rad and (not os.path.exists(em_path) or not sel_trans): return messagebox.showerror("Error", "Para Prop. Radiativas, elija fuente y seleccione transiciones.")
        if do_cs and not self.user_bands: return messagebox.showerror("Error", "Para Sección Eficaz, añada al menos una banda.")
        if do_cs and not paths["em_dir"]: return messagebox.showerror("Error", "Para Sección Eficaz, especifique 'Carpeta Espectros Emisión'.")
        self.log("--- Iniciando Análisis... ---"); self.root.config(cursor="watch")
        try:
            from src.physics_core import run_full_analysis
            jo, rad, cs = run_full_analysis(paths['osc'], paths['abs'], paths['sell'], paths['em_dir'], self.sellmeier_model.get(), do_rad, em_path, sel_trans, do_cs, self.user_bands)
            self.log("¡Análisis completado! Mostrando resultados...");
            if self.results_win: self.results_win.destroy()
            self.results_win = ResultsWindow(self.root, jo, rad, cs, {"do_rad":do_rad, "do_cs":do_cs})
        except Exception as e:
            self.log(f"ERROR: {e}"); traceback.print_exc(); messagebox.showerror("Error en Cálculo", f"Ocurrió un error:\n{e}")
        finally:
            self.root.config(cursor="")

if __name__ == "__main__":
    app_root = tk.Tk()
    JuddOfeltApp(app_root)
    app_root.mainloop()