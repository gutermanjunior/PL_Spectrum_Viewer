"""Exemplo reproduzível, usa apenas espectros reais do ZIP embarcado."""
from pathlib import Path
from matplotlib.figure import Figure

from pl_viewer.readers import scan_source
from pl_viewer.plotting import (
    PlotSettings, VerticalAnnotation, HorizontalAnnotation,
    render_plot, export_vector, save_session,
)

root = Path(__file__).resolve().parent
example = root / 'exemplos' / 'v1_3_2_anotacoes_horizontal_vertical'
example.mkdir(parents=True, exist_ok=True)
report = scan_source(root / 'exemplos' / '20261009 PL 4573-4574-4575-4576-4577.zip')
assert report.errors == []
acquisitions = []
for sample in ('4574', '4575', '4576'):
    [sp] = [s for s in report.spectra if s.sample == sample and s.slit_filename_um == 300]
    acquisitions.append(sp)
settings = PlotSettings(
    title='9 October 2026 | PL — Reference lines in X and Y',
    subtitle='Samples #4574, #4575 and #4576 · 300 µm · 77 K indicated · 200 mV setting',
    x_label='Wavelength',
    y_label='Recorded lock-in signal (original units; uncalibrated)',
    footer='Reference annotations are illustrative. Values derive from the acquisition files; no intensity calibration.',
    x_unit='nm', x_min=805, x_max=850,
)
marks = [
    VerticalAnnotation(824.5, 'Vertical reference', color='#687180',
                       linestyle=':', label_y=.75, label_dx_pt=-62),
    HorizontalAnnotation(.045, 'Horizontal reference', color='#894bba',
                         linestyle='--', label_x=.76, label_dy_pt=32),
]
fig = Figure(figsize=(15, 8.7), dpi=140)
render_plot(fig, acquisitions, settings, marks)
for extension in ('png', 'svg', 'pdf'):
    export_vector(fig, example / ('referencias_vertical_horizontal.' + extension), title='PL 9 Oct 2026 example')
save_session(example / 'referencias_vertical_horizontal_edicao.json', settings, marks,
             str(root/'exemplos'/'20261009 PL 4573-4574-4575-4576-4577.zip'),
             [s.uid for s in acquisitions], 0, True, True)
print(example)
