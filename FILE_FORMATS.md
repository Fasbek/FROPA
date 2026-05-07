# **FROPA: Input File Format Guide (.txt)**

The FROPA application requires several text files (.txt) as input. It is crucial that these files adhere to the formats described below. Data should be separated by spaces or tabs. Lines starting with \# are treated as comments and ignored.

**1\. Oscillator Strength File (Oscillator\_\*.txt)**

Maps absorption bands (identified by peak wavelength in nm) to their experimental oscillator strengths (dimensionless) for one or more samples.

* **First line:** Header row with column names.
* **First column:** Contains the name of the transition (e.g., 4I11/2, 4F9/2). These labels are used for reporting.
* **Second column:** Contains the peak absorption wavelengths in nm. Used for refractive index and Lorentz local field calculations.
* **Subsequent columns:** Each additional column represents a different sample. The header name (e.g., Glass\_A) will be used as the unique sample identifier.

**Example (for 2 samples):**

\# Experimental Oscillator Strength Data for XYZ Glasses  
Transition    Band    Glass\_A     Glass\_B  
4I11/2    976.96  2.641E-6    2.286E-6  
4I9/2    797.93  1.347E-6    1.213E-6  
4F9/2    652.97  1.023E-5    8.710E-6  
\# ... (more rows, one for each observed band)

**2\. Absorption Matrix Elements File (AbsMatrixElements\_\*.txt)**

Contains the theoretical reduced matrix elements ($U^2, U^4, U^6$, dimensionless) corresponding to the **absorption** transitions from the ground state.

* **No header line.**  
* Each row corresponds to an absorption transition.  
* **CRITICAL:** The rows in this file must be in the **exact same order** as the wavelengths (bands) listed in the Oscillator Strength file.  
* **Format:** Three numerical columns separated by spaces/tabs: $U^2$ $U^4$ $U^6$

**Example (matching the order of the previous example):**

\# Reduced Matrix Elements (Absorption)  
\# Order: Transition at \~977 nm, \~798 nm, \~653 nm, etc.  
0.0282  0.0003  0.3953  
0       0.1733  0.0099  
0       0.5354  0.4618  
\# ... (more rows)

*   **Scientific Reference:** The theoretical reduced matrix elements ($U^k$) for Erbium (Er³⁺) and other rare-earth ions can be found in the classic works of **W. T. Carnall et al.**. 
    *   For the Er³⁺ aquo-ion values often used in glass analysis, refer to: *Carnall W, Fields P, Rajnak K. Electronic energy levels in the trivalent lanthanide aquo ions. I. Pr3+, Nd3+, Pm3+, Sm3+, Dy3+, Ho3+, Er3+, and Tm3+. J Chem Phys 1968;49:4424–42. https://doi.org/10.1063/1.1669893.*

**3\. Sellmeier Coefficients File (Sellmeier\_\*.txt)**

Defines the coefficients (dimensionless) used to calculate the refractive index for each sample via the Sellmeier equation. The expected format depends on the **Sellmeier Model** selected in the GUI.

* **First line:** Header row with column names.  
* **First column:** Sample identifier (e.g., Sample). This name must match (or map via TZGE→TZGNE logic) the identifiers used in the Oscillator Strength file.  
* **Subsequent columns:** The numerical coefficients.  
  * **Model n² \= 1 \+ Σ \[Bᵢ / (1 \- Cᵢ/λ²)\]**: Must have an **EVEN** number of coefficient columns (e.g., B1, C1, B2, C2).  
  * **Model n² \= A \+ Σ \[Bᵢ / (1 \- Cᵢ/λ²)\]**: Must have an **ODD** number of coefficient columns (e.g., A, B1, C1).  
* **Note on Column Names:** The exact names used in the header for the coefficients (e.g., B1, C1, A) **do not matter** to the code. The code reads coefficients by their **position** and validates based on the **total number** of coefficient columns according to the selected model. The names B1, C1, etc., are just conventional labels.

**Example (Model 1 with 4 coefficients: B1, C1, B2, C2):**

\# Sellmeier Coefficients (Model n² \= 1 \+ ...)  
Sample      B1          C1          B2          C2  
TZGNE025    2.15202     109667.9    2.61829     \-115084.3  
Glass\_B     2.2         110000.0    2.7         \-120000.0  
\# ... (more samples)

**Example (Model 2 with 3 coefficients: A, B1, C1):**

\# Sellmeier Coefficients (Model n² \= A \+ ...)  
Sample      Coeff\_A     Coeff\_B1    Coeff\_C1  
MyGlassX    1.9         1.0         10000.0  
MyGlassY    1.95        1.1         11000.0  
\# ... (more samples)

**4\. Folder Containing Emission Spectra**

Unlike absorption data, emission spectra are **selected individually** for each sample through the GUI.
This is **not a single file**, but a **folder** containing multiple .txt files, one for each emission spectrum you wish to analyze for cross-sections.

* In Section 5, you must manually select the specific .txt file corresponding to each sample identifier listed in your Oscillator Strength file.  
* The **filename** must exactly match the sample identifier, prefixed with emision\_ (e.g., emision\_Glass\_A.txt). The TZGE→TZGNE mapping logic also applies here.  
* Each spectrum .txt file must contain **two numerical columns**, separated by spaces or tabs, with no header:  
  1. Wavelength in nm.  
  2. Emission Intensity (arbitrary units; will be normalized internally).
* Files should ideally not have headers, but if they do, ensure they start with # to be ignored

**Example (content of emision\_Glass\_A.txt):**

\# Emission Spectrum for Glass\_A sample  
\# Wavelength (nm)   Intensity (a.u.)  
1450.0  100.5  
1450.5  102.1  
1451.0  105.3  
\# ... (full spectrum data) ...  
1650.0  95.2

**5\. Emission Matrix Elements File (EmMatrixElements\_\*.txt) \- Optional**

This file is only needed if you select "Load custom file" as the Emission Data Source. It contains the reduced matrix elements ($U^2, U^4, U^6$) and quantum numbers for **emission** transitions.

* **No header line.**  
* **Ten numerical columns**, separated by spaces/tabs:  
  1. J\_initial  
  2. L\_initial  
  3. S\_initial  
  4. J\_final  
  5. L\_final  
  6. S\_final  
  7. wavenumber\_cm\_1 (Barycenter of the J→J' transition in cm⁻¹)  
  8. $U^2$  
  9. $U^4$  
  10. $U^6$  
* **Note on Internal Data:** The default internal data used by FROPA is based on the calculations reported for Er³⁺ by A. A. Kaminskii et al., phys. stat. sol. (a) **151**, 231 (1995) \[cite: 1\].

**Example (for Er³⁺):**

\# Reduced Matrix Elements (Emission) \- Example Er3+  
\# J\_i L\_i S\_i J\_f L\_f S\_f wavenumber U2      U4      U6  
4.5 6 1.5 5.5 6 1.5 2150       0.003   0.0674  0.1271  \# 4I9/2 \-\> 4I11/2  
6.5 6 1.5 7.5 6 1.5 6500       0.0160  0.1180  1.4580  \# 4I13/2 \-\> 4I15/2  
\# ... (more rows for all relevant J-\>J' transitions)  

## 📝 Templates and Examples

If you are unsure about the formatting, please refer to the example files provided in the `data_original/` directory:
- **Oscillator_*.txt:** See `Oscillator.txt` for a multi-sample header structure.
- **AbsMatrixElements_*.txt:** See `AbsMatrixElements_C1968.txt` for the 3-column matrix format.
- **Sellmeier_*.txt:** See `Sellmeier.txt` for the 4-coefficient model structure.

These files use dummy data but maintain the strict structural requirements of FROPA.