# FROPA: Fluorescence Radiative and Optical Parameter Analyzer (v1.2.1)

FROPA is an open-source software tool, written in Python with a graphical user interface (GUI). It is designed to facilitate the calculation of Judd-Ofelt intensity parameters ($\Omega_{\lambda}$), oscillator strengths ($f_{exp}$ and $f_{cal}$) and subsequent optical and radiative properties for rare-earth ions (currently Er³⁺) in glass matrices and other materials.

## Key Features 

- **Dynamic Transition Labeling:** Automatically identifies and formats absorption/emission bands using standard spectroscopic notation (e.g., $^2K_{15/2}$, $^4G_{9/2}$, $^4I_{15/2}$).
- **JO Parameter Calculation:** Performs a least-squares fit to determine $\Omega_{\lambda}$ parameters from experimental oscillator strengths.  
- **Flexible Radiative Property Calculation:** Computes transition probabilities (A), branching ratios (β), and radiative lifetimes (τ) for *user-selected* emission transitions.  
- **Flexible Cross-Section Calculation:** Estimates the stimulated emission cross-section (σₑ) for *user-defined* emission bands using the Fütchbauer-Ladenburg relation.  
- **Configurable Data Sources:** Allows using internal emission matrix elements (based on literature data, e.g., Kaminskii et al. \[cite: 1\]) or loading a custom user file.  
- **Configurable Sellmeier Model:** Supports the two common models (n² \= 1 \+ ... and n² \= A \+ ...) and automatically validates the coefficient file structure.  
- **Intuitive GUI & Export:** Simplifies file loading, calculation setup, and allows saving the full analysis report to a .txt file via a separate results window.

## 📚 Theoretical Background

FROPA performs calculations based on the standard Judd-Ofelt theory. The reduced matrix elements ($U^\lambda$) used for the absorption fitting are based on the spectroscopic data established by **Carnall et al. (1968)**. For emission analysis, the software provides internal matrix elements based on the data reported by **Kaminskii et al. (1995)**.

If you choose to use a custom file for the matrix elements, ensure it follows the strict row-order consistency and structure described in [FILE_FORMATS.md](FILE_FORMATS.md) to maintain calculation accuracy.

## **Installation and Usage**

There are two ways to use FROPA:

### **Option 1: Executable (Recommended)**

1. Go to the **"Releases"** section of this GitHub repository.  
2. Download the executable file (FROPA\_v1.2.1.exe or the latest version).  
3. Run the file. No installation is required.  
4. Load your experimental data files (.txt) as indicated in the interface. Refer to [FILE\_FORMATS.md](https://www.google.com/search?q=FILE_FORMATS.md) for the required file formats.

### **Option 2: From Source Code (For developers)**

1. Clone or download this repository.  
2. Open a terminal in the project folder.  
3. (Optional but recommended) Create and activate a virtual environment:  
   python \-m venv venv  
   \# Windows:  
   venv\\Scripts\\activate  
   \# macOS/Linux:  
   \# source venv/bin/activate

4. Install dependencies:  
   pip install \-r requirements.txt

5. Run the application:  
   python main\_gui.py

## **Input File Formats**

The application requires specific formats for the input .txt files.

**\- Please consult the detailed format guide [FILE_FORMATS.md](FILE_FORMATS.md)** for detailed examples of:

* Oscillator Strength files (now including the Transition column).
* Absorption Matrix Elements.
* Sellmeier Coefficients.
* Emission Spectra data.

## 🧪 Testing with Example Data

To help you get started, the repository includes a set of dummy experimental data located in the `data_original/` folder. You can use these files to test the software's functionality:

1. **Input Files:** Use `Oscillator.txt`, `AbsMatrixElements_C1968.txt`, and `Sellmeier.txt`.
2. **Emission Data:** For Cross-Section calculations, use the individual `emision_SAMPLEA.txt` and `emision_SAMPLEB.txt` files.
3. **Verification:** You can compare your results with the reference outputs provided in the `data_original/res/` folder, which contains the expected parameters and tables for these specific dummy samples.

## **How to Cite**

If you use FROPA in your research, **please cite BOTH**: the primary article describing the methodology and the DOI for this software.

1. **Primary Article:**  
   *F. Angulo S.*, et al. "Title (to be updated after publication)". *Journal Name*, Volume, Pages (Year).  
   DOI: **[to be updated after publication]**

2. **Software (FROPA v1.1):**  
   *F. Angulo S.*. *FROPA: Fluorescence Radiative and Optical Parameter Analyzer* (v1.1) [Software].  
   Zenodo (2025). DOI: [10.5281/zenodo.17437584](https://doi.org/10.5281/zenodo.17437584)

## **License**

This project is distributed under the MIT License. See the LICENSE file for details.