# Praxis Analyze — Scientific Data Analysis with Publication-Quality Figures

Analyze experimental data using the Praxis toolkit (50+ characterisation techniques, 9 journal styles).

## Prerequisites

Check if Praxis is available: look for `vendor/praxis/scripts/` directory. If not found, report: "Praxis not installed. Run: git submodule add https://github.com/zmtsikriteas/praxis.git vendor/praxis && pip install -r vendor/praxis/requirements.txt" and fall back to generic matplotlib analysis.

## Instructions

1. **Read the Praxis skill** at `.claude/skills/praxis/SKILL.md` for full capabilities and API reference
2. **Read the Praxis cookbook** at `vendor/praxis/references/cookbook.md` for worked examples of the relevant technique
3. **Identify the data type** from the files in `attachments/` or the path specified:
   - Praxis auto-detects 16 formats: CSV, TSV, Excel, JSON, .xy, .dat, .spe, JCAMP-DX, HDF5, MATLAB, Bruker XRD, Gamry, etc.
4. **Detect the characterisation technique** from the data and user description:

| Data pattern | Technique | Praxis module |
|-|-|-|
| 2theta + intensity | XRD | `techniques.xrd` — phase ID, Scherrer crystallite size, Williamson-Hall |
| Temperature + heat flow | DSC | `techniques.dsc` — Tg, Tm, Tc, enthalpy |
| Temperature + weight | TGA | `techniques.dsc` — decomposition, residue |
| Stress + strain | Mechanical | `techniques.mechanical` — modulus, UTS, elongation |
| Wavenumber + transmittance | FTIR | `techniques.spectro` — peak assignment, baseline |
| Raman shift + intensity | Raman | `techniques.spectro` — peak fitting |
| Binding energy + counts | XPS | `techniques.xps` — peak deconvolution |
| Z_real + Z_imag | EIS | `techniques.impedance` — Nyquist, Bode, circuit fit |
| Voltage + current | I-V | `techniques.impedance` — solar cell J-V |
| Field + magnetisation | VSM/SQUID | `techniques.magnetic` — M-H loops, coercivity |
| Wavelength + absorbance | UV-Vis | `techniques.spectro` — band gap, Beer-Lambert |
| Relative pressure + volume | BET | `techniques.porosity` — surface area, pore distribution |
| Generic x-y data | General | `analysis.fitting`, `analysis.peaks` |

5. **Match journal style to venue**: Read `.venue.json` for the target venue, map to Praxis style:

| Venue | Praxis style |
|-|-|
| `nature` | `nature` |
| `ieee` | `ieee` |
| `acm` | `acs` (closest) |
| `neurips` | `science` (closest) |
| `arxiv` | `nature` (clean default) |
| `apa` | `elsevier` (closest) |
| `generic` | `nature` |

6. **Write and execute a Python analysis script**:
   ```python
   import sys
   sys.path.insert(0, "vendor/praxis/scripts")

   from core.loader import load_data
   from core.plotter import plot_data
   from core.exporter import export_figure
   from core.utils import apply_style, set_palette
   from techniques.<module> import <analysis_function>

   # Load
   df = load_data("attachments/<datafile>")

   # Analyse (technique-specific)
   results = <analysis_function>(df[...], df[...], ...)

   # Plot with venue-matched style
   apply_style("<venue_style>")
   set_palette("okabe_ito")  # colourblind-safe default
   fig, ax = plot_data(x, y, kind="line", xlabel="...", ylabel="...", title="...")

   # Export as PDF for LaTeX
   export_figure(fig, "figures/<descriptive_name>.pdf", dpi=300)
   ```
   Save the script to `figures/scripts/<analysis_name>.py`
   Run it: `python3 figures/scripts/<analysis_name>.py`
   Verify the output exists: `ls figures/<descriptive_name>.pdf`

7. **Extract quantitative results** from the analysis (crystallite size, Tg, modulus, etc.)

8. **Integrate into the paper**:
   - Add `\includegraphics{figures/<name>.pdf}` with descriptive caption to Results section of `main.tex`
   - Add quantitative results to the text: "XRD analysis revealed a crystallite size of X nm..."
   - Add methodology details to Methods section: "XRD patterns were analysed using Scherrer equation..."

9. **Write analysis report** to `research/praxis_analysis.md`:
   - Technique used
   - Key parameters and results
   - Figure file paths
   - Script file paths (for reproducibility)

## Batch Processing

If multiple data files of the same type exist, use Praxis batch processing:
```python
from batch.processor import batch_process
batch_process("attachments/*.csv", pipeline="xrd_standard", output_dir="figures")
```

## Arguments

$ARGUMENTS

Accepts a file path or technique name. If empty, scans `attachments/` and auto-detects techniques.
