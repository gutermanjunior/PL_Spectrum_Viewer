"""Headless example: click order #4576 -> #4574 -> #4575, tab10 colors."""
from pathlib import Path
from matplotlib.figure import Figure
from pl_viewer.readers import scan_source
from pl_viewer.plotting import PlotSettings, export_vector, render_plot, save_session
from pl_viewer.selection_order import SelectionOrder

root = Path(__file__).resolve().parent
spectra = scan_source(str(root / 'exemplos' / '20261009 PL 4573-4574-4575-4576-4577.zip'), False, 'auto').spectra
order = SelectionOrder()
by_uid = {}
for sample in ('4576', '4574', '4575'):
    spec = next(sp for sp in spectra if sp.sample == sample and sp.slit_filename_um == 300 and sp.lockin_range_mv == 200)
    by_uid[spec.uid] = spec
    order.set_checked(spec.uid, True)
selected = [by_uid[uid] for uid in order.uids]
settings = PlotSettings(
    title='09/10/2026  |  Cores na ordem de seleção',
    subtitle='Marcação: #4576 → #4574 → #4575',
    x_label='Comprimento de onda',
    y_label='Sinal registrado no lock-in (unidades originais, não calibradas)',
    footer='Azul: primeiro clique  •  Laranja: segundo  •  Verde: terceiro. Mesma fenda nominal e configuração do lock-in.',
    x_min=760, x_max=930, y_min=0,
)
fig = Figure(figsize=(14.5, 8.2))
axes = render_plot(fig, selected, settings, mode=0)
out = root / 'exemplos' / 'v1_3_1_cores_por_selecao'
out.mkdir(parents=True, exist_ok=True)
for extension in ('png', 'svg'):
    export_vector(fig, out / f'ordem_4576_4574_4575.{extension}', title=settings.title)
save_session(out / 'ordem_4576_4574_4575_edicao.json', settings, [],
             str(root / 'exemplos' / '20261009 PL 4573-4574-4575-4576-4577.zip'),
             order.uids, 0, True, True)
print('Seleção/legenda:', [line.get_label() for line in axes[0].lines])
print('Cores:', [line.get_color() for line in axes[0].lines])
print('Exemplo:', out)
