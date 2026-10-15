"""Generate a reproducible v1.3 sample, without altering any raw PL acquisition.

Usage: python gerar_exemplo_v13.py
"""
from pathlib import Path
from matplotlib.figure import Figure
from pl_viewer.readers import scan_source
from pl_viewer.plotting import (PlotSettings, VerticalAnnotation, render_plot,
                                export_vector, save_session)

ROOT = Path(__file__).resolve().parent
SOURCE = ROOT / 'exemplos' / '20261009 PL 4573-4574-4575-4576-4577.zip'
OUT = ROOT / 'exemplos' / 'v1_3_maximo_e_fatores'
OUT.mkdir(parents=True, exist_ok=True)
records = [sp for sp in scan_source(SOURCE).spectra
           if sp.sample in ('4574', '4575', '4576')
           and sp.slit_filename_um == 300 and sp.lockin_range_mv == 200]
records = sorted(records, key=lambda sp: sp.sample)
assert len(records) == 3, 'Exemplo requer as três medidas de 300 µm/200 mV'
settings = PlotSettings(
    title='October 9, 2026  |  Low-temperature growth series',
    subtitle='Máximo discreto assinalado na série #4575; série #4576 multiplicada por 2',
    x_min=760, x_max=930,
    x_label='Wavelength',
    y_label='Recorded lock-in signal (original units; uncalibrated)',
    footer='Visual scaling only (×2 applied to #4576). No baseline correction or absolute calibration.',
)
marks = [VerticalAnnotation(824.5, 'Referência visual', color='#687180',
                            label_y=.69, label_dx_pt=70)]
scale_factors = {sp.uid: 2.0 for sp in records if sp.sample == '4576'}
peak_uid = next(sp.uid for sp in records if sp.sample == '4575')
fig = Figure(figsize=(15, 8.7), dpi=100)
render_plot(fig, records, settings, marks, scale_factors=scale_factors,
            highlight_peak_uid=peak_uid)
for ext in ('pdf', 'svg', 'png'):
    export_vector(fig, OUT / f'exemplo_PL_v13.{ext}', title=settings.title)
save_session(OUT / 'exemplo_PL_v13_edicao.json', settings, marks, str(SOURCE),
             [sp.uid for sp in records], 0, True, True,
             scale_factors=scale_factors, highlight_peak_uid=peak_uid)
print('Created in', OUT)
