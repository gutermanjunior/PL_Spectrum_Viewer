"""Cria dois exemplos a partir das aquisições reais de 09/10/2026 incluídas no projeto.

As anotações são demonstrativas e não atribuem causas físicas às feições.
Nenhuma correção de linha de base, calibração ou normalização é aplicada.
"""
from pathlib import Path
from matplotlib.figure import Figure
from pl_viewer.readers import scan_source
from pl_viewer.plotting import PlotSettings, VerticalAnnotation, render_plot, export_vector, save_session

ROOT = Path(__file__).resolve().parent
source = ROOT / "exemplos" / "20261009 PL 4573-4574-4575-4576-4577.zip"
output = ROOT / "exemplos" / "figuras_vetoriais"
output.mkdir(exist_ok=True)
spectra = scan_source(source).spectra

selected = [s for s in spectra if s.sample in ("4574", "4575", "4576")
            and s.slit_filename_um == 300 and s.lockin_range_mv == 200]
figure = Figure(figsize=(15, 8.7), dpi=100)
style = PlotSettings(
    title="October 9, 2026  |  Low-temperature growth series",
    x_label="Wavelength", y_label="Recorded lock-in signal (original units; uncalibrated)",
    footer="Same nominal 300 µm slits and 200 mV lock-in setting. Do not infer quantum efficiency from peak height.",
    x_min=760, x_max=930, y_min=0, y_max=.167,
)
markings = [
    VerticalAnnotation(824.5, "Observed maximum", linestyle=":", label_y=.71, label_dx_pt=-65),
    VerticalAnnotation(834, "Reference only", color="#d14343", linestyle="--", label_y=.39, label_dx_pt=75),
]
render_plot(figure, selected, style, markings)
for extension in (".pdf", ".svg", ".png"):
    export_vector(figure, output / ("PL_09out_300um_200mV_anotado" + extension), title=style.title)
save_session(output / "PL_09out_300um_200mV_anotado_edicao.json", style, markings,
             str(source), [sp.uid for sp in selected], 0, True, True)

selected = [s for s in spectra if s.sample in ("4573", "4577")
            and s.slit_filename_um == 90 and s.lockin_range_mv == 500]
figure = Figure(figsize=(15, 8.7), dpi=100)
style = PlotSettings(
    title="October 9, 2026  |  Five wells vs. one well",
    x_label="Wavelength", y_label="Recorded lock-in signal (original units; uncalibrated)",
    footer="Direct measurement comparison: same nominal slit width and lock-in setting. No baseline correction or normalization.",
    x_min=760, x_max=855, y_min=0, y_max=.51,
)
render_plot(figure, selected, style)
for extension in (".pdf", ".svg", ".png"):
    export_vector(figure, output / ("PL_09out_90um_500mV_comparacao" + extension), title=style.title)
print("Figuras de exemplo criadas em", output)
